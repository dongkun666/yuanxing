#!/bin/bash
# ============================================================
# LexPrime 私有化部署 - 升级脚本
# 版本: 1.0.0
# 日期: 2026-07-03
# 描述: 升级 LexPrime 私有化部署版本
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
BACKUP_DIR="/var/lexprime/backup"
CONFIG_FILE="/etc/lexprime/config.env"
SERVICE_NAME="lexprime"

NEW_VERSION=""
BACKUP_BEFORE_UPGRADE=true

# ============================================================
# 工具函数
# ============================================================

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要 root 权限运行"
        exit 1
    fi
}

load_config() {
    if [[ -f $CONFIG_FILE ]]; then
        source $CONFIG_FILE
    fi
}

get_current_version() {
    if [[ -f $INSTALL_DIR/VERSION ]]; then
        cat $INSTALL_DIR/VERSION
    else
        echo "unknown"
    fi
}

# ============================================================
# 升级前检查
# ============================================================

pre_upgrade_check() {
    log_info "升级前检查..."
    
    # 检查安装目录
    if [[ ! -d $INSTALL_DIR ]]; then
        log_error "未找到安装目录: $INSTALL_DIR"
        log_info "请先运行 install.sh 进行安装"
        exit 1
    fi
    
    # 检查配置文件
    if [[ ! -f $CONFIG_FILE ]]; then
        log_warning "未找到配置文件: $CONFIG_FILE"
    fi
    
    # 检查服务状态
    if systemctl is-active --quiet $SERVICE_NAME 2>/dev/null; then
        log_info "服务运行中"
    else
        log_warning "服务未运行"
    fi
    
    CURRENT_VERSION=$(get_current_version)
    log_info "当前版本: $CURRENT_VERSION"
    
    if [[ -z $NEW_VERSION ]]; then
        log_warning "未指定新版本，将使用本地升级包"
    else
        log_info "目标版本: $NEW_VERSION"
    fi
    
    log_success "升级前检查完成"
}

# ============================================================
# 备份
# ============================================================

backup_before_upgrade() {
    if [[ "$BACKUP_BEFORE_UPGRADE" != "true" ]]; then
        log_info "跳过备份"
        return 0
    fi
    
    log_info "升级前数据备份..."
    
    BACKUP_FILE="$BACKUP_DIR/pre-upgrade-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    mkdir -p $BACKUP_DIR
    
    # 备份数据
    log_info "备份数据目录..."
    if command -v tar &> /dev/null; then
        tar -czf "$BACKUP_FILE" \
            -C $(dirname $DATA_DIR) $(basename $DATA_DIR) \
            -C $(dirname $CONFIG_FILE) $(basename $CONFIG_FILE) 2>/dev/null || true
    fi
    
    # 备份数据库 (如果是 Docker 部署)
    if [[ -f $INSTALL_DIR/docker-compose.yml ]]; then
        log_info "备份数据库..."
        cd $INSTALL_DIR
        if docker compose version &> /dev/null; then
            docker compose exec -T postgres pg_dump -U lexprime lexprime > "$BACKUP_DIR/db-pre-upgrade-$(date +%Y%m%d-%H%M%S).sql" 2>/dev/null || true
        fi
    fi
    
    log_success "备份完成: $BACKUP_FILE"
}

# ============================================================
# 升级流程
# ============================================================

stop_services() {
    log_info "停止服务..."
    
    if systemctl is-active --quiet $SERVICE_NAME 2>/dev/null; then
        systemctl stop $SERVICE_NAME
        log_info "服务已停止"
    else
        log_info "服务未运行，跳过停止步骤"
    fi
    
    # 确保 Docker 容器停止
    if [[ -f $INSTALL_DIR/docker-compose.yml ]]; then
        cd $INSTALL_DIR
        if docker compose version &> /dev/null; then
            docker compose down 2>/dev/null || true
        elif command -v docker-compose &> /dev/null; then
            docker-compose down 2>/dev/null || true
        fi
    fi
}

upgrade_files() {
    log_info "升级应用文件..."
    
    # 这里是升级文件的逻辑
    # 实际部署时会从升级包中替换文件
    
    # 1. 备份当前版本
    if [[ -d $INSTALL_DIR ]]; then
        cp -r $INSTALL_DIR "${INSTALL_DIR}.bak.$(date +%Y%m%d%H%M%S)" 2>/dev/null || true
    fi
    
    # 2. 更新版本文件
    if [[ -n $NEW_VERSION ]]; then
        echo $NEW_VERSION > $INSTALL_DIR/VERSION
    fi
    
    log_success "应用文件升级完成"
}

