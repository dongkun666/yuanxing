"""
合同审查规则引擎 - 规则管理器

负责规则的注册、启用/禁用、权重配置等管理功能。
"""
from __future__ import annotations

from typing import List, Dict, Optional, Callable
from loguru import logger

from skills.contract_review.rule_engine.models import (
    Rule,
    RuleSeverity,
    RuleCategory,
)


class RuleManager:
    """规则管理器
    
    提供规则的注册、查询、启用/禁用、权重调整等功能。
    """

    def __init__(self):
        self._rules: Dict[str, Rule] = {}
        self._detection_functions: Dict[str, Callable] = {}

    def register_rule(self, rule: Rule) -> None:
        """注册一条规则"""
        if rule.rule_id in self._rules:
            logger.warning(f"规则 {rule.rule_id} 已存在, 将被覆盖")
        self._rules[rule.rule_id] = rule
        logger.debug(f"已注册规则: {rule.rule_id} ({rule.name})")

    def register_detection_function(self, name: str, func: Callable) -> None:
        """注册自定义检测函数"""
        self._detection_functions[name] = func

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """根据规则ID获取规则"""
        return self._rules.get(rule_id)

    def get_all_rules(self) -> List[Rule]:
        """获取所有规则"""
        return list(self._rules.values())

    def get_enabled_rules(self, contract_type: Optional[str] = None) -> List[Rule]:
        """获取启用的规则
        
        Args:
            contract_type: 合同类型, 如果提供则只返回适用该类型的规则
        """
        rules = [r for r in self._rules.values() if r.enabled]
        if contract_type:
            rules = [r for r in rules if r.applies_to(contract_type)]
        return rules

    def get_rules_by_category(self, category: RuleCategory) -> List[Rule]:
        """按分类获取规则"""
        return [r for r in self._rules.values() if r.category == category and r.enabled]

    def get_rules_by_severity(self, severity: RuleSeverity) -> List[Rule]:
        """按严重程度获取规则"""
        return [r for r in self._rules.values() if r.severity == severity and r.enabled]

    def enable_rule(self, rule_id: str) -> bool:
        """启用规则"""
        rule = self._rules.get(rule_id)
        if rule:
            rule.enabled = True
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """禁用规则"""
        rule = self._rules.get(rule_id)
        if rule:
            rule.enabled = False
            return True
        return False

    def set_rule_weight(self, rule_id: str, weight: float) -> bool:
        """设置规则权重"""
        rule = self._rules.get(rule_id)
        if rule:
            rule.weight = max(0.1, min(10.0, weight))
            return True
        return False

    def get_detection_function(self, name: str) -> Optional[Callable]:
        """获取自定义检测函数"""
        return self._detection_functions.get(name)

    def rule_count(self) -> Dict[str, int]:
        """统计规则数量"""
        total = len(self._rules)
        enabled = len([r for r in self._rules.values() if r.enabled])
        disabled = total - enabled
        return {
            "total": total,
            "enabled": enabled,
            "disabled": disabled,
        }

    def category_stats(self) -> Dict[str, int]:
        """按分类统计规则数量"""
        stats: Dict[str, int] = {}
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            cat_name = rule.category.display_name
            stats[cat_name] = stats.get(cat_name, 0) + 1
        return stats

    def severity_stats(self) -> Dict[str, int]:
        """按严重程度统计规则数量"""
        stats: Dict[str, int] = {}
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            sev_name = rule.severity.display_name
            stats[sev_name] = stats.get(sev_name, 0) + 1
        return stats
