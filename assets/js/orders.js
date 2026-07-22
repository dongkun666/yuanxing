(function () {
    'use strict';

    function escapeHtml(s) {
        if (s === null || s === undefined) return '';
        return String(s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', '\'': '&#39;' }[c];
        });
    }

    var _orders = [
        {
            id: 'LP20260821001',
            product: '专业版 · 月付',
            amount: 299,
            status: '支付成功',
            statusType: 'success',
            date: '2026-08-21 15:30',
            icon: 'mdi:star',
            iconBg: 'bg-gradient-to-br from-brand-tint to-brand-tint2',
            iconColor: 'text-brand'
        },
        {
            id: 'LP20260721001',
            product: '专业版 · 月付',
            amount: 299,
            status: '支付成功',
            statusType: 'success',
            date: '2026-07-21 14:20',
            icon: 'mdi:star',
            iconBg: 'bg-gradient-to-br from-brand-tint to-brand-tint2',
            iconColor: 'text-brand'
        },
        {
            id: 'LP20260615001',
            product: '企业版 · 年付',
            amount: 7199,
            status: '已取消',
            statusType: 'cancelled',
            date: '2026-06-15 10:05',
            icon: 'mdi:domain',
            iconBg: 'bg-gradient-to-br from-gray-100 to-bg',
            iconColor: 'text-fg-tertiary'
        },
        {
            id: 'LP20260520001',
            product: '基础版 · 月付',
            amount: 99,
            status: '支付成功',
            statusType: 'success',
            date: '2026-05-20 09:15',
            icon: 'mdi:star-outline',
            iconBg: 'bg-gradient-to-br from-brand-tint to-brand-tint2',
            iconColor: 'text-brand'
        },
        {
            id: 'LP20260410001',
            product: '专业版 · 季付',
            amount: 799,
            status: '处理中',
            statusType: 'pending',
            date: '2026-04-10 16:45',
            icon: 'mdi:star',
            iconBg: 'bg-gradient-to-br from-brand-tint to-brand-tint2',
            iconColor: 'text-brand'
        }
    ];

    var _currentFilter = 'all';
    var _dateFilter = 'all';
    var _searchKeyword = '';
    var _closeOrderDetail = null;
    var _closeInvoiceModal = null;

    function getStatusBadgeClass(statusType) {
        switch (statusType) {
        case 'success':
            return 'order-status-badge status-completed';
        case 'pending':
            return 'order-status-badge status-pending';
        case 'cancelled':
            return 'order-status-badge status-cancelled';
        case 'refunded':
            return 'order-status-badge status-refunded';
        case 'waiting':
            return 'order-status-badge status-waiting';
        default:
            return 'order-status-badge status-cancelled';
        }
    }

    function getAmountClass(statusType) {
        return statusType === 'cancelled' ? 'text-fg-disabled' : 'text-fg-primary';
    }

    function getOrderOpacity(statusType) {
        return statusType === 'cancelled' ? 'opacity-70' : '';
    }

    function getFilteredOrders() {
        return _orders.filter(function (order) {
            var matchStatus = _currentFilter === 'all' || order.status === _currentFilter;
            var keyword = _searchKeyword.toLowerCase();
            var matchSearch =
                !keyword ||
                order.id.toLowerCase().indexOf(keyword) > -1 ||
                order.product.toLowerCase().indexOf(keyword) > -1;
            return matchStatus && matchSearch;
        });
    }

    function updateStats() {
        var totalEl = document.getElementById('stat-total-orders');
        var monthEl = document.getElementById('stat-month-orders');
        var pendingEl = document.getElementById('stat-pending-orders');
        var completedEl = document.getElementById('stat-completed-orders');
        var revenueEl = document.getElementById('stat-total-revenue');

        if (!totalEl) return;

        var total = _orders.length;
        var monthCount = _orders.filter(function (o) {
            return o.date.indexOf('2026-08') === 0;
        }).length;
        var pendingCount = _orders.filter(function (o) {
            return o.statusType === 'pending' || o.status === '待支付';
        }).length;
        var completedCount = _orders.filter(function (o) {
            return o.statusType === 'success';
        }).length;
        var totalRevenue = _orders
            .filter(function (o) {
                return o.statusType === 'success';
            })
            .reduce(function (sum, o) {
                return sum + o.amount;
            }, 0);

        totalEl.textContent = total;
        monthEl.textContent = monthCount;
        pendingEl.textContent = pendingCount;
        completedEl.textContent = completedCount;
        revenueEl.textContent = '¥' + totalRevenue.toLocaleString();
    }

    function renderOrderCard(order, index) {
        var statusBadgeCls = getStatusBadgeClass(order.statusType);
        var amountCls = getAmountClass(order.statusType);
        var opacityCls = getOrderOpacity(order.statusType);
        var animDelay = (index * 0.06).toFixed(2);

        var actions = '';
        if (order.statusType === 'success') {
            actions =
                '<div class="flex items-center gap-2">' +
                '<button class="table-action-btn table-action-btn-primary" onclick="viewOrderDetail(\'' +
                order.id +
                '\')">' +
                '<iconify-icon icon="mdi:eye-outline" class="text-xs"></iconify-icon>' +
                '<span>详情</span>' +
                '</button>' +
                '<button class="table-action-btn table-action-btn-default" onclick="applyInvoice(\'' +
                order.id +
                '\')">' +
                '<iconify-icon icon="mdi:file-text-outline" class="text-xs"></iconify-icon>' +
                '<span>发票</span>' +
                '</button>' +
                '</div>';
        } else if (order.statusType === 'cancelled') {
            actions =
                '<button class="table-action-btn table-action-btn-primary" onclick="resubscribe(\'' +
                order.id +
                '\')">' +
                '<iconify-icon icon="mdi:refresh" class="text-xs"></iconify-icon>' +
                '<span>重新订阅</span>' +
                '</button>';
        } else {
            actions =
                '<button class="table-action-btn table-action-btn-primary" onclick="viewOrderDetail(\'' +
                order.id +
                '\')">' +
                '<iconify-icon icon="mdi:eye-outline" class="text-xs"></iconify-icon>' +
                '<span>详情</span>' +
                '</button>';
        }

        return (
            '<div class="order-card p-4 rounded-xl border border-bg-border bg-white hover:shadow-md hover:border-gray-200 transition-all duration-300 hover:-translate-y-0.5 ' +
            opacityCls +
            '" style="animation: fadeInUp 0.5s ease-out ' +
            animDelay +
            's backwards;">' +
            '<div class="flex items-center justify-between">' +
            '<div class="flex items-center gap-3">' +
            '<div class="w-10 h-10 rounded-xl ' +
            order.iconBg +
            ' flex items-center justify-center flex-shrink-0 shadow-sm">' +
            '<iconify-icon class="text-lg ' +
            order.iconColor +
            '" icon="' +
            order.icon +
            '"></iconify-icon>' +
            '</div>' +
            '<div class="min-w-0">' +
            '<p class="text-sm font-semibold text-fg-primary truncate">' +
            escapeHtml(order.product) +
            '</p>' +
            '<p class="text-xs text-fg-tertiary mt-0.5 font-mono">订单号：' +
            order.id +
            '</p>' +
            '</div>' +
            '</div>' +
            '<div class="text-right flex-shrink-0">' +
            '<p class="text-base font-bold ' +
            amountCls +
            ' tabular-nums">¥' +
            order.amount.toLocaleString() +
            '</p>' +
            '<span class="' +
            statusBadgeCls +
            ' mt-1 inline-flex items-center gap-1">' +
            order.status +
            '</span>' +
            '</div>' +
            '</div>' +
            '<div class="flex items-center justify-between mt-3 pt-3 border-t border-bg-border">' +
            '<span class="text-xs text-fg-tertiary flex items-center gap-1">' +
            '<iconify-icon icon="mdi:calendar-clock-outline" class="text-[11px]"></iconify-icon>' +
            order.date +
            '</span>' +
            actions +
            '</div>' +
            '</div>'
        );
    }

    function renderOrders() {
        var container = document.getElementById('orders-list');
        var countEl = document.getElementById('orders-count');
        var paginationInfoEl = document.getElementById('orders-pagination-info');
        if (!container) return;

        var filtered = getFilteredOrders();

        if (filtered.length === 0) {
            container.innerHTML = '';
            if (typeof Utils !== 'undefined' && Utils.createEmptyState) {
                Utils.createEmptyState({
                    preset: _searchKeyword ? 'no-result' : 'empty-list',
                    title: _searchKeyword ? '没有找到匹配的订单' : '暂无订单记录',
                    description: _searchKeyword ? '请尝试其他搜索关键词' : '还没有任何订单，快去选择适合您的套餐吧',
                    actionText: _searchKeyword ? '清除搜索' : '去选购',
                    actionHandler: function () {
                        if (_searchKeyword) {
                            var input = document.getElementById('orders-search-input');
                            if (input) input.value = '';
                            _searchKeyword = '';
                            renderOrders();
                        } else if (typeof switchView === 'function') {
                            switchView('subscription');
                        }
                    },
                    container: container
                });
            } else {
                container.innerHTML =
                    '<div class="text-center py-12">' +
                    '<iconify-icon class="text-5xl text-fg-disabled" icon="mdi:receipt-text-outline"></iconify-icon>' +
                    '<p class="text-sm text-fg-tertiary mt-3">暂无订单记录</p>' +
                    '</div>';
            }
        } else {
            container.innerHTML = filtered
                .map(function (o, idx) {
                    return renderOrderCard(o, idx);
                })
                .join('');
        }

        if (countEl) countEl.textContent = '共 ' + filtered.length + ' 条记录';
        if (paginationInfoEl) {
            paginationInfoEl.textContent = '显示 1-' + filtered.length + ' 条，共 ' + filtered.length + ' 条';
        }
    }

    function initStatusFilter() {
        var select = document.getElementById('orders-status-filter');
        if (select) {
            select.addEventListener('change', function () {
                var val = this.value;
                _currentFilter = val;
                renderOrders();
            });
        }
    }

    function initDateFilter() {
        var select = document.getElementById('orders-date-filter');
        if (select) {
            select.addEventListener('change', function () {
                _dateFilter = this.value;
                renderOrders();
            });
        }
    }

    function initSearch() {
        var input = document.getElementById('orders-search-input');
        if (input && typeof Utils !== 'undefined' && Utils.debounce) {
            input.addEventListener(
                'input',
                Utils.debounce(function () {
                    _searchKeyword = this.value.trim();
                    renderOrders();
                }, 300)
            );
        } else if (input) {
            var timer = null;
            input.addEventListener('input', function () {
                var val = this.value.trim();
                clearTimeout(timer);
                timer = setTimeout(function () {
                    _searchKeyword = val;
                    renderOrders();
                }, 300);
            });
        }
    }

    function viewOrderDetail(orderId) {
        var order = _orders.find(function (x) {
            return x.id === orderId;
        });
        if (!order) {
            if (typeof showToast === 'function') showToast('未找到订单 ' + orderId);
            return;
        }
        var statusBadgeCls = getStatusBadgeClass(order.statusType);

        var content =
            '<div class="space-y-4">' +
            '<div class="p-4 rounded-xl bg-gradient-to-br from-brand-tint3 to-brand-tint border border-brand-tint2 relative overflow-hidden">' +
            '<div class="absolute top-0 right-0 w-20 h-20 bg-brand/5 rounded-full -translate-y-1/2 translate-x-1/2"></div>' +
            '<div class="relative z-10">' +
            '<div class="flex items-center gap-2 flex-wrap mb-2">' +
            '<span class="text-sm font-bold font-mono text-fg-primary">' +
            escapeHtml(order.id) +
            '</span>' +
            '<span class="' +
            statusBadgeCls +
            '">' +
            escapeHtml(order.status) +
            '</span>' +
            '</div>' +
            '<p class="text-xs text-fg-secondary">' +
            escapeHtml(order.product) +
            '</p>' +
            '</div>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3 rounded-xl bg-bg-subtle/50 hover:bg-bg-subtle transition-colors">' +
            '<p class="text-[11px] text-fg-tertiary mb-1 flex items-center gap-1">' +
            '<iconify-icon icon="mdi:cash-multiple" class="text-xs"></iconify-icon>' +
            '订单金额' +
            '</p>' +
            '<p class="text-xl font-bold text-brand tabular-nums">¥' +
            order.amount.toLocaleString() +
            '</p>' +
            '</div>' +
            '<div class="p-3 rounded-xl bg-bg-subtle/50 hover:bg-bg-subtle transition-colors">' +
            '<p class="text-[11px] text-fg-tertiary mb-1 flex items-center gap-1">' +
            '<iconify-icon icon="mdi:calendar-clock-outline" class="text-xs"></iconify-icon>' +
            '下单时间' +
            '</p>' +
            '<p class="text-sm font-medium text-fg-primary">' +
            escapeHtml(order.date) +
            '</p>' +
            '</div>' +
            '</div>' +
            '<div class="p-4 rounded-xl bg-bg-subtle/50 space-y-3">' +
            '<h4 class="text-xs font-semibold text-fg-primary flex items-center gap-1.5">' +
            '<iconify-icon icon="mdi:credit-card-outline" class="text-sm"></iconify-icon>' +
            '支付信息' +
            '</h4>' +
            '<div class="flex items-center justify-between text-sm">' +
            '<span class="text-fg-tertiary">支付方式</span>' +
            '<span class="text-fg-primary font-medium">支付宝</span>' +
            '</div>' +
            '<div class="flex items-center justify-between text-sm">' +
            '<span class="text-fg-tertiary">支付流水号</span>' +
            '<span class="text-fg-primary font-mono text-xs">20260821213000100456789012345678</span>' +
            '</div>' +
            '<div class="flex items-center justify-between text-sm">' +
            '<span class="text-fg-tertiary">交易时间</span>' +
            '<span class="text-fg-primary">' +
            escapeHtml(order.date) +
            '</span>' +
            '</div>' +
            '</div>' +
            '<div class="p-4 rounded-xl bg-bg-subtle/50 space-y-3">' +
            '<h4 class="text-xs font-semibold text-fg-primary flex items-center gap-1.5">' +
            '<iconify-icon icon="mdi:cart-outline" class="text-sm"></iconify-icon>' +
            '购买明细' +
            '</h4>' +
            '<div class="flex items-center justify-between text-sm">' +
            '<span class="text-fg-secondary">' +
            escapeHtml(order.product) +
            '</span>' +
            '<span class="text-fg-primary font-semibold tabular-nums">¥' +
            order.amount.toLocaleString() +
            '</span>' +
            '</div>' +
            '<div class="flex items-center justify-between text-sm pt-2 border-t border-bg-border">' +
            '<span class="text-fg-primary font-semibold">合计</span>' +
            '<span class="text-brand font-bold text-lg tabular-nums">¥' +
            order.amount.toLocaleString() +
            '</span>' +
            '</div>' +
            '</div>' +
            '</div>';

        var footer =
            '<button class="px-4 py-2 text-xs font-medium text-fg-secondary bg-white border border-bg-border rounded-xl hover:bg-bg-subtle transition-all" onclick="closeOrderDetail()">关闭</button>' +
            (order.statusType === 'success'
                ? '<button class="btn-primary px-4 py-2 text-xs font-semibold flex items-center gap-1.5" onclick="closeOrderDetail(); applyInvoice(\'' +
                  order.id +
                  '\')">' +
                  '<iconify-icon icon="mdi:file-text-outline" class="text-sm"></iconify-icon>' +
                  '申请发票' +
                  '</button>'
                : '') +
            (order.statusType === 'cancelled'
                ? '<button class="btn-primary px-4 py-2 text-xs font-semibold flex items-center gap-1.5" onclick="closeOrderDetail(); resubscribe(\'' +
                  order.id +
                  '\')">' +
                  '<iconify-icon icon="mdi:refresh" class="text-sm"></iconify-icon>' +
                  '重新订阅' +
                  '</button>'
                : '');

        if (_closeOrderDetail) _closeOrderDetail();
        if (typeof Utils !== 'undefined' && Utils.showModal) {
            _closeOrderDetail = Utils.showModal({
                id: 'order-detail-modal',
                title: '订单详情',
                icon: 'mdi:receipt-text-outline',
                content: content,
                footer: footer,
                size: 'md'
            });
        }
    }

    function closeOrderDetail() {
        if (_closeOrderDetail) {
            _closeOrderDetail();
            _closeOrderDetail = null;
        }
    }

    function applyInvoice(orderId) {
        var order = _orders.find(function (x) {
            return x.id === orderId;
        });
        if (!order) {
            if (typeof showToast === 'function') showToast('未找到订单 ' + orderId);
            return;
        }

        var content =
            '<div class="space-y-4">' +
            '<div class="p-3 rounded-xl bg-gradient-to-r from-brand-tint3 to-brand-tint border border-brand-tint2 text-sm">' +
            '<div class="flex items-center justify-between mb-1">' +
            '<span class="text-fg-tertiary">订单号</span>' +
            '<span class="font-mono text-fg-primary font-medium">' +
            escapeHtml(order.id) +
            '</span>' +
            '</div>' +
            '<div class="flex items-center justify-between">' +
            '<span class="text-fg-tertiary">开票金额</span>' +
            '<span class="font-bold text-brand text-base tabular-nums">¥' +
            order.amount.toLocaleString() +
            '</span>' +
            '</div>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">发票类型</label>' +
            '<div class="flex gap-3">' +
            '<label class="flex items-center gap-2 cursor-pointer">' +
            '<input type="radio" name="invoice-type" value="personal" checked class="accent-brand"/>' +
            '<span class="text-xs text-fg-secondary">个人</span>' +
            '</label>' +
            '<label class="flex items-center gap-2 cursor-pointer">' +
            '<input type="radio" name="invoice-type" value="company" class="accent-brand"/>' +
            '<span class="text-xs text-fg-secondary">企业</span>' +
            '</label>' +
            '</div>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">接收邮箱</label>' +
            '<input type="email" placeholder="请输入接收发票的邮箱" class="form-input w-full"/>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">发票抬头</label>' +
            '<input type="text" placeholder="个人姓名或企业名称" class="form-input w-full"/>' +
            '</div>' +
            '</div>';

        var footer =
            '<button class="px-4 py-2 text-xs font-medium text-fg-secondary bg-white border border-bg-border rounded-xl hover:bg-bg-subtle transition-all" onclick="closeInvoiceModal()">取消</button>' +
            '<button class="btn-primary px-4 py-2 text-xs font-semibold flex items-center gap-1.5" onclick="submitInvoice(\'' +
            order.id +
            '\')">' +
            '<iconify-icon icon="mdi:send-outline" class="text-sm"></iconify-icon>' +
            '提交申请' +
            '</button>';

        if (_closeInvoiceModal) _closeInvoiceModal();
        if (typeof Utils !== 'undefined' && Utils.showModal) {
            _closeInvoiceModal = Utils.showModal({
                id: 'invoice-modal',
                title: '申请发票',
                icon: 'mdi:file-text-outline',
                content: content,
                footer: footer,
                size: 'sm'
            });
        }
    }

    function closeInvoiceModal() {
        if (_closeInvoiceModal) {
            _closeInvoiceModal();
            _closeInvoiceModal = null;
        }
    }

    function submitInvoice(orderId) {
        if (typeof showToast === 'function') showToast('发票申请已提交，将在 3 个工作日内发送到您的邮箱', 'success');
        closeInvoiceModal();
    }

    function resubscribe(orderId) {
        if (typeof switchView === 'function') {
            switchView('subscription');
        } else if (typeof showToast === 'function') {
            showToast('正在跳转订阅页面...');
        }
    }

    function exportOrders() {
        if (typeof showToast === 'function') {
            showToast('订单数据导出中，请稍候...', 'info');
            setTimeout(function () {
                showToast('订单数据导出成功', 'success');
            }, 1500);
        }
    }

    function prevOrdersPage() {
        if (typeof showToast === 'function') showToast('已经是第一页了', 'info');
    }

    function nextOrdersPage() {
        if (typeof showToast === 'function') showToast('已经是最后一页了', 'info');
    }

    function initOrders() {
        initStatusFilter();
        initDateFilter();
        initSearch();
        updateStats();
        renderOrders();

        if (typeof Animations !== 'undefined' && Animations.initPageAnimations) {
            var viewEl = document.getElementById('view-orders');
            if (viewEl) {
                Animations.initPageAnimations(viewEl);
            }
        }
    }

    globalThis.viewOrderDetail = viewOrderDetail;
    globalThis.closeOrderDetail = closeOrderDetail;
    globalThis.applyInvoice = applyInvoice;
    globalThis.closeInvoiceModal = closeInvoiceModal;
    globalThis.submitInvoice = submitInvoice;
    globalThis.resubscribe = resubscribe;
    globalThis.exportOrders = exportOrders;
    globalThis.prevOrdersPage = prevOrdersPage;
    globalThis.nextOrdersPage = nextOrdersPage;
    globalThis.initOrders = initOrders;
})();
