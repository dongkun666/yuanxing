/**
 * API 客户端层 - 统一封装 fetch, 自动注入 Bearer token
 * Phase 3 P0 新增: 后端地址配置 + 401 拦截 + 错误统一处理
 *
 * 依赖: Auth (auth.js) - token 存储
 */

(function () {
    'use strict';

    // 后端服务地址 (dev 模式)
    const CONFIG = {
        backend: 'http://127.0.0.1:3847', // Rust Actix-web
        aiService: 'http://127.0.0.1:8088', // Python FastAPI
        timeoutMs: 30000 // 30s 超时
    };

    /**
     * 发起 HTTP 请求
     * @param {string} url - 完整 URL
     * @param {object} options - { method, body, headers, raw }
     *   raw=true 时 body 不会被 JSON.stringify
     * @returns {Promise<{ok: bool, status: number, data: any}>}
     */
    async function request(url, options) {
        options = options || {};
        const method = options.method || 'GET';
        const headers = Object.assign({}, options.headers || {});

        // 注入 Bearer token
        if (typeof Auth !== 'undefined' && Auth.getToken) {
            const token = Auth.getToken();
            if (token) {
                headers['Authorization'] = 'Bearer ' + token;
            }
        }

        // 默认 JSON body
        let body = options.body;
        if (body && !(body instanceof FormData) && !options.raw) {
            headers['Content-Type'] = headers['Content-Type'] || 'application/json';
            body = JSON.stringify(body);
        }

        // 超时
        const controller = new AbortController();
        const timeoutId = setTimeout(function () {
            controller.abort();
        }, CONFIG.timeoutMs);

        try {
            const res = await fetch(url, {
                method: method,
                headers: headers,
                body: body,
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            // 401: token 失效, 跳登录
            if (res.status === 401 && typeof Auth !== 'undefined') {
                Auth.logout();
                if (typeof showToast === 'function') {
                    showToast('登录已过期, 请重新登录');
                }
                if (typeof switchView === 'function') {
                    switchView('login');
                }
                return { ok: false, status: 401, data: null, error: 'unauthorized' };
            }

            // 解析响应
            let data = null;
            const ct = res.headers.get('content-type') || '';
            if (ct.indexOf('application/json') >= 0) {
                data = await res.json().catch(function () {
                    return null;
                });
            } else {
                data = await res.text().catch(function () {
                    return null;
                });
            }

            return {
                ok: res.ok,
                status: res.status,
                data: data
            };
        } catch (err) {
            clearTimeout(timeoutId);
            return {
                ok: false,
                status: 0,
                data: null,
                error: err.name === 'AbortError' ? 'timeout' : err.message
            };
        }
    }

    /**
     * GET 请求
     */
    function get(path, opts) {
        opts = opts || {};
        return request(CONFIG[opts.service || 'backend'] + path, Object.assign({}, opts, { method: 'GET' }));
    }

    /**
     * POST 请求
     */
    function post(path, body, opts) {
        opts = opts || {};
        return request(
            CONFIG[opts.service || 'backend'] + path,
            Object.assign({}, opts, { method: 'POST', body: body })
        );
    }

    /**
     * PUT 请求
     */
    function put(path, body, opts) {
        opts = opts || {};
        return request(
            CONFIG[opts.service || 'backend'] + path,
            Object.assign({}, opts, { method: 'PUT', body: body })
        );
    }

    /**
     * DELETE 请求
     */
    function del(path, opts) {
        opts = opts || {};
        return request(CONFIG[opts.service || 'backend'] + path, Object.assign({}, opts, { method: 'DELETE' }));
    }

    /**
     * 上传文件 (multipart/form-data)
     */
    async function upload(service, path, formData) {
        const url = CONFIG[service] + path;
        const headers = {};
        if (typeof Auth !== 'undefined' && Auth.getToken) {
            const token = Auth.getToken();
            if (token) headers['Authorization'] = 'Bearer ' + token;
        }
        const controller = new AbortController();
        const timeoutId = setTimeout(function () {
            controller.abort();
        }, 60000); // 上传 60s

        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: headers,
                body: formData,
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            if (res.status === 401 && typeof Auth !== 'undefined') {
                Auth.logout();
                return { ok: false, status: 401, data: null };
            }
            const data = await res.json().catch(function () {
                return null;
            });
            return { ok: res.ok, status: res.status, data: data };
        } catch (err) {
            clearTimeout(timeoutId);
            return { ok: false, status: 0, data: null, error: err.message };
        }
    }

    // ============================================================
    // API 端点封装 (按业务域)
    // ============================================================

    const API = {
        config: CONFIG,

        // ===== 健康检查 =====
        health: {
            backend: function () {
                return get('/health');
            },
            ai: function () {
                return get('/health', { service: 'aiService' });
            }
        },

        // ===== Auth (Phase 3 后端待补, 暂走 demo 模式) =====
        auth: {
            /**
             * 登录 - 暂走 demo (后端 Phase 2 hardcode u-1)
             */
            login: function (email, password) {
                // TODO: 替换为 POST /api/v1/auth/login
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    data: {
                        token: 'demo-token-' + Date.now(),
                        user: {
                            id: 'u-1',
                            email: email || 'demo@lexprime.cn',
                            displayName: email ? email.split('@')[0] : '演示律师'
                        }
                    }
                });
            },
            register: function (email, password, displayName) {
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    data: {
                        token: 'demo-token-' + Date.now(),
                        user: {
                            id: 'u-1',
                            email: email,
                            displayName: displayName || email.split('@')[0]
                        }
                    }
                });
            },
            me: function () {
                return Promise.resolve({ ok: true, status: 200, data: Auth.currentUser() });
            },
            /**
             * Demo 模式登录 (无需邮箱密码)
             */
            demo: function () {
                return this.login('demo@lexprime.cn', '');
            }
        },

        // ===== 案件 (Rust backend) =====
        cases: {
            list: function () {
                return get('/api/v1/cases');
            },
            create: function (body) {
                return post('/api/v1/cases', body);
            },
            get: function (id) {
                return get('/api/v1/cases/' + id);
            }
        },

        // ===== OCR (Python ai-service) =====
        ocr: {
            /**
             * 提取文件文本
             * @param {File} file - 用户上传的文件
             */
            extract: function (file) {
                var fd = new FormData();
                fd.append('file', file);
                return upload('aiService', '/api/ocr', fd);
            }
        },

        // ===== Knowledge / LLM 编译 (Python ai-service) =====
        knowledge: {
            /**
             * LLM 编译原始资料为 Wiki 页
             * @param {string} rawText - OCR 提取的文本
             * @param {object} opts - { source: string, metadata: object }
             */
            compile: function (rawText, opts) {
                opts = opts || {};
                var body = {
                    template: 'knowledge_compile',
                    variables: {
                        raw_text: rawText.slice(0, 8000), // 限制长度
                        source_type: opts.source || 'document',
                        source_meta: opts.metadata || {}
                    },
                    temperature: 0.2,
                    max_tokens: 2048
                };
                return post('/v1/generate', body, { service: 'aiService' });
            },

            /**
             * LLM 巡检 Wiki
             * @param {array} pages - Wiki 页面列表
             */
            lint: function (pages) {
                var body = {
                    template: 'knowledge_lint',
                    variables: {
                        pages: pages.slice(0, 20)
                    },
                    temperature: 0.1,
                    max_tokens: 2048,
                    response_format_json: true
                };
                return post('/v1/generate', body, { service: 'aiService' });
            }
        }
    };

    // 暴露到全局
    globalThis.API = API;
    globalThis.apiFetch = request;
})();
