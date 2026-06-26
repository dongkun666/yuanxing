with open('E:/元枢法智前端/yuanxing/templates/views/template.html', 'rb') as f:
    c = f.read().decode('utf-8')
import re
stack = []
extras = []
for m in re.finditer(r'<(/?)div[^>]*>', c):
    if m.group(1) == '/':
        if stack:
            stack.pop()
        else:
            extras.append(m.start())
    else:
        cls = re.search(r'class="([^"]*)"', m.group(0))
        stack.append((m.start(), cls.group(1) if cls else '?'))

print(f'Extra </div> count: {len(extras)}')
for pos in extras[:3]:
    print(f'  at pos {pos}:')
    print(f'    before: {c[max(0,pos-60):pos]!r}')
    print(f'    after:  {c[pos:pos+60]!r}')

print(f'\nRemaining unclosed: {len(stack)}')
for pos, cls in stack[-5:]:
    print(f'  pos {pos}: {cls[:60]}')
