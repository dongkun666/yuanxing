/**
 * 订单记录模块
 * 包含: 订单列表渲染、筛选、分页、详情弹窗、发票申请、重新订阅
 */
(function() {
    'use strict';

    // ===== 订单数据 =====
    var ordersData = [];

    function initOrdersData() {
        try {
            var saved = localStorage.getItem('lexprime_orders');
            if (saved) {
                var data = JSON.parse(saved);
                if (Array.isArray(data) && data.length > 0) return data;
            }
        } catch (e) { /* fall through to mock */ }

        return [
            {
                id: 'LP20260821001',
                plan: '专业版',
                billing: '月付',
                amount: 299,
                originalAmount: 299,
                status: 'paid',
                statusText: '支付成功',
                createTime: '2026-08-21 15:30',
                payTime: '2026-08-21 15:31',
                payMethod: '支付宝',
                invoiceStatus: 'none',
                description: 'LexPrime 专业版会员 · 月付'
            },
            {
                id: 'LP20260721001',
                plan: '专业版',
                billing: '月付',
                amount: 299,
                originalAmount: 299,
                status: 'paid',
                statusText: '支付成功',
                createTime: '2026-07-21 14:20',
                payTime: '2026-07-21 14:21',
                payMethod: '微信支付',
                invoiceStatus: 'applied',
                description: 'LexPrime 专业版会员 · 月付'
            },
            {
                id: 'LP20260615001',
                plan: '企业版',
                billing: '年付',
                amount: 7199,
                originalAmount: 10788,
                status: 'cancelled',
                statusText: '已取消',
                createTime: '2026-06-15 10:05',
                payTime: '',
                payMethod: '',
                invoiceStatus: 'none',
                cancelReason: '用户主动取消',
                description: 'LexPrime 企业版会员 · 年付'
            },
            {
                id: 'LP20260515001',
                plan: '专业版',
                billing: '年付',
                amount: 2399,
                originalAmount: 3588,
                status: 'paid',
                statusText: '支付成功',
                createTime: '2026-05-15 09:10',
                payTime: '2026-05-15 09:12',
                payMethod: '支付宝',
                invoiceStatus: 'done',
                description: 'LexPrime 专业版会员 · 年付（享8折优惠）'
            },
            {
                id: 'LP20260412001',
                plan: '专业版',
                billing: '月付',
                amount: 299,
                originalAmount: 299,
                status: 'paid',
                statusText: '支付成功',
                createTime: '2026-04-12 16:45',
                payTime: '2026-04-12 16:46',
                payMethod: '微信支付',
                invoiceStatus: 'done',
                description: 'LexPrime 专业版会员 · 月付'
            },
            {
                id: 'LP20260312001',
                plan: '专业版',
                billing: '月付',
                amount: 299,
                originalAmount: 299,
                status: 'paid',
                statusText: '支付成功',
                createTime: '2026-03-12 11:30',
                payTime: '2026-03-12 11:30',
                payMethod: '支付宝',
                invoiceStatus: 'done',
                description: 'LexPrime 专业版会员 · 月付'
            },
            {
                id: 'LP20260208001',
                plan: '专业版',
                billing: '月付',
                amount: 299,
                originalAmount: 299,
                status: 'refunded',
                statusText: '已退款',
                createTime: '2026-02-08 08:20',
                payTime: '2026-02-08 08:21',
                payMethod: '支付宝',
                invoiceStatus: 'none',
                refundTime: '2026-02-10 14:00',
                refundAmount: 299,
                description: 'LexPrime 专业版会员 · 月付'
            }
        ];
    }

    // ===== 筛选状态 =====
    var currentOrderFilter = 'all';
    var currentPage = 1;
    var pageSize = 5;

    // ===== 初始化 =====
    function initOrders() {
        ordersData = initOrdersData();
        currentOrderFilter = 'all';
        currentPage = 1;
        renderOrders();
    }

    // ===== 持久化 =====
    function persistOrders() {
        try { localStorage.setItem('lexprime_orders', JSON.stringify(ordersData)); } catch (e) {}
    }

    // ===== 筛选订单 =====
    function getFilteredOrders() {
        if (currentOrderFilter === 'all') return ordersData;
        var statusMap = {
            'paid': 'paid',
            'processing': 'processing',
            'cancelled': 'cancelled',
            'refunded': 'refunded'
        };
        var targetStatus = statusMap[currentOrderFilter];
        if (!targetStatus) return ordersData;
        return ordersData.filter(function(o) { return o.status === targetStatus; });
    }

    // ===== 筛选回调 =====
    window.filterOrders = function(filterValue) {
        currentOrderFilter = filterValue;
        currentPage = 1;
        updateFilterButtons();
        renderOrders();
    };

    function updateFilterButtons() {
        var select = document.getElementById('order-filter-select');
        if (select) select.value = currentOrderFilter;
    }

    // ===== 渲染订单列表 =====
    function renderOrders() {
        var container = document.getElementById('orders-container');
        if (!container) return;

        var filtered = getFilteredOrders();
        var totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
        if (currentPage > totalPages) currentPage = totalPages;
        var start = (currentPage - 1) * pageSize;
        var pageItems = filtered.slice(start, start + pageSize);

        // 更新筛选下拉框
        var select = document.getElementById('order-filter-select');
        if (select) {
            select.value = currentOrderFilter;
            select.onchange = function() { filterOrders(this.value); };
        }

        if (pageItems.length === 0) {
            container.innerHTML =
                '<div class="bg-white rounded-xl border border-bg-border p-10 text-center">' +
                '<iconify-icon icon="mdi:receipt-text-outline" class="text-4xl text-fg-tertiary mb-3"></iconify-icon>' +
                '<p class="text-sm text-fg-tertiary">暂无订单记录</p>' +
                '</div>';
            renderPagination(0, 1);
            return;
        }

        var html = '';
        pageItems.forEach(function(order) {
            var planIcon = getPlanIcon(order.plan);
            var statusCls = getStatusClass(order.status);
            var isInactive = (order.status === 'cancelled' || order.status === 'refunded');
            var discount = order.amount < order.originalAmount;

            html += '<div class="bg-white rounded-xl border border-bg-border p-5 hover:shadow-sm transition-shadow' + (isInactive ? ' opacity-70' : '') + '" data-order-id="' + order.id + '">' +
                '<div class="flex items-center justify-between">' +
                    '<div class="flex items-center gap-3">' +
                        '<div class="w-10 h-10 rounded-lg ' + planIcon.bg + ' flex items-center justify-center">' +
                            '<iconify-icon class="text-lg ' + planIcon.color + '" icon="' + planIcon.icon + '"></iconify-icon>' +
                        '</div>' +
                        '<div>' +
                            '<p class="text-sm font-medium text-fg-primary">' + escapeHtml(order.plan) + ' · ' + escapeHtml(order.billing) + '</p>' +
                            '<p class="text-xs text-fg-tertiary mt-0.5">订单号：' + escapeHtml(order.id) + '</p>' +
                        '</div>' +
                    '</div>' +
                    '<div class="text-right">' +
                        '<p class="text-sm font-semibold ' + (isInactive ? 'text-fg-disabled' : 'text-fg-primary') + '">' + formatAmount(order.amount) + '</p>' +
                        (discount ? '<p class="text-[10px] text-fg-tertiary line-through">' + formatAmount(order.originalAmount) + '</p>' : '') +
                        '<span class="text-[10px] ' + statusCls + ' font-medium px-2 py-0.5 rounded mt-1 inline-block">' + escapeHtml(order.statusText) + '</span>' +
                    '</div>' +
                '</div>' +
                '<div class="flex items-center justify-between mt-3 pt-3 border-t border-bg-border text-xs text-fg-tertiary">' +
                    '<span>' + escapeHtml(order.createTime) + '</span>' +
                    '<div class="flex gap-3">' +
                        '<button class="text-brand hover:underline" onclick="openOrderDetail(\'' + order.id + '\')">查看详情</button>' +
                        renderOrderActions(order) +
                    '</div>' +
                '</div>' +
            '</div>';
        });

        container.innerHTML = html;
        renderPagination(filtered.length, totalPages);
    }

    function getPlanIcon(plan) {
        if (plan === '企业版') return { icon: 'mdi:domain', bg: 'bg-purple-50', color: 'text-purple-500' };
        if (plan === '专业版') return { icon: 'mdi:star', bg: 'bg-brand-tint3', color: 'text-brand' };
        return { icon: 'mdi:account-outline', bg: 'bg-gray-50', color: 'text-gray-500' };
    }

    function getStatusClass(status) {
        var map = {
            'paid': 'bg-green-50 text-success',
            'processing': 'bg-amber-50 text-warning',
            'cancelled': 'bg-bg text-fg-tertiary',
            'refunded': 'bg-red-50 text-red-500'
        };
        return map[status] || 'bg-bg text-fg-tertiary';
    }

    function renderOrderActions(order) {
        var actions = '';
        if (order.status === 'paid' || order.status === 'processing') {
            if (order.invoiceStatus === 'none') {
                actions += '<button class="text-brand hover:underline" onclick="applyInvoice(\'' + order.id + '\')">申请发票</button>';
            } else if (order.invoiceStatus === 'applied') {
                actions += '<button class="text-fg-tertiary cursor-default">发票处理中</button>';
            } else {
                actions += '<button class="text-fg-tertiary cursor-default">已开票</button>';
            }
        }
        if (order.status === 'cancelled' || order.status === 'refunded') {
            actions += '<button class="text-brand hover:underline" onclick="resubscribe(\'' + order.plan + '\')">重新订阅</button>';
        }
        return actions;
    }

    function renderPagination(totalItems, totalPages) {
        var paginationContainer = document.querySelector('#view-orders .flex.items-center.justify-between.text-xs');
        if (!paginationContainer) return;

        var countSpan = paginationContainer.querySelector('span');
        if (countSpan) countSpan.textContent = '共 ' + totalItems + ' 条记录';

        var pageDiv = document.getElementById('orders-pagination');
        if (!pageDiv) return;

        if (totalPages <= 1) {
            pageDiv.innerHTML = '';
            return;
        }

        var html = '';
        // 上一页
        html += '<button class="w-8 h-8 rounded-lg hover:bg-bg-subtle flex items-center justify-center text-xs' + (currentPage <= 1 ? ' opacity-50 cursor-not-allowed' : '') + '" onclick="' + (currentPage > 1 ? 'goToOrderPage(' + (currentPage - 1) + ')' : '') + '"><iconify-icon icon="mdi:chevron-left"></iconify-icon></button>';

        for (var i = 1; i <= totalPages; i++) {
            if (i === currentPage) {
                html += '<button class="w-8 h-8 rounded-lg bg-brand text-white flex items-center justify-center text-xs font-medium">' + i + '</button>';
            } else if (i === 1 || i === totalPages || Math.abs(i - currentPage) <= 1) {
                html += '<button class="w-8 h-8 rounded-lg hover:bg-bg-subtle flex items-center justify-center text-xs" onclick="goToOrderPage(' + i + ')">' + i + '</button>';
            } else if (i === currentPage - 2 || i === currentPage + 2) {
                html += '<span class="w-8 h-8 flex items-center justify-center text-fg-tertiary">...</span>';
            }
        }

        // 下一页
        html += '<button class="w-8 h-8 rounded-lg hover:bg-bg-subtle flex items-center justify-center text-xs' + (currentPage >= totalPages ? ' opacity-50 cursor-not-allowed' : '') + '" onclick="' + (currentPage < totalPages ? 'goToOrderPage(' + (currentPage + 1) + ')' : '') + '"><iconify-icon icon="mdi:chevron-right"></iconify-icon></button>';

        pageDiv.innerHTML = html;
    }

    // ===== 分页回调 =====
    window.goToOrderPage = function(page) {
        var filtered = getFilteredOrders();
        var totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
        if (page < 1 || page > totalPages) return;
        currentPage = page;
        renderOrders();
    };

    // ===== 订单详情弹窗 =====
    window.openOrderDetail = function(orderId) {
        var order = ordersData.find(function(o) { return o.id === orderId; });
        if (!order) return;

        var modal = document.getElementById('order-detail-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'order-detail-modal';
            modal.className = 'hidden fixed inset-0 z-[1000] bg-black/40 flex items-center justify-center p-4';
            modal.onclick = function(e) { if (e.target === modal) modal.classList.add('hidden'); };
            document.body.appendChild(modal);
        }

        var isInactive = (order.status === 'cancelled' || order.status === 'refunded');
        var statusCls = getStatusClass(order.status);
        var discount = order.amount < order.originalAmount;

        modal.innerHTML =
            '<div class="bg-white rounded-xl w-[520px] max-w-full max-h-[85vh] flex flex-col shadow-2xl" onclick="event.stopPropagation()">' +
                '<div class="flex items-center justify-between p-5 border-b border-bg-border">' +
                    '<h3 class="text-base font-semibold text-fg-primary">订单详情</h3>' +
                    '<button class="text-fg-tertiary hover:text-fg-secondary" onclick="closeOrderDetail()"><iconify-icon icon="mdi:close" class="text-xl"></iconify-icon></button>' +
                '</div>' +
                '<div class="p-5 overflow-y-auto flex-1 space-y-4">' +
                    // 订单状态
                    '<div class="flex items-center justify-between p-3 rounded-lg bg-bg-subtle">' +
                        '<span class="text-xs text-fg-secondary">订单状态</span>' +
                        '<span class="text-xs font-medium px-2 py-0.5 rounded ' + statusCls + '">' + escapeHtml(order.statusText) + '</span>' +
                    '</div>' +
                    // 订单信息
                    '<div class="space-y-3">' +
                        '<h4 class="text-xs font-medium text-fg-secondary">订单信息</h4>' +
                        '<div class="space-y-2">' +
                            orderInfoRow('订单号', order.id) +
                            orderInfoRow('商品描述', order.description) +
                            orderInfoRow('创建时间', order.createTime) +
                            (order.payTime ? orderInfoRow('支付时间', order.payTime) : '') +
                            (order.payMethod ? orderInfoRow('支付方式', order.payMethod) : '') +
                        '</div>' +
                    '</div>' +
                    // 金额明细
                    '<div class="space-y-3">' +
                        '<h4 class="text-xs font-medium text-fg-secondary">金额明细</h4>' +
                        '<div class="bg-white border border-bg-border rounded-lg p-3 space-y-2">' +
                            '<div class="flex justify-between text-xs"><span class="text-fg-secondary">原价</span><span class="text-fg-tertiary">' + formatAmount(order.originalAmount) + '</span></div>' +
                            (discount ? '<div class="flex justify-between text-xs"><span class="text-fg-secondary">优惠</span><span class="text-success">-' + formatAmount(order.originalAmount - order.amount) + '</span></div>' : '') +
                            '<div class="flex justify-between text-sm font-semibold pt-2 border-t border-bg-border"><span>实付金额</span><span class="text-brand">' + formatAmount(order.amount) + '</span></div>' +
                        '</div>' +
                    '</div>' +
                    // 发票信息
                    (order.status === 'paid' || order.status === 'processing' ? (
                        '<div class="space-y-3">' +
                            '<h4 class="text-xs font-medium text-fg-secondary">发票信息</h4>' +
                            '<div class="flex items-center justify-between">' +
                                '<span class="text-xs text-fg-tertiary">' + getInvoiceText(order.invoiceStatus) + '</span>' +
                                (order.invoiceStatus === 'none' ? '<button class="text-xs text-brand hover:underline" onclick="applyInvoice(\'' + order.id + '\'); closeOrderDetail();">申请发票</button>' : '') +
                            '</div>' +
                        '</div>'
                    ) : '') +
                    // 退款信息
                    (order.status === 'refunded' ? (
                        '<div class="space-y-3">' +
                            '<h4 class="text-xs font-medium text-fg-secondary">退款信息</h4>' +
                            '<div class="space-y-2">' +
                                (order.refundTime ? orderInfoRow('退款时间', order.refundTime) : '') +
                                (order.refundAmount ? orderInfoRow('退款金额', formatAmount(order.refundAmount)) : '') +
                            '</div>' +
                        '</div>'
                    ) : '') +
                    // 取消原因
                    (order.cancelReason ? (
                        '<div class="space-y-3">' +
                            '<h4 class="text-xs font-medium text-fg-secondary">取消原因</h4>' +
                            '<p class="text-xs text-fg-tertiary">' + escapeHtml(order.cancelReason) + '</p>' +
                        '</div>'
                    ) : '') +
                '</div>' +
                '<div class="p-4 border-t border-bg-border flex justify-end">' +
                    '<button class="px-4 py-2 text-xs text-fg-secondary hover:bg-bg-subtle rounded-lg" onclick="closeOrderDetail()">关闭</button>' +
                '</div>' +
            '</div>';

        modal.classList.remove('hidden');
    };

    function orderInfoRow(label, value) {
        return '<div class="flex justify-between text-xs"><span class="text-fg-secondary">' + escapeHtml(label) + '</span><span class="text-fg-primary">' + escapeHtml(value) + '</span></div>';
    }

    function getInvoiceText(status) {
        var map = { 'none': '未申请发票', 'applied': '发票开具中', 'done': '发票已开具' };
        return map[status] || '未申请发票';
    }

    window.closeOrderDetail = function() {
        var modal = document.getElementById('order-detail-modal');
        if (modal) modal.classList.add('hidden');
    };

    // ===== 申请发票 =====
    window.applyInvoice = function(orderId) {
        var order = ordersData.find(function(o) { return o.id === orderId; });
        if (!order) return;
        if (order.invoiceStatus !== 'none') {
            showToast('该订单已申请发票');
            return;
        }
        order.invoiceStatus = 'applied';
        persistOrders();
        showToast('发票申请已提交，预计 3 个工作日内开具');
        renderOrders();
    };

    // ===== 重新订阅 =====
    window.resubscribe = function(planName) {
        if (typeof switchView === 'function') {
            switchView('subscription');
        }
        if (typeof showToast === 'function') {
            showToast('已跳转到订阅页面，请选择' + planName + '方案');
        }
    };

    // ===== 工具函数 =====
    function formatAmount(amount) {
        return '¥' + Number(amount).toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
    }

    function escapeHtml(str) {
        return String(str || '').replace(/[&<>"']/g, function(m) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
        });
    }

    // ===== 视图加载监听 =====
    function watchOrdersView() {
        var observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(m) {
                if (m.target.id === 'view-orders' && !m.target.classList.contains('hidden')) {
                    initOrders();
                }
            });
        });
        var viewEl = document.getElementById('view-orders');
        if (viewEl) {
            observer.observe(viewEl, { attributes: true, attributeFilter: ['class'] });
        }
    }

    // 初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', watchOrdersView);
    } else {
        watchOrdersView();
    }

    // 全局暴露（供router/switchView回调）
    window.initOrders = initOrders;
    window.renderOrders = renderOrders;
})();
