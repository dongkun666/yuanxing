"""完整重写 knowledge.html - LLM Wiki 风格 - Step 1: stats + tabs"""
import re

path = r'E:\元枢法智前端\yuanxing\templates\views\knowledge.html'
with open(path, 'rb') as f:
    raw = f.read().decode('utf-8').replace('\r\n', '\n')

# 生成 sparkline
def make_sparkline(data, color, w=64, h=24):
    if max(data) == min(data):
        mn, mx = min(data) - 1, max(data) + 1
    else:
        mn, mx = min(data), max(data)
    n = len(data)
    step_x = w / (n - 1)
    points = []
    for i, v in enumerate(data):
        x = i * step_x
        y = h - (v - mn) / (mx - mn) * h
        points.append((x, y))
    path = f"M {points[0][0]:.1f} {points[0][1]:.1f}"
    for i in range(1, n):
        path += f" L {points[i][0]:.1f} {points[i][1]:.1f}"
    fill_path = path + f" L {points[-1][0]:.1f} {h} L {points[0][0]:.1f} {h} Z"
    return f'''<svg class="overflow-visible" viewBox="0 0 64 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="{fill_path}" fill="{color}" fill-opacity="0.12"/>
<path d="{path}" stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

# ===== 1. 4 统计卡 =====
raw_data = [5, 8, 6, 10, 12, 11, 15, 14, 18, 22, 20, 25]
wiki_data = [120, 128, 135, 142, 148, 155, 162, 168, 173, 178, 182, 186]
topic_data = [10, 10, 10, 11, 11, 12, 12, 12, 12, 13, 13, 13]
lint_data = [8, 6, 7, 5, 4, 6, 5, 3, 4, 5, 4, 4]

raw_svg = make_sparkline(raw_data, '#165DFF')
wiki_svg = make_sparkline(wiki_data, '#9333EA')
topic_svg = make_sparkline(topic_data, '#16A34A')
lint_svg = make_sparkline(lint_data, '#FAAD14')

new_stats = f'''<div class="grid grid-cols-4 gap-4">
<div class="bg-white rounded-xl border border-[#E5E6EB] p-4">
<div class="flex items-center justify-between mb-1">
<p class="text-xs text-[#86909C]">原始资料 (Raw)</p>
<div class="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
<iconify-icon class="text-base text-[#165DFF]" icon="mdi:file-document-multiple-outline"></iconify-icon>
</div>
</div>
<p class="text-2xl font-bold text-[#1D2129] leading-tight">42</p>
<div class="flex items-end justify-between mt-1.5">
<p class="text-[10px] text-green-600">↑ 7 天 +3</p>
{raw_svg}
</div>
</div>
<div class="bg-white rounded-xl border border-[#E5E6EB] p-4">
<div class="flex items-center justify-between mb-1">
<p class="text-xs text-[#86909C]">Wiki 页面</p>
<div class="w-8 h-8 rounded-lg bg-purple-50 flex items-center justify-center">
<iconify-icon class="text-base text-purple-600" icon="mdi:graph-outline"></iconify-icon>
</div>
</div>
<p class="text-2xl font-bold text-[#1D2129] leading-tight">186</p>
<div class="flex items-end justify-between mt-1.5">
<p class="text-[10px] text-purple-600">由 LLM 维护</p>
{wiki_svg}
</div>
</div>
<div class="bg-white rounded-xl border border-[#E5E6EB] p-4">
<div class="flex items-center justify-between mb-1">
<p class="text-xs text-[#86909C]">主题树</p>
<div class="w-8 h-8 rounded-lg bg-green-50 flex items-center justify-center">
<iconify-icon class="text-base text-green-600" icon="mdi:family-tree"></iconify-icon>
</div>
</div>
<p class="text-2xl font-bold text-[#1D2129] leading-tight">13</p>
<div class="flex items-end justify-between mt-1.5">
<p class="text-[10px] text-[#FAAD14]">● 2 个待补</p>
{topic_svg}
</div>
</div>
<div class="bg-white rounded-xl border border-[#E5E6EB] p-4">
<div class="flex items-center justify-between mb-1">
<p class="text-xs text-[#86909C]">巡检状态</p>
<div class="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center">
<iconify-icon class="text-base text-[#FAAD14]" icon="mdi:shield-check-outline"></iconify-icon>
</div>
</div>
<p class="text-2xl font-bold text-[#1D2129] leading-tight">4 <span class="text-xs font-normal text-[#86909C]">项待处理</span></p>
<div class="flex items-end justify-between mt-1.5">
<p class="text-[10px] text-red-500">● 1 项紧急</p>
{lint_svg}
</div>
</div>
</div>'''

# 替换 stats grid (用 regex 匹配整段)
stats_pattern = re.compile(
    r'<div class="grid grid-cols-4 gap-4">\s*'
    r'(?:<div class="bg-white rounded-xl border border-\[#E5E6EB\] p-4">.*?</div>\s*){4}'
    r'</div>',
    re.DOTALL
)
m = stats_pattern.search(raw)
if m:
    print(f'stats 块长度: {len(m.group(0))}')
    raw = raw[:m.start()] + new_stats + raw[m.end():]
    print('✓ stats 已替换')
else:
    print('✗ stats 块未找到')

# ===== 2. 6 tabs 块 -> 3 tabs 块 =====
# 用 regex 匹配整个 6-tabs 块 (从 <!-- 分类筛选 --> 到 </div> 结束)
# 因为 6 tabs 块有右侧的 flex-1 + 2 个 sort/export 按钮
old_tabs_pattern = re.compile(
    r'<!-- 分类筛选 -->\s*'
    r'<div class="bg-white rounded-xl border border-\[#E5E6EB\] p-3">\s*'
    r'<div class="flex items-center gap-1 flex-wrap">\s*'
    r'(?:.*?)'
    r'</div>\s*</div>',
    re.DOTALL
)
m = old_tabs_pattern.search(raw)
if m:
    print(f'6 tabs 块长度: {len(m.group(0))}')

    new_3tabs = '''<!-- LLM Wiki 三大操作 Tab 切换 -->
