(function() {
    'use strict';

    var _dynamics = [
        { id: 0, type: '紧急', title: '证据提交即将截止', desc: '案件：李明诉XX公司买卖合同纠纷 · 剩余 2 天', time: '今天 10:30', user: '张律师', icon: 'mdi:clock-alert-outline', iconColor: 'text-red-500', iconBg: 'bg-red-50', borderColor: 'border-l-red-500', badgeBg: 'bg-red-100', badgeColor: 'text-red-700', action: '去处理' },
        { id: 1, type: '文书', title: '起诉状已完成', desc: '李明诉XX公司买卖合同纠纷 · 民事起诉状已由AI生成并保存', time: '今天 10:30', user: '张律师', icon: 'mdi:file-document-outline', iconColor: 'text-brand', iconBg: 'bg-brand-tint3', borderColor: 'border-l-blue-500', badgeBg: 'bg-brand-tint', badgeColor: 'text-brand', action: '查看' },
        { id: 2, type: '开庭', title: '开庭日期已确定', desc: '王华借贷纠纷 · 2026-08-28 14:00 第5法庭', time: '昨天 16:00', user: '李律师', icon: 'mdi:gavel', iconColor: 'text-purple-500', iconBg: 'bg-purple-50', borderColor: 'border-l-purple-500', badgeBg: 'bg-wiki-tint', badgeColor: 'text-wiki', action: '查看日程' },
        { id: 3, type: '归档', title: '案件已归档', desc: '张三合同纠纷 · 全部卷宗已完成归档', time: '昨天 14:30', user: '张律师', icon: 'mdi:check-circle-outline', iconColor: 'text-green-500', iconBg: 'bg-green-50', borderColor: 'border-l-green-500', badgeBg: 'bg-success-tint', badgeColor: 'text-success', action: '查看归档' },
        { id: 4, type: '提醒', title: '续约提醒', desc: '某科技公司法律顾问合同即将到期（2026-09-30）', time: '昨天 09:00', user: '系统', icon: 'mdi:calendar-check-outline', iconColor: 'text-amber-500', iconBg: 'bg-amber-50', borderColor: 'border-l-amber-500', badgeBg: 'bg-amber-100', badgeColor: 'text-amber-700', action: '去处理' },
        { id: 5, type: '文书', title: '证据目录已更新', desc: '某科技公司股权纠纷 · 新增3份补充证据', time: '2天前 11:20', user: '王律师', icon: 'mdi:file-compare', iconColor: 'text-brand', iconBg: 'bg-brand-tint3', borderColor: 'border-l-blue-500', badgeBg: 'bg-brand-tint', badgeColor: 'text-brand', action: '查看' },
        { id: 6, type: '开庭', title: '合议庭组成已确定', desc: '赵六劳动争议仲裁 · 审判长：王法官', time: '3天前 09:45', user: '系统', icon: 'mdi:account-group-outline', iconColor: 'text-purple-500', iconBg: 'bg-purple-50', borderColor: 'border-l-purple-500', badgeBg: 'bg-wiki-tint', badgeColor: 'text-wiki', action: '详情' },
        { id: 7, type: '归档', title: '判决书已上传', desc: '王华借贷纠纷 · 一审判决书已归档', time: '3天前 16:20', user: '张律师', icon: 'mdi:file-document-check-outline', iconColor: 'text-green-500', iconBg: 'bg-green-50', borderColor: 'border-l-green-500', badgeBg: 'bg-success-tint', badgeColor: 'text-success', action: '查看' }
    ];

    var _currentFilter = 'all';
    var _searchKeyword = '';
    var _currentView = 'list';
    var _searchTimer = null;

    function getFilteredDynamics() {
        return _dynamics.filter(function(item) {
            var matchType = _currentFilter === 'all' || item.type === _currentFilter;
            var keyword = _searchKeyword.toLowerCase();
            var matchSearch = !keyword ||
                item.title.toLowerCase().indexOf(keyword) > -1 ||
                item.desc.toLowerCase().indexOf(keyword) > -1;
            return matchType && matchSearch;
        });
    }

    function renderListItem(item) {
        return '<div class="bg-white rounded-xl border border-bg-border p-4 hover:shadow-sm transition-shadow border-l-4 ' + item.borderColor + '">' +
            '<div class="flex items-start gap-3">' +
            '<div class="w-9 h-9 rounded-lg ' + item.iconBg + ' flex items-center justify-center flex-shrink-0">' +
            '<iconify-icon class="' + item.iconColor + ' text-lg" icon="' + item.icon + '"></iconify-icon>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<div class="flex items-center gap-2 mb-1">' +
            '<span class="text-[10px] ' + item.badgeBg + ' ' + item.badgeColor + ' font-medium px-1.5 py-0.5 rounded-full">' + item.type + '</span>' +
            '<span class="font-medium text-sm text-fg-primary">' + escapeHtml(item.title) + '</span>' +
            '</div>' +
            '<p class="text-xs text-fg-tertiary">' + escapeHtml(item.desc) + '</p>' +
            '<div class="flex items-center gap-3 mt-2">' +
            '<span class="text-[10px] text-fg-tertiary"><iconify-icon class="inline" icon="mdi:clock-outline"></iconify-icon> ' + item.time + '</span>' +
            '<span class="text-[10px] text-fg-tertiary"><iconify-icon class="inline" icon="mdi:account-outline"></iconify-icon> ' + item.user + '</span>' +
            '</div>' +
            '</div>' +
            '<button class="text-[10px] text-brand hover:underline flex-shrink-0 mt-1" onclick="openCaseDynamicDetail(' + item.id + ')">' + item.action + '</button>' +
            '</div>' +
            '</div>';
    }

    function renderTimelineItem(item, index) {
        var isLast = index === getFilteredDynamics().length - 1;
        return '<div class="relative pb-8 ' + (isLast ? '' : '') + '">' +
            '<div class="absolute -left-8 top-1 w-6 h-6 rounded-full ' + item.iconBg + ' border-2 border-white flex items-center justify-center z-10">' +
            '<iconify-icon class="' + item.iconColor + ' text-sm" icon="' + item.icon + '"></iconify-icon>' +
            '</div>' +
            '<div class="bg-white rounded-xl border border-bg-border p-4 hover:shadow-sm transition-shadow ml-4">' +
            '<div class="flex items-center gap-2 mb-1">' +
            '<span class="text-[10px] ' + item.badgeBg + ' ' + item.badgeColor + ' font-medium px-1.5 py-0.5 rounded-full">' + item.type + '</span>' +
            '<span class="font-medium text-sm text-fg-primary">' + escapeHtml(item.title) + '</span>' +
            '</div>' +
            '<p class="text-xs text-fg-tertiary">' + escapeHtml(item.desc) + '</p>' +
            '<div class="flex items-center gap-3 mt-2">' +
            '<span class="text-[10px] text-fg-tertiary"><iconify-icon class="inline" icon="mdi:clock-outline"></iconify-icon> ' + item.time + '</span>' +
            '<span class="text-[10px] text-fg-tertiary"><iconify-icon class="inline" icon="mdi:account-outline"></iconify-icon> ' + item.user + '</span>' +
            '<button class="text-[10px] text-brand hover:underline ml-auto" onclick="openCaseDynamicDetail(' + item.id + ')">' + item.action + '</button>' +
            '</div>' +
            '</div>' +
            '</div>';
    }

    function renderDynamics() {
        var listView = document.getElementById('dynamics-list-view');
        var timelineView = document.getElementById('dynamics-timeline-view');
        var emptyState = document.getElementById('dynamics-empty-state');
        var countEl = document.getElementById('dynamics-count');

        var filtered = getFilteredDynamics();

        if (filtered.length === 0) {
            if (listView) listView.classList.add('hidden');
            if (timelineView) timelineView.classList.add('hidden');
            if (emptyState) emptyState.classList.remove('hidden');
        } else {
            if (emptyState) emptyState.classList.add('hidden');

            if (_currentView === 'list') {
                if (listView) {
                    listView.classList.remove('hidden');
                    listView.innerHTML = filtered.map(function(item) { return renderListItem(item); }).join('') +
                        '<div class="text-center py-4"><span class="text-[10px] text-gray-300">— 没有更多动态 —</span></div>';
                }
                if (timelineView) timelineView.classList.add('hidden');
            } else {
                if (timelineView) {
                    timelineView.classList.remove('hidden');
                    timelineView.innerHTML = '<div class="relative pl-8 ml-4 space-y-0">' +
                        '<div class="absolute left-3 top-3 bottom-3 w-0.5 bg-bg-border"></div>' +
                        filtered.map(function(item, idx) { return renderTimelineItem(item, idx); }).join('') +
                        '</div>';
                }
                if (listView) listView.classList.add('hidden');
            }
        }

        if (countEl) countEl.textContent = '共 ' + filtered.length + ' 条';
    }

    function filterDynamics(type, el) {
        _currentFilter = type;
        renderDynamics();

        var btns = document.querySelectorAll('.dyn-filter-btn');
        btns.forEach(function(btn) {
            btn.className = 'dyn-filter-btn text-xs px-3 py-1.5 rounded-full bg-bg text-fg-secondary hover:bg-bg-border';
        });
        if (el) {
            el.className = 'dyn-filter-btn text-xs px-3 py-1.5 rounded-full bg-brand text-white';
        }
    }

    function searchDynamics() {
        var input = document.getElementById('dynamics-search-input');
        if (input) {
            clearTimeout(_searchTimer);
            var val = input.value;
            _searchTimer = setTimeout(function() {
                _searchKeyword = val;
                renderDynamics();
            }, 300);
        }
    }

    function switchDynamicsView(view) {
        _currentView = view;

        var listBtn = document.getElementById('dyn-view-list');
        var timelineBtn = document.getElementById('dyn-view-timeline');

        if (view === 'list') {
            if (listBtn) listBtn.className = 'flex items-center gap-1 h-8 px-2.5 text-xs bg-brand text-white transition-colors';
            if (timelineBtn) timelineBtn.className = 'flex items-center gap-1 h-8 px-2.5 text-xs bg-white text-fg-secondary hover:bg-gray-50 transition-colors';
        } else {
            if (timelineBtn) timelineBtn.className = 'flex items-center gap-1 h-8 px-2.5 text-xs bg-brand text-white transition-colors';
            if (listBtn) listBtn.className = 'flex items-center gap-1 h-8 px-2.5 text-xs bg-white text-fg-secondary hover:bg-gray-50 transition-colors';
        }

        renderDynamics();
    }

    function openCaseDynamicDetail(id) {
        if (typeof showToast === 'function') showToast('查看动态详情 #' + id);
    }

    function openNewDynamicModal() {
        if (typeof showToast === 'function') showToast('发布动态功能开发中...');
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function initCaseDynamics() {
        var searchInput = document.getElementById('dynamics-search-input');
        if (searchInput) {
            searchInput.addEventListener('input', searchDynamics);
        }

        var typeSelect = document.getElementById('dynamics-type-filter');
        if (typeSelect) {
            typeSelect.addEventListener('change', function() {
                var val = this.value;
                if (val === '全部类型') val = 'all';
                _currentFilter = val;
                renderDynamics();
            });
        }

        renderDynamics();
    }

    globalThis.filterDynamics = filterDynamics;
    globalThis.searchDynamics = searchDynamics;
    globalThis.switchDynamicsView = switchDynamicsView;
    globalThis.openCaseDynamicDetail = openCaseDynamicDetail;
    globalThis.openNewDynamicModal = openNewDynamicModal;
    globalThis.initCaseDynamics = initCaseDynamics;
})();
