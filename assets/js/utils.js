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

    var _toastTimer = null;

    /**
     * 轻量 Toast 提示
     * @param {string} type - 类型 'success'|'error'|'info'|'warning'
     * @param {string} message - 提示内容
     * @param {number} [duration=3000] - 显示时长（毫秒）
     */
    function showToast(type, message, duration) {
        if (!message) {
            message = type;
            type = 'info';
        }
        if (!duration) duration = 3000;

        var typeConfig = {
            success: {
                bg: 'bg-green-50',
                border: 'border-green-200',
                text: 'text-green-700',
                icon: 'mdi:check-circle-outline',
                iconColor: 'text-green-500'
            },
            error: {
                bg: 'bg-red-50',
                border: 'border-red-200',
                text: 'text-red-700',
                icon: 'mdi:alert-circle-outline',
                iconColor: 'text-red-500'
            },
            info: {
                bg: 'bg-blue-50',
                border: 'border-blue-200',
                text: 'text-blue-700',
                icon: 'mdi:information-outline',
                iconColor: 'text-blue-500'
            },
            warning: {
                bg: 'bg-amber-50',
                border: 'border-amber-200',
                text: 'text-amber-700',
                icon: 'mdi:alert-outline',
                iconColor: 'text-amber-500'
            }
        };

        var config = typeConfig[type] || typeConfig.info;

        var existing = document.querySelector('.utils-toast');
        if (existing) existing.remove();
        if (_toastTimer) {
            clearTimeout(_toastTimer);
            _toastTimer = null;
        }

        var toast = document.createElement('div');
        toast.className =
            'utils-toast fixed top-4 left-1/2 -translate-x-1/2 z-[9999] ' +
            config.bg +
            ' border ' +
            config.border +
            ' ' +
            config.text +
            ' text-xs px-4 py-2.5 rounded-lg shadow-lg flex items-center gap-2 transform transition-all duration-300 opacity-0 -translate-y-4';
        toast.innerHTML =
            '<iconify-icon icon="' +
            config.icon +
            '" class="' +
            config.iconColor +
            '"></iconify-icon><span>' +
            escapeHtml(message) +
            '</span>';
        document.body.appendChild(toast);

        requestAnimationFrame(function () {
            toast.classList.remove('opacity-0', '-translate-y-4');
            toast.classList.add('opacity-100', 'translate-y-0');
        });

        _toastTimer = setTimeout(function () {
            toast.classList.add('opacity-0', '-translate-y-4');
            setTimeout(function () {
                if (toast.parentNode) toast.remove();
            }, 300);
            _toastTimer = null;
        }, duration);
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
        showPrompt: showPrompt
    };

    // 兼容旧版：单独暴露 escapeHtml（供各模块迁移过渡）
    globalThis.escapeHtml = escapeHtml;
})();
