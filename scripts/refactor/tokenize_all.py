"""tokenize 全 view (除 knowledge.html 已经处理过)
保留 LF 行尾 (用 newline='' 显式)
"""
import re
from pathlib import Path

ROOT = Path(r'E:\元枢法智前端\yuanxing')

# 颜色映射 (arbitrary value → 命名 token)
# 完整版 (含 knowledge 替换过的)
REPLACEMENTS = [
    # ===== 主品牌 =====
    ('bg-[#165DFF]', 'bg-brand'),
    ('hover:bg-[#165DFF]', 'hover:bg-brand'),
    ('text-[#165DFF]', 'text-brand'),
    ('hover:text-[#165DFF]', 'hover:text-brand'),
    ('border-[#165DFF]', 'border-brand'),
    ('focus:border-[#165DFF]', 'focus:border-brand'),
    ('focus:ring-[#165DFF]', 'focus:ring-brand'),

    # 蓝变体
    ('bg-[#4080FF]', 'bg-brand-hover'),
    ('hover:bg-[#4080FF]', 'hover:bg-brand-hover'),
    ('bg-[#0E4AD8]', 'bg-brand-active'),
    ('hover:bg-[#0E4AD8]', 'hover:bg-brand-active'),

    # 浅蓝背景
    ('bg-[#E8F3FF]', 'bg-brand-tint'),
    ('hover:bg-[#E8F3FF]', 'hover:bg-brand-tint'),
    ('bg-[#EEF3FF]', 'bg-brand-tint2'),
    ('hover:bg-[#EEF3FF]', 'hover:bg-brand-tint2'),
    ('bg-[#F2F7FF]', 'bg-brand-tint3'),
    ('bg-[#E5EBFF]', 'bg-brand-tint4'),
    ('hover:bg-[#E5EBFF]', 'hover:bg-brand-tint4'),
    ('bg-[#F2F5FF]', 'bg-brand-tint2'),
    ('hover:bg-[#F2F5FF]', 'hover:bg-brand-tint2'),
    ('bg-[#D6E4FF]', 'bg-brand-tint4'),

    # 文字色
    ('text-[#1D2129]', 'text-fg-primary'),
    ('hover:text-[#1D2129]', 'hover:text-fg-primary'),
    ('text-[#4E5969]', 'text-fg-secondary'),
    ('hover:text-[#4E5969]', 'hover:text-fg-secondary'),
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
    ('hover:text-green-600', 'hover:text-success'),
    ('bg-[#16A34A]', 'bg-success'),
    ('text-[#FAAD14]', 'text-urgent'),
    ('bg-[#FAAD14]', 'bg-urgent'),
    ('text-[#FA8C16]', 'text-urgent'),
    ('bg-[#FA8C16]', 'bg-urgent'),
    ('text-[#F5222D]', 'text-danger'),
    ('hover:text-[#F5222D]', 'hover:text-danger'),
    ('border-[#F5222D]', 'border-danger'),
    ('text-[#FF7D00]', 'text-warning'),
    ('bg-[#FFF3E0]', 'bg-urgent-tint'),
    ('bg-[#FFF7E6]', 'bg-warning-tint'),
    ('bg-[#FFF1F0]', 'bg-danger-tint'),

    # 业务色
    ('text-[#9333EA]', 'text-wiki'),
    ('hover:text-[#9333EA]', 'hover:text-wiki'),
    ('text-purple-600', 'text-wiki'),
    ('bg-[#9333EA]', 'bg-wiki'),
    ('bg-[#F5EBFF]', 'bg-wiki-tint'),

    # AI 业务色
    ('text-[#6C5CE7]', 'text-ai'),
    ('bg-[#6C5CE7]', 'bg-ai'),
    ('bg-[#EDEBFF]', 'bg-ai-tint'),

    # 微信绿
    ('bg-[#07C160]', 'bg-wechat'),

    # 文字色特殊 (Tailwind 默认色)
    ('text-blue-700', 'text-brand'),
    ('text-blue-600', 'text-brand'),
    ('text-blue-500', 'text-brand'),
    ('bg-blue-50', 'bg-brand-tint3'),
    ('bg-blue-100', 'bg-brand-tint'),
    ('bg-blue-700', 'bg-brand'),
    ('hover:bg-blue-700', 'hover:bg-brand'),
    ('text-green-700', 'text-success'),
    ('bg-green-100', 'bg-success-tint'),
    ('text-gray-700', 'text-fg-primary'),
    ('text-gray-600', 'text-fg-secondary'),
    ('text-gray-500', 'text-fg-tertiary'),
    ('text-gray-400', 'text-fg-tertiary'),
    ('hover:text-gray-700', 'hover:text-fg-primary'),
    ('hover:text-gray-500', 'hover:text-fg-secondary'),
    ('hover:text-gray-400', 'hover:text-fg-tertiary'),
    ('text-gray-800', 'text-fg-primary'),
    ('bg-gray-100', 'bg-bg'),
    ('hover:bg-gray-100', 'hover:bg-bg'),
    ('bg-gray-200', 'bg-bg-border'),
    ('border-gray-200', 'border-bg-border'),
    ('border-gray-300', 'border-bg-border'),
    ('bg-white', 'bg-white'),  # 保留 white

    # 状态语义色 (Tailwind 默认 → token)
    ('text-orange-600', 'text-warning'),
    ('bg-orange-50', 'bg-warning-tint'),
    ('bg-orange-100', 'bg-warning-tint'),
    ('text-amber-600', 'text-urgent'),

    # 紫色
    ('text-purple-700', 'text-wiki'),
    ('bg-purple-100', 'bg-wiki-tint'),
]

# 处理的文件
ALL_VIEWS = [
    'ai.html', 'attention-list.html', 'case-analysis.html', 'case-detail.html',
    'case-dynamics.html', 'case-list.html', 'client-detail.html', 'client.html',
    'member-center.html', 'orders.html', 'payment-success.html', 'payment.html',
    'schedule-calendar.html', 'schedule-list.html', 'subscription.html',
    'template.html', 'workstation.html',
    'archive.html', 'attachment-list.html', 'account-settings.html', 'modals.html',
]

total_files = 0
total_changes = 0
for fname in ALL_VIEWS:
    p = ROOT / 'templates' / fname if (ROOT / 'templates' / fname).exists() else ROOT / 'templates' / 'views' / fname
    if not p.exists():
        print(f'  SKIP: {fname} not found')
        continue
    text = p.read_text(encoding='utf-8')
    orig = text
    file_changes = 0
    for old, new in REPLACEMENTS:
        if old in text:
            n = text.count(old)
            text = text.replace(old, new)
            file_changes += n
    if text != orig:
        # LF-safe write
        with open(p, 'w', encoding='utf-8', newline='') as fp:
            fp.write(text)
        total_files += 1
        total_changes += file_changes
        print(f'  ✓ {fname}: {file_changes} 处')

print(f'\n总计: {total_files} 文件, {total_changes} 处替换')
