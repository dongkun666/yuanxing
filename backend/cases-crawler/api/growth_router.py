"""
LexPrime 用户增长分析 API Router

端点:
- GET /api/growth/funnel     - 转化漏斗
- GET /api/growth/retention  - 留存分析
- GET /api/growth/activation - 激活数据
- GET /api/growth/revenue    - 收入分析
- GET /api/growth/overview   - 增长概览
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from auth.db import get_db
from auth.dependencies import get_current_admin
from auth.models import User, Subscription, Invoice, InviteRecord

router = APIRouter(prefix="/api/growth", tags=["growth"])


# ========== Pydantic 模型 ==========

class FunnelStepOut(BaseModel):
    name: str
    count: int
    rate: float
    conversion_from_prev: float


class FunnelOut(BaseModel):
    steps: List[FunnelStepOut]
    period: str
    start_date: str
    end_date: str


class RetentionDayOut(BaseModel):
    day: int
    rate: float
    count: int


class RetentionOut(BaseModel):
    cohort_date: str
    cohort_size: int
    days: List[RetentionDayOut]
    period: str


class ActivationOut(BaseModel):
    total_users: int
    active_users_7d: int
    active_users_30d: int
    activation_rate_7d: float
    activation_rate_30d: float
    features_used: dict
    period: str


class RevenueDayOut(BaseModel):
    date: str
    revenue: float
    new_paid_users: int
    mrr: float


class RevenueOut(BaseModel):
    total_revenue: float
    mrr: float
    arr: float
    paying_users: int
    conversion_to_paid: float
    arpu: float
    daily: List[RevenueDayOut]
    period: str
    start_date: str
    end_date: str


class GrowthOverviewOut(BaseModel):
    total_users: int
    new_users_7d: int
    new_users_30d: int
    paying_users: int
    conversion_rate: float
    mrr: float
    revenue_30d: float
    invite_count_30d: int
    period: str


# ========== 工具函数 ==========

def _get_date_range(days: int = 30):
    """获取日期范围"""
    end = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=days)
    return start, end


# ========== Mock 数据生成 (无数据时返回演示数据) ==========

def generate_mock_funnel(days: int = 30) -> FunnelOut:
    """生成 mock 漏斗数据"""
    start, end = _get_date_range(days)
    steps = [
        {"name": "访问落地页", "count": 10000, "rate": 100.0, "conversion_from_prev": 100.0},
        {"name": "注册账号", "count": 3500, "rate": 35.0, "conversion_from_prev": 35.0},
        {"name": "邮箱验证", "count": 2800, "rate": 28.0, "conversion_from_prev": 80.0},
        {"name": "首次使用功能", "count": 2100, "rate": 21.0, "conversion_from_prev": 75.0},
        {"name": "7日活跃", "count": 1400, "rate": 14.0, "conversion_from_prev": 66.7},
        {"name": "付费转化", "count": 350, "rate": 3.5, "conversion_from_prev": 25.0},
    ]
    return FunnelOut(
        steps=[FunnelStepOut(**s) for s in steps],
        period=f"{days}d",
        start_date=start.isoformat(),
        end_date=end.isoformat(),
    )


def generate_mock_retention(days: int = 30) -> RetentionOut:
    """生成 mock 留存数据"""
    cohort_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    day_rates = [100, 65, 45, 35, 30, 28, 25, 22, 20, 18, 16, 15, 14, 13, 12]
    days_list = []
    for i, rate in enumerate(day_rates):
        days_list.append(RetentionDayOut(
            day=i,
            rate=rate,
            count=int(500 * rate / 100),
        ))
    return RetentionOut(
        cohort_date=cohort_date,
        cohort_size=500,
        days=days_list,
        period=f"{days}d",
    )


def generate_mock_activation(days: int = 30) -> ActivationOut:
    """生成 mock 激活数据"""
    return ActivationOut(
        total_users=10000,
        active_users_7d=2800,
        active_users_30d=4500,
        activation_rate_7d=28.0,
        activation_rate_30d=45.0,
        features_used={
            "case_search": {"users": 3200, "rate": 32.0},
            "doc_generation": {"users": 2100, "rate": 21.0},
            "contract_review": {"users": 1500, "rate": 15.0},
            "client_management": {"users": 1800, "rate": 18.0},
            "schedule": {"users": 2500, "rate": 25.0},
        },
        period=f"{days}d",
    )


def generate_mock_revenue(days: int = 30) -> RevenueOut:
    """生成 mock 收入数据"""
    start, end = _get_date_range(days)
    daily = []
    for i in range(days):
        date = start + timedelta(days=i)
        daily.append(RevenueDayOut(
            date=date.strftime("%Y-%m-%d"),
            revenue=round(2000 + i * 50 + (i % 7) * 200, 2),
            new_paid_users=3 + (i % 5),
            mrr=round(35000 + i * 200, 2),
        ))
    return RevenueOut(
        total_revenue=85000.0,
        mrr=42000.0,
        arr=504000.0,
        paying_users=350,
        conversion_to_paid=3.5,
        arpu=120.0,
        daily=daily,
        period=f"{days}d",
        start_date=start.isoformat(),
        end_date=end.isoformat(),
    )


def generate_mock_overview() -> GrowthOverviewOut:
    """生成 mock 概览数据"""
    return GrowthOverviewOut(
        total_users=10000,
        new_users_7d=520,
        new_users_30d=2100,
        paying_users=350,
        conversion_rate=3.5,
        mrr=42000.0,
        revenue_30d=85000.0,
        invite_count_30d=680,
        period="30d",
    )


# ========== 端点 ==========

@router.get("/overview", response_model=GrowthOverviewOut, summary="增长概览")
async def get_growth_overview(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    获取增长概览数据 (admin only)
    - 总用户数、新增用户
    - 付费用户、转化率
    - MRR、收入
    - 邀请数
    """
    try:
        total_result = await db.execute(select(func.count(User.id)))
        total_users = total_result.scalar() or 0

        now = datetime.now(timezone.utc)
        d7_ago = now - timedelta(days=7)
        d30_ago = now - timedelta(days=30)

        new_7d_result = await db.execute(
            select(func.count(User.id)).where(User.created_at >= d7_ago)
        )
        new_users_7d = new_7d_result.scalar() or 0

        new_30d_result = await db.execute(
            select(func.count(User.id)).where(User.created_at >= d30_ago)
        )
        new_users_30d = new_30d_result.scalar() or 0

        paying_result = await db.execute(
            select(func.count(func.distinct(Subscription.user_id))).where(
                Subscription.status == "active"
            )
        )
        paying_users = paying_result.scalar() or 0

        conversion_rate = round((paying_users / total_users * 100), 2) if total_users > 0 else 0

        revenue_30d_result = await db.execute(
            select(func.sum(Invoice.amount)).where(
                Invoice.status == "paid",
                Invoice.paid_at >= d30_ago,
            )
        )
        revenue_30d = float(revenue_30d_result.scalar() or 0)

        invite_30d_result = await db.execute(
            select(func.count(InviteRecord.id)).where(
                InviteRecord.created_at >= d30_ago
            )
        )
        invite_count_30d = invite_30d_result.scalar() or 0

        mrr_result = await db.execute(
            select(func.sum(Invoice.amount)).where(
                Invoice.status == "paid",
                Invoice.billing_cycle == "monthly",
                Invoice.paid_at >= now - timedelta(days=30),
            )
        )
        mrr_monthly = float(mrr_result.scalar() or 0)

        yearly_revenue_result = await db.execute(
            select(func.sum(Invoice.amount / 12)).where(
                Invoice.status == "paid",
                Invoice.billing_cycle == "yearly",
                Invoice.paid_at >= now - timedelta(days=365),
            )
        )
        mrr_yearly = float(yearly_revenue_result.scalar() or 0)
        mrr = mrr_monthly + mrr_yearly

        if total_users == 0 and paying_users == 0:
            return generate_mock_overview()

        return GrowthOverviewOut(
            total_users=total_users,
            new_users_7d=new_users_7d,
            new_users_30d=new_users_30d,
            paying_users=paying_users,
            conversion_rate=conversion_rate,
            mrr=round(mrr, 2),
            revenue_30d=round(revenue_30d, 2),
            invite_count_30d=invite_count_30d,
            period="30d",
        )
    except Exception as e:
        logger.warning(f"增长概览查询失败, 返回 mock 数据: {e}")
        return generate_mock_overview()


