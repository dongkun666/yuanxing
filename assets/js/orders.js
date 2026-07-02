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
            iconBg: 'bg-brand-tint3',
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
            iconBg: 'bg-brand-tint3',
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
            iconBg: 'bg-gray-50',
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
            iconBg: 'bg-brand-tint3',
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
            iconBg: 'bg-brand-tint3',
            iconColor: 'text-brand'
        }
    ];

    var _currentFilter = 'all';
    var _searchKeyword = '';
    var _closeOrderDetail = null;
    var _closeInvoiceModal = null;

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

    function getStatusClass(statusType) {
        switch (statusType) {
        case 'success':
            return 'bg-green-50 text-success';
        case 'pending':
            return 'bg-yellow-50 text-yellow-700';
        case 'cancelled':
            return 'bg-bg text-fg-tertiary';
        default:
            return 'bg-bg text-fg-tertiary';
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
            actions =
                '<div class="flex gap-3">' +
                '<button class="text-brand hover:underline" onclick="viewOrderDetail(\'' +
                order.id +
                '\')">查看详情</button>' +
                '<button class="text-brand hover:underline" onclick="applyInvoice(\'' +
                order.id +
                '\')">申请发票</button>' +
                '</div>';
        } else if (order.statusType === 'cancelled') {
            actions =
                '<button class="text-brand hover:underline" onclick="resubscribe(\'' +
                order.id +
                '\')">重新订阅</button>';
        } else {
            actions =
                '<button class="text-brand hover:underline" onclick="viewOrderDetail(\'' +
                order.id +
                '\')">查看详情</button>';
        }

        return (
            '<div class="bg-white rounded-xl border border-bg-border p-5 hover:shadow-sm transition-shadow ' +
            opacityCls +
            '">' +
            '<div class="flex items-center justify-between">' +
            '<div class="flex items-center gap-3">' +
            '<div class="w-10 h-10 rounded-lg ' +
            order.iconBg +
            ' flex items-center justify-center">' +
            '<iconify-icon class="text-lg ' +
            order.iconColor +
            '" icon="' +
            order.icon +
            '"></iconify-icon>' +
            '</div>' +
            '<div>' +
            '<p class="text-sm font-medium text-fg-primary">' +
            escapeHtml(order.product) +
            '</p>' +
            '<p class="text-xs text-fg-tertiary mt-0.5">订单号：' +
            order.id +
            '</p>' +
            '</div>' +
            '</div>' +
            '<div class="text-right">' +
            '<p class="text-sm font-semibold ' +
            amountCls +
            '">¥' +
            order.amount.toLocaleString() +
            '</p>' +
            '<span class="text-[10px] ' +
            statusCls +
            ' font-medium px-2 py-0.5 rounded mt-1 inline-block">' +
            order.status +
            '</span>' +
            '</div>' +
            '</div>' +
            '<div class="flex items-center justify-between mt-3 pt-3 border-t border-bg-border text-xs text-fg-tertiary">' +
            '<span>' +
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
        if (!container) return;

        var filtered = getFilteredOrders();

        if (filtered.length === 0) {
            container.innerHTML =
                '<div class="text-center py-12">' +
                '<iconify-icon class="text-5xl text-fg-disabled" icon="mdi:receipt-text-outline"></iconify-icon>' +
                '<p class="text-sm text-fg-tertiary mt-3">暂无订单记录</p>' +
                '</div>';
        } else {
            container.innerHTML = filtered
                .map(function (o) {
                    return renderOrderCard(o);
                })
                .join('');
        }

        if (countEl) countEl.textContent = '共 ' + filtered.length + ' 条记录';
    }

    function initStatusFilter() {
        var select = document.getElementById('orders-status-filter');
        if (select) {
            select.addEventListener('change', function () {
                var val = this.value;
                if (val === '全部状态') val = 'all';
                _currentFilter = val;
                renderOrders();
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
        var statusCls = getStatusClass(order.statusType);

        var content =
            '<div class="space-y-4">' +
            '<div class="p-3 bg-bg-subtle rounded-xl">' +
            '<div class="flex items-center gap-2 flex-wrap mb-2">' +
            '<span class="text-sm font-semibold font-mono text-fg-primary">' +
            escapeHtml(order.id) +
            '</span>' +
            '<span class="text-[10px] ' +
            statusCls +
            ' font-medium px-2 py-0.5 rounded-full">' +
            escapeHtml(order.status) +
            '</span>' +
            '</div>' +
            '<p class="text-xs text-fg-secondary">' +
            escapeHtml(order.product) +
            '</p>' +
            '</div>' +
            '<div class="grid grid-cols-2 gap-3 text-sm">' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">订单金额</p>' +
            '<p class="text-lg font-bold text-brand">¥' +
            order.amount.toLocaleString() +
            '</p>' +
            '</div>' +
            '<div class="p-3 bg-white border border-bg-border rounded-lg">' +
            '<p class="text-[11px] text-fg-tertiary mb-1">下单时间</p>' +
            '<p class="text-sm text-fg-primary">' +
            escapeHtml(order.date) +
            '</p>' +
            '</div>' +
            '</div>' +
            '<div class="p-3 bg-bg-subtle rounded-xl space-y-2">' +
            '<div class="flex items-center justify-between text-sm">' +
            '<span class="text-fg-tertiary">支付方式</span>' +
            '<span class="text-fg-primary">支付宝</span>' +
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
            '<div class="p-3 bg-bg-subtle rounded-xl space-y-2">' +
            '<p class="text-[11px] text-fg-tertiary">购买明细</p>' +
            '<div class="flex items-center justify-between text-sm">' +
            '<span class="text-fg-secondary">' +
            escapeHtml(order.product) +
            '</span>' +
            '<span class="text-fg-primary">¥' +
            order.amount.toLocaleString() +
            '</span>' +
            '</div>' +
            '</div>' +
            '</div>';

        var footer =
            '<button class="h-9 px-4 text-xs text-fg-secondary bg-white border border-bg-border rounded-lg hover:bg-bg" onclick="closeOrderDetail()">关闭</button>' +
            (order.statusType === 'success'
                ? '<button class="h-9 px-4 text-xs text-white bg-brand hover:bg-brand-hover rounded-lg" onclick="closeOrderDetail(); applyInvoice(\'' +
                  order.id +
                  '\')">申请发票</button>'
                : '') +
            (order.statusType === 'cancelled'
                ? '<button class="h-9 px-4 text-xs text-white bg-brand hover:bg-brand-hover rounded-lg" onclick="closeOrderDetail(); resubscribe(\'' +
                  order.id +
                  '\')">重新订阅</button>'
                : '');

        if (_closeOrderDetail) _closeOrderDetail();
        _closeOrderDetail = Utils.showModal({
            id: 'order-detail-modal',
            title: '订单详情',
            icon: 'mdi:receipt-text-outline',
            content: content,
            footer: footer,
            size: 'md'
        });
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
            '<div class="p-3 bg-bg-subtle rounded-xl text-sm">' +
            '<div class="flex items-center justify-between mb-1">' +
            '<span class="text-fg-tertiary">订单号</span>' +
            '<span class="font-mono text-fg-primary">' +
            escapeHtml(order.id) +
            '</span>' +
            '</div>' +
            '<div class="flex items-center justify-between">' +
            '<span class="text-fg-tertiary">开票金额</span>' +
            '<span class="font-semibold text-brand">¥' +
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
            '<input type="email" placeholder="请输入接收发票的邮箱" class="w-full h-9 px-3 text-sm border border-bg-border rounded-lg focus:outline-none focus:border-brand"/>' +
            '</div>' +
            '<div>' +
            '<label class="block text-xs font-medium text-fg-secondary mb-1.5">发票抬头</label>' +
            '<input type="text" placeholder="个人姓名或企业名称" class="w-full h-9 px-3 text-sm border border-bg-border rounded-lg focus:outline-none focus:border-brand"/>' +
            '</div>' +
            '</div>';

        var footer =
            '<button class="h-9 px-4 text-xs text-fg-secondary bg-white border border-bg-border rounded-lg hover:bg-bg" onclick="closeInvoiceModal()">取消</button>' +
            '<button class="h-9 px-4 text-xs text-white bg-brand hover:bg-brand-hover rounded-lg" onclick="submitInvoice(\'' +
            order.id +
            '\')">提交申请</button>';

        if (_closeInvoiceModal) _closeInvoiceModal();
        _closeInvoiceModal = Utils.showModal({
            id: 'invoice-modal',
            title: '申请发票',
            icon: 'mdi:file-text-outline',
            content: content,
            footer: footer,
            size: 'sm'
        });
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

    function initOrders() {
        initStatusFilter();
        renderOrders();
    }

    globalThis.viewOrderDetail = viewOrderDetail;
    globalThis.closeOrderDetail = closeOrderDetail;
    globalThis.applyInvoice = applyInvoice;
    globalThis.closeInvoiceModal = closeInvoiceModal;
    globalThis.submitInvoice = submitInvoice;
    globalThis.resubscribe = resubscribe;
    globalThis.initOrders = initOrders;
})();
