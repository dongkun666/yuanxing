"""把 knowledge.html 里的 arbitrary value 替换为命名 token"""
import re
from pathlib import Path

ROOT = Path(r'E:\元枢法智前端\yuanxing')
p = ROOT / 'templates' / 'views' / 'knowledge.html'
content = p.read_text(encoding='utf-8')
orig = content

# 颜色映射 (arbitrary value → 命名 class)
# 注意: 必须用 \ 转义 - 和 # 因为 Tailwind class 不允许裸的
# 实际上 Tailwind 的 class 名是 bg-[#165DFF] 这种,我们要替换为 bg-brand 或 bg-brand-hover
# 但 Tailwind 编译后的 class 是 .bg-brand
# 所以 HTML 里要写 class="bg-brand" 而不是 class="bg-[#brand]"

replacements = [
    # 主品牌
    ('bg-[#165DFF]', 'bg-brand'),
    ('hover:bg-[#165DFF]', 'hover:bg-brand'),
    ('text-[#165DFF]', 'text-brand'),
    ('hover:text-[#165DFF]', 'hover:text-brand'),
    ('border-[#165DFF]', 'border-brand'),

    # 蓝变体
    ('bg-[#4080FF]', 'bg-brand-hover'),
    ('hover:bg-[#4080FF]', 'hover:bg-brand-hover'),

    # 浅蓝背景
    ('bg-[#E8F3FF]', 'bg-brand-tint'),
    ('bg-[#EEF3FF]', 'bg-brand-tint2'),
    ('bg-[#F2F7FF]', 'bg-brand-tint3'),
    ('bg-[#E5EBFF]', 'bg-brand-tint4'),
    ('hover:bg-[#E5EBFF]', 'hover:bg-brand-tint4'),

    # 文字色 (主文字系列)
    ('text-[#1D2129]', 'text-fg-primary'),
    ('text-[#4E5969]', 'text-fg-secondary'),
    ('text-[#86909C]', 'text-fg-tertiary'),
    ('text-[#C9CDD4]', 'text-fg-disabled'),

    # 背景/边框
    ('bg-[#F2F3F5]', 'bg-bg'),
    ('bg-[#F7F8FA]', 'bg-bg-subtle'),
    ('hover:bg-[#F7F8FA]', 'hover:bg-bg-subtle'),
    ('border-[#E5E6EB]', 'border-bg-border'),

    # 状态色
    ('text-[#16A34A]', 'text-success'),
    ('text-green-600', 'text-success'),
    ('text-[#FAAD14]', 'text-urgent'),  # amber
    ('text-[#FA8C16]', 'text-urgent'),
    ('text-[#F5222D]', 'text-danger'),
    ('bg-[#FFF3E0]', 'bg-urgent-tint'),

    # 业务色
    ('text-[#9333EA]', 'text-wiki'),
    ('text-purple-600', 'text-wiki'),
    ('bg-[#F2F5FF]', 'bg-brand-tint2'),  # 主蓝 tab active 态

    # 主题统计卡 tint
    ('text-[#FAAD14]', 'text-urgent'),  # amber
    ('bg-[#FAAD14]', 'bg-urgent'),  # 修正: amber 是 #FAAD14, 收为 urgent
]

count = 0
for old, new in replacements:
    n = content.count(old)
    if n:
        content = content.replace(old, new)
        count += n
        print(f'  {old} → {new}: {n} 处')

print(f'\n总计替换: {count} 处')

# 写回
p.write_text(content, encoding='utf-8')
print('已写回 knowledge.html')

# 验证 div 平衡
import re
opens = len(re.findall(r'<div\b', content))
closes = content.count('</div>')
print(f'div 平衡: {opens} / {closes}')
