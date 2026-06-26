import re
from pathlib import Path
ROOT = Path(r'E:\元枢法智前端\yuanxing')
js = (ROOT / 'assets' / 'js' / 'script.js').read_text(encoding='utf-8')
defined = set()
for m in re.finditer(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', js):
    defined.add(m.group(1))
print('switchKnowledgeMainTab defined?', 'switchKnowledgeMainTab' in defined)
print('sortKnowledgeTable defined?', 'sortKnowledgeTable' in defined)
print('triggerKnowledgeSearch defined?', 'triggerKnowledgeSearch' in defined)

onclick_calls = set()
for f in (ROOT / 'templates').rglob('*.html'):
    c = f.read_text(encoding='utf-8', errors='ignore')
    for m in re.finditer(r'''onclick=['"]([a-zA-Z_][a-zA-Z0-9_]*)\(''', c):
        onclick_calls.add(m.group(1))
print('switchKnowledgeMainTab in onclick?', 'switchKnowledgeMainTab' in onclick_calls)
print('sortKnowledgeTable in onclick?', 'sortKnowledgeTable' in onclick_calls)
print('triggerKnowledgeSearch in onclick?', 'triggerKnowledgeSearch' in onclick_calls)
print('Total onclick calls:', len(onclick_calls))
print('switchKnowledgeMainTab in calls?', 'switchKnowledgeMainTab' in onclick_calls)
print('  - calls containing it:', [c for c in onclick_calls if 'switch' in c.lower()])
