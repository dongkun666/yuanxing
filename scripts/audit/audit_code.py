"""全面体检脚本"""
import os, re, json
from pathlib import Path

ROOT = Path(r'E:\元枢法智前端\yuanxing')

results = {
    'html_balance': [],
    'js_syntax': [],
    'html_issues': [],
    'tailwind_typos': [],
    'design_tokens': {},
    'a11y': [],
}

# ===== 1. HTML 平衡检查 =====
def check_html_balance(path):
    with open(path, 'rb') as f:
        content = f.read().decode('utf-8')
    # 只取 <body> 内的内容（如果有）
    opens = len(re.findall(r'<div\b', content))
    closes = content.count('</div>')
    if opens != closes:
        return (opens, closes, opens - closes)
    return None

for f in sorted((ROOT / 'templates' / 'views').glob('*.html')):
    bal = check_html_balance(f)
    if bal:
        results['html_balance'].append((f.name, bal[0], bal[1], bal[2]))

# 同样检查 modals.html
modals = ROOT / 'templates' / 'modals.html'
bal = check_html_balance(modals)
if bal:
    results['html_balance'].append(('modals.html', bal[0], bal[1], bal[2]))

# ===== 2. JS 语法检查 (简单 grep 检查未闭合花括号) =====
script = ROOT / 'assets' / 'js' / 'script.js'
with open(script, 'rb') as f:
    js = f.read().decode('utf-8')
# 统计花括号 (粗略)
brace_open = js.count('{')
brace_close = js.count('}')
paren_open = js.count('(')
paren_close = js.count(')')

results['js_syntax'] = {
    'file': 'script.js',
    'size_kb': len(js) // 1024,
    'lines': js.count('\n'),
    'braces': (brace_open, brace_open - brace_close),
    'parens': (paren_open, paren_open - paren_close),
}

# ===== 3. inline onclick 引用检查 =====
# 检查所有 onclick 调用的函数是否在 script.js 中定义
onclick_funcs = set()
for f in sorted((ROOT / 'templates').rglob('*.html')):
    with open(f, 'rb') as fp:
        c = fp.read().decode('utf-8')
    for m in re.finditer(r'onclick="([a-zA-Z_][a-zA-Z0-9_]*)\(', c):
        onclick_funcs.add(m.group(1))

# 从 script.js 找所有 function 声明
defined_funcs = set()
for m in re.finditer(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', js):
    defined_funcs.add(m.group(1))

# 缺定义
missing = onclick_funcs - defined_funcs - {'switchView', 'switchTemplateView'}  # 这俩可能动态生成
# 排除 window 全局函数 (alert, confirm)
missing -= {'alert', 'confirm'}

if missing:
    results['html_issues'].append(('missing_funcs', sorted(missing)))

# ===== 4. Tailwind 拼写 + 设计 token 检查 =====
# 收集所有用到的颜色 (bg-# / text-# / border-#)
color_pattern = re.compile(r'#([0-9A-Fa-f]{6})')
colors = set()
for f in sorted((ROOT / 'templates').rglob('*.html')):
    with open(f, 'rb') as fp:
        c = fp.read().decode('utf-8')
    for m in color_pattern.finditer(c):
        colors.add('#' + m.group(1).upper())

# 已知设计 token (LexPrime 主色)
design_tokens = {
    '#165DFF': '主蓝 (primary)',
    '#9333EA': '紫 (secondary)',
    '#FAAD14': '琥珀 (warning)',
    '#16A34A': '绿 (success)',
    '#FA8C16': '橙 (urgent)',
    '#F5222D': '红 (danger)',
    '#1D2129': '主文字',
    '#4E5969': '副文字',
    '#86909C': '次要文字',
    '#C9CDD4': '禁用',
    '#E5E6EB': '边框',
    '#F2F3F5': '背景灰',
    '#F7F8FA': '浅背景',
    '#FFFFFF': '白',
    '#FFF3E0': '浅琥珀',
    '#E8F3FF': '浅蓝',
    '#F2F5FF': '浅蓝2',
    '#FEF3C7': '浅黄',
}

# 找出 token 外的颜色
out_of_palette = colors - set(design_tokens.keys())
if out_of_palette:
    results['design_tokens']['out_of_palette'] = sorted(out_of_palette)
results['design_tokens']['used'] = sorted(colors)
results['design_tokens']['design_palette'] = design_tokens

# ===== 5. 找可能的拼写错误 (class 中常见 typo) =====
typo_patterns = [
    (r'fex-', '应该用 flex-'),
    (r'flex-col-', 'flex-col 后面只有数字'),  # e.g. flex-col-2 错误
    (r'hover:bg-#', 'hover:bg-# 需要在 [] 中'),
    (r'bg-\[#', 'OK'),
    (r'p-\d+\.\d+\.\d+', 'p-X.Y.Z 应该是 4 段数字'),
]

# ===== 6. 排版 / 间距 检查 =====
# 字号一致性: 12/14/16/20/24/32 等
# 找不一致 (e.g. text-[11px] text-[13px] 跟 12px 体系混)
text_sizes = set()
for f in sorted((ROOT / 'templates').rglob('*.html')):
    with open(f, 'rb') as fp:
        c = fp.read().decode('utf-8')
    for m in re.finditer(r'text-\[(\d+)px\]', c):
        text_sizes.add(int(m.group(1)))

results['design_tokens']['text_sizes_used'] = sorted(text_sizes)

# ===== 7. JS function 总数 + 死代码检测 =====
funcs_defined = list(defined_funcs)
results['js_syntax']['funcs_defined_count'] = len(funcs_defined)
results['js_syntax']['funcs_used_in_html'] = len(onclick_funcs)
results['js_syntax']['funcs_defined_but_not_used'] = sorted(defined_funcs - onclick_funcs - {
    'switchView', 'switchTemplateView', '_init', 'loadView',  # 框架核心
})

# 输出
print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