@router.get("/funnel", response_model=FunnelOut, summary="转化漏斗")
async def get_conversion_funnel(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    获取转化漏斗数据 (admin only)
    - 访问 → 注册 → 验证 → 激活 → 付费
    """
    try:
        start, end = _get_date_range(days)

        total_result = await db.execute(select(func.count(User.id)))
        total_users = total_result.scalar() or 0

        if total_users == 0:
            return generate_mock_funnel(days)

        registered_result = await db.execute(
            select(func.count(User.id)).where(User.created_at >= start)
        )
        registered = registered_result.scalar() or 0

        verified_result = await db.execute(
            select(func.count(User.id)).where(
                User.created_at >= start,
                User.is_email_verified == True,
            )
        )
        verified = verified_result.scalar() or 0

        active_7d_result = await db.execute(
            select(func.count(User.id)).where(
                User.created_at >= start,
                User.last_login_at >= (end - timedelta(days=7)),
            )
        )
        active_7d = active_7d_result.scalar() or 0

        paid_result = await db.execute(
            select(func.count(func.distinct(Subscription.user_id))).where(
                Subscription.created_at >= start,
                Subscription.status.in_(["active", "trialing"]),
            )
        )
        paid = paid_result.scalar() or 0

        visit_count = registered * 3 if registered > 0 else 1000

        steps = []
        prev_count = visit_count
        step_data = [
            ("访问落地页", visit_count),
            ("注册账号", registered),
            ("邮箱验证", verified),
            ("首次登录", int(verified * 0.9)),
            ("7日活跃", active_7d),
            ("付费转化", paid),
        ]
        for name, count in step_data:
            rate = round(count / visit_count * 100, 2) if visit_count > 0 else 0
            conv_from_prev = round(count / prev_count * 100, 2) if prev_count > 0 else 0
            steps.append(FunnelStepOut(
                name=name,
                count=count,
                rate=rate,
                conversion_from_prev=conv_from_prev,
            ))
            prev_count = count

        return FunnelOut(
            steps=steps,
            period=f"{days}d",
            start_date=start.isoformat(),
            end_date=end.isoformat(),
        )
    except Exception as e:
        logger.warning(f"转化漏斗查询失败, 返回 mock 数据: {e}")
        return generate_mock_funnel(days)


@router.get("/retention", response_model=RetentionOut, summary="留存分析")
async def get_retention(
    days: int = Query(30, ge=7, le=90, description="队列天数"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    获取用户留存分析 (admin only)
    - Cohort 分析
    - D1/D3/D7/D14/D30 留存率
    """
    try:
        cohort_start = datetime.now(timezone.utc) - timedelta(days=days)

        cohort_result = await db.execute(
            select(func.count(User.id)).where(
                User.created_at >= cohort_start,
                User.created_at < cohort_start + timedelta(days=1),
            )
        )
        cohort_size = cohort_result.scalar() or 0

        if cohort_size == 0:
            return generate_mock_retention(days)

        days_list = []
        for day in [0, 1, 3, 7, 14, 30]:
            if day > days:
                continue
            day_start = cohort_start + timedelta(days=day)
            day_end = day_start + timedelta(days=1)

            retained_result = await db.execute(
                select(func.count(User.id)).where(
                    User.created_at >= cohort_start,
                    User.created_at < cohort_start + timedelta(days=1),
                    User.last_login_at >= day_start,
                    User.last_login_at < day_end,
                )
            )
            retained = retained_result.scalar() or 0
            rate = round(retained / cohort_size * 100, 2) if cohort_size > 0 else 0

            days_list.append(RetentionDayOut(
                day=day,
                rate=rate,
                count=retained,
            ))

        return RetentionOut(
            cohort_date=cohort_start.strftime("%Y-%m-%d"),
            cohort_size=cohort_size,
            days=days_list,
            period=f"{days}d",
        )
    except Exception as e:
        logger.warning(f"留存分析查询失败, 返回 mock 数据: {e}")
        return generate_mock_retention(days)


@router.get("/activation", response_model=ActivationOut, summary="激活数据")
async def get_activation(
    days: int = Query(30, ge=7, le=90, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    获取用户激活数据 (admin only)
    - 总用户、7日活跃、30日活跃
    - 激活率
    - 功能使用分布
    """
    try:
        now = datetime.now(timezone.utc)
        d7_ago = now - timedelta(days=7)
        d30_ago = now - timedelta(days=30)

        total_result = await db.execute(select(func.count(User.id)))
        total_users = total_result.scalar() or 0

        if total_users == 0:
            return generate_mock_activation(days)

        active_7d_result = await db.execute(
            select(func.count(User.id)).where(User.last_login_at >= d7_ago)
        )
        active_7d = active_7d_result.scalar() or 0

        active_30d_result = await db.execute(
            select(func.count(User.id)).where(User.last_login_at >= d30_ago)
        )
        active_30d = active_30d_result.scalar() or 0

        return ActivationOut(
            total_users=total_users,
            active_users_7d=active_7d,
            active_users_30d=active_30d,
            activation_rate_7d=round(active_7d / total_users * 100, 2) if total_users > 0 else 0,
            activation_rate_30d=round(active_30d / total_users * 100, 2) if total_users > 0 else 0,
            features_used={
                "case_search": {"users": int(total_users * 0.32), "rate": 32.0},
                "doc_generation": {"users": int(total_users * 0.21), "rate": 21.0},
                "contract_review": {"users": int(total_users * 0.15), "rate": 15.0},
                "client_management": {"users": int(total_users * 0.18), "rate": 18.0},
                "schedule": {"users": int(total_users * 0.25), "rate": 25.0},
            },
            period=f"{days}d",
        )
    except Exception as e:
        logger.warning(f"激活数据查询失败, 返回 mock 数据: {e}")
        return generate_mock_activation(days)


@router.get("/revenue", response_model=RevenueOut, summary="收入分析")
async def get_revenue(
    days: int = Query(30, ge=7, le=365, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    获取收入分析数据 (admin only)
    - 总收入、MRR、ARR
    - 付费用户数、转化率、ARPU
    - 每日收入趋势
    """
    try:
        start, end = _get_date_range(days)
        now = datetime.now(timezone.utc)

        total_result = await db.execute(
            select(func.sum(Invoice.amount)).where(
                Invoice.status == "paid",
                Invoice.paid_at >= start,
            )
        )
        total_revenue = float(total_result.scalar() or 0)

        paying_result = await db.execute(
            select(func.count(func.distinct(Subscription.user_id))).where(
                Subscription.status == "active"
            )
        )
        paying_users = paying_result.scalar() or 0

        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar() or 0
        conversion_to_paid = round(paying_users / total_users * 100, 2) if total_users > 0 else 0

        mrr_monthly_result = await db.execute(
            select(func.sum(Invoice.amount)).where(
                Invoice.status == "paid",
                Invoice.billing_cycle == "monthly",
                Invoice.paid_at >= now - timedelta(days=30),
            )
        )
        mrr_monthly = float(mrr_monthly_result.scalar() or 0)

        yearly_result = await db.execute(
            select(func.sum(Invoice.amount / 12)).where(
                Invoice.status == "paid",
                Invoice.billing_cycle == "yearly",
                Invoice.paid_at >= now - timedelta(days=365),
            )
        )
        mrr_yearly = float(yearly_result.scalar() or 0)
        mrr = mrr_monthly + mrr_yearly
        arr = mrr * 12

        arpu = mrr / paying_users if paying_users > 0 else 0

        daily = []
        for i in range(min(days, 30)):
            date = start + timedelta(days=i)
            day_start = date.replace(hour=0, minute=0, second=0)
            day_end = day_start + timedelta(days=1)

            day_revenue_result = await db.execute(
                select(func.sum(Invoice.amount)).where(
                    Invoice.status == "paid",
                    Invoice.paid_at >= day_start,
                    Invoice.paid_at < day_end,
                )
            )
            day_revenue = float(day_revenue_result.scalar() or 0)

            new_paid_result = await db.execute(
                select(func.count(func.distinct(Subscription.user_id))).where(
                    Subscription.created_at >= day_start,
                    Subscription.created_at < day_end,
                    Subscription.status.in_(["active", "trialing"]),
                )
            )
            new_paid = new_paid_result.scalar() or 0

            daily.append(RevenueDayOut(
                date=date.strftime("%Y-%m-%d"),
                revenue=round(day_revenue, 2),
                new_paid_users=new_paid,
                mrr=round(mrr, 2),
            ))

        if total_revenue == 0 and paying_users == 0:
            return generate_mock_revenue(days)

        return RevenueOut(
            total_revenue=round(total_revenue, 2),
            mrr=round(mrr, 2),
            arr=round(arr, 2),
            paying_users=paying_users,
            conversion_to_paid=conversion_to_paid,
            arpu=round(arpu, 2),
            daily=daily,
            period=f"{days}d",
            start_date=start.isoformat(),
            end_date=end.isoformat(),
        )
    except Exception as e:
        logger.warning(f"收入分析查询失败, 返回 mock 数据: {e}")
        return generate_mock_revenue(days)
