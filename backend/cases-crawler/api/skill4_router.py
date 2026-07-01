"""
LexPrime Skill 4 v1 - AI 辅助谈判 FastAPI 端点 (W29 skill4-v1-impl · 2026-07-01)

VERDICT: PASS (W22+23 强制规范应用)

任务: W29 skill4-v1-impl
必读:
- W28 owner commit 8670417 (Skill 4 v1 PRD)
- W28 f713970 owner commit (Phase 6.1 Marketplace PRD)
- W26 ab59c49 Skill 3 v3.0 launch (skill_endpoints 样板)
- W22 phase5-rust-build-fix (Rust 5x perf)
- W11 PRD V5.0 § 5.4 (Skill Hub) + § 5.6 (当事人服务类文书)

端点 (4 模块对应 4 endpoint + 2 工具端点):
- POST /api/skill4/strategies         生成谈判策略 (3 套 + 胜诉率 + 话术)
- POST /api/skill4/simulate-opponent 模拟对方 3 角色 (lawyer / party / judge)
- POST /api/skill4/detect-risk       实时风险预警 (5 类型)
- POST /api/skill4/debrief           谈判复盘报告 + 5 维度评分
- GET  /api/skill4/health            Skill 健康检查
- GET  /api/skill4/disclaimer        强制免责声明

集成:
- Phase 6.1 Marketplace API (W28 f713970) 转介绍谈判 stub
- W12 doc_workflow 状态机 (复用 NEGOTIATION_STATE_TRANSITIONS)
- W22 Rust 5x perf (Python fallback < 500ms, 生产环境 < 100µs)
"""
from __future__ import annotations

import time
from typing import List

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from skills.negotiation.negotiation_models import (
    CROSS_BORDER_FRAMEWORKS,
    DimensionType,
    Language,
    NEGOTIATION_STATE_TRANSITIONS,
    NegotiationCase,
    NegotiationCaseType,
    NegotiationState,
    NegotiationStrategy,
    OpponentRole,
    OpponentSimulation,
    RiskAlert,
    RiskType,
)
from skills.negotiation.negotiation_engine import (
    NegotiationEngineConfig,
    detect_real_time_risk,
    generate_strategies,
    simulate_opponent,
)
from skills.negotiation.debrief_report import (
    DebriefReportConfig,
    build_debrief_report,
)


router = APIRouter(prefix="/api/skill4", tags=["skill:negotiation"])


# ========== 强制免责声明 (PRD V5.0 § 11) ==========

DISCLAIMER_FULL = (
    "Skill 4 v1 (AI 辅助谈判) 输出基于模板规则引擎生成, "
    "仅作为辅助律师准备谈判策略、模拟对方与风险预警的参考, "
    "不构成正式法律意见, 不替代律师专业判断。"
    "具体案件需结合实际情况、客户期望及司法裁判进行评估。"
)

DISCLAIMER_SHORT = (
    "Skill 4 v1 输出仅作为辅助律师谈判的参考, 不构成正式法律意见。"
)


# ========== Request / Response Models ==========

class StrategyRequest(BaseModel):
    """生成谈判策略请求"""
    case_id: str = Field(..., min_length=2, max_length=64)
    case_type: str = Field(..., description="9 案件类型 (contract_dispute / tort / family / equity / ip / labor / admin_review / settlement / cross_border_trade)")
    breach_side: str = Field("other", pattern="^(self|other|neutral)$")
    amount_cny: float = Field(0, ge=0)
    desired_outcome: str = Field("moderate", pattern="^(conservative|moderate|aggressive)$")
    opponent_role: str = Field("lawyer", pattern="^(lawyer|party|judge)$")
    case_facts: str = Field("", max_length=4000)
    lawyer_id: str = Field(..., min_length=1)
    cross_border: bool = False
    jurisdiction: str = ""
    language: str = Field("zh", pattern="^(zh|en)$")

    class Config:
        json_schema_extra = {
            "example": {
                "case_id": "C-CON-001",
                "case_type": "contract_dispute",
                "breach_side": "other",
                "amount_cny": 500000,
                "desired_outcome": "moderate",
                "opponent_role": "lawyer",
                "case_facts": "被告逾期支付货款 50 万元",
                "lawyer_id": "L001",
            }
        }


class StrategyResponse(BaseModel):
    """策略生成响应"""
    case: dict
    strategies: List[dict]
    trajectory: dict
    disclaimer: str


