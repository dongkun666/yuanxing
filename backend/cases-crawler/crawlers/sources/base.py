"""
4 个免费数据源爬虫 (基类)
2026-06-28 · 共享 httpx 客户端 + 反爬中间件

数据源:
1. 国家法律法规数据库 (npc_laws)
2. 人民法院案例库 (court_cases)
3. 中国执行信息公开网 (zhixing)
4. 国家企业信用信息公示系统 (gsxt)
"""
import asyncio
import httpx
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from loguru import logger

from core.config import settings
from crawlers.middlewares.anti_ban import AntiBanMiddleware, RetryMiddleware


class BaseSource(ABC):
    """免费数据源基类"""

    source_name: str = "base"

    def __init__(self):
        self.anti_ban = AntiBanMiddleware(
            delay_range=(1.0, 3.0) if not settings.proxy_enabled else (2.0, 5.0)
        )
        self.retry = RetryMiddleware(max_retries=settings.crawler_max_retries)
        self.client: Optional[httpx.AsyncClient] = None
        self.stats = {
            "requests": 0,
            "success": 0,
            "failed": 0,
            "items": 0,
        }

    async def init(self):
        """初始化 httpx 客户端"""
        proxy = None
        if settings.proxy_enabled and settings.proxy_pool:
            # 简单随机取一个
            import random
            proxy = random.choice([p.strip() for p in settings.proxy_pool.split(",") if p.strip()])
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.crawler_timeout),
            follow_redirects=True,
            http2=True,
            proxy=proxy,
            headers=self.anti_ban.get_headers(),
        )
        logger.info(f"[{self.source_name}] HTTP client initialized")

    async def close(self):
        if self.client:
            await self.client.aclose()
            logger.info(f"[{self.source_name}] HTTP client closed")

    async def fetch(self, url: str, method: str = "GET", **kwargs) -> Optional[httpx.Response]:
        """带反爬的请求"""
        await self.anti_ban.delay()
        self.stats["requests"] += 1

        async def _do():
            resp = await self.client.request(method, url, **kwargs)
            return resp

        try:
            resp = await self.retry.retry(_do)
            if self.anti_ban.is_blocked(resp.status_code, resp.text):
                logger.warning(f"[{self.source_name}] Blocked detected: {resp.status_code}")
                self.stats["failed"] += 1
                return None
            if self.anti_ban.is_captcha_page(resp.text):
                logger.error(f"[{self.source_name}] CAPTCHA detected, need manual handling")
                self.stats["failed"] += 1
                return None
            self.stats["success"] += 1
            return resp
        except Exception as e:
            logger.error(f"[{self.source_name}] Fetch failed: {url[:80]} - {e}")
            self.stats["failed"] += 1
            return None

    @abstractmethod
    async def crawl(self, **kwargs) -> List[Dict[str, Any]]:
        """爬取入口 - 子类实现"""
        pass

    def report(self):
        """统计报告"""
        logger.info(f"[{self.source_name}] Stats: {self.stats}")
