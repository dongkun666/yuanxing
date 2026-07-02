"""
反爬中间件单元测试
测试 AntiBanMiddleware、RetryMiddleware、ProxyMiddleware
"""
import asyncio
import pytest
from unittest.mock import patch, AsyncMock

from crawlers.middlewares.anti_ban import (
    AntiBanMiddleware,
    RetryMiddleware,
    ProxyMiddleware,
)


class TestAntiBanMiddleware:
    """AntiBanMiddleware 测试"""

    def test_init_default_delay_range(self):
        """初始化默认延迟范围"""
        mw = AntiBanMiddleware()
        assert mw.delay_range == (1.0, 3.0)
        assert mw.request_count == 0

    def test_init_custom_delay_range(self):
        """初始化自定义延迟范围"""
        mw = AntiBanMiddleware(delay_range=(2.0, 5.0))
        assert mw.delay_range == (2.0, 5.0)

    def test_get_random_ua_fallback(self):
        """获取随机 UA - fake_useragent 失败时回退到 UA_POOL"""
        mw = AntiBanMiddleware()
        with patch("crawlers.middlewares.anti_ban.UserAgent", side_effect=Exception("mock error")):
            ua = mw.get_random_ua()
            assert ua in AntiBanMiddleware.UA_POOL

    def test_get_random_ua_success(self):
        """获取随机 UA - fake_useragent 成功"""
        mw = AntiBanMiddleware()
        mock_ua = "MockBrowser/1.0"
        with patch("crawlers.middlewares.anti_ban.UserAgent") as mock_ua_class:
            mock_instance = mock_ua_class.return_value
            mock_instance.random = mock_ua
            result = mw.get_random_ua()
            assert result == mock_ua

    @pytest.mark.asyncio
    async def test_delay_increments_count(self):
        """delay 方法增加请求计数"""
        mw = AntiBanMiddleware(delay_range=(0.01, 0.02))
        initial_count = mw.request_count
        await mw.delay()
        assert mw.request_count == initial_count + 1

    def test_get_headers_basic(self):
        """获取基础请求头"""
        mw = AntiBanMiddleware()
        with patch.object(mw, "get_random_ua", return_value="TestUA/1.0"):
            headers = mw.get_headers()
            assert headers["User-Agent"] == "TestUA/1.0"
            assert "Accept" in headers
            assert "Accept-Language" in headers
            assert "Referer" not in headers

    def test_get_headers_with_referer(self):
        """获取带 Referer 的请求头"""
        mw = AntiBanMiddleware()
        referer = "https://example.com"
        with patch.object(mw, "get_random_ua", return_value="TestUA/1.0"):
            headers = mw.get_headers(referer=referer)
            assert headers["Referer"] == referer

    def test_is_captcha_page_true(self):
        """检测验证码页面 - 命中关键词"""
        mw = AntiBanMiddleware()
        assert mw.is_captcha_page("请输入验证码以继续") is True
        assert mw.is_captcha_page("Please complete the CAPTCHA") is True
        assert mw.is_captcha_page("人机验证 滑块") is True

    def test_is_captcha_page_false(self):
        """检测验证码页面 - 未命中"""
        mw = AntiBanMiddleware()
        assert mw.is_captcha_page("正常页面内容") is False
        assert mw.is_captcha_page("") is False

    def test_is_blocked_by_status_code(self):
        """通过状态码检测封禁"""
        mw = AntiBanMiddleware()
        assert mw.is_blocked(403) is True
        assert mw.is_blocked(429) is True
        assert mw.is_blocked(503) is True
        assert mw.is_blocked(200) is False
        assert mw.is_blocked(404) is False

    def test_is_blocked_by_text(self):
        """通过文本内容检测封禁"""
        mw = AntiBanMiddleware()
        assert mw.is_blocked(200, "访问频繁，请稍后再试") is True
        assert mw.is_blocked(200, "rate limit exceeded") is True
        assert mw.is_blocked(200, "正常响应") is False


class TestRetryMiddleware:
    """RetryMiddleware 测试"""

    def test_init_default(self):
        """初始化默认参数"""
        mw = RetryMiddleware()
        assert mw.max_retries == 3
        assert mw.base_delay == 2.0

    def test_init_custom(self):
        """初始化自定义参数"""
        mw = RetryMiddleware(max_retries=5, base_delay=1.0)
        assert mw.max_retries == 5
        assert mw.base_delay == 1.0

    @pytest.mark.asyncio
    async def test_retry_success_first_attempt(self):
        """重试 - 第一次就成功"""
        mw = RetryMiddleware(max_retries=3, base_delay=0.01)
        mock_func = AsyncMock(return_value="success")
        result = await mw.retry(mock_func)
        assert result == "success"
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_success_after_retries(self):
        """重试 - 失败几次后成功"""
        mw = RetryMiddleware(max_retries=3, base_delay=0.01)
        call_count = 0

        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("temporary error")
            return "eventual success"

        result = await mw.retry(flaky_func)
        assert result == "eventual success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_all_failed(self):
        """重试 - 全部失败"""
        mw = RetryMiddleware(max_retries=3, base_delay=0.01)
        mock_func = AsyncMock(side_effect=RuntimeError("persistent error"))
        with pytest.raises(RuntimeError, match="persistent error"):
            await mw.retry(mock_func)
        assert mock_func.call_count == 3


class TestProxyMiddleware:
    """ProxyMiddleware 测试"""

    def test_init_empty_pool(self):
        """初始化空代理池"""
        mw = ProxyMiddleware()
        assert mw.proxies == []

    def test_init_with_pool(self):
        """初始化带代理池"""
        pool = "http://proxy1:8080, http://proxy2:8080 , http://proxy3:8080"
        mw = ProxyMiddleware(proxy_pool=pool)
        assert len(mw.proxies) == 3
        assert "http://proxy1:8080" in mw.proxies
        assert "http://proxy2:8080" in mw.proxies
        assert "http://proxy3:8080" in mw.proxies

    def test_get_random_proxy_empty(self):
        """空代理池返回 None"""
        mw = ProxyMiddleware()
        assert mw.get_random_proxy() is None

    def test_get_random_proxy_from_pool(self):
        """从代理池获取随机代理"""
        pool = "http://proxy1:8080,http://proxy2:8080"
        mw = ProxyMiddleware(proxy_pool=pool)
        proxy = mw.get_random_proxy()
        assert proxy in mw.proxies
