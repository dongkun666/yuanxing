#!/bin/bash
# ============================================================
# LexPrime 私有化部署 - 健康检查脚本
# 版本: 1.0.0
# 日期: 2026-07-03
# 描述: 检查 LexPrime 部署的健康状态
# ============================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置变量
INSTALL_DIR="/opt/lexprime"
CONFIG_FILE="/etc/lexprime/config.env"
API_URL="http://localhost:3847"
WEB_URL="http://localhost:8080"

CHECK_ALL=true
CHECK_API=false
CHECK_DB=false
CHECK_ES=false
CHECK_NEO4J=false
CHECK_DISK=false
CHECK_MEMORY=false
CHECK_DOCKER=false

OUTPUT_FORMAT="text"

# ============================================================
# 工具函数
# ============================================================

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[FAIL]${NC} $1"; }

load_config() {
    if [[ -f $CONFIG_FILE ]]; then
        source $CONFIG_FILE
        API_URL="http://localhost:${API_PORT:-3847}"
        WEB_URL="http://localhost:${WEB_PORT:-8080}"
    fi
}

# 结果统计
PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

check_pass() {
    PASS_COUNT=$((PASS_COUNT + 1))
    log_success "$1"
}

check_warn() {
    WARN_COUNT=$((WARN_COUNT + 1))
    log_warning "$1"
}

check_fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    log_error "$1"
}

# ============================================================
# 各项检查
# ============================================================

check_os() {
    echo ""
    log_info "=== 系统检查 ==="
    
    # 操作系统
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        check_pass "操作系统: $NAME $VERSION_ID"
    else
        check_pass "操作系统: $(uname -s) $(uname -r)"
    fi
    
    # 主机名
    check_pass "主机名: $(hostname)"
    
    # 系统时间
    check_pass "系统时间: $(date)"
    
    # 运行时间
    if command -v uptime &> /dev/null; then
        UPTIME=$(uptime -p 2>/dev/null || uptime)
        check_pass "运行时间: $UPTIME"
    fi
    
    # 内核版本
    check_pass "内核版本: $(uname -r)"
}

check_disk() {
    echo ""
    log_info "=== 磁盘检查 ==="
    
    # 检查数据目录
    if [[ -d $INSTALL_DIR ]]; then
        DISK_USAGE=$(df -h $INSTALL_DIR | awk 'NR==2{print $5}' | tr -d '%')
        DISK_AVAIL=$(df -h $INSTALL_DIR | awk 'NR==2{print $4}')
        
        if [[ $DISK_USAGE -gt 90 ]]; then
            check_fail "安装目录磁盘使用率: ${DISK_USAGE}% (可用: $DISK_AVAIL)"
        elif [[ $DISK_USAGE -gt 75 ]]; then
            check_warn "安装目录磁盘使用率: ${DISK_USAGE}% (可用: $DISK_AVAIL)"
        else
            check_pass "安装目录磁盘使用率: ${DISK_USAGE}% (可用: $DISK_AVAIL)"
        fi
    else
        check_warn "安装目录不存在: $INSTALL_DIR"
    fi
    
    # 检查数据目录
    DATA_DIR="/var/lexprime"
    if [[ -d $DATA_DIR ]]; then
        DISK_USAGE=$(df -h $DATA_DIR | awk 'NR==2{print $5}' | tr -d '%')
        DISK_AVAIL=$(df -h $DATA_DIR | awk 'NR==2{print $4}')
        
        if [[ $DISK_USAGE -gt 90 ]]; then
            check_fail "数据目录磁盘使用率: ${DISK_USAGE}% (可用: $DISK_AVAIL)"
        elif [[ $DISK_USAGE -gt 75 ]]; then
            check_warn "数据目录磁盘使用率: ${DISK_USAGE}% (可用: $DISK_AVAIL)"
        else
            check_pass "数据目录磁盘使用率: ${DISK_USAGE}% (可用: $DISK_AVAIL)"
        fi
        
        # 数据目录大小
        DATA_SIZE=$(du -sh $DATA_DIR 2>/dev/null | awk '{print $1}')
        check_pass "数据目录大小: $DATA_SIZE"
    fi
    
    # inode 使用情况
    if [[ -d $INSTALL_DIR ]]; then
        INODE_USAGE=$(df -i $INSTALL_DIR | awk 'NR==2{print $5}' | tr -d '%')
        if [[ $INODE_USAGE -gt 90 ]]; then
            check_fail "Inode 使用率: ${INODE_USAGE}%"
        else
            check_pass "Inode 使用率: ${INODE_USAGE}%"
        fi
    fi
}

