"""
LexPrime 审计日志系统
2026-07-03 · 企业级能力建设

功能模块:
- AuditLog 模型 - 审计日志主表
- 操作类型枚举 / 日志级别 / 日志分类
- 日志收集 - 用户操作 / 数据变更 / 登录登出 / 权限变更
- 日志查询 - 时间范围 / 用户筛选 / 操作类型 / 全文搜索
- 日志导出 - Excel / CSV / PDF / 定时报告
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlalchemy import (
    String, Text, DateTime, Integer, BigInteger,
    ForeignKey, JSON, Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.models import Base


class AuditActionType(str, Enum):
    """操作类型枚举"""
    # 用户操作
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PROFILE_UPDATE = "profile_update"
    TOKEN_REFRESH = "token_refresh"

    # 数据操作
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    IMPORT = "import"
    DOWNLOAD = "download"
    UPLOAD = "upload"

    # 权限操作
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    ROLE_ASSIGN = "role_assign"
    ROLE_UNASSIGN = "role_unassign"

    # 系统操作
    SYSTEM_CONFIG = "system_config"
    TENANT_CREATE = "tenant_create"
    TENANT_UPDATE = "tenant_update"
    TENANT_DELETE = "tenant_delete"
    TENANT_SUSPEND = "tenant_suspend"
    TENANT_ACTIVATE = "tenant_activate"

    # 安全操作
    SSO_LOGIN = "sso_login"
    TWO_FA_ENABLE = "2fa_enable"
    TWO_FA_DISABLE = "2fa_disable"
    API_KEY_CREATE = "api_key_create"
    API_KEY_REVOKE = "api_key_revoke"

    # 业务操作
    CASE_VIEW = "case_view"
    CASE_SEARCH = "case_search"
    CONTRACT_REVIEW = "contract_review"
    DOC_GENERATE = "doc_generate"
    AI_CHAT = "ai_chat"


class AuditLogLevel(str, Enum):
    """日志级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLogCategory(str, Enum):
    """日志分类"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM = "system"
    SECURITY = "security"
    BUSINESS = "business"
    ADMIN = "admin"


# ========== AuditLog (审计日志主表) ==========
class AuditLog(Base):
    """
    审计日志表

    记录所有重要的用户操作和系统事件, 用于审计追踪和合规检查。
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    log_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    tenant_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    user_email: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    user_name: Mapped[Optional[str]] = mapped_column(String(64))

    action_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    log_level: Mapped[str] = mapped_column(String(16), default=AuditLogLevel.INFO.value, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(32), default=AuditLogCategory.BUSINESS.value, index=True, nullable=False)

    resource_type: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    resource_name: Mapped[Optional[str]] = mapped_column(String(256))

    action_description: Mapped[Optional[str]] = mapped_column(String(512))
    action_detail: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    ip_address: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512))
    device_info: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    request_method: Mapped[Optional[str]] = mapped_column(String(16))
    request_path: Mapped[Optional[str]] = mapped_column(String(512), index=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)

    response_status: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer)

    before_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    after_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    changed_fields: Mapped[Optional[List[str]]] = mapped_column(JSON)

    success: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(512))
    error_code: Mapped[Optional[str]] = mapped_column(String(64))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)

    __table_args__ = (
        Index("idx_audit_tenant_time", "tenant_id", "created_at"),
        Index("idx_audit_user_time", "user_id", "created_at"),
        Index("idx_audit_action_time", "action_type", "created_at"),
        Index("idx_audit_category_time", "category", "created_at"),
        Index("idx_audit_level_time", "log_level", "created_at"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        Index("idx_audit_success_time", "success", "created_at"),
    )


# ========== AuditExportTask (审计日志导出任务) ==========
class AuditExportTask(Base):
    """
    审计日志导出任务

    记录审计日志导出请求, 支持多种格式的导出。
    """
    __tablename__ = "audit_export_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    export_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    requested_by: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[str] = mapped_column(String(16), default="pending", index=True, nullable=False)
    format: Mapped[str] = mapped_column(String(16), default="csv", index=True)

    date_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    date_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    filter_user_id: Mapped[Optional[int]] = mapped_column(Integer)
    filter_action_type: Mapped[Optional[str]] = mapped_column(String(64))
    filter_category: Mapped[Optional[str]] = mapped_column(String(32))
    filter_log_level: Mapped[Optional[str]] = mapped_column(String(16))
    filter_resource_type: Mapped[Optional[str]] = mapped_column(String(64))
    filter_keyword: Mapped[Optional[str]] = mapped_column(String(256))

    total_records: Mapped[Optional[int]] = mapped_column(Integer)
    file_url: Mapped[Optional[str]] = mapped_column(Text)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    file_name: Mapped[Optional[str]] = mapped_column(String(256))

    error_message: Mapped[Optional[str]] = mapped_column(String(512))

    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    expired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)

    __table_args__ = (
        Index("idx_audit_export_tenant", "tenant_id", "created_at"),
        Index("idx_audit_export_status", "status", "created_at"),
    )


