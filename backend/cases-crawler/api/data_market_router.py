"""
LexPrime 数据市场 API 路由

功能:
- GET /api/data-market/datasets - 数据集列表
- GET /api/data-market/datasets/{id} - 数据集详情
- POST /api/data-market/datasets/{id}/purchase - 购买数据集
- GET /api/data-market/my - 我的数据集
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Header, Query
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import (
    Integer, String, Text, DateTime, Float, Boolean, JSON, Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.models import Base


router = APIRouter(prefix="/api/data-market", tags=["数据市场"])


class Dataset(Base):
    """数据集表"""
    __tablename__ = "data_market_datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    category: Mapped[str] = mapped_column(String(64), index=True)
    provider_id: Mapped[str] = mapped_column(String(64))
    provider_name: Mapped[str] = mapped_column(String(128))
    price: Mapped[float] = mapped_column(Float, default=0.0)
    price_type: Mapped[str] = mapped_column(String(16), default="subscription")
    is_free: Mapped[bool] = mapped_column(Boolean, default=False)
    data_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    purchase_count: Mapped[int] = mapped_column(Integer, default=0)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    fields: Mapped[List[str]] = mapped_column(JSON, default=list)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    api_endpoint: Mapped[Optional[str]] = mapped_column(String(256), default=None)
    status: Mapped[str] = mapped_column(String(16), default="published")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class UserDataset(Base):
    """用户购买的数据集"""
    __tablename__ = "user_datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    dataset_id: Mapped[int] = mapped_column(Integer, index=True)
    dataset_title: Mapped[str] = mapped_column(String(256))
    price_type: Mapped[str] = mapped_column(String(16))
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    api_key: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=None)
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


_mock_datasets: List[Dict[str, Any]] = [
    {
        "id": 1,
        "title": "全国裁判文书库",
        "description": "涵盖全国各级法院裁判文书，支持按案由、法院、当事人、律师等多维度检索，数据每日更新。",
        "category": "cases",
        "provider_id": "p-001",
        "provider_name": "LexPrime 官方数据",
        "price": 999.0,
        "price_type": "subscription",
        "is_free": False,
        "data_count": 120000000,
        "rating": 4.9,
        "review_count": 256,
        "purchase_count": 1258,
        "view_count": 8956,
        "fields": ["案件名称", "案号", "审理法院", "案由", "当事人", "裁判日期", "法律依据", "判决结果", "全文"],
        "tags": ["裁判文书", "判例", "法院"],
        "api_endpoint": "/api/data/cases",
        "status": "published",
        "created_at": "2026-01-15T10:00:00",
    },
    {
        "id": 2,
        "title": "法律法规全集",
        "description": "收录宪法、法律、行政法规、部门规章、司法解释等各类规范性文件，实时更新。",
        "category": "laws",
        "provider_id": "p-001",
        "provider_name": "LexPrime 官方数据",
        "price": 499.0,
        "price_type": "subscription",
        "is_free": False,
        "data_count": 500000,
        "rating": 4.8,
        "review_count": 189,
        "purchase_count": 856,
        "view_count": 5678,
        "fields": ["法规名称", "发文字号", "发布机关", "效力级别", "施行日期", "效力状态", "全文"],
        "tags": ["法律法规", "法条", "规范性文件"],
        "api_endpoint": "/api/data/laws",
        "status": "published",
        "created_at": "2026-02-01T10:00:00",
    },
    {
        "id": 3,
        "title": "企业工商信息库",
        "description": "全国企业工商信息、股东结构、经营风险、知识产权、司法涉诉等全方位企业数据。",
        "category": "companies",
        "provider_id": "p-002",
        "provider_name": "企信数据",
        "price": 799.0,
        "price_type": "subscription",
        "is_free": False,
        "data_count": 80000000,
        "rating": 4.7,
        "review_count": 156,
        "purchase_count": 623,
        "view_count": 4521,
        "fields": ["企业名称", "统一社会信用代码", "法定代表人", "注册资本", "成立日期", "经营范围", "股东信息"],
        "tags": ["企业信息", "工商", "经营风险"],
        "api_endpoint": "/api/data/companies",
        "status": "published",
        "created_at": "2026-02-15T10:00:00",
    },
    {
        "id": 4,
        "title": "律师执业数据库",
        "description": "全国执业律师基本信息、执业领域、律所归属、专业认证等数据查询。",
        "category": "lawyers",
        "provider_id": "p-001",
        "provider_name": "LexPrime 官方数据",
        "price": 0.0,
        "price_type": "free",
        "is_free": True,
        "data_count": 600000,
        "rating": 4.6,
        "review_count": 98,
        "purchase_count": 3456,
        "view_count": 12345,
        "fields": ["律师姓名", "执业证号", "所属律所", "执业领域", "执业年限", "专业认证"],
        "tags": ["律师", "律所", "执业信息"],
        "api_endpoint": "/api/data/lawyers",
        "status": "published",
        "created_at": "2026-03-01T10:00:00",
    },
    {
        "id": 5,
        "title": "司法大数据分析报告",
        "description": "基于海量司法数据的行业分析报告，涵盖诉讼趋势、裁判规律、律师排行等。",
        "category": "analytics",
        "provider_id": "p-003",
        "provider_name": "法研智库",
        "price": 2999.0,
        "price_type": "one_time",
        "is_free": False,
        "data_count": 1,
        "rating": 4.9,
        "review_count": 67,
        "purchase_count": 234,
        "view_count": 1890,
        "fields": ["行业趋势", "裁判规律", "地域分布", "律师排行", "律所排行"],
        "tags": ["数据分析", "行业报告", "大数据"],
        "api_endpoint": None,
        "status": "published",
        "created_at": "2026-03-15T10:00:00",
    },
    {
        "id": 6,
        "title": "房地产纠纷数据库",
        "description": "房屋买卖、租赁、拆迁、物业等房地产领域专项裁判文书数据集。",
        "category": "cases",
        "provider_id": "p-004",
        "provider_name": "房产法律研究中心",
        "price": 599.0,
        "price_type": "subscription",
        "is_free": False,
        "data_count": 5000000,
        "rating": 4.7,
        "review_count": 45,
        "purchase_count": 189,
        "view_count": 1256,
        "fields": ["案件名称", "案号", "案由", "房产类型", "争议标的", "判决结果"],
        "tags": ["房地产", "房产纠纷", "房屋买卖"],
        "api_endpoint": "/api/data/real-estate",
        "status": "published",
        "created_at": "2026-04-01T10:00:00",
    },
]

_mock_user_datasets: Dict[str, List[Dict[str, Any]]] = {
    "u-1": [
        {
            "id": 1,
            "user_id": "u-1",
            "dataset_id": 1,
            "dataset_title": "全国裁判文书库",
            "price_type": "subscription",
            "amount": 999.0,
            "api_key": "ds_demo_abc123",
            "start_date": "2026-01-15T10:00:00",
            "end_date": "2027-01-15T10:00:00",
            "status": "active",
            "created_at": "2026-01-15T10:00:00",
        },
        {
            "id": 2,
            "user_id": "u-1",
            "dataset_id": 2,
            "dataset_title": "法律法规全集",
            "price_type": "subscription",
            "amount": 499.0,
            "api_key": "ds_demo_def456",
            "start_date": "2026-02-20T10:00:00",
            "end_date": "2026-12-20T10:00:00",
            "status": "active",
            "created_at": "2026-02-20T10:00:00",
        },
    ]
}


def _get_current_user_id(x_user_id: Optional[str]) -> str:
    return x_user_id or "u-1"


@router.get("/datasets", summary="获取数据集列表")
async def list_datasets(
    category: Optional[str] = Query(None, description="分类筛选"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    price_type: Optional[str] = Query(None, description="价格类型: free/paid/subscription"),
    sort: str = Query("default", description="排序方式"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    x_user_id: Optional[str] = Header(None),
):
    datasets = _mock_datasets

    if category and category != "all":
        datasets = [d for d in datasets if d["category"] == category]

    if keyword:
        kw = keyword.lower()
        datasets = [d for d in datasets if kw in d["title"].lower() or kw in d["description"].lower()]

    if price_type == "free":
        datasets = [d for d in datasets if d["is_free"]]
    elif price_type == "paid":
        datasets = [d for d in datasets if not d["is_free"]]
    elif price_type == "subscription":
        datasets = [d for d in datasets if d["price_type"] == "subscription"]

    if sort == "sales":
        datasets.sort(key=lambda x: x["purchase_count"], reverse=True)
    elif sort == "rating":
        datasets.sort(key=lambda x: x["rating"], reverse=True)
    elif sort == "newest":
        datasets.sort(key=lambda x: x["created_at"], reverse=True)

    total = len(datasets)
    start = (page - 1) * size
    end = start + size
    page_items = datasets[start:end]

    return {
        "items": page_items,
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/datasets/{dataset_id}", summary="获取数据集详情")
async def get_dataset_detail(
    dataset_id: int,
    x_user_id: Optional[str] = Header(None),
):
    dataset = None
    for d in _mock_datasets:
        if d["id"] == dataset_id:
            dataset = d
            break

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    dataset["view_count"] = dataset["view_count"] + 1

    return dataset


@router.post("/datasets/{dataset_id}/purchase", summary="购买数据集")
async def purchase_dataset(
    dataset_id: int,
    x_user_id: Optional[str] = Header(None),
):
    user_id = _get_current_user_id(x_user_id)

    dataset = None
    for d in _mock_datasets:
        if d["id"] == dataset_id:
            dataset = d
            break

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    if user_id not in _mock_user_datasets:
        _mock_user_datasets[user_id] = []

    existing = None
    for ud in _mock_user_datasets[user_id]:
        if ud["dataset_id"] == dataset_id and ud["status"] == "active":
            existing = ud
            break

    if existing:
        raise HTTPException(400, "您已购买该数据集")

    import secrets
    api_key = "ds_" + secrets.token_hex(12)

    end_date = None
    if dataset["price_type"] == "subscription":
        end_date = (datetime.now() + timedelta(days=365)).isoformat()

    user_dataset = {
        "id": len(_mock_user_datasets[user_id]) + 1,
        "user_id": user_id,
        "dataset_id": dataset_id,
        "dataset_title": dataset["title"],
        "price_type": dataset["price_type"],
        "amount": dataset["price"],
        "api_key": api_key,
        "start_date": datetime.now().isoformat(),
        "end_date": end_date,
        "status": "active",
        "created_at": datetime.now().isoformat(),
    }
    _mock_user_datasets[user_id].append(user_dataset)

    dataset["purchase_count"] = dataset["purchase_count"] + 1

    logger.info(f"Dataset purchased: {dataset_id} by {user_id}")

    return {
        "status": "ok",
        "user_dataset": user_dataset,
    }


@router.get("/my", summary="获取我的数据集")
async def get_my_datasets(
    status: Optional[str] = Query(None, description="状态筛选"),
    x_user_id: Optional[str] = Header(None),
):
    user_id = _get_current_user_id(x_user_id)

    datasets = _mock_user_datasets.get(user_id, [])

    if status:
        datasets = [d for d in datasets if d["status"] == status]

    return {
        "items": datasets,
        "total": len(datasets),
    }


@router.get("/categories", summary="获取数据分类")
async def get_categories():
    categories = [
        {"value": "cases", "label": "判例数据", "count": 12},
        {"value": "laws", "label": "法规数据", "count": 8},
        {"value": "companies", "label": "企业数据", "count": 5},
        {"value": "lawyers", "label": "律师数据", "count": 3},
        {"value": "analytics", "label": "分析报告", "count": 6},
    ]
    return {
        "items": categories,
        "total": len(categories),
    }
