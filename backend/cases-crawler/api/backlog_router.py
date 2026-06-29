"""
LexPrime W8 PRD Backlog Ticket Router (lex-coder · 2026-06-29)

A2 任务: 把 W7 review_questions (commit 651e3d6) 现场问题自动转 PRD backlog ticket,
给 W8+ plan engine 自动调度, 律师每个问题自动转成 backlog ticket.

端点 (4 个):
- POST /api/backlog/from-question         review_question_id → backlog ticket
                                            (单条转换, 律师现场提问后即转)
- GET  /api/backlog/list                  列表 (按 status / priority / owner / category 过滤)
- POST /api/backlog/{id}/assign           owner 分配 (改写 owner 字段)
- GET  /api/backlog/board                 W8 backlog 总览看板 (5 视图汇总)

数据模型 (新增 prd_backlog 表):
- id                  INTEGER PK autoincrement
- source_question_id  INTEGER (W7 review_questions.id, nullable - 律师手动提交可无)
- source_lawyer_id    TEXT (L1-L5, nullable)
- title               TEXT (≤ 120 字, 必填)
- description         TEXT (≤ 1000 字, 必填, 含律师原话)
- category            TEXT (产品 / 技术 / 法务 / 其他, 复用 W7 review_categories)
- priority            TEXT (P0 / P1 / P2 / P3)
- owner               TEXT (lex-pm / lex-coder / lex-ai / lex-design / unassigned)
- status              TEXT (open / in_progress / done / deferred / wontfix)
- created_at          DATETIME 服务端 UTC
- updated_at          DATETIME 服务端 UTC, onupdate

字段语义:
- source_question_id: 关联 W7 review_questions 表 (律师原话的问题源头)
- source_lawyer_id:   关联律师 (L1-L5), 即便没有 source_question_id 也可手动填
- title:              ticket 标题 (短摘要)
- description:        ticket 详情 (律师原始语言 + A1 PM 归并后的归并原因)
- category:           复用 W7 QUESTION_CATEGORIES (产品/技术/法务/其他)
- priority:           P0/P1/P2/P3 (P3=锦上添花给 plan engine 优先级排期用)
- owner:              接手团队 (lex-coder/lex-ai/lex-design/lex-pm/unassigned)
- status:             open / in_progress / done / deferred / wontfix

W8 plan 接力 (plan_5dcb8424):
- A1 prd-feedback-action → 提供 w8-review-questions-summary.md 42 项独立问题
- A2 本任务 → 把 42 项 + 评审 #1 #2 真实问题 → prd_backlog 表, 给 W8+ plan engine 调度
- W8 末 (08-09) → review_data_v1_0.md + backlog 总览输出

与 W7 review_questions 表的关系:
- W7 review_questions: 律师现场原始问题 (1 条记录)
- W8 prd_backlog:       PM 归并后 + 排期 ticket (1 条 / 多条问题归并 → 1 ticket)
- 关系: source_question_id → review_questions.id (多对 1, 多个原始问题归并为 1 ticket)
- 兼容: 律师手动直接提交 ticket (无需先 review_question)
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    select,
)

from core.db import Database
from core.models import Base  # noqa: F402  # SQLAlchemy 2.0 declarative base


router = APIRouter(prefix="/api/backlog", tags=["backlog:prd-tickets"])


# ====== ORM Model: prd_backlog ======
class PrdBacklog(Base):
    """W8 PRD backlog ticket 表 (评审问题归并 + plan engine 调度)

    Schema:
        id                  INTEGER PK
        source_question_id  INTEGER (W7 review_questions.id, nullable)
        source_lawyer_id    TEXT (L1-L5, nullable)
        title               TEXT (≤ 120 字)
        description         TEXT (≤ 1000 字, 律师原话 + 归并原因)
        category            TEXT (产品/技术/法务/其他)
        priority            TEXT (P0/P1/P2/P3)
        owner               TEXT (lex-pm/lex-coder/lex-ai/lex-design/unassigned)
        status              TEXT (open/in_progress/done/deferred/wontfix)
        created_at          DATETIME 服务端 UTC
        updated_at          DATETIME 服务端 UTC, onupdate

    Indexes:
        - ix_backlog_status (status)
        - ix_backlog_priority (priority)
        - ix_backlog_owner_status (owner, status)
        - ix_backlog_category_priority (category, priority)

    Constraints:
        - uq_backlog_source_question: (source_question_id) UNIQUE
          防重复从同一 review_question 转 backlog (幂等)

    Notes:
        source_question_id 用 SQLAlchemy Integer (避免 BigInt SQLite 不兼容, 跟 W8 auth_* 4 表一致)
    """
    __tablename__ = "prd_backlog"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_question_id = Column(Integer, nullable=True, index=True)
    source_lawyer_id = Column(String(16), nullable=True, index=True)
    title = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(16), nullable=False, index=True)
    priority = Column(String(4), nullable=False, index=True)
    owner = Column(String(16), nullable=False, default="unassigned", index=True)
    status = Column(String(16), nullable=False, default="open", index=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=None,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=None,
    )

    __table_args__ = (
        UniqueConstraint(
            "source_question_id", name="uq_backlog_source_question",
        ),
        Index("ix_backlog_owner_status", "owner", "status"),
        Index("ix_backlog_category_priority", "category", "priority"),
    )


# ====== 常量 (跟 W7 review_router 对齐) ======
# 复用 W7 QUESTION_CATEGORIES (产品/技术/法务/其他)
QUESTION_CATEGORIES = ["产品", "技术", "法务", "其他"]

# P0/P1/P2/P3 四档优先级 (P3 = 锦上添花, 排期备用)
BACKLOG_PRIORITIES = ["P0", "P1", "P2", "P3"]

# ticket 状态: open (新建) / in_progress (实施中) / done (完成) / deferred (推迟) / wontfix (不做)
BACKLOG_STATUSES = ["open", "in_progress", "done", "deferred", "wontfix"]

# owner 取值: lex-pm / lex-coder / lex-ai / lex-design / unassigned
BACKLOG_OWNERS = [
    "lex-pm",
    "lex-coder",
    "lex-ai",
    "lex-design",
    "lex-data",
    "unassigned",
]

# 律师编号白名单 (复用 W7)
LAWYER_IDS = ["L1", "L2", "L3", "L4", "L5"]


# ====== Pydantic Models ======
class CreateFromQuestionRequest(BaseModel):
    """从 review_question 创建 backlog ticket 请求

    字段:
        review_question_id  源问题 ID (W7 review_questions.id)
        priority            P0/P1/P2/P3 (默认 = 从 review_question.category 推断, 也可手动覆盖)
        owner               分配给哪个 agent (默认 unassigned)
        title               ticket 标题 (默认 = review_question.question_text 前 100 字)
        description         ticket 描述 (默认 = "律师原话: ..." + "分类: ..." + "评审: ...")
    """
    review_question_id: int = Field(..., description="W7 review_questions.id")
    priority: Optional[str] = Field(None, description="P0/P1/P2/P3 (默认从律师原话推断)")
    owner: Optional[str] = Field("unassigned", description="分配 owner")
    title: Optional[str] = Field(None, max_length=120, description="ticket 标题 (默认 = 问题前 100 字)")
    description: Optional[str] = Field(None, max_length=1000, description="ticket 描述")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if v not in BACKLOG_PRIORITIES:
            raise ValueError(f"priority 必须是 {BACKLOG_PRIORITIES} 之一")
        return v

    @field_validator("owner")
    @classmethod
    def validate_owner(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return "unassigned"
        v = v.strip()
        if v not in BACKLOG_OWNERS:
            raise ValueError(f"owner 必须是 {BACKLOG_OWNERS} 之一")
        return v


class CreateFromQuestionResponse(BaseModel):
    """从 question 创建 ticket 响应"""
    backlog_id: int
    source_question_id: int
    title: str
    priority: str
    owner: str
    status: str
    category: str
    created_at: str
    next: str  # "GET /api/backlog/list"


class BacklogEntry(BaseModel):
    """单条 backlog ticket (用于 list / board 响应)"""
    id: int
    source_question_id: Optional[int]
    source_lawyer_id: Optional[str]
    title: str
    description: str
    category: str
    priority: str
    owner: str
    status: str
    created_at: str
    updated_at: str


class BacklogListResponse(BaseModel):
    """列表响应 (按 status / priority / owner / category 过滤)"""
    total: int
    by_status: Dict[str, int]
    by_priority: Dict[str, int]
    by_owner: Dict[str, int]
    by_category: Dict[str, int]
    tickets: List[BacklogEntry]


class AssignRequest(BaseModel):
    """分配 / 更新 ticket 请求

    字段 (所有字段可选, 至少 1 项):
        owner      新 owner
        status     新 status
        priority   新 priority
    """
    owner: Optional[str] = Field(None, description="新 owner")
    status: Optional[str] = Field(None, description="新 status")
    priority: Optional[str] = Field(None, description="新 priority")

    @field_validator("owner")
    @classmethod
    def validate_owner(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if v not in BACKLOG_OWNERS:
            raise ValueError(f"owner 必须是 {BACKLOG_OWNERS} 之一")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if v not in BACKLOG_STATUSES:
            raise ValueError(f"status 必须是 {BACKLOG_STATUSES} 之一")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if v not in BACKLOG_PRIORITIES:
            raise ValueError(f"priority 必须是 {BACKLOG_PRIORITIES} 之一")
        return v


class AssignResponse(BaseModel):
    """分配响应"""
    backlog_id: int
    owner: str
    status: str
    priority: str
    updated_at: str
    changed_fields: List[str]


class BoardOwnerStat(BaseModel):
    """按 owner 看板统计"""
    owner: str
    total: int
    by_status: Dict[str, int]
    by_priority: Dict[str, int]


class BoardCategoryStat(BaseModel):
    """按 category 看板统计"""
    category: str
    total: int
    by_status: Dict[str, int]
    by_priority: Dict[str, int]


class BoardSourceStat(BaseModel):
    """按 source_lawyer_id 看板统计"""
    source_lawyer_id: Optional[str]
    total: int
    by_category: Dict[str, int]


class BoardResponse(BaseModel):
    """W8 backlog 总览看板 - 5 视图汇总

    视图 (5 个):
    1. summary:          总览统计 (总 ticket, open, in_progress, done)
    2. by_status:        按状态分组
    3. by_priority:      按优先级分组 (P0/P1/P2/P3 票数)
    4. by_owner:         按 owner 分组
    5. by_source_lawyer: 按反馈律师 L1-L5 分组 (按来源问题)
    """
    summary: Dict[str, Any]
    by_status: Dict[str, int]
    by_priority: Dict[str, int]
    by_owner: Dict[str, BoardOwnerStat]
    by_category: Dict[str, BoardCategoryStat]
    by_source_lawyer: Dict[str, BoardSourceStat]
    recent_tickets: List[BacklogEntry]
    generated_at: str


# ====== 帮助函数 ======
def _infer_priority_from_question(question_text: str, category: str) -> str:
    """从律师原话推断优先级 (默认规则)

    推断规则:
    1. 包含"急需"/"强烈要求"/"必备"/"P0"/"必须" → P0
    2. 包含"需要"/"建议"/"应该"/"希望加" → P1
    3. 包含"锦上添花"/"未来"/"可选"/"可考虑" → P2
    4. 其他 → 默认 P1
    5. category = 法务 + 包含"漏标"/"应标"  → 升级到 P0 (法务风险)

    实现: 关键词匹配, 不依赖 LLM (W8 dev 简化)
    """
    if not question_text:
        return "P1"

    text_lower = question_text.lower()

    p0_keywords = ["急需", "强烈要求", "必备", "必须", "p0", "应当", "应标", "漏标", "标 major"]
    p2_keywords = ["锦上添花", "未来", "可选", "可考虑", "未来扩展"]
    p1_keywords = ["需要", "建议", "应该", "希望加", "希望", "需要补充"]

    for kw in p0_keywords:
        if kw in text_lower:
            return "P0"
    for kw in p2_keywords:
        if kw in text_lower:
            return "P2"
    for kw in p1_keywords:
        if kw in text_lower:
            return "P1"

    # 法务 category 涉及漏检/漏标 → 升级 P0
    if category == "法务":
        legal_risk = ["漏", "应", "重大风险", "致命", "严禁", "违反"]
        for kw in legal_risk:
            if kw in text_lower:
                return "P0"

    return "P1"


def _infer_owner_from_category(category: str) -> str:
    """从 category 推断 owner (默认分配规则)

    默认:
    - 产品 → lex-pm
    - 技术 → lex-ai
    - 法务 → lex-coder (LexPrime 全栈工程师最熟 PRD 法务细节)
    - 其他 → unassigned
    """
    return {
        "产品": "lex-pm",
        "技术": "lex-ai",
        "法务": "lex-coder",
        "其他": "unassigned",
    }.get(category, "unassigned")


# ====== 端点 1: POST /api/backlog/from-question ======
@router.post("/from-question", response_model=CreateFromQuestionResponse, status_code=201)
async def create_from_question(req: CreateFromQuestionRequest):
    """从 W7 review_question 创建 backlog ticket

    流程:
        1. 查 W7 review_questions 表 (跨 router, 直接读 review_questions 表)
           - 不存在 → 404
        2. 如果已转 backlog (uq_backlog_source_question 冲突) → 409, 返回已存在 ID
        3. 默认字段:
           - title = question_text 前 100 字
           - description = "律师原话: ...\n分类: ...\n评审场景: ..."
           - priority = 从 question_text 推断 (可手动覆盖)
           - owner = unassigned (可手动覆盖)
           - status = open
        4. 写入 prd_backlog 表

    Idempotency:
        - source_question_id UNIQUE 约束 (uq_backlog_source_question)
        - 重复转 → 409 冲突 (跟 W7 review_questions UNIQUE 一致)
    """
    # 跨 router 直接读 review_questions 表 (SQLAlchemy ORM)
    from api.review_router import ReviewQuestion

    async with Database.session() as session:
        # 1. 查 source question
        q_stmt = select(ReviewQuestion).where(ReviewQuestion.id == req.review_question_id)
        q_result = await session.execute(q_stmt)
        source_q = q_result.scalar_one_or_none()
        if source_q is None:
            raise HTTPException(404, f"review_question_id={req.review_question_id} 不存在")

        # 2. 检查是否已转换 (uq_backlog_source_question)
        dup_stmt = select(PrdBacklog).where(PrdBacklog.source_question_id == req.review_question_id)
        dup_result = await session.execute(dup_stmt)
        existing = dup_result.scalar_one_or_none()
        if existing is not None:
            raise HTTPException(
                409,
                f"review_question_id={req.review_question_id} 已转 backlog (id={existing.id}), 不能重复创建",
            )

        # 3. 默认字段推断
        title_default = source_q.question_text[:100] if source_q.question_text else "未命名 ticket"
        desc_default = (
            f"律师原话: {source_q.question_text}\n"
            f"分类: {source_q.category}\n"
            f"律师: {source_q.lawyer_id}\n"
            f"使用场景: {source_q.context or '(无)'}"
        )
        title = req.title or title_default
        description = req.description or desc_default

        # 优先级推断 (未指定时)
        priority = req.priority or _infer_priority_from_question(
            source_q.question_text or "", source_q.category
        )
        owner = req.owner or "unassigned"

        # 4. 写入
        entry = PrdBacklog(
            source_question_id=req.review_question_id,
            source_lawyer_id=source_q.lawyer_id,
            title=title,
            description=description,
            category=source_q.category,
            priority=priority,
            owner=owner,
            status="open",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(entry)
        try:
            await session.flush()
        except Exception as e:
            await session.rollback()
            logger.exception(f"[backlog.from-question] DB error: {e}")
            raise HTTPException(500, f"创建 ticket 失败: {e}")

    logger.info(
        f"[backlog.from-question] qid={req.review_question_id} → bid={entry.id} "
        f"priority={priority} owner={owner} category={source_q.category}"
    )

    return CreateFromQuestionResponse(
        backlog_id=entry.id,
        source_question_id=entry.source_question_id,
        title=entry.title,
        priority=entry.priority,
        owner=entry.owner,
        status=entry.status,
        category=entry.category,
        created_at=entry.created_at.isoformat() if entry.created_at else "",
        next=f"GET /api/backlog/list?priority={priority}",
    )


# ====== 端点 2: GET /api/backlog/list ======
@router.get("/list", response_model=BacklogListResponse)
async def list_backlog(
    status: Optional[str] = Query(None, description="按状态过滤"),
    priority: Optional[str] = Query(None, description="按优先级过滤"),
    owner: Optional[str] = Query(None, description="按 owner 过滤"),
    category: Optional[str] = Query(None, description="按 category 过滤"),
    source_lawyer_id: Optional[str] = Query(None, description="按反馈律师过滤 (L1-L5)"),
):
    """backlog ticket 列表 (支持 4 维组合过滤)

    支持过滤:
        - status         open / in_progress / done / deferred / wontfix
        - priority       P0 / P1 / P2 / P3
        - owner          lex-pm / lex-coder / lex-ai / lex-design / lex-data / unassigned
        - category       产品 / 技术 / 法务 / 其他 (复用 W7 QUESTION_CATEGORIES)
        - source_lawyer_id  L1-L5 (按反馈律师过滤)

    返回:
        - total:           总数
        - by_status:       按 status 计数
        - by_priority:     按 priority 计数
        - by_owner:        按 owner 计数
        - by_category:     按 category 计数
        - tickets:         详情列表 (按 created_at DESC)
    """
    async with Database.session() as session:
        stmt = select(PrdBacklog).order_by(PrdBacklog.created_at.desc())

        if status:
            st = status.strip()
            if st not in BACKLOG_STATUSES:
                raise HTTPException(400, f"status 必须是 {BACKLOG_STATUSES} 之一")
            stmt = stmt.where(PrdBacklog.status == st)
        if priority:
            p = priority.strip()
            if p not in BACKLOG_PRIORITIES:
                raise HTTPException(400, f"priority 必须是 {BACKLOG_PRIORITIES} 之一")
            stmt = stmt.where(PrdBacklog.priority == p)
        if owner:
            o = owner.strip()
            if o not in BACKLOG_OWNERS:
                raise HTTPException(400, f"owner 必须是 {BACKLOG_OWNERS} 之一")
            stmt = stmt.where(PrdBacklog.owner == o)
        if category:
            cat = category.strip()
            if cat not in QUESTION_CATEGORIES:
                raise HTTPException(400, f"category 必须是 {QUESTION_CATEGORIES} 之一")
            stmt = stmt.where(PrdBacklog.category == cat)
        if source_lawyer_id:
            lid = source_lawyer_id.strip()
            # W7 review_router 接受 L1-L5 + L 开头 ≤ 4 字符
            if lid not in LAWYER_IDS and not (lid.startswith("L") and len(lid) <= 4):
                raise HTTPException(400, "source_lawyer_id 必须是 L1-L5 或 L 开头 ≤ 4 字符")
            stmt = stmt.where(PrdBacklog.source_lawyer_id == lid)

        result = await session.execute(stmt)
        rows = result.scalars().all()

    # 4 维计数 (即便被过滤, 也基于已过滤的结果集统计, 跟 W7 questions 一致)
    by_status_count: Dict[str, int] = {s: 0 for s in BACKLOG_STATUSES}
    by_priority_count: Dict[str, int] = {p: 0 for p in BACKLOG_PRIORITIES}
    by_owner_count: Dict[str, int] = {o: 0 for o in BACKLOG_OWNERS}
    by_category_count: Dict[str, int] = {c: 0 for c in QUESTION_CATEGORIES}

    entries: List[BacklogEntry] = []
    for r in rows:
        by_status_count[r.status] = by_status_count.get(r.status, 0) + 1
        by_priority_count[r.priority] = by_priority_count.get(r.priority, 0) + 1
        by_owner_count[r.owner] = by_owner_count.get(r.owner, 0) + 1
        by_category_count[r.category] = by_category_count.get(r.category, 0) + 1
        entries.append(BacklogEntry(
            id=r.id,
            source_question_id=r.source_question_id,
            source_lawyer_id=r.source_lawyer_id,
            title=r.title or "",
            description=r.description or "",
            category=r.category,
            priority=r.priority,
            owner=r.owner,
            status=r.status,
            created_at=r.created_at.isoformat() if r.created_at else "",
            updated_at=r.updated_at.isoformat() if r.updated_at else "",
        ))

    return BacklogListResponse(
        total=len(entries),
        by_status=by_status_count,
        by_priority=by_priority_count,
        by_owner=by_owner_count,
        by_category=by_category_count,
        tickets=entries,
    )


# ====== 端点 3: POST /api/backlog/{id}/assign ======
@router.post("/{backlog_id}/assign", response_model=AssignResponse)
async def assign_backlog(backlog_id: int, req: AssignRequest):
    """分配 / 更新 ticket 字段 (owner / status / priority)

    至少传入 1 个字段 (Pydantic 校验)
    返回:
        - changed_fields: 哪些字段被改了 (用于 UI 显示)
    """
    changed: List[str] = []
    if req.owner is None and req.status is None and req.priority is None:
        raise HTTPException(
            400,
            "至少传入 1 个字段 (owner / status / priority)",
        )

    async with Database.session() as session:
        stmt = select(PrdBacklog).where(PrdBacklog.id == backlog_id)
        result = await session.execute(stmt)
        entry = result.scalar_one_or_none()
        if entry is None:
            raise HTTPException(404, f"backlog_id={backlog_id} 不存在")

        # 增量更新 (只改传入的字段)
        if req.owner is not None and req.owner != entry.owner:
            entry.owner = req.owner
            changed.append("owner")
        if req.status is not None and req.status != entry.status:
            entry.status = req.status
            changed.append("status")
        if req.priority is not None and req.priority != entry.priority:
            entry.priority = req.priority
            changed.append("priority")

        # 强制更新 updated_at (即便字段没改, 也刷新; 跟 W7 my-scores 的 created_at 一致)
        entry.updated_at = datetime.now(timezone.utc)

    logger.info(
        f"[backlog.assign] bid={backlog_id} changed={changed} "
        f"owner={entry.owner} status={entry.status} priority={entry.priority}"
    )

    return AssignResponse(
        backlog_id=entry.id,
        owner=entry.owner,
        status=entry.status,
        priority=entry.priority,
        updated_at=entry.updated_at.isoformat() if entry.updated_at else "",
        changed_fields=changed if changed else ["updated_at (refresh)"],
    )


# ====== 端点 4: GET /api/backlog/board ======
@router.get("/board", response_model=BoardResponse)
async def backlog_board():
    """W8 backlog 总览看板 - 5 视图汇总

    5 视图:
        1. 总览统计 (summary)
        2. 按状态分组 (by_status)
        3. 按优先级分组 (by_priority)
        4. 按 owner 分组 (by_owner)
        5. 按 category + source_lawyer 来源分组 (by_source_lawyer)

    用途:
        - W8 plan engine 自动调度 (P0 自动派单 + AI 自动出 PRD 提案)
        - PM 评审 #2 后 24h 看 board 一屏掌握 42 项问题归属
        - 自动汇总 + 计数跟 W7 board 保持风格一致
    """
    async with Database.session() as session:
        stmt = select(PrdBacklog).order_by(PrdBacklog.created_at.desc())
        result = await session.execute(stmt)
        rows = result.scalars().all()

    if not rows:
        # 空数据兜底
        return BoardResponse(
            summary={
                "total_tickets": 0,
                "open_tickets": 0,
                "in_progress_tickets": 0,
                "done_tickets": 0,
                "p0_tickets": 0,
                "completed_rate": 0.0,
                "min_required_tickets": 0,
                "next_actions": ["W8 评审结束后批量导入 A1 归并的 42 项问题"],
            },
            by_status={s: 0 for s in BACKLOG_STATUSES},
            by_priority={p: 0 for p in BACKLOG_PRIORITIES},
            by_owner={},
            by_category={},
            by_source_lawyer={},
            recent_tickets=[],
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # 1. 基础计数
    total = len(rows)
    status_counts: Dict[str, int] = {s: 0 for s in BACKLOG_STATUSES}
    priority_counts: Dict[str, int] = {p: 0 for p in BACKLOG_PRIORITIES}
    owner_data: Dict[str, Dict[str, Dict[str, int]]] = {
        o: {"by_status": {s: 0 for s in BACKLOG_STATUSES}, "by_priority": {p: 0 for p in BACKLOG_PRIORITIES}}
        for o in BACKLOG_OWNERS
    }
    category_data: Dict[str, Dict[str, Dict[str, int]]] = {
        c: {"by_status": {s: 0 for s in BACKLOG_STATUSES}, "by_priority": {p: 0 for p in BACKLOG_PRIORITIES}}
        for c in QUESTION_CATEGORIES
    }
    source_lawyer_data: Dict[str, Dict[str, int]] = {}

    for r in rows:
        status_counts[r.status] = status_counts.get(r.status, 0) + 1
        priority_counts[r.priority] = priority_counts.get(r.priority, 0) + 1
        owner_data.setdefault(r.owner, {"by_status": {s: 0 for s in BACKLOG_STATUSES}, "by_priority": {p: 0 for p in BACKLOG_PRIORITIES}})
        owner_data[r.owner]["by_status"][r.status] = owner_data[r.owner]["by_status"].get(r.status, 0) + 1
        owner_data[r.owner]["by_priority"][r.priority] = owner_data[r.owner]["by_priority"].get(r.priority, 0) + 1
        category_data.setdefault(r.category, {"by_status": {s: 0 for s in BACKLOG_STATUSES}, "by_priority": {p: 0 for p in BACKLOG_PRIORITIES}})
        category_data[r.category]["by_status"][r.status] = category_data[r.category]["by_status"].get(r.status, 0) + 1
        category_data[r.category]["by_priority"][r.priority] = category_data[r.category]["by_priority"].get(r.priority, 0) + 1
        # source_lawyer (None 时归为 "no_source")
        sl = r.source_lawyer_id or "no_source"
        source_lawyer_data.setdefault(sl, {"total": 0, "by_category": {c: 0 for c in QUESTION_CATEGORIES}})
        source_lawyer_data[sl]["total"] += 1
        source_lawyer_data[sl]["by_category"][r.category] = source_lawyer_data[sl]["by_category"].get(r.category, 0) + 1

    # 2. by_owner (只输出有数据的 owner)
    by_owner: Dict[str, BoardOwnerStat] = {}
    for owner, data in owner_data.items():
        owner_total = sum(data["by_status"].values())
        if owner_total > 0:
            by_owner[owner] = BoardOwnerStat(
                owner=owner,
                total=owner_total,
                by_status=data["by_status"],
                by_priority=data["by_priority"],
            )

    # 3. by_category (只输出有数据的 category)
    by_category: Dict[str, BoardCategoryStat] = {}
    for cat, data in category_data.items():
        cat_total = sum(data["by_status"].values())
        if cat_total > 0:
            by_category[cat] = BoardCategoryStat(
                category=cat,
                total=cat_total,
                by_status=data["by_status"],
                by_priority=data["by_priority"],
            )

    # 4. by_source_lawyer
    by_source_lawyer: Dict[str, BoardSourceStat] = {}
    for lid, data in source_lawyer_data.items():
        sl_id: Optional[str] = None if lid == "no_source" else lid
        by_source_lawyer[lid] = BoardSourceStat(
            source_lawyer_id=sl_id,
            total=data["total"],
            by_category=data["by_category"],
        )

    # 5. recent_tickets (最多 10 条最新)
    recent: List[BacklogEntry] = []
    for r in rows[:10]:
        recent.append(BacklogEntry(
            id=r.id,
            source_question_id=r.source_question_id,
            source_lawyer_id=r.source_lawyer_id,
            title=r.title or "",
            description=r.description or "",
            category=r.category,
            priority=r.priority,
            owner=r.owner,
            status=r.status,
            created_at=r.created_at.isoformat() if r.created_at else "",
            updated_at=r.updated_at.isoformat() if r.updated_at else "",
        ))

    # 6. summary
    done_count = status_counts.get("done", 0)
    completed_rate = round(done_count / max(total, 1), 3)
    p0_count = priority_counts.get("P0", 0)
    summary = {
        "total_tickets": total,
        "open_tickets": status_counts.get("open", 0),
        "in_progress_tickets": status_counts.get("in_progress", 0),
        "done_tickets": done_count,
        "deferred_tickets": status_counts.get("deferred", 0),
        "wontfix_tickets": status_counts.get("wontfix", 0),
        "p0_tickets": p0_count,
        "completed_rate": completed_rate,
        "min_required_tickets": total,
        "next_actions": _build_next_actions(status_counts, priority_counts, by_owner),
    }

    return BoardResponse(
        summary=summary,
        by_status=status_counts,
        by_priority=priority_counts,
        by_owner=by_owner,
        by_category=by_category,
        by_source_lawyer=by_source_lawyer,
        recent_tickets=recent,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def _build_next_actions(
    status_counts: Dict[str, int],
    priority_counts: Dict[str, int],
    by_owner: Dict[str, "BoardOwnerStat"],
) -> List[str]:
    """根据当前 backlog 状态生成 next_actions (中文)"""
    actions: List[str] = []
    p0_count = priority_counts.get("P0", 0)
    open_count = status_counts.get("open", 0)
    deferred_count = status_counts.get("deferred", 0)
    unassigned_total = sum(
        s.by_status.get("open", 0) + s.by_status.get("in_progress", 0)
        for s in by_owner.values() if s.owner == "unassigned"
    )

    if p0_count > 0:
        actions.append(f"P0 tickets {p0_count} 条 → 24h 内分配 owner + 启动实施")
    if open_count > 0:
        actions.append(f"open {open_count} 条 → 启动 triage (PM 24h 内分给 agent)")
    if unassigned_total > 0:
        actions.append(f"unassigned {unassigned_total} 条 → PM 接手分配")
    if deferred_count > 0:
        actions.append(f"deferred {deferred_count} 条 → 1 周后复评")
    if not actions:
        actions.append("backlog 已清空, 下次评审继续收集")
    return actions


# ====== Health ======
@router.get("/health")
async def backlog_health():
    """backlog 健康检查 (W8 plan engine 调度用)"""
    from sqlalchemy import func as sa_func
    async with Database.session() as session:
        total_stmt = select(sa_func.count(PrdBacklog.id))
        total_count = (await session.execute(total_stmt)).scalar() or 0
        p0_stmt = select(sa_func.count(PrdBacklog.id)).where(PrdBacklog.priority == "P0")
        p0_count = (await session.execute(p0_stmt)).scalar() or 0

    return {
        "status": "ok",
        "service_id": "lexprime.backlog.prd-tickets",
        "version": "0.1.0-w8",
        "total_tickets": total_count,
        "p0_tickets": p0_count,
        "expected_initial_import": 42,  # A1 归并 42 项独立问题
        "endpoints": [
            "POST /api/backlog/from-question",
            "GET /api/backlog/list",
            "POST /api/backlog/{id}/assign",
            "GET /api/backlog/board",
            "GET /api/backlog/health",
        ],
    }
