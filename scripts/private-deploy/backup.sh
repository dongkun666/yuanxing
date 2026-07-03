#!/bin/bash
# ============================================================
# LexPrime 私有化部署 - 备份脚本
# 版本: 1.0.0
# 日期: 2026-07-03
# 描述: 备份 LexPrime 数据和配置
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

BACKUP_DB=true
BACKUP_FILES=true
BACKUP_CONFIG=true
BACKUP_COMPRESS=true
BACKUP_RETENTION_DAYS=30

# ============================================================
# 工具函数
# ============================================================

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

load_config() {
    if [[ -f $CONFIG_FILE ]]; then
        source $CONFIG_FILE
    fi
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要 root 权限运行"
        exit 1
    fi
}

# ============================================================
# 备份流程
# ============================================================

create_backup_dir() {
    mkdir -p $BACKUP_DIR
    log_info "备份目录: $BACKUP_DIR"
}

backup_database() {
    if [[ "$BACKUP_DB" != "true" ]]; then
        log_info "跳过数据库备份"
        return 0
    fi
    
    log_info "备份数据库..."
    
    BACKUP_FILE="$BACKUP_DIR/db-$(date +%Y%m%d-%H%M%S).sql"
    
    if [[ -f $INSTALL_DIR/docker-compose.yml ]]; then
        cd $INSTALL_DIR
        
        if docker compose version &> /dev/null; then
            # 使用 Docker Compose V2
            docker compose exec -T postgres pg_dump -U lexprime lexprime > "$BACKUP_FILE" 2>/dev/null
        elif command -v docker-compose &> /dev/null; then
            # 使用 Docker Compose V1
            docker-compose exec -T postgres pg_dump -U lexprime lexprime > "$BACKUP_FILE" 2>/dev/null
        fi
        
        if [[ -f "$BACKUP_FILE" ]]; then
            if [[ "$BACKUP_COMPRESS" == "true" ]]; then
                gzip "$BACKUP_FILE"
                BACKUP_FILE="${BACKUP_FILE}.gz"
            fi
            
            FILE_SIZE=$(du -h "$BACKUP_FILE" | awk '{print $1}')
            log_success "数据库备份完成: $BACKUP_FILE ($FILE_SIZE)"
        else
            log_error "数据库备份失败"
            return 1
        fi
    else
        log_warning "未找到 Docker Compose 配置，跳过数据库备份"
    fi
}

backup_files() {
    if [[ "$BACKUP_FILES" != "true" ]]; then
        log_info "跳过文件备份"
        return 0
    fi
    
    log_info "备份数据文件..."
    
    BACKUP_FILE="$BACKUP_DIR/data-$(date +%Y%m%d-%H%M%S).tar"
    
    if [[ -d $DATA_DIR ]]; then
        if [[ "$BACKUP_COMPRESS" == "true" ]]; then
            BACKUP_FILE="${BACKUP_FILE}.gz"
            tar -czf "$BACKUP_FILE" -C $(dirname $DATA_DIR) $(basename $DATA_DIR) 2>/dev/null || true
        else
            tar -cf "$BACKUP_FILE" -C $(dirname $DATA_DIR) $(basename $DATA_DIR) 2>/dev/null || true
        fi
        
        if [[ -f "$BACKUP_FILE" ]]; then
            FILE_SIZE=$(du -h "$BACKUP_FILE" | awk '{print $1}')
            log_success "数据文件备份完成: $BACKUP_FILE ($FILE_SIZE)"
        else
            log_error "数据文件备份失败"
            return 1
        fi
    else
        log_warning "数据目录不存在，跳过文件备份"
    fi
}

backup_config() {
    if [[ "$BACKUP_CONFIG" != "true" ]]; then
        log_info "跳过配置备份"
        return 0
    fi
    
    log_info "备份配置文件..."
    
    BACKUP_FILE="$BACKUP_DIR/config-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    if [[ -f $CONFIG_FILE ]]; then
        tar -czf "$BACKUP_FILE" \
            -C $(dirname $CONFIG_FILE) $(basename $CONFIG_FILE) \
            -C $(dirname $INSTALL_DIR) $(basename $INSTALL_DIR)/VERSION 2>/dev/null || true
        
        if [[ -f "$BACKUP_FILE" ]]; then
            FILE_SIZE=$(du -h "$BACKUP_FILE" | awk '{print $1}')
            log_success "配置文件备份完成: $BACKUP_FILE ($FILE_SIZE)"
        else
            log_warning "配置文件备份完成（部分文件可能缺失）"
        fi
    else
        log_warning "配置文件不存在，跳过配置备份"
    fi
}

