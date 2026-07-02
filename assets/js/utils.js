/**
 * 公共工具函数模块
 * 提供 XSS 防护、防抖、节流等通用工具
 *
 * 暴露: Utils.escapeHtml, Utils.debounce, Utils.throttle
 */
(function () {
    'use strict';

    /**
     * HTML 转义函数，防止 XSS 攻击
     * @param {string} text - 需要转义的文本
     * @returns {string} - 转义后的安全文本
     */
    function escapeHtml(text) {
        if (!text) return '';
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 防抖函数，延迟执行并在多次调用时只执行最后一次
     * @param {Function} fn - 需要防抖的函数
     * @param {number} delay - 延迟时间（毫秒）
     * @returns {Function} - 防抖后的函数
     */
    function debounce(fn, delay) {
        var timer = null;
        return function () {
            var context = this;
            var args = arguments;
            clearTimeout(timer);
            timer = setTimeout(function () {
                fn.apply(context, args);
            }, delay);
        };
    }

    /**
     * 节流函数，限制函数执行频率
     * @param {Function} fn - 需要节流的函数
     * @param {number} interval - 执行间隔（毫秒）
     * @returns {Function} - 节流后的函数
     */
    function throttle(fn, interval) {
        var lastTime = 0;
        return function () {
            var now = Date.now();
            if (now - lastTime >= interval) {
                lastTime = now;
                fn.apply(this, arguments);
            }
        };
    }

    /**
     * 格式化日期
     * @param {Date|string|number} date - 日期对象/字符串/时间戳
     * @param {string} format - 格式模板（如 'YYYY-MM-DD'）
     * @returns {string} - 格式化后的日期字符串
     */
    function formatDate(date, format) {
        if (!date) return '';
        var d = new Date(date);
        if (isNaN(d.getTime())) return '';

        var year = d.getFullYear();
        var month = String(d.getMonth() + 1).padStart(2, '0');
        var day = String(d.getDate()).padStart(2, '0');
        var hours = String(d.getHours()).padStart(2, '0');
        var minutes = String(d.getMinutes()).padStart(2, '0');
        var seconds = String(d.getSeconds()).padStart(2, '0');

        if (!format) format = 'YYYY-MM-DD';

        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes)
            .replace('ss', seconds);
    }

    /**
     * 格式化数字（千分位）
     * @param {number} num - 需要格式化的数字
     * @returns {string} - 格式化后的数字字符串
     */
    function formatNumber(num) {
        if (num === null || num === undefined) return '';
        return String(num).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    /**
     * 深拷贝对象
     * @param {Object} obj - 需要拷贝的对象
     * @returns {Object} - 拷贝后的新对象
     */
    function deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj);
        if (obj instanceof Array)
            return obj.map(function (item) {
                return deepClone(item);
            });

        var cloned = {};
        for (var key in obj) {
            if (obj.hasOwnProperty(key)) {
                cloned[key] = deepClone(obj[key]);
            }
        }
        return cloned;
    }

    var _modalRegistry = {};

    /**
     * 统一模态框工具函数
     * @param {Object} options - 模态框配置
     * @param {string} options.id - 模态框唯一ID
     * @param {string} options.title - 标题
     * @param {string} options.content - 内容HTML
     * @param {string} [options.footer] - 底部按钮HTML
     * @param {string} [options.size] - 尺寸 'sm'|'md'(默认)|'lg'|'xl'
     * @param {string} [options.icon] - 标题图标（iconify icon name）
     * @param {Function} [options.onClose] - 关闭回调
     * @param {boolean} [options.escClose=true] - ESC键关闭
     * @returns {Function} - 关闭函数
     */
    function showModal(options) {
        var id = options.id;
        var title = options.title || '';
        var content = options.content || '';
        var footer = options.footer || '';
        var size = options.size || 'md';
        var icon = options.icon || '';
        var onClose = options.onClose || function () {};
        var escClose = options.escClose !== false;

        var sizeClasses = {
            sm: 'max-w-sm',
            md: 'max-w-lg',
            lg: 'max-w-xl',
            xl: 'max-w-2xl'
        };

        var previousFocus = document.activeElement;
        var modal = document.getElementById(id);
        if (!modal) {
            modal = document.createElement('div');
            modal.id = id;
            modal.className = 'fixed inset-0 z-[1000] bg-black/40 flex items-center justify-center p-4 hidden';
            modal.setAttribute('role', 'dialog');
            modal.setAttribute('aria-modal', 'true');
            modal.addEventListener('click', function (e) {
                if (e.target === modal) close();
            });
            document.body.appendChild(modal);
        }

        if (title) {
            modal.setAttribute('aria-labelledby', id + '-title');
        }

        var iconHtml = icon ? '<iconify-icon icon="' + icon + '" class="text-brand text-lg"></iconify-icon>' : '';

        modal.innerHTML =
            '<div class="bg-white rounded-2xl shadow-2xl w-full ' +
            sizeClasses[size] +
            ' overflow-hidden" role="document">' +
            '<div class="flex items-center justify-between px-5 py-4 border-b border-bg-border">' +
            '<h3 id="' +
            id +
            '-title" class="text-base font-semibold text-fg-primary flex items-center gap-2">' +
            iconHtml +
            title +
            '</h3>' +
            '<button class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-bg text-fg-tertiary focus:outline-none focus:ring-2 focus:ring-brand/40" data-modal-close aria-label="关闭">' +
            '<iconify-icon icon="mdi:close" class="text-lg"></iconify-icon>' +
            '</button>' +
            '</div>' +
            '<div class="px-5 py-4 max-h-[70vh] overflow-y-auto">' +
            content +
            '</div>' +
            (footer
                ? '<div class="flex items-center justify-end gap-2 px-5 py-4 bg-bg-subtle border-t border-bg-border">' +
                  footer +
                  '</div>'
                : '') +
            '</div>';

        function trapFocus(e) {
            if (e.key !== 'Tab') return;
            var focusable = modal.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            if (focusable.length === 0) return;
            var first = focusable[0];
            var last = focusable[focusable.length - 1];
            if (e.shiftKey) {
                if (document.activeElement === first) {
                    e.preventDefault();
                    last.focus();
                }
            } else {
                if (document.activeElement === last) {
                    e.preventDefault();
                    first.focus();
                }
            }
        }

        function close() {
            modal.classList.add('hidden');
            if (escClose) {
                document.removeEventListener('keydown', onKeyDown);
            }
            document.removeEventListener('keydown', trapFocus);
            delete _modalRegistry[id];
            if (previousFocus && typeof previousFocus.focus === 'function') {
                try {
                    previousFocus.focus();
                } catch (ignore) {}
            }
            onClose();
        }

        function onKeyDown(e) {
            if (e.key === 'Escape') close();
        }

        var closeBtn = modal.querySelector('[data-modal-close]');
        if (closeBtn) {
            closeBtn.onclick = close;
        }

        modal.classList.remove('hidden');
        if (escClose) {
            document.addEventListener('keydown', onKeyDown);
        }
        document.addEventListener('keydown', trapFocus);

        setTimeout(function () {
            var firstInput = modal.querySelector(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            if (firstInput) firstInput.focus();
        }, 50);

        _modalRegistry[id] = close;

        return close;
    }

    function closeAllModals() {
        for (var id in _modalRegistry) {
            try {
                _modalRegistry[id]();
            } catch (e) {
                console.warn('[closeAllModals] 关闭模态框失败:', id, e);
            }
        }
        _modalRegistry = {};
    }

    var _toastQueue = [];
    var _activeToasts = [];
    var _toastContainers = {};
    var MAX_ACTIVE_TOASTS = 3;

    function _getToastContainer(position) {
        var containerId = 'toast-container-' + position;
        if (_toastContainers[position]) return _toastContainers[position];

        var container = document.getElementById(containerId);
        if (!container) {
            container = document.createElement('div');
            container.id = containerId;
            container.className = 'fixed z-[9999] flex flex-col gap-2 pointer-events-none';

            if (position === 'top-right') {
                container.className += ' top-4 right-4 items-end';
            } else if (position === 'top-center') {
                container.className += ' top-4 left-1/2 -translate-x-1/2 items-center';
            } else if (position === 'bottom-right') {
                container.className += ' bottom-4 right-4 items-end';
            } else {
                container.className += ' top-4 left-1/2 -translate-x-1/2 items-center';
            }

            document.body.appendChild(container);
        }

        _toastContainers[position] = container;
        return container;
    }

    function _processToastQueue() {
        while (_activeToasts.length < MAX_ACTIVE_TOASTS && _toastQueue.length > 0) {
            var options = _toastQueue.shift();
            _showToastInternal(options);
        }
    }

    function _showToastInternal(options) {
        var type = options.type;
        var message = options.message;
        var duration = options.duration;
        var position = options.position;
        var closable = options.closable;
        var progress = options.progress;

        var typeConfig = {
            success: {
                bg: 'bg-green-50',
                border: 'border-green-200',
                text: 'text-green-700',
                icon: 'mdi:check-circle-outline',
                iconColor: 'text-green-500',
                progressColor: 'bg-green-500'
            },
            error: {
                bg: 'bg-red-50',
                border: 'border-red-200',
                text: 'text-red-700',
                icon: 'mdi:alert-circle-outline',
                iconColor: 'text-red-500',
                progressColor: 'bg-red-500'
            },
            info: {
                bg: 'bg-blue-50',
                border: 'border-blue-200',
                text: 'text-blue-700',
                icon: 'mdi:information-outline',
                iconColor: 'text-blue-500',
                progressColor: 'bg-blue-500'
            },
            warning: {
                bg: 'bg-amber-50',
                border: 'border-amber-200',
                text: 'text-amber-700',
                icon: 'mdi:alert-outline',
                iconColor: 'text-amber-500',
                progressColor: 'bg-amber-500'
            }
        };

        var config = typeConfig[type] || typeConfig.info;
        var container = _getToastContainer(position);

        var toast = document.createElement('div');
        toast.className =
            'utils-toast pointer-events-auto ' +
            config.bg +
            ' border ' +
            config.border +
            ' ' +
            config.text +
            ' text-xs px-4 py-3 rounded-lg shadow-xl flex items-start gap-3 transform transition-all duration-300 ease-out opacity-0 w-72 relative overflow-hidden';

        var slideClass = '';
        if (position === 'top-right' || position === 'bottom-right') {
            toast.style.transform = 'translateX(100%)';
            slideClass = 'slide-in-right';
        } else {
            toast.style.transform = 'translateY(-100%)';
            slideClass = 'slide-in-top';
        }

        var contentHtml =
            '<iconify-icon icon="' +
            config.icon +
            '" class="' +
            config.iconColor +
            ' text-base flex-shrink-0 mt-0.5"></iconify-icon>' +
            '<span class="flex-1 leading-relaxed">' +
            escapeHtml(message) +
            '</span>';

        var closeHtml = closable
            ? '<button class="toast-close-btn flex-shrink-0 -mr-1 -mt-1 w-5 h-5 flex items-center justify-center rounded hover:bg-black/5 transition-colors" aria-label="关闭">' +
              '<iconify-icon icon="mdi:close" class="text-sm ' + config.text + '"></iconify-icon>' +
              '</button>'
            : '';

        var progressHtml = progress
            ? '<div class="toast-progress-bar absolute bottom-0 left-0 h-0.5 ' +
              config.progressColor +
              ' transition-all ease-linear" style="width: 100%; transition-duration: ' +
              duration +
              'ms"></div>'
            : '';

        toast.innerHTML = contentHtml + closeHtml + progressHtml;
        container.appendChild(toast);

        var toastId = Date.now() + Math.random();
        toast.setAttribute('data-toast-id', toastId);
        _activeToasts.push({ id: toastId, element: toast, position: position });

        requestAnimationFrame(function () {
            requestAnimationFrame(function () {
                if (position === 'top-right' || position === 'bottom-right') {
                    toast.style.transform = 'translateX(0)';
                    toast.style.opacity = '1';
                } else {
                    toast.style.transform = 'translateY(0)';
                    toast.style.opacity = '1';
                }

                if (progress) {
                    setTimeout(function () {
                        var progressBar = toast.querySelector('.toast-progress-bar');
                        if (progressBar) {
                            progressBar.style.width = '0%';
                        }
                    }, 10);
                }
            });
        });

        function removeToast() {
            if (!toast.parentNode) return;

            if (position === 'top-right' || position === 'bottom-right') {
                toast.style.transform = 'translateX(100%)';
            } else {
                toast.style.transform = 'translateY(-100%)';
            }
            toast.style.opacity = '0';

            setTimeout(function () {
                if (toast.parentNode) {
                    toast.remove();
                }
                _activeToasts = _activeToasts.filter(function (t) {
                    return t.id !== toastId;
                });
                _processToastQueue();
            }, 300);
        }

        var closeBtn = toast.querySelector('.toast-close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', removeToast);
        }

        if (duration > 0) {
            setTimeout(removeToast, duration);
        }
    }

    /**
     * 增强版 Toast 提示
     * @param {string|Object} typeOrOptions - 类型 'success'|'error'|'info'|'warning' 或配置对象
     * @param {string} [message] - 提示内容
     * @param {Object} [options] - 配置选项
     * @param {number} [options.duration=3000] - 显示时长（毫秒），0 表示不自动关闭
     * @param {string} [options.position='top-right'] - 位置: 'top-right' | 'top-center' | 'bottom-right'
     * @param {boolean} [options.closable=true] - 是否显示关闭按钮
     * @param {boolean} [options.progress=true] - 是否显示进度条
     * @returns {Function} - 手动关闭函数
     */
    function showToast(typeOrOptions, message, options) {
        var type = 'info';
        var msg = '';
        var opts = options || {};

        if (typeof typeOrOptions === 'object' && typeOrOptions !== null) {
            type = typeOrOptions.type || 'info';
            msg = typeOrOptions.message || '';
            opts = typeOrOptions;
        } else {
            type = typeOrOptions;
            msg = message || '';
            if (!message) {
                msg = typeOrOptions;
                type = 'info';
            }
        }

        var duration = opts.duration !== undefined ? opts.duration : 3000;
        var position = opts.position || 'top-right';
        var closable = opts.closable !== false;
        var progress = opts.progress !== false && duration > 0;

        var toastOptions = {
            type: type,
            message: msg,
            duration: duration,
            position: position,
            closable: closable,
            progress: progress
        };

        _toastQueue.push(toastOptions);
        _processToastQueue();

        return function () {
            var found = _activeToasts.find(function (t) {
                return t.element.textContent.includes(msg);
            });
            if (found) {
                if (position === 'top-right' || position === 'bottom-right') {
                    found.element.style.transform = 'translateX(100%)';
                } else {
                    found.element.style.transform = 'translateY(-100%)';
                }
                found.element.style.opacity = '0';
                setTimeout(function () {
                    if (found.element.parentNode) found.element.remove();
                    _activeToasts = _activeToasts.filter(function (t) {
                        return t.id !== found.id;
                    });
                    _processToastQueue();
                }, 300);
            }
        };
    }

    /**
     * 设置按钮 loading 状态
     * @param {HTMLElement|string} button - 按钮元素或选择器
     * @param {string} [loadingText] - 加载时显示的文字，默认"加载中..."
     */
    function setButtonLoading(button, loadingText) {
        var btn = typeof button === 'string' ? document.querySelector(button) : button;
        if (!btn || btn.tagName !== 'BUTTON') return;

        if (btn.getAttribute('data-loading') === 'true') return;

        var originalText = btn.textContent;
        var originalHtml = btn.innerHTML;
        btn.setAttribute('data-loading', 'true');
        btn.setAttribute('data-original-html', originalHtml);
        btn.setAttribute('data-original-text', originalText);
        btn.disabled = true;

        var text = loadingText || '加载中...';
        var spinnerHtml =
            '<iconify-icon icon="mdi:loading" class="animate-spin text-sm"></iconify-icon>';

        var originalIcon = btn.querySelector('iconify-icon');
        var originalIconHtml = originalIcon ? originalIcon.outerHTML : '';

        if (originalIcon) {
            btn.innerHTML = btn.innerHTML.replace(originalIcon.outerHTML, spinnerHtml);
            var textNode = btn.querySelector('span, .text');
            if (textNode) {
                textNode.textContent = text;
            } else {
                var lastChild = btn.lastChild;
                if (lastChild && lastChild.nodeType === Node.TEXT_NODE) {
                    lastChild.textContent = ' ' + text;
                } else {
                    btn.innerHTML = spinnerHtml + ' ' + text;
                }
            }
        } else {
            btn.innerHTML = spinnerHtml + ' ' + text;
        }

        btn.style.opacity = '0.7';
        btn.style.cursor = 'not-allowed';
    }

    /**
     * 恢复按钮正常状态
     * @param {HTMLElement|string} button - 按钮元素或选择器
     * @param {string} [originalText] - 恢复后显示的文字，默认恢复原始内容
     */
    function setButtonNormal(button, originalText) {
        var btn = typeof button === 'string' ? document.querySelector(button) : button;
        if (!btn || btn.tagName !== 'BUTTON') return;

        if (btn.getAttribute('data-loading') !== 'true') return;

        var savedHtml = btn.getAttribute('data-original-html');
        var savedText = btn.getAttribute('data-original-text');

        btn.removeAttribute('data-loading');
        btn.removeAttribute('data-original-html');
        btn.removeAttribute('data-original-text');
        btn.disabled = false;
        btn.style.opacity = '';
        btn.style.cursor = '';

        if (originalText !== undefined) {
            if (savedHtml) {
                var tempDiv = document.createElement('div');
                tempDiv.innerHTML = savedHtml;
                var icon = tempDiv.querySelector('iconify-icon');
                if (icon) {
                    btn.innerHTML = icon.outerHTML + ' ' + originalText;
                } else {
                    btn.textContent = originalText;
                }
            } else {
                btn.textContent = originalText;
            }
        } else if (savedHtml) {
            btn.innerHTML = savedHtml;
        }
    }

    /**
     * 统一错误处理
     * @param {Error|string|Object} error - 错误对象、错误消息或错误配置
     * @param {Object} [options] - 配置选项
     * @param {boolean} [options.retry=false] - 是否显示重试按钮
     * @param {Function} [options.onRetry] - 重试回调函数
     * @param {string} [options.position='top-right'] - Toast 位置
     * @returns {Function} - 关闭函数
     */
    function showError(error, options) {
        options = options || {};
        var errorType = 'unknown';
        var errorMessage = '操作失败，请稍后重试';
        var errorDetail = '';

        if (typeof error === 'string') {
            errorMessage = error;
            errorType = 'business';
        } else if (error instanceof Error) {
            errorMessage = error.message || '操作失败';
            errorDetail = error.stack || '';
            if (error.name === 'NetworkError' || error.message.includes('network') || error.message.includes('fetch')) {
                errorType = 'network';
            } else {
                errorType = 'business';
            }
        } else if (error && typeof error === 'object') {
            errorMessage = error.message || error.msg || error.detail || '操作失败';
            errorType = error.type || 'business';

            if (error.code === 'NETWORK_ERROR' || error.status === 0 || error.isNetworkError) {
                errorType = 'network';
            }
        }

        var typeConfig = {
            network: {
                title: '网络连接失败',
                description: errorMessage || '请检查您的网络连接后重试',
                icon: 'mdi:wifi-off',
                iconBg: 'bg-red-50',
                iconColor: 'text-red-500'
            },
            business: {
                title: '操作失败',
                description: errorMessage,
                icon: 'mdi:alert-circle-outline',
                iconBg: 'bg-amber-50',
                iconColor: 'text-amber-500'
            },
            unknown: {
                title: '发生未知错误',
                description: errorMessage || '请稍后重试，如问题持续请联系技术支持',
                icon: 'mdi:help-circle-outline',
                iconBg: 'bg-gray-50',
                iconColor: 'text-gray-500'
            }
        };

        var config = typeConfig[errorType] || typeConfig.unknown;
        var position = options.position || 'top-right';

        if (!options.retry || !options.onRetry) {
            return showToast({
                type: 'error',
                message: config.description,
                position: position,
                duration: 4000,
                closable: true,
                progress: true
            });
        }

        var container = _getToastContainer(position);
        var toast = document.createElement('div');
        toast.className =
            'utils-toast pointer-events-auto bg-white border border-red-100 text-fg-primary text-xs rounded-lg shadow-xl p-4 transform transition-all duration-300 ease-out opacity-0 w-80';

        if (position === 'top-right' || position === 'bottom-right') {
            toast.style.transform = 'translateX(100%)';
        } else {
            toast.style.transform = 'translateY(-100%)';
        }

        toast.innerHTML =
            '<div class="flex items-start gap-3">' +
            '<div class="w-8 h-8 rounded-lg ' +
            config.iconBg +
            ' flex items-center justify-center flex-shrink-0">' +
            '<iconify-icon icon="' +
            config.icon +
            '" class="' +
            config.iconColor +
            ' text-base"></iconify-icon>' +
            '</div>' +
            '<div class="flex-1 min-w-0">' +
            '<p class="text-sm font-semibold text-fg-primary mb-1">' +
            config.title +
            '</p>' +
            '<p class="text-xs text-fg-secondary leading-relaxed">' +
            escapeHtml(config.description) +
            '</p>' +
            '<div class="flex items-center gap-2 mt-3">' +
            '<button class="error-retry-btn px-3 py-1.5 text-xs font-medium text-white bg-brand hover:bg-brand-hover rounded-lg transition-colors flex items-center gap-1">' +
            '<iconify-icon icon="mdi:refresh" class="text-xs"></iconify-icon>重试' +
            '</button>' +
            '<button class="error-close-btn px-3 py-1.5 text-xs font-medium text-fg-secondary bg-bg hover:bg-bg-hover rounded-lg transition-colors">' +
            '知道了' +
            '</button>' +
            '</div>' +
            '</div>' +
            '</div>';

        container.appendChild(toast);

        var toastId = Date.now() + Math.random();
        toast.setAttribute('data-toast-id', toastId);
        _activeToasts.push({ id: toastId, element: toast, position: position });

        requestAnimationFrame(function () {
            requestAnimationFrame(function () {
                if (position === 'top-right' || position === 'bottom-right') {
                    toast.style.transform = 'translateX(0)';
                } else {
                    toast.style.transform = 'translateY(0)';
                }
                toast.style.opacity = '1';
            });
        });

        function removeToast() {
            if (!toast.parentNode) return;
            if (position === 'top-right' || position === 'bottom-right') {
                toast.style.transform = 'translateX(100%)';
            } else {
                toast.style.transform = 'translateY(-100%)';
            }
            toast.style.opacity = '0';
            setTimeout(function () {
                if (toast.parentNode) {
                    toast.remove();
                }
                _activeToasts = _activeToasts.filter(function (t) {
                    return t.id !== toastId;
                });
                _processToastQueue();
            }, 300);
        }

        var retryBtn = toast.querySelector('.error-retry-btn');
        if (retryBtn && options.onRetry) {
            retryBtn.addEventListener('click', function () {
                removeToast();
                try {
                    options.onRetry();
                } catch (e) {
                    console.error('[showError] 重试回调执行失败:', e);
                }
            });
        }

        var closeBtn = toast.querySelector('.error-close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', removeToast);
        }

        return removeToast;
    }

    /**
     * 确认对话框
     * @param {string} message - 确认内容
     * @param {string} [title] - 标题
     * @returns {Promise<boolean>} - 用户是否确认
     */
    function showConfirm(message, title) {
        return new Promise(function (resolve) {
            var modalId = 'confirm-modal-' + Date.now();
            var confirmed = false;

            function close(result) {
                confirmed = result;
                closeFn();
            }

            var footer =
                '<button class="px-4 py-2 text-sm font-medium text-fg-secondary bg-bg hover:bg-bg-hover rounded-lg transition-colors" data-modal-cancel>' +
                '取消' +
                '</button>' +
                '<button class="px-4 py-2 text-sm font-medium text-white bg-brand hover:bg-brand-hover rounded-lg transition-colors" data-modal-confirm>' +
                '确定' +
                '</button>';

            var closeFn = showModal({
                id: modalId,
                title: title || '确认操作',
                content: '<p class="text-sm text-fg-secondary">' + escapeHtml(message) + '</p>',
                footer: footer,
                size: 'sm',
                icon: 'mdi:help-circle-outline',
                onClose: function () {
                    resolve(confirmed);
                },
                escClose: true
            });

            setTimeout(function () {
                var modal = document.getElementById(modalId);
                if (!modal) return;

                var cancelBtn = modal.querySelector('[data-modal-cancel]');
                if (cancelBtn) {
                    cancelBtn.addEventListener('click', function () {
                        close(false);
                    });
                }

                var confirmBtn = modal.querySelector('[data-modal-confirm]');
                if (confirmBtn) {
                    confirmBtn.addEventListener('click', function () {
                        close(true);
                    });
                }
            }, 50);
        });
    }

    /**
     * 输入对话框
     * @param {string} message - 提示内容
     * @param {string} [defaultValue] - 默认值
     * @param {string} [title] - 标题
     * @returns {Promise<string|null>} - 用户输入的值，取消返回 null
     */
    function showPrompt(message, defaultValue, title) {
        return new Promise(function (resolve) {
            var modalId = 'prompt-modal-' + Date.now();
            var result = null;

            function close(val) {
                result = val;
                closeFn();
            }

            var content =
                '<p class="text-sm text-fg-secondary mb-3" style="white-space: pre-wrap;">' +
                escapeHtml(message) +
                '</p>' +
                '<input type="text" class="prompt-input w-full px-3 py-2 border border-bg-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand/40" value="' +
                escapeHtml(defaultValue || '') +
                '">';

            var footer =
                '<button class="px-4 py-2 text-sm font-medium text-fg-secondary bg-bg hover:bg-bg-hover rounded-lg transition-colors" data-modal-cancel>' +
                '取消' +
                '</button>' +
                '<button class="px-4 py-2 text-sm font-medium text-white bg-brand hover:bg-brand-hover rounded-lg transition-colors" data-modal-confirm>' +
                '确定' +
                '</button>';

            var closeFn = showModal({
                id: modalId,
                title: title || '请输入',
                content: content,
                footer: footer,
                size: 'sm',
                icon: 'mdi:form-textbox',
                onClose: function () {
                    resolve(result);
                },
                escClose: true
            });

            setTimeout(function () {
                var modal = document.getElementById(modalId);
                if (!modal) return;

                var input = modal.querySelector('.prompt-input');
                if (input) {
                    input.focus();
                    input.select();
                    input.addEventListener('keydown', function (e) {
                        if (e.key === 'Enter') {
                            close(input.value);
                        }
                    });
                }

                var cancelBtn = modal.querySelector('[data-modal-cancel]');
                if (cancelBtn) {
                    cancelBtn.addEventListener('click', function () {
                        close(null);
                    });
                }

                var confirmBtn = modal.querySelector('[data-modal-confirm]');
                if (confirmBtn) {
                    confirmBtn.addEventListener('click', function () {
                        close(input ? input.value : '');
                    });
                }
            }, 50);
        });
    }

    /**
     * 空状态组件预设配置
     */
    var emptyStatePresets = {
        'empty-list': {
            icon: 'mdi:folder-open-outline',
            title: '暂无数据',
            description: '列表中还没有任何内容，快来添加第一条吧',
            iconClass: 'empty-list'
        },
        'no-result': {
            icon: 'mdi:magnify-scan',
            title: '没有找到结果',
            description: '没有匹配的内容，请尝试其他关键词',
            iconClass: 'no-result'
        },
        'error': {
            icon: 'mdi:alert-circle-outline',
            title: '加载失败',
            description: '抱歉，加载过程中出现了问题，请稍后重试',
            iconClass: 'error'
        },
        'loading': {
            icon: 'mdi:loading',
            title: '加载中',
            description: '正在加载数据，请稍候...',
            iconClass: 'loading'
        }
    };

    /**
     * 创建空状态组件
     * @param {Object} options - 配置选项
     * @param {string} [options.preset] - 预设类型: 'empty-list' | 'no-result' | 'error' | 'loading'
     * @param {string} [options.icon] - 自定义图标 (iconify icon name)
     * @param {string} [options.title] - 标题文本
     * @param {string} [options.description] - 描述文本
     * @param {string} [options.actionText] - 主按钮文本
     * @param {Function} [options.actionHandler] - 主按钮点击回调
     * @param {string} [options.secondaryActionText] - 次按钮文本
     * @param {Function} [options.secondaryActionHandler] - 次按钮点击回调
     * @param {HTMLElement|string} [options.container] - 容器元素或选择器，传入则自动挂载
     * @param {boolean} [options.returnElement=false] - 是否返回 DOM 元素，默认返回 HTML 字符串
     * @returns {string|HTMLElement} - HTML 字符串或 DOM 元素
     */
    function createEmptyState(options) {
        options = options || {};
        var preset = options.preset ? emptyStatePresets[options.preset] : null;
        var icon = options.icon || (preset ? preset.icon : 'mdi:folder-open-outline');
        var title = options.title !== undefined ? options.title : (preset ? preset.title : '暂无数据');
        var description = options.description !== undefined ? options.description : (preset ? preset.description : '');
        var iconClass = preset ? preset.iconClass : '';
        var actionText = options.actionText || '';
        var actionHandler = options.actionHandler || null;
        var secondaryActionText = options.secondaryActionText || '';
        var secondaryActionHandler = options.secondaryActionHandler || null;
        var returnElement = options.returnElement === true;
        var container = options.container || null;

        var actionHtml = '';
        if (actionText || secondaryActionText) {
            actionHtml = '<div class="empty-state-action">';
            if (secondaryActionText) {
                actionHtml += '<button class="px-4 py-2 text-sm font-medium text-fg-secondary bg-bg hover:bg-bg-hover rounded-lg transition-colors" data-empty-secondary>' + escapeHtml(secondaryActionText) + '</button>';
            }
            if (actionText) {
                actionHtml += '<button class="px-4 py-2 text-sm font-medium text-white bg-brand hover:bg-brand-hover rounded-lg transition-colors" data-empty-action>' + escapeHtml(actionText) + '</button>';
            }
            actionHtml += '</div>';
        }

        var html =
            '<div class="empty-state">' +
            '<div class="empty-state-icon ' + iconClass + '">' +
            '<iconify-icon icon="' + icon + '"></iconify-icon>' +
            '</div>' +
            (title ? '<div class="empty-state-title">' + escapeHtml(title) + '</div>' : '') +
            (description ? '<div class="empty-state-description">' + escapeHtml(description) + '</div>' : '') +
            actionHtml +
            '</div>';

        if (returnElement || container) {
            var wrapper = document.createElement('div');
            wrapper.innerHTML = html;
            var el = wrapper.firstElementChild;

            if (actionHandler && el.querySelector('[data-empty-action]')) {
                el.querySelector('[data-empty-action]').addEventListener('click', actionHandler);
            }
            if (secondaryActionHandler && el.querySelector('[data-empty-secondary]')) {
                el.querySelector('[data-empty-secondary]').addEventListener('click', secondaryActionHandler);
            }

            if (container) {
                var containerEl = typeof container === 'string' ? document.querySelector(container) : container;
                if (containerEl) {
                    containerEl.innerHTML = '';
                    containerEl.appendChild(el);
                }
            }

            if (returnElement) {
                return el;
            }
            return html;
        }

        return html;
    }

    /**
     * 创建骨架屏组件
     * @param {string} type - 骨架屏类型: 'list' | 'card' | 'table' | 'text'
     * @param {number} [count=1] - 数量
     * @returns {string} - HTML 字符串
     */
    function createSkeleton(type, count) {
        if (!count || count < 1) count = 1;
        var html = '';

        switch (type) {
        case 'list':
            for (var i = 0; i < count; i++) {
                html +=
                        '<div class="skeleton-list-item">' +
                        '<div class="skeleton skeleton-avatar"></div>' +
                        '<div class="skeleton-content">' +
                        '<div class="skeleton skeleton-line medium"></div>' +
                        '<div class="skeleton skeleton-line short"></div>' +
                        '</div>' +
                        '</div>';
            }
            break;

        case 'card':
            for (var j = 0; j < count; j++) {
                html +=
                        '<div class="skeleton-card">' +
                        '<div class="skeleton skeleton-title"></div>' +
                        '<div class="skeleton skeleton-text"></div>' +
                        '<div class="skeleton skeleton-text"></div>' +
                        '<div class="skeleton skeleton-text"></div>' +
                        '</div>';
            }
            break;

        case 'table':
            html += '<div class="space-y-0">';
            for (var k = 0; k < count; k++) {
                html += '<div class="skeleton skeleton-table-row" style="margin-bottom: 0; border-radius: 0;"></div>';
            }
            html += '</div>';
            break;

        case 'text':
            for (var l = 0; l < count; l++) {
                var widthClass = l === count - 1 ? 'short' : 'medium';
                html += '<div class="skeleton skeleton-line ' + widthClass + '"></div>';
            }
            break;

        default:
            for (var m = 0; m < count; m++) {
                html += '<div class="skeleton skeleton-line"></div>';
            }
        }

        return html;
    }

    /**
     * 全局页面加载状态
     */
    var _pageLoadingEl = null;
    var _pageLoadingTimer = null;

    /**
     * 显示全局加载状态
     * @param {string} [text] - 加载文字
     */
    function showPageLoading(text) {
        if (!_pageLoadingEl) {
            _pageLoadingEl = document.createElement('div');
            _pageLoadingEl.className = 'page-loading';
            _pageLoadingEl.innerHTML =
                '<div class="page-loading-spinner"></div>' +
                '<div class="page-loading-text">加载中...</div>';
            document.body.appendChild(_pageLoadingEl);
        }

        if (text !== undefined) {
            var textEl = _pageLoadingEl.querySelector('.page-loading-text');
            if (textEl) {
                textEl.textContent = text;
            }
        }

        if (_pageLoadingTimer) {
            clearTimeout(_pageLoadingTimer);
            _pageLoadingTimer = null;
        }

        requestAnimationFrame(function () {
            if (_pageLoadingEl) {
                _pageLoadingEl.classList.add('visible');
            }
        });
    }

    /**
     * 隐藏全局加载状态
     */
    function hidePageLoading() {
        if (!_pageLoadingEl) return;

        _pageLoadingEl.classList.remove('visible');

        if (_pageLoadingTimer) {
            clearTimeout(_pageLoadingTimer);
        }
        _pageLoadingTimer = setTimeout(function () {
            if (_pageLoadingEl && !_pageLoadingEl.classList.contains('visible')) {
                if (_pageLoadingEl.parentNode) {
                    _pageLoadingEl.remove();
                }
                _pageLoadingEl = null;
            }
            _pageLoadingTimer = null;
        }, 300);
    }

    // 暴露到全局
    globalThis.Utils = {
        escapeHtml: escapeHtml,
        debounce: debounce,
        throttle: throttle,
        formatDate: formatDate,
        formatNumber: formatNumber,
        deepClone: deepClone,
        showModal: showModal,
        closeAllModals: closeAllModals,
        showToast: showToast,
        showConfirm: showConfirm,
        showPrompt: showPrompt,
        createEmptyState: createEmptyState,
        createSkeleton: createSkeleton,
        showPageLoading: showPageLoading,
        hidePageLoading: hidePageLoading,
        setButtonLoading: setButtonLoading,
        setButtonNormal: setButtonNormal,
        showError: showError
    };

    // 兼容旧版：单独暴露 escapeHtml（供各模块迁移过渡）
    globalThis.escapeHtml = escapeHtml;
})();
