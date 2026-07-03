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
     * HTML 净化函数，过滤危险标签和属性
     * @param {string} html - 需要净化的 HTML
     * @returns {string} - 净化后的安全 HTML
     */
    function sanitizeHtml(html) {
        if (!html) return '';

        var allowedTags = {
            b: true,
            strong: true,
            i: true,
            em: true,
            u: true,
            s: true,
            del: true,
            sub: true,
            sup: true,
            br: true,
            p: true,
            div: true,
            span: true,
            a: { href: true, target: '_blank', rel: 'noopener noreferrer' },
            img: { src: true, alt: true },
            ul: true,
            ol: true,
            li: true,
            h1: true,
            h2: true,
            h3: true,
            h4: true,
            h5: true,
            h6: true,
            table: true,
            tr: true,
            td: true,
            th: true,
            thead: true,
            tbody: true,
            tfoot: true,
            blockquote: true,
            code: true,
            pre: true,
            hr: true
        };

        var allowedProtocols = ['http:', 'https:', 'data:'];

        var temp = document.createElement('div');
        temp.innerHTML = html;

        function sanitizeNode(node) {
            if (node.nodeType === Node.TEXT_NODE) {
                return;
            }

            if (node.nodeType === Node.ELEMENT_NODE) {
                var tagName = node.tagName.toLowerCase();

                if (!allowedTags[tagName]) {
                    node.parentNode.replaceChild(document.createTextNode(node.textContent), node);
                    return;
                }

                var allowedAttrs = allowedTags[tagName];
                for (var i = node.attributes.length - 1; i >= 0; i--) {
                    var attr = node.attributes[i];
                    var attrName = attr.name.toLowerCase();

                    if (typeof allowedAttrs === 'object') {
                        if (!allowedAttrs[attrName]) {
                            node.removeAttribute(attr.name);
                            continue;
                        }

                        if (attrName === 'href' || attrName === 'src') {
                            var url = attr.value;
                            var protocol = url.split(':')[0] + ':';
                            if (allowedProtocols.indexOf(protocol) === -1 && !url.startsWith('/')) {
                                node.removeAttribute(attr.name);
                            } else if (attrName === 'href') {
                                node.setAttribute('rel', 'noopener noreferrer');
                                node.setAttribute('target', '_blank');
                            }
                        }
                    } else {
                        node.removeAttribute(attr.name);
                    }
                }
            }

            for (var j = node.childNodes.length - 1; j >= 0; j--) {
                sanitizeNode(node.childNodes[j]);
            }
        }

        sanitizeNode(temp);

        return temp.innerHTML;
    }

    /**
     * 防抖函数，延迟执行并在多次调用时只执行最后一次
     * @param {Function} fn - 需要防抖的函数
     * @param {number} wait - 延迟时间（毫秒）
     * @param {boolean} [immediate=false] - 是否立即执行
     * @returns {Function} - 防抖后的函数
     */
    function debounce(fn, wait, immediate) {
        var timer = null;
        return function () {
            var context = this;
            var args = arguments;
            var callNow = immediate && !timer;

            clearTimeout(timer);
            timer = setTimeout(function () {
                timer = null;
                if (!immediate) {
                    fn.apply(context, args);
                }
            }, wait);

            if (callNow) {
                fn.apply(context, args);
            }
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
              '<iconify-icon icon="mdi:close" class="text-sm ' +
              config.text +
              '"></iconify-icon>' +
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
        var spinnerHtml = '<iconify-icon icon="mdi:loading" class="animate-spin text-sm"></iconify-icon>';

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
        error: {
            icon: 'mdi:alert-circle-outline',
            title: '加载失败',
            description: '抱歉，加载过程中出现了问题，请稍后重试',
            iconClass: 'error'
        },
        loading: {
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
        var title = options.title !== undefined ? options.title : preset ? preset.title : '暂无数据';
        var description = options.description !== undefined ? options.description : preset ? preset.description : '';
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
                actionHtml +=
                    '<button class="px-4 py-2 text-sm font-medium text-fg-secondary bg-bg hover:bg-bg-hover rounded-lg transition-colors" data-empty-secondary>' +
                    escapeHtml(secondaryActionText) +
                    '</button>';
            }
            if (actionText) {
                actionHtml +=
                    '<button class="px-4 py-2 text-sm font-medium text-white bg-brand hover:bg-brand-hover rounded-lg transition-colors" data-empty-action>' +
                    escapeHtml(actionText) +
                    '</button>';
            }
            actionHtml += '</div>';
        }

        var html =
            '<div class="empty-state">' +
            '<div class="empty-state-icon ' +
            iconClass +
            '">' +
            '<iconify-icon icon="' +
            icon +
            '"></iconify-icon>' +
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
     * 生成空状态 HTML
     * @param {Object} options - 配置选项
     * @param {string} [options.icon] - 图标 (iconify icon name)
     * @param {string} [options.title] - 标题
     * @param {string} [options.description] - 描述
     * @param {string} [options.actionText] - 操作按钮文本
     * @param {Function} [options.actionHandler] - 操作按钮点击回调
     * @param {string} [options.secondaryActionText] - 次要操作按钮文本
     * @param {Function} [options.secondaryActionHandler] - 次要操作按钮点击回调
     * @param {string} [options.iconColor] - 图标颜色 (如 'success', 'danger', 'warning')
     * @param {string} [options.type='default'] - 类型: 'default' | 'search' | 'data' | 'error' | 'loading'
     * @returns {string} - HTML 字符串
     */
    function renderEmptyState(options) {
        options = options || {};
        var type = options.type || 'default';

        var typeConfig = {
            default: {
                icon: 'mdi:folder-open-outline',
                title: '暂无数据',
                description: '列表中还没有任何内容',
                iconClass: 'empty-list'
            },
            search: {
                icon: 'mdi:magnify-scan',
                title: '没有找到结果',
                description: '没有匹配的内容，请尝试其他关键词',
                iconClass: 'no-result'
            },
            data: {
                icon: 'mdi:database-outline',
                title: '暂无数据',
                description: '数据加载中或暂无内容',
                iconClass: 'empty-list'
            },
            error: {
                icon: 'mdi:alert-circle-outline',
                title: '加载失败',
                description: '抱歉，加载过程中出现了问题，请稍后重试',
                iconClass: 'error'
            },
            loading: {
                icon: 'mdi:loading',
                title: '加载中',
                description: '正在加载数据，请稍候...',
                iconClass: 'loading'
            }
        };

        var config = typeConfig[type] || typeConfig['default'];
        var icon = options.icon || config.icon;
        var title = options.title !== undefined ? options.title : config.title;
        var description = options.description !== undefined ? options.description : config.description;
        var iconClass = config.iconClass;
        var iconColor = options.iconColor || '';
        var actionText = options.actionText || '';
        var actionHandler = options.actionHandler || null;
        var secondaryActionText = options.secondaryActionText || '';
        var secondaryActionHandler = options.secondaryActionHandler || null;

        var iconColorClass = iconColor ? ' text-' + iconColor : '';

        var actionHtml = '';
        if (actionText || secondaryActionText) {
            actionHtml = '<div class="empty-state-action flex items-center gap-2">';
            if (actionText) {
                var handlerAttr = actionHandler ? 'data-empty-action="true"' : '';
                actionHtml +=
                    '<button class="px-4 py-2 text-sm font-medium text-white bg-brand hover:bg-brand-hover rounded-lg transition-colors" ' +
                    handlerAttr +
                    '>' +
                    escapeHtml(actionText) +
                    '</button>';
            }
            if (secondaryActionText) {
                var secondaryHandlerAttr = secondaryActionHandler ? 'data-empty-secondary-action="true"' : '';
                actionHtml +=
                    '<button class="px-4 py-2 text-sm font-medium text-fg-secondary bg-bg-subtle hover:bg-bg rounded-lg transition-colors" ' +
                    secondaryHandlerAttr +
                    '>' +
                    escapeHtml(secondaryActionText) +
                    '</button>';
            }
            actionHtml += '</div>';
        }

        var html =
            '<div class="empty-state">' +
            '<div class="empty-state-icon ' +
            iconClass +
            iconColorClass +
            '">' +
            '<iconify-icon icon="' +
            icon +
            '"' +
            (type === 'loading' ? ' class="animate-spin"' : '') +
            '></iconify-icon>' +
            '</div>' +
            (title ? '<div class="empty-state-title">' + escapeHtml(title) + '</div>' : '') +
            (description ? '<div class="empty-state-desc">' + escapeHtml(description) + '</div>' : '') +
            actionHtml +
            '</div>';

        if (actionHandler && typeof actionHandler === 'function') {
            setTimeout(function () {
                var btn = document.querySelector('[data-empty-action="true"]:not([data-bound])');
                if (btn) {
                    btn.setAttribute('data-bound', 'true');
                    btn.addEventListener('click', actionHandler);
                }
            }, 0);
        }

        if (secondaryActionHandler && typeof secondaryActionHandler === 'function') {
            setTimeout(function () {
                var btn = document.querySelector('[data-empty-secondary-action="true"]:not([data-bound])');
                if (btn) {
                    btn.setAttribute('data-bound', 'true');
                    btn.addEventListener('click', secondaryActionHandler);
                }
            }, 0);
        }

        return html;
    }

    /**
     * 生成错误状态 HTML
     * @param {Object} options - 配置选项
     * @param {string} [options.title] - 标题
     * @param {string} [options.description] - 描述
     * @param {string} [options.retryText] - 重试按钮文本
     * @param {Function} [options.retryHandler] - 重试按钮点击回调
     * @param {Error|string} [options.error] - 原始错误对象
     * @returns {string} - HTML 字符串
     */
    function renderErrorState(options) {
        options = options || {};
        var title = options.title || '加载失败';
        var description = options.description || '抱歉，加载过程中出现了问题，请稍后重试';
        var retryText = options.retryText || '重新加载';
        var retryHandler = options.retryHandler || null;
        var error = options.error || null;

        var errorDetail = '';
        if (error) {
            var errorMsg = typeof error === 'string' ? error : error.message || '';
            if (errorMsg) {
                errorDetail =
                    '<div class="empty-state-error-detail text-[11px] text-fg-tertiary mt-2 p-2 bg-bg-subtle rounded-lg text-left max-w-xs overflow-x-auto">' +
                    '<code>' +
                    escapeHtml(errorMsg) +
                    '</code>' +
                    '</div>';
            }
        }

        var retryHtml = '';
        if (retryText) {
            var handlerAttr = retryHandler ? 'data-error-retry="true"' : '';
            retryHtml =
                '<div class="empty-state-action">' +
                '<button class="px-4 py-2 text-sm font-medium text-white bg-brand hover:bg-brand-hover rounded-lg transition-colors flex items-center gap-1.5" ' +
                handlerAttr +
                '>' +
                '<iconify-icon icon="mdi:refresh" class="text-sm"></iconify-icon>' +
                escapeHtml(retryText) +
                '</button>' +
                '</div>';
        }

        var html =
            '<div class="empty-state error-state">' +
            '<div class="empty-state-icon error">' +
            '<iconify-icon icon="mdi:alert-circle-outline"></iconify-icon>' +
            '</div>' +
            '<div class="empty-state-title">' +
            escapeHtml(title) +
            '</div>' +
            '<div class="empty-state-desc">' +
            escapeHtml(description) +
            '</div>' +
            errorDetail +
            retryHtml +
            '</div>';

        if (retryHandler && typeof retryHandler === 'function') {
            setTimeout(function () {
                var btn = document.querySelector('[data-error-retry="true"]:not([data-bound])');
                if (btn) {
                    btn.setAttribute('data-bound', 'true');
                    btn.addEventListener('click', retryHandler);
                }
            }, 0);
        }

        return html;
    }

    /**
     * 生成骨架屏 HTML
     * @param {Object} options - 配置选项
     * @param {string} [options.type='list'] - 类型: 'list' | 'card' | 'detail'
     * @param {number} [options.count=5] - 数量
     * @returns {string} - HTML 字符串
     */
    function renderSkeleton(options) {
        options = options || {};
        var type = options.type || 'list';
        var count = options.count || 5;
        if (count < 1) count = 1;

        return createSkeleton(type, count);
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
                html +=
                        '<div class="skeleton skeleton-table-row" style="margin-bottom: 0; border-radius: 0;"></div>';
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
                '<div class="page-loading-spinner"></div>' + '<div class="page-loading-text">加载中...</div>';
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

    // ===== 全局快捷键系统 =====
    var _shortcutRegistry = {};
    var _currentScope = 'global';
    var _isMac = /Mac|iPod|iPhone|iPad/.test(navigator.platform);

    function _normalizeKey(key) {
        if (!key) return '';
        return key
            .toLowerCase()
            .replace(/\s+/g, '')
            .replace(/cmd|command|⌘/g, 'meta')
            .replace(/ctrl|control|^/g, 'ctrl')
            .replace(/alt|option|⌥/g, 'alt')
            .replace(/shift|⇧/g, 'shift')
            .replace(/esc|escape/g, 'escape')
            .replace(/enter|return/g, 'enter')
            .replace(/\++/g, '+');
    }

    function _formatKeyDisplay(key) {
        if (!key) return '';
        var normalized = _normalizeKey(key);
        var parts = normalized.split('+');
        var formatted = parts.map(function (part) {
            if (_isMac) {
                if (part === 'ctrl') return '⌃';
                if (part === 'meta') return '⌘';
                if (part === 'alt') return '⌥';
                if (part === 'shift') return '⇧';
                if (part === 'escape') return '⎋';
                if (part === 'enter') return '↵';
                if (part === 'backspace') return '⌫';
            } else {
                if (part === 'ctrl') return 'Ctrl';
                if (part === 'meta') return 'Win';
                if (part === 'alt') return 'Alt';
                if (part === 'shift') return 'Shift';
                if (part === 'escape') return 'Esc';
                if (part === 'enter') return 'Enter';
                if (part === 'backspace') return 'Backspace';
            }
            if (part.length === 1) return part.toUpperCase();
            return part.charAt(0).toUpperCase() + part.slice(1);
        });
        return formatted.join(_isMac ? '' : '+');
    }

    function _getKeyFromEvent(e) {
        var key = e.key.toLowerCase();
        if (key === ' ') key = 'space';
        var parts = [];
        if (e.ctrlKey) parts.push('ctrl');
        if (e.metaKey) parts.push('meta');
        if (e.altKey) parts.push('alt');
        if (e.shiftKey) parts.push('shift');
        if (key !== 'control' && key !== 'meta' && key !== 'alt' && key !== 'shift') {
            parts.push(key);
        }
        return parts.join('+');
    }

    function _isInputElement(el) {
        if (!el) return false;
        var tag = el.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true;
        if (el.isContentEditable) return true;
        return false;
    }

    function _handleKeyDown(e) {
        var eventKey = _getKeyFromEvent(e);
        if (!eventKey) return;

        var isInput = _isInputElement(e.target);
        var scopes = ['global'];
        if (_currentScope && _currentScope !== 'global') {
            scopes.unshift(_currentScope);
        }

        for (var i = 0; i < scopes.length; i++) {
            var scope = scopes[i];
            var scopeShortcuts = _shortcutRegistry[scope];
            if (!scopeShortcuts) continue;

            var shortcut = scopeShortcuts[eventKey];
            if (!shortcut) continue;

            if (isInput && !shortcut.allowInInput) {
                if (eventKey !== 'escape') continue;
            }

            if (shortcut.preventDefault !== false) {
                e.preventDefault();
            }
            if (shortcut.stopPropagation) {
                e.stopPropagation();
            }

            try {
                shortcut.callback(e);
            } catch (err) {
                console.error('[Shortcut] 执行快捷键回调失败:', eventKey, err);
            }
            return;
        }
    }

    function registerShortcut(key, callback, options) {
        if (!key || !callback) return false;
        options = options || {};
        var normalizedKey = _normalizeKey(key);
        var scope = options.scope || 'global';

        if (!_shortcutRegistry[scope]) {
            _shortcutRegistry[scope] = {};
        }

        _shortcutRegistry[scope][normalizedKey] = {
            key: normalizedKey,
            displayKey: _formatKeyDisplay(key),
            callback: callback,
            scope: scope,
            description: options.description || '',
            category: options.category || 'other',
            allowInInput: options.allowInInput === true,
            preventDefault: options.preventDefault !== false,
            stopPropagation: options.stopPropagation === true
        };

        return true;
    }

    function unregisterShortcut(key, scope) {
        var normalizedKey = _normalizeKey(key);
        scope = scope || 'global';
        if (_shortcutRegistry[scope] && _shortcutRegistry[scope][normalizedKey]) {
            delete _shortcutRegistry[scope][normalizedKey];
            return true;
        }
        return false;
    }

    function setShortcutScope(scope) {
        _currentScope = scope || 'global';
    }

    function getShortcuts() {
        var result = {};
        for (var scope in _shortcutRegistry) {
            result[scope] = {};
            for (var key in _shortcutRegistry[scope]) {
                var s = _shortcutRegistry[scope][key];
                result[scope][key] = {
                    key: s.key,
                    displayKey: s.displayKey,
                    description: s.description,
                    category: s.category,
                    scope: s.scope
                };
            }
        }
        return result;
    }

    function showShortcutHelp() {
        var allShortcuts = getShortcuts();
        var categories = {
            navigation: { label: '页面导航', icon: 'mdi:compass-outline', items: [] },
            action: { label: '快速操作', icon: 'mdi:lightning-bolt', items: [] },
            setting: { label: '设置与帮助', icon: 'mdi:cog-outline', items: [] },
            other: { label: '其他', icon: 'mdi:dots-horizontal', items: [] }
        };

        var globalShortcuts = allShortcuts['global'] || {};
        for (var key in globalShortcuts) {
            var s = globalShortcuts[key];
            var cat = categories[s.category] || categories.other;
            cat.items.push(s);
        }

        var contentHtml = '<div class="shortcut-help-content">';
        for (var catKey in categories) {
            var cat = categories[catKey];
            if (cat.items.length === 0) continue;
            contentHtml +=
                '<div class="shortcut-category mb-4">' +
                '<div class="flex items-center gap-2 mb-2">' +
                '<iconify-icon icon="' +
                cat.icon +
                '" class="text-brand"></iconify-icon>' +
                '<span class="text-sm font-semibold text-fg-primary">' +
                cat.label +
                '</span>' +
                '</div>' +
                '<div class="space-y-1 pl-6">';
            cat.items.forEach(function (item) {
                contentHtml +=
                    '<div class="flex items-center justify-between py-1.5 px-2 rounded-lg hover:bg-bg-subtle">' +
                    '<span class="text-xs text-fg-secondary">' +
                    escapeHtml(item.description) +
                    '</span>' +
                    '<kbd class="shortcut-kbd">' +
                    item.displayKey +
                    '</kbd>' +
                    '</div>';
            });
            contentHtml += '</div></div>';
        }
        contentHtml += '</div>';

        showModal({
            id: 'shortcut-help-modal',
            title: '键盘快捷键',
            content: contentHtml,
            size: 'md',
            icon: 'mdi:keyboard-variant',
            escClose: true
        });
    }

    // ===== 命令面板 =====
    var _commandPaletteEl = null;
    var _commandPaletteInput = null;
    var _commandListEl = null;
    var _commands = [];
    var _filteredCommands = [];
    var _selectedIndex = 0;
    var _isPaletteOpen = false;

    function _registerDefaultCommands() {
        _commands = [
            {
                id: 'nav-workstation',
                name: '工作台',
                description: '返回工作台首页',
                icon: 'mdi:view-dashboard-outline',
                category: 'navigation',
                shortcut: '',
                action: function () {
                    if (typeof switchView === 'function') switchView('workstation');
                }
            },
            {
                id: 'nav-cases',
                name: '案件管理',
                description: '查看和管理所有案件',
                icon: 'mdi:briefcase-outline',
                category: 'navigation',
                shortcut: '',
                action: function () {
                    if (typeof switchToList === 'function') switchToList('case-list');
                }
            },
            {
                id: 'nav-schedule',
                name: '日程管理',
                description: '查看和管理日程安排',
                icon: 'mdi:calendar-month-outline',
                category: 'navigation',
                shortcut: '',
                action: function () {
                    if (typeof switchView === 'function') switchView('schedule-calendar');
                }
            },
            {
                id: 'nav-clients',
                name: '客户管理',
                description: '管理客户信息',
                icon: 'mdi:account-group-outline',
                category: 'navigation',
                shortcut: '',
                action: function () {
                    if (typeof switchView === 'function') switchView('client');
                }
            },
            {
                id: 'nav-templates',
                name: '模板管理',
                description: '管理文书模板',
                icon: 'mdi:file-document-outline',
                category: 'navigation',
                shortcut: '',
                action: function () {
                    if (typeof switchView === 'function') switchView('template');
                }
            },
            {
                id: 'nav-knowledge',
                name: '知识库',
                description: '法律知识库检索',
                icon: 'mdi:bookshelf',
                category: 'navigation',
                shortcut: '',
                action: function () {
                    if (typeof switchView === 'function') switchView('knowledge');
                }
            },
            {
                id: 'nav-archive',
                name: '归档管理',
                description: '已归档案件',
                icon: 'mdi:archive-outline',
                category: 'navigation',
                shortcut: '',
                action: function () {
                    if (typeof switchView === 'function') switchView('archive');
                }
            },
            {
                id: 'nav-ai-chat',
                name: 'AI 对话',
                description: '打开 LexPrime 助手',
                icon: 'mdi:chat-processing-outline',
                category: 'navigation',
                shortcut: '',
                action: function () {
                    if (typeof switchSidebarTab === 'function') switchSidebarTab('ai');
                }
            },
            {
                id: 'nav-settings',
                name: '账号设置',
                description: '个人设置与偏好',
                icon: 'mdi:cog-outline',
                category: 'navigation',
                shortcut: '',
                action: function () {
                    if (typeof window.switchToAccountSettings === 'function') window.switchToAccountSettings();
                }
            },
            {
                id: 'action-new-case',
                name: '新建案件',
                description: '创建一个新的案件',
                icon: 'mdi:plus-circle-outline',
                category: 'action',
                shortcut: 'Ctrl+N',
                action: function () {
                    if (typeof window.showNewCaseModal === 'function') window.showNewCaseModal();
                    else showToast('新建案件功能开发中');
                }
            },
            {
                id: 'action-new-schedule',
                name: '新建日程',
                description: '添加新的日程安排',
                icon: 'mdi:calendar-plus',
                category: 'action',
                shortcut: '',
                action: function () {
                    if (typeof window.openScheduleModal === 'function') window.openScheduleModal();
                    else showToast('新建日程功能开发中');
                }
            },
            {
                id: 'action-upload-file',
                name: '上传文件',
                description: '上传文件到附件库',
                icon: 'mdi:upload',
                category: 'action',
                shortcut: '',
                action: function () {
                    showToast('上传文件功能开发中');
                }
            },
            {
                id: 'action-search',
                name: '全局搜索',
                description: '搜索案件、文书、证据',
                icon: 'mdi:magnify',
                category: 'action',
                shortcut: 'Ctrl+/',
                action: function () {
                    var input = document.querySelector('header input[type="text"]');
                    if (input) {
                        input.focus();
                        input.select();
                    }
                }
            },
            {
                id: 'setting-shortcuts',
                name: '快捷键帮助',
                description: '查看所有键盘快捷键',
                icon: 'mdi:keyboard-variant',
                category: 'setting',
                shortcut: '?',
                action: function () {
                    closeCommandPalette();
                    setTimeout(showShortcutHelp, 100);
                }
            },
            {
                id: 'setting-theme-toggle',
                name: '切换主题',
                description: '切换浅色/深色模式',
                icon: 'mdi:theme-light-dark',
                category: 'setting',
                shortcut: 'Ctrl+Shift+L',
                action: function () {
                    closeCommandPalette();
                    setTimeout(toggleTheme, 100);
                }
            },
            {
                id: 'setting-theme-light',
                name: '浅色模式',
                description: '使用浅色主题',
                icon: 'mdi:white-balance-sunny',
                category: 'setting',
                shortcut: '',
                action: function () {
                    closeCommandPalette();
                    setTimeout(function () {
                        setTheme('light');
                    }, 100);
                }
            },
            {
                id: 'setting-theme-dark',
                name: '深色模式',
                description: '使用深色主题',
                icon: 'mdi:moon-waning-crescent',
                category: 'setting',
                shortcut: '',
                action: function () {
                    closeCommandPalette();
                    setTimeout(function () {
                        setTheme('dark');
                    }, 100);
                }
            },
            {
                id: 'setting-theme-auto',
                name: '跟随系统',
                description: '自动跟随系统主题',
                icon: 'mdi:monitor-screenshot',
                category: 'setting',
                shortcut: '',
                action: function () {
                    closeCommandPalette();
                    setTimeout(function () {
                        setTheme('auto');
                    }, 100);
                }
            }
        ];
    }

    function _fuzzyMatch(query, text) {
        if (!query) return true;
        query = query.toLowerCase();
        text = text.toLowerCase();
        if (text.indexOf(query) !== -1) return true;
        var qIndex = 0;
        for (var i = 0; i < text.length && qIndex < query.length; i++) {
            if (text[i] === query[qIndex]) qIndex++;
        }
        return qIndex === query.length;
    }

    function _filterCommands(query) {
        if (!query) {
            _filteredCommands = _commands.slice();
            return;
        }
        _filteredCommands = _commands.filter(function (cmd) {
            return (
                _fuzzyMatch(query, cmd.name) || _fuzzyMatch(query, cmd.description) || _fuzzyMatch(query, cmd.category)
            );
        });
    }

    function _getCategoryLabel(cat) {
        var map = { navigation: '页面导航', action: '快速操作', setting: '设置' };
        return map[cat] || cat;
    }

    function _renderCommandList() {
        if (!_commandListEl) return;

        var html = '';
        var currentCategory = '';
        var displayIndex = 0;

        if (_filteredCommands.length === 0) {
            html =
                '<div class="p-8 text-center text-fg-tertiary text-sm">' +
                '<iconify-icon icon="mdi:magnify-scan" class="text-3xl mb-2 block mx-auto"></iconify-icon>' +
                '没有找到匹配的命令' +
                '</div>';
            _commandListEl.innerHTML = html;
            return;
        }

        _filteredCommands.forEach(function (cmd, idx) {
            if (cmd.category !== currentCategory) {
                currentCategory = cmd.category;
                html +=
                    '<div class="command-category px-3 py-1.5 text-[11px] font-medium text-fg-tertiary bg-bg-subtle/50 sticky top-0 backdrop-blur-sm z-10">' +
                    _getCategoryLabel(cmd.category) +
                    '</div>';
            }
            var isSelected = idx === _selectedIndex;
            var shortcutHtml = cmd.shortcut
                ? '<kbd class="shortcut-kbd text-[10px]">' + _formatKeyDisplay(cmd.shortcut) + '</kbd>'
                : '';
            html +=
                '<div class="command-item flex items-center gap-3 px-3 py-2 cursor-pointer transition-colors ' +
                (isSelected ? 'bg-brand/10' : 'hover:bg-bg-subtle') +
                '" data-index="' +
                idx +
                '" role="option" aria-selected="' +
                (isSelected ? 'true' : 'false') +
                '">' +
                '<div class="w-8 h-8 rounded-lg bg-bg-subtle flex items-center justify-center flex-shrink-0 ' +
                (isSelected ? 'bg-brand/20' : '') +
                '">' +
                '<iconify-icon icon="' +
                cmd.icon +
                '" class="' +
                (isSelected ? 'text-brand' : 'text-fg-tertiary') +
                '"></iconify-icon>' +
                '</div>' +
                '<div class="flex-1 min-w-0">' +
                '<div class="text-sm font-medium text-fg-primary truncate">' +
                escapeHtml(cmd.name) +
                '</div>' +
                '<div class="text-[11px] text-fg-tertiary truncate">' +
                escapeHtml(cmd.description) +
                '</div>' +
                '</div>' +
                shortcutHtml +
                '</div>';
            displayIndex++;
        });

        _commandListEl.innerHTML = html;

        var selectedEl = _commandListEl.querySelector('.command-item[aria-selected="true"]');
        if (selectedEl) {
            selectedEl.scrollIntoView({ block: 'nearest' });
        }

        if (typeof gsap !== 'undefined') {
            gsap.fromTo(
                _commandListEl.querySelectorAll('.command-item'),
                { opacity: 0, y: 4 },
                { opacity: 1, y: 0, duration: 0.15, stagger: 0.02, ease: 'power2.out' }
            );
        }
    }

    function _onCommandInput() {
        var query = _commandPaletteInput ? _commandPaletteInput.value : '';
        _filterCommands(query);
        _selectedIndex = 0;
        _renderCommandList();
    }

    function _onCommandKeyDown(e) {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (_filteredCommands.length > 0) {
                _selectedIndex = (_selectedIndex + 1) % _filteredCommands.length;
                _renderCommandList();
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (_filteredCommands.length > 0) {
                _selectedIndex = (_selectedIndex - 1 + _filteredCommands.length) % _filteredCommands.length;
                _renderCommandList();
            }
        } else if (e.key === 'Enter') {
            e.preventDefault();
            _executeSelectedCommand();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            closeCommandPalette();
        }
    }

    function _executeSelectedCommand() {
        var cmd = _filteredCommands[_selectedIndex];
        if (cmd && cmd.action) {
            closeCommandPalette();
            setTimeout(function () {
                try {
                    cmd.action();
                } catch (err) {
                    console.error('[CommandPalette] 执行命令失败:', cmd.id, err);
                }
            }, 150);
        }
    }

    function _createCommandPalette() {
        if (_commandPaletteEl) return;

        var overlay = document.createElement('div');
        overlay.id = 'command-palette';
        overlay.className = 'command-palette-overlay fixed inset-0 z-[2000] bg-black/40 backdrop-blur-sm hidden';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.setAttribute('aria-label', '命令面板');

        overlay.innerHTML =
            '<div class="command-palette-container mx-auto mt-[15vh] w-full max-w-lg px-4">' +
            '<div class="command-palette-modal bg-white rounded-2xl shadow-2xl overflow-hidden">' +
            '<div class="flex items-center gap-3 px-4 py-3 border-b border-bg-border">' +
            '<iconify-icon icon="mdi:magnify" class="text-fg-tertiary text-lg"></iconify-icon>' +
            '<input type="text" class="command-palette-input flex-1 text-sm bg-transparent outline-none placeholder-fg-tertiary" placeholder="输入命令或搜索... (Ctrl+K)" autocomplete="off" spellcheck="false">' +
            '<kbd class="shortcut-kbd text-[10px]">Esc</kbd>' +
            '</div>' +
            '<div class="command-list max-h-[60vh] overflow-y-auto py-1" role="listbox"></div>' +
            '<div class="px-3 py-2 border-t border-bg-border bg-bg-subtle/50 flex items-center justify-between text-[11px] text-fg-tertiary">' +
            '<div class="flex items-center gap-3">' +
            '<span><kbd class="shortcut-kbd text-[9px]">↑↓</kbd> 选择</span>' +
            '<span><kbd class="shortcut-kbd text-[9px]">↵</kbd> 执行</span>' +
            '<span><kbd class="shortcut-kbd text-[9px]">Esc</kbd> 关闭</span>' +
            '</div>' +
            '<span class="text-fg-tertiary">' +
            _commands.length +
            ' 个命令</span>' +
            '</div>' +
            '</div>' +
            '</div>';

        document.body.appendChild(overlay);

        _commandPaletteEl = overlay;
        _commandPaletteInput = overlay.querySelector('.command-palette-input');
        _commandListEl = overlay.querySelector('.command-list');

        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) closeCommandPalette();
        });

        _commandPaletteInput.addEventListener('input', debounce(_onCommandInput, 50));
        _commandPaletteInput.addEventListener('keydown', _onCommandKeyDown);

        _commandListEl.addEventListener('click', function (e) {
            var item = e.target.closest('.command-item');
            if (item) {
                var idx = parseInt(item.getAttribute('data-index'));
                if (!isNaN(idx)) {
                    _selectedIndex = idx;
                    _executeSelectedCommand();
                }
            }
        });

        _commandListEl.addEventListener('mouseover', function (e) {
            var item = e.target.closest('.command-item');
            if (item) {
                var idx = parseInt(item.getAttribute('data-index'));
                if (!isNaN(idx)) {
                    _selectedIndex = idx;
                    _renderCommandList();
                }
            }
        });
    }

    function openCommandPalette() {
        if (_isPaletteOpen) return;

        if (!_commandPaletteEl) {
            _registerDefaultCommands();
            _createCommandPalette();
        }

        _filterCommands('');
        _selectedIndex = 0;
        _renderCommandList();

        _commandPaletteEl.classList.remove('hidden');
        _isPaletteOpen = true;

        setTimeout(function () {
            if (_commandPaletteInput) {
                _commandPaletteInput.value = '';
                _commandPaletteInput.focus();
            }
        }, 50);

        if (typeof gsap !== 'undefined') {
            var modal = _commandPaletteEl.querySelector('.command-palette-modal');
            gsap.fromTo(
                modal,
                { opacity: 0, y: -20, scale: 0.96 },
                { opacity: 1, y: 0, scale: 1, duration: 0.2, ease: 'power3.out' }
            );
            gsap.fromTo(_commandPaletteEl, { opacity: 0 }, { opacity: 1, duration: 0.15, ease: 'power2.out' });
        }
    }

    function closeCommandPalette() {
        if (!_isPaletteOpen || !_commandPaletteEl) return;

        if (typeof gsap !== 'undefined') {
            var modal = _commandPaletteEl.querySelector('.command-palette-modal');
            gsap.to(modal, {
                opacity: 0,
                y: -10,
                scale: 0.98,
                duration: 0.15,
                ease: 'power2.in',
                onComplete: function () {
                    if (_commandPaletteEl) _commandPaletteEl.classList.add('hidden');
                }
            });
            gsap.to(_commandPaletteEl, { opacity: 0, duration: 0.1, ease: 'power2.in' });
        } else {
            _commandPaletteEl.classList.add('hidden');
        }

        _isPaletteOpen = false;

        if (_commandPaletteInput) {
            _commandPaletteInput.blur();
        }
    }

    function registerCommand(cmd) {
        if (!cmd || !cmd.id || !cmd.name) return false;
        _commands.push({
            id: cmd.id,
            name: cmd.name,
            description: cmd.description || '',
            icon: cmd.icon || 'mdi:circle-outline',
            category: cmd.category || 'other',
            shortcut: cmd.shortcut || '',
            action: cmd.action || function () {}
        });
        return true;
    }

    // ===== 主题系统 =====
    var THEME_STORAGE_KEY = 'lexprime-theme';
    var _currentTheme = 'auto';
    var _systemThemeMedia = null;
    var _themeChangeListeners = [];

    function _getSystemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    function _applyTheme(theme) {
        var effectiveTheme = theme === 'auto' ? _getSystemTheme() : theme;
        document.documentElement.setAttribute('data-theme', effectiveTheme);
        document.documentElement.setAttribute('data-theme-mode', theme);

        _updateThemeUI(theme, effectiveTheme);

        _themeChangeListeners.forEach(function (fn) {
            try {
                fn(effectiveTheme, theme);
            } catch (e) {
                console.warn('[Theme] 监听回调执行失败:', e);
            }
        });
    }

    function _updateThemeUI(theme, effectiveTheme) {
        var icon = document.getElementById('status-bar-theme-icon');
        if (icon) {
            if (theme === 'auto') {
                icon.setAttribute('icon', 'mdi:monitor-shimmer');
            } else if (effectiveTheme === 'dark') {
                icon.setAttribute('icon', 'mdi:weather-night');
            } else {
                icon.setAttribute('icon', 'mdi:weather-sunny');
            }
        }

        var themeSelector = document.getElementById('theme-selector');
        if (themeSelector) {
            var options = themeSelector.querySelectorAll('.theme-option');
            options.forEach(function (opt) {
                var optTheme = opt.getAttribute('data-theme');
                if (optTheme === theme) {
                    opt.classList.add('border-brand', 'bg-brand-tint/30');
                    opt.classList.remove('border-bg-border');
                } else {
                    opt.classList.remove('border-brand', 'bg-brand-tint/30');
                    opt.classList.add('border-bg-border');
                }
            });
        }
    }

    function selectThemeOption(theme) {
        setTheme(theme);
    }

    function _initThemeSystem() {
        try {
            var saved = localStorage.getItem(THEME_STORAGE_KEY);
            if (saved === 'light' || saved === 'dark' || saved === 'auto') {
                _currentTheme = saved;
            }
        } catch (e) {
            console.warn('[Theme] 读取 localStorage 失败:', e);
        }

        _applyTheme(_currentTheme);

        if (window.matchMedia) {
            _systemThemeMedia = window.matchMedia('(prefers-color-scheme: dark)');
            var handleSystemChange = function () {
                if (_currentTheme === 'auto') {
                    _applyTheme('auto');
                }
            };

            if (_systemThemeMedia.addEventListener) {
                _systemThemeMedia.addEventListener('change', handleSystemChange);
            } else if (_systemThemeMedia.addListener) {
                _systemThemeMedia.addListener(handleSystemChange);
            }
        }
    }

    function setTheme(theme) {
        if (theme !== 'light' && theme !== 'dark' && theme !== 'auto') {
            console.warn('[Theme] 无效的主题值:', theme);
            return false;
        }

        _currentTheme = theme;

        try {
            localStorage.setItem(THEME_STORAGE_KEY, theme);
        } catch (e) {
            console.warn('[Theme] 保存到 localStorage 失败:', e);
        }

        _applyTheme(theme);

        var effectiveTheme = theme === 'auto' ? _getSystemTheme() : theme;
        showToast({
            type: 'success',
            message: '已切换到' + (theme === 'auto' ? '跟随系统' : effectiveTheme === 'dark' ? '深色模式' : '浅色模式'),
            duration: 2000
        });

        return true;
    }

    function getTheme() {
        return _currentTheme;
    }

    function getEffectiveTheme() {
        return _currentTheme === 'auto' ? _getSystemTheme() : _currentTheme;
    }

    function toggleTheme() {
        var effective = getEffectiveTheme();
        var next = effective === 'dark' ? 'light' : 'dark';
        setTheme(next);
        return next;
    }

    function onThemeChange(callback) {
        if (typeof callback !== 'function') return;
        _themeChangeListeners.push(callback);
        return function () {
            _themeChangeListeners = _themeChangeListeners.filter(function (fn) {
                return fn !== callback;
            });
        };
    }

    function initShortcuts() {
        document.addEventListener('keydown', _handleKeyDown);

        registerShortcut('Ctrl+K', openCommandPalette, {
            description: '打开命令面板',
            category: 'setting',
            allowInInput: true
        });

        registerShortcut('Meta+K', openCommandPalette, {
            description: '打开命令面板',
            category: 'setting',
            allowInInput: true
        });

        registerShortcut(
            'Ctrl+/',
            function () {
                var input = document.querySelector('header input[type="text"]');
                if (input) {
                    input.focus();
                    input.select();
                }
            },
            {
                description: '聚焦搜索框',
                category: 'action',
                allowInInput: false
            }
        );

        registerShortcut(
            'Ctrl+N',
            function () {
                var view = _currentScope;
                if (view === 'case-list' || view === 'cases') {
                    if (typeof window.showNewCaseModal === 'function') window.showNewCaseModal();
                } else if (view === 'schedule' || view === 'schedule-calendar') {
                    if (typeof window.openScheduleModal === 'function') window.openScheduleModal();
                } else {
                    openCommandPalette();
                }
            },
            {
                description: '新建（智能判断）',
                category: 'action',
                allowInInput: false
            }
        );

        registerShortcut('Ctrl+Shift+L', toggleTheme, {
            description: '切换深色/浅色模式',
            category: 'setting',
            allowInInput: true
        });

        registerShortcut(
            'Escape',
            function () {
                if (_isPaletteOpen) {
                    closeCommandPalette();
                    return;
                }
                var modals = document.querySelectorAll('[role="dialog"]:not(.hidden)');
                for (var i = modals.length - 1; i >= 0; i--) {
                    var closeBtn = modals[i].querySelector('[data-modal-close]');
                    if (closeBtn) {
                        closeBtn.click();
                        return;
                    }
                }
            },
            {
                description: '关闭弹窗/取消',
                category: 'other',
                allowInInput: true
            }
        );

        registerShortcut('?', showShortcutHelp, {
            description: '显示快捷键帮助',
            category: 'setting',
            allowInInput: false
        });
    }

    // ===== 移动端优化工具 =====

    function isMobile() {
        if (typeof window !== 'undefined' && window.matchMedia) {
            return window.matchMedia('(max-width: 768px)').matches;
        }
        if (typeof navigator !== 'undefined') {
            var ua = navigator.userAgent.toLowerCase();
            return /android|iphone|ipad|ipod|blackberry|windows phone/i.test(ua);
        }
        return false;
    }

    function preventClickDelay() {
        if (!('ontouchstart' in window)) return;

        var lastTouchEnd = 0;
        document.addEventListener(
            'touchend',
            function (e) {
                var now = Date.now();
                if (now - lastTouchEnd <= 300) {
                    e.preventDefault();
                }
                lastTouchEnd = now;
            },
            false
        );

        document.addEventListener('touchstart', function () {}, { passive: true });
    }

    function optimizeMobileScroll() {
        if (!('ontouchstart' in window)) return;

        var scrollContainers = document.querySelectorAll(
            'body, .overflow-y-auto, .overflow-x-auto, .overflow-auto, #main-content, #sidebar'
        );

        scrollContainers.forEach(function (container) {
            var hasTouchHandler = container.getAttribute('data-touch-optimized') === 'true';
            if (hasTouchHandler) return;

            container.setAttribute('data-touch-optimized', 'true');

            container.addEventListener('touchstart', function () {}, { passive: true });
            container.addEventListener('touchmove', function () {}, { passive: true });
        });
    }

    function adjustForKeyboard() {
        if (!('ontouchstart' in window)) return;

        var originalBodyPadding = document.body.style.paddingBottom;

        function handleResize() {
            var viewportHeight = window.innerHeight;
            var documentHeight = document.documentElement.clientHeight;
            var keyboardHeight = documentHeight - viewportHeight;

            if (keyboardHeight > 50) {
                document.body.style.paddingBottom = keyboardHeight + 'px';
                document.body.style.overflow = 'hidden';
            } else {
                document.body.style.paddingBottom = originalBodyPadding;
                document.body.style.overflow = '';
            }
        }

        if (window.visualViewport) {
            window.visualViewport.addEventListener('resize', handleResize);
        } else {
            window.addEventListener('resize', debounce(handleResize, 100));
        }

        document.addEventListener('focusin', function (e) {
            var target = e.target;
            if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
                setTimeout(function () {
                    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 300);
            }
        });

        document.addEventListener('focusout', function () {
            setTimeout(function () {
                document.body.style.paddingBottom = originalBodyPadding;
                document.body.style.overflow = '';
            }, 300);
        });
    }

    function initMobileOptimizations() {
        preventClickDelay();
        optimizeMobileScroll();
        adjustForKeyboard();
    }

    // ===== 图片懒加载 =====
    var _lazyLoadObserver = null;

    /**
     * 初始化图片懒加载
     * 为所有 img 标签添加 loading="lazy" 属性
     * 使用 Intersection Observer API 实现视口外图片的懒加载
     */
    function initImageLazyLoad() {
        var images = document.querySelectorAll('img');

        images.forEach(function (img) {
            if (!img.hasAttribute('loading')) {
                img.setAttribute('loading', 'lazy');
            }

            if (img.dataset.src && !img.src) {
                img.style.opacity = '0';
                img.style.transition = 'opacity 0.3s ease-in';
            }
        });

        if ('IntersectionObserver' in window) {
            _lazyLoadObserver = new IntersectionObserver(
                function (entries) {
                    entries.forEach(function (entry) {
                        if (entry.isIntersecting) {
                            var img = entry.target;
                            if (img.dataset.src) {
                                img.src = img.dataset.src;
                                img.removeAttribute('data-src');
                            }
                            img.onload = function () {
                                img.style.opacity = '1';
                            };
                            _lazyLoadObserver.unobserve(img);
                        }
                    });
                },
                {
                    rootMargin: '50px',
                    threshold: 0.1
                }
            );

            images.forEach(function (img) {
                if (img.dataset.src) {
                    _lazyLoadObserver.observe(img);
                }
            });
        } else {
            var lazyLoadHandler = throttle(function () {
                images.forEach(function (img) {
                    if (img.dataset.src && isInViewport(img)) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        img.style.opacity = '1';
                    }
                });
            }, 200);

            document.addEventListener('DOMContentLoaded', lazyLoadHandler);
            window.addEventListener('scroll', lazyLoadHandler);
            window.addEventListener('resize', lazyLoadHandler);
        }
    }

    /**
     * 检查元素是否在视口内
     * @param {HTMLElement} el - 要检查的元素
     * @returns {boolean} - 是否在视口内
     */
    function isInViewport(el) {
        var rect = el.getBoundingClientRect();
        var windowHeight = window.innerHeight || document.documentElement.clientHeight;
        var windowWidth = window.innerWidth || document.documentElement.clientWidth;
        return (
            rect.top >= -50 && rect.left >= -50 && rect.bottom <= windowHeight + 50 && rect.right <= windowWidth + 50
        );
    }

    /**
     * 创建图片占位图（渐变色）
     * @param {number} width - 宽度
     * @param {number} height - 高度
     * @returns {string} - base64 图片 URL
     */
    function createPlaceholderImage(width, height) {
        var canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        var ctx = canvas.getContext('2d');

        var gradient = ctx.createLinearGradient(0, 0, width, height);
        gradient.addColorStop(0, '#f3f4f6');
        gradient.addColorStop(1, '#e5e7eb');

        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, width, height);

        return canvas.toDataURL('image/png');
    }

    // 暴露到全局
    globalThis.Utils = {
        escapeHtml: escapeHtml,
        sanitizeHtml: sanitizeHtml,
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
        renderEmptyState: renderEmptyState,
        renderErrorState: renderErrorState,
        renderSkeleton: renderSkeleton,
        showPageLoading: showPageLoading,
        hidePageLoading: hidePageLoading,
        setButtonLoading: setButtonLoading,
        setButtonNormal: setButtonNormal,
        showError: showError,
        registerShortcut: registerShortcut,
        unregisterShortcut: unregisterShortcut,
        setShortcutScope: setShortcutScope,
        getShortcuts: getShortcuts,
        showShortcutHelp: showShortcutHelp,
        openCommandPalette: openCommandPalette,
        closeCommandPalette: closeCommandPalette,
        registerCommand: registerCommand,
        initShortcuts: initShortcuts,
        formatShortcutKey: _formatKeyDisplay,
        setTheme: setTheme,
        getTheme: getTheme,
        getEffectiveTheme: getEffectiveTheme,
        toggleTheme: toggleTheme,
        onThemeChange: onThemeChange,
        selectThemeOption: selectThemeOption,
        _initThemeSystem: _initThemeSystem,
        isMobile: isMobile,
        preventClickDelay: preventClickDelay,
        optimizeMobileScroll: optimizeMobileScroll,
        adjustForKeyboard: adjustForKeyboard,
        initMobileOptimizations: initMobileOptimizations,
        initImageLazyLoad: initImageLazyLoad,
        isInViewport: isInViewport,
        createPlaceholderImage: createPlaceholderImage
    };

    // 兼容旧版：单独暴露 escapeHtml（供各模块迁移过渡）
    globalThis.escapeHtml = escapeHtml;
    globalThis.selectThemeOption = selectThemeOption;
})();
