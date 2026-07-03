"""
LexPrime 开放平台 - 开发者 API 路由

功能:
- POST /api/developer/register - 开发者注册
- GET /api/developer/api-keys - API Key 列表
- POST /api/developer/api-keys - 创建 API Key
- DELETE /api/developer/api-keys/{id} - 删除 API Key
- GET /api/developer/usage - 使用统计
"""
from __future__ import annotations

import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Header, Query
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import (
    Integer, String, Text, DateTime, Boolean, JSON, Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.models import Base


router = APIRouter(prefix="/api/developer", tags=["开发者平台"])


class Developer(Base):
    """开发者表"""
    __tablename__ = "developers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(128))
    developer_type: Mapped[str] = mapped_column(String(32), default="individual")
    purpose: Mapped[Optional[str]] = mapped_column(Text, default=None)
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ApiKey(Base):
    """API Key 表"""
    __tablename__ = "developer_api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    developer_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(128))
    api_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    scopes: Mapped[List[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(16), default="active")
    call_count: Mapped[int] = mapped_column(Integer, default=0)
    rate_limit: Mapped[int] = mapped_column(Integer, default=60)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ApiUsage(Base):
    """API 使用统计表"""
    __tablename__ = "developer_api_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    api_key_id: Mapped[int] = mapped_column(Integer, index=True)
    endpoint: Mapped[str] = mapped_column(String(128))
    date: Mapped[str] = mapped_column(String(10), index=True)
    call_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_api_key_date", "api_key_id", "date"),
    )


class DeveloperRegisterIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=128, description="开发者名称")
    email: str = Field(..., min_length=5, max_length=128, description="联系邮箱")
    developer_type: str = Field("individual", description="开发者类型")
    purpose: Optional[str] = Field(None, description="使用场景")


class ApiKeyCreateIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=128, description="API Key 名称")
    scopes: List[str] = Field(default_factory=list, description="权限范围")


class ApiKeyOut(BaseModel):
    id: int
    name: str
    api_key: str
    scopes: List[str]
    status: str
    call_count: int
    rate_limit: int
    created_at: str


class UsageOut(BaseModel):
    today_calls: int
    monthly_calls: int
    total_calls: int
    daily_data: List[Dict[str, Any]]


_mock_developers: Dict[str, Dict[str, Any]] = {}
_mock_api_keys: List[Dict[str, Any]] = []
_mock_usage: List[Dict[str, Any]] = []


def _generate_api_key() -> str:
    return "lp_" + secrets.token_hex(24)


def _get_current_user_id(x_user_id: Optional[str]) -> str:
    return x_user_id or "u-1"


@router.post("/register", summary="开发者注册")
async def register_developer(
    data: DeveloperRegisterIn,
    x_user_id: Optional[str] = Header(None),
):
    user_id = _get_current_user_id(x_user_id)

    dev = {
        "id": len(_mock_developers) + 1,
        "user_id": user_id,
        "name": data.name,
        "email": data.email,
        "developer_type": data.developer_type,
        "purpose": data.purpose,
        "status": "active",
        "created_at": datetime.now().isoformat(),
    }
    _mock_developers[user_id] = dev

    logger.info(f"Developer registered: {data.name} ({user_id})")

    return {
        "status": "ok",
        "developer": dev,
    }


@router.get("/api-keys", summary="获取 API Key 列表")
async def list_api_keys(
    x_user_id: Optional[str] = Header(None),
):
    user_id = _get_current_user_id(x_user_id)

    if not _mock_api_keys:
        _mock_api_keys.append({
            "id": 1,
            "developer_id": 1,
            "name": "默认 Key",
            "api_key": _generate_api_key(),
            "scopes": ["cases", "contract", "doc_gen", "companies"],
            "status": "active",
            "call_count": 1256,
            "rate_limit": 60,
            "created_at": "2026-06-01T10:00:00",
        })

    keys = []
    for k in _mock_api_keys:
        keys.append({
            "id": k["id"],
            "name": k["name"],
            "api_key": k["api_key"],
            "scopes": k["scopes"],
            "status": k["status"],
            "call_count": k["call_count"],
            "rate_limit": k["rate_limit"],
            "created_at": k["created_at"],
        })

    return {
        "items": keys,
        "total": len(keys),
    }


@router.post("/api-keys", summary="创建 API Key")
async def create_api_key(
    data: ApiKeyCreateIn,
    x_user_id: Optional[str] = Header(None),
):
    user_id = _get_current_user_id(x_user_id)

    new_key = {
        "id": len(_mock_api_keys) + 1,
        "developer_id": 1,
        "name": data.name,
        "api_key": _generate_api_key(),
        "scopes": data.scopes or ["cases", "contract", "doc_gen", "companies"],
        "status": "active",
        "call_count": 0,
        "rate_limit": 60,
        "created_at": datetime.now().isoformat(),
    }
    _mock_api_keys.append(new_key)

    logger.info(f"API Key created: {data.name} for user {user_id}")

    return {
        "status": "ok",
        "api_key": new_key,
    }


@router.delete("/api-keys/{key_id}", summary="删除 API Key")
async def delete_api_key(
    key_id: int,
    x_user_id: Optional[str] = Header(None),
):
    global _mock_api_keys

    found = False
    new_keys = []
    for k in _mock_api_keys:
        if k["id"] == key_id:
            found = True
        else:
            new_keys.append(k)

    if not found:
        raise HTTPException(404, "API Key not found")

    _mock_api_keys = new_keys

    logger.info(f"API Key deleted: {key_id}")

    return {
        "status": "ok",
    }


@router.get("/usage", summary="获取使用统计")
async def get_usage(
    period: str = Query("30d", description="统计周期"),
    x_user_id: Optional[str] = Header(None),
):
    daily_data = []
    today = datetime.now().date()

    for i in range(29, -1, -1):
        date = today - timedelta(days=i)
        base = 50 + (i % 7) * 15
        daily_data.append({
            "date": date.isoformat(),
            "calls": base + int(time.time() * 0.001) % 30,
        })

    total = sum(d["calls"] for d in daily_data)
    today_calls = daily_data[-1]["calls"] if daily_data else 0

    return {
        "today_calls": today_calls,
        "monthly_calls": total,
        "total_calls": total + 5000,
        "daily_data": daily_data,
        "by_endpoint": {
            "cases": int(total * 0.45),
            "contract": int(total * 0.30),
            "doc_gen": int(total * 0.15),
            "companies": int(total * 0.10),
        },
    }
