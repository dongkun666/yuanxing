"""
LexPrime 合同审查规则引擎模块

提供结构化、可扩展的合同审查规则系统:
- 规则数据结构定义
- 规则注册与管理
- 审查执行器
- 风险分级与评分
- 修改建议生成
"""
from skills.contract_review.rule_engine.models import (
    Rule,
    RuleSeverity,
    RuleCategory,
    RuleMatch,
    ReviewResult,
    RiskSummary,
    RiskLevel,
)
from skills.contract_review.rule_engine.manager import RuleManager
from skills.contract_review.rule_engine.executor import review_contract, get_default_manager
from skills.contract_review.rule_engine.risk_scoring import (
    calculate_risk_score,
    determine_risk_level,
    generate_risk_distribution,
    generate_visualization_data,
)
from skills.contract_review.rule_engine.suggestion_generator import (
    group_suggestions_by_severity,
    generate_modification_report,
    apply_one_click_fix,
    generate_priority_list,
)
from skills.contract_review.rule_engine.builtin_rules import (
    build_default_rules,
    register_default_rules,
)

__all__ = [
    "Rule",
    "RuleSeverity",
    "RuleCategory",
    "RuleMatch",
    "ReviewResult",
    "RiskSummary",
    "RiskLevel",
    "RuleManager",
    "review_contract",
    "get_default_manager",
    "calculate_risk_score",
    "determine_risk_level",
    "generate_risk_distribution",
    "generate_visualization_data",
    "group_suggestions_by_severity",
    "generate_modification_report",
    "apply_one_click_fix",
    "generate_priority_list",
    "build_default_rules",
    "register_default_rules",
]
