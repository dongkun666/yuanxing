"""
LexPrime 反爬中间件
2026-06-28 · 4 个免费数据源 + cncases 的反爬策略

策略:
1. 随机 User-Agent
2. 随机请求间隔 (1-3 秒)
3. 慢速 (1 req/s) - 避免触发风控
4. 失败重试 + 指数退避
5. 简单验证码检测 (跳到手动处理)
"""
import random
import asyncio
from typing import Optional
from loguru import logger
from fake_useragent import UserAgent


class AntiBanMiddleware:
    """反爬中间件 - 通用"""

    # 浏览器 User-Agent 池
    UA_POOL = [
        # Chrome Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        # Chrome Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Firefox Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]

    def __init__(self, delay_range: tuple = (1.0, 3.0)):
        self.delay_range = delay_range
        self.request_count = 0
        self.last_request_time = 0

    def get_random_ua(self) -> str:
        """获取随机 UA"""
        try:
            ua = UserAgent(browsers=['chrome', 'firefox', 'edge'])
            return ua.random
        except Exception:
            return random.choice(self.UA_POOL)

    async def delay(self):
        """请求间隔 - 慢速反爬"""
        delay = random.uniform(*self.delay_range)
        await asyncio.sleep(delay)
        self.request_count += 1

    def get_headers(self, referer: Optional[str] = None) -> dict:
        """生成请求头"""
        headers = {
            "User-Agent": self.get_random_ua(),
            "Accept": "application/json, text/plain, text/html, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        if referer:
            headers["Referer"] = referer
        return headers

    def is_captcha_page(self, text: str) -> bool:
        """检测验证码页面"""
        captcha_keywords = [
            "验证码", "captcha", "人机验证", "滑块", "极验",
            "请输入验证码", "请完成验证", "robot check",
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in captcha_keywords)

    def is_blocked(self, status_code: int, text: str = "") -> bool:
        """检测是否被封禁"""
        # 403/429 通常是反爬响应
        if status_code in (403, 429):
            return True
        # 503 维护
        if status_code == 503:
            return True
        # 检测文本中的封禁关键词
        blocked_keywords = ["访问频繁", "请求过快", "已被封禁", "请稍后再试", "rate limit"]
        return any(kw in text for kw in blocked_keywords)


class ProxyMiddleware:
    """代理池中间件 (可选, 需要付费代理时启用)"""

    def __init__(self, proxy_pool: str = ""):
        self.proxies = [p.strip() for p in proxy_pool.split(",") if p.strip()] if proxy_pool else []

    def get_random_proxy(self) -> Optional[str]:
        """获取随机代理"""
        if not self.proxies:
            return None
        return random.choice(self.proxies)


class RetryMiddleware:
    """重试中间件 - 指数退避"""

    def __init__(self, max_retries: int = 3, base_delay: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def retry(self, func, *args, **kwargs):
        """执行函数, 失败时指数退避重试"""
        for attempt in range(self.max_retries):
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_retries} attempts failed: {e}")
                    raise
