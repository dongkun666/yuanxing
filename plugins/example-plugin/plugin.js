/**
 * LexPrime 示例插件 - 前端代码
 *
 * 展示插件开发的基本模式:
 * - 生命周期钩子 (onLoad, onEnable, onDisable)
 * - UI 扩展点注入
 * - 事件监听和触发
 * - 与主应用 API 交互
 */

(function () {
    'use strict';

    var ExamplePlugin = {
        _id: null,
        _manifest: null,
        _enabled: true,

        name: '示例插件',
        version: '1.0.0',

        extensions: {
            'workstation.top': function (_options) {
                return (
                    '<div class="bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl p-5 text-white mb-4">' +
                    '    <div class="flex items-center gap-3 mb-2">' +
                    '        <iconify-icon icon="mdi:rocket-launch" class="text-2xl"></iconify-icon>' +
                    '        <h3 class="text-lg font-bold">欢迎使用示例插件</h3>' +
                    '    </div>' +
                    '    <p class="text-sm text-white/80 mb-3">这是一个 LexPrime 插件开发示例。</p>' +
                    '    <button class="px-4 py-2 bg-white text-purple-600 font-medium rounded-lg hover:bg-white/90 transition-colors text-sm" onclick="ExamplePlugin.showHello()">' +
                    '        点击体验' +
                    '    </button>' +
                    '</div>'
                );
            },

            'settings.section': {
                render: function (container, _options) {
                    var section = document.createElement('div');
                    section.className = 'border border-bg-border rounded-lg p-4';
                    section.innerHTML = (
                        '<h4 class="text-sm font-semibold text-fg-primary mb-3">示例插件设置</h4>' +
                        '<div class="space-y-3">' +
                        '    <div class="flex items-center justify-between">' +
                        '        <span class="text-xs text-fg-secondary">启用欢迎消息</span>' +
                        '        <label class="relative inline-flex items-center cursor-pointer">' +
                        '            <input type="checkbox" checked class="sr-only peer" onchange="ExamplePlugin.toggleWelcome(this.checked)">' +
                        '            <div class="w-9 h-5 bg-bg-border peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[\'\'] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-brand"></div>' +
                        '        </label>' +
                        '    </div>' +
                        '    <div>' +
                        '        <label class="text-xs text-fg-secondary block mb-1">自定义问候语</label>' +
                        '        <input type="text" value="你好，LexPrime！" class="w-full px-3 py-2 text-xs border border-bg-border rounded-lg focus:outline-none focus:border-brand transition-colors" onchange="ExamplePlugin.setGreeting(this.value)">' +
                        '    </div>' +
                        '</div>'
                    );
                    container.appendChild(section);
                }
            }
        },

        onLoad: function () {
            console.warn('[ExamplePlugin] Plugin loaded');
            this._loadSettings();

            if (window.PluginManager) {
                window.PluginManager.on('case.opened', this._onCaseOpened.bind(this));
            }
        },

        onEnable: function () {
            console.warn('[ExamplePlugin] Plugin enabled');
        },

        onDisable: function () {
            console.warn('[ExamplePlugin] Plugin disabled');
        },

        showHello: function () {
            var greeting = this._settings.greeting || '你好，LexPrime！';
            if (typeof showToast === 'function') {
                showToast(greeting + ' 这是来自示例插件的问候！', 'success');
            }
        },

        toggleWelcome: function (enabled) {
            this._settings.welcomeEnabled = enabled;
            this._saveSettings();
            if (typeof showToast === 'function') {
                showToast(enabled ? '欢迎消息已启用' : '欢迎消息已关闭', 'info');
            }
        },

        setGreeting: function (text) {
            this._settings.greeting = text;
            this._saveSettings();
        },

        _settings: {
            welcomeEnabled: true,
            greeting: '你好，LexPrime！'
        },

        _loadSettings: function () {
            try {
                var saved = localStorage.getItem('example-plugin-settings');
                if (saved) {
                    this._settings = JSON.parse(saved);
                }
            } catch (e) {
                console.warn('[ExamplePlugin] Failed to load settings:', e);
            }
        },

        _saveSettings: function () {
            try {
                localStorage.setItem('example-plugin-settings', JSON.stringify(this._settings));
            } catch (e) {
                console.warn('[ExamplePlugin] Failed to save settings:', e);
            }
        },

        _onCaseOpened: function (caseData) {
            console.warn('[ExamplePlugin] Case opened:', caseData);
        }
    };

    window['__plugin_example_plugin'] = ExamplePlugin;

    window.ExamplePlugin = {
        showHello: function () {
            var plugin = window['__plugin_example_plugin'];
            if (plugin) {
                plugin.showHello();
            }
        },
        toggleWelcome: function (enabled) {
            var plugin = window['__plugin_example_plugin'];
            if (plugin) {
                plugin.toggleWelcome(enabled);
            }
        },
        setGreeting: function (text) {
            var plugin = window['__plugin_example_plugin'];
            if (plugin) {
                plugin.setGreeting(text);
            }
        }
    };
})();
