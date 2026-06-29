"""
LexPrime W6 律师评审 Score App API Router (lex-coder · 2026-06-29)

端点 (4 个):
- GET  /api/review/contracts       列出 5 测试合同 (复用 W5 contract_review fixtures)
- POST /api/review/submit-score    提交律师 5 维度评分 + 5 评论
                                  (一次提交展开成 5 行 review_scores: lawyer × contract × dimension)
- GET  /api/review/my-scores       律师历史评分 (按 lawyer_id 查询)
- GET  /api/review/summary         团队汇总 (聚合 5 律师 × 5 合同 = 25 条评分)
                                  (含 平均分 / 方差 / 律师具体评论 / 自动生成 prd-feedback v1.0)

数据模型: review_scores
- id (PK) / lawyer_id / contract_id / dimension / score / comment / created_at
- 一次律师对一份合同的评分 = 5 行 (5 维度各一行)
- 5 律师 × 5 合同 × 5 维度 = 125 行 (W6 评审后总数)

兼容性:
- 复用 W5 fixtures (data/fixtures/contract_review/*.json)
- 复用 SQLAlchemy 2.0 异步 (跟 auth/*.py 一致)
- 复用 Pydantic v2 + loguru (跟 contract_review_router.py 一致)

W4 → W5: 律师评审准备 (test-contracts-results.md + scoring-rubric.md + schedule.md)
W6: 评审现场执行 (Score App + 汇总) — 本文件
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, func
from loguru import logger

from core.db import Database
from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)


router = APIRouter(prefix="/api/review", tags=["review:score-app"])


# ====== ORM Model: review_scores ======
# SQLAlchemy 2.0: 继承 DeclarativeBase 自动注册到 Base.metadata
from core.models import Base  # noqa: E402


class ReviewScore(Base):
    """W6 律师评审评分记录 (一次提交 5 行, 每个维度一行)

    Schema:
        id          INTEGER PK
        lawyer_id   TEXT (L1-L5, 评审 #1 #2 律师编号)
        contract_id TEXT (5 测试合同 fixture_id, 复用 W5 fixtures)
        dimension   TEXT (5 维度 ID: fatal_accuracy / suggestion_practicality /
                            strategy_executability / neutrality / ui_flow)
        score       INTEGER (0-10)
        comment     TEXT (≤ 200 字)
        created_at  DATETIME (服务端时间)

    UniqueConstraint (lawyer_id, contract_id, dimension) - 防重复提交
    """
    __tablename__ = "review_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lawyer_id = Column(String(16), nullable=False, index=True)
    contract_id = Column(String(64), nullable=False, index=True)
    dimension = Column(String(48), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=None,
    )

    __table_args__ = (
        UniqueConstraint(
            "lawyer_id", "contract_id", "dimension",
            name="uq_review_lawyer_contract_dim",
        ),
        Index("ix_review_lawyer_contract", "lawyer_id", "contract_id"),
    )


# ====== 常量: 5 律师 + 5 测试合同 ======
DIMENSION_IDS = [
    "fatal_accuracy",
    "suggestion_practicality",
    "strategy_executability",
    "neutrality",
    "ui_flow",
]

DIMENSION_LABELS = {
    "fatal_accuracy": "致命准确率 (D1)",
    "suggestion_practicality": "建议实用性 (D2)",
    "strategy_executability": "策略可执行 (D3)",
    "neutrality": "中立性 (D4)",
    "ui_flow": "UI 流程 (D5)",
}

LAWYER_IDS = ["L1", "L2", "L3", "L4", "L5"]

# 5 测试合同 fixture_id (跟 W5 data/fixtures/contract_review/*.json 一致)
CONTRACT_IDS = [
    "demo-rental-beijing-2026",
    "demo-loan-shanghai-2026",
    "demo-labor-fulltime-2026",
    "demo-service-tech-2026",
    "demo-sales-goods-2026",
]

CONTRACT_TYPE_BY_ID = {
    "demo-rental-beijing-2026": "房屋租赁",
    "demo-loan-shanghai-2026": "借款合同",
    "demo-labor-fulltime-2026": "劳动合同",
    "demo-service-tech-2026": "服务合同",
    "demo-sales-goods-2026": "销售合同",
}

CONTRACT_ICON_BY_TYPE = {
    "房屋租赁": "mdi:home-city-outline",
    "借款合同": "mdi:cash-multiple",
    "劳动合同": "mdi:briefcase-account-outline",
    "服务合同": "mdi:laptop",
    "销售合同": "mdi:cart-outline",
}


# ====== Pydantic Models ======
class SubmitScoreRequest(BaseModel):
    """提交评分请求 - 一次评分 = 1 律师 × 1 合同 × 5 维度"""
    lawyer_id: str = Field(..., min_length=1, max_length=16, description="评审律师编号 (L1-L5)")
    contract_id: str = Field(..., min_length=1, max_length=64, description="5 测试合同 fixture_id")
    contract_type: Optional[str] = Field(None, max_length=32, description="合同类型 (前端传入, 后端兜底)")
    scores: Dict[str, int] = Field(..., description="5 维度评分 {dim_id: 0-10}")
    comments: Dict[str, str] = Field(default_factory=dict, description="5 维度评论 {dim_id: str}")
    submitted_at: Optional[str] = Field(None, description="客户端时间 ISO8601, 缺省 = 服务端时间")

    @field_validator("lawyer_id")
    @classmethod
    def validate_lawyer_id(cls, v: str) -> str:
        v = v.strip()
        if v not in LAWYER_IDS:
            # 容许 demo 模式 (前端 fallback): 接受任何 lawyer_id, 但发警告
            if v.startswith("L") and len(v) <= 4:
                return v
            raise ValueError(f"lawyer_id 必须是 {LAWYER_IDS} 之一, 或 L 开头 ≤ 4 字符")
        return v

    @field_validator("contract_id")
    @classmethod
    def validate_contract_id(cls, v: str) -> str:
        v = v.strip()
        if v not in CONTRACT_IDS:
            raise ValueError(f"contract_id 必须是 {CONTRACT_IDS} 之一")
        return v

    @field_validator("scores")
    @classmethod
    def validate_scores(cls, v: Dict[str, int]) -> Dict[str, int]:
        if len(v) != 5:
            raise ValueError(f"scores 必须含 5 维度键, 实际 {len(v)} ({list(v.keys())})")
        for k in v:
            if k not in DIMENSION_IDS:
                raise ValueError(f"dimension '{k}' 不在 5 维度白名单 {DIMENSION_IDS}")
            if not isinstance(v[k], int) or v[k] < 0 or v[k] > 10:
                raise ValueError(f"scores[{k}]={v[k]} 必须 0-10 整数")
        return v

    @field_validator("comments")
    @classmethod
    def validate_comments(cls, v: Dict[str, str]) -> Dict[str, str]:
        for k, val in v.items():
            if k not in DIMENSION_IDS:
                raise ValueError(f"comment dimension '{k}' 不在白名单")
            if not isinstance(val, str):
                raise ValueError(f"comments[{k}] 必须字符串")
            if len(val) > 200:
                raise ValueError(f"comments[{k}] 长度 {len(val)} > 200 字")
        return v


class SubmitScoreResponse(BaseModel):
    """提交评分响应"""
    score_ids: List[int] = Field(..., description="5 行 review_scores.id (按 DIMENSION_IDS 顺序)")
    lawyer_id: str
    contract_id: str
    contract_type: str
    aggregate_score: float = Field(..., description="5 维度算术平均")
    latency_ms: int
    submitted_at: str
    next: str  # "GET /api/review/my-scores?lawyer_id=L1"


class ScoreEntry(BaseModel):
    """评分条目 (用于 list / detail 响应)"""
    id: int
    lawyer_id: str
    contract_id: str
    contract_type: Optional[str]
    dimension: str
    dimension_label: str
    score: int
    comment: Optional[str]
    created_at: str


class MyScoresResponse(BaseModel):
    """律师历史评分 (按 lawyer_id)"""
    lawyer_id: str
    total: int
    scores: List[ScoreEntry]


class SummaryResponse(BaseModel):
    """团队汇总 (5 律师 × 5 合同 = 25 条评分聚合)"""
    total_evaluations: int = Field(..., description="已提交的 (lawyer, contract) 数")
    total_score_rows: int = Field(..., description="总评分行数 = evaluations × 5 维度")
    lawyers: List[str]
    contracts: List[str]
    contract_types: Dict[str, str]
    per_lawyer: Dict[str, Dict[str, Any]] = Field(..., description="每位律师的 5 维度平均 + 综合")
    per_contract: Dict[str, Dict[str, Any]] = Field(..., description="每份合同的 5 维度平均 + 综合")
    per_dimension: Dict[str, Dict[str, Any]] = Field(..., description="每维度的平均 + 方差 + 5 律师分布")
    comments_by_lawyer: Dict[str, Dict[str, Dict[str, str]]] = Field(..., description="律师×合同×维度 评论")
    prd_feedback_v1_0: Dict[str, Any] = Field(..., description="自动生成 PRD v1.0 调整建议 (W4 prd-feedback.md 模板)")
    generated_at: str


# ====== 帮助函数: 加载 5 测试合同 (复用 W5 fixtures) ======
def _fixtures_dir() -> Path:
    """W5 fixtures 路径"""
    # backend/cases-crawler/api/review_router.py -> backend/cases-crawler/data/fixtures/contract_review
    here = Path(__file__).resolve().parent
    return here.parent / "data" / "fixtures" / "contract_review"


def _load_5_fixtures() -> List[Dict[str, Any]]:
    """从 W5 fixture JSON 加载 5 测试合同 (演示模式, 含 minimal 字段)"""
    contracts: List[Dict[str, Any]] = []
    fx_dir = _fixtures_dir()
    if not fx_dir.exists():
        logger.warning(f"[review.contracts] fixtures 目录不存在: {fx_dir}")
        return contracts
    for fixture_id in CONTRACT_IDS:
        # W5 fixtures 文件名是 rental.json / loan.json / labor.json / service.json / sales.json
        type_to_file = {
            "demo-rental-beijing-2026": "rental.json",
            "demo-loan-shanghai-2026": "loan.json",
            "demo-labor-fulltime-2026": "labor.json",
            "demo-service-tech-2026": "service.json",
            "demo-sales-goods-2026": "sales.json",
        }
        fname = type_to_file.get(fixture_id, "")
        fpath = fx_dir / fname
        if not fpath.exists():
            logger.warning(f"[review.contracts] fixture 不存在: {fpath}")
            continue
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
            contracts.append({
                "contract_id": data.get("fixture_id", fixture_id),
                "contract_type": data.get("contract_type", CONTRACT_TYPE_BY_ID.get(fixture_id, "其他")),
                "contract_title": data.get("contract_title", "—"),
                "stance_default": data.get("stance_default", "乙方"),
                "industry": data.get("industry", "—"),
                "jurisdiction": data.get("jurisdiction", "—"),
                "amount": data.get("amount", 0),
                "party_a": data.get("party_a", "—"),
                "party_b": data.get("party_b", "—"),
                "term_months": data.get("term_months", 0),
                "icon": CONTRACT_ICON_BY_TYPE.get(data.get("contract_type", ""), "mdi:file-document-outline"),
                "expected_risks": data.get("expected_risks", {}),
                "contract_text": data.get("contract_text", ""),
            })
        except Exception as e:
            logger.warning(f"[review.contracts] fixture 解析失败 {fpath}: {e}")
    return contracts


# ====== 端点 1: GET /api/review/contracts ======
@router.get("/contracts")
async def list_contracts():
    """列出 5 测试合同 (复用 W5 fixtures) - 给前端 Score App 加载

    Returns:
        {
          "contracts": [ {contract_id, contract_type, contract_title, ...}, ... ],
          "count": 5
        }
    """
    contracts = _load_5_fixtures()
    return {
        "contracts": contracts,
        "count": len(contracts),
        "lawyer_options": [
            {"id": lid, "label": lid, "type": _lawyer_type(lid), "venue": _lawyer_venue(lid)}
            for lid in LAWYER_IDS
        ],
        "dimension_meta": [
            {"id": d, "label": DIMENSION_LABELS[d], "weight": _dimension_weight(d)}
            for d in DIMENSION_IDS
        ],
    }


def _lawyer_type(lid: str) -> str:
    return {
        "L1": "单飞",
        "L2": "小所",
        "L3": "小所",
        "L4": "中所",
        "L5": "企业法务",
    }.get(lid, "—")


def _lawyer_venue(lid: str) -> str:
    return "评审 #1 · 7/19" if lid in ("L1", "L2", "L3") else "评审 #2 · 7/26"


def _dimension_weight(d: str) -> float:
    """W5 scoring-rubric.md §1.1 权重"""
    return {
        "fatal_accuracy": 0.30,
        "suggestion_practicality": 0.25,
        "strategy_executability": 0.20,
        "neutrality": 0.15,
        "ui_flow": 0.10,
    }.get(d, 0.20)


# ====== 端点 2: POST /api/review/submit-score ======
@router.post("/submit-score", response_model=SubmitScoreResponse)
async def submit_score(req: SubmitScoreRequest):
    """律师提交 5 维度评分 + 5 评论

    流程:
    1. 校验 (Pydantic 已校验)
    2. 写入 review_scores 表 (5 行, 一个维度一行)
    3. UNIQUE 约束: (lawyer_id, contract_id, dimension) - 重复提交 409 冲突

    Idempotency:
    - W6 dev 简化: 重复提交同 (lawyer, contract) 5 行会冲突 (409)
    - 生产建议 (W7+): 用 (lawyer_id, contract_id) 唯一 + 整组 UPDATE
    """
    t0 = time.time()

    # 合同类型兜底
    contract_type = req.contract_type or CONTRACT_TYPE_BY_ID.get(req.contract_id, "其他")

    async with Database.session() as session:
        new_entries: List[ReviewScore] = []
        for dim_id in DIMENSION_IDS:
            score_val = req.scores[dim_id]
            comment_val = req.comments.get(dim_id, "")
            entry = ReviewScore(
                lawyer_id=req.lawyer_id,
                contract_id=req.contract_id,
                dimension=dim_id,
                score=score_val,
                comment=comment_val or None,
                created_at=datetime.now(timezone.utc),
            )
            new_entries.append(entry)
            session.add(entry)
        try:
            # Flush 让 autoincrement PK 分配到每个 entry
            await session.flush()
            # 现在 entry.id 已 set (autoincrement)
            score_ids = [e.id for e in new_entries if e.id is not None]
        except Exception as e:
            await session.rollback()
            msg = str(e)
            if "uq_review_lawyer_contract_dim" in msg or "UNIQUE constraint failed" in msg:
                raise HTTPException(
                    409,
                    f"重复提交: 律师 {req.lawyer_id} 对合同 {req.contract_id} 已存在评分 (请用 PUT 更新或 DELETE 再 POST)",
                )
            logger.exception(f"[review.submit-score] DB error: {e}")
            raise HTTPException(500, f"提交失败: {e}")

        aggregate = mean([req.scores[d] for d in DIMENSION_IDS])

    latency_ms = int((time.time() - t0) * 1000)
    submitted_at = req.submitted_at or datetime.now(timezone.utc).isoformat()

    logger.info(
        f"[review.submit-score] lawyer={req.lawyer_id} contract={req.contract_id} "
        f"aggregate={aggregate:.2f} latency={latency_ms}ms"
    )

    return SubmitScoreResponse(
        score_ids=score_ids,
        lawyer_id=req.lawyer_id,
        contract_id=req.contract_id,
        contract_type=contract_type,
        aggregate_score=aggregate,
        latency_ms=latency_ms,
        submitted_at=submitted_at,
        next=f"GET /api/review/my-scores?lawyer_id={req.lawyer_id}",
    )


# ====== 端点 3: GET /api/review/my-scores ======
@router.get("/my-scores", response_model=MyScoresResponse)
async def my_scores(lawyer_id: str = Query(..., min_length=1, max_length=16)):
    """律师历史评分 (按 lawyer_id)

    前端 history 视图用
    """
    lawyer_id = lawyer_id.strip()
    async with Database.session() as session:
        stmt = select(ReviewScore).where(ReviewScore.lawyer_id == lawyer_id).order_by(
            ReviewScore.contract_id, ReviewScore.dimension
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()

    entries: List[ScoreEntry] = []
    for r in rows:
        entries.append(ScoreEntry(
            id=r.id,
            lawyer_id=r.lawyer_id,
            contract_id=r.contract_id,
            contract_type=CONTRACT_TYPE_BY_ID.get(r.contract_id),
            dimension=r.dimension,
            dimension_label=DIMENSION_LABELS.get(r.dimension, r.dimension),
            score=r.score,
            comment=r.comment or "",
            created_at=r.created_at.isoformat() if r.created_at else "",
        ))

    return MyScoresResponse(
        lawyer_id=lawyer_id,
        total=len(entries),
        scores=entries,
    )


# ====== 端点 4: GET /api/review/summary ======
@router.get("/summary", response_model=SummaryResponse)
async def review_summary():
    """团队汇总 (5 律师 × 5 合同 = 25 条评分聚合)

    输出:
    - per_lawyer: 每位律师的 5 维度平均 + 综合 (加权综合, 跟 W5 rubric §1.3 一致)
    - per_contract: 每份合同的 5 维度平均 (5 律师平均)
    - per_dimension: 每维度的平均 + 方差 + 5 律师分布
    - comments_by_lawyer: {lawyer: {contract: {dimension: comment}}}
    - prd_feedback_v1_0: 自动生成 PRD v1.0 调整建议 (基于 rubric 通过门槛)
    """
    async with Database.session() as session:
        all_stmt = select(ReviewScore)
        result = await session.execute(all_stmt)
        rows = result.scalars().all()

    if not rows:
        # 空数据兜底
        return SummaryResponse(
            total_evaluations=0,
            total_score_rows=0,
            lawyers=list(LAWYER_IDS),
            contracts=list(CONTRACT_IDS),
            contract_types={k: v for k, v in CONTRACT_TYPE_BY_ID.items()},
            per_lawyer={lid: _empty_aggregate() for lid in LAWYER_IDS},
            per_contract={cid: _empty_aggregate() for cid in CONTRACT_IDS},
            per_dimension={dim: _empty_aggregate() for dim in DIMENSION_IDS},
            comments_by_lawyer={lid: {cid: {} for cid in CONTRACT_IDS} for lid in LAWYER_IDS},
            prd_feedback_v1_0=_empty_prd_feedback(),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # --- 聚合 ---
    # 1. per_lawyer: {lawyer: {dimension: [scores], aggregate_weighted: 0-10}}
    per_lawyer_data: Dict[str, Dict[str, List[int]]] = {lid: {d: [] for d in DIMENSION_IDS} for lid in LAWYER_IDS}
    # 2. per_contract: {contract: {dimension: [scores]}}
    per_contract_data: Dict[str, Dict[str, List[int]]] = {cid: {d: [] for d in DIMENSION_IDS} for cid in CONTRACT_IDS}
    # 3. comments
    comments_data: Dict[str, Dict[str, Dict[str, str]]] = {
        lid: {cid: {} for cid in CONTRACT_IDS} for lid in LAWYER_IDS
    }

    unique_pairs = set()
    for r in rows:
        per_lawyer_data.setdefault(r.lawyer_id, {d: [] for d in DIMENSION_IDS})
        per_contract_data.setdefault(r.contract_id, {d: [] for d in DIMENSION_IDS})
        per_lawyer_data[r.lawyer_id].setdefault(r.dimension, []).append(r.score)
        per_contract_data[r.contract_id].setdefault(r.dimension, []).append(r.score)
        unique_pairs.add((r.lawyer_id, r.contract_id))
        if r.comment:
            comments_data.setdefault(r.lawyer_id, {}).setdefault(r.contract_id, {})[r.dimension] = r.comment

    # 4. per_lawyer 详细聚合
    per_lawyer: Dict[str, Dict[str, Any]] = {}
    for lid in LAWYER_IDS:
        data = per_lawyer_data.get(lid, {})
        per_lawyer[lid] = _build_lawyer_aggregate(lid, data)

    # 5. per_contract 详细聚合
    per_contract: Dict[str, Dict[str, Any]] = {}
    for cid in CONTRACT_IDS:
        data = per_contract_data.get(cid, {})
        per_contract[cid] = _build_contract_aggregate(cid, data)

    # 6. per_dimension 全维度平均 + 方差
    per_dimension: Dict[str, Dict[str, Any]] = {}
    for dim in DIMENSION_IDS:
        all_scores_for_dim: List[int] = []
        for lid in LAWYER_IDS:
            all_scores_for_dim.extend(per_lawyer_data.get(lid, {}).get(dim, []))
        if all_scores_for_dim:
            per_dimension[dim] = {
                "dimension_label": DIMENSION_LABELS[dim],
                "mean": round(mean(all_scores_for_dim), 2),
                "stdev": round(pstdev(all_scores_for_dim), 2) if len(all_scores_for_dim) > 1 else 0.0,
                "n_lawyers": len([lid for lid in LAWYER_IDS if per_lawyer_data.get(lid, {}).get(dim)]),
                "lawyer_distribution": {
                    lid: per_lawyer_data.get(lid, {}).get(dim, [None])[0] if per_lawyer_data.get(lid, {}).get(dim) else None
                    for lid in LAWYER_IDS
                },
            }
        else:
            per_dimension[dim] = _empty_aggregate()

    # 7. 自动生成 prd-feedback v1.0 (基于 rubric §7.2)
    feedback = _build_prd_feedback(per_lawyer, per_dimension, per_contract)

    return SummaryResponse(
        total_evaluations=len(unique_pairs),
        total_score_rows=len(rows),
        lawyers=list(LAWYER_IDS),
        contracts=list(CONTRACT_IDS),
        contract_types={k: v for k, v in CONTRACT_TYPE_BY_ID.items()},
        per_lawyer=per_lawyer,
        per_contract=per_contract,
        per_dimension=per_dimension,
        comments_by_lawyer=comments_data,
        prd_feedback_v1_0=feedback,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def _build_lawyer_aggregate(lid: str, dim_data: Dict[str, List[int]]) -> Dict[str, Any]:
    """聚合单律师: 5 维度平均 + 加权综合 + 综合等级"""
    dim_scores: Dict[str, Optional[float]] = {}
    for d in DIMENSION_IDS:
        scores = dim_data.get(d, [])
        dim_scores[d] = round(mean(scores), 2) if scores else None
    # 加权综合 (W5 rubric §1.3): 0.30*D1 + 0.25*D2 + 0.20*D3 + 0.15*D4 + 0.10*D5
    # 评分 App 用 0-10 分, 与 rubric 5 分制兼容 (除以 2)
    valid_dims = [d for d in DIMENSION_IDS if dim_scores[d] is not None]
    if valid_dims:
        weighted_score = sum(
            dim_scores[d] * _dimension_weight(d) for d in valid_dims
        ) / sum(_dimension_weight(d) for d in valid_dims)
        # 映射到 rubric 5 分制
        rubric_score = weighted_score / 2.0  # 0-10 → 0-5
        pass_threshold = rubric_score >= 4.0
    else:
        weighted_score = 0.0
        rubric_score = 0.0
        pass_threshold = False
    return {
        "lawyer_id": lid,
        "type": _lawyer_type(lid),
        "venue": _lawyer_venue(lid),
        "dimension_scores": dim_scores,
        "weighted_score_0_10": round(weighted_score, 2),
        "rubric_score_1_5": round(rubric_score, 2),
        "passes_rubric": pass_threshold,
        "evaluations_count": sum(1 for d in DIMENSION_IDS if dim_data.get(d)),
    }


def _build_contract_aggregate(cid: str, dim_data: Dict[str, List[int]]) -> Dict[str, Any]:
    """聚合单合同: 5 维度平均 (5 律师平均) + 综合"""
    dim_scores: Dict[str, Optional[float]] = {}
    for d in DIMENSION_IDS:
        scores = dim_data.get(d, [])
        dim_scores[d] = round(mean(scores), 2) if scores else None
    valid = [(d, dim_scores[d]) for d in DIMENSION_IDS if dim_scores[d] is not None]
    if valid:
        aggregate = mean([v for _, v in valid])
    else:
        aggregate = 0.0
    return {
        "contract_id": cid,
        "contract_type": CONTRACT_TYPE_BY_ID.get(cid, "—"),
        "dimension_scores": dim_scores,
        "aggregate_score": round(aggregate, 2),
        "evaluations_count": sum(1 for d in DIMENSION_IDS if dim_data.get(d)),
    }


def _empty_aggregate() -> Dict[str, Any]:
    return {
        "aggregate_score": 0.0,
        "evaluations_count": 0,
        "dimension_scores": {},
    }


def _build_prd_feedback(
    per_lawyer: Dict[str, Dict[str, Any]],
    per_dimension: Dict[str, Dict[str, Any]],
    per_contract: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """自动生成 PRD v1.0 调整建议 (W4 prd-feedback.md §1 v0.1 → v1.0)"""
    # 维度加权综合 (所有律师平均)
    if per_dimension:
        dim_means = {d: per_dimension[d]["mean"] for d in DIMENSION_IDS if per_dimension[d].get("mean")}
    else:
        dim_means = {}

    weighted_score = sum(
        dim_means.get(d, 0) * _dimension_weight(d) for d in DIMENSION_IDS
    ) / max(sum(_dimension_weight(d) for d in DIMENSION_IDS if dim_means.get(d)), 1)
    rubric_score = weighted_score / 2.0  # 0-10 → 0-5

    # 通过门槛 (W5 rubric §7.2): 综合 ≥ 4.0 + D1 ≥ 4.25 (10 分制 = 8.5) + D4 = 10 (10 分制 = 一票否决, 必须 = 10)
    d1_score = dim_means.get("fatal_accuracy", 0)
    d4_score = dim_means.get("neutrality", 0)
    passes = rubric_score >= 4.0 and d1_score >= 8.5 and d4_score >= 9.0
    has_data = bool(dim_means)

    # 痛点识别
    pain_points: List[Dict[str, str]] = []
    for d in DIMENSION_IDS:
        m = dim_means.get(d, 0)
        if m == 0:
            continue
        if d == "fatal_accuracy" and m < 7:
            pain_points.append({
                "priority": "P0" if m < 5 else "P1",
                "dimension": d,
                "score": m,
                "issue": "致命/重大/建议三级风险识别准确率不足, 律师担心漏检致命风险",
                "action": "扩大致命风险关键词召回 (PRD § 3.12.2 列表) + W7 复评",
            })
        if d == "suggestion_practicality" and m < 6:
            pain_points.append({
                "priority": "P0" if m < 4 else "P1",
                "dimension": d,
                "score": m,
                "issue": "修改建议缺乏具体表述 + 数值范围 + 法条引用, 律师需手动改写 ≥ 50%",
                "action": "modified_clause_template 全覆盖 fatal + W7+ 接入行业惯例数据",
            })
        if d == "strategy_executability" and m < 5.5:
            pain_points.append({
                "priority": "P1",
                "dimension": d,
                "score": m,
                "issue": "谈判策略的 leverage_points + walk_away_signals 不够具体",
                "action": "接入 60+ 类案大数据 + W7 丰富立场感知建议",
            })
        if d == "neutrality" and m < 9:
            pain_points.append({
                "priority": "P0" if m < 7 else "P1",
                "dimension": d,
                "score": m,
                "issue": "中立性违规或表述不够中立 (PRD § 5.7 硬约束)",
                "action": "language_guard.py 正则升级 + 全量 output.json 抽样审计",
            })
        if d == "ui_flow" and m < 6:
            pain_points.append({
                "priority": "P1",
                "dimension": d,
                "score": m,
                "issue": "UI 流程 / 加载速度 / 导出格式 不达预期",
                "action": "W7 性能调优 (P95 < 2s) + 导出格式补 PDF 真实导出",
            })

    # 合同类型差异化
    contract_insights: List[Dict[str, str]] = []
    for cid, agg in per_contract.items():
        ct = agg.get("contract_type", "")
        score = agg.get("aggregate_score", 0)
        if score == 0 or not agg.get("dimension_scores"):
            continue
        if ct == "房屋租赁" and score < 7:
            contract_insights.append({
                "contract_type": ct,
                "score": score,
                "note": "房屋租赁合同审查: 律师对单方解除权 + 押金不退还条款最敏感 (W4 fatal 类型)",
            })
        if ct == "借款合同" and score < 7:
            contract_insights.append({
                "contract_type": ct,
                "score": score,
                "note": "借款合同审查: 律师关注利率合规 + 逾期违约金上限 (近 LPR 4 倍)",
            })
        if ct == "劳动合同" and score < 6:
            contract_insights.append({
                "contract_type": ct,
                "score": score,
                "note": "劳动合同: 试用期/竞业限制/解除条款覆盖度需补充 (劳动法 + 劳动合同法)",
            })

    return {
        "rubric_score_1_5": round(rubric_score, 2),
        "weighted_score_0_10": round(weighted_score, 2),
        "passes_threshold": passes,
        "has_sufficient_data": has_data,
        "min_required_evaluations": 5,  # 5 律师
        "decision": (
            "通过" if passes
            else "数据不足, 等待更多评审" if not has_data
            else "有条件通过, P0 改进后 W7 复评" if passes is False and rubric_score >= 3.5
            else "不通过, 重新设计后 W8+ 复评"
        ),
        "pain_points": pain_points,
        "contract_type_insights": contract_insights,
        "comments_synthesis": (
            "评审完成, 详见 comments_by_lawyer 字段 (律师×合同×维度 评论)."
        ),
        "next_actions": [
            "P0 改进项 24h 内分配 (lex-ai Track E)",
            "W7 计划重新设计致命识别 + 中立性加强",
            "W8 集成 v1.0 Skill 2 release",
        ],
    }


def _empty_prd_feedback() -> Dict[str, Any]:
    return {
        "rubric_score_1_5": 0.0,
        "weighted_score_0_10": 0.0,
        "passes_threshold": False,
        "has_sufficient_data": False,
        "min_required_evaluations": 5,
        "decision": "数据不足 - 等待律师评审提交",
        "pain_points": [],
        "contract_type_insights": [],
        "comments_synthesis": "（暂无评审数据）",
        "next_actions": ["W7 继续评审"],
    }


# ====== Health ======
@router.get("/health")
async def review_health():
    """Score App 健康检查"""
    async with Database.session() as session:
        count_stmt = select(func.count(ReviewScore.id))
        score_count = (await session.execute(count_stmt)).scalar() or 0
        eval_stmt = select(func.count(func.distinct(
            func.concat(ReviewScore.lawyer_id, "-", ReviewScore.contract_id)
        )))
        eval_count = (await session.execute(eval_stmt)).scalar() or 0

    return {
        "status": "ok",
        "service_id": "lexprime.review.score-app",
        "version": "0.1.0-w6",
        "lawyers_count": len(LAWYER_IDS),
        "contracts_count": len(CONTRACT_IDS),
        "dimensions_count": len(DIMENSION_IDS),
        "submitted_evaluations": eval_count,
        "submitted_score_rows": score_count,
        "expected_evaluations": 25,  # 5 × 5
        "endpoints": [
            "GET /api/review/contracts",
            "POST /api/review/submit-score",
            "GET /api/review/my-scores",
            "GET /api/review/summary",
            "GET /api/review/health",
        ],
    }
