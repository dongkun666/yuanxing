"""
LexPrime 企业库管理 API
========================

提供企业数据库的管理接口，包括统计、批量导入、股权结构、风险画像、企业关系和索引管理。

端点:
- GET  /api/companies-db/stats          - 数据库统计
- POST /api/companies-db/import         - 批量导入
- GET  /api/companies-db/{id}/equity    - 股权结构
- GET  /api/companies-db/{id}/risk      - 风险画像
- GET  /api/companies-db/{id}/relations - 企业关系
- POST /api/companies-db/reindex        - 重建索引
- GET  /api/companies-db/health         - 健康检查
"""
from __future__ import annotations

import time
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Body
from loguru import logger
from pydantic import BaseModel, Field

from core.company_database import get_company_database


router = APIRouter(prefix="/api/companies-db", tags=["company-database"])

company_db = get_company_database()


# ========== Request / Response Models ==========

class CompanyImportItem(BaseModel):
    """批量导入企业项"""
    name: str = Field(..., description="企业名称")
    unified_social_credit_code: Optional[str] = Field(None, description="统一社会信用代码")
    legal_representative: Optional[str] = Field(None, description="法定代表人")
    registered_capital: Optional[str] = Field(None, description="注册资本")
    established_date: Optional[str] = Field(None, description="成立日期")
    industry: Optional[str] = Field(None, description="所属行业")
    region: Optional[str] = Field(None, description="所在地区")
    source: Optional[str] = Field(None, description="数据来源")


class CompanyImportRequest(BaseModel):
    """批量导入请求"""
    companies: List[CompanyImportItem] = Field(..., description="企业数据列表")
    parse_equity: bool = Field(True, description="是否解析股权结构")


class CompanyImportResponse(BaseModel):
    """批量导入响应"""
    total: int
    success: int
    failed: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    duration_ms: int = 0


class StatsOut(BaseModel):
    """统计输出模型"""
    total_companies: int
    total_persons: int
    total_relations: int
    total_litigations: int
    industry_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
    risk_distribution: Dict[str, int]
    region_distribution: Dict[str, int]
    capital_distribution: Dict[str, int]
    last_updated: str


class ReindexResponse(BaseModel):
    """重建索引响应"""
    status: str
    total_indexed: int
    indexes: List[Dict[str, Any]] = Field(default_factory=list)
    duration_ms: int
    started_at: str
    completed_at: str


class CompanyOut(BaseModel):
    """企业输出模型"""
    id: str
    name: str
    unified_social_credit_code: Optional[str] = None
    legal_representative: Optional[str] = None
    registered_capital: Optional[str] = None
    established_date: Optional[str] = None
    status: str
    status_name: str
    industry: Optional[str] = None
    region: Optional[str] = None
    enterprise_type: Optional[str] = None
    business_scope: Optional[str] = None
    registered_address: Optional[str] = None
    view_count: int = 0
    shareholder_count: int = 0
    subsidiary_count: int = 0
    litigation_count: int = 0
    risk_score: float = 0.0
    risk_level: str
    risk_level_name: str
    tags: List[str] = Field(default_factory=list)


# ========== 端点 ==========

@router.get("/health", summary="企业数据库健康检查")
async def company_db_health():
    """企业数据库服务健康检查"""
    stats = company_db.get_stats()
    return {
        "status": "ok",
        "service": "lexprime-company-database",
        "version": "1.0.0",
        "mock_mode": True,
        "features": [
            "equity_penetration",
            "actual_controller_identification",
            "risk_profile",
            "company_relations",
            "affiliated_company_discovery",
            "equity_chain_analysis"
        ],
        "stats": {
            "total_companies": stats["total_companies"],
            "total_relations": stats["total_relations"],
            "total_litigations": stats["total_litigations"]
        },
        "endpoints": [
            {"path": "/api/companies-db/stats", "method": "GET", "purpose": "数据库统计"},
            {"path": "/api/companies-db/import", "method": "POST", "purpose": "批量导入"},
            {"path": "/api/companies-db/{id}/equity", "method": "GET", "purpose": "股权结构"},
            {"path": "/api/companies-db/{id}/risk", "method": "GET", "purpose": "风险画像"},
            {"path": "/api/companies-db/{id}/relations", "method": "GET", "purpose": "企业关系"},
            {"path": "/api/companies-db/reindex", "method": "POST", "purpose": "重建索引"}
        ]
    }


@router.get("/stats", response_model=StatsOut, summary="获取数据库统计")
async def get_company_db_stats():
    """获取企业数据库的整体统计信息

    包括企业总数、人员总数、关系总数、涉诉总数、行业分布、状态分布、风险分布、地区分布等。
    """
    t0 = time.time()
    try:
        stats = company_db.get_stats()
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"Company DB stats request processed in {latency_ms}ms")
        return StatsOut(**stats)
    except Exception as e:
        logger.exception(f"Company DB stats failed: {e}")
        raise HTTPException(500, f"获取统计信息失败: {str(e)}")


