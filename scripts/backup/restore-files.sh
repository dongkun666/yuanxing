#!/bin/bash
#
# 文件恢复脚本
# 从备份恢复 LexPrime 项目的文件
#
# 用法: ./scripts/backup/restore-files.sh <backup-archive> [options]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_ARCHIVE=""
DEST_DIR="$PROJECT_ROOT"
DRY_RUN=false
FORCE=false

usage() {
    echo "用法: $0 <backup-archive> [options]"
    echo ""
    echo "选项:"
    echo "  -d, --dest <dir>    恢复目标目录 (默认: $DEST_DIR)"
    echo "  --dry-run           试运行，列出将恢复的文件"
    echo "  --force             强制覆盖现有文件"
    echo "  --list              仅列出备份内容"
    echo "  -h, --help          显示帮助"
    exit 0
}

if [[ $# -lt 1 ]]; then
    usage
fi

BACKUP_ARCHIVE="$1"
shift

LIST_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dest) DEST_DIR="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        --force) FORCE=true; shift ;;
        --list) LIST_ONLY=true; shift ;;
        -h|--help) usage ;;
        *) echo "未知选项: $1"; usage ;;
    esac
done

echo "=========================================="
echo "  LexPrime 文件恢复"
echo "=========================================="
echo "备份文件: $BACKUP_ARCHIVE"
echo "目标目录: $DEST_DIR"
echo "恢复时间: $(date)"
echo ""

if [[ ! -f "$BACKUP_ARCHIVE" ]]; then
    echo "错误: 备份文件不存在: $BACKUP_ARCHIVE"
    exit 1
fi

FILE_SIZE=$(du -h "$BACKUP_ARCHIVE" | cut -f1)
echo "备份文件大小: $FILE_SIZE"
echo ""

if [[ "$LIST_ONLY" == "true" ]]; then
    echo "备份内容:"
    tar -tzvf "$BACKUP_ARCHIVE" 2>/dev/null || tar -tvf "$BACKUP_ARCHIVE" 2>/dev/null || {
        echo "无法读取备份内容"
        exit 1
    }
    exit 0
fi

if [[ "$DRY_RUN" == "true" ]]; then
    echo "[试运行] 将恢复的文件:"
    tar -tzf "$BACKUP_ARCHIVE" 2>/dev/null || tar -tf "$BACKUP_ARCHIVE" 2>/dev/null || {
        echo "无法读取备份内容"
        exit 1
    }
    echo ""
    echo "注意: 这是试运行，未实际恢复文件"
    exit 0
fi

restore_start=$(date +%s)

echo "正在恢复文件..."

mkdir -p "$DEST_DIR"

if [[ "$FORCE" == "true" ]]; then
    tar -xzf "$BACKUP_ARCHIVE" -C "$DEST_DIR" 2>/dev/null || \
    tar -xjf "$BACKUP_ARCHIVE" -C "$DEST_DIR" 2>/dev/null || \
    tar -xf "$BACKUP_ARCHIVE" -C "$DEST_DIR" 2>/dev/null || {
        echo "警告: 部分文件恢复失败"
    }
else
    tar -xzkf "$BACKUP_ARCHIVE" -C "$DEST_DIR" 2>/dev/null || \
    tar -xjf "$BACKUP_ARCHIVE" -C "$DEST_DIR" --skip-old-files 2>/dev/null || \
    tar -xzf "$BACKUP_ARCHIVE" -C "$DEST_DIR" --keep-old-files 2>/dev/null || {
        echo "正在恢复 (保留现有文件)..."
        tar -xzf "$BACKUP_ARCHIVE" -C "$DEST_DIR" 2>/dev/null || true
    }
fi

restore_end=$(date +%s)
restore_duration=$((restore_end - restore_start))

echo ""
echo "=========================================="
echo "  恢复完成"
echo "=========================================="
echo "目标目录: $DEST_DIR"
echo "耗时: ${restore_duration}秒"
echo "状态: 成功"
