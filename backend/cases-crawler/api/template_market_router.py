"""
LexPrime 模板市场 API 路由

功能:
- GET /api/templates/market - 模板列表
- GET /api/templates/market/{id} - 模板详情
- POST /api/templates/market - 上传模板
- POST /api/templates/market/{id}/review - 评分评论
- GET /api/templates/market/{id}/download - 下载模板
"""
from __future__ import annotations

import time
from datetime import datetime
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


router = APIRouter(prefix="/api/templates/market", tags=["模板市场"])


class MarketTemplate(Base):
    """模板市场模板表"""
    __tablename__ = "market_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    category: Mapped[str] = mapped_column(String(64), index=True)
    author_id: Mapped[str] = mapped_column(String(64))
    author_name: Mapped[str] = mapped_column(String(64))
    price: Mapped[float] = mapped_column(Float, default=0.0)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True)
    file_url: Mapped[Optional[str]] = mapped_column(String(512), default=None)
    file_type: Mapped[str] = mapped_column(String(16), default="docx")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    favorite_count: Mapped[int] = mapped_column(Integer, default=0)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(16), default="published")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TemplateReview(Base):
    """模板评论表"""
    __tablename__ = "template_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[str] = mapped_column(String(64))
    user_name: Mapped[str] = mapped_column(String(64))
    rating: Mapped[int] = mapped_column(Integer)
    content: Mapped[Optional[str]] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TemplateListOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    category: str
    author_name: str
    price: float
    is_free: bool
    file_type: str
    rating: float
    review_count: int
    download_count: int
    tags: List[str]
    created_at: str


class TemplateDetailOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    category: str
    author_id: str
    author_name: str
    price: float
    is_free: bool
    file_url: Optional[str]
    file_type: str
    file_size: int
    rating: float
    review_count: int
    download_count: int
    view_count: int
    favorite_count: int
    tags: List[str]
    status: str
    created_at: str


class TemplateUploadIn(BaseModel):
    title: str = Field(..., min_length=2, max_length=256)
    description: Optional[str] = Field(None, max_length=2000)
    category: str = Field(..., max_length=64)
    price: float = Field(0.0, ge=0)
    file_url: Optional[str] = None
    file_type: str = "docx"
    file_size: int = 0
    tags: List[str] = Field(default_factory=list)


class ReviewCreateIn(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="评分 1-5")
    content: Optional[str] = Field(None, max_length=1000)


