"""
LexPrime 社区 API 路由

功能:
- GET /api/community/posts - 帖子列表
- POST /api/community/posts - 发布帖子
- GET /api/community/posts/{id} - 帖子详情
- POST /api/community/posts/{id}/comments - 发表评论
- POST /api/community/posts/{id}/like - 点赞
"""
from __future__ import annotations

from datetime import datetime
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


router = APIRouter(prefix="/api/community", tags=["社区"])


class CommunityPost(Base):
    """社区帖子表"""
    __tablename__ = "community_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    user_name: Mapped[str] = mapped_column(String(64))
    user_avatar: Mapped[Optional[str]] = mapped_column(String(256), default=None)
    user_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    category: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(256))
    content: Mapped[str] = mapped_column(Text)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    share_count: Mapped[int] = mapped_column(Integer, default=0)
    favorite_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="published")
    is_hot: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PostComment(Base):
    """帖子评论表"""
    __tablename__ = "post_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[str] = mapped_column(String(64))
    user_name: Mapped[str] = mapped_column(String(64))
    user_avatar: Mapped[Optional[str]] = mapped_column(String(256), default=None)
    user_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    reply_to_user_id: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    reply_to_user_name: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    content: Mapped[str] = mapped_column(Text)
    like_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="published")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PostLike(Base):
    """帖子点赞表"""
    __tablename__ = "post_likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_post_user_like", "post_id", "user_id", unique=True),
    )


class PostCreateIn(BaseModel):
    title: str = Field(..., min_length=2, max_length=256, description="帖子标题")
    content: str = Field(..., min_length=5, max_length=10000, description="帖子内容")
    category: str = Field(..., max_length=64, description="板块分类")
    tags: List[str] = Field(default_factory=list, description="标签列表")


class CommentCreateIn(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000, description="评论内容")
    parent_id: Optional[int] = Field(None, description="父评论ID")
    reply_to_user_id: Optional[str] = Field(None, description="回复的用户ID")
    reply_to_user_name: Optional[str] = Field(None, description="回复的用户名")


_mock_posts: List[Dict[str, Any]] = [
    {
        "id": 1,
        "user_id": "u-101",
        "user_name": "李律师",
        "user_avatar": None,
        "user_verified": True,
        "category": "contract",
        "title": "关于民间借贷利息计算的几个实务问题",
        "content": "近期处理了几个民间借贷案件，发现很多当事人对利息计算存在误解。今天整理一下常见的几个问题...",
        "tags": ["民间借贷", "利息", "实务"],
        "like_count": 128,
        "comment_count": 36,
        "view_count": 1256,
        "share_count": 23,
        "favorite_count": 56,
        "status": "published",
        "is_hot": True,
        "created_at": "2026-07-03T08:00:00",
    },
    {
        "id": 2,
        "user_id": "u-102",
        "user_name": "王律师",
        "user_avatar": None,
        "user_verified": True,
        "category": "litigation",
        "title": "开庭时如何有效质证？分享我的质证方法论",
        "content": "质证是庭审中非常重要的环节，直接影响案件结果。这些年我总结了一套质证方法...",
        "tags": ["质证", "庭审", "诉讼技巧"],
        "like_count": 256,
        "comment_count": 58,
        "view_count": 2345,
        "share_count": 45,
        "favorite_count": 128,
        "status": "published",
        "is_hot": True,
        "created_at": "2026-07-03T05:00:00",
    },
    {
        "id": 3,
        "user_id": "u-103",
        "user_name": "赵法务",
        "user_avatar": None,
        "user_verified": False,
        "category": "inhouse",
        "title": "刚入职互联网公司法务，求问日常工作重点？",
        "content": "各位前辈好，我刚入职一家互联网公司做法务，之前是做诉讼的，对非诉业务不太熟悉...",
        "tags": ["公司法务", "新人", "请教"],
        "like_count": 89,
        "comment_count": 42,
        "view_count": 890,
        "share_count": 12,
        "favorite_count": 34,
        "status": "published",
        "is_hot": False,
        "created_at": "2026-07-02T15:00:00",
    },
    {
        "id": 4,
        "user_id": "u-104",
        "user_name": "刘律师",
        "user_avatar": None,
        "user_verified": True,
        "category": "family",
        "title": "离婚案件中房产分割的常见情形总结",
        "content": "房产是离婚案件中最主要的财产争议点。我把实务中常见的房产分割情形做了一个总结...",
        "tags": ["离婚", "房产分割", "婚姻家事"],
        "like_count": 342,
        "comment_count": 76,
        "view_count": 3456,
        "share_count": 67,
        "favorite_count": 234,
        "status": "published",
        "is_hot": True,
        "created_at": "2026-07-01T10:00:00",
    },
    {
        "id": 5,
        "user_id": "u-105",
        "user_name": "陈律师",
        "user_avatar": None,
        "user_verified": True,
        "category": "career",
        "title": "授薪转独立两年，聊聊我的感受和建议",
        "content": "从授薪律师转独立律师刚好两年了，这两年经历了很多，也成长了很多...",
        "tags": ["独立律师", "职业发展", "经验分享"],
        "like_count": 521,
        "comment_count": 128,
        "view_count": 5678,
        "share_count": 123,
        "favorite_count": 456,
        "status": "published",
        "is_hot": True,
        "created_at": "2026-06-30T14:00:00",
    },
]

