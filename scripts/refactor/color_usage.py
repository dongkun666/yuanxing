"""统计每个「out of palette」颜色的使用次数"""
import re
from pathlib import Path

ROOT = Path(r'E:\元枢法智前端\yuanxing')

# 关注的非 token 颜色
oop_colors = [
    '#07C160', '#0E4AD8', '#1677FF', '#3370FF', '#4080FF', '#5B8FF9',
    '#6C5CE7', '#D6E4FF', '#E5EBFF', '#E6000F', '#EEF3FF', '#F2F7FF',
    '#F53F3F', '#FFF1F0', '#FFF7E6',
]

# 统计每个颜色的使用次数 (跨所有 html/css)
usage = {}
for color in oop_colors:
    count = 0
    files = set()
    for f in (ROOT / 'templates').rglob('*.html'):
        c = f.read_text(encoding='utf-8')
        n = c.count(color)
        if n > 0:
            count += n
            files.add(f.name)
    for f in (ROOT / 'assets').rglob('*.css'):
        c = f.read_text(encoding='utf-8')
        n = c.count(color)
        if n > 0:
            count += n
            files.add(f.name)
    usage[color] = (count, len(files))

# 按使用次数排序
for color, (count, nfiles) in sorted(usage.items(), key=lambda x: -x[1][0]):
    print(f'{color}: {count} 次 in {nfiles} 文件')

# 提取每个颜色第一次出现的前后文 (判断是否值得归并)
print('\n=== 代表性使用 (前 5 个使用) ===')
for color in ['#4080FF', '#1677FF', '#F53F3F', '#E5EBFF', '#3370FF', '#FFF7E6']:
    print(f'\n--- {color} ---')
    for f in (ROOT / 'templates').rglob('*.html'):
        c = f.read_text(encoding='utf-8')
        if color in c:
            idx = c.find(color)
            ctx = c[max(0, idx-50):idx+50]
            print(f'  {f.name}: ...{ctx}...')
            break