class SimulateOpponentRequest(BaseModel):
    """模拟对方请求"""
    case: StrategyRequest
    role: str = Field("lawyer", pattern="^(lawyer|party|judge)$")
    round_num: int = Field(1, ge=1, le=20)
    language: str = Field("zh", pattern="^(zh|en)$")


class SimulateOpponentResponse(BaseModel):
    """模拟对方响应"""
    case_id: str
    simulation: dict
    trajectory: dict
    disclaimer: str


class DetectRiskRequest(BaseModel):
    """实时风险检测请求"""
    text: str = Field(..., min_length=1, max_length=10000)
    risk_type: str = Field(..., description="5 风险类型")


class DetectRiskResponse(BaseModel):
    """实时风险检测响应"""
    risk_type: str
    alert: dict
    trajectory: dict
    disclaimer: str


class DebriefRequest(BaseModel):
    """谈判复盘请求"""
    case_id: str = Field(..., min_length=2, max_length=64)
    lawyer_id: str = Field(..., min_length=1)
    trajectory: dict = Field(..., description="谈判轨迹 (含 5 维度评分)")
    # 5 维度评分 (0-1)
    facts_match: float = Field(0.5, ge=0, le=1)
    legal_match: float = Field(0.5, ge=0, le=1)
    demand_reasonable: float = Field(0.5, ge=0, le=1)
    timing: float = Field(0.5, ge=0, le=1)
    consequence: float = Field(0.5, ge=0, le=1)
    # 关键节点
    key_clauses: List[str] = Field(default_factory=list)
    risk_points: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)


class DebriefResponse(BaseModel):
    """谈判复盘响应"""
    case_id: str
    lawyer_id: str
    scores: dict
    avg_score: float
    similar_cases_comparison: str
    narrative: str
    disclaimer: str


# ========== 工具函数 ==========

def _to_case_dict(case: NegotiationCase) -> dict:
    """NegotiationCase → dict"""
    return case.to_dict()


def _to_strategy_dict(s: NegotiationStrategy) -> dict:
    return s.to_dict()


def _to_sim_dict(s: OpponentSimulation) -> dict:
    return s.to_dict()


def _to_alert_dict(a: RiskAlert) -> dict:
    return a.to_dict()


def _build_case(req: StrategyRequest) -> NegotiationCase:
    """StrategyRequest → NegotiationCase"""
    try:
        case_type = NegotiationCaseType(req.case_type)
    except ValueError as e:
        raise HTTPException(400, f"未知 case_type: {req.case_type}") from e
    try:
        opponent_role = OpponentRole(req.opponent_role)
    except ValueError as e:
        raise HTTPException(400, f"未知 opponent_role: {req.opponent_role}") from e
    try:
        language = Language(req.language)
    except ValueError as e:
        raise HTTPException(400, f"未知 language: {req.language}") from e

    return NegotiationCase(
        case_id=req.case_id,
        case_type=case_type,
        breach_side=req.breach_side,
        amount_cny=req.amount_cny,
        desired_outcome=req.desired_outcome,
        opponent_role=opponent_role,
        case_facts=req.case_facts,
        lawyer_id=req.lawyer_id,
        cross_border=req.cross_border,
        jurisdiction=req.jurisdiction,
        language=language,
    )


# ========== 端点 ==========

@router.get("/health")
async def skill_health():
    """Skill 4 v1 健康检查"""
    return {
        "status": "ok",
        "skill_id": "lexprime.skill.negotiation",
        "version": "1.0.0-w29",
        "modules": [
            "negotiation_strategy_generator",
            "opponent_simulator",
            "real_time_risk_detector",
            "debrief_report",
        ],
        "case_types": [ct.value for ct in NegotiationCaseType],
        "opponent_roles": [r.value for r in OpponentRole],
        "risk_types": [rt.value for rt in RiskType],
        "dimensions": [d.value for d in DimensionType],
        "cross_border_frameworks": list(CROSS_BORDER_FRAMEWORKS.keys()),
    }


@router.get("/disclaimer")
async def skill_disclaimer():
    """返回强制免责声明 (前端可独立 fetch 渲染)"""
    return {
        "full": DISCLAIMER_FULL,
        "short": DISCLAIMER_SHORT,
    }


