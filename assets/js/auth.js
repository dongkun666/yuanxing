/**
 * Auth 模块 - 登录/注册/登出, token 持久化
 * Phase 3 P0 - 后端 auth 端点未到位, 暂走 demo 模式 (API.auth.demo/login)
 *
 * 依赖: API (api.js), AppState (main.js)
 *
 * 当前架构: IIFE + globalThis 双绑定
 * 评估过 ES module 化, ROI 不高 (见 docs/es-module-roi.md), 暂保留 IIFE
 */

(function() {
    'use strict';

    var STORAGE_KEY = 'lexprime.auth';
    var TOKEN_KEY = 'lexprime.token';

    /**
     * 持久化 token 到 localStorage
     */
    function saveSession(token, user) {
        try {
            localStorage.setItem(TOKEN_KEY, token);
            localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
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
        } catch (e) {}
        if (typeof AppState !== 'undefined') {
            AppState.token = null;
            AppState.user = null;
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
                try { user = JSON.parse(userRaw); } catch (e) {
                    // corrupted storage, clear and force re-login
                    localStorage.removeItem(TOKEN_KEY);
                    localStorage.removeItem(STORAGE_KEY);
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

    var Auth = {
        /**
         * 当前 token
         */
        getToken: function() {
            if (typeof AppState !== 'undefined' && AppState.token) {
                return AppState.token;
            }
            try { return localStorage.getItem(TOKEN_KEY); } catch (e) { return null; }
        },

        /**
         * 当前用户
         */
        currentUser: function() {
            if (typeof AppState !== 'undefined' && AppState.user) {
                return AppState.user;
            }
            try {
                var raw = localStorage.getItem(STORAGE_KEY);
                if (!raw) return null;
                var u = JSON.parse(raw);
                return (u && typeof u === 'object') ? u : null;
            } catch (e) { return null; }
        },

        /**
         * 是否已登录
         */
        isLoggedIn: function() {
            return !!this.getToken();
        },

        /**
         * 登录
         * @returns {Promise<{ok, user, error?}>}
         */
        login: async function(email, password) {
            if (!email || !password) {
                return { ok: false, error: '请输入邮箱和密码' };
            }
            var res = await API.auth.login(email, password);
            if (res.ok && res.data && res.data.token) {
                saveSession(res.data.token, res.data.user);
                return { ok: true, user: res.data.user };
            }
            return { ok: false, error: (res.data && res.data.detail) || '登录失败' };
        },

        /**
         * 注册
         */
        register: async function(email, password, displayName) {
            if (!email || !password) {
                return { ok: false, error: '请输入邮箱和密码' };
            }
            var res = await API.auth.register(email, password, displayName);
            if (res.ok && res.data && res.data.token) {
                saveSession(res.data.token, res.data.user);
                return { ok: true, user: res.data.user };
            }
            return { ok: false, error: (res.data && res.data.detail) || '注册失败' };
        },

        /**
         * Demo 模式登录 (跳过邮箱密码, 使用 MVP_USER_ID=u-1)
         */
        demoLogin: async function() {
            var res = await API.auth.demo();
            if (res.ok && res.data && res.data.token) {
                saveSession(res.data.token, res.data.user);
                return { ok: true, user: res.data.user };
            }
            return { ok: false, error: 'Demo 登录失败' };
        },

        /**
         * 登出
         */
        logout: function() {
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
         * 拦截器: 401 时自动清 session 并跳登录
         * (api.js 内已调用)
         */
        onUnauthorized: function() {
            this.logout();
        },
    };

    globalThis.Auth = Auth;

    // 启动时自动恢复
    restore();
})();