backup_full() {
    log_info "创建完整备份..."
    
    BACKUP_FILE="$BACKUP_DIR/full-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    TMP_DIR=$(mktemp -d)
    
    # 数据库备份
    if [[ "$BACKUP_DB" == "true" ]]; then
        if [[ -f $INSTALL_DIR/docker-compose.yml ]]; then
            cd $INSTALL_DIR
            if docker compose version &> /dev/null; then
                docker compose exec -T postgres pg_dump -U lexprime lexprime > "$TMP_DIR/database.sql" 2>/dev/null || true
            elif command -v docker-compose &> /dev/null; then
                docker-compose exec -T postgres pg_dump -U lexprime lexprime > "$TMP_DIR/database.sql" 2>/dev/null || true
            fi
        fi
    fi
    
    # 配置文件
    if [[ -f $CONFIG_FILE ]]; then
        cp $CONFIG_FILE "$TMP_DIR/config.env"
    fi
    
    # 版本信息
    if [[ -f $INSTALL_DIR/VERSION ]]; then
        cp $INSTALL_DIR/VERSION "$TMP_DIR/"
    fi
    
    # 元数据
    cat > "$TMP_DIR/backup-info.json" << EOF
{
  "backup_time": "$(date -Iseconds)",
  "backup_type": "full",
  "version": "$(cat $INSTALL_DIR/VERSION 2>/dev/null || echo 'unknown')",
  "hostname": "$(hostname)"
}
EOF
    
    # 打包数据目录
    if [[ -d $DATA_DIR ]]; then
        tar -czf "$BACKUP_FILE" \
            -C "$TMP_DIR" . \
            -C $(dirname $DATA_DIR) $(basename $DATA_DIR) 2>/dev/null || true
    else
        tar -czf "$BACKUP_FILE" -C "$TMP_DIR" . 2>/dev/null || true
    fi
    
    rm -rf "$TMP_DIR"
    
    if [[ -f "$BACKUP_FILE" ]]; then
        FILE_SIZE=$(du -h "$BACKUP_FILE" | awk '{print $1}')
        log_success "完整备份完成: $BACKUP_FILE ($FILE_SIZE)"
    else
        log_error "完整备份失败"
        return 1
    fi
}

cleanup_old_backups() {
    if [[ $BACKUP_RETENTION_DAYS -gt 0 ]]; then
        log_info "清理 $BACKUP_RETENTION_DAYS 天前的备份..."
        
        DELETED_COUNT=$(find $BACKUP_DIR -type f -mtime +$BACKUP_RETENTION_DAYS -name "*.gz" -o -name "*.sql" -o -name "*.tar" 2>/dev/null | wc -l)
        
        find $BACKUP_DIR -type f -mtime +$BACKUP_RETENTION_DAYS \
            \( -name "*.gz" -o -name "*.sql" -o -name "*.tar" \) \
            -delete 2>/dev/null || true
        
        log_success "已清理 $DELETED_COUNT 个旧备份文件"
    fi
}

list_backups() {
    echo ""
    echo "============================================================"
    echo "  备份列表"
    echo "============================================================"
    echo ""
    
    if [[ -d $BACKUP_DIR ]]; then
        ls -lh $BACKUP_DIR/ 2>/dev/null | head -20 || echo "  暂无备份文件"
    else
        echo "  备份目录不存在"
    fi
    
    echo ""
    echo "============================================================"
}

# ============================================================
# 主流程
# ============================================================

main() {
    echo ""
    echo "============================================================"
    echo "  LexPrime 私有化部署 - 数据备份"
    echo "============================================================"
    echo ""
    
    check_root
    load_config
    create_backup_dir
    
    START_TIME=$(date +%s)
    
    # 执行备份
    backup_full
    cleanup_old_backups
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo ""
    echo "============================================================"
    echo -e "${GREEN}  备份完成！${NC}"
    echo "============================================================"
    echo ""
    echo "  耗时: ${DURATION}秒"
    echo "  备份目录: $BACKUP_DIR"
    echo ""
    echo "  最近备份文件:"
    ls -t $BACKUP_DIR/*.gz 2>/dev/null | head -5 | while read f; do
        echo "    - $(basename $f) ($(du -h $f | awk '{print $1}'))"
    done
    echo ""
    echo "============================================================"
}

# 解析参数
BACKUP_TYPE="full"

while [[ $# -gt 0 ]]; do
    case $1 in
        --type=*)
            BACKUP_TYPE="${1#*=}"
            shift
            ;;
        --db-only)
            BACKUP_TYPE="db"
            shift
            ;;
        --files-only)
            BACKUP_TYPE="files"
            shift
            ;;
        --config-only)
            BACKUP_TYPE="config"
            shift
            ;;
        --no-compress)
            BACKUP_COMPRESS=false
            shift
            ;;
        --retention=*)
            BACKUP_RETENTION_DAYS="${1#*=}"
            shift
            ;;
        --list)
            list_backups
            exit 0
            ;;
        --dir=*)
            BACKUP_DIR="${1#*=}"
            shift
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --type=TYPE     备份类型: full/db/files/config (默认: full)"
            echo "  --db-only       仅备份数据库"
            echo "  --files-only    仅备份数据文件"
            echo "  --config-only   仅备份配置文件"
            echo "  --no-compress   不压缩备份"
            echo "  --retention=N   保留 N 天的备份 (默认: 30)"
            echo "  --list          列出备份文件"
            echo "  --dir=PATH      备份目录 (默认: /var/lexprime/backup)"
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

# 根据类型调整
case $BACKUP_TYPE in
    db)
        BACKUP_DB=true
        BACKUP_FILES=false
        BACKUP_CONFIG=false
        ;;
    files)
        BACKUP_DB=false
        BACKUP_FILES=true
        BACKUP_CONFIG=false
        ;;
    config)
        BACKUP_DB=false
        BACKUP_FILES=false
        BACKUP_CONFIG=true
        ;;
    full)
        BACKUP_DB=true
        BACKUP_FILES=true
        BACKUP_CONFIG=true
        ;;
    *)
        log_error "未知备份类型: $BACKUP_TYPE"
        exit 1
        ;;
esac

main
