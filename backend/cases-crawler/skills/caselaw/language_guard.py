"""
LexPrime 类案检索 Skill — 界面语言规范守卫

强制执行 PRD § 5.7 横切面 7 "界面语言规范":
- ✅ 正确: "近 3 年本法院 87 件类似案件中, 支持原告诉请 72 件 (约 83%)"
- ❌ 禁止: "本案胜诉率约 83%" / "预计本案判赔 XX 元"

任何 narrative 字段在输出前必须通过 check_narrative(), 不通过则 reject 重新生成。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple


# ===== 禁用模式 (HIGH 违规, 致命) =====

# 1) "胜诉率" 类: 把统计说成"本案的胜诉概率"
RE_WINRATE_HIGH = [
    # "本案胜诉率约 83%" / "胜诉率 80%" / "胜诉率约 80%"
    re.compile(r"(?i)(本案|这场|这场官司|这次诉讼)?\s*胜诉率(\s*约)?\s*\d"),
    # 单独的"本案胜诉率"也直接禁
    re.compile(r"(?i)(本案|这场|这场官司)\s*胜诉率"),
    re.compile(r"(?i)胜诉率\s*(约|大概|大概为|为|是)\s*\d"),
    re.compile(r"(?i)本场\s*胜诉"),
    re.compile(r"(?i)预计\s*.*?\s*胜诉"),
]

# 2) "预计/将会" 类: 把统计说成"本案的预计结果"
RE_PREDICT_HIGH = [
    re.compile(r"(?i)预计\s*本案"),
    re.compile(r"(?i)预计\s*判赔"),
    re.compile(r"(?i)预计\s*.{0,20}\s*元"),
    re.compile(r"(?i)预计\s*.{0,20}\s*天"),
    re.compile(r"(?i)本案\s*将会"),
    re.compile(r"(?i)本案\s*可能"),
    re.compile(r"(?i)大概\s*.{0,5}\s*胜诉"),
    re.compile(r"(?i)胜诉\s*概率\s*[:：]?\s*\d"),
]

# 3) 主观评价类: 对法官 / 法院做定性判断
RE_OPINION_HIGH = [
    re.compile(r"(?i)该\s*法官\s*.{0,15}(好|坏|偏袒|不公|优秀|较差|靠谱|不靠谱)"),
    re.compile(r"(?i)该\s*法院\s*.{0,15}(偏袒|不公|支持原告|支持被告)"),
    re.compile(r"(?i)该\s*地区\s*.{0,10}\s*法院\s*.{0,15}(好|坏|差)"),
]

ALL_HIGH = RE_WINRATE_HIGH + RE_PREDICT_HIGH + RE_OPINION_HIGH

# ===== LOW 违规 (建议修改) =====
RE_LOW = [
    re.compile(r"(?i)我觉得"),
    re.compile(r"(?i)我认为"),
    re.compile(r"(?i)一般来说\s*.{0,30}\s*胜诉"),
]


@dataclass
class LanguageCheckResult:
    passed: bool
    high_violations: List[str]
    low_violations: List[str]
    corrected_text: str

    def __str__(self) -> str:
        if self.passed:
            return f"PASS (low={len(self.low_violations)})"
        return f"FAIL high={len(self.high_violations)} low={len(self.low_violations)}: {self.high_violations[:3]}"


def check_narrative(text: str) -> LanguageCheckResult:
    """检查 narrative 字段是否违反界面语言规范。

    Returns:
        LanguageCheckResult — passed=True 表示无 HIGH 违规
    """
    high: List[str] = []
    low: List[str] = []

    for pat in ALL_HIGH:
        for m in pat.finditer(text):
            high.append(m.group(0))

    for pat in RE_LOW:
        for m in pat.finditer(text):
            low.append(m.group(0))

    return LanguageCheckResult(
        passed=len(high) == 0,
        high_violations=high,
        low_violations=low,
        corrected_text=_suggest_correction(text) if high else text,
    )


def _suggest_correction(text: str) -> str:
    """简单降级: 把 '本案胜诉率' 替换为 '样本中支持原告诉请的比例', 把 '预计' 替换为 '样本显示'"""
    out = text
    out = re.sub(r"(?i)本案\s*胜诉率", "样本中支持原告诉请的比例", out)
    out = re.sub(r"(?i)预计", "样本显示", out)
    out = re.sub(r"(?i)本案\s*将会", "在已公开样本中, 类似案件倾向于", out)
    out = re.sub(r"(?i)该\s*法官\s*", "该法官在同类案件样本中 ", out)
    return out


# ===== 强制降级模板 (LLM 拒答 3 次后使用) =====

def template_outcome_distribution(sample_size: int, support_total: int) -> str:
    pct = round(support_total / sample_size * 100, 2) if sample_size else 0
    return f"在 {sample_size} 件样本中, 支持原告诉请 (含部分支持) {support_total} 件, 占比约 {pct}%。"


def template_amount_stats(median: float, q1: float, q3: float, mn: float, mx: float) -> str:
    return (
        f"判赔金额中位数约 {median:.0f} 元, "
        f"四分位距 {q1:.0f}-{q3:.0f} 元, "
        f"极值范围 {mn:.0f}-{mx:.0f} 元。"
    )


def template_judge_style(judge: str, n: int, pct: float, days: float, tendency: str) -> str:
    return (
        f"该法官在 {n} 件样本中, 支持原告诉请的比例约 {pct:.2f}%; "
        f"平均审理周期 {days:.0f} 天; 证据采信倾向 {tendency}。"
    )


def template_overall(sample_size: int, cause: str, region: str = "",
                     year_from: int = 0, year_to: int = 0) -> str:
    span = f"{year_from}-{year_to}" if year_from else "近 5 年"
    return (
        f"本检索基于 {span} {region} {cause} 的 {sample_size} 件已公开裁判文书。"
        f"以上数据仅为统计结果, 不代表对本案结果的预测。"
    )


# ===== UI 底部免责声明 =====

DISCLAIMER_FULL = (
    "以上数据仅为已公开裁判文书的统计结果, 不代表对本案结果的任何预测或判断。"
    "LexPrime 类案检索 Skill 输出仅供执业律师研究参考, 不构成法律意见, "
    "更不替代律师的专业判断。"
)

DISCLAIMER_SHORT = "以上数据为已公开裁判文书的统计结果, 不代表本案预测。"


# ===== CLI =====

if __name__ == "__main__":
    samples = [
        # PASS
        "近 3 年本法院 87 件类似案件中, 支持原告诉请 72 件 (约 83%)。",
        "该法官在同类案件中, 判赔金额中位数约 38 万元。",
        # FAIL high
        "本案胜诉率约 83%。",
        "预计本案判赔 50 万元。",
        "该法官审理案件偏袒原告。",
    ]
    for s in samples:
        r = check_narrative(s)
        print(f"{r}\n  text: {s}\n")