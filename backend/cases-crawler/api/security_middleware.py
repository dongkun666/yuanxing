"""
安全加固中间件
2026-07-03

功能:
1. 请求速率限制 (Rate Limiting) - 基于 IP 的内存令牌桶
2. 输入验证和过滤 - XSS/SQL 注入字符过滤
3. 安全头添加 - 各种安全响应头
4. 异常信息脱敏 - 生产环境隐藏详细错误信息
"""
import time
import re
import threading
from collections import defaultdict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger

from core.config import settings


class TokenBucket:
    """令牌桶速率限制器"""

    def __init__(self, capacity: float, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = threading.Lock()

    def consume(self, tokens: float = 1.0) -> bool:
        with self._lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.refill_rate
            )
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False


class RateLimiter:
    """基于 IP 的速率限制器"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_limiter()
        return cls._instance

    def _init_limiter(self):
        self.buckets = defaultdict(self._create_bucket)
        self._global_bucket = TokenBucket(
            capacity=getattr(settings, 'rate_limit_global_capacity', 1000),
            refill_rate=getattr(settings, 'rate_limit_global_rate', 500)
        )
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_expired,
            daemon=True
        )
        self._cleanup_thread.start()

    def _create_bucket(self) -> TokenBucket:
        return TokenBucket(
            capacity=getattr(settings, 'rate_limit_per_ip_capacity', 60),
            refill_rate=getattr(settings, 'rate_limit_per_ip_rate', 30)
        )

    def is_allowed(self, client_ip: str) -> tuple:
        if not self._global_bucket.consume():
            return False, "global_rate_limit_exceeded"

        bucket = self.buckets[client_ip]
        if not bucket.consume():
            return False, "ip_rate_limit_exceeded"

        return True, None

    def _cleanup_expired(self):
        while True:
            time.sleep(300)
            try:
                with self._lock:
                    now = time.time()
                    expired = [
                        ip for ip, bucket in self.buckets.items()
                        if now - bucket.last_refill > 600
                    ]
                    for ip in expired:
                        del self.buckets[ip]
            except Exception:
                pass


rate_limiter = RateLimiter()


XSS_PATTERNS = [
    re.compile(r'<script[^>]*>', re.IGNORECASE),
    re.compile(r'javascript:', re.IGNORECASE),
    re.compile(r'on\w+\s*=', re.IGNORECASE),
    re.compile(r'<iframe[^>]*>', re.IGNORECASE),
    re.compile(r'<img[^>]+on\w+', re.IGNORECASE),
    re.compile(r'eval\s*\(', re.IGNORECASE),
    re.compile(r'<svg[^>]*>', re.IGNORECASE),
]

SQL_INJECTION_PATTERNS = [
    re.compile(r"('|--|;)\s*(drop|delete|insert|update|truncate)\s+", re.IGNORECASE),
    re.compile(r"\bunion\s+select\b", re.IGNORECASE),
    re.compile(r"\bor\s+['\"]?1['\"]?\s*=\s*['\"]?1['\"]?", re.IGNORECASE),
    re.compile(r"\bsleep\s*\(", re.IGNORECASE),
    re.compile(r"\bbenchmark\s*\(", re.IGNORECASE),
]


def sanitize_input(value: str) -> str:
    """输入过滤 - 移除潜在危险字符"""
    if not isinstance(value, str):
        return value

    sanitized = value

    for pattern in XSS_PATTERNS:
        sanitized = pattern.sub('', sanitized)

    for pattern in SQL_INJECTION_PATTERNS:
        sanitized = pattern.sub('', sanitized)

    return sanitized


def add_security_headers(response: JSONResponse) -> JSONResponse:
    """添加安全响应头"""
    security_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        ),
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    }

    for header, value in security_headers.items():
        if header not in response.headers:
            response.headers[header] = value

    response.headers.pop("X-Powered-By", None)

    return response


def sanitize_error_message(error: Exception) -> str:
    """异常信息脱敏"""
    debug_mode = getattr(settings, 'api_debug', False)

    if debug_mode:
        return str(error)

    generic_messages = {
        "400": "请求参数错误",
        "401": "未授权访问",
        "403": "禁止访问",
        "404": "资源未找到",
        "422": "请求格式错误",
        "429": "请求过于频繁",
        "500": "服务器内部错误",
        "502": "网关错误",
        "503": "服务不可用",
        "504": "网关超时",
    }

    if isinstance(error, HTTPException):
        status_str = str(error.status_code)
        return generic_messages.get(status_str, "请求处理失败")

    return "服务器内部错误，请稍后重试"


async def security_middleware(request: Request, call_next):
    """FastAPI 安全加固中间件"""
    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    path = request.url.path

    try:
        allowed, reason = rate_limiter.is_allowed(client_ip)
        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                extra={
                    "client_ip": client_ip,
                    "method": method,
                    "path": path,
                    "reason": reason,
                },
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "too_many_requests",
                    "message": "请求过于频繁，请稍后再试",
                    "retry_after": 60,
                },
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)

        if hasattr(response, 'headers'):
            response = add_security_headers(response)

        return response

    except HTTPException as e:
        sanitized_msg = sanitize_error_message(e)
        logger.warning(
            "http_exception",
            extra={
                "client_ip": client_ip,
                "method": method,
                "path": path,
                "status_code": e.status_code,
                "original_detail": str(e.detail),
            },
        )
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": "request_error",
                "message": sanitized_msg,
            },
        )

    except Exception as e:
        sanitized_msg = sanitize_error_message(e)
        logger.error(
            "unhandled_exception_sanitized",
            extra={
                "client_ip": client_ip,
                "method": method,
                "path": path,
                "exception_type": type(e).__name__,
                "exception_detail": str(e),
            },
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": sanitized_msg,
            },
        )
