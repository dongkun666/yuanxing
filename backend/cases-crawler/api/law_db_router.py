"""
LexPrime 法规库管理 API
========================

提供法规数据库的管理接口，包括统计、分类管理、批量导入、版本历史、引用关系和索引管理。

端点:
- GET  /api/laws-db/stats          - 数据库统计
- GET  /api/laws-db/categories     - 分类体系
- POST /api/laws-db/import         - 批量导入
- GET  /api/laws-db/{id}/versions  - 版本历史
- GET  /api/laws-db/{id}/references - 引用关系
- POST /api/laws-db/reindex        - 重建索引
- GET  /api/laws-db/health         - 健康检查
"""
from __future__ import annotations

import time
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Body
from loguru import logger
from pydantic import BaseModel, Field

from core.law_database import get_law_database


router = APIRouter(prefix="/api/laws-db", tags=["law-database"])

law_db = get_law_database()


# ========== Request / Response Models ==========

class LawCategoryOut(BaseModel):
    """法规分类输出模型"""
    key: str
    name: str
    law_count: int
    color: str


class LawImportItem(BaseModel):
    """批量导入法规项"""
    title: str = Field(..., description="法规标题")
    category: Optional[str] = Field(None, description="法规分类")
    level: Optional[str] = Field(None, description="效力层级")
    issuing_authority: Optional[str] = Field(None, description="发布机关")
    issue_date: Optional[str] = Field(None, description="发布日期")
    effective_date: Optional[str] = Field(None, description="实施日期")
    full_text: Optional[str] = Field(None, description="法规全文")
    source: Optional[str] = Field(None, description="数据来源")


class LawImportRequest(BaseModel):
    """批量导入请求"""
    laws: List[LawImportItem] = Field(..., description="法规数据列表")
    parse_structure: bool = Field(True, description="是否解析层级结构")


class LawImportResponse(BaseModel):
    """批量导入响应"""
    total: int
    success: int
    failed: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    duration_ms: int = 0


class LawVersionOut(BaseModel):
    """法规版本输出模型"""
    id: str
    version_number: str
    effective_date: str
    status: str
    change_summary: str
    changed_articles: List[str] = Field(default_factory=list)


class LawReferenceOut(BaseModel):
    """法规引用关系输出模型"""
    id: str
    source_law_id: str
    source_law_title: str
    target_law_id: str
    target_law_title: str
    source_article: Optional[str] = None
    target_article: Optional[str] = None
    reference_type: str
    description: Optional[str] = None


class StatsOut(BaseModel):
    """统计输出模型"""
    total_laws: int
    total_articles: int
    total_versions: int
    total_references: int
    total_related_cases: int
    category_distribution: Dict[str, int]
    level_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
    authority_distribution: Dict[str, int]
    year_distribution: Dict[str, int]
    last_updated: str


class ReindexResponse(BaseModel):
    """重建索引响应"""
    status: str
    total_indexed: int
    indexes: List[Dict[str, Any]] = Field(default_factory=list)
    duration_ms: int
    started_at: str
    completed_at: str


class LawOut(BaseModel):
    """法规输出模型"""
    id: str
    title: str
    category: str
    category_name: str
    category_color: str
    level: str
    level_name: str
    status: str
    status_name: str
    issuing_authority: str
    issue_date: str
    effective_date: str
    document_number: Optional[str] = None
    summary: Optional[str] = None
    version_count: int = 0
    view_count: int = 0
    reference_count: int = 0
    cited_count: int = 0
    related_case_count: int = 0
    tags: List[str] = Field(default_factory=list)


# ========== 端点 ==========

@router.get("/health", summary="法规数据库健康检查")
async def law_db_health():
    """法规数据库服务健康检查"""
    stats = law_db.get_stats()
    return {
        "status": "ok",
        "service": "lexprime-law-database",
        "version": "1.0.0",
        "mock_mode": True,
        "features": [
            "hierarchical_structure",
            "version_management",
            "reference_analysis",
            "enhanced_search",
            "related_cases",
            "judicial_interpretations"
        ],
        "stats": {
            "total_laws": stats["total_laws"],
            "total_articles": stats["total_articles"],
            "total_references": stats["total_references"]
        },
        "endpoints": [
            {"path": "/api/laws-db/stats", "method": "GET", "purpose": "数据库统计"},
            {"path": "/api/laws-db/categories", "method": "GET", "purpose": "分类体系"},
            {"path": "/api/laws-db/import", "method": "POST", "purpose": "批量导入"},
            {"path": "/api/laws-db/{id}/versions", "method": "GET", "purpose": "版本历史"},
            {"path": "/api/laws-db/{id}/references", "method": "GET", "purpose": "引用关系"},
            {"path": "/api/laws-db/reindex", "method": "POST", "purpose": "重建索引"}
        ]
    }


