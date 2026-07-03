"""
LexPrime 订阅计费系统 API Router

端点:
- GET /api/subscription/plans    - 套餐列表
- GET /api/subscription/current  - 当前订阅
- POST /api/subscription/subscribe - 订阅套餐
- POST /api/subscription/cancel  - 取消订阅
- GET /api/subscription/invoices - 账单列表
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from auth.db import get_db
from auth.dependencies import get_current_user
from auth.models import User, Plan, Subscription, Invoice

router = APIRouter(prefix="/api/subscription", tags=["subscription"])


# ========== Pydantic 模型 ==========

class PlanOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    tier: str
    billing_cycle: str
    price_monthly: float
    price_yearly: float
    currency: str
    trial_days: int
    features: Optional[dict] = None
    limits: Optional[dict] = None
    is_popular: bool = False
    sort_order: int = 0


class CurrentSubscriptionOut(BaseModel):
    id: Optional[int] = None
    plan_code: str
    plan_name: str
    status: str
    billing_cycle: str
    amount: float
    currency: str
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    trial_end: Optional[str] = None
    cancel_at_period_end: bool = False
    canceled_at: Optional[str] = None


class SubscribeRequest(BaseModel):
    plan_code: str = Field(..., description="套餐代码")
    billing_cycle: str = Field("monthly", description="计费周期: monthly/yearly")


class InvoiceOut(BaseModel):
    id: int
    invoice_no: str
    plan_code: str
    plan_name: str
    status: str
    amount: float
    currency: str
    discount: float
    billing_cycle: str
    payment_method: Optional[str] = None
    paid_at: Optional[str] = None
    created_at: str


# ========== 内置套餐数据 (首次启动自动同步到 DB) ==========

DEFAULT_PLANS = [
    {
        "code": "free",
        "name": "免费版",
        "description": "基础功能体验",
        "tier": "free",
        "billing_cycle": "monthly",
        "price_monthly": 0.0,
        "price_yearly": 0.0,
        "currency": "CNY",
        "trial_days": 0,
        "is_popular": False,
        "sort_order": 0,
        "features": {
            "ai_chat_daily": 3,
            "cases_limit": 3,
            "schedule_basic": True,
            "case_search": False,
            "doc_generation": False,
            "contract_review": False,
        },
        "limits": {
            "cases": 3,
            "ai_chat_monthly": 90,
            "storage_gb": 1,
        },
    },
    {
        "code": "basic",
        "name": "个人基础版",
        "description": "入门体验",
        "tier": "basic",
        "billing_cycle": "monthly",
        "price_monthly": 99.0,
        "price_yearly": 899.0,
        "currency": "CNY",
        "trial_days": 30,
        "is_popular": False,
        "sort_order": 1,
        "features": {
            "case_management": True,
            "client_management": True,
            "schedule": True,
            "templates": True,
            "case_search": True,
            "doc_generation": True,
            "storage_gb": 5,
            "support": "email_48h",
        },
        "limits": {
            "doc_generation_monthly": 200,
            "storage_gb": 5,
        },
    },
    {
        "code": "pro",
        "name": "个人专业版",
        "description": "最适合个人律师",
        "tier": "pro",
        "billing_cycle": "monthly",
        "price_monthly": 199.0,
        "price_yearly": 1910.0,
        "currency": "CNY",
        "trial_days": 30,
        "is_popular": True,
        "sort_order": 2,
        "features": {
            "case_management": True,
            "client_management": True,
            "schedule": True,
            "templates": True,
            "case_search": True,
            "doc_generation": True,
            "judicial_opinions": True,
            "legal_qa": True,
            "trial_prep": True,
            "batch_contract_review": True,
            "local_knowledge_base": True,
            "storage_gb": 20,
            "support": "priority_24h",
        },
        "limits": {
            "doc_generation_monthly": -1,
            "trial_prep_monthly": 50,
            "batch_contract_monthly": 20,
            "storage_gb": 20,
        },
    },
    {
        "code": "enterprise",
        "name": "企业版",
        "description": "适合律所及团队",
        "tier": "enterprise",
        "billing_cycle": "yearly",
        "price_monthly": 1500.0,
        "price_yearly": 15000.0,
        "currency": "CNY",
        "trial_days": 14,
        "is_popular": False,
        "sort_order": 3,
        "features": {
            "team_collaboration": True,
            "team_members": 10,
            "shared_knowledge_base": True,
            "analytics": True,
            "custom_sop": True,
            "dedicated_manager": True,
            "private_deployment": True,
            "storage_gb": 200,
            "support": "dedicated_7x24",
        },
        "limits": {
            "team_members": 10,
            "storage_gb": 200,
        },
    },
]


# ========== 工具函数 ==========

async def ensure_default_plans(db: AsyncSession):
    """确保默认套餐存在于数据库中"""
    result = await db.execute(select(Plan))
    existing = result.scalars().all()
    if existing:
        return

    for plan_data in DEFAULT_PLANS:
        plan = Plan(**plan_data)
        db.add(plan)
    await db.commit()
    logger.info("默认套餐已初始化")


def _plan_to_out(plan: Plan) -> PlanOut:
    return PlanOut(
        id=plan.id,
        code=plan.code,
        name=plan.name,
        description=plan.description,
        tier=plan.tier,
        billing_cycle=plan.billing_cycle,
        price_monthly=plan.price_monthly,
        price_yearly=plan.price_yearly,
        currency=plan.currency,
        trial_days=plan.trial_days,
        features=plan.features,
        limits=plan.limits,
        is_popular=plan.is_popular,
        sort_order=plan.sort_order,
    )


def _sub_to_out(sub: Subscription) -> CurrentSubscriptionOut:
    return CurrentSubscriptionOut(
        id=sub.id,
        plan_code=sub.plan_code,
        plan_name=sub.plan_name,
        status=sub.status,
        billing_cycle=sub.billing_cycle,
        amount=sub.amount,
        currency=sub.currency,
        current_period_start=sub.current_period_start.isoformat() if sub.current_period_start else None,
        current_period_end=sub.current_period_end.isoformat() if sub.current_period_end else None,
        trial_end=sub.trial_end.isoformat() if sub.trial_end else None,
        cancel_at_period_end=sub.cancel_at_period_end,
        canceled_at=sub.canceled_at.isoformat() if sub.canceled_at else None,
    )


def _invoice_to_out(inv: Invoice) -> InvoiceOut:
    return InvoiceOut(
        id=inv.id,
        invoice_no=inv.invoice_no,
        plan_code=inv.plan_code,
        plan_name=inv.plan_name,
        status=inv.status,
        amount=inv.amount,
        currency=inv.currency,
        discount=inv.discount,
        billing_cycle=inv.billing_cycle,
        payment_method=inv.payment_method,
        paid_at=inv.paid_at.isoformat() if inv.paid_at else None,
        created_at=inv.created_at.isoformat(),
    )


def generate_invoice_no() -> str:
    """生成账单号"""
    now = datetime.now(timezone.utc)
    random_str = uuid.uuid4().hex[:8].upper()
    return f"INV{now.strftime('%Y%m%d')}{random_str}"


# ========== 启动钩子 ==========

@router.on_event("startup")
async def _startup_init_plans():
    try:
        from auth.db import async_session_maker
        async with async_session_maker() as db:
            await ensure_default_plans(db)
    except Exception as e:
        logger.warning(f"默认套餐初始化失败 (非致命): {e}")


# ========== 端点 ==========

@router.get("/plans", response_model=List[PlanOut], summary="获取套餐列表")
async def get_plans(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    获取所有可用订阅套餐
    - 按 sort_order 排序
    - 只返回 active 的套餐
    """
    await ensure_default_plans(db)

    result = await db.execute(
        select(Plan).where(Plan.is_active == True).order_by(Plan.sort_order.asc())
    )
    plans = result.scalars().all()

    return [_plan_to_out(p) for p in plans]


