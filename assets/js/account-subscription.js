/**
 * 账号 - 会员/支付模块
 * 拆分自 account.js (2026-06-28 IIFE 拆分计划)
 *
 * 包含: 用户菜单 + 会员订阅页 + 月年付切换 + 支付方式 + 支付成功页 + 订单 + 会员中心 + 账号设置路由
 * 依赖: AppState (app-state.js), switchView/switchSidebarTab/loadView (router.js),
 *       setupOutsideClickClose (account-notifications.js)
 *
 * 加载顺序: 在 account-notifications.js 之后, account-profile.js 之前
 */

(function () {
    'use strict';

    // 右上角用户菜单 toggle
    function toggleUserMenu(event) {
        if (event) event.stopPropagation();
        var menu = document.getElementById('userMenu');
        if (!menu) return;
        if (menu.classList.contains('hidden')) {
            menu.classList.remove('hidden');
            setTimeout(function () {
                setupOutsideClickClose('userMenu', '[onclick*="toggleUserMenu"]');
            }, 0);
        } else {
            menu.classList.add('hidden');
        }
    }

    // 跳到订阅页
    function switchToSubscription() {
        var userMenu = document.getElementById('userMenu');
        if (userMenu) userMenu.classList.add('hidden');

        switchSidebarTab('work');

        document.querySelectorAll('.sidebar-item').forEach(function (item) {
            item.classList.remove('active');
        });

        var target = document.getElementById('view-subscription');
        if (target) {
            document.querySelectorAll('.view-content').forEach(function (v) {
                v.classList.add('hidden');
            });
            target.classList.remove('hidden');
        } else {
            loadView('subscription', function (html) {
                document.getElementById('main-content').insertAdjacentHTML('beforeend', html);
                var newTarget = document.getElementById('view-subscription');
                if (newTarget) {
                    document.querySelectorAll('.view-content').forEach(function (v) {
                        v.classList.add('hidden');
                    });
                    newTarget.classList.remove('hidden');
                }
            });
        }
    }

    // 月/年付切换
    function toggleBilling() {
        AppState.isYearly = !AppState.isYearly;
        var toggle = document.getElementById('billing-toggle');
        var knob = document.getElementById('billing-knob');
        var monthlyLabel = document.getElementById('monthly-label');
        var yearlyLabel = document.getElementById('yearly-label');

        if (AppState.isYearly) {
            toggle.style.backgroundColor = '#165DFF';
            knob.style.transform = 'translateX(24px)';
            monthlyLabel.style.color = '#86909C';
            yearlyLabel.style.color = '#1D2129';

            document.getElementById('pro-price').textContent = '¥2,399';
            document.getElementById('pro-period').textContent = '/年';
            document.getElementById('pro-tip').textContent = '年付省 ¥1,189';

            document.getElementById('enterprise-price').textContent = '¥7,199';
            document.getElementById('enterprise-period').textContent = '/年';
            document.getElementById('enterprise-tip').textContent = '年付省 ¥3,589';
        } else {
            toggle.style.backgroundColor = '#165DFF';
            knob.style.transform = 'translateX(0)';
            monthlyLabel.style.color = '#1D2129';
            yearlyLabel.style.color = '#86909C';

            document.getElementById('pro-price').textContent = '¥299';
            document.getElementById('pro-period').textContent = '/月';
            document.getElementById('pro-tip').textContent = '最适合个人律师';

            document.getElementById('enterprise-price').textContent = '¥899';
            document.getElementById('enterprise-period').textContent = '/月';
            document.getElementById('enterprise-tip').textContent = '适合律所及团队';
        }
    }

    // 跳到支付页
    function showPayment(plan) {
        var planNames = {
            free: '免费版',
            professional: '专业版',
            enterprise: '企业版'
        };
        var planDesc = {
            free: '基础功能体验',
            professional: '最适合个人律师',
            enterprise: '适合律所及团队'
        };
        var planPrice = {
            free: '¥0',
            professional: AppState.isYearly ? '¥2,399' : '¥299',
            enterprise: AppState.isYearly ? '¥7,199' : '¥899'
        };

        if (plan === 'free') {
            Utils.showToast('info', '免费版无需支付，可直接使用。如需要更多功能，请选择专业版或企业版。');
            return;
        }

        var billingText = AppState.isYearly ? '年付' : '月付';
        document.getElementById('payment-plan-name').textContent = planNames[plan] + ' · ' + billingText;
        document.getElementById('payment-plan-desc').textContent = planDesc[plan];
        document.getElementById('payment-amount').textContent = planPrice[plan];
        document.getElementById('payment-subtotal').textContent = planPrice[plan];
        document.getElementById('payment-total').textContent = planPrice[plan];
        document.getElementById('pay-button-amount').textContent = planPrice[plan];

        document.querySelectorAll('.view-content').forEach(function (v) {
            v.classList.add('hidden');
        });
        document.getElementById('view-payment').classList.remove('hidden');
    }

    // 返回订阅页
    function backToSubscription() {
        document.querySelectorAll('.view-content').forEach(function (v) {
            v.classList.add('hidden');
        });
        document.getElementById('view-subscription').classList.remove('hidden');
    }

    // 支付方式选择
    function selectPaymentMethod(el, method) {
        AppState.selectedPayment = method;
        document.querySelectorAll('.payment-method').forEach(function (btn) {
            btn.classList.remove('border-[#165DFF]', 'bg-[#F2F7FF]');
            btn.classList.add('border-[#E5E6EB]');
            var dot = btn.querySelector('.w-5.h-5');
            if (dot) {
                dot.classList.remove('border-[#165DFF]');
                dot.classList.add('border-[#E5E6EB]');
                var inner = dot.querySelector('.w-2\\.5');
                if (inner) inner.remove();
            }
        });
        el.classList.remove('border-[#E5E6EB]');
        el.classList.add('border-[#165DFF]', 'bg-[#F2F7FF]');
        var dot = el.querySelector('.w-5.h-5');
        if (dot) {
            dot.classList.remove('border-[#E5E6EB]');
            dot.classList.add('border-[#165DFF]');
            var inner = document.createElement('div');
            inner.className = 'w-2.5 h-2.5 rounded-full bg-[#165DFF]';
            dot.appendChild(inner);
        }
    }

    // 支付成功 → 跳成功页
    function paySuccess() {
        var planEl = document.getElementById('payment-plan-name');
        var amountEl = document.getElementById('payment-total');
        var planName = planEl ? planEl.textContent : '专业版 · 月付';
        var amount = amountEl ? amountEl.textContent : '¥299';

        var methodNames = { alipay: '支付宝', wechat: '微信支付', unionpay: '银联支付' };
        var methodName = methodNames[AppState.selectedPayment] || '支付宝';

        document.getElementById('success-plan-info').textContent = planName + ' 已生效';
        document.getElementById('success-plan').textContent = planName;
        document.getElementById('success-amount').textContent = amount;
        document.getElementById('success-payment-method').textContent = methodName;

        var now = new Date();
        var orderNo =
            'LP' +
            now.getFullYear() +
            String(now.getMonth() + 1).padStart(2, '0') +
            String(now.getDate()).padStart(2, '0') +
            '001';
        document.getElementById('success-order-no').textContent = orderNo;

        var expiry = new Date(now);
        expiry.setMonth(expiry.getMonth() + 1);
        document.getElementById('success-expiry').textContent =
            expiry.getFullYear() +
            '-' +
            String(expiry.getMonth() + 1).padStart(2, '0') +
            '-' +
            String(expiry.getDate()).padStart(2, '0');

        document.querySelectorAll('.view-content').forEach(function (v) {
            v.classList.add('hidden');
        });
        document.getElementById('view-payment-success').classList.remove('hidden');
    }

    function goToSubscription() {
        switchView('subscription');
    }

    function goToWorkstation() {
        switchView('workstation');
    }

    function switchToOrders() {
        var userMenu = document.getElementById('userMenu');
        if (userMenu) userMenu.classList.add('hidden');
        switchView('orders');
    }

    function switchToMemberCenter() {
        var userMenu = document.getElementById('userMenu');
        if (userMenu) userMenu.classList.add('hidden');
        switchView('member-center');
    }

    function goToMemberCenter() {
        switchView('member-center');
    }

    function switchToAccountSettings() {
        var userMenu = document.getElementById('userMenu');
        if (userMenu) userMenu.classList.add('hidden');
        switchView('account-settings');
    }

    // ===== 双绑定 =====
    globalThis.toggleUserMenu = toggleUserMenu;
    globalThis.switchToSubscription = switchToSubscription;
    globalThis.toggleBilling = toggleBilling;
    globalThis.showPayment = showPayment;
    globalThis.backToSubscription = backToSubscription;
    globalThis.selectPaymentMethod = selectPaymentMethod;
    globalThis.paySuccess = paySuccess;
    globalThis.goToSubscription = goToSubscription;
    globalThis.goToWorkstation = goToWorkstation;
    globalThis.switchToOrders = switchToOrders;
    globalThis.switchToMemberCenter = switchToMemberCenter;
    globalThis.goToMemberCenter = goToMemberCenter;
    globalThis.switchToAccountSettings = switchToAccountSettings;
})();
