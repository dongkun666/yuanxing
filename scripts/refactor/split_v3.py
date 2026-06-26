"""拆 script.js (4355 行, 8-space 缩进, 在 IIFE 内) 为 5 文件
- 4 模块: 顶层 function 声明 (无 IIFE 包装)
- 主 script.js: 删掉模块函数, 保留原 IIFE 包装

由于模块用 <script> 同步加载, 它们的全局函数在主 script.js 之前已定义
"""
import re
from pathlib import Path

ROOT = Path(r'E:\元枢法智前端\yuanxing')
src_file = ROOT / 'assets' / 'js' / 'script.js'
src = src_file.read_text(encoding='utf-8')
lines = src.split('\n')
total = len(lines)

# 找 function 起始行
func_re = re.compile(r'^\s*function\s+(\w+)\s*\(', re.MULTILINE)
funcs = {}
for m in func_re.finditer(src):
    funcs[m.group(1)] = src[:m.start()].count('\n') + 1

def find_func_end(name, start):
    depth = 0
    seen_open = False
    for i in range(start - 1, total):
        line = lines[i]
        for ch in line:
            if ch == '{':
                depth += 1
                seen_open = True
            elif ch == '}':
                depth -= 1
                if seen_open and depth == 0:
                    return i + 1
    return total

func_end = {n: find_func_end(n, s) for n, s in funcs.items()}

# 模块函数表
MODULES = {
    'knowledge.js': [
        'applyKnowledgeFilter', 'switchKnowledgeMainTab',
        'startCompile', 'cancelCompile', 'recompile',
        'viewCompileProgress', 'viewWikiPages', 'runLintNow', 'simulateUpload',
    ],
    'ai.js': [
        'switchAITab', 'startNewChat', 'selectHistory', 'filterHistory',
        'switchAIView', 'switchAIViewSubView', 'selectAIHistory', 'filterAIHistory',
        'toggleMoreMenu', 'handleMoreAction',
        'selectExtractSource', 'closeAIExtractModal',
        'startAIExtract', 'copyExtractResult', 'exportExtractResult',
    ],
    'templates.js': [
        'switchTemplateTab', 'fixTemplateViewDOM', 'switchTemplateView',
        'openUploadTemplateModal', 'closeUploadTemplateModal', 'submitUploadTemplate',
        'deletePersonalTemplate', 'openCategoryManageModal', 'closeCategoryManageModal',
        'addCategory', 'sortPersonalTemplates', 'parseTime',
        'updateAllCategoryCount', 'filterPersonalByCategory', 'filterOfficialByCategory',
        'filterOfficialByType', 'applyOfficialFilter', 'clearOfficialSearch',
        'previewOfficialTemplate', 'deleteCategory',
    ],
    'account.js': [
        'toggleNotifications', 'markAllNotifications', 'toggleUserMenu',
        'switchToSubscription', 'toggleBilling', 'showPayment',
        'backToSubscription', 'selectPaymentMethod', 'paySuccess',
        'goToSubscription', 'goToWorkstation', 'switchToOrders', 'switchToMemberCenter',
        'goToMemberCenter', 'switchToAccountSettings',
        'toggleProfileEdit', 'cancelProfileEdit', 'saveProfile', 'showSaveSuccess',
        'addTagInput', 'handleAvatarUpload', 'removeTag', 'showAddTagDialog',
        'removeCertFile', 'toggle2FA', 'showDeviceManager', 'confirmAccountDeletion',
        'autoSaveProfile', 'validateField', 'validateEmail',
        'saveNotificationSettings', 'bindAccount', 'unbindAccount',
    ],
}

# 收集每个模块的函数 (s, e, name) - 排序
module_items = {}
for mod, fnames in MODULES.items():
    items = []
    for fname in fnames:
        if fname not in funcs:
            print(f'  WARN: {fname} not found')
            continue
        s = funcs[fname]
        e = func_end[fname]
        items.append((s, e, fname))
    items.sort()
    module_items[mod] = items
    total_lines = sum(e - s + 1 for s, e, _ in items)
    print(f'  {mod}: {len(items)} 函数, {total_lines} 行')

