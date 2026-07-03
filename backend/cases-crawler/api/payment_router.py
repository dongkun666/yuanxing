"""
LexPrime 支付集成 API Router (Mock 实现)

端点:
- POST /api/payment/create  - 创建支付订单
- POST /api/payment/notify  - 支付回调 (mock)
- GET  /api/payment/{id}    - 支付状态
- GET  /api/payment/methods - 支付方式列表
"""
from __future__ import annotations

import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from auth.db import get_db
from auth.dependencies import get_current_user
from auth.models import User, Plan, Subscription, Invoice

router = APIRouter(prefix="/api/payment", tags=["payment"])


# ========== Pydantic 模型 ==========

class CreatePaymentRequest(BaseModel):
    plan_code: str = Field(..., description="套餐代码")
    billing_cycle: str = Field("monthly", description="计费周期: monthly/yearly")
    payment_method: str = Field("alipay", description="支付方式: alipay/wechat/stripe")
    coupon_code: Optional[str] = Field(None, description="优惠码")
    return_url: Optional[str] = Field(None, description="支付后跳转地址")


class PaymentOrderOut(BaseModel):
    order_id: str
    invoice_no: str
    plan_code: str
    plan_name: str
    amount: float
    currency: str
    payment_method: str
    status: str
    qr_code_url: Optional[str] = None
    pay_url: Optional[str] = None
    expires_at: str
    created_at: str


class PaymentStatusOut(BaseModel):
    order_id: str
    invoice_no: str
    status: str
    amount: float
    currency: str
    payment_method: Optional[str] = None
    paid_at: Optional[str] = None
    created_at: str


class PaymentMethodOut(BaseModel):
    code: str
    name: str
    icon: str
    enabled: bool = True
    sort_order: int = 0


# ========== 支付方式列表 ==========

PAYMENT_METHODS = [
    {"code": "alipay", "name": "支付宝", "icon": "mdi:alipay", "enabled": True, "sort_order": 0},
    {"code": "wechat", "name": "微信支付", "icon": "mdi:wechat", "enabled": True, "sort_order": 1},
    {"code": "stripe", "name": "Stripe", "icon": "mdi:credit-card-outline", "enabled": True, "sort_order": 2},
]


# ========== Mock 支付订单存储 (内存级) ==========

_payment_orders = {}
_payment_lock = None


def _get_lock():
    global _payment_lock
    if _payment_lock is None:
        _payment_lock = asyncio.Lock()
    return _payment_lock


# ========== 工具函数 ==========

def generate_order_id() -> str:
    """生成支付订单号"""
    now = datetime.now(timezone.utc)
    random_str = uuid.uuid4().hex[:12].upper()
    return f"PAY{now.strftime('%Y%m%d%H%M%S')}{random_str}"


def generate_qr_code_url(order_id: str, payment_method: str, amount: float) -> str:
    """生成 mock 二维码 URL (真实场景应为支付链接二维码)"""
    return f"/api/payment/mock-qr/{order_id}?method={payment_method}&amount={amount}"


def generate_pay_url(order_id: str, payment_method: str) -> str:
    """生成 mock 支付链接"""
    return f"/payment/confirm?order_id={order_id}&method={payment_method}"


# ========== 端点 ==========

@router.get("/methods", response_model=list[PaymentMethodOut], summary="获取支持的支付方式")
async def get_payment_methods(
    _: User = Depends(get_current_user),
):
    """获取支持的支付方式列表"""
    return [
        PaymentMethodOut(**m)
        for m in sorted(PAYMENT_METHODS, key=lambda x: x["sort_order"])
        if m["enabled"]
    ]


