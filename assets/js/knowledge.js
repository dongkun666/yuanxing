/**
 * 知识库管理模块 - LLM Wiki 风格
 * 包含: 知识库搜索过滤 + 3 Tab 切换 + AI 编译交互
 * 加载: 在 script.js 之前同步加载 (使用其 AppState)
 */

function applyKnowledgeFilter() {
    var rows = document.querySelectorAll('#view-knowledge tbody tr[data-knowledge-type]');
    var visible = 0;
    var kw = (_knowledgeSearch || '').toLowerCase().trim();
    rows.forEach(function (tr) {
        var t = tr.getAttribute('data-knowledge-type');
        var title = (tr.getAttribute('data-title') || '').toLowerCase();
        var matchType = _knowledgeType === 'all' || t === _knowledgeType;
        var matchKw = !kw || title.indexOf(kw) >= 0;
        tr.style.display = matchType && matchKw ? '' : 'none';
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
    tabs.forEach(function (t) {
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
    panels.forEach(function (p) {
        p.classList.add('hidden');
    });
    var active = document.getElementById('kb-panel-' + name);
    if (active) active.classList.remove('hidden');
}

/**
 * AI 编译 - 接真后端 (ai-service):
 *   1) POST /api/ocr   (如果用户选择了文件, 提取文本)
 *   2) POST /v1/generate (LLM 编译为 Wiki 页)
 * 后端不可达时回退到本地模拟状态 (原 5% → 100% 进度条)
 *
 * Phase 3 P0: 接 ai-service (Python FastAPI :8088)
 */
function startCompile(btn) {
    var row = btn.closest('tr');
    if (!row) return;
    var cells = row.querySelectorAll('td');
    var statusCell = cells[2];
    var impactCell = cells[3];
    var actionCell = cells[5];

    // 找原始资料名称 (1st td)
    var rawName = cells[0] ? cells[0].textContent.trim() : '';
    var rawType = cells[1] ? cells[1].textContent.trim() : 'document';

    // 状态: 待编译 → 编译中
    statusCell.innerHTML =
        '<div class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-brand-tint text-brand"><iconify-icon class="text-xs animate-spin" icon="mdi:loading"></iconify-icon><span class="text-[10px] font-medium">编译中 5%</span></div><div class="w-full bg-bg-subtle rounded-full h-1 mt-1.5"><div class="bg-brand h-1 rounded-full" style="width: 5%"></div></div>';
    impactCell.innerHTML = '<span class="text-[10px] text-fg-tertiary">OCR 提取中...</span>';
    actionCell.innerHTML =
        '<button class="text-brand hover:underline" onclick="viewCompileProgress(this)">查看进度</button><span class="text-fg-disabled mx-1">|</span><button class="text-fg-tertiary hover:underline" onclick="cancelCompile(this)">取消</button>';

    // 内部模拟定时器 (fallback 时用)
    var pct = 5;
    var timer = null;
    var backendOk = false;

    function updateProgress(p, label) {
        var fill = statusCell.querySelector('div div div');
        if (fill) fill.style.width = p + '%';
        var txt = statusCell.querySelector('span.font-medium');
        if (txt) txt.textContent = label || '编译中 ' + p + '%';
    }

    function completeSuccess(wikiPageCount) {
        if (timer) clearInterval(timer);
        statusCell.innerHTML =
            '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-success-tint text-success"><iconify-icon class="text-xs" icon="mdi:check-circle"></iconify-icon><span class="text-[10px] font-medium">已编译</span></span>';
        impactCell.innerHTML =
            '<span class="text-[10px] text-fg-secondary"><span class="font-medium text-wiki">' +
            (wikiPageCount || 6) +
            '</span> Wiki 页<br><span class="text-fg-tertiary">刚刚</span></span>';
        actionCell.innerHTML =
            '<button class="text-brand hover:underline" onclick="viewWikiPages(this)">查看 Wiki</button><span class="text-fg-disabled mx-1">|</span><button class="text-brand hover:underline" onclick="recompile(this)">重新编译</button>';
    }

    function fallbackToMock() {
        // 后端不可达, 用本地模拟进度
        if (backendOk) return;
        backendOk = false;
        if (timer) clearInterval(timer);
        pct = 5;
        impactCell.innerHTML = '<span class="text-[10px] text-fg-tertiary">本地模拟 (后端未启动)</span>';
        timer = setInterval(function () {
            pct += 7;
            if (pct >= 100) {
                completeSuccess(6);
            } else {
                updateProgress(pct);
            }
        }, 200);
    }

    // ===== 尝试调真后端 =====
    // 注意: 当前 row 没有真实文件 (mock UI), 直接调 LLM 编译 (假设 OCR 已完成)
    // 真实场景: 用户上传 PDF → 先 OCR → 再 LLM
    if (typeof API !== 'undefined' && API.knowledge && API.knowledge.compile) {
        // 准备 mock 文本 (真实文件会从 OCR 拿)
        var mockText = rawName + ' - 模拟原始资料文本内容...';
        updateProgress(15, 'OCR 提取中...');

        API.ocr
            .extract(new Blob([mockText], { type: 'text/plain' }))
            .then(function (ocrRes) {
                updateProgress(40, 'LLM 编译中...');
                if (!ocrRes.ok) {
                    console.warn('[knowledge] OCR 后端不可达, 回退 mock:', ocrRes.error);
                    throw new Error('OCR fail');
                }
                var rawText = (ocrRes.data && ocrRes.data.text) || mockText;
                return API.knowledge.compile(rawText, {
                    source: rawType,
                    metadata: { name: rawName }
                });
            })
            .then(function (llmRes) {
                if (!llmRes.ok) {
                    console.warn('[knowledge] LLM 后端不可达, 回退 mock:', llmRes.error);
                    throw new Error('LLM fail');
                }
                backendOk = true;
                if (timer) clearInterval(timer);
                // LLM 完成: 估算生成的 Wiki 页数 (completion 长度 / 200 字符)
                var completion = (llmRes.data && llmRes.data.completion) || '';
                var wikiCount = Math.max(1, Math.min(12, Math.ceil(completion.length / 300)));
                if (typeof showToast === 'function') {
                    showToast(
                        'LLM 编译完成 (用时 ' + ((llmRes.data && llmRes.data.latency_ms) || 0).toFixed(0) + 'ms)'
                    );
                }
                completeSuccess(wikiCount);
            })
            .catch(function (err) {
                console.warn('[knowledge] 后端链路失败, 回退 mock:', err.message);
                fallbackToMock();
            });

        // 超时保护: 5s 后端没响应 → fallback
        setTimeout(function () {
            if (!backendOk && pct < 100) {
                // 检查进度条还在动没
                var fill = statusCell.querySelector('div div div');
                if (fill && parseInt(fill.style.width || '0') < 60) {
                    console.warn('[knowledge] 后端超时 (5s), 回退 mock');
                    fallbackToMock();
                }
            }
        }, 5000);
    } else {
        // api.js 还没加载 (异常), 直接 mock
        fallbackToMock();
    }
}

async function cancelCompile(btn) {
    var confirmed = await Utils.showConfirm('确定取消本次 AI 编译？已完成的中间结果会保留。');
    if (!confirmed) return;
    var row = btn.closest('tr');
    if (!row) return;
    var cells = row.querySelectorAll('td');
    var statusCell = cells[2];
    var actionCell = cells[5];
    statusCell.innerHTML =
        '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-50 text-[#FAAD14]"><iconify-icon class="text-xs" icon="mdi:clock-outline"></iconify-icon><span class="text-[10px] font-medium">待编译</span></span>';
    actionCell.innerHTML =
        '<button class="px-2.5 py-1 text-[10px] font-medium rounded-md bg-[#165DFF] text-white hover:bg-[#4080FF] transition-colors flex items-center gap-1 mx-auto" onclick="startCompile(this)"><iconify-icon class="text-xs" icon="mdi:robot"></iconify-icon>AI 编译</button>';
}

async function recompile(btn) {
    var confirmed = await Utils.showConfirm('确定重新编译？LLM 会重新阅读原始资料并更新相关 Wiki 页面。');
    if (!confirmed) return;
    var row = btn.closest('tr');
    if (!row) return;
    var cells = row.querySelectorAll('td');
    var statusCell = cells[2];
    var actionCell = cells[5];
    statusCell.innerHTML =
        '<div class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-50 text-[#165DFF]"><iconify-icon class="text-xs animate-spin" icon="mdi:loading"></iconify-icon><span class="text-[10px] font-medium">重新编译 10%</span></div><div class="w-full bg-[#F2F3F5] rounded-full h-1 mt-1.5"><div class="bg-[#165DFF] h-1 rounded-full" style="width: 10%"></div></div>';
    actionCell.innerHTML = '<button class="text-[#86909C] cursor-not-allowed">编译中...</button>';
    // 自动完成
    setTimeout(function () {
        statusCell.innerHTML =
            '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-50 text-green-600"><iconify-icon class="text-xs" icon="mdi:check-circle"></iconify-icon><span class="text-[10px] font-medium">已编译</span></span>';
        actionCell.innerHTML =
            '<button class="text-[#165DFF] hover:underline" onclick="viewWikiPages(this)">查看 Wiki</button><span class="text-[#C9CDD4] mx-1">|</span><button class="text-[#165DFF] hover:underline" onclick="recompile(this)">重新编译</button>';
    }, 3000);
}

function viewCompileProgress(btn) {
    var row = btn.closest('tr');
    var name = row ? row.querySelector('.text-xs.font-medium')?.textContent : '资料';
    var content =
        '<p class="text-sm text-fg-secondary mb-2">AI 编译进度:</p>' +
        '<div class="bg-bg-subtle p-3 rounded-lg text-xs text-fg-secondary space-y-1">' +
        '<p><strong>资料:</strong> ' + Utils.escapeHtml(name) + '</p>' +
        '<p><strong>阶段:</strong> 阅读原文 → 提取关键概念 → 检索相关 Wiki 页 → 更新/新建页面 → 写入反向链接</p>' +
        '<p><strong>预估剩余:</strong> 2 分钟</p>' +
        '</div>';
    Utils.showModal({
        id: 'compile-progress-modal',
        title: '编译进度',
        content: content,
        size: 'md',
        icon: 'mdi:progress-clock'
    });
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
    setTimeout(function () {
        btn.innerHTML = '<iconify-icon class="text-sm" icon="mdi:check-circle"></iconify-icon>巡检完成';
        setTimeout(function () {
            btn.innerHTML = orig;
            btn.disabled = false;
        }, 1500);
    }, 2500);
}

function simulateUpload() {
    var content =
        '<p class="text-sm text-fg-secondary mb-2">上传资料:</p>' +
        '<div class="bg-bg-subtle p-3 rounded-lg text-xs text-fg-secondary space-y-1">' +
        '<p>支持 PDF / Word / 扫描件 / 网页 URL</p>' +
        '<p>上传后状态为「待编译」,可手动触发「AI 编译」,或开启自动编译。</p>' +
        '</div>';
    Utils.showModal({
        id: 'upload-info-modal',
        title: '上传资料说明',
        content: content,
        size: 'md',
        icon: 'mdi:cloud-upload-outline'
    });
}
