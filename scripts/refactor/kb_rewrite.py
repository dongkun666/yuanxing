"""完全重写 knowledge.html - LLM Wiki 风格"""
import re

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

# 4 stat card sparklines
raw_svg = make_sparkline([5, 8, 6, 10, 12, 11, 15, 14, 18, 22, 20, 25], '#165DFF')
wiki_svg = make_sparkline([120, 128, 135, 142, 148, 155, 162, 168, 173, 178, 182, 186], '#9333EA')
topic_svg = make_sparkline([10, 10, 10, 11, 11, 12, 12, 12, 12, 13, 13, 13], '#16A34A')
lint_svg = make_sparkline([8, 6, 7, 5, 4, 6, 5, 3, 4, 5, 4, 4], '#FAAD14')

html = f'''<div class="view-content hidden flex-1 flex flex-col overflow-y-auto p-6 bg-[#F2F3F5]" id="view-knowledge">
<div class="max-w-6xl mx-auto w-full space-y-5">
<!-- 顶部 4 概念卡 (LLM Wiki 视角) -->
<div class="grid grid-cols-4 gap-4">
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
</div>

<!-- LLM Wiki 三大操作 Tab 切换 -->
<div class="bg-white rounded-xl border border-[#E5E6EB] p-2">
<div class="flex items-center gap-1">
<button class="flex-1 px-4 py-2.5 text-sm font-medium rounded-lg bg-[#F2F5FF] text-[#165DFF] flex items-center justify-center gap-2 transition-colors" id="kb-tab-ingest" onclick="switchKnowledgeMainTab('ingest', this)">
<iconify-icon class="text-lg" icon="mdi:upload-multiple"></iconify-icon>
<span>摄入 (Ingest)</span>
<span class="text-[10px] bg-white text-[#165DFF] px-1.5 py-0.5 rounded font-medium">42 原始</span>
</button>
<button class="flex-1 px-4 py-2.5 text-sm font-medium rounded-lg text-[#4E5969] hover:bg-[#F7F8FA] flex items-center justify-center gap-2 transition-colors" id="kb-tab-wiki" onclick="switchKnowledgeMainTab('wiki', this)">
<iconify-icon class="text-lg" icon="mdi:graph"></iconify-icon>
<span>Wiki 页面</span>
<span class="text-[10px] bg-[#F2F3F5] text-[#4E5969] px-1.5 py-0.5 rounded font-medium">186 页</span>
</button>
<button class="flex-1 px-4 py-2.5 text-sm font-medium rounded-lg text-[#4E5969] hover:bg-[#F7F8FA] flex items-center justify-center gap-2 transition-colors" id="kb-tab-lint" onclick="switchKnowledgeMainTab('lint', this)">
<iconify-icon class="text-lg" icon="mdi:shield-search"></iconify-icon>
<span>巡检 (Lint)</span>
<span class="text-[10px] bg-[#FFF3E0] text-[#FAAD14] px-1.5 py-0.5 rounded font-medium">4 待处理</span>
</button>
</div>
</div>

<!-- ============== Tab 1: 摄入 (Ingest) ============== -->
<div id="kb-panel-ingest" class="kb-panel space-y-4">
<!-- 摄入状态汇总 -->
<div class="grid grid-cols-4 gap-3">
<div class="bg-white rounded-lg border border-[#E5E6EB] p-3 flex items-center gap-3">
<div class="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
<iconify-icon class="text-xl text-green-600" icon="mdi:check-circle"></iconify-icon>
</div>
<div>
<p class="text-xs text-[#86909C]">已编译</p>
<p class="text-xl font-bold text-[#1D2129]">22</p>
</div>
</div>
<div class="bg-white rounded-lg border border-[#E5E6EB] p-3 flex items-center gap-3">
<div class="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
<iconify-icon class="text-xl text-[#165DFF]" icon="mdi:loading"></iconify-icon>
</div>
<div>
<p class="text-xs text-[#86909C]">编译中</p>
<p class="text-xl font-bold text-[#1D2129]">2</p>
</div>
</div>
<div class="bg-white rounded-lg border border-[#E5E6EB] p-3 flex items-center gap-3">
<div class="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center">
<iconify-icon class="text-xl text-[#FAAD14]" icon="mdi:clock-outline"></iconify-icon>
</div>
<div>
<p class="text-xs text-[#86909C]">待编译</p>
<p class="text-xl font-bold text-[#1D2129]">8</p>
</div>
</div>
<div class="bg-white rounded-lg border border-[#E5E6EB] p-3 flex items-center gap-3">
<div class="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center">
<iconify-icon class="text-xl text-red-500" icon="mdi:alert-circle"></iconify-icon>
</div>
<div>
<p class="text-xs text-[#86909C]">失败</p>
<p class="text-xl font-bold text-[#1D2129]">0</p>
</div>
</div>
</div>

<!-- 原始资料列表 -->
<div class="bg-white rounded-xl border border-[#E5E6EB] overflow-hidden">
<div class="p-3 border-b border-[#E5E6EB] flex items-center justify-between">
<div>
<h4 class="text-sm font-semibold text-[#1D2129] flex items-center gap-2">
<iconify-icon class="text-base text-[#165DFF]" icon="mdi:file-multiple"></iconify-icon>
原始资料 (Raw Sources)
</h4>
<p class="text-[10px] text-[#86909C] mt-0.5">只读资料,AI 编译后生成结构化 Wiki 页面。点击「AI 编译」启动 LLM 提取与跨页面更新。</p>
</div>
<div class="flex items-center gap-2">
<button class="px-3 py-1.5 text-xs font-medium rounded-lg border border-[#E5E6EB] text-[#4E5969] hover:bg-[#F7F8FA] transition-colors flex items-center gap-1">
<iconify-icon class="text-sm" icon="mdi:filter-variant"></iconify-icon>
筛选
</button>
<button class="px-3 py-1.5 text-xs font-medium rounded-lg border border-[#E5E6EB] text-[#4E5969] hover:bg-[#F7F8FA] transition-colors flex items-center gap-1">
<iconify-icon class="text-sm" icon="mdi:sort-variant"></iconify-icon>
时间
</button>
<button class="px-3 py-1.5 text-xs font-medium rounded-lg bg-[#165DFF] text-white hover:bg-[#4080FF] transition-colors flex items-center gap-1" onclick="simulateUpload()">
<iconify-icon class="text-sm" icon="mdi:upload-outline"></iconify-icon>
上传资料
</button>
</div>
</div>
<table class="w-full text-sm">
<thead>
<tr class="bg-[#F7F8FA] border-b border-[#E5E6EB]">
<th class="text-left py-2.5 px-4 text-xs font-semibold text-[#4E5969]">资料名称</th>
<th class="text-center py-2.5 px-4 text-xs font-semibold text-[#4E5969] w-24">类型</th>
<th class="text-center py-2.5 px-4 text-xs font-semibold text-[#4E5969] w-28">状态</th>
<th class="text-center py-2.5 px-4 text-xs font-semibold text-[#4E5969] w-32">影响</th>
<th class="text-center py-2.5 px-4 text-xs font-semibold text-[#4E5969] w-28">上传时间</th>
<th class="text-center py-2.5 px-4 text-xs font-semibold text-[#4E5969] w-36">操作</th>
</tr>
</thead>
<tbody class="divide-y divide-[#F2F3F5]">
<!-- 编译中 1 -->
<tr class="hover:bg-[#F7F8FA] transition-colors">
<td class="py-3 px-4">
<div class="flex items-center gap-2.5">
<div class="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
<iconify-icon class="text-base text-[#165DFF]" icon="mdi:file-pdf-box"></iconify-icon>
</div>
<div class="min-w-0">
<p class="text-xs font-medium text-[#1D2129] truncate">张明楷·刑法学中因果关系与客观归责研究.pdf</p>
<p class="text-[10px] text-[#86909C] mt-0.5">2.4 MB · 18 页 · 学术文献</p>
</div>
</div>
</td>
<td class="text-center py-3 px-4 text-xs text-[#4E5969]">PDF</td>
<td class="text-center py-3 px-4">
<div class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 text-[#165DFF]">
<iconify-icon class="text-xs animate-spin" icon="mdi:loading"></iconify-icon>
<span class="text-[10px] font-medium">编译中 65%</span>
</div>
<div class="w-full bg-[#F2F3F5] rounded-full h-1 mt-1.5">
<div class="bg-[#165DFF] h-1 rounded-full" style="width: 65%"></div>
</div>
</td>
<td class="text-center py-3 px-4 text-[10px] text-[#4E5969]">
<span class="font-medium text-[#165DFF]">8</span> Wiki 页
<br><span class="text-[#86909C]">+ 新建 2</span>
</td>
<td class="text-center py-3 px-4 text-[10px] text-[#86909C]">3 分钟前</td>
<td class="text-center py-3 px-4 text-xs">
<button class="text-[#165DFF] hover:underline" onclick="viewCompileProgress(this)">查看进度</button>
<span class="text-[#C9CDD4] mx-1">|</span>
<button class="text-[#86909C] hover:underline" onclick="cancelCompile(this)">取消</button>
</td>
</tr>
<!-- 待编译 1 -->
<tr class="hover:bg-[#F7F8FA] transition-colors">
<td class="py-3 px-4">
<div class="flex items-center gap-2.5">
<div class="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center flex-shrink-0">
<iconify-icon class="text-base text-[#FAAD14]" icon="mdi:file-document-outline"></iconify-icon>
</div>
<div class="min-w-0">
<p class="text-xs font-medium text-[#1D2129] truncate">指导案例 214 号:XX 科技公司诉 YY 网络公司买卖合同纠纷案</p>
<p class="text-[10px] text-[#86909C] mt-0.5">判决书 · 最高人民法院 · 2024</p>
</div>
</div>
</td>
<td class="text-center py-3 px-4 text-xs text-[#4E5969]">判决书</td>
<td class="text-center py-3 px-4">
<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-50 text-[#FAAD14]">
<iconify-icon class="text-xs" icon="mdi:clock-outline"></iconify-icon>
<span class="text-[10px] font-medium">待编译</span>
</span>
</td>
<td class="text-center py-3 px-4 text-[10px] text-[#86909C]">预计 ~5 页</td>
<td class="text-center py-3 px-4 text-[10px] text-[#86909C]">1 小时前</td>
<td class="text-center py-3 px-4 text-xs">
<button class="px-2.5 py-1 text-[10px] font-medium rounded-md bg-[#165DFF] text-white hover:bg-[#4080FF] transition-colors flex items-center gap-1 mx-auto" onclick="startCompile(this)">
<iconify-icon class="text-xs" icon="mdi:robot"></iconify-icon>
AI 编译
</button>
</td>
</tr>
<!-- 待编译 2 -->
<tr class="hover:bg-[#F7F8FA] transition-colors">
<td class="py-3 px-4">
<div class="flex items-center gap-2.5">
<div class="w-8 h-8 rounded-lg bg-purple-50 flex items-center justify-center flex-shrink-0">
<iconify-icon class="text-base text-purple-600" icon="mdi:file-word-box"></iconify-icon>
</div>
<div class="min-w-0">
<p class="text-xs font-medium text-[#1D2129] truncate">中华人民共和国民法典(合同编).docx</p>
<p class="text-[10px] text-[#86909C] mt-0.5">528 KB · 64 页 · 全国人大</p>
</div>
</div>
</td>
<td class="text-center py-3 px-4 text-xs text-[#4E5969]">Word</td>
<td class="text-center py-3 px-4">
<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-50 text-[#FAAD14]">
<iconify-icon class="text-xs" icon="mdi:clock-outline"></iconify-icon>
<span class="text-[10px] font-medium">待编译</span>
</span>
</td>
<td class="text-center py-3 px-4 text-[10px] text-[#86909C]">预计 ~12 页</td>
<td class="text-center py-3 px-4 text-[10px] text-[#86909C]">2 小时前</td>
<td class="text-center py-3 px-4 text-xs">
<button class="px-2.5 py-1 text-[10px] font-medium rounded-md bg-[#165DFF] text-white hover:bg-[#4080FF] transition-colors flex items-center gap-1 mx-auto" onclick="startCompile(this)">
<iconify-icon class="text-xs" icon="mdi:robot"></iconify-icon>
AI 编译
</button>
</td>
</tr>
<!-- 已编译 1 -->
<tr class="hover:bg-[#F7F8FA] transition-colors">
<td class="py-3 px-4">
<div class="flex items-center gap-2.5">
<div class="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
<iconify-icon class="text-base text-[#165DFF]" icon="mdi:file-pdf-box"></iconify-icon>
</div>
<div class="min-w-0">
<p class="text-xs font-medium text-[#1D2129] truncate">最高人民法院关于审理民间借贷案件适用法律若干问题的规定</p>
<p class="text-[10px] text-[#86909C] mt-0.5">法释 [2020] 17 号 · 最高人民法院</p>
</div>
</div>
</td>
<td class="text-center py-3 px-4 text-xs text-[#4E5969]">PDF</td>
<td class="text-center py-3 px-4">
<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-50 text-green-600">
<iconify-icon class="text-xs" icon="mdi:check-circle"></iconify-icon>
<span class="text-[10px] font-medium">已编译</span>
</span>
</td>
<td class="text-center py-3 px-4 text-[10px] text-[#4E5969]">
<span class="font-medium text-purple-600">11</span> Wiki 页
<br><span class="text-[#86909C]">更新 1 周前</span>
</td>
<td class="text-center py-3 px-4 text-[10px] text-[#86909C]">2024-08-18</td>
<td class="text-center py-3 px-4 text-xs">
<button class="text-[#165DFF] hover:underline" onclick="viewWikiPages(this)">查看 Wiki</button>
<span class="text-[#C9CDD4] mx-1">|</span>
<button class="text-[#165DFF] hover:underline" onclick="recompile(this)">重新编译</button>
</td>
</tr>
<!-- 已编译 2 -->
<tr class="hover:bg-[#F7F8FA] transition-colors">
<td class="py-3 px-4">
<div class="flex items-center gap-2.5">
<div class="w-8 h-8 rounded-lg bg-green-50 flex items-center justify-center flex-shrink-0">
<iconify-icon class="text-base text-green-600" icon="mdi:web"></iconify-icon>
</div>
<div class="min-w-0">
<p class="text-xs font-medium text-[#1D2129] truncate">王迁·网络环境下著作权侵权认定标准研究</p>
<p class="text-[10px] text-[#86909C] mt-0.5">《中国法学》2024 年第 1 期 · 学术文献</p>
</div>
</div>
</td>
<td class="text-center py-3 px-4 text-xs text-[#4E5969]">网页</td>
<td class="text-center py-3 px-4">
<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-50 text-green-600">
<iconify-icon class="text-xs" icon="mdi:check-circle"></iconify-icon>
<span class="text-[10px] font-medium">已编译</span>
</span>
</td>
<td class="text-center py-3 px-4 text-[10px] text-[#4E5969]">
<span class="font-medium text-purple-600">6</span> Wiki 页
<br><span class="text-[#86909C]">更新 3 天前</span>
</td>
<td class="text-center py-3 px-4 text-[10px] text-[#86909C]">2024-01-30</td>
<td class="text-center py-3 px-4 text-xs">
<button class="text-[#165DFF] hover:underline" onclick="viewWikiPages(this)">查看 Wiki</button>
<span class="text-[#C9CDD4] mx-1">|</span>
<button class="text-[#165DFF] hover:underline" onclick="recompile(this)">重新编译</button>
</td>
</tr>
<!-- 待编译 3 -->
<tr class="hover:bg-[#F7F8FA] transition-colors">
<td class="py-3 px-4">
<div class="flex items-center gap-2.5">
<div class="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center flex-shrink-0">
<iconify-icon class="text-base text-[#FAAD14]" icon="mdi:image-outline"></iconify-icon>
</div>
<div class="min-w-0">
<p class="text-xs font-medium text-[#1D2129] truncate">诉讼案件证据清单与举证指引(2024 修订版).pdf</p>
<p class="text-[10px] text-[#86909C] mt-0.5">律所内部 · 张律师上传 · 28 页</p>
</div>
</div>
</td>
<td class="text-center py-3 px-4 text-xs text-[#4E5969]">扫描件</td>
<td class="text-center py-3 px-4">
<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-50 text-[#FAAD14]">
<iconify-icon class="text-xs" icon="mdi:clock-outline"></iconify-icon>
<span class="text-[10px] font-medium">待编译</span>
</span>
</td>
<td class="text-center py-3 px-4 text-[10px] text-[#86909C]">预计 ~4 页</td>
<td class="text-center py-3 px-4 text-[10px] text-[#86909C]">昨天</td>
<td class="text-center py-3 px-4 text-xs">
<button class="px-2.5 py-1 text-[10px] font-medium rounded-md bg-[#165DFF] text-white hover:bg-[#4080FF] transition-colors flex items-center gap-1 mx-auto" onclick="startCompile(this)">
<iconify-icon class="text-xs" icon="mdi:robot"></iconify-icon>
AI 编译
</button>
</td>
</tr>
</tbody>
</table>
</div>
</div>

<!-- ============== Tab 2: Wiki 页面 ============== -->
<div id="kb-panel-wiki" class="kb-panel hidden space-y-4">
<div class="bg-white rounded-xl border border-[#E5E6EB] overflow-hidden">
<div class="p-3 border-b border-[#E5E6EB] flex items-center justify-between">
<div>
<h4 class="text-sm font-semibold text-[#1D2129] flex items-center gap-2">
<iconify-icon class="text-base text-purple-600" icon="mdi:graph"></iconify-icon>
Wiki 知识页
<span class="text-[10px] bg-purple-50 text-purple-600 px-1.5 py-0.5 rounded ml-1">由 LLM 维护</span>
</h4>
<p class="text-[10px] text-[#86909C] mt-0.5">每页基于原始资料自动生成,带交叉链接和反向引用。LLM 持续更新。</p>
</div>
<input id="kb-search-input" placeholder="搜索 Wiki 页面..." type="text" class="w-64 border border-[#E5E6EB] rounded-lg pl-3 pr-3 py-1.5 text-xs text-[#4E5969] focus:outline-none focus:border-[#165DFF] transition-colors"/>
</div>
<table class="w-full text-sm">
<thead>
<tr class="bg-[#F7F8FA] border-b border-[#E5E6EB]">
<th class="text-left py-2.5 px-4 text-xs font-semibold text-[#4E5969]">Wiki 页面</th>
<th class="text-center py-2.5 px-4 text-xs font-semibold text-[#4E5969] w-24">主题</th>
<th class="text-center py-2.5 px-4 text-xs font-semibold text-[#4E5969] w-28">来源 Raw</th>
<th class="text-center py-2.5 px-4 text-xs font-semibold text-[#4E5969] w-24">反向链接</th>
<th class="text-center py-2.5 px-4 text-xs font-semibold text-[#4E5969] w-28">更新</th>
</tr>
</thead>
<tbody class="divide-y divide-[#F2F3F5]">
<tr class="hover:bg-[#F7F8FA] transition-colors" data-knowledge-title="合同纠纷处理要点">
<td class="py-3 px-4">
<p class="text-xs font-medium text-[#1D2129]">合同纠纷处理要点</p>
<p class="text-[10px] text-[#86909C] mt-0.5">合同效力 / 违约责任 / 解除条件 / 损害赔偿</p>
</td>
<td class="text-center py-3 px-4"><span class="text-[10px] px-2 py-0.5 rounded bg-blue-50 text-[#165DFF]">民商事</span></td>
<td class="text-center py-3 px-4 text-[10px] text-[#4E5969]"><span class="font-medium text-purple-600">7</span> 原始</td>
<td class="text-center py-3 px-4 text-[10px] text-[#4E5969]">23 ↔</td>
<td class="text-center py-3 px-4 text-[10px] text-[#86909C]">2 天前</td>
</tr>
<tr class="hover:bg-[#F7F8FA] transition-colors" data-knowledge-title="民间借贷利息计算规则">
<td class="py-3 px-4">
<p class="text-xs font-medium text-[#1D2129]">民间借贷利息计算规则</p>
<p class="text-[10px] text-[#86909C] mt-0.5">利率上限 / LPR 4 倍 / 复利 / 逾期利息</p>
</td>
<td class="text-center py-3 px-4"><span class="text-[10px] px-2 py-0.5 rounded bg-blue-50 text-[#165DFF]">民商事</span></td>
<td class="text-center py-3 px-4 text-[10px] text-[#4E5969]"><span class="font-medium text-purple-600">3</span> 原始</td>
<td class="text-center py-3 px-4 text-[10px] text-[#4E5969]">15 ↔</td>
<td class="text-center py-3 px-4 text-[10px] text-[#86909C]">1 周前</td>
</tr>
<tr class="hover:bg-[#F7F8FA] transition-colors" data-knowledge-title="网络著作权侵权认定">
<td class="py-3 px-4">
<p class="text-xs font-medium text-[#1D2129]">网络著作权侵权认定</p>
<p class="text-[10px] text-[#86909C] mt-0.5">信息网络传播权 / 避风港原则 / 主观过错</p>
</td>
<td class="text-center py-3 px-4"><span class="text-[10px] px-2 py-0.5 rounded bg-purple-50 text-purple-600">知识产权</span></td>
<td class="text-center py-3 px-4 text-[10px] text-[#4E5969]"><span class="font-medium text-purple-600">4</span> 原始</td>
<td class="text-center py-3 px-4 text-[10px] text-[#4E5969]">11 ↔</td>
<td class="text-center py-3 px-4 text-[10px] text-[#86909C]">3 天前</td>
</tr>
<tr class="hover:bg-[#F7F8FA] transition-colors" data-knowledge-title="故意伤害罪辩护要点">
<td class="py-3 px-4">
<p class="text-xs font-medium text-[#1D2129]">故意伤害罪辩护要点</p>
<p class="text-[10px] text-[#86909C] mt-0.5">正当防卫 / 防卫过当 / 轻重伤鉴定</p>
</td>
<td class="text-center py-3 px-4"><span class="text-[10px] px-2 py-0.5 rounded bg-red-50 text-red-600">刑事</span></td>
<td class="text-center py-3 px-4 text-[10px] text-[#4E5969]"><span class="font-medium text-purple-600">5</span> 原始</td>
<td class="text-center py-3 px-4 text-[10px] text-[#4E5969]">9 ↔</td>
<td class="text-center py-3 px-4 text-[10px] text-[#86909C]">1 周前</td>
</tr>
<tr class="hover:bg-[#F7F8FA] transition-colors" data-knowledge-title="劳动合同解除实务">
<td class="py-3 px-4">
<p class="text-xs font-medium text-[#1D2129]">劳动合同解除实务</p>
<p class="text-[10px] text-[#86909C] mt-0.5">合法解除 / 经济补偿 / 违法解除赔偿</p>
</td>
<td class="text-center py-3 px-4"><span class="text-[10px] px-2 py-0.5 rounded bg-amber-50 text-[#FAAD14]">劳动争议</span></td>
<td class="text-center py-3 px-4 text-[10px] text-[#4E5969]"><span class="font-medium text-purple-600">2</span> 原始</td>
<td class="text-center py-3 px-4 text-[10px] text-[#4E5969]">6 ↔</td>
<td class="text-center py-3 px-4 text-[10px] text-[#86909C]">2 月前 ⚠</td>
</tr>
</tbody>
</table>
</div>
</div>

<!-- ============== Tab 3: 巡检 (Lint) ============== -->
<div id="kb-panel-lint" class="kb-panel hidden space-y-4">
<!-- 巡检状态栏 -->
<div class="bg-white rounded-xl border border-[#E5E6EB] p-4 flex items-center justify-between">
<div class="flex items-center gap-3">
<div class="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center">
<iconify-icon class="text-xl text-[#FAAD14]" icon="mdi:shield-search"></iconify-icon>
</div>
<div>
<p class="text-sm font-semibold text-[#1D2129]">上次巡检:7 天前</p>
<p class="text-[10px] text-[#86909C] mt-0.5">下次自动巡检: 3 天后 · 配置: 每周一次</p>
</div>
</div>
<button class="px-4 py-2 text-xs font-medium rounded-lg bg-[#165DFF] text-white hover:bg-[#4080FF] transition-colors flex items-center gap-1.5" onclick="runLintNow()">
<iconify-icon class="text-sm" icon="mdi:refresh"></iconify-icon>
立即巡检
</button>
</div>

<!-- 4 类巡检问题 -->
<div class="grid grid-cols-2 gap-4">
<!-- 孤儿页面 -->
<div class="bg-white rounded-xl border border-[#E5E6EB] overflow-hidden">
<div class="p-3 border-b border-[#E5E6EB] flex items-center gap-2">
<div class="w-7 h-7 rounded-lg bg-orange-50 flex items-center justify-center">
<iconify-icon class="text-base text-[#FA8C16]" icon="mdi:link-off"></iconify-icon>
</div>
<h5 class="text-sm font-semibold text-[#1D2129]">孤儿页面</h5>
<span class="text-[10px] bg-orange-50 text-[#FA8C16] px-1.5 py-0.5 rounded font-medium">3 项</span>
</div>
<div class="divide-y divide-[#F2F3F5]">
<div class="p-3 hover:bg-[#F7F8FA] transition-colors">
<p class="text-xs font-medium text-[#1D2129]">新业态用工关系认定</p>
<p class="text-[10px] text-[#86909C] mt-0.5">无反向链接 · 建议: 在「劳动合同解除」加入引用</p>
</div>
<div class="p-3 hover:bg-[#F7F8FA] transition-colors">
<p class="text-xs font-medium text-[#1D2129]">数据爬取合法性边界</p>
<p class="text-[10px] text-[#86909C] mt-0.5">无反向链接 · 建议: 在「网络著作权」加入引用</p>
</div>
<div class="p-3 hover:bg-[#F7F8FA] transition-colors">
<p class="text-xs font-medium text-[#1D2129]">破产债权申报实务</p>
<p class="text-[10px] text-[#86909C] mt-0.5">无反向链接 · 建议: 创建主题索引页</p>
</div>
</div>
</div>

<!-- 过期知识 -->
<div class="bg-white rounded-xl border border-[#E5E6EB] overflow-hidden">
<div class="p-3 border-b border-[#E5E6EB] flex items-center gap-2">
<div class="w-7 h-7 rounded-lg bg-red-50 flex items-center justify-center">
<iconify-icon class="text-base text-red-500" icon="mdi:clock-alert-outline"></iconify-icon>
</div>
<h5 class="text-sm font-semibold text-[#1D2129]">过期知识</h5>
<span class="text-[10px] bg-red-50 text-red-500 px-1.5 py-0.5 rounded font-medium">2 项 (1 紧急)</span>
</div>
<div class="divide-y divide-[#F2F3F5]">
<div class="p-3 hover:bg-[#F7F8FA] transition-colors bg-red-50/30">
<div class="flex items-center gap-2">
<p class="text-xs font-medium text-[#1D2129]">民间借贷利率上限</p>
<span class="text-[9px] bg-red-500 text-white px-1 py-0.5 rounded font-medium">紧急</span>
</div>
<p class="text-[10px] text-red-500 mt-0.5">最后更新: 8 个月前 · LPR 已调整 3 次,数据可能已过时</p>
<button class="text-[10px] text-[#165DFF] hover:underline mt-1">立即重新编译 →</button>
</div>
<div class="p-3 hover:bg-[#F7F8FA] transition-colors">
<p class="text-xs font-medium text-[#1D2129]">劳动合同解除实务</p>
<p class="text-[10px] text-[#86909C] mt-0.5">最后更新: 2 月前 · 建议加入 2024 年新司法解释</p>
</div>
</div>
</div>

<!-- 内容矛盾 -->
<div class="bg-white rounded-xl border border-[#E5E6EB] overflow-hidden">
<div class="p-3 border-b border-[#E5E6EB] flex items-center gap-2">
<div class="w-7 h-7 rounded-lg bg-yellow-50 flex items-center justify-center">
<iconify-icon class="text-base text-[#FAAD14]" icon="mdi:alert-outline"></iconify-icon>
</div>
<h5 class="text-sm font-semibold text-[#1D2129]">内容矛盾</h5>
<span class="text-[10px] bg-yellow-50 text-[#FAAD14] px-1.5 py-0.5 rounded font-medium">1 项</span>
</div>
<div class="divide-y divide-[#F2F3F5]">
<div class="p-3 hover:bg-[#F7F8FA] transition-colors">
<p class="text-xs font-medium text-[#1D2129]">网络服务提供者责任</p>
<p class="text-[10px] text-[#86909C] mt-0.5">两个 Wiki 页面表述不一致:</p>
<ul class="text-[10px] text-[#4E5969] mt-1 ml-3 space-y-0.5">
<li>• 「网络著作权侵权」: 需主观过错</li>
<li>• 「避风港原则适用」: 通知后即负责</li>
</ul>
<button class="text-[10px] text-[#165DFF] hover:underline mt-1.5">让 LLM 调和 →</button>
</div>
</div>
</div>

<!-- 缺失引用 -->
<div class="bg-white rounded-xl border border-[#E5E6EB] overflow-hidden">
<div class="p-3 border-b border-[#E5E6EB] flex items-center gap-2">
<div class="w-7 h-7 rounded-lg bg-blue-50 flex items-center justify-center">
<iconify-icon class="text-base text-[#165DFF]" icon="mdi:link-plus"></iconify-icon>
</div>
<h5 class="text-sm font-semibold text-[#1D2129]">缺失引用</h5>
<span class="text-[10px] bg-blue-50 text-[#165DFF] px-1.5 py-0.5 rounded font-medium">5 项</span>
</div>
<div class="divide-y divide-[#F2F3F5]">
<div class="p-3 hover:bg-[#F7F8FA] transition-colors">
<p class="text-xs font-medium text-[#1D2129]">合同纠纷处理要点</p>
<p class="text-[10px] text-[#86909C] mt-0.5">引用了 [[违约金酌减规则]] 但该页面不存在 · 建议创建</p>
</div>
<div class="p-3 hover:bg-[#F7F8FA] transition-colors">
<p class="text-xs font-medium text-[#1D2129]">故意伤害罪辩护要点</p>
<p class="text-[10px] text-[#86909C] mt-0.5">引用了 [[伤情重新鉴定]] 但该页面不存在 · 建议创建</p>
</div>
<div class="p-3 hover:bg-[#F7F8FA] transition-colors">
<p class="text-xs font-medium text-[#1D2129]">网络著作权侵权认定</p>
<p class="text-[10px] text-[#86909C] mt-0.5">引用了 [[合理使用判断]] 但该页面不存在</p>
</div>
</div>
</div>
</div>

<!-- Lint 健康度 -->
<div class="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-100 p-4">
<div class="flex items-center gap-2 mb-2">
<iconify-icon class="text-base text-[#165DFF]" icon="mdi:lightbulb-on-outline"></iconify-icon>
<h4 class="text-sm font-semibold text-[#1D2129]">LLM 巡检建议</h4>
</div>
<p class="text-[10px] text-[#4E5969]">知识库整体健康度评分 <span class="font-semibold text-[#1D2129]">82</span> / 100。已识别 11 个潜在问题。建议优先处理 <span class="text-red-500 font-semibold">1 项紧急</span>(民间借贷利率),并补充 5 个缺失引用页,可让健康度提升至 95+。</p>
<div class="flex gap-2 mt-3">
<button class="px-3 py-1.5 text-[10px] font-medium rounded-md bg-white border border-[#E5E6EB] text-[#4E5969] hover:bg-[#F7F8FA] transition-colors">查看趋势</button>
<button class="px-3 py-1.5 text-[10px] font-medium rounded-md bg-[#165DFF] text-white hover:bg-[#4080FF] transition-colors">一键处理全部</button>
</div>
</div>
</div>

</div>
</div>
'''

with open(r'E:\元枢法智前端\yuanxing\templates\views\knowledge.html', 'wb') as f:
    f.write(html.encode('utf-8'))

# 验证
print('总行数:', html.count('\n'))
print('<div:', html.count('<div'), '</div>:', html.count('</div>'))
print('panel ingest:', 'kb-panel-ingest' in html)
print('panel wiki:', 'kb-panel-wiki' in html)
print('panel lint:', 'kb-panel-lint' in html)
print('AI 编译按钮:', html.count('AI 编译'))
print('compile row count:', html.count('onclick="startCompile'))
