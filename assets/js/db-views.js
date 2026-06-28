/*
 * LexPrime 判例/法规/企业 3 个自建库 - UI 逻辑 v2
 * 2026-06-28 · A 任务: 接真实 API
 *
 * 数据源优先级:
 * 1. window.SERVER_API (运行 API 后端的 URL, 如 http://127.0.0.1:8000)
 * 2. 自动探测 http://localhost:8000
 * 3. Fallback: globalThis.MOCK_CASES / MOCK_LAWS / MOCK_COMPANIES
 *
 * API 字段与 mock 字段一致 (核心字段: id/cause/cause_category/cause_color/...)
 */

(function() {
    'use strict';

    // ===== 状态 =====
    var apiBase = null;
    var apiStatus = { cases: 'mock', laws: 'mock', companies: 'mock' };
    var dataCache = {
        cases: null,        // API 返回的 cases 列表
        laws: null,
        companies: null,
    };

    // ===== 通用工具 =====
    function escapeHtml(s) {
        if (s == null) return '';
        return String(s).replace(/[&<>"']/g, function(c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    function resolveApiBase() {
        if (typeof window.SERVER_API !== 'undefined' && window.SERVER_API) return window.SERVER_API;
        // 默认探测 localhost
        return 'http://localhost:8000';
    }

    async function fetchApi(path) {
        if (!apiBase) apiBase = resolveApiBase();
        try {
            var resp = await fetch(apiBase + path, {
                signal: AbortSignal.timeout(3000),
                headers: { 'Accept': 'application/json' },
            });
            if (resp.ok) return await resp.json();
        } catch (e) {
            // API 不可用, fallback
        }
        return null;
    }

    function setApiStatus(prefix, status) {
        apiStatus[prefix] = status;
        var el = document.getElementById(prefix + '-db-api-status');
        if (el) {
            el.innerHTML = status === 'live'
                ? '<span class="text-success font-medium">● 实时 API</span> · ' + apiBase
                : '<span class="text-fg-tertiary">● Mock 数据 (后端未启动)</span>';
        }
    }

    // ============================================================
    // 1. 判例库 (cases-db)
    // ============================================================
    function getActiveCases() {
        // 优先 API 缓存, fallback mock
        return (dataCache.cases && dataCache.cases.length > 0) ? dataCache.cases : (globalThis.MOCK_CASES || []);
    }

    async function loadCasesFromApi() {
        var data = await fetchApi('/api/cases?limit=200&full=true');
        if (data && Array.isArray(data) && data.length > 0) {
            // 适配: API 返回字段 {id, doc_id, case_id, case_name, court, cause, cause_category, cause_color, year, lex_score, view_count, favorite_count}
            // mock 字段 {id, doc_id, case_id, case_name, court, case_type, procedure, judgment_date, public_date, parties, cause, cause_category, cause_color, legal_basis, full_text, source, source_url, region, year, lex_score, lex_tags, view_count, favorite_count}
            // API 是简化版, mock 是完整版. 字段映射兼容.
            dataCache.cases = data;
            setApiStatus('cases', 'live');
            return true;
        }
        setApiStatus('cases', 'mock');
        return false;
    }

    function renderCasesDb() {
        var allCases = getActiveCases();
        var search = (document.getElementById('cases-db-search') || {}).value || '';
        var causeFilter = (document.getElementById('cases-db-cause-filter') || {}).value || 'all';
        var courtFilter = (document.getElementById('cases-db-court-filter') || {}).value || 'all';
        var sourceFilter = (document.getElementById('cases-db-source-filter') || {}).value || 'all';
        var yearFilter = (document.getElementById('cases-db-year-filter') || {}).value || 'all';
        var sortBy = (document.getElementById('cases-db-sort') || {}).value || 'lex_score_desc';

        var filtered = allCases.filter(function(c) {
            if (causeFilter !== 'all' && c.cause_category !== causeFilter) return false;
            // 法院级别 (前匹配)
            if (courtFilter !== 'all') {
                var court = c.court || '';
                if (court.indexOf(courtFilter) < 0) return false;
            }
            // source 在 API 返回中可能没有, fallback 时跳过
            if (sourceFilter !== 'all' && c.source && c.source !== sourceFilter) return false;
            if (yearFilter !== 'all' && String(c.year) !== yearFilter) return false;
            if (search) {
                var s = search.toLowerCase();
                var hay = (c.case_name + ' ' + (c.case_id || '') + ' ' + (c.cause || '') + ' ' + (c.full_text || '') + ' ' + (c.legal_basis || '')).toLowerCase();
                if (hay.indexOf(s) < 0) return false;
            }
            return true;
        });

        // 排序
        if (sortBy === 'year_desc') {
            filtered.sort(function(a, b) { return (b.year || 0) - (a.year || 0); });
        } else if (sortBy === 'view_count_desc') {
            filtered.sort(function(a, b) { return (b.view_count || 0) - (a.view_count || 0); });
        } else if (sortBy === 'law_refs_desc') {
            filtered.sort(function(a, b) { return (b.legal_basis_count || 0) - (a.legal_basis_count || 0); });
        } else {
            filtered.sort(function(a, b) { return (b.lex_score || 0) - (a.lex_score || 0); });
        }

        // 更新统计
        var elTotal = document.getElementById('cases-db-stat-total');
        if (elTotal) elTotal.textContent = allCases.length;
        var elGuide = document.getElementById('cases-db-stat-guide');
        if (elGuide) elGuide.textContent = allCases.filter(function(c) { return (c.lex_tags || []).indexOf('指导性案例') >= 0 || (c.case_name || '').indexOf('指导') >= 0; }).length;
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
            var sourceLabel = c.source ? (sourceLabels[c.source] || c.source) : 'API';
            var sourceColor = c.source ? (sourceColors[c.source] || 'bg-gray-100 text-gray-700') : 'bg-green-100 text-green-700';
            var causeColorCls = c.cause_color === 'indigo' ? 'bg-indigo-100 text-indigo-700' :
                                 c.cause_color === 'red' ? 'bg-red-100 text-red-700' :
                                 c.cause_color === 'pink' ? 'bg-pink-100 text-pink-700' :
                                 c.cause_color === 'orange' ? 'bg-orange-100 text-orange-700' :
                                 c.cause_color === 'purple' ? 'bg-purple-100 text-purple-700' :
                                 c.cause_color === 'gray' ? 'bg-gray-100 text-gray-700' :
                                 c.cause_color === 'blue' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700';
            return '<div class="bg-white rounded-xl border border-bg-border p-4 hover:shadow-md hover:border-brand/30 transition-all cursor-pointer" onclick="openCaseDbDetail(' + c.id + ')">'
                + '<div class="flex items-start justify-between gap-3 mb-2">'
                +   '<div class="flex items-center gap-2 flex-wrap flex-1 min-w-0">'
                +     '<h3 class="text-sm font-semibold text-fg-primary hover:text-brand transition-colors">' + escapeHtml(c.case_name || '(无名)') + '</h3>'
                +     '<span class="text-[10px] ' + sourceColor + ' px-1.5 py-0.5 rounded-full font-medium whitespace-nowrap">' + sourceLabel + '</span>'
                +     (c.cause ? '<span class="text-[10px] ' + causeColorCls + ' px-1.5 py-0.5 rounded-full font-medium whitespace-nowrap">' + escapeHtml(c.cause) + '</span>' : '')
                +   '</div>'
                +   '<div class="flex items-center gap-1 text-[10px] text-fg-tertiary whitespace-nowrap">'
                +     '<iconify-icon class="text-xs text-amber-500" icon="mdi:star"></iconify-icon>'
                +     (c.lex_score || 0)
                +     (c.view_count ? '<span class="text-fg-disabled ml-1">· ' + c.view_count + ' 浏览</span>' : '')
                +   '</div>'
                + '</div>'
                + '<div class="flex items-center gap-3 text-[10px] text-fg-tertiary flex-wrap">'
                +   (c.case_id ? '<span class="font-mono">' + escapeHtml(c.case_id) + '</span><span class="text-fg-disabled">·</span>' : '')
                +   (c.court ? '<span><iconify-icon class="text-xs" icon="mdi:scale-balance"></iconify-icon> ' + escapeHtml(c.court) + '</span><span class="text-fg-disabled">·</span>' : '')
                +   (c.judgment_date ? '<span><iconify-icon class="text-xs" icon="mdi:calendar"></iconify-icon> ' + c.judgment_date + '</span>' : '<span><iconify-icon class="text-xs" icon="mdi:calendar"></iconify-icon> --</span>')
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

    window.openCaseDbDetail = function(id) {
        var all = getActiveCases();
        var c = all.find(function(x) { return x.id === id; });
        if (!c) return;
        if (typeof showToast === 'function') {
            showToast('查看判例: ' + (c.case_name || '').substring(0, 30) + '... (开发中)');
        }
    };

    // 高频案由 tab (律师 80% 用前 6 个案由, 1-click 切换)
    window.filterCasesByPill = function(btn, cause) {
        // 切 active 样式
        document.querySelectorAll('.cases-db-pill').forEach(function(el) {
            el.className = 'cases-db-pill text-[11px] px-3 py-1 rounded-full bg-bg-subtle text-fg-secondary hover:bg-bg-hover font-medium transition-colors';
        });
        btn.className = 'cases-db-pill text-[11px] px-3 py-1 rounded-full bg-brand text-white font-medium transition-colors';
        // 同步到隐藏 select (兼容 renderCasesDb 内部读取)
        // 总重新填充 (防止空 select 残留)
        var sel = document.getElementById('cases-db-cause-filter');
        if (!sel) {
            sel = document.createElement('select');
            sel.id = 'cases-db-cause-filter';
            sel.style.display = 'none';
            document.body.appendChild(sel);
        }
        sel.innerHTML = '<option value="all">全部</option>'
            + '<option value="合同纠纷">合同纠纷</option>'
            + '<option value="婚姻家事">婚姻家事</option>'
            + '<option value="侵权责任">侵权责任</option>'
            + '<option value="刑事">刑事</option>'
            + '<option value="行政">行政</option>'
            + '<option value="知识产权">知识产权</option>'
            + '<option value="执行">执行</option>';
        sel.value = cause;
        renderCasesDb();
    };

    // ============================================================
    // 2. 法规库 (laws-db)
    // ============================================================
    function getActiveLaws() {
        return (dataCache.laws && dataCache.laws.length > 0) ? dataCache.laws : (globalThis.MOCK_LAWS || []);
    }

    async function loadLawsFromApi() {
        var data = await fetchApi('/api/laws?limit=200');
        if (data && Array.isArray(data) && data.length > 0) {
            dataCache.laws = data;
            setApiStatus('laws', 'live');
            return true;
        }
        setApiStatus('laws', 'mock');
        return false;
    }

    function renderLawsDb() {
        var allLaws = getActiveLaws();
        var search = (document.getElementById('laws-db-search') || {}).value || '';
        var typeFilter = (document.getElementById('laws-db-type-filter') || {}).value || 'all';
        var statusFilter = (document.getElementById('laws-db-status-filter') || {}).value || 'all';

        var filtered = allLaws.filter(function(l) {
            if (typeFilter !== 'all' && l.law_type !== typeFilter) return false;
            if (statusFilter !== 'all' && l.status !== statusFilter) return false;
            if (search) {
                var s = search.toLowerCase();
                var hay = (l.title + ' ' + (l.law_number || '') + ' ' + (l.summary || '') + ' ' + (l.full_text || '')).toLowerCase();
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
                +   '<h3 class="text-sm font-semibold text-fg-primary flex-1 min-w-0 hover:text-brand transition-colors">' + escapeHtml(l.title || '(无名)') + '</h3>'
                +   '<div class="flex items-center gap-1.5 flex-shrink-0">'
                +     (l.law_type ? '<span class="text-[10px] ' + tColor + ' px-1.5 py-0.5 rounded-full font-medium whitespace-nowrap">' + escapeHtml(l.law_type) + '</span>' : '')
                +     (l.status ? '<span class="text-[10px] ' + sColor + ' px-1.5 py-0.5 rounded-full font-medium whitespace-nowrap">' + escapeHtml(l.status) + '</span>' : '')
                +   '</div>'
                + '</div>'
                + (l.summary ? '<p class="text-xs text-fg-secondary leading-relaxed mb-2 line-clamp-2">' + escapeHtml(l.summary) + '</p>' : '')
                + '<div class="flex items-center gap-3 text-[10px] text-fg-tertiary flex-wrap">'
                +   (l.law_number ? '<span class="font-mono">' + escapeHtml(l.law_number) + '</span><span class="text-fg-disabled">·</span>' : '')
                +   (l.issuing_organ ? '<span><iconify-icon class="text-xs" icon="mdi:office-building-outline"></iconify-icon> ' + escapeHtml(l.issuing_organ) + '</span><span class="text-fg-disabled">·</span>' : '')
                +   (l.effective_date ? '<span><iconify-icon class="text-xs" icon="mdi:calendar"></iconify-icon> ' + l.effective_date + ' 生效</span>' : '')
                +   ((l.related_cases_count || 0) > 0
                    ?   '<span class="text-fg-disabled">·</span>'
                      + '<span class="text-brand"><iconify-icon class="text-xs" icon="mdi:gavel"></iconify-icon> ' + l.related_cases_count + ' 关联判例</span>'
                    : '')
                + '</div>'
            + '</div>';
        }).join('');
    }

    window.openLawDbDetail = function(id) {
        var all = getActiveLaws();
        var l = all.find(function(x) { return x.id === id; });
        if (!l) return;
        if (typeof showToast === 'function') {
            showToast('查看法规: ' + (l.title || '').substring(0, 30) + '... (开发中)');
        }
    };

    // ============================================================
    // 3. 企业征信 (companies-db)
    // ============================================================
    function getActiveCompanies() {
        return (dataCache.companies && dataCache.companies.length > 0) ? dataCache.companies : (globalThis.MOCK_COMPANIES || []);
    }

    async function loadCompaniesFromApi() {
        var data = await fetchApi('/api/companies?limit=200');
        if (data && Array.isArray(data) && data.length > 0) {
            dataCache.companies = data;
            setApiStatus('companies', 'live');
            return true;
        }
        setApiStatus('companies', 'mock');
        return false;
    }

    function renderCompaniesDb() {
        var allComps = getActiveCompanies();
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
                var hay = (c.company_name + ' ' + (c.legal_rep || '') + ' ' + (c.unified_id || '')).toLowerCase();
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
                +     '<h3 class="text-sm font-semibold text-fg-primary mb-1 hover:text-brand transition-colors">' + escapeHtml(c.company_name || '(无名)') + '</h3>'
                +     (c.unified_id ? '<p class="text-[10px] text-fg-tertiary font-mono">' + escapeHtml(c.unified_id) + '</p>' : '')
                +   '</div>'
                +   '<div class="flex flex-col items-end gap-1 flex-shrink-0">'
                +     (c.business_status ? '<span class="text-[10px] ' + sColor + ' px-1.5 py-0.5 rounded-full font-medium whitespace-nowrap">' + escapeHtml(c.business_status) + '</span>' : '')
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
        var all = getActiveCompanies();
        var c = all.find(function(x) { return x.id === id; });
        if (!c) return;
        if (typeof showToast === 'function') {
            showToast('查看企业: ' + (c.company_name || '').substring(0, 30) + '... (开发中)');
        }
    };

    // ============================================================
    // 初始化
    // ============================================================
    function bindInputs(prefix, renderFn) {
        var inputs = [
            prefix + '-search',
            prefix + '-cause-filter',
            prefix + '-type-filter',
            prefix + '-source-filter',
            prefix + '-year-filter',
            prefix + '-court-filter',
            prefix + '-sort',
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
            // 先渲染 mock, 然后 fetch API
            renderCasesDb();
            loadCasesFromApi().then(function(ok) {
                if (ok) renderCasesDb();
            });
        }
        // 法规
        var lawsView = document.getElementById('view-laws-db');
        if (lawsView && !lawsView.classList.contains('hidden') && !lawsView.dataset.dbInit) {
            lawsView.dataset.dbInit = '1';
            bindInputs('laws-db', renderLawsDb);
            renderLawsDb();
            loadLawsFromApi().then(function(ok) {
                if (ok) renderLawsDb();
            });
        }
        // 企业
        var compsView = document.getElementById('view-companies-db');
        if (compsView && !compsView.classList.contains('hidden') && !compsView.dataset.dbInit) {
            compsView.dataset.dbInit = '1';
            bindInputs('companies-db', renderCompaniesDb);
            renderCompaniesDb();
            loadCompaniesFromApi().then(function(ok) {
                if (ok) renderCompaniesDb();
            });
        }
    });
    if (document.body) {
        initObserver.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
    }

    // 全局暴露
    globalThis.renderCasesDb = renderCasesDb;
    globalThis.renderLawsDb = renderLawsDb;
    globalThis.renderCompaniesDb = renderCompaniesDb;
    globalThis.reloadCasesDb = function() { return loadCasesFromApi().then(function(ok) { renderCasesDb(); return ok; }); };
    globalThis.reloadLawsDb = function() { return loadLawsFromApi().then(function(ok) { renderLawsDb(); return ok; }); };
    globalThis.reloadCompaniesDb = function() { return loadCompaniesFromApi().then(function(ok) { renderCompaniesDb(); return ok; }); };
})();
