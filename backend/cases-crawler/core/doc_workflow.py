"""
LexPrime W12 A2 双审工作流状态机 (lex-coder · 2026-06-30)

承接 W9 C1 Skill 3 文书生成 (4 端点) + W10 A1 一体化流水线 + W3 Skill 2 reviewer
实现 5 状态双审状态机: draft → ai_reviewed → lawyer_reviewed → client_signed → archived

设计:
- 状态机是核心, API 层只是 thin wrapper
- 状态转换需要 actor + reason (审计追溯)
- 历史记录 JSON 数组, 每条 {from, to, actor, reason, ts}
- transition_back 支持任意状态回退一格 (律师返工)
- ORM 模型 DocReviewState (SQLite / PostgreSQL 通用, Integer PK)
- ORM 模型 Signature (客户签字, 大字段 base64)
- 强制 disclaimer (AI 辅助声明)

依赖:
- SQLAlchemy 2.0 (ORM)
- core.db (Database 全局 session)
- core.models (Base)
- skills.contract_review.reviewer (风险标注, 4 文书类型)
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Integer, String, Text, DateTime, JSON,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from loguru import logger

# 复用 core.models 的 Base (避免重复 DeclarativeBase)
from core.models import Base


# ===== 状态枚举 =====

class DocState(str, Enum):
    """双审工作流 5 状态枚举 (按 PRD § 11 法务自检)"""
    DRAFT = "draft"                   # 律师起草中 (Skill 3 生成后)
    AI_REVIEWED = "ai_reviewed"       # AI 风险标注完成 (Skill 2 reviewer)
    LAWYER_REVIEWED = "lawyer_reviewed"  # 律师审核通过 (含修改)
    CLIENT_SIGNED = "client_signed"   # 客户签字确认 (含律师执业证号)
    ARCHIVED = "archived"             # 归档 (法律留痕)


# ===== 状态转换图 (合法转换) =====
# 前向: draft → ai_reviewed → lawyer_reviewed → client_signed → archived
# 后向: 任意状态可回退一格 (transition_back) 用于返工

VALID_TRANSITIONS: Dict[str, List[str]] = {
    DocState.DRAFT.value:          [DocState.AI_REVIEWED.value],
    DocState.AI_REVIEWED.value:    [DocState.LAWYER_REVIEWED.value],
    DocState.LAWYER_REVIEWED.value:[DocState.CLIENT_SIGNED.value],
    DocState.CLIENT_SIGNED.value:  [DocState.ARCHIVED.value],
    DocState.ARCHIVED.value:       [],  # 终态, 不可再转换
}


def get_next_state(current: str) -> Optional[str]:
    """给定当前状态, 返回下一个合法状态 (前向)"""
    nexts = VALID_TRANSITIONS.get(current, [])
    return nexts[0] if nexts else None


def get_previous_state(current: str) -> Optional[str]:
    """给定当前状态, 返回上一状态 (语义信息, transition_back 仍走专用 guard)
    
    按前向链倒序推导:
    archived ← client_signed ← lawyer_reviewed ← ai_reviewed ← draft
    
    终态 archived 仍返回 client_signed (语义上确实从 client_signed 来),
    但 transition_back 函数会单独 guard archived (不允许回退)。
    
    初态 draft 返回 None (没有上一状态)。
    """
    if current == DocState.DRAFT.value:
        return None

    for prev, nexts in VALID_TRANSITIONS.items():
        if current in nexts:
            return prev
    return None


def can_transition(current: str, target: str) -> bool:
    """检查转换是否合法
    
    archived 不可作为 source (终态, 即使 get_previous_state 返 client_signed)
    """
    if current == DocState.ARCHIVED.value:
        # archived 是终态, 不可再转换 (包括 transition_back)
        return False
    nexts = VALID_TRANSITIONS.get(current, [])
    if target in nexts:
        return True
    # transition_back 允许 (除 ARCHIVED 外, 任意状态可回退一格)
    if get_previous_state(current) == target:
        return True
    return False


# ===== 状态转换异常 =====

class StateTransitionError(Exception):
    """状态转换异常 (非法转换 / 文档不存在 / 状态机冲突)"""
    def __init__(self, code: str, message: str, current: Optional[str] = None,
                 target: Optional[str] = None):
        self.code = code
        self.message = message
        self.current = current
        self.target = target
        super().__init__(message)


# ===== ORM 模型 =====

class DocReviewState(Base):
    """双审工作流状态表 (每份文书一条)
    
    Fields:
        id              PK (autoincrement)
        doc_id          文书 ID (与 Skill 3 gen_id 关联, 例如 dg-abc123)
        case_id         案号 (与 Skill 1+2 case_id 关联)
        doc_type        4 文书类型 (complaint/defense/contract/letter)
        state           当前状态 (5 状态枚举)
        history         状态转换历史 (JSON 数组)
        current_risk_summary  AI 风险标注 (JSON, {fatal/major/advisory/ok_count})
        lawyer_notes    律师审核备注 (TEXT)
        actor           当前操作人 (律师 ID)
        created_at      创建时间
        updated_at      更新时间
    """
    __tablename__ = "doc_review_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    case_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    doc_type: Mapped[str] = mapped_column(String(32), index=True)
    state: Mapped[str] = mapped_column(String(32), default=DocState.DRAFT.value, index=True)
    history: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    current_risk_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)
    lawyer_notes: Mapped[Optional[str]] = mapped_column(Text)
    actor: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                  onupdate=func.now())


class Signature(Base):
    """客户签字表 (每份文书一条, 与 DocReviewState.doc_id 关联)
    
    Fields:
        id              PK (autoincrement)
        doc_id          文书 ID (unique, 一份文书只允许一次签字)
        signature_image Base64 编码的图片 (PNG/JPEG, ≤ 500KB)
        license_no      律师执业证号 (审计追溯)
        signed_at       签字时间
        client_name     客户姓名 (可选, 前端填写)
        client_id_no    客户身份证号 / 护照号 (可选, 可加密)
        notes           备注 (TEXT)
        created_at      创建时间
    """
    __tablename__ = "signatures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    signature_image: Mapped[str] = mapped_column(Text)  # Base64, 大字段
    license_no: Mapped[str] = mapped_column(String(64), index=True)
    signed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    client_name: Mapped[Optional[str]] = mapped_column(String(128))
    client_id_no: Mapped[Optional[str]] = mapped_column(String(64))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ===== 数据传输对象 =====

@dataclass
class StateTransitionRecord:
    """单次状态转换记录 (写入 history JSON)"""
    from_state: str
    to_state: str
    actor: str
    reason: str
    ts: str  # ISO 8601 UTC

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DocWorkflowStatus:
    """工作流状态响应 (DTO)"""
    doc_id: str
    case_id: Optional[str]
    doc_type: str
    state: str
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
    transitionable_targets: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ===== 核心: 5 状态转换函数 =====

async def transition_to_ai_reviewed(session, doc_id: str, case_id: Optional[str],
                                      doc_type: str, actor: str, reason: str,
                                      risk_summary: Optional[Dict[str, Any]] = None) -> DocWorkflowStatus:
    """状态转换 1: draft → ai_reviewed (AI 风险标注完成)
    
    Args:
        session:  AsyncSession
        doc_id:   文书 ID (与 Skill 3 gen_id 关联)
        case_id:  案号
        doc_type: 4 文书类型
        actor:    操作人 (律师 ID)
        reason:   转换原因 (审计追溯)
        risk_summary: AI 风险标注 (来自 Skill 2 reviewer, 可选)
    
    Returns:
        DocWorkflowStatus
    """
    return await _do_transition(
        session, doc_id, case_id, doc_type, actor, reason,
        target=DocState.AI_REVIEWED.value,
        risk_summary=risk_summary,
    )


async def transition_to_lawyer_reviewed(session, doc_id: str, actor: str,
                                          reason: str, lawyer_notes: Optional[str] = None) -> DocWorkflowStatus:
    """状态转换 2: ai_reviewed → lawyer_reviewed (律师审核通过)
    
    Args:
        lawyer_notes: 律师审核备注 (可选)
    """
    return await _do_transition(
        session, doc_id, None, None, actor, reason,
        target=DocState.LAWYER_REVIEWED.value,
        lawyer_notes=lawyer_notes,
    )


async def transition_to_client_signed(session, doc_id: str, actor: str,
                                        reason: str) -> DocWorkflowStatus:
    """状态转换 3: lawyer_reviewed → client_signed (客户签字)
    
    注意: 必须先通过 signature_router POST 写入签字记录,
    这里只负责状态推进. 调用方应在签名提交后调用此函数.
    """
    return await _do_transition(
        session, doc_id, None, None, actor, reason,
        target=DocState.CLIENT_SIGNED.value,
    )


async def transition_to_archived(session, doc_id: str, actor: str,
                                   reason: str) -> DocWorkflowStatus:
    """状态转换 4: client_signed → archived (归档, 法律留痕)"""
    return await _do_transition(
        session, doc_id, None, None, actor, reason,
        target=DocState.ARCHIVED.value,
    )


async def transition_back(session, doc_id: str, actor: str, reason: str) -> DocWorkflowStatus:
    """状态转换 5: 任意状态 → 上一状态 (返工)
    
    例外:
    - archived → 不可回退 (终态, 错误码 no_previous_state)
    - draft → 不可回退 (初态, 错误码 no_previous_state)
    """
    # 先查 current state, 给 archived/draft 提供更明确的错误信息
    from sqlalchemy import select
    stmt = select(DocReviewState).where(DocReviewState.doc_id == doc_id)
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()
    if record is not None and record.state == DocState.ARCHIVED.value:
        raise StateTransitionError(
            "no_previous_state",
            "当前状态 archived 是终态, 不可回退",
            current=record.state,
        )

    return await _do_transition(
        session, doc_id, None, None, actor, reason,
        target=None,  # 让 _do_transition 计算上一状态
        allow_back=True,
    )


# ===== 内部: 通用转换函数 =====

async def _do_transition(session, doc_id: str, case_id: Optional[str],
                          doc_type: Optional[str], actor: str, reason: str,
                          target: Optional[str] = None,
                          allow_back: bool = False,
                          risk_summary: Optional[Dict[str, Any]] = None,
                          lawyer_notes: Optional[str] = None) -> DocWorkflowStatus:
    """通用状态转换核心逻辑
    
    1. 查询或新建 DocReviewState (如果不存在, 默认为 draft)
    2. 验证转换合法性
    3. 计算目标状态 (target 或回退到上一格)
    4. 写入 history JSON
    5. 更新 state + updated_at
    6. 返回 DocWorkflowStatus
    """
    from sqlalchemy import select

    # 1. 查询现有记录
    stmt = select(DocReviewState).where(DocReviewState.doc_id == doc_id)
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()

    # 计算当前 effective state (新建时默认 draft, 用于前置校验)
    effective_current = record.state if record is not None else DocState.DRAFT.value

    # 2. 计算目标状态
    if target is None and allow_back:
        target = get_previous_state(effective_current)
        if target is None:
            raise StateTransitionError(
                "no_previous_state",
                f"当前状态 {effective_current} 没有可回退的上一状态 (draft 是初态, archived 是终态)",
                current=effective_current,
            )

    if target is None:
        raise StateTransitionError(
            "missing_target",
            "必须指定目标状态 target 或 allow_back=True",
        )

    # 3. 验证转换合法性 (用 effective state 校验, 防止 doc 不存在时非法转换)
    if not can_transition(effective_current, target):
        valid_nexts = VALID_TRANSITIONS.get(effective_current, [])
        prev = get_previous_state(effective_current)
        valid = valid_nexts + ([prev] if prev else [])
        raise StateTransitionError(
            "invalid_transition",
            f"不能从 {effective_current} 转换到 {target} (合法目标: {valid})",
            current=effective_current,
            target=target,
        )

    # 4. 校验通过后再新建 (如需要)
    if record is None:
        if not doc_type:
            raise StateTransitionError(
                "missing_doc_type",
                "新建 doc 状态记录时必须提供 doc_type (首次转换需要)",
            )
        record = DocReviewState(
            doc_id=doc_id,
            case_id=case_id,
            doc_type=doc_type,
            state=DocState.DRAFT.value,
            history=[],
            actor=actor,
        )
        session.add(record)
        await session.flush()
        logger.info(f"[doc-workflow] 新建 doc_id={doc_id} doc_type={doc_type}")

    # 4. 写入 history
    transition = StateTransitionRecord(
        from_state=record.state,
        to_state=target,
        actor=actor,
        reason=reason,
        ts=datetime.now(timezone.utc).isoformat(),
    )

    if record.history is None:
        record.history = []
    record.history = record.history + [transition.to_dict()]

    # 5. 更新字段
    record.state = target
    record.actor = actor
    if risk_summary is not None:
        record.current_risk_summary = risk_summary
    if lawyer_notes is not None:
        existing = record.lawyer_notes or ""
        record.lawyer_notes = (existing + "\n" + lawyer_notes).strip() if existing else lawyer_notes

    # 6. 提交
    await session.flush()
    await session.refresh(record)

    logger.info(
        f"[doc-workflow] doc_id={doc_id} {transition.from_state} → {transition.to_state} "
        f"actor={actor} reason={reason[:50]}"
    )

    # 7. 检查是否有签字记录
    sig_stmt = select(Signature).where(Signature.doc_id == doc_id)
    sig_result = await session.execute(sig_stmt)
    sig = sig_result.scalar_one_or_none()

    return DocWorkflowStatus(
        doc_id=record.doc_id,
        case_id=record.case_id,
        doc_type=record.doc_type,
        state=record.state,
        next_state=get_next_state(record.state),
        previous_state=get_previous_state(record.state),
        history=record.history or [],
        current_risk_summary=record.current_risk_summary,
        lawyer_notes=record.lawyer_notes,
        actor=record.actor,
        has_signature=sig is not None,
        signature_signed_at=sig.signed_at.isoformat() if sig else None,
        created_at=record.created_at.isoformat() if record.created_at else None,
        updated_at=record.updated_at.isoformat() if record.updated_at else None,
        transitionable_targets=_get_transitionable_targets(record.state),
    )


def _get_transitionable_targets(current: str) -> List[str]:
    """计算当前状态的所有合法目标 (含回退)"""
    targets: List[str] = []
    for t in VALID_TRANSITIONS.get(current, []):
        if t not in targets:
            targets.append(t)
    prev = get_previous_state(current)
    if prev and prev not in targets:
        targets.append(prev)
    return targets


# ===== 查询函数 =====

async def get_workflow_status(session, doc_id: str) -> Optional[DocWorkflowStatus]:
    """查询工作流状态 (含签字状态)
    
    Returns:
        DocWorkflowStatus 或 None (doc_id 不存在)
    """
    from sqlalchemy import select

    stmt = select(DocReviewState).where(DocReviewState.doc_id == doc_id)
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()
    if record is None:
        return None

    sig_stmt = select(Signature).where(Signature.doc_id == doc_id)
    sig_result = await session.execute(sig_stmt)
    sig = sig_result.scalar_one_or_none()

    return DocWorkflowStatus(
        doc_id=record.doc_id,
        case_id=record.case_id,
        doc_type=record.doc_type,
        state=record.state,
        next_state=get_next_state(record.state),
        previous_state=get_previous_state(record.state),
        history=record.history or [],
        current_risk_summary=record.current_risk_summary,
        lawyer_notes=record.lawyer_notes,
        actor=record.actor,
        has_signature=sig is not None,
        signature_signed_at=sig.signed_at.isoformat() if sig else None,
        created_at=record.created_at.isoformat() if record.created_at else None,
        updated_at=record.updated_at.isoformat() if record.updated_at else None,
        transitionable_targets=_get_transitionable_targets(record.state),
    )


async def list_workflow_by_state(session, state: str,
                                   limit: int = 100, offset: int = 0) -> List[DocReviewState]:
    """按状态查询工作流列表 (前端看板用)
    
    Args:
        state: 5 状态之一
        limit: 最多返回条数
        offset: 偏移
    """
    from sqlalchemy import select

    if state not in VALID_TRANSITIONS and state != DocState.DRAFT.value:
        # 仍允许 query, 但 log 警告
        logger.warning(f"[doc-workflow] list_workflow_by_state 未知状态: {state}")

    stmt = (
        select(DocReviewState)
        .where(DocReviewState.state == state)
        .order_by(DocReviewState.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


# ===== 强制 AI 辅助声明 =====

DOC_WORKFLOW_DISCLAIMER = (
    "本双审工作流基于 LexPrime 元枢法智 (W12 A2) 自动驱动, "
    "AI 风险标注仅供参考与辅助律师审核使用, 不构成正式法律意见, "
    "律师应根据案件实际情况进行审核、修改和完善, 最终以律师签字确认为准。"
)