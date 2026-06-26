"""检查所有 view 模板的 div 嵌套是否平衡"""
import re
import os
from html.parser import HTMLParser

VIEW_DIR = r'E:\元枢法智前端\yuanxing\templates\views'
MODALS = r'E:\元枢法智前端\yuanxing\templates\modals.html'

class Tracker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.extra_closes = []
    def handle_starttag(self, t, a):
        if t == 'div':
            ident = dict(a).get('id', '')
            self.stack.append((self.getpos(), ident))
    def handle_endtag(self, t):
        if t == 'div':
            if self.stack:
                self.stack.pop()
            else:
                self.extra_closes.append(self.getpos())

def check_file(path):
    name = os.path.basename(path)
    with open(path, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8', errors='replace')
    o = len(re.findall(r'<div\b', text))
    c = len(re.findall(r'</div>', text))
    p = Tracker()
    try:
        p.feed(text)
    except Exception as e:
        return name, o, c, f'PARSE_ERR: {e}'
    extras = len(p.extra_closes)
    unclosed = len(p.stack)
    if o == c and extras == 0 and unclosed == 0:
        status = 'OK'
    else:
        status = f'UNCLOSED={unclosed} EXTRA_CLOSE={extras}'
    return name, o, c, status

print(f'{"File":<35} {"open":>6} {"close":>6}  status')
print('-' * 80)
for d in [VIEW_DIR, os.path.dirname(MODALS)]:
    for f in sorted(os.listdir(d)):
        if f.endswith('.html'):
            r = check_file(os.path.join(d, f))
            print(f'{r[0]:<35} {r[1]:>6} {r[2]:>6}  {r[3]}')
