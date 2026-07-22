"""
LexPrime 用户管理 API (FastAPI)
2026-07-03

端点:
- GET  /api/users                  用户列表 (支持分页、搜索、筛选)
- GET  /api/users/{id}             用户详情
- PUT  /api/users/{id}             更新用户 (角色、状态、权限)
- DELETE /api/users/{id}           删除用户
- POST /api/users/batch-status     批量启用/禁用用户
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, func

from core.db import Database
from auth.models import User
from auth.dependencies import get_current_admin

router = APIRouter(prefix="/api/users", tags=["users"])

VALID_ROLES = ["lawyer", "firm_admin", "admin"]


class UserOut(BaseModel):
    id: int
    email: str
    phone: Optional[str]
    role: str
    subscription_tier: str
    is_active: bool
    is_email_verified: bool
    is_phone_verified: bool
    is_2fa_enabled: bool
    last_login_at: Optional[str]
    created_at: str
    updated_at: str


class UserUpdateRequest(BaseModel):
    role: Optional[str] = Field(None, description="用户角色")
    is_active: Optional[bool] = Field(None, description="是否启用")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if v not in VALID_ROLES:
            raise ValueError(f"role 必须是 {VALID_ROLES} 之一")
        return v


class BatchStatusRequest(BaseModel):
    user_ids: List[int] = Field(..., description="用户 ID 列表")
    is_active: bool = Field(..., description="目标状态")


class UserListResponse(BaseModel):
    total: int
    page: int
    size: int
    users: List[UserOut]


def _user_to_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        phone=user.phone,
        role=user.role,
        subscription_tier=user.subscription_tier,
        is_active=user.is_active,
        is_email_verified=user.is_email_verified,
        is_phone_verified=user.is_phone_verified,
        is_2fa_enabled=user.is_2fa_enabled,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        created_at=user.created_at.isoformat() if user.created_at else "",
        updated_at=user.updated_at.isoformat() if user.updated_at else "",
    )


@router.get("", response_model=UserListResponse)
async def list_users(
    search: Optional[str] = Query(None, description="搜索关键词 (邮箱/手机号)"),
    role: Optional[str] = Query(None, description="按角色筛选"),
    is_active: Optional[bool] = Query(None, description="按状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """用户列表 (支持分页、搜索、筛选)"""
    async with Database.session() as session:
        stmt = select(User).order_by(User.created_at.desc())

        if search:
            search_lower = search.lower()
            stmt = stmt.where(
                (User.email.ilike(f"%{search_lower}%")) |
                (User.phone.ilike(f"%{search_lower}%"))
            )

        if role:
            if role not in VALID_ROLES:
                raise HTTPException(400, f"role 必须是 {VALID_ROLES} 之一")
            stmt = stmt.where(User.role == role)

        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)

        count_stmt = select(func.count(User.id))
        if search:
            count_stmt = count_stmt.where(
                (User.email.ilike(f"%{search_lower}%")) |
                (User.phone.ilike(f"%{search_lower}%"))
            )
        if role:
            count_stmt = count_stmt.where(User.role == role)
        if is_active is not None:
            count_stmt = count_stmt.where(User.is_active == is_active)

        total = (await session.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * size
        stmt = stmt.offset(offset).limit(size)
        result = await session.execute(stmt)
        users = result.scalars().all()

    return UserListResponse(
        total=total,
        page=page,
        size=size,
        users=[_user_to_out(u) for u in users],
    )


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int):
    """用户详情"""
    async with Database.session() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(404, "用户不存在")

    return _user_to_out(user)


@router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, req: UserUpdateRequest):
    """更新用户 (角色、状态)"""
    async with Database.session() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(404, "用户不存在")

    changed_fields = []

    if req.role is not None and req.role != user.role:
        user.role = req.role
        changed_fields.append("role")

    if req.is_active is not None and req.is_active != user.is_active:
        user.is_active = req.is_active
        changed_fields.append("is_active")

    if not changed_fields:
        raise HTTPException(400, "未指定需要更新的字段")

    user.updated_at = datetime.now(timezone.utc)

    logger.info(f"[users.update] user_id={user_id} changed={changed_fields}")

    return _user_to_out(user)


@router.delete("/{user_id}")
async def delete_user(user_id: int):
    """删除用户"""
    async with Database.session() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(404, "用户不存在")

        await session.delete(user)

    logger.info(f"[users.delete] user_id={user_id} email={user.email}")

    return {"status": "ok", "message": "用户已删除"}


@router.post("/batch-status")
async def batch_update_status(req: BatchStatusRequest):
    """批量启用/禁用用户"""
    if not req.user_ids:
        raise HTTPException(400, "用户 ID 列表不能为空")

    async with Database.session() as session:
        stmt = select(User).where(User.id.in_(req.user_ids))
        result = await session.execute(stmt)
        users = result.scalars().all()

        updated_count = 0
        for user in users:
            if user.is_active != req.is_active:
                user.is_active = req.is_active
                user.updated_at = datetime.now(timezone.utc)
                updated_count += 1

    logger.info(f"[users.batch-status] updated={updated_count} is_active={req.is_active}")

    return {
        "status": "ok",
        "message": f"成功更新 {updated_count} 个用户状态",
        "updated_count": updated_count,
    }