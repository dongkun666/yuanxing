#!/usr/bin/env bash
# W15 l4l5-triggers-825 提前 6 天转化邮件触发脚本 (cron 调用入口)
# (lex-bd · 2026-06-30)
#
# 用途:
#   - 2026-08-19 09:00 CST cron 跑一次 (提前 6 天 L4/L5 转化邮件触发)
#   - 手动测试: ./trigger-l4l5-email-819.sh --dry-run
#
# 设计原则:
#   - 默认 dry-run (不污染 owner 队列, 见 first-paid-triggers.md v1.0)
#   - L4/L5 律师 (BETA2025-0119/0120) 群发 800 字转化邮件 + 创史 5 折推荐
#   - exit code 0 = 发送成功, 非 0 = 失败 (cron 触发器会发邮件)
#
# 复用关系:
#   - 100% 复用 scripts/trigger-paid-email-723.sh (W14 v1.0, commit 6f785e5)
#   - 增量调整: 律师数 5→2 + 时间线 7/23→8/19 + 邀请码 BETA2025-0119/0120
#
# 集成:
#   mavis cron self lex-bd l4l5-email-819 \
#     --every "1d" \
#     --start "2026-08-18T09:00:00+08:00" \
#     --prompt "8/19 09:00 提前 6 天 L4/L5 转化邮件待触发 (2 律师 BETA2025-0119/0120)"
#
# 调用示例:
#   # 干跑测试 (公测前验证)
#   ./trigger-l4l5-email-819.sh --dry-run
#
#   # 真启 (8/19 09:00 cron 自动触发)
#   ./trigger-l4l5-email-819.sh --commit
#
# 落地文件:
#   - docs/marketing/l4l5-triggers-runbook.md § 3.1 (邮件模板)
#   - docs/marketing/dashboard-l4l5-triggers.md § 1 (触达率 log)
#   - logs/cron/trigger-l4l5-email-819-YYYYMMDD-HHMMSS.log (执行日志)
#
# 状态:
#   - W15 v1.0 落档 (2026-06-30)
#   - 等 2026-08-19 09:00 实际触发
set -euo pipefail

# 解析参数 (传到 Python send_email.py + log_trigger.py)
PY_ARGS=("$@")

# 计算 SCRIPT_DIR (这个 shell 所在目录, 跨 OS 兼容)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# 邮件触发脚本路径 (复用 W14 v1.0, 公测前补全 SMTP)
SEND_EMAIL_SCRIPT="${PROJECT_ROOT}/scripts/send_email.py"
LOG_TRIGGER_SCRIPT="${PROJECT_ROOT}/scripts/log_trigger.py"

# 检查 Python 脚本存在
if [ ! -f "$SEND_EMAIL_SCRIPT" ]; then
    echo "[ERROR] Python script not found: $SEND_EMAIL_SCRIPT" >&2
    echo "[INFO] 公测前补全 send_email.py (Mavis SMTP 触发器, W14 v1.0 已落档占位符)" >&2
    exit 1
fi

if [ ! -f "$LOG_TRIGGER_SCRIPT" ]; then
    echo "[ERROR] Python script not found: $LOG_TRIGGER_SCRIPT" >&2
    echo "[INFO] 公测前补全 log_trigger.py (触达日志写入 dashboard, W14 v1.0 已落档占位符)" >&2
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

# L4/L5 律师邮箱 (placeholder, 公测前 8/18 替换为真实邮箱)
# L4 BETA2025-0119: 中所合伙人 (深圳 12 年 30 人中大所金融/商事)
# L5 BETA2025-0120: 企业法务总监 (北京 10 年 互联网大厂 100+ 法务部)
# W14 follow-up 已建立 lawyer-emails.json (placeholder 占位符)
LAWYER_EMAILS=(
  "l4.founding@lexprime.cn"  # BETA2025-0119 中所合伙人
  "l5.founding@lexprime.cn"  # BETA2025-0120 企业法务总监
)

LAWYER_INVITE_CODES=(
  "BETA2025-0119"  # L4 中所合伙人 (评审 #2, 7/26 启动仪式)
  "BETA2025-0120"  # L5 企业法务总监 (评审 #2, 7/26 启动仪式)
)

LAWYER_NAMES=(
  "L4 中所合伙人"
  "L5 企业法务总监"
)

# 邮件主题 (复用 W14 模板, 加 (8/25) 区分 L4/L5 vs L1-L3 7/29 触发)
EMAIL_SUBJECT="您的 LexPrime 试用即将到期 - 创史体验官特别优惠 (8/25)"

# 邮件模板路径 (W15 l4l5-triggers-825)
EMAIL_TEMPLATE_PATH="${PROJECT_ROOT}/docs/marketing/l4l5-triggers-runbook.md"