_mock_templates: List[Dict[str, Any]] = [
    {
        "id": 1,
        "title": "商品房买卖合同范本",
        "description": "适用于商品房预售和现售，包含房屋基本信息、价格、付款方式、交付标准等完整条款。",
        "category": "contract",
        "author_id": "u-101",
        "author_name": "张律师",
        "price": 0.0,
        "is_free": True,
        "file_url": "/templates/house-sale-contract.docx",
        "file_type": "docx",
        "file_size": 45000,
        "rating": 4.8,
        "review_count": 128,
        "download_count": 2345,
        "view_count": 5678,
        "favorite_count": 156,
        "tags": ["买卖合同", "商品房", "房产"],
        "status": "published",
        "created_at": "2026-06-01T10:00:00",
    },
    {
        "id": 2,
        "title": "民事起诉状模板（标准版）",
        "description": "包含原被告信息、诉讼请求、事实与理由等完整结构，适用于各类民事案件。",
        "category": "pleading",
        "author_id": "u-102",
        "author_name": "李律师",
        "price": 19.9,
        "is_free": False,
        "file_url": "/templates/civil-complaint.docx",
        "file_type": "docx",
        "file_size": 32000,
        "rating": 4.9,
        "review_count": 256,
        "download_count": 5623,
        "view_count": 12345,
        "favorite_count": 456,
        "tags": ["起诉状", "民事诉讼", "一审"],
        "status": "published",
        "created_at": "2026-05-15T14:30:00",
    },
    {
        "id": 3,
        "title": "劳动合同模板（全面版）",
        "description": "符合劳动合同法规定，包含试用期、工资、社保、工作内容、违约责任等条款。",
        "category": "contract",
        "author_id": "u-103",
        "author_name": "王律师",
        "price": 0.0,
        "is_free": True,
        "file_url": "/templates/labor-contract.docx",
        "file_type": "docx",
        "file_size": 52000,
        "rating": 4.7,
        "review_count": 189,
        "download_count": 8956,
        "view_count": 15678,
        "favorite_count": 789,
        "tags": ["劳动合同", "劳动法", "雇佣"],
        "status": "published",
        "created_at": "2026-04-20T09:00:00",
    },
    {
        "id": 4,
        "title": "离婚协议书（财产分割版）",
        "description": "包含子女抚养、财产分割、债务承担、探望权等完整条款，律师起草审核。",
        "category": "agreement",
        "author_id": "u-104",
        "author_name": "赵律师",
        "price": 29.9,
        "is_free": False,
        "file_url": "/templates/divorce-agreement.docx",
        "file_type": "docx",
        "file_size": 38000,
        "rating": 4.9,
        "review_count": 342,
        "download_count": 12567,
        "view_count": 23456,
        "favorite_count": 1234,
        "tags": ["离婚协议", "财产分割", "婚姻家庭"],
        "status": "published",
        "created_at": "2026-03-10T16:00:00",
    },
    {
        "id": 5,
        "title": "房屋租赁合同（标准版）",
        "description": "适用于住宅和商业租赁，包含租金、押金、租期、维修责任等完整条款。",
        "category": "contract",
        "author_id": "u-105",
        "author_name": "刘律师",
        "price": 0.0,
        "is_free": True,
        "file_url": "/templates/house-rent-contract.docx",
        "file_type": "docx",
        "file_size": 41000,
        "rating": 4.6,
        "review_count": 156,
        "download_count": 6789,
        "view_count": 11234,
        "favorite_count": 567,
        "tags": ["租赁合同", "房屋租赁", "住宅"],
        "status": "published",
        "created_at": "2026-05-01T11:00:00",
    },
    {
        "id": 6,
        "title": "民事答辩状模板",
        "description": "包含答辩意见、事实陈述、证据列举等完整结构，适用于各类民事案件答辩。",
        "category": "defense",
        "author_id": "u-106",
        "author_name": "陈律师",
        "price": 9.9,
        "is_free": False,
        "file_url": "/templates/civil-defense.docx",
        "file_type": "docx",
        "file_size": 28000,
        "rating": 4.8,
        "review_count": 98,
        "download_count": 3245,
        "view_count": 7890,
        "favorite_count": 234,
        "tags": ["答辩状", "民事诉讼", "答辩"],
        "status": "published",
        "created_at": "2026-06-10T13:00:00",
    },
]

_mock_reviews: Dict[int, List[Dict[str, Any]]] = {
    2: [
        {
            "id": 1,
            "template_id": 2,
            "user_id": "u-201",
            "user_name": "用户A",
            "rating": 5,
            "content": "模板结构完整，非常实用，节省了很多时间！",
            "created_at": "2026-06-20T10:00:00",
        },
        {
            "id": 2,
            "template_id": 2,
            "user_id": "u-202",
            "user_name": "用户B",
            "rating": 4,
            "content": "整体不错，建议增加更多案由的示例。",
            "created_at": "2026-06-18T15:00:00",
        },
    ]
}

_favorites = set()


def _get_current_user_id(x_user_id: Optional[str]) -> str:
    return x_user_id or "u-1"