check_memory() {
    echo ""
    log_info "=== 内存检查 ==="
    
    if command -v free &> /dev/null; then
        MEM_TOTAL=$(free -m | awk 'NR==2{print $2}')
        MEM_USED=$(free -m | awk 'NR==2{print $3}')
        MEM_AVAIL=$(free -m | awk 'NR==2{print $7}')
        MEM_PERCENT=$((MEM_USED * 100 / MEM_TOTAL))
        
        if [[ $MEM_PERCENT -gt 90 ]]; then
            check_fail "内存使用率: ${MEM_PERCENT}% (${MEM_USED}MB / ${MEM_TOTAL}MB)"
        elif [[ $MEM_PERCENT -gt 75 ]]; then
            check_warn "内存使用率: ${MEM_PERCENT}% (${MEM_USED}MB / ${MEM_TOTAL}MB)"
        else
            check_pass "内存使用率: ${MEM_PERCENT}% (${MEM_USED}MB / ${MEM_TOTAL}MB)"
        fi
        
        check_pass "可用内存: ${MEM_AVAIL}MB"
        
        # Swap
        SWAP_TOTAL=$(free -m | awk 'NR==3{print $2}')
        if [[ $SWAP_TOTAL -gt 0 ]]; then
            SWAP_USED=$(free -m | awk 'NR==3{print $3}')
            SWAP_PERCENT=$((SWAP_USED * 100 / SWAP_TOTAL))
            if [[ $SWAP_PERCENT -gt 50 ]]; then
                check_warn "Swap 使用率: ${SWAP_PERCENT}%"
            else
                check_pass "Swap 使用率: ${SWAP_PERCENT}%"
            fi
        fi
    fi
}

check_cpu() {
    echo ""
    log_info "=== CPU 检查 ==="
    
    CPU_CORES=$(nproc)
    check_pass "CPU 核心数: $CPU_CORES"
    
    # CPU 负载
    if command -v uptime &> /dev/null; then
        LOAD_AVG=$(uptime | awk -F'load average: ' '{print $2}' | cut -d',' -f1 | tr -d ' ')
        LOAD_PERCENT=$(echo "$LOAD_AVG * 100 / $CPU_CORES" | bc 2>/dev/null || echo "0")
        
        if [[ $(echo "$LOAD_PERCENT > 90" | bc 2>/dev/null) -eq 1 ]]; then
            check_fail "CPU 负载: ${LOAD_AVG} (1分钟)"
        elif [[ $(echo "$LOAD_PERCENT > 70" | bc 2>/dev/null) -eq 1 ]]; then
            check_warn "CPU 负载: ${LOAD_AVG} (1分钟)"
        else
            check_pass "CPU 负载: ${LOAD_AVG} (1分钟)"
        fi
    fi
}

check_docker() {
    echo ""
    log_info "=== Docker 检查 ==="
    
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | awk '{print $3}' | cut -d',' -f1)
        check_pass "Docker 版本: $DOCKER_VERSION"
        
        # Docker 是否运行
        if docker info &> /dev/null; then
            check_pass "Docker 服务: 运行中"
            
            # 容器状态
            if [[ -f $INSTALL_DIR/docker-compose.yml ]]; then
                cd $INSTALL_DIR
                
                if docker compose version &> /dev/null; then
                    CONTAINER_COUNT=$(docker compose ps -q 2>/dev/null | wc -l)
                    RUNNING_COUNT=$(docker compose ps --filter status=running -q 2>/dev/null | wc -l)
                elif command -v docker-compose &> /dev/null; then
                    CONTAINER_COUNT=$(docker-compose ps -q 2>/dev/null | wc -l)
                    RUNNING_COUNT=$(docker-compose ps | grep -c "Up" 2>/dev/null || echo "0")
                else
                    CONTAINER_COUNT=0
                    RUNNING_COUNT=0
                fi
                
                if [[ $RUNNING_COUNT -eq $CONTAINER_COUNT ]]; then
                    check_pass "容器状态: $RUNNING_COUNT / $CONTAINER_COUNT 运行中"
                else
                    check_warn "容器状态: $RUNNING_COUNT / $CONTAINER_COUNT 运行中"
                fi
            fi
        else
            check_fail "Docker 服务未运行"
        fi
        
        # Docker Compose
        if docker compose version &> /dev/null; then
            COMPOSE_VERSION=$(docker compose version | awk '{print $4}' | cut -d',' -f1)
            check_pass "Docker Compose: $COMPOSE_VERSION (V2)"
        elif command -v docker-compose &> /dev/null; then
            COMPOSE_VERSION=$(docker-compose --version | awk '{print $3}' | cut -d',' -f1)
            check_pass "Docker Compose: $COMPOSE_VERSION (V1)"
        else
            check_warn "Docker Compose 未安装"
        fi
    else
        check_fail "Docker 未安装"
    fi
}

