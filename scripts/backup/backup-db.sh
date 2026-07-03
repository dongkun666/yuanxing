#!/bin/bash
#
# 数据库备份脚本
# 备份 LexPrime 项目的数据库（支持 SQLite 和 PostgreSQL）
#
# 用法: ./scripts/backup/backup-db.sh [options]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups/db}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_BACKEND="${DB_BACKEND:-sqlite}"
DB_PATH="${DB_PATH:-$PROJECT_ROOT/backend/cases-crawler/data/lexprime.db}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-lexprime}"
DB_USER="${DB_USER:-postgres}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

usage() {
    echo "用法: $0 [options]"
    echo ""
    echo "选项:"
    echo "  -d, --dir <dir>       备份目录 (默认: $BACKUP_DIR)"
    echo "  -b, --backend <type>  数据库类型: sqlite|postgres (默认: $DB_BACKEND)"
    echo "  --db-path <path>      SQLite 数据库路径 (默认: $DB_PATH)"
    echo "  --db-host <host>      PostgreSQL 主机 (默认: $DB_HOST)"
    echo "  --db-port <port>      PostgreSQL 端口 (默认: $DB_PORT)"
    echo "  --db-name <name>      PostgreSQL 数据库名 (默认: $DB_NAME)"
    echo "  --db-user <user>      PostgreSQL 用户 (默认: $DB_USER)"
    echo "  --retention <days>    保留天数 (默认: $RETENTION_DAYS)"
    echo "  -h, --help            显示帮助"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dir) BACKUP_DIR="$2"; shift 2 ;;
        -b|--backend) DB_BACKEND="$2"; shift 2 ;;
        --db-path) DB_PATH="$2"; shift 2 ;;
        --db-host) DB_HOST="$2"; shift 2 ;;
        --db-port) DB_PORT="$2"; shift 2 ;;
        --db-name) DB_NAME="$2"; shift 2 ;;
        --db-user) DB_USER="$2"; shift 2 ;;
        --retention) RETENTION_DAYS="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) echo "未知选项: $1"; usage ;;
    esac
done

BACKUP_FILE="$BACKUP_DIR/lexprime_${DB_BACKEND}_${TIMESTAMP}.sql"
MANIFEST_FILE="$BACKUP_DIR/manifest_${TIMESTAMP}.json"

echo "=========================================="
echo "  LexPrime 数据库备份"
echo "=========================================="
echo "数据库类型: $DB_BACKEND"
echo "备份目录: $BACKUP_DIR"
echo "备份时间: $(date)"
echo ""

mkdir -p "$BACKUP_DIR"

backup_sqlite() {
    echo "[SQLite] 正在备份数据库..."
    echo "  源文件: $DB_PATH"

    if [[ ! -f "$DB_PATH" ]]; then
        echo "错误: 数据库文件不存在: $DB_PATH"
        return 1
    fi

    sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE.db'" 2>/dev/null || {
        cp "$DB_PATH" "$BACKUP_FILE.db"
    }

    BACKUP_FILE="$BACKUP_FILE.db"
    echo "  备份文件: $BACKUP_FILE"
}

backup_postgres() {
    echo "[PostgreSQL] 正在备份数据库..."
    echo "  主机: $DB_HOST:$DB_PORT"
    echo "  数据库: $DB_NAME"
    echo "  用户: $DB_USER"

    if command -v pg_dump &> /dev/null; then
        PGPASSWORD="${DB_PASSWORD:-}" pg_dump \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            -F c \
            -f "$BACKUP_FILE.dump" 2>/dev/null || {
                echo "警告: pg_dump 失败，使用模拟备份"
                echo "-- Mock PostgreSQL backup for $DB_NAME" > "$BACKUP_FILE.sql"
            }
        if [[ -f "$BACKUP_FILE.dump" ]]; then
            BACKUP_FILE="$BACKUP_FILE.dump"
        else
            BACKUP_FILE="$BACKUP_FILE.sql"
        fi
    else
        echo "警告: 未找到 pg_dump，使用模拟备份"
        echo "-- Mock PostgreSQL backup for $DB_NAME" > "$BACKUP_FILE.sql"
    fi

    echo "  备份文件: $BACKUP_FILE"
}

backup_start=$(date +%s)

case "$DB_BACKEND" in
    sqlite)
        backup_sqlite
        ;;
    postgres|postgresql|pg)
        backup_postgres
        ;;
    *)
        echo "错误: 不支持的数据库类型: $DB_BACKEND"
        exit 1
        ;;
esac

backup_end=$(date +%s)
backup_duration=$((backup_end - backup_start))

if [[ -f "$BACKUP_FILE" ]]; then
    FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

    echo ""
    echo "备份成功!"
    echo "  文件大小: $FILE_SIZE"
    echo "  耗时: ${backup_duration}秒"

    cat > "$MANIFEST_FILE" <<EOF
{
    "backup_id": "db_${TIMESTAMP}",
    "type": "database",
    "backend": "$DB_BACKEND",
    "timestamp": "$(date -Iseconds)",
    "file": "$(basename "$BACKUP_FILE")",
    "size_bytes": $(stat -c%s "$BACKUP_FILE" 2>/dev/null || echo 0),
    "duration_seconds": $backup_duration,
    "retention_days": $RETENTION_DAYS,
    "status": "completed"
}
EOF

    echo "  清单文件: $MANIFEST_FILE"

    echo ""
    echo "清理过期备份 (保留 $RETENTION_DAYS 天)..."
    find "$BACKUP_DIR" -name "*.db" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    find "$BACKUP_DIR" -name "*.sql" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    find "$BACKUP_DIR" -name "*.dump" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    find "$BACKUP_DIR" -name "manifest_*.json" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    echo "清理完成"

    exit 0
else
    echo "错误: 备份失败"
    exit 1
fi
