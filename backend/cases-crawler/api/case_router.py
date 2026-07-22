"""
LexPrime 案件管理 API (FastAPI)
2026-07-03

端点:
- POST /api/cases/{case_id}/status      变更案件状态
- GET  /api/cases/{case_id}/timeline    获取案件时间线
- POST /api/cases/{case_id}/note        添加案件备注

案件状态流转:
待处理 → 审查中 → 匹配中 → 进行中 → 结案 → 归档
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Index, select

from core.db import Database
from core.models import Base

router = APIRouter(prefix="/api/cases", tags=["cases"])

CASE_STATUSES = [
    "pending",
    "reviewing",
    "matching",
    "in_progress",
    "closed",
    "archived",
]

STATUS_FLOW = {
    "pending": ["reviewing"],
    "reviewing": ["matching", "pending"],
    "matching": ["in_progress", "reviewing"],
    "in_progress": ["closed", "matching"],
    "closed": ["archived", "in_progress"],
    "archived": [],
}


class CaseStatusChange(Base):
    __tablename__ = "case_status_changes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, nullable=False, index=True)
    from_status = Column(String(32), nullable=True)
    to_status = Column(String(32), nullable=False, index=True)
    actor_type = Column(String(16), default="system", nullable=False)
    actor_id = Column(Integer, nullable=True)
    actor_name = Column(String(64), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_case_status_case_id", "case_id"),
        Index("idx_case_status_created", "created_at"),
    )


class CaseNote(Base):
    __tablename__ = "case_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=False)
    actor_id = Column(Integer, nullable=True)
    actor_name = Column(String(64), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_case_notes_case_id", "case_id"),
    )


class StatusChangeRequest(BaseModel):
    to_status: str = Field(..., description="目标状态")
    reason: Optional[str] = Field(None, description="变更原因")
    actor_name: Optional[str] = Field(None, description="操作人名称")

    @field_validator("to_status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        v = v.strip()
        if v not in CASE_STATUSES:
            raise ValueError(f"to_status 必须是 {CASE_STATUSES} 之一")
        return v


class StatusChangeResponse(BaseModel):
    case_id: int
    from_status: Optional[str]
    to_status: str
    reason: Optional[str]
    created_at: str


class TimelineEntry(BaseModel):
    id: int
    type: str
    title: str
    description: Optional[str]
    actor_name: Optional[str]
    created_at: str


class TimelineResponse(BaseModel):
    case_id: int
    timeline: List[TimelineEntry]


class AddNoteRequest(BaseModel):
    content: str = Field(..., description="备注内容")
    actor_name: Optional[str] = Field(None, description="操作人名称")


class AddNoteResponse(BaseModel):
    id: int
    case_id: int
    content: str
    created_at: str


async def _get_current_case_status(case_id: int) -> Optional[str]:
    async with Database.session() as session:
        stmt = select(CaseStatusChange) \
            .where(CaseStatusChange.case_id == case_id) \
            .order_by(CaseStatusChange.created_at.desc()) \
            .limit(1)
        result = await session.execute(stmt)
        change = result.scalar_one_or_none()
        return change.to_status if change else None


@router.post("/{case_id}/status", response_model=StatusChangeResponse)
async def change_case_status(case_id: int, req: StatusChangeRequest):
    """变更案件状态"""
    current_status = await _get_current_case_status(case_id)

    if current_status:
        allowed_transitions = STATUS_FLOW.get(current_status, [])
        if req.to_status not in allowed_transitions:
            raise HTTPException(
                400,
                f"状态流转不允许: {current_status} -> {req.to_status}, "
                f"允许的流转: {allowed_transitions}",
            )
    else:
        if req.to_status != "pending":
            raise HTTPException(
                400,
                f"新建案件必须从 pending 开始",
            )

    async with Database.session() as session:
        change = CaseStatusChange(
            case_id=case_id,
            from_status=current_status,
            to_status=req.to_status,
            reason=req.reason,
            actor_name=req.actor_name,
            created_at=datetime.now(timezone.utc),
        )
        session.add(change)
        await session.flush()

    logger.info(
        f"[case.status] case_id={case_id} "
        f"{current_status} -> {req.to_status} "
        f"reason={req.reason}"
    )

    return StatusChangeResponse(
        case_id=case_id,
        from_status=current_status,
        to_status=req.to_status,
        reason=req.reason,
        created_at=change.created_at.isoformat(),
    )


@router.get("/{case_id}/timeline", response_model=TimelineResponse)
async def get_case_timeline(case_id: int):
    """获取案件时间线"""
    async with Database.session() as session:
        status_stmt = select(CaseStatusChange) \
            .where(CaseStatusChange.case_id == case_id) \
            .order_by(CaseStatusChange.created_at.asc())
        status_result = await session.execute(status_stmt)
        status_changes = status_result.scalars().all()

        note_stmt = select(CaseNote) \
            .where(CaseNote.case_id == case_id) \
            .order_by(CaseNote.created_at.asc())
        note_result = await session.execute(note_stmt)
        notes = note_result.scalars().all()

    events = []

    for change in status_changes:
        events.append(TimelineEntry(
            id=change.id,
            type="status",
            title=f"状态变更: {change.from_status or '新建'} -> {change.to_status}",
            description=change.reason,
            actor_name=change.actor_name,
            created_at=change.created_at.isoformat(),
        ))

    for note in notes:
        events.append(TimelineEntry(
            id=note.id,
            type="note",
            title="添加备注",
            description=note.content,
            actor_name=note.actor_name,
            created_at=note.created_at.isoformat(),
        ))

    events.sort(key=lambda x: x.created_at)

    return TimelineResponse(
        case_id=case_id,
        timeline=events,
    )


@router.post("/{case_id}/note", response_model=AddNoteResponse)
async def add_case_note(case_id: int, req: AddNoteRequest):
    """添加案件备注"""
    if not req.content.strip():
        raise HTTPException(400, "备注内容不能为空")

    async with Database.session() as session:
        note = CaseNote(
            case_id=case_id,
            content=req.content,
            actor_name=req.actor_name,
            created_at=datetime.now(timezone.utc),
        )
        session.add(note)
        await session.flush()

    logger.info(f"[case.note] case_id={case_id} added note")

    return AddNoteResponse(
        id=note.id,
        case_id=case_id,
        content=req.content,
        created_at=note.created_at.isoformat(),
    )


@router.get("/{case_id}/status")
async def get_case_status(case_id: int):
    """获取案件当前状态"""
    status = await _get_current_case_status(case_id)

    return {
        "case_id": case_id,
        "current_status": status or "pending",
        "allowed_transitions": STATUS_FLOW.get(status, []),
    }