@router.get("/stats", response_model=StatsOut, summary="获取数据库统计")
async def get_law_db_stats():
    """获取法规数据库的整体统计信息

    包括法规总数、法条总数、版本数、引用关系数、分类分布、层级分布、效力状态分布、发布机关分布等。
    """
    t0 = time.time()
    try:
        stats = law_db.get_stats()
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"Law DB stats request processed in {latency_ms}ms")
        return StatsOut(**stats)
    except Exception as e:
        logger.exception(f"Law DB stats failed: {e}")
        raise HTTPException(500, f"获取统计信息失败: {str(e)}")


@router.get("/categories", summary="获取分类体系")
async def get_law_categories():
    """获取法规数据库的分类体系

    返回十大法律部门分类及其法规数量。
    """
    t0 = time.time()
    try:
        categories = law_db.get_categories()
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"Law DB categories request processed in {latency_ms}ms, count={len(categories)}")
        return {
            "total": len(categories),
            "categories": [LawCategoryOut(**c) for c in categories]
        }
    except Exception as e:
        logger.exception(f"Law DB categories failed: {e}")
        raise HTTPException(500, f"获取分类体系失败: {str(e)}")


@router.post("/import", response_model=LawImportResponse, summary="批量导入法规")
async def batch_import_laws(
    request: LawImportRequest = Body(..., description="批量导入请求")
):
    """批量导入法规数据

    支持批量导入多个法规，可选择是否解析层级结构。

    **请求体**:
    - laws: 法规数据列表
    - parse_structure: 是否解析层级结构（默认 True）
    """
    t0 = time.time()
    try:
        laws_data = [c.dict() for c in request.laws]
        result = law_db.batch_import(laws_data)
        result["duration_ms"] = int((time.time() - t0) * 1000)

        logger.info(
            f"Law DB import request processed, "
            f"total={result['total']}, success={result['success']}, failed={result['failed']}"
        )

        return LawImportResponse(**result)
    except Exception as e:
        logger.exception(f"Law DB import failed: {e}")
        raise HTTPException(500, f"批量导入失败: {str(e)}")


@router.get("/{law_id}/versions", summary="获取版本历史")
async def get_law_versions(law_id: str):
    """获取指定法规的版本历史

    - **law_id**: 法规ID
    """
    t0 = time.time()
    try:
        law = law_db.get_law(law_id)
        if not law:
            raise HTTPException(404, f"法规不存在: {law_id}")

        versions = law_db.get_versions(law_id)
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"Law DB versions request processed in {latency_ms}ms, law_id={law_id}, count={len(versions)}")

        return {
            "law_id": law_id,
            "law_title": law.title,
            "total_versions": len(versions),
            "versions": [LawVersionOut(
                id=v.id,
                version_number=v.version_number,
                effective_date=v.effective_date,
                status=v.status,
                change_summary=v.change_summary,
                changed_articles=v.changed_articles
            ) for v in versions]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Law DB versions failed: {e}")
        raise HTTPException(500, f"获取版本历史失败: {str(e)}")


@router.get("/{law_id}/versions/compare", summary="版本对比")
async def compare_law_versions(
    law_id: str,
    version1: str = Query(..., description="版本1 ID"),
    version2: str = Query(..., description="版本2 ID")
):
    """对比法规两个版本的差异

    - **law_id**: 法规ID
    - **version1**: 版本1 ID
    - **version2**: 版本2 ID
    """
    t0 = time.time()
    try:
        law = law_db.get_law(law_id)
        if not law:
            raise HTTPException(404, f"法规不存在: {law_id}")

        result = law_db.compare_versions(law_id, version1, version2)
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"Law DB version compare request processed in {latency_ms}ms, law_id={law_id}")

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Law DB version compare failed: {e}")
        raise HTTPException(500, f"版本对比失败: {str(e)}")


@router.get("/{law_id}/references", summary="获取引用关系")
async def get_law_references(law_id: str):
    """获取指定法规的引用关系

    包括该法规引用的其他法规，以及引用该法规的其他法规。

    - **law_id**: 法规ID
    """
    t0 = time.time()
    try:
        law = law_db.get_law(law_id)
        if not law:
            raise HTTPException(404, f"法规不存在: {law_id}")

        refs = law_db.get_references(law_id)
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Law DB references request processed in {latency_ms}ms, "
            f"law_id={law_id}, outgoing={refs['outgoing_count']}, incoming={refs['incoming_count']}"
        )

        return refs
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Law DB references failed: {e}")
        raise HTTPException(500, f"获取引用关系失败: {str(e)}")