@router.post("/import", response_model=CompanyImportResponse, summary="批量导入企业")
async def batch_import_companies(
    request: CompanyImportRequest = Body(..., description="批量导入请求")
):
    """批量导入企业数据

    支持批量导入多个企业，可选择是否解析股权结构。

    **请求体**:
    - companies: 企业数据列表
    - parse_equity: 是否解析股权结构（默认 True）
    """
    t0 = time.time()
    try:
        companies_data = [c.dict() for c in request.companies]
        result = company_db.batch_import(companies_data)
        result["duration_ms"] = int((time.time() - t0) * 1000)

        logger.info(
            f"Company DB import request processed, "
            f"total={result['total']}, success={result['success']}, failed={result['failed']}"
        )

        return CompanyImportResponse(**result)
    except Exception as e:
        logger.exception(f"Company DB import failed: {e}")
        raise HTTPException(500, f"批量导入失败: {str(e)}")


@router.get("/{company_id}/equity", summary="获取股权结构")
async def get_equity_structure(
    company_id: str,
    max_depth: int = Query(3, ge=1, le=5, description="最大穿透深度")
):
    """获取指定企业的股权结构图谱

    支持多层股权穿透，展示股东、子公司等股权关系。

    - **company_id**: 企业ID
    - **max_depth**: 最大穿透深度 (1-5)
    """
    t0 = time.time()
    try:
        company = company_db.get_company(company_id)
        if not company:
            raise HTTPException(404, f"企业不存在: {company_id}")

        structure = company_db.get_equity_structure(company_id, max_depth=max_depth)
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Company DB equity request processed in {latency_ms}ms, "
            f"company_id={company_id}, depth={max_depth}, nodes={len(structure['nodes'])}"
        )

        return structure
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Company DB equity failed: {e}")
        raise HTTPException(500, f"获取股权结构失败: {str(e)}")


@router.get("/{company_id}/equity/controller", summary="识别实际控制人")
async def find_actual_controller(company_id: str):
    """识别企业的实际控制人

    通过股权穿透分析，识别企业的最终实际控制人。

    - **company_id**: 企业ID
    """
    t0 = time.time()
    try:
        company = company_db.get_company(company_id)
        if not company:
            raise HTTPException(404, f"企业不存在: {company_id}")

        controllers = company_db.find_actual_controller(company_id)
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Company DB controller request processed in {latency_ms}ms, "
            f"company_id={company_id}, controllers={len(controllers)}"
        )

        return {
            "company_id": company_id,
            "company_name": company.name,
            "controller_count": len(controllers),
            "controllers": controllers
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Company DB controller failed: {e}")
        raise HTTPException(500, f"实际控制人识别失败: {str(e)}")


@router.get("/{company_id}/equity/affiliated", summary="发现关联企业")
async def find_affiliated_companies(
    company_id: str,
    max_depth: int = Query(2, ge=1, le=4, description="最大关联深度")
):
    """发现与指定企业相关联的其他企业

    基于共同股东、同一控制人、投资关系等发现关联企业。

    - **company_id**: 企业ID
    - **max_depth**: 最大关联深度 (1-4)
    """
    t0 = time.time()
    try:
        company = company_db.get_company(company_id)
        if not company:
            raise HTTPException(404, f"企业不存在: {company_id}")

        affiliated = company_db.find_affiliated_companies(company_id, max_depth=max_depth)
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Company DB affiliated request processed in {latency_ms}ms, "
            f"company_id={company_id}, count={len(affiliated)}"
        )

        return {
            "company_id": company_id,
            "company_name": company.name,
            "max_depth": max_depth,
            "total": len(affiliated),
            "companies": affiliated
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Company DB affiliated failed: {e}")
        raise HTTPException(500, f"关联企业发现失败: {str(e)}")


@router.get("/{company_id}/equity/chain", summary="股权链路分析")
async def get_equity_chain(
    company_id: str,
    target_person: str = Query(..., description="目标人员名称")
):
    """分析从目标人员到企业的股权链路

    - **company_id**: 企业ID
    - **target_person**: 目标人员名称
    """
    t0 = time.time()
    try:
        company = company_db.get_company(company_id)
        if not company:
            raise HTTPException(404, f"企业不存在: {company_id}")

        chains = company_db.get_equity_chain(company_id, target_person)
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Company DB equity chain request processed in {latency_ms}ms, "
            f"company_id={company_id}, chains={len(chains)}"
        )

        return {
            "company_id": company_id,
            "company_name": company.name,
            "target_person": target_person,
            "chain_count": len(chains),
            "chains": chains
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Company DB equity chain failed: {e}")
        raise HTTPException(500, f"股权链路分析失败: {str(e)}")


@router.get("/{company_id}/risk", summary="获取风险画像")
async def get_risk_profile(company_id: str):
    """获取指定企业的风险画像

    包括整体风险评分、风险等级、各维度风险（涉诉、经营、信用、合规）和风险趋势。

    - **company_id**: 企业ID
    """
    t0 = time.time()
    try:
        company = company_db.get_company(company_id)
        if not company:
            raise HTTPException(404, f"企业不存在: {company_id}")

        risk = company_db.get_risk_profile(company_id)
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"Company DB risk request processed in {latency_ms}ms, company_id={company_id}")

        return {
            "company_id": company_id,
            "company_name": company.name,
            "overall_score": risk.overall_score,
            "overall_level": risk.overall_level,
            "litigation_risk": risk.litigation_risk,
            "operation_risk": risk.operation_risk,
            "credit_risk": risk.credit_risk,
            "compliance_risk": risk.compliance_risk,
            "risk_items": risk.risk_items,
            "risk_trend": risk.risk_trend,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Company DB risk failed: {e}")
        raise HTTPException(500, f"获取风险画像失败: {str(e)}")


@router.get("/{company_id}/relations", summary="获取企业关系")
async def get_company_relations(
    company_id: str,
    relation_type: Optional[str] = Query(None, description="关系类型过滤"),
    direction: str = Query("all", description="关系方向 (outgoing/incoming/all)")
):
    """获取指定企业的关系网络

    包括投资关系、诉讼关系、合作关系、竞争关系等。

    - **company_id**: 企业ID
    - **relation_type**: 关系类型过滤 (investment/subsidiary/shareholder/litigation_opponent/business_partner/competitor)
    - **direction**: 关系方向 (outgoing/incoming/all)
    """
    t0 = time.time()
    try:
        company = company_db.get_company(company_id)
        if not company:
            raise HTTPException(404, f"企业不存在: {company_id}")

        relations = company_db.get_company_relations(
            company_id,
            relation_type=relation_type,
            direction=direction
        )
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Company DB relations request processed in {latency_ms}ms, "
            f"company_id={company_id}, total={relations['total_count']}"
        )

        return relations
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Company DB relations failed: {e}")
        raise HTTPException(500, f"获取企业关系失败: {str(e)}")


