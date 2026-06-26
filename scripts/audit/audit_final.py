"""生成完整体检报告"""
import re
import json
from pathlib import Path

ROOT = Path(r'E:\元枢法智前端\yuanxing')

report = {
    '扫描范围': {},
    'HTML 平衡': [],
    'JS 语法': {},
    '缺失函数': [],
    '设计 Token 偏离': [],
    '未使用函数 (死代码)': [],
    '总览': '',
}

# 1. 扫描范围
htmls = list((ROOT / 'templates').rglob('*.html'))
report['扫描范围'] = {
    'HTML 文件': len(htmls),
    '总 HTML 行数': sum(len(open(f, 'rb').read().decode('utf-8', errors='ignore').split('\n')) for f in htmls),
    'script.js 大小 (KB)': (ROOT / 'assets' / 'js' / 'script.js').stat().st_size // 1024,
    'styles.css 大小 (KB)': (ROOT / 'assets' / 'css' / 'styles.css').stat().st_size // 1024,
}

# 2. HTML 平衡
for f in htmls:
    c = f.read_text(encoding='utf-8', errors='ignore')
    opens = len(re.findall(r'<div\b', c))
    closes = c.count('</div>')
    if opens != closes:
        report['HTML 平衡'].append({'file': f.relative_to(ROOT).as_posix(), 'opens': opens, 'closes': closes, 'diff': opens - closes})

# 3. JS
js = (ROOT / 'assets' / 'js' / 'script.js').read_text(encoding='utf-8')
report['JS 语法'] = {
    'file': 'assets/js/script.js',
    'size_kb': len(js) // 1024,
    'lines': js.count('\n'),
    'function 数': len(re.findall(r'function\s+[a-zA-Z_]', js)),
}

# 4. 缺失函数 (onclick 调用但 script.js 未定义)
onclick_calls = set()
for f in htmls:
    c = f.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'onclick="([a-zA-Z_][a-zA-Z0-9_]*)\(', c):
        onclick_calls.add(m.group(1))

defined = set()
for m in re.finditer(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', js):
    defined.add(m.group(1))

# 排除框架核心 + 全局
excluded = {'switchView', 'switchTemplateView', 'alert', 'confirm'}
missing = onclick_calls - defined - excluded
# 排除可能的 if 误报
missing = {f for f in missing if not f.startswith('if') and len(f) > 1}
if missing:
    report['缺失函数'] = sorted(missing)

# 5. 设计 token 偏离 (合理衍生)
all_colors = set()
for f in htmls:
    c = f.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'#([0-9A-Fa-f]{6})', c):
        all_colors.add('#' + m.group(1).upper())

palette = {'#165DFF', '#9333EA', '#FAAD14', '#16A34A', '#FA8C16', '#F5222D',
           '#1D2129', '#4E5969', '#86909C', '#C9CDD4', '#E5E6EB',
           '#F2F3F5', '#F7F8FA', '#FFFFFF', '#FFF3E0', '#E8F3FF', '#F2F5FF'}
oop = sorted(all_colors - palette)
report['设计 Token 偏离'] = oop

# 6. 未使用函数 (粗筛: 不被 onclick 调用)
# 注意: 也包括被动态调用的，需要排除
unused = defined - onclick_calls
# 排除可能是动态调用 / 事件监听
# 太严格的 dead code 容易误报, 仅列最确定的
def is_likely_event_handler(name):
    return name.startswith('on') or name.startswith('handle') or name.startswith('bind') or 'event' in name.lower()

def is_likely_internal(name):
    return name.startswith('_') or name.startswith('apply') or name.startswith('update') or name.startswith('render') or name.startswith('filter') or name.startswith('escape') or name.startswith('parse') or name.startswith('format') or name.startswith('validate') or name.startswith('get') or name.startswith('set') or name.startswith('check') or name.startswith('mark') or name.startswith('remove') or name.startswith('add') or name.startswith('delete') or name.startswith('load') or name.startswith('save') or name.startswith('try') or name.startswith('submit') or name.startswith('cancel') or name.startswith('suggest') or name.startswith('open') or name.startswith('close') or name.startswith('show') or name.startswith('hide') or name.startswith('edit') or name.startswith('finish') or name.startswith('select') or name.startswith('preview') or name.startswith('goTo')

# 仅列 完全未被任何 HTML onclick / 动态字符串 调用的函数
# 由于动态调用难检测, 这只是粗筛
likely_unused = []
for name in sorted(unused):
    if name in {'switchView', 'switchTemplateView', '_init', 'loadView'}:
        continue
    # 跳过内部 helper
    if is_likely_internal(name):
        continue
    if is_likely_event_handler(name):
        continue
    # 不在 onclick 也不在 JS 内被其他函数调用
    # 简化: 检查 JS 内是否有引用
    if not re.search(r'\b' + re.escape(name) + r'\b', js.replace('function ' + name, '', 1)):
        likely_unused.append(name)
report['未使用函数 (死代码)'] = likely_unused

# 输出
print(json.dumps(report, indent=2, ensure_ascii=False))

with open(r'E:\falvxiangmu\audit_final.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
