(function () {
    'use strict';

    var _attentionData = [
        {
            id: 1,
            type: '逾期',
            title: '举证期限即将截止',
            desc: '案件：张三合同纠纷 · 截止日期：2026-06-20',
            extra: '已逾期 3 天',
            action: '去处理',
            icon: 'mdi:clock-alert-outline',
            iconColor: 'text-red-500',
            iconBg: 'bg-red-50',
            borderColor: 'border-l-red-500',
            badgeBg: 'bg-red-100',
            badgeColor: 'text-red-700',
            actionColor: 'text-red-500'
        },
        {
            id: 2,
            type: '待处理',
            title: '王华借贷纠纷上诉状待审核',
            desc: '提交人：李律师 · 已等待 2 天',
            extra: '优先级：高',
            action: '去处理',
            icon: 'mdi:file-document-edit-outline',
            iconColor: 'text-orange-500',
            iconBg: 'bg-warning-tint',
            borderColor: 'border-l-orange-500',
            badgeBg: 'bg-warning-tint',
            badgeColor: 'text-orange-700',
            actionColor: 'text-orange-500'
        },
        {
            id: 3,
            type: '提醒',
            title: '明日开庭提醒',
            desc: '李明诉XX公司买卖合同纠纷 · 朝阳法院 09:00',
            extra: '距离开庭 18h',
            action: '查看详情',
            icon: 'mdi:calendar-check-outline',
            iconColor: 'text-brand',
            iconBg: 'bg-brand-tint3',
            borderColor: 'border-l-blue-500',
            badgeBg: 'bg-brand-tint',
            badgeColor: 'text-brand',
            actionColor: 'text-brand'
        },
        {
            id: 4,
            type: '待处理',
            title: '某科技公司案代理费发票待开具',
            desc: '金额：¥50,000 · 客户要求本周内提供',
            extra: '截止：本周五',
            action: '去处理',
            icon: 'mdi:account-cash-outline',
            iconColor: 'text-orange-500',
            iconBg: 'bg-warning-tint',
            borderColor: 'border-l-orange-500',
            badgeBg: 'bg-warning-tint',
            badgeColor: 'text-orange-700',
            actionColor: 'text-orange-500'
        },
        {
            id: 5,
            type: '提醒',
            title: '某劳动争议案调解方案待确认',
            desc: '对方已同意调解 · 建议方案已生成 · 请尽快确认',
            extra: '待回复：2 天',
            action: '确认方案',
            icon: 'mdi:handshake-outline',
            iconColor: 'text-brand',
            iconBg: 'bg-brand-tint3',
            borderColor: 'border-l-blue-500',
            badgeBg: 'bg-brand-tint',
            badgeColor: 'text-brand',
            actionColor: 'text-brand'
        }
    ];

    var _currentFilter = 'all';
    var _searchKeyword = '';
    var _searchTimer = null;
    var _closeAttentionDetail = null;

    function getFilteredData() {
        return _attentionData.filter(function (item) {
            var matchType = _currentFilter === 'all' || item.type === _currentFilter;
            var keyword = _searchKeyword.toLowerCase();
            var matchSearch =
                !keyword ||
                item.title.toLowerCase().indexOf(keyword) > -1 ||
                item.desc.toLowerCase().indexOf(keyword) > -1;
            return matchType && matchSearch;
        });
    }

    function renderCard(item, index) {
        var gradientFrom = item.type === '逾期' ? 'from-danger/5' : item.type === '待处理' ? 'from-warning/5' : 'from-brand/5';
        var iconGradientFrom = item.type === '逾期' ? 'from-red-100' : item.type === '待处理' ? 'from-amber-100' : 'from-brand-tint';
        var iconGradientTo = item.type === '逾期' ? 'to-red-200' : item.type === '待处理' ? 'to-warning-tint' : 'to-brand-tint2';
        var badgeClass = item.type === '逾期'
            ? 'bg-gradient-to-r from-danger to-red-500 text-white shadow-sm shadow-danger/20'
            : item.type === '待处理'
                ? 'bg-gradient-to-r from-warning-tint to-amber-100 text-warning'
                : 'bg-gradient-to-r from-brand-tint to-brand-tint2 text-brand';
        var borderClass = item.type === '逾期' ? 'border-l-danger' : item.type === '待处理' ? 'border-l-warning' : 'border-l-brand';
        var btnClass = item.type === '逾期'
            ? 'text-white bg-gradient-to-r from-danger to-red-500 hover:shadow-lg hover:shadow-danger/25'
            : item.type === '待处理'
                ? 'text-warning bg-warning-tint hover:bg-amber-100'
                : 'text-brand bg-brand-tint hover:bg-brand-tint2';
        var extraIcon = item.type === '逾期' ? 'mdi:clock-alert' : item.type === '待处理' ? 'mdi:flag' : 'mdi:clock-outline';

        return (
            '<div class="ws-card p-4 group cursor-pointer border-l-4 ' + borderClass + ' relative overflow-hidden min-h-[140px]" data-animate="fade-in-up" data-stagger-group="att-list" data-stagger-index="' + (index || 0) + '" data-delay="0.2">' +
            '<div class="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ' + gradientFrom + ' to-transparent rounded-bl-full -translate-y-1/2 translate-x-1/2 group-hover:scale-110 transition-transform duration-500"></div>' +
            '<div class="relative z-10">' +
            '<div class="flex items-center gap-3">' +
            '<div class="w-11 h-11 rounded-xl bg-gradient-to-br ' + iconGradientFrom + ' ' + iconGradientTo + ' flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform shadow-sm">' +
            '<iconify-icon class="' + item.iconColor + ' text-lg" icon="' + item.icon + '"></iconify-icon>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<div class="flex items-center gap-2 mb-0.5">' +
            '<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ' + badgeClass + '">' +
            (item.type === '逾期' ? '<iconify-icon icon="mdi:alert-circle" class="text-[9px]"></iconify-icon>' : '') +
            item.type +
            '</span>' +
            '<span class="font-semibold text-sm text-fg-primary group-hover:text-brand transition-colors truncate">' +
            escapeHtml(item.title) +
            '</span>' +
            '</div>' +
            '<p class="text-xs text-fg-tertiary truncate">' +
            escapeHtml(item.desc) +
            '</p>' +
            '</div>' +
            '<iconify-icon class="text-gray-300 text-lg flex-shrink-0 group-hover:text-brand group-hover:translate-x-0.5 transition-all" icon="mdi:chevron-right"></iconify-icon>' +
            '</div>' +
            '<div class="mt-3 flex items-center justify-between">' +
            '<span class="text-[11px] ' + item.actionColor + ' font-semibold flex items-center gap-1">' +
            '<iconify-icon icon="' + extraIcon + '" class="text-xs"></iconify-icon>' +
            item.extra +
            '</span>' +
            '<button class="text-[11px] ' + btnClass + ' px-3 py-1.5 rounded-lg font-medium transition-all duration-300 hover:-translate-y-0.5" onclick="event.stopPropagation(); handleAttentionAction(' + item.id + ')">' +
            item.action +
            '</button>' +
            '</div>' +
            '</div>' +
            '</div>'
        );
    }

    function renderAttentionList() {
        var container = document.getElementById('attention-list-container');
        var emptyEl = document.getElementById('attention-empty');
        if (!container) return;

        var filtered = getFilteredData();

        if (filtered.length === 0) {
            container.innerHTML = '';
            if (emptyEl) emptyEl.classList.remove('hidden');
        } else {
            if (emptyEl) emptyEl.classList.add('hidden');
            container.innerHTML =
                '<div class="grid grid-cols-1 lg:grid-cols-2 gap-4">' +
                filtered
                    .map(function (item, index) {
                        return renderCard(item, index);
                    })
                    .join('') +
                '</div>';
        }

        var countEl = document.getElementById('attention-count');
        if (countEl) countEl.textContent = '共 ' + filtered.length + ' 项';
    }

    function filterAttention(type, el) {
        _currentFilter = type;
        renderAttentionList();

        var btns = document.querySelectorAll('.att-filter-btn');
        btns.forEach(function (btn) {
            var btnType = btn.getAttribute('onclick') || '';
            var hoverClass = '';
            if (btnType.indexOf('逾期') > -1) {
                hoverClass = 'hover:bg-danger-tint hover:text-danger';
            } else if (btnType.indexOf('待处理') > -1) {
                hoverClass = 'hover:bg-warning-tint hover:text-warning';
            } else if (btnType.indexOf('提醒') > -1) {
                hoverClass = 'hover:bg-brand-tint hover:text-brand';
            } else {
                hoverClass = 'hover:bg-bg-border';
            }
            btn.className =
                'att-filter-btn text-xs px-4 py-2 rounded-full bg-bg-subtle text-fg-secondary font-medium transition-all duration-200 ' + hoverClass;
        });
        if (el) {
            el.className = 'att-filter-btn text-xs px-4 py-2 rounded-full bg-gradient-to-r from-brand to-brand-hover text-white font-medium shadow-sm shadow-brand/20 transition-all duration-200';
        }
    }

    function handleAttentionAction(id) {
        var item = _attentionData.find(function (x) {
            return x.id === id;
        });
        if (!item) {
            if (typeof showToast === 'function') showToast('未找到事项 #' + id);
            return;
        }

        var content =
            '<div class="space-y-4">' +
            '<div class="flex items-center gap-3 p-3 bg-bg-subtle rounded-xl">' +
            '<div class="w-12 h-12 rounded-lg ' +
            item.iconBg +
            ' flex items-center justify-center flex-shrink-0">' +
            '<iconify-icon class="' +
            item.iconColor +
            ' text-xl" icon="' +
            item.icon +
            '"></iconify-icon>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<div class="flex items-center gap-2 mb-0.5">' +
            '<span class="text-[10px] ' +
            item.badgeBg +
            ' ' +
            item.badgeColor +
            ' font-medium px-1.5 py-0.5 rounded-full">' +
            escapeHtml(item.type) +
            '</span>' +
            '<span class="font-medium text-sm text-fg-primary">' +
            escapeHtml(item.title) +
            '</span>' +
            '</div>' +
            '<p class="text-xs text-fg-tertiary">' +
            escapeHtml(item.desc) +
            '</p>' +
            '</div>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">状态信息</p>' +
            '<p class="text-sm ' +
            item.actionColor +
            ' font-medium">' +
            escapeHtml(item.extra) +
            '</p>' +
            '</div>' +
            '</div>';

        var footer =
            '<button class="h-9 px-4 text-xs text-fg-secondary bg-white border border-bg-border rounded-lg hover:bg-bg" onclick="closeAttentionDetail()">关闭</button>' +
            '<button class="h-9 px-4 text-xs text-white bg-brand hover:bg-brand-hover rounded-lg" onclick="handleAttentionComplete(' +
            item.id +
            ')">标记已完成</button>';

        if (_closeAttentionDetail) _closeAttentionDetail();
        _closeAttentionDetail = Utils.showModal({
            id: 'attention-detail-modal',
            title: '事项详情',
            icon: item.icon,
            content: content,
            footer: footer,
            size: 'md'
        });
    }

    function closeAttentionDetail() {
        if (_closeAttentionDetail) {
            _closeAttentionDetail();
            _closeAttentionDetail = null;
        }
    }

    function handleAttentionComplete(id) {
        var item = _attentionData.find(function (x) {
            return x.id === id;
        });
        if (!item) return;
        _attentionData = _attentionData.filter(function (x) {
            return x.id !== id;
        });
        closeAttentionDetail();
        renderAttentionList();
        if (typeof showToast === 'function') showToast('"' + item.title + '" 已标记完成', 'success');
    }

    function initSearch() {
        var searchInput = document.getElementById('attention-search');
        if (searchInput) {
            searchInput.addEventListener('input', function () {
                clearTimeout(_searchTimer);
                var val = this.value;
                _searchTimer = setTimeout(function () {
                    _searchKeyword = val;
                    renderAttentionList();
                }, 300);
            });
        }
    }

    function markAllAttentionDone() {
        if (_attentionData.length === 0) return;
        var count = _attentionData.length;
        _attentionData = [];
        renderAttentionList();
        if (typeof showToast === 'function') showToast('已将 ' + count + ' 项全部标记为已完成', 'success');
    }

    function initAttentionList() {
        initSearch();
        renderAttentionList();
    }

    globalThis.initAttentionList = initAttentionList;
    globalThis.filterAttention = filterAttention;
    globalThis.handleAttentionAction = handleAttentionAction;
    globalThis.closeAttentionDetail = closeAttentionDetail;
    globalThis.handleAttentionComplete = handleAttentionComplete;
    globalThis.markAllAttentionDone = markAllAttentionDone;
})();
