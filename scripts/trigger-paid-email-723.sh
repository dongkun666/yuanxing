#!/usr/bin/env bash
# W14 first-paid-triggers-729 提前 6 天转化邮件触发脚本 (cron 调用入口)
# (lex-bd · 2026-06-30, W15 w14-followup-fixes 路径修复: lex-coder · 2026-06-30)
#
# 用途:
#   - 2026-07-23 09:00 CST cron 跑一次 (提前 6 天转化邮件触发)
#   - 手动测试: ./trigger-paid-email-723.sh --dry-run
#
# 设计原则:
#   - 默认 dry-run (不污染 owner 队列, 见 first-paid-triggers.md v1.0)
#   - 5 律师 (L1-L5) 群发 800 字转化邮件 + 创史 5 折推荐
#   - exit code 0 = 发送成功, 非 0 = 失败 (cron 触发器会发邮件)
#
# 集成:
#   mavis cron self lex-bd first-paid-email-723 \
#     --every "1d" \
#     --start "2026-07-22T09:00:00+08:00" \
#     --prompt "7/23 09:00 提前 6 天转化邮件待触发 (5 律师 L1-L5)"
#
# 调用示例:
#   # 干跑测试 (公测前验证)
#   ./trigger-paid-email-723.sh --dry-run
#
#   # 真启 (7/23 09:00 cron 自动触发)
#   ./trigger-paid-email-723.sh --commit
#
# 落地文件:
#   - docs/marketing/first-paid-triggers-runbook.md § 3.1 (邮件模板)
#   - docs/marketing/dashboard-paid-triggers.md § 1 (触达率 log)
#   - logs/cron/trigger-paid-email-723-YYYYMMDD-HHMMSS.log (执行日志)
#
# 状态:
#   - W14 v1.0 落档 (2026-06-30)
#   - W15 v1.1 路径修复 (2026-06-30): SCRIPT_DIR/../.. → SCRIPT_DIR/.. (yuanxing/ 而非根目录)
#   - W16 v1.2 路径加固 (2026-06-30):
#     * BASH_SOURCE 兜底: 当 BASH_SOURCE[0] 为空 (如 bash -c "..." 调用) 时
#       回退到 $0 / readlink -f, 防止 silent fail
#     * 跟 trigger-l4l5-email-819.sh 保持一致 (W16 w15-followup-path 同步加固)
#   - 等 2026-07-23 09:00 实际触发
set -euo pipefail

# 解析参数 (传到 Python send_email.py + log_trigger.py)
PY_ARGS=("$@")

# 计算 SCRIPT_DIR (这个 shell 所在目录, 跨 OS 兼容, 不依赖 cwd)
# BASH_SOURCE[0] = 这个 shell 脚本自身路径
# 兜底链:
#   1. BASH_SOURCE[0]  (Git Bash / WSL bash / 常规 bash 调脚本)
#   2. $0              (POSIX 兜底, 当 BASH_SOURCE 为空时, 例如 bash -c "..." 调用)
#   3. readlink -f     (处理符号链接, 拿到真实路径)
#   4. 显式 fail       (若以上都失败, cron 触发器会发邮件)
_SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"
if [ -z "$_SCRIPT_PATH" ] || [ "$_SCRIPT_PATH" = "bash" ]; then
    # bash -c "..." 场景: $0 = "bash", BASH_SOURCE 为空
    # 这种情况下 cron 一般直接写绝对路径调用, 此分支主要是防御性
    echo "[ERROR] 无法定位脚本路径 (BASH_SOURCE 和 \$0 都为空)" >&2
    echo "[INFO] 请用绝对路径调用: bash $PROJECT_ROOT/scripts/$(basename "$0") --dry-run" >&2
    exit 1
fi
# 处理符号链接 (Linux/macOS 有 readlink -f, Windows Git Bash 也有; WSL 也有)
if command -v readlink >/dev/null 2>&1; then
    _SCRIPT_REAL="$(readlink -f "$_SCRIPT_PATH" 2>/dev/null || echo "$_SCRIPT_PATH")"
else
    _SCRIPT_REAL="$_SCRIPT_PATH"
fi
SCRIPT_DIR="$(cd "$(dirname "$_SCRIPT_REAL")" && pwd)"
# PROJECT_ROOT = yuanxing/ (SCRIPT_DIR 的上一级)
# W14 v1.0 bug: 用了 SCRIPT_DIR/../.. 导致 PROJECT_ROOT = E:\元枢法智前端\ (根目录)
# W15 v1.1 fix: 改为 SCRIPT_DIR/.. = E:\元枢法智前端\yuanxing\ (yuanxing 项目根)
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# 邮件触发脚本路径 (SCRIPT_DIR 同级, yuanxing/scripts/)
SEND_EMAIL_SCRIPT="${SCRIPT_DIR}/send_email.py"
LOG_TRIGGER_SCRIPT="${SCRIPT_DIR}/log_trigger.py"

