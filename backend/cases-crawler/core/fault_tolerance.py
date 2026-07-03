"""
容错机制模块
2026-07-03

功能:
1. 熔断器模式 (Circuit Breaker)
2. 重试机制 (Retry with backoff)
3. 降级策略 (Fallback)
4. 超时控制 (Timeout)
"""
import time
import asyncio
import functools
import threading
from enum import Enum
from typing import Callable, Any, Optional, Type, Tuple
from loguru import logger


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """熔断器模式实现

    状态流转:
    CLOSED → 失败次数达到阈值 → OPEN
    OPEN → 冷却时间结束 → HALF_OPEN
    HALF_OPEN → 成功 → CLOSED
    HALF_OPEN → 失败 → OPEN
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_limit: int = 3,
        expected_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_limit = half_open_limit
        self.expected_exceptions = expected_exceptions

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure_time > self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    logger.info(
                        f"Circuit breaker '{self.name}': OPEN -> HALF_OPEN"
                    )
            return self._state

    def call(self, func: Callable, *args, **kwargs) -> Any:
        state = self.state

        if state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is open"
            )

        if state == CircuitState.HALF_OPEN:
            with self._lock:
                if self._success_count >= self.half_open_limit:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    logger.info(
                        f"Circuit breaker '{self.name}': HALF_OPEN -> CLOSED"
                    )
                    state = CircuitState.CLOSED

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exceptions as e:
            self._on_failure()
            raise

    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        state = self.state

        if state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is open"
            )

        if state == CircuitState.HALF_OPEN:
            with self._lock:
                if self._success_count >= self.half_open_limit:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    logger.info(
                        f"Circuit breaker '{self.name}': HALF_OPEN -> CLOSED"
                    )
                    state = CircuitState.CLOSED

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exceptions as e:
            self._on_failure()
            raise

    def _on_success(self):
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.half_open_limit:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    logger.info(
                        f"Circuit breaker '{self.name}': HALF_OPEN -> CLOSED (success)"
                    )
            else:
                self._failure_count = max(0, self._failure_count - 1)

    def _on_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker '{self.name}': HALF_OPEN -> OPEN"
                )
            elif (
                self._state == CircuitState.CLOSED
                and self._failure_count >= self.failure_threshold
            ):
                self._state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker '{self.name}': CLOSED -> OPEN "
                    f"(failures: {self._failure_count})"
                )

    def reset(self):
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = 0.0

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "last_failure_time": self._last_failure_time,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
            }


class CircuitBreakerOpenError(Exception):
    """熔断器打开状态异常"""
    pass


class RetryConfig:
    """重试配置"""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        retry_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.retry_exceptions = retry_exceptions


def retry(config: Optional[RetryConfig] = None):
    """重试装饰器 (同步)"""
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            delay = config.initial_delay

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.retry_exceptions as e:
                    last_exception = e
                    if attempt < config.max_attempts - 1:
                        actual_delay = delay
                        if config.jitter:
                            actual_delay = delay * (0.5 + 0.5 * __import__('random').random())

                        logger.warning(
                            f"Retry attempt {attempt + 1}/{config.max_attempts} "
                            f"for {func.__name__}: {str(e)}, "
                            f"retrying in {actual_delay:.2f}s"
                        )
                        time.sleep(min(actual_delay, config.max_delay))
                        delay *= config.backoff_factor
                        delay = min(delay, config.max_delay)

            raise last_exception

        return wrapper

    return decorator


def async_retry(config: Optional[RetryConfig] = None):
    """重试装饰器 (异步)"""
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            import random
            last_exception = None
            delay = config.initial_delay

            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except config.retry_exceptions as e:
                    last_exception = e
                    if attempt < config.max_attempts - 1:
                        actual_delay = delay
                        if config.jitter:
                            actual_delay = delay * (0.5 + 0.5 * random.random())

                        logger.warning(
                            f"Async retry attempt {attempt + 1}/{config.max_attempts} "
                            f"for {func.__name__}: {str(e)}, "
                            f"retrying in {actual_delay:.2f}s"
                        )
                        await asyncio.sleep(min(actual_delay, config.max_delay))
                        delay *= config.backoff_factor
                        delay = min(delay, config.max_delay)

            raise last_exception

        return wrapper

    return decorator


class FallbackStrategy:
    """降级策略"""

    def __init__(self, fallback_func: Callable, name: str = "default"):
        self.fallback_func = fallback_func
        self.name = name
        self._fallback_count = 0
        self._lock = threading.Lock()

    def execute_with_fallback(self, primary_func: Callable, *args, **kwargs) -> Any:
        try:
            return primary_func(*args, **kwargs)
        except Exception as e:
            with self._lock:
                self._fallback_count += 1
            logger.warning(
                f"Fallback triggered for '{self.name}': {str(e)}"
            )
            return self.fallback_func(*args, **kwargs)

    async def execute_with_fallback_async(
        self, primary_func: Callable, *args, **kwargs
    ) -> Any:
        try:
            return await primary_func(*args, **kwargs)
        except Exception as e:
            with self._lock:
                self._fallback_count += 1
            logger.warning(
                f"Async fallback triggered for '{self.name}': {str(e)}"
            )
            return self.fallback_func(*args, **kwargs)

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "name": self.name,
                "fallback_count": self._fallback_count,
            }


class TimeoutGuard:
    """超时控制"""

    def __init__(self, timeout_seconds: float = 30.0):
        self.timeout_seconds = timeout_seconds

    def execute_with_timeout(self, func: Callable, *args, **kwargs) -> Any:
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=self.timeout_seconds)
            except concurrent.futures.TimeoutError:
                future.cancel()
                raise TimeoutError(
                    f"Operation timed out after {self.timeout_seconds}s"
                )

    async def execute_with_timeout_async(
        self, func: Callable, *args, **kwargs
    ) -> Any:
        try:
            return await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Async operation timed out after {self.timeout_seconds}s"
            )


class FaultToleranceManager:
    """容错管理器 - 组合所有容错机制"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_manager()
        return cls._instance

    def _init_manager(self):
        self._circuit_breakers: dict = {}
        self._fallback_strategies: dict = {}
        self._lock = threading.Lock()

    def get_circuit_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ) -> CircuitBreaker:
        with self._lock:
            if name not in self._circuit_breakers:
                self._circuit_breakers[name] = CircuitBreaker(
                    name=name,
                    failure_threshold=failure_threshold,
                    recovery_timeout=recovery_timeout,
                )
            return self._circuit_breakers[name]

    def get_fallback_strategy(
        self, name: str, fallback_func: Callable
    ) -> FallbackStrategy:
        with self._lock:
            if name not in self._fallback_strategies:
                self._fallback_strategies[name] = FallbackStrategy(
                    fallback_func=fallback_func,
                    name=name,
                )
            return self._fallback_strategies[name]

    def get_all_stats(self) -> dict:
        with self._lock:
            return {
                "circuit_breakers": {
                    name: cb.get_stats()
                    for name, cb in self._circuit_breakers.items()
                },
                "fallback_strategies": {
                    name: fs.get_stats()
                    for name, fs in self._fallback_strategies.items()
                },
            }


fault_tolerance = FaultToleranceManager()
