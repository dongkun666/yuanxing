"""
LexPrime 简易 API (FastAPI)
2026-06-28 · 给前端 LexPrime 主系统用

端点:
- GET  /api/cases                    判例列表 (带筛选)
- GET  /api/cases/{doc_id}           判例详情
- POST /api/cases/search             全文搜索
- GET  /api/laws                     法规列表
- GET  /api/laws/{law_id}            法规详情
- GET  /api/companies                企业列表
- GET  /api/companies/{unified_id}   企业详情
- POST /api/cases/{doc_id}/favorite  收藏
- POST /api/firm/lawyers             律所律师列表
- POST /api/firm/time-entries        工时记录
- GET  /api/health                   健康检查
- POST /api/logs                     前端日志上报 (错误 + 性能)
"""
import os
import json
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List, Optional, Any
from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
from loguru import logger

from core.db import Database, ESClient, Neo4jClient
from core.config import settings
from core.models import Case, Law, Company, Lawyer, Firm, FirmTimeEntry


def _get_log_file_path() -> str:
    """获取日志文件路径"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, f"frontend_{datetime.now().strftime('%Y-%m-%d')}.log")


def _write_log_entry(entry_type: str, data: dict):
    """写入日志条目到文件"""
    try:
        log_path = _get_log_file_path()
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": entry_type,
            "data": data,
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Failed to write log entry: {e}")


# ========== Pydantic 模型 ==========
class CaseOut(BaseModel):
    id: int
    doc_id: Optional[str]
    case_id: Optional[str]
    case_name: Optional[str]
    court: Optional[str]
    cause: Optional[str]
    cause_category: Optional[str]
    cause_color: Optional[str]
    judgment_date: Optional[str]
    year: Optional[int]
    lex_score: Optional[int]
    view_count: int
    favorite_count: int


class CaseDetail(CaseOut):
    parties: Optional[str]
    legal_basis: Optional[str]
    full_text: Optional[str]
    source: str
    source_url: Optional[str]
    keywords: Optional[List[str]]


class LawOut(BaseModel):
    id: int
    law_id: str
    title: str
    law_type: str
    status: Optional[str]
    issue_date: Optional[str]
    effective_date: Optional[str]
    level: Optional[int]


class CompanyOut(BaseModel):
    id: int
    unified_id: str
    company_name: str
    legal_rep: Optional[str]
    business_status: Optional[str]
    industry: Optional[str]
    region: Optional[str]
    is_zxgk: bool


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=200)
    index: str = Field("cases", pattern="^(cases|laws|companies)$")
    page: int = 1
    size: int = 20
    filters: Optional[dict] = None


class TimeEntryIn(BaseModel):
    lawyer_id: str
    case_id: Optional[int] = None
    entry_date: str
    hours: float
    description: Optional[str] = None
    billable: bool = True
    rate: Optional[float] = None


# ========== App lifespan ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.init()
    await ESClient.init()
    await Neo4jClient.init()
    logger.info("LexPrime API started")
    yield
    await Database.close()
    await ESClient.close()
    await Neo4jClient.close()
    logger.info("LexPrime API stopped")


app = FastAPI(
    title="LexPrime API",
    description="LexPrime 自建数据基础设施 API · 律所版 0.1",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志中间件
try:
    from api.logging_middleware import logging_middleware
    app.middleware("http")(logging_middleware)
    logger.info("请求日志中间件已注册")
except Exception as e:
    logger.warning(f"请求日志中间件加载失败 (非致命): {e}")


# ========== Skill Hub 端点 (Track E) ==========
# 类案检索 Skill (W7 实现)
try:
    from api.skill_endpoints import router as skill_router
    app.include_router(skill_router)
    logger.info("Skill Hub: 类案检索 router registered")
except Exception as e:
    logger.warning(f"Skill Hub 类案检索 router 加载失败 (非致命): {e}")

# 合同风险审查 Skill (W5 实施 · lex-coder)
try:
    from api.contract_review_router import router as contract_review_router
    app.include_router(contract_review_router)
    logger.info("Skill Hub: 合同风险审查 (Skill 2) router registered")
except Exception as e:
    logger.warning(f"Skill Hub 合同审查 router 加载失败 (非致命): {e}")

# 公测邀请码 Router (W6 实施 · lex-design)
# 端点: POST /api/invite/generate (admin) / POST /api/invite/redeem (用户)
try:
    from api.invite_router import router as invite_router
    app.include_router(invite_router)
    logger.info("Marketing: 公测邀请码 router registered (W6)")
except Exception as e:
    logger.warning(f"Marketing 邀请码 router 加载失败 (非致命): {e}")

# W6 律师评审 Score App (lex-coder · 2026-06-29)
# 5 律师 × 5 测试合同 = 25 条评分
# 端点: /api/review/contracts, /api/review/submit-score, /api/review/my-scores, /api/review/summary
# W7: +3 端点 (POST /question, GET /questions, GET /board)
try:
    from api.review_router import router as review_router
    app.include_router(review_router)
    logger.info("W6 律师评审 Score App router registered (W7 扩 3 端点)")
except Exception as e:
    logger.warning(f"W6 律师评审 Score App router 加载失败 (非致命): {e}")

# W8 (lex-coder · 2026-06-29) PRD backlog ticket 系统
# A2: 把 W7 review_questions 表问题 → prd_backlog 表 ticket, 给 plan engine 自动调度
# 端点: /api/backlog/from-question, /api/backlog/list, /api/backlog/{id}/assign, /api/backlog/board
try:
    from api.backlog_router import router as backlog_router
    app.include_router(backlog_router)
    logger.info("W8 PRD backlog ticket router registered (A2)")
except Exception as e:
    logger.warning(f"W8 PRD backlog ticket router 加载失败 (非致命): {e}")

# W9 (lex-coder · 2026-06-29) Skill 3 文书生成
# C1: 评审 #1 #2 律师最常问 Top 3 = 自动生成法律文书, 4 端点 + 4 模板
# 端点: /api/doc-gen/complaint, /api/doc-gen/defense, /api/doc-gen/contract, /api/doc-gen/letter
try:
    from api.doc_gen_router import router as doc_gen_router
    app.include_router(doc_gen_router)
    logger.info("W9 Skill 3 文书生成 router registered (C1)")
except Exception as e:
    logger.warning(f"W9 Skill 3 文书生成 router 加载失败 (非致命): {e}")

# W10 A1 (lex-ai · 2026-06-29) Skill 1+2+3 一体化全流程
# W9 C1 4 端点 + W4 类案 + W3 Skill 2 合同审查, 律师一个案件跑完三步
# 端点: POST /api/case/full-workflow, GET /api/case/full-workflow/{case_id}, GET /api/case/full-workflow/health
try:
    from api.full_workflow_router import router as full_workflow_router
    app.include_router(full_workflow_router)
    logger.info("W10 Skill 1+2+3 一体化 router registered (A1)")
except Exception as e:
    logger.warning(f"W10 Skill 一体化 router 加载失败 (非致命): {e}")

# W12 A2 (lex-coder · 2026-06-30) 双审工作流 (5 状态机 + 4 文书风险标注)
# 承接 W9 C1 4 文书 + W10 A1 一体化 + W3 Skill 2 reviewer
# 端点: GET/PATCH /api/doc-gen/{doc_id}/state, POST /api/doc-gen/{doc_id}/risk-annotation,
#       GET /api/doc-gen/workflow/board, GET /api/doc-gen/workflow/health
try:
    # 显式 import core.doc_workflow 注册 ORM 模型到 Base.metadata
    from core import doc_workflow as _dw  # noqa: F401
    from api.doc_workflow_router import router as doc_workflow_router
    app.include_router(doc_workflow_router)
    logger.info("W12 A2 双审工作流状态机 router registered")
except Exception as e:
    logger.warning(f"W12 A2 双审工作流 router 加载失败 (非致命): {e}")

# W12 A2 (lex-coder · 2026-06-30) 客户签字确认 (signature_router)
# 端点: POST /api/signature/{doc_id}, GET /api/signature/{doc_id}
try:
    from api.signature_router import router as signature_router
    app.include_router(signature_router)
    logger.info("W12 A2 客户签字 router registered")
except Exception as e:
    logger.warning(f"W12 A2 客户签字 router 加载失败 (非致命): {e}")

# W29 phase6-1-backend (lex-coder · 2026-07-01) Phase 6.1 Marketplace API
# 7 端点 + 1 health + 1 disclaimer + 1 manifest = 10 endpoints
# 端点: /api/marketplace/lawyers (POST/GET), /api/marketplace/cases (POST/GET),
#       /api/marketplace/referrals (POST), /api/marketplace/cross-border (POST),
#       /api/marketplace/metrics (GET)
try:
    # 显式 import core.marketplace_engine 注册 ORM 模型到 Base.metadata
    from core import marketplace_engine as _mp_engine  # noqa: F401
    from api.marketplace_router import router as marketplace_router
    app.include_router(marketplace_router)
    logger.info("W29 phase6-1-backend Marketplace API router registered")
except Exception as e:
    logger.warning(f"W29 phase6-1-backend Marketplace API router 加载失败 (非致命): {e}")

# W30 phase6-ai-backend (lex-ai · 2026-07-03) AI 服务统一 API
# 4 核心端点 + 1 health + 1 disclaimer = 6 endpoints
# 端点: POST /api/ai/chat, POST /api/ai/case-summary,
#       POST /api/ai/polish, POST /api/ai/auto-fill
try:
    from api.ai_router import router as ai_router
    app.include_router(ai_router)
    logger.info("W30 phase6-ai-backend AI 服务统一 API router registered")
except Exception as e:
    logger.warning(f"W30 phase6-ai-backend AI 服务 API router 加载失败 (非致命): {e}")

# W31 phase6-clients-backend (lex-coder · 2026-07-02) 客户管理 API
# 7 端点 + 1 health = 8 endpoints
# 端点: GET /api/clients (列表/搜索/过滤), GET /api/clients/{client_id} (详情),
#       POST /api/clients (创建), PUT /api/clients/{client_id} (更新),
#       DELETE /api/clients/{client_id} (删除),
#       POST /api/clients/{client_id}/conflict-check (利益冲突检查),
#       GET /api/clients/stats (统计)
# W31: 客户管理 API
try:
    from api.clients_router import router as clients_router
    app.include_router(clients_router)
    logger.info("W31 phase6-clients-backend 客户管理 API router registered")
except Exception as e:
    logger.warning(f"clients_router 加载失败: {e}")

# 日程管理 (lex-coder · 2026-07-02) Phase 6
# 4 CRUD + 1 conflicts + 1 today + 1 health = 7 endpoints
# 端点: GET/POST /api/schedule, PUT/DELETE /api/schedule/{id},
#       GET /api/schedule/conflicts, GET /api/schedule/today
try:
    from api.schedule_router import router as schedule_router
    app.include_router(schedule_router)
    logger.info("日程管理 schedule_router registered")
except Exception as e:
    logger.warning(f"schedule_router 加载失败: {e}")


# ========== 端点 ==========
@app.get("/api/health")
async def health():
    """增强健康检查 - 检查数据库连接、ES、Neo4j"""
    import time
    
    db_status = {
        "connected": Database._engine is not None,
        "backend": Database._backend if hasattr(Database, "_backend") else "unknown",
    }
    
    if Database._engine is not None:
        try:
            start_time = time.time()
            async with Database.session() as session:
                await session.execute("SELECT 1")
            db_status["latency_ms"] = round((time.time() - start_time) * 1000, 2)
            db_status["query_ok"] = True
        except Exception as e:
            db_status["query_ok"] = False
            db_status["error"] = str(e)
    
    es_status = {
        "connected": ESClient._client is not None,
        "using_mock": ESClient.is_mock(),
    }
    
    if ESClient._client is not None and not ESClient.is_mock():
        try:
            start_time = time.time()
            await ESClient._client.info()
            es_status["latency_ms"] = round((time.time() - start_time) * 1000, 2)
            es_status["query_ok"] = True
        except Exception as e:
            es_status["query_ok"] = False
            es_status["error"] = str(e)
    
    neo4j_status = {
        "connected": Neo4jClient._driver is not None,
        "available": Neo4jClient.is_available(),
    }
    
    if Neo4jClient._driver is not None:
        try:
            start_time = time.time()
            async with Neo4jClient._driver.session() as session:
                await session.run("RETURN 1").single()
            neo4j_status["latency_ms"] = round((time.time() - start_time) * 1000, 2)
            neo4j_status["query_ok"] = True
        except Exception as e:
            neo4j_status["query_ok"] = False
            neo4j_status["error"] = str(e)
    
    all_ok = (
        db_status.get("connected", False) and
        es_status.get("connected", False) and
        neo4j_status.get("available", True)
    )
    
    return {
        "status": "ok" if all_ok else "degraded",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat(),
        "databases": {
            "main": db_status,
            "elasticsearch": es_status,
            "neo4j": neo4j_status,
        },
        "environment": settings.api_debug and "development" or "production",
    }


class FrontendError(BaseModel):
    timestamp: str
    user: dict = {}
    browser: dict = {}
    page: dict = {}
    error: dict = {}
    type: str = "frontend_error"


class FrontendPerformance(BaseModel):
    timestamp: str
    user: dict = {}
    browser: dict = {}
    page: dict = {}
    performance: dict = {}
    type: str = "frontend_performance"


class LogsRequest(BaseModel):
    errors: Optional[List[FrontendError]] = None
    performance: Optional[List[FrontendPerformance]] = None


@app.post("/api/logs")
async def receive_frontend_logs(req: LogsRequest, request: Request):
    """接收前端错误和性能日志"""
    client_ip = request.client.host if request.client else "unknown"
    
    if req.errors:
        for error in req.errors:
            logger.error("frontend_error", extra={
                "client_ip": client_ip,
                **error.dict(),
            })
            _write_log_entry("frontend_error", error.dict())
    
    if req.performance:
        for perf in req.performance:
            logger.info("frontend_performance", extra={
                "client_ip": client_ip,
                **perf.dict(),
            })
            _write_log_entry("frontend_performance", perf.dict())
    
    return {"status": "ok", "received_errors": len(req.errors or []), "received_performance": len(req.performance or [])}


# --- 判例 ---
@app.get("/api/cases")
async def list_cases(
    cause: Optional[str] = None,
    cause_category: Optional[str] = None,
    year: Optional[int] = None,
    court: Optional[str] = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
    full: bool = Query(False, description="包含完整字段 (full_text, legal_basis, lex_tags, source 等)"),
):
    """判例列表 (默认精简, ?full=true 返完整)"""
    async with Database.session() as session:
        from sqlalchemy import select
        stmt = select(Case).order_by(Case.lex_score.desc(), Case.judgment_date.desc())
        if cause_category:
            stmt = stmt.where(Case.cause_category == cause_category)
        if year:
            stmt = stmt.where(Case.year == year)
        if court:
            stmt = stmt.where(Case.court.contains(court))
        if cause:
            stmt = stmt.where(Case.cause.contains(cause))
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        cases = result.scalars().all()
        if full:
            # 完整数据 (给前端 view)
            return [CaseDetail(
                id=c.id, doc_id=c.doc_id, case_id=c.case_id, case_name=c.case_name,
                court=c.court, cause=c.cause, cause_category=c.cause_category,
                cause_color=c.cause_color,
                judgment_date=c.judgment_date.isoformat() if c.judgment_date else None,
                year=c.year, lex_score=c.lex_score,
                view_count=c.view_count, favorite_count=c.favorite_count,
                parties=c.parties, legal_basis=c.legal_basis,
                full_text=c.full_text_plain or c.full_text, source=c.source, source_url=c.source_url,
                keywords=c.keywords or [],
            ) for c in cases]
        else:
            return [CaseOut(
                id=c.id, doc_id=c.doc_id, case_id=c.case_id, case_name=c.case_name,
                court=c.court, cause=c.cause, cause_category=c.cause_category,
                cause_color=c.cause_color,
                judgment_date=c.judgment_date.isoformat() if c.judgment_date else None,
                year=c.year, lex_score=c.lex_score,
                view_count=c.view_count, favorite_count=c.favorite_count,
            ) for c in cases]


@app.get("/api/cases/{doc_id}", response_model=CaseDetail)
async def get_case(doc_id: str):
    """判例详情"""
    async with Database.session() as session:
        from sqlalchemy import select
        stmt = select(Case).where(Case.doc_id == doc_id)
        result = await session.execute(stmt)
        c = result.scalar_one_or_none()
        if not c:
            raise HTTPException(404, "Case not found")
        # 增加查看次数
        c.view_count += 1
        await session.commit()
        return CaseDetail(
            id=c.id, doc_id=c.doc_id, case_id=c.case_id, case_name=c.case_name,
            court=c.court, cause=c.cause, cause_category=c.cause_category,
            cause_color=c.cause_color,
            judgment_date=c.judgment_date.isoformat() if c.judgment_date else None,
            year=c.year, lex_score=c.lex_score,
            view_count=c.view_count, favorite_count=c.favorite_count,
            parties=c.parties, legal_basis=c.legal_basis,
            full_text=c.full_text, source=c.source, source_url=c.source_url,
            keywords=c.keywords,
        )


# --- 搜索 (ES 全文检索) ---
@app.post("/api/search")
async def search(req: SearchRequest):
    """全文搜索"""
    es = ESClient.get()
    index_name = {
        "cases": settings.es_index_cases,
        "laws": settings.es_index_laws,
        "companies": settings.es_index_companies,
    }[req.index]

    from_ = (req.page - 1) * req.size
    query = {
        "multi_match": {
            "query": req.query,
            "fields": ["*"],
            "type": "best_fields",
        }
    }
    if req.filters:
        # 简单 filter 应用
        filter_clauses = []
        for k, v in req.filters.items():
            filter_clauses.append({"term": {k: v}})
        body = {
            "query": {"bool": {"must": [query], "filter": filter_clauses}},
            "from": from_,
            "size": req.size,
        }
    else:
        body = {"query": query, "from": from_, "size": req.size}

    try:
        resp = await es.search(index=index_name, body=body)
        hits = resp["hits"]["hits"]
        total = resp["hits"]["total"]["value"]
        return {
            "total": total,
            "page": req.page,
            "size": req.size,
            "items": [h["_source"] for h in hits],
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(500, f"Search failed: {e}")


# --- 法规 ---
@app.get("/api/laws", response_model=List[LawOut])
async def list_laws(
    law_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
):
    async with Database.session() as session:
        from sqlalchemy import select
        stmt = select(Law).order_by(Law.effective_date.desc())
        if law_type:
            stmt = stmt.where(Law.law_type == law_type)
        if status:
            stmt = stmt.where(Law.status == status)
        stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        laws = result.scalars().all()
        return [LawOut(
            id=l.id, law_id=l.law_id, title=l.title, law_type=l.law_type,
            status=l.status, issue_date=l.issue_date.isoformat() if l.issue_date else None,
            effective_date=l.effective_date.isoformat() if l.effective_date else None,
            level=l.level,
        ) for l in laws]


# --- 企业 ---
@app.get("/api/companies", response_model=List[CompanyOut])
async def list_companies(
    name: Optional[str] = None,
    is_zxgk: Optional[bool] = None,
    region: Optional[str] = None,
    limit: int = Query(50, le=200),
):
    async with Database.session() as session:
        from sqlalchemy import select
        stmt = select(Company).order_by(Company.id.desc())
        if name:
            stmt = stmt.where(Company.company_name.contains(name))
        if is_zxgk is not None:
            stmt = stmt.where(Company.is_zxgk == is_zxgk)
        if region:
            stmt = stmt.where(Company.region == region)
        stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        comps = result.scalars().all()
        return [CompanyOut(
            id=c.id, unified_id=c.unified_id, company_name=c.company_name,
            legal_rep=c.legal_rep, business_status=c.business_status,
            industry=c.industry, region=c.region, is_zxgk=c.is_zxgk,
        ) for c in comps]


# --- 律所版 0.1 ---
@app.get("/api/firm/lawyers")
async def list_firm_lawyers(firm_id: str, role: Optional[str] = None):
    """律所律师列表"""
    async with Database.session() as session:
        from sqlalchemy import select
        stmt = select(Lawyer).where(Lawyer.firm_id == firm_id, Lawyer.is_active == True)
        if role:
            stmt = stmt.where(Lawyer.role == role)
        result = await session.execute(stmt)
        lawyers = result.scalars().all()
        return [{
            "id": l.id, "name": l.name, "email": l.email, "role": l.role,
            "specialties": l.specialties, "avatar_url": l.avatar_url,
        } for l in lawyers]


@app.post("/api/firm/time-entries")
async def create_time_entry(entry: TimeEntryIn, firm_id: str):
    """创建工时记录"""
    async with Database.session() as session:
        from decimal import Decimal
        record = FirmTimeEntry(
            firm_id=firm_id,
            lawyer_id=entry.lawyer_id,
            case_id=entry.case_id,
            entry_date=entry.entry_date,
            hours=Decimal(str(entry.hours)),
            description=entry.description,
            billable=entry.billable,
            rate=Decimal(str(entry.rate)) if entry.rate else None,
            amount=Decimal(str(entry.hours * entry.rate)) if entry.rate else None,
        )
        session.add(record)
        await session.commit()
        return {"id": record.id, "status": "created"}


@app.get("/api/firm/stats")
async def firm_stats(firm_id: str):
    """律所统计"""
    from sqlalchemy import select, func
    async with Database.session() as session:
        # 律师数
        lawyer_stmt = select(func.count(Lawyer.id)).where(Lawyer.firm_id == firm_id, Lawyer.is_active == True)
        lawyer_count = (await session.execute(lawyer_stmt)).scalar() or 0

        # 工时本月
        from datetime import date
        first_of_month = date.today().replace(day=1)
        time_stmt = select(func.sum(FirmTimeEntry.hours)).where(
            FirmTimeEntry.firm_id == firm_id,
            FirmTimeEntry.entry_date >= first_of_month,
        )
        month_hours = (await session.execute(time_stmt)).scalar() or 0

        return {
            "lawyer_count": lawyer_count,
            "month_hours": float(month_hours),
            "firm_id": firm_id,
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
