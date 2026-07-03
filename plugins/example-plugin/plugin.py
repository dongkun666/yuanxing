"""
LexPrime 示例插件 - 后端代码

展示后端插件开发的基本模式:
- API 扩展 (注册新的路由)
- 钩子函数 (Hooks)
- 数据访问
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from loguru import logger


PLUGIN_ID = "example-plugin"
PLUGIN_NAME = "示例插件"
PLUGIN_VERSION = "1.0.0"


class ExamplePlugin:
    """示例后端插件"""

    def __init__(self):
        self.id = PLUGIN_ID
        self.name = PLUGIN_NAME
        self.version = PLUGIN_VERSION
        self.enabled = True
        self._data = {}

    def on_load(self, app=None):
        """插件加载时调用

        Args:
            app: FastAPI 应用实例
        """
        logger.info(f"[{self.id}] Plugin loaded (v{self.version})")

        if app:
            self._register_routes(app)

    def on_enable(self):
        """插件启用时调用"""
        logger.info(f"[{self.id}] Plugin enabled")
        self.enabled = True

    def on_disable(self):
        """插件禁用时调用"""
        logger.info(f"[{self.id}] Plugin disabled")
        self.enabled = False

    def on_uninstall(self):
        """插件卸载时调用"""
        logger.info(f"[{self.id}] Plugin uninstalled")

    def _register_routes(self, app):
        """注册插件 API 路由"""

        @app.get("/api/plugins/example/hello")
        async def example_hello(name: Optional[str] = None):
            """示例 API - 打招呼"""
            greeting = f"Hello, {name}!" if name else "Hello, LexPrime!"
            return {
                "plugin": self.id,
                "version": self.version,
                "message": greeting,
            }

        @app.get("/api/plugins/example/stats")
        async def example_stats():
            """示例 API - 插件统计"""
            return {
                "plugin": self.id,
                "enabled": self.enabled,
                "data_count": len(self._data),
            }

        logger.info(f"[{self.id}] Routes registered")

    def hook_before_case_search(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """钩子: 案件搜索前

        Args:
            query: 搜索查询参数

        Returns:
            修改后的查询参数
        """
        logger.debug(f"[{self.id}] Before case search: {query}")
        return query

    def hook_after_case_search(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """钩子: 案件搜索后

        Args:
            results: 搜索结果列表

        Returns:
            修改后的结果列表
        """
        logger.debug(f"[{self.id}] After case search: {len(results)} results")
        return results


_plugin_instance = None


def get_plugin() -> ExamplePlugin:
    """获取插件单例"""
    global _plugin_instance
    if _plugin_instance is None:
        _plugin_instance = ExamplePlugin()
    return _plugin_instance


def register(app=None):
    """注册插件

    这是后端插件的入口函数，由插件加载器调用。
    """
    plugin = get_plugin()
    plugin.on_load(app)
    return plugin
