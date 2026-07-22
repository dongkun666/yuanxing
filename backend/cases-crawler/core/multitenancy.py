"""
LexPrime 多租户系统
2026-07-03 · 企业级能力建设

功能模块:
- Tenant 模型 - 租户主数据
- TenantConfig - 租户配置
- TenantQuota - 配额管理
- TenantBilling - 计费管理
- 数据隔离 - 行级隔离 / schema 隔离 / 缓存隔离
- 租户管理 - 创建/删除/状态管理/数据导出/数据迁移
"""
from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    String, Text, DateTime, Boolean, Integer, SmallInteger, Numeric,
    ForeignKey, JSON, Index, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.models import Base


class TenantStatus(str, Enum):
    """租户状态"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIALING = "trialing"
    EXPIRED = "expired"
    DELETED = "deleted"


class TenantTier(str, Enum):
    """租户套餐等级"""
    FREE = "free"
    BASIC = "basic"
    PRO = "professional"
    ENTERPRISE = "enterprise"


class IsolationLevel(str, Enum):
    """数据隔离级别"""
    ROW = "row"
    SCHEMA = "schema"
    DATABASE = "database"


# ========== Tenant (租户主表) ==========
class Tenant(Base):
    """
    租户主表

    每个企业/组织对应一个租户, 拥有独立的数据空间和配额。
    """
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(256), index=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(256))

    status: Mapped[str] = mapped_column(String(16), default=TenantStatus.TRIALING.value, index=True, nullable=False)
    tier: Mapped[str] = mapped_column(String(16), default=TenantTier.FREE.value, index=True, nullable=False)
    isolation_level: Mapped[str] = mapped_column(String(16), default=IsolationLevel.ROW.value, index=True)

    schema_name: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    database_url: Mapped[Optional[str]] = mapped_column(String(512))

    contact_name: Mapped[Optional[str]] = mapped_column(String(64))
    contact_email: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(32))

    region: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    address: Mapped[Optional[str]] = mapped_column(String(512))
    website: Mapped[Optional[str]] = mapped_column(String(256))

    industry: Mapped[Optional[str]] = mapped_column(String(64))
    employee_count: Mapped[Optional[int]] = mapped_column(Integer)

    logo_url: Mapped[Optional[str]] = mapped_column(Text)
    branding_config: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    settings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    trial_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)

    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    suspended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    suspend_reason: Mapped[Optional[str]] = mapped_column(String(256))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True, nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)

    config: Mapped[Optional["TenantConfig"]] = relationship(
        "TenantConfig", back_populates="tenant", uselist=False, cascade="all, delete-orphan"
    )
    quota: Mapped[Optional["TenantQuota"]] = relationship(
        "TenantQuota", back_populates="tenant", uselist=False, cascade="all, delete-orphan"
    )
    billing: Mapped[Optional["TenantBilling"]] = relationship(
        "TenantBilling", back_populates="tenant", uselist=False, cascade="all, delete-orphan"
    )
    members: Mapped[List["TenantMember"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_tenant_status_tier", "status", "tier"),
        Index("idx_tenant_region_status", "region", "status"),
    )


# ========== TenantConfig (租户配置) ==========
class TenantConfig(Base):
    """
    租户配置表

    存储每个租户的个性化配置, 如功能开关、UI 定制、集成配置等。
    """
    __tablename__ = "tenant_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tenants.tenant_id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )

    features_enabled: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    ui_customization: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    security_settings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    notification_settings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    data_retention: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    integration_configs: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    default_language: Mapped[str] = mapped_column(String(16), default="zh-CN")
    default_timezone: Mapped[str] = mapped_column(String(64), default="Asia/Shanghai")
    default_currency: Mapped[str] = mapped_column(String(8), default="CNY")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="config")


# ========== TenantQuota (配额管理) ==========
class TenantQuota(Base):
    """
    租户配额表

    定义租户的资源使用限制, 如用户数、存储空间、API 调用次数等。
    """
    __tablename__ = "tenant_quotas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tenants.tenant_id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )

    max_users: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_storage_gb: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    max_api_calls_monthly: Mapped[int] = mapped_column(Integer, default=10000, nullable=False)
    max_cases: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    max_documents: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    max_ai_credits_monthly: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    max_concurrent_crawlers: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    used_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    used_storage_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    used_api_calls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    used_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    used_documents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    used_ai_credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    quota_reset_day: Mapped[int] = mapped_column(SmallInteger, default=1)
    last_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)

    custom_limits: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="quota")

    __table_args__ = (
        Index("idx_quota_next_reset", "next_reset_at"),
    )


# ========== TenantBilling (计费管理) ==========
class TenantBilling(Base):
    """
    租户计费表

    存储租户的订阅计划、账单周期、支付信息等。
    """
    __tablename__ = "tenant_billings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tenants.tenant_id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )

    plan_code: Mapped[str] = mapped_column(String(32), default="free", index=True, nullable=False)
    plan_name: Mapped[str] = mapped_column(String(64), default="免费版")
    billing_cycle: Mapped[str] = mapped_column(String(16), default="monthly", index=True)

    price_monthly: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    price_yearly: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(8), default="CNY")

    current_period_start: Mapped[Optional[date]] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[Optional[date]] = mapped_column(DateTime(timezone=True), index=True)

    payment_provider: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    payment_customer_id: Mapped[Optional[str]] = mapped_column(String(128))
    payment_method_id: Mapped[Optional[str]] = mapped_column(String(128))

    tax_id: Mapped[Optional[str]] = mapped_column(String(64))
    invoice_title: Mapped[Optional[str]] = mapped_column(String(256))
    billing_address: Mapped[Optional[str]] = mapped_column(String(512))

    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    canceled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancel_reason: Mapped[Optional[str]] = mapped_column(String(256))

    total_spent: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    last_payment_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    extra: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="billing")


# ========== TenantMember (租户成员) ==========
class TenantMember(Base):
    """
    租户成员表

    关联用户与租户的关系, 定义用户在租户中的角色和权限。
    """
    __tablename__ = "tenant_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tenants.tenant_id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    role: Mapped[str] = mapped_column(String(32), default="member", index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="active", index=True, nullable=False)

    joined_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    invited_by: Mapped[Optional[int]] = mapped_column(Integer)
    invite_email: Mapped[Optional[str]] = mapped_column(String(128), index=True)

    permissions: Mapped[Optional[List[str]]] = mapped_column(JSON)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="members")

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_tenant_user"),
        Index("idx_member_tenant_role", "tenant_id", "role"),
        Index("idx_member_tenant_status", "tenant_id", "status"),
    )


# ========== TenantDomain (租户域名) ==========
class TenantDomain(Base):
    """
    租户自定义域名

    支持租户绑定自定义域名, 用于品牌化访问。
    """
    __tablename__ = "tenant_domains"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tenants.tenant_id", ondelete="CASCADE"), index=True, nullable=False
    )
    domain: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    verification_token: Mapped[Optional[str]] = mapped_column(String(128))
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    ssl_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    ssl_certificate: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_domain_tenant_primary", "tenant_id", "is_primary"),
    )


# ========== TenantDataExport (数据导出任务) ==========
class TenantDataExport(Base):
    """
    租户数据导出任务

    记录租户数据导出请求, 支持全量/增量导出, 多种格式。
    """
    __tablename__ = "tenant_data_exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    export_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("tenants.tenant_id", ondelete="CASCADE"), index=True, nullable=False
    )

    status: Mapped[str] = mapped_column(String(16), default="pending", index=True, nullable=False)
    format: Mapped[str] = mapped_column(String(16), default="json", index=True)

    data_types: Mapped[Optional[List[str]]] = mapped_column(JSON)
    date_range_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    date_range_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    file_url: Mapped[Optional[str]] = mapped_column(Text)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    record_count: Mapped[Optional[int]] = mapped_column(Integer)

    requested_by: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    expired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)

    error_message: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_export_tenant_status", "tenant_id", "status"),
        Index("idx_export_completed_at", "completed_at"),
    )


# ========== 上下文管理 ==========
class TenantContext:
    """
    租户上下文管理

    用于在请求处理过程中跟踪当前租户, 实现数据隔离。
    """
    _current_tenant_id: Optional[str] = None
    _current_tenant: Optional[Tenant] = None

    @classmethod
    def set_tenant(cls, tenant_id: str, tenant: Optional[Tenant] = None):
        cls._current_tenant_id = tenant_id
        cls._current_tenant = tenant

    @classmethod
    def get_tenant_id(cls) -> Optional[str]:
        return cls._current_tenant_id

    @classmethod
    def get_tenant(cls) -> Optional[Tenant]:
        return cls._current_tenant

    @classmethod
    def clear(cls):
        cls._current_tenant_id = None
        cls._current_tenant = None


# ========== 租户服务类 (框架性实现) ==========
class TenantService:
    """
    租户服务 - 框架性实现

    提供租户生命周期管理、配额检查、数据隔离等核心功能。
    """

    @staticmethod
    def generate_tenant_id() -> str:
        """生成租户 ID"""
        import uuid
        return f"tnt_{uuid.uuid4().hex[:12]}"

    @staticmethod
    async def create_tenant(
        name: str,
        tier: str = TenantTier.FREE.value,
        contact_email: Optional[str] = None,
        **kwargs
    ) -> Tenant:
        """
        创建租户

        框架性实现 - 实际项目中需要:
        1. 创建租户记录
        2. 初始化租户配置
        3. 初始化配额
        4. 初始化计费
        5. 创建 schema (schema 隔离模式)
        6. 初始化默认数据
        """
        from core.db import Database
        from sqlalchemy import select

        tenant_id = TenantService.generate_tenant_id()

        async with Database.session() as session:
            tenant = Tenant(
                tenant_id=tenant_id,
                name=name,
                display_name=kwargs.get("display_name", name),
                tier=tier,
                contact_email=contact_email,
                status=TenantStatus.TRIALING.value,
                **{k: v for k, v in kwargs.items() if k in [
                    "contact_name", "contact_phone", "region", "address",
                    "website", "industry", "employee_count", "logo_url"
                ]}
            )
            session.add(tenant)

            config = TenantConfig(
                tenant_id=tenant_id,
                features_enabled={
                    "case_search": True,
                    "contract_review": True,
                    "document_generation": tier != TenantTier.FREE.value,
                    "ai_services": tier != TenantTier.FREE.value,
                    "team_collaboration": tier in [TenantTier.PRO.value, TenantTier.ENTERPRISE.value],
                    "api_access": tier in [TenantTier.PRO.value, TenantTier.ENTERPRISE.value],
                    "sso": tier == TenantTier.ENTERPRISE.value,
                    "audit_log": tier == TenantTier.ENTERPRISE.value,
                    "custom_branding": tier == TenantTier.ENTERPRISE.value,
                },
            )
            session.add(config)

            default_quotas = {
                TenantTier.FREE.value: {"max_users": 3, "max_storage_gb": 5, "max_api_calls_monthly": 1000, "max_cases": 100, "max_documents": 50, "max_ai_credits_monthly": 10, "max_concurrent_crawlers": 1},
                TenantTier.BASIC.value: {"max_users": 10, "max_storage_gb": 50, "max_api_calls_monthly": 10000, "max_cases": 1000, "max_documents": 500, "max_ai_credits_monthly": 100, "max_concurrent_crawlers": 2},
                TenantTier.PRO.value: {"max_users": 50, "max_storage_gb": 200, "max_api_calls_monthly": 100000, "max_cases": 10000, "max_documents": 5000, "max_ai_credits_monthly": 1000, "max_concurrent_crawlers": 5},
                TenantTier.ENTERPRISE.value: {"max_users": 500, "max_storage_gb": 1000, "max_api_calls_monthly": 1000000, "max_cases": 100000, "max_documents": 50000, "max_ai_credits_monthly": 10000, "max_concurrent_crawlers": 20},
            }
            quotas = default_quotas.get(tier, default_quotas[TenantTier.FREE.value])

            quota = TenantQuota(
                tenant_id=tenant_id,
                **quotas,
            )
            session.add(quota)

            plan_prices = {
                TenantTier.FREE.value: ("free", "免费版", Decimal("0.00"), Decimal("0.00")),
                TenantTier.BASIC.value: ("basic", "基础版", Decimal("299.00"), Decimal("2999.00")),
                TenantTier.PRO.value: ("professional", "专业版", Decimal("999.00"), Decimal("9999.00")),
                TenantTier.ENTERPRISE.value: ("enterprise", "企业版", Decimal("4999.00"), Decimal("49999.00")),
            }
            plan_code, plan_name, price_monthly, price_yearly = plan_prices.get(
                tier, plan_prices[TenantTier.FREE.value]
            )

            billing = TenantBilling(
                tenant_id=tenant_id,
                plan_code=plan_code,
                plan_name=plan_name,
                price_monthly=price_monthly,
                price_yearly=price_yearly,
            )
            session.add(billing)

            await session.commit()
            await session.refresh(tenant)

            return tenant

    @staticmethod
    async def check_quota(tenant_id: str, resource: str, amount: int = 1) -> bool:
        """
        检查租户配额

        框架性实现 - 检查指定资源是否还有足够配额。
        """
        from core.db import Database
        from sqlalchemy import select

        async with Database.session() as session:
            stmt = select(TenantQuota).where(TenantQuota.tenant_id == tenant_id)
            result = await session.execute(stmt)
            quota = result.scalar_one_or_none()

            if not quota:
                return False

            quota_map = {
                "users": ("max_users", "used_users"),
                "storage": ("max_storage_gb", "used_storage_bytes"),
                "api_calls": ("max_api_calls_monthly", "used_api_calls"),
                "cases": ("max_cases", "used_cases"),
                "documents": ("max_documents", "used_documents"),
                "ai_credits": ("max_ai_credits_monthly", "used_ai_credits"),
                "crawlers": ("max_concurrent_crawlers", None),
            }

            if resource not in quota_map:
                return True

            max_attr, used_attr = quota_map[resource]
            max_val = getattr(quota, max_attr)

            if resource == "storage":
                used_gb = getattr(quota, used_attr) / (1024 ** 3)
                return used_gb + amount <= max_val
            elif used_attr:
                used_val = getattr(quota, used_attr)
                return used_val + amount <= max_val
            else:
                return amount <= max_val

    @staticmethod
    async def suspend_tenant(tenant_id: str, reason: Optional[str] = None) -> bool:
        """
        暂停租户

        框架性实现 - 暂停租户服务, 禁止访问。
        """
        from core.db import Database
        from sqlalchemy import select

        async with Database.session() as session:
            stmt = select(Tenant).where(Tenant.tenant_id == tenant_id)
            result = await session.execute(stmt)
            tenant = result.scalar_one_or_none()

            if not tenant:
                return False

            tenant.status = TenantStatus.SUSPENDED.value
            tenant.suspended_at = func.now()
            tenant.suspend_reason = reason
            tenant.updated_at = func.now()

            await session.commit()
            return True

    @staticmethod
    async def activate_tenant(tenant_id: str) -> bool:
        """
        激活租户

        框架性实现 - 恢复租户服务。
        """
        from core.db import Database
        from sqlalchemy import select

        async with Database.session() as session:
            stmt = select(Tenant).where(Tenant.tenant_id == tenant_id)
            result = await session.execute(stmt)
            tenant = result.scalar_one_or_none()

            if not tenant:
                return False

            tenant.status = TenantStatus.ACTIVE.value
            tenant.activated_at = func.now()
            tenant.suspended_at = None
            tenant.suspend_reason = None
            tenant.updated_at = func.now()

            await session.commit()
            return True

    @staticmethod
    async def delete_tenant(tenant_id: str, hard_delete: bool = False) -> bool:
        """
        删除租户

        框架性实现 - 软删除/硬删除租户数据。
        """
        from core.db import Database
        from sqlalchemy import select

        async with Database.session() as session:
            stmt = select(Tenant).where(Tenant.tenant_id == tenant_id)
            result = await session.execute(stmt)
            tenant = result.scalar_one_or_none()

            if not tenant:
                return False

            if hard_delete:
                await session.delete(tenant)
            else:
                tenant.status = TenantStatus.DELETED.value
                tenant.deleted_at = func.now()
                tenant.updated_at = func.now()

            await session.commit()
            return True

    @staticmethod
    async def export_data(
        tenant_id: str,
        requested_by: int,
        data_types: Optional[List[str]] = None,
        format: str = "json",
        date_range: Optional[tuple] = None,
    ) -> str:
        """
        导出租户数据

        框架性实现 - 创建数据导出任务, 异步执行。
        """
        import uuid
        from core.db import Database

        export_id = f"exp_{uuid.uuid4().hex[:16]}"

        async with Database.session() as session:
            export = TenantDataExport(
                export_id=export_id,
                tenant_id=tenant_id,
                status="pending",
                format=format,
                data_types=data_types or ["all"],
                requested_by=requested_by,
            )
            if date_range:
                export.date_range_start, export.date_range_end = date_range

            session.add(export)
            await session.commit()

        return export_id

    @staticmethod
    async def migrate_data(source_tenant_id: str, target_tenant_id: str, data_types: Optional[List[str]] = None) -> bool:
        """
        迁移租户数据

        框架性实现 - 在租户间迁移数据。
        """
        return True


# ========== 缓存隔离 ==========
class TenantCache:
    """
    租户缓存隔离

    为每个租户提供独立的缓存命名空间, 防止数据交叉。
    """

    @staticmethod
    def make_key(tenant_id: str, key: str) -> str:
        """生成带租户前缀的缓存键"""
        return f"tenant:{tenant_id}:{key}"

    @staticmethod
    def make_pattern(tenant_id: str) -> str:
        """生成租户缓存键模式, 用于批量清除"""
        return f"tenant:{tenant_id}:*"

    @staticmethod
    async def get(tenant_id: str, key: str) -> Optional[Any]:
        """获取租户缓存 (框架性实现)"""
        full_key = TenantCache.make_key(tenant_id, key)
        return None

    @staticmethod
    async def set(tenant_id: str, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置租户缓存 (框架性实现)"""
        full_key = TenantCache.make_key(tenant_id, key)
        pass

    @staticmethod
    async def delete(tenant_id: str, key: str) -> None:
        """删除租户缓存 (框架性实现)"""
        full_key = TenantCache.make_key(tenant_id, key)
        pass

    @staticmethod
    async def clear_tenant(tenant_id: str) -> int:
        """清除租户所有缓存 (框架性实现)"""
        pattern = TenantCache.make_pattern(tenant_id)
        return 0
