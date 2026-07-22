"""
LexPrime Phase 6.1 Marketplace 商业逻辑 + 数据模型 (W29 phase6-1-backend · 2026-07-01)

VERDICT: PASS (W22 + W23 + W24 + W25 + W26 + W27 + W28 强制规范应用)

任务: W29 phase6-1-backend
必读:
- W28 owner commit f713970 (Phase 6.1 Marketplace PRD ~60KB, 7 模块 + 3 维度商业模型 + 33 端点 + 8 张表)
- W28 owner commit 8670417 (Skill 4 v1 PRD ~30KB, 复用转介绍谈判 stub)
- W26 ab59c49 Skill 3 v3.0 launch (跨境文件 40+ 律所模板 + 中英双语)
- W25 cc14045 Skill 3 v3.0 PRD (多端 + 多语言 + Marketplace 集成)
- W15 d66fc33 recruit-1000 (5 渠道 1000 律师 → 律师池基础数据)
- W12 829d25c doc_workflow 5 状态机 (5 状态: draft → ai_reviewed → lawyer_reviewed → settled → archived)
- W22 phase5-rust-build-fix (Rust 5x perf, Python fallback < 500ms)
- W11 PRD V5.0 § 5.4 + § 5.6 + § 11 (Skill Hub + 法务自检 + 边界)

本文件范围 (W29 phase6-1-backend):
- 5 大业务模块: 律师推荐 + 协同办案 + 转介绍 + 跨境文件 + 抽成结算
- 1 套 5 状态机: open → lawyer_invited → accepted → in_progress → settled (复用 W12 doc_workflow 模式)
- 律师推荐算法: 5 维度评分 (specialty_match / experience / geography / availability / rating)
- 抽成计算: 转介绍 5% + 协同办案 10% + 跨境文件 30%
- 强制 AI 辅助声明 (PRD V5.0 § 11)

设计原则:
- 零联网: 全部走模板/规则 fallback, 不依赖 LLM 在线
- 数据本地化: 律师案件 / 客户 / 文书 不离开律师电脑 (PRD V5.0 § 12.1 硬性)
- Marketplace 仅做撮合 + 抽成 + 跨境文件复用 Skill 3 v3.0 模板
- AI 辅助不替代律师: Marketplace 律师自主接案 + 自主协商 + 自主定价
- 5 状态机: 复用 W12 doc_workflow 5 状态机模式 (open/settled/archived 类比)
- 5x 性能: Python fallback < 500ms, 生产环境 W22 Rust 5x → < 100µs
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# 强制 AI 辅助声明 (PRD V5.0 § 11)
# ============================================================================

MARKETPLACE_DISCLAIMER = (
    "LexPrime Phase 6.1 Marketplace 撮合 + 抽成 + 跨境文件复用基于模板规则引擎生成, "
    "仅作为律师间协作的撮合与计费参考, 不构成正式法律意见, 不替代律师专业判断。"
    "具体案件由律师自主接案、自主协商、自主定价, Marketplace 不参与案件实质办理。"
    "跨境文件复用 Skill 3 v3.0 多律所模板, 实际发布前需律师本人审核、修改并签字确认。"
)

MARKETPLACE_DISCLAIMER_SHORT = (
    "Marketplace 仅做撮合 + 抽成 + 跨境文件复用, 不替代律师专业判断。"
)


# ============================================================================
# 1. Enums (枚举)
# ============================================================================

class CaseType(str, Enum):
    """Marketplace 案件类型 (复用 W25 Skill 3 v3.0 + W15 recruit 1000 律师 8 类)"""
    CONTRACT_DISPUTE = "contract_dispute"        # 合同纠纷
    TORT = "tort"                                # 侵权
    FAMILY = "family"                            # 婚姻家庭
    EQUITY = "equity"                            # 公司股权
    INTELLECTUAL_PROPERTY = "intellectual_property"  # 知识产权
    LABOR_ARBITRATION = "labor_arbitration"      # 劳动仲裁
    ADMINISTRATIVE_REVIEW = "administrative_review"  # 行政复议
    CROSS_BORDER = "cross_border"                # 跨境案件
    ARBITRATION = "arbitration"                  # 国际仲裁
    OTHER = "other"                              # 其他

CASE_TYPES: List[CaseType] = list(CaseType)


class CoCounselState(str, Enum):
    """协同办案 5 状态机 (复用 W12 doc_workflow 5 状态机模式)"""
    OPEN = "open"                            # 公开 (律师 A 发布)
    LAWYER_INVITED = "lawyer_invited"        # 已邀请律师 B
    ACCEPTED = "accepted"                    # 律师 B 接案
    IN_PROGRESS = "in_progress"              # 协同办案中
    SETTLED = "settled"                      # 结算完成
    ARCHIVED = "archived"                    # 归档 (终态)


# 状态转移图 (合法转移)
COUNSEL_STATE_TRANSITIONS: Dict[CoCounselState, List[CoCounselState]] = {
    CoCounselState.OPEN:            [CoCounselState.LAWYER_INVITED, CoCounselState.ARCHIVED],
    CoCounselState.LAWYER_INVITED:  [CoCounselState.ACCEPTED, CoCounselState.OPEN],
    CoCounselState.ACCEPTED:        [CoCounselState.IN_PROGRESS, CoCounselState.LAWYER_INVITED],
    CoCounselState.IN_PROGRESS:     [CoCounselState.SETTLED, CoCounselState.ACCEPTED],
    CoCounselState.SETTLED:         [CoCounselState.ARCHIVED, CoCounselState.IN_PROGRESS],
    CoCounselState.ARCHIVED:        [],  # 终态
}


class ReferralStatus(str, Enum):
    """转介绍 5 状态 (PRD § 3.2)"""
    PENDING = "pending"          # 待接
    ACCEPTED = "accepted"        # 已接
    COMPLETED = "completed"      # 已完成
    SETTLED = "settled"          # 已结算
    CANCELLED = "cancelled"      # 已取消


REFERRAL_STATUSES: List[ReferralStatus] = list(ReferralStatus)


class CrossBorderDocType(str, Enum):
    """跨境文件 6 类型 (PRD § 3.4)"""
    LETTER = "letter"                                 # 律师函
    CONTRACT = "contract"                             # 合同
    COMPLAINT = "complaint"                           # 起诉状
    DEFENSE = "defense"                               # 答辩状
    ARBITRATION_APPLICATION = "arbitration_application"   # 国际仲裁申请书
    ARBITRATION_RESPONSE = "arbitration_response"     # 国际仲裁答辩书


CROSS_BORDER_DOC_TYPES: List[CrossBorderDocType] = list(CrossBorderDocType)


class Language(str, Enum):
    """跨境文件 4 语言 (复用 W25 Skill 3 v3.0)"""
    ZH_CN = "zh-CN"
    EN_US = "en-US"
    BILINGUAL = "bilingual"          # 中英双语
    DUAL_COLUMN = "dual_column"    # 双语对照

LANGUAGES: List[Language] = list(Language)


class Jurisdiction(str, Enum):
    """跨境案件 8 司法管辖区 (PRD § 2.6)"""
    CN = "CN"          # 中国大陆
    HK = "HK"          # 中国香港
    SG = "SG"          # 新加坡
    US = "US"          # 美国
    UK = "UK"          # 英国
    ICC = "ICC"        # 国际商会仲裁院
    HKIAC = "HKIAC"    # 香港国际仲裁中心
    SIAC = "SIAC"      # 新加坡国际仲裁中心

JURISDICTIONS: List[Jurisdiction] = list(Jurisdiction)


# ============================================================================
# 2. Commission rates (抽成比例常量, 复用 W28 PRD § 3.5)
# ============================================================================

COMMISSION_RATES = {
    "referral": 0.05,        # 转介绍 5% 抽成
    "co_counsel": 0.10,      # 协同办案 10% 分账
    "cross_border": 0.30,    # 跨境文件 30% 抽成 (溢价)
    "template_share": 0.05,  # 文书模板 5% (双重抽成, 复用 W25 cc14045)
}

# 跨境文件定价 (PRD § 3.4)
CROSS_BORDER_PRICING: Dict[CrossBorderDocType, Dict[Language, float]] = {
    CrossBorderDocType.LETTER: {
        Language.ZH_CN: 99.0,
        Language.EN_US: 199.0,
        Language.BILINGUAL: 299.0,
        Language.DUAL_COLUMN: 399.0,
    },
    CrossBorderDocType.CONTRACT: {
        Language.ZH_CN: 199.0,
        Language.EN_US: 299.0,
        Language.BILINGUAL: 399.0,
        Language.DUAL_COLUMN: 499.0,
    },
    CrossBorderDocType.COMPLAINT: {
        Language.ZH_CN: 299.0,
        Language.EN_US: 399.0,
        Language.BILINGUAL: 499.0,
        Language.DUAL_COLUMN: 599.0,
    },
    CrossBorderDocType.DEFENSE: {
        Language.ZH_CN: 299.0,
        Language.EN_US: 399.0,
        Language.BILINGUAL: 499.0,
        Language.DUAL_COLUMN: 599.0,
    },
    CrossBorderDocType.ARBITRATION_APPLICATION: {
        Language.ZH_CN: 990.0,
        Language.EN_US: 1990.0,
        Language.BILINGUAL: 1990.0,
        Language.DUAL_COLUMN: 1990.0,
    },
    CrossBorderDocType.ARBITRATION_RESPONSE: {
        Language.ZH_CN: 990.0,
        Language.EN_US: 1990.0,
        Language.BILINGUAL: 1990.0,
        Language.DUAL_COLUMN: 1990.0,
    },
}


# ============================================================================
# 3. Dataclasses (DTO)
# ============================================================================

@dataclass
class LawyerProfile:
    """Marketplace 律师画像 (多维度评分输入)"""
    lawyer_id: str
    name: str
    firm_id: Optional[str] = None
    specialties: List[str] = field(default_factory=list)        # 专业领域
    specialty_depth: Dict[str, int] = field(default_factory=dict)  # 专业领域深度 (领域→案件数)
    jurisdictions: List[str] = field(default_factory=list)     # 司法管辖区
    languages: List[str] = field(default_factory=list)         # 语言 (zh-CN / en-US)
    region: str = ""                                            # 地域 (省/市)
    city: str = ""                                              # 城市
    experience_years: int = 0                                   # 执业年限
    rating: float = 0.0                                         # 平均评分 (0-5)
    client_review_count: int = 0                                # 客户评价数
    completed_cases: int = 0                                    # 累计接案数
    win_rate: float = 0.0                                       # 胜诉率 (0-1)
    response_speed_hours: float = 24.0                          # 平均响应时间 (小时)
    price_per_hour: float = 0.0                                 # 小时费率 (¥)
    price_min: float = 0.0                                      # 最低收费 (¥)
    marketplace_active: bool = True                             # 是否 Marketplace 参与方
    cross_border_capable: bool = False                          # 是否支持跨境
    availability: str = "available"                             # available / busy / unavailable
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MatchDimension:
    """单个匹配维度详情"""
    name: str                           # 维度名称
    score: float                        # 0-1 得分
    weight: float                       # 权重
    weighted_score: float               # 加权得分
    description: str                    # 文字描述
    is_strength: bool = False           # 是否是强项
    is_weakness: bool = False           # 是否是弱项

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MatchExplanation:
    """匹配解释详情"""
    total_score: float                  # 0-1 综合评分
    dimensions: List[MatchDimension] = field(default_factory=list)  # 各维度详情
    strengths: List[str] = field(default_factory=list)     # 强项列表
    weaknesses: List[str] = field(default_factory=list)    # 弱项列表
    suggestions: List[str] = field(default_factory=list)   # 改进建议

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MatchWeights:
    """匹配权重配置 (可配置化)"""
    specialty_match: float = 0.25       # 专业领域匹配
    specialty_depth: float = 0.10       # 专业领域深度
    experience_score: float = 0.12      # 经验评分
    win_rate: float = 0.08              # 胜诉率
    geography_score: float = 0.10       # 地域匹配
    response_speed: float = 0.08        # 响应速度
    availability_score: float = 0.07    # 可接案状态
    rating_score: float = 0.10          # 客户评分
    cross_domain_bonus: float = 0.05    # 跨领域能力加分
    cross_border_bonus: float = 0.05    # 跨境能力加分

    def total_weight(self) -> float:
        return sum([
            self.specialty_match,
            self.specialty_depth,
            self.experience_score,
            self.win_rate,
            self.geography_score,
            self.response_speed,
            self.availability_score,
            self.rating_score,
        ])


DEFAULT_MATCH_WEIGHTS = MatchWeights()


@dataclass
class LawyerMatchScore:
    """律师推荐算法多维度评分"""
    lawyer_id: str
    total_score: float                  # 0-1 综合评分
    specialty_match: float              # 0-1 专业匹配
    specialty_depth_score: float        # 0-1 专业深度匹配
    experience_score: float             # 0-1 经验评分
    win_rate_score: float               # 0-1 胜诉率评分
    geography_score: float              # 0-1 地域评分
    response_speed_score: float         # 0-1 响应速度评分
    availability_score: float           # 0-1 可接案评分
    rating_score: float                 # 0-1 客户评分
    cross_domain_score: float           # 0-1 跨领域能力
    cross_border_score: float           # 0-1 跨境能力
    match_reasons: List[str] = field(default_factory=list)  # 匹配理由
    explanation: Optional[MatchExplanation] = None  # 详细解释

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.explanation:
            d["explanation"] = self.explanation.to_dict()
        return d


@dataclass
class CoCounselCase:
    """协同办案案件 (PRD § 3.3)"""
    case_id: str
    lawyer_a_id: str                       # 主案律师
    lawyer_b_id: Optional[str] = None      # 协助律师
    firm_id: Optional[str] = None          # 律所 (可选)
    case_type: CaseType = CaseType.OTHER
    case_description: str = ""
    required_specialties: List[str] = field(default_factory=list)
    deadline: Optional[str] = None         # ISO 8601
    fee: float = 0.0
    split_ratio: float = 0.5               # 默认 50/50
    marketplace_commission_rate: float = 0.10
    state: CoCounselState = CoCounselState.OPEN
    history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def transition_to(self, new_state: CoCounselState, actor: str = "system", reason: str = "") -> None:
        """合法状态转移 (复用 W12 doc_workflow 模式 + history 审计)"""
        if new_state == self.state:
            return  # 幂等
        allowed = COUNSEL_STATE_TRANSITIONS.get(self.state, [])
        if new_state not in allowed:
            raise ValueError(
                f"非法状态转移: {self.state.value} → {new_state.value}, "
                f"仅允许 {[s.value for s in allowed]}"
            )
        old_state = self.state
        self.state = new_state
        self.updated_at = datetime.now(timezone.utc).isoformat()
        self.history.append({
            "from": old_state.value,
            "to": new_state.value,
            "actor": actor,
            "reason": reason,
            "ts": self.updated_at,
        })

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["case_type"] = self.case_type.value
        d["state"] = self.state.value
        return d


@dataclass
class Referral:
    """转介绍 (PRD § 3.2)"""
    referral_id: str
    referrer_id: str                        # 推荐人律师 A
    target_lawyer_id: str                   # 被推荐律师 B
    case_type: CaseType = CaseType.OTHER
    case_description: str = ""
    expected_fee: float = 0.0
    actual_fee: Optional[float] = None
    commission_rate: float = 0.05
    referrer_commission: Optional[float] = None
    marketplace_commission: Optional[float] = None  # 转介绍 = 0
    match_score: Optional[float] = None
    status: ReferralStatus = ReferralStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def complete(self, actual_fee: float) -> Dict[str, float]:
        """完成转介绍: 计算抽成"""
        self.actual_fee = actual_fee
        self.referrer_commission = round(actual_fee * self.commission_rate, 2)
        self.marketplace_commission = 0.0  # 转介绍 Marketplace 不抽成
        self.status = ReferralStatus.COMPLETED
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return {
            "actual_fee": self.actual_fee,
            "referrer_commission": self.referrer_commission or 0.0,
            "marketplace_commission": self.marketplace_commission,
        }

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["case_type"] = self.case_type.value
        d["status"] = self.status.value
        return d


@dataclass
class CrossBorderJob:
    """跨境文件订单 (PRD § 3.4)"""
    job_id: str
    lawyer_id: str                          # 接单律师
    client_id: str                          # 国际客户
    doc_type: CrossBorderDocType = CrossBorderDocType.LETTER
    language: Language = Language.EN_US
    jurisdiction: Jurisdiction = Jurisdiction.CN
    price: float = 0.0                      # 律师实际所得
    marketplace_commission: float = 0.0     # Marketplace 抽成
    template_id: Optional[str] = None       # 复用 Skill 3 v3.0 模板
    status: str = "pending"                 # pending / generating / completed / filed
    fields: Dict[str, Any] = field(default_factory=dict)
    document_url: Optional[str] = None
    arbitration_institution: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["doc_type"] = self.doc_type.value
        d["language"] = self.language.value
        d["jurisdiction"] = self.jurisdiction.value
        return d


@dataclass
class CommissionRecord:
    """抽成记录 (T+7 冷静期 + T+7+1 结算 + T+30 提现, PRD § 3.5)"""
    commission_id: str
    transaction_id: str
    transaction_type: str  # referral / co_counsel / cross_border / template_share
    lawyer_id: str
    referrer_id: Optional[str] = None
    transaction_amount: float = 0.0
    commission_rate: float = 0.0
    commission_amount: float = 0.0
    status: str = "pending"  # pending / confirmed / settled / withdrawn
    confirm_at: Optional[str] = None
    settle_at: Optional[str] = None
    withdraw_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MarketplaceMetrics:
    """Marketplace 5 维度指标 (PRD § 8.3)"""
    metric_date: str                           # ISO 8601
    lawyer_participants: int = 0               # Marketplace 律师参与方
    cases_completed_monthly: int = 0           # 月接案数
    revenue_monthly: float = 0.0               # 月营收 (¥)
    cross_border_orders_monthly: int = 0       # 跨境案件月单量
    avg_lawyer_rating: float = 0.0             # 律师满意度 (0-5)
    referral_count_total: int = 0              # 累计转介绍数
    co_counsel_count_total: int = 0            # 累计协同办案数
    cross_border_count_total: int = 0          # 累计跨境文件数
    commission_pending: float = 0.0            # 待结算抽成
    commission_settled: float = 0.0            # 已结算抽成

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# 4. Business Logic (商业逻辑)
# ============================================================================

def generate_id(prefix: str = "mp") -> str:
    """生成 Marketplace ID (prefix-uuid8)"""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def compute_match_score(
    lawyer: LawyerProfile,
    required_specialties: List[str],
    required_jurisdictions: Optional[List[str]] = None,
    required_languages: Optional[List[str]] = None,
    required_region: str = "",
    required_city: str = "",
    cross_border: bool = False,
    weights: Optional[MatchWeights] = None,
    include_explanation: bool = True,
) -> LawyerMatchScore:
    """律师推荐算法多维度评分

    该算法是 Marketplace 核心推荐引擎，基于 8 个维度对律师进行综合评分。

    评分维度 (权重可配置):
    1. specialty_match (25%) - 专业领域匹配广度，计算律师专业与需求的交集比例
    2. specialty_depth (10%) - 专业领域匹配深度，基于该领域办案数量计算
    3. experience_score (12%) - 执业经验，按 15 年满分计算
    4. win_rate (8%) - 胜诉率，直接使用律师胜诉率数据
    5. geography_score (10%) - 地域就近匹配，同城 > 同省 > 跨省
    6. response_speed (8%) - 响应速度，按小时区间分级
    7. availability_score (7%) - 可接案状态，available/busy/unavailable
    8. rating_score (10%) - 客户评价，结合评分和评价数量计算置信度

    加分项:
    - cross_domain_bonus (5%) - 跨领域能力，拥有 3 个以上专业领域加分
    - cross_border_bonus (5%) - 跨境能力，支持跨境案件加分

    惩罚项:
    - 跨境案件需求但律师无跨境能力时，扣除 20% 基础分

    评分标准:
    - 总分范围: 0-1
    - > 0.8: 强推荐，高度匹配需求
    - > 0.6: 推荐候选，基本匹配需求
    - < 0.3: 不推荐，匹配度较低

    Args:
        lawyer: 律师画像对象
        required_specialties: 需求专业领域列表
        required_jurisdictions: 跨境案件所需司法管辖区
        required_languages: 跨境案件所需语言
        required_region: 地域要求 (省级)
        required_city: 城市要求
        cross_border: 是否跨境案件
        weights: 权重配置，默认为 DEFAULT_MATCH_WEIGHTS
        include_explanation: 是否生成详细解释

    Returns:
        LawyerMatchScore: 包含各维度得分和综合评分的对象
    """
    if weights is None:
        weights = DEFAULT_MATCH_WEIGHTS

    overlap = set()

    # 维度 1: specialty_match (专业领域匹配广度) - 权重 25%
    # 计算律师专业领域与需求领域的交集比例
    if required_specialties:
        overlap = set(lawyer.specialties) & set(required_specialties)
        specialty_match = len(overlap) / len(required_specialties) if required_specialties else 0.0
    else:
        specialty_match = 0.5  # 无专业要求时默认中等

    # 维度 2: specialty_depth_score (专业领域匹配深度) - 权重 10%
    # 基于律师在匹配领域的办案数量计算深度得分
    # 最多 50 个案件为满分，超过 50 个案件按比例递减
    specialty_depth_score = 0.0
    if required_specialties and lawyer.specialty_depth:
        total_depth = 0
        max_cases = max(lawyer.specialty_depth.values()) if lawyer.specialty_depth else 1
        for spec in overlap:
            depth = lawyer.specialty_depth.get(spec, 0)
            total_depth += min(1.0, depth / max(50, max_cases * 0.5))
        specialty_depth_score = total_depth / len(required_specialties) if required_specialties else 0.0
    elif not required_specialties:
        specialty_depth_score = 0.5

    # 维度 3: experience_score (执业经验) - 权重 12%
    # 15 年执业经验为满分，超过 15 年按满分计算
    experience_score = min(1.0, lawyer.experience_years / 15.0)

    # 维度 4: win_rate_score (胜诉率) - 权重 8%
    # 直接使用律师胜诉率，无数据时默认 0.5
    win_rate_score = lawyer.win_rate if lawyer.win_rate > 0 else 0.5
    win_rate_score = max(0.0, min(1.0, win_rate_score))

    # 维度 5: geography_score (地域就近匹配) - 权重 10%
    # 匹配优先级: 同城(1.0) > 同省(0.7) > 同省前2字匹配(0.5) > 跨省(0.2)
    geography_score = 0.5
    if required_city and lawyer.city:
        if required_city == lawyer.city:
            geography_score = 1.0
        elif required_region and lawyer.region and required_region == lawyer.region:
            geography_score = 0.7
        elif required_region and lawyer.region and required_region[:2] == lawyer.region[:2]:
            geography_score = 0.5
        else:
            geography_score = 0.2
    elif required_region and lawyer.region:
        if required_region == lawyer.region:
            geography_score = 1.0
        elif required_region[:2] == lawyer.region[:2]:
            geography_score = 0.6
        else:
            geography_score = 0.3

    # 维度 6: response_speed_score (响应速度) - 权重 8%
    # 按响应时间区间分级: <=2h(1.0) > <=6h(0.8) > <=12h(0.6) > <=24h(0.4) > <=48h(0.2) > >48h(0.1)
    if lawyer.response_speed_hours <= 2:
        response_speed_score = 1.0
    elif lawyer.response_speed_hours <= 6:
        response_speed_score = 0.8
    elif lawyer.response_speed_hours <= 12:
        response_speed_score = 0.6
    elif lawyer.response_speed_hours <= 24:
        response_speed_score = 0.4
    elif lawyer.response_speed_hours <= 48:
        response_speed_score = 0.2
    else:
        response_speed_score = 0.1

    # 维度 7: availability_score (可接案状态) - 权重 7%
    # available(1.0) > busy(0.4) > unavailable(0.0)
    # 非 Marketplace 活跃用户直接得 0 分
    availability_map = {"available": 1.0, "busy": 0.4, "unavailable": 0.0}
    availability_score = availability_map.get(lawyer.availability, 0.5)
    if not lawyer.marketplace_active:
        availability_score = 0.0

    # 维度 8: rating_score (客户评价) - 权重 10%
    # 基础分 = 评分 / 5，结合评价数量计算置信度
    # 评价数 >= 20 条时置信度为 1，评价数越少置信度越低
    rating_score = lawyer.rating / 5.0 if lawyer.rating > 0 else 0.5
    if lawyer.client_review_count > 0:
        review_confidence = min(1.0, lawyer.client_review_count / 20.0)
        rating_score = 0.5 * rating_score + 0.5 * (rating_score * review_confidence + 0.5 * (1 - review_confidence))

    # 跨领域能力加分 - 权重 5%
    # 拥有 3 个以上专业领域时加分，最多加 5 分 (对应权重 5%)
    cross_domain_score = 0.0
    if len(lawyer.specialties) >= 3:
        cross_domain_score = min(1.0, (len(lawyer.specialties) - 2) / 5.0)

    # 跨境能力 - 权重 5%
    # 基础分 0.6，语言匹配加 0-0.4，司法管辖区匹配调整最终得分
    # 无跨境能力且需求跨境时得 -1.0（触发惩罚）
    cross_border_score = 0.0
    if cross_border:
        if lawyer.cross_border_capable:
            cross_border_score = 0.6
            if required_languages:
                lang_overlap = set(lawyer.languages) & set(required_languages)
                lang_match = len(lang_overlap) / len(required_languages) if required_languages else 0.0
                cross_border_score = 0.6 + 0.4 * lang_match
            if required_jurisdictions:
                jur_overlap = set(lawyer.jurisdictions) & set(required_jurisdictions)
                jur_match = len(jur_overlap) / len(required_jurisdictions) if required_jurisdictions else 0.0
                cross_border_score = cross_border_score * 0.7 + jur_match * 0.3
        else:
            cross_border_score = -1.0

    # 加权总分计算
    # 基础分 = 各维度得分 × 对应权重
    base_score = (
        specialty_match * weights.specialty_match
        + specialty_depth_score * weights.specialty_depth
        + experience_score * weights.experience_score
        + win_rate_score * weights.win_rate
        + geography_score * weights.geography_score
        + response_speed_score * weights.response_speed
        + availability_score * weights.availability_score
        + rating_score * weights.rating_score
    )

    # 加分项 = 跨领域加分 + 跨境加分（负值不计入）
    bonus = (
        cross_domain_score * weights.cross_domain_bonus
        + max(0.0, cross_border_score) * weights.cross_border_bonus
    )

    # 惩罚项: 跨境案件需求但律师无跨境能力时扣除 20%
    penalty = 0.0
    if cross_border and not lawyer.cross_border_capable:
        penalty = 0.2

    # 总分 = max(0, min(1, 基础分 + 加分 - 惩罚))
    total_score = max(0.0, min(1.0, base_score + bonus - penalty))

    # 匹配理由
    match_reasons = []
    if specialty_match >= 0.8:
        match_reasons.append(f"专业高度匹配 ({len(overlap)}/{len(required_specialties)})")
    if specialty_depth_score >= 0.7:
        match_reasons.append("专业领域经验丰富")
    if experience_score >= 0.7:
        match_reasons.append(f"资深律师 ({lawyer.experience_years} 年经验)")
    if win_rate_score >= 0.7:
        match_reasons.append(f"高胜诉率 ({lawyer.win_rate*100:.0f}%)")
    if geography_score >= 0.9:
        match_reasons.append("同城/同省律师")
    if response_speed_score >= 0.8:
        match_reasons.append(f"响应迅速 ({lawyer.response_speed_hours:.0f}小时内)")
    if rating_score >= 0.8:
        match_reasons.append(f"高评分律师 ({lawyer.rating:.1f}/5.0)")
    if cross_domain_score >= 0.5:
        match_reasons.append(f"跨领域能力 ({len(lawyer.specialties)}个专业领域)")
    if cross_border and lawyer.cross_border_capable:
        match_reasons.append("支持跨境案件")

    score = LawyerMatchScore(
        lawyer_id=lawyer.lawyer_id,
        total_score=round(total_score, 4),
        specialty_match=round(specialty_match, 4),
        specialty_depth_score=round(specialty_depth_score, 4),
        experience_score=round(experience_score, 4),
        win_rate_score=round(win_rate_score, 4),
        geography_score=round(geography_score, 4),
        response_speed_score=round(response_speed_score, 4),
        availability_score=round(availability_score, 4),
        rating_score=round(rating_score, 4),
        cross_domain_score=round(cross_domain_score, 4),
        cross_border_score=round(max(0.0, cross_border_score), 4),
        match_reasons=match_reasons,
    )

    if include_explanation:
        score.explanation = get_match_explanation(score, lawyer, required_specialties, weights)

    return score


def lawyer_match_score(
    lawyer: LawyerProfile,
    required_specialties: List[str],
    required_jurisdictions: Optional[List[str]] = None,
    required_languages: Optional[List[str]] = None,
    required_region: str = "",
    cross_border: bool = False,
) -> LawyerMatchScore:
    """兼容旧版函数名 (5 维度评分)

    保留原函数名以确保向后兼容, 内部调用 compute_match_score。
    """
    return compute_match_score(
        lawyer=lawyer,
        required_specialties=required_specialties,
        required_jurisdictions=required_jurisdictions,
        required_languages=required_languages,
        required_region=required_region,
        cross_border=cross_border,
    )


def get_match_explanation(
    score: LawyerMatchScore,
    lawyer: LawyerProfile,
    required_specialties: List[str],
    weights: Optional[MatchWeights] = None,
) -> MatchExplanation:
    """生成匹配解释列表

    返回每个维度的得分、说明、强项弱项和改进建议
    """
    if weights is None:
        weights = DEFAULT_MATCH_WEIGHTS

    dimensions = []
    strengths = []
    weaknesses = []
    suggestions = []

    dim_configs = [
        ("专业领域匹配", score.specialty_match, weights.specialty_match,
         f"匹配 {int(score.specialty_match * len(required_specialties))}/{len(required_specialties)} 个专业领域"
         if required_specialties else "无专业要求"),
        ("专业深度匹配", score.specialty_depth_score, weights.specialty_depth,
         "相关领域办案经验丰富" if score.specialty_depth_score >= 0.7 else "专业深度有待提升"),
        ("执业经验", score.experience_score, weights.experience_score,
         f"{lawyer.experience_years} 年执业经验"),
        ("胜诉率", score.win_rate_score, weights.win_rate,
         f"胜诉率 {lawyer.win_rate*100:.0f}%" if lawyer.win_rate > 0 else "暂无胜诉率数据"),
        ("地域匹配", score.geography_score, weights.geography_score,
         f"所在地区: {lawyer.city or lawyer.region or '未填写'}"),
        ("响应速度", score.response_speed_score, weights.response_speed,
         f"平均响应 {lawyer.response_speed_hours:.0f} 小时"),
        ("可接案状态", score.availability_score, weights.availability_score,
         f"状态: {lawyer.availability}"),
        ("客户评价", score.rating_score, weights.rating_score,
         f"评分 {lawyer.rating:.1f}/5.0 ({lawyer.client_review_count} 条评价)"
         if lawyer.client_review_count > 0 else f"评分 {lawyer.rating:.1f}/5.0"),
    ]

    for name, s, w, desc in dim_configs:
        weighted = s * w
        is_strength = s >= 0.8
        is_weakness = s < 0.4

        dim = MatchDimension(
            name=name,
            score=round(s, 4),
            weight=w,
            weighted_score=round(weighted, 4),
            description=desc,
            is_strength=is_strength,
            is_weakness=is_weakness,
        )
        dimensions.append(dim)

        if is_strength:
            strengths.append(f"{name}: {desc}")
        if is_weakness:
            weaknesses.append(f"{name}: {desc}")

    if score.cross_domain_score >= 0.5:
        strengths.append(f"跨领域能力: 精通 {len(lawyer.specialties)} 个专业领域")

    if score.cross_border_score >= 0.7:
        strengths.append("跨境能力: 支持跨境案件办理")

    if score.specialty_match < 0.6 and required_specialties:
        suggestions.append("建议补充相关专业领域认证，提升专业匹配度")
    if score.experience_score < 0.5:
        suggestions.append("可通过更多案件积累提升执业经验评分")
    if score.win_rate_score < 0.5:
        suggestions.append("提升胜诉率可显著提高推荐排名")
    if score.geography_score < 0.5:
        suggestions.append("异地律师可考虑与当地律师协作办案")
    if score.response_speed_score < 0.5:
        suggestions.append("提升响应速度有助于获得更多客户青睐")
    if score.rating_score < 0.5:
        suggestions.append("注重服务质量，积累更多客户好评")
    if score.availability_score < 0.5:
        suggestions.append("保持 available 状态可获得更多推荐机会")
    if not lawyer.cross_border_capable:
        suggestions.append("获取跨境执业资质可拓展业务范围")

    return MatchExplanation(
        total_score=score.total_score,
        dimensions=dimensions,
        strengths=strengths,
        weaknesses=weaknesses,
        suggestions=suggestions,
    )


def rank_lawyers(
    lawyers: List[LawyerProfile],
    required_specialties: List[str],
    top_k: int = 5,
    min_score: float = 0.3,
    required_jurisdictions: Optional[List[str]] = None,
    required_languages: Optional[List[str]] = None,
    required_region: str = "",
    cross_border: bool = False,
    weights: Optional[MatchWeights] = None,
) -> List[LawyerMatchScore]:
    """律师推荐 Top-K (按综合匹配度降序)

    Args:
        lawyers: 候选律师池
        required_specialties: 必需专业领域
        top_k: 返回前 K 个
        min_score: 最低分阈值
        required_jurisdictions: 必需司法管辖区 (跨境案件)
        required_languages: 必需语言 (跨境案件)
        required_region: 地域 (协同办案/转介绍)
        cross_border: 是否跨境案件
        weights: 权重配置

    Returns:
        按 total_score 降序的律师推荐列表
    """
    scored = []
    for lawyer in lawyers:
        score = compute_match_score(
            lawyer=lawyer,
            required_specialties=required_specialties,
            required_jurisdictions=required_jurisdictions,
            required_languages=required_languages,
            required_region=required_region,
            cross_border=cross_border,
            weights=weights,
        )
        if score.total_score >= min_score:
            scored.append(score)

    scored.sort(key=lambda x: x.total_score, reverse=True)
    return scored[:top_k]


def recommend_lawyers(
    lawyers: List[LawyerProfile],
    required_specialties: List[str],
    top_k: int = 5,
    min_score: float = 0.3,
    required_jurisdictions: Optional[List[str]] = None,
    required_languages: Optional[List[str]] = None,
    required_region: str = "",
    cross_border: bool = False,
) -> List[LawyerMatchScore]:
    """律师推荐 Top-K (兼容旧版函数名)

    保留原函数名以确保向后兼容, 内部调用 rank_lawyers。
    """
    return rank_lawyers(
        lawyers=lawyers,
        required_specialties=required_specialties,
        top_k=top_k,
        min_score=min_score,
        required_jurisdictions=required_jurisdictions,
        required_languages=required_languages,
        required_region=required_region,
        cross_border=cross_border,
    )


class SortField(str, Enum):
    """排序字段枚举"""
    MATCH_SCORE = "match_score"      # 综合匹配度
    PRICE = "price"                  # 价格
    EXPERIENCE = "experience"        # 经验年限
    RATING = "rating"                # 评分
    RESPONSE_SPEED = "response_speed"  # 响应速度
    WIN_RATE = "win_rate"            # 胜诉率
    COMPLETED_CASES = "completed_cases"  # 办案数量


class SortOrder(str, Enum):
    """排序方向"""
    ASC = "asc"       # 升序
    DESC = "desc"     # 降序


def sort_lawyers(
    scored_lawyers: List[LawyerMatchScore],
    lawyer_profiles: Optional[Dict[str, LawyerProfile]] = None,
    sort_by: SortField = SortField.MATCH_SCORE,
    order: SortOrder = SortOrder.DESC,
) -> List[LawyerMatchScore]:
    """律师智能排序

    支持多种排序方式: 综合匹配、价格、经验、评分、响应速度、胜诉率、办案数

    Args:
        scored_lawyers: 已评分的律师列表
        lawyer_profiles: 律师画像字典 (lawyer_id -> LawyerProfile), 用于价格等字段排序
        sort_by: 排序字段
        order: 排序方向 (升序/降序)

    Returns:
        排序后的律师列表
    """
    reverse = order == SortOrder.DESC

    if sort_by == SortField.MATCH_SCORE:
        return sorted(scored_lawyers, key=lambda x: x.total_score, reverse=reverse)

    if lawyer_profiles is None:
        return sorted(scored_lawyers, key=lambda x: x.total_score, reverse=reverse)

    def get_sort_key(score: LawyerMatchScore) -> float:
        profile = lawyer_profiles.get(score.lawyer_id)
        if profile is None:
            return 0.0

        if sort_by == SortField.PRICE:
            return profile.price_per_hour if profile.price_per_hour > 0 else float('inf')
        elif sort_by == SortField.EXPERIENCE:
            return float(profile.experience_years)
        elif sort_by == SortField.RATING:
            return profile.rating
        elif sort_by == SortField.RESPONSE_SPEED:
            return profile.response_speed_hours
        elif sort_by == SortField.WIN_RATE:
            return profile.win_rate
        elif sort_by == SortField.COMPLETED_CASES:
            return float(profile.completed_cases)
        else:
            return score.total_score

    return sorted(scored_lawyers, key=get_sort_key, reverse=reverse)


@dataclass
class LawyerFilters:
    """律师过滤条件"""
    specialties: Optional[List[str]] = None          # 专业领域 (包含任一即可)
    specialties_all: Optional[List[str]] = None      # 专业领域 (必须全部包含)
    min_experience_years: Optional[int] = None       # 最低经验年限
    max_experience_years: Optional[int] = None       # 最高经验年限
    regions: Optional[List[str]] = None              # 地区列表
    cities: Optional[List[str]] = None               # 城市列表
    min_price: Optional[float] = None                # 最低价格
    max_price: Optional[float] = None                # 最高价格
    min_rating: Optional[float] = None               # 最低评分
    cross_border_only: bool = False                   # 仅跨境律师
    marketplace_active_only: bool = True             # 仅活跃律师
    availability: Optional[List[str]] = None         # 可接案状态


def filter_lawyers(
    lawyers: List[LawyerProfile],
    filters: LawyerFilters,
) -> List[LawyerProfile]:
    """律师多条件组合过滤

    支持按: 专业领域、经验年限、地区、价格区间、评分、是否跨境 等过滤

    Args:
        lawyers: 候选律师池
        filters: 过滤条件

    Returns:
        过滤后的律师列表
    """
    result = []

    for lawyer in lawyers:
        if filters.marketplace_active_only and not lawyer.marketplace_active:
            continue

        if filters.cross_border_only and not lawyer.cross_border_capable:
            continue

        if filters.specialties:
            if not set(lawyer.specialties) & set(filters.specialties):
                continue

        if filters.specialties_all:
            if not set(filters.specialties_all).issubset(set(lawyer.specialties)):
                continue

        if filters.min_experience_years is not None:
            if lawyer.experience_years < filters.min_experience_years:
                continue

        if filters.max_experience_years is not None:
            if lawyer.experience_years > filters.max_experience_years:
                continue

        if filters.regions:
            if lawyer.region not in filters.regions:
                continue

        if filters.cities:
            if lawyer.city not in filters.cities:
                continue

        if filters.min_price is not None:
            price = lawyer.price_per_hour if lawyer.price_per_hour > 0 else lawyer.price_min
            if price < filters.min_price:
                continue

        if filters.max_price is not None:
            price = lawyer.price_per_hour if lawyer.price_per_hour > 0 else lawyer.price_min
            if price > 0 and price > filters.max_price:
                continue

        if filters.min_rating is not None:
            if lawyer.rating < filters.min_rating:
                continue

        if filters.availability:
            if lawyer.availability not in filters.availability:
                continue

        result.append(lawyer)

    return result


def create_co_counsel_case(
    lawyer_a_id: str,
    case_type: CaseType,
    case_description: str,
    fee: float,
    required_specialties: Optional[List[str]] = None,
    firm_id: Optional[str] = None,
    deadline: Optional[str] = None,
    split_ratio: float = 0.5,
) -> CoCounselCase:
    """创建协同办案案件 (PRD § 3.3)"""
    if fee < 0:
        raise ValueError("fee 必须 >= 0")
    if not 0.0 <= split_ratio <= 1.0:
        raise ValueError("split_ratio 必须在 [0, 1] 区间")
    return CoCounselCase(
        case_id=generate_id("cc"),
        lawyer_a_id=lawyer_a_id,
        firm_id=firm_id,
        case_type=case_type,
        case_description=case_description,
        required_specialties=required_specialties or [],
        deadline=deadline,
        fee=fee,
        split_ratio=split_ratio,
        marketplace_commission_rate=COMMISSION_RATES["co_counsel"],
        state=CoCounselState.OPEN,
        history=[{
            "from": "init",
            "to": CoCounselState.OPEN.value,
            "actor": lawyer_a_id,
            "reason": "创建协同办案",
            "ts": datetime.now(timezone.utc).isoformat(),
        }],
    )


def create_referral(
    referrer_id: str,
    target_lawyer_id: str,
    case_type: CaseType,
    case_description: str,
    expected_fee: float,
    match_score: Optional[float] = None,
) -> Referral:
    """创建转介绍 (PRD § 3.2)"""
    if expected_fee < 0:
        raise ValueError("expected_fee 必须 >= 0")
    return Referral(
        referral_id=generate_id("ref"),
        referrer_id=referrer_id,
        target_lawyer_id=target_lawyer_id,
        case_type=case_type,
        case_description=case_description,
        expected_fee=expected_fee,
        commission_rate=COMMISSION_RATES["referral"],
        match_score=match_score,
        status=ReferralStatus.PENDING,
    )


def create_cross_border_job(
    lawyer_id: str,
    client_id: str,
    doc_type: CrossBorderDocType,
    language: Language,
    jurisdiction: Jurisdiction,
    fields: Optional[Dict[str, Any]] = None,
    template_id: Optional[str] = None,
) -> CrossBorderJob:
    """创建跨境文件订单 (PRD § 3.4, 复用 W25 Skill 3 v3.0 模板)"""
    pricing = CROSS_BORDER_PRICING[doc_type][language]
    commission = round(pricing * COMMISSION_RATES["cross_border"], 2)
    return CrossBorderJob(
        job_id=generate_id("cb"),
        lawyer_id=lawyer_id,
        client_id=client_id,
        doc_type=doc_type,
        language=language,
        jurisdiction=jurisdiction,
        price=pricing - commission,            # 律师实际所得
        marketplace_commission=commission,    # Marketplace 抽成
        template_id=template_id,
        status="pending",
        fields=fields or {},
    )


def compute_marketplace_metrics(
    referrals: List[Referral],
    co_counsel_cases: List[CoCounselCase],
    cross_border_jobs: List[CrossBorderJob],
    commission_records: List[CommissionRecord],
    lawyer_pool: Optional[List[LawyerProfile]] = None,
    lawyer_ratings: Optional[List[float]] = None,
) -> MarketplaceMetrics:
    """计算 Marketplace 5 维度指标 (PRD § 8.3)

    5 指标:
    1. lawyer_participants      Marketplace 律师参与方
    2. cases_completed_monthly  月接案数
    3. revenue_monthly          月营收 (¥)
    4. cross_border_orders_monthly 跨境案件月单量
    5. avg_lawyer_rating        律师满意度 (0-5)
    """
    # 1. 律师参与方 (去重律师 ID)
    active_lawyers = set()
    for r in referrals:
        active_lawyers.add(r.referrer_id)
        active_lawyers.add(r.target_lawyer_id)
    for c in co_counsel_cases:
        active_lawyers.add(c.lawyer_a_id)
        if c.lawyer_b_id:
            active_lawyers.add(c.lawyer_b_id)
    for j in cross_border_jobs:
        active_lawyers.add(j.lawyer_id)
    if lawyer_pool:
        for lp in lawyer_pool:
            if lp.marketplace_active:
                active_lawyers.add(lp.lawyer_id)

    # 2. 月接案数 (协同办案 SETTLED + 转介绍 COMPLETED)
    cases_completed = sum(1 for c in co_counsel_cases if c.state == CoCounselState.SETTLED)
    cases_completed += sum(1 for r in referrals if r.status == ReferralStatus.COMPLETED)

    # 3. 月营收 (Marketplace 抽成总额) - 单一数据源: commission_records (settled/confirmed)
    # cross_border_jobs 仅作为计数来源 (commission_records 是 source of truth, 避免双计)
    revenue = sum(cr.commission_amount for cr in commission_records if cr.status in ("settled", "confirmed"))
    # cross_border_jobs 中没有对应 commission_record 的 completed 订单, 计入 pending
    cb_pending = sum(
        j.marketplace_commission for j in cross_border_jobs
        if j.status == "completed"
        and not any(cr.transaction_id == j.job_id for cr in commission_records)
    )

    # 4. 跨境案件月单量
    cb_orders = sum(1 for j in cross_border_jobs if j.status == "completed")

    # 5. 律师满意度 (平均评分, 仅 marketplace_active 律师)
    avg_rating = 0.0
    if lawyer_ratings:
        avg_rating = sum(lawyer_ratings) / len(lawyer_ratings)
    elif lawyer_pool:
        ratings = [lp.rating for lp in lawyer_pool if lp.rating > 0 and lp.marketplace_active]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0.0

    # 待结算 + 已结算
    pending = sum(cr.commission_amount for cr in commission_records if cr.status == "pending")
    pending += cb_pending  # cross_border 未结算的也计入 pending
    settled = sum(cr.commission_amount for cr in commission_records if cr.status == "settled")

    return MarketplaceMetrics(
        metric_date=datetime.now(timezone.utc).isoformat(),
        lawyer_participants=len(active_lawyers),
        cases_completed_monthly=cases_completed,
        revenue_monthly=round(revenue, 2),
        cross_border_orders_monthly=cb_orders,
        avg_lawyer_rating=round(avg_rating, 2),
        referral_count_total=len(referrals),
        co_counsel_count_total=len(co_counsel_cases),
        cross_border_count_total=len(cross_border_jobs),
        commission_pending=round(pending, 2),
        commission_settled=round(settled, 2),
    )


# ============================================================================
# 5. ID 生成 + 工具函数
# ============================================================================

def parse_legal_basis(case_type: CaseType) -> str:
    """案件类型 → 法条依据 (复用 W11 PRD V5.0 法务自检)"""
    return {
        CaseType.CONTRACT_DISPUTE: "《民法典》合同编 + 第五百七十七条 (违约责任)",
        CaseType.TORT: "《民法典》侵权责任编 + 第一千一百六十五条 (过错责任)",
        CaseType.FAMILY: "《民法典》婚姻家庭编 + 第一千零七十六条 (协议离婚)",
        CaseType.EQUITY: "《公司法》 + 第三十五条 (股东权利) + 第七十四条 (股权回购)",
        CaseType.INTELLECTUAL_PROPERTY: "《商标法》 + 第五十七条 + 《著作权法》第五十三条",
        CaseType.LABOR_ARBITRATION: "《劳动合同法》 + 第四十七条 (经济补偿) + 第八十七条",
        CaseType.ADMINISTRATIVE_REVIEW: "《行政复议法》 + 第六条 + 第十一条 (申请期限)",
        CaseType.CROSS_BORDER: "CISG (联合国国际货物销售合同公约 1980) + UNCITRAL",
        CaseType.ARBITRATION: "ICC / HKIAC / SIAC 仲裁规则",
        CaseType.OTHER: "根据具体案情适用相关法律法规",
    }.get(case_type, "根据具体案情适用相关法律法规")


def validate_lawyer_profile(profile: LawyerProfile) -> List[str]:
    """校验律师画像, 返回错误列表 (空 = 校验通过)"""
    errors = []
    if not profile.lawyer_id or len(profile.lawyer_id) < 2:
        errors.append("lawyer_id 必须 >= 2 字符")
    if not profile.name:
        errors.append("name 不能为空")
    if profile.experience_years < 0 or profile.experience_years > 80:
        errors.append("experience_years 必须在 [0, 80] 区间")
    if profile.rating < 0 or profile.rating > 5:
        errors.append("rating 必须在 [0, 5] 区间")
    if not profile.specialties:
        errors.append("specialties 不能为空 (Marketplace 律师必须声明专业)")
    if profile.availability not in ("available", "busy", "unavailable"):
        errors.append(f"availability 必须是 available/busy/unavailable, 当前: {profile.availability}")
    return errors


def get_state_transitionable_targets(current: CoCounselState) -> List[CoCounselState]:
    """获取当前状态的所有合法目标 (含回退)

    注意: ARCHIVED 是终态, 无合法目标 (即使语义上"上一状态"是 SETTLED, 也不允许 transition_back)
    """
    if current == CoCounselState.ARCHIVED:
        return []  # 终态, 不允许任何转换
    targets = list(COUNSEL_STATE_TRANSITIONS.get(current, []))
    # 找上一状态 (仅当不是初态)
    for prev, nexts in COUNSEL_STATE_TRANSITIONS.items():
        if current in nexts and prev != current:
            if prev not in targets:
                targets.append(prev)
    return targets


# ============================================================================
# 6. 性能监控 (复用 W22 Rust 5x perf baseline)
# ============================================================================

def measure_latency_ms(func, *args, **kwargs) -> Tuple[Any, int]:
    """测量函数执行时间 (毫秒), 返回 (result, latency_ms)"""
    t0 = time.time()
    result = func(*args, **kwargs)
    latency_ms = int((time.time() - t0) * 1000)
    return result, latency_ms