_mock_comments: Dict[int, List[Dict[str, Any]]] = {
    1: [
        {
            "id": 1,
            "post_id": 1,
            "user_id": "u-201",
            "user_name": "王律师",
            "user_avatar": None,
            "user_verified": True,
            "parent_id": None,
            "reply_to_user_id": None,
            "reply_to_user_name": None,
            "content": "总结得很好！补充一点：关于\"砍头息\"的问题，根据民法典规定...",
            "like_count": 45,
            "status": "published",
            "created_at": "2026-07-03T09:00:00",
        },
        {
            "id": 2,
            "post_id": 1,
            "user_id": "u-202",
            "user_name": "赵法务",
            "user_avatar": None,
            "user_verified": False,
            "parent_id": None,
            "reply_to_user_id": None,
            "reply_to_user_name": None,
            "content": "请问李律师，如果借贷双方没有约定利息，但是借款人逾期还款了...",
            "like_count": 12,
            "status": "published",
            "created_at": "2026-07-03T09:30:00",
        },
    ]
}

_post_likes: set = set()
_comment_likes: set = set()


def _get_current_user_id(x_user_id: Optional[str]) -> str:
    return x_user_id or "u-1"


def _get_current_user_name(x_user_id: Optional[str]) -> str:
    return "当前用户"