@router.get("", summary="获取模板列表")
async def list_templates(
    category: Optional[str] = Query(None, description="分类筛选"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    price_type: Optional[str] = Query(None, description="价格类型: free/paid"),
    sort: str = Query("default", description="排序方式"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    x_user_id: Optional[str] = Header(None),
):
    templates = _mock_templates

    if category and category != "all":
        templates = [t for t in templates if t["category"] == category]

    if keyword:
        kw = keyword.lower()
        templates = [t for t in templates if kw in t["title"].lower() or kw in t["description"].lower()]

    if price_type == "free":
        templates = [t for t in templates if t["is_free"]]
    elif price_type == "paid":
        templates = [t for t in templates if not t["is_free"]]

    if sort == "downloads":
        templates.sort(key=lambda x: x["download_count"], reverse=True)
    elif sort == "rating":
        templates.sort(key=lambda x: x["rating"], reverse=True)
    elif sort == "newest":
        templates.sort(key=lambda x: x["created_at"], reverse=True)

    total = len(templates)
    start = (page - 1) * size
    end = start + size
    page_items = templates[start:end]

    return {
        "items": page_items,
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/{template_id}", summary="获取模板详情")
async def get_template_detail(
    template_id: int,
    x_user_id: Optional[str] = Header(None),
):
    template = None
    for t in _mock_templates:
        if t["id"] == template_id:
            template = t
            break

    if not template:
        raise HTTPException(404, "Template not found")

    template["view_count"] = template["view_count"] + 1

    return template


@router.post("", summary="上传模板")
async def upload_template(
    data: TemplateUploadIn,
    x_user_id: Optional[str] = Header(None),
):
    user_id = _get_current_user_id(x_user_id)

    new_template = {
        "id": len(_mock_templates) + 1,
        "title": data.title,
        "description": data.description,
        "category": data.category,
        "author_id": user_id,
        "author_name": "当前用户",
        "price": data.price,
        "is_free": data.price == 0,
        "file_url": data.file_url,
        "file_type": data.file_type,
        "file_size": data.file_size,
        "rating": 0.0,
        "review_count": 0,
        "download_count": 0,
        "view_count": 0,
        "favorite_count": 0,
        "tags": data.tags,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    }
    _mock_templates.insert(0, new_template)

    logger.info(f"Template uploaded: {data.title} by {user_id}")

    return {
        "status": "ok",
        "template": new_template,
    }


@router.post("/{template_id}/review", summary="提交评分评论")
async def create_review(
    template_id: int,
    data: ReviewCreateIn,
    x_user_id: Optional[str] = Header(None),
):
    user_id = _get_current_user_id(x_user_id)

    template = None
    for t in _mock_templates:
        if t["id"] == template_id:
            template = t
            break

    if not template:
        raise HTTPException(404, "Template not found")

    if template_id not in _mock_reviews:
        _mock_reviews[template_id] = []

    review = {
        "id": len(_mock_reviews[template_id]) + 1,
        "template_id": template_id,
        "user_id": user_id,
        "user_name": "当前用户",
        "rating": data.rating,
        "content": data.content,
        "created_at": datetime.now().isoformat(),
    }
    _mock_reviews[template_id].insert(0, review)

    reviews = _mock_reviews[template_id]
    if reviews:
        avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
        template["rating"] = round(avg_rating, 1)
        template["review_count"] = len(reviews)

    logger.info(f"Review submitted for template {template_id}: {data.rating} stars")

    return {
        "status": "ok",
        "review": review,
    }


@router.get("/{template_id}/reviews", summary="获取模板评论列表")
async def list_reviews(
    template_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    reviews = _mock_reviews.get(template_id, [])
    total = len(reviews)
    start = (page - 1) * size
    end = start + size

    return {
        "items": reviews[start:end],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/{template_id}/download", summary="下载模板")
async def download_template(
    template_id: int,
    x_user_id: Optional[str] = Header(None),
):
    template = None
    for t in _mock_templates:
        if t["id"] == template_id:
            template = t
            break

    if not template:
        raise HTTPException(404, "Template not found")

    template["download_count"] = template["download_count"] + 1

    logger.info(f"Template downloaded: {template_id}")

    return {
        "status": "ok",
        "download_url": template.get("file_url", ""),
        "file_name": template["title"] + "." + template["file_type"],
    }


@router.post("/{template_id}/favorite", summary="收藏/取消收藏模板")
async def toggle_favorite(
    template_id: int,
    x_user_id: Optional[str] = Header(None),
):
    user_id = _get_current_user_id(x_user_id)
    key = f"{user_id}:{template_id}"

    template = None
    for t in _mock_templates:
        if t["id"] == template_id:
            template = t
            break

    if not template:
        raise HTTPException(404, "Template not found")

    if key in _favorites:
        _favorites.remove(key)
        template["favorite_count"] = max(0, template["favorite_count"] - 1)
        favorited = False
    else:
        _favorites.add(key)
        template["favorite_count"] = template["favorite_count"] + 1
        favorited = True

    return {
        "status": "ok",
        "favorited": favorited,
    }
