"""
LexPrime W12 A2 双审工作流 API Router (lex-coder · 2026-06-30)

承接 core/doc_workflow.py 状态机 + skills/contract_review/reviewer 风险标注

端点 (4 个):
- GET  /api/doc-gen/{doc_id}/state      查询工作流状态
- PATCH /api/doc-gen/{doc_id}/state     状态转换 (5 状态机)
- POST /api/doc-gen/{doc_id}/risk-annotation  4 文书风险标注 (Skill 2 扩展)
- GET  /api/doc-gen/workflow/board      状态看板 (前端看板)
- GET  /api/doc-gen/workflow/health     健康检查 (含状态机统计)

数据流:
1. 律师提交 doc_id + case_id + doc_type + actor + reason
2. core.doc_workflow 状态机校验转换合法性
3. 写入 DocReviewState 表 (history JSON)
4. 返回 DocWorkflowStatus

风险标注:
- 调用 skills.contract_review.reviewer.annotate_doc_risk_dimensions
- 4 文书类型各自维度 (PRD V5.0 § 11)
- 复用 Skill 2 FATAL/MAJOR/ADVISORY 关键词库

依赖:
- core.doc_workflow (状态机)
- core.db (Database session)
- skills.contract_review.reviewer (风险标注)
- doc_gen_router (DISCLAIMER 复用)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from core.db import Database
from core.doc_workflow import (
    DocState,
    StateTransitionError,
    transition_to_ai_reviewed,
    transition_to_lawyer_reviewed,
    transition_to_client_signed,
    transition_to_archived,
    transition_back,
    get_workflow_status,
    list_workflow_by_state,
    DOC_WORKFLOW_DISCLAIMER,
)

# 风险标注 (Skill 2 W12 A2 扩展)
from skills.contract_review.reviewer import (
    annotate_doc_risk_dimensions,
    DOC_TYPE_LABELS as SKILL2_DOC_TYPE_LABELS,
    DOC_TYPE_RISK_DIMENSIONS,
)


router = APIRouter(prefix="/api/doc-gen", tags=["skill:doc-workflow"])


# ===== Pydantic Models =====

class DocWorkflowTransitionRequest(BaseModel):
    """状态转换请求"""
    target_state: Optional[str] = Field(
        None,
        description="目标状态 (5 状态之一: draft/ai_reviewed/lawyer_reviewed/client_signed/archived)"
    )
    transition_back: bool = Field(
        False,
        description="回退到上一状态 (律师返工)"
    )
    actor: str = Field(..., min_length=1, max_length=64, description="操作人 (律师 ID)")
    reason: str = Field(..., min_length=1, max_length=500, description="转换原因 (审计追溯)")
    case_id: Optional[str] = Field(None, max_length=64, description="案号 (新建时必填)")
    doc_type: Optional[str] = Field(
        None,
        description="4 文书类型 (新建时必填): complaint/defense/contract/letter"
    )
    risk_summary: Optional[Dict[str, Any]] = Field(
        None,
        description="AI 风险标注 (ai_reviewed 时可附带)"
    )
    lawyer_notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="律师审核备注 (lawyer_reviewed 时可附带)"
    )

    @field_validator("actor", "reason")
    @classmethod
    def validate_required_text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("不能为空 (含空白)")
        return v

    @field_validator("target_state")
    @classmethod
    def validate_target_state(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if v not in [s.value for s in DocState]:
            raise ValueError(f"target_state 必须是 5 状态之一: {[s.value for s in DocState]}")
        return v

    @field_validator("doc_type")
    @classmethod
    def validate_doc_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if v not in DOC_TYPE_RISK_DIMENSIONS:
            raise ValueError(f"doc_type 必须是 4 文书类型之一: {list(DOC_TYPE_RISK_DIMENSIONS.keys())}")
        return v


class DocWorkflowStateResponse(BaseModel):
    """工作流状态响应 (前端双审界面用)"""
    doc_id: str
    case_id: Optional[str]
    doc_type: str
    doc_type_label: Optional[str] = None
    state: str
    state_label: str
    next_state: Optional[str]
    previous_state: Optional[str]
    history: List[Dict[str, Any]]
    current_risk_summary: Optional[Dict[str, Any]]
    lawyer_notes: Optional[str]
    actor: Optional[str]
    has_signature: bool
    signature_signed_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    transitionable_targets: List[str]
    disclaimer: str = DOC_WORKFLOW_DISCLAIMER


STATE_LABELS = {
    DocState.DRAFT.value: "起草中",
    DocState.AI_REVIEWED.value: "AI 已审",
    DocState.LAWYER_REVIEWED.value: "律师已审",
    DocState.CLIENT_SIGNED.value: "客户已签",
    DocState.ARCHIVED.value: "已归档",
}


class RiskAnnotationRequest(BaseModel):
    """风险标注请求 (前端传文书 markdown)"""
    doc_id: str = Field(..., min_length=1, max_length=64)
    doc_type: str = Field(..., description="4 文书类型: complaint/defense/contract/letter")
    doc_markdown: str = Field(..., min_length=10, max_length=60000,
                               description="文书 markdown 全文")
    case_id: Optional[str] = Field(None, max_length=64)

    @field_validator("doc_type")
    @classmethod
    def validate_doc_type(cls, v: str) -> str:
        v = v.strip()
        if v not in DOC_TYPE_RISK_DIMENSIONS:
            raise ValueError(f"doc_type 必须是 4 文书类型之一: {list(DOC_TYPE_RISK_DIMENSIONS.keys())}")
        return v


class DimensionAnnotationOut(BaseModel):
    """单维度标注 (响应)"""
    dimension: str
    risk_level: str
    matched_keywords: List[str]
    description: str
    matched_count: int


class RiskAnnotationResponse(BaseModel):
    """风险标注响应"""
    doc_id: str
    case_id: Optional[str]
    doc_type: str
    doc_type_label: str
    dimensions: List[DimensionAnnotationOut]
    fatal_count: int
    major_count: int
    advisory_count: int
    ok_count: int
    overall_risk_level: str
    disclaimer: str
    latency_ms: int
    next: str = "POST /api/doc-gen/{doc_id}/state (transition to ai_reviewed)"


# ===== 端点 =====

@router.get("/workflow/health")
async def workflow_health():
    """双审工作流健康检查 (含 5 状态机 + 风险标注统计)"""
    return {
        "status": "ok",
        "service_id": "lexprime.skill.doc-workflow",
        "version": "0.1.0-w12",
        "states": [s.value for s in DocState],
        "state_labels": STATE_LABELS,
        "valid_transitions": {
            s.value: VALID_TRANSITIONS_DISPLAY.get(s.value, [])
            for s in DocState
        },
        "doc_type_dimensions": DOC_TYPE_RISK_DIMENSIONS,
        "endpoints": [
            "GET /api/doc-gen/{doc_id}/state",
            "PATCH /api/doc-gen/{doc_id}/state",
            "POST /api/doc-gen/{doc_id}/risk-annotation",
            "GET /api/doc-gen/workflow/board",
            "GET /api/doc-gen/workflow/health",
        ],
    }


VALID_TRANSITIONS_DISPLAY = {
    "draft": ["ai_reviewed"],
    "ai_reviewed": ["lawyer_reviewed"],
    "lawyer_reviewed": ["client_signed"],
    "client_signed": ["archived"],
    "archived": [],
}


@router.get("/workflow/board")
async def workflow_board(
    state: Optional[str] = Query(None, description="5 状态之一, 不传返全部"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    """状态看板 (前端看板 + 调度面板用)"""
    async with Database.session() as session:
        if state:
            if state not in [s.value for s in DocState]:
                raise HTTPException(400, f"state 必须是 5 状态之一: {[s.value for s in DocState]}")
            records = await list_workflow_by_state(session, state, limit=limit, offset=offset)
        else:
            # 全部状态
            from sqlalchemy import select
            from core.doc_workflow import DocReviewState
            stmt = (
                select(DocReviewState)
                .order_by(DocReviewState.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(stmt)
            records = list(result.scalars().all())

        return {
            "total": len(records),
            "state_filter": state,
            "items": [_serialize_state(r) for r in records],
            "limit": limit,
            "offset": offset,
        }


@router.get("/{doc_id}/state", response_model=DocWorkflowStateResponse)
async def get_doc_workflow_state(doc_id: str):
    """查询双审工作流状态 (含签字状态)"""
    async with Database.session() as session:
        status = await get_workflow_status(session, doc_id)
        if status is None:
            raise HTTPException(404, f"doc_id 不存在: {doc_id}")

        doc_type_label = SKILL2_DOC_TYPE_LABELS.get(status.doc_type)
        state_label = STATE_LABELS.get(status.state, status.state)

        return DocWorkflowStateResponse(
            doc_id=status.doc_id,
            case_id=status.case_id,
            doc_type=status.doc_type,
            doc_type_label=doc_type_label,
            state=status.state,
            state_label=state_label,
            next_state=status.next_state,
            previous_state=status.previous_state,
            history=status.history,
            current_risk_summary=status.current_risk_summary,
            lawyer_notes=status.lawyer_notes,
            actor=status.actor,
            has_signature=status.has_signature,
            signature_signed_at=status.signature_signed_at,
            created_at=status.created_at,
            updated_at=status.updated_at,
            transitionable_targets=status.transitionable_targets,
        )


@router.patch("/{doc_id}/state", response_model=DocWorkflowStateResponse)
async def patch_doc_workflow_state(doc_id: str, req: DocWorkflowTransitionRequest):
    """状态转换 (PATCH)
    
    5 状态转换通过 target_state 或 transition_back 控制:
    - target_state="ai_reviewed" / "lawyer_reviewed" / "client_signed" / "archived"
      → 前向转换到指定状态 (必须合法路径)
    - transition_back=True → 回退到上一状态 (返工)
    
    Args:
        doc_id: 文书 ID
        req:    转换请求
    
    Returns:
        DocWorkflowStateResponse (更新后状态)
    
    Errors:
        400: target_state 非法 / doc_type 不支持
        404: doc_id 不存在 (新建时不抛 404)
        409: 状态机冲突 (非法转换)
    """
    # 校验 target_state / transition_back 必须二选一
    if req.target_state is None and not req.transition_back:
        raise HTTPException(
            400,
            "必须指定 target_state (前向) 或 transition_back=True (回退)"
        )
    if req.target_state is not None and req.transition_back:
        raise HTTPException(
            400,
            "target_state 和 transition_back 互斥, 不能同时指定"
        )

    async with Database.session() as session:
        try:
            if req.transition_back:
                status = await transition_back(
                    session, doc_id=doc_id,
                    actor=req.actor, reason=req.reason,
                )
            elif req.target_state == DocState.AI_REVIEWED.value:
                status = await transition_to_ai_reviewed(
                    session, doc_id=doc_id,
                    case_id=req.case_id,
                    doc_type=req.doc_type or "",
                    actor=req.actor, reason=req.reason,
                    risk_summary=req.risk_summary,
                )
            elif req.target_state == DocState.LAWYER_REVIEWED.value:
                status = await transition_to_lawyer_reviewed(
                    session, doc_id=doc_id,
                    actor=req.actor, reason=req.reason,
                    lawyer_notes=req.lawyer_notes,
                )
            elif req.target_state == DocState.CLIENT_SIGNED.value:
                status = await transition_to_client_signed(
                    session, doc_id=doc_id,
                    actor=req.actor, reason=req.reason,
                )
            elif req.target_state == DocState.ARCHIVED.value:
                status = await transition_to_archived(
                    session, doc_id=doc_id,
                    actor=req.actor, reason=req.reason,
                )
            else:
                raise HTTPException(400, f"不支持的 target_state: {req.target_state}")
        except StateTransitionError as e:
            raise HTTPException(409, f"状态转换失败: {e.message} (code={e.code})")
        except ValueError as e:
            raise HTTPException(400, str(e))

        # 提交
        await session.commit()

        doc_type_label = SKILL2_DOC_TYPE_LABELS.get(status.doc_type)
        state_label = STATE_LABELS.get(status.state, status.state)

        return DocWorkflowStateResponse(
            doc_id=status.doc_id,
            case_id=status.case_id,
            doc_type=status.doc_type,
            doc_type_label=doc_type_label,
            state=status.state,
            state_label=state_label,
            next_state=status.next_state,
            previous_state=status.previous_state,
            history=status.history,
            current_risk_summary=status.current_risk_summary,
            lawyer_notes=status.lawyer_notes,
            actor=status.actor,
            has_signature=status.has_signature,
            signature_signed_at=status.signature_signed_at,
            created_at=status.created_at,
            updated_at=status.updated_at,
            transitionable_targets=status.transitionable_targets,
        )


@router.post("/{doc_id}/risk-annotation", response_model=RiskAnnotationResponse)
async def post_risk_annotation(doc_id: str, req: RiskAnnotationRequest):
    """4 文书风险维度标注 (Skill 2 扩展)
    
    调用 skills.contract_review.reviewer.annotate_doc_risk_dimensions
    对 4 文书类型之一进行风险维度扫描, 输出 per-dimension 风险等级 + 命中关键词。
    
    Args:
        doc_id: 文书 ID (URL path, 必须与 body.doc_id 一致)
        req:    RiskAnnotationRequest
    
    Returns:
        RiskAnnotationResponse
    """
    if doc_id != req.doc_id:
        raise HTTPException(400, f"URL doc_id ({doc_id}) 与 body.doc_id ({req.doc_id}) 不一致")

    try:
        result = annotate_doc_risk_dimensions(
            doc_id=req.doc_id,
            doc_type=req.doc_type,
            doc_markdown=req.doc_markdown,
            case_id=req.case_id,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    return RiskAnnotationResponse(
        doc_id=result.doc_id,
        case_id=req.case_id,
        doc_type=result.doc_type,
        doc_type_label=result.doc_type_label,
        dimensions=[
            DimensionAnnotationOut(
                dimension=d.dimension,
                risk_level=d.risk_level,
                matched_keywords=d.matched_keywords,
                description=d.description,
                matched_count=d.matched_count,
            )
            for d in result.dimensions
        ],
        fatal_count=result.fatal_count,
        major_count=result.major_count,
        advisory_count=result.advisory_count,
        ok_count=result.ok_count,
        overall_risk_level=result.overall_risk_level,
        disclaimer=result.disclaimer,
        latency_ms=result.latency_ms,
    )


# ===== Helper =====

def _serialize_state(record) -> Dict[str, Any]:
    """DocReviewState ORM → dict"""
    return {
        "doc_id": record.doc_id,
        "case_id": record.case_id,
        "doc_type": record.doc_type,
        "doc_type_label": SKILL2_DOC_TYPE_LABELS.get(record.doc_type),
        "state": record.state,
        "state_label": STATE_LABELS.get(record.state, record.state),
        "actor": record.actor,
        "current_risk_summary": record.current_risk_summary,
        "lawyer_notes": record.lawyer_notes,
        "history_count": len(record.history or []),
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }