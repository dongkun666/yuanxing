import os

ROOT = r'E:\雍行\诉讼模板'

def walk(d, depth=0, max_depth=4):
    if depth > max_depth:
        return
    indent = '  ' * depth
    try:
        items = sorted(os.listdir(d))
    except PermissionError:
        return
    for name in items:
        full = os.path.join(d, name)
        if os.path.isdir(full):
            print(f'{indent}[{name}]')
            walk(full, depth+1, max_depth)
        else:
            size = os.path.getsize(full)
            print(f'{indent}{name}  ({size} bytes)')

for d in sorted(os.listdir(ROOT)):
    full = os.path.join(ROOT, d)
    if os.path.isdir(full):
        print(f'\n=== [{d}] ===')
        walk(full, 1, 4)