@router.get("/{law_id}/structure", summary="获取法规层级结构")
async def get_law_structure(law_id: str):
    """获取指定法规的层级结构（篇-章-节-条-款-项）

    - **law_id**: 法规ID
    """
    t0 = time.time()
    try:
        law = law_db.get_law(law_id)
        if not law:
            raise HTTPException(404, f"法规不存在: {law_id}")

        structure = law_db.get_structure(law_id)
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"Law DB structure request processed in {latency_ms}ms, law_id={law_id}")

        return {
            "law_id": law_id,
            "law_title": law.title,
            "structure": structure
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Law DB structure failed: {e}")
        raise HTTPException(500, f"获取层级结构失败: {str(e)}")


@router.get("/{law_id}/related-cases", summary="获取相关案例")
async def get_law_related_cases(
    law_id: str,
    article_id: Optional[str] = Query(None, description="法条ID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取引用该法规的相关案例

    - **law_id**: 法规ID
    - **article_id**: 可选的法条ID
    - **page**: 页码
    - **size**: 每页数量
    """
    t0 = time.time()
    try:
        law = law_db.get_law(law_id)
        if not law:
            raise HTTPException(404, f"法规不存在: {law_id}")

        result = law_db.get_related_cases(law_id, article_id=article_id, page=page, size=size)
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Law DB related cases request processed in {latency_ms}ms, "
            f"law_id={law_id}, total={result['total']}"
        )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Law DB related cases failed: {e}")
        raise HTTPException(500, f"获取相关案例失败: {str(e)}")


@router.post("/reindex", response_model=ReindexResponse, summary="重建索引")
async def rebuild_law_indexes(
    index_type: Optional[str] = Query(None, description="指定索引类型，为空则重建全部")
):
    """重建法规数据库的索引

    - **index_type**: 指定要重建的索引类型（full_text/title/article_content/category/level/tags），为空则重建全部
    """
    t0 = time.time()
    try:
        result = law_db.reindex()

        if index_type:
            filtered_indexes = [idx for idx in result["indexes"] if idx["name"] == index_type]
            result["indexes"] = filtered_indexes

        result["duration_ms"] = int((time.time() - t0) * 1000)

        logger.info(
            f"Law DB reindex request processed in {result['duration_ms']}ms, "
            f"index_type={index_type or 'all'}, total_indexed={result['total_indexed']}"
        )

        return ReindexResponse(**result)
    except Exception as e:
        logger.exception(f"Law DB reindex failed: {e}")
        raise HTTPException(500, f"重建索引失败: {str(e)}")


@router.get("/search", summary="法规检索")
async def search_laws(
    q: str = Query("", description="搜索关键词"),
    category: Optional[str] = Query(None, description="分类筛选"),
    level: Optional[str] = Query(None, description="效力层级筛选"),
    status: Optional[str] = Query(None, description="效力状态筛选"),
    issuing_authority: Optional[str] = Query(None, description="发布机关筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """增强型法规检索

    支持全文检索、多维度筛选和多种排序方式。

    - **q**: 搜索关键词
    - **category**: 分类筛选 (civil/criminal/administrative/economic/social/ip/environmental/procedural/other)
    - **level**: 效力层级筛选 (law/administrative_regulation/local_regulation/departmental_rule/judicial_interpretation)
    - **status**: 效力状态筛选 (effective/amended/repealed/draft)
    - **issuing_authority**: 发布机关筛选
    - **page**: 页码
    - **size**: 每页数量
    """
    t0 = time.time()
    try:
        result = law_db.search_laws(
            query=q,
            category=category,
            level=level,
            status=status,
            issuing_authority=issuing_authority,
            page=page,
            size=size
        )

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Law DB search request processed in {latency_ms}ms, "
            f"query='{q}', total={result['total']}, page={page}"
        )

        return result
    except Exception as e:
        logger.exception(f"Law DB search failed: {e}")
        raise HTTPException(500, f"法规检索失败: {str(e)}")


@router.get("/{law_id}", response_model=LawOut, summary="获取法规详情")
async def get_law_detail(law_id: str):
    """根据法规ID获取法规详情

    - **law_id**: 法规ID
    """
    t0 = time.time()
    try:
        law = law_db.get_law(law_id)
        if not law:
            raise HTTPException(404, f"法规不存在: {law_id}")

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"Law DB detail request processed in {latency_ms}ms, law_id={law_id}")
        return LawOut(**law_db._law_to_dict(law))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Law DB detail failed: {e}")
        raise HTTPException(500, f"获取法规详情失败: {str(e)}")
