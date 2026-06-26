"""把卡片网格改成表格行（单栏布局）"""
import re

CASE_DETAIL = r'E:\元枢法智前端\yuanxing\templates\views\case-detail.html'

with open(CASE_DETAIL, 'r', encoding='utf-8', newline='') as f:
    content = f.read()
lines = content.split('\n')

# L373 (grid-cols-3 开) - L450 (grid 关) 替换
# 但 3 张卡片在 L374-L449
# L450: </div> (关 grid)
# L451: </div> (关右栏 flex-1 容器) - 现在不需要了, 因为是单栏
# L452: </div> (关 case-tab-documents)

# 实际上 max-w-6xl > toolbar + 标题栏 (没有 flex-1 容器了, 因为单栏)
# 看 L334 之后结构:
# 334: <div id="case-tab-documents" ...>
# 335: <div class="max-w-6xl mx-auto space-y-4">
# 336-371: toolbar + 标题栏
# 372: </div> (关 max-w-6xl? 不对, 是 grid 关的)
# 实际上当前结构是:
#   case-tab-documents
#     max-w-6xl space-y-4
#       toolbar
#       标题栏
#       grid-cols-3
#         卡片1
#         卡片2
#         卡片3
#       </div> (关 grid)
#     </div> (关 max-w-6xl)
#   </div> (关 case-tab-documents)

# 表格行替代卡片网格
TABLE_HTML = '''<div class="bg-white rounded-xl border border-[#E5E6EB] overflow-hidden">
<div class="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
<div class="flex items-center gap-2">
<iconify-icon class="text-base text-[#165DFF]" icon="mdi:scale-balance"></iconify-icon>
<span class="text-sm font-bold text-gray-800">民事起诉状</span>
<span class="text-xs text-gray-400">共 3 份历史版本</span>
</div>
<div class="flex items-center gap-2 text-xs">
<button class="bg-white border border-gray-200 px-2.5 py-1 rounded hover:bg-gray-50 flex items-center gap-1">
<iconify-icon icon="mdi:sort-variant"></iconify-icon>按时间排序
</button>
<button class="bg-white border border-gray-200 px-2.5 py-1 rounded hover:bg-gray-50 flex items-center gap-1">
<iconify-icon icon="mdi:filter-variant"></iconify-icon>筛选
</button>
</div>
</div>
<table class="w-full text-sm">
<thead>
<tr class="bg-gray-50 border-b border-[#E5E6EB]">
<th class="text-left py-3 px-5 text-[11px] font-semibold text-gray-600 w-16">版本</th>
<th class="text-left py-3 px-5 text-[11px] font-semibold text-gray-600">标题</th>
<th class="text-center py-3 px-5 text-[11px] font-semibold text-gray-600 w-24">状态</th>
<th class="text-left py-3 px-5 text-[11px] font-semibold text-gray-600 w-24">创建人</th>
<th class="text-left py-3 px-5 text-[11px] font-semibold text-gray-600 w-40">最后编辑</th>
<th class="text-right py-3 px-5 text-[11px] font-semibold text-gray-600 w-24">字数</th>
<th class="text-center py-3 px-5 text-[11px] font-semibold text-gray-600 w-32">操作</th>
</tr>
</thead>
<tbody class="divide-y divide-gray-50">
<tr class="hover:bg-gray-50 group">
<td class="py-3 px-5"><span class="text-[10px] font-mono font-bold text-[#165DFF] bg-blue-50 px-1.5 py-0.5 rounded">v1</span></td>
<td class="py-3 px-5">
<div class="flex items-center gap-2">
<iconify-icon class="text-base text-[#165DFF]" icon="mdi:file-document-outline"></iconify-icon>
<span class="text-sm text-gray-800 font-medium">民事起诉状 - 初稿</span>
</div>
<p class="text-[11px] text-gray-500 mt-0.5 truncate max-w-md">AI 智能起草的基础版本，包含当事人信息、诉讼请求、事实与理由。</p>
</td>
<td class="py-3 px-5 text-center"><span class="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded font-medium">草稿</span></td>
<td class="py-3 px-5 text-xs text-gray-600">张律师</td>
<td class="py-3 px-5 text-xs text-gray-500">2026-06-20 14:30</td>
<td class="py-3 px-5 text-right text-xs text-gray-600">1,256 字 · 4 页</td>
<td class="py-3 px-5 text-center">
<div class="flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-2 py-1 rounded">编辑</button>
<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-2 py-1 rounded">预览</button>
<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-2 py-1 rounded">复制</button>
<button class="text-xs text-red-500 hover:bg-red-50 px-2 py-1 rounded">删除</button>
</div>
</td>
</tr>
<tr class="hover:bg-gray-50 group">
<td class="py-3 px-5"><span class="text-[10px] font-mono font-bold text-[#165DFF] bg-blue-50 px-1.5 py-0.5 rounded">v2</span></td>
<td class="py-3 px-5">
<div class="flex items-center gap-2">
<iconify-icon class="text-base text-[#165DFF]" icon="mdi:file-document-outline"></iconify-icon>
<span class="text-sm text-gray-800 font-medium">民事起诉状 - 修改稿</span>
</div>
<p class="text-[11px] text-gray-500 mt-0.5 truncate max-w-md">基于初稿修改，补充证据目录引用，优化诉讼请求结构。</p>
</td>
<td class="py-3 px-5 text-center"><span class="text-[10px] bg-orange-100 text-orange-700 px-1.5 py-0.5 rounded font-medium">审核中</span></td>
<td class="py-3 px-5 text-xs text-gray-600">李合伙人</td>
<td class="py-3 px-5 text-xs text-gray-500">2026-06-23 10:15</td>
<td class="py-3 px-5 text-right text-xs text-gray-600">1,485 字 · 5 页</td>
<td class="py-3 px-5 text-center">
<div class="flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-2 py-1 rounded">编辑</button>
<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-2 py-1 rounded">预览</button>
<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-2 py-1 rounded">复制</button>
<button class="text-xs text-red-500 hover:bg-red-50 px-2 py-1 rounded">删除</button>
</div>
</td>
</tr>
<tr class="hover:bg-gray-50 group bg-blue-50/30">
<td class="py-3 px-5"><span class="text-[10px] font-mono font-bold text-[#165DFF] bg-blue-100 px-1.5 py-0.5 rounded">v3</span></td>
<td class="py-3 px-5">
<div class="flex items-center gap-2">
<iconify-icon class="text-base text-[#165DFF]" icon="mdi:file-document-outline"></iconify-icon>
<span class="text-sm text-gray-800 font-medium">民事起诉状 - 立案终稿</span>
<iconify-icon class="text-green-500 text-sm" icon="mdi:check-decagram" title="当前生效版本"></iconify-icon>
</div>
<p class="text-[11px] text-gray-500 mt-0.5 truncate max-w-md">合伙人审核通过，已提交法院立案。案号：(2026)沪0115民初12345号。</p>
</td>
<td class="py-3 px-5 text-center"><span class="text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded font-medium">已立案</span></td>
<td class="py-3 px-5 text-xs text-gray-600">王主任</td>
<td class="py-3 px-5 text-xs text-gray-500">2026-06-25 16:40</td>
<td class="py-3 px-5 text-right text-xs text-gray-600">1,632 字 · 5 页</td>
<td class="py-3 px-5 text-center">
<div class="flex items-center justify-center gap-1">
<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-2 py-1 rounded font-medium">编辑</button>
<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-2 py-1 rounded">预览</button>
<button class="text-xs text-[#165DFF] hover:bg-blue-50 px-2 py-1 rounded">复制</button>
</div>
</td>
</tr>
</tbody>
</table>
</div>'''