# log: stdout → 文件 (cron 要求落档)
LOG_DIR="${PROJECT_ROOT}/logs/cron"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/trigger-l4l5-email-819-$(date +%Y%m%d-%H%M%S).log"

echo "[INFO] $(date -Iseconds 2>/dev/null || date) trigger-l4l5-email-819 START" | tee -a "$LOG_FILE"
echo "[INFO] Project: $PROJECT_ROOT" | tee -a "$LOG_FILE"
echo "[INFO] Subject: $EMAIL_SUBJECT" | tee -a "$LOG_FILE"
echo "[INFO] Template: $EMAIL_TEMPLATE_PATH" | tee -a "$LOG_FILE"
echo "[INFO] Lawyers: 2 (L4 BETA2025-0119 + L5 BETA2025-0120)" | tee -a "$LOG_FILE"
echo "[INFO] Trigger: 2026-08-19 09:00 CST (提前 6 天 L4/L5 转化邮件)" | tee -a "$LOG_FILE"
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

# 触发 L4/L5 律师邮件 (2 位律师, 群发 800 字转化邮件)
set +e
TRIGGER_SUCCESS=0
TRIGGER_FAIL=0

for i in "${!LAWYER_EMAILS[@]}"; do
    EMAIL="${LAWYER_EMAILS[$i]}"
    INVITE_CODE="${LAWYER_INVITE_CODES[$i]}"
    LAWYER_NAME="${LAWYER_NAMES[$i]}"

    echo "[INFO] [$((i+1))/2] 触发邮件至 $EMAIL ($LAWYER_NAME, invite_code=$INVITE_CODE)" | tee -a "$LOG_FILE"

    if [ $IS_DRY_RUN -eq 1 ]; then
        # Dry-run 模式: 仅打印 + 写日志, 不真发邮件
        echo "[DRY-RUN] 邮件触发 (placeholder):" | tee -a "$LOG_FILE"
        echo "  to:      $EMAIL" | tee -a "$LOG_FILE"
        echo "  lawyer:  $LAWYER_NAME" | tee -a "$LOG_FILE"
        echo "  subject: $EMAIL_SUBJECT" | tee -a "$LOG_FILE"
        echo "  body:    docs/marketing/l4l5-triggers-runbook.md § 3.1 (800 字)" | tee -a "$LOG_FILE"
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
            --trigger-id "l4l5-triggers-825" \
            --trigger-time "2026-08-19T09:00:00+08:00" \
            2>&1 | tee -a "$LOG_FILE"
        RC=$?

        if [ $RC -ne 0 ]; then
            echo "[ERROR] 邮件发送失败: $EMAIL ($LAWYER_NAME, rc=$RC)" | tee -a "$LOG_FILE"
            TRIGGER_FAIL=$((TRIGGER_FAIL + 1))
        else
            TRIGGER_SUCCESS=$((TRIGGER_SUCCESS + 1))
        fi
    fi
done

# 写入 dashboard 触达日志 (L4/L5 律师批量)
echo "[INFO] 写入 dashboard 触达日志..." | tee -a "$LOG_FILE"

"$PYTHON" "$LOG_TRIGGER_SCRIPT" \
    --trigger-id "l4l5-triggers-825" \
    --trigger-time "2026-08-19T09:00:00+08:00" \
    --trigger-channel "email" \
    --trigger-target "2-lawyers-l4-l5" \
    --trigger-success "$TRIGGER_SUCCESS" \
    --trigger-fail "$TRIGGER_FAIL" \
    --trigger-dry-run "$IS_DRY_RUN" \
    --log-file "${PROJECT_ROOT}/docs/marketing/dashboard-l4l5-triggers.md" \
    2>&1 | tee -a "$LOG_FILE"
RC=$?

if [ $RC -ne 0 ]; then
    echo "[ERROR] dashboard 触达日志写入失败 (rc=$RC)" | tee -a "$LOG_FILE"
    set -e
    exit $RC
fi

set -e

echo "[INFO] $(date -Iseconds 2>/dev/null || date) trigger-l4l5-email-819 OK" | tee -a "$LOG_FILE"
echo "[INFO] 触发统计: 成功 $TRIGGER_SUCCESS / 失败 $TRIGGER_FAIL / 总计 2" | tee -a "$LOG_FILE"
echo "[INFO] 日志: $LOG_FILE" | tee -a "$LOG_FILE"

# 退出码: 全部成功 = 0, 部分失败 = 1, 全部失败 = 2
if [ $TRIGGER_FAIL -eq 0 ]; then
    exit 0
elif [ $TRIGGER_SUCCESS -eq 0 ]; then
    exit 2
else
    exit 1
fi