@router.get("/current", response_model=CurrentSubscriptionOut, summary="获取当前订阅")
async def get_current_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取用户当前有效的订阅
    - 优先返回 active 状态的
    - 其次返回 trialing 状态的
    - 都没有则返回免费版
    """
    await ensure_default_plans(db)

    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .order_by(desc(Subscription.created_at))
        .limit(10)
    )
    subs = result.scalars().all()

    active_sub = next((s for s in subs if s.status == "active"), None)
    if active_sub:
        return _sub_to_out(active_sub)

    trialing_sub = next((s for s in subs if s.status == "trialing"), None)
    if trialing_sub:
        return _sub_to_out(trialing_sub)

    cancelled_sub = next((s for s in subs if s.status in ("cancelled", "expired")), None)
    if cancelled_sub:
        return _sub_to_out(cancelled_sub)

    free_plan_result = await db.execute(select(Plan).where(Plan.code == "free"))
    free_plan = free_plan_result.scalar_one_or_none()

    return CurrentSubscriptionOut(
        plan_code="free",
        plan_name=free_plan.name if free_plan else "免费版",
        status="free",
        billing_cycle="monthly",
        amount=0.0,
        currency="CNY",
    )


@router.post("/subscribe", summary="订阅套餐 (mock 实现, 支付集成调用)")
async def subscribe(
    req: SubscribeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建订阅 (mock 实现)
    - 找到对应套餐
    - 创建订阅记录 (状态: active, 用于 mock)
    - 生成账单 (paid)
    - 注意: 真实支付流程应走 payment_router
    """
    await ensure_default_plans(db)

    plan_result = await db.execute(select(Plan).where(Plan.code == req.plan_code, Plan.is_active == True))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, f"套餐 {req.plan_code} 不存在")

    now = datetime.now(timezone.utc)
    if req.billing_cycle == "yearly":
        amount = plan.price_yearly
        period_end = now + timedelta(days=365)
    else:
        amount = plan.price_monthly
        period_end = now + timedelta(days=30)

    existing_result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id, Subscription.status.in_(["active", "trialing"]))
        .order_by(desc(Subscription.created_at))
        .limit(1)
    )
    existing_sub = existing_result.scalar_one_or_none()
    if existing_sub:
        existing_sub.status = "cancelled"
        existing_sub.canceled_at = now
        existing_sub.cancel_reason = "upgraded/downgraded"
        await db.flush()

    subscription = Subscription(
        user_id=current_user.id,
        plan_id=plan.id,
        plan_code=plan.code,
        plan_name=plan.name,
        status="active",
        billing_cycle=req.billing_cycle,
        amount=amount,
        currency=plan.currency,
        current_period_start=now,
        current_period_end=period_end,
        payment_provider="mock",
        provider_subscription_id=f"mock-sub-{uuid.uuid4().hex[:12]}",
    )
    db.add(subscription)
    await db.flush()

    invoice = Invoice(
        invoice_no=generate_invoice_no(),
        user_id=current_user.id,
        subscription_id=subscription.id,
        plan_code=plan.code,
        plan_name=plan.name,
        status="paid",
        amount=amount,
        currency=plan.currency,
        discount=0.0,
        billing_cycle=req.billing_cycle,
        period_start=now,
        period_end=period_end,
        payment_method="mock",
        payment_provider="mock",
        provider_payment_id=f"mock-pay-{uuid.uuid4().hex[:12]}",
        paid_at=now,
    )
    db.add(invoice)

    current_user.subscription_tier = plan.tier

    await db.commit()
    await db.refresh(subscription)

    logger.info(f"用户 {current_user.id} 订阅 {plan.code} ({req.billing_cycle}) 成功")

    return {
        "status": "success",
        "subscription": _sub_to_out(subscription),
        "invoice_no": invoice.invoice_no,
    }