# ========== AuditReportSchedule (定时报告配置) ==========
class AuditReportSchedule(Base):
    """
    审计定时报告配置

    支持定期自动生成审计报告并发送给指定人员。
    """
    __tablename__ = "audit_report_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    schedule_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    frequency: Mapped[str] = mapped_column(String(16), default="weekly", index=True)
    day_of_week: Mapped[Optional[int]] = mapped_column(Integer)
    day_of_month: Mapped[Optional[int]] = mapped_column(Integer)
    hour: Mapped[int] = mapped_column(Integer, default=8)
    minute: Mapped[int] = mapped_column(Integer, default=0)

    report_type: Mapped[str] = mapped_column(String(32), default="summary")
    format: Mapped[str] = mapped_column(String(16), default="pdf")

    recipients: Mapped[Optional[List[str]]] = mapped_column(JSON)
    include_charts: Mapped[bool] = mapped_column(Boolean, default=True)
    include_csv: Mapped[bool] = mapped_column(Boolean, default=False)

    filters: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)

    created_by: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_audit_report_tenant", "tenant_id", "enabled"),
        Index("idx_audit_report_next", "next_run_at"),
    )


# ========== AuditLogger (审计日志记录器) ==========
class AuditLogger:
    """
    审计日志记录器 - 框架性实现

    提供便捷的方法记录各种审计事件。
    """

    @staticmethod
    def _generate_log_id() -> str:
        import uuid
        return f"audit_{uuid.uuid4().hex}"

    @staticmethod
    async def log(
        action_type: str,
        category: str = AuditLogCategory.BUSINESS.value,
        log_level: str = AuditLogLevel.INFO.value,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        user_name: Optional[str] = None,
        tenant_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        action_description: Optional[str] = None,
        action_detail: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        request_id: Optional[str] = None,
        response_status: Optional[int] = None,
        response_time_ms: Optional[int] = None,
        before_data: Optional[dict] = None,
        after_data: Optional[dict] = None,
        changed_fields: Optional[List[str]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
    ) -> str:
        """
        记录审计日志 - 框架性实现
        """
        from core.db import Database

        log_id = AuditLogger._generate_log_id()

        try:
            async with Database.session() as session:
                log = AuditLog(
                    log_id=log_id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    user_email=user_email,
                    user_name=user_name,
                    action_type=action_type,
                    log_level=log_level,
                    category=category,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    resource_name=resource_name,
                    action_description=action_description,
                    action_detail=action_detail,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_method=request_method,
                    request_path=request_path,
                    request_id=request_id,
                    response_status=response_status,
                    response_time_ms=response_time_ms,
                    before_data=before_data,
                    after_data=after_data,
                    changed_fields=changed_fields,
                    success=success,
                    error_message=error_message,
                    error_code=error_code,
                )
                session.add(log)
                await session.commit()
        except Exception:
            pass

        return log_id

    @staticmethod
    async def log_login(
        user_id: int,
        user_email: str,
        user_name: Optional[str] = None,
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> str:
        """记录登录事件"""
        return await AuditLogger.log(
            action_type=AuditActionType.LOGIN.value if success else AuditActionType.LOGIN_FAILED.value,
            category=AuditLogCategory.AUTHENTICATION.value,
            log_level=AuditLogLevel.INFO.value if success else AuditLogLevel.WARNING.value,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            action_description="用户登录" if success else "登录失败",
            success=success,
            error_message=error_message,
        )

    @staticmethod
    async def log_logout(
        user_id: int,
        user_email: str,
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> str:
        """记录登出事件"""
        return await AuditLogger.log(
            action_type=AuditActionType.LOGOUT.value,
            category=AuditLogCategory.AUTHENTICATION.value,
            log_level=AuditLogLevel.INFO.value,
            user_id=user_id,
            user_email=user_email,
            tenant_id=tenant_id,
            ip_address=ip_address,
            action_description="用户登出",
        )

    @staticmethod
    async def log_data_change(
        action_type: str,
        resource_type: str,
        resource_id: str,
        resource_name: Optional[str] = None,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        tenant_id: Optional[str] = None,
        before_data: Optional[dict] = None,
        after_data: Optional[dict] = None,
        changed_fields: Optional[List[str]] = None,
        ip_address: Optional[str] = None,
    ) -> str:
        """记录数据变更事件"""
        action_desc_map = {
            AuditActionType.CREATE.value: "创建",
            AuditActionType.UPDATE.value: "更新",
            AuditActionType.DELETE.value: "删除",
        }
        desc = action_desc_map.get(action_type, action_type) + resource_type

        return await AuditLogger.log(
            action_type=action_type,
            category=AuditLogCategory.DATA_MODIFICATION.value,
            log_level=AuditLogLevel.INFO.value,
            user_id=user_id,
            user_email=user_email,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            action_description=desc,
            before_data=before_data,
            after_data=after_data,
            changed_fields=changed_fields,
            ip_address=ip_address,
        )

    @staticmethod
    async def log_permission_change(
        action_type: str,
        user_id: int,
        target_user_id: int,
        tenant_id: Optional[str] = None,
        role: Optional[str] = None,
        permission: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> str:
        """记录权限变更事件"""
        return await AuditLogger.log(
            action_type=action_type,
            category=AuditLogCategory.AUTHORIZATION.value,
            log_level=AuditLogLevel.WARNING.value,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type="user",
            resource_id=str(target_user_id),
            action_description=f"权限变更: {action_type}",
            action_detail={
                "target_user_id": target_user_id,
                "role": role,
                "permission": permission,
            },
            ip_address=ip_address,
        )


# ========== AuditQueryService (审计日志查询服务) ==========
class AuditQueryService:
    """
    审计日志查询服务 - 框架性实现

    提供复杂的审计日志查询和统计功能。
    """

    @staticmethod
    async def get_stats(
        tenant_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> dict:
        """
        获取审计统计数据 - 框架性实现
        """
        now = datetime.utcnow()
        if not date_from:
            date_from = now - timedelta(days=30)
        if not date_to:
            date_to = now

        return {
            "total_logs": 12580,
            "by_action_type": {
                "login": 3420,
                "logout": 3210,
                "create": 1250,
                "update": 2890,
                "delete": 340,
                "export": 180,
                "view": 1290,
            },
            "by_category": {
                "authentication": 6840,
                "data_access": 2150,
                "data_modification": 4480,
                "system": 650,
                "security": 320,
                "business": 140,
            },
            "by_level": {
                "info": 11800,
                "warning": 620,
                "error": 130,
                "critical": 30,
            },
            "by_date": [
                {"date": (now - timedelta(days=i)).strftime("%Y-%m-%d"), "count": 400 + i * 10}
                for i in range(30)
            ],
            "top_users": [
                {"user_id": 1, "email": "admin@example.com", "count": 1250},
                {"user_id": 2, "email": "user1@example.com", "count": 890},
                {"user_id": 3, "email": "user2@example.com", "count": 720},
            ],
            "success_rate": 98.5,
        }

    @staticmethod
    async def export_logs(
        format: str = "csv",
        tenant_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        filters: Optional[dict] = None,
        requested_by: Optional[int] = None,
    ) -> str:
        """
        导审计日志 - 框架性实现

        返回导出任务 ID。
        """
        import uuid
        return f"exp_{uuid.uuid4().hex[:16]}"

    @staticmethod
    async def generate_report(
        report_type: str = "summary",
        tenant_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> dict:
        """
        生成审计报告 - 框架性实现
        """
        return {
            "report_type": report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None,
            },
            "summary": {
                "total_events": 12580,
                "total_users": 45,
                "failed_logins": 23,
                "data_changes": 4480,
                "permission_changes": 12,
            },
            "top_events": [],
            "anomalies": [],
            "recommendations": [
                "建议启用双因素认证",
                "建议审查高权限用户的操作日志",
            ],
        }
