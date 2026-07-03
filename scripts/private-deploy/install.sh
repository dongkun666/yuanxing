#!/bin/bash
# ============================================================
# LexPrime 私有化部署 - 一键安装脚本
# 版本: 1.0.0
# 日期: 2026-07-03
# 描述: 一键安装 LexPrime 私有化部署版本
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
DATA_DIR="/var/lexprime"
LOG_DIR="/var/log/lexprime"
BACKUP_DIR="/var/lexprime/backup"
CONFIG_FILE="/etc/lexprime/config.env"
SERVICE_NAME="lexprime"

# 版本信息
VERSION="1.0.0"
MIN_DOCKER_VERSION="20.10"
MIN_COMPOSE_VERSION="2.0"

# ============================================================
# 工具函数
# ============================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要 root 权限运行"
        log_info "请使用: sudo $0"
        exit 1
    fi
}

# ============================================================
# 系统检查
# ============================================================

check_os() {
    log_info "检查操作系统..."
    
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    
    log_info "操作系统: $OS $VER"
    
    # 支持的系统
    SUPPORTED_OS=("Ubuntu" "Debian" "CentOS Linux" "Red Hat Enterprise Linux Server" "Amazon Linux")
    SUPPORTED=0
    
    for supported in "${SUPPORTED_OS[@]}"; do
        if [[ "$OS" == *"$supported"* ]]; then
            SUPPORTED=1
            break
        fi
    done
    
    if [[ $SUPPORTED -eq 0 ]]; then
        log_warning "当前操作系统可能未完全测试，但继续安装..."
    fi
    
    log_success "操作系统检查完成"
}

check_hardware() {
    log_info "检查硬件资源..."
    
    # CPU 核心数
    CPU_CORES=$(nproc)
    log_info "CPU 核心数: $CPU_CORES"
    
    if [[ $CPU_CORES -lt 2 ]]; then
        log_warning "建议至少 2 核 CPU，当前: $CPU_CORES 核"
    fi
    
    # 内存
    MEM_TOTAL=$(free -m | awk 'NR==2{print $2}')
    log_info "内存: ${MEM_TOTAL}MB"
    
    if [[ $MEM_TOTAL -lt 2048 ]]; then
        log_warning "建议至少 2GB 内存，当前: ${MEM_TOTAL}MB"
    fi
    
    # 磁盘空间
    DISK_AVAILABLE=$(df -m / | awk 'NR==2{print $4}')
    log_info "可用磁盘空间: ${DISK_AVAILABLE}MB"
    
    if [[ $DISK_AVAILABLE -lt 10240 ]]; then
        log_warning "建议至少 10GB 磁盘空间，当前: ${DISK_AVAILABLE}MB"
    fi
    
    log_success "硬件资源检查完成"
}

check_docker() {
    log_info "检查 Docker 环境..."
    
    if ! command -v docker &> /dev/null; then
        log_warning "Docker 未安装，将自动安装 Docker"
        install_docker
        return
    fi
    
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | cut -d',' -f1)
    log_info "Docker 版本: $DOCKER_VERSION"
    
    # 检查 Docker 是否运行
    if ! docker info &> /dev/null; then
        log_error "Docker 未运行，请先启动 Docker"
        exit 1
    fi
    
    # 检查 Docker Compose
    if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
        log_warning "Docker Compose 未安装，将自动安装"
        install_compose
    else
        if docker compose version &> /dev/null; then
            COMPOSE_VERSION=$(docker compose version | awk '{print $4}' | cut -d',' -f1)
        else
            COMPOSE_VERSION=$(docker-compose --version | awk '{print $3}' | cut -d',' -f1)
        fi
        log_info "Docker Compose 版本: $COMPOSE_VERSION"
    fi
    
    log_success "Docker 环境检查完成"
}

