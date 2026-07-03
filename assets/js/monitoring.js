/**
 * LexPrime 前端监控模块 - 错误追踪 + 性能监控
 * 2026-07-03
 *
 * 依赖: API (api.js), Auth (auth.js)
 *
 * 功能:
 * 1. 全局错误捕获 (window.onerror, unhandledrejection)
 * 2. 核心 Web 指标收集 (LCP, FID, CLS, FCP, TTFB)
 * 3. API 请求耗时监控
 * 4. 页面加载时间统计
 * 5. 错误和性能数据上报到后端
 */

(function () {
    'use strict';

    var _config = {
        enabled: true,
        reportUrl: '/api/logs',
        batchSize: 10,
        batchInterval: 5000,
        maxQueueSize: 100,
        sendTimeout: 10000
    };

    var _errorQueue = [];
    var _performanceQueue = [];
    var _sendTimer = null;
    var _isSending = false;

    var _pageStartTime = Date.now();
    var _apiRequestTimings = {};
    var _webVitals = {};

    function _getUserInfo() {
        try {
            if (typeof Auth !== 'undefined' && Auth.currentUser) {
                var user = Auth.currentUser();
                if (user) {
                    return {
                        id: user.id || '',
                        email: user.email || '',
                        displayName: user.displayName || ''
                    };
                }
            }
        } catch (ignore) {}
        return { id: '', email: '', displayName: '' };
    }

    function _getBrowserInfo() {
        var navigatorObj = window.navigator || {};
        return {
            userAgent: navigatorObj.userAgent || '',
            language: navigatorObj.language || '',
            platform: navigatorObj.platform || '',
            screenWidth: window.screen ? window.screen.width : 0,
            screenHeight: window.screen ? window.screen.height : 0,
            viewportWidth: window.innerWidth || 0,
            viewportHeight: window.innerHeight || 0
        };
    }

    function _getPageInfo() {
        return {
            url: window.location.href || '',
            path: window.location.pathname || '',
            search: window.location.search || '',
            referrer: document.referrer || ''
        };
    }

    function _sendBatch() {
        if (!_config.enabled || _isSending) return;

        var errorsToSend = _errorQueue.splice(0, _config.batchSize);
        var perfToSend = _performanceQueue.splice(0, _config.batchSize);

        if (errorsToSend.length === 0 && perfToSend.length === 0) return;

        _isSending = true;
        var data = {};
        if (errorsToSend.length > 0) data.errors = errorsToSend;
        if (perfToSend.length > 0) data.performance = perfToSend;

        var xhr = new XMLHttpRequest();
        xhr.open('POST', _config.reportUrl, true);
        xhr.setRequestHeader('Content-Type', 'application/json');

        if (typeof Auth !== 'undefined' && Auth.getToken) {
            var token = Auth.getToken();
            if (token) {
                xhr.setRequestHeader('Authorization', 'Bearer ' + token);
            }
        }

        xhr.timeout = _config.sendTimeout;

        xhr.onload = function () {
            _isSending = false;
        };

        xhr.onerror = function () {
            _errorQueue = errorsToSend.concat(_errorQueue).slice(0, _config.maxQueueSize);
            _performanceQueue = perfToSend.concat(_performanceQueue).slice(0, _config.maxQueueSize);
            _isSending = false;
        };

        xhr.ontimeout = function () {
            _errorQueue = errorsToSend.concat(_errorQueue).slice(0, _config.maxQueueSize);
            _performanceQueue = perfToSend.concat(_performanceQueue).slice(0, _config.maxQueueSize);
            _isSending = false;
        };

        try {
            xhr.send(JSON.stringify(data));
        } catch (ignore) {
            _errorQueue = errorsToSend.concat(_errorQueue).slice(0, _config.maxQueueSize);
            _performanceQueue = perfToSend.concat(_performanceQueue).slice(0, _config.maxQueueSize);
            _isSending = false;
        }
    }

    function _scheduleSend() {
        if (_sendTimer) clearTimeout(_sendTimer);
        _sendTimer = setTimeout(_sendBatch, _config.batchInterval);
    }

    function _addError(errorData) {
        if (!_config.enabled) return;

        var error = {
            timestamp: new Date().toISOString(),
            user: _getUserInfo(),
            browser: _getBrowserInfo(),
            page: _getPageInfo(),
            error: errorData,
            type: 'frontend_error'
        };

        _errorQueue.push(error);
        if (_errorQueue.length >= _config.batchSize) {
            _sendBatch();
        } else {
            _scheduleSend();
        }
    }

    function _addPerformance(perfData) {
        if (!_config.enabled) return;

        var perf = {
            timestamp: new Date().toISOString(),
            user: _getUserInfo(),
            browser: _getBrowserInfo(),
            page: _getPageInfo(),
            performance: perfData,
            type: 'frontend_performance'
        };

        _performanceQueue.push(perf);
        if (_performanceQueue.length >= _config.batchSize) {
            _sendBatch();
        } else {
            _scheduleSend();
        }
    }

    function _handleGlobalError(message, source, lineno, colno, error) {
        var errorData = {
            message: message || '',
            source: source || '',
            line: lineno || 0,
            column: colno || 0,
            stack: error ? error.stack || '' : '',
            name: error ? error.name || '' : 'Error'
        };

        _addError(errorData);
    }

    function _handleUnhandledRejection(event) {
        var reason = event.reason;
        var errorData = {
            message: reason ? reason.message || String(reason) : 'Unhandled Promise rejection',
            source: '',
            line: 0,
            column: 0,
            stack: reason && reason.stack ? reason.stack : '',
            name: reason && reason.name ? reason.name : 'PromiseRejection',
            promiseRejection: true
        };

        _addError(errorData);
    }

    function _initWebVitals() {
        if (!window.PerformanceObserver) return;

        try {
            var lcpObserver = new PerformanceObserver(function (entryList) {
                var entries = entryList.getEntries();
                if (entries.length > 0) {
                    var lcpEntry = entries[entries.length - 1];
                    _webVitals.lcp = {
                        value: lcpEntry.value,
                        startTime: lcpEntry.startTime,
                        url: lcpEntry.url || ''
                    };
                    _addPerformance({
                        metric: 'lcp',
                        value: lcpEntry.value,
                        startTime: lcpEntry.startTime,
                        url: lcpEntry.url || ''
                    });
                }
            });
            lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
        } catch (ignore) {}

        try {
            var fidObserver = new PerformanceObserver(function (entryList) {
                var entries = entryList.getEntries();
                if (entries.length > 0) {
                    var fidEntry = entries[0];
                    _webVitals.fid = {
                        value: fidEntry.processingStart - fidEntry.startTime,
                        startTime: fidEntry.startTime
                    };
                    _addPerformance({
                        metric: 'fid',
                        value: fidEntry.processingStart - fidEntry.startTime,
                        startTime: fidEntry.startTime
                    });
                }
            });
            fidObserver.observe({ type: 'first-input', buffered: true });
        } catch (ignore) {}

        try {
            var clsObserver = new PerformanceObserver(function (entryList) {
                var entries = entryList.getEntries();
                var clsValue = 0;
                entries.forEach(function (entry) {
                    if (!entry.hadRecentInput) {
                        clsValue += entry.value;
                    }
                });
                _webVitals.cls = { value: clsValue };
                _addPerformance({
                    metric: 'cls',
                    value: clsValue
                });
            });
            clsObserver.observe({ type: 'layout-shift', buffered: true });
        } catch (ignore) {}
    }

    function _collectPageLoadMetrics() {
        if (!window.performance || !window.performance.timing) return;

        var timing = window.performance.timing;
        var navigation = window.performance.navigation || {};

        var metrics = {
            metric: 'page_load',
            ttfb: timing.responseStart - timing.navigationStart,
            fcp: timing.domContentLoadedEventStart - timing.navigationStart,
            domReady: timing.domContentLoadedEventEnd - timing.navigationStart,
            loadTime: timing.loadEventEnd - timing.navigationStart,
            dnsLookup: timing.domainLookupEnd - timing.domainLookupStart,
            tcpConnect: timing.connectEnd - timing.connectStart,
            requestTime: timing.responseEnd - timing.requestStart,
            navigationType: navigation.type === 0 ? 'navigate' : navigation.type === 1 ? 'reload' : 'back_forward',
            pageLoadTime: Date.now() - _pageStartTime
        };

        _addPerformance(metrics);
    }

    function _initApiMonitoring() {
        if (typeof API === 'undefined') return;

        var originalRequest = API.request || function () {};

        function _monitoredRequest(url, options) {
            var startTime = Date.now();
            var requestId = 'req_' + startTime + '_' + Math.random().toString(36).substr(2, 9);

            return originalRequest(url, options)
                .then(function (result) {
                    var duration = Date.now() - startTime;
                    _apiRequestTimings[requestId] = {
                        url: url,
                        method: (options && options.method) || 'GET',
                        status: result.status,
                        duration: duration,
                        ok: result.ok
                    };

                    if (duration > 2000) {
                        _addPerformance({
                            metric: 'slow_api',
                            url: url,
                            method: (options && options.method) || 'GET',
                            status: result.status,
                            duration: duration,
                            ok: result.ok
                        });
                    }

                    return result;
                })
                .catch(function (error) {
                    var duration = Date.now() - startTime;
                    _addPerformance({
                        metric: 'api_error',
                        url: url,
                        method: (options && options.method) || 'GET',
                        duration: duration,
                        error: error.message || String(error)
                    });
                    throw error;
                });
        }

        if (typeof apiFetch === 'function') {
            window.apiFetch = _monitoredRequest;
        }
        if (typeof API !== 'undefined' && typeof API.request === 'function') {
            API.request = _monitoredRequest;
        }
    }

    function _onLoad() {
        _collectPageLoadMetrics();

        if (window.performance && window.performance.getEntriesByType) {
            var resourceEntries = window.performance.getEntriesByType('resource');
            if (resourceEntries.length > 0) {
                var slowResources = [];
                resourceEntries.forEach(function (entry) {
                    if (entry.duration > 1000) {
                        slowResources.push({
                            name: entry.name,
                            type: entry.initiatorType,
                            duration: entry.duration,
                            size: entry.transferSize || 0
                        });
                    }
                });
                if (slowResources.length > 0) {
                    _addPerformance({
                        metric: 'slow_resources',
                        resources: slowResources
                    });
                }
            }
        }
    }

    function init() {
        window.addEventListener('error', _handleGlobalError);
        window.addEventListener('unhandledrejection', _handleUnhandledRejection);

        _initWebVitals();

        if (document.readyState === 'complete') {
            _onLoad();
        } else {
            window.addEventListener('load', _onLoad);
        }

        _initApiMonitoring();

        console.warn('[Monitoring] LexPrime 前端监控模块已初始化');
    }

    var Monitoring = {
        init: init,

        captureError: function (error, context) {
            var errorData = {
                message: error.message || String(error),
                source: (context && context.source) || '',
                line: (context && context.line) || 0,
                column: (context && context.column) || 0,
                stack: error.stack || '',
                name: error.name || 'Error',
                context: context || {}
            };
            _addError(errorData);
        },

        capturePerformance: function (metricName, value, details) {
            var perfData = {
                metric: metricName,
                value: value
            };
            if (details) {
                for (var key in details) {
                    if (details.hasOwnProperty(key)) {
                        perfData[key] = details[key];
                    }
                }
            }
            _addPerformance(perfData);
        },

        setConfig: function (config) {
            if (config && typeof config === 'object') {
                for (var key in config) {
                    if (config.hasOwnProperty(key) && _config.hasOwnProperty(key)) {
                        _config[key] = config[key];
                    }
                }
            }
        },

        enable: function () {
            _config.enabled = true;
        },

        disable: function () {
            _config.enabled = false;
        },

        getWebVitals: function () {
            return _webVitals;
        },

        getApiTimings: function () {
            return _apiRequestTimings;
        }
    };

    globalThis.Monitoring = Monitoring;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