# 检查 Python 脚本存在
if [ ! -f "$SEND_EMAIL_SCRIPT" ]; then
    echo "[ERROR] Python script not found: $SEND_EMAIL_SCRIPT" >&2
    echo "[INFO] 公测前补全 send_email.py (Mavis SMTP 触发器)" >&2
    exit 1
fi

if [ ! -f "$LOG_TRIGGER_SCRIPT" ]; then
    echo "[ERROR] Python script not found: $LOG_TRIGGER_SCRIPT" >&2
    echo "[INFO] 公测前补全 log_trigger.py (触达日志写入 dashboard)" >&2
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

# 切换到项目根目录 (跟 core/config.py 相对路径一致)
cd "$PROJECT_ROOT"

# 5 律师邮箱 (从 scripts/lawyer-emails.json 读取, W14 follow-up 落地)
# 公测前 7/22 总指挥填实邮箱, 只改 lawyer-emails.json 一个文件
LAWYER_EMAILS_JSON="${SCRIPT_DIR}/lawyer-emails.json"

if [ ! -f "$LAWYER_EMAILS_JSON" ]; then
    echo "[ERROR] 律师邮箱 JSON 不存在: $LAWYER_EMAILS_JSON" >&2
    echo "[INFO] 公测前补全 lawyer-emails.json (W15 w14-followup-fixes 落地)" >&2
    exit 1
fi

# 解析 JSON 提取 emails[] 和 invite_codes[]
# 优先 jq, 降级 python (Windows 默认 python 3.14)
LAWYER_EMAILS=()
LAWYER_INVITE_CODES=()

if command -v jq >/dev/null 2>&1; then
    while IFS=$'\t' read -r EMAIL INVITE; do
        LAWYER_EMAILS+=("$EMAIL")
        LAWYER_INVITE_CODES+=("$INVITE")
    done < <(jq -r '.lawyers[] | "\(.email)\t\(.invite_code)"' "$LAWYER_EMAILS_JSON")
