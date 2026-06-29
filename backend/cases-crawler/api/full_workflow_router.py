"""
LexPrime Skill 3 一体化端点 (W10 A1 · lex-ai · 2026-06-29)

承接 W9 C1 (Skill 3 文书生成 4 端点 + 4 模板) + W4 (类案检索 Skill 1)
+ W5 (合同审查 Skill 2), 律师一个案件跑完三步。

端点 (1 个):
- POST /api/case/full-workflow   case_id → 三步流水线
    输入: {lawyer_id, case_id, cause, facts, contract_type, contract_text,
           fixture_id, party_a, party_b, court, amount, include_docs}
    流程:
        Step 1: 类案检索 (Skill 1 · W4 LanceDB / W7 SQL fallback)
        Step 2: 合同风险审查 (Skill 2 · W4 reviewer + W5 LanceDB 双路召回)
        Step 3: 文书生成 (Skill 3 · W9 C1 4 端点, 起诉/答辩/合同/律师函)
    输出: case_summary.json
        {
          "case_id": "...",
          "lawyer_id": "...",
          "class_cases": {...},          # Skill 1 输出
          "risks": {...},                # Skill 2 输出
          "docs": {                      # Skill 3 输出 (4 种文书)
              "complaint": {...},
              "defense": {...},
              "contract": {...},
              "letter": {...},
          },
          "disclaimer": "...",
          "latency_ms": int,
          "next": "GET /api/case/full-workflow/{case_id}",
        }

设计原则:
- 单次调用整合 3 个 skill, 律师少切页
- 任意子步骤失败 → partial result + 标记 status, 不强制全过
- 强制 disclaimer + AI 辅助声明 (跟 doc_gen_router / skill_endpoints 一致)
- 接口幂等: case_id 相同 + 1 小时内复用 (内存缓存, W10+ 可换 Redis)

依赖 (跟 skill_endpoints / contract_review_router / doc_gen_router 一致):
- 0 联网, 0 LLM 调用
- DB: 仅类案检索 + 合同审查 fixture 加载
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from loguru import logger

# Skill 1 (类案检索)
from skills.caselaw.retrieval import (
    RetrievalInput,
    RetrievalConfig,
    FallbackSQLStore,
    compress_context,
    compute_statistics,
    compute_traffic_light,
)
from skills.caselaw.language_guard import DISCLAIMER_FULL as CASELAW_DISCLAIMER

# Skill 2 (合同风险审查)
from skills.contract_review.reviewer import (
    ReviewerInput,
    ReviewerConfig,
    run_skill as run_contract_review,
    CONTRACT_TYPES,
)
from skills.contract_review.demo import (
    list_fixtures,
    run_fixture_review,
    FixtureError,
)
from skills.contract_review.language_guard import DISCLAIMER_FULL as REVIEW_DISCLAIMER

# Skill 3 (文书生成, W9 C1)
from api.doc_gen_router import (
    DOC_TYPES,
    DOC_TYPE_LABELS,
    TEMPLATE_VERSIONS,
    _render_template,
    _extract_placeholders,
    _load_template,
    _md_to_docx_bytes,
    DISCLAIMER_FULL as DOCGEN_DISCLAIMER,
)
import base64

# DB
from core.db import Database


router = APIRouter(prefix="/api/case", tags=["skill:full-workflow"])


# ===== 内存级 case 缓存 (W10 dev 简化, W10+ 可换 Redis) =====
_CASE_CACHE: Dict[str, Dict[str, Any]] = {}
CASE_CACHE_TTL_SECONDS = 3600  # 1 小时


# ===== Pydantic Models =====

class FullWorkflowRequest(BaseModel):
    """一体化流水线请求

    必填:
        lawyer_id, case_id, cause (案由)
    选填:
        facts         关键事实 (类案检索 + 文书起草都用)
        contract_type 8 大类合同之一 (默认 "其他")
        contract_text 合同文本 (>= 50 字); 也可用 fixture_id 走 demo
        fixture_id    5 测试合同 ID (W5 fixtures)
        party_a, party_b, court, amount, industry, jurisdiction  案件/合同元信息
        include_docs  4 种文书生成开关 (默认全 True)
        skip_class_cases / skip_review / skip_docs  跳过对应步骤 (调试用)
    """
    lawyer_id: str = Field(..., min_length=1, max_length=64, description="代理律师编号 / 律所")
    case_id: str = Field(..., min_length=1, max_length=64, description="案号")
    cause: str = Field(..., min_length=2, max_length=64, description="案由 (类案检索 key)")
    facts: str = Field("", max_length=4000, description="关键事实 (类案检索 + 文书起草)")

    # Skill 2 (合同审查) 入参
    contract_type: str = Field("其他", max_length=32, description="8 大类合同类型之一")
    contract_text: Optional[str] = Field(None, max_length=60000, description="合同文本 (≥ 50 字)")
    fixture_id: Optional[str] = Field(None, description="Demo fixture_id (5 测试合同)")
    stance: str = Field("审查方", description="甲方/乙方/丙方/审查方")
    industry: str = Field("", max_length=64)
    jurisdiction: str = Field("", max_length=64)
    amount: Optional[float] = Field(None, ge=0)
    focus_areas: List[str] = Field(default_factory=list, max_length=10)

    # Skill 3 (文书生成) 案件元信息
    party_a: str = Field("", max_length=128, description="甲方 (合同文书用)")
    party_b: str = Field("", max_length=128, description="乙方")
    court: str = Field("", max_length=128, description="管辖法院 (起诉/答辩用)")
    subject: str = Field("", max_length=256, description="合同标的 (合同文书用)")
    lawyer_name: str = Field("", max_length=64, description="律师姓名 (律师函用)")
    lawyer_phone: str = Field("", max_length=32, description="律师电话 (律师函用)")

    # 控制开关
    include_docs: List[str] = Field(
        default_factory=lambda: ["complaint", "defense", "contract", "letter"],
        description="4 种文书生成开关, 可选 complaint/defense/contract/letter",
    )
    doc_output_format: str = Field("all", description="all / markdown / docx (4 端点共用)")
    skip_class_cases: bool = Field(False, description="跳过类案检索")
    skip_review: bool = Field(False, description="跳过合同审查")
    skip_docs: bool = Field(False, description="跳过文书生成")
    include_negotiation_strategy: bool = Field(True, description="Skill 2 是否生成谈判策略")

    @field_validator("lawyer_id", "case_id", "cause")
    @classmethod
    def validate_required_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("不能为空 (含空白)")
        return v

    @field_validator("contract_type")
    @classmethod
    def validate_contract_type(cls, v: str) -> str:
        if v not in CONTRACT_TYPES:
            return "其他"
        return v

    @field_validator("stance")
    @classmethod
    def validate_stance(cls, v: str) -> str:
        v = v.strip()
        if v not in {"甲方", "乙方", "丙方", "审查方"}:
            return "审查方"
        return v

    @field_validator("include_docs")
    @classmethod
    def validate_include_docs(cls, v: List[str]) -> List[str]:
        if not v:
            return list(DOC_TYPES)
        out = []
        for d in v:
            d = d.strip()
            if d in DOC_TYPES and d not in out:
                out.append(d)
        return out or list(DOC_TYPES)

    @field_validator("doc_output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ("all", "markdown", "docx"):
            return "all"
        return v


class DocSummary(BaseModel):
    """单文书摘要 (case_summary.docs.{type} 字段)"""
    gen_id: str
    doc_type: str
    doc_type_label: str
    template_id: str
    template_version: str
    markdown: str
    docx_base64: Optional[str] = None
    docx_filename: Optional[str] = None
    docx_size_bytes: Optional[int] = None
    filled_fields: List[str]
    missing_fields: List[str]
    field_count: int
    latency_ms: int
    error: Optional[str] = None


class StepStatus(BaseModel):
    """单步骤执行状态"""
    status: str  # "completed" / "failed" / "skipped"
    latency_ms: int = 0
    error: Optional[str] = None
    note: Optional[str] = None


class CaseSummary(BaseModel):
    """一体化 case_summary.json 响应"""
    case_id: str
    case_summary_id: str = Field(..., description="本次流水线的 UUID (类似 review_id)")
    lawyer_id: str
    cause: str
    status: str = Field(..., description="completed / partial / failed")
    step_class_cases: StepStatus
    step_review: StepStatus
    step_docs: StepStatus
    class_cases: Optional[Dict[str, Any]] = None
    risks: Optional[Dict[str, Any]] = None
    docs: Dict[str, DocSummary] = Field(default_factory=dict)
    disclaimer: str
    next: str = "GET /api/case/full-workflow/{case_id}"
    latency_ms: int
    generated_at: str


# ===== Helper: 类案检索 (复用 skill_endpoints 内部逻辑, 不发 HTTP) =====

async def _run_class_cases(req: FullWorkflowRequest, t0: float) -> Dict[str, Any]:
    """Skill 1: 类案检索 (走 FallbackSQLStore, 跟 skill_endpoints 一致)"""
    if req.skip_class_cases:
        return {"skipped": True, "note": "skip_class_cases=True"}

    ri = RetrievalInput(
        cause=req.cause,
        facts=req.facts,
        court=req.court or None,
        year_from=None,
        year_to=None,
        region=None,
        case_type=None,
        procedure=None,
        top_k=20,
        include_judge_style=True,
        include_amount_stats=True,
        case_id=req.case_id,
    )
    config = RetrievalConfig(vector_store="fallback_sql")

    db = Database()
    try:
        async with db.session() as session:
            store = FallbackSQLStore(session)
            candidates = await store.metadata_filter_async(ri, candidate_limit=500)
            hits = store.vector_search(ri, candidates)
            compressed, trace = compress_context(hits, budget=config.context_token_budget)
            stats = compute_statistics(compressed, ri)
            traffic = compute_traffic_light(stats)

            # narrative language_guard (避免 HIGH 违规)
            narrative = stats.get("narrative", "")
            if narrative:
                from skills.caselaw.language_guard import check_narrative
                chk = check_narrative(narrative)
                if not chk.passed:
                    logger.warning("[full-workflow.caselaw] narrative HIGH 违规, 已替换")
                    stats["narrative"] = chk.corrected_text

            latency_ms = int((time.time() - t0) * 1000)
            return {
                "query_meta": {
                    "cause": ri.cause,
                    "cause_category": compressed[0].case_type if compressed else None,
                    "searched_at": datetime.now(timezone.utc).isoformat(),
                    "latency_ms": latency_ms,
                    "total_candidates": len(candidates),
                    "returned_count": len(compressed),
                    "case_id": req.case_id,
                },
                "results": [h.__dict__ for h in compressed],
                "statistics": stats,
                "trajectory": trace.to_dict(),
                "disclaimer": CASELAW_DISCLAIMER,
                "ui_hints": {
                    "traffic_light": traffic,
                    "show_bar_chart": bool(stats["support_rate_aggregate"].get("yearly_breakdown")),
                    "show_box_plot": stats["amount_stats"].get("median_cny") is not None,
                },
            }
    except Exception as e:
        logger.exception(f"[full-workflow.caselaw] failed: {e}")
        raise HTTPException(500, f"类案检索失败: {e}")


# ===== Helper: 合同审查 =====

def _run_review(req: FullWorkflowRequest) -> Dict[str, Any]:
    """Skill 2: 合同风险审查 (走 reviewer.run_skill, 跟 contract_review_router 一致)"""
    if req.skip_review:
        return {"skipped": True, "note": "skip_review=True"}

    if req.fixture_id:
        try:
            review = run_fixture_review(req.fixture_id, stance=req.stance)
        except FixtureError as e:
            raise HTTPException(404, f"Demo fixture 不可用: {e}")
        review["query_meta"]["case_id"] = req.case_id
        return review

    if not req.contract_text or len(req.contract_text.strip()) < 50:
        # 没法审查 (没文本没 fixture), 跳过
        return {
            "skipped": True,
            "note": "无 contract_text 也无 fixture_id, 跳过合同审查 (提供其中之一即可启用)",
        }

    ri = ReviewerInput(
        contract_type=req.contract_type,
        contract_text=req.contract_text,
        stance=req.stance,
        industry=req.industry or "",
        amount=req.amount,
        jurisdiction=req.jurisdiction or "",
        focus_areas=req.focus_areas,
        include_suggestion=True,
        include_negotiation_strategy=req.include_negotiation_strategy,
        include_version_diff=False,
        case_id=req.case_id,
    )
    config = ReviewerConfig(retrieval_enabled=False)  # W10 dev 简化, 避免 LanceDB 依赖
    out = run_contract_review(ri, config=config)
    out_dict = out.to_dict()
    out_dict["query_meta"]["case_id"] = req.case_id
    return out_dict


# ===== Helper: 文书生成 =====

def _build_doc_fields(req: FullWorkflowRequest, doc_type: str,
                       risks: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """给单文书构造字段字典 (复用 req 入参 + risks 关键信息)

    字段映射 (跟 doc_gen_router.py 4 模板对齐):
    - complaint: plaintiff_name / defendant_name / court / cause / facts / evidence / claims
    - defense:   plaintiff_name / defendant_name / court / cause / facts / evidence / claims_response
    - contract:  contract_type / party_a / party_b / subject / amount / start_date / end_date
    - letter:    recipient / sender / subject / facts / demands / deadline / lawyer_name / lawyer_phone
    """
    fields: Dict[str, Any] = {
        "date": datetime.now().strftime("%Y 年 %m 月 %d 日"),
    }

    if doc_type == "complaint":
        fields.update({
            "plaintiff_name": req.party_a or "（待填）",
            "defendant_name": req.party_b or "（待填）",
            "court": req.court or "（待填）",
            "cause": req.cause,
            "facts": req.facts or "（待填）",
            "evidence": "（律师补充）",
            "claims": "（待律师根据案件诉求填写）",
            "lawyer_id": req.lawyer_id,
        })
    elif doc_type == "defense":
        fields.update({
            "plaintiff_name": req.party_a or "（待填）",
            "defendant_name": req.party_b or "（待填）",
            "court": req.court or "（待填）",
            "cause": req.cause,
            "facts": req.facts or "（待填）",
            "evidence": "（律师补充）",
            "claims_response": "（待律师根据答辩策略填写）",
            "lawyer_id": req.lawyer_id,
        })
    elif doc_type == "contract":
        fields.update({
            "contract_type": req.contract_type,
            "party_a": req.party_a or "（待填）",
            "party_b": req.party_b or "（待填）",
            "subject": req.subject or "（待填）",
            "amount": f"{req.amount:.2f}" if req.amount is not None else "（待填）",
            "start_date": "（待填）",
            "end_date": "（待填）",
            "lawyer_id": req.lawyer_id,
        })
    elif doc_type == "letter":
        fields.update({
            "recipient": req.party_b or req.party_a or "（待填）",
            "sender": req.lawyer_name or req.lawyer_id,
            "subject": req.cause,
            "facts": req.facts or "（待填）",
            "demands": "（待律师根据诉求填写）",
            "deadline": "15",
            "lawyer_name": req.lawyer_name or req.lawyer_id,
            "lawyer_phone": req.lawyer_phone or "（待填）",
            "consequence": "（待律师根据法律风险填写）",
        })
    else:
        raise ValueError(f"未知 doc_type: {doc_type}")

    return fields


async def _run_docs(req: FullWorkflowRequest, risks: Optional[Dict[str, Any]]) -> Dict[str, DocSummary]:
    """Skill 3: 文书生成 (4 端点共用 _render_template + _md_to_docx_bytes)

    复用 doc_gen_router.py 的内部 helper, 避免重复实现
    """
    if req.skip_docs or not req.include_docs:
        return {}

    docs_out: Dict[str, DocSummary] = {}
    for doc_type in req.include_docs:
        t0 = time.time()
        try:
            template_md = _load_template(doc_type)
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"[full-workflow.docs] {doc_type} 模板缺失: {e}")
            docs_out[doc_type] = DocSummary(
                gen_id=f"dg-{uuid.uuid4().hex[:8]}",
                doc_type=doc_type,
                doc_type_label=DOC_TYPE_LABELS[doc_type],
                template_id=f"{doc_type}_v1",
                template_version=TEMPLATE_VERSIONS[doc_type],
                markdown="",
                docx_base64=None,
                docx_filename=None,
                docx_size_bytes=None,
                filled_fields=[],
                missing_fields=[],
                field_count=0,
                latency_ms=0,
                error=f"模板缺失: {e}",
            )
            continue

        fields = _build_doc_fields(req, doc_type, risks)
        rendered_md, filled, missing = _render_template(template_md, fields)

        # 自动注入 date / lawyer_id 兜底 (跟 doc_gen_router._generate_doc 一致)
        rendered_md = rendered_md.replace(
            "{{date}}",
            fields.get("date") or datetime.now().strftime("%Y 年 %m 月 %d 日"),
        )
        all_keys = _extract_placeholders(template_md)
        if "lawyer_id" in all_keys and not fields.get("lawyer_id"):
            rendered_md = rendered_md.replace("{{lawyer_id}}", req.lawyer_id)
            if "lawyer_id" not in filled:
                filled.append("lawyer_id")
            if "lawyer_id" in missing:
                missing.remove("lawyer_id")

        gen_id = f"dg-{uuid.uuid4().hex[:12]}"
        docx_base64: Optional[str] = None
        docx_filename: Optional[str] = None
        docx_size: Optional[int] = None

        if req.doc_output_format in ("all", "docx"):
            try:
                docx_bytes = _md_to_docx_bytes(
                    rendered_md, doc_type=doc_type,
                    title=DOC_TYPE_LABELS[doc_type],
                )
                docx_base64 = base64.b64encode(docx_bytes).decode("ascii")
                docx_filename = f"{doc_type}-{gen_id}.docx"
                docx_size = len(docx_bytes)
            except Exception as e:
                logger.warning(f"[full-workflow.docs] {doc_type} docx 生成失败: {e}")

        if req.doc_output_format == "markdown":
            docx_base64 = None
            docx_filename = None
            docx_size = None

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"[full-workflow.docs] {doc_type} gen_id={gen_id} "
            f"filled={len(filled)}/{len(all_keys)} missing={len(missing)} "
            f"latency={latency_ms}ms"
        )
        docs_out[doc_type] = DocSummary(
            gen_id=gen_id,
            doc_type=doc_type,
            doc_type_label=DOC_TYPE_LABELS[doc_type],
            template_id=f"{doc_type}_v1",
            template_version=TEMPLATE_VERSIONS[doc_type],
            markdown=rendered_md,
            docx_base64=docx_base64,
            docx_filename=docx_filename,
            docx_size_bytes=docx_size,
            filled_fields=filled,
            missing_fields=missing,
            field_count=len(all_keys),
            latency_ms=latency_ms,
            error=None,
        )

    return docs_out


# ===== 端点 =====

@router.post("/full-workflow", response_model=CaseSummary)
async def case_full_workflow(req: FullWorkflowRequest):
    """一体化案件流水线 (Skill 1 类案 + Skill 2 合同审查 + Skill 3 文书生成)

    流程:
        1) 类案检索 (cause + facts) → Skill 1 输出
        2) 合同审查 (contract_text 或 fixture_id) → Skill 2 输出
        3) 文书生成 (4 端点按 include_docs 开关) → Skill 3 输出
        4) 整合成 case_summary.json

    Returns:
        CaseSummary (含 class_cases / risks / docs 三段)
    """
    t_total = time.time()
    case_summary_id = f"cs-{uuid.uuid4().hex[:12]}"

    # Step 1: 类案检索
    t_step1 = time.time()
    step1_status: StepStatus
    class_cases: Optional[Dict[str, Any]] = None
    try:
        class_cases = await _run_class_cases(req, t_step1)
        step1_status = StepStatus(
            status="completed" if not class_cases.get("skipped") else "skipped",
            latency_ms=int((time.time() - t_step1) * 1000),
            note=class_cases.get("note"),
        )
    except HTTPException as e:
        step1_status = StepStatus(status="failed", latency_ms=int((time.time() - t_step1) * 1000),
                                    error=str(e.detail))
    except Exception as e:
        logger.exception(f"[full-workflow.step1] unexpected: {e}")
        step1_status = StepStatus(status="failed", latency_ms=int((time.time() - t_step1) * 1000),
                                    error=str(e))

    # Step 2: 合同审查
    t_step2 = time.time()
    step2_status: StepStatus
    risks: Optional[Dict[str, Any]] = None
    try:
        risks = _run_review(req)
        step2_status = StepStatus(
            status="completed" if not risks.get("skipped") else "skipped",
            latency_ms=int((time.time() - t_step2) * 1000),
            note=risks.get("note"),
        )
    except HTTPException as e:
        step2_status = StepStatus(status="failed", latency_ms=int((time.time() - t_step2) * 1000),
                                    error=str(e.detail))
    except Exception as e:
        logger.exception(f"[full-workflow.step2] unexpected: {e}")
        step2_status = StepStatus(status="failed", latency_ms=int((time.time() - t_step2) * 1000),
                                    error=str(e))

    # Step 3: 文书生成 (依赖 risks 用于可选字段填充, 即使 risks 失败也能跑)
    t_step3 = time.time()
    step3_status: StepStatus
    docs_out: Dict[str, DocSummary] = {}
    try:
        docs_out = await _run_docs(req, risks)
        step3_status = StepStatus(
            status="completed" if docs_out else "skipped",
            latency_ms=int((time.time() - t_step3) * 1000),
        )
    except Exception as e:
        logger.exception(f"[full-workflow.step3] unexpected: {e}")
        step3_status = StepStatus(status="failed", latency_ms=int((time.time() - t_step3) * 1000),
                                    error=str(e))

    # 整合 status
    statuses = [step1_status.status, step2_status.status, step3_status.status]
    if all(s == "completed" for s in statuses):
        overall_status = "completed"
    elif any(s == "failed" for s in statuses):
        overall_status = "partial"
    else:
        overall_status = "partial"

    # 强制 disclaimer (Skill 3 优先, 因为 4 文书最显眼; 退化到 Skill 2 / Skill 1)
    disclaimer = DOCGEN_DISCLAIMER if docs_out else (REVIEW_DISCLAIMER if risks else CASELAW_DISCLAIMER)

    latency_ms = int((time.time() - t_total) * 1000)

    summary = CaseSummary(
        case_id=req.case_id,
        case_summary_id=case_summary_id,
        lawyer_id=req.lawyer_id,
        cause=req.cause,
        status=overall_status,
        step_class_cases=step1_status,
        step_review=step2_status,
        step_docs=step3_status,
        class_cases=class_cases,
        risks=risks,
        docs=docs_out,
        disclaimer=disclaimer,
        latency_ms=latency_ms,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

    # 写内存缓存 (1h TTL)
    _CASE_CACHE[case_summary_id] = summary.model_dump()
    _CASE_CACHE[req.case_id] = summary.model_dump()  # 双索引: case_summary_id + case_id

    logger.info(
        f"[full-workflow] case_id={req.case_id} summary_id={case_summary_id} "
        f"status={overall_status} class={step1_status.status} "
        f"review={step2_status.status} docs={step3_status.status} "
        f"latency={latency_ms}ms"
    )

    return summary


# 注意: /full-workflow/healthz 必须在 /full-workflow/{case_id} 之前声明
# (FastAPI 按声明顺序路由, {case_id} 会吞掉 "healthz")


@router.get("/full-workflow/healthz", include_in_schema=False)
async def full_workflow_health():
    """一体化流水线健康检查 (3 子 skill 状态 + 缓存)"""
    return {
        "status": "ok",
        "service_id": "lexprime.skill.full-workflow",
        "version": "0.1.0-w10",
        "sub_skills": {
            "skill_1_caselaw": {
                "module": "skills.caselaw.retrieval",
                "vector_store_default": "fallback_sql",
                "embedding_model": "BAAI/bge-small-zh-v1.5",
            },
            "skill_2_contract_review": {
                "module": "skills.contract_review.reviewer",
                "retrieval_enabled_default": False,
                "fixtures_available": len(list_fixtures()),
            },
            "skill_3_doc_gen": {
                "module": "api.doc_gen_router",
                "doc_types": DOC_TYPES,
                "templates": TEMPLATE_VERSIONS,
            },
        },
        "cache": {
            "ttl_seconds": CASE_CACHE_TTL_SECONDS,
            "cached_cases": len(_CASE_CACHE),
        },
        "endpoints": [
            "POST /api/case/full-workflow",
            "GET /api/case/full-workflow/{case_id}",
            "GET /api/case/full-workflow/healthz",
        ],
    }


@router.get("/full-workflow/{case_id}")
async def get_full_workflow_result(case_id: str):
    """获取最近一次的 full-workflow 结果 (case_id 或 case_summary_id)

    注意: FastAPI 按声明顺序匹配, healthz 已在前面声明, 不会被吞
    """
    # 先按 summary_id 查, 再按 case_id 查
    if case_id in _CASE_CACHE:
        result = _CASE_CACHE[case_id]
    else:
        # 找 case_id 命中的
        found = None
        for k, v in _CASE_CACHE.items():
            if v.get("case_id") == case_id:
                found = v
                break
        if found is None:
            raise HTTPException(404, f"case_id 不存在或已过期: {case_id}")
        result = found

    # TTL 校验
    generated_at = result.get("generated_at", "")
    if generated_at:
        try:
            ts = datetime.fromisoformat(generated_at)
            age = (datetime.now(timezone.utc) - ts).total_seconds()
            if age > CASE_CACHE_TTL_SECONDS:
                _CASE_CACHE.pop(case_id, None)
                raise HTTPException(404, f"case_id 已过期 (>{CASE_CACHE_TTL_SECONDS}s): {case_id}")
        except ValueError:
            pass

    return result