@router.post("/cancel", summary="取消订阅")
async def cancel_subscription(
    reason: Optional[str] = Query(None, description="取消原因"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取消当前订阅
    - 标记 cancel_at_period_end = true
    - 到期前仍可使用
    """
    sub_result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id, Subscription.status == "active")
        .order_by(desc(Subscription.created_at))
        .limit(1)
    )
    subscription = sub_result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(404, "没有活跃的订阅")

    now = datetime.now(timezone.utc)
    subscription.cancel_at_period_end = True
    subscription.canceled_at = now
    subscription.cancel_reason = reason or "用户主动取消"

    await db.commit()
    await db.refresh(subscription)

    logger.info(f"用户 {current_user.id} 取消订阅 {subscription.id}")

    return {
        "status": "cancelled",
        "subscription": _sub_to_out(subscription),
        "message": "订阅已取消, 将在当前周期结束后失效",
    }


@router.get("/invoices", response_model=List[InvoiceOut], summary="账单列表")
async def list_invoices(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="筛选状态"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取用户的账单列表
    - 按创建时间倒序
    - 支持状态筛选
    """
    stmt = select(Invoice).where(Invoice.user_id == current_user.id)
    if status:
        stmt = stmt.where(Invoice.status == status)
    stmt = stmt.order_by(desc(Invoice.created_at)).limit(page_size).offset((page - 1) * page_size)

    result = await db.execute(stmt)
    invoices = result.scalars().all()

    return [_invoice_to_out(inv) for inv in invoices]
