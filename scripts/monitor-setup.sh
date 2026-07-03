#!/bin/bash
set -e

MONITOR_DIR="/opt/lexprime-monitor"
LOG_DIR="/var/log/lexprime"
ALERT_DIR="$MONITOR_DIR/alerts"
CONFIG_DIR="$MONITOR_DIR/config"

echo "=== LexPrime Monitoring Setup ==="

mkdir -p "$MONITOR_DIR" "$LOG_DIR" "$ALERT_DIR" "$CONFIG_DIR"

echo "1. Installing monitoring tools..."

if command -v apt-get &> /dev/null; then
    apt-get update && apt-get install -y \
        curl \
        wget \
        jq \
        bc \
        htop \
        iotop \
        iftop \
        net-tools \
        dstat \
        fail2ban \
        postfix \
        mailutils
elif command -v yum &> /dev/null; then
    yum install -y \
        curl \
        wget \
        jq \
        bc \
        htop \
        iotop \
        iftop \
        net-tools \
        dstat \
        fail2ban \
        postfix \
        mailx
else
    echo "Unsupported package manager. Please install dependencies manually."
    exit 1
fi

echo "2. Setting up log monitoring..."

cat > "$CONFIG_DIR/log-monitor.conf" << 'EOF'
LOG_PATHS="/var/log/nginx/*.log /var/log/lexprime/*.log"
ERROR_PATTERNS="ERROR|error|CRITICAL|critical|FATAL|fatal"
WARNING_PATTERNS="WARNING|warning"
CHECK_INTERVAL=60
MAX_ERRORS_PER_MINUTE=10
ALERT_EMAIL="admin@lexprime.com"
EOF

cat > "$MONITOR_DIR/log-monitor.sh" << 'EOF'
#!/bin/bash
source /opt/lexprime-monitor/config/log-monitor.conf

check_errors() {
    local error_count=0
    local warning_count=0
    
    for log_path in $LOG_PATHS; do
        if [ -f "$log_path" ]; then
            local errors=$(grep -cE "$ERROR_PATTERNS" "$log_path" 2>/dev/null || 0)
            local warnings=$(grep -cE "$WARNING_PATTERNS" "$log_path" 2>/dev/null || 0)
            error_count=$((error_count + errors))
            warning_count=$((warning_count + warnings))
        fi
    done
    
    echo "{\"errors\": $error_count, \"warnings\": $warning_count, \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
}

while true; do
    result=$(check_errors)
    echo "$result" >> "$ALERT_DIR/log-stats.log"
    
    errors=$(echo "$result" | jq -r '.errors')
    
    if [ "$errors" -gt "$MAX_ERRORS_PER_MINUTE" ]; then
        echo "ALERT: High error rate detected - $errors errors" >> "$ALERT_DIR/alerts.log"
        echo "High error rate detected: $errors errors" | mail -s "LexPrime Alert: High Error Rate" "$ALERT_EMAIL"
    fi
    
    sleep "$CHECK_INTERVAL"
done
EOF

chmod +x "$MONITOR_DIR/log-monitor.sh"

echo "3. Setting up performance monitoring..."

cat > "$CONFIG_DIR/performance.conf" << 'EOF'
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90
NETWORK_THRESHOLD=1000000
CHECK_INTERVAL=30
ALERT_EMAIL="admin@lexprime.com"
EOF

cat > "$MONITOR_DIR/performance-monitor.sh" << 'EOF'
#!/bin/bash
source /opt/lexprime-monitor/config/performance.conf

check_cpu() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    echo "$cpu_usage"
}

check_memory() {
    local mem_total=$(free -m | grep Mem | awk '{print $2}')
    local mem_used=$(free -m | grep Mem | awk '{print $3}')
    local mem_percent=$(echo "scale=2; $mem_used / $mem_total * 100" | bc)
    echo "$mem_percent"
}

check_disk() {
    local disk_percent=$(df -h / | grep / | awk '{print $5}' | sed 's/%//g')
    echo "$disk_percent"
}

