import re

with open(r'E:\元枢法智前端\yuanxing\templates\views\template.html', 'rb') as f:
    raw = f.read().decode('utf-8')

# 用正则匹配: <p class="text-[10px] text-gray-400 mb-3"><span ...>X</span>vY · .docx</p>
# 替换: vY · .docx</p> -> vY · .docx · <span class="text-gray-300">2024-09</span></p>

# 1. 找到所有 p class="text-[10px] text-gray-400 mb-3" 内部含 .docx
# 2. 在 .docx 后加 2024-09

# 模拟 split('\n') 然后逐行处理 (因为之前只匹配全字符串没匹配到分开的)
lines = raw.split('\n')
modified_count = 0
in_card_view = False
for i, line in enumerate(lines):
    if 'grid-cols-4 gap-4 template-view template-view-card' in line:
        in_card_view = True
    # 匹配卡片视图里的 meta p
    if in_card_view and '<p class="text-[10px] text-gray-400 mb-3">' in line and '.docx</p>' in line:
        # 简单替换: 把 .docx</p> → .docx · <span class="text-gray-300">2024-09</span></p>
        if '2024-09' not in line:  # 避免重复
            new_line = line.replace('.docx</p>', '.docx · <span class="text-gray-300">2024-09</span></p>', 1)
            lines[i] = new_line
            modified_count += 1

new_content = '\n'.join(lines)
with open(r'E:\元枢法智前端\yuanxing\templates\views\template.html', 'wb') as f:
    f.write(new_content.encode('utf-8'))
print(f'modified {modified_count} lines')
