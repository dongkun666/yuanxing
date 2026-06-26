"""字号收敛 - 全项目 5 档体系
- text-[9px] / [10px] / [11px] → text-[10px] (保留为最小档, 1px 差异可忽略)
- text-[12px] → text-xs
- text-[13px] / [14px] → text-sm
- text-[15px] / [16px] / [17px] → text-base
- text-[18px] / [19px] / [20px] / [22px] → text-lg
- text-[24px] / [25px] / [28px] → text-xl
- text-[32px] / [36px] / [40px] → text-2xl
"""
import re
from pathlib import Path

ROOT = Path(r'E:\元枢法智前端\yuanxing')

# 收敛规则: (old_px, new_class)
# 注意: 顺序很关键, 必须先处理大值, 否则 20px 会被先匹配成 2 然后 xl
# 实际: 9/10/11 都映射到 10 (保留为 1 档, 用 arbitrary)
#       12 → xs (12)
#       13/14 → sm (14)
#       16 → base (16)
#       18/20/22 → lg (20, 跟 Tailwind 18 对应 lg)
#       24/28 → xl (24)
#       32 → 2xl (32)

# 用更精准的: 只映射那些「非主档」到「主档」, 已经在主档的不变
# 5 档主: 12/14/16/20/24 (与 Tailwind xs/sm/base/lg/xl 对齐)
# 32 → 2xl
# 10/11 → 收为 10 (保留最小档)
# 9 → 收为 10
# 13 → 收为 14 (sm) — 但 13 跟 14 视觉差别小
# 15/17 → 收为 14 (sm) 或 16 (base)
# 18 → 收为 20 (lg) — 2px 差
# 22/25/28 → 收为 24 (xl)
# 36/40 → 收为 32 (2xl)

# 简化: 用映射
SIZE_MAP = {
    '9': '10',  # → text-[10px]
    '11': '10', # → text-[10px]
    '13': '14', # → text-sm
    '15': '14', # → text-sm
    '17': '16', # → text-base
    '18': '20', # → text-lg
    '19': '20', # → text-lg
    '22': '20', # → text-lg
    '25': '24', # → text-xl
    '28': '24', # → text-xl
    '36': '32', # → text-2xl
    '40': '32', # → text-2xl
}

# 对应的 tailwind class
PIXEL_TO_CLASS = {
    '10': 'text-[10px]',  # 保留为最小档
    '12': 'text-xs',
    '14': 'text-sm',
    '16': 'text-base',
    '20': 'text-lg',
    '24': 'text-xl',
    '32': 'text-2xl',
}

# 构建最终映射: (text-[Npx] → final class)
MAPPING = {}
for from_px, to_px in SIZE_MAP.items():
    MAPPING[f'text-[{from_px}px]'] = PIXEL_TO_CLASS[to_px]
# 已经对齐的也要映射 (为了 tree-shake 一致性, 12/14/16/20/24/32)
# 实际上 12/14/16 这些已经是 Tailwind 命名前缀, 不必替换
# 但 text-[12px] 跟 text-xs 是同一渲染, 选短的 text-xs 更省字节
# 但替换会改变源文件可读性, 我保守只替换非主档
# (text-[10px] 保留 arbitrary, text-[12px] 跟 text-xs 同效, 12 是主档, 不必替换)
# 最终: 只替换 SIZE_MAP 里的

# 但 SIZE_MAP 包含 13/15/17/22 等会变成 text-sm/text-base/text-lg
# 注意 text-sm 是 14, 把 13 映射成 14 后会变 1px, 视觉影响小
# 但 text-[10px] 11/9 都被映射到 text-[10px] 不变

# 实施
total_files = 0
total_changes = 0
for f in (ROOT / 'templates').rglob('*.html'):
    c = f.read_text(encoding='utf-8', errors='ignore')
    orig = c
    for old, new in MAPPING.items():
        if old in c:
            c = c.replace(old, new)
    if c != orig:
        f.write_text(c, encoding='utf-8')
        # 统计
        for old in MAPPING:
            n = orig.count(old) - c.count(old)
            if n:
                total_changes += n
        total_files += 1

print(f'修改 {total_files} 个文件, {total_changes} 处替换')

# 输出最终使用统计
sizes = {}
for f in (ROOT / 'templates').rglob('*.html'):
    c = f.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'text-\[(\d+)px\]', c):
        s = m.group(1)
        sizes[s] = sizes.get(s, 0) + 1
print(f'\n收敛后剩余 arbitrary 字号: {sizes}')

# Tailwind 命名 class 数量
named = {'text-xs': 0, 'text-sm': 0, 'text-base': 0, 'text-lg': 0, 'text-xl': 0, 'text-2xl': 0}
for f in (ROOT / 'templates').rglob('*.html'):
    c = f.read_text(encoding='utf-8', errors='ignore')
    for k in named:
        named[k] += c.count(k)
print(f'命名 class 使用: {named}')