check_network() {
    local rx_bytes=$(cat /proc/net/dev | grep eth0 | awk '{print $2}')
    echo "$rx_bytes"
}

send_alert() {
    local metric=$1
    local current=$2
    local threshold=$3
    echo "ALERT: $metric usage is ${current}%, exceeds threshold ${threshold}%" >> "$ALERT_DIR/alerts.log"
    echo "$metric usage is ${current}%, exceeds threshold ${threshold}%" | mail -s "LexPrime Alert: $metric High" "$ALERT_EMAIL"
}

while true; do
    cpu=$(check_cpu)
    mem=$(check_memory)
    disk=$(check_disk)
    
    echo "{\"cpu\": $cpu, \"memory\": $mem, \"disk\": $disk, \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" >> "$ALERT_DIR/performance-stats.log"
    
    cpu_int=$(echo "$cpu" | awk -F. '{print $1}')
    mem_int=$(echo "$mem" | awk -F. '{print $1}')
    
    if [ "$cpu_int" -ge "$CPU_THRESHOLD" ]; then
        send_alert "CPU" "$cpu" "$CPU_THRESHOLD"
    fi
    
    if [ "$mem_int" -ge "$MEMORY_THRESHOLD" ]; then
        send_alert "Memory" "$mem" "$MEMORY_THRESHOLD"
    fi
    
    if [ "$disk" -ge "$DISK_THRESHOLD" ]; then
        send_alert "Disk" "$disk" "$DISK_THRESHOLD"
    fi
    
    sleep "$CHECK_INTERVAL"
done
EOF

chmod +x "$MONITOR_DIR/performance-monitor.sh"

echo "4. Setting up alert rules..."

cat > "$CONFIG_DIR/alert-rules.conf" << 'EOF'
ALERT_LEVELS=critical,warning,info

CRITICAL_RULES=(
    "cpu_usage>=90"
    "memory_usage>=95"
    "disk_usage>=95"
    "service_down"
    "database_connection_failure"
)

WARNING_RULES=(
    "cpu_usage>=70"
    "memory_usage>=80"
    "disk_usage>=85"
    "high_error_rate"
    "slow_response_time"
)

INFO_RULES=(
    "deployment_start"
    "deployment_complete"
    "backup_start"
    "backup_complete"
)

NOTIFICATION_CHANNELS=email,slack

SLACK_WEBHOOK_URL=""
EMAIL_RECIPIENTS="admin@lexprime.com,devops@lexprime.com"
EOF

cat > "$MONITOR_DIR/alert-manager.sh" << 'EOF'
#!/bin/bash
source /opt/lexprime-monitor/config/alert-rules.conf

send_notification() {
    local level=$1
    local message=$2
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    echo "[$timestamp] [$level] $message" >> "$ALERT_DIR/alerts.log"
    
    for channel in $NOTIFICATION_CHANNELS; do
        case $channel in
            email)
                echo "$message" | mail -s "LexPrime $level Alert" "$EMAIL_RECIPIENTS"
                ;;
            slack)
                if [ -n "$SLACK_WEBHOOK_URL" ]; then
                    curl -X POST -H 'Content-type: application/json' \
                        --data "{\"text\": \"*LexPrime $level Alert*\n$message\"}" \
                        "$SLACK_WEBHOOK_URL"
                fi
                ;;
        esac
    done
}

trigger_alert() {
    local level=$1
    local message=$2
    
    case $level in
        critical)
            send_notification "CRITICAL" "$message"
            ;;
        warning)
            send_notification "WARNING" "$message"
            ;;
        info)
            send_notification "INFO" "$message"
            ;;
        *)
            send_notification "UNKNOWN" "$message"
            ;;
    esac
}

