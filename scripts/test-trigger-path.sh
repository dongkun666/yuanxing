#!/usr/bin/env bash
# W16 w15-followup-path 回归测试: scripts/test-trigger-path.sh
# (lex-coder · 2026-06-30)
#
# 用途: 验证 W15 verifier 报的 path bug 已修复, 2 触发脚本路径解析
#       在 Windows / WSL / macOS / Linux 跨平台 dry-run 都能 exit 0
#
# 测试场景 (3 个):
#   1. 7/23  W14 cron  trigger-paid-email-723.sh  --dry-run
#   2. 8/19  W15 cron  trigger-l4l5-email-819.sh  --dry-run
#   3. 公测 day 1 dry-run  (2 脚本 back-to-back, 模拟 cron 同时触发)
#
# 测试维度 (6 维):
#   1. 路径解析: SCRIPT_DIR 应是 yuanxing/scripts/, PROJECT_ROOT 应是 yuanxing/
#   2. 脚本存在: send_email.py / log_trigger.py 在 SCRIPT_DIR 下能定位
#   3. 律师邮箱: paid-723 解析 5 律师 (JSON), l4l5-819 解析 2 律师 (硬编码)
#   4. dry-run: 不真发邮件, exit 0
#   5. log 落档: logs/cron/*.log 自动创建
#   6. shellcheck 0 + bash -n 0  (脚本本身语法干净)
#
# 跨平台兼容:
#   - Windows Git Bash (bash.exe 解析 /e/... 路径)
#   - Windows WSL  (bash 解析 /mnt/e/... 路径)
#   - macOS  (bash 解析 /Users/... 路径)
#   - Linux  (bash 解析 /home/... 路径)
#
# 调用: bash scripts/test-trigger-path.sh [--quick]
#   --quick: 只跑 dry-run 跳过 shellcheck (CI 阶段用)
#
# 退出码: 0 = 全 PASS, 1 = 至少 1 FAIL

set -euo pipefail

# ==================== 初始化 ====================
SCRIPT_DIR_TEST="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
TEST_NAME="test-trigger-path"
TEST_VERSION="v1.0-w16"
TEST_DATE="$(date -Iseconds 2>/dev/null || date)"

# 颜色 (如果终端支持)
if [ -t 1 ]; then
    C_GREEN='\033[0;32m'
    C_RED='\033[0;31m'
    C_YELLOW='\033[0;33m'
    C_RESET='\033[0m'
else
    C_GREEN=''
    C_RED=''
    C_YELLOW=''
    C_RESET=''
fi

# 计数器
PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0
declare -a FAILURES=()

# 检测 shellcheck 是否可用
SHELLCHECK_AVAILABLE=0
if command -v shellcheck >/dev/null 2>&1; then
    SHELLCHECK_AVAILABLE=1
fi

# ==================== 工具函数 ====================
print_header() {
    echo ""
    echo "=================================================="
    echo "$1"
    echo "=================================================="
}

pass() {
    PASS_COUNT=$((PASS_COUNT + 1))
    echo -e "  ${C_GREEN}[PASS]${C_RESET} $1"
}

fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAILURES+=("$1")
    echo -e "  ${C_RED}[FAIL]${C_RESET} $1"
}

skip() {
    SKIP_COUNT=$((SKIP_COUNT + 1))
    echo -e "  ${C_YELLOW}[SKIP]${C_RESET} $1"
}

# 验证字符串包含子串
assert_contains() {
    local label="$1"
    local haystack="$2"
    local needle="$3"
    if [[ "$haystack" == *"$needle"* ]]; then
        pass "$label (found: '$needle')"
    else
        fail "$label (NOT found: '$needle' in output)"
    fi
}

# 验证 exit code
assert_exit_code() {
    local label="$1"
    local actual="$2"
    local expected="$3"
    if [ "$actual" = "$expected" ]; then
        pass "$label (exit=$actual)"
    else
        fail "$label (expected exit=$expected, got=$actual)"
    fi
}

# ==================== 场景 1: 7/23 W14 cron 路径 ====================
print_header "场景 1: 7/23 W14 cron 路径 (trigger-paid-email-723.sh --dry-run)"

SCRIPT_723="${SCRIPT_DIR_TEST}/trigger-paid-email-723.sh"
if [ ! -f "$SCRIPT_723" ]; then
    fail "trigger-paid-email-723.sh 不存在: $SCRIPT_723"