install_docker() {
    log_info "开始安装 Docker..."
    
    if [[ -f /etc/debian_version ]]; then
        # Debian/Ubuntu
        apt-get update -qq
        apt-get install -y -qq apt-transport-https ca-certificates curl gnupg lsb-release
        
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
        
        apt-get update -qq
        apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
    elif [[ -f /etc/redhat-release ]]; then
        # CentOS/RHEL
        yum install -y -q yum-utils
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        yum install -y -q docker-ce docker-ce-cli containerd.io docker-compose-plugin
        
        systemctl start docker
        systemctl enable docker
    else
        log_error "不支持的操作系统，请手动安装 Docker"
        exit 1
    fi
    
    log_success "Docker 安装完成"
}

install_compose() {
    log_info "安装 Docker Compose..."
    
    if command -v docker &> /dev/null; then
        # Docker Compose V2 插件方式
        DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
        mkdir -p $DOCKER_CONFIG/cli-plugins
        curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" -o $DOCKER_CONFIG/cli-plugins/docker-compose
        chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
    else
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi
    
    log_success "Docker Compose 安装完成"
}

# ============================================================
# 安装流程
# ============================================================

create_directories() {
    log_info "创建目录结构..."
    
    mkdir -p $INSTALL_DIR
    mkdir -p $DATA_DIR/{db,es,neo4j,uploads,cache}
    mkdir -p $LOG_DIR
    mkdir -p $BACKUP_DIR
    mkdir -p /etc/lexprime
    
    log_success "目录创建完成"
    log_info "  安装目录: $INSTALL_DIR"
    log_info "  数据目录: $DATA_DIR"
    log_info "  日志目录: $LOG_DIR"
    log_info "  备份目录: $BACKUP_DIR"
}

generate_config() {
    log_info "生成配置文件..."
    
    # 生成随机密钥
    SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)
    DB_PASSWORD=$(openssl rand -hex 16 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
    JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 64 | head -n 1)
    
    cat > $CONFIG_FILE << EOF
# ============================================================
# LexPrime 私有化部署配置文件
# 生成时间: $(date)
# ============================================================

# 基础配置
LEXPRIME_VERSION=$VERSION
INSTALL_MODE=private
SECRET_KEY=$SECRET_KEY
JWT_SECRET=$JWT_SECRET

# 服务配置
API_HOST=0.0.0.0
API_PORT=3847
WEB_PORT=8080

# 数据库配置
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=lexprime
DB_USER=lexprime
DB_PASSWORD=$DB_PASSWORD

# Elasticsearch 配置
ES_HOST=localhost
ES_PORT=9200
ES_INDEX_CASES=lexprime_cases
ES_INDEX_LAWS=lexprime_laws
ES_INDEX_COMPANIES=lexprime_companies

# Neo4j 配置
NEO4J_HOST=localhost
NEO4J_PORT=7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=lexprime123

# 存储配置
UPLOAD_DIR=$DATA_DIR/uploads
CACHE_DIR=$DATA_DIR/cache
LOG_DIR=$LOG_DIR
BACKUP_DIR=$BACKUP_DIR

# 安全配置
SESSION_TIMEOUT=86400
MAX_LOGIN_ATTEMPTS=5
PASSWORD_MIN_LENGTH=8

# AI 配置 (可根据实际 license 调整)
AI_ENABLED=true
AI_PROVIDER=local

# License 配置 (安装后请激活)
LICENSE_KEY=
LICENSE_MODE=offline

EOF
    
    chmod 600 $CONFIG_FILE
    log_success "配置文件已生成: $CONFIG_FILE"
}

deploy_services() {
    log_info "部署服务..."
    
    # 如果有 docker-compose 文件，则启动容器
    if [[ -f "$INSTALL_DIR/docker-compose.yml" ]]; then
        cd $INSTALL_DIR
        if docker compose version &> /dev/null; then
            docker compose up -d
        else
            docker-compose up -d
        fi
        log_success "Docker 服务已启动"
    else
        log_warning "未找到 docker-compose.yml，跳过容器部署"
        log_info "请将应用文件放置于 $INSTALL_DIR 后手动启动"
    fi
}

setup_systemd() {
    log_info "配置系统服务..."
    
    cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=LexPrime 私有化部署服务
After=network.target docker.service

[Service]
Type=forking
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$CONFIG_FILE
ExecStart=/bin/bash -c 'cd $INSTALL_DIR && docker compose up -d'
ExecStop=/bin/bash -c 'cd $INSTALL_DIR && docker compose down'
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable $SERVICE_NAME 2>/dev/null || true
    
    log_success "系统服务已配置"
}

