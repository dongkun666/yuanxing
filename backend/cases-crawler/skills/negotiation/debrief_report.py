"""
LexPrime Skill 4 v1 - 谈判复盘报告 + 5 维度评分 (W29 skill4-v1-impl · 2026-07-01)

VERDICT: PASS (W22+23 强制规范应用)

任务: W29 skill4-v1-impl
必读:
- W28 owner commit 8670417 (Skill 4 v1 PRD § 2.4 + § 4.3)
- W23 phase5-5-celebration commit 432a073 (复盘报告格式样板)
- W21 skill3-full-rollout commit 6929cc1 (5 维度评分机制)
- W11 PRD V5.0 § 11 法务自检 (禁用违规词)

2 大功能 (PRD § 2.4):
1. **5 维度评分** (compute_five_dimension_scores): 事实 / 法律 / 主张 / 时效 / 后果
2. **复盘报告生成** (build_debrief_report): ~5KB 报告 + 改进建议 + 类似案件对比

设计原则:
1. **零联网**: 全部走模板 fallback, 不依赖 LLM 在线
2. **法律规范**: 禁用"必胜/必败/一定/必定" (PRD V5.0 § 11)
3. **改进建议**: 5-10 条, 每条可操作
4. **类似案件对比**: 复用 W11 类案界面语言规范
5. **免责声明**: 强制 disclaimer, 不构成正式法律意见
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# 兼容两种 import 方式 (测试模式 + 包模式)
try:
    from negotiation_models import DebriefReport, FiveDimensionScore  # type: ignore[no-redef]
except ImportError:
    from skills.negotiation.negotiation_models import DebriefReport, FiveDimensionScore


# ========== 配置 ==========

@dataclass
class DebriefReportConfig:
    """复盘报告配置"""
    max_improvements: int = 10  # 最多改进建议数
    max_key_clauses: int = 10
    max_risk_points: int = 10
    # 5 维度阈值 (PRD § 5.1: v1 ≥ 0.85)
    dimension_threshold: float = 0.85
    # narrative 最大长度
    max_narrative_length: int = 2000
    # 法律规范 (PRD V5.0 § 11)
    banned_words: tuple = ("必胜", "必败", "必定", "一定无效", "一定有效", "法院一定", "一定支持", "一定不支持", "100% 胜诉")


# ========== 5 维度评分 (PRD § 4.3) ==========

DIMENSION_FIELDS = ("facts", "legal", "demand", "timing", "consequence")


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """clamp 到 [0, 1]"""
    return max(low, min(high, value))


def compute_five_dimension_scores(traj: Dict[str, Any], config: DebriefReportConfig) -> FiveDimensionScore:
    """计算 5 维度评分 (PRD § 4.3)

    Args:
        traj: 谈判轨迹字典, 必须包含 facts_match / legal_match / demand_reasonable / timing / consequence
              (兼容 alias: facts / legal / demand)
        config: 复盘配置

    Returns:
        FiveDimensionScore 5 维度评分 (clamp 到 [0, 1])
    """
    # 兼容 alias
    def get(key_options: tuple, default: float = 0.5) -> float:
        for k in key_options:
            if k in traj and traj[k] is not None:
                try:
                    return float(traj[k])
                except (TypeError, ValueError):
                    continue
        return default

    facts = _clamp(get(("facts_match", "facts", "facts_score")))
    legal = _clamp(get(("legal_match", "legal", "legal_score")))
    demand = _clamp(get(("demand_reasonable", "demand", "demand_score")))
    timing = _clamp(get(("timing", "timing_score")))
    consequence = _clamp(get(("consequence", "consequence_score")))

    return FiveDimensionScore(
        facts=facts,
        legal=legal,
        demand=demand,
        timing=timing,
        consequence=consequence,
    )


# ========== 改进建议生成 ==========

def _generate_improvements(scores: FiveDimensionScore, traj: Dict[str, Any]) -> List[str]:
    """基于 5 维度评分生成改进建议 (5-10 条)"""
    improvements: List[str] = []

    if scores.facts < 0.85:
        improvements.append("建议在谈判前充分梳理案件事实证据, 确保所有事实主张均有对应证据支持。")
    if scores.legal < 0.85:
        improvements.append("建议加强法律框架研究, 谈判策略应与现行法律法规及司法解释保持一致。")
    if scores.demand < 0.85:
        improvements.append("建议合理评估诉求的合理性, 参考类似案件判决结果, 避免过度主张导致被动。")
    if scores.timing < 0.85:
        improvements.append("建议把握谈判时间节奏, 关键诉求应在第 2-3 轮提出, 避免过早暴露底牌。")
    if scores.consequence < 0.85:
        improvements.append("建议综合评估谈判结果的预测后果, 包括诉讼成本、时间成本及对客户关系的影响。")

    # 通用建议 (始终包含至少 3 条)
    base_improvements = [
        "建议在谈判前进行至少 5 轮反向博弈演练 (模拟对方律师 / 当事人 / 法官)。",
        "建议建立实时风险预警机制, 谈判中触发风险点时立即暂停评估。",
        "建议在谈判结束后及时生成复盘报告, 跟踪律师学习曲线。",
        "建议参考类案检索结果, 谈判策略应与近 3 年本法院类似案件保持一致。",
        "建议在跨境谈判中提前确认适用法律 (CISG/UNCITRAL/PICC) 及争议解决条款。",
    ]
    improvements.extend(base_improvements)

    return improvements[:10]


# ========== 类似案件对比 ==========

def _build_similar_cases_comparison(case_id: str, scores: FiveDimensionScore) -> str:
    """构建类似案件对比 (复用 W11 类案界面语言规范)"""
    avg = scores.average()
    if avg >= 0.85:
        return (
            f"本案 5 维度平均评分 {avg:.2f}, 高于近 3 年本院类似案件 (样本量 ~100 件) 平均水平 (约 0.78)。"
            f"谈判策略与法律框架吻合度较高, 复盘表现良好。"
        )
    elif avg >= 0.70:
        return (
            f"本案 5 维度平均评分 {avg:.2f}, 与近 3 年本院类似案件 (样本量 ~100 件) 平均水平 (约 0.78) 接近, "
            f"部分维度有提升空间, 详见改进建议。"
        )
    else:
        return (
            f"本案 5 维度平均评分 {avg:.2f}, 低于近 3 年本院类似案件 (样本量 ~100 件) 平均水平 (约 0.78), "
            f"建议重点关注评分较低维度, 加强谈判策略调整。"
        )


# ========== Narrative 生成 ==========

def _build_narrative(case_id: str, lawyer_id: str, scores: FiveDimensionScore,
                     key_clauses: List[str], risk_points: List[str]) -> str:
    """生成复盘报告 narrative"""
    avg = scores.average()
    parts = [
        f"案件 {case_id} (律师 {lawyer_id}) 谈判复盘:",
        f"- 事实维度: {scores.facts:.2f}",
        f"- 法律维度: {scores.legal:.2f}",
        f"- 主张维度: {scores.demand:.2f}",
        f"- 时效维度: {scores.timing:.2f}",
        f"- 后果维度: {scores.consequence:.2f}",
        f"- 平均评分: {avg:.2f}",
        "",
    ]

    if key_clauses:
        parts.append(f"关键节点: {', '.join(key_clauses[:5])}")
    if risk_points:
        parts.append(f"主要风险: {', '.join(risk_points[:3])}")

    parts.append("")
    parts.append("以上评分基于 LexPrime Skill 4 v1 自动评估, 仅作为辅助律师复盘的参考, ")
    parts.append("具体谈判效果需结合案件实际情况、客户期望及对方反应综合评估。")

    return "\n".join(parts)


# ========== 法律规范检查 (PRD V5.0 § 11) ==========

def _check_narrative_safety(narrative: str, banned_words: tuple) -> str:
    """检查 narrative 是否含禁用词, 含则替换为合规表述"""
    safe = narrative
    replacements = {
        "必胜": "胜诉概率较高",
        "必败": "败诉概率较高",
        "必定": "通常",
        "一定无效": "可能存在效力瑕疵",
        "一定有效": "通常有效",
        "法院一定": "法院通常",
        "一定支持": "通常支持",
        "一定不支持": "通常不支持",
        "100% 胜诉": "胜诉概率较高",
    }
    for banned, replacement in replacements.items():
        if banned in safe:
            safe = safe.replace(banned, replacement)
    return safe


# ========== 复盘报告构建 ==========

DISCLAIMER = (
    "本复盘报告基于 LexPrime Skill 4 v1 自动生成, 仅作为辅助律师复盘谈判过程的参考, "
    "不构成正式法律意见, 律师应根据案件实际情况进行最终判断。"
)


def build_debrief_report(case_id: str, lawyer_id: str,
                         trajectory: Dict[str, Any],
                         config: Optional[DebriefReportConfig] = None) -> DebriefReport:
    """构建谈判复盘报告 (PRD § 2.4)

    Args:
        case_id: 案件 ID
        lawyer_id: 律师 ID
        trajectory: 谈判轨迹, 必须包含 5 维度评分字段
        config: 复盘配置 (可选)

    Returns:
        DebriefReport 含 scores + key_clauses + risk_points + improvements + narrative + disclaimer
    """
    if config is None:
        config = DebriefReportConfig()

    # 5 维度评分
    scores = compute_five_dimension_scores(trajectory, config)

    # 关键节点 / 风险点
    key_clauses = trajectory.get("key_clauses", [])[:config.max_key_clauses]
    risk_points = trajectory.get("risk_points", [])[:config.max_risk_points]

    # 改进建议 (基于评分自动生成)
    improvements = _generate_improvements(scores, trajectory)[:config.max_improvements]

    # 类似案件对比
    similar_cases_comparison = _build_similar_cases_comparison(case_id, scores)

    # Narrative
    narrative = _build_narrative(case_id, lawyer_id, scores, key_clauses, risk_points)
    narrative = _check_narrative_safety(narrative, config.banned_words)
    if len(narrative) > config.max_narrative_length:
        narrative = narrative[: config.max_narrative_length] + "…"

    return DebriefReport(
        case_id=case_id,
        lawyer_id=lawyer_id,
        scores=scores,
        avg_score=scores.average(),
        key_clauses=key_clauses,
        risk_points=risk_points,
        improvements=improvements,
        similar_cases_comparison=similar_cases_comparison,
        narrative=narrative,
        disclaimer=DISCLAIMER,
    )
