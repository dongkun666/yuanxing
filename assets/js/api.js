/**
 * API 客户端层 - 统一封装 fetch, 自动注入 Bearer token
 * Phase 3 P0 新增: 后端地址配置 + 401 拦截 + 错误统一处理
 * Phase 6 扩展: Marketplace / Contract Review / AI API + Loading 管理 + 增强错误处理
 *
 * 依赖: Auth (auth.js) - token 存储
 *       Utils (utils.js) - showToast / showError (可选)
 */

(function () {
    'use strict';

    // 后端服务地址 (dev 模式)
    const CONFIG = {
        backend: 'http://127.0.0.1:3847', // Rust Actix-web
        aiService: 'http://127.0.0.1:8088', // Python FastAPI
        timeoutMs: 30000, // 30s 超时
        uploadTimeoutMs: 60000, // 上传 60s
        retryCount: 2, // 幂等请求重试次数
        retryDelayMs: 1000 // 重试间隔
    };

    // ============================================================
    // Loading 状态管理
    // ============================================================
    const LoadingManager = {
        _activeRequests: 0,
        _loadingElement: null,

        _ensureElement: function () {
            if (!this._loadingElement) {
                var el = document.getElementById('global-loading');
                if (!el) {
                    el = document.createElement('div');
                    el.id = 'global-loading';
                    el.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;' +
                        'background:rgba(0,0,0,0.3);z-index:9999;display:none;' +
                        'align-items:center;justify-content:center;' +
                        'color:#fff;font-size:14px;';
                    el.innerHTML = '<div style="background:rgba(0,0,0,0.7);padding:16px 24px;' +
                        'border-radius:8px;">加载中...</div>';
                    document.body.appendChild(el);
                }
                this._loadingElement = el;
            }
        },

        show: function () {
            this._activeRequests++;
            if (this._activeRequests === 1) {
                this._ensureElement();
                if (this._loadingElement) {
                    this._loadingElement.style.display = 'flex';
                }
            }
        },

        hide: function () {
            this._activeRequests = Math.max(0, this._activeRequests - 1);
            if (this._activeRequests === 0) {
                this._ensureElement();
                if (this._loadingElement) {
                    this._loadingElement.style.display = 'none';
                }
            }
        },

        getActiveCount: function () {
            return this._activeRequests;
        },

        setButtonLoading: function (btn, loading) {
            if (!btn) return;
            if (loading) {
                btn.dataset.originalText = btn.innerText;
                btn.disabled = true;
                btn.innerText = '加载中...';
                btn.style.opacity = '0.6';
                btn.style.cursor = 'not-allowed';
            } else {
                if (btn.dataset.originalText) {
                    btn.innerText = btn.dataset.originalText;
                }
                btn.disabled = false;
                btn.style.opacity = '';
                btn.style.cursor = '';
            }
        }
    };

    // ============================================================
    // 防抖 / 节流 - 避免重复请求
    // ============================================================
    const RequestDeduplicator = {
        _pending: {},

        _getKey: function (url, options) {
            var method = (options && options.method) || 'GET';
            var body = '';
            if (options && options.body) {
                if (typeof options.body === 'string') {
                    body = options.body;
                } else if (options.body instanceof FormData) {
                    body = 'formdata';
                } else {
                    try {
                        body = JSON.stringify(options.body);
                    } catch (e) {
                        body = '';
                    }
                }
            }
            return method + ':' + url + ':' + body;
        },

        check: function (url, options) {
            var key = this._getKey(url, options);
            if (this._pending[key]) {
                return this._pending[key];
            }
            return null;
        },

        register: function (url, options, promise) {
            var key = this._getKey(url, options);
            this._pending[key] = promise;
            var self = this;
            promise.finally(function () {
                delete self._pending[key];
            });
            return promise;
        }
    };

    // ============================================================
    // 错误处理工具
    // ============================================================
    const ErrorHandler = {
        showError: function (message, error) {
            var msg = message || '请求失败';
            if (error && error.message) {
                msg += ': ' + error.message;
            }
            if (typeof Utils !== 'undefined' && Utils.showError) {
                Utils.showError(msg);
            } else if (typeof Utils !== 'undefined' && Utils.showToast) {
                Utils.showToast(msg, 'error');
            } else if (typeof showToast === 'function') {
                showToast(msg);
            } else {
                console.error('[API Error]', msg, error);
            }
        },

        showToast: function (message, type) {
            type = type || 'info';
            if (typeof Utils !== 'undefined' && Utils.showToast) {
                Utils.showToast(message, type);
            } else if (typeof showToast === 'function') {
                showToast(message);
            } else {
                console.log('[API Toast]', '[' + type + ']', message);
            }
        },

        isNetworkError: function (status) {
            return status === 0;
        },

        isAuthError: function (status) {
            return status === 401;
        },

        isRetryable: function (status, method) {
            var retryableStatuses = [0, 408, 429, 500, 502, 503, 504];
            var idempotentMethods = ['GET', 'HEAD', 'PUT', 'DELETE', 'OPTIONS'];
            return retryableStatuses.indexOf(status) >= 0 &&
                idempotentMethods.indexOf((method || 'GET').toUpperCase()) >= 0;
        }
    };

    // ============================================================
    // 核心 request 函数
    // ============================================================

    /**
     * 发起 HTTP 请求
     * @param {string} url - 完整 URL
     * @param {object} options - { method, body, headers, raw, showLoading, dedupe, retry }
     *   raw=true 时 body 不会被 JSON.stringify
     *   showLoading=true 时显示全局 loading (默认 false)
     *   dedupe=true 时启用去重 (默认 false)
     *   retry=true 时启用重试 (仅幂等请求, 默认 false)
     * @returns {Promise<{ok: bool, status: number, data: any, error: string}>}
     */
    async function request(url, options) {
        options = options || {};
        const method = (options.method || 'GET').toUpperCase();
        const headers = Object.assign({}, options.headers || {});
        const showLoading = options.showLoading === true;
        const enableDedupe = options.dedupe === true;
        const enableRetry = options.retry === true;

        // 去重检查
        if (enableDedupe) {
            var pending = RequestDeduplicator.check(url, options);
            if (pending) {
                return pending;
            }
        }

        // 显示 loading
        if (showLoading) {
            LoadingManager.show();
        }

        var promise = _doRequestWithRetry(url, method, headers, options, enableRetry);

        // 注册去重
        if (enableDedupe) {
            promise = RequestDeduplicator.register(url, options, promise);
        }

        // 隐藏 loading
        promise.finally(function () {
            if (showLoading) {
                LoadingManager.hide();
            }
        });

        return promise;
    }

    async function _doRequestWithRetry(url, method, headers, options, enableRetry) {
        var lastError = null;
        var maxRetries = enableRetry ? CONFIG.retryCount : 0;

        for (var attempt = 0; attempt <= maxRetries; attempt++) {
            if (attempt > 0) {
                await _sleep(CONFIG.retryDelayMs * attempt);
            }

            var result = await _doRequest(url, method, headers, options);

            if (result.ok) {
                return result;
            }

            lastError = result;

            if (!enableRetry || !ErrorHandler.isRetryable(result.status, method)) {
                break;
            }

            if (attempt >= maxRetries) {
                break;
            }
        }

        return lastError;
    }

    async function _doRequest(url, method, headers, options) {
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
        const timeoutMs = options.timeoutMs || CONFIG.timeoutMs;
        const timeoutId = setTimeout(function () {
            controller.abort();
        }, timeoutMs);

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
                ErrorHandler.showToast('登录已过期, 请重新登录', 'error');
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

            // 业务错误统一处理
            if (!res.ok && options.showError !== false) {
                var errMsg = '请求失败';
                if (data && typeof data === 'object') {
                    errMsg = data.detail || data.message || data.error || errMsg;
                }
                ErrorHandler.showError(errMsg, { status: res.status });
            }

            return {
                ok: res.ok,
                status: res.status,
                data: data
            };
        } catch (err) {
            clearTimeout(timeoutId);
            var errorType = err.name === 'AbortError' ? 'timeout' : 'network';
            var errorMsg = err.name === 'AbortError' ? '请求超时' : (err.message || '网络错误');

            if (options.showError !== false) {
                ErrorHandler.showError(errorMsg, err);
            }

            return {
                ok: false,
                status: 0,
                data: null,
                error: errorType,
                message: errorMsg
            };
        }
    }

    function _sleep(ms) {
        return new Promise(function (resolve) {
            setTimeout(resolve, ms);
        });
    }

    // ============================================================
    // HTTP 方法封装
    // ============================================================

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
    async function upload(service, path, formData, opts) {
        opts = opts || {};
        const url = CONFIG[service] + path;
        const headers = {};

        if (typeof Auth !== 'undefined' && Auth.getToken) {
            const token = Auth.getToken();
            if (token) headers['Authorization'] = 'Bearer ' + token;
        }

        if (opts.showLoading) {
            LoadingManager.show();
        }

        const controller = new AbortController();
        const timeoutId = setTimeout(function () {
            controller.abort();
        }, opts.timeoutMs || CONFIG.uploadTimeoutMs);

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
                ErrorHandler.showToast('登录已过期, 请重新登录', 'error');
                if (typeof switchView === 'function') {
                    switchView('login');
                }
                return { ok: false, status: 401, data: null, error: 'unauthorized' };
            }

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

            if (!res.ok && opts.showError !== false) {
                var errMsg = '上传失败';
                if (data && typeof data === 'object') {
                    errMsg = data.detail || data.message || data.error || errMsg;
                }
                ErrorHandler.showError(errMsg, { status: res.status });
            }

            return { ok: res.ok, status: res.status, data: data };
        } catch (err) {
            clearTimeout(timeoutId);
            var errorMsg = err.name === 'AbortError' ? '上传超时' : (err.message || '网络错误');

            if (opts.showError !== false) {
                ErrorHandler.showError(errorMsg, err);
            }

            return {
                ok: false,
                status: 0,
                data: null,
                error: err.name === 'AbortError' ? 'timeout' : 'network',
                message: errorMsg
            };
        } finally {
            if (opts.showLoading) {
                LoadingManager.hide();
            }
        }
    }

    /**
     * 构建查询字符串
     */
    function buildQueryString(params) {
        if (!params) return '';
        var parts = [];
        for (var key in params) {
            if (params.hasOwnProperty(key) && params[key] !== undefined && params[key] !== null) {
                parts.push(encodeURIComponent(key) + '=' + encodeURIComponent(params[key]));
            }
        }
        return parts.length > 0 ? '?' + parts.join('&') : '';
    }

    // ============================================================
    // API 端点封装 (按业务域)
    // ============================================================

    const API = {
        config: CONFIG,
        loading: LoadingManager,
        errorHandler: ErrorHandler,

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
            list: function (params) {
                var qs = buildQueryString(params);
                return get('/api/v1/cases' + qs);
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
            extract: function (file, opts) {
                opts = opts || {};
                var fd = new FormData();
                fd.append('file', file);
                return upload('aiService', '/api/ocr', fd, opts);
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
                        raw_text: rawText.slice(0, 8000),
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
        },

        // ===== 搜索 (Python ai-service) =====
        search: {
            /**
             * 全文搜索
             * @param {object} params - { query, index, page, size, filters }
             */
            search: function (params, opts) {
                opts = opts || {};
                return post('/api/search', params, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 搜索案件
             */
            cases: function (query, params, opts) {
                params = params || {};
                return this.search(
                    Object.assign({ query: query, index: 'cases' }, params),
                    opts
                );
            },

            /**
             * 搜索法规
             */
            laws: function (query, params, opts) {
                params = params || {};
                return this.search(
                    Object.assign({ query: query, index: 'laws' }, params),
                    opts
                );
            },

            /**
             * 搜索企业
             */
            companies: function (query, params, opts) {
                params = params || {};
                return this.search(
                    Object.assign({ query: query, index: 'companies' }, params),
                    opts
                );
            }
        },

        // ===== 法规 (Python ai-service) =====
        laws: {
            /**
             * 获取法规列表
             * @param {object} params - { law_type, status, limit }
             */
            list: function (params, opts) {
                opts = opts || {};
                var qs = buildQueryString(params);
                return get('/api/laws' + qs, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 获取法规详情
             */
            get: function (lawId, opts) {
                opts = opts || {};
                return get('/api/laws/' + lawId, Object.assign({ service: 'aiService' }, opts));
            }
        },

        // ===== 企业 (Python ai-service) =====
        companies: {
            /**
             * 获取企业列表
             * @param {object} params - { name, is_zxgk, region, limit }
             */
            list: function (params, opts) {
                opts = opts || {};
                var qs = buildQueryString(params);
                return get('/api/companies' + qs, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 获取企业详情
             */
            get: function (unifiedId, opts) {
                opts = opts || {};
                return get('/api/companies/' + unifiedId, Object.assign({ service: 'aiService' }, opts));
            }
        },

        // ===== 判例 (Python ai-service) =====
        caseLaw: {
            /**
             * 获取判例列表
             * @param {object} params - { cause, cause_category, year, court, limit, offset, full }
             */
            list: function (params, opts) {
                opts = opts || {};
                var qs = buildQueryString(params);
                return get('/api/cases' + qs, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 获取判例详情
             */
            get: function (docId, opts) {
                opts = opts || {};
                return get('/api/cases/' + docId, Object.assign({ service: 'aiService' }, opts));
            }
        },

        // ===== Marketplace (Python ai-service) =====
        marketplace: {
            /**
             * 获取律师列表 (支持分页、过滤、排序)
             * @param {object} params - 过滤参数
             * @param {object} opts - 请求选项
             */
            getLawyers: function (params, opts) {
                opts = opts || {};
                params = params || {};
                var qs = buildQueryString(params);
                return get('/api/marketplace/lawyers' + qs, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 创建律师画像
             * @param {object} lawyerData - 律师画像数据
             * @param {object} opts - 请求选项
             */
            createLawyer: function (lawyerData, opts) {
                opts = opts || {};
                return post('/api/marketplace/lawyers', lawyerData, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 获取律师详情
             * @param {string} lawyerId - 律师 ID
             * @param {object} params - { required_specialty, top_k }
             * @param {object} opts - 请求选项
             */
            getLawyerDetail: function (lawyerId, params, opts) {
                opts = opts || {};
                params = params || {};
                var qs = buildQueryString(params);
                return get('/api/marketplace/lawyers/' + lawyerId + qs, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 律师匹配 (推荐律师列表) - POST 接口 (匹配 2.0)
             * @param {object} criteria - 匹配标准 { required_specialties, region, city, sort_by, filters, page, page_size }
             * @param {object} opts - 请求选项
             */
            matchLawyers: function (criteria, opts) {
                opts = opts || {};
                criteria = criteria || {};
                return post('/api/marketplace/match', criteria, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 匹配解释 - POST 接口 (匹配 2.0)
             * @param {string} lawyerId - 律师 ID
             * @param {object} criteria - 匹配标准 { required_specialties, region, city, ... }
             * @param {object} opts - 请求选项
             */
            getMatchExplanation: function (lawyerId, criteria, opts) {
                opts = opts || {};
                criteria = criteria || {};
                var body = Object.assign({ lawyer_id: lawyerId }, criteria);
                return post('/api/marketplace/match-explain', body, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 律师列表 - POST 接口 (支持排序、过滤、分页)
             * @param {object} params - 过滤和排序参数
             * @param {object} opts - 请求选项
             */
            listLawyers: function (params, opts) {
                opts = opts || {};
                params = params || {};
                return post('/api/marketplace/lawyers/list', params, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 获取 marketplace 统计数据
             * @param {object} params - { period_days }
             * @param {object} opts - 请求选项
             */
            getMetrics: function (params, opts) {
                opts = opts || {};
                params = params || {};
                var qs = buildQueryString(params);
                return get('/api/marketplace/metrics' + qs, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 创建协同办案案件
             * @param {object} caseData - 案件数据
             * @param {object} opts - 请求选项
             */
            createCoCounselCase: function (caseData, opts) {
                opts = opts || {};
                return post('/api/marketplace/cases', caseData, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 获取协同办案案件详情
             * @param {string} caseId - 案件 ID
             * @param {object} opts - 请求选项
             */
            getCoCounselCase: function (caseId, opts) {
                opts = opts || {};
                return get('/api/marketplace/cases/' + caseId, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 创建转介绍
             * @param {object} referralData - 转介绍数据
             * @param {object} opts - 请求选项
             */
            createReferral: function (referralData, opts) {
                opts = opts || {};
                return post('/api/marketplace/referrals', referralData, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 创建跨境文件订单
             * @param {object} jobData - 订单数据
             * @param {object} opts - 请求选项
             */
            createCrossBorderJob: function (jobData, opts) {
                opts = opts || {};
                return post('/api/marketplace/cross-border', jobData, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * Marketplace 健康检查
             */
            health: function (opts) {
                opts = opts || {};
                return get('/api/marketplace/health', Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 获取免责声明
             */
            getDisclaimer: function (opts) {
                opts = opts || {};
                return get('/api/marketplace/disclaimer', Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 获取 manifest
             */
            getManifest: function (opts) {
                opts = opts || {};
                return get('/api/marketplace/manifest', Object.assign({ service: 'aiService' }, opts));
            }
        },

        // ===== Contract Review (Python ai-service) =====
        contractReview: {
            /**
             * 上传合同 (文本方式)
             * @param {object} data - { contract_type, contract_text, fixture_id, stance, ... }
             * @param {object} opts - 请求选项
             */
            uploadContract: function (data, opts) {
                opts = opts || {};
                return post('/api/contract-review/upload', data, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 上传合同文件 (OCR 方式)
             * @param {File} file - 合同文件
             * @param {object} params - { contract_type, stance, industry, ... }
             * @param {object} opts - 请求选项
             */
            uploadContractFile: function (file, params, opts) {
                opts = opts || {};
                params = params || {};
                var fd = new FormData();
                fd.append('file', file);
                if (params.contract_type) fd.append('contract_type', params.contract_type);
                if (params.stance) fd.append('stance', params.stance);
                if (params.industry) fd.append('industry', params.industry);
                if (params.jurisdiction) fd.append('jurisdiction', params.jurisdiction);
                if (params.amount !== undefined && params.amount !== null) fd.append('amount', params.amount);
                if (params.focus_areas) fd.append('focus_areas', params.focus_areas);
                if (params.case_id) fd.append('case_id', params.case_id);
                if (params.skip_pii) fd.append('skip_pii', params.skip_pii);
                return upload('aiService', '/api/contract-review/ocr-upload', fd, opts);
            },

            /**
             * 纯文本合同审查
             * @param {string} text - 合同文本
             * @param {string} contractType - 合同类型
             * @param {object} options - 其他选项 { stance, industry, ... }
             * @param {object} opts - 请求选项
             */
            reviewText: function (text, contractType, options, opts) {
                opts = opts || {};
                options = options || {};
                var body = Object.assign({
                    contract_type: contractType,
                    contract_text: text
                }, options);
                return post('/api/contract-review/upload', body, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 获取审查结果
             * @param {string} reviewId - 审查 ID
             * @param {object} opts - 请求选项
             */
            getResult: function (reviewId, opts) {
                opts = opts || {};
                return get('/api/contract-review/result/' + reviewId, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 获取谈判策略
             * @param {object} data - { review_id, stance, additional_priorities }
             * @param {object} opts - 请求选项
             */
            getNegotiationStrategy: function (data, opts) {
                opts = opts || {};
                return post('/api/contract-review/negotiation', data, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 导出报告
             * @param {string} reviewId - 审查 ID
             * @param {string} format - 导出格式 (markdown/html/word/pdf)
             * @param {object} options - 其他选项
             * @param {object} opts - 请求选项
             */
            exportReport: function (reviewId, format, options, opts) {
                opts = opts || {};
                options = options || {};
                var body = Object.assign({
                    review_id: reviewId,
                    format: format || 'markdown'
                }, options);
                return post('/api/contract-review/export', body, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 获取 demo fixtures 列表
             */
            getFixtures: function (opts) {
                opts = opts || {};
                return get('/api/contract-review/fixtures', Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * Contract Review 健康检查
             */
            health: function (opts) {
                opts = opts || {};
                return get('/api/contract-review/health', Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * OCR 健康检查
             */
            ocrHealth: function (opts) {
                opts = opts || {};
                return get('/api/contract-review/ocr-health', Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 获取免责声明
             */
            getDisclaimer: function (opts) {
                opts = opts || {};
                return get('/api/contract-review/disclaimer', Object.assign({ service: 'aiService' }, opts));
            }
        },

        // ===== AI 服务统一 API (Phase 6 · 2026-07-03) =====
        ai: {
            /**
             * AI 对话
             * @param {string} message - 用户消息
             * @param {object} opts - { conversationId, history, stream }
             */
            chat: function (message, opts) {
                opts = opts || {};
                var body = {
                    message: message,
                    conversation_id: opts.conversationId || null,
                    history: opts.history || null,
                    stream: opts.stream || false
                };
                return post('/api/ai/chat', body, { service: 'aiService' });
            },

            /**
             * 案件摘要
             * @param {object} caseData - 案件信息
             *   { caseName, caseNumber, caseType, parties, plaintiff, defendant,
             *     amount, court, cause, claims, facts, evidence, signDate }
             */
            caseSummary: function (caseData) {
                var data = caseData || {};
                var body = {
                    case_name: data.caseName || data.case_name || '',
                    case_number: data.caseNumber || data.case_number || '',
                    case_type: data.caseType || data.case_type || '',
                    parties: data.parties || '',
                    plaintiff: data.plaintiff || '',
                    defendant: data.defendant || '',
                    amount: data.amount || '',
                    court: data.court || '',
                    cause: data.cause || '',
                    claims: data.claims || '',
                    facts: data.facts || '',
                    evidence: data.evidence || '',
                    sign_date: data.signDate || data.sign_date || ''
                };
                return post('/api/ai/case-summary', body, { service: 'aiService' });
            },

            /**
             * 文书润色
             * @param {string} content - 原文内容
             * @param {object} options - 润色选项
             *   { legalTerms, logic, typos, format, tone }
             */
            polishDocument: function (content, options) {
                var body = {
                    content: content,
                    options: options || {}
                };
                return post('/api/ai/polish', body, { service: 'aiService' });
            },

            /**
             * 智能填空
             * @param {string} templateId - 模板ID
             * @param {object} caseInfo - 案件信息
             */
            autoFill: function (templateId, caseInfo) {
                var body = {
                    template_id: templateId || '',
                    case_info: caseInfo || {}
                };
                return post('/api/ai/auto-fill', body, { service: 'aiService' });
            },

            /**
             * AI 服务健康检查
             */
            health: function () {
                return get('/api/ai/health', { service: 'aiService' });
            },

            /**
             * 获取免责声明
             */
            disclaimer: function () {
                return get('/api/ai/disclaimer', { service: 'aiService' });
            },

            /**
             * 兼容旧接口: 法律问题咨询 (内部走 chat)
             * @deprecated 请使用 chat 方法
             */
            legalQA: function (question, context, opts) {
                return this.chat(question, opts);
            },

            /**
             * 兼容旧接口: 翻译
             * @deprecated 暂保留, 后续迁移
             */
            translate: function (text, targetLang, opts) {
                opts = opts || {};
                var body = {
                    template: 'translate',
                    variables: {
                        text: text,
                        target_language: targetLang || 'en'
                    },
                    temperature: 0.3,
                    max_tokens: 4096
                };
                return post('/v1/generate', body, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 兼容旧接口: autoFillTemplate
             * @deprecated 请使用 autoFill 方法
             */
            autoFillTemplate: function (templateData, caseInfo, opts) {
                return this.autoFill(templateData, caseInfo);
            }
        },

        // ===== 律所 (Python ai-service) =====
        firm: {
            /**
             * 获取律所律师列表
             * @param {string} firmId - 律所 ID
             * @param {object} params - { role }
             * @param {object} opts - 请求选项
             */
            getLawyers: function (firmId, params, opts) {
                opts = opts || {};
                params = params || {};
                params.firm_id = firmId;
                var qs = buildQueryString(params);
                return get('/api/firm/lawyers' + qs, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 创建工时记录
             * @param {string} firmId - 律所 ID
             * @param {object} entryData - 工时数据
             * @param {object} opts - 请求选项
             */
            createTimeEntry: function (firmId, entryData, opts) {
                opts = opts || {};
                entryData = entryData || {};
                var qs = buildQueryString({ firm_id: firmId });
                return post('/api/firm/time-entries' + qs, entryData, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 获取律所统计
             * @param {string} firmId - 律所 ID
             * @param {object} opts - 请求选项
             */
            getStats: function (firmId, opts) {
                opts = opts || {};
                var qs = buildQueryString({ firm_id: firmId });
                return get('/api/firm/stats' + qs, Object.assign({ service: 'aiService' }, opts));
            }
        },

        // ===== Schedule (Python ai-service) =====
        schedule: {
            /**
             * 获取日程列表 (支持 date_from, date_to, type 过滤)
             * @param {object} params - { date_from, date_to, type }
             * @param {object} opts - 请求选项
             */
            list: function (params, opts) {
                opts = opts || {};
                var qs = buildQueryString(params);
                return get('/api/schedule' + qs, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 创建日程
             * @param {object} data - 日程数据
             * @param {object} opts - 请求选项
             */
            create: function (data, opts) {
                opts = opts || {};
                return post('/api/schedule', data, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 更新日程
             * @param {string|number} id - 日程 ID
             * @param {object} data - 更新字段
             * @param {object} opts - 请求选项
             */
            update: function (id, data, opts) {
                opts = opts || {};
                return put('/api/schedule/' + id, data, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 删除日程
             * @param {string|number} id - 日程 ID
             * @param {object} opts - 请求选项
             */
            delete: function (id, opts) {
                opts = opts || {};
                return del('/api/schedule/' + id, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 检查时间冲突 (给定日期+时间, 返回是否有冲突)
             * @param {object} params - { date, time, exclude_id }
             * @param {object} opts - 请求选项
             */
            checkConflict: function (params, opts) {
                opts = opts || {};
                var qs = buildQueryString(params);
                return get('/api/schedule/conflicts' + qs, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 获取今日日程
             * @param {object} opts - 请求选项
             */
            getToday: function (opts) {
                opts = opts || {};
                return get('/api/schedule/today', Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 日程服务健康检查
             * @param {object} opts - 请求选项
             */
            health: function (opts) {
                opts = opts || {};
                return get('/api/schedule/health', Object.assign({ service: 'aiService' }, opts));
            }
        },

        // ===== 客户管理 (Python ai-service · W31) =====
        clients: {
            /**
             * 获取客户列表 (支持 page / page_size / search / client_type / grade / firm_id)
             * @param {object} params - 查询参数
             * @param {object} opts - 请求选项
             */
            list: function (params, opts) {
                opts = opts || {};
                var qs = buildQueryString(params);
                return get('/api/clients' + qs, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 获取客户详情
             * @param {string} clientId - 客户 ID (client_id)
             * @param {object} opts - 请求选项
             */
            get: function (clientId, opts) {
                opts = opts || {};
                return get('/api/clients/' + encodeURIComponent(clientId), Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 创建客户
             * @param {object} data - 客户数据 (name / client_type / id_number / phone / email / address / grade / notes / firm_id)
             * @param {object} opts - 请求选项
             */
            create: function (data, opts) {
                opts = opts || {};
                return post('/api/clients', data, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 更新客户
             * @param {string} clientId - 客户 ID
             * @param {object} data - 更新字段
             * @param {object} opts - 请求选项
             */
            update: function (clientId, data, opts) {
                opts = opts || {};
                return put('/api/clients/' + encodeURIComponent(clientId), data, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 删除客户
             * @param {string} clientId - 客户 ID
             * @param {object} opts - 请求选项
             */
            delete: function (clientId, opts) {
                opts = opts || {};
                return del('/api/clients/' + encodeURIComponent(clientId), Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 利益冲突检查 (基于客户名称匹配其他客户 + 案件当事人)
             * @param {string} clientId - 客户 ID
             * @param {object} opts - 请求选项
             */
            conflictCheck: function (clientId, opts) {
                opts = opts || {};
                return post('/api/clients/' + encodeURIComponent(clientId) + '/conflict-check', {}, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 客户统计 (总数 / 类型分布 / 等级分布)
             * @param {object} params - { firm_id }
             * @param {object} opts - 请求选项
             */
            getStats: function (params, opts) {
                opts = opts || {};
                var qs = buildQueryString(params);
                return get('/api/clients/stats' + qs, Object.assign({ service: 'aiService' }, opts));
            },

            /**
             * 客户管理服务健康检查
             * @param {object} opts - 请求选项
             */
            health: function (opts) {
                opts = opts || {};
                return get('/api/clients/health', Object.assign({ service: 'aiService' }, opts));
            }
        },

        // ===== 工具函数 =====
        utils: {
            /**
             * 构建查询字符串
             */
            buildQueryString: buildQueryString,

            /**
             * 设置按钮 loading 状态
             */
            setButtonLoading: function (btn, loading) {
                LoadingManager.setButtonLoading(btn, loading);
            },

            /**
             * 显示全局 loading
             */
            showLoading: function () {
                LoadingManager.show();
            },

            /**
             * 隐藏全局 loading
             */
            hideLoading: function () {
                LoadingManager.hide();
            },

            /**
             * 获取当前活动请求数
             */
            getActiveRequestCount: function () {
                return LoadingManager.getActiveCount();
            }
        }
    };

    // 暴露到全局
    globalThis.API = API;
    globalThis.apiFetch = request;
})();