else
    # 降级: 用 python 解析 JSON (Windows 默认 python 3.14)
    while IFS=$'\t' read -r EMAIL INVITE; do
        LAWYER_EMAILS+=("$EMAIL")
        LAWYER_INVITE_CODES+=("$INVITE")
    done < <("$PYTHON" -c "
import json, sys
with open(r'$LAWYER_EMAILS_JSON', encoding='utf-8') as f:
    data = json.load(f)
for l in data['lawyers']:
    print(f\"{l['email']}\t{l['invite_code']}\")
")
fi

if [ ${#LAWYER_EMAILS[@]} -eq 0 ]; then
    echo "[ERROR] lawyer-emails.json 解析失败或为空: $LAWYER_EMAILS_JSON" >&2
    exit 1
fi

LAWYER_COUNT=${#LAWYER_EMAILS[@]}
echo "[INFO] 律师邮箱 JSON 解析成功: $LAWYER_COUNT 律师"

# 邮件主题
EMAIL_SUBJECT="您的 LexPrime 试用即将到期 - 创史体验官特别优惠"

# 邮件模板路径
EMAIL_TEMPLATE_PATH="${PROJECT_ROOT}/docs/marketing/first-paid-triggers-runbook.md"

# log: stdout → 文件 (cron 要求落档)
LOG_DIR="${PROJECT_ROOT}/logs/cron"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/trigger-paid-email-723-$(date +%Y%m%d-%H%M%S).log"

echo "[INFO] $(date -Iseconds 2>/dev/null || date) trigger-paid-email-723 START" | tee -a "$LOG_FILE"
echo "[INFO] Project: $PROJECT_ROOT" | tee -a "$LOG_FILE"
echo "[INFO] Subject: $EMAIL_SUBJECT" | tee -a "$LOG_FILE"
echo "[INFO] Template: $EMAIL_TEMPLATE_PATH" | tee -a "$LOG_FILE"
echo "[INFO] Lawyers: $LAWYER_COUNT (从 $LAWYER_EMAILS_JSON)" | tee -a "$LOG_FILE"
echo "[INFO] Args:    $*" | tee -a "$LOG_FILE"
echo "[INFO] Log:     $LOG_FILE" | tee -a "$LOG_FILE"

# 检查 dry-run 参数
IS_DRY_RUN=1
for arg in "$@"; do
    if [ "$arg" = "--commit" ]; then
        IS_DRY_RUN=0
        break
    fi
done

if [ $IS_DRY_RUN -eq 1 ]; then
    echo "[INFO] DRY-RUN 模式 (默认): 不真发邮件, 仅记录日志" | tee -a "$LOG_FILE"
fi

# 触发 5 律师邮件
set +e
TRIGGER_SUCCESS=0
TRIGGER_FAIL=0

for i in "${!LAWYER_EMAILS[@]}"; do
    EMAIL="${LAWYER_EMAILS[$i]}"
    INVITE_CODE="${LAWYER_INVITE_CODES[$i]}"

    echo "[INFO] [$((i+1))/$LAWYER_COUNT] 触发邮件至 $EMAIL (invite_code=$INVITE_CODE)" | tee -a "$LOG_FILE"

    if [ $IS_DRY_RUN -eq 1 ]; then
        # Dry-run 模式: 仅打印 + 写日志, 不真发邮件
        echo "[DRY-RUN] 邮件触发 (placeholder):" | tee -a "$LOG_FILE"
        echo "  to:      $EMAIL" | tee -a "$LOG_FILE"
        echo "  subject: $EMAIL_SUBJECT" | tee -a "$LOG_FILE"
        echo "  body:    docs/marketing/first-paid-triggers-runbook.md § 3.1 (800 字)" | tee -a "$LOG_FILE"
        echo "  invite:  $INVITE_CODE" | tee -a "$LOG_FILE"
        TRIGGER_SUCCESS=$((TRIGGER_SUCCESS + 1))
    else
        # 真启模式: 调用 send_email.py + log_trigger.py
        "$PYTHON" "$SEND_EMAIL_SCRIPT" \
            --to "$EMAIL" \
            --subject "$EMAIL_SUBJECT" \
            --body "$EMAIL_TEMPLATE_PATH" \
            --body-section "### 3.1" \
            --invite-code "$INVITE_CODE" \
            --trigger-id "first-paid-triggers-729" \
            --trigger-time "2026-07-23T09:00:00+08:00" \
            2>&1 | tee -a "$LOG_FILE"
        RC=$?

        if [ $RC -ne 0 ]; then
            echo "[ERROR] 邮件发送失败: $EMAIL (rc=$RC)" | tee -a "$LOG_FILE"
            TRIGGER_FAIL=$((TRIGGER_FAIL + 1))
        else
            TRIGGER_SUCCESS=$((TRIGGER_SUCCESS + 1))
        fi
    fi
done

# 写入 dashboard 触达日志 (5 律师批量)
echo "[INFO] 写入 dashboard 触达日志..." | tee -a "$LOG_FILE"

# 准备 log_trigger.py 调用参数 (dry-run 模式透传, 不污染 dashboard)
LOG_TRIGGER_ARGS=(
    --trigger-id "first-paid-triggers-729"
    --trigger-time "2026-07-23T09:00:00+08:00"
    --trigger-channel "email"
    --trigger-target "5-lawyers"
    --trigger-success "$TRIGGER_SUCCESS"
    --trigger-fail "$TRIGGER_FAIL"
    --trigger-dry-run "$IS_DRY_RUN"
    --log-file "${PROJECT_ROOT}/docs/marketing/dashboard-paid-triggers.md"
)
if [ $IS_DRY_RUN -eq 1 ]; then
    LOG_TRIGGER_ARGS+=(--dry-run)
fi

"$PYTHON" "$LOG_TRIGGER_SCRIPT" "${LOG_TRIGGER_ARGS[@]}" \
    2>&1 | tee -a "$LOG_FILE"
RC=$?

if [ $RC -ne 0 ]; then
    echo "[ERROR] dashboard 触达日志写入失败 (rc=$RC)" | tee -a "$LOG_FILE"
    set -e
    exit $RC
fi

set -e

echo "[INFO] $(date -Iseconds 2>/dev/null || date) trigger-paid-email-723 OK" | tee -a "$LOG_FILE"
echo "[INFO] 触发统计: 成功 $TRIGGER_SUCCESS / 失败 $TRIGGER_FAIL / 总计 $LAWYER_COUNT" | tee -a "$LOG_FILE"
echo "[INFO] 日志: $LOG_FILE" | tee -a "$LOG_FILE"

# 退出码: 全部成功 = 0, 部分失败 = 1, 全部失败 = 2
if [ $TRIGGER_FAIL -eq 0 ]; then
    exit 0
elif [ $TRIGGER_SUCCESS -eq 0 ]; then
    exit 2
else
    exit 1
fi