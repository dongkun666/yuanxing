"""
LexPrime Auth SQLAlchemy ORM 模型
2026-06-28 · W1 脚手架 → 2026-06-29 · W2 业务表 → 2026-06-29 · W3 扩展表

W1+W2 (4 表):
- User           认证实体 (email + password + 角色 + 状态)
- LawyerProfile  律师扩展档案 (1-to-1 with User) - 执业证 / 律所 / 审核状态
- Token          Refresh Token 持久化 (含设备/IP/撤销标记)
- OTPLog         邮箱/手机验证码 (purpose: register/reset/login/2fa/license_verify)

W3 (3 新表):
- EmailVerification       邮箱验证长 token (24h 过期, 一次性)
- TotpBackupCode          TOTP 一次性恢复码 (10 个, hashed)
- LicenseReviewLog        律师执业证审核状态变迁审计

与现有 core/models.py 的 Lawyer/Firm 解耦:
- User 是认证层, LawyerProfile 是业务档案层
- 这样后续个人版/企业版 RBAC 可以基于 User.role 灵活扩展, 不动业务表
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    String,
    Text,
    DateTime,
    Boolean,
    Integer,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.dialects.sqlite import INTEGER as SQLITE_INTEGER  # noqa: F401
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.models import Base

# SQLite 不支持 BIGINT 自增 (只 INTEGER PRIMARY KEY 走 rowid 自增)
# PG 端保持 BigInteger, dev SQLite 退化到 Integer
BigIntPK = BigInteger().with_variant(Integer(), "sqlite")
BigIntFK = BigInteger().with_variant(Integer(), "sqlite")


# ========== User (认证实体) ==========
class User(Base):
    """
    律师用户认证实体

    - 邮箱为主账号 (唯一, 登录用)
    - 手机为辅 (可选, 用于短信验证/2FA)
    - 密码 bcrypt 哈希 (W2 实现)
    - role: lawyer (律师) / firm_admin (律所管理员) / admin (平台管理员)
    - subscription_tier: trial / pro / enterprise (与 Firm 对齐, 个人版可独立订阅)
    """
    __tablename__ = "auth_users"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(32), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(16), default="lawyer", index=True, nullable=False)
    subscription_tier: Mapped[str] = mapped_column(String(16), default="trial", index=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    totp_secret: Mapped[Optional[str]] = mapped_column(String(64))

    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(64))
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )

    __table_args__ = (
        Index("idx_user_role_active", "role", "is_active"),
        Index("idx_user_tier_active", "subscription_tier", "is_active"),
    )

    # Relationships
    # 注: LawyerProfile 表有两个 FK 回指 auth_users:
    #   - user_id (1:1 关系, 本关系的承载列)
    #   - license_reviewed_by (审核人, 单向 FK 不建反向关系)
    # 必须显式指定 foreign_keys, 否则 SQLAlchemy 无法决定 join 路径
    profile: Mapped[Optional["LawyerProfile"]] = relationship(
        "LawyerProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="[LawyerProfile.user_id]",
    )
    tokens: Mapped[List["Token"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


# ========== LawyerProfile (律师扩展档案) ==========
class LawyerProfile(Base):
    """
    律师扩展档案 - 1:1 with User

    与 core.models.Lawyer 字段对齐, 但走 auth schema (避免业务表污染)
    W3 律师执业证审核工作流会用到:
    - license_status: pending / ai_reviewing / human_reviewing / approved / rejected
    - license_image_url: 上传的执业证图片 (本地路径, 不上云)
    - license_ocr_data: PaddleOCR 提取的 JSON
    """
    __tablename__ = "auth_lawyer_profiles"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigIntFK, ForeignKey("auth_users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )

    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    license_no: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True)
    firm_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("firms.id", ondelete="SET NULL"), index=True
    )
    firm_role: Mapped[str] = mapped_column(String(16), default="lawyer", index=True)

    # 执业证审核状态
    license_status: Mapped[str] = mapped_column(String(16), default="pending", index=True, nullable=False)
    license_image_url: Mapped[Optional[str]] = mapped_column(Text)
    license_ocr_data: Mapped[Optional[dict]] = mapped_column(JSON)
    license_submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    license_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    license_reviewed_by: Mapped[Optional[int]] = mapped_column(
        BigIntFK, ForeignKey("auth_users.id", ondelete="SET NULL"), index=True
    )
    license_reject_reason: Mapped[Optional[str]] = mapped_column(Text)

    specialties: Mapped[Optional[List[str]]] = mapped_column(JSON)
    bio: Mapped[Optional[str]] = mapped_column(Text)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    region: Mapped[Optional[str]] = mapped_column(String(32), index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )

    __table_args__ = (
        Index("idx_profile_license_status", "license_status", "created_at"),
        Index("idx_profile_firm_status", "firm_id", "license_status"),
    )

    # Relationships
    # 反向关系, 跟 User.profile 一样要显式指定 foreign_keys
    # license_reviewed_by 是另一个 FK 回指 auth_users, 不建反向关系 (单向足够)
    user: Mapped["User"] = relationship(
        "User",
        back_populates="profile",
        foreign_keys="[LawyerProfile.user_id]",
    )


# ========== Token (Refresh Token 持久化) ==========
class Token(Base):
    """
    Refresh Token 持久化 (W2 实现 JWT 签发时用)

    - 存 token_hash (不存明文, 跟密码一样)
    - device_info / ip 用于 UEBA 异常检测 (企业版)
    - revoked_at 非空 = 已撤销 (登出/换设备/异常)
    """
    __tablename__ = "auth_tokens"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigIntFK, ForeignKey("auth_users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    token_type: Mapped[str] = mapped_column(String(16), default="refresh", nullable=False, index=True)

    device_info: Mapped[Optional[str]] = mapped_column(String(512))
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)

    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    revoked_reason: Mapped[Optional[str]] = mapped_column(String(64))

    __table_args__ = (
        Index("idx_token_user_revoked", "user_id", "revoked_at"),
        Index("idx_token_expires_revoked", "expires_at", "revoked_at"),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="tokens")


# ========== OTPLog (邮箱/手机验证码) ==========
class OTPLog(Base):
    """
    OTP 验证码日志 (邮箱/手机)

    - target: 邮箱地址 或 手机号
    - purpose: register / login / reset_password / verify_email / verify_phone / 2fa / license_verify
    - code_hash: 验证码哈希 (不存明文, 跟密码一样)
    - attempt_count: 尝试次数 (防爆破, >5 锁定)
    - consumed_at: 使用时间 (用一次即失效)
    """
    __tablename__ = "auth_otp_logs"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    target: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    target_type: Mapped[str] = mapped_column(String(16), default="email", nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    sent_to: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    related_user_id: Mapped[Optional[int]] = mapped_column(
        BigIntFK, ForeignKey("auth_users.id", ondelete="SET NULL"), index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("idx_otp_target_purpose", "target", "purpose"),
        Index("idx_otp_user_purpose", "related_user_id", "purpose"),
    )


# ========== EmailVerification (W3: 邮箱验证长 token) ==========
class EmailVerification(Base):
    """
    邮箱验证长 token (W3)

    - token_hash 存 sha256 (跟密码一样原则)
    - 24h 过期 (auth_email_verify_ttl_hours)
    - 一次性: consumed_at 非空 = 已用
    - 重复发送会撤销旧 token (防滥用)
    """
    __tablename__ = "auth_email_verifications"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigIntFK, ForeignKey("auth_users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    purpose: Mapped[str] = mapped_column(String(32), default="verify_email", nullable=False, index=True)
    # purpose: verify_email / reset_password / change_email

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)

    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("idx_email_verify_user_purpose", "user_id", "purpose"),
        Index("idx_email_verify_email_purpose", "email", "purpose"),
    )


# ========== TotpBackupCode (W3: TOTP 一次性恢复码) ==========
class TotpBackupCode(Base):
    """
    TOTP 一次性恢复码 (W3)

    - 用户绑定 TOTP 时生成 10 个 (auth_totp_backup_codes_count)
    - 用 bcrypt 哈希存 (跟密码一样), 不存明文
    - 一次性: consumed_at 非空 = 已用
    - 用完后 user 可重置 (W3 POST /api/auth/totp/reset)
    """
    __tablename__ = "auth_totp_backup_codes"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigIntFK, ForeignKey("auth_users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # 短码标记 (前 4 位明文, 帮助用户识别"哪一组")
    code_prefix: Mapped[str] = mapped_column(String(8), nullable=False)

    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    consumed_ip: Mapped[Optional[str]] = mapped_column(String(64))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("idx_totp_backup_user", "user_id"),
        Index("idx_totp_backup_user_consumed", "user_id", "consumed_at"),
    )


# ========== LicenseReviewLog (W3: 律师执业证审核审计) ==========
class LicenseReviewLog(Base):
    """
    律师执业证审核状态变迁审计 (W3)

    状态机: pending → ai_reviewing → human_reviewing → approved / rejected
    每一步变迁记录一条 (from_status / to_status / actor / reason / ai_score)
    人工复审管理员只能看到状态 + 操作历史, 不允许改 OCR 数据
    """
    __tablename__ = "auth_license_review_logs"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        BigIntFK, ForeignKey("auth_lawyer_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        BigIntFK, ForeignKey("auth_users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    from_status: Mapped[Optional[str]] = mapped_column(String(16), index=True)
    to_status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    actor_type: Mapped[str] = mapped_column(String(16), default="system", nullable=False, index=True)
    # actor_type: system / ai / admin / user (user = 用户自己上传触发)
    actor_id: Mapped[Optional[int]] = mapped_column(
        BigIntFK, ForeignKey("auth_users.id", ondelete="SET NULL"), index=True
    )

    ai_score: Mapped[Optional[float]] = mapped_column()  # 0.0 - 1.0
    reason: Mapped[Optional[str]] = mapped_column(Text)
    extra: Mapped[Optional[dict]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("idx_license_review_profile", "profile_id"),
        Index("idx_license_review_actor", "actor_id", "actor_type"),
        Index("idx_license_review_status", "from_status", "to_status"),
    )


# ========== Plan (订阅套餐) ==========
class Plan(Base):
    """
    订阅套餐定义
    - 免费/基础/专业/企业 四档
    - 支持月付/年付
    - 功能配置以 JSON 存储 (灵活扩展)
    """
    __tablename__ = "subscription_plans"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))

    tier: Mapped[str] = mapped_column(String(16), default="basic", index=True, nullable=False)
    billing_cycle: Mapped[str] = mapped_column(String(16), default="monthly", index=True, nullable=False)

    price_monthly: Mapped[float] = mapped_column(default=0.0)
    price_yearly: Mapped[float] = mapped_column(default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="CNY")

    trial_days: Mapped[int] = mapped_column(Integer, default=0)

    features: Mapped[Optional[dict]] = mapped_column(JSON)
    limits: Mapped[Optional[dict]] = mapped_column(JSON)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False)

    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_plan_tier_active", "tier", "is_active"),
        Index("idx_plan_billing_active", "billing_cycle", "is_active"),
    )


# ========== Subscription (用户订阅) ==========
class Subscription(Base):
    """
    用户订阅记录
    - 用户可以有多个订阅 (历史/升级/降级)
    - status: active / cancelled / expired / trialing
    """
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigIntFK, ForeignKey("auth_users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    plan_id: Mapped[int] = mapped_column(
        BigIntFK, ForeignKey("subscription_plans.id", ondelete="SET NULL"), index=True
    )

    plan_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    plan_name: Mapped[str] = mapped_column(String(64))

    status: Mapped[str] = mapped_column(String(16), default="trialing", index=True, nullable=False)
    billing_cycle: Mapped[str] = mapped_column(String(16), default="monthly")

    amount: Mapped[float] = mapped_column(default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="CNY")

    current_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)

    trial_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    trial_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    canceled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancel_reason: Mapped[Optional[str]] = mapped_column(Text)

    payment_provider: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    provider_subscription_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)

    extra: Mapped[Optional[dict]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_sub_user_status", "user_id", "status"),
        Index("idx_sub_plan_status", "plan_id", "status"),
        Index("idx_sub_period_end", "current_period_end"),
    )

    user: Mapped["User"] = relationship("User")


# ========== Invoice (账单/发票) ==========
class Invoice(Base):
    """
    账单/支付记录
    - 每次支付生成一条
    - status: paid / unpaid / refunded / void
    """
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    invoice_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    user_id: Mapped[int] = mapped_column(
        BigIntFK, ForeignKey("auth_users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    subscription_id: Mapped[Optional[int]] = mapped_column(
        BigIntFK, ForeignKey("subscriptions.id", ondelete="SET NULL"), index=True
    )

    plan_code: Mapped[str] = mapped_column(String(32), index=True)
    plan_name: Mapped[str] = mapped_column(String(64))

    status: Mapped[str] = mapped_column(String(16), default="unpaid", index=True, nullable=False)

    amount: Mapped[float] = mapped_column(default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    discount: Mapped[float] = mapped_column(default=0.0)

    billing_cycle: Mapped[str] = mapped_column(String(16), default="monthly")
    period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    payment_method: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    payment_provider: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    provider_payment_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)

    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    invoice_url: Mapped[Optional[str]] = mapped_column(Text)
    receipt_url: Mapped[Optional[str]] = mapped_column(Text)

    extra: Mapped[Optional[dict]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_invoice_user_status", "user_id", "status"),
        Index("idx_invoice_paid_at", "paid_at"),
        Index("idx_invoice_provider", "payment_provider", "provider_payment_id"),
    )

    user: Mapped["User"] = relationship("User")


# ========== InviteCode (邀请码) ==========
class InviteCode(Base):
    """
    邀请码
    - 每个用户一个专属邀请码
    - 也支持 admin 批量生成
    """
    __tablename__ = "invite_codes"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)

    user_id: Mapped[Optional[int]] = mapped_column(
        BigIntFK, ForeignKey("auth_users.id", ondelete="SET NULL"), index=True
    )

    channel: Mapped[str] = mapped_column(String(32), default="referral", index=True)
    batch: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    max_uses: Mapped[int] = mapped_column(Integer, default=0)
    used_count: Mapped[int] = mapped_column(Integer, default=0)

    reward_type: Mapped[Optional[str]] = mapped_column(String(32))
    reward_days: Mapped[int] = mapped_column(Integer, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)

    note: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_invite_user_active", "user_id", "is_active"),
        Index("idx_invite_channel", "channel"),
    )

    user: Mapped[Optional["User"]] = relationship("User")


# ========== InviteRecord (邀请记录) ==========
class InviteRecord(Base):
    """
    邀请记录
    - 谁用了谁的邀请码
    - 奖励发放状态
    """
    __tablename__ = "invite_records"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)

    invite_code_id: Mapped[int] = mapped_column(
        BigIntFK, ForeignKey("invite_codes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    inviter_user_id: Mapped[Optional[int]] = mapped_column(
        BigIntFK, ForeignKey("auth_users.id", ondelete="SET NULL"), index=True
    )
    invitee_user_id: Mapped[Optional[int]] = mapped_column(
        BigIntFK, ForeignKey("auth_users.id", ondelete="SET NULL"), index=True
    )

    invite_code: Mapped[str] = mapped_column(String(32), index=True)
    invitee_email: Mapped[Optional[str]] = mapped_column(String(128), index=True)

    status: Mapped[str] = mapped_column(String(16), default="registered", index=True, nullable=False)
    reward_status: Mapped[str] = mapped_column(String(16), default="pending", index=True)

    reward_type: Mapped[Optional[str]] = mapped_column(String(32))
    reward_days: Mapped[int] = mapped_column(Integer, default=0)
    reward_granted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    source: Mapped[Optional[str]] = mapped_column(String(64))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_invite_rec_inviter", "inviter_user_id"),
        Index("idx_invite_rec_invitee", "invitee_user_id"),
        Index("idx_invite_rec_code", "invite_code_id"),
        Index("idx_invite_rec_status", "status"),
    )

    inviter: Mapped[Optional["User"]] = relationship("User", foreign_keys=[inviter_user_id])
    invitee: Mapped[Optional["User"]] = relationship("User", foreign_keys=[invitee_user_id])


# ========== Reward (奖励记录) ==========
class Reward(Base):
    """
    奖励记录
    - 邀请奖励 / 活动奖励等
    """
    __tablename__ = "rewards"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        BigIntFK, ForeignKey("auth_users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    reward_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    reward_source: Mapped[str] = mapped_column(String(32), default="invite", index=True)

    amount_days: Mapped[int] = mapped_column(Integer, default=0)
    amount_money: Mapped[float] = mapped_column(default=0.0)

    related_invite_id: Mapped[Optional[int]] = mapped_column(
        BigIntFK, ForeignKey("invite_records.id", ondelete="SET NULL"), index=True
    )

    status: Mapped[str] = mapped_column(String(16), default="granted", index=True, nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)

    description: Mapped[Optional[str]] = mapped_column(String(255))

    extra: Mapped[Optional[dict]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_reward_user_type", "user_id", "reward_type"),
        Index("idx_reward_status", "status"),
        Index("idx_reward_granted_at", "granted_at"),
    )

    user: Mapped["User"] = relationship("User")
