"""收 design token 到 knowledge.html (保持 LF 行尾)"""
import re
from pathlib import Path

ROOT = Path(r'E:\元枢法智前端\yuanxing')
p = ROOT / 'templates' / 'views' / 'knowledge.html'
# read_text 走 universal newlines: CRLF → LF
text = p.read_text(encoding='utf-8')

replacements = [
    ('bg-[#165DFF]', 'bg-brand'),
    ('hover:bg-[#165DFF]', 'hover:bg-brand'),
    ('text-[#165DFF]', 'text-brand'),
    ('hover:text-[#165DFF]', 'hover:text-brand'),
    ('border-[#165DFF]', 'border-brand'),
    ('bg-[#4080FF]', 'bg-brand-hover'),
    ('hover:bg-[#4080FF]', 'hover:bg-brand-hover'),
    ('bg-[#E8F3FF]', 'bg-brand-tint'),
    ('bg-[#EEF3FF]', 'bg-brand-tint2'),
    ('bg-[#F2F7FF]', 'bg-brand-tint3'),
    ('bg-[#E5EBFF]', 'bg-brand-tint4'),
    ('hover:bg-[#E5EBFF]', 'hover:bg-brand-tint4'),
    ('text-[#1D2129]', 'text-fg-primary'),
    ('text-[#4E5969]', 'text-fg-secondary'),
    ('text-[#86909C]', 'text-fg-tertiary'),
    ('text-[#C9CDD4]', 'text-fg-disabled'),
    ('bg-[#F2F3F5]', 'bg-bg'),
    ('bg-[#F7F8FA]', 'bg-bg-subtle'),
    ('hover:bg-[#F7F8FA]', 'hover:bg-bg-subtle'),
    ('border-[#E5E6EB]', 'border-bg-border'),
    ('text-[#16A34A]', 'text-success'),
    ('text-green-600', 'text-success'),
    ('text-[#FAAD14]', 'text-urgent'),
    ('text-[#FA8C16]', 'text-urgent'),
    ('text-[#F5222D]', 'text-danger'),
    ('bg-[#FFF3E0]', 'bg-urgent-tint'),
    ('text-[#9333EA]', 'text-wiki'),
    ('text-purple-600', 'text-wiki'),
    ('bg-[#F2F5FF]', 'bg-brand-tint2'),
]

count = 0
for old, new in replacements:
    n = text.count(old)
    if n:
        text = text.replace(old, new)
        count += n
        print(f'  {old} → {new}: {n}')

# Sparkline 缩窄 + nowrap
text = text.replace(
    '<svg class="overflow-visible" viewBox="0 0 64 24"',
    '<svg class="overflow-visible w-14 h-5" viewBox="0 0 64 24"'
)
patterns = [
    ('<p class="text-[10px] text-success">↑ 7 天 +3</p>', '<p class="text-[10px] text-success whitespace-nowrap">↑ 7 天 +3</p>'),
    ('<p class="text-[10px] text-wiki">由 LLM 维护</p>', '<p class="text-[10px] text-wiki whitespace-nowrap">由 LLM 维护</p>'),
    ('<p class="text-[10px] text-urgent">● 2 个待补</p>', '<p class="text-[10px] text-urgent whitespace-nowrap">● 2 个待补</p>'),
    ('<p class="text-[10px] text-danger">● 1 项紧急</p>', '<p class="text-[10px] text-danger whitespace-nowrap">● 1 项紧急</p>'),
]
for old, new in patterns:
    if old in text:
        text = text.replace(old, new)

# 用 write_text 写回 + newline='' 保持 LF
# 但要确保 LF 不被 Windows 改成 CRLF
# Python write_text 默认 newline=None 用 os.linesep (Windows=CRLF)
# 显式 newline='' 保持原样
with open(p, 'w', encoding='utf-8', newline='') as f:
    f.write(text)
print(f'\n总计替换: {count} 处')

# div 平衡
opens = len(re.findall(r'<div\b', text))
closes = text.count('</div>')
print(f'div 平衡: {opens} / {closes}')
