"""把 script.js 拆成模块
- main.js (保留) - 案件 + 客户 + 日程 + 路由 + 弹窗
- knowledge.js (新) - 知识库 LLM Wiki 3 Tab + 搜索 + 编译 (L1443-1620)
- ai.js (新) - AI 对话 + 历史 + 侧栏 + AI 一键提取 (L635-790 + L4104-4130)
- templates.js (新) - 模板管理 (L1810-2400)
- batch.js (新) - 批量上传 + 附件 (L4131-4207)
- account.js (新) - 账号/会员/支付 (L893-1380)
"""
import re
from pathlib import Path

ROOT = Path(r'E:\元枢法智前端\yuanxing')
src = (ROOT / 'assets' / 'js' / 'script.js').read_text(encoding='utf-8')
lines = src.split('\n')

# 每个模块的起止行号 (1-based, 含) - 基于 func_map.txt 分析
MODULES = {
    'account.js':    (893, 1438),    # 会员中心 + 账号设置 + 支付 + 通知
    'ai.js':         (605,  838),    # AI 对话 + 历史 + 侧栏
    'knowledge.js':  (1443, 1620),   # 知识库 LLM Wiki + 搜索
    'templates.js':  (1810, 2397),   # 模板管理
    'batch.js':      (4131, 4207),   # 批量上传 + AI 提取弹窗
}

# 主文件保留: 0-892, 838-1442, 1620-1809, 2397-4130, 4207-4355
# 但实际跨边界要小心: 我们用「包含函数完整定义」原则

# 重写为更准确的边界
# 重要: 边界必须包含完整的 function 定义, 不能切到一半

# 重新分析: 用 function 起始行定位
# - L1605 switchView
# - L1620 switchSidebarTab
# - L1630 switchAITab
# - L1635 startNewChat
# - L1765 filterHistory
# - L1775 switchAIView
# - L1786 switchAIViewSubView
# - L1801 selectAIHistory
# - L1827 filterAIHistory
# - L1841 toggleMoreMenu
# - L1874 handleMoreAction
# - L1896 toggleNotifications
# - L1903 markAllNotifications
# - L1915 toggleUserMenu
# - L1927 switchToSubscription
# - L1960 toggleBilling
# - L1999 showPayment
# - L2038 backToSubscription
# - L2048 selectPaymentMethod
# - L2074 paySuccess
# - L2112 goToSubscription
# - L2116 goToWorkstation
# - L2121 switchToOrders
# - L2128 switchToMemberCenter
# - L2133 goToMemberCenter
# - L2138 switchToAccountSettings
# - L2145 toggleProfileEdit
# - L2166 cancelProfileEdit
# - L2181 saveProfile
# - L2279 showSaveSuccess
# - L2299 addTagInput
# - L2311 handleAvatarUpload
# - L2366 removeTag
# - L2374 showAddTagDialog
# - L2385 removeCertFile
# - L2393 toggle2FA
# - L2413 showDeviceManager
# - L2431 confirmAccountDeletion

# AI 部分: L1635-1893 (startNewChat 到 handleMoreAction 结束)
# Account 部分: L1896-2450 (toggleNotifications 到 confirmAccountDeletion 结束)
# 知识库: L2455-2582 (switchClientTab 之后到 knowledge 相关)
# 模板: L2617-3230 (switchTemplateTab 到 templates 相关)
# 批量: L4959-5035 (openBatchUploadModal 到 confirmBatchUpload)

# 太复杂, 实际用更宽松的范围, 然后用「复制整段 + 引用 + 注释」方式
# 不用拆, 而是用 lazy load?

# 简单方案: 用 <script type="module"> + 直接 import, 但浏览器需要 HTTP
# 而当前是 file:// 或 8080, 都支持

# 进一步简化方案: **拆成 5 个 .js 文件 + 主 .js 变 main.js 引用**
# 每个 .js 用 IIFE 包装, 把函数挂到 window.LP 全局命名空间
# main.js 启动时按需调用, 或直接同步

# 我先做模块边界提取, 再写每个文件
print('OK 计划: 5 modules + main')
