"""扫描 script.js 的所有 function, 映射到模块"""
import re
from pathlib import Path

p = Path(r'E:\元枢法智前端\yuanxing\assets\js\script.js')
c = p.read_text(encoding='utf-8')

# 1. 找所有 function name + 行号
# function NAME(...) 或 async function NAME
funcs = []
for m in re.finditer(r'function\s+(\w+)\s*\(', c):
    name = m.group(1)
    line = c[:m.start()].count('\n') + 1
    funcs.append((line, name))

# 2. 看代码里大的注释块, 提取主题
# 找 // ===== XXX ===== 这种分割
sections = []
for m in re.finditer(r'(//\s*=+\s*[^\n]*=+\s*\n)', c):
    line = c[:m.start()].count('\n') + 1
    title = m.group(1).strip().replace('//', '').replace('=', '').strip()
    sections.append((line, title))

# 3. 找 var/const 状态
vars = []
for m in re.finditer(r'^\s*(?:var|let|const)\s+(\w+)\s*=', c, re.MULTILINE):
    name = m.group(1)
    line = c[:m.start()].count('\n') + 1
    if not name.startswith('_') and name[0].islower() and len(name) < 30:
        vars.append((line, name))

# 4. 找 紧跟着的注释 // XXX - xxx 模式
fcomments = {}
for i, (line, name) in enumerate(funcs):
    # 向前看最多 5 行找注释
    lines = c.split('\n')
    for j in range(max(0, line-5), line):
        m = re.match(r'\s*//\s*(.+)$', lines[j])
        if m:
            fcomments[name] = (j+1, m.group(1).strip())

print(f'总 function: {len(funcs)}')
print(f'总 section: {len(sections)}')
print(f'总 var: {len(vars)}')

# 5. 找 onclick 在 HTML 中调用哪些
ROOT = Path(r'E:\元枢法智前端\yuanxing')
html_calls = {}
for f in (ROOT / 'templates').rglob('*.html'):
    c2 = f.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'onclick="([^"]+)"', c2):
        code = m.group(1)
        for name_match in re.finditer(r'\b(\w+)\s*\(', code):
            fname = name_match.group(1)
            if fname not in ('if', 'for', 'while', 'function'):
                html_calls.setdefault(fname, []).append(f.name)

# 6. 输出 function + 注释 + 哪个 view 调
print('\n=== Functions ===')
for line, name in funcs:
    comment = fcomments.get(name, (None, ''))[1]
    views = set(html_calls.get(name, []))
    views_str = ','.join(v.replace('.html', '') for v in views) if views else '-'
    print(f'  L{line:4d} {name:35s} | {comment[:40]:40s} | used: {views_str}')

# 7. 大区块
print('\n=== Sections ===')
for line, title in sections:
    print(f'  L{line:4d} {title}')
