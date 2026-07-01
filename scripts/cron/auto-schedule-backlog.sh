#!/usr/bin/env bash
# W9 A2 自动调度 shell 包装 (cron 调用入口)
# (lex-coder · 2026-06-29)
#
# 用途:
#   - 每日 09:00 cron 跑一次 (增量调度, --since 24)
#   - 或者手动跑全量: ./auto-schedule-backlog.sh --week 9
#
# 设计原则:
#   - 默认 dry-run (不污染 owner 队列, 见 plan_841af3e9 a2-backlog-to-plan-tasks spec)
#   - 增量调度 (--since 24) 每天拉过去 24h 新增的 open P0/P1 ticket
#   - exit code 0 = 调度成功, 非 0 = 失败 (cron 触发器会发邮件)
#
# 集成:
#   mavis cron create lex-coder auto-schedule-backlog \
#     --schedule "0 9 * * *" \
#     --prompt "Run auto-schedule-backlog.sh"
#
# 调用示例:
#   # 干跑全量 (本期 W9 验证用)
#   ./auto-schedule-backlog.sh --week 9
#
#   # 干跑增量 (cron 默认用)
#   ./auto-schedule-backlog.sh --week 9 --since 24
#
#   # 真启 (owner 验收后用)
#   ./auto-schedule-backlog.sh --week 9 --since 24 --commit
#
# 落地文件:
#   - docs/plans/plan-auto-w{N+1}-from-backlog.yaml  (自动生成)
#   - docs/plans/backlog-auto-schedule-w{N}.md  (调度日志)
# - scripts 路径
set -euo pipefail

# 解析参数 (传到 Python)
PY_ARGS=("$@")

# 计算 SCRIPT_DIR (这个 shell 所在目录, 跨 OS 兼容)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKEND_ROOT="${PROJECT_ROOT}/backend/cases-crawler"

# 检查 Python 脚本存在
CONVERT_SCRIPT="${BACKEND_ROOT}/scripts/backlog_to_plan_tasks.py"
SCHEDULE_SCRIPT="${BACKEND_ROOT}/scripts/auto_schedule_backlog.py"

if [ ! -f "$SCHEDULE_SCRIPT" ]; then
    echo "[ERROR] Python script not found: $SCHEDULE_SCRIPT" >&2
    exit 1
fi

# 检查 Python (Windows 用 py launcher, Linux/Mac 用 python3)
if command -v python >/dev/null 2>&1; then
    PYTHON=python
elif command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v py >/dev/null 2>&1; then
    PYTHON="py -3.11"
else
    echo "[ERROR] Python not found in PATH" >&2
    exit 1
fi

# 切换到 backend/cases-crawler 跑 (跟 core/config.py 相对路径一致)
cd "$BACKEND_ROOT"

# 默认参数 (cron 默认增量 24h, 真启 --commit 由 owner 触发)
DEFAULT_ARGS=(--week 9)

# 如果用户没传 --week, 加默认
HAS_WEEK=0
for arg in "$@"; do
    if [ "$arg" = "--week" ]; then
        HAS_WEEK=1
        break
    fi
done

if [ $HAS_WEEK -eq 0 ]; then
    set -- "${DEFAULT_ARGS[@]}" "$@"
fi

# log: stdout → 文件 (cron 要求落档)
LOG_DIR="${PROJECT_ROOT}/logs/cron"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/auto-schedule-backlog-$(date +%Y%m%d-%H%M%S).log"

echo "[INFO] $(date -Iseconds 2>/dev/null || date) auto-schedule-backlog START" | tee -a "$LOG_FILE"
echo "[INFO] Backend: $BACKEND_ROOT" | tee -a "$LOG_FILE"
echo "[INFO] Args:  $*" | tee -a "$LOG_FILE"
echo "[INFO] Log:   $LOG_FILE" | tee -a "$LOG_FILE"

# 调用 Python (后台跑 + 落档, 不阻塞 cron 调度)
set +e
"$PYTHON" "$SCHEDULE_SCRIPT" "$@" 2>&1 | tee -a "$LOG_FILE"
RC=$?
set -e

if [ $RC -ne 0 ]; then
    echo "[ERROR] auto-schedule-backlog failed: returncode=$RC, log=$LOG_FILE" >&2
    exit $RC
fi

echo "[INFO] $(date -Iseconds 2>/dev/null || date) auto-schedule-backlog OK" | tee -a "$LOG_FILE"
exit 0
