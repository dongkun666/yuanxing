import re
from pathlib import Path
ROOT = Path(r'E:\元枢法智前端\yuanxing')
js = (ROOT / 'assets' / 'js' / 'script.js').read_text(encoding='utf-8')

# 5 个可疑函数
suspects = ['shareCase', 'openAIExtractModal', 'handleAvatarUpload', 'handleCertUpload', 'submitCertification']
for name in suspects:
    # 在 js 中去掉自己的定义行
    pattern = re.compile(r'function\s+' + re.escape(name) + r'\s*\([^)]*\)\s*\{[^{}]*\}', re.DOTALL)
    # 简化: 直接在 js 中搜索 函数名
    occ = re.findall(r'\b' + re.escape(name) + r'\b', js)
    # 找位置
    funcs = list(re.finditer(r'function\s+' + re.escape(name) + r'\s*\(', js))
    html_calls = []
    for f in (ROOT / 'templates').rglob('*.html'):
        c = f.read_text(encoding='utf-8', errors='ignore')
        for m in re.finditer(r'\b' + re.escape(name) + r'\b', c):
            ctx = c[max(0, m.start()-30):m.end()+30].replace('\n', ' ')
            html_calls.append(f'{f.name}: ...{ctx}...')
    print(f'\n=== {name} ===')
    print(f'  defined at L{funcs[0].start() if funcs else "?"} ({len(funcs)} defs)')
    print(f'  total JS occurrences: {len(occ)} (1 = definition only, > 1 = called)')
    if html_calls:
        print(f'  HTML calls:')
        for h in html_calls[:5]:
            print(f'    {h}')
    else:
        print(f'  HTML calls: NONE')
