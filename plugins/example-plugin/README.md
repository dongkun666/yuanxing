# LexPrime 示例插件

这是一个 LexPrime 插件开发示例，展示了插件系统的基本功能。

## 功能特性

- 🚀 **工作台欢迎卡片** - 在工作台顶部显示欢迎消息
- ⚙️ **设置面板** - 在设置页面添加插件配置选项
- 🔌 **生命周期钩子** - 演示插件加载、启用、禁用流程
- 📡 **事件系统** - 监听和触发应用事件
- 💾 **数据持久化** - 使用 localStorage 存储设置

## 文件结构

```
example-plugin/
├── manifest.json    # 插件配置清单
├── plugin.js        # 前端插件代码
├── plugin.py        # 后端插件代码
└── README.md        # 插件说明文档
```

## manifest.json 说明

```json
{
  "id": "example-plugin",           // 插件唯一标识
  "name": "示例插件",                // 插件显示名称
  "version": "1.0.0",               // 版本号
  "description": "插件描述",         // 插件功能描述
  "author": "LexPrime Team",        // 作者
  "type": "frontend",               // 插件类型: frontend / backend / full
  "entry": "plugin.js",             // 前端入口文件
  "backend_entry": "plugin.py",     // 后端入口文件
  "permissions": [                  // 所需权限
    "case.read",
    "ui.inject"
  ],
  "extension_points": {             // UI 扩展点
    "workstation.top": { ... }
  },
  "min_version": "0.7.0",           // 最低支持版本
  "max_version": "1.0.0"            // 最高支持版本
}
```

## 前端插件开发

### 基本结构

```javascript
(function () {
    'use strict';

    var MyPlugin = {
        name: '我的插件',
        version: '1.0.0',

        extensions: {
            // 扩展点定义
        },

        onLoad: function () {
            // 插件加载时执行
        },

        onEnable: function () {
            // 插件启用时执行
        },

        onDisable: function () {
            // 插件禁用时执行
        }
    };

    window['__plugin_my_plugin'] = MyPlugin;
})();
```

### 可用扩展点

| 扩展点 | 位置 | 说明 |
|--------|------|------|
| `sidebar.before` | 侧边栏顶部 | 在侧边栏菜单前注入内容 |
| `sidebar.after` | 侧边栏底部 | 在侧边栏菜单后注入内容 |
| `workstation.top` | 工作台顶部 | 在工作台页面顶部注入内容 |
| `workstation.bottom` | 工作台底部 | 在工作台页面底部注入内容 |
| `case.detail.top` | 案件详情顶部 | 在案件详情页顶部注入内容 |
| `case.detail.bottom` | 案件详情底部 | 在案件详情页底部注入内容 |
| `contract.review.before` | 合同审查前 | 在合同审查页面顶部注入内容 |
| `contract.review.after` | 合同审查后 | 在合同审查页面底部注入内容 |
| `settings.section` | 设置页面 | 在设置页面添加配置区块 |
| `global.menu` | 全局菜单 | 在全局菜单中添加项目 |

### 插件 API

```javascript
// 获取插件管理器
PluginManager.getPlugin('plugin-id');

// 获取所有插件
PluginManager.getAllPlugins();

// 获取某个扩展点的所有扩展
PluginManager.getExtensions('workstation.top');

// 渲染扩展点内容
PluginManager.renderExtensions('workstation.top', containerEl);

// 启用/禁用插件
PluginManager.enablePlugin('plugin-id');
PluginManager.disablePlugin('plugin-id');

// 事件系统
PluginManager.on('event.name', callback);
PluginManager.off('event.name', callback);
PluginManager.emit('event.name', data);

// 调用插件方法
PluginManager.callPluginMethod('plugin-id', 'methodName', [arg1, arg2]);
```

## 后端插件开发

### 基本结构

```python
class MyPlugin:
    def __init__(self):
        self.id = "my-plugin"
        self.name = "我的插件"

    def on_load(self, app=None):
        if app:
            self._register_routes(app)

    def _register_routes(self, app):
        @app.get("/api/plugins/my-plugin/hello")
        async def hello():
            return {"message": "Hello from plugin!"}


def register(app=None):
    plugin = MyPlugin()
    plugin.on_load(app)
    return plugin
```

### 可用钩子

| 钩子 | 触发时机 | 参数 | 返回值 |
|------|----------|------|--------|
| `hook_before_case_search` | 案件搜索前 | query: dict | 修改后的 query |
| `hook_after_case_search` | 案件搜索后 | results: list | 修改后的 results |

## 安装

1. 将插件文件夹放入 `plugins/` 目录
2. 刷新页面，插件会自动加载
3. 在设置中可以启用/禁用插件

## 开发调试

1. 打开浏览器开发者工具
2. 在控制台访问 `PluginManager` 对象
3. 调用 `PluginManager.getAllPlugins()` 查看已加载的插件
4. 使用 `PluginManager.getPlugin('example-plugin')` 获取插件实例

## License

MIT
