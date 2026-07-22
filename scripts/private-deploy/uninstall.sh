#!/bin/bash
# ============================================================
# LexPrime 私有化部署 - 卸载脚本
# 版本: 1.0.0
# 日期: 2026-07-03
# 描述: 卸载 LexPrime 私有化部署
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
CONFIG_FILE="/etc/lexprime/config.env"
SERVICE_NAME="lexprime"

REMOVE_DATA=false
REMOVE_CONFIG=false
REMOVE_LOGS=false

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

# ============================================================
# 卸载流程
# ============================================================

stop_services() {
    log_info "停止服务..."
    
    # 停止 systemd 服务
    if systemctl list-unit-files | grep -q $SERVICE_NAME; then
        systemctl stop $SERVICE_NAME 2>/dev/null || true
        systemctl disable $SERVICE_NAME 2>/dev/null || true
        rm -f /etc/systemd/system/$SERVICE_NAME.service
        systemctl daemon-reload
        log_info "系统服务已移除"
    fi
    
    # 停止 Docker 容器
    if [[ -f $INSTALL_DIR/docker-compose.yml ]]; then
        cd $INSTALL_DIR
        if docker compose version &> /dev/null; then
            docker compose down -v 2>/dev/null || true
        elif command -v docker-compose &> /dev/null; then
            docker-compose down -v 2>/dev/null || true
        fi
        log_info "Docker 容器已停止并移除"
    fi
}

remove_app_files() {
    log_info "移除应用文件..."
    
    if [[ -d $INSTALL_DIR ]]; then
        rm -rf $INSTALL_DIR
        log_info "安装目录已删除: $INSTALL_DIR"
    fi
}

remove_config() {
    if [[ "$REMOVE_CONFIG" != "true" ]]; then
        log_info "保留配置文件"
        return 0
    fi
    
    log_info "移除配置文件..."
    
    if [[ -f $CONFIG_FILE ]]; then
        rm -f $CONFIG_FILE
        log_info "配置文件已删除: $CONFIG_FILE"
    fi
    
    if [[ -d /etc/lexprime ]]; then
        rm -rf /etc/lexprime
        log_info "配置目录已删除: /etc/lexprime"
    fi
}

remove_data() {
    if [[ "$REMOVE_DATA" != "true" ]]; then
        log_info "保留数据目录"
        return 0
    fi
    
    log_warning "将删除所有数据！此操作不可恢复！"
    
    if [[ -d $DATA_DIR ]]; then
        rm -rf $DATA_DIR
        log_info "数据目录已删除: $DATA_DIR"
    fi
}

remove_logs() {
    if [[ "$REMOVE_LOGS" != "true" ]]; then
        log_info "保留日志文件"
        return 0
    fi
    
    log_info "移除日志文件..."
    
    if [[ -d $LOG_DIR ]]; then
        rm -rf $LOG_DIR
        log_info "日志目录已删除: $LOG_DIR"
    fi
}

cleanup_docker() {
    log_info "清理 Docker 资源..."
    
    # 移除相关镜像 (可选)
    if command -v docker &> /dev/null; then
        # 只移除 LexPrime 相关的镜像
        docker images | grep lexprime | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true
        log_info "Docker 镜像已清理"
    fi
}

# ============================================================
# 主流程
# ============================================================

main() {
    echo ""
    echo "============================================================"
    echo "  LexPrime 私有化部署 - 卸载"
    echo "============================================================"
    echo ""
    
    check_root
    
    # 确认卸载
    log_warning "此操作将卸载 LexPrime 私有化部署！"
    echo ""
    echo "  将执行以下操作:"
    echo "    1. 停止并移除服务"
    echo "    2. 删除应用文件 ($INSTALL_DIR)"
    if [[ "$REMOVE_CONFIG" == "true" ]]; then
        echo "    3. 删除配置文件"
    else
        echo "    3. 保留配置文件"
    fi
    if [[ "$REMOVE_DATA" == "true" ]]; then
        echo "    4. [危险] 删除所有数据"
    else
        echo "    4. 保留数据"
    fi
    if [[ "$REMOVE_LOGS" == "true" ]]; then
        echo "    5. 删除日志文件"
    else
        echo "    5. 保留日志文件"
    fi
    echo ""
    
    read -p "确认卸载? (输入 UNINSTALL 确认): " confirm
    if [[ $confirm != "UNINSTALL" ]]; then
        log_info "已取消卸载"
        exit 0
    fi
    
    echo ""
    stop_services
    remove_app_files
    remove_config
    remove_data
    remove_logs
    cleanup_docker
    
    echo ""
    echo "============================================================"
    echo -e "${GREEN}  卸载完成！${NC}"
    echo "============================================================"
    echo ""
    
    if [[ "$REMOVE_DATA" != "true" ]]; then
        echo -e "${YELLOW}  数据目录已保留: $DATA_DIR ${NC}"
        echo "  如需完全清除，请手动删除"
        echo ""
    fi
    
    if [[ "$REMOVE_CONFIG" != "true" ]]; then
        echo -e "${YELLOW}  配置文件已保留: $CONFIG_FILE ${NC}"
        echo ""
    fi
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --remove-data)
            REMOVE_DATA=true
            shift
            ;;
        --remove-config)
            REMOVE_CONFIG=true
            shift
            ;;
        --remove-logs)
            REMOVE_LOGS=true
            shift
            ;;
        --remove-all)
            REMOVE_DATA=true
            REMOVE_CONFIG=true
            REMOVE_LOGS=true
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
            echo "  --remove-data    删除数据目录 (危险!)"
            echo "  --remove-config  删除配置文件"
            echo "  --remove-logs    删除日志文件"
            echo "  --remove-all     删除所有数据/配置/日志"
            echo "  --dir=PATH       指定安装目录 (默认: /opt/lexprime)"
            echo "  --help, -h       显示帮助信息"
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
