"""
LexPrime 律师数据库管理 API
============================

律师库管理相关的API接口
- GET /stats - 数据库统计
- POST /import - 批量导入
- GET /{id}/profile - 律师画像
- GET /{id}/cases - 代理案件
- GET /{id}/reviews - 客户评价
- GET /match - 律师匹配
- POST /reindex - 重建索引
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from core.lawyer_database import get_lawyer_database


router = APIRouter(prefix="/api/lawyers-db", tags=["律师库管理"])


class LawyerImportItem(BaseModel):
    name: str
    law_firm: Optional[str] = None
    level: Optional[str] = None
    practice_years: Optional[int] = 0
    region: Optional[str] = None
    specialties: Optional[List[str]] = None
    total_cases: Optional[int] = 0
    win_rate: Optional[float] = 0.0


class LawyerImportRequest(BaseModel):
    lawyers: List[LawyerImportItem] = Field(..., description="律师列表")
    source: Optional[str] = Field("manual", description="数据来源")
    update_mode: Optional[str] = Field("skip", description="更新模式: skip/overwrite/merge")


class MatchRequest(BaseModel):
    field: Optional[str] = None
    region: Optional[str] = None
    min_practice_years: Optional[int] = 0
    max_fee: Optional[int] = None
    case_type: Optional[str] = None
    top_k: Optional[int] = 10


lawyer_db = get_lawyer_database()


@router.get("/stats", summary="获取数据库统计")
async def get_stats():
    stats = lawyer_db.get_stats()
    return stats


@router.get("/search", summary="律师搜索")
async def search_lawyers(
    q: str = Query("", description="搜索关键词"),
    field: Optional[str] = Query(None, description="专业领域"),
    region: Optional[str] = Query(None, description="地区"),
    level: Optional[str] = Query(None, description="级别"),
    min_years: Optional[int] = Query(None, description="最低执业年限"),
    fee_min: Optional[int] = Query(None, description="最低费用"),
    fee_max: Optional[int] = Query(None, description="最高费用"),
    sort_by: str = Query("relevance", description="排序方式"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    result = lawyer_db.search_lawyers(
        query=q,
        field=field,
        region=region,
        level=level,
        min_practice_years=min_years,
        fee_min=fee_min,
        fee_max=fee_max,
        sort_by=sort_by,
        page=page,
        size=size,
    )
    return result


@router.get("/{lawyer_id}", summary="获取律师详情")
async def get_lawyer_detail(lawyer_id: str):
    lawyer = lawyer_db.get_lawyer(lawyer_id)
    if not lawyer:
        raise HTTPException(404, f"律师不存在: {lawyer_id}")
    return lawyer_db._lawyer_to_dict(lawyer)


@router.get("/{lawyer_id}/profile", summary="获取律师能力画像")
async def get_lawyer_profile(lawyer_id: str):
    lawyer = lawyer_db.get_lawyer(lawyer_id)
    if not lawyer:
        raise HTTPException(404, f"律师不存在: {lawyer_id}")
    profile = lawyer_db.get_profile(lawyer_id)
    lawyer_data = lawyer_db._lawyer_to_dict(lawyer)
    return {
        "lawyer": lawyer_data,
        "profile": {
            "overall_score": profile.overall_score,
            "experience_score": profile.experience_score,
            "expertise_score": profile.expertise_score,
            "success_score": profile.success_score,
            "reputation_score": profile.reputation_score,
            "cost_score": profile.cost_score,
            "strengths": profile.strengths,
            "weaknesses": profile.weaknesses,
        },
    }


@router.get("/{lawyer_id}/cases", summary="获取律师代理案件")
async def get_lawyer_cases(
    lawyer_id: str,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    is_win: Optional[bool] = Query(None, description="是否胜诉"),
    is_representative: Optional[bool] = Query(None, description="是否典型案例"),
):
    lawyer = lawyer_db.get_lawyer(lawyer_id)
    if not lawyer:
        raise HTTPException(404, f"律师不存在: {lawyer_id}")
    result = lawyer_db.get_cases(
        lawyer_id,
        page=page,
        size=size,
        is_win=is_win,
        is_representative=is_representative,
    )
    return result


@router.get("/{lawyer_id}/reviews", summary="获取律师客户评价")
async def get_lawyer_reviews(
    lawyer_id: str,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    lawyer = lawyer_db.get_lawyer(lawyer_id)
    if not lawyer:
        raise HTTPException(404, f"律师不存在: {lawyer_id}")
    result = lawyer_db.get_reviews(lawyer_id, page=page, size=size)
    return result


@router.post("/match", summary="律师专长匹配")
async def match_lawyers(request: MatchRequest = Body(...)):
    result = lawyer_db.match_lawyers(
        requirements={
            "field": request.field,
            "region": request.region,
            "min_practice_years": request.min_practice_years,
            "max_fee": request.max_fee,
            "case_type": request.case_type,
        },
        top_k=request.top_k or 10,
    )
    return result


@router.post("/import", summary="批量导入律师")
async def batch_import_lawyers(request: LawyerImportRequest = Body(...)):
    lawyer_dicts = [item.model_dump() for item in request.lawyers]
    result = lawyer_db.batch_import(lawyer_dicts)
    return result


@router.post("/reindex", summary="重建索引")
async def rebuild_index():
    result = lawyer_db.reindex()
    return result