@router.post("/reindex", response_model=ReindexResponse, summary="重建索引")
async def rebuild_company_indexes(
    index_type: Optional[str] = Query(None, description="指定索引类型，为空则重建全部")
):
    """重建企业数据库的索引

    - **index_type**: 指定要重建的索引类型（full_text/company_name/credit_code/legal_rep/industry/region/risk），为空则重建全部
    """
    t0 = time.time()
    try:
        result = company_db.reindex()

        if index_type:
            filtered_indexes = [idx for idx in result["indexes"] if idx["name"] == index_type]
            result["indexes"] = filtered_indexes

        result["duration_ms"] = int((time.time() - t0) * 1000)

        logger.info(
            f"Company DB reindex request processed in {result['duration_ms']}ms, "
            f"index_type={index_type or 'all'}, total_indexed={result['total_indexed']}"
        )

        return ReindexResponse(**result)
    except Exception as e:
        logger.exception(f"Company DB reindex failed: {e}")
        raise HTTPException(500, f"重建索引失败: {str(e)}")


@router.get("/search", summary="企业检索")
async def search_companies(
    q: str = Query("", description="搜索关键词"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    region: Optional[str] = Query(None, description="地区筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    risk_level: Optional[str] = Query(None, description="风险等级筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """增强型企业检索

    支持全文检索、多维度筛选。

    - **q**: 搜索关键词（企业名称、统一社会信用代码、法定代表人）
    - **industry**: 行业筛选
    - **region**: 地区筛选
    - **status**: 状态筛选 (active/suspended/revoked/cancelled/liquidation)
    - **risk_level**: 风险等级筛选 (low/medium/high/very_high)
    - **page**: 页码
    - **size**: 每页数量
    """
    t0 = time.time()
    try:
        result = company_db.search_companies(
            query=q,
            industry=industry,
            region=region,
            status=status,
            risk_level=risk_level,
            page=page,
            size=size
        )

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Company DB search request processed in {latency_ms}ms, "
            f"query='{q}', total={result['total']}, page={page}"
        )

        return result
    except Exception as e:
        logger.exception(f"Company DB search failed: {e}")
        raise HTTPException(500, f"企业检索失败: {str(e)}")


@router.get("/{company_id}", response_model=CompanyOut, summary="获取企业详情")
async def get_company_detail(company_id: str):
    """根据企业ID获取企业详情

    - **company_id**: 企业ID
    """
    t0 = time.time()
    try:
        company = company_db.get_company(company_id)
        if not company:
            raise HTTPException(404, f"企业不存在: {company_id}")

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"Company DB detail request processed in {latency_ms}ms, company_id={company_id}")
        return CompanyOut(**company_db._company_to_dict(company))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Company DB detail failed: {e}")
        raise HTTPException(500, f"获取企业详情失败: {str(e)}")
