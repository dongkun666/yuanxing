#!/bin/bash
# ============================================================
# LexPrime 私有化部署 - 恢复脚本
# 版本: 1.0.0
# 日期: 2026-07-03
# 描述: 从备份恢复 LexPrime 数据
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

BACKUP_FILE=""
RESTORE_DB=true
RESTORE_FILES=true
RESTORE_CONFIG=false

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

# ============================================================
# 恢复流程
# ============================================================

validate_backup() {
    log_info "验证备份文件..."
    
    if [[ -z $BACKUP_FILE ]]; then
        log_error "请指定备份文件"
        exit 1
    fi
    
    if [[ ! -f $BACKUP_FILE ]]; then
        log_error "备份文件不存在: $BACKUP_FILE"
        exit 1
    fi
    
    FILE_SIZE=$(du -h "$BACKUP_FILE" | awk '{print $1}')
    log_info "备份文件: $BACKUP_FILE ($FILE_SIZE)"
    
    # 检查文件类型
    FILE_TYPE=$(file -b "$BACKUP_FILE")
    log_info "文件类型: $FILE_TYPE"
    
    log_success "备份文件验证通过"
}

stop_services() {
    log_info "停止服务..."
    
    if systemctl is-active --quiet lexprime 2>/dev/null; then
        systemctl stop lexprime
        log_info "系统服务已停止"
    fi
    
    if [[ -f $INSTALL_DIR/docker-compose.yml ]]; then
        cd $INSTALL_DIR
        if docker compose version &> /dev/null; then
            docker compose stop 2>/dev/null || true
        elif command -v docker-compose &> /dev/null; then
            docker-compose stop 2>/dev/null || true
        fi
        log_info "Docker 容器已停止"
    fi
}

restore_database() {
    if [[ "$RESTORE_DB" != "true" ]]; then
        log_info "跳过数据库恢复"
        return 0
    fi
    
    log_info "恢复数据库..."
    
    DB_SQL=""
    
    # 查找 SQL 文件
    if [[ $BACKUP_FILE == *.sql ]] || [[ $BACKUP_FILE == *.sql.gz ]]; then
        DB_SQL="$BACKUP_FILE"
    elif [[ $BACKUP_FILE == *.tar.gz ]] || [[ $BACKUP_FILE == *.tgz ]]; then
        # 从 tar 包中提取数据库文件
        TMP_DIR=$(mktemp -d)
        tar -xzf "$BACKUP_FILE" -C "$TMP_DIR" 2>/dev/null || true
        
        if [[ -f "$TMP_DIR/database.sql" ]]; then
            DB_SQL="$TMP_DIR/database.sql"
        elif [[ -f "$TMP_DIR/database.sql.gz" ]]; then
            gunzip "$TMP_DIR/database.sql.gz"
            DB_SQL="$TMP_DIR/database.sql"
        fi
    fi
    
    if [[ -z $DB_SQL ]]; then
        log_warning "未找到数据库备份，跳过数据库恢复"
        return 0
    fi
    
    # 解压 gz
    if [[ $DB_SQL == *.gz ]]; then
        gunzip -k "$DB_SQL" 2>/dev/null || true
        DB_SQL="${DB_SQL%.gz}"
    fi
    
    # 恢复数据库
    if [[ -f $INSTALL_DIR/docker-compose.yml ]]; then
        cd $INSTALL_DIR
        
        # 启动数据库
        if docker compose version &> /dev/null; then
            docker compose start postgres 2>/dev/null || true
            sleep 5
            
            # 等待数据库就绪
            for i in {1..30}; do
                if docker compose exec -T postgres pg_isready -U lexprime 2>/dev/null | grep -q "accepting connections"; then
                    break
                fi
                sleep 2
            done
            
            # 恢复数据库
            docker compose exec -T postgres psql -U lexprime -d lexprime < "$DB_SQL" 2>/dev/null || true
        elif command -v docker-compose &> /dev/null; then
            docker-compose start postgres 2>/dev/null || true
            sleep 5
            docker-compose exec -T postgres psql -U lexprime -d lexprime < "$DB_SQL" 2>/dev/null || true
        fi
        
        log_success "数据库恢复完成"
    else
        log_warning "未找到 Docker Compose 配置，跳过数据库恢复"
    fi
    
    # 清理临时文件
    if [[ -n $TMP_DIR ]] && [[ -d $TMP_DIR ]]; then
        rm -rf "$TMP_DIR"
    fi
}

