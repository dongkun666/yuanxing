"""
LexPrime Auth TOTP 二步验证模块 (W3)
2026-06-29

RFC 6238 TOTP 实现 (基于 pyotp):
- 用户绑定 TOTP (QR code + 手动 secret)
- 登录后强制 TOTP 验证 (律师执业必备, 后续 W4 接入登录流)
- 10 个一次性 backup codes (丢失设备时恢复)

绑定流程 (W3 endpoint):
1. POST /api/auth/totp/setup
   - 输入当前密码 (二次确认)
   - 服务端生成 secret, 返回 {secret, qr_code_url, backup_codes}
   - 不立即启用, user 用 authenticator 扫描后还需 verify

2. POST /api/auth/totp/verify  (绑定时验证, 启用 2FA)
   - body: {code: "123456"}
   - 验证通过 -> user.is_2fa_enabled = True, user.totp_secret = secret

3. POST /api/auth/totp/disable (解绑)
   - 输入当前密码 + code (或 backup code)
   - 撤销所有 backup codes, 清空 secret, is_2fa_enabled = False

Backup codes:
- 10 个 8 位 base32 字符串
- bcrypt 哈希存 (跟密码一样)
- 一次性, 用一个 mark 一个
- 全用完后, user 必须重新 setup
"""
from __future__ import annotations

import io
import secrets
from base64 import b64encode
from datetime import datetime, timezone
from typing import Optional, Tuple

import bcrypt
import pyotp
import qrcode
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import TotpBackupCode, User
from auth.ratelimit import totp_key_by_user, rate_limit_check
from auth.security import (
    AuthError,
    InvalidCredentialsError,
    verify_password,
)
from core.config import settings


# ========== 业务异常 ==========
class TotpError(AuthError):
    code = "totp_error"


class TotpAlreadyEnabledError(TotpError):
    code = "totp_already_enabled"


class TotpNotEnabledError(TotpError):
    code = "totp_not_enabled"


class InvalidTotpCodeError(TotpError):
    code = "invalid_totp_code"


class InvalidBackupCodeError(TotpError):
    code = "invalid_backup_code"


class NoBackupCodesError(TotpError):
    code = "no_backup_codes"


# ========== Secret 生成 ==========
def generate_totp_secret() -> str:
    """
    生成 base32 TOTP secret (160 bits)
    - pyotp.random_base32() 默认 32 chars / 160 bits
    - 跟 Google Authenticator / Authy / 1Password 兼容
    """
    return pyotp.random_base32()


def provisioning_uri(secret: str, account_name: str) -> str:
    """
    生成 otpauth:// provisioning URI

    客户端 (Google Authenticator / Authy) 扫这个 URI 自动填 secret + issuer
    """
    issuer = settings.auth_totp_issuer
    return pyotp.TOTP(secret).provisioning_uri(
        name=account_name,
        issuer_name=issuer,
    )


