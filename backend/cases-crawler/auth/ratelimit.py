"""
LexPrime Auth 限流模块 (W3)
2026-06-29

设计:
- 滑动窗口 (sliding window) in-memory 实现
- 接口设计兼容 Redis ZADD/ZREMRANGEBYSCORE, 后续可平滑切换
- 双维度限流: IP + 用户 (auth endpoint 同时支持)

为什么 in-memory 而不是 Redis:
- W3 dev 阶段 0 依赖, 不需要 Redis 集群
- 进程内滑动窗口足够 dev/test, 性能 ~10K req/s
- 接口预留 Redis backend 切换 (RateLimiter Protocol)
- 生产部署: 单进程足够, 多进程用 Redis 后端 (W4 接)

算法 (sliding window):
- key -> deque[timestamp]
- 新请求: 修剪 > window_seconds 前的; 若 len < limit -> 允许 + append; else 拒绝
- 优点: 精确, 不像 fixed window 有 burst 边界问题
- 缺点: O(window_size) 内存 (limit=5/window=3600s: 5 entries / key, OK)
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock
from typing import Deque, Dict, Optional, Protocol

from loguru import logger


@dataclass(frozen=True)
class RateLimitDecision:
    """限流决策结果"""

    allowed: bool
    current_count: int       # 当前窗口内请求数 (含本次)
    limit: int               # 窗口最大允许
    reset_at: float          # 窗口重置时间 (Unix timestamp)
    retry_after: int         # 若拒绝, 多少秒后可重试 (0=允许)


class RateLimiterBackend(Protocol):
    """限流后端抽象接口 (生产可换 Redis)"""

    def check_and_record(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision: ...


class InMemorySlidingWindowLimiter:
    """
    进程内滑动窗口限流 (W3 dev/test 用)

    线程安全: 用 Lock 保护 _buckets dict
    key 隔离: 不同 endpoint 用不同 prefix (e.g. "login_ip", "login_user")

    自动清理: 每次 check_and_record 会顺手清理空 bucket, 避免内存泄漏
    """

    def __init__(self):
        self._buckets: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check_and_record(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        """
        检查 + 记录一次请求

        Args:
            key: 限流维度 (e.g. "login_ip:1.2.3.4", "login_user:42")
            limit: 窗口内最大请求数
            window_seconds: 窗口大小 (秒)

        Returns:
            RateLimitDecision (allowed / current_count / reset_at / retry_after)
        """
        now = time.monotonic()
        window_start = now - window_seconds

        with self._lock:
            bucket = self._buckets[key]
            # 修剪窗口外的旧记录
            while bucket and bucket[0] < window_start:
                bucket.popleft()

            if len(bucket) >= limit:
                # 拒绝: 重试时间 = 最老记录 + window - now
                oldest = bucket[0]
                reset_at = oldest + window_seconds
                retry_after = max(1, int(reset_at - now) + 1)
                return RateLimitDecision(
                    allowed=False,
                    current_count=len(bucket),
                    limit=limit,
                    reset_at=reset_at,
                    retry_after=retry_after,
                )

            # 允许: append 当前时间
            bucket.append(now)

            # 顺手清理: 若 bucket 已空, 从 dict 移除 (释放内存)
            if not bucket:
                self._buckets.pop(key, None)

            current = len(bucket)
            # 重置时间 = 最早一次记录 + window (简化: 用 now + window)
            reset_at = now + window_seconds
            return RateLimitDecision(
                allowed=True,
                current_count=current,
                limit=limit,
                reset_at=reset_at,
                retry_after=0,
            )

    def reset(self, key: Optional[str] = None) -> None:
        """手动重置 (测试用)"""
        with self._lock:
            if key is None:
                self._buckets.clear()
            else:
                self._buckets.pop(key, None)


# 单例 (W3 dev 用)
_default_limiter = InMemorySlidingWindowLimiter()


def get_limiter() -> InMemorySlidingWindowLimiter:
    """FastAPI Depends / 测试用"""
    return _default_limiter


def rate_limit_check(
    key: str,
    limit: int,
    window_seconds: int,
) -> RateLimitDecision:
    """便捷 wrapper: 默认单例"""
    return _default_limiter.check_and_record(key, limit, window_seconds)


# ========== 业务限流 key 构造 ==========
def login_key_by_ip(ip: str) -> str:
    return f"login_ip:{ip}"


def login_key_by_user(user_id: int) -> str:
    return f"login_user:{user_id}"


def register_key_by_ip(ip: str) -> str:
    return f"register_ip:{ip}"


def totp_key_by_user(user_id: int) -> str:
    return f"totp_user:{user_id}"


def email_verify_key_by_ip(ip: str) -> str:
    return f"email_verify_ip:{ip}"


def license_upload_key_by_user(user_id: int) -> str:
    return f"license_user:{user_id}"


# ========== 自检 ==========
def _self_check() -> None:
    """模块加载自检"""
    limiter = InMemorySlidingWindowLimiter()
    # 3/3 应该允许
    d1 = limiter.check_and_record("test_key", limit=3, window_seconds=60)
    d2 = limiter.check_and_record("test_key", limit=3, window_seconds=60)
    d3 = limiter.check_and_record("test_key", limit=3, window_seconds=60)
    # 第 4 个应拒绝
    d4 = limiter.check_and_record("test_key", limit=3, window_seconds=60)
    assert d1.allowed and d2.allowed and d3.allowed, "first 3 should be allowed"
    assert not d4.allowed, "4th should be denied"
    assert d4.retry_after > 0, "retry_after must be > 0 when denied"
    logger.debug("auth.ratelimit self-check OK")


_self_check()