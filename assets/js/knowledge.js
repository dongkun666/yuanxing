/**
 * 知识库管理模块 - LLM Wiki 风格
 * 包含: 知识库搜索过滤 + 3 Tab 切换 + AI 编译交互
 * 加载: 在 script.js 之前同步加载 (使用其 AppState)
 */



    function applyKnowledgeFilter() {
        var rows = document.querySelectorAll('#view-knowledge tbody tr[data-knowledge-type]');
        var visible = 0;
        var kw = (_knowledgeSearch || '').toLowerCase().trim();
        rows.forEach(function(tr) {
            var t = tr.getAttribute('data-knowledge-type');
            var title = (tr.getAttribute('data-title') || '').toLowerCase();
            var matchType = (_knowledgeType === 'all') || (t === _knowledgeType);
            var matchKw = !kw || title.indexOf(kw) >= 0;
            tr.style.display = (matchType && matchKw) ? '' : 'none';
            if (matchType && matchKw) visible++;
        });
        // 更新底部「共 X 篇」
        var totalSpan = document.getElementById('kb-total-count');
        if (totalSpan) {
            totalSpan.textContent = '共 ' + visible + ' 篇文档，当前第 1 页';
        }
    }

    function switchKnowledgeMainTab(name, el) {
        // 1. 切换 tab 样式
        var tabs = document.querySelectorAll('#view-knowledge [id^="kb-tab-"]');
        tabs.forEach(function(t) {
            t.classList.remove('bg-[#F2F5FF]', 'text-[#165DFF]');
            t.classList.add('text-[#4E5969]', 'hover:bg-[#F7F8FA]');
            // 数字 badge 改灰
            var badge = t.querySelector('span:last-child');
            if (badge) {
                badge.classList.remove('bg-white', 'text-[#165DFF]');
                if (name === 'lint' && t.id === 'kb-tab-lint') {
                    badge.classList.add('bg-[#FFF3E0]', 'text-[#FAAD14]');
                } else {
                    badge.classList.add('bg-[#F2F3F5]', 'text-[#4E5969]');
                }
            }
        });
        el.classList.remove('text-[#4E5969]', 'hover:bg-[#F7F8FA]');
        el.classList.add('bg-[#F2F5FF]', 'text-[#165DFF]');
        // 当前 tab 的数字 badge 蓝底
        var activeBadge = el.querySelector('span:last-child');
        if (activeBadge && name === 'ingest') {
            activeBadge.classList.remove('bg-[#F2F3F5]', 'text-[#4E5969]');
            activeBadge.classList.add('bg-white', 'text-[#165DFF]');
        }

        // 2. 切换 panel
        var panels = document.querySelectorAll('#view-knowledge .kb-panel');
        panels.forEach(function(p) { p.classList.add('hidden'); });
        var active = document.getElementById('kb-panel-' + name);
        if (active) active.classList.remove('hidden');
    }

    function startCompile(btn) {
        var row = btn.closest('tr');
        if (!row) return;
        // 找到状态 cell (3rd td)
        var cells = row.querySelectorAll('td');
        var statusCell = cells[2];
        var impactCell = cells[3];
        var actionCell = cells[5];
        // 状态: 待编译 → 编译中
        statusCell.innerHTML = '<div class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 text-[#165DFF]"><iconify-icon class="text-xs animate-spin" icon="mdi:loading"></iconify-icon><span class="text-[10px] font-medium">编译中 5%</span></div><div class="w-full bg-[#F2F3F5] rounded-full h-1 mt-1.5"><div class="bg-[#165DFF] h-1 rounded-full" style="width: 5%"></div></div>';
        impactCell.innerHTML = '<span class="text-[10px] text-[#86909C]">预估中...</span>';
        actionCell.innerHTML = '<button class="text-[#165DFF] hover:underline" onclick="viewCompileProgress(this)">查看进度</button><span class="text-[#C9CDD4] mx-1">|</span><button class="text-[#86909C] hover:underline" onclick="cancelCompile(this)">取消</button>';

        // 模拟进度
        var pct = 5;
        var timer = setInterval(function() {
            pct += 7;
            if (pct >= 100) {
                pct = 100;
                clearInterval(timer);
                statusCell.innerHTML = '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-50 text-green-600"><iconify-icon class="text-xs" icon="mdi:check-circle"></iconify-icon><span class="text-[10px] font-medium">已编译</span></span>';
                impactCell.innerHTML = '<span class="text-[10px] text-[#4E5969]"><span class="font-medium text-purple-600">6</span> Wiki 页<br><span class="text-[#86909C]">刚刚</span></span>';
                actionCell.innerHTML = '<button class="text-[#165DFF] hover:underline" onclick="viewWikiPages(this)">查看 Wiki</button><span class="text-[#C9CDD4] mx-1">|</span><button class="text-[#165DFF] hover:underline" onclick="recompile(this)">重新编译</button>';
            } else {
                var fill = statusCell.querySelector('div div div');
                if (fill) fill.style.width = pct + '%';
                var txt = statusCell.querySelector('span.font-medium');
                if (txt) txt.textContent = '编译中 ' + pct + '%';
            }
        }, 200);
    }


    function cancelCompile(btn) {
        if (!confirm('确定取消本次 AI 编译？已完成的中间结果会保留。')) return;
        var row = btn.closest('tr');
        if (!row) return;
        var cells = row.querySelectorAll('td');
        var statusCell = cells[2];
        var actionCell = cells[5];
        statusCell.innerHTML = '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-50 text-[#FAAD14]"><iconify-icon class="text-xs" icon="mdi:clock-outline"></iconify-icon><span class="text-[10px] font-medium">待编译</span></span>';
        actionCell.innerHTML = '<button class="px-2.5 py-1 text-[10px] font-medium rounded-md bg-[#165DFF] text-white hover:bg-[#4080FF] transition-colors flex items-center gap-1 mx-auto" onclick="startCompile(this)"><iconify-icon class="text-xs" icon="mdi:robot"></iconify-icon>AI 编译</button>';
    }


    function recompile(btn) {
        if (!confirm('确定重新编译？LLM 会重新阅读原始资料并更新相关 Wiki 页面。')) return;
        var row = btn.closest('tr');
        if (!row) return;
        var cells = row.querySelectorAll('td');
        var statusCell = cells[2];
        var actionCell = cells[5];
        statusCell.innerHTML = '<div class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 text-[#165DFF]"><iconify-icon class="text-xs animate-spin" icon="mdi:loading"></iconify-icon><span class="text-[10px] font-medium">重新编译 10%</span></div><div class="w-full bg-[#F2F3F5] rounded-full h-1 mt-1.5"><div class="bg-[#165DFF] h-1 rounded-full" style="width: 10%"></div></div>';
        actionCell.innerHTML = '<button class="text-[#86909C] cursor-not-allowed">编译中...</button>';
        // 自动完成
        setTimeout(function() {
            statusCell.innerHTML = '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-50 text-green-600"><iconify-icon class="text-xs" icon="mdi:check-circle"></iconify-icon><span class="text-[10px] font-medium">已编译</span></span>';
            actionCell.innerHTML = '<button class="text-[#165DFF] hover:underline" onclick="viewWikiPages(this)">查看 Wiki</button><span class="text-[#C9CDD4] mx-1">|</span><button class="text-[#165DFF] hover:underline" onclick="recompile(this)">重新编译</button>';
        }, 3000);
    }


    function viewCompileProgress(btn) {
        var row = btn.closest('tr');
        var name = row ? row.querySelector('.text-xs.font-medium')?.textContent : '资料';
        alert('AI 编译进度:\n\n资料: ' + name + '\n阶段: 阅读原文 → 提取关键概念 → 检索相关 Wiki 页 → 更新/新建页面 → 写入反向链接\n\n预估剩余: 2 分钟');
    }


    function viewWikiPages(btn) {
        // 跳到 Wiki 页面
        if (typeof switchKnowledgeMainTab === 'function') {
            var wikiTab = document.getElementById('kb-tab-wiki');
            if (wikiTab) {
                switchKnowledgeMainTab('wiki', wikiTab);
            }
        }
    }


    function runLintNow() {
        var btn = event.currentTarget;
        var orig = btn.innerHTML;
        btn.innerHTML = '<iconify-icon class="text-sm animate-spin" icon="mdi:loading"></iconify-icon>巡检中...';
        btn.disabled = true;
        setTimeout(function() {
            btn.innerHTML = '<iconify-icon class="text-sm" icon="mdi:check-circle"></iconify-icon>巡检完成';
            setTimeout(function() {
                btn.innerHTML = orig;
                btn.disabled = false;
            }, 1500);
        }, 2500);
    }


    function simulateUpload() {
        alert('上传资料:\n\n支持 PDF / Word / 扫描件 / 网页 URL\n上传后状态为「待编译」,可手动触发「AI 编译」,或开启自动编译。');
    }