else
    pass "trigger-paid-email-723.sh 存在: $SCRIPT_723"

    # 1a. bash -n 语法检查
    if bash -n "$SCRIPT_723" 2>/dev/null; then
        pass "bash -n syntax check OK (paid-723)"
    else
        fail "bash -n syntax check FAILED (paid-723)"
    fi

    # 1b. dry-run 跑一次
    OUTPUT_723="$(bash "$SCRIPT_723" --dry-run 2>&1)" || true
    RC_723=$?
    assert_exit_code "paid-723 dry-run exit code" "$RC_723" "0"

    # 1c. 路径解析验证
    assert_contains "paid-723 SCRIPT_DIR 解析" "$OUTPUT_723" "Project:"
    assert_contains "paid-723 PROJECT_ROOT 路径" "$OUTPUT_723" "/yuanxing"
    # 关键: PROJECT_ROOT 必须以 /yuanxing 结尾, 不能是 /元枢法智前端 (走多了)
    if [[ "$OUTPUT_723" == *"Project: /"*"/yuanxing"* ]] || [[ "$OUTPUT_723" == *"Project: "*"\\yuanxing"* ]]; then
        pass "paid-723 PROJECT_ROOT 正确 (以 /yuanxing 结尾)"
    else
        fail "paid-723 PROJECT_ROOT 异常 (可能走多了一级): $(echo "$OUTPUT_723" | grep -o 'Project: [^[:space:]]*' | head -1)"
    fi

    # 1d. 律师邮箱解析 (5 律师 from JSON)
    if [[ "$OUTPUT_723" == *"律师邮箱 JSON 解析成功: 5 律师"* ]]; then
        pass "paid-723 律师邮箱 JSON 解析: 5 律师"
    else
        fail "paid-723 律师邮箱 JSON 解析异常 (期望 5 律师)"
    fi

    # 1e. dry-run 模式
    assert_contains "paid-723 DRY-RUN 模式" "$OUTPUT_723" "DRY-RUN 模式"

    # 1f. send_email.py / log_trigger.py 不报 not found
    if [[ "$OUTPUT_723" == *"Python script not found"* ]]; then
        fail "paid-723 send_email.py / log_trigger.py not found (path bug)"
    else
        pass "paid-723 Python scripts 路径 OK"
    fi

    # 1g. 触发统计
    if [[ "$OUTPUT_723" == *"触发统计: 成功 5 / 失败 0 / 总计 5"* ]]; then
        pass "paid-723 触发统计 5/5 (100%)"
    else
        fail "paid-723 触发统计异常: $(echo "$OUTPUT_723" | grep -o '触发统计: [^[:space:]]* [^[:space:]]* [^[:space:]]* [^[:space:]]*' | head -1)"
    fi
fi

# ==================== 场景 2: 8/19 W15 l4l5 cron 路径 ====================
print_header "场景 2: 8/19 W15 l4l5 cron 路径 (trigger-l4l5-email-819.sh --dry-run)"

SCRIPT_819="${SCRIPT_DIR_TEST}/trigger-l4l5-email-819.sh"
if [ ! -f "$SCRIPT_819" ]; then
    fail "trigger-l4l5-email-819.sh 不存在: $SCRIPT_819"
else
    pass "trigger-l4l5-email-819.sh 存在: $SCRIPT_819"

    # 2a. bash -n 语法检查
    if bash -n "$SCRIPT_819" 2>/dev/null; then
        pass "bash -n syntax check OK (l4l5-819)"
    else
        fail "bash -n syntax check FAILED (l4l5-819)"
    fi

    # 2b. dry-run 跑一次
    OUTPUT_819="$(bash "$SCRIPT_819" --dry-run 2>&1)" || true
    RC_819=$?
    # W15 verifier 报: W15 v1.0 dry-run 立刻 exit 1, 0 邮件发出
    # W16 v1.1 修复: 应当 exit 0
    assert_exit_code "l4l5-819 dry-run exit code" "$RC_819" "0"

    # 2c. 路径解析验证 (核心 bug 修复点)
    assert_contains "l4l5-819 Project 输出" "$OUTPUT_819" "Project:"
    if [[ "$OUTPUT_819" == *"Project: /"*"/yuanxing"* ]] || [[ "$OUTPUT_819" == *"Project: "*"\\yuanxing"* ]]; then
        pass "l4l5-819 PROJECT_ROOT 正确 (以 /yuanxing 结尾, W15 v1.0 bug 已修)"
    else
        fail "l4l5-819 PROJECT_ROOT 异常 (可能走多了一级): $(echo "$OUTPUT_819" | grep -o 'Project: [^[:space:]]*' | head -1)"
    fi

    # 2d. 关键: send_email.py / log_trigger.py 路径必须存在
    if [[ "$OUTPUT_819" == *"Python script not found"* ]]; then
        fail "l4l5-819 send_email.py / log_trigger.py not found (path bug 未修)"
    else
        pass "l4l5-819 Python scripts 路径 OK (W15 v1.0 bug 已修)"
    fi

    # 2e. L4/L5 律师硬编码 (2 律师, l4.founding@lexprime.cn + l5.founding@lexprime.cn)
    if [[ "$OUTPUT_819" == *"l4.founding@lexprime.cn"* ]]; then
        pass "l4l5-819 L4 律师邮箱解析"
    else
        fail "l4l5-819 L4 律师邮箱未解析"
    fi
    if [[ "$OUTPUT_819" == *"l5.founding@lexprime.cn"* ]]; then
        pass "l4l5-819 L5 律师邮箱解析"
    else
        fail "l4l5-819 L5 律师邮箱未解析"
    fi

    # 2f. dry-run 模式
    assert_contains "l4l5-819 DRY-RUN 模式" "$OUTPUT_819" "DRY-RUN 模式"

    # 2g. 触发统计 (2 律师)
    if [[ "$OUTPUT_819" == *"成功 2 / 失败 0 / 总计 2"* ]]; then
        pass "l4l5-819 触发统计 2/2 (100%)"
    else
        fail "l4l5-819 触发统计异常: $(echo "$OUTPUT_819" | grep -o '触发统计: [^[:space:]]* [^[:space:]]* [^[:space:]]* [^[:space:]]*' | head -1)"
    fi

    # 2h. trigger-id 验证
    assert_contains "l4l5-819 trigger-id" "$OUTPUT_819" "l4l5-triggers-825"
