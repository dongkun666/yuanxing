#!/bin/bash
#
# 文件备份脚本
# 备份 LexPrime 项目的重要文件（上传文件、配置、日志等）
#
# 用法: ./scripts/backup/backup-files.sh [options]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups/files}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RETENTION_DAYS="${RETENTION_DAYS:-30}"
COMPRESSION="${COMPRESSION:-gzip}"

INCLUDE_PATHS=(
    "backend/cases-crawler/data"
    "backend/cases-crawler/.env"
    ".uploads"
    "templates"
)

EXCLUDE_PATTERNS=(
    "*.pyc"
    "__pycache__"
    "node_modules"
    ".git"
    "*.log"
)

usage() {
    echo "用法: $0 [options]"
    echo ""
    echo "选项:"
    echo "  -d, --dir <dir>       备份目录 (默认: $BACKUP_DIR)"
    echo "  -c, --compression <t> 压缩方式: gzip|bzip2|none (默认: $COMPRESSION)"
    echo "  --retention <days>    保留天数 (默认: $RETENTION_DAYS)"
    echo "  --include <path>      额外包含的路径（可多次指定）"
    echo "  -h, --help            显示帮助"
    exit 0
}

EXTRA_INCLUDES=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dir) BACKUP_DIR="$2"; shift 2 ;;
        -c|--compression) COMPRESSION="$2"; shift 2 ;;
        --retention) RETENTION_DAYS="$2"; shift 2 ;;
        --include) EXTRA_INCLUDES+=("$2"); shift 2 ;;
        -h|--help) usage ;;
        *) echo "未知选项: $1"; usage ;;
    esac
done

BACKUP_NAME="lexprime_files_${TIMESTAMP}"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
MANIFEST_FILE="$BACKUP_DIR/${BACKUP_NAME}_manifest.json"

echo "=========================================="
echo "  LexPrime 文件备份"
echo "=========================================="
echo "备份目录: $BACKUP_DIR"
echo "压缩方式: $COMPRESSION"
echo "备份时间: $(date)"
echo ""

mkdir -p "$BACKUP_DIR"

backup_start=$(date +%s)

echo "正在收集文件..."

TAR_ARGS=()
TAR_ARGS+=("--create")

case "$COMPRESSION" in
    gzip) TAR_ARGS+=("--gzip") ;;
    bzip2) TAR_ARGS+=("--bzip2") ;;
    none) ;;
    *) echo "警告: 未知压缩方式 $COMPRESSION，使用 gzip"; TAR_ARGS+=("--gzip") ;;
esac

TAR_ARGS+=("--file" "${BACKUP_PATH}.tar${COMPRESSION:+.$([ "$COMPRESSION" = "gzip" ] && echo gz || [ "$COMPRESSION" = "bzip2" ] && echo bz2)}")

for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    TAR_ARGS+=("--exclude=$pattern")
done

TAR_ARGS+=("-C" "$PROJECT_ROOT")

FILES_TO_BACKUP=()
for rel_path in "${INCLUDE_PATHS[@]}"; do
    full_path="$PROJECT_ROOT/$rel_path"
    if [[ -e "$full_path" ]]; then
        FILES_TO_BACKUP+=("$rel_path")
    else
        echo "  跳过 (不存在): $rel_path"
    fi
done

for inc_path in "${EXTRA_INCLUDES[@]}"; do
    FILES_TO_BACKUP+=("$inc_path")
done

if [[ ${#FILES_TO_BACKUP[@]} -eq 0 ]]; then
    echo "错误: 没有可备份的文件"
    exit 1
fi

echo "  备份 ${#FILES_TO_BACKUP[@]} 个路径..."

TAR_ARGS+=("${FILES_TO_BACKUP[@]}")

tar "${TAR_ARGS[@]}" 2>/dev/null || {
    echo "警告: tar 命令部分失败，继续..."
}

backup_end=$(date +%s)
backup_duration=$((backup_end - backup_start))

ARCHIVE_FILE="${BACKUP_PATH}.tar${COMPRESSION:+.$([ "$COMPRESSION" = "gzip" ] && echo gz || [ "$COMPRESSION" = "bzip2" ] && echo bz2)}"

if [[ -f "$ARCHIVE_FILE" ]]; then
    FILE_SIZE=$(du -h "$ARCHIVE_FILE" | cut -f1)

    echo ""
    echo "备份成功!"
    echo "  备份文件: $ARCHIVE_FILE"
    echo "  文件大小: $FILE_SIZE"
    echo "  耗时: ${backup_duration}秒"

    cat > "$MANIFEST_FILE" <<EOF
{
    "backup_id": "files_${TIMESTAMP}",
    "type": "files",
    "timestamp": "$(date -Iseconds)",
    "archive_file": "$(basename "$ARCHIVE_FILE")",
    "size_bytes": $(stat -c%s "$ARCHIVE_FILE" 2>/dev/null || echo 0),
    "duration_seconds": $backup_duration,
    "compression": "$COMPRESSION",
    "retention_days": $RETENTION_DAYS,
    "file_count": ${#FILES_TO_BACKUP[@]},
    "included_paths": $(printf '%s\n' "${FILES_TO_BACKUP[@]}" | jq -R . | jq -s . 2>/dev/null || echo "[]"),
    "status": "completed"
}
EOF

    echo "  清单文件: $MANIFEST_FILE"

    echo ""
    echo "清理过期备份 (保留 $RETENTION_DAYS 天)..."
    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    find "$BACKUP_DIR" -name "*.tar.bz2" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    find "$BACKUP_DIR" -name "*_manifest.json" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    echo "清理完成"

    exit 0
else
    echo "错误: 备份失败"
    exit 1
fi
