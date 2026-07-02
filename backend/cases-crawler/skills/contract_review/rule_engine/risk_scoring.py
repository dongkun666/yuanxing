"""
合同审查规则引擎 - 风险评分与分级

基于各风险等级加权计算综合评分，确定整体风险等级，
并生成可视化数据分布。
"""
from __future__ import annotations

from typing import List, Dict

from skills.contract_review.rule_engine.models import (
    RuleMatch,
    RuleSeverity,
    RuleCategory,
    RiskLevel,
)


# 风险等级权重配置
SEVERITY_WEIGHTS = {
    RuleSeverity.HIGH: 10.0,
    RuleSeverity.MEDIUM: 5.0,
    RuleSeverity.LOW: 2.0,
    RuleSeverity.INFO: 0.5,
}

# 风险等级阈值（分数越高风险越大）
RISK_LEVEL_THRESHOLDS = {
    RiskLevel.SAFE: 5.0,
    RiskLevel.LOW: 15.0,
    RiskLevel.MEDIUM: 30.0,
    RiskLevel.HIGH: float("inf"),
}


def calculate_risk_score(matches: List[RuleMatch]) -> float:
    """计算综合风险评分

    基于各风险等级加权计算：
    高危 × 10 + 中危 × 5 + 低危 × 2 + 提示 × 0.5

    Args:
        matches: 规则匹配结果列表

    Returns:
        float: 综合风险评分
    """
    score = 0.0
    for match in matches:
        base_weight = SEVERITY_WEIGHTS.get(match.severity, 0.5)
        # 乘以规则权重和置信度
        weighted = base_weight * match.confidence
        score += weighted

    return round(score, 2)


def determine_risk_level(score: float) -> RiskLevel:
    """根据评分确定风险等级

    风险等级划分：
    - 安全 (safe): 0-5分
    - 低风险 (low): 5-15分
    - 中风险 (medium): 15-30分
    - 高风险 (high): 30分以上

    Args:
        score: 风险评分

    Returns:
        RiskLevel: 风险等级
    """
    if score <= RISK_LEVEL_THRESHOLDS[RiskLevel.SAFE]:
        return RiskLevel.SAFE
    elif score <= RISK_LEVEL_THRESHOLDS[RiskLevel.LOW]:
        return RiskLevel.LOW
    elif score <= RISK_LEVEL_THRESHOLDS[RiskLevel.MEDIUM]:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.HIGH


def generate_risk_distribution(
    matches: List[RuleMatch],
    dimension: str = "category"
) -> Dict[str, int]:
    """生成风险分布数据

    Args:
        matches: 规则匹配结果列表
        dimension: 分布维度 ('category' 或 'severity')

    Returns:
        Dict[str, int]: 分布统计
    """
    distribution: Dict[str, int] = {}

    for match in matches:
        if dimension == "category":
            key = match.category.display_name
        elif dimension == "severity":
            key = match.severity.display_name
        else:
            raise ValueError(f"不支持的分布维度: {dimension}")

        distribution[key] = distribution.get(key, 0) + 1

    return distribution


def generate_visualization_data(matches: List[RuleMatch]) -> Dict:
    """生成可视化数据

    用于前端图表展示的完整数据。

    Args:
        matches: 规则匹配结果列表

    Returns:
        Dict: 可视化数据
    """
    score = calculate_risk_score(matches)
    level = determine_risk_level(score)

    # 严重程度分布（饼图）
    severity_data = {
        "labels": [],
        "values": [],
        "colors": [],
    }
    for sev in [RuleSeverity.HIGH, RuleSeverity.MEDIUM, RuleSeverity.LOW, RuleSeverity.INFO]:
        count = sum(1 for m in matches if m.severity == sev)
        if count > 0:
            severity_data["labels"].append(sev.display_name)
            severity_data["values"].append(count)
            severity_data["colors"].append(sev.color)

    # 分类分布（柱状图）
    category_data = {
        "labels": [],
        "values": [],
    }
    for cat in RuleCategory:
        count = sum(1 for m in matches if m.category == cat)
        if count > 0:
            category_data["labels"].append(cat.display_name)
            category_data["values"].append(count)

    # 风险评分仪表盘数据
    gauge_data = {
        "score": score,
        "max_score": 50,
        "level": level.value,
        "level_name": level.display_name,
        "color": level.color,
    }

    return {
        "severity_chart": severity_data,
        "category_chart": category_data,
        "gauge": gauge_data,
        "total_matches": len(matches),
    }


def get_severity_weight(severity: RuleSeverity) -> float:
    """获取严重程度的权重"""
    return SEVERITY_WEIGHTS.get(severity, 0.5)


def set_severity_weight(severity: RuleSeverity, weight: float) -> None:
    """设置严重程度的权重"""
    if weight <= 0:
        raise ValueError("权重必须大于0")
    SEVERITY_WEIGHTS[severity] = weight


def get_risk_thresholds() -> Dict[RiskLevel, float]:
    """获取风险等级阈值"""
    return dict(RISK_LEVEL_THRESHOLDS)


def set_risk_threshold(level: RiskLevel, threshold: float) -> None:
    """设置风险等级阈值"""
    if threshold < 0:
        raise ValueError("阈值不能为负数")
    RISK_LEVEL_THRESHOLDS[level] = threshold
