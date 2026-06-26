import re

path = r'E:\元枢法智前端\yuanxing\templates\views\knowledge.html'
with open(path, 'rb') as f:
    raw = f.read().decode('utf-8')

# 匹配每个 data row 并提取 date + cite + title
pattern = re.compile(
    r'(<tr class="hover:bg-\[#F7F8FA\] transition-colors" data-knowledge-type="[^"]*" data-knowledge-area="[^"]*")>'
    r'(.*?)'
    r'</tr>',
    re.DOTALL
)

def process_row(m):
    head, body = m.group(1), m.group(2)
    # 提取 title (第 1 个 td 的 .font-medium 文本)
    title_match = re.search(r'<p class="text-sm font-medium text-\[#1D2129\][^"]*">([^<]+)</p>', body)
    title = title_match.group(1) if title_match else ''
    # 提取 date (YYYY-MM-DD)
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', body)
    date = date_match.group(1) if date_match else ''
    # 提取 cite (4th col, 128/76 这种数字)
    cite_match = re.search(r'<td class="text-center py-3 px-4 text-sm font-semibold text-\[#165DFF\]">(\d+)</td>', body)
    cite = cite_match.group(1) if cite_match else '0'

    # 加 data 属性
    new_head = head[:-1] + f' data-date="{date}" data-cite="{cite}" data-title="{title}">'
    return new_head + body + '</tr>'

new_raw = pattern.sub(process_row, raw)

# 验证
data_date_count = new_raw.count('data-date="')
data_cite_count = new_raw.count('data-cite="')
data_title_count = new_raw.count('data-title="')
print(f'data-date: {data_date_count}, data-cite: {data_cite_count}, data-title: {data_title_count}')

# 抽样
sample = re.search(r'<tr class="hover[^>]+>', new_raw)
print('sample:', sample.group(0)[:300] if sample else 'none')

# div 平衡
print('div 平衡:', new_raw.count('<div'), '==', new_raw.count('</div>'))

with open(path, 'wb') as f:
    f.write(new_raw.encode('utf-8'))
