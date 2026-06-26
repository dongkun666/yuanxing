"""把 script.js 拆成 4 模块 + 1 main
- knowledge.js: 知识库 (L1443-1620)
- ai.js: AI 对话 + 提取 (L605-838 + L4104-4130)
- templates.js: 模板管理 (L1810-2397)
- account.js: 账号/会员/支付/通知 (L839-1442)
- script.js (main): 案件/客户/日程/弹窗/批量/路由
"""
import re
from pathlib import Path

ROOT = Path(r'E:\元枢法智前端\yuanxing')
src_file = ROOT / 'assets' / 'js' / 'script.js'
src = src_file.read_text(encoding='utf-8')
lines = src.split('\n')
total = len(lines)
print(f'总行数: {total}')

# 1. 找到每个模块边界 (注释标题)
# 知识库从 L1443 switchClientTab 之后开始 (注意 switchClientTab 不在知识库!)
# 实际知识库 section 是 "知识库管理 - 搜索" 注释
# 让我搜索注释标题位置

# 用 regex 找带标题的注释
section_re = re.compile(r'^\s*(//\s*[#=\s]*[\u4e00-\u9fff].*?)$', re.MULTILINE)
markers = []
for m in section_re.finditer(src):
    line = src[:m.start()].count('\n') + 1
    title = m.group(1).strip().lstrip('/').strip().lstrip('=').strip()
    if title:
        markers.append((line, title))

# 输出关键标题 (筛特定关键词)
keywords = ['知识库', '模板', '账号', '会员', '支付', '订阅', 'AI 对话', 'AI 一键', 'AI 提取', 'AI 视图', '历史', '通知', '案件归档', '归档管理']
print('\n=== 关键 section 位置 ===')
for line, title in markers:
    if any(k in title for k in keywords):
        print(f'  L{line:4d} {title[:60]}')