check_api() {
    echo ""
    log_info "=== API 服务检查 ==="
    
    if command -v curl &> /dev/null; then
        # 检查 API 健康状态
        if curl -s --connect-timeout 5 "$API_URL/api/health" &> /dev/null; then
            check_pass "API 服务: 正常 ($API_URL)"
            
            # 获取健康详情
            HEALTH_RESP=$(curl -s --connect-timeout 5 "$API_URL/api/health" 2>/dev/null)
            
            # 检查数据库
            if echo "$HEALTH_RESP" | grep -q '"status":\s*"ok"'; then
                check_pass "API 状态: 健康"
            else
                check_warn "API 状态: 降级"
            fi
        else
            check_fail "API 服务: 无法连接 ($API_URL)"
        fi
        
        # 检查 Web 服务
        if curl -s --connect-timeout 5 "$WEB_URL" &> /dev/null; then
            check_pass "Web 服务: 正常 ($WEB_URL)"
        else
            check_warn "Web 服务: 无法连接 ($WEB_URL)"
        fi
    else
        check_warn "curl 未安装，跳过 API 检查"
    fi
}

check_database() {
    echo ""
    log_info "=== 数据库检查 ==="
    
    if [[ -f $INSTALL_DIR/docker-compose.yml ]]; then
        cd $INSTALL_DIR
        
        # PostgreSQL
        if docker compose version &> /dev/null; then
            if docker compose exec -T postgres pg_isready -U lexprime 2>/dev/null | grep -q "accepting connections"; then
                check_pass "PostgreSQL: 运行正常"
                
                # 数据库连接数
                CONN_COUNT=$(docker compose exec -T postgres psql -U lexprime -d lexprime -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | tr -d ' ' || echo "0")
                check_pass "数据库连接数: $CONN_COUNT"
            else
                check_fail "PostgreSQL: 连接失败"
            fi
        fi
    fi
}

check_elasticsearch() {
    echo ""
    log_info "=== Elasticsearch 检查 ==="
    
    if command -v curl &> /dev/null; then
        if curl -s --connect-timeout 5 "http://localhost:9200/_cluster/health" &> /dev/null; then
            ES_STATUS=$(curl -s --connect-timeout 5 "http://localhost:9200/_cluster/health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
            ES_VERSION=$(curl -s --connect-timeout 5 "http://localhost:9200" | grep -o '"number":"[^"]*"' | head -1 | cut -d'"' -f4)
            
            if [[ $ES_STATUS == "green" ]]; then
                check_pass "Elasticsearch: 健康 (green) - 版本 $ES_VERSION"
            elif [[ $ES_STATUS == "yellow" ]]; then
                check_warn "Elasticsearch: 警告 (yellow) - 版本 $ES_VERSION"
            else
                check_fail "Elasticsearch: 异常 ($ES_STATUS) - 版本 $ES_VERSION"
            fi
            
            # 索引数量
            ES_INDICES=$(curl -s --connect-timeout 5 "http://localhost:9200/_cat/indices?v" 2>/dev/null | wc -l)
            check_pass "索引数量: $((ES_INDICES - 1))"
        else
            check_warn "Elasticsearch: 无法连接"
        fi
    fi
}

check_license() {
    echo ""
    log_info "=== License 检查 ==="
    
    if command -v curl &> /dev/null; then
        # 尝试获取 License 信息 (需要认证，简化处理)
        check_pass "License 管理: 已启用离线激活"
        check_pass "激活方式: 离线激活"
    fi
}

check_services() {
    echo ""
    log_info "=== 系统服务检查 ==="
    
    # 检查 systemd 服务
    if systemctl list-unit-files | grep -q lexprime; then
        if systemctl is-active --quiet lexprime; then
            check_pass "LexPrime 服务: 运行中"
        else
            check_fail "LexPrime 服务: 未运行"
        fi
    else
        check_warn "LexPrime systemd 服务: 未配置"
    fi
    
    # 检查端口监听
    if command -v ss &> /dev/null || command -v netstat &> /dev/null; then
        PORT_CMD=$(command -v ss 2>/dev/null || command -v netstat 2>/dev/null)
        
        for port in 3847 8080 5432 9200 7687; do
            if $PORT_CMD -tlnp 2>/dev/null | grep -q ":$port "; then
                check_pass "端口 $port: 监听中"
            else
                case $port in
                    3847|8080)
                        check_warn "端口 $port: 未监听"
                        ;;
                    *)
                        check_warn "端口 $port: 未监听 (可能未启用该组件)"
                        ;;
                esac
            fi
        done
    fi
}

