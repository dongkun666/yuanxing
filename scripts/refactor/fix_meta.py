import re

with open(r'E:\元枢法智前端\yuanxing\templates\views\template.html', 'rb') as f:
    raw = f.read().decode('utf-8')

# 1. meta 行加更新时间 (使用现在已有的 p 标签)
# 现有: <p class="text-[10px] text-gray-400 mb-3"><span class="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded mr-1.5">其他</span>v1.0 · .docx</p>
# 改:  <p class="text-[10px] text-gray-400 mb-3"><span class="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded mr-1.5">其他</span>v1.0 · .docx · <span class="text-gray-300">2024-09</span></p>

# 只在卡片视图 (template-view-card) 的 p 标签中加, 不影响列表视图
old = '<p class="text-[10px] text-gray-400 mb-3"><span class="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded mr-1.5">'
new = '<p class="text-[10px] text-gray-400 mb-3"><span class="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded mr-1.5">'

# 验证 p 标签只在卡片视图里 (L456+ grid-cols-4 后, L704 前)
content_lines = raw.split('\n')
in_card_view = False
modified_count = 0
new_lines = []
for i, line in enumerate(content_lines):
    if 'grid-cols-4 gap-4 template-view template-view-card' in line:
        in_card_view = True
    if in_card_view and '<p class="text-[10px] text-gray-400 mb-3"><span class="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded mr-1.5">' in line:
        # 替换 .docx</p> -> .docx · <span class="text-gray-300">2024-09</span></p>
        line = line.replace('· .docx</p>', '· .docx · <span class="text-gray-300">2024-09</span></p>')
        modified_count += 1
    new_lines.append(line)

new_content = '\n'.join(new_lines)
with open(r'E:\元枢法智前端\yuanxing\templates\views\template.html', 'wb') as f:
    f.write(new_content.encode('utf-8'))
print(f'modified {modified_count} lines')
