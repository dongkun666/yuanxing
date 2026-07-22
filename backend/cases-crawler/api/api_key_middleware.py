"""
LexPrime API Key 中间件

功能:
- API Key 验证
- 调用频率限制
- 使用量统计
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, Optional
from loguru import logger

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


_rate_limit_store: Dict[str, list] = defaultdict(list)


_api_key_store: Dict[str, dict] = {}


def register_api_key(api_key: str, info: dict):
    _api_key_store[api_key] = info


def validate_api_key(api_key: str) -> Optional[dict]:
    if api_key in _api_key_store:
        return _api_key_store[api_key]
    return None


def check_rate_limit(api_key: str, limit: int = 60, window: int = 60) -> bool:
    now = time.time()
    window_start = now - window

    calls = _rate_limit_store[api_key]
    calls = [t for t in calls if t > window_start]
    _rate_limit_store[api_key] = calls

    if len(calls) >= limit:
        return False

    calls.append(now)
    return True


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """API Key 验证中间件

    验证 X-API-Key 请求头，进行频率限制和使用统计。
    仅对 /api/ 前缀的接口生效（排除 /api/developer 自身的管理接口）。
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if not path.startswith("/api/"):
            return await call_next(request)

        if path.startswith("/api/developer/"):
            return await call_next(request)

        if path in ("/api/health", "/api/docs", "/api/redoc", "/api/openapi.json"):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                bearer_token = auth_header[7:]
                if bearer_token.startswith("lp_"):
                    api_key = bearer_token

        if not api_key:
            return await call_next(request)

        key_info = validate_api_key(api_key)
        if key_info is None:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid API Key"},
            )

        rate_limit = key_info.get("rate_limit", 60)
        if not check_rate_limit(api_key, rate_limit):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": "60"},
            )

        request.state.api_key_info = key_info

        response = await call_next(request)

        try:
            if key_info.get("call_count") is not None:
                key_info["call_count"] = key_info["call_count"] + 1
        except Exception as e:
            logger.warning(f"Failed to update usage stats: {e}")

        return response


def init_mock_api_keys():
    mock_keys = [
        {
            "api_key": "lp_demo_key_001",
            "name": "Demo Key",
            "developer_id": 1,
            "scopes": ["cases", "contract", "doc_gen", "companies"],
            "rate_limit": 60,
            "call_count": 0,
        },
    ]
    for k in mock_keys:
        register_api_key(k["api_key"], k)
    logger.info(f"Initialized {len(mock_keys)} mock API keys")


init_mock_api_keys()
