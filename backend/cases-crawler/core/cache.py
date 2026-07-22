"""
LexPrime 缓存模块
支持 Redis 和内存缓存两种模式
2026-06-28
"""
import json
import time
import hashlib
from typing import Any, Optional, Callable, TypeVar
from functools import wraps
from loguru import logger

from core.config import settings

T = TypeVar("T")


class MemoryCache:
    """内存缓存实现 - 用于开发环境或 Redis 不可用时"""

    def __init__(self):
        self._cache: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, expires_at = self._cache[key]
            if time.time() < expires_at:
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        expires_at = time.time() + ttl
        self._cache[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        self._cache.clear()

    def exists(self, key: str) -> bool:
        if key in self._cache:
            _, expires_at = self._cache[key]
            if time.time() < expires_at:
                return True
            else:
                del self._cache[key]
        return False


class RedisCache:
    """Redis 缓存实现 - 用于生产环境"""

    def __init__(self):
        self._client = None
        self._connected = False

    def _get_client(self):
        if self._client is None or not self._connected:
            try:
                import redis
                if settings.redis_url:
                    self._client = redis.Redis.from_url(settings.redis_url)
                else:
                    self._client = redis.Redis(
                        host=settings.redis_host,
                        port=settings.redis_port,
                        password=settings.redis_password,
                        db=settings.redis_db,
                        decode_responses=True,
                    )
                self._client.ping()
                self._connected = True
                logger.info("Redis 缓存连接成功")
            except ImportError:
                logger.warning("redis 库未安装，使用内存缓存")
                self._connected = False
            except Exception as e:
                logger.warning(f"Redis 连接失败: {e}，使用内存缓存")
                self._connected = False
        return self._client

    def get(self, key: str) -> Optional[Any]:
        client = self._get_client()
        if not client:
            return None
        try:
            value = client.get(key)
            if value is not None:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        client = self._get_client()
        if not client:
            return
        try:
            client.set(key, json.dumps(value), ex=ttl)
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    def delete(self, key: str) -> None:
        client = self._get_client()
        if not client:
            return
        try:
            client.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error: {e}")

    def clear(self) -> None:
        client = self._get_client()
        if not client:
            return
        try:
            client.flushdb()
        except Exception as e:
            logger.error(f"Redis clear error: {e}")

    def exists(self, key: str) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            return client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False


class Cache:
    """统一缓存接口 - 自动选择 Redis 或内存缓存"""

    def __init__(self):
        self._redis_cache = RedisCache()
        self._memory_cache = MemoryCache()

    @property
    def _backend(self):
        if self._redis_cache._connected:
            return self._redis_cache
        return self._memory_cache

    def get(self, key: str) -> Optional[Any]:
        return self._backend.get(key)

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        if ttl is None:
            ttl = settings.cache_default_ttl
        self._backend.set(key, value, ttl)

    def delete(self, key: str) -> None:
        self._backend.delete(key)

    def clear(self) -> None:
        self._backend.clear()

    def exists(self, key: str) -> bool:
        return self._backend.exists(key)

    def cached(
        self,
        key_prefix: str,
        ttl: int = None,
        key_builder: Optional[Callable[..., str]] = None,
    ):
        """缓存装饰器"""

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> T:
                cache_key = _build_cache_key(key_prefix, args, kwargs, key_builder)
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"缓存命中: {cache_key}")
                    return cached_result

                result = await func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                logger.debug(f"缓存设置: {cache_key}")
                return result

            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> T:
                cache_key = _build_cache_key(key_prefix, args, kwargs, key_builder)
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"缓存命中: {cache_key}")
                    return cached_result

                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                logger.debug(f"缓存设置: {cache_key}")
                return result

            import asyncio

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator


def _build_cache_key(
    key_prefix: str,
    args: tuple,
    kwargs: dict,
    key_builder: Optional[Callable[..., str]],
) -> str:
    """构建缓存键"""
    if key_builder:
        return f"{key_prefix}:{key_builder(*args, **kwargs)}"

    key_parts = []
    for arg in args:
        key_parts.append(str(arg))
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={v}")

    key_suffix = "-".join(key_parts)
    if len(key_suffix) > 200:
        key_suffix = hashlib.md5(key_suffix.encode()).hexdigest()

    return f"{key_prefix}:{key_suffix}"


cache = Cache()