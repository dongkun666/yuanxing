"""
LexPrime 判例库管理 API
========================

提供判例数据库的管理接口，包括统计、标签管理、批量导入、去重、质量报告和索引管理。

端点:
- GET  /api/cases-db/stats       - 数据库统计
- GET  /api/cases-db/tags        - 标签体系
- POST /api/cases-db/import      - 批量导入
- POST /api/cases-db/dedupe      - 去重处理
- GET  /api/cases-db/quality     - 质量报告
- POST /api/cases-db/reindex     - 重建索引
- GET  /api/cases-db/health      - 健康检查
"""
from __future__ import annotations

import time
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Body
from loguru import logger
from pydantic import BaseModel, Field

from core.case_database import get_case_database


router = APIRouter(prefix="/api/cases-db", tags=["case-database"])

case_db = get_case_database()


# ========== Request / Response Models ==========

class CaseTagOut(BaseModel):
    """标签输出模型"""
    id: str
    name: str
    type: str
    level: int = 1
    parent_id: Optional[str] = None
    color: Optional[str] = None
    case_count: int = 0


class CaseImportItem(BaseModel):
    """批量导入案件项"""
    case_name: str = Field(..., description="案件名称")
    case_id: Optional[str] = Field(None, description="案件编号")
    court: Optional[str] = Field(None, description="审理法院")
    cause: Optional[str] = Field(None, description="案由")
    cause_category: Optional[str] = Field(None, description="案由分类")
    judgment_date: Optional[str] = Field(None, description="判决日期")
    full_text: Optional[str] = Field(None, description="判决书全文")
    source: Optional[str] = Field(None, description="数据来源")


class CaseImportRequest(BaseModel):
    """批量导入请求"""
    cases: List[CaseImportItem] = Field(..., description="案件数据列表")
    dedupe: bool = Field(True, description="是否自动去重")
    parse_structured: bool = Field(True, description="是否结构化解析")


class CaseImportResponse(BaseModel):
    """批量导入响应"""
    total: int
    success: int
    failed: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    duration_ms: int = 0


class DedupeResponse(BaseModel):
    """去重响应"""
    total_checked: int
    duplicates_found: int
    duplicates_removed: int
    duplicate_groups: List[Dict[str, Any]] = Field(default_factory=list)


class QualityReportOut(BaseModel):
    """质量报告输出模型"""
    total_cases: int
    avg_quality_score: float
    quality_distribution: Dict[str, int]
    completeness_avg: float
    accuracy_avg: float
    standardization_avg: float
    top_issues: List[Dict[str, Any]] = Field(default_factory=list)
    top_suggestions: List[Dict[str, Any]] = Field(default_factory=list)
    quality_trend: List[Dict[str, Any]] = Field(default_factory=list)


class StatsOut(BaseModel):
    """统计输出模型"""
    total_cases: int
    total_tags: int
    type_counts: Dict[str, int]
    cause_distribution: Dict[str, int]
    year_distribution: Dict[str, int]
    court_level_distribution: Dict[str, int]
    procedure_distribution: Dict[str, int]
    avg_quality_score: float
    high_quality_count: int
    medium_quality_count: int
    low_quality_count: int
    sources: Dict[str, int]
    last_updated: str


class ReindexResponse(BaseModel):
    """重建索引响应"""
    status: str
    total_indexed: int
    indexes: List[Dict[str, Any]] = Field(default_factory=list)
    duration_ms: int
    started_at: str
    completed_at: str


# ========== 端点 ==========

@router.get("/health", summary="判例数据库健康检查")
async def case_db_health():
    """判例数据库服务健康检查"""
    stats = case_db.get_stats()
    return {
        "status": "ok",
        "service": "lexprime-case-database",
        "version": "1.0.0",
        "mock_mode": True,
        "features": [
            "structured_parsing",
            "tag_system",
            "enhanced_search",
            "deduplication",
            "quality_assessment",
            "batch_import"
        ],
        "stats": {
            "total_cases": stats["total_cases"],
            "total_tags": stats["total_tags"],
            "avg_quality_score": stats["avg_quality_score"]
        },
        "endpoints": [
            {"path": "/api/cases-db/stats", "method": "GET", "purpose": "数据库统计"},
            {"path": "/api/cases-db/tags", "method": "GET", "purpose": "标签体系"},
            {"path": "/api/cases-db/import", "method": "POST", "purpose": "批量导入"},
            {"path": "/api/cases-db/dedupe", "method": "POST", "purpose": "去重处理"},
            {"path": "/api/cases-db/quality", "method": "GET", "purpose": "质量报告"},
            {"path": "/api/cases-db/reindex", "method": "POST", "purpose": "重建索引"}
        ]
    }


@router.get("/stats", response_model=StatsOut, summary="获取数据库统计")
async def get_case_db_stats():
    """获取判例数据库的整体统计信息

    包括案件总数、标签数量、案由分布、年份分布、法院层级分布、程序类型分布、质量评分分布等。
    """
    t0 = time.time()
    try:
        stats = case_db.get_stats()
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"Case DB stats request processed in {latency_ms}ms")
        return StatsOut(**stats)
    except Exception as e:
        logger.exception(f"Case DB stats failed: {e}")
        raise HTTPException(500, f"获取统计信息失败: {str(e)}")


