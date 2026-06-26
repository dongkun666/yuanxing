"""字号收敛 (保持 LF 行尾)"""
import re
from pathlib import Path

ROOT = Path(r'E:\元枢法智前端\yuanxing')

SIZE_MAP = {
    '9': '10', '11': '10',
    '13': '14', '15': '14',
    '17': '16',
    '18': '20', '19': '20', '22': '20',
    '25': '24', '28': '24',
    '36': '32', '40': '32',
}

PIXEL_TO_CLASS = {
    '10': 'text-[10px]',
    '12': 'text-xs',
    '14': 'text-sm',
    '16': 'text-base',
    '20': 'text-lg',
    '24': 'text-xl',
    '32': 'text-2xl',
}

MAPPING = {f'text-[{from_px}px]': PIXEL_TO_CLASS[to_px] for from_px, to_px in SIZE_MAP.items()}

total_files = 0
total_changes = 0
for f in (ROOT / 'templates').rglob('*.html'):
    # read_text 走 universal newlines (CRLF → LF)
    text = f.read_text(encoding='utf-8')
    orig = text
    for old, new in MAPPING.items():
        if old in text:
            text = text.replace(old, new)
    if text != orig:
        # 用 newline='' 显式保持 LF
        with open(f, 'w', encoding='utf-8', newline='') as fp:
            fp.write(text)
        for old in MAPPING:
            n = orig.count(old) - text.count(old)
            if n:
                total_changes += n
        total_files += 1

print(f'修改 {total_files} 个文件, {total_changes} 处替换')

# 验证所有 html 文件行尾都是 LF
crlf_files = 0
for f in (ROOT / 'templates').rglob('*.html'):
    b = f.read_bytes()
    if b'\r\n' in b:
        crlf_files += 1
        print(f'  WARN: {f.name} 仍有 CRLF')
print(f'\n有 CRLF 的文件: {crlf_files}')

# 输出统计
sizes = {}
for f in (ROOT / 'templates').rglob('*.html'):
    text = f.read_text(encoding='utf-8')
    for m in re.finditer(r'text-\[(\d+)px\]', text):
        s = m.group(1)
        sizes[s] = sizes.get(s, 0) + 1
print(f'剩余 arbitrary 字号: {sizes}')

named = {'text-xs': 0, 'text-sm': 0, 'text-base': 0, 'text-lg': 0, 'text-xl': 0, 'text-2xl': 0}
for f in (ROOT / 'templates').rglob('*.html'):
    text = f.read_text(encoding='utf-8')
    for k in named:
        named[k] += text.count(k)
print(f'命名 class: {named}')
