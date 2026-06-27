/**
 * 账号/会员/支付模块
 * 包含: 通知面板 + 会员订阅 + 支付 + 账号设置 + 个人资料 + 第三方账号
 * 加载: 在 script.js 之前同步加载
 */


        function toggleNotifications(event) {
            if (event) event.stopPropagation();
            var panel = document.getElementById('notificationPanel');
            panel.classList.toggle('hidden');
            if (!panel.classList.contains('hidden')) {
                // 打开时渲染最新通知 (数据驱动)
                renderNotificationsPanel();
                // 打开后注册外部点击关闭 (延迟 0ms 避免本次 click 立即触发)
                setTimeout(function() {
                    setupOutsideClickClose('notificationPanel', '[onclick*="toggleNotifications"]');
                }, 0);
            }
        }

        // 通用外部点击关闭 helper
        // panelId: 弹出框元素 ID
        // triggerSelector: 触发按钮 selector (可省略, 默认通过 [onclick*="toggle${panelId}"] 推断)
        // 注册一个 document click 监听, 点击 panel 或 trigger 外时关闭 panel
        // 多次调用幂等 (同 listener 函数引用不会重复注册)
        function setupOutsideClickClose(panelId, triggerSelector) {
            var handlerName = 'close' + panelId.charAt(0).toUpperCase() + panelId.slice(1) + 'OnOutside';
            // 复用同一个全局 listener 函数 (避免重复注册)
            if (!window[handlerName]) {
                window[handlerName] = function(e) {
                    var panel = document.getElementById(panelId);
                    if (!panel || panel.classList.contains('hidden')) return;
                    // 推断 trigger: 优先用传入的 selector, 否则找 onclick 含 toggleXXX 的元素
                    var trig = triggerSelector ? document.querySelector(triggerSelector) : document.querySelector('[onclick*="toggle' + panelId.charAt(0).toUpperCase() + panelId.slice(1) + '"]');
                    if (panel.contains(e.target)) return;
                    if (trig && trig.contains(e.target)) return;
                    panel.classList.add('hidden');
                };
            }
            document.addEventListener('click', window[handlerName]);
        }

        function markAllNotifications() {
            AppState.notifications.forEach(function(n) { n.unread = false; });
            persistNotifications();
            renderNotificationsPanel();
            if (typeof renderNotificationsPage === 'function') renderNotificationsPage();
            updateNotificationBadge();
            showToast('已全部标记为已读');
        }

        // localStorage 持久化
        function persistNotifications() {
            try { localStorage.setItem('lexprime_notifications', JSON.stringify(AppState.notifications)); } catch (e) { console.warn('持久化通知失败:', e); }
        }

        // 铃铛小红点 (未读数 > 0 才显示)
        function updateNotificationBadge() {
            var badge = document.querySelector('button[onclick*="toggleNotifications"] .w-2.h-2');
            if (!badge) return;
            var unread = AppState.notifications.filter(function(n) { return n.unread; }).length;
            if (unread === 0) badge.classList.add('hidden');
            else badge.classList.remove('hidden');
        }

        // 渲染通知面板 (右上角下拉, 最多 5 条)
        function renderNotificationsPanel() {
            var panel = document.getElementById('notificationPanel');
            if (!panel) return;
            var listEl = panel.querySelector('.notification-list');
            if (!listEl) return;
            var items = AppState.notifications.slice(0, 5);
            var colorMap = {
                brand: 'bg-brand-tint text-brand',
                danger: 'bg-danger-tint text-danger',
                warning: 'bg-warning-tint text-warning',
                success: 'bg-success-tint text-success'
            };
            if (items.length === 0) {
                listEl.innerHTML = '<div class="px-3 py-8 text-center text-fg-tertiary text-xs">暂无通知</div>';
                return;
            }
            var htmlStr = '';
            items.forEach(function(n) {
                var cls = colorMap[n.color] || colorMap.brand;
                htmlStr += '<div class="flex items-start gap-3 p-3 hover:bg-bg-subtle border-b border-bg cursor-pointer" onclick="openNotification(\'' + n.id + '\', event)">' +
                    '<div class="w-8 h-8 rounded-full ' + cls + ' flex items-center justify-center flex-shrink-0">' +
                        '<iconify-icon class="text-sm" icon="' + escapeHtml(n.icon || 'mdi:bell-outline') + '"></iconify-icon>' +
                    '</div>' +
                    '<div class="flex-1 min-w-0">' +
                        '<p class="text-xs font-medium text-fg-primary">' + escapeHtml(n.title || '') + '</p>' +
                        '<p class="text-[11px] text-fg-tertiary mt-0.5 line-clamp-2">' + escapeHtml(n.desc || '') + '</p>' +
                        '<p class="text-[10px] text-fg-disabled mt-1">' + escapeHtml(formatTimeAgo(n.timestamp)) + '</p>' +
                    '</div>' +
                    (n.unread ? '<div class="w-1.5 h-1.5 rounded-full bg-brand flex-shrink-0 mt-1.5"></div>' : '') +
                '</div>';
            });
            listEl.innerHTML = htmlStr;
        }

        // 单条点击: 标记已读 + 跳转
        function openNotification(id, event) {
            if (event) event.stopPropagation();
            var n = AppState.notifications.find(function(x) { return x.id === id; });
            if (!n) return;
            // 标记已读
            if (n.unread) {
                n.unread = false;
                persistNotifications();
                renderNotificationsPanel();
                if (typeof renderNotificationsPage === 'function') renderNotificationsPage();
                updateNotificationBadge();
            }
            // 跳转
            if (n.linkTo && typeof switchView === 'function') {
                // 关闭面板
                var panel = document.getElementById('notificationPanel');
                if (panel) panel.classList.add('hidden');
                if (n.linkParam) {
                    // 拼接 query string (例如 case-detail?id=1)
                    switchView(n.linkTo + (n.linkTo.includes('?') ? '&' : '?') + 'id=' + n.linkParam);
                } else {
                    switchView(n.linkTo);
                }
            }
        }

        // 打开「全部通知」全屏页
        function switchToNotifications() {
            // 关闭面板
            var panel = document.getElementById('notificationPanel');
            if (panel) panel.classList.add('hidden');
            if (typeof switchView === 'function') switchView('notifications');
        }

        // 渲染全屏通知页
        // filter: 'all' (默认) | 'unread' | 'read' (状态维度)
        // type:   'all' (默认) | 'document' | 'deadline' | 'case' | 'member' | 'system' (主题维度)
        // 两 filter 独立并存, 叠加生效 (AND)
        function setNotificationsFilter(f) {
            if (typeof AppState === 'undefined') return;
            AppState.notificationsFilter = f;
            renderNotificationsPage();
            // 同步 tab active
            document.querySelectorAll('.notif-filter-tab').forEach(function(btn) {
                if (btn.dataset.filter === f) {
                    btn.className = 'notif-filter-tab text-xs px-3 py-1.5 rounded-full bg-brand text-white font-medium';
                } else {
                    btn.className = 'notif-filter-tab text-xs px-3 py-1.5 rounded-full bg-bg-subtle text-fg-secondary hover:bg-bg font-medium';
                }
            });
        }
        // 类型 filter (独立维度)
        function setNotificationsType(t) {
            if (typeof AppState === 'undefined') return;
            AppState.notificationsType = t;
            renderNotificationsPage();
            document.querySelectorAll('.notif-type-tab').forEach(function(btn) {
                if (btn.dataset.type === t) {
                    // active: bg-brand text-white + 保留 type-tab 前缀 (用于下次查询)
                    var iconHtml = btn.innerHTML.match(/<iconify-icon[^>]*><\/iconify-icon>/);
                    var iconStr = iconHtml ? iconHtml[0] + ' ' : '';
                    btn.className = 'notif-type-tab text-xs px-3 py-1.5 rounded-full bg-brand text-white font-medium flex items-center gap-1';
                    btn.innerHTML = iconStr + escapeHtml(btn.dataset.type === 'all' ? '全部类型' : ({
                        document: '文档', deadline: '截止', case: '案件', member: '会员', system: '系统'
                    })[btn.dataset.type] || '');
                } else {
                    var iconHtml2 = btn.innerHTML.match(/<iconify-icon[^>]*><\/iconify-icon>/);
                    var iconStr2 = iconHtml2 ? iconHtml2[0] + ' ' : '';
                    var lbl = btn.dataset.type === 'all' ? '全部类型' : ({
                        document: '文档', deadline: '截止', case: '案件', member: '会员', system: '系统'
                    })[btn.dataset.type] || '';
                    btn.className = 'notif-type-tab text-xs px-3 py-1.5 rounded-full bg-bg-subtle text-fg-secondary hover:bg-bg font-medium flex items-center gap-1';
                    btn.innerHTML = iconStr2 + escapeHtml(lbl);
                }
            });
        }
        // 清空通知 (一键)
        function clearAllNotifications() {
            if (typeof AppState === 'undefined') return;
            if (AppState.notifications.length === 0) {
                showToast('通知已是空的');
                return;
            }
            if (!confirm('确定清空所有通知？此操作不可恢复。')) return;
            AppState.notifications = [];
            persistNotifications();
            renderNotificationsPanel();
            renderNotificationsPage();
            updateNotificationBadge();
            showToast('通知已清空');
        }
        // 「···」更多菜单 toggle
        function toggleNotifMoreMenu(event) {
            if (event) event.stopPropagation();
            var menu = document.getElementById('notifMoreMenu');
            if (!menu) return;
            menu.classList.toggle('hidden');
            if (!menu.classList.contains('hidden')) {
                setTimeout(function() {
                    setupOutsideClickClose('notifMoreMenu', '[onclick*="toggleNotifMoreMenu"]');
                }, 0);
            }
        }
        // 实时时间格式化: 从 timestamp 计算 "X 分钟前 / X 小时前 / 昨天 / M月D日 / YYYY-MM-DD"
        function formatTimeAgo(ts) {
            if (!ts) return '';
            var diffMs = Date.now() - ts;
            var sec = Math.floor(diffMs / 1000);
            if (sec < 60) return '刚刚';
            var min = Math.floor(sec / 60);
            if (min < 60) return min + ' 分钟前';
            var hr = Math.floor(min / 60);
            if (hr < 24) return hr + ' 小时前';
            var day = Math.floor(hr / 24);
            if (day === 1) return '昨天';
            if (day < 7) return day + ' 天前';
            var d = new Date(ts);
            var y = d.getFullYear();
            var m = d.getMonth() + 1;
            var dd = d.getDate();
            if (day < 365) return m + '月' + dd + '日';
            return y + '-' + (m < 10 ? '0' + m : m) + '-' + (dd < 10 ? '0' + dd : dd);
        }
        // 每分钟重渲染可见通知的 timeAgo (让 "3 分钟前" 实时变 "5 分钟前")
        var notifRefreshTimer = null;
        function startNotificationTimeRefresh() {
            if (notifRefreshTimer) return;
            notifRefreshTimer = setInterval(function() {
                if (typeof AppState === 'undefined') return;
                renderNotificationsPanel();
                var view = document.getElementById('view-notifications');
                if (view && !view.classList.contains('hidden')) renderNotificationsPage();
            }, 60 * 1000);
        }
        function renderNotificationsPage() {
            if (typeof AppState === 'undefined') return;
            if (!AppState.notificationsFilter) AppState.notificationsFilter = 'all';
            if (!AppState.notificationsType) AppState.notificationsType = 'all';
            var container = document.getElementById('notifications-list');
            var countEl = document.getElementById('notifications-count');
            if (!container) return;
            var f = AppState.notificationsFilter || 'all';
            var t = AppState.notificationsType || 'all';
            var items = AppState.notifications.slice().sort(function(a, b) {
                // 未读优先 + 时间倒序
                if (!!a.unread !== !!b.unread) return a.unread ? -1 : 1;
                return (b.timestamp || 0) - (a.timestamp || 0);
            }).filter(function(n) {
                if (f === 'unread' && !n.unread) return false;
                if (f === 'read' && n.unread) return false;
                if (t !== 'all' && n.type !== t) return false;
                return true;
            });
            // 顶部计数 (实时计算)
            if (countEl) {
                var total = AppState.notifications.length;
                var show = items.length;
                countEl.textContent = total === show ? ('共 ' + total + ' 条') : ('显示 ' + show + ' / 共 ' + total + ' 条');
            }
            var colorMap = {
                brand: 'bg-brand-tint text-brand',
                danger: 'bg-danger-tint text-danger',
                warning: 'bg-warning-tint text-warning',
                success: 'bg-success-tint text-success'
            };
            if (items.length === 0) {
                var emptyMsg = '没有通知';
                if (f === 'unread' && t !== 'all') emptyMsg = '没有' + typeLabel(t) + '类型的未读通知';
                else if (f === 'read' && t !== 'all') emptyMsg = '没有' + typeLabel(t) + '类型的已读通知';
                else if (f === 'unread') emptyMsg = '没有未读通知';
                else if (f === 'read') emptyMsg = '没有已读通知';
                else if (t !== 'all') emptyMsg = '没有' + typeLabel(t) + '类型的通知';
                container.innerHTML = '<div class="text-center py-20 text-fg-tertiary">' +
                    '<iconify-icon icon="mdi:bell-check-outline" class="text-5xl mb-3"></iconify-icon>' +
                    '<p class="text-sm">' + escapeHtml(emptyMsg) + '</p>' +
                    (AppState.notifications.length > 0 ? '<button class="mt-3 text-xs text-brand hover:text-brand-hover" onclick="setNotificationsFilter(\'all\'); setNotificationsType(\'all\');">清除筛选条件</button>' : '') +
                '</div>';
                return;
            }
            var htmlStr = '';
            items.forEach(function(n) {
                var cls = colorMap[n.color] || colorMap.brand;
                htmlStr += '<div class="bg-white rounded-xl border border-bg-border p-4 hover:shadow-sm transition-shadow cursor-pointer flex items-start gap-3 ' + (n.unread ? 'border-l-4 border-l-brand' : '') + '" onclick="openNotification(\'' + n.id + '\', event)">' +
                    '<div class="w-10 h-10 rounded-full ' + cls + ' flex items-center justify-center flex-shrink-0">' +
                        '<iconify-icon icon="' + escapeHtml(n.icon || 'mdi:bell-outline') + '"></iconify-icon>' +
                    '</div>' +
                    '<div class="flex-1 min-w-0">' +
                        '<div class="flex items-center gap-2 mb-1">' +
                            '<span class="text-sm font-medium text-fg-primary">' + escapeHtml(n.title || '') + '</span>' +
                            (n.unread ? '<span class="text-[10px] px-1.5 py-0.5 rounded-full bg-brand text-white font-medium">未读</span>' : '') +
                        '</div>' +
                        '<p class="text-xs text-fg-secondary mb-1">' + escapeHtml(n.desc || '') + '</p>' +
                        '<p class="text-[11px] text-fg-tertiary">' + escapeHtml(formatTimeAgo(n.timestamp)) + '</p>' +
                    '</div>' +
                '</div>';
            });
            container.innerHTML = htmlStr;
        }
        // 类型中文标签
        function typeLabel(t) {
            return ({ document: '文档', deadline: '截止', case: '案件', member: '会员', system: '系统' })[t] || t;
        }

        function toggleUserMenu(event) {
            if (event) event.stopPropagation();
            var menu = document.getElementById('userMenu');
            if (!menu) return;
            if (menu.classList.contains('hidden')) {
                // 打开: 移除 hidden + 延迟注册外部点击关闭 (避免本次 click 立刻触发关闭)
                menu.classList.remove('hidden');
                setTimeout(function() {
                    setupOutsideClickClose('userMenu', '[onclick*="toggleUserMenu"]');
                }, 0);
            } else {
                // 关闭
                menu.classList.add('hidden');
            }
        }

        function switchToSubscription() {
            var userMenu = document.getElementById('userMenu');
            if (userMenu) userMenu.classList.add('hidden');
            
            switchSidebarTab('work');
            
            document.querySelectorAll('.sidebar-item').forEach(function(item) {
                item.classList.remove('active');
            });

            var target = document.getElementById('view-subscription');
            if (target) {
                document.querySelectorAll('.view-content').forEach(function(v) {
                    v.classList.add('hidden');
                });
                target.classList.remove('hidden');
            } else {
                loadView('subscription', function(html) {
                    document.getElementById('main-content').insertAdjacentHTML('beforeend', html);
                    var newTarget = document.getElementById('view-subscription');
                    if (newTarget) {
                        document.querySelectorAll('.view-content').forEach(function(v) {
                            v.classList.add('hidden');
                        });
                        newTarget.classList.remove('hidden');
                    }
                });
            }
        }


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
                
                // 专业版：¥299/月 → ¥2399/年（省 ¥1199）
                document.getElementById('pro-price').textContent = '¥2,399';
                document.getElementById('pro-period').textContent = '/年';
                document.getElementById('pro-tip').textContent = '年付省 ¥1,189';
                
                // 企业版：¥899/月 → ¥7,199/年
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

        function showPayment(plan) {
            var planNames = {
                'free': '免费版',
                'professional': '专业版',
                'enterprise': '企业版'
            };
            var planDesc = {
                'free': '基础功能体验',
                'professional': '最适合个人律师',
                'enterprise': '适合律所及团队'
            };
            var planPrice = {
                'free': '¥0',
                'professional': AppState.isYearly ? '¥2,399' : '¥299',
                'enterprise': AppState.isYearly ? '¥7,199' : '¥899'
            };
            
            if (plan === 'free') {
                // 免费版直接提示
                alert('免费版无需支付，可直接使用。如需要更多功能，请选择专业版或企业版。');
                return;
            }
            
            var billingText = AppState.isYearly ? '年付' : '月付';
            document.getElementById('payment-plan-name').textContent = planNames[plan] + ' · ' + billingText;
            document.getElementById('payment-plan-desc').textContent = planDesc[plan];
            document.getElementById('payment-amount').textContent = planPrice[plan];
            document.getElementById('payment-subtotal').textContent = planPrice[plan];
            document.getElementById('payment-total').textContent = planPrice[plan];
            document.getElementById('pay-button-amount').textContent = planPrice[plan];
            
            // 切换视图
            document.querySelectorAll('.view-content').forEach(function(v) {
                v.classList.add('hidden');
            });
            document.getElementById('view-payment').classList.remove('hidden');
        }

        function backToSubscription() {
            document.querySelectorAll('.view-content').forEach(function(v) {
                v.classList.add('hidden');
            });
            document.getElementById('view-subscription').classList.remove('hidden');
        }


        function selectPaymentMethod(el, method) {
            AppState.selectedPayment = method;
            document.querySelectorAll('.payment-method').forEach(function(btn) {
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

        function paySuccess() {
            // 获取当前支付信息
            var planEl = document.getElementById('payment-plan-name');
            var amountEl = document.getElementById('payment-total');
            var planName = planEl ? planEl.textContent : '专业版 · 月付';
            var amount = amountEl ? amountEl.textContent : '¥299';
            
            var methodNames = {'alipay': '支付宝', 'wechat': '微信支付', 'unionpay': '银联支付'};
            var methodName = methodNames[AppState.selectedPayment] || '支付宝';
            
            // 填充成功页信息
            document.getElementById('success-plan-info').textContent = planName + ' 已生效';
            document.getElementById('success-plan').textContent = planName;
            document.getElementById('success-amount').textContent = amount;
            document.getElementById('success-payment-method').textContent = methodName;
            
            // 生成订单号和到期时间
            var now = new Date();
            var orderNo = 'LP' + now.getFullYear() + 
                String(now.getMonth()+1).padStart(2,'0') + 
                String(now.getDate()).padStart(2,'0') + '001';
            document.getElementById('success-order-no').textContent = orderNo;
            
            var expiry = new Date(now);
            expiry.setMonth(expiry.getMonth() + 1);
            document.getElementById('success-expiry').textContent = 
                expiry.getFullYear() + '-' + 
                String(expiry.getMonth()+1).padStart(2,'0') + '-' + 
                String(expiry.getDate()).padStart(2,'0');
            
            // 切换视图
            document.querySelectorAll('.view-content').forEach(function(v) {
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

    function toggleProfileEdit() {
        var display = document.getElementById('profile-display');
        var edit = document.getElementById('profile-edit');
        var btn = document.getElementById('edit-profile-btn');
        
        if (display && edit && btn) {
            var isEditing = !edit.classList.contains('hidden');
            if (isEditing) {
                // 当前是编辑模式 → 切回只读
                cancelProfileEdit();
            } else {
                // 当前是只读模式 → 切到编辑
                display.classList.add('hidden');
                edit.classList.remove('hidden');
                // 隐藏右上角按钮
                btn.classList.add('hidden');
            }
        }
    }

    function cancelProfileEdit() {
        var display = document.getElementById('profile-display');
        var edit = document.getElementById('profile-edit');
        var btn = document.getElementById('edit-profile-btn');
        if (display && edit && btn) {
            edit.classList.add('hidden');
            display.classList.remove('hidden');
            // 显示「修改」按钮
            btn.classList.remove('hidden');
            btn.textContent = '修改';
            btn.className = 'px-5 py-2 text-xs font-semibold rounded-lg border border-[#165DFF] text-[#165DFF] hover:bg-[#E8F3FF] transition-colors';
        }
    }

    function saveProfile() {
        var name = document.getElementById('profile-name');
        var phone = document.getElementById('profile-phone');
        var email = document.getElementById('profile-email');
        var firm = document.getElementById('profile-firm');
        var license = document.getElementById('profile-license');
        var bio = document.getElementById('profile-bio');
        
        // 校验必填
        if (!name || !name.value.trim()) {
            alert('请输入姓名');
            if (name) name.focus();
            return;
        }
        if (!phone || !phone.value.trim()) {
            alert('请输入手机号');
            if (phone) phone.focus();
            return;
        }
        
        // 手机号格式校验
        var phoneVal = phone.value.trim();
        if (!/^1\d{10}$/.test(phoneVal) && !/^\d{3,4}\*{4}\d{4}$/.test(phoneVal)) {
            if (!confirm('手机号格式异常，是否仍要保存？')) return;
        }
        
        // 邮箱格式校验
        var emailVal = email ? email.value.trim() : '';
        if (emailVal && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailVal)) {
            if (!confirm('邮箱格式不正确，是否仍要保存？')) return;
        }
        
        // 更新只读区域的显示内容
        var displayGrid = document.querySelector('#profile-display .grid.grid-cols-2');
        if (displayGrid) {
            var displayItems = displayGrid.querySelectorAll('div');
            if (displayItems.length >= 6) {
                // 姓名
                var nameP = displayItems[0].querySelector('p.text-sm');
                if (nameP) nameP.textContent = name.value.trim();
                
                // 手机号
                var phoneP = displayItems[1].querySelector('p.text-sm');
                if (phoneP) phoneP.textContent = phone.value.trim();
                
                // 邮箱
                var emailP = displayItems[2].querySelector('p.text-sm');
                if (emailP) emailP.textContent = email.value.trim() || '未设置';
                
                // 律所
                var firmP = displayItems[3].querySelector('p.text-sm');
                if (firmP) firmP.textContent = firm.value.trim() || '未设置';
                
                // 执业证号
                var licenseP = displayItems[4].querySelector('p.text-sm');
                if (licenseP) licenseP.textContent = license.value.trim() || '未设置';
                
                // 专业领域（从编辑区同步标签到只读区）
                var editTags = document.querySelectorAll('#edit-skill-tags .inline-flex');
                var displayTagsContainer = displayItems[5].querySelector('.flex.flex-wrap');
                if (displayTagsContainer && editTags.length > 0) {
                    displayTagsContainer.innerHTML = '';
                    editTags.forEach(function(tag) {
                        var tagText = tag.textContent.replace('×', '').replace('+ 添加', '').trim();
                        if (tagText) {
                            var span = document.createElement('span');
                            span.className = 'inline-flex px-2.5 py-1 rounded-full bg-[#E8F3FF] text-[#165DFF] text-[10px] font-medium';
                            span.textContent = tagText;
                            displayTagsContainer.appendChild(span);
                        }
                    });
                }
            }
        }
        
        // 更新个人简介
        var displayBio = document.querySelector('#profile-display .border-t p.text-sm');
        if (displayBio && bio) {
            displayBio.textContent = bio.value.trim() || '未填写';
        }
        
        // 更新左侧头像下方的名称
        var avatarName = document.querySelector('#profile-display + .flex-shrink-0 p.text-xs, #profile-display').closest('.flex').querySelector('.flex-shrink-0 p.text-xs');
        // 更靠谱：找父级 flex 容器中的左侧 p
        var profileContainer = document.querySelector('#profile-display')?.closest('.flex');
        if (profileContainer) {
            var nameUnderAvatar = profileContainer.querySelector('.flex-shrink-0 p.text-xs');
            if (nameUnderAvatar) nameUnderAvatar.textContent = name.value.trim();
        }
        
        // 显示保存成功提示
        showSaveSuccess('个人资料已保存成功');
        
        // 切回只读模式
        cancelProfileEdit();
    }

    function showSaveSuccess(msg) {
        var existing = document.getElementById('save-toast');
        if (existing) existing.remove();
        
        var toast = document.createElement('div');
        toast.id = 'save-toast';
        toast.className = 'fixed top-4 right-4 z-[999] bg-green-50 border border-green-200 text-green-700 text-sm px-5 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-slide-in';
        toast.innerHTML = '<iconify-icon icon="mdi:check-circle" class="text-green-600 text-lg"></iconify-icon><span>' + msg + '</span><button onclick="this.parentElement.remove()" class="ml-2 text-green-400 hover:text-green-600"><iconify-icon icon="mdi:close" class="text-sm"></iconify-icon></button>';
        document.body.appendChild(toast);
        
        setTimeout(function() {
            if (toast.parentElement) {
                toast.style.opacity = '0';
                toast.style.transition = 'opacity 0.3s';
                setTimeout(function() { if (toast.parentElement) toast.remove(); }, 300);
            }
        }, 3000);
    }

    function addTagInput(el) {
        var tag = prompt('请输入专业领域名称：');
        if (tag && tag.trim()) {
            var span = document.createElement('span');
            span.className = 'inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#E8F3FF] text-[#165DFF] text-[10px] font-medium';
            span.innerHTML = tag.trim() + ' <button onclick="removeTag(this); autoSaveProfile()" class="hover:text-red-500"><iconify-icon icon="mdi:close" class="text-xs"></iconify-icon></button>';
            el.parentNode.insertBefore(span, el);
        }
    }

    function handleAvatarUpload(event) {
        var file = event.target.files[0];
        if (!file) return;
        
        // 校验文件大小（5MB）
        if (file.size > 5 * 1024 * 1024) {
            showSaveSuccess('头像文件大小不能超过 5MB');
            return;
        }
        
        // 校验文件类型
        var allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            showSaveSuccess('仅支持 JPG、PNG、WebP 格式的图片');
            return;
        }
        
        // 显示上传中状态
        var progress = document.getElementById('avatar-progress-display');
        var success = document.getElementById('avatar-success-display');
        if (progress) progress.classList.remove('hidden');
        if (success) success.classList.add('hidden');
        
        // 模拟上传延迟后显示预览
        setTimeout(function() {
            var reader = new FileReader();
            reader.onload = function(e) {
                var img = document.getElementById('avatar-image-display');
                var icon = document.getElementById('avatar-icon-display');
                var preview = document.getElementById('avatar-preview-display');
                
                if (img && icon && preview) {
                    img.src = e.target.result;
                    img.classList.remove('hidden');
                    icon.style.display = 'none';
                    preview.style.backgroundImage = 'none';
                }
                
                // 显示成功状态
                if (progress) progress.classList.add('hidden');
                if (success) success.classList.remove('hidden');
                
                // 显示保存成功提示
                showSaveSuccess('头像上传成功');
                
                // 3秒后隐藏成功标识
                setTimeout(function() {
                    if (success) success.classList.add('hidden');
                }, 3000);
            };
            reader.readAsDataURL(file);
        }, 800);
    }

    function removeTag(btn) {
        var tag = btn.closest('span');
        if (tag) {
            tag.remove();
        }
    }

    function showAddTagDialog(el) {
        var tag = prompt('请输入专业领域名称：\n（如：知识产权、刑事辩护、婚姻家事等）');
        if (tag && tag.trim()) {
            var span = document.createElement('span');
            span.className = 'inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-[#E8F3FF] text-[#165DFF] text-xs font-medium';
            span.innerHTML = tag.trim() + ' <button onclick="removeTag(this); autoSaveProfile()" class="hover:text-red-500 transition-colors"><iconify-icon icon="mdi:close" class="text-xs"></iconify-icon></button>';
            el.parentNode.insertBefore(span, el);
        }
    }

    function removeCertFile() {
        var preview = document.getElementById('cert-file-preview');
        var upload = document.getElementById('cert-upload');
        if (preview) preview.classList.add('hidden');
        if (upload) upload.value = '';
    }

    function toggle2FA(checkbox) {
        var status = document.getElementById('2fa-status');
        if (checkbox.checked) {
            if (confirm('开启双因素认证将提高账号安全性。\n\n建议使用 Authenticator App（如 Google Authenticator、Microsoft Authenticator）或短信验证码。\n\n是否继续开启？')) {
                status.textContent = '已开启';
                status.className = 'text-[10px] text-green-600 font-medium';
            } else {
                checkbox.checked = false;
            }
        } else {
            if (confirm('关闭双因素认证将降低账号安全等级，确定要关闭吗？')) {
                status.textContent = '未开启';
                status.className = 'text-[10px] text-[#C9CDD4]';
            } else {
                checkbox.checked = true;
            }
        }
    }

    function showDeviceManager() {
        var deviceInfo = 
            '📱 当前登录设备\n' +
            '━━━━━━━━━━━━━━━━━━\n' +
            '1️⃣ Windows PC\n' +
            '   浏览器：Chrome 120.0\n' +
            '   IP：192.168.1.100\n' +
            '   最近活动：现在\n' +
            '   [当前设备]\n\n' +
            '2️⃣ iPhone 15\n' +
            '   系统：iOS 18.0\n' +
            '   IP：192.168.1.101\n' +
            '   最近活动：2 小时前\n' +
            '   [点击移除此设备]';
        alert(deviceInfo);
    }

    function confirmAccountDeletion() {
        var step1 = confirm('⚠️ 确认要注销账号吗？\n\n注销后：\n· 所有案件数据将被永久清除\n· 所有文书和材料将无法恢复\n· 您的会员权益将立即终止\n\n此操作不可撤销！');
        if (step1) {
            var step2 = prompt('请输入「确认注销」以继续操作：');
            if (step2 === '确认注销') {
                alert('您的账号注销申请已提交。\n系统将在 7 天冷静期后执行注销。\n在此期间重新登录可取消注销。');
            } else {
                alert('输入不正确，注销操作已取消。');
            }
        }
    }

    function validateField(el, msg) {
        if (!el.value.trim()) {
            el.classList.add('border-red-400', 'bg-[#FFF0F0]');
            el.classList.remove('border-[#E5E6EB]');
            var errorEl = el.parentNode.querySelector('.field-error');
            if (!errorEl) {
                errorEl = document.createElement('p');
                errorEl.className = 'field-error text-[10px] text-red-400 mt-1';
                errorEl.textContent = msg;
                el.parentNode.appendChild(errorEl);
            }
        } else {
            el.classList.remove('border-red-400', 'bg-[#FFF0F0]');
            el.classList.add('border-[#E5E6EB]');
            var errorEl = el.parentNode.querySelector('.field-error');
            if (errorEl) errorEl.remove();
        }
    }

    function validateEmail(el) {
        var val = el.value.trim();
        if (val && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) {
            el.classList.add('border-[#FAAD14]', 'bg-[#FFF7E6]');
            el.classList.remove('border-[#E5E6EB]');
            var errorEl = el.parentNode.querySelector('.field-error');
            if (!errorEl) {
                errorEl = document.createElement('p');
                errorEl.className = 'field-error text-[10px] text-[#FAAD14] mt-1';
                errorEl.textContent = '邮箱格式不正确';
                el.parentNode.appendChild(errorEl);
            }
        } else {
            el.classList.remove('border-[#FAAD14]', 'bg-[#FFF7E6]');
            el.classList.add('border-[#E5E6EB]');
            var errorEl = el.parentNode.querySelector('.field-error');
            if (errorEl) errorEl.remove();
        }
    }


    function autoSaveProfile() {
        if (AppState.autoSaveTimer) clearTimeout(AppState.autoSaveTimer);

        var saveBtn = document.getElementById('profile-save-btn');
        var saveText = document.getElementById('save-btn-text');
        var saveSpinner = document.getElementById('save-btn-spinner');
        if (saveBtn) {
            saveBtn.classList.remove('bg-[#165DFF]');
            saveBtn.classList.add('bg-[#4080FF]', 'cursor-default', 'opacity-80');
        }
        if (saveText) saveText.textContent = '保存中...';
        if (saveSpinner) saveSpinner.classList.remove('hidden');

        AppState.autoSaveTimer = setTimeout(function() {
            if (saveBtn) {
                saveBtn.classList.remove('bg-[#4080FF]', 'cursor-default', 'opacity-80');
                saveBtn.classList.add('bg-[#165DFF]');
            }
            if (saveText) saveText.textContent = '已保存';
            if (saveSpinner) saveSpinner.classList.add('hidden');

            setTimeout(function() {
                if (saveText && saveText.textContent === '已保存') {
                    saveText.textContent = '保存';
                }
            }, 2000);
        }, 1500);
    }

    function saveNotificationSettings() {
        var toggles = document.querySelectorAll('.notif-toggle');
        var enabled = [];
        var disabled = [];
        toggles.forEach(function(t, i) {
            if (t.checked) enabled.push(i);
            else disabled.push(i);
        });
        showSaveSuccess('通知设置已保存');
    }

    function bindAccount(name) {
        showSaveSuccess('正在跳转至' + name + '授权页面...');
    }

    function unbindAccount(name) {
        if (confirm('确定要解绑' + name + '吗？解绑后可能影响相关功能使用。')) {
            showSaveSuccess(name + '已解绑');
        }
    }
