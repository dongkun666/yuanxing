"""
LexPrime Auth FastAPI 依赖注入
2026-06-29 · Track A Phase 4 W2

提供:
- get_current_user: 必须有有效 access_token, 否则 401
- get_optional_user: 可选, 用于公共页面但登录态有更好体验
- csrf_protect: CSRF 防护依赖

注: refresh endpoint 不走这里, 走自己的链路 (refresh_token 单独验证)
"""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth.db import get_db
from auth.models import User
from auth.security import (
    AuthError,
    TokenExpiredError,
    TokenInvalidError,
    decode_token,
    extract_user_id_from_payload,
    generate_csrf_token,
    validate_csrf_token,
)


async def _resolve_user_from_bearer(
    authorization: Optional[str], db: AsyncSession
) -> Optional[User]:
    """Bearer token → User (含 profile via selectinload)"""
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    if not token:
        return None

    try:
        payload = decode_token(token, expected_type="access")
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "token_expired", "message": "access token expired"},
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )
    except TokenInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "token_invalid", "message": "invalid access token"},
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )
    except AuthError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "auth_error", "message": "authentication failed"},
        )

    user_id = extract_user_id_from_payload(payload)
    # selectinload profile 避免后续跨 session lazy load
    result = await db.execute(
        select(User).options(selectinload(User.profile)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        # token 有效但 user 已被删除 (admin 删号 / 数据迁移)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "user_not_found", "message": "user no longer exists"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "user_inactive", "message": "user account is inactive"},
        )
    return user


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    强制要求有效 access_token, 否则 401
    """
    user = await _resolve_user_from_bearer(authorization, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "missing_token", "message": "Authorization header missing or malformed"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_optional_user(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    可选 user — 有 token 就解析, 没 token 返回 None
    用于: 首页 (登录后看到名字) / 公共 API (登录后更精确)
    """
    if not authorization:
        return None
    return await _resolve_user_from_bearer(authorization, db)


async def get_current_admin(
    user: User = Depends(get_current_user),
) -> User:
    """要求 role == admin, 否则 403 (W4 审计日志 / admin panel 用)"""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "admin_required", "message": "admin role required"},
        )
    return user


# ========== CSRF 防护依赖 ==========
async def csrf_protect(
    x_csrf_token: Optional[str] = Header(default=None),
) -> str:
    """
    CSRF 防护依赖
    - 验证请求头中的 X-CSRF-Token
    - 对于有状态请求(POST/PUT/DELETE)必须提供有效的 CSRF token
    - 返回验证通过的 token 供后续使用
    """
    if not x_csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "csrf_missing", "message": "CSRF token missing"},
        )

    if not validate_csrf_token(x_csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "csrf_invalid", "message": "CSRF token invalid"},
        )

    return x_csrf_token


async def get_csrf_token(
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """
    获取 CSRF token (用于前端初始化)
    - 需要先登录
    - 返回新生成的 CSRF token
    """
    token = generate_csrf_token()
    return {"csrf_token": token}