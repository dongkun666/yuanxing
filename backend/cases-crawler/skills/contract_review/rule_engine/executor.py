"""
合同审查规则引擎 - 审查执行器

主入口函数 reviewContract，执行完整的合同审查流程。
"""
from __future__ import annotations

import time
from typing import List, Optional

from loguru import logger

from skills.contract_review.rule_engine.models import (
    Rule,
    RuleMatch,
    ReviewResult,
    RiskSummary,
    RuleCategory,
    RuleSeverity,
)
from skills.contract_review.rule_engine.manager import RuleManager
from skills.contract_review.rule_engine.builtin_rules import register_default_rules
from skills.contract_review.rule_engine.risk_scoring import (
    calculate_risk_score,
    determine_risk_level,
    generate_risk_distribution,
)


_global_manager: Optional[RuleManager] = None


def get_default_manager() -> RuleManager:
    """获取默认的规则管理器（单例）"""
    global _global_manager
    if _global_manager is None:
        _global_manager = RuleManager()
        register_default_rules(_global_manager)
        logger.info(f"已加载默认规则: {_global_manager.rule_count()}")
    return _global_manager


def reset_default_manager() -> None:
    """重置默认规则管理器（测试用）"""
    global _global_manager
    _global_manager = None


def _match_pattern_rules(rule: Rule, text: str) -> List[RuleMatch]:
    """匹配基于正则表达式的规则"""
    matches: List[RuleMatch] = []
    if not rule.compiled_patterns:
        return matches

    seen_positions = set()

    for pattern in rule.compiled_patterns:
        for m in pattern.finditer(text):
            start = m.start()
            end = m.end()
            original = m.group(0)

            # 避免重复匹配同一位置
            pos_key = (start, end)
            if pos_key in seen_positions:
                continue
            seen_positions.add(pos_key)

            # 提取上下文（前后各20字符）
            context_start = max(0, start - 20)
            context_end = min(len(text), end + 20)
            context = text[context_start:context_end]

            match = RuleMatch(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                category=rule.category,
                severity=rule.severity,
                position=start,
                length=end - start,
                original_text=original[:200],
                problem_description=f"在「{context[:100]}...」中检测到{rule.name}：{rule.description}",
                modification_suggestion=rule.modification_suggestion,
                one_click_fix=rule.one_click_fix,
                legal_basis=rule.legal_basis,
                confidence=0.8,
            )
            matches.append(match)

    return matches


def _match_detection_function_rules(rule: Rule, text: str,
                                    manager: RuleManager) -> List[RuleMatch]:
    """匹配基于检测函数的规则"""
    matches: List[RuleMatch] = []
    if not rule.detection_function:
        return matches

    func = manager.get_detection_function(rule.detection_function)
    if not func:
        logger.warning(f"检测函数未找到: {rule.detection_function}")
        return matches

    try:
        results = func(text)
        for result in results:
            match = RuleMatch(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                category=rule.category,
                severity=rule.severity,
                position=result.get("position", 0),
                length=result.get("length", 0),
                original_text=text[
                    result.get("position", 0):
                    result.get("position", 0) + result.get("length", 0)
                ][:200] if result.get("length", 0) > 0 else "",
                problem_description=result.get("problem", rule.description),
                modification_suggestion=rule.modification_suggestion,
                one_click_fix=rule.one_click_fix,
                legal_basis=rule.legal_basis,
                confidence=0.7,
            )
            matches.append(match)
    except Exception as e:
        logger.error(f"检测函数执行失败 {rule.detection_function}: {e}")

    return matches


def review_contract(
    contract_text: str,
    contract_type: str = "其他",
    manager: Optional[RuleManager] = None,
) -> ReviewResult:
    """合同审查主函数

    逐条匹配规则，返回审查结果列表和统计概览。

    Args:
        contract_text: 合同文本
        contract_type: 合同类型（房屋租赁、借款合同、劳动合同等）
        manager: 规则管理器，如不提供则使用默认管理器

    Returns:
        ReviewResult: 完整的审查结果
    """
    t0 = time.time()

    if manager is None:
        manager = get_default_manager()

    if not contract_text or not contract_text.strip():
        empty_summary = RiskSummary(
            total_score=0,
            risk_level=determine_risk_level(0),
            high_count=0,
            medium_count=0,
            low_count=0,
            info_count=0,
            category_distribution={},
            severity_distribution={},
        )
        return ReviewResult(
            contract_text="",
            contract_type=contract_type,
            matches=[],
            risk_summary=empty_summary,
            review_time_ms=0,
        )

    # 获取适用的规则
    enabled_rules = manager.get_enabled_rules(contract_type)
    logger.debug(f"适用规则数: {len(enabled_rules)}, 合同类型: {contract_type}")

    all_matches: List[RuleMatch] = []

    for rule in enabled_rules:
        rule_matches: List[RuleMatch] = []

        # 1. 正则匹配
        if rule.compiled_patterns:
            rule_matches.extend(_match_pattern_rules(rule, contract_text))

        # 2. 检测函数匹配
        if rule.detection_function:
            rule_matches.extend(_match_detection_function_rules(rule, contract_text, manager))

        # 限制单条规则的匹配数，避免过多
        if len(rule_matches) > 10:
            rule_matches = rule_matches[:10]

        all_matches.extend(rule_matches)

    # 按位置排序
    all_matches.sort(key=lambda m: m.position)

    # 计算风险评分
    total_score = calculate_risk_score(all_matches)
    risk_level = determine_risk_level(total_score)
    category_dist = generate_risk_distribution(all_matches, "category")
    severity_dist = generate_risk_distribution(all_matches, "severity")

    # 统计各级别数量
    high_count = sum(1 for m in all_matches if m.severity == RuleSeverity.HIGH)
    medium_count = sum(1 for m in all_matches if m.severity == RuleSeverity.MEDIUM)
    low_count = sum(1 for m in all_matches if m.severity == RuleSeverity.LOW)
    info_count = sum(1 for m in all_matches if m.severity == RuleSeverity.INFO)

    risk_summary = RiskSummary(
        total_score=total_score,
        risk_level=risk_level,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        info_count=info_count,
        category_distribution=category_dist,
        severity_distribution=severity_dist,
    )

    latency_ms = int((time.time() - t0) * 1000)

    logger.info(
        f"合同审查完成: 类型={contract_type}, "
        f"匹配数={len(all_matches)}, "
        f"高危={high_count}, 中危={medium_count}, 低危={low_count}, "
        f"评分={total_score:.2f}, 等级={risk_level.display_name}, "
        f"耗时={latency_ms}ms"
    )

    return ReviewResult(
        contract_text=contract_text,
        contract_type=contract_type,
        matches=all_matches,
        risk_summary=risk_summary,
        review_time_ms=latency_ms,
    )