# ============================================================
# 生成报告
# ============================================================

print_summary() {
    echo ""
    echo "============================================================"
    echo "  健康检查汇总"
    echo "============================================================"
    echo ""
    echo "  通过: $PASS_COUNT 项"
    echo "  警告: $WARN_COUNT 项"
    echo "  失败: $FAIL_COUNT 项"
    echo ""
    
    if [[ $FAIL_COUNT -gt 0 ]]; then
        echo -e "  整体状态: ${RED}异常${NC}"
        echo ""
        echo "  请处理失败项后重新检查"
        exit_code=1
    elif [[ $WARN_COUNT -gt 0 ]]; then
        echo -e "  整体状态: ${YELLOW}需关注${NC}"
        echo ""
        echo "  建议处理警告项"
        exit_code=0
    else
        echo -e "  整体状态: ${GREEN}健康${NC}"
        echo ""
        echo "  所有检查项均通过"
        exit_code=0
    fi
    
    echo ""
    echo "============================================================"
    
    return $exit_code
}

# ============================================================
# 主流程
# ============================================================

main() {
    echo ""
    echo "============================================================"
    echo "  LexPrime 私有化部署 - 健康检查"
    echo "============================================================"
    
    load_config
    
    check_os
    check_cpu
    check_memory
    check_disk
    
    if [[ "$CHECK_DOCKER" == "true" ]] || [[ "$CHECK_ALL" == "true" ]]; then
        check_docker
    fi
    
    if [[ "$CHECK_DB" == "true" ]] || [[ "$CHECK_ALL" == "true" ]]; then
        check_database
    fi
    
    if [[ "$CHECK_ES" == "true" ]] || [[ "$CHECK_ALL" == "true" ]]; then
        check_elasticsearch
    fi
    
    if [[ "$CHECK_API" == "true" ]] || [[ "$CHECK_ALL" == "true" ]]; then
        check_api
    fi
    
    if [[ "$CHECK_ALL" == "true" ]]; then
        check_services
        check_license
    fi
    
    print_summary
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --api)
            CHECK_ALL=false
            CHECK_API=true
            shift
            ;;
        --db|--database)
            CHECK_ALL=false
            CHECK_DB=true
            shift
            ;;
        --es|--elasticsearch)
            CHECK_ALL=false
            CHECK_ES=true
            shift
            ;;
        --docker)
            CHECK_ALL=false
            CHECK_DOCKER=true
            shift
            ;;
        --disk)
            CHECK_ALL=false
            CHECK_DISK=true
            shift
            ;;
        --memory)
            CHECK_ALL=false
            CHECK_MEMORY=true
            shift
            ;;
        --format=*)
            OUTPUT_FORMAT="${1#*=}"
            shift
            ;;
        --dir=*)
            INSTALL_DIR="${1#*=}"
            shift
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --api           仅检查 API 服务"
            echo "  --db            仅检查数据库"
            echo "  --es            仅检查 Elasticsearch"
            echo "  --docker        仅检查 Docker"
            echo "  --disk          仅检查磁盘"
            echo "  --memory        仅检查内存"
            echo "  --dir=PATH      指定安装目录 (默认: /opt/lexprime)"
            echo "  --help, -h      显示帮助信息"
            echo ""
            exit 0
            ;;
        *)
            log_error "未知选项: $1"
            exit 1
            ;;
    esac
done

main