@router.post("/create", response_model=PaymentOrderOut, summary="创建支付订单")
async def create_payment(
    req: CreatePaymentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建支付订单 (mock 实现)
    - 校验套餐
    - 计算金额
    - 创建/获取 unpaid 状态 invoice
    - 返回支付参数 (二维码 URL / 支付链接)
    - 真实场景: 调用支付宝/微信/Stripe API 创建预支付订单
    """
    enabled_methods = [m["code"] for m in PAYMENT_METHODS if m["enabled"]]
    if req.payment_method not in enabled_methods:
        raise HTTPException(400, f"不支持的支付方式: {req.payment_method}")

    plan_result = await db.execute(
        select(Plan).where(Plan.code == req.plan_code, Plan.is_active == True)
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, f"套餐 {req.plan_code} 不存在")

    if req.billing_cycle == "yearly":
        amount = plan.price_yearly
    else:
        amount = plan.price_monthly

    discount = 0.0
    if req.coupon_code:
        if req.coupon_code.upper() == "LEXPRIME50":
            discount = amount * 0.5
        elif req.coupon_code.upper() == "LEXPRIME20":
            discount = amount * 0.2

    final_amount = round(amount - discount, 2)
    if final_amount < 0:
        final_amount = 0

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=30)
    order_id = generate_order_id()

    invoice_no = f"INV{now.strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"

    invoice = Invoice(
        invoice_no=invoice_no,
        user_id=current_user.id,
        plan_code=plan.code,
        plan_name=plan.name,
        status="unpaid",
        amount=final_amount,
        currency="CNY",
        discount=discount,
        billing_cycle=req.billing_cycle,
        payment_method=req.payment_method,
        payment_provider="mock",
        provider_payment_id=order_id,
    )
    db.add(invoice)
    await db.flush()

    order = {
        "order_id": order_id,
        "invoice_id": invoice.id,
        "invoice_no": invoice_no,
        "user_id": current_user.id,
        "plan_code": plan.code,
        "plan_name": plan.name,
        "amount": final_amount,
        "currency": "CNY",
        "payment_method": req.payment_method,
        "status": "pending",
        "billing_cycle": req.billing_cycle,
        "qr_code_url": generate_qr_code_url(order_id, req.payment_method, final_amount),
        "pay_url": generate_pay_url(order_id, req.payment_method),
        "expires_at": expires_at.isoformat(),
        "created_at": now.isoformat(),
        "return_url": req.return_url,
    }

    lock = _get_lock()
    async with lock:
        _payment_orders[order_id] = order

    await db.commit()

    logger.info(f"创建支付订单: {order_id}, 用户: {current_user.id}, 套餐: {plan.code}, 金额: {final_amount}")

    return PaymentOrderOut(
        order_id=order_id,
        invoice_no=invoice_no,
        plan_code=plan.code,
        plan_name=plan.name,
        amount=final_amount,
        currency="CNY",
        payment_method=req.payment_method,
        status="pending",
        qr_code_url=order["qr_code_url"],
        pay_url=order["pay_url"],
        expires_at=expires_at.isoformat(),
        created_at=now.isoformat(),
    )


@router.get("/{order_id}", response_model=PaymentStatusOut, summary="获取支付状态")
async def get_payment_status(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    查询支付订单状态
    - 用于前端轮询
    """
    lock = _get_lock()
    async with lock:
        order = _payment_orders.get(order_id)

    if not order:
        inv_result = await db.execute(
            select(Invoice).where(Invoice.provider_payment_id == order_id, Invoice.user_id == current_user.id)
        )
        invoice = inv_result.scalar_one_or_none()
        if not invoice:
            raise HTTPException(404, "支付订单不存在")

        return PaymentStatusOut(
            order_id=order_id,
            invoice_no=invoice.invoice_no,
            status=invoice.status,
            amount=invoice.amount,
            currency=invoice.currency,
            payment_method=invoice.payment_method,
            paid_at=invoice.paid_at.isoformat() if invoice.paid_at else None,
            created_at=invoice.created_at.isoformat(),
        )

    if order["user_id"] != current_user.id:
        raise HTTPException(403, "无权访问此订单")

    return PaymentStatusOut(
        order_id=order["order_id"],
        invoice_no=order["invoice_no"],
        status=order["status"],
        amount=order["amount"],
        currency=order["currency"],
        payment_method=order["payment_method"],
        paid_at=None,
        created_at=order["created_at"],
    )


@router.post("/notify", summary="支付回调 (mock)")
async def payment_notify(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    支付回调接口 (mock 实现)
    - 真实场景: 支付宝/微信/Stripe 服务器回调
    - 验证签名 → 更新 invoice 状态 → 开通订阅
    """
    body = await request.json()
    order_id = body.get("order_id")
    status = body.get("status", "success")

    if not order_id:
        raise HTTPException(400, "缺少 order_id")

    lock = _get_lock()
    async with lock:
        order = _payment_orders.get(order_id)

    if not order:
        raise HTTPException(404, "订单不存在")

    if status == "success" and order["status"] == "pending":
        now = datetime.now(timezone.utc)

        inv_result = await db.execute(select(Invoice).where(Invoice.id == order["invoice_id"]))
        invoice = inv_result.scalar_one_or_none()
        if invoice:
            invoice.status = "paid"
            invoice.paid_at = now
            await db.flush()

        plan_result = await db.execute(select(Plan).where(Plan.code == order["plan_code"]))
        plan = plan_result.scalar_one_or_none()

        if order["billing_cycle"] == "yearly":
            period_end = now + timedelta(days=365)
        else:
            period_end = now + timedelta(days=30)

        existing_result = await db.execute(
            select(Subscription)
            .where(Subscription.user_id == order["user_id"], Subscription.status.in_(["active", "trialing"]))
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
            user_id=order["user_id"],
            plan_id=plan.id if plan else None,
            plan_code=order["plan_code"],
            plan_name=order["plan_name"],
            status="active",
            billing_cycle=order["billing_cycle"],
            amount=order["amount"],
            currency=order["currency"],
            current_period_start=now,
            current_period_end=period_end,
            payment_provider="mock",
            provider_subscription_id=f"mock-sub-{uuid.uuid4().hex[:12]}",
        )
        db.add(subscription)

        if invoice:
            invoice.subscription_id = subscription.id

        user_result = await db.execute(select(User).where(User.id == order["user_id"]))
        user = user_result.scalar_one_or_none()
        if user and plan:
            user.subscription_tier = plan.tier

        await db.commit()

        async with lock:
            order["status"] = "paid"
            order["paid_at"] = now.isoformat()
            _payment_orders[order_id] = order

        logger.info(f"支付成功回调: {order_id}, 用户: {order['user_id']}, 套餐: {order['plan_code']}")

    return {"status": "ok", "order_id": order_id}


@router.post("/{order_id}/mock-confirm", summary="模拟支付成功 (测试用)")
async def mock_confirm_payment(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    模拟支付成功 (测试/开发用)
    - 直接调用支付回调逻辑
    """
    lock = _get_lock()
    async with lock:
        order = _payment_orders.get(order_id)

    if not order:
        raise HTTPException(404, "订单不存在")

    if order["user_id"] != current_user.id:
        raise HTTPException(403, "无权操作此订单")

    if order["status"] == "paid":
        return {"status": "already_paid", "order_id": order_id}

    now = datetime.now(timezone.utc)

    inv_result = await db.execute(select(Invoice).where(Invoice.id == order["invoice_id"]))
    invoice = inv_result.scalar_one_or_none()
    if invoice:
        invoice.status = "paid"
        invoice.paid_at = now
        await db.flush()

    plan_result = await db.execute(select(Plan).where(Plan.code == order["plan_code"]))
    plan = plan_result.scalar_one_or_none()

    if order["billing_cycle"] == "yearly":
        period_end = now + timedelta(days=365)
    else:
        period_end = now + timedelta(days=30)

    existing_result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == order["user_id"], Subscription.status.in_(["active", "trialing"]))
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
        user_id=order["user_id"],
        plan_id=plan.id if plan else None,
        plan_code=order["plan_code"],
        plan_name=order["plan_name"],
        status="active",
        billing_cycle=order["billing_cycle"],
        amount=order["amount"],
        currency=order["currency"],
        current_period_start=now,
        current_period_end=period_end,
        payment_provider="mock",
        provider_subscription_id=f"mock-sub-{uuid.uuid4().hex[:12]}",
    )
    db.add(subscription)
    await db.flush()

    if invoice:
        invoice.subscription_id = subscription.id

    user_result = await db.execute(select(User).where(User.id == order["user_id"]))
    user = user_result.scalar_one_or_none()
    if user and plan:
        user.subscription_tier = plan.tier

    await db.commit()

    async with lock:
        order["status"] = "paid"
        order["paid_at"] = now.isoformat()
        _payment_orders[order_id] = order

    logger.info(f"模拟支付成功: {order_id}, 用户: {current_user.id}")

    return {
        "status": "success",
        "order_id": order_id,
        "message": "支付成功",
    }
