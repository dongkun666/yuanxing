/**
 * LexPrime 插件加载器
 *
 * 功能:
 * - 插件发现和加载
 * - 插件生命周期管理
 * - 前端 UI 扩展点
 * - 插件间通信
 *
 * 插件规范:
 * - 每个插件包含 manifest.json 配置文件
 * - 前端插件通过 plugin.js 导出插件对象
 * - 插件支持 UI 扩展点注入
 */

(function () {
    'use strict';

    var PluginManager = {
        _plugins: {},
        _extensionPoints: {},
        _eventListeners: {},
        _loaded: false,
        _baseUrl: './plugins/',

        init: function () {
            if (this._loaded) {
                return;
            }
            this._loaded = true;
            this._initExtensionPoints();
            this._loadBuiltinPlugins();
        },

        _initExtensionPoints: function () {
            var points = [
                'sidebar.before',
                'sidebar.after',
                'workstation.top',
                'workstation.bottom',
                'case.detail.top',
                'case.detail.bottom',
                'contract.review.before',
                'contract.review.after',
                'settings.section',
                'global.menu'
            ];
            for (var i = 0; i < points.length; i++) {
                this._extensionPoints[points[i]] = [];
            }
        },

        _loadBuiltinPlugins: function () {
            var builtins = ['example-plugin'];
            for (var i = 0; i < builtins.length; i++) {
                this.loadPlugin(builtins[i]);
            }
        },

        loadPlugin: function (pluginId) {
            var self = this;
            var manifestUrl = this._baseUrl + pluginId + '/manifest.json';

            return fetch(manifestUrl)
                .then(function (res) {
                    return res.json();
                })
                .then(function (manifest) {
                    if (!manifest || !manifest.id) {
                        throw new Error('Invalid plugin manifest');
                    }
                    return self._loadPluginScript(manifest);
                })
                .then(function (pluginObj) {
                    return self._registerPlugin(pluginObj);
                })
                .catch(function (err) {
                    console.warn('[Plugin] Failed to load plugin ' + pluginId + ':', err);
                });
        },

        _loadPluginScript: function (manifest) {
            var self = this;
            return new Promise(function (resolve, reject) {
                var scriptUrl = self._baseUrl + manifest.id + '/plugin.js';
                var script = document.createElement('script');
                script.src = scriptUrl;
                script.onload = function () {
                    var pluginObj = window['__plugin_' + manifest.id.replace(/-/g, '_')];
                    if (!pluginObj) {
                        reject(new Error('Plugin script loaded but no plugin object found'));
                        return;
                    }
                    pluginObj._manifest = manifest;
                    resolve(pluginObj);
                };
                script.onerror = function () {
                    reject(new Error('Failed to load plugin script'));
                };
                document.head.appendChild(script);
            });
        },

        _registerPlugin: function (plugin) {
            var id = plugin._manifest.id;
            if (this._plugins[id]) {
                console.warn('[Plugin] Plugin already registered:', id);
                return this._plugins[id];
            }

            plugin._id = id;
            plugin._enabled = true;

            if (typeof plugin.extensions === 'object' && plugin.extensions) {
                for (var point in plugin.extensions) {
                    if (plugin.extensions.hasOwnProperty(point)) {
                        this._registerExtension(id, point, plugin.extensions[point]);
                    }
                }
            }

            this._plugins[id] = plugin;

            if (typeof plugin.onLoad === 'function') {
                try {
                    plugin.onLoad.call(plugin);
                } catch (e) {
                    console.error('[Plugin] onLoad error for ' + id + ':', e);
                }
            }

            console.warn('[Plugin] Loaded:', id);
            return plugin;
        },

        _registerExtension: function (pluginId, point, extension) {
            if (!this._extensionPoints[point]) {
                this._extensionPoints[point] = [];
            }
            this._extensionPoints[point].push({
                pluginId: pluginId,
                extension: extension
            });
        },

        getPlugin: function (id) {
            return this._plugins[id] || null;
        },

        getAllPlugins: function () {
            var result = [];
            for (var id in this._plugins) {
                if (this._plugins.hasOwnProperty(id)) {
                    result.push(this._plugins[id]);
                }
            }
            return result;
        },

        getExtensions: function (point) {
            return this._extensionPoints[point] || [];
        },

        renderExtensions: function (point, containerEl, options) {
            var extensions = this.getExtensions(point);
            if (!containerEl || extensions.length === 0) {
                return;
            }

            options = options || {};

            for (var i = 0; i < extensions.length; i++) {
                var ext = extensions[i];
                var plugin = this._plugins[ext.pluginId];
                if (!plugin || !plugin._enabled) {
                    continue;
                }

                try {
                    var extObj = ext.extension;
                    if (typeof extObj === 'function') {
                        var html = extObj.call(plugin, options);
                        if (html && typeof html === 'string') {
                            var wrapper = document.createElement('div');
                            wrapper.className = 'plugin-extension plugin-' + ext.pluginId;
                            wrapper.innerHTML = html;
                            containerEl.appendChild(wrapper);
                        }
                    } else if (typeof extObj.render === 'function') {
                        extObj.render.call(extObj, containerEl, options);
                    } else if (typeof extObj === 'string') {
                        var wrapper2 = document.createElement('div');
                        wrapper2.className = 'plugin-extension plugin-' + ext.pluginId;
                        wrapper2.innerHTML = extObj;
                        containerEl.appendChild(wrapper2);
                    }
                } catch (e) {
                    console.error('[Plugin] Extension render error for ' + ext.pluginId + ':' + point, e);
                }
            }
        },

        enablePlugin: function (id) {
            var plugin = this._plugins[id];
            if (!plugin) {
                return false;
            }
            plugin._enabled = true;
            if (typeof plugin.onEnable === 'function') {
                try {
                    plugin.onEnable.call(plugin);
                } catch (e) {
                    console.error('[Plugin] onEnable error:', e);
                }
            }
            return true;
        },

        disablePlugin: function (id) {
            var plugin = this._plugins[id];
            if (!plugin) {
                return false;
            }
            plugin._enabled = false;
            if (typeof plugin.onDisable === 'function') {
                try {
                    plugin.onDisable.call(plugin);
                } catch (e) {
                    console.error('[Plugin] onDisable error:', e);
                }
            }
            return true;
        },

        on: function (event, callback) {
            if (!this._eventListeners[event]) {
                this._eventListeners[event] = [];
            }
            this._eventListeners[event].push(callback);
        },

        off: function (event, callback) {
            if (!this._eventListeners[event]) {
                return;
            }
            var listeners = this._eventListeners[event];
            for (var i = listeners.length - 1; i >= 0; i--) {
                if (listeners[i] === callback) {
                    listeners.splice(i, 1);
                }
            }
        },

        emit: function (event, data) {
            var listeners = this._eventListeners[event];
            if (!listeners) {
                return;
            }
            for (var i = 0; i < listeners.length; i++) {
                try {
                    listeners[i](data);
                } catch (e) {
                    console.error('[Plugin] Event listener error for ' + event, e);
                }
            }
        },

        callPluginMethod: function (pluginId, method, args) {
            var plugin = this._plugins[pluginId];
            if (!plugin || !plugin._enabled) {
                return null;
            }
            if (typeof plugin[method] !== 'function') {
                return null;
            }
            try {
                return plugin[method].apply(plugin, args || []);
            } catch (e) {
                console.error('[Plugin] Method call error ' + pluginId + '.' + method, e);
                return null;
            }
        }
    };

    window.PluginManager = PluginManager;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            PluginManager.init();
        });
    } else {
        PluginManager.init();
    }
})();
