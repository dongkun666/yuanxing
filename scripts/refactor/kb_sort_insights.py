import re

path = r'E:\元枢法智前端\yuanxing\templates\views\knowledge.html'
with open(path, 'rb') as f:
    raw = f.read().decode('utf-8')

# 1. 给搜索框加 id
raw = raw.replace(
    'placeholder="搜索法条、案例、文书关键词..." type="text"/>',
    'id="kb-search-input" placeholder="搜索法条、案例、文书关键词..." type="text"/>'
)

# 2. 给 4 个表头加 sortable + onclick
# 标题 / 发布时间 / 引用 (3 个最常用排序)
old_ths = '''<th class="text-left py-3 px-4 text-xs font-semibold text-[#4E5969] w-2/5">文档标题</th>
<th class="text-center py-3 px-4 text-xs font-semibold text-[#4E5969]">类型</th>
<th class="text-center py-3 px-4 text-xs font-semibold text-[#4E5969]">领域</th>
<th class="text-center py-3 px-4 text-xs font-semibold text-[#4E5969]">来源</th>
<th class="text-center py-3 px-4 text-xs font-semibold text-[#4E5969]">发布时间</th>
<th class="text-center py-3 px-4 text-xs font-semibold text-[#4E5969]">引用</th>
<th class="text-center py-3 px-4 text-xs font-semibold text-[#4E5969] w-44">操作</th>'''

new_ths = '''<th class="text-left py-3 px-4 text-xs font-semibold text-[#4E5969] w-2/5 cursor-pointer hover:text-[#165DFF] select-none" onclick="sortKnowledgeTable('title', this)">文档标题<span class="sort-arrow ml-1 text-[#C9CDD4]">⇅</span></th>
<th class="text-center py-3 px-4 text-xs font-semibold text-[#4E5969]">类型</th>
<th class="text-center py-3 px-4 text-xs font-semibold text-[#4E5969]">领域</th>
<th class="text-center py-3 px-4 text-xs font-semibold text-[#4E5969]">来源</th>
<th class="text-center py-3 px-4 text-xs font-semibold text-[#4E5969] cursor-pointer hover:text-[#165DFF] select-none" onclick="sortKnowledgeTable('date', this)">发布时间<span class="sort-arrow ml-1 text-[#C9CDD4]">⇅</span></th>
<th class="text-center py-3 px-4 text-xs font-semibold text-[#4E5969] cursor-pointer hover:text-[#165DFF] select-none" onclick="sortKnowledgeTable('cite', this)">引用<span class="sort-arrow ml-1 text-[#C9CDD4]">⇅</span></th>
<th class="text-center py-3 px-4 text-xs font-semibold text-[#4E5969] w-44">操作</th>'''

assert old_ths in raw, 'th row not found'
raw = raw.replace(old_ths, new_ths)

# 3. AI 洞察 3 个卡片加 onclick + cursor-pointer
old_insights = '''<div class="grid grid-cols-3 gap-4">
<div class="p-3 rounded-lg bg-[#F7F8FA]">
<div class="flex items-center gap-2 mb-2">
<iconify-icon class="text-base text-[#165DFF]" icon="mdi:fire"></iconify-icon>
<span class="text-xs font-medium text-[#1D2129]">高频引用</span>
</div>
<p class="text-[10px] text-[#4E5969]">本月引用 Top 3: 民法典合同编（128 次）、刑法修正案十二（89 次）、民间借贷司法解释（76 次）。建议重点关注修订解读。</p>
</div>
<div class="p-3 rounded-lg bg-[#F7F8FA]">
<div class="flex items-center gap-2 mb-2">
<iconify-icon class="text-base text-[#FAAD14]" icon="mdi:alert-circle-outline"></iconify-icon>
<span class="text-xs font-medium text-[#1D2129]">知识缺口</span>
</div>
<p class="text-[10px] text-[#4E5969]">劳动争议领域仅有 2 篇内部资料。建议补充：劳动合同解除典型案例、新就业形态劳动关系认定相关裁判规则。</p>
</div>
<div class="p-3 rounded-lg bg-[#F7F8FA]">
<div class="flex items-center gap-2 mb-2">
<iconify-icon class="text-base text-green-600" icon="mdi:update"></iconify-icon>
<span class="text-xs font-medium text-[#1D2129]">最近更新</span>
</div>
<p class="text-[10px] text-[#4E5969]">过去 7 天新增 12 篇文档，包括 3 件最高法新发布指导案例和 1 部新法律法规。可在搜索框输入 "2024" 快速查找。</p>
</div>
</div>'''

new_insights = '''<div class="grid grid-cols-3 gap-4">
<div class="p-3 rounded-lg bg-[#F7F8FA] cursor-pointer hover:bg-[#F2F3F5] transition-colors" onclick="triggerKnowledgeSearch('民法典')">
<div class="flex items-center gap-2 mb-2">
<iconify-icon class="text-base text-[#165DFF]" icon="mdi:fire"></iconify-icon>
<span class="text-xs font-medium text-[#1D2129]">高频引用</span>
<span class="text-[10px] text-[#165DFF] ml-auto">点击搜索 →</span>
</div>
<p class="text-[10px] text-[#4E5969]">本月引用 Top 3: 民法典合同编（128 次）、刑法修正案十二（89 次）、民间借贷司法解释（76 次）。建议重点关注修订解读。</p>
</div>
<div class="p-3 rounded-lg bg-[#F7F8FA] cursor-pointer hover:bg-[#F2F3F5] transition-colors" onclick="triggerKnowledgeSearch('劳动争议')">
<div class="flex items-center gap-2 mb-2">
<iconify-icon class="text-base text-[#FAAD14]" icon="mdi:alert-circle-outline"></iconify-icon>
<span class="text-xs font-medium text-[#1D2129]">知识缺口</span>
<span class="text-[10px] text-[#FAAD14] ml-auto">点击搜索 →</span>
</div>
<p class="text-[10px] text-[#4E5969]">劳动争议领域仅有 2 篇内部资料。建议补充：劳动合同解除典型案例、新就业形态劳动关系认定相关裁判规则。</p>
</div>
<div class="p-3 rounded-lg bg-[#F7F8FA] cursor-pointer hover:bg-[#F2F3F5] transition-colors" onclick="triggerKnowledgeSearch('2024')">
<div class="flex items-center gap-2 mb-2">
<iconify-icon class="text-base text-green-600" icon="mdi:update"></iconify-icon>
<span class="text-xs font-medium text-[#1D2129]">最近更新</span>
<span class="text-[10px] text-green-600 ml-auto">点击搜索 →</span>
</div>
<p class="text-[10px] text-[#4E5969]">过去 7 天新增 12 篇文档，包括 3 件最高法新发布指导案例和 1 部新法律法规。可在搜索框输入 "2024" 快速查找。</p>
</div>
</div>'''

assert old_insights in raw, 'insights block not found'
raw = raw.replace(old_insights, new_insights)

with open(path, 'wb') as f:
    f.write(raw.encode('utf-8'))

# 验证
print('id 注入:', 'id="kb-search-input"' in raw)
print('sortable th:', 'sortKnowledgeTable' in raw)
print('AI onclick:', raw.count('triggerKnowledgeSearch'))
print('div 平衡:', raw.count('<div'), '==', raw.count('</div>'))
