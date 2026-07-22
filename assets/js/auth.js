/**
 * Auth 模块 - 登录/注册/登出, token 持久化
 * Phase 3 P0 - 后端 auth 端点未到位, 暂走 demo 模式 (API.auth.demo/login)
 * Phase 4 - 添加 refresh_token 自动刷新机制
 *
 * 依赖: API (api.js), AppState (main.js)
 *
 * 当前架构: IIFE + globalThis 双绑定
 * 评估过 ES module 化, ROI 不高 (见 docs/es-module-roi.md), 暂保留 IIFE
 */

(function () {
    'use strict';

    var STORAGE_KEY = 'lexprime.auth';
    var TOKEN_KEY = 'lexprime.token';
    var REFRESH_TOKEN_KEY = 'lexprime.refresh_token';
    var TOKEN_EXPIRE_KEY = 'lexprime.token_expire';

    var _refreshTimer = null;
    var _isRefreshing = false;

    /**
     * 持久化 token 到 localStorage
     */
    function saveSession(token, user, refreshToken, expiresIn) {
        try {
            localStorage.setItem(TOKEN_KEY, token);
            localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
            if (refreshToken) {
                localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
            }
            if (expiresIn) {
                var expireTime = Date.now() + expiresIn * 1000;
                localStorage.setItem(TOKEN_EXPIRE_KEY, String(expireTime));
            }
        } catch (e) {
            console.warn('[Auth] localStorage 写入失败:', e.message);
        }
        if (typeof AppState !== 'undefined') {
            AppState.token = token;
            AppState.user = user;
        }
    }

    /**
     * 清空 session
     */
    function clearSession() {
        try {
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(STORAGE_KEY);
            localStorage.removeItem(REFRESH_TOKEN_KEY);
            localStorage.removeItem(TOKEN_EXPIRE_KEY);
        } catch (e) {}
        if (typeof AppState !== 'undefined') {
            AppState.token = null;
            AppState.user = null;
        }
        if (_refreshTimer) {
            clearInterval(_refreshTimer);
            _refreshTimer = null;
        }
    }

    /**
     * 从 localStorage 恢复 session
     */
    function restore() {
        try {
            var token = localStorage.getItem(TOKEN_KEY);
            var userRaw = localStorage.getItem(STORAGE_KEY);
            if (token && userRaw) {
                var user;
                try {
                    user = JSON.parse(userRaw);
                } catch (e) {
                    localStorage.removeItem(TOKEN_KEY);
                    localStorage.removeItem(STORAGE_KEY);
                    localStorage.removeItem(REFRESH_TOKEN_KEY);
                    localStorage.removeItem(TOKEN_EXPIRE_KEY);
                    return;
                }
                if (typeof AppState !== 'undefined') {
                    AppState.token = token;
                    AppState.user = user;
                }
                return { token: token, user: user };
            }
        } catch (e) {
            console.warn('[Auth] localStorage 读取失败:', e.message);
        }
        return null;
    }

    /**
     * 获取 refresh_token
     */
    function getRefreshToken() {
        try {
            return localStorage.getItem(REFRESH_TOKEN_KEY);
        } catch (e) {
            return null;
        }
    }

    /**
     * 获取 token 过期时间
     */
    function getTokenExpireTime() {
        try {
            var expireStr = localStorage.getItem(TOKEN_EXPIRE_KEY);
            return expireStr ? parseInt(expireStr, 10) : null;
        } catch (e) {
            return null;
        }
    }

    /**
     * 检查 token 是否即将过期（5分钟内）
     */
    function isTokenAboutToExpire() {
        var expireTime = getTokenExpireTime();
        if (!expireTime) return false;
        var now = Date.now();
        var fiveMinutes = 5 * 60 * 1000;
        return expireTime - now < fiveMinutes && expireTime > now;
    }

    /**
     * 检查 token 是否已过期
     */
    function isTokenExpired() {
        var expireTime = getTokenExpireTime();
        if (!expireTime) return true;
        return Date.now() > expireTime;
    }

    /**
     * 使用 refresh_token 刷新 access_token
     */
    async function refreshToken() {
        if (_isRefreshing) return null;
        var refreshToken = getRefreshToken();
        if (!refreshToken) return null;

        _isRefreshing = true;
        try {
            var res = await API.auth.refresh(refreshToken);
            if (res.ok && res.data && res.data.token) {
                saveSession(
                    res.data.token,
                    res.data.user || Auth.currentUser(),
                    res.data.refresh_token,
                    res.data.expires_in
                );
                if (typeof Utils !== 'undefined' && Utils.showToast) {
                    Utils.showToast('登录已自动续期', 'success');
                }
                return res.data.token;
            }
            return null;
        } catch (e) {
            console.error('[Auth] refreshToken 失败:', e);
            return null;
        } finally {
            _isRefreshing = false;
        }
    }

    /**
     * 在 token 过期前 5 分钟自动刷新
     */
    function refreshBeforeExpire() {
        if (!Auth.isLoggedIn()) return;
        if (isTokenAboutToExpire()) {
            refreshToken();
        }
    }

    /**
     * 启动自动刷新定时器（每分钟检查一次）
     */
    function setupAutoRefresh() {
        if (_refreshTimer) {
            clearInterval(_refreshTimer);
        }
        _refreshTimer = setInterval(refreshBeforeExpire, 60000);
        refreshBeforeExpire();
    }

    var Auth = {
        /**
         * 当前 token
         */
        getToken: function () {
            if (typeof AppState !== 'undefined' && AppState.token) {
                return AppState.token;
            }
            try {
                return localStorage.getItem(TOKEN_KEY);
            } catch (e) {
                return null;
            }
        },

        /**
         * 当前用户
         */
        currentUser: function () {
            if (typeof AppState !== 'undefined' && AppState.user) {
                return AppState.user;
            }
            try {
                var raw = localStorage.getItem(STORAGE_KEY);
                if (!raw) return null;
                var u = JSON.parse(raw);
                return u && typeof u === 'object' ? u : null;
            } catch (e) {
                return null;
            }
        },

        /**
         * 是否已登录
         */
        isLoggedIn: function () {
            return !!this.getToken() && !isTokenExpired();
        },

        /**
         * 获取 refresh_token
         */
        getRefreshToken: getRefreshToken,

        /**
         * 检查 token 是否即将过期
         */
        isTokenAboutToExpire: isTokenAboutToExpire,

        /**
         * 检查 token 是否已过期
         */
        isTokenExpired: isTokenExpired,

        /**
         * 手动刷新 token
         */
        refreshToken: refreshToken,

        /**
         * 启动自动刷新定时器
         */
        setupAutoRefresh: setupAutoRefresh,

        /**
         * 登录
         * @returns {Promise<{ok, user, error?}>}
         */
        login: async function (email, password) {
            if (!email || !password) {
                return { ok: false, error: '请输入邮箱和密码' };
            }
            var res = await API.auth.login(email, password);
            if (res.ok && res.data && res.data.token) {
                saveSession(res.data.token, res.data.user, res.data.refresh_token, res.data.expires_in);
                setupAutoRefresh();
                return { ok: true, user: res.data.user };
            }
            return { ok: false, error: (res.data && res.data.detail) || '登录失败' };
        },

        /**
         * 注册
         */
        register: async function (email, password, displayName) {
            if (!email || !password) {
                return { ok: false, error: '请输入邮箱和密码' };
            }
            var res = await API.auth.register(email, password, displayName);
            if (res.ok && res.data && res.data.token) {
                saveSession(res.data.token, res.data.user, res.data.refresh_token, res.data.expires_in);
                setupAutoRefresh();
                return { ok: true, user: res.data.user };
            }
            return { ok: false, error: (res.data && res.data.detail) || '注册失败' };
        },

        /**
         * Demo 模式登录 (跳过邮箱密码, 使用 MVP_USER_ID=u-1)
         */
        demoLogin: async function () {
            var res = await API.auth.demo();
            if (res.ok && res.data && res.data.token) {
                saveSession(res.data.token, res.data.user, res.data.refresh_token, res.data.expires_in);
                setupAutoRefresh();
                return { ok: true, user: res.data.user };
            }
            return { ok: false, error: 'Demo 登录失败' };
        },

        /**
         * 登出
         */
        logout: function () {
            clearSession();
            if (typeof switchView === 'function') {
                switchView('login');
            }
        },

        /**
         * 启动时恢复 session
         */
        restore: restore,

        /**
         * 拦截器: 401 时尝试刷新 token，失败后跳登录
         * (api.js 内已调用)
         */
        onUnauthorized: async function () {
            var refreshToken = getRefreshToken();
            if (refreshToken) {
                var newToken = await refreshToken();
                if (newToken) {
                    return;
                }
            }
            this.logout();
            if (typeof switchView === 'function') {
                switchView('login');
            }
        }
    };

    globalThis.Auth = Auth;

    // 启动时自动恢复并启动自动刷新
    restore();
    setupAutoRefresh();
})();