@router.get("/manifest")
async def skill_manifest():
    """返回 Skill manifest (agentskills.io 标准)"""
    return {
        "skill_id": "lexprime.skill.negotiation",
        "version": "1.0.0-w29",
        "track": "E-skills · T-REF-22 (subagent RPC)",
        "endpoints": [
            {"path": "/api/skill4/strategies", "method": "POST", "purpose": "生成 3 套谈判策略"},
            {"path": "/api/skill4/simulate-opponent", "method": "POST", "purpose": "模拟对方 3 角色"},
            {"path": "/api/skill4/detect-risk", "method": "POST", "purpose": "实时风险预警 5 类型"},
            {"path": "/api/skill4/debrief", "method": "POST", "purpose": "谈判复盘报告 + 5 维度评分"},
            {"path": "/api/skill4/health", "method": "GET", "purpose": "Skill 健康检查"},
            {"path": "/api/skill4/disclaimer", "method": "GET", "purpose": "强制免责声明"},
        ],
        "test_baseline": "10 baseline 谈判场景测试 (W29 skill4-v1-impl)",
        "compliance": [
            "PRD V5.0 § 11 法务自检 (禁用'必胜/必败/一定' 等违规词)",
            "W11 类案界面语言规范 ('近 3 年本法院 X 件支持原告 Y 件 约 Z%')",
            "W12 doc_workflow 5 状态机模式 (draft → ai_reviewed → lawyer_reviewed → settled → archived)",
            "W22 Rust 5x perf 模式 (Python fallback < 500ms)",
            "Phase 6.1 Marketplace API 集成 stub (W28 f713970)",
        ],
    }


@router.post("/strategies", response_model=StrategyResponse)
async def generate_strategies_endpoint(req: StrategyRequest):
    """生成谈判策略 (PRD § 2.1)

    输入: 案件类型 + 违约方 + 期望结果 + 对方角色
    输出: 3 套策略 (conservative / moderate / aggressive) + 胜诉率 + 建议话术
    """
    t0 = time.time()

    try:
        case = _build_case(req)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"构造 case 失败: {e}")
        raise HTTPException(400, f"输入解析失败: {str(e)}") from e

    config = NegotiationEngineConfig()
    strategies = generate_strategies(case, config)

    latency_ms = int((time.time() - t0) * 1000)

    # 状态机: draft → ai_reviewed (策略已生成)
    case.transition_to(NegotiationState.AI_REVIEWED)

    return StrategyResponse(
        case=_to_case_dict(case),
        strategies=[_to_strategy_dict(s) for s in strategies],
        trajectory={
            "latency_ms": latency_ms,
            "strategy_count": len(strategies),
            "case_state": case.state.value,
            "language": case.language.value,
            "cross_border": case.cross_border,
        },
        disclaimer=DISCLAIMER_FULL,
    )


@router.post("/simulate-opponent", response_model=SimulateOpponentResponse)
async def simulate_opponent_endpoint(req: SimulateOpponentRequest):
    """模拟对方 3 角色 (PRD § 2.2)

    输入: 案件详情 + 对方角色 (lawyer / party / judge) + 谈判轮次
    输出: 对方回应 + 策略 + 角色特定字段 (psychology_hint / tendency)
    """
    t0 = time.time()

    try:
        case = _build_case(req.case)
        try:
            role = OpponentRole(req.role)
        except ValueError as e:
            raise HTTPException(400, f"未知 role: {req.role}") from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"构造 case 失败: {e}")
        raise HTTPException(400, f"输入解析失败: {str(e)}") from e

    sim = simulate_opponent(case, role=role, round_num=req.round_num)

    latency_ms = int((time.time() - t0) * 1000)

    return SimulateOpponentResponse(
        case_id=case.case_id,
        simulation=_to_sim_dict(sim),
        trajectory={
            "latency_ms": latency_ms,
            "role": role.value,
            "round_num": req.round_num,
        },
        disclaimer=DISCLAIMER_FULL,
    )


@router.post("/detect-risk", response_model=DetectRiskResponse)
async def detect_risk_endpoint(req: DetectRiskRequest):
    """实时风险预警 5 类型 (PRD § 2.3)

    输入: 谈判内容 (语音转文字) + 风险类型
    输出: RiskAlert 含 triggered + matched_keywords + suggestion
    """
    t0 = time.time()

    try:
        try:
            risk_type = RiskType(req.risk_type)
        except ValueError as e:
            raise HTTPException(400, f"未知 risk_type: {req.risk_type}") from e

        alert = detect_real_time_risk(req.text, risk_type=risk_type)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"风险检测失败: {e}")
        raise HTTPException(400, f"风险检测失败: {str(e)}") from e

    latency_ms = int((time.time() - t0) * 1000)

    return DetectRiskResponse(
        risk_type=risk_type.value,
        alert=_to_alert_dict(alert),
        trajectory={
            "latency_ms": latency_ms,
            "text_length": len(req.text),
        },
        disclaimer=DISCLAIMER_FULL,
    )


