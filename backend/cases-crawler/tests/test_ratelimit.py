"""
ratelimit 滑动窗口测试 (W3)
2026-06-29
"""
import pytest

from auth.ratelimit import (
    InMemorySlidingWindowLimiter,
    RateLimitDecision,
    email_verify_key_by_ip,
    get_limiter,
    license_upload_key_by_user,
    login_key_by_ip,
    login_key_by_user,
    rate_limit_check,
    register_key_by_ip,
    totp_key_by_user,
)


class TestInMemorySlidingWindowLimiter:
    """in-memory 滑动窗口核心行为"""

    def test_under_limit_allows(self):
        """limit=3, 3 次请求都允许"""
        limiter = InMemorySlidingWindowLimiter()
        for i in range(3):
            d = limiter.check_and_record("k1", limit=3, window_seconds=60)
            assert d.allowed, f"request {i+1} should be allowed"
            assert d.current_count == i + 1
            assert d.limit == 3
            assert d.retry_after == 0

    def test_over_limit_denies(self):
        """limit=3, 第 4 次拒绝"""
        limiter = InMemorySlidingWindowLimiter()
        for _ in range(3):
            limiter.check_and_record("k2", limit=3, window_seconds=60)
        d4 = limiter.check_and_record("k2", limit=3, window_seconds=60)
        assert not d4.allowed
        assert d4.current_count == 3
        assert d4.limit == 3
        assert d4.retry_after > 0

    def test_separate_keys_isolated(self):
        """不同 key 互不干扰"""
        limiter = InMemorySlidingWindowLimiter()
        for _ in range(3):
            limiter.check_and_record("kA", limit=3, window_seconds=60)
        # kA 已满, kB 应仍可用
        d = limiter.check_and_record("kB", limit=3, window_seconds=60)
        assert d.allowed
        assert d.current_count == 1

    def test_window_expiry_releases(self):
        """窗口过期后重新可用"""
        limiter = InMemorySlidingWindowLimiter()
        # 用一个非常短的窗口 (1s) 测试
        for _ in range(2):
            limiter.check_and_record("k3", limit=2, window_seconds=1)
        d3 = limiter.check_and_record("k3", limit=2, window_seconds=1)
        assert not d3.allowed, "should deny when at limit"

        import time
        time.sleep(1.1)  # 等过窗口

        d4 = limiter.check_and_record("k3", limit=2, window_seconds=1)
        assert d4.allowed, "should allow after window expires"

    def test_reset_clears_bucket(self):
        """reset() 清空桶"""
        limiter = InMemorySlidingWindowLimiter()
        for _ in range(3):
            limiter.check_and_record("k4", limit=3, window_seconds=60)
        limiter.reset("k4")
        d = limiter.check_and_record("k4", limit=3, window_seconds=60)
        assert d.allowed
        assert d.current_count == 1

    def test_reset_all(self):
        """reset(None) 清空所有"""
        limiter = InMemorySlidingWindowLimiter()
        for _ in range(3):
            limiter.check_and_record("kA", limit=3, window_seconds=60)
            limiter.check_and_record("kB", limit=3, window_seconds=60)
        limiter.reset()
        d = limiter.check_and_record("kA", limit=3, window_seconds=60)
        assert d.allowed

    def test_decision_is_frozen_dataclass(self):
        """RateLimitDecision 是 frozen dataclass"""
        d = RateLimitDecision(allowed=True, current_count=1, limit=3, reset_at=0.0, retry_after=0)
        with pytest.raises(Exception):  # FrozenInstanceError
            d.allowed = False  # type: ignore[misc]


class TestRateLimitKeyFactories:
    """key 工厂函数"""

    def test_login_keys(self):
        assert login_key_by_ip("1.2.3.4") == "login_ip:1.2.3.4"
        assert login_key_by_user(42) == "login_user:42"

    def test_register_key(self):
        assert register_key_by_ip("1.2.3.4") == "register_ip:1.2.3.4"

    def test_totp_key(self):
        assert totp_key_by_user(42) == "totp_user:42"

    def test_email_verify_key(self):
        assert email_verify_key_by_ip("1.2.3.4") == "email_verify_ip:1.2.3.4"

    def test_license_key(self):
        assert license_upload_key_by_user(42) == "license_user:42"


class TestModuleLevelHelpers:
    """module-level 函数"""

    def test_get_limiter_singleton(self):
        l1 = get_limiter()
        l2 = get_limiter()
        assert l1 is l2, "get_limiter must return singleton"

    def test_rate_limit_check_uses_singleton(self):
        """rate_limit_check() 走单例"""
        get_limiter().reset("mod_level_key")
        for _ in range(5):
            d = rate_limit_check("mod_level_key", limit=5, window_seconds=60)
            assert d.allowed
        d6 = rate_limit_check("mod_level_key", limit=5, window_seconds=60)
        assert not d6.allowed