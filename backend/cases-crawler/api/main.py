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
"""
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from loguru import logger

from core.db import Database, ESClient, Neo4jClient
from core.config import settings
from core.models import Case, Law, Company, Lawyer, Firm, FirmTimeEntry


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


# ========== 端点 ==========
@app.get("/api/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "version": "0.1.0",
        "databases": {
            "postgres": Database._engine is not None,
            "elasticsearch": ESClient._client is not None,
            "neo4j": Neo4jClient._driver is not None,
        },
    }


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
