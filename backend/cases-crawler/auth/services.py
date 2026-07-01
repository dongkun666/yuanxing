"""
LexPrime Auth 业务服务层
2026-06-29 · Track A Phase 4 W2

职责:
- 注册: 重复检测 + bcrypt + 建 LawyerProfile + 触发邮箱验证
- 登录: bcrypt 验证 + 失败计数 + 锁定 + JWT 签发 + refresh token 持久化
- 刷新: refresh_token 签名验证 + 轮转 (旧撤销 + 新签发)
- 登出: 撤销 refresh_token
- 当前用户: User + Profile 聚合

错误约定:
- 用 AuthError 子类表达业务错误 (不抛 HTTPException, 让 endpoint 翻译)
- 邮箱重复 → EmailAlreadyRegisteredError
- 密码错 → InvalidCredentialsError
- 账号锁定 → AccountLockedError
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import LawyerProfile, OTPLog, Token, User
from auth.schemas import LoginRequest, RegisterRequest
from auth.security import (
    AccountLockedError,
    AuthError,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError,
    create_access_token,
    create_refresh_token,
    decode_token,
    extract_user_id_from_payload,
    hash_password,
    hash_token,
    verify_password,
)
from core.config import settings


# ========== 业务异常 ==========
class EmailAlreadyRegisteredError(AuthError):
    code = "email_already_registered"


class UserNotFoundError(AuthError):
    code = "user_not_found"


class LicenseAlreadyRegisteredError(AuthError):
    code = "license_already_registered"


# ========== 注册 ==========
async def register_user(
    payload: RegisterRequest,
    db: AsyncSession,
    *,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    device_info: Optional[str] = None,
) -> User:
    """
    注册用户

    流程:
    1. 查 email 是否已注册
    2. 查 license_no 是否已注册 (如有)
    3. bcrypt 密码
    4. 创建 User (transaction)
    5. 创建 LawyerProfile (1:1)
    6. 提交, 失败回滚

    注: 邮箱验证 token 通过 OTPLog 表模拟 (W4 接真邮件服务)
        - W2 阶段: 写 OTPLog + loguru.info (开发可见), 不真发邮件
    """
    email_normalized = payload.email.lower().strip()

    # 1. 邮箱重复检测
    existing = await db.execute(select(User).where(User.email == email_normalized))
    if existing.scalar_one_or_none() is not None:
        raise EmailAlreadyRegisteredError(f"email '{email_normalized}' is already registered")

    # 2. 执业证号重复检测 (如有)
    if payload.license_no:
        existing_license = await db.execute(
            select(LawyerProfile).where(LawyerProfile.license_no == payload.license_no)
        )
        if existing_license.scalar_one_or_none() is not None:
            raise LicenseAlreadyRegisteredError(
                f"license_no '{payload.license_no}' is already registered"
            )

    # 3. 密码哈希
    password_hashed = hash_password(payload.password)

    # 4. 创建 User
    user = User(
        email=email_normalized,
        phone=payload.phone,
        password_hash=password_hashed,
        role="lawyer",
        subscription_tier="trial",
        is_active=True,
        is_email_verified=False,  # 需后续验证
    )
    db.add(user)
    try:
        await db.flush()  # 拿 user.id, 不 commit
    except IntegrityError as e:
        await db.rollback()
        # race condition: 同一 email 并发注册
        raise EmailAlreadyRegisteredError(f"email '{email_normalized}' is already registered") from e

    # 5. 建 LawyerProfile
    profile = LawyerProfile(
        user_id=user.id,
        name=payload.name,
        license_no=payload.license_no,
        license_status="pending",
    )
    db.add(profile)

    # 6. 触发邮箱验证 (开发模式: 写 OTPLog + loguru.info; W4 接 SendGrid)
    otp_code = _generate_otp_code()
    otp_log = OTPLog(
        target=email_normalized,
        target_type="email",
        purpose="verify_email",
        code_hash=hash_token(otp_code),  # 直接存 sha256 (OTP 是短码, 不需要 bcrypt)
        sent_to=email_normalized,
        expires_at=datetime.now(tz=timezone.utc) + timedelta(minutes=10),
        max_attempts=5,
        ip_address=ip_address,
        user_agent=user_agent,
        related_user_id=user.id,
    )
    db.add(otp_log)

    await db.commit()
    await db.refresh(user)

    logger.info(
        f"[auth.register] new user id={user.id} email={email_normalized} "
        f"license_no={payload.license_no} "
        f"email_verify_otp={otp_code} (dev only, W4 接 SendGrid)"
    )

    return user


# ========== 登录 ==========
async def authenticate_user(
    payload: LoginRequest,
    db: AsyncSession,
    *,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    device_info: Optional[str] = None,
) -> tuple[User, str, str, int]:
    """
    认证用户, 返回 (user, access_token, refresh_token, access_expires_in)

    流程:
    1. 查 user by email
    2. 检查锁定状态
    3. bcrypt verify
       - 错: failed_login_count++, >=max 就锁
       - 对: 重置 count, 更新 last_login_at
    4. 签发 access + refresh
    5. refresh_token 哈希持久化 (auth_tokens)
    """
    email_normalized = payload.email.lower().strip()
    now = datetime.now(tz=timezone.utc)

    # 1. 查 user
    result = await db.execute(select(User).where(User.email == email_normalized))
    user = result.scalar_one_or_none()
    if user is None:
        # 不暴露用户是否存在, 用统一错
        raise InvalidCredentialsError("invalid email or password")

    # 2. 锁定检查 (SQLite 读回的 datetime 是 naive, 强制 UTC 比较)
    locked_until = user.locked_until
    if locked_until is not None:
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        if locked_until > now:
            remaining_min = int((locked_until - now).total_seconds() / 60) + 1
            raise AccountLockedError(
                f"account locked, retry in {remaining_min} minutes",
            )

    # 3. 密码验证
    if not verify_password(payload.password, user.password_hash):
        user.failed_login_count = (user.failed_login_count or 0) + 1
        if user.failed_login_count >= settings.auth_max_failed_logins:
            user.locked_until = now + timedelta(minutes=settings.auth_lock_minutes)
            user.failed_login_count = 0  # 重置, 锁定后再失败再累计
            logger.warning(
                f"[auth.login] user id={user.id} email={email_normalized} "
                f"locked until {user.locked_until.isoformat()} (5 failed attempts)"
            )
        await db.commit()
        raise InvalidCredentialsError("invalid email or password")

    # 4. 账号未激活
    if not user.is_active:
        raise InvalidCredentialsError("account is inactive")

    # 5. 签发 tokens
    access_token, access_expires = create_access_token(user.id, role=user.role)
    refresh_token, refresh_expires = create_refresh_token(user.id)

    # 6. 持久化 refresh_token (存 hash, 不存明文)
    token_record = Token(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        token_type="refresh",
        device_info=device_info,
        ip_address=ip_address,
        user_agent=user_agent,
        issued_at=now,
        expires_at=now + timedelta(seconds=refresh_expires),
    )
    db.add(token_record)

    # 7. 更新用户登录状态
    user.last_login_at = now
    user.last_login_ip = ip_address
    user.failed_login_count = 0
    user.locked_until = None

    await db.commit()
    await db.refresh(user)

    logger.info(
        f"[auth.login] user id={user.id} email={email_normalized} "
        f"role={user.role} ip={ip_address}"
    )

    return user, access_token, refresh_token, access_expires


# ========== 刷新 ==========
async def refresh_tokens(
    refresh_token: str,
    db: AsyncSession,
    *,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    device_info: Optional[str] = None,
) -> tuple[str, str, int]:
    """
    刷新 access_token (轮转 refresh_token)

    流程:
    1. 验证 refresh_token JWT 签名 + 过期
    2. 查 token_hash 持久化记录, 检查是否已撤销
    3. 撤销旧 token (single-use)
    4. 签发新 access + 新 refresh
    5. 持久化新 refresh

    Returns: (new_access, new_refresh, access_expires_in)
    """
    # 1. 验证签名 + 过期 + type
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
    except TokenExpiredError:
        raise TokenExpiredError("refresh token expired")
    except TokenInvalidError as e:
        raise TokenInvalidError(f"invalid refresh token: {e}")

    user_id = extract_user_id_from_payload(payload)

    # 2. 查持久化记录 (token_hash 匹配 + 未撤销 + 未过期)
    token_hash = hash_token(refresh_token)
    now = datetime.now(tz=timezone.utc)

    result = await db.execute(
        select(Token).where(
            Token.token_hash == token_hash,
            Token.token_type == "refresh",
        )
    )
    token_record = result.scalar_one_or_none()
    if token_record is None:
        raise TokenInvalidError("refresh token not recognized")
    if token_record.revoked_at is not None:
        # 重放检测: 旧 token 被用过 → 撤销同 user 所有 token (防 token 偷窃后攻击)
        logger.warning(
            f"[auth.refresh] REPLAY DETECTED for user id={user_id}, "
            f"revoking all refresh tokens"
        )
        await _revoke_all_user_tokens(db, user_id, reason="replay_detected")
        raise TokenInvalidError("refresh token already used (potential replay)")
    if token_record.expires_at.replace(tzinfo=timezone.utc) < now:
        raise TokenExpiredError("refresh token expired (db record)")

    # 3. 验证 user 状态
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise InvalidCredentialsError("user not active")

    # 4. 撤销旧 token
    token_record.revoked_at = now
    token_record.revoked_reason = "rotated"

    # 5. 签发新 tokens
    new_access, access_expires = create_access_token(user.id, role=user.role)
    new_refresh, refresh_expires = create_refresh_token(user.id)

    new_token_record = Token(
        user_id=user.id,
        token_hash=hash_token(new_refresh),
        token_type="refresh",
        device_info=device_info or token_record.device_info,  # 优先用新 device_info, 否则继承
        ip_address=ip_address or token_record.ip_address,
        user_agent=user_agent or token_record.user_agent,
        issued_at=now,
        expires_at=now + timedelta(seconds=refresh_expires),
    )
    db.add(new_token_record)

    await db.commit()

    logger.info(
        f"[auth.refresh] user id={user.id} rotated, "
        f"old jti={payload.get('jti', '?')[:8]}... new jti={new_token_record.id}"
    )

    return new_access, new_refresh, access_expires


async def _revoke_all_user_tokens(db: AsyncSession, user_id: int, reason: str = "admin") -> int:
    """撤销 user 的所有未撤销 refresh tokens"""
    now = datetime.now(tz=timezone.utc)
    result = await db.execute(
        select(Token).where(
            Token.user_id == user_id,
            Token.revoked_at.is_(None),
        )
    )
    tokens = result.scalars().all()
    for t in tokens:
        t.revoked_at = now
        t.revoked_reason = reason
    await db.commit()
    return len(tokens)


# ========== 登出 (Bonus) ==========
async def logout(
    refresh_token: str,
    db: AsyncSession,
    *,
    user_id: Optional[int] = None,
) -> bool:
    """
    登出: 撤销单个 refresh_token
    返回是否成功撤销 (False = token 不存在或已撤销)
    """
    token_hash = hash_token(refresh_token)
    result = await db.execute(
        select(Token).where(
            Token.token_hash == token_hash,
            Token.token_type == "refresh",
        )
    )
    token_record = result.scalar_one_or_none()
    if token_record is None or token_record.revoked_at is not None:
        return False

    # 如果指定 user_id, 校验匹配 (防止误撤销别人的 token)
    if user_id is not None and token_record.user_id != user_id:
        return False

    token_record.revoked_at = datetime.now(tz=timezone.utc)
    token_record.revoked_reason = "logout"
    await db.commit()
    logger.info(f"[auth.logout] revoked token id={token_record.id}")
    return True


# ========== 当前用户 ==========
async def get_user_with_profile(db: AsyncSession, user_id: int) -> tuple[User, Optional[LawyerProfile]]:
    """
    拿 user + profile (1:1)
    - 用 joinedload 避免 lazy load 跨 session 失败
    """
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(User)
        .options(selectinload(User.profile))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise UserNotFoundError(f"user id={user_id} not found")
    return user, user.profile


# ========== 工具 ==========
def _generate_otp_code(length: int = 6) -> str:
    """生成数字 OTP 验证码 (W2 dev 用, W4 接 SendGrid 时换真随机)"""
    import secrets

    return "".join(str(secrets.randbelow(10)) for _ in range(length))