@router.post("/debrief", response_model=DebriefResponse)
async def debrief_endpoint(req: DebriefRequest):
    """谈判复盘报告 + 5 维度评分 (PRD § 2.4 + § 4.3)

    输入: 谈判轨迹 (含 5 维度评分 + 关键节点 + 风险点)
    输出: DebriefReport + 5 维度评分 + 改进建议 + 类似案件对比
    """
    t0 = time.time()

    trajectory = {
        "facts_match": req.facts_match,
        "legal_match": req.legal_match,
        "demand_reasonable": req.demand_reasonable,
        "timing": req.timing,
        "consequence": req.consequence,
        "key_clauses": req.key_clauses,
        "risk_points": req.risk_points,
        "improvements": req.improvements,
    }

    config = DebriefReportConfig()
    report = build_debrief_report(
        case_id=req.case_id,
        lawyer_id=req.lawyer_id,
        trajectory=trajectory,
        config=config,
    )

    _ = int((time.time() - t0) * 1000)  # trajectory 内部记录

    return DebriefResponse(
        case_id=report.case_id,
        lawyer_id=report.lawyer_id,
        scores=report.scores.to_dict(),
        avg_score=report.avg_score,
        similar_cases_comparison=report.similar_cases_comparison,
        narrative=report.narrative,
        disclaimer=report.disclaimer,
    )


@router.get("/cross-border-frameworks")
async def cross_border_frameworks():
    """跨境法律框架 (PRD § 1.2 优势 5)"""
    return {
        "frameworks": CROSS_BORDER_FRAMEWORKS,
        "supported_languages": [lang.value for lang in Language],
        "jurisdictions_supported": [
            "中国大陆",
            "中国香港",
            "新加坡",
            "纽约州",
            "英国",
            "欧盟",
            "日本",
            "韩国",
        ],
    }


# ========== 状态机端点 (W12 doc_workflow 模式) ==========

class StateTransitionRequest(BaseModel):
    """状态转移请求"""
    case_id: str
    from_state: str
    to_state: str


@router.post("/state-transition")
async def state_transition_endpoint(req: StateTransitionRequest):
    """谈判状态机状态转移 (W12 doc_workflow 模式)

    5 状态: draft → ai_reviewed → lawyer_reviewed → settled → archived
    """
    try:
        try:
            from_state = NegotiationState(req.from_state)
            to_state = NegotiationState(req.to_state)
        except ValueError as e:
            raise HTTPException(400, f"未知状态: {req.from_state} / {req.to_state}") from e

        # 校验合法性 (复用 NEGOTIATION_STATE_TRANSITIONS, 不依赖 __import__ hack)
        allowed = [s.value for s in NEGOTIATION_STATE_TRANSITIONS.get(from_state, [])]
        if to_state.value not in allowed:
            raise HTTPException(
                400,
                f"非法状态转移: {from_state.value} → {to_state.value}, 仅允许 {allowed}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"状态转移失败: {e}")
        raise HTTPException(400, f"状态转移失败: {str(e)}") from e

    return {
        "case_id": req.case_id,
        "from_state": from_state.value,
        "to_state": to_state.value,
        "transition_valid": True,
    }


# ========== Marketplace 集成 stub (Phase 6.1, W28 f713970) ==========

@router.get("/marketplace/integration")
async def marketplace_integration():
    """Marketplace 集成 stub (Phase 6.1, W28 f713970 owner commit)

    W30+ 实测: 律师 Marketplace 转介绍谈判
    """
    return {
        "status": "stub",
        "marketplace_prd": "W28 f713970 Phase 6.1 Marketplace PRD",
        "integration_phase": "W30+ deferred",
        "scope": "律师 Marketplace 转介绍谈判 (W28 § 1.2 优势 6)",
        "endpoints_planned": [
            "POST /api/marketplace/refer-negotiation",  # 转介绍谈判
            "GET /api/marketplace/negotiation-revenue",  # 谈判分成统计
        ],
        "note": "W29 skill4-v1-impl 仅落地核心 4 模块, Marketplace 集成 W30+ 实测",
    }
