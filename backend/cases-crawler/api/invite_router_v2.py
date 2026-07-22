"""
LexPrime 邀请裂变 API Router

端点:
- GET  /api/invite/code     - 获取我的邀请码
- POST /api/invite/redeem   - 兑换邀请码
- GET  /api/invite/records  - 邀请记录
- GET  /api/invite/rewards  - 奖励列表
- GET  /api/invite/stats    - 邀请统计
"""
from __future__ import annotations

import secrets
import string
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from auth.db import get_db
from auth.dependencies import get_current_user
from auth.models import User, InviteCode, InviteRecord, Reward, Subscription

router = APIRouter(prefix="/api/invite", tags=["marketing:invite-v2"])


# ========== Pydantic 模型 ==========

class InviteCodeOut(BaseModel):
    code: str
    channel: str
    used_count: int
    max_uses: int
    reward_days: int
    reward_type: Optional[str] = None
    share_link: str
    qr_code_url: Optional[str] = None
    created_at: str


class RedeemRequest(BaseModel):
    code: str = Field(..., description="邀请码")
    email: Optional[EmailStr] = Field(None, description="邮箱 (未登录时)")
    source: Optional[str] = Field("share", description="来源: share/wechat/link")


class RedeemResponse(BaseModel):
    success: bool
    code: str
    reward_days: int
    reward_type: str
    message: str


class InviteRecordOut(BaseModel):
    id: int
    invite_code: str
    invitee_email: Optional[str] = None
    status: str
    reward_status: str
    reward_days: int
    source: Optional[str] = None
    created_at: str


class RewardOut(BaseModel):
    id: int
    reward_type: str
    reward_source: str
    amount_days: int
    amount_money: float
    status: str
    description: Optional[str] = None
    granted_at: str
    expires_at: Optional[str] = None


class InviteStatsOut(BaseModel):
    total_invited: int
    total_rewards_days: int
    valid_invited: int
    pending_rewards: int


# ========== 配置 ==========

DEFAULT_REWARD_DAYS = 30
REFERRAL_REWARD_DAYS = 30
INVITED_USER_REWARD_DAYS = 15


# ========== 工具函数 ==========

def generate_invite_code(user_id: int) -> str:
    """生成邀请码"""
    prefix = "LP"
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(8))
    return f"{prefix}{random_part}"


def generate_share_link(code: str) -> str:
    """生成分享链接"""
    return f"/register?invite_code={code}"


# ========== 端点 ==========

