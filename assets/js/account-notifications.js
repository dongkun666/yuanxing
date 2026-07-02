/**
 * 账号 - 通知模块
 * 拆分自 account.js (2026-06-28 IIFE 拆分计划)
 *
 * 包含: 通知面板 (右上角下拉) + 通知全屏页 + 通知 filter/type + 实时时间刷新
 * 依赖: AppState (app-state.js), switchView (router.js), showToast/escapeHtml (script.js)
 *
 * 加载顺序: 在 account-subscription.js / account-profile.js 之前
 *           (因为 subscription.js 的 toggleUserMenu 用 setupOutsideClickClose)
 */

(function () {
    'use strict';

    // ===== 外部点击关闭通用 helper (被 account-subscription.js 共用) =====
    function setupOutsideClickClose(panelId, triggerSelector) {
        var handlerName = 'close' + panelId.charAt(0).toUpperCase() + panelId.slice(1) + 'OnOutside';
        if (!window[handlerName]) {
            window[handlerName] = function (e) {
                var panel = document.getElementById(panelId);
                if (!panel || panel.classList.contains('hidden')) return;
                var trig = triggerSelector
                    ? document.querySelector(triggerSelector)
                    : document.querySelector(
                        '[onclick*="toggle' + panelId.charAt(0).toUpperCase() + panelId.slice(1) + '"]'
                    );
                if (panel.contains(e.target)) return;
                if (trig && trig.contains(e.target)) return;
                panel.classList.add('hidden');
            };
        }
        document.addEventListener('click', window[handlerName]);
    }

    // 通知铃铛 panel toggle
    function toggleNotifications(event) {
        if (event) event.stopPropagation();
        var panel = document.getElementById('notificationPanel');
        panel.classList.toggle('hidden');
        if (!panel.classList.contains('hidden')) {
            renderNotificationsPanel();
            setTimeout(function () {
                setupOutsideClickClose('notificationPanel', '[onclick*="toggleNotifications"]');
            }, 0);
        }
    }

    // 全部标为已读
    function markAllNotifications() {
        AppState.notifications.forEach(function (n) {
            n.unread = false;
        });
        persistNotifications();
        renderNotificationsPanel();
        if (typeof renderNotificationsPage === 'function') renderNotificationsPage();
        updateNotificationBadge();
        showToast('已全部标记为已读');
    }

    // localStorage 持久化
    function persistNotifications() {
        try {
            localStorage.setItem('lexprime_notifications', JSON.stringify(AppState.notifications));
        } catch (e) {
            console.warn('持久化通知失败:', e);
        }
    }

    // 铃铛红点 (未读 > 0 才显示)
    function updateNotificationBadge() {
        var badge = document.querySelector('button[onclick*="toggleNotifications"] .w-2.h-2');
        if (!badge) return;
        var unread = AppState.notifications.filter(function (n) {
            return n.unread;
        }).length;
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
        items.forEach(function (n) {
            var cls = colorMap[n.color] || colorMap.brand;
            htmlStr +=
                '<div class="flex items-start gap-3 p-3 hover:bg-bg-subtle border-b border-bg cursor-pointer" onclick="openNotification(\'' +
                n.id +
                '\', event)">' +
                '<div class="w-8 h-8 rounded-full ' +
                cls +
                ' flex items-center justify-center flex-shrink-0">' +
                '<iconify-icon class="text-sm" icon="' +
                escapeHtml(n.icon || 'mdi:bell-outline') +
                '"></iconify-icon>' +
                '</div>' +
                '<div class="flex-1 min-w-0">' +
                '<p class="text-xs font-medium text-fg-primary">' +
                escapeHtml(n.title || '') +
                '</p>' +
                '<p class="text-[11px] text-fg-tertiary mt-0.5 line-clamp-2">' +
                escapeHtml(n.desc || '') +
                '</p>' +
                '<p class="text-[10px] text-fg-disabled mt-1">' +
                escapeHtml(formatTimeAgo(n.timestamp)) +
                '</p>' +
                '</div>' +
                (n.unread ? '<div class="w-1.5 h-1.5 rounded-full bg-brand flex-shrink-0 mt-1.5"></div>' : '') +
                '</div>';
        });
        listEl.innerHTML = htmlStr;
    }

    // 单条点击: 标记已读 + 跳转
    function openNotification(id, event) {
        if (event) event.stopPropagation();
        var n = AppState.notifications.find(function (x) {
            return x.id === id;
        });
        if (!n) return;
        if (n.unread) {
            n.unread = false;
            persistNotifications();
            renderNotificationsPanel();
            if (typeof renderNotificationsPage === 'function') renderNotificationsPage();
            updateNotificationBadge();
        }
        if (n.linkTo && typeof switchView === 'function') {
            var panel = document.getElementById('notificationPanel');
            if (panel) panel.classList.add('hidden');
            if (n.linkParam) {
                switchView(n.linkTo + (n.linkTo.includes('?') ? '&' : '?') + 'id=' + n.linkParam);
            } else {
                switchView(n.linkTo);
            }
        }
    }

    // 打开「全部通知」全屏页
    function switchToNotifications() {
        var panel = document.getElementById('notificationPanel');
        if (panel) panel.classList.add('hidden');
        if (typeof switchView === 'function') switchView('notifications');
    }

    // filter: 'all' | 'unread' | 'read' (状态维度)
    function setNotificationsFilter(f) {
        if (typeof AppState === 'undefined') return;
        AppState.notificationsFilter = f;
        renderNotificationsPage();
        document.querySelectorAll('.notif-filter-tab').forEach(function (btn) {
            if (btn.dataset.filter === f) {
                btn.className = 'notif-filter-tab text-xs px-3 py-1.5 rounded-full bg-brand text-white font-medium';
            } else {
                btn.className =
                    'notif-filter-tab text-xs px-3 py-1.5 rounded-full bg-bg-subtle text-fg-secondary hover:bg-bg font-medium';
            }
        });
    }

    // type: 'all' | 'document' | 'deadline' | 'case' | 'member' | 'system' (主题维度)
    function setNotificationsType(t) {
        if (typeof AppState === 'undefined') return;
        AppState.notificationsType = t;
        renderNotificationsPage();
        document.querySelectorAll('.notif-type-tab').forEach(function (btn) {
            if (btn.dataset.type === t) {
                var iconHtml = btn.innerHTML.match(/<iconify-icon[^>]*><\/iconify-icon>/);
                var iconStr = iconHtml ? iconHtml[0] + ' ' : '';
                btn.className =
                    'notif-type-tab text-xs px-3 py-1.5 rounded-full bg-brand text-white font-medium flex items-center gap-1';
                btn.innerHTML =
                    iconStr +
                    escapeHtml(
                        btn.dataset.type === 'all'
                            ? '全部类型'
                            : {
                                document: '文档',
                                deadline: '截止',
                                case: '案件',
                                member: '会员',
                                system: '系统'
                            }[btn.dataset.type] || ''
                    );
            } else {
                var iconHtml2 = btn.innerHTML.match(/<iconify-icon[^>]*><\/iconify-icon>/);
                var iconStr2 = iconHtml2 ? iconHtml2[0] + ' ' : '';
                var lbl =
                    btn.dataset.type === 'all'
                        ? '全部类型'
                        : {
                            document: '文档',
                            deadline: '截止',
                            case: '案件',
                            member: '会员',
                            system: '系统'
                        }[btn.dataset.type] || '';
                btn.className =
                    'notif-type-tab text-xs px-3 py-1.5 rounded-full bg-bg-subtle text-fg-secondary hover:bg-bg font-medium flex items-center gap-1';
                btn.innerHTML = iconStr2 + escapeHtml(lbl);
            }
        });
    }

    // 清空通知
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
            setTimeout(function () {
                setupOutsideClickClose('notifMoreMenu', '[onclick*="toggleNotifMoreMenu"]');
            }, 0);
        }
    }

    // 实时时间格式化
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

    // 每分钟重渲染 timeAgo
    var notifRefreshTimer = null;
    function startNotificationTimeRefresh() {
        if (notifRefreshTimer) return;
        notifRefreshTimer = setInterval(function () {
            if (typeof AppState === 'undefined') return;
            renderNotificationsPanel();
            var view = document.getElementById('view-notifications');
            if (view && !view.classList.contains('hidden')) renderNotificationsPage();
        }, 60 * 1000);
    }

    // 渲染全屏通知页
    function renderNotificationsPage() {
        if (typeof AppState === 'undefined') return;
        if (!AppState.notificationsFilter) AppState.notificationsFilter = 'all';
        if (!AppState.notificationsType) AppState.notificationsType = 'all';
        var container = document.getElementById('notifications-list');
        var countEl = document.getElementById('notifications-count');
        if (!container) return;
        var f = AppState.notificationsFilter || 'all';
        var t = AppState.notificationsType || 'all';
        var items = AppState.notifications
            .slice()
            .sort(function (a, b) {
                if (!!a.unread !== !!b.unread) return a.unread ? -1 : 1;
                return (b.timestamp || 0) - (a.timestamp || 0);
            })
            .filter(function (n) {
                if (f === 'unread' && !n.unread) return false;
                if (f === 'read' && n.unread) return false;
                if (t !== 'all' && n.type !== t) return false;
                return true;
            });
        if (countEl) {
            var total = AppState.notifications.length;
            var show = items.length;
            countEl.textContent = total === show ? '共 ' + total + ' 条' : '显示 ' + show + ' / 共 ' + total + ' 条';
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
            container.innerHTML =
                '<div class="text-center py-20 text-fg-tertiary">' +
                '<iconify-icon icon="mdi:bell-check-outline" class="text-5xl mb-3"></iconify-icon>' +
                '<p class="text-sm">' +
                escapeHtml(emptyMsg) +
                '</p>' +
                (AppState.notifications.length > 0
                    ? '<button class="mt-3 text-xs text-brand hover:text-brand-hover" onclick="setNotificationsFilter(\'all\'); setNotificationsType(\'all\');">清除筛选条件</button>'
                    : '') +
                '</div>';
            return;
        }
        var htmlStr = '';
        items.forEach(function (n) {
            var cls = colorMap[n.color] || colorMap.brand;
            htmlStr +=
                '<div class="bg-white rounded-xl border border-bg-border p-4 hover:shadow-sm transition-shadow cursor-pointer flex items-start gap-3 ' +
                (n.unread ? 'border-l-4 border-l-brand' : '') +
                '" onclick="openNotification(\'' +
                n.id +
                '\', event)">' +
                '<div class="w-10 h-10 rounded-full ' +
                cls +
                ' flex items-center justify-center flex-shrink-0">' +
                '<iconify-icon icon="' +
                escapeHtml(n.icon || 'mdi:bell-outline') +
                '"></iconify-icon>' +
                '</div>' +
                '<div class="flex-1 min-w-0">' +
                '<div class="flex items-center gap-2 mb-1">' +
                '<span class="text-sm font-medium text-fg-primary">' +
                escapeHtml(n.title || '') +
                '</span>' +
                (n.unread
                    ? '<span class="text-[10px] px-1.5 py-0.5 rounded-full bg-brand text-white font-medium">未读</span>'
                    : '') +
                '</div>' +
                '<p class="text-xs text-fg-secondary mb-1">' +
                escapeHtml(n.desc || '') +
                '</p>' +
                '<p class="text-[11px] text-fg-tertiary">' +
                escapeHtml(formatTimeAgo(n.timestamp)) +
                '</p>' +
                '</div>' +
                '</div>';
        });
        container.innerHTML = htmlStr;
    }

    // 类型中文标签 (被 setNotificationsType + renderNotificationsPage 引用)
    function typeLabel(t) {
        return { document: '文档', deadline: '截止', case: '案件', member: '会员', system: '系统' }[t] || t;
    }

    // ===== 双绑定 =====
    globalThis.setupOutsideClickClose = setupOutsideClickClose;
    globalThis.toggleNotifications = toggleNotifications;
    globalThis.markAllNotifications = markAllNotifications;
    globalThis.persistNotifications = persistNotifications;
    globalThis.updateNotificationBadge = updateNotificationBadge;
    globalThis.renderNotificationsPanel = renderNotificationsPanel;
    globalThis.openNotification = openNotification;
    globalThis.switchToNotifications = switchToNotifications;
    globalThis.setNotificationsFilter = setNotificationsFilter;
    globalThis.setNotificationsType = setNotificationsType;
    globalThis.clearAllNotifications = clearAllNotifications;
    globalThis.toggleNotifMoreMenu = toggleNotifMoreMenu;
    globalThis.formatTimeAgo = formatTimeAgo;
    globalThis.startNotificationTimeRefresh = startNotificationTimeRefresh;
    globalThis.renderNotificationsPage = renderNotificationsPage;
    globalThis.typeLabel = typeLabel;
})();
