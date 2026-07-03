"""
LexPrime Auth 安全工具
2026-06-29 · Track A Phase 4 W2

提供:
- bcrypt 密码哈希 / 验证
- JWT access_token / refresh_token 签发
- Token 哈希 (持久化到 DB 用, 不存明文)
- 通用 decode + 异常类型

设计原则:
- 密码字段绝不返回
- Token 持久化存 hash (跟密码一样原则)
- 默认值从 settings 读, 单元测试可 monkeypatch
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
import jwt
from loguru import logger

from core.config import settings


# ========== 异常类型 ==========
class AuthError(Exception):
    """认证业务异常基类

    子类用类属性 code 定义错误码, 不要在 __init__ 里覆盖 (会 break 类属性查找)
    """

    code: str = "auth_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
        # 注: self.code 通过类属性查找, 不写到实例 dict (子类专属 code 才生效)


class InvalidCredentialsError(AuthError):
    code = "invalid_credentials"


class TokenInvalidError(AuthError):
    code = "token_invalid"


class TokenExpiredError(AuthError):
    code = "token_expired"


class AccountLockedError(AuthError):
    code = "account_locked"


# ========== 密码 ==========
def hash_password(plain_password: str) -> str:
    """
    bcrypt 哈希密码

    - 自动盐 (bcrypt 内置)
    - cost factor 走 settings.auth_bcrypt_rounds (默认 12)
    - 返回 str (跟 SQLAlchemy String(255) 兼容)
    """
    if not plain_password:
        raise ValueError("password must not be empty")
    rounds = settings.auth_bcrypt_rounds
    salt = bcrypt.gensalt(rounds=rounds)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed: str) -> bool:
    """
    bcrypt 验证密码
    - 哈希格式错 (DB 被破坏) 返回 False 不抛异常, 防止泄露信息
    """
    if not plain_password or not hashed:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        # bcrypt.checkpw 在 hash 格式错误时抛 ValueError
        return False


# ========== Token 哈希 (持久化用) ==========
def hash_token(token: str) -> str:
    """
    对 token 做 SHA-256 哈希, 用于持久化到 auth_tokens.token_hash
    - 跟密码一样: 不存明文
    - SHA-256 够用: token 自身有 256+ bits 熵, 不需要 bcrypt 这种慢算法
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ========== JWT 签发 / 验证 ==========
def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_access_token(
    user_id: int,
    role: str = "lawyer",
    extra_claims: Optional[dict[str, Any]] = None,
) -> tuple[str, int]:
    """
    签发 access token

    返回: (token, expires_in_seconds)
    - 15min TTL (settings.auth_access_token_ttl_min)
    - claims: sub (user_id), role, iat, exp, jti, type='access'
    """
    now = _now()
    ttl = timedelta(minutes=settings.auth_access_token_ttl_min)
    exp = now + ttl
    jti = secrets.token_urlsafe(16)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": jti,
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(
        payload,
        settings.auth_secret_key,
        algorithm=settings.auth_jwt_algorithm,
    )
    return token, int(ttl.total_seconds())


def create_refresh_token(
    user_id: int,
    extra_claims: Optional[dict[str, Any]] = None,
) -> tuple[str, int]:
    """
    签发 refresh token

    返回: (token, expires_in_seconds)
    - 7d TTL (settings.auth_refresh_token_ttl_days)
    - claims: sub (user_id), iat, exp, jti, type='refresh'
    - 单次使用: 刷新时轮转 (revoke old + issue new), 防 token 重放
    """
    now = _now()
    ttl = timedelta(days=settings.auth_refresh_token_ttl_days)
    exp = now + ttl
    jti = secrets.token_urlsafe(32)  # refresh 用更长 jti

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": jti,
        "type": "refresh",
    }
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(
        payload,
        settings.auth_secret_key,
        algorithm=settings.auth_jwt_algorithm,
    )
    return token, int(ttl.total_seconds())


def decode_token(token: str, expected_type: Optional[str] = None) -> dict[str, Any]:
    """
    验证 + 解码 JWT

    Raises:
    - TokenInvalidError: 签名错 / 格式错 / type 不匹配
    - TokenExpiredError: 已过期
    """
    if not token:
        raise TokenInvalidError("token is empty")
    try:
        payload = jwt.decode(
            token,
            settings.auth_secret_key,
            algorithms=[settings.auth_jwt_algorithm],
        )
    except jwt.ExpiredSignatureError as e:
        raise TokenExpiredError(f"token expired: {e}") from e
    except jwt.InvalidTokenError as e:
        raise TokenInvalidError(f"invalid token: {e}") from e

    if expected_type and payload.get("type") != expected_type:
        raise TokenInvalidError(
            f"expected token type '{expected_type}', got '{payload.get('type')}'"
        )

    return payload


def extract_user_id_from_payload(payload: dict[str, Any]) -> int:
    """从 payload['sub'] 解析 user_id (JWT 标准 sub 是字符串)"""
    sub = payload.get("sub")
    if not sub:
        raise TokenInvalidError("token missing 'sub' claim")
    try:
        return int(sub)
    except (TypeError, ValueError) as e:
        raise TokenInvalidError(f"invalid sub claim: {sub}") from e


# ========== CSRF 防护 ==========
def generate_csrf_token() -> str:
    """
    生成 CSRF token
    - 使用 secrets.token_urlsafe 生成高熵随机字符串
    - 长度 32 字符，约 192 bits 熵
    """
    return secrets.token_urlsafe(32)


def validate_csrf_token(token: Optional[str]) -> bool:
    """
    验证 CSRF token 格式
    - 检查非空且长度合理
    - 实际验证需要结合 session 存储的 token 进行比对
    """
    if not token:
        return False
    if len(token) < 16 or len(token) > 128:
        return False
    try:
        decoded = token.replace("-", "+").replace("_", "/")
        if len(decoded) % 4 != 0:
            decoded += "=" * (4 - len(decoded) % 4)
        import base64
        base64.b64decode(decoded)
        return True
    except Exception:
        return False


# ========== 自检 (模块加载时跑一次, 早失败) ==========
def _self_check() -> None:
    """确保 hash/verify 闭环工作"""
    sample = "lexprime-self-check-password"
    h = hash_password(sample)
    assert h.startswith("$2"), f"bcrypt hash format unexpected: {h[:5]}"
    assert verify_password(sample, h), "bcrypt verify self-check failed"
    assert not verify_password("wrong", h), "bcrypt should reject wrong password"

    csrf_token = generate_csrf_token()
    assert len(csrf_token) >= 32, f"CSRF token too short: {len(csrf_token)}"
    assert validate_csrf_token(csrf_token), "CSRF token validation failed"
    assert not validate_csrf_token(None), "CSRF should reject None"
    assert not validate_csrf_token(""), "CSRF should reject empty"

    logger.debug("auth.security self-check OK")


_self_check()