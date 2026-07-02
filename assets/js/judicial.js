/**
 * 司法观点库 - UI 逻辑 (2026-06-28)
 *
 * 集成到 knowledge.html 的第 4 个 tab
 * 数据: judicial-data.js (12 条 mock 司法观点)
 * 功能: 列表 / 详情 / 搜索 / 案由筛选 / 收藏
 */

(function() {
    'use strict';

    // ===== 状态 =====
    var currentView = 'list';  // 'list' | 'detail'
    var currentPointId = null;
    var currentSearchKw = '';
    var currentCauseFilter = 'all';
    var currentSortBy = 'date';  // 'date' | 'cause' | 'source'

    // 收藏列表 (用 localStorage 持久化, 失败时用内存)
    var _favorites = {};
    function loadFavorites() {
        try {
            var raw = localStorage.getItem('lexprime_judicial_favorites');
            if (raw) _favorites = JSON.parse(raw);
        } catch (e) {
            _favorites = {};
        }
    }
    function saveFavorites() {
        try {
            localStorage.setItem('lexprime_judicial_favorites', JSON.stringify(_favorites));
        } catch (e) {}
    }
    loadFavorites();

    // ===== 工具 =====
    function escapeHtml(s) {
        if (s === null || s === undefined) return '';
        return String(s).replace(/[&<>"']/g, function(c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', '\'': '&#39;' }[c];
        });
    }

    // ===== 列表渲染 =====
    function renderJudicialList() {
        var panel = document.getElementById('kb-panel-judicial');
        if (!panel) return;
        currentView = 'list';
        currentPointId = null;

        var points = filterAndSortPoints();
        var causes = getJudicialCauses();

        var html =
            // 搜索 + 筛选
            '<div class="bg-white rounded-xl border border-bg-border p-5 space-y-3">' +
                '<div class="flex items-center gap-2 flex-wrap">' +
                    '<div class="flex-1 relative min-w-[200px]">' +
                        '<iconify-icon class="absolute left-3 top-1/2 -translate-y-1/2 text-fg-tertiary text-base" icon="mdi:magnify"></iconify-icon>' +
                        '<input type="text" id="judicial-search-input" placeholder="搜索观点标题/全文/法条/案例号..." class="w-full bg-bg-subtle border border-bg-border rounded-lg pl-9 pr-3 py-2 text-sm text-fg-primary focus:outline-none focus:border-brand focus:bg-white transition-colors" value="' + escapeHtml(currentSearchKw) + '" oninput="onJudicialSearch(this.value)"/>' +
                    '</div>' +
                    '<select class="appearance-none bg-bg-subtle border border-bg-border rounded-lg pl-3 pr-9 py-2 text-sm text-fg-primary focus:outline-none focus:border-brand focus:bg-white transition-colors" onchange="onJudicialCauseFilter(this.value)">' +
                        '<option value="all"' + (currentCauseFilter === 'all' ? ' selected' : '') + '>全部案由</option>' +
                        causes.map(function(c) {
                            return '<option value="' + escapeHtml(c) + '"' + (currentCauseFilter === c ? ' selected' : '') + '>' + escapeHtml(c) + '</option>';
                        }).join('') +
                    '</select>' +
                    '<select class="appearance-none bg-bg-subtle border border-bg-border rounded-lg pl-3 pr-9 py-2 text-sm text-fg-primary focus:outline-none focus:border-brand focus:bg-white transition-colors" onchange="onJudicialSort(this.value)">' +
                        '<option value="date"' + (currentSortBy === 'date' ? ' selected' : '') + '>按时间</option>' +
                        '<option value="cause"' + (currentSortBy === 'cause' ? ' selected' : '') + '>按案由</option>' +
                        '<option value="source"' + (currentSortBy === 'source' ? ' selected' : '') + '>按来源</option>' +
                    '</select>' +
                '</div>' +
                '<div class="flex items-center justify-between text-[10px] text-fg-tertiary">' +
                    '<span><iconify-icon class="text-xs" icon="mdi:format-list-bulleted"></iconify-icon> 共 ' + points.length + ' 条观点' + (currentSearchKw || currentCauseFilter !== 'all' ? ' (已筛选)' : '') + '</span>' +
                    '<span><iconify-icon class="text-xs" icon="mdi:star-outline"></iconify-icon> 已收藏 ' + Object.keys(_favorites).length + ' 条</span>' +
                '</div>' +
            '</div>' +
            // 列表
            '<div class="space-y-2.5">' + (points.length === 0
                ? '<div class="bg-white rounded-xl border border-bg-border p-12 text-center"><iconify-icon class="text-5xl text-fg-disabled" icon="mdi:book-search-outline"></iconify-icon><p class="text-sm text-fg-tertiary mt-3">未找到匹配的司法观点</p><p class="text-[10px] text-fg-disabled mt-1">试试调整搜索关键词或清除筛选</p></div>'
                : points.map(function(p) { return renderPointCard(p); }).join('')
            ) + '</div>';

        panel.innerHTML = html;
    }

    function renderPointCard(p) {
        var isFav = !!_favorites[p.id];
        var causeColorMap = {
            'blue': 'bg-blue-100 text-blue-700',
            'pink': 'bg-pink-100 text-pink-700',
            'orange': 'bg-orange-100 text-orange-700',
            'red': 'bg-red-100 text-red-700',
            'purple': 'bg-purple-100 text-purple-700',
            'indigo': 'bg-indigo-100 text-indigo-700',
            'gray': 'bg-gray-100 text-gray-700'
        };
        var causeCls = causeColorMap[p.causeColor] || 'bg-blue-100 text-blue-700';

        return '<div class="bg-white rounded-xl border border-bg-border p-4 hover:shadow-md hover:border-brand/30 transition-all cursor-pointer" onclick="openJudicialPoint(\'' + p.id + '\')">' +
            '<div class="flex items-start justify-between gap-3 mb-2">' +
                '<div class="flex items-center gap-2 flex-wrap flex-1 min-w-0">' +
                    '<h3 class="text-sm font-semibold text-fg-primary hover:text-brand transition-colors">' + escapeHtml(p.title) + '</h3>' +
                    '<span class="text-[10px] ' + causeCls + ' px-1.5 py-0.5 rounded-full font-medium whitespace-nowrap">' + escapeHtml(p.cause) + '</span>' +
                '</div>' +
                '<button class="text-fg-tertiary hover:text-amber-500 transition-colors flex-shrink-0" onclick="event.stopPropagation(); toggleJudicialFavorite(\'' + p.id + '\')" title="' + (isFav ? '取消收藏' : '收藏') + '">' +
                    '<iconify-icon class="text-base" icon="' + (isFav ? 'mdi:star' : 'mdi:star-outline') + '"></iconify-icon>' +
                '</button>' +
            '</div>' +
            '<p class="text-xs text-fg-secondary leading-relaxed line-clamp-2 mb-2">' + escapeHtml(p.summary) + '</p>' +
            '<div class="flex items-center gap-3 text-[10px] text-fg-tertiary flex-wrap">' +
                '<span class="inline-flex items-center gap-0.5"><iconify-icon class="text-xs" icon="mdi:account-outline"></iconify-icon> ' + escapeHtml(p.author) + '</span>' +
                '<span class="text-fg-disabled">·</span>' +
                '<span class="inline-flex items-center gap-0.5"><iconify-icon class="text-xs" icon="mdi:calendar-outline"></iconify-icon> ' + escapeHtml(p.date) + '</span>' +
                '<span class="text-fg-disabled">·</span>' +
                '<span class="inline-flex items-center gap-0.5"><iconify-icon class="text-xs" icon="mdi:bookshelf"></iconify-icon> ' + escapeHtml(p.source) + '</span>' +
                ((p.tags || []).length > 0
                    ? '<span class="text-fg-disabled">·</span>' +
                      '<span class="inline-flex items-center gap-0.5">' + p.tags.slice(0, 3).map(function(t) {
                        return '<span class="px-1.5 py-0.5 rounded bg-bg-subtle text-fg-secondary">#' + escapeHtml(t) + '</span>';
                    }).join('') + '</span>'
                    : '') +
            '</div>' +
        '</div>';
    }

    // ===== 详情渲染 =====
    function openJudicialPoint(id) {
        var p = getJudicialPointById(id);
        if (!p) {
            showToast('观点不存在');
            return;
        }
        currentView = 'detail';
        currentPointId = id;
        renderJudicialDetail(p);
    }

    function renderJudicialDetail(p) {
        var panel = document.getElementById('kb-panel-judicial');
        if (!panel) return;

        var isFav = !!_favorites[p.id];
        var causeColorMap = {
            'blue': 'bg-blue-100 text-blue-700',
            'pink': 'bg-pink-100 text-pink-700',
            'orange': 'bg-orange-100 text-orange-700',
            'red': 'bg-red-100 text-red-700',
            'purple': 'bg-purple-100 text-purple-700',
            'indigo': 'bg-indigo-100 text-indigo-700',
            'gray': 'bg-gray-100 text-gray-700'
        };
        var causeCls = causeColorMap[p.causeColor] || 'bg-blue-100 text-blue-700';

        // 全文 (按 \n 拆段, 保留格式)
        var fullTextHtml = (p.fullText || '').split('\n').map(function(line) {
            var trimmed = line.trim();
            if (!trimmed) return '<br/>';
            if (/^【.+】$/.test(trimmed)) {
                return '<h3 class="text-sm font-semibold text-fg-primary mt-4 mb-2">' + escapeHtml(trimmed) + '</h3>';
            }
            return '<p class="text-xs leading-relaxed text-fg-secondary">' + escapeHtml(trimmed) + '</p>';
        }).join('');

        var html =
            // 顶部操作
            '<div class="bg-white rounded-xl border border-bg-border p-4 flex items-center justify-between">' +
                '<button class="text-xs text-fg-secondary hover:text-brand flex items-center gap-1 transition-colors" onclick="backToJudicialList()">' +
                    '<iconify-icon class="text-base" icon="mdi:arrow-left"></iconify-icon> 返回列表' +
                '</button>' +
                '<div class="flex items-center gap-2">' +
                    '<button class="text-xs px-3 py-1.5 rounded-lg border border-bg-border text-fg-secondary hover:bg-bg-subtle flex items-center gap-1 transition-colors" onclick="copyJudicialPoint()">' +
                        '<iconify-icon class="text-base" icon="mdi:content-copy"></iconify-icon> 复制全文' +
                    '</button>' +
                    '<button class="text-xs px-3 py-1.5 rounded-lg border flex items-center gap-1 transition-colors ' + (isFav ? 'border-amber-200 bg-amber-50 text-amber-700 hover:bg-amber-100' : 'border-bg-border text-fg-secondary hover:bg-bg-subtle') + '" onclick="toggleJudicialFavorite(\'' + p.id + '\')">' +
                        '<iconify-icon class="text-base" icon="' + (isFav ? 'mdi:star' : 'mdi:star-outline') + '"></iconify-icon> ' + (isFav ? '已收藏' : '收藏') +
                    '</button>' +
                '</div>' +
            '</div>' +
            // 标题
            '<div class="bg-white rounded-xl border border-bg-border p-5">' +
                '<div class="flex items-start gap-2 flex-wrap mb-2">' +
                    '<span class="text-[10px] ' + causeCls + ' px-2 py-0.5 rounded-full font-medium">' + escapeHtml(p.cause) + '</span>' +
                    '<span class="text-[10px] bg-purple-50 text-purple-700 px-2 py-0.5 rounded-full font-medium">司法观点</span>' +
                    ((p.tags || []).slice(0, 4).map(function(t) {
                        return '<span class="text-[10px] px-2 py-0.5 rounded-full bg-bg-subtle text-fg-secondary">#' + escapeHtml(t) + '</span>';
                    }).join('')) +
                '</div>' +
                '<h1 class="text-xl font-bold text-fg-primary mb-3 leading-tight">' + escapeHtml(p.title) + '</h1>' +
                '<p class="text-sm text-fg-secondary leading-relaxed mb-3">' + escapeHtml(p.summary) + '</p>' +
                '<div class="flex items-center gap-3 text-[11px] text-fg-tertiary flex-wrap">' +
                    '<span class="inline-flex items-center gap-1"><iconify-icon class="text-xs" icon="mdi:account-outline"></iconify-icon> ' + escapeHtml(p.author) + '</span>' +
                    '<span class="text-fg-disabled">·</span>' +
                    '<span class="inline-flex items-center gap-1"><iconify-icon class="text-xs" icon="mdi:bookshelf"></iconify-icon> ' + escapeHtml(p.source) + '</span>' +
                    '<span class="text-fg-disabled">·</span>' +
                    '<span class="inline-flex items-center gap-1"><iconify-icon class="text-xs" icon="mdi:calendar-outline"></iconify-icon> ' + escapeHtml(p.date) + '</span>' +
                '</div>' +
            '</div>' +
            // 全文
            '<div class="bg-white rounded-xl border border-bg-border p-5">' +
                '<h2 class="text-sm font-semibold text-fg-primary mb-3 flex items-center gap-1.5"><iconify-icon class="text-base text-fg-tertiary" icon="mdi:text-box-outline"></iconify-icon> 观点全文</h2>' +
                '<div class="space-y-1">' + fullTextHtml + '</div>' +
            '</div>' +
            // 适用情形
            ((p.applicableScenarios || []).length > 0
                ? '<div class="bg-white rounded-xl border border-bg-border p-5">' +
                    '<h2 class="text-sm font-semibold text-fg-primary mb-3 flex items-center gap-1.5"><iconify-icon class="text-base text-fg-tertiary" icon="mdi:target"></iconify-icon> 适用情形</h2>' +
                    '<div class="grid grid-cols-1 md:grid-cols-2 gap-2">' +
                        p.applicableScenarios.map(function(s) {
                            return '<div class="flex items-start gap-2 text-xs"><iconify-icon class="text-sm text-success flex-shrink-0 mt-0.5" icon="mdi:check-circle"></iconify-icon> <span class="text-fg-secondary">' + escapeHtml(s) + '</span></div>';
                        }).join('') +
                    '</div>' +
                '</div>'
                : '') +
            // 相关法条
            ((p.relatedLaws || []).length > 0
                ? '<div class="bg-white rounded-xl border border-bg-border p-5">' +
                    '<h2 class="text-sm font-semibold text-fg-primary mb-3 flex items-center gap-1.5"><iconify-icon class="text-base text-fg-tertiary" icon="mdi:scale-balance"></iconify-icon> 相关法律法规</h2>' +
                    '<div class="space-y-1.5">' +
                        p.relatedLaws.map(function(l) {
                            return '<div class="flex items-start gap-2 text-xs"><iconify-icon class="text-sm text-brand flex-shrink-0 mt-0.5" icon="mdi:bookmark-outline"></iconify-icon> <span class="text-fg-secondary font-mono">' + escapeHtml(l) + '</span></div>';
                        }).join('') +
                    '</div>' +
                '</div>'
                : '') +
            // 引用案例
            ((p.citedCases || []).length > 0
                ? '<div class="bg-white rounded-xl border border-bg-border p-5">' +
                    '<h2 class="text-sm font-semibold text-fg-primary mb-3 flex items-center gap-1.5"><iconify-icon class="text-base text-fg-tertiary" icon="mdi:gavel"></iconify-icon> 引用案例</h2>' +
                    '<div class="space-y-1.5">' +
                        p.citedCases.map(function(c) {
                            return '<div class="flex items-start gap-2 text-xs"><iconify-icon class="text-sm text-urgent flex-shrink-0 mt-0.5" icon="mdi:file-document-outline"></iconify-icon> <span class="text-fg-secondary font-mono">' + escapeHtml(c) + '</span></div>';
                        }).join('') +
                    '</div>' +
                '</div>'
                : '');

        panel.innerHTML = html;
    }

    // ===== 筛选 / 搜索 / 排序 =====
    function filterAndSortPoints() {
        var points = getAllJudicialPoints().slice();
        var kw = currentSearchKw.toLowerCase().trim();
        var cause = currentCauseFilter;

        // 筛选
        points = points.filter(function(p) {
            // 案由
            if (cause !== 'all' && p.cause !== cause) return false;
            // 关键词
            if (kw) {
                var haystack = (p.title + ' ' + (p.summary || '') + ' ' + (p.fullText || '') + ' ' + (p.tags || []).join(' ') + ' ' + (p.relatedLaws || []).join(' ') + ' ' + (p.citedCases || []).join(' ')).toLowerCase();
                if (haystack.indexOf(kw) < 0) return false;
            }
            return true;
        });

        // 排序
        points.sort(function(a, b) {
            if (currentSortBy === 'cause') {
                return a.cause.localeCompare(b.cause);
            } else if (currentSortBy === 'source') {
                return a.source.localeCompare(b.source);
            } else {
                // date desc
                return b.date.localeCompare(a.date);
            }
        });

        return points;
    }

    function onJudicialSearch(kw) {
        currentSearchKw = kw;
        if (currentView === 'detail') {
            backToJudicialList();
        } else {
            renderJudicialList();
        }
    }

    function onJudicialCauseFilter(cause) {
        currentCauseFilter = cause;
        if (currentView === 'detail') {
            backToJudicialList();
        } else {
            renderJudicialList();
        }
    }

    function onJudicialSort(sort) {
        currentSortBy = sort;
        if (currentView === 'detail') {
            backToJudicialList();
        } else {
            renderJudicialList();
        }
    }

    function backToJudicialList() {
        currentView = 'list';
        currentPointId = null;
        renderJudicialList();
    }

    // ===== 收藏 =====
    function toggleJudicialFavorite(id) {
        if (_favorites[id]) {
            delete _favorites[id];
            showToast('已取消收藏');
        } else {
            _favorites[id] = { at: Date.now() };
            showToast('已收藏');
        }
        saveFavorites();

        // 重新渲染当前视图
        if (currentView === 'detail' && currentPointId === id) {
            var p = getJudicialPointById(id);
            if (p) renderJudicialDetail(p);
        } else {
            renderJudicialList();
        }
    }

    // ===== 复制全文 =====
    function copyJudicialPoint() {
        if (!currentPointId) return;
        var p = getJudicialPointById(currentPointId);
        if (!p) return;
        var text = p.title + '\n\n' + (p.summary || '') + '\n\n' + (p.fullText || '') + '\n\n';
        if (p.relatedLaws && p.relatedLaws.length) {
            text += '\n相关法条: \n' + p.relatedLaws.map(function(l) { return '  ' + l; }).join('\n');
        }
        if (p.citedCases && p.citedCases.length) {
            text += '\n\n引用案例:\n' + p.citedCases.map(function(c) { return '  ' + c; }).join('\n');
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(function() {
                showToast('已复制: ' + p.title);
            });
        } else {
            showToast('复制功能需要 HTTPS 环境');
        }
    }

    // ===== 初始化 (view-knowledge 首次显示时) =====
    function initJudicialTab() {
        var el = document.getElementById('kb-panel-judicial');
        if (!el) return;
        if (el.dataset.init) return;
        el.dataset.init = '1';
        renderJudicialList();
    }

    var initObserver = new MutationObserver(function() {
        var kbEl = document.getElementById('view-knowledge');
        if (kbEl && !kbEl.classList.contains('hidden') && !kbEl.dataset.judicialInit) {
            kbEl.dataset.judicialInit = '1';
            initJudicialTab();
        }
    });
    if (document.body) {
        initObserver.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
    }

    // ===== 双绑定 =====
    globalThis.openJudicialPoint = openJudicialPoint;
    globalThis.backToJudicialList = backToJudicialList;
    globalThis.onJudicialSearch = onJudicialSearch;
    globalThis.onJudicialCauseFilter = onJudicialCauseFilter;
    globalThis.onJudicialSort = onJudicialSort;
    globalThis.toggleJudicialFavorite = toggleJudicialFavorite;
    globalThis.copyJudicialPoint = copyJudicialPoint;
    globalThis.renderJudicialList = renderJudicialList;
})();