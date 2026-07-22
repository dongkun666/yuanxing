"""
限流模块单元测试
测试 InMemorySlidingWindowLimiter、RateLimitDecision、辅助函数
"""
import time
import pytest

from auth.ratelimit import (
    InMemorySlidingWindowLimiter,
    RateLimitDecision,
    rate_limit_check,
    get_limiter,
    login_key_by_ip,
    login_key_by_user,
    register_key_by_ip,
    totp_key_by_user,
    email_verify_key_by_ip,
    license_upload_key_by_user,
)


class TestRateLimitDecision:
    """RateLimitDecision 数据类测试"""

    def test_allowed_decision(self):
        """允许的决策"""
        d = RateLimitDecision(
            allowed=True,
            current_count=1,
            limit=5,
            reset_at=time.time() + 60,
            retry_after=0,
        )
        assert d.allowed is True
        assert d.current_count == 1
        assert d.limit == 5
        assert d.retry_after == 0

    def test_denied_decision(self):
        """拒绝的决策"""
        d = RateLimitDecision(
            allowed=False,
            current_count=5,
            limit=5,
            reset_at=time.time() + 30,
            retry_after=31,
        )
        assert d.allowed is False
        assert d.current_count == 5
        assert d.retry_after > 0


class TestInMemorySlidingWindowLimiter:
    """InMemorySlidingWindowLimiter 测试"""

    def test_init(self):
        """初始化"""
        limiter = InMemorySlidingWindowLimiter()
        assert limiter._buckets is not None
        assert limiter._lock is not None

    def test_check_and_record_allow(self):
        """允许请求 - 窗口内未满"""
        limiter = InMemorySlidingWindowLimiter()
        key = "test_key"
        limit = 5
        window = 60

        for i in range(limit):
            d = limiter.check_and_record(key, limit, window)
            assert d.allowed is True
            assert d.current_count == i + 1
            assert d.retry_after == 0

    def test_check_and_record_deny(self):
        """拒绝请求 - 窗口已满"""
        limiter = InMemorySlidingWindowLimiter()
        key = "test_key"
        limit = 3
        window = 60

        for _ in range(limit):
            limiter.check_and_record(key, limit, window)

        d = limiter.check_and_record(key, limit, window)
        assert d.allowed is False
        assert d.current_count == limit
        assert d.retry_after > 0

    def test_multiple_keys_isolated(self):
        """不同 key 之间隔离"""
        limiter = InMemorySlidingWindowLimiter()
        limit = 3
        window = 60

        for _ in range(limit):
            limiter.check_and_record("key1", limit, window)

        d1 = limiter.check_and_record("key1", limit, window)
        assert d1.allowed is False

        d2 = limiter.check_and_record("key2", limit, window)
        assert d2.allowed is True
        assert d2.current_count == 1

    def test_reset_all(self):
        """重置所有限流"""
        limiter = InMemorySlidingWindowLimiter()
        key = "test_key"
        limit = 3
        window = 60

        for _ in range(limit):
            limiter.check_and_record(key, limit, window)

        assert limiter.check_and_record(key, limit, window).allowed is False

        limiter.reset()

        assert limiter.check_and_record(key, limit, window).allowed is True

    def test_reset_specific_key(self):
        """重置特定 key 的限流"""
        limiter = InMemorySlidingWindowLimiter()
        limit = 3
        window = 60

        for _ in range(limit):
            limiter.check_and_record("key1", limit, window)
            limiter.check_and_record("key2", limit, window)

        limiter.reset("key1")

        assert limiter.check_and_record("key1", limit, window).allowed is True
        assert limiter.check_and_record("key2", limit, window).allowed is False

    def test_empty_key_reset_no_error(self):
        """重置不存在的 key 不报错"""
        limiter = InMemorySlidingWindowLimiter()
        limiter.reset("nonexistent_key")


class TestKeyGenerators:
    """限流 key 生成函数测试"""

    def test_login_key_by_ip(self):
        assert login_key_by_ip("192.168.1.1") == "login_ip:192.168.1.1"

    def test_login_key_by_user(self):
        assert login_key_by_user(42) == "login_user:42"

    def test_register_key_by_ip(self):
        assert register_key_by_ip("10.0.0.1") == "register_ip:10.0.0.1"

    def test_totp_key_by_user(self):
        assert totp_key_by_user(100) == "totp_user:100"

    def test_email_verify_key_by_ip(self):
        assert email_verify_key_by_ip("127.0.0.1") == "email_verify_ip:127.0.0.1"

    def test_license_upload_key_by_user(self):
        assert license_upload_key_by_user(999) == "license_user:999"


class TestModuleLevelFunctions:
    """模块级函数测试"""

    def test_get_limiter_returns_singleton(self):
        """get_limiter 返回单例"""
        l1 = get_limiter()
        l2 = get_limiter()
        assert l1 is l2

    def test_rate_limit_check_wrapper(self):
        """rate_limit_check 便捷函数"""
        limiter = get_limiter()
        limiter.reset("test_wrapper")

        d1 = rate_limit_check("test_wrapper", limit=2, window_seconds=60)
        assert d1.allowed is True

        d2 = rate_limit_check("test_wrapper", limit=2, window_seconds=60)
        assert d2.allowed is True

        d3 = rate_limit_check("test_wrapper", limit=2, window_seconds=60)
        assert d3.allowed is False