@router.get("/tags", summary="获取标签体系")
async def get_case_tags(
    tag_type: Optional[str] = Query(None, description="标签类型 (cause/procedure/document/custom)"),
    tree: bool = Query(False, description="是否返回树形结构")
):
    """获取判例数据库的标签体系

    - **tag_type**: 标签类型过滤，支持 cause(案由)、procedure(程序)、document(文书)、custom(自定义)
    - **tree**: 是否返回树形结构（适用于多级案由）
    """
    t0 = time.time()
    try:
        if tree:
            tag_tree = case_db.get_tag_tree(tag_type or "cause")
            latency_ms = int((time.time() - t0) * 1000)
            logger.info(f"Case DB tag tree request processed in {latency_ms}ms, type={tag_type}")
            return {
                "tag_type": tag_type or "cause",
                "tree": True,
                "tags": tag_tree
            }
        else:
            tags = case_db.get_tags(tag_type)
            latency_ms = int((time.time() - t0) * 1000)
            logger.info(f"Case DB tags request processed in {latency_ms}ms, type={tag_type}, count={len(tags)}")
            return {
                "tag_type": tag_type or "all",
                "tree": False,
                "total": len(tags),
                "tags": [CaseTagOut(**{
                    "id": t.id,
                    "name": t.name,
                    "type": t.type,
                    "level": t.level,
                    "parent_id": t.parent_id,
                    "color": t.color,
                    "case_count": t.case_count
                }) for t in tags]
            }
    except Exception as e:
        logger.exception(f"Case DB tags failed: {e}")
        raise HTTPException(500, f"获取标签体系失败: {str(e)}")


@router.post("/import", response_model=CaseImportResponse, summary="批量导入案件")
async def batch_import_cases(
    request: CaseImportRequest = Body(..., description="批量导入请求")
):
    """批量导入案件数据

    支持批量导入多个案件，可选择自动去重和结构化解析。

    **请求体**:
    - cases: 案件数据列表
    - dedupe: 是否自动去重（默认 True）
    - parse_structured: 是否进行结构化解析（默认 True）
    """
    t0 = time.time()
    try:
        cases_data = [c.dict() for c in request.cases]

        if request.parse_structured:
            for i, case in enumerate(cases_data):
                if case.get("full_text"):
                    parsed = case_db.parse_case_document(case["full_text"])
                    if parsed.case_number and not case.get("case_id"):
                        cases_data[i]["case_id"] = parsed.case_number
                    if parsed.court and not case.get("court"):
                        cases_data[i]["court"] = parsed.court
                    if parsed.cause and not case.get("cause"):
                        cases_data[i]["cause"] = parsed.cause

        result = case_db.batch_import(cases_data)

        if request.dedupe:
            dedupe_result = case_db.deduplicate(threshold=0.9)
            result["duplicates_found"] = dedupe_result.duplicates_found
            result["duplicates_removed"] = dedupe_result.duplicates_removed

        result["duration_ms"] = int((time.time() - t0) * 1000)

        logger.info(
            f"Case DB import request processed, "
            f"total={result['total']}, success={result['success']}, failed={result['failed']}"
        )

        return CaseImportResponse(**result)
    except Exception as e:
        logger.exception(f"Case DB import failed: {e}")
        raise HTTPException(500, f"批量导入失败: {str(e)}")


@router.post("/dedupe", response_model=DedupeResponse, summary="去重处理")
async def deduplicate_cases(
    threshold: float = Query(0.85, ge=0.5, le=1.0, description="相似度阈值"),
    auto_remove: bool = Query(False, description="是否自动删除重复项")
):
    """对案件数据库进行去重处理

    - **threshold**: 相似度阈值 (0.5-1.0)，超过该阈值认为是重复案件
    - **auto_remove**: 是否自动删除重复案件（默认 False，仅检测）
    """
    t0 = time.time()
    try:
        result = case_db.deduplicate(threshold=threshold)

        if auto_remove:
            result.duplicates_removed = result.duplicates_found
        else:
            result.duplicates_removed = 0

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Case DB dedupe request processed in {latency_ms}ms, "
            f"threshold={threshold}, found={result.duplicates_found}, removed={result.duplicates_removed}"
        )

        return DedupeResponse(
            total_checked=result.total_checked,
            duplicates_found=result.duplicates_found,
            duplicates_removed=result.duplicates_removed,
            duplicate_groups=result.duplicate_groups
        )
    except Exception as e:
        logger.exception(f"Case DB dedupe failed: {e}")
        raise HTTPException(500, f"去重处理失败: {str(e)}")


@router.get("/quality", response_model=QualityReportOut, summary="获取质量报告")
async def get_quality_report():
    """获取判例数据库的数据质量报告

    包括平均质量评分、质量分布、完整性、准确性、标准化指标，以及主要问题和改进建议。
    """
    t0 = time.time()
    try:
        report = case_db.get_quality_report()
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"Case DB quality report request processed in {latency_ms}ms")
        return QualityReportOut(**report)
    except Exception as e:
        logger.exception(f"Case DB quality report failed: {e}")
        raise HTTPException(500, f"获取质量报告失败: {str(e)}")