<div class="bg-white rounded-xl border border-[#E5E6EB] p-2">
<div class="flex items-center gap-1">
<button class="flex-1 px-4 py-2.5 text-sm font-medium rounded-lg bg-[#F2F5FF] text-[#165DFF] flex items-center justify-center gap-2 transition-colors" id="kb-tab-ingest" onclick="switchKnowledgeMainTab('ingest', this)">
<iconify-icon class="text-base" icon="mdi:upload-multiple"></iconify-icon>
<span>摄入 (Ingest)</span>
<span class="text-[10px] bg-white text-[#165DFF] px-1.5 py-0.5 rounded font-medium">42 原始</span>
</button>
<button class="flex-1 px-4 py-2.5 text-sm font-medium rounded-lg text-[#4E5969] hover:bg-[#F7F8FA] flex items-center justify-center gap-2 transition-colors" id="kb-tab-wiki" onclick="switchKnowledgeMainTab('wiki', this)">
<iconify-icon class="text-base" icon="mdi:graph"></iconify-icon>
<span>Wiki 页面</span>
<span class="text-[10px] bg-[#F2F3F5] text-[#4E5969] px-1.5 py-0.5 rounded font-medium">186 页</span>
</button>
<button class="flex-1 px-4 py-2.5 text-sm font-medium rounded-lg text-[#4E5969] hover:bg-[#F7F8FA] flex items-center justify-center gap-2 transition-colors" id="kb-tab-lint" onclick="switchKnowledgeMainTab('lint', this)">
<iconify-icon class="text-base" icon="mdi:shield-search"></iconify-icon>
<span>巡检 (Lint)</span>
<span class="text-[10px] bg-[#FFF3E0] text-[#FAAD14] px-1.5 py-0.5 rounded font-medium">4 待处理</span>
</button>
</div>
</div>'''

    raw = raw[:m.start()] + new_3tabs + raw[m.end():]
    print('✓ 6 tabs → 3 tabs 已替换')
else:
    print('✗ 6 tabs 块未找到')

with open(path, 'wb') as f:
    f.write(raw.encode('utf-8'))

# div 平衡
print('div 平衡:', raw.count('<div'), '==', raw.count('</div>'))