if [ $# -ge 2 ]; then
    trigger_alert "$1" "$2"
fi
EOF

chmod +x "$MONITOR_DIR/alert-manager.sh"

echo "5. Setting up Docker container monitoring..."

cat > "$MONITOR_DIR/docker-monitor.sh" << 'EOF'
#!/bin/bash

check_containers() {
    local containers=$(docker ps -a --format "{{.Names}}:{{.Status}}")
    
    while IFS= read -r container; do
        name=$(echo "$container" | cut -d: -f1)
        status=$(echo "$container" | cut -d: -f2)
        
        if echo "$status" | grep -q "Exited"; then
            echo "ALERT: Container $name is not running" >> "$ALERT_DIR/alerts.log"
            echo "Container $name is not running (Status: $status)" | mail -s "LexPrime Alert: Container Down" admin@lexprime.com
        fi
    done <<< "$containers"
}

check_container_resources() {
    docker stats --no-stream --format "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
}

if [ "$1" = "check" ]; then
    check_containers
elif [ "$1" = "stats" ]; then
    check_container_resources
else
    check_containers
    check_container_resources
fi
EOF

chmod +x "$MONITOR_DIR/docker-monitor.sh"

echo "6. Setting up cron jobs..."

cat > /etc/cron.d/lexprime-monitor << 'EOF'
* * * * * root /opt/lexprime-monitor/log-monitor.sh &
* * * * * root /opt/lexprime-monitor/performance-monitor.sh &
*/5 * * * * root /opt/lexprime-monitor/docker-monitor.sh check
*/15 * * * * * root /opt/lexprime-monitor/docker-monitor.sh stats >> /var/log/lexprime/docker-stats.log
EOF

echo "7. Setting up fail2ban..."

cat > /etc/fail2ban/jail.d/lexprime.conf << 'EOF'
[lexprime-nginx]
enabled = true
port = http,https
filter = lexprime-nginx
logpath = /var/log/nginx/access.log
maxretry = 5
bantime = 3600
findtime = 600
EOF

cat > /etc/fail2ban/filter.d/lexprime-nginx.conf << 'EOF'
[Definition]
failregex = ^<HOST> .* "(GET|POST|PUT|DELETE).*" 403
ignoreregex =
EOF

systemctl enable fail2ban
systemctl start fail2ban

echo "8. Setting up log rotation..."

cat > /etc/logrotate.d/lexprime << 'EOF'
/var/log/lexprime/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root adm
    postrotate
        systemctl reload nginx > /dev/null 2>&1 || true
    endscript
}

/var/log/nginx/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root adm
    postrotate
        systemctl reload nginx > /dev/null 2>&1 || true
    endscript
}
EOF

echo "9. Creating monitoring dashboard script..."

cat > "$MONITOR_DIR/dashboard.sh" << 'EOF'
#!/bin/bash

echo "=== LexPrime System Dashboard ==="
echo "Last Updated: $(date)"
echo ""

echo "--- System Resources ---"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')%"
echo "Memory Usage: $(free -m | grep Mem | awk '{print $3 "/" $2 "MB (" $3/$2*100 "%)"}')"
echo "Disk Usage: $(df -h / | grep / | awk '{print $5 " used"}')"
echo ""

echo "--- Network Status ---"
echo "$(netstat -tuln | grep LISTEN | head -5)"
echo ""

echo "--- Docker Containers ---"
echo "$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}")"
echo ""

echo "--- Recent Alerts ---"
echo "$(tail -10 /opt/lexprime-monitor/alerts/alerts.log)"
EOF

chmod +x "$MONITOR_DIR/dashboard.sh"

echo ""
echo "=== Monitoring Setup Complete ==="
echo ""
echo "Monitoring scripts installed to: $MONITOR_DIR"
echo "Log files stored at: $LOG_DIR"
echo "Alert files stored at: $ALERT_DIR"
echo ""
echo "Usage:"
echo "  Check dashboard: $MONITOR_DIR/dashboard.sh"
echo "  Check containers: $MONITOR_DIR/docker-monitor.sh check"
echo "  View container stats: $MONITOR_DIR/docker-monitor.sh stats"
echo "  Trigger alert: $MONITOR_DIR/alert-manager.sh <level> <message>"
echo ""
echo "Note: Configure SLACK_WEBHOOK_URL in $CONFIG_DIR/alert-rules.conf for Slack notifications"
echo "Note: Update ALERT_EMAIL in config files for email notifications"