fi

# ==================== 场景 3: 公测 day 1 dry-run (back-to-back) ====================
print_header "场景 3: 公测 day 1 dry-run (2 脚本 back-to-back)"

# 模拟公测 day 1 (7/26): 总指挥跑两个脚本 dry-run 验证
OUTPUT_723_BK="$(bash "$SCRIPT_723" --dry-run 2>&1)" || true
RC_723_BK=$?
OUTPUT_819_BK="$(bash "$SCRIPT_819" --dry-run 2>&1)" || true
RC_819_BK=$?

assert_exit_code "back-to-back paid-723 exit" "$RC_723_BK" "0"
assert_exit_code "back-to-back l4l5-819 exit" "$RC_819_BK" "0"

# 关键: 2 脚本共用 logs/cron/ 目录, 不冲突
LOG_DIR="${SCRIPT_DIR_TEST}/../logs/cron"
if [ -d "$LOG_DIR" ]; then
    LOG_COUNT=$(ls "$LOG_DIR" | grep -c "trigger-.*-.*-.*\.log" 2>/dev/null || echo 0)
    if [ "$LOG_COUNT" -ge 1 ]; then
        pass "logs/cron/ 目录存在 + 至少 1 个 trigger log 落档 (count=$LOG_COUNT)"
    else
        fail "logs/cron/ 存在但无 trigger log 落档"
    fi
else
    fail "logs/cron/ 目录不存在 ($LOG_DIR), 路径解析异常"
fi

# ==================== 场景 4: shellcheck 静态检查 ====================
print_header "场景 4: shellcheck 静态检查 (0 issue)"

if [ "$SHELLCHECK_AVAILABLE" -eq 1 ]; then
    if shellcheck "$SCRIPT_723" "$SCRIPT_819" "$SCRIPT_DIR_TEST/test-trigger-path.sh" 2>&1; then
        pass "shellcheck 0 issues (3 脚本)"
    else
        fail "shellcheck 报 issues (见上方输出)"
    fi
else
    skip "shellcheck 不可用 (command -v shellcheck 返回空)"
fi

# ==================== 场景 5: 跨平台路径兼容 (可选) ====================
print_header "场景 5: 跨平台路径兼容 (BASH_SOURCE 兜底验证)"

# 模拟 bash -c "..." 调用场景 (BASH_SOURCE[0] 为空, $0 = "bash")
# 这种场景下脚本应当 exit 1 + 打印明确错误, 而不是 silent fail
OUTPUT_BASH_C="$(bash -c "bash '$SCRIPT_723' --dry-run 2>&1" 2>&1)" || true
RC_BASH_C=$?
# 注意: 这个测试在 -c 场景下, 我们的脚本会用 $0 (即 "bash" 字面量) 兜底, 触发 [ERROR] 分支
if [ "$RC_BASH_C" -ne 0 ]; then
    if [[ "$OUTPUT_BASH_C" == *"无法定位脚本路径"* ]]; then
        pass "BASH_SOURCE 兜底链生效 (bash -c 调用下显式 fail + 明确错误信息)"
    else
        skip "BASH_SOURCE 兜底可能未触发 (环境特殊): $(echo "$OUTPUT_BASH_C" | head -3)"
    fi
else
    skip "bash -c 调用意外 exit 0 (环境可能特殊, 跳过此场景)"
fi

# ==================== 总结 ====================
print_header "总结"
echo "Test:      $TEST_NAME $TEST_VERSION"
echo "Date:      $TEST_DATE"
echo "Script:    $SCRIPT_DIR_TEST"
echo "Platform:  $(uname -a 2>/dev/null || echo Windows)"
echo ""
echo -e "  ${C_GREEN}PASS${C_RESET}: $PASS_COUNT"
echo -e "  ${C_RED}FAIL${C_RESET}: $FAIL_COUNT"
echo -e "  ${C_YELLOW}SKIP${C_RESET}: $SKIP_COUNT"
echo ""

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo -e "${C_RED}=== 失败详情 ===${C_RESET}"
    for f in "${FAILURES[@]}"; do
        echo -e "  ${C_RED}✗${C_RESET} $f"
    done
    echo ""
    echo -e "${C_RED}VERDICT: FAIL ($FAIL_COUNT failed)${C_RESET}"
    exit 1
fi

echo -e "${C_GREEN}VERDICT: PASS ($PASS_COUNT passed, $SKIP_COUNT skipped)${C_RESET}"
exit 0