@router.get("/code", response_model=InviteCodeOut, summary="获取我的邀请码")
async def get_my_invite_code(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户的邀请码
    - 如果没有则自动生成
    - 返回分享链接
    """
    result = await db.execute(
        select(InviteCode).where(
            InviteCode.user_id == current_user.id,
            InviteCode.is_active == True,
        ).limit(1)
    )
    invite_code = result.scalar_one_or_none()

    if not invite_code:
        code_str = generate_invite_code(current_user.id)
        for attempt in range(5):
            check_result = await db.execute(select(InviteCode).where(InviteCode.code == code_str))
            exists = check_result.scalar_one_or_none()
            if not exists:
                break
            code_str = generate_invite_code(current_user.id)
        else:
            raise HTTPException(500, "生成邀请码失败，请稍后重试")

        invite_code = InviteCode(
            code=code_str,
            user_id=current_user.id,
            channel="referral",
            max_uses=0,
            used_count=0,
            reward_type="subscription_days",
            reward_days=REFERRAL_REWARD_DAYS,
            is_active=True,
        )
        db.add(invite_code)
        await db.commit()
        await db.refresh(invite_code)
        logger.info(f"为用户 {current_user.id} 生成邀请码: {code_str}")

    return InviteCodeOut(
        code=invite_code.code,
        channel=invite_code.channel,
        used_count=invite_code.used_count,
        max_uses=invite_code.max_uses,
        reward_days=invite_code.reward_days,
        reward_type=invite_code.reward_type,
        share_link=generate_share_link(invite_code.code),
        qr_code_url=None,
        created_at=invite_code.created_at.isoformat(),
    )


@router.post("/redeem", response_model=RedeemResponse, summary="兑换邀请码")
async def redeem_invite_code(
    req: RedeemRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(lambda: None),
):
    """
    兑换邀请码
    - 未登录: 记录邮箱，注册后发放奖励
    - 已登录: 直接发放奖励到当前用户
    - 同时给邀请人发放奖励
    """
    code = req.code.strip().upper()

    code_result = await db.execute(
        select(InviteCode).where(
            InviteCode.code == code,
            InviteCode.is_active == True,
        )
    )
    invite_code = code_result.scalar_one_or_none()
    if not invite_code:
        raise HTTPException(404, "邀请码无效或已过期")

    if invite_code.max_uses > 0 and invite_code.used_count >= invite_code.max_uses:
        raise HTTPException(400, "邀请码已达使用上限")

    now = datetime.now(timezone.utc)

    if current_user:
        existing_result = await db.execute(
            select(InviteRecord).where(
                InviteRecord.invite_code_id == invite_code.id,
                InviteRecord.invitee_user_id == current_user.id,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            return RedeemResponse(
                success=True,
                code=code,
                reward_days=invite_code.reward_days,
                reward_type=invite_code.reward_type or "subscription_days",
                message="您已使用过此邀请码",
            )

        record = InviteRecord(
            invite_code_id=invite_code.id,
            inviter_user_id=invite_code.user_id,
            invitee_user_id=current_user.id,
            invite_code=code,
            invitee_email=current_user.email,
            status="registered",
            reward_status="granted",
            reward_type=invite_code.reward_type or "subscription_days",
            reward_days=INVITED_USER_REWARD_DAYS,
            reward_granted_at=now,
            source=req.source,
        )
        db.add(record)

        invite_code.used_count += 1

        reward = Reward(
            user_id=current_user.id,
            reward_type="subscription_days",
            reward_source="invited",
            amount_days=INVITED_USER_REWARD_DAYS,
            amount_money=0.0,
            related_invite_id=None,
            status="granted",
            granted_at=now,
            description=f"使用邀请码 {code} 获得奖励",
        )
        db.add(reward)

        if invite_code.user_id and invite_code.user_id != current_user.id:
            inviter_reward = Reward(
                user_id=invite_code.user_id,
                reward_type="subscription_days",
                reward_source="referral",
                amount_days=invite_code.reward_days,
                amount_money=0.0,
                related_invite_id=None,
                status="granted",
                granted_at=now,
                description=f"邀请好友 {current_user.email} 注册获得奖励",
            )
            db.add(inviter_reward)

            await db.flush()
            record.related_invite_id = inviter_reward.id
            reward.related_invite_id = record.id

        await db.commit()

        logger.info(f"邀请码 {code} 已被用户 {current_user.id} 兑换")

        return RedeemResponse(
            success=True,
            code=code,
            reward_days=INVITED_USER_REWARD_DAYS,
            reward_type=invite_code.reward_type or "subscription_days",
            message=f"恭喜！获得 {INVITED_USER_REWARD_DAYS} 天订阅奖励",
        )
    else:
        if not req.email:
            raise HTTPException(400, "请提供邮箱或登录后再兑换")

        existing_result = await db.execute(
            select(InviteRecord).where(
                InviteRecord.invite_code_id == invite_code.id,
                InviteRecord.invitee_email == req.email.lower(),
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            return RedeemResponse(
                success=True,
                code=code,
                reward_days=invite_code.reward_days,
                reward_type=invite_code.reward_type or "subscription_days",
                message="此邮箱已使用过该邀请码",
            )

        record = InviteRecord(
            invite_code_id=invite_code.id,
            inviter_user_id=invite_code.user_id,
            invitee_user_id=None,
            invite_code=code,
            invitee_email=req.email.lower(),
            status="pending",
            reward_status="pending",
            reward_type=invite_code.reward_type or "subscription_days",
            reward_days=INVITED_USER_REWARD_DAYS,
            source=req.source,
        )
        db.add(record)

        invite_code.used_count += 1

        await db.commit()

        logger.info(f"邀请码 {code} 已被邮箱 {req.email} 预兑换 (待注册)")

        return RedeemResponse(
            success=True,
            code=code,
            reward_days=INVITED_USER_REWARD_DAYS,
            reward_type=invite_code.reward_type or "subscription_days",
            message=f"注册后将获得 {INVITED_USER_REWARD_DAYS} 天订阅奖励",
        )


@router.get("/records", response_model=List[InviteRecordOut], summary="邀请记录")
async def get_invite_records(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户的邀请记录
    - 我邀请的人
    - 按时间倒序
    """
    result = await db.execute(
        select(InviteRecord)
        .where(InviteRecord.inviter_user_id == current_user.id)
        .order_by(desc(InviteRecord.created_at))
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    records = result.scalars().all()

    return [
        InviteRecordOut(
            id=r.id,
            invite_code=r.invite_code,
            invitee_email=r.invitee_email,
            status=r.status,
            reward_status=r.reward_status,
            reward_days=r.reward_days,
            source=r.source,
            created_at=r.created_at.isoformat(),
        )
        for r in records
    ]


@router.get("/rewards", response_model=List[RewardOut], summary="奖励列表")
async def get_rewards(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    reward_source: Optional[str] = Query(None, description="奖励来源"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户的奖励记录
    - 支持按来源筛选 (invite/referral/activity)
    """
    stmt = select(Reward).where(Reward.user_id == current_user.id)
    if reward_source:
        stmt = stmt.where(Reward.reward_source == reward_source)
    stmt = stmt.order_by(desc(Reward.granted_at)).limit(page_size).offset((page - 1) * page_size)

    result = await db.execute(stmt)
    rewards = result.scalars().all()

    return [
        RewardOut(
            id=r.id,
            reward_type=r.reward_type,
            reward_source=r.reward_source,
            amount_days=r.amount_days,
            amount_money=r.amount_money,
            status=r.status,
            description=r.description,
            granted_at=r.granted_at.isoformat(),
            expires_at=r.expires_at.isoformat() if r.expires_at else None,
        )
        for r in rewards
    ]


@router.get("/stats", response_model=InviteStatsOut, summary="邀请统计")
async def get_invite_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户的邀请统计数据
    - 总邀请人数
    - 累计奖励天数
    - 有效邀请数
    - 待发放奖励数
    """
    total_result = await db.execute(
        select(func.count(InviteRecord.id)).where(
            InviteRecord.inviter_user_id == current_user.id
        )
    )
    total_invited = total_result.scalar() or 0

    valid_result = await db.execute(
        select(func.count(InviteRecord.id)).where(
            InviteRecord.inviter_user_id == current_user.id,
            InviteRecord.status == "registered",
        )
    )
    valid_invited = valid_result.scalar() or 0

    rewards_result = await db.execute(
        select(func.sum(Reward.amount_days)).where(
            Reward.user_id == current_user.id,
            Reward.reward_source == "referral",
            Reward.status == "granted",
        )
    )
    total_rewards_days = rewards_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(InviteRecord.id)).where(
            InviteRecord.inviter_user_id == current_user.id,
            InviteRecord.reward_status == "pending",
        )
    )
    pending_rewards = pending_result.scalar() or 0

    return InviteStatsOut(
        total_invited=total_invited,
        total_rewards_days=total_rewards_days,
        valid_invited=valid_invited,
        pending_rewards=pending_rewards,
    )
