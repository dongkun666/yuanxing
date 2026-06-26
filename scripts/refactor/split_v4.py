"""拆 3 模块: cases / clients / schedule
延续之前 split_v3.py 的方案 (顶层 function 声明)
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(r'E:\元枢法智前端\yuanxing')
src_file = ROOT / 'assets' / 'js' / 'script.js'
src = src_file.read_text(encoding='utf-8')
lines = src.split('\n')
total = len(lines)

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

MODULES = {
    'cases.js': [
        'filterCaseList', 'goToCasePage', 'archiveCase', 'editCaseTitle', 'finishEdit',
        'deleteCase', 'openNewCaseModal', 'closeNewCaseModal', 'submitNewCase',
        # 归档 (已移到 archive, 但 case 内的引用保留 main 函数作为 caller)
        'openArchiveDetail', 'restoreArchive', 'deleteArchive',
        # 字段编辑
        'getFieldValue', 'setFieldValue', 'renderEditForm', 'renderFieldInput',
        'editSection', 'closeEditSectionModal', 'saveEditSection',
        # 案件详情
        'openCaseDetail', 'switchCaseTab', 'switchMaterialsTab',
        # 证据目录 (case-detail 内的证据 tab)
        'addEvidenceCatalogItem', 'loadCatalogFileList', 'toggleCatalogFileSelect',
        'updateCatalogSelectedCount', 'closeAddEvidenceCatalogModal',
        'submitEvidenceCatalog', 'editCatalogItem', 'deleteCatalogItem',
        'aiCreateEvidenceCatalog',
        # 时间线
        'openAddTimelineModal', 'closeAddTimelineModal', 'submitTimeline',
        'deleteTimeline',
        # 证据材料/证件/合同/文书/委托
        'openUploadEvidenceModal', 'closeUploadEvidenceModal', 'submitEvidence',
        'deleteEvidence',
        'openUploadContractModal', 'closeUploadContractModal', 'submitContract',
        'deleteContract',
        'openUploadMaterialModal', 'closeUploadMaterialModal', 'submitMaterial',
        'deleteMaterial',
        'openUploadDocumentModal', 'closeUploadDocumentModal', 'submitDocument',
        'deleteDocument',
        # AI 侧栏 (案件)
        'switchAIPanel', 'switchEvidenceAIPanel',
        # 智能卷宗分析
        'openCaseAnalysis', 'backToCaseList',
    ],
    'clients.js': [
        'switchClientTab', 'openClientDetail', 'backToClientList',
        'showNewClientModal', 'closeNewClientModal', 'submitNewClient',
        'runNewClientConflictCheck', 'runConflictCheck',
    ],
    'schedule.js': [
        # 工作台待办
        'toggleTodo', 'editSchedule', 'deleteSchedule',
        # 案件动态
        'openCaseDynamicDetail', 'closeCaseDynamicDetail',
        'searchDynamics', 'selectDynamicType',
        'openNewDynamicModal', 'closeNewDynamicModal',
        'handleDynamicFileSelect', 'handleDynamicFileDrop',
        'addDynamicFile', 'removeDynamicFile', 'renderDynamicFilePreview',
        'escapeHtml', 'submitNewDynamic', 'switchDynamicsView',
        'renderDynamicsTimeline',
        # AI 一键提取 (move from main to clients?)  - 留在 clients
        # 工作台日程
        'openScheduleCalendar', 'markCalendarConflicts',
        # 日程相关
        'getTodayDate', 'getFutureDate', 'checkScheduleConflict',
        'checkAndShowConflict', 'bindScheduleConflictCheck',
        'openScheduleModal', 'closeScheduleModal', 'saveSchedule',
        'updateTodayScheduleBadge', 'filterSchedule', 'filterAttention',
        'filterDynamics',
        # 日程详情/冲突
        'openScheduleDetail', 'closeScheduleDetail', 'checkDetailConflict',
        'editScheduleFromDetail', 'deleteScheduleFromDetail',
        'showConflictResolve', 'closeConflictResolve', 'conflictResolveAction',
        'selectSuggestedSlot', 'suggestFreeSlots',
        'checkCourtConflicts', 'dismissCourtConflict',
        # 视图路由
        'switchToList', 'loadView',
    ],
}

# 收集每个模块的函数
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

# 验证 5 模块 + main 互斥
all_mod_funcs = set()
for items in module_items.values():
    for _, _, n in items:
        all_mod_funcs.add(n)
# 同时从其它 4 模块排除 (knowledge/ai/templates/account 已在主文件外)
# 检查冲突
duplicate = []
for n in all_mod_funcs:
    if n in ['applyKnowledgeFilter', 'switchKnowledgeMainTab', 'startCompile',
             'switchAITab', 'startNewChat', 'switchTemplateTab', 'fixTemplateViewDOM',
             'toggleNotifications', 'switchToSubscription', 'toggleBilling']:
        duplicate.append(n)
if duplicate:
    print(f'  CONFLICT: {duplicate}')

# 收集 main.js 保留的函数 (在 script.js 里)
main_items = [(s, e, n) for n, s in funcs.items() if n not in all_mod_funcs]
main_items.sort()

# 写模块
HEADERS = {
    'cases.js': '''/**
 * 案件管理模块 - 案件列表/详情/归档 + 9 个 case tab
 * 包含: 案件 CRUD + 字段编辑 + 案件详情 tab 切换 + 证据目录/时间线/证据/合同/委托/文书
 * 加载: 在 script.js 之前同步加载
 */
''',
    'clients.js': '''/**
 * 客户管理模块
 * 包含: 客户分类切换 + 详情页 + 新建/冲突检查
 * 加载: 在 script.js 之前同步加载
 */
''',
    'schedule.js': '''/**
 * 日程/工作台/案件动态模块
 * 包含: 日程 CRUD + 冲突检测 + 案件动态 + 工作台待办 + 庭审冲突预警
 * 加载: 在 script.js 之前同步加载
 */
''',
}

print('\n=== 写入模块 ===')
for name, items in module_items.items():
    out = ROOT / 'assets' / 'js' / name
    parts = [HEADERS[name], '']
    for s, e, n in items:
        body = '\n'.join(lines[s-1:e])
        parts.append(body)
        parts.append('')
    out.write_text('\n'.join(parts), encoding='utf-8')
    size_kb = out.stat().st_size / 1024
    print(f'  ✓ {name}: {size_kb:.1f} KB')

# 写主 script.js: 删除模块函数
print('\n=== 写主 script.js ===')
mod_line_ranges = []
for items in module_items.values():
    for s, e, _ in items:
        mod_line_ranges.append((s, e))
mod_line_ranges.sort()

delete = set()
for s, e in mod_line_ranges:
    for i in range(s, e + 1):
        delete.add(i)

new_lines = [l for i, l in enumerate(lines, 1) if i not in delete]

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
for f in ['cases.js', 'clients.js', 'schedule.js', 'script.js']:
    r = subprocess.run(['node', '--check', str(ROOT / 'assets' / 'js' / f)],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print(f'  ✓ {f}')
    else:
        print(f'  ✗ {f}: {r.stderr[:300]}')
