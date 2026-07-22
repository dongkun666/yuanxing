/**
 * Bootstrap 模块 - 应用启动流程
 * 拆分自 script.js (2026-06-28 IIFE 拆分计划)
 *
 * 加载顺序: 最后一个 (在 script.js 之后)
 * 依赖: Auth (auth.js), API (api.js), AppState (app-state.js),
 *       switchView (router.js), renderAppVersion / updateNotificationBadgeState
 *
 * 暴露: bootstrapApp, renderAppVersion, updateNotificationBadgeState,
 *       recordError, initLoginView, registerServiceWorker, checkSWUpdate,
 *       isOnline, showUpdateNotification
 */

(function () {
    'use strict';

    var swRegistration = null;
    var updateAvailable = false;

    /**
     * 应用启动入口: 同步 Auth + 切初始 view + 通知红点
     * 任何 view 想单独初始化可调此函数 (不用重复 Auth.restore 逻辑)
     */
    function bootstrapApp() {
        // Auth.restore() 在 auth.js IIFE 末尾自动跑过, 但当时 AppState 还没定义
        // (auth.js 在 script.js 之前加载), token/user 没同步到 AppState
        // 这里再调一次 restore, 把 localStorage 的 token/user 灌进 AppState
        if (typeof Auth !== 'undefined' && Auth.restore) {
            Auth.restore();
        }

        if (typeof Utils !== 'undefined' && typeof Utils._initThemeSystem === 'function') {
            Utils._initThemeSystem();
        }

        renderAppVersion();
        switchView(getStartView());
        updateNotificationBadgeState();

        if (typeof Utils !== 'undefined' && typeof Utils.initShortcuts === 'function') {
            Utils.initShortcuts();
        }

        registerServiceWorker();
        initOnlineStatus();
    }

    /**
     * 计算初始 view (已登录 → workstation, 否则 → login)
     */
    function getStartView() {
        if (typeof Auth !== 'undefined' && Auth.isLoggedIn && Auth.isLoggedIn()) {
            return 'workstation';
        }
        return 'login';
    }

    /**
     * 应用版本号渲染 - 从 window.APP_VERSION/APP_BUILD/APP_GIT_SHA 读取
     * 未来 build manifest 可覆盖 window.APP_VERSION, 此函数无需改动
     */
    function renderAppVersion() {
        var el = document.getElementById('footer-version');
        if (!el) return;
        var version = typeof window.APP_VERSION === 'string' ? window.APP_VERSION : 'dev';
        var build = window.APP_BUILD || '';
        var sha = window.APP_GIT_SHA || '';
        el.innerHTML = '<iconify-icon class="text-fg-tertiary" icon="mdi:tag-outline"></iconify-icon> ' + version;
        var tipParts = [];
        if (build) tipParts.push('构建 ' + build);
        if (sha) tipParts.push('SHA ' + sha);
        if (tipParts.length) el.title = tipParts.join(' · ');
    }

    /**
     * 启动时同步通知铃铛红点状态 (按 AppState.notifications 真实未读数)
     */
    function updateNotificationBadgeState() {
        var btn = document.getElementById('notificationBellBtn');
        if (!btn || typeof AppState === 'undefined') return;
        // AppState.notifications 来自 account.js 初始化, 首次访问可能为空数组
        var unread = 0;
        if (Array.isArray(AppState.notifications)) {
            unread = AppState.notifications.filter(function (n) {
                return n.unread;
            }).length;
        }
        var badge = btn.querySelector('[data-notif-badge]') || btn.querySelector('.bg-red-500');
        if (unread > 0) {
            if (badge) {
                badge.textContent = unread > 99 ? '99+' : String(unread);
                badge.classList.remove('hidden');
            }
        } else if (badge) {
            badge.classList.add('hidden');
        }
    }

    /**
     * 记录全局错误到 AppState.errorLog (上限 50, 防 localStorage 爆炸)
     */
    function recordError(type, msg, file, line, stack) {
        try {
            if (typeof AppState === 'undefined') return;
            if (!Array.isArray(AppState.errorLog)) AppState.errorLog = [];
            AppState.errorLog.push({
                time: new Date().toISOString(),
                type: type,
                msg: msg,
                file: file || '',
                line: line || 0,
                stack: stack || ''
            });
            if (AppState.errorLog.length > 50) {
                AppState.errorLog.splice(0, AppState.errorLog.length - 50);
            }
            console.error('[' + type + ']', msg, file || '', line || '', stack || '');
        } catch (e) {
            // 记录错误自身失败, 静默吞掉
        }
    }

    // ===== 全局错误处理 =====
    if (typeof window !== 'undefined') {
        window.addEventListener('error', function (e) {
            var stack = e.error && e.error.stack ? e.error.stack : '';
            recordError('GlobalError', e.message || 'unknown', e.filename, e.lineno, stack);
        });
        window.addEventListener('unhandledrejection', function (e) {
            var reason = e.reason;
            var msg = reason && reason.message ? reason.message : String(reason);
            var stack = reason && reason.stack ? reason.stack : '';
            recordError('UnhandledPromise', msg, '', 0, stack);
        });
    }

    // ===== 双绑定 =====
    globalThis.bootstrapApp = bootstrapApp;
    globalThis.renderAppVersion = renderAppVersion;
    globalThis.updateNotificationBadgeState = updateNotificationBadgeState;
    globalThis.recordError = recordError;

    // ===== Login 视图事件绑定 =====
    function initLoginView() {
        var loginForm = document.getElementById('loginForm');
        if (loginForm && !loginForm.dataset.bound) {
            loginForm.dataset.bound = '1';
            loginForm.addEventListener('submit', async function (e) {
                e.preventDefault();
                var email = document.getElementById('loginEmail')?.value;
                var password = document.getElementById('loginPassword')?.value;
                var res = await Auth.login(email, password);
                if (res.ok) {
                    showToast('登录成功');
                    switchView('workstation');
                } else {
                    showToast(res.error || '登录失败');
                }
            });
        }
        var demoBtn = document.getElementById('demoLoginBtn');
        if (demoBtn && !demoBtn.dataset.bound) {
            demoBtn.dataset.bound = '1';
            demoBtn.addEventListener('click', async function () {
                var res = await Auth.demoLogin();
                if (res.ok) {
                    showToast('进入 Demo 模式');
                    switchView('workstation');
                } else {
                    showToast('Demo 模式失败');
                }
            });
        }
    }
    globalThis.initLoginView = initLoginView;

    /**
     * 注册 Service Worker
     */
    function registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', function () {
                navigator.serviceWorker
                    .register('./service-worker.js')
                    .then(function (registration) {
                        swRegistration = registration;
                        checkSWUpdate(registration);

                        registration.addEventListener('updatefound', function () {
                            var newWorker = registration.installing;
                            newWorker.addEventListener('statechange', function () {
                                if (newWorker.state === 'installed') {
                                    if (navigator.serviceWorker.controller) {
                                        updateAvailable = true;
                                        showUpdateNotification();
                                    }
                                }
                            });
                        });
                    })
                    .catch(function (error) {
                        console.warn('Service Worker 注册失败:', error);
                    });
            });
        }
    }

    /**
     * 检查 Service Worker 更新
     */
    function checkSWUpdate(registration) {
        if (registration && registration.waiting) {
            updateAvailable = true;
            showUpdateNotification();
        }
    }

    /**
     * 显示更新通知
     */
    function showUpdateNotification() {
        if (typeof showToast === 'function') {
            showToast('应用已更新，请刷新页面以获取最新版本');
        }
    }

    /**
     * 获取当前在线状态
     */
    function isOnline() {
        return typeof navigator !== 'undefined' && navigator.onLine;
    }

    /**
     * 初始化在线状态监听
     */
    function initOnlineStatus() {
        if (typeof navigator !== 'undefined') {
            window.addEventListener('online', function () {
                if (typeof showToast === 'function') {
                    showToast('网络连接已恢复');
                }
            });

            window.addEventListener('offline', function () {
                if (typeof showToast === 'function') {
                    showToast('网络连接已断开，已切换至离线模式');
                }
            });
        }
    }

    /**
     * 触发 Service Worker 更新
     */
    function triggerSWUpdate() {
        if (swRegistration && swRegistration.waiting) {
            swRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });
            window.location.reload();
        }
    }

    // ===== 双绑定 (Service Worker 相关) =====
    globalThis.registerServiceWorker = registerServiceWorker;
    globalThis.checkSWUpdate = checkSWUpdate;
    globalThis.isOnline = isOnline;
    globalThis.showUpdateNotification = showUpdateNotification;
    globalThis.triggerSWUpdate = triggerSWUpdate;

    // ===== MutationObserver 监听 view-login 出现 =====
    if (document.body) {
        var observer = new MutationObserver(function () {
            if (
                document.getElementById('view-login') &&
                !document.getElementById('view-login').classList.contains('hidden')
            ) {
                initLoginView();
                observer.disconnect();
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    // ===== 启动: 等 DOM ready 后调 bootstrapApp =====
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            bootstrapApp();
        });
    } else {
        bootstrapApp();
    }
})();