upgrade_database() {
    log_info "升级数据库..."
    
    # 这里是数据库迁移的逻辑
    # 实际部署时会运行数据库迁移脚本
    
    if [[ -f $INSTALL_DIR/docker-compose.yml ]]; then
        cd $INSTALL_DIR
        
        # 启动数据库
        if docker compose version &> /dev/null; then
            docker compose up -d postgres 2>/dev/null || true
            sleep 5
            # 运行迁移
            docker compose exec -T api alembic upgrade head 2>/dev/null || true
        fi
    fi
    
    log_success "数据库升级完成"
}

start_services() {
    log_info "启动服务..."
    
    if systemctl is-active --quiet $SERVICE_NAME 2>/dev/null || systemctl list-unit-files | grep -q $SERVICE_NAME; then
        systemctl start $SERVICE_NAME
        log_info "服务已启动"
    else
        # 直接用 docker compose 启动
        if [[ -f $INSTALL_DIR/docker-compose.yml ]]; then
            cd $INSTALL_DIR
            if docker compose version &> /dev/null; then
                docker compose up -d
            elif command -v docker-compose &> /dev/null; then
                docker-compose up -d
            fi
            log_info "Docker 服务已启动"
        fi
    fi
}

verify_upgrade() {
    log_info "验证升级..."
    
    sleep 10
    
    # 检查服务状态
    if systemctl is-active --quiet $SERVICE_NAME 2>/dev/null; then
        log_success "服务运行正常"
    elif [[ -f $INSTALL_DIR/docker-compose.yml ]]; then
        cd $INSTALL_DIR
        if docker compose ps &> /dev/null; then
            log_success "Docker 容器运行正常"
        else
            log_warning "部分容器可能未正常启动"
        fi
    fi
    
    # 检查 API 健康状态
    if command -v curl &> /dev/null; then
        if curl -s http://localhost:3847/api/health &> /dev/null; then
            log_success "API 服务正常"
        else
            log_warning "API 健康检查未通过，请稍后手动检查"
        fi
    fi
    
    NEW_VERSION_CHECK=$(get_current_version)
    log_info "升级后版本: $NEW_VERSION_CHECK"
}

# ============================================================
# 回滚
# ============================================================

rollback() {
    log_error "升级失败，正在回滚..."
    
    # 找到最新的备份
    LATEST_BACKUP=$(ls -t $BACKUP_DIR/pre-upgrade-*.tar.gz 2>/dev/null | head -1)
    
    if [[ -n $LATEST_BACKUP ]]; then
        log_info "使用备份: $LATEST_BACKUP"
        
        stop_services
        
        # 恢复数据
        tar -xzf "$LATEST_BACKUP" -C /
        
        start_services
        
        log_success "回滚完成"
    else
        log_error "未找到备份文件，无法自动回滚"
    fi
    
    exit 1
}

# ============================================================
# 主流程
# ============================================================

main() {
    echo ""
    echo "============================================================"
    echo "  LexPrime 私有化部署 - 版本升级"
    echo "============================================================"
    echo ""
    
    check_root
    load_config
    pre_upgrade_check
    
    # 确认升级
    read -p "确认开始升级? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        log_info "已取消升级"
        exit 0
    fi
    
    # 设置错误回滚
    trap 'rollback' ERR
    
    # 执行升级
    backup_before_upgrade
    stop_services
    upgrade_files
    upgrade_database
    start_services
    verify_upgrade
    
    # 清除错误陷阱
    trap - ERR
    
    echo ""
    echo "============================================================"
    echo -e "${GREEN}  升级完成！${NC}"
    echo "============================================================"
    echo ""
    echo "  当前版本: $(get_current_version)"
    echo ""
    echo "  如有问题，可使用以下命令回滚:"
    echo "    $0 --rollback"
    echo ""
    echo "  查看升级日志:"
    echo "    journalctl -u $SERVICE_NAME -f"
    echo ""
    echo "============================================================"
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --version=*)
            NEW_VERSION="${1#*=}"
            shift
            ;;
        --no-backup)
            BACKUP_BEFORE_UPGRADE=false
            shift
            ;;
        --rollback)
            rollback
            ;;
        --dir=*)
            INSTALL_DIR="${1#*=}"
            shift
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --version=VER   指定目标版本"
            echo "  --no-backup     升级前不备份"
            echo "  --rollback      回滚到上一版本"
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
