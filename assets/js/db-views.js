/*
 * LexPrime 判例/法规/企业 3 个自建库 - UI 逻辑
 * 2026-06-28
 *
 * 数据源: data-db.js mock → 可选 backend API
 * 风格: 复用 judicial.js 模式
 */

(function() {
    'use strict';

    // ===== 通用工具 =====
    function escapeHtml(s) {
        if (s == null) return '';
        return String(s).replace(/[&<>"']/g, function(c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    function getApiBase() {
        if (typeof window.SERVER_API !== 'undefined' && window.SERVER_API) return window.SERVER_API;
        return 'http://localhost:8000';
    }

    async function tryApi(path) {
        try {
            var resp = await fetch(getApiBase() + path, { signal: AbortSignal.timeout(2000) });
            if (resp.ok) return await resp.json();
        } catch (e) {}
        return null;
    }

    function setApiStatus(text, isLive) {
        var el = document.getElementById('cases-db-api-status');
        if (el) el.innerHTML = isLive
            ? '<span class="text-success">● 实时 API</span>'
            : '<span class="text-fg-tertiary">● Mock 数据 (后端未启动)</span>';
    }

    // ============================================================
    // 1. 判例库 (cases-db)
    // ============================================================
    function renderCasesDb() {
        var allCases = globalThis.MOCK_CASES || [];
        var search = (document.getElementById('cases-db-search') || {}).value || '';
        var causeFilter = (document.getElementById('cases-db-cause-filter') || {}).value || 'all';
        var sourceFilter = (document.getElementById('cases-db-source-filter') || {}).value || 'all';
        var yearFilter = (document.getElementById('cases-db-year-filter') || {}).value || 'all';

        var filtered = allCases.filter(function(c) {
            if (causeFilter !== 'all' && c.cause_category !== causeFilter) return false;
            if (sourceFilter !== 'all' && c.source !== sourceFilter) return false;
            if (yearFilter !== 'all' && String(c.year) !== yearFilter) return false;
            if (search) {
                var s = search.toLowerCase();
                var hay = (c.case_name + ' ' + c.case_id + ' ' + c.cause + ' ' + (c.full_text || '') + ' ' + (c.legal_basis || '')).toLowerCase();
                if (hay.indexOf(s) < 0) return false;
            }
            return true;
        });

        // 排序: lex_score desc
        filtered.sort(function(a, b) { return (b.lex_score || 0) - (a.lex_score || 0); });

        // 更新统计
        var elTotal = document.getElementById('cases-db-stat-total');
        if (elTotal) elTotal.textContent = allCases.length;
        var elGuide = document.getElementById('cases-db-stat-guide');
        if (elGuide) elGuide.textContent = allCases.filter(function(c) { return (c.lex_tags || []).indexOf('指导性案例') >= 0; }).length;
        var elFirm = document.getElementById('cases-db-stat-firm');
        if (elFirm) elFirm.textContent = allCases.filter(function(c) { return c.source === 'lawyer_added'; }).length;
        var elCount = document.getElementById('cases-db-count');
        if (elCount) elCount.textContent = filtered.length;

        // 列表
        var container = document.getElementById('cases-db-list');
        if (!container) return;

        if (filtered.length === 0) {
            container.innerHTML = '<div class="bg-white rounded-xl border border-bg-border p-12 text-center">'
                + '<iconify-icon class="text-5xl text-fg-disabled" icon="mdi:book-search-outline"></iconify-icon>'
                + '<p class="text-sm text-fg-tertiary mt-3">未找到匹配的判例</p>'
                + '<p class="text-[10px] text-fg-disabled mt-1">试试调整筛选条件</p></div>';
            return;
        }

        var sourceLabels = {
            'court_cases': '人民法院案例库',
            'cncases': 'cncases 8500万',
            'lawyer_added': '律师自加'
        };
        var sourceColors = {
            'court_cases': 'bg-blue-100 text-blue-700',
            'cncases': 'bg-purple-100 text-purple-700',
            'lawyer_added': 'bg-amber-100 text-amber-700'
        };

        container.innerHTML = filtered.map(function(c) {
            var sourceLabel = sourceLabels[c.source] || c.source;
            var sourceColor = sourceColors[c.source] || 'bg-gray-100 text-gray-700';
            return '<div class="bg-white rounded-xl border border-bg-border p-4 hover:shadow-md hover:border-brand/30 transition-all cursor-pointer" onclick="openCaseDbDetail(' + c.id + ')">'
                + '<div class="flex items-start justify-between gap-3 mb-2">'
                +   '<div class="flex items-center gap-2 flex-wrap flex-1 min-w-0">'
                +     '<h3 class="text-sm font-semibold text-fg-primary hover:text-brand transition-colors">' + escapeHtml(c.case_name) + '</h3>'
                +     '<span class="text-[10px] ' + sourceColor + ' px-1.5 py-0.5 rounded-full font-medium whitespace-nowrap">' + sourceLabel + '</span>'
                +     '<span class="text-[10px] ' + (c.cause_color === 'indigo' ? 'bg-indigo-100 text-indigo-700' : c.cause_color === 'red' ? 'bg-red-100 text-red-700' : c.cause_color === 'pink' ? 'bg-pink-100 text-pink-700' : c.cause_color === 'orange' ? 'bg-orange-100 text-orange-700' : c.cause_color === 'purple' ? 'bg-purple-100 text-purple-700' : c.cause_color === 'gray' ? 'bg-gray-100 text-gray-700' : 'bg-blue-100 text-blue-700') + ' px-1.5 py-0.5 rounded-full font-medium whitespace-nowrap">' + escapeHtml(c.cause) + '</span>'
                +   '</div>'
                +   '<div class="flex items-center gap-1 text-[10px] text-fg-tertiary whitespace-nowrap">'
                +     '<iconify-icon class="text-xs text-amber-500" icon="mdi:star"></iconify-icon>'
                +     c.lex_score
                +   '</div>'
                + '</div>'
                + '<div class="flex items-center gap-3 text-[10px] text-fg-tertiary flex-wrap">'
                +   '<span class="font-mono">' + escapeHtml(c.case_id || '暂无案号') + '</span>'
                +   '<span class="text-fg-disabled">·</span>'
                +   '<span><iconify-icon class="text-xs" icon="mdi:scale-balance"></iconify-icon> ' + escapeHtml(c.court) + '</span>'
                +   '<span class="text-fg-disabled">·</span>'
                +   '<span><iconify-icon class="text-xs" icon="mdi:calendar"></iconify-icon> ' + (c.judgment_date || '--') + '</span>'
                +   ((c.lex_tags || []).length > 0
                    ?   '<span class="text-fg-disabled">·</span>'
                      + '<span>' + c.lex_tags.slice(0, 3).map(function(t) {
                          return '<span class="px-1.5 py-0.5 rounded bg-bg-subtle text-fg-secondary mr-1">#' + escapeHtml(t) + '</span>';
                      }).join('') + '</span>'
                    : '')
                + '</div>'
            + '</div>';
        }).join('');
    }

    // 判例详情 (简化, alert 形式)
    window.openCaseDbDetail = function(id) {
        var c = (globalThis.MOCK_CASES || []).find(function(x) { return x.id === id; });
        if (!c) return;
        if (typeof showToast === 'function') {
            showToast('查看判例: ' + c.case_name.substring(0, 30) + '...');
        }
        // TODO: 完整详情页 (Phase 2)
    };

    // ============================================================
    // 2. 法规库 (laws-db)
    // ============================================================
    function renderLawsDb() {
        var allLaws = globalThis.MOCK_LAWS || [];
        var search = (document.getElementById('laws-db-search') || {}).value || '';
        var typeFilter = (document.getElementById('laws-db-type-filter') || {}).value || 'all';
        var statusFilter = (document.getElementById('laws-db-status-filter') || {}).value || 'all';

        var filtered = allLaws.filter(function(l) {
            if (typeFilter !== 'all' && l.law_type !== typeFilter) return false;
            if (statusFilter !== 'all' && l.status !== statusFilter) return false;
            if (search) {
                var s = search.toLowerCase();
                var hay = (l.title + ' ' + l.law_number + ' ' + (l.summary || '') + ' ' + (l.full_text || '')).toLowerCase();
                if (hay.indexOf(s) < 0) return false;
            }
            return true;
        });

        // 更新统计
        var elTotal = document.getElementById('laws-db-stat-total');
        if (elTotal) elTotal.textContent = allLaws.length;
        var elLaw = document.getElementById('laws-db-stat-law');
        if (elLaw) elLaw.textContent = allLaws.filter(function(l) { return l.law_type === '法律'; }).length;
        var elInterp = document.getElementById('laws-db-stat-interp');
        if (elInterp) elInterp.textContent = allLaws.filter(function(l) { return l.law_type === '司法解释'; }).length;
        var elCount = document.getElementById('laws-db-count');
        if (elCount) elCount.textContent = filtered.length;

        var container = document.getElementById('laws-db-list');
        if (!container) return;

        if (filtered.length === 0) {
            container.innerHTML = '<div class="bg-white rounded-xl border border-bg-border p-12 text-center">'
                + '<iconify-icon class="text-5xl text-fg-disabled" icon="mdi:book-search-outline"></iconify-icon>'
                + '<p class="text-sm text-fg-tertiary mt-3">未找到匹配的法规</p></div>';
            return;
        }

        var typeColor = {
            '法律': 'bg-blue-100 text-blue-700',
            '行政法规': 'bg-purple-100 text-purple-700',
            '司法解释': 'bg-amber-100 text-amber-700',
            '地方性法规': 'bg-green-100 text-green-700',
            '部门规章': 'bg-gray-100 text-gray-700'
        };
        var statusColor = {
            '有效': 'bg-green-100 text-green-700',
            '已修订': 'bg-amber-100 text-amber-700',
            '已废止': 'bg-red-100 text-red-700'
        };

        container.innerHTML = filtered.map(function(l) {
            var tColor = typeColor[l.law_type] || 'bg-gray-100 text-gray-700';
            var sColor = statusColor[l.status] || 'bg-gray-100 text-gray-700';
            return '<div class="bg-white rounded-xl border border-bg-border p-4 hover:shadow-md hover:border-brand/30 transition-all cursor-pointer" onclick="openLawDbDetail(' + l.id + ')">'
                + '<div class="flex items-start justify-between gap-3 mb-2">'
                +   '<h3 class="text-sm font-semibold text-fg-primary flex-1 min-w-0 hover:text-brand transition-colors">' + escapeHtml(l.title) + '</h3>'
                +   '<div class="flex items-center gap-1.5 flex-shrink-0">'
                +     '<span class="text-[10px] ' + tColor + ' px-1.5 py-0.5 rounded-full font-medium whitespace-nowrap">' + escapeHtml(l.law_type) + '</span>'
                +     '<span class="text-[10px] ' + sColor + ' px-1.5 py-0.5 rounded-full font-medium whitespace-nowrap">' + escapeHtml(l.status) + '</span>'
                +   '</div>'
                + '</div>'
                + '<p class="text-xs text-fg-secondary leading-relaxed mb-2 line-clamp-2">' + escapeHtml(l.summary || '') + '</p>'
                + '<div class="flex items-center gap-3 text-[10px] text-fg-tertiary flex-wrap">'
                +   '<span class="font-mono">' + escapeHtml(l.law_number || '') + '</span>'
                +   '<span class="text-fg-disabled">·</span>'
                +   '<span><iconify-icon class="text-xs" icon="mdi:office-building-outline"></iconify-icon> ' + escapeHtml(l.issuing_organ || '') + '</span>'
                +   '<span class="text-fg-disabled">·</span>'
                +   '<span><iconify-icon class="text-xs" icon="mdi:calendar"></iconify-icon> ' + (l.effective_date || '--') + ' 生效</span>'
                +   ((l.related_cases_count || 0) > 0
                    ?   '<span class="text-fg-disabled">·</span>'
                      + '<span class="text-brand"><iconify-icon class="text-xs" icon="mdi:gavel"></iconify-icon> ' + l.related_cases_count + ' 关联判例</span>'
                    : '')
                + '</div>'
            + '</div>';
        }).join('');
    }

    window.openLawDbDetail = function(id) {
        var l = (globalThis.MOCK_LAWS || []).find(function(x) { return x.id === id; });
        if (!l) return;
        if (typeof showToast === 'function') {
            showToast('查看法规: ' + l.title);
        }
    };

    // ============================================================
    // 3. 企业征信 (companies-db)
    // ============================================================
    function renderCompaniesDb() {
        var allComps = globalThis.MOCK_COMPANIES || [];
        var search = (document.getElementById('companies-db-search') || {}).value || '';
        var regionFilter = (document.getElementById('companies-db-region-filter') || {}).value || 'all';
        var statusFilter = (document.getElementById('companies-db-status-filter') || {}).value || 'all';
        var zxgkOnly = (document.getElementById('companies-db-zxgk-only') || {}).checked || false;

        var filtered = allComps.filter(function(c) {
            if (regionFilter !== 'all' && c.region !== regionFilter) return false;
            if (statusFilter !== 'all' && c.business_status !== statusFilter) return false;
            if (zxgkOnly && !c.is_zxgk) return false;
            if (search) {
                var s = search.toLowerCase();
                var hay = (c.company_name + ' ' + c.legal_rep + ' ' + c.unified_id).toLowerCase();
                if (hay.indexOf(s) < 0) return false;
            }
            return true;
        });

        // 更新统计
        var elTotal = document.getElementById('companies-db-stat-total');
        if (elTotal) elTotal.textContent = allComps.length;
        var elZxgk = document.getElementById('companies-db-stat-zxgk');
        if (elZxgk) elZxgk.textContent = allComps.filter(function(c) { return c.is_zxgk; }).length;
        var elAbnormal = document.getElementById('companies-db-stat-abnormal');
        if (elAbnormal) elAbnormal.textContent = allComps.filter(function(c) { return c.business_status === '经营异常' || c.business_status === '吊销' || c.business_status === '注销'; }).length;
        var elCount = document.getElementById('companies-db-count');
        if (elCount) elCount.textContent = filtered.length;

        var container = document.getElementById('companies-db-list');
        if (!container) return;

        if (filtered.length === 0) {
            container.innerHTML = '<div class="bg-white rounded-xl border border-bg-border p-12 text-center">'
                + '<iconify-icon class="text-5xl text-fg-disabled" icon="mdi:office-building-cog-outline"></iconify-icon>'
                + '<p class="text-sm text-fg-tertiary mt-3">未找到匹配的企业</p></div>';
            return;
        }

        var statusColor = {
            '存续': 'bg-green-100 text-green-700',
            '注销': 'bg-gray-100 text-gray-700',
            '吊销': 'bg-red-100 text-red-700',
            '迁出': 'bg-amber-100 text-amber-700',
            '经营异常': 'bg-orange-100 text-orange-700'
        };

        container.innerHTML = filtered.map(function(c) {
            var sColor = statusColor[c.business_status] || 'bg-gray-100 text-gray-700';
            return '<div class="bg-white rounded-xl border border-bg-border p-4 hover:shadow-md hover:border-brand/30 transition-all cursor-pointer" onclick="openCompanyDbDetail(' + c.id + ')">'
                + '<div class="flex items-start justify-between gap-3 mb-2">'
                +   '<div class="flex-1 min-w-0">'
                +     '<h3 class="text-sm font-semibold text-fg-primary mb-1 hover:text-brand transition-colors">' + escapeHtml(c.company_name) + '</h3>'
                +     '<p class="text-[10px] text-fg-tertiary font-mono">' + escapeHtml(c.unified_id) + '</p>'
                +   '</div>'
                +   '<div class="flex flex-col items-end gap-1 flex-shrink-0">'
                +     '<span class="text-[10px] ' + sColor + ' px-1.5 py-0.5 rounded-full font-medium whitespace-nowrap">' + escapeHtml(c.business_status) + '</span>'
                +     (c.is_zxgk ? '<span class="text-[10px] bg-red-100 text-red-700 px-1.5 py-0.5 rounded-full font-medium whitespace-nowrap flex items-center gap-0.5"><iconify-icon class="text-xs" icon="mdi:alert-decagram"></iconify-icon> 失信</span>' : '')
                +   '</div>'
                + '</div>'
                + '<div class="grid grid-cols-2 gap-2 text-[11px] mt-2">'
                +   '<div><span class="text-fg-tertiary">法人:</span> <span class="text-fg-primary">' + escapeHtml(c.legal_rep || '--') + '</span></div>'
                +   '<div><span class="text-fg-tertiary">注册资本:</span> <span class="text-fg-primary">' + escapeHtml(c.registered_capital || '--') + '</span></div>'
                +   '<div><span class="text-fg-tertiary">成立日期:</span> <span class="text-fg-primary">' + (c.establish_date || '--') + '</span></div>'
                +   '<div><span class="text-fg-tertiary">行业:</span> <span class="text-fg-primary">' + escapeHtml(c.industry || '--') + '</span></div>'
                + '</div>'
                + (c.is_zxgk && c.zxgk_reason
                    ? '<div class="mt-2 p-2 bg-red-50 rounded text-[10px] text-red-700 leading-relaxed">'
                      + '<iconify-icon class="text-xs" icon="mdi:alert-circle"></iconify-icon> '
                      + '<span class="font-semibold">失信情形:</span> ' + escapeHtml(c.zxgk_reason) + ' · ' + escapeHtml(c.zxgk_court || '') + ' · ' + escapeHtml(c.zxgk_case_no || '')
                      + '</div>'
                    : '')
            + '</div>';
        }).join('');
    }

    window.openCompanyDbDetail = function(id) {
        var c = (globalThis.MOCK_COMPANIES || []).find(function(x) { return x.id === id; });
        if (!c) return;
        if (typeof showToast === 'function') {
            showToast('查看企业: ' + c.company_name);
        }
    };

    // ============================================================
    // 初始化 (view 切换时自动渲染)
    // ============================================================
    function bindInputs(prefix, renderFn) {
        var inputs = [
            prefix + '-search',
            prefix + '-cause-filter',
            prefix + '-type-filter',
            prefix + '-source-filter',
            prefix + '-year-filter',
            prefix + '-status-filter',
            prefix + '-region-filter',
            prefix + '-zxgk-only'
        ];
        inputs.forEach(function(id) {
            var el = document.getElementById(id);
            if (el) {
                el.addEventListener('input', renderFn);
                el.addEventListener('change', renderFn);
            }
        });
    }

    var initObserver = new MutationObserver(function() {
        // 判例
        var casesView = document.getElementById('view-cases-db');
        if (casesView && !casesView.classList.contains('hidden') && !casesView.dataset.dbInit) {
            casesView.dataset.dbInit = '1';
            bindInputs('cases-db', renderCasesDb);
            renderCasesDb();
            // 检查 API
            tryApi('/api/cases?limit=1').then(function(data) {
                setApiStatus(data ? 'live' : 'mock', !!data);
            });
        }
        // 法规
        var lawsView = document.getElementById('view-laws-db');
        if (lawsView && !lawsView.classList.contains('hidden') && !lawsView.dataset.dbInit) {
            lawsView.dataset.dbInit = '1';
            bindInputs('laws-db', renderLawsDb);
            renderLawsDb();
        }
        // 企业
        var compsView = document.getElementById('view-companies-db');
        if (compsView && !compsView.classList.contains('hidden') && !compsView.dataset.dbInit) {
            compsView.dataset.dbInit = '1';
            bindInputs('companies-db', renderCompaniesDb);
            renderCompaniesDb();
        }
    });
    if (document.body) {
        initObserver.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
    }

    // 双绑定
    globalThis.renderCasesDb = renderCasesDb;
    globalThis.renderLawsDb = renderLawsDb;
    globalThis.renderCompaniesDb = renderCompaniesDb;
})();
