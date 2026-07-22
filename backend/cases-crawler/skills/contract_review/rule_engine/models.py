"""
合同审查规则引擎 - 数据模型定义

定义规则、匹配结果、审查结果等核心数据结构。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict, Any, Callable, Pattern


class RuleSeverity(str, Enum):
    """规则严重程度"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    @classmethod
    def from_string(cls, value: str) -> "RuleSeverity":
        mapping = {
            "high": cls.HIGH,
            "高危": cls.HIGH,
            "medium": cls.MEDIUM,
            "中危": cls.MEDIUM,
            "low": cls.LOW,
            "低危": cls.LOW,
            "info": cls.INFO,
            "提示": cls.INFO,
        }
        return mapping.get(value.lower() if isinstance(value, str) else value, cls.INFO)

    @property
    def weight(self) -> float:
        weights = {
            RuleSeverity.HIGH: 10.0,
            RuleSeverity.MEDIUM: 5.0,
            RuleSeverity.LOW: 2.0,
            RuleSeverity.INFO: 0.5,
        }
        return weights[self]

    @property
    def display_name(self) -> str:
        names = {
            RuleSeverity.HIGH: "高危",
            RuleSeverity.MEDIUM: "中危",
            RuleSeverity.LOW: "低危",
            RuleSeverity.INFO: "提示",
        }
        return names[self]

    @property
    def color(self) -> str:
        colors = {
            RuleSeverity.HIGH: "red",
            RuleSeverity.MEDIUM: "orange",
            RuleSeverity.LOW: "yellow",
            RuleSeverity.INFO: "blue",
        }
        return colors[self]


class RuleCategory(str, Enum):
    """规则分类"""
    PARTY_QUALIFICATION = "party_qualification"
    RIGHTS_OBLIGATIONS = "rights_obligations"
    BREACH_OF_CONTRACT = "breach_of_contract"
    DISPUTE_RESOLUTION = "dispute_resolution"
    AMOUNT_DEADLINE = "amount_deadline"
    WORDING = "wording"
    LEGAL_RISK = "legal_risk"

    @property
    def display_name(self) -> str:
        names = {
            RuleCategory.PARTY_QUALIFICATION: "主体资格",
            RuleCategory.RIGHTS_OBLIGATIONS: "权利义务",
            RuleCategory.BREACH_OF_CONTRACT: "违约责任",
            RuleCategory.DISPUTE_RESOLUTION: "争议解决",
            RuleCategory.AMOUNT_DEADLINE: "金额期限",
            RuleCategory.WORDING: "文字表述",
            RuleCategory.LEGAL_RISK: "法律风险",
        }
        return names[self]


class RiskLevel(str, Enum):
    """整体风险等级"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def display_name(self) -> str:
        names = {
            RiskLevel.SAFE: "安全",
            RiskLevel.LOW: "低风险",
            RiskLevel.MEDIUM: "中风险",
            RiskLevel.HIGH: "高风险",
        }
        return names[self]

    @property
    def color(self) -> str:
        colors = {
            RiskLevel.SAFE: "green",
            RiskLevel.LOW: "blue",
            RiskLevel.MEDIUM: "orange",
            RiskLevel.HIGH: "red",
        }
        return colors[self]


@dataclass
class Rule:
    """审查规则定义"""
    rule_id: str
    name: str
    category: RuleCategory
    severity: RuleSeverity
    description: str
    applicable_contract_types: List[str] = field(default_factory=lambda: ["*"])
    enabled: bool = True
    weight: float = 1.0
    patterns: List[str] = field(default_factory=list)
    detection_function: Optional[str] = None
    modification_suggestion: str = ""
    one_click_fix: str = ""
    legal_basis: List[str] = field(default_factory=list)
    compiled_patterns: List[Pattern] = field(default_factory=list, repr=False)

    def __post_init__(self):
        if not self.compiled_patterns and self.patterns:
            self.compiled_patterns = [
                re.compile(p, re.MULTILINE | re.IGNORECASE)
                for p in self.patterns
            ]

    def applies_to(self, contract_type: str) -> bool:
        if "*" in self.applicable_contract_types:
            return True
        return contract_type in self.applicable_contract_types

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("compiled_patterns", None)
        d["category"] = self.category.value
        d["severity"] = self.severity.value
        return d


@dataclass
class RuleMatch:
    """规则匹配结果"""
    rule_id: str
    rule_name: str
    category: RuleCategory
    severity: RuleSeverity
    position: int
    length: int
    original_text: str
    problem_description: str
    modification_suggestion: str
    one_click_fix: str
    legal_basis: List[str]
    confidence: float = 0.8

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "category": self.category.value,
            "category_name": self.category.display_name,
            "severity": self.severity.value,
            "severity_name": self.severity.display_name,
            "position": self.position,
            "length": self.length,
            "original_text": self.original_text,
            "problem_description": self.problem_description,
            "modification_suggestion": self.modification_suggestion,
            "one_click_fix": self.one_click_fix,
            "legal_basis": self.legal_basis,
            "confidence": self.confidence,
        }


@dataclass
class RiskSummary:
    """风险汇总"""
    total_score: float
    risk_level: RiskLevel
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    category_distribution: Dict[str, int]
    severity_distribution: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_score": round(self.total_score, 2),
            "risk_level": self.risk_level.value,
            "risk_level_name": self.risk_level.display_name,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "info_count": self.info_count,
            "category_distribution": self.category_distribution,
            "severity_distribution": self.severity_distribution,
        }


@dataclass
class ReviewResult:
    """完整审查结果"""
    contract_text: str
    contract_type: str
    matches: List[RuleMatch]
    risk_summary: RiskSummary
    review_time_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_type": self.contract_type,
            "matches": [m.to_dict() for m in self.matches],
            "risk_summary": self.risk_summary.to_dict(),
            "review_time_ms": self.review_time_ms,
            "match_count": len(self.matches),
        }