@router.get("/posts", summary="获取帖子列表")
async def list_posts(
    category: Optional[str] = Query(None, description="板块分类"),
    tab: str = Query("latest", description="排序方式: latest/hot/following"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    x_user_id: Optional[str] = Header(None),
):
    posts = _mock_posts

    if category and category != "all":
        posts = [p for p in posts if p["category"] == category]

    if keyword:
        kw = keyword.lower()
        posts = [p for p in posts if kw in p["title"].lower() or kw in p["content"].lower()]

    if tab == "hot":
        posts.sort(key=lambda x: (x["is_hot"], x["like_count"] + x["comment_count"] * 2), reverse=True)
    elif tab == "following":
        posts = [p for p in posts if p["like_count"] > 100]
    else:
        posts.sort(key=lambda x: x["created_at"], reverse=True)

    total = len(posts)
    start = (page - 1) * size
    end = start + size
    page_items = posts[start:end]

    return {
        "items": page_items,
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("/posts", summary="发布帖子")
async def create_post(
    data: PostCreateIn,
    x_user_id: Optional[str] = Header(None),
):
    user_id = _get_current_user_id(x_user_id)
    user_name = _get_current_user_name(x_user_id)

    new_post = {
        "id": len(_mock_posts) + 1,
        "user_id": user_id,
        "user_name": user_name,
        "user_avatar": None,
        "user_verified": False,
        "category": data.category,
        "title": data.title,
        "content": data.content,
        "tags": data.tags,
        "like_count": 0,
        "comment_count": 0,
        "view_count": 0,
        "share_count": 0,
        "favorite_count": 0,
        "status": "published",
        "is_hot": False,
        "created_at": datetime.now().isoformat(),
    }
    _mock_posts.insert(0, new_post)

    logger.info(f"Post created: {data.title} by {user_id}")

    return {
        "status": "ok",
        "post": new_post,
    }


@router.get("/posts/{post_id}", summary="获取帖子详情")
async def get_post_detail(
    post_id: int,
    x_user_id: Optional[str] = Header(None),
):
    post = None
    for p in _mock_posts:
        if p["id"] == post_id:
            post = p
            break

    if not post:
        raise HTTPException(404, "Post not found")

    post["view_count"] = post["view_count"] + 1

    return post


@router.get("/posts/{post_id}/comments", summary="获取帖子评论列表")
async def list_comments(
    post_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    comments = _mock_comments.get(post_id, [])
    total = len(comments)
    start = (page - 1) * size
    end = start + size

    return {
        "items": comments[start:end],
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("/posts/{post_id}/comments", summary="发表评论")
async def create_comment(
    post_id: int,
    data: CommentCreateIn,
    x_user_id: Optional[str] = Header(None),
):
    user_id = _get_current_user_id(x_user_id)
    user_name = _get_current_user_name(x_user_id)

    post = None
    for p in _mock_posts:
        if p["id"] == post_id:
            post = p
            break

    if not post:
        raise HTTPException(404, "Post not found")

    if post_id not in _mock_comments:
        _mock_comments[post_id] = []

    comment = {
        "id": len(_mock_comments[post_id]) + 1,
        "post_id": post_id,
        "user_id": user_id,
        "user_name": user_name,
        "user_avatar": None,
        "user_verified": False,
        "parent_id": data.parent_id,
        "reply_to_user_id": data.reply_to_user_id,
        "reply_to_user_name": data.reply_to_user_name,
        "content": data.content,
        "like_count": 0,
        "status": "published",
        "created_at": datetime.now().isoformat(),
    }
    _mock_comments[post_id].insert(0, comment)

    post["comment_count"] = post["comment_count"] + 1

    logger.info(f"Comment created on post {post_id} by {user_id}")

    return {
        "status": "ok",
        "comment": comment,
    }


@router.post("/posts/{post_id}/like", summary="点赞/取消点赞帖子")
async def like_post(
    post_id: int,
    x_user_id: Optional[str] = Header(None),
):
    user_id = _get_current_user_id(x_user_id)

    post = None
    for p in _mock_posts:
        if p["id"] == post_id:
            post = p
            break

    if not post:
        raise HTTPException(404, "Post not found")

    key = f"{user_id}:{post_id}"
    if key in _post_likes:
        _post_likes.remove(key)
        post["like_count"] = max(0, post["like_count"] - 1)
        liked = False
    else:
        _post_likes.add(key)
        post["like_count"] = post["like_count"] + 1
        liked = True

    return {
        "status": "ok",
        "liked": liked,
        "like_count": post["like_count"],
    }


@router.get("/categories", summary="获取板块分类")
async def get_categories():
    categories = [
        {"value": "all", "label": "全部板块", "post_count": 12000},
        {"value": "contract", "label": "合同纠纷", "post_count": 2345},
        {"value": "family", "label": "婚姻家事", "post_count": 1892},
        {"value": "litigation", "label": "诉讼技巧", "post_count": 1567},
        {"value": "inhouse", "label": "公司法务", "post_count": 1234},
        {"value": "ip", "label": "知识产权", "post_count": 987},
        {"value": "career", "label": "职业发展", "post_count": 876},
    ]
    return {
        "items": categories,
        "total": len(categories),
    }


@router.get("/hot-topics", summary="获取热门话题")
async def get_hot_topics():
    topics = [
        {"id": 1, "tag": "#民法典司法解释新变化", "discussion_count": 23000, "trending": "up"},
        {"id": 2, "tag": "#青年律师成长", "discussion_count": 18000, "trending": "up"},
        {"id": 3, "tag": "#AI 与法律实务", "discussion_count": 15000, "trending": "up"},
        {"id": 4, "tag": "#公司法修改解读", "discussion_count": 8000, "trending": "stable"},
        {"id": 5, "tag": "#执行实务经验", "discussion_count": 6000, "trending": "down"},
    ]
    return {
        "items": topics,
        "total": len(topics),
    }
