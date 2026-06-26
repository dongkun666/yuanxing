"""拆 script.js 为 5 文件 (4 modules + main)
策略: 用函数名 + 行号做精准分块
"""
import re
from pathlib import Path

ROOT = Path(r'E:\元枢法智前端\yuanxing')
src_file = ROOT / 'assets' / 'js' / 'script.js'
src = src_file.read_text(encoding='utf-8')
lines = src.split('\n')
total = len(lines)

# 找每个 function 起始行
func_re = re.compile(r'^\s*function\s+(\w+)\s*\(', re.MULTILINE)
funcs = {}
for m in func_re.finditer(src):
    name = m.group(1)
    line = src[:m.start()].count('\n') + 1
    funcs[name] = line
funcs_sorted = sorted(funcs.items(), key=lambda x: x[1])

# 模块函数表 (按主题)
MODULES = {
    'knowledge.js': [
        'applyKnowledgeFilter',
        'switchKnowledgeMainTab',
        'startCompile', 'cancelCompile', 'recompile',
        'viewCompileProgress', 'viewWikiPages', 'runLintNow',
        'simulateUpload',
    ],
    'ai.js': [
        'switchAITab', 'startNewChat', 'selectHistory', 'filterHistory',
        'switchAIView', 'switchAIViewSubView', 'selectAIHistory', 'filterAIHistory',
        'toggleMoreMenu', 'handleMoreAction',
        # AI 一键提取
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
        # 通知
        'toggleNotifications', 'markAllNotifications', 'toggleUserMenu',
        # 会员 / 支付
        'switchToSubscription', 'toggleBilling', 'showPayment',
        'backToSubscription', 'selectPaymentMethod', 'paySuccess', 'getCurrentPaymentInfo',
        'goToSubscription', 'goToWorkstation', 'switchToOrders', 'switchToMemberCenter',
        'goToMemberCenter', 'switchToAccountSettings',
        # 账号设置
        'toggleProfileEdit', 'cancelProfileEdit', 'saveProfile', 'showSaveSuccess',
        'addTagInput', 'handleAvatarUpload', 'removeTag', 'showAddTagDialog',
        'removeCertFile', 'toggle2FA', 'showDeviceManager', 'confirmAccountDeletion',
        # 自动保存
        'autoSaveProfile', 'validateField', 'validateEmail',
        # 通知设置 + 第三方账号
        'saveNotificationSettings', 'bindAccount', 'unbindAccount',
    ],
}

# 计算每个模块的行号范围
# 起始 = 第一个函数 (往前找最近的注释)
# 结束 = 最后一个函数 (往下找下一个模块的第一个函数)
all_module_funcs = set()
for fnames in MODULES.values():
    all_module_funcs.update(fnames)

# 给每个模块排序函数
module_ranges = {}
for mod_name, fnames in MODULES.items():
    fl = sorted([funcs[f] for f in fnames if f in funcs])
    if not fl:
        print(f'  WARN: {mod_name} 无函数')
        continue
    start = fl[0]
    end = fl[-1]
    # 找 end 函数的右括号配对结束行
    end_brace = end
    depth = 0
    for i in range(end - 1, total):
        line = lines[i]
        depth += line.count('{') - line.count('}')
        if depth == 0 and i >= end - 1:
            end_brace = i + 1
            break
    module_ranges[mod_name] = (start, end_brace)
    print(f'  {mod_name}: L{start} - L{end_brace} ({end_brace-start+1} 行, {len(fnames)} 函数)')

# 验证
print('\n=== 模块函数总览 ===')
for mod, (s, e) in module_ranges.items():
    funcs_in_mod = [n for n, l in funcs_sorted if s <= l <= e]
    print(f'\n  {mod} (L{s}-L{e}, {len(funcs_in_mod)} 函数):')
    for n in funcs_in_mod[:8]:
        print(f'    L{funcs[n]:4d} {n}')
    if len(funcs_in_mod) > 8:
        print(f'    ... +{len(funcs_in_mod)-8} more')