restore_files() {
    if [[ "$RESTORE_FILES" != "true" ]]; then
        log_info "跳过数据文件恢复"
        return 0
    fi
    
    log_info "恢复数据文件..."
    
    # 备份当前数据
    if [[ -d $DATA_DIR ]]; then
        BACKUP_OLD="$DATA_DIR.bak.$(date +%Y%m%d%H%M%S)"
        mv $DATA_DIR "$BACKUP_OLD"
        log_info "当前数据已备份到: $BACKUP_OLD"
    fi
    
    mkdir -p $DATA_DIR
    
    # 判断备份类型
    if [[ $BACKUP_FILE == *.tar.gz ]] || [[ $BACKUP_FILE == *.tgz ]]; then
        # 从完整备份中提取数据目录
        TMP_DIR=$(mktemp -d)
        tar -xzf "$BACKUP_FILE" -C "$TMP_DIR" 2>/dev/null || true
        
        if [[ -d "$TMP_DIR/$(basename $DATA_DIR)" ]]; then
            cp -r "$TMP_DIR/$(basename $DATA_DIR)"/* $DATA_DIR/
            log_success "数据文件恢复完成"
        else
            log_warning "备份中未找到数据目录"
        fi
        
        rm -rf "$TMP_DIR"
    elif [[ $BACKUP_FILE == *.tar ]]; then
        TMP_DIR=$(mktemp -d)
        tar -xf "$BACKUP_FILE" -C "$TMP_DIR" 2>/dev/null || true
        
        if [[ -d "$TMP_DIR/$(basename $DATA_DIR)" ]]; then
            cp -r "$TMP_DIR/$(basename $DATA_DIR)"/* $DATA_DIR/
            log_success "数据文件恢复完成"
        fi
        
        rm -rf "$TMP_DIR"
    else
        log_warning "不支持的备份格式，跳过数据文件恢复"
    fi
}

restore_config() {
    if [[ "$RESTORE_CONFIG" != "true" ]]; then
        log_info "跳过配置文件恢复"
        return 0
    fi
    
    log_info "恢复配置文件..."
    
    if [[ $BACKUP_FILE == *.tar.gz ]] || [[ $BACKUP_FILE == *.tgz ]]; then
        TMP_DIR=$(mktemp -d)
        tar -xzf "$BACKUP_FILE" -C "$TMP_DIR" 2>/dev/null || true
        
        if [[ -f "$TMP_DIR/config.env" ]]; then
            cp "$TMP_DIR/config.env" $CONFIG_FILE
            chmod 600 $CONFIG_FILE
            log_success "配置文件恢复完成"
        else
            log_warning "备份中未找到配置文件"
        fi
        
        rm -rf "$TMP_DIR"
    else
        log_warning "配置文件仅支持从完整备份恢复"
    fi
}

start_services() {
    log_info "启动服务..."
    
    if [[ -f $INSTALL_DIR/docker-compose.yml ]]; then
        cd $INSTALL_DIR
        if docker compose version &> /dev/null; then
            docker compose up -d
        elif command -v docker-compose &> /dev/null; then
            docker-compose up -d
        fi
        log_info "Docker 服务已启动"
    fi
    
    if systemctl list-unit-files | grep -q lexprime; then
        systemctl start lexprime 2>/dev/null || true
        log_info "系统服务已启动"
    fi
}

verify_restore() {
    log_info "验证恢复结果..."
    
    sleep 10
    
    # 检查服务状态
    if command -v curl &> /dev/null; then
        if curl -s --connect-timeout 10 "http://localhost:3847/api/health" &> /dev/null; then
            log_success "API 服务正常"
        else
            log_warning "API 服务健康检查未通过，请稍后手动检查"
        fi
    fi
    
    log_success "恢复验证完成"
}

# ============================================================
# 主流程
# ============================================================

main() {
    echo ""
    echo "============================================================"
    echo "  LexPrime 私有化部署 - 数据恢复"
    echo "============================================================"
    echo ""
    
    check_root
    load_config
    validate_backup
    
    # 警告
    echo ""
    log_warning "此操作将覆盖现有数据！"
    echo ""
    echo "  将恢复以下内容:"
    [[ "$RESTORE_DB" == "true" ]] && echo "    - 数据库"
    [[ "$RESTORE_FILES" == "true" ]] && echo "    - 数据文件"
    [[ "$RESTORE_CONFIG" == "true" ]] && echo "    - 配置文件"
    echo ""
    echo "  备份文件: $BACKUP_FILE"
    echo ""
    
    read -p "确认恢复? (输入 RESTORE 确认): " confirm
    if [[ $confirm != "RESTORE" ]]; then
        log_info "已取消恢复"
        exit 0
    fi
    
    echo ""
    START_TIME=$(date +%s)
    
    stop_services
    restore_database
    restore_files
    restore_config
    start_services
    verify_restore
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo ""
    echo "============================================================"
    echo -e "${GREEN}  恢复完成！${NC}"
    echo "============================================================"
    echo ""
    echo "  耗时: ${DURATION}秒"
    echo ""
    echo "  建议:"
    echo "    1. 检查数据完整性"
    echo "    2. 确认服务正常运行"
    echo "    3. 如有问题可回滚到旧数据备份"
    echo ""
    echo "============================================================"
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --file=*)
            BACKUP_FILE="${1#*=}"
            shift
            ;;
        --db-only)
            RESTORE_DB=true
            RESTORE_FILES=false
            RESTORE_CONFIG=false
            shift
            ;;
        --files-only)
            RESTORE_DB=false
            RESTORE_FILES=true
            RESTORE_CONFIG=false
            shift
            ;;
        --config)
            RESTORE_CONFIG=true
            shift
            ;;
        --list)
            echo ""
            echo "可用的备份文件:"
            ls -lh $BACKUP_DIR/ 2>/dev/null || echo "  暂无备份文件"
            echo ""
            exit 0
            ;;
        --dir=*)
            BACKUP_DIR="${1#*=}"
            shift
            ;;
        --help|-h)
            echo "用法: $0 --file=BACKUP_FILE [选项]"
            echo ""
            echo "选项:"
            echo "  --file=FILE     指定备份文件路径"
            echo "  --db-only       仅恢复数据库"
            echo "  --files-only    仅恢复数据文件"
            echo "  --config        恢复配置文件 (谨慎使用)"
            echo "  --list          列出可用备份文件"
            echo "  --dir=PATH      备份目录 (默认: /var/lexprime/backup)"
            echo "  --help, -h      显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0 --file=/var/lexprime/backup/full-20260703-120000.tar.gz"
            echo "  $0 --db-only --file=/var/lexprime/backup/db-20260703-120000.sql.gz"
            echo ""
            exit 0
            ;;
        *)
            log_error "未知选项: $1"
            exit 1
            ;;
    esac
done

if [[ -z $BACKUP_FILE ]]; then
    log_error "请使用 --file 参数指定备份文件"
    echo ""
    echo "可用的备份文件:"
    ls -lh $BACKUP_DIR/ 2>/dev/null || echo "  暂无备份文件"
    exit 1
fi

main