@router.get("/quality/{case_id}", summary="获取单个案件质量评分")
async def get_case_quality(case_id: str):
    """获取单个案件的质量评分

    - **case_id**: 案件ID
    """
    t0 = time.time()
    try:
        quality = case_db.calculate_quality(case_id)
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"Case DB case quality request processed in {latency_ms}ms, case_id={case_id}")
        return {
            "case_id": case_id,
            "overall_score": quality.overall_score,
            "completeness": quality.completeness,
            "accuracy": quality.accuracy,
            "standardization": quality.standardization,
            "issues": quality.issues,
            "suggestions": quality.suggestions
        }
    except Exception as e:
        logger.exception(f"Case DB case quality failed: {e}")
        raise HTTPException(500, f"获取案件质量评分失败: {str(e)}")


@router.post("/reindex", response_model=ReindexResponse, summary="重建索引")
async def rebuild_indexes(
    index_type: Optional[str] = Query(None, description="指定索引类型，为空则重建全部")
):
    """重建案件数据库的索引

    - **index_type**: 指定要重建的索引类型（full_text/case_id/cause/court/date/tags），为空则重建全部
    """
    t0 = time.time()
    try:
        result = case_db.reindex()

        if index_type:
            filtered_indexes = [idx for idx in result["indexes"] if idx["name"] == index_type]
            result["indexes"] = filtered_indexes

        result["duration_ms"] = int((time.time() - t0) * 1000)

        logger.info(
            f"Case DB reindex request processed in {result['duration_ms']}ms, "
            f"index_type={index_type or 'all'}, total_indexed={result['total_indexed']}"
        )

        return ReindexResponse(**result)
    except Exception as e:
        logger.exception(f"Case DB reindex failed: {e}")
        raise HTTPException(500, f"重建索引失败: {str(e)}")


@router.post("/parse", summary="结构化解析裁判文书")
async def parse_case_document(
    text: str = Body(..., embed=True, description="裁判文书全文")
):
    """对裁判文书进行结构化解析

    从原始文书文本中提取案件编号、当事人、法院、案由、法律依据等结构化信息。

    **请求体**:
    - text: 裁判文书全文
    """
    t0 = time.time()
    try:
        parsed = case_db.parse_case_document(text)
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"Case DB parse request processed in {latency_ms}ms")
        return {
            "case_id": parsed.case_id,
            "case_name": parsed.case_name,
            "case_number": parsed.case_number,
            "court": parsed.court,
            "court_level": parsed.court_level,
            "cause": parsed.cause,
            "cause_category": parsed.cause_category,
            "procedure_type": parsed.procedure_type,
            "document_type": parsed.document_type,
            "plaintiffs": parsed.plaintiffs,
            "defendants": parsed.defendants,
            "lawyers": parsed.lawyers,
            "judges": parsed.judges,
            "legal_basis": parsed.legal_basis,
            "judgment_result": parsed.judgment_result,
            "case_amount": parsed.case_amount,
            "keywords": parsed.keywords,
            "summary": parsed.summary,
        }
    except Exception as e:
        logger.exception(f"Case DB parse failed: {e}")
        raise HTTPException(500, f"文书解析失败: {str(e)}")


@router.get("/search", summary="增强检索")
async def enhanced_search(
    q: str = Query("", description="搜索关键词"),
    cause_category: Optional[str] = Query(None, description="案由分类筛选"),
    court_level: Optional[str] = Query(None, description="法院层级筛选"),
    year: Optional[int] = Query(None, description="年份筛选"),
    procedure_type: Optional[str] = Query(None, description="程序类型筛选"),
    sort_by: str = Query("relevance", description="排序方式 (relevance/date/score)"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """增强型案件检索

    支持全文检索、多维度筛选和多种排序方式。

    - **q**: 搜索关键词
    - **cause_category**: 案由分类筛选
    - **court_level**: 法院层级筛选 (supreme/high/intermediate/basic/specialized)
    - **year**: 年份筛选
    - **procedure_type**: 程序类型筛选 (civil/criminal/administrative/commercial/ip/labor)
    - **sort_by**: 排序方式 (relevance=相关度, date=日期, score=评分)
    - **page**: 页码
    - **size**: 每页数量
    """
    t0 = time.time()
    try:
        filters = {}
        if cause_category:
            filters["cause_category"] = cause_category
        if court_level:
            filters["court_level"] = court_level
        if year:
            filters["year"] = year
        if procedure_type:
            filters["procedure_type"] = procedure_type

        result = case_db.search_enhanced(
            query=q,
            filters=filters if filters else None,
            sort_by=sort_by,
            page=page,
            size=size
        )

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Case DB enhanced search request processed in {latency_ms}ms, "
            f"query='{q}', total={result['total']}, page={page}"
        )

        return result
    except Exception as e:
        logger.exception(f"Case DB enhanced search failed: {e}")
        raise HTTPException(500, f"增强检索失败: {str(e)}")
