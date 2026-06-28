"""
LexPrime Auth 邮箱验证模块 (W3)
2026-06-29

W2 已有 OTPLog 短码 (6 位 + 10min) 用于注册即时验证。
W3 新增长 token (URL-safe + 24h) 用于:
- 注册后通过邮件链接验证
- 改邮箱验证
- 找回密码验证 (Phase 4 后)

发送方式:
- dev: 写到 loguru (生产切 SendGrid/阿里云)
- token 明文仅出现一次 (创建时 + 邮件正文), DB 存 sha256
- 重复发送会撤销同 user+purpose 旧 token (防滥用)

W3 endpoint:
- POST /api/auth/email/send       重新发送验证邮件
- POST /api/auth/email/verify     验证 token (body: {token})
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import EmailVerification, User
from auth.security import hash_token
from auth.ratelimit import (
    email_verify_key_by_ip,
    rate_limit_check,
)
from core.config import settings


# ========== 业务异常 ==========
class EmailVerificationError(Exception):
    """邮箱验证业务异常基类"""

    code: str = "email_verification_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidVerificationTokenError(EmailVerificationError):
    code = "invalid_verification_token"


class VerificationTokenExpiredError(EmailVerificationError):
    code = "verification_token_expired"


class VerificationTokenUsedError(EmailVerificationError):
    code = "verification_token_used"


class EmailRateLimitedError(EmailVerificationError):
    code = "email_rate_limited"


# ========== Token 生成 ==========
def generate_verification_token() -> str:
    """
    生成 URL-safe 邮箱验证 token
    - 32 字节 (256 bit) 熵, url-safe base64 编码 (无 padding)
    - 邮件正文: https://lexprime.com/verify?token=<token>
    - 长度 ~43 字符
    """
    return secrets.token_urlsafe(32)


# ========== 业务逻辑 ==========
async def send_email_verification(
    user: User,
    db: AsyncSession,
    *,
    purpose: str = "verify_email",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    device_info: Optional[str] = None,
) -> str:
    """
    发送邮箱验证邮件 (W3 dev: log 模式, 不真发)

    Args:
        user: 目标 User (必须是已存在的律师用户)
        purpose: 用途 (verify_email / reset_password / change_email)
        ip_address / user_agent: 审计用

    Returns:
        token 明文 (调用方负责嵌入邮件正文; 仅本次可见, 之后只能 hash 比对)

    Raises:
        EmailRateLimitedError: 触发限流 (默认 5 次/小时/IP)

    Side effects:
        - 撤销该 user + purpose 的旧未用 token (避免多个 link 漂泊)
        - 创建新 EmailVerification 记录 (24h 过期)
        - loguru.info 输出 token (dev 模式)
    """
    # 限流检查 (按 IP, 默认 5 次/小时)
    if ip_address:
        decision = rate_limit_check(
            key=email_verify_key_by_ip(ip_address),
            limit=settings.auth_max_failed_logins,
            window_seconds=3600,
        )
        if not decision.allowed:
            logger.warning(
                f"[auth.email_verify] rate-limited ip={ip_address} "
                f"count={decision.current_count}/{decision.limit} "
                f"retry_after={decision.retry_after}s"
            )
            raise EmailRateLimitedError(
                f"too many email verification requests, retry in {decision.retry_after}s"
            )

    # 撤销该 user + purpose 的旧未用 token
    now = datetime.now(tz=timezone.utc)
    await db.execute(
        update(EmailVerification)
        .where(
            EmailVerification.user_id == user.id,
            EmailVerification.purpose == purpose,
            EmailVerification.consumed_at.is_(None),
            EmailVerification.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )

    # 生成新 token
    token = generate_verification_token()
    token_hash = hash_token(token)

    record = EmailVerification(
        user_id=user.id,
        email=user.email,
        token_hash=token_hash,
        purpose=purpose,
        expires_at=now + timedelta(hours=settings.auth_email_verify_ttl_hours),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    # dev 模式: 直接 log token (W4 接 SendGrid 时换发送逻辑)
    logger.info(
        f"[auth.email_verify] {purpose} token for user id={user.id} email={user.email}: "
        f"token={token} "
        f"verify_url=http://localhost:8080/verify-email?token={token} "
        f"(dev only, W4 接 SendGrid)"
    )

    return token


async def verify_email_token(
    token: str,
    db: AsyncSession,
    *,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    device_info: Optional[str] = None,
) -> User:
    """
    验证邮箱 token (来自邮件链接)

    流程:
    1. 限流 (按 IP, 防爆破)
    2. hash 查 EmailVerification
    3. 检查未过期 + 未使用 + 未撤销
    4. 标记 consumed_at
    5. 标记 user.is_email_verified = True
    6. 返回 user

    Raises:
        EmailRateLimitedError
        InvalidVerificationTokenError: token 不存在
        VerificationTokenExpiredError: 已过期
        VerificationTokenUsedError: 已使用
    """
    if not token:
        raise InvalidVerificationTokenError("token is empty")

    # 限流 (按 IP)
    if ip_address:
        decision = rate_limit_check(
            key=email_verify_key_by_ip(ip_address),
            limit=settings.auth_max_failed_logins,
            window_seconds=3600,
        )
        if not decision.allowed:
            raise EmailRateLimitedError(
                f"too many verification attempts, retry in {decision.retry_after}s"
            )

    token_hash = hash_token(token)
    now = datetime.now(tz=timezone.utc)

    result = await db.execute(
        select(EmailVerification).where(EmailVerification.token_hash == token_hash)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise InvalidVerificationTokenError("verification token not recognized")

    if record.revoked_at is not None:
        raise InvalidVerificationTokenError("verification token has been revoked")

    if record.consumed_at is not None:
        raise VerificationTokenUsedError("verification token already used")

    # SQLite 读回的 datetime 是 naive, 强制 UTC 比较
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        raise VerificationTokenExpiredError("verification token expired")

    # 拿 user
    user_result = await db.execute(select(User).where(User.id == record.user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise InvalidVerificationTokenError("user no longer exists")

    # 标记 consumed + user.email_verified
    record.consumed_at = now
    user.is_email_verified = True

    await db.commit()
    await db.refresh(user)

    logger.info(
        f"[auth.email_verify] user id={user.id} email={user.email} "
        f"purpose={record.purpose} verified via token"
    )

    return user


# ========== 自检 ==========
def _self_check() -> None:
    token = generate_verification_token()
    assert len(token) >= 32, "token must have at least 32 chars"
    assert hash_token(token) != token, "hash must differ from plain"
    logger.debug("auth.email_verify self-check OK")


_self_check()