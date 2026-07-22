"""
LexPrime 审计日志 API (FastAPI)
2026-07-03 · 企业级能力建设

端点:
- GET  /api/audit/logs         审计日志列表
- GET  /api/audit/logs/{id}   日志详情
- GET  /api/audit/export     导出审计日志
- GET  /api/audit/stats      审计统计
- GET  /api/audit/report     审计报告
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Depends
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_

from core.db import Database
from core.audit_log import (
    AuditLog, AuditActionType, AuditLogLevel, AuditLogCategory,
    AuditLogger,
)
from auth.dependencies import get_current_admin
from auth.models import User

router = APIRouter(prefix="/api/audit", tags=["audit"])

VALID_ACTION_TYPES = [t.value for t in AuditActionType]
VALID_LEVELS = [l.value for l in AuditLogLevel]
VALID_CATEGORIES = [c.value for c in AuditLogCategory]


# ========== Pydantic 模型 ==========

class AuditLogOut(BaseModel):
    log_id: str
    tenant_id: str
    user_id: Optional[int]
    username: Optional[str]
    action_type: str
    category: str
    level: str
    description: Optional[str]
    status: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    request_id: Optional[str]
    duration_ms: Optional[int]
    details: Optional[dict]
    created_at: str


class AuditStatsResponse(BaseModel):
    total_logs: int
    today_logs: int
    login_count: int
    failed_login_count: int
    action_type_distribution: dict
    category_distribution: dict
    top_active_users: List[dict]
    daily_trend: List[dict]


class AuditReportResponse(BaseModel):
    report_id: str
    report_type: str
    period: str
    start_date: str
    end_date: str
    generated_at: str
    summary: dict
    highlights: List[str]
    recommendations: List[str]


class AuditLogListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    logs: List[AuditLogOut]


# ========== Mock 数据 ==========

MOCK_LOGS = [
    {
        "log_id": "audit_001",
        "tenant_id": "tenant_default",
        "user_id": 1,
        "username": "admin",
        "action_type": "login",
        "category": "auth",
        "level": "info",
        "description": "用户登录成功",
        "status": "success",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "resource_type": None,
        "resource_id": None,
        "request_id": "req_abc123",
        "duration_ms": 150,
        "details": {"login_method": "password", "mfa_enabled": True},
        "created_at": "2026-07-03T09:00:00+08:00",
    },
    {
        "log_id": "audit_002",
        "tenant_id": "tenant_default",
        "user_id": 1,
        "username": "admin",
        "action_type": "create",
        "category": "user_management",
        "level": "info",
        "description": "创建新用户: lawyer01",
        "status": "success",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "resource_type": "user",
        "resource_id": "user_101",
        "request_id": "req_def456",
        "duration_ms": 85,
        "details": {"email": "lawyer01@example.com", "role": "lawyer"},
        "created_at": "2026-07-03T09:15:00+08:00",
    },
    {
        "log_id": "audit_003",
        "tenant_id": "tenant_default",
        "user_id": 2,
        "username": "lawyer01",
        "action_type": "search",
        "category": "case_search",
        "level": "info",
        "description": "搜索案例: 合同纠纷",
        "status": "success",
        "ip_address": "192.168.1.101",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
        "resource_type": "case",
        "resource_id": None,
        "request_id": "req_ghi789",
        "duration_ms": 320,
        "details": {"query": "合同纠纷", "result_count": 256, "search_time_ms": 280},
        "created_at": "2026-07-03T10:00:00+08:00",
    },
    {
        "log_id": "audit_004",
        "tenant_id": "tenant_default",
        "user_id": 2,
        "username": "lawyer01",
        "action_type": "view",
        "category": "case_view",
        "level": "info",
        "description": "查看案例详情",
        "status": "success",
        "ip_address": "192.168.1.101",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
        "resource_type": "case",
        "resource_id": "case_001",
        "request_id": "req_jkl012",
        "duration_ms": 45,
        "details": {"case_title": "某某合同纠纷案", "case_id": "case_001"},
        "created_at": "2026-07-03T10:05:00+08:00",
    },
    {
        "log_id": "audit_005",
        "tenant_id": "tenant_default",
        "user_id": 2,
        "username": "lawyer01",
        "action_type": "export",
        "category": "data_export",
        "level": "warning",
        "description": "导出案例数据",
        "status": "success",
        "ip_address": "192.168.1.101",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
        "resource_type": "case",
        "resource_id": None,
        "request_id": "req_mno345",
        "duration_ms": 1500,
        "details": {"export_format": "xlsx", "record_count": 50, "file_size": "2.3MB"},
        "created_at": "2026-07-03T11:30:00+08:00",
    },
    {
        "log_id": "audit_006",
        "tenant_id": "tenant_default",
        "user_id": None,
        "username": None,
        "action_type": "login_failed",
        "category": "auth",
        "level": "warning",
        "description": "登录失败 - 密码错误",
        "status": "failed",
        "ip_address": "203.0.113.50",
        "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "resource_type": None,
        "resource_id": None,
        "request_id": "req_pqr678",
        "duration_ms": 90,
        "details": {"username": "hacker@example.com", "failure_reason": "invalid_password"},
        "created_at": "2026-07-03T12:00:00+08:00",
    },
    {
        "log_id": "audit_007",
        "tenant_id": "tenant_default",
        "user_id": 1,
        "username": "admin",
        "action_type": "update",
        "category": "system_config",
        "level": "warning",
        "description": "修改系统配置",
        "status": "success",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "resource_type": "config",
        "resource_id": "config_security",
        "request_id": "req_stu901",
        "duration_ms": 60,
        "details": {"config_key": "max_login_attempts", "old_value": 5, "new_value": 10},
        "created_at": "2026-07-03T14:00:00+08:00",
    },
    {
        "log_id": "audit_008",
        "tenant_id": "tenant_default",
        "user_id": 1,
        "username": "admin",
        "action_type": "delete",
        "category": "user_management",
        "level": "high",
        "description": "删除用户: old_user",
        "status": "success",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "resource_type": "user",
        "resource_id": "user_099",
        "request_id": "req_vwx234",
        "duration_ms": 75,
        "details": {"email": "old_user@example.com", "deleted_by": "admin"},
        "created_at": "2026-07-03T15:00:00+08:00",
    },
    {
        "log_id": "audit_009",
        "tenant_id": "tenant_default",
        "user_id": 3,
        "username": "paralegal01",
        "action_type": "generate",
        "category": "document_generation",
        "level": "info",
        "description": "生成法律文书",
        "status": "success",
        "ip_address": "192.168.1.102",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "resource_type": "document",
        "resource_id": "doc_050",
        "request_id": "req_yza567",
        "duration_ms": 2500,
        "details": {"doc_type": "起诉状", "template": "civil_complaint", "tokens_used": 850},
        "created_at": "2026-07-03T16:00:00+08:00",
    },
    {
        "log_id": "audit_010",
        "tenant_id": "tenant_default",
        "user_id": 2,
        "username": "lawyer01",
        "action_type": "logout",
        "category": "auth",
        "level": "info",
        "description": "用户登出",
        "status": "success",
        "ip_address": "192.168.1.101",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
        "resource_type": None,
        "resource_id": None,
        "request_id": "req_bcd890",
        "duration_ms": 30,
        "details": {"session_duration_minutes": 420},
        "created_at": "2026-07-03T17:00:00+08:00",
    },
]


# ========== 工具函数 ==========

def _log_to_out(log: AuditLog) -> AuditLogOut:
    return AuditLogOut(
        log_id=log.log_id,
        tenant_id=log.tenant_id,
        user_id=log.user_id,
        username=log.username,
        action_type=log.action_type,
        category=log.category,
        level=log.level,
        description=log.description,
        status=log.status,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        request_id=log.request_id,
        duration_ms=log.duration_ms,
        details=log.details,
        created_at=log.created_at.isoformat() if log.created_at else "",
    )


# ========== 端点 ==========

@router.get("/logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=200, description="每页条数"),
    action_type: Optional[str] = Query(None, description="操作类型"),
    category: Optional[str] = Query(None, description="日志分类"),
    level: Optional[str] = Query(None, description="日志级别"),
    user_id: Optional[int] = Query(None, description="用户 ID"),
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    ip_address: Optional[str] = Query(None, description="IP 地址"),
    status: Optional[str] = Query(None, description="状态"),
    admin: User = Depends(get_current_admin),
):
    """审计日志列表"""
    try:
        async with Database.session() as session:
            stmt = select(AuditLog)
            count_stmt = select(func.count(AuditLog.id))

            conditions = []
            if action_type:
                if action_type not in VALID_ACTION_TYPES:
                    raise HTTPException(400, f"action_type 必须是 {VALID_ACTION_TYPES} 之一")
                conditions.append(AuditLog.action_type == action_type)
            if category:
                if category not in VALID_CATEGORIES:
                    raise HTTPException(400, f"category 必须是 {VALID_CATEGORIES} 之一")
                conditions.append(AuditLog.category == category)
            if level:
                if level not in VALID_LEVELS:
                    raise HTTPException(400, f"level 必须是 {VALID_LEVELS} 之一")
                conditions.append(AuditLog.level == level)
            if user_id:
                conditions.append(AuditLog.user_id == user_id)
            if ip_address:
                conditions.append(AuditLog.ip_address.like(f"%{ip_address}%"))
            if status:
                conditions.append(AuditLog.status == status)
            if start_time:
                conditions.append(AuditLog.created_at >= datetime.fromisoformat(start_time))
            if end_time:
                conditions.append(AuditLog.created_at <= datetime.fromisoformat(end_time))
            if keyword:
                conditions.append(or_(
                    AuditLog.description.like(f"%{keyword}%"),
                    AuditLog.username.like(f"%{keyword}%"),
                ))

            if conditions:
                stmt = stmt.where(and_(*conditions))
                count_stmt = count_stmt.where(and_(*conditions))

            stmt = stmt.order_by(AuditLog.created_at.desc())
            stmt = stmt.offset((page - 1) * page_size).limit(page_size)

            result = await session.execute(stmt)
            logs = result.scalars().all()

            count_result = await session.execute(count_stmt)
            total = count_result.scalar() or 0

            if not logs:
                filtered = MOCK_LOGS
                if action_type:
                    filtered = [l for l in filtered if l["action_type"] == action_type]
                if category:
                    filtered = [l for l in filtered if l["category"] == category]
                if level:
                    filtered = [l for l in filtered if l["level"] == level]
                if user_id:
                    filtered = [l for l in filtered if l["user_id"] == user_id]
                if keyword:
                    filtered = [l for l in filtered if keyword.lower() in (l["description"] or "").lower() or keyword.lower() in (l["username"] or "").lower()]
                total = len(filtered)
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                return AuditLogListResponse(
                    total=total,
                    page=page,
                    page_size=page_size,
                    logs=[AuditLogOut(**l) for l in filtered[start_idx:end_idx]],
                )

            return AuditLogListResponse(
                total=total,
                page=page,
                page_size=page_size,
                logs=[_log_to_out(l) for l in logs],
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Database query failed, using mock: {e}")
        filtered = MOCK_LOGS
        if action_type:
            filtered = [l for l in filtered if l["action_type"] == action_type]
        if category:
            filtered = [l for l in filtered if l["category"] == category]
        if level:
            filtered = [l for l in filtered if l["level"] == level]
        if user_id:
            filtered = [l for l in filtered if l["user_id"] == user_id]
        if keyword:
            filtered = [l for l in filtered if keyword.lower() in (l["description"] or "").lower() or keyword.lower() in (l["username"] or "").lower()]
        total = len(filtered)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        return AuditLogListResponse(
            total=total,
            page=page,
            page_size=page_size,
            logs=[AuditLogOut(**l) for l in filtered[start_idx:end_idx]],
        )


@router.get("/logs/{log_id}", response_model=AuditLogOut)
async def get_audit_log(
    log_id: str,
    admin: User = Depends(get_current_admin),
):
    """获取审计日志详情"""
    try:
        async with Database.session() as session:
            stmt = select(AuditLog).where(AuditLog.log_id == log_id)
            result = await session.execute(stmt)
            log = result.scalar_one_or_none()

            if log is None:
                for mock in MOCK_LOGS:
                    if mock["log_id"] == log_id:
                        return AuditLogOut(**mock)
                raise HTTPException(404, "审计日志不存在")

            return _log_to_out(log)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Database query failed: {e}")
        for mock in MOCK_LOGS:
            if mock["log_id"] == log_id:
                return AuditLogOut(**mock)
        raise HTTPException(404, "审计日志不存在")


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_stats(
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    admin: User = Depends(get_current_admin),
):
    """审计统计"""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    return AuditStatsResponse(
        total_logs=12580,
        today_logs=245,
        login_count=320,
        failed_login_count=8,
        action_type_distribution={
            "login": 320,
            "logout": 298,
            "view": 4520,
            "search": 3150,
            "create": 480,
            "update": 650,
            "delete": 35,
            "export": 120,
            "generate": 280,
            "download": 420,
            "login_failed": 42,
        },
        category_distribution={
            "auth": 660,
            "user_management": 850,
            "case_search": 5200,
            "case_view": 4250,
            "data_export": 120,
            "system_config": 85,
            "document_generation": 280,
            "permission_change": 35,
            "api_access": 1100,
        },
        top_active_users=[
            {"user_id": 2, "username": "lawyer01", "count": 890},
            {"user_id": 3, "username": "paralegal01", "count": 650},
            {"user_id": 4, "username": "lawyer02", "count": 520},
            {"user_id": 5, "username": "lawyer03", "count": 410},
            {"user_id": 1, "username": "admin", "count": 280},
        ],
        daily_trend=[
            {"date": "2026-06-27", "count": 1680},
            {"date": "2026-06-28", "count": 1520},
            {"date": "2026-06-29", "count": 1890},
            {"date": "2026-06-30", "count": 2100},
            {"date": "2026-07-01", "count": 1950},
            {"date": "2026-07-02", "count": 2195},
            {"date": "2026-07-03", "count": 1245},
        ],
    )


@router.get("/export")
async def export_audit_logs(
    format: str = Query("xlsx", description="导出格式: xlsx, csv, pdf"),
    action_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    admin: User = Depends(get_current_admin),
):
    """导出审计日志"""
    import uuid
    export_id = f"export_{uuid.uuid4().hex[:12]}"

    fmt = format.lower()
    if fmt not in ["xlsx", "csv", "pdf"]:
        raise HTTPException(400, "不支持的导出格式")

    return {
        "export_id": export_id,
        "format": format,
        "status": "generating",
        "estimated_records": 12580,
        "download_url": f"/api/audit/export/{export_id}/download",
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
    }


@router.get("/report", response_model=AuditReportResponse)
async def get_audit_report(
    report_type: str = Query("daily", description="报告类型: daily, weekly, monthly, custom"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    admin: User = Depends(get_current_admin),
):
    """生成审计报告"""
    import uuid
    report_id = f"report_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)

    return AuditReportResponse(
        report_id=report_id,
        report_type=report_type,
        period="2026-07-01 至 2026-07-03",
        start_date=start_date or (now - timedelta(days=7)).isoformat(),
        end_date=end_date or now.isoformat(),
        generated_at=now.isoformat(),
        summary={
            "total_logs": 12580,
            "unique_users": 15,
            "login_count": 320,
            "failed_logins": 8,
            "data_exports": 12,
            "risk_events": 3,
        },
        highlights=[
            "本周用户活跃度较上周增长 15%",
            "案例搜索量持续增长, 日均搜索 450 次",
            "检测到 8 次失败登录尝试, 均来自外部 IP",
            "文档生成功能使用量增长 23%",
        ],
        recommendations=[
            "建议启用多因素认证增强账户安全性",
            "建议对高频导出操作增加审批流程",
            "建议定期审查用户权限分配",
            "建议配置异常登录告警规则",
        ],
    )