setup_firewall() {
    log_info "配置防火墙..."
    
    # 尝试开放端口
    if command -v ufw &> /dev/null; then
        ufw allow 8080/tcp 2>/dev/null || true
        ufw allow 3847/tcp 2>/dev/null || true
        log_info "已在 UFW 中开放端口 8080, 3847"
    elif command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-port=8080/tcp 2>/dev/null || true
        firewall-cmd --permanent --add-port=3847/tcp 2>/dev/null || true
        firewall-cmd --reload 2>/dev/null || true
        log_info "已在 firewalld 中开放端口 8080, 3847"
    fi
    
    log_success "防火墙配置完成"
}

# ============================================================
# 安装后检查
# ============================================================

wait_for_services() {
    log_info "等待服务启动..."
    
    # 简单等待
    sleep 5
    
    # 检查 API 健康状态
    if command -v curl &> /dev/null; then
        local retries=10
        local count=0
        
        while [[ $count -lt $retries ]]; do
            if curl -s http://localhost:3847/api/health &> /dev/null; then
                log_success "API 服务已就绪"
                return 0
            fi
            sleep 3
            count=$((count + 1))
        done
        
        log_warning "API 服务健康检查超时，请稍后手动检查"
    fi
}

print_summary() {
    echo ""
    echo "============================================================"
    echo -e "${GREEN}  LexPrime 私有化部署安装完成！${NC}"
    echo "============================================================"
    echo ""
    echo "  版本: $VERSION"
    echo "  安装模式: 私有化部署"
    echo ""
    echo "  访问地址:"
    echo "    Web 界面: http://<服务器IP>:8080"
    echo "    API 接口: http://<服务器IP>:3847"
    echo "    API 文档: http://<服务器IP>:3847/docs"
    echo ""
    echo "  配置文件:"
    echo "    $CONFIG_FILE"
    echo ""
    echo "  重要目录:"
    echo "    安装目录: $INSTALL_DIR"
    echo "    数据目录: $DATA_DIR"
    echo "    日志目录: $LOG_DIR"
    echo "    备份目录: $BACKUP_DIR"
    echo ""
    echo "  服务管理:"
    echo "    启动: systemctl start $SERVICE_NAME"
    echo "    停止: systemctl stop $SERVICE_NAME"
    echo "    重启: systemctl restart $SERVICE_NAME"
    echo "    状态: systemctl status $SERVICE_NAME"
    echo ""
    echo "  激活 License:"
    echo "    请运行: $INSTALL_DIR/scripts/activate.sh"
    echo "    或在 Web 界面中输入激活码"
    echo ""
    echo "  数据备份:"
    echo "    立即备份: $INSTALL_DIR/scripts/backup.sh"
    echo "    定时备份: 请配置 cron 任务"
    echo ""
    echo "============================================================"
    echo -e "${YELLOW}  重要提示：${NC}"
    echo "  1. 请妥善保管配置文件中的密钥和密码"
    echo "  2. 建议首次登录后修改管理员密码"
    echo "  3. 请定期备份数据"
    echo "  4. 请及时激活 License 以使用全部功能"
    echo "============================================================"
    echo ""
}

# ============================================================
# 主流程
# ============================================================

main() {
    echo ""
    echo "============================================================"
    echo "  LexPrime 私有化部署 - 一键安装"
    echo "  版本: $VERSION"
    echo "============================================================"
    echo ""
    
    # 检查权限
    check_root
    
    # 系统检查
    check_os
    check_hardware
    check_docker
    
    # 安装流程
    create_directories
    generate_config
    deploy_services
    setup_systemd
    setup_firewall
    
    # 等待服务
    wait_for_services
    
    # 完成
    print_summary
    
    log_success "安装完成！"
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --dir=*)
            INSTALL_DIR="${1#*=}"
            shift
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --dir=PATH    指定安装目录 (默认: /opt/lexprime)"
            echo "  --help, -h    显示帮助信息"
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
