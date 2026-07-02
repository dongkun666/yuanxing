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

        var iconHtml = icon ? '<iconify-icon icon="' + icon + '" class="text-brand text-lg"></iconify-icon>' : '';

        modal.innerHTML =
            '<div class="bg-white rounded-2xl shadow-2xl w-full ' +
            sizeClasses[size] +
            ' overflow-hidden">' +
            '<div class="flex items-center justify-between px-5 py-4 border-b border-bg-border">' +
            '<h3 class="text-base font-semibold text-fg-primary flex items-center gap-2">' +
            iconHtml +
            title +
            '</h3>' +
            '<button class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-bg text-fg-tertiary" onclick="close()" aria-label="关闭">' +
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

        function close() {
            modal.classList.add('hidden');
            if (escClose) {
                document.removeEventListener('keydown', onKeyDown);
            }
            delete _modalRegistry[id];
            onClose();
        }

        function onKeyDown(e) {
            if (e.key === 'Escape') close();
        }

        modal.classList.remove('hidden');
        if (escClose) {
            document.addEventListener('keydown', onKeyDown);
        }

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

    // 暴露到全局
    globalThis.Utils = {
        escapeHtml: escapeHtml,
        debounce: debounce,
        throttle: throttle,
        formatDate: formatDate,
        formatNumber: formatNumber,
        deepClone: deepClone,
        showModal: showModal,
        closeAllModals: closeAllModals
    };

    // 兼容旧版：单独暴露 escapeHtml（供各模块迁移过渡）
    globalThis.escapeHtml = escapeHtml;
})();