def qr_code_data_uri(uri: str) -> str:
    """
    生成 otpauth:// URI 的 QR code (base64 PNG data URI)
    - 直接给前端 <img src="data:image/png;base64,...">
    - 用 qrcode + PIL (Pillow)
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    encoded = b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


# ========== TOTP 验证 ==========
def verify_totp_code(secret: str, code: str) -> bool:
    """
    验证 6 位 TOTP code

    - valid_window=settings.auth_totp_window (±1 步, 容忍客户端时钟漂移 ~30s)
    - 防重放: 一次性使用需要在调用方做 (本函数只判断 code 是否正确)
    """
    if not secret or not code or len(code) != 6 or not code.isdigit():
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=settings.auth_totp_window)


# ========== Backup codes ==========
def _generate_backup_code() -> str:
    """生成 8 位 base32 单个 backup code (人类可读, 不会与 TOTP 混淆)"""
    # 8 chars * 5 bits/char = 40 bits, 防爆破够用
    alphabet = "ABCDEFGHIJKLMNPQRSTUVWXYZ23456789"  # 去 0/1/I/O 防视觉混淆
    return "".join(secrets.choice(alphabet) for _ in range(8))


def _hash_backup_code(code: str) -> str:
    """bcrypt 哈希 (跟密码一样)"""
    return bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt(rounds=10)).decode("utf-8")


def _verify_backup_code(plain: str, hashed: str) -> bool:
    """bcrypt 验"""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def generate_backup_codes(n: Optional[int] = None) -> list[str]:
    """生成 n 个新 backup codes (明文, 给用户一次性展示)"""
    count = n or settings.auth_totp_backup_codes_count
    return [_generate_backup_code() for _ in range(count)]


# ========== 业务逻辑 ==========
async def setup_totp(
    user: User,
    password: str,
    db: AsyncSession,
) -> Tuple[str, str, list[str]]:
    """
    TOTP setup - 第一步: 生成 secret + QR + backup codes (不立即启用)

    Args:
        user: 当前 user (已登录)
        password: 当前密码 (二次确认)
        db: AsyncSession

    Returns:
        (secret, qr_code_data_uri, backup_codes_plain)
        - secret: base32, 用户也可手动输入 authenticator
        - qr_code_data_uri: data:image/png;base64,... 前端直接展示
        - backup_codes_plain: 一次性明文, 用户需妥善保存

    Raises:
        InvalidCredentialsError: 密码错
        TotpAlreadyEnabledError: 已启用 2FA (须先 disable)
        EmailRateLimitedError / TotpError: 限流等
    """
    # 密码二次确认
    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("password incorrect")

    # 限流 (按 user, 防 setup 滥用)
    decision = rate_limit_check(
        key=totp_key_by_user(user.id),
        limit=settings.auth_max_failed_logins,
        window_seconds=3600,
    )
    if not decision.allowed:
        raise TotpError(f"too many setup attempts, retry in {decision.retry_after}s")

    # 已经在启用状态 → 拒绝 (用户应该 disable 再 setup)
    if user.is_2fa_enabled and user.totp_secret:
        raise TotpAlreadyEnabledError(
            "2FA already enabled, disable first to re-setup"
        )

    # 生成 secret (存到 user.totp_secret 临时, 待 verify 确认才设 is_2fa_enabled=True)
    secret = generate_totp_secret()
    user.totp_secret = secret
    await db.commit()
    await db.refresh(user)

    # 生成 QR code (data URI)
    uri = provisioning_uri(secret, user.email)
    qr_uri = qr_code_data_uri(uri)

    # 生成 backup codes (明文返回给用户, hashed 存 DB)
    codes = generate_backup_codes()
    await _save_backup_codes(user, codes, db)

    logger.info(
        f"[auth.totp.setup] user id={user.id} email={user.email} "
        f"generated secret (10 backup codes)"
    )

    return secret, qr_uri, codes


async def _save_backup_codes(user: User, codes_plain: list[str], db: AsyncSession) -> None:
    """
    保存 backup codes 到 DB (hashed)
    - 先清空该 user 旧的 (重置场景)
    """
    # 删旧 (如果重置)
    old_result = await db.execute(
        select(TotpBackupCode).where(TotpBackupCode.user_id == user.id)
    )
    for old in old_result.scalars().all():
        await db.delete(old)
    await db.flush()

    # 加新
    for code in codes_plain:
        record = TotpBackupCode(
            user_id=user.id,
            code_hash=_hash_backup_code(code),
            code_prefix=code[:4],  # 前 4 位标记, 用户识别用
        )
        db.add(record)
    await db.commit()


async def verify_and_enable_totp(
    user: User,
    code: str,
    db: AsyncSession,
) -> bool:
    """
    TOTP setup - 第二步: 用户在 authenticator 看到 code 后, 提交验证启用 2FA

    Args:
        user: 当前 user (已经 setup, user.totp_secret 已存)
        code: 6 位 TOTP code (来自 authenticator)

    Returns:
        True = 验证通过, is_2fa_enabled 已设 True

    Raises:
        TotpNotEnabledError: setup 未完成 (secret 为空)
        InvalidTotpCodeError: code 不对
    """
    if not user.totp_secret:
        raise TotpNotEnabledError("totp not set up, call setup_totp first")

    if not verify_totp_code(user.totp_secret, code):
        logger.warning(
            f"[auth.totp.verify] user id={user.id} invalid code "
            f"(len={len(code) if code else 0})"
        )
        raise InvalidTotpCodeError("invalid totp code")

    user.is_2fa_enabled = True
    await db.commit()
    await db.refresh(user)

    logger.info(f"[auth.totp.verify] user id={user.id} 2FA enabled")
    return True


async def verify_totp_for_login(
    user: User,
    code: str,
    db: AsyncSession,
) -> bool:
    """
    登录时验证 TOTP code (W3 dev 暴露 endpoint, W4 接入登录流)

    - 正常 6 位 code -> verify
    - 8 位 backup code -> 匹配 backup_codes 表 (一次性, 用后失效)
    """
    if not user.is_2fa_enabled or not user.totp_secret:
        raise TotpNotEnabledError("2FA not enabled")

    # 先尝试 6 位 TOTP code
    if code and len(code) == 6 and code.isdigit():
        if verify_totp_code(user.totp_secret, code):
            return True

    # 再尝试 backup code (8 位 base32)
    if code and len(code) == 8:
        result = await db.execute(
            select(TotpBackupCode).where(
                TotpBackupCode.user_id == user.id,
                TotpBackupCode.consumed_at.is_(None),
            )
        )
        for record in result.scalars().all():
            if _verify_backup_code(code, record.code_hash):
                record.consumed_at = datetime.now(tz=timezone.utc)
                await db.commit()
                logger.info(
                    f"[auth.totp.backup] user id={user.id} "
                    f"consumed backup code id={record.id}"
                )
                return True

    raise InvalidTotpCodeError("invalid totp code or backup code")


async def disable_totp(
    user: User,
    password: str,
    code: Optional[str],
    db: AsyncSession,
) -> bool:
    """
    关闭 2FA (需要密码 + 当前 code/backup code 二次确认)

    Returns:
        True = 关闭成功

    Raises:
        InvalidCredentialsError: 密码错
        InvalidTotpCodeError: code 错
        TotpNotEnabledError: 未启用 2FA
    """
    if not user.is_2fa_enabled or not user.totp_secret:
        raise TotpNotEnabledError("2FA not enabled")

    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("password incorrect")

    if not code:
        raise InvalidTotpCodeError("code required to disable 2FA")

    # 验证 code 或 backup code (复用 login 验证函数, 但这里不需要 log 副作用)
    await verify_totp_for_login(user, code, db)

    # 关闭
    user.is_2fa_enabled = False
    user.totp_secret = None

    # 清 backup codes
    result = await db.execute(
        select(TotpBackupCode).where(TotpBackupCode.user_id == user.id)
    )
    for record in result.scalars().all():
        await db.delete(record)

    await db.commit()
    await db.refresh(user)

    logger.info(f"[auth.totp.disable] user id={user.id} 2FA disabled")
    return True


# ========== 自检 ==========
def _self_check() -> None:
    secret = generate_totp_secret()
    assert len(secret) >= 16, "secret must be at least 16 chars"
    totp = pyotp.TOTP(secret)
    code = totp.now()
    assert verify_totp_code(secret, code), "fresh code must verify"
    assert not verify_totp_code(secret, "000000"), "wrong code must fail"

    uri = provisioning_uri(secret, "test@lexprime.com")
    assert uri.startswith("otpauth://totp/"), "uri must use otpauth scheme"

    qr = qr_code_data_uri(uri)
    assert qr.startswith("data:image/png;base64,"), "qr must be data URI"

    codes = generate_backup_codes(3)
    assert len(codes) == 3
    for c in codes:
        assert len(c) == 8
        assert _verify_backup_code(c, _hash_backup_code(c))
        assert not _verify_backup_code(c, _hash_backup_code(codes[0] if c == codes[1] else codes[1]))

    logger.debug("auth.totp self-check OK")


_self_check()