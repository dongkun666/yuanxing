"""
LexPrime Auth SQLAlchemy ORM 模型
2026-06-28 · W1 脚手架

4 表设计:
- User           认证实体 (email + password + 角色 + 状态)
- LawyerProfile  律师扩展档案 (1-to-1 with User) - 执业证 / 律所 / 审核状态
- Token          Refresh Token 持久化 (含设备/IP/撤销标记)
- OTPLog         邮箱/手机验证码 (purpose: register/reset/login/2fa/license_verify)

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
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    totp_secret: Mapped[Optional[str]] = mapped_column(String(64))  # W2 用, TOTP 密钥

    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(64))
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
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

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    license_no: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True)
    firm_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("firms.id", ondelete="SET NULL"), index=True
    )
    firm_role: Mapped[str] = mapped_column(String(16), default="lawyer")  # partner/senior/lawyer/assistant

    # 执业证审核状态
    license_status: Mapped[str] = mapped_column(String(16), default="pending", index=True, nullable=False)
    license_image_url: Mapped[Optional[str]] = mapped_column(Text)
    license_ocr_data: Mapped[Optional[dict]] = mapped_column(JSON)
    license_submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    license_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    license_reviewed_by: Mapped[Optional[int]] = mapped_column(
        BigIntFK, ForeignKey("auth_users.id", ondelete="SET NULL")
    )
    license_reject_reason: Mapped[Optional[str]] = mapped_column(Text)

    specialties: Mapped[Optional[List[str]]] = mapped_column(JSON)
    bio: Mapped[Optional[str]] = mapped_column(Text)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    region: Mapped[Optional[str]] = mapped_column(String(32))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
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
    token_type: Mapped[str] = mapped_column(String(16), default="refresh", nullable=False)

    device_info: Mapped[Optional[str]] = mapped_column(String(512))
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)

    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    revoked_reason: Mapped[Optional[str]] = mapped_column(String(64))

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
    target_type: Mapped[str] = mapped_column(String(16), default="email", nullable=False)  # email / phone
    purpose: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    sent_to: Mapped[str] = mapped_column(String(128), nullable=False)  # 冗余, 方便查询"哪些用户收到过 OTP"

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    related_user_id: Mapped[Optional[int]] = mapped_column(
        BigIntFK, ForeignKey("auth_users.id", ondelete="SET NULL"), index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (Index("idx_otp_target_purpose", "target", "purpose"),)
