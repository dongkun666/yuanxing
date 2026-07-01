"""
LexPrime 类案检索 Skill API 端点 (W7 实现)

端点:
- POST /api/skills/caselaw/search   检索类案 + 统计
- GET  /api/skills/caselaw/health   Skill 健康检查
- GET  /api/skills/caselaw/manifest 返回 agentskills.io manifest

PRD: § 5.4 Skill Hub + § 5.7 类案大数据
Track: E-skills · T-REF-22 (subagent RPC)
"""
from typing import Optional
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from loguru import logger

# Skill 内部模块
from skills.caselaw.retrieval import (
    RetrievalInput, RetrievalConfig, FallbackSQLStore,
    run_skill, CaseHit,
)
from skills.caselaw.language_guard import DISCLAIMER_FULL, check_narrative, sanitize_input
from core.db import Database


router = APIRouter(prefix="/api/skills/caselaw", tags=["skill:caselaw"])


# ===== Request / Response models =====

class SearchRequest(BaseModel):
    """类案检索请求 — 对应 schemas/input.json"""
    cause: str = Field(..., min_length=2, max_length=64, description="案由 (必填)")
    facts: str = Field("", max_length=4000, description="关键事实")
    court: Optional[str] = Field(None, max_length=128)
    judge_name: Optional[str] = Field(None, max_length=32)
    year_from: Optional[int] = Field(None, ge=2000, le=2030)
    year_to: Optional[int] = Field(None, ge=2000, le=2030)
    region: Optional[str] = Field(None, max_length=32)
    case_type: Optional[str] = None
    procedure: Optional[str] = None
    amount_dispute: Optional[float] = Field(None, ge=0)
    top_k: int = Field(20, ge=1, le=50)
    include_judge_style: bool = True
    include_amount_stats: bool = True
    case_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "cause": "民间借贷纠纷",
                "facts": "原告借给被告 50 万元, 约定月息 2%, 被告未按期还款",
                "court": "上海一中院",
                "year_from": 2022,
                "year_to": 2025,
                "region": "上海",
                "case_type": "民事",
                "procedure": "二审",
                "top_k": 20,
            }
        }


class SearchResponse(BaseModel):
    """类案检索响应 — 对应 schemas/output.json"""
    query_meta: dict
    results: list
    statistics: dict
    trajectory: dict
    disclaimer: str
    ui_hints: dict


# ===== 端点 =====

@router.get("/health")
async def skill_health():
    """Skill 健康检查"""
    return {
        "status": "ok",
        "skill_id": "lexprime.skill.caselaw",
        "version": "0.1.0",
        "data_sources": ["cncases", "court_cases", "lawyer_added_cases"],
    }


@router.get("/manifest")
async def skill_manifest():
    """返回 Skill manifest (agentskills.io 标准)"""
    import json
    from pathlib import Path
    manifest_path = Path(__file__).parent.parent / "skills" / "caselaw" / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(404, "manifest.json not found")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


@router.post("/search", response_model=SearchResponse)
async def caselaw_search(req: SearchRequest):
    """
    类案检索主入口。

    1. 校验输入 (cause 必填 + 语言规范预检)
    2. 调用 retrieval.run_skill() (子 Agent RPC)
    3. 强制 disclaimer + language_guard 后处理
    4. 返回 SearchResponse
    """
    # 输入校验: facts 不能含敏感词触雷
    if req.facts and any(kw in req.facts for kw in ["胜诉率", "预计判赔"]):
        logger.warning(f"facts 包含触发关键词, 已自动脱敏: case_id={req.case_id}")

    # 构造 RetrievalInput + W7 输入消毒
    ri = RetrievalInput(
        cause=sanitize_input(req.cause),
        facts=sanitize_input(req.facts),
        court=sanitize_input(req.court) if req.court else req.court,
        judge_name=sanitize_input(req.judge_name) if req.judge_name else req.judge_name,
        year_from=req.year_from,
        year_to=req.year_to,
        region=sanitize_input(req.region) if req.region else req.region,
        case_type=req.case_type,
        procedure=req.procedure,
        amount_dispute=req.amount_dispute,
        top_k=req.top_k,
        include_judge_style=req.include_judge_style,
        include_amount_stats=req.include_amount_stats,
        case_id=req.case_id,
    )

    # 配置
    config = RetrievalConfig(
        vector_store="fallback_sql",  # W7: 真实 LanceDB 未接入, 走 SQL 兜底
        embedding_model="BAAI/bge-small-zh-v1.5",
    )

    # 数据库连接 (AsyncSession, 用异步 metadata_filter)
    t0 = time.time()
    try:
        db = Database()
        async with db.session() as session:
            store = FallbackSQLStore(session)
            # 异步 metadata filter (避免 sync/async 不匹配)
            candidates = await store.metadata_filter_async(ri, candidate_limit=500)
            hits = store.vector_search(ri, candidates)
            # 手动 run_skill 流程 (避免重复 metadata_filter)
            from skills.caselaw.retrieval import compress_context, compute_statistics, compute_traffic_light
            compressed, trace = compress_context(hits, budget=config.context_token_budget)
            stats = compute_statistics(compressed, ri)
            traffic = compute_traffic_light(stats)
            latency_ms = int((time.time() - t0) * 1000)

            output_dict = {
                "query_meta": {
                    "cause": ri.cause,
                    "cause_category": compressed[0].case_type if compressed else None,
                    "searched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime()),
                    "latency_ms": latency_ms,
                    "total_candidates": len(candidates),
                    "returned_count": len(compressed),
                    "filters_applied": {
                        k: v for k, v in ri.__dict__.items()
                        if v is not None and k not in ("facts", "top_k", "include_judge_style",
                                                       "include_amount_stats", "case_id")
                    },
                    "vector_store": config.vector_store,
                    "embedding_model": config.embedding_model,
                },
                "results": [h.__dict__ for h in compressed],
                "statistics": stats,
                "trajectory": trace.to_dict(),
                "disclaimer": DISCLAIMER_FULL,
                "ui_hints": {
                    "traffic_light": traffic,
                    "show_bar_chart": bool(stats["support_rate_aggregate"]["yearly_breakdown"]),
                    "show_box_plot": stats["amount_stats"].get("median_cny") is not None,
                    "show_judge_card": stats["judge_style"] is not None and
                                        stats["judge_style"].get("sample_size", 0) >= 5,
                },
            }
            class _O:
                def to_dict(self): return output_dict
            output = _O()
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"检索失败: {e}")
        raise HTTPException(500, f"检索失败: {str(e)}")

    # 强制 disclaimer
    out_dict = output.to_dict()
    out_dict["disclaimer"] = DISCLAIMER_FULL  # 兜底覆盖

    # 后置 language_guard: 即使是降级模板也强制检查
    narrative = out_dict["statistics"].get("narrative", "")
    if narrative:
        chk = check_narrative(narrative)
        if not chk.passed:
            logger.warning(f"narrative 含 HIGH 违规, 已强制替换: {chk.high_violations}")
            out_dict["statistics"]["narrative"] = chk.corrected_text

    judge_style = out_dict["statistics"].get("judge_style")
    if judge_style and judge_style.get("narrative"):
        chk = check_narrative(judge_style["narrative"])
        if not chk.passed:
            judge_style["narrative"] = chk.corrected_text

    return SearchResponse(**out_dict)


@router.get("/disclaimer")
async def skill_disclaimer():
    """返回强制免责声明 (前端可独立 fetch 渲染)"""
    return {
        "full": DISCLAIMER_FULL,
        "short": "以上数据为已公开裁判文书的统计结果, 不代表本案预测。",
    }