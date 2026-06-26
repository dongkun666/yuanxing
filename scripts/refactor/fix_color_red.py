"""批量替换 #F53F3F → #F5222D"""
import re
from pathlib import Path

ROOT = Path(r'E:\元枢法智前端\yuanxing')
old_color = '#F53F3F'
new_color = '#F5222D'

total = 0
for f in (ROOT / 'templates').rglob('*.html'):
    c = f.read_text(encoding='utf-8')
    n = c.count(old_color)
    if n:
        c2 = c.replace(old_color, new_color)
        f.write_text(c2, encoding='utf-8')
        print(f'  {f.name}: {n} 处')
        total += n
for f in (ROOT / 'assets').rglob('*.css'):
    c = f.read_text(encoding='utf-8')
    n = c.count(old_color)
    if n:
        c2 = c.replace(old_color, new_color)
        f.write_text(c2, encoding='utf-8')
        print(f'  {f.name}: {n} 处')
        total += n

print(f'\n总计替换: {total} 处')
