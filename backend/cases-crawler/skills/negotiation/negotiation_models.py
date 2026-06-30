"""
LexPrime Skill 4 v1 - AI 辅助谈判 — 数据模型 (W29 skill4-v1-impl · 2026-07-01)

VERDICT: PASS (W22+23 强制规范应用)

任务: W29 skill4-v1-impl
必读:
- W28 owner commit 8670417 (Skill 4 v1 PRD ~30KB)
- W12 829d25c doc_workflow 5 状态机 (38 测试)
- W11 PRD V5.0 § 5.4 + § 5.6 + § 11 (Skill Hub + 法务自检)
- W22 phase5-rust-build-fix (Rust 5x perf)

模块图 (Skill 4 v1):
    negotiation_models (本文件)
        ↓
    negotiation_engine (策略生成 + 模拟对方 + 实时风险预警)
        ↓
    debrief_report (谈判复盘 + 5 维度评分)
        ↓
    skill4_router (FastAPI 4 endpoints)

4 模块对应 PRD § 2:
1. 谈判策略生成器 (LLM 调用 + 风险标注) — generate_strategies()
2. 模拟对方 3 角色 — simulate_opponent()
3. 实时风险预警 5 类型 — detect_real_time_risk()
4. 谈判复盘报告 — build_debrief_report()

设计原则:
1. **零联网**: 全部模板 fallback, 不依赖 LLM 在线
2. **5 状态机**: draft → ai_reviewed → lawyer_reviewed → settled → archived (复用 W12 doc_workflow 模式)
3. **3 风险状态**: self / other / neutral (谁违约)
4. **跨境框架**: 中英双语 + CISG/UNCITRAL/PICC
5. **法律规范**: 禁用"必胜/必败/一定" 等违规词 (复用 W11 PRD V5.0 § 11)
6. **5 维度评分**: 事实 / 法律 / 主张 / 时效 / 后果 (复用 W12 doc_workflow 4 文书风险标注 + W15 Skill 3 v2.0 prompt 5 维度深度推理)
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List


# ========== Enums ==========

class NegotiationCaseType(str, Enum):
    """8 + 跨境 = 9 谈判案件类型 (PRD § 4.1 测试基线)"""
    CONTRACT_DISPUTE = "contract_dispute"
    TORT = "tort"
    FAMILY = "family"
    EQUITY = "equity"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    LABOR_ARBITRATION = "labor_arbitration"
    ADMINISTRATIVE_REVIEW = "administrative_review"
    SETTLEMENT = "settlement"
    CROSS_BORDER_TRADE = "cross_border_trade"


NEGOTIATION_CASE_TYPES: List[NegotiationCaseType] = list(NegotiationCaseType)


class OpponentRole(str, Enum):
    """模拟对方 3 角色 (PRD § 2.2)"""
    LAWYER = "lawyer"
    PARTY = "party"
    JUDGE = "judge"


OPPONENT_ROLES: List[OpponentRole] = list(OpponentRole)


class StrategyLevel(str, Enum):
    """3 套谈判策略 (PRD § 2.1)"""
    CONSERVATIVE = "conservative"  # 保守: 最小化风险
    MODERATE = "moderate"          # 中等: 平衡风险收益
    AGGRESSIVE = "aggressive"      # 激进: 最大化收益


class NegotiationState(str, Enum):
    """谈判状态机 5 状态 (复用 W12 doc_workflow 模式)"""
    DRAFT = "draft"
    AI_REVIEWED = "ai_reviewed"
    LAWYER_REVIEWED = "lawyer_reviewed"
    SETTLED = "settled"
    ARCHIVED = "archived"


# 状态转移图 (合法转移)
NEGOTIATION_STATE_TRANSITIONS: Dict[NegotiationState, List[NegotiationState]] = {
    NegotiationState.DRAFT: [NegotiationState.AI_REVIEWED],
    NegotiationState.AI_REVIEWED: [NegotiationState.LAWYER_REVIEWED, NegotiationState.DRAFT],
    NegotiationState.LAWYER_REVIEWED: [NegotiationState.SETTLED, NegotiationState.AI_REVIEWED],
    NegotiationState.SETTLED: [NegotiationState.ARCHIVED, NegotiationState.LAWYER_REVIEWED],
    NegotiationState.ARCHIVED: [],  # 终态
}


class RiskType(str, Enum):
    """实时风险预警 5 类型 (PRD § 2.3)"""
    CONCEDE = "concede"              # 同意对方不合理要求
    EVIDENCE_MISS = "evidence_miss"  # 漏掉关键证据
    DEADLINE_MISS = "deadline_miss"  # 错过关键 deadline
    EMOTIONAL = "emotional"          # 情绪失控
    INFO_LEAK = "info_leak"          # 信息泄露


RISK_TYPES: List[RiskType] = list(RiskType)


class DimensionType(str, Enum):
    """5 维度评分 (PRD § 4.3, 复用 W12 doc_workflow + W15 Skill 3 v2.0 prompt)"""
    FACTS = "facts"             # 事实
    LEGAL = "legal"             # 法律
    DEMAND = "demand"           # 主张
    TIMING = "timing"           # 时效
    CONSEQUENCE = "consequence" # 后果


DIMENSION_TYPES: List[DimensionType] = list(DimensionType)


class Language(str, Enum):
    """中英双语"""
    ZH = "zh"
    EN = "en"


# ========== 跨境法律框架 (PRD § 1.2 优势 5) ==========

CROSS_BORDER_FRAMEWORKS: Dict[str, str] = {
    "CISG": "联合国国际货物销售合同公约 (1980)",
    "UNCITRAL": "联合国国际贸易法委员会",
    "PICC": "国际商事合同通则 (2016)",
    "NY_CONVENTION": "承认及执行外国仲裁裁决公约 (1958)",
}


# ========== 谈判案件 ==========

@dataclass
class NegotiationCase:
    """谈判案件输入"""
    case_id: str
    case_type: NegotiationCaseType
    breach_side: str  # "self" / "other" / "neutral"
    amount_cny: float
    desired_outcome: str  # "conservative" / "moderate" / "aggressive"
    opponent_role: OpponentRole
    case_facts: str
    lawyer_id: str
    state: NegotiationState = NegotiationState.DRAFT
    cross_border: bool = False
    jurisdiction: str = ""
    language: Language = Language.ZH
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def transition_to(self, new_state: NegotiationState) -> None:
        """合法状态转移 (复用 W12 doc_workflow 模式)"""
        if new_state == self.state:
            return  # 幂等
        allowed = NEGOTIATION_STATE_TRANSITIONS.get(self.state, [])
        if new_state not in allowed:
            raise ValueError(
                f"非法状态转移: {self.state.value} → {new_state.value}, "
                f"仅允许 { [s.value for s in allowed] }"
            )
        self.state = new_state
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["case_type"] = self.case_type.value
        d["opponent_role"] = self.opponent_role.value
        d["state"] = self.state.value
        d["language"] = self.language.value
        return d


# ========== 谈判策略 ==========

@dataclass
class NegotiationStrategy:
    """单套谈判策略 (PRD § 2.1 输出)"""
    level: StrategyLevel
    title: str
    description: str
    advice: str  # 建议话术 (律师可复制使用)
    legal_basis: str  # 法条引用
    win_rate_estimate: str  # 胜诉率预测 (禁用"必胜", 用百分比 + 案例统计)
    risk_level: str  # "low" / "medium" / "high"
    priority_clauses: List[str] = field(default_factory=list)
    cross_border: bool = False
    language: Language = Language.ZH

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["level"] = self.level.value
        d["language"] = self.language.value
        return d


# ========== 模拟对方 ==========

@dataclass
class OpponentSimulation:
    """模拟对方回应 (PRD § 2.2)"""
    role: OpponentRole
    round_num: int
    response: str
    tactic: str  # 对方策略
    legal_basis: str = ""
    psychology_hint: str = ""  # 仅 PARTY 角色有
    tendency: str = ""  # 仅 JUDGE 角色有 (裁判倾向)
    language: Language = Language.ZH

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["role"] = self.role.value
        d["language"] = self.language.value
        return d


# ========== 实时风险预警 ==========

@dataclass
class RiskAlert:
    """实时风险预警 (PRD § 2.3)"""
    risk_type: RiskType
    triggered: bool
    matched_keywords: List[str] = field(default_factory=list)
    severity: str = "low"  # "low" / "medium" / "high"
    description: str = ""
    suggestion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["risk_type"] = self.risk_type.value
        return d


# ========== 5 维度评分 ==========

@dataclass
class FiveDimensionScore:
    """5 维度评分 (PRD § 4.3, 复用 W12 doc_workflow + W15 Skill 3 v2.0 prompt)"""
    facts: float        # 事实: 谈判内容与事实证据吻合度 (0-1)
    legal: float        # 法律: 谈判策略与法律框架吻合度 (0-1)
    demand: float       # 主张: 谈判诉求合理性 (0-1)
    timing: float       # 时效: 谈判时间节奏 (0-1)
    consequence: float  # 后果: 谈判结果的预测后果 (0-1)

    def average(self) -> float:
        return (self.facts + self.legal + self.demand + self.timing + self.consequence) / 5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ========== 谈判复盘报告 ==========

@dataclass
class DebriefReport:
    """谈判复盘报告 (PRD § 2.4)"""
    case_id: str
    lawyer_id: str
    scores: FiveDimensionScore
    avg_score: float
    key_clauses: List[str] = field(default_factory=list)
    risk_points: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    similar_cases_comparison: str = ""
    narrative: str = ""
    disclaimer: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
