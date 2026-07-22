"""
合同审查规则引擎 - 修改建议生成器

为每条风险提供具体的修改建议，支持"一键修复"格式，
并提供法律依据引用。
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any

from skills.contract_review.rule_engine.models import (
    RuleMatch,
    RuleSeverity,
    RuleCategory,
    ReviewResult,
)


@dataclass
class SuggestionGroup:
    """按严重程度分组的修改建议"""
    severity: RuleSeverity
    suggestions: List[RuleMatch] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity.value,
            "severity_name": self.severity.display_name,
            "count": len(self.suggestions),
            "suggestions": [s.to_dict() for s in self.suggestions],
        }


@dataclass
class OneClickFixResult:
    """一键修复结果"""
    original_text: str
    fixed_text: str
    applied_count: int
    skipped_count: int
    skipped_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_text": self.original_text,
            "fixed_text": self.fixed_text,
            "applied_count": self.applied_count,
            "skipped_count": self.skipped_count,
            "skipped_reasons": self.skipped_reasons,
        }


def group_suggestions_by_severity(
    matches: List[RuleMatch]
) -> List[SuggestionGroup]:
    """按严重程度分组修改建议

    Args:
        matches: 规则匹配结果列表

    Returns:
        List[SuggestionGroup]: 按严重程度从高到低排序的分组
    """
    groups: Dict[RuleSeverity, List[RuleMatch]] = {}

    for match in matches:
        if match.severity not in groups:
            groups[match.severity] = []
        groups[match.severity].append(match)

    # 按严重程度从高到低排序
    severity_order = [
        RuleSeverity.HIGH,
        RuleSeverity.MEDIUM,
        RuleSeverity.LOW,
        RuleSeverity.INFO,
    ]

    result = []
    for sev in severity_order:
        if sev in groups:
            result.append(SuggestionGroup(
                severity=sev,
                suggestions=groups[sev],
            ))

    return result


def group_suggestions_by_category(
    matches: List[RuleMatch]
) -> Dict[str, List[RuleMatch]]:
    """按分类分组修改建议

    Args:
        matches: 规则匹配结果列表

    Returns:
        Dict[str, List[RuleMatch]]: 按分类分组的建议
    """
    groups: Dict[str, List[RuleMatch]] = {}

    for match in matches:
        cat_name = match.category.display_name
        if cat_name not in groups:
            groups[cat_name] = []
        groups[cat_name].append(match)

    return groups


def generate_modification_report(
    result: ReviewResult
) -> Dict[str, Any]:
    """生成修改建议报告

    Args:
        result: 审查结果

    Returns:
        Dict: 修改建议报告
    """
    matches = result.matches
    high_matches = [m for m in matches if m.severity == RuleSeverity.HIGH]
    medium_matches = [m for m in matches if m.severity == RuleSeverity.MEDIUM]
    low_matches = [m for m in matches if m.severity == RuleSeverity.LOW]

    # 优先级排序的建议列表
    priority_suggestions = sorted(
        matches,
        key=lambda m: (
            -SEVERITY_PRIORITY[m.severity],
            m.position
        )
    )

    # 生成摘要
    summary_lines = []
    if high_matches:
        summary_lines.append(f"发现 {len(high_matches)} 项高危风险，建议优先修改")
    if medium_matches:
        summary_lines.append(f"发现 {len(medium_matches)} 项中危风险，建议重点关注")
    if low_matches:
        summary_lines.append(f"发现 {len(low_matches)} 项低危风险，可酌情优化")

    return {
        "total_suggestions": len(matches),
        "priority_suggestions": [m.to_dict() for m in priority_suggestions[:20]],
        "by_severity": {
            "high": [m.to_dict() for m in high_matches],
            "medium": [m.to_dict() for m in medium_matches],
            "low": [m.to_dict() for m in low_matches],
        },
        "by_category": {
            k: [m.to_dict() for m in v]
            for k, v in group_suggestions_by_category(matches).items()
        },
        "summary": "；".join(summary_lines) if summary_lines else "未发现明显风险",
        "can_one_click_fix": any(m.one_click_fix for m in matches),
    }


SEVERITY_PRIORITY = {
    RuleSeverity.HIGH: 4,
    RuleSeverity.MEDIUM: 3,
    RuleSeverity.LOW: 2,
    RuleSeverity.INFO: 1,
}


def apply_one_click_fix(
    contract_text: str,
    matches: List[RuleMatch],
    severity_filter: Optional[RuleSeverity] = None,
) -> OneClickFixResult:
    """应用一键修复

    对可自动修复的问题应用修改建议。

    Args:
        contract_text: 原始合同文本
        matches: 匹配结果
        severity_filter: 只修复指定严重程度的问题（可选）

    Returns:
        OneClickFixResult: 修复结果
    """
    if not contract_text:
        return OneClickFixResult(
            original_text="",
            fixed_text="",
            applied_count=0,
            skipped_count=len(matches) if matches else 0,
            skipped_reasons=["合同文本为空"],
        )

    fixed_text = contract_text
    applied = 0
    skipped = 0
    skipped_reasons: List[str] = []

    # 按位置从后往前修复，避免位置偏移
    sorted_matches = sorted(matches, key=lambda m: -m.position)

    for match in sorted_matches:
        # 严重程度过滤
        if severity_filter and match.severity != severity_filter:
            skipped += 1
            skipped_reasons.append(f"{match.rule_name}: 严重程度不匹配")
            continue

        # 检查是否有一键修复内容
        if not match.one_click_fix:
            skipped += 1
            skipped_reasons.append(f"{match.rule_name}: 无可一键修复方案")
            continue

        # 检查位置是否有效
        if match.position < 0 or match.position + match.length > len(fixed_text):
            skipped += 1
            skipped_reasons.append(f"{match.rule_name}: 位置无效")
            continue

        # 应用修复（这里用替换标记的方式，实际使用可能需要更复杂的逻辑）
        original = fixed_text[match.position:match.position + match.length]
        if original:
            replacement = f"【建议修改: {match.one_click_fix[:50]}...】"
            fixed_text = (
                fixed_text[:match.position]
                + replacement
                + fixed_text[match.position + match.length:]
            )
            applied += 1
        else:
            skipped += 1
            skipped_reasons.append(f"{match.rule_name}: 原文为空")

    return OneClickFixResult(
        original_text=contract_text,
        fixed_text=fixed_text,
        applied_count=applied,
        skipped_count=skipped,
        skipped_reasons=skipped_reasons[:10],
    )


def generate_legal_basis_summary(matches: List[RuleMatch]) -> Dict[str, List[str]]:
    """生成法律依据汇总

    Args:
        matches: 匹配结果

    Returns:
        Dict: 按风险分类汇总的法律依据
    """
    basis_by_category: Dict[str, List[str]] = {}
    seen_basis = set()

    for match in matches:
        if not match.legal_basis:
            continue
        cat = match.category.display_name
        if cat not in basis_by_category:
            basis_by_category[cat] = []
        for basis in match.legal_basis:
            if basis not in seen_basis:
                seen_basis.add(basis)
                basis_by_category[cat].append(basis)

    return basis_by_category


def generate_priority_list(
    matches: List[RuleMatch],
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """生成优先修改清单

    Args:
        matches: 匹配结果
        top_n: 返回前N项

    Returns:
        List[Dict]: 优先级清单
    """
    sorted_matches = sorted(
        matches,
        key=lambda m: (
            -SEVERITY_PRIORITY.get(m.severity, 0),
            -m.confidence,
            m.position
        )
    )

    result = []
    for i, match in enumerate(sorted_matches[:top_n]):
        result.append({
            "priority": i + 1,
            "rule_id": match.rule_id,
            "rule_name": match.rule_name,
            "severity": match.severity.value,
            "severity_name": match.severity.display_name,
            "category": match.category.value,
            "category_name": match.category.display_name,
            "problem_description": match.problem_description,
            "modification_suggestion": match.modification_suggestion,
            "legal_basis": match.legal_basis,
            "confidence": match.confidence,
        })

    return result
