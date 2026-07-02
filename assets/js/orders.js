(function() {
    'use strict';

    var _orders = [
        { id: 'LP20260821001', product: '专业版 · 月付', amount: 299, status: '支付成功', statusType: 'success', date: '2026-08-21 15:30', icon: 'mdi:star', iconBg: 'bg-brand-tint3', iconColor: 'text-brand' },
        { id: 'LP20260721001', product: '专业版 · 月付', amount: 299, status: '支付成功', statusType: 'success', date: '2026-07-21 14:20', icon: 'mdi:star', iconBg: 'bg-brand-tint3', iconColor: 'text-brand' },
        { id: 'LP20260615001', product: '企业版 · 年付', amount: 7199, status: '已取消', statusType: 'cancelled', date: '2026-06-15 10:05', icon: 'mdi:domain', iconBg: 'bg-gray-50', iconColor: 'text-fg-tertiary' },
        { id: 'LP20260520001', product: '基础版 · 月付', amount: 99, status: '支付成功', statusType: 'success', date: '2026-05-20 09:15', icon: 'mdi:star-outline', iconBg: 'bg-brand-tint3', iconColor: 'text-brand' },
        { id: 'LP20260410001', product: '专业版 · 季付', amount: 799, status: '处理中', statusType: 'pending', date: '2026-04-10 16:45', icon: 'mdi:star', iconBg: 'bg-brand-tint3', iconColor: 'text-brand' }
    ];

    var _currentFilter = 'all';
    var _searchKeyword = '';

    function getFilteredOrders() {
        return _orders.filter(function(order) {
            var matchStatus = _currentFilter === 'all' || order.status === _currentFilter;
            var keyword = _searchKeyword.toLowerCase();
            var matchSearch = !keyword ||
                order.id.toLowerCase().indexOf(keyword) > -1 ||
                order.product.toLowerCase().indexOf(keyword) > -1;
            return matchStatus && matchSearch;
        });
    }

    function getStatusClass(statusType) {
        switch (statusType) {
            case 'success': return 'bg-green-50 text-success';
            case 'pending': return 'bg-yellow-50 text-yellow-700';
            case 'cancelled': return 'bg-bg text-fg-tertiary';
            default: return 'bg-bg text-fg-tertiary';
        }
    }

    function getAmountClass(statusType) {
        return statusType === 'cancelled' ? 'text-fg-disabled' : 'text-fg-primary';
    }

    function getOrderOpacity(statusType) {
        return statusType === 'cancelled' ? 'opacity-70' : '';
    }

    function renderOrderCard(order) {
        var statusCls = getStatusClass(order.statusType);
        var amountCls = getAmountClass(order.statusType);
        var opacityCls = getOrderOpacity(order.statusType);

        var actions = '';
        if (order.statusType === 'success') {
            actions = '<div class="flex gap-3">' +
                '<button class="text-brand hover:underline" onclick="viewOrderDetail(\'' + order.id + '\')">查看详情</button>' +
                '<button class="text-brand hover:underline" onclick="applyInvoice(\'' + order.id + '\')">申请发票</button>' +
                '</div>';
        } else if (order.statusType === 'cancelled') {
            actions = '<button class="text-brand hover:underline" onclick="resubscribe(\'' + order.id + '\')">重新订阅</button>';
        } else {
            actions = '<button class="text-brand hover:underline" onclick="viewOrderDetail(\'' + order.id + '\')">查看详情</button>';
        }

        return '<div class="bg-white rounded-xl border border-bg-border p-5 hover:shadow-sm transition-shadow ' + opacityCls + '">' +
            '<div class="flex items-center justify-between">' +
            '<div class="flex items-center gap-3">' +
            '<div class="w-10 h-10 rounded-lg ' + order.iconBg + ' flex items-center justify-center">' +
            '<iconify-icon class="text-lg ' + order.iconColor + '" icon="' + order.icon + '"></iconify-icon>' +
            '</div>' +
            '<div>' +
            '<p class="text-sm font-medium text-fg-primary">' + escapeHtml(order.product) + '</p>' +
            '<p class="text-xs text-fg-tertiary mt-0.5">订单号：' + order.id + '</p>' +
            '</div>' +
            '</div>' +
            '<div class="text-right">' +
            '<p class="text-sm font-semibold ' + amountCls + '">¥' + order.amount.toLocaleString() + '</p>' +
            '<span class="text-[10px] ' + statusCls + ' font-medium px-2 py-0.5 rounded mt-1 inline-block">' + order.status + '</span>' +
            '</div>' +
            '</div>' +
            '<div class="flex items-center justify-between mt-3 pt-3 border-t border-bg-border text-xs text-fg-tertiary">' +
            '<span>' + order.date + '</span>' +
            actions +
            '</div>' +
            '</div>';
    }

    function renderOrders() {
        var container = document.getElementById('orders-list');
        var countEl = document.getElementById('orders-count');
        if (!container) return;

        var filtered = getFilteredOrders();

        if (filtered.length === 0) {
            container.innerHTML = '<div class="text-center py-12">' +
                '<iconify-icon class="text-5xl text-fg-disabled" icon="mdi:receipt-text-outline"></iconify-icon>' +
                '<p class="text-sm text-fg-tertiary mt-3">暂无订单记录</p>' +
                '</div>';
        } else {
            container.innerHTML = filtered.map(function(o) { return renderOrderCard(o); }).join('');
        }

        if (countEl) countEl.textContent = '共 ' + filtered.length + ' 条记录';
    }

    function initStatusFilter() {
        var select = document.getElementById('orders-status-filter');
        if (select) {
            select.addEventListener('change', function() {
                var val = this.value;
                if (val === '全部状态') val = 'all';
                _currentFilter = val;
                renderOrders();
            });
        }
    }

    function viewOrderDetail(orderId) {
        if (typeof showToast === 'function') showToast('查看订单详情：' + orderId);
    }

    function applyInvoice(orderId) {
        if (typeof showToast === 'function') showToast('发票申请已提交：' + orderId);
    }

    function resubscribe(orderId) {
        if (typeof showToast === 'function') showToast('正在跳转订阅页面...');
    }

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function initOrders() {
        initStatusFilter();
        renderOrders();
    }

    globalThis.viewOrderDetail = viewOrderDetail;
    globalThis.applyInvoice = applyInvoice;
    globalThis.resubscribe = resubscribe;
    globalThis.initOrders = initOrders;
})();