# 找到主文件保留的函数
all_mod_funcs = set()
for items in module_items.values():
    for _, _, n in items:
        all_mod_funcs.add(n)
main_items = [(s, e, n) for n, s in funcs.items() if n not in all_mod_funcs]
main_items.sort()

# 写入模块文件 (无 IIFE, 顶层 function)
HEADERS = {
    'knowledge.js': '''/**
 * 知识库管理模块 - LLM Wiki 风格
 * 包含: 知识库搜索过滤 + 3 Tab 切换 + AI 编译交互
 * 加载: 在 script.js 之前同步加载 (使用其 AppState)
 */
''',
    'ai.js': '''/**
 * AI 对话模块 - AI 助手 + 历史 + AI 一键提取
 * 包含: AI 标签切换 + 新建对话 + 历史搜索 + 提取要素
 * 加载: 在 script.js 之前同步加载
 */
''',
    'templates.js': '''/**
 * 模板管理模块 - 官方模板 + 个人模板
 * 包含: Tab 切换 + 视图切换 + 上传/分类/筛选/排序/预览
 * 加载: 在 script.js 之前同步加载
 */
''',
    'account.js': '''/**
 * 账号/会员/支付模块
 * 包含: 通知面板 + 会员订阅 + 支付 + 账号设置 + 个人资料 + 第三方账号
 * 加载: 在 script.js 之前同步加载
 */
''',
}

print('\n=== 写入模块 ===')
for name, items in module_items.items():
    out = ROOT / 'assets' / 'js' / name
    parts = [HEADERS[name], '']
    # 8-space 缩进 (跟主文件保持一致)
    for s, e, n in items:
        body = '\n'.join(lines[s-1:e])
        parts.append(body)
        parts.append('')
    out.write_text('\n'.join(parts), encoding='utf-8')
    size_kb = out.stat().st_size / 1024
    print(f'  ✓ {name}: {size_kb:.1f} KB')

# 写主 script.js: 删除模块函数, 保留原结构
print('\n=== 写主 script.js ===')
mod_line_ranges = []
for items in module_items.values():
    for s, e, _ in items:
        mod_line_ranges.append((s, e))

# 按行号排序并合并
mod_line_ranges.sort()
# 标记哪些行要删除
delete = set()
for s, e in mod_line_ranges:
    for i in range(s, e + 1):
        delete.add(i)

# 同时删除空行 (模块函数之间的空行)
# 策略: 找到被删除函数之间连续的「空行段」, 也一起删, 避免产生大空块
# 简单起见, 只删除函数行 (s..e), 保留函数之间的空行
# 然后再做一次"清理连续空行 >2 的"

new_lines = []
for i, line in enumerate(lines, 1):
    if i not in delete:
        new_lines.append(line)

# 清理连续空行 >2
cleaned = []
empty_count = 0
for line in new_lines:
    if line.strip() == '':
        empty_count += 1
        if empty_count <= 2:
            cleaned.append(line)
    else:
        empty_count = 0
        cleaned.append(line)

(ROOT / 'assets' / 'js' / 'script.js').write_text('\n'.join(cleaned), encoding='utf-8')
size_kb = (ROOT / 'assets' / 'js' / 'script.js').stat().st_size / 1024
print(f'  ✓ script.js: {size_kb:.1f} KB, {len(cleaned)} 行')

# 验证
print('\n=== 验证语法 ===')
import subprocess
for f in ['knowledge.js', 'ai.js', 'templates.js', 'account.js', 'script.js']:
    r = subprocess.run(['node', '--check', str(ROOT / 'assets' / 'js' / f)],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print(f'  ✓ {f}')
    else:
        print(f'  ✗ {f}: {r.stderr[:200]}')
