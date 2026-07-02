(function() {
    'use strict';

    var _attentionData = [
        { id: 1, type: '逾期', title: '举证期限即将截止', desc: '案件：张三合同纠纷 · 截止日期：2026-06-20', extra: '已逾期 3 天', action: '去处理', icon: 'mdi:clock-alert-outline', iconColor: 'text-red-500', iconBg: 'bg-red-50', borderColor: 'border-l-red-500', badgeBg: 'bg-red-100', badgeColor: 'text-red-700', actionColor: 'text-red-500' },
        { id: 2, type: '待处理', title: '王华借贷纠纷上诉状待审核', desc: '提交人：李律师 · 已等待 2 天', extra: '优先级：高', action: '去处理', icon: 'mdi:file-document-edit-outline', iconColor: 'text-orange-500', iconBg: 'bg-warning-tint', borderColor: 'border-l-orange-500', badgeBg: 'bg-warning-tint', badgeColor: 'text-orange-700', actionColor: 'text-orange-500' },
        { id: 3, type: '提醒', title: '明日开庭提醒', desc: '李明诉XX公司买卖合同纠纷 · 朝阳法院 09:00', extra: '距离开庭 18h', action: '查看详情', icon: 'mdi:calendar-check-outline', iconColor: 'text-brand', iconBg: 'bg-brand-tint3', borderColor: 'border-l-blue-500', badgeBg: 'bg-brand-tint', badgeColor: 'text-brand', actionColor: 'text-brand' },
        { id: 4, type: '待处理', title: '某科技公司案代理费发票待开具', desc: '金额：¥50,000 · 客户要求本周内提供', extra: '截止：本周五', action: '去处理', icon: 'mdi:account-cash-outline', iconColor: 'text-orange-500', iconBg: 'bg-warning-tint', borderColor: 'border-l-orange-500', badgeBg: 'bg-warning-tint', badgeColor: 'text-orange-700', actionColor: 'text-orange-500' },
        { id: 5, type: '提醒', title: '某劳动争议案调解方案待确认', desc: '对方已同意调解 · 建议方案已生成 · 请尽快确认', extra: '待回复：2 天', action: '确认方案', icon: 'mdi:handshake-outline', iconColor: 'text-brand', iconBg: 'bg-brand-tint3', borderColor: 'border-l-blue-500', badgeBg: 'bg-brand-tint', badgeColor: 'text-brand', actionColor: 'text-brand' }
    ];

    var _currentFilter = 'all';
    var _searchKeyword = '';
    var _searchTimer = null;

    function getFilteredData() {
        return _attentionData.filter(function(item) {
            var matchType = _currentFilter === 'all' || item.type === _currentFilter;
            var keyword = _searchKeyword.toLowerCase();
            var matchSearch = !keyword ||
                item.title.toLowerCase().indexOf(keyword) > -1 ||
                item.desc.toLowerCase().indexOf(keyword) > -1;
            return matchType && matchSearch;
        });
    }

    function renderCard(item) {
        return '<div class="bg-white rounded-xl border border-bg-border shadow-sm p-4 hover:shadow-md transition-shadow cursor-pointer border-l-4 ' + item.borderColor + ' min-h-[140px]">' +
            '<div class="flex items-center gap-3">' +
            '<div class="w-10 h-10 rounded-lg ' + item.iconBg + ' flex items-center justify-center flex-shrink-0">' +
            '<iconify-icon class="' + item.iconColor + ' text-xl" icon="' + item.icon + '"></iconify-icon>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<div class="flex items-center gap-2 mb-0.5">' +
            '<span class="text-[10px] ' + item.badgeBg + ' ' + item.badgeColor + ' font-medium px-1.5 py-0.5 rounded-full">' + item.type + '</span>' +
            '<span class="font-medium text-sm text-fg-primary truncate">' + escapeHtml(item.title) + '</span>' +
            '</div>' +
            '<p class="text-xs text-fg-tertiary truncate">' + escapeHtml(item.desc) + '</p>' +
            '</div>' +
            '<iconify-icon class="text-gray-300 text-lg flex-shrink-0" icon="mdi:chevron-right"></iconify-icon>' +
            '</div>' +
            '<div class="mt-3 flex items-center justify-between">' +
            '<span class="text-[10px] ' + item.actionColor + ' font-medium">' + item.extra + '</span>' +
            '<button class="text-[10px] text-brand hover:underline" onclick="event.stopPropagation(); handleAttentionAction(' + item.id + ')">' + item.action + '</button>' +
            '</div>' +
            '</div>';
    }

    function renderAttentionList() {
        var container = document.getElementById('attention-list-container');
        if (!container) return;

        var filtered = getFilteredData();

        if (filtered.length === 0) {
            container.innerHTML = '<div class="col-span-2 text-center py-12">' +
                '<iconify-icon class="text-5xl text-fg-disabled" icon="mdi:check-circle-outline"></iconify-icon>' +
                '<p class="text-sm text-fg-tertiary mt-3">暂无需要关注的事项</p>' +
                '</div>';
        } else {
            container.innerHTML = '<div class="grid grid-cols-1 lg:grid-cols-2 gap-4">' +
                filtered.map(function(item) { return renderCard(item); }).join('') +
                '</div>';
        }

        var countEl = document.getElementById('attention-count');
        if (countEl) countEl.textContent = '共 ' + filtered.length + ' 项';
    }

    function filterAttention(type, el) {
        _currentFilter = type;
        renderAttentionList();

        var btns = document.querySelectorAll('.att-filter-btn');
        btns.forEach(function(btn) {
            btn.className = 'att-filter-btn text-xs px-3 py-1.5 rounded-full bg-bg text-fg-secondary hover:bg-bg-border';
        });
        if (el) {
            el.className = 'att-filter-btn text-xs px-3 py-1.5 rounded-full bg-brand text-white';
        }
    }

    function handleAttentionAction(id) {
        var item = _attentionData.find(function(x) { return x.id === id; });
        if (item && typeof showToast === 'function') {
            showToast('正在处理: ' + item.title);
        }
    }

    function initSearch() {
        var searchInput = document.getElementById('attention-search');
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                clearTimeout(_searchTimer);
                var val = this.value;
                _searchTimer = setTimeout(function() {
                    _searchKeyword = val;
                    renderAttentionList();
                }, 300);
            });
        }
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function initAttentionList() {
        initSearch();
        renderAttentionList();
    }

    globalThis.initAttentionList = initAttentionList;
    globalThis.filterAttention = filterAttention;
    globalThis.handleAttentionAction = handleAttentionAction;
})();