# L373 = grid-cols-3 div 开
# L450 = </div> (关 grid)
# 我们替换 L373-L450 (1-based 373-450 = 0-based 372-449)
# L451 还要保留: 它关的是 right panel 容器 (flex-1 flex-col) - 但单栏下没有这个 div 了
# 实际: 之前的卡片网格 (grid-cols-3) 是 right panel flex-1 容器内的子 div
# 之前结构: case-tab > max-w-7xl flex > [左栏 flex-none] [右栏 flex-1 > toolbar > 标题 > grid-cols-3 > cards]
# 现在: case-tab > max-w-6xl space-y-4 > toolbar > 标题 > table

# 现在的 max-w-6xl 后是 toolbar (336-368), 标题栏, 然后 grid
# grid-cols-3 (L373) 替换为 TABLE
# L450 </div> 关 grid
# L451 </div> 关 max-w-6xl 容器
# L452 </div> 关 case-tab-documents
# 我替换 L373-L450 (0-based 372-449) 用 TABLE_HTML
# 然后 L451 (</div> 关 max-w-6xl) 不动
# L452 (</div> 关 case-tab-documents) 不动

new_lines = lines[:372] + [TABLE_HTML] + lines[450:]

with open(CASE_DETAIL, 'w', encoding='utf-8', newline='') as f:
    f.write('\n'.join(new_lines))

# 验证
with open(CASE_DETAIL, 'r', encoding='utf-8') as f:
    c = f.read()
opens = len(re.findall(r'<div\b', c))
closes = c.count('</div>')
print(f'\nnew file: {len(c.split(chr(10)))} lines, {opens}o, {closes}c, diff {opens-closes}')
