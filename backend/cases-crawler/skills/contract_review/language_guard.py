"""
LexPrime 合同风险审查 Skill — 界面语言规范守卫

强制执行 PRD § 5.4 横切面 4 Skill Hub + § 11 风险合规 "界面语言规范":
- ✅ 正确: "该条款逾期违约金约定为月租金 5%/日, 年化约 1825%, 超出 LPR 四倍司法保护上限, 司法实践中通常被调减。"
- ❌ 禁止: "合同必败" / "该条款无效" / "对方将承担全部责任"

任何 narrative 字段在输出前必须通过 check_narrative(), 不通过则 reject 重新生成。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


# ===== 禁用模式 (HIGH 违规, 致命) =====

# 1) "合同必败/必胜" 类: 把审查说成"对结果的确定性预测"
RE_PREDICT_HIGH = [
    # "合同必败" / "合同必胜" / "合同必赢"
    re.compile(r"(?i)合同\s*必\s*(?:败|胜|赢|输|失败|成功|无效)"),
    # "该合同一定会败" / "该合同必然无效"
    re.compile(r"(?i)该\s*合同\s*(?:必定|必然|一定|百分百|绝对|将会)(?:败|输|无效|胜|赢|失败|成功)"),
    # "本合同必定胜诉"
    re.compile(r"(?i)本\s*合同\s*(?:必定|必然|一定|将会)(?:败|输|无效|胜|赢|失败|成功)"),
]

# 2) "该条款无效/有效" 类: 把审查说成"对条款效力的确定性裁决"
RE_INVALIDITY_HIGH = [
    # "该条款一定无效" / "该条款必定有效"
    re.compile(r"(?i)该\s*条款\s*(?:必定|必然|一定|百分百|绝对|将会)?\s*(?:无效|有效)"),
    # "该条款一定会被认定无效"
    re.compile(r"(?i)该\s*条款\s*(?:一定|必定|百分百|绝对)?\s*(?:会|将)?\s*(?:被\s*)?(?:认定|判定|裁决)\s*(?:为|是)?\s*(?:无效|有效)"),
    # "该条款违反法律无效" (允许"可能违反")
    re.compile(r"(?i)该\s*条款\s*违反\s*法律\s*(?:当然|自始)?\s*无效"),
    # "该条款必然无效"
    re.compile(r"(?i)该\s*条款\s*(?:必然|必定|一定)\s*无效"),
]

# 3) "对方将承担/败诉" 类: 把审查说成"对责任的确定性分配"
RE_LIABILITY_HIGH = [
    # "对方将承担全部责任"
    re.compile(r"(?i)对方\s*(?:将|必定|一定|必然|百分百|绝对)\s*(?:承担|败诉|输|赔偿)"),
    # "应当完全承担"
    re.compile(r"(?i)(?:应当|应)\s*(?:完全|全部)\s*(?:承担|赔偿)(?:\s*全部)?\s*(?:责任|损失)?\s*"),
    re.compile(r"(?i)(?:将|必定|一定|必然)\s*(?:承担|败诉|输|赔偿)\s*(?:全部|所有)\s*责任"),
    # "对方百分百败诉"
    re.compile(r"(?i)对方\s*百分百\s*(?:败诉|输|承担)"),
]

# 4) "本合同无效/有效" 类
RE_CONTRACT_VALIDITY_HIGH = [
    re.compile(r"(?i)本\s*合同\s*(?:必定|必然|一定|百分百|绝对|将会)?\s*(?:无效|有效|可撤销|可变更)"),
    re.compile(r"(?i)本\s*合同\s*(?:一定|必定|百分百)\s*(?:会\s*被)?\s*(?:认定|判定)\s*(?:为|是)?\s*(?:无效|有效)"),
]

# 5) "司法实践一定会..." 类
RE_COURT_CERTAINTY_HIGH = [
    re.compile(r"(?i)司法实践中\s*(?:一定|必定|必然|百分百|绝对)\s*(?:会|将|判定|认定)"),
    re.compile(r"(?i)法院\s*(?:一定|必定|必然|百分百|绝对)\s*(?:会|将|判定|支持|采纳)"),
]

ALL_HIGH = (
    RE_PREDICT_HIGH
    + RE_INVALIDITY_HIGH
    + RE_LIABILITY_HIGH
    + RE_CONTRACT_VALIDITY_HIGH
    + RE_COURT_CERTAINTY_HIGH
)

# ===== LOW 违规 (建议修改) =====
RE_LOW = [
    re.compile(r"(?i)我\s*(?:认为|觉得)"),
    re.compile(r"(?i)可能\s*(?:会|将)?\s*(?:败诉|无效|胜诉)"),
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
    """强力降级: 把所有 HIGH 违规词替换为合规表述。"""
    out = text
    # 1. "合同必败/必胜" 类 → "合同存在 X 风险"
    out = re.sub(r"(?i)合同\s*必\s*(?:败|输|失败)", "合同存在被认定 X 的风险", out)
    out = re.sub(r"(?i)合同\s*必\s*(?:胜|赢|成功)", "合同约定 X 条款", out)
    out = re.sub(r"(?i)合同\s*必\s*无效", "合同存在效力瑕疵", out)
    out = re.sub(r"(?i)(?:该|本)\s*合同\s*(?:必定|必然|一定|百分百|绝对|将会)\s*(?:败|输|无效|胜|赢|失败|成功)", "合同存在相应法律风险", out)
    # 2. "该条款无效/有效" 类 → "该条款可能存在效力瑕疵 / 存在效力认定风险"
    out = re.sub(r"(?i)该\s*条款\s*(?:必定|必然|一定|百分百|绝对|将会)\s*(?:无效|有效)", "该条款存在效力认定风险", out)
    out = re.sub(r"(?i)该\s*条款\s*(?:一定|必定|百分百)\s*(?:会\s*被)?\s*(?:认定|判定|裁决)\s*(?:为|是)?\s*(?:无效|有效)", "该条款可能存在效力认定风险", out)
    out = re.sub(r"(?i)该\s*条款\s*违反\s*法律\s*(?:当然|自始)?\s*无效", "该条款可能违反相关法律规定, 存在效力瑕疵", out)
    out = re.sub(r"(?i)该\s*条款\s*(?:必然|必定|一定)\s*无效", "该条款存在效力瑕疵", out)
    # 3. "对方将承担/败诉" 类 → "对方可能承担 X 责任"
    out = re.sub(r"(?i)对方\s*(?:将|必定|一定|必然|百分百|绝对)\s*(?:承担|败诉|输|赔偿)", "对方可能承担相应责任", out)
    out = re.sub(r"(?i)(?:应当|应)\s*(?:完全|全部)\s*(?:承担|赔偿)(?:\s*全部)?\s*(?:责任|损失)?", "可能需要承担相应责任", out)
    out = re.sub(r"(?i)(?:将|必定|一定|必然)\s*(?:承担|败诉|输|赔偿)\s*(?:全部|所有)\s*责任", "可能需要承担相应责任", out)
    out = re.sub(r"(?i)对方\s*百分百\s*(?:败诉|输|承担)", "对方可能承担相应责任", out)
    # 4. "本合同无效/有效" 类
    out = re.sub(r"(?i)本\s*合同\s*(?:必定|必然|一定|百分百|绝对|将会)?\s*(?:无效|有效|可撤销|可变更)", "本合同可能存在效力瑕疵", out)
    out = re.sub(r"(?i)本\s*合同\s*(?:一定|必定|百分百)\s*(?:会\s*被)?\s*(?:认定|判定)\s*(?:为|是)?\s*(?:无效|有效)", "本合同可能存在效力认定风险", out)
    # 5. "司法实践一定会..." 类 → "司法实践中通常..."
    out = re.sub(r"(?i)司法实践中\s*(?:一定|必定|必然|百分百|绝对)\s*(?:会|将|判定|认定)", "司法实践中通常", out)
    out = re.sub(r"(?i)法院\s*(?:一定|必定|必然|百分百|绝对)\s*(?:会|将|判定|支持|采纳)", "法院通常", out)
    return out


def sanitize_input(value: str) -> str:
    """输入消毒: 把输入字段中的禁用词替换为合规表述。

    防止 user input (contract_text / industry) 携带禁用词绕过 narrative 检查。
    """
    if not value:
        return value
    return _suggest_correction(value)


def assert_no_bypass(narrative: str, source_fields: dict = None) -> bool:
    """强校验: 任何 narrative 输出必须 0 HIGH 违规, 否则抛 ValueError。

    这是 "三重防护" 的最后一层 — 前端 client guard + 后端 reviewer
    重生成, 仍可能在极端 case 下输出违规 (LLM 幻觉 / 模板 fallback 边界)。
    一旦发现, 拒绝输出 (抛 ValueError), 由调用方 fallback 到纯数字模板。

    Args:
        narrative: 待校验的 narrative 字符串
        source_fields: 触发该 narrative 的输入字段 (用于审计)

    Raises:
        ValueError: 仍有 HIGH 违规
    """
    r = check_narrative(narrative)
    if not r.passed:
        import logging
        logging.error(f"language_guard bypass detected: violations={r.high_violations}, "
                       f"source={source_fields}")
        raise ValueError(
            f"language_guard bypass: narrative 仍含 HIGH 违规: {r.high_violations}. "
            f"不应在生产环境出现, 请检查 reviewer 流程。"
        )
    return True


# ===== 强制降级模板 (LLM 拒答 3 次后使用) =====

def template_clause_risk_description(clause_summary: str, legal_basis: str,
                                       risk_pattern: str) -> str:
    """条款风险描述降级模板。

    Args:
        clause_summary: 条款摘要 (律师填写或 LLM 提取)
        legal_basis: 法条 / 司法解释引用
        risk_pattern: 风险模式 (例: '违约金过高', '管辖不利')
    """
    return (
        f"该条款约定 {clause_summary}。"
        f"在 {legal_basis} 框架下, 此类约定 {risk_pattern}, 存在相应法律风险。"
        f"具体后果取决于履行情况、双方证据及司法裁判, 建议结合个案评估。"
    )


def template_risk_summary(total: int, fatal: int, major: int,
                          advisory: int, top_categories: List[str]) -> str:
    pct_fatal = round(fatal / total * 100, 2) if total else 0.0
    return (
        f"本合同共审查 {total} 个条款, 其中致命风险 {fatal} 个 ({pct_fatal}%), "
        f"重大风险 {major} 个, 建议风险 {advisory} 个。"
        f"高频风险分类: {'、'.join(top_categories[:3])}。"
        f"以上仅为基于合同文本的客观风险标注, 不构成法律意见, 不替代律师判断。"
    )


def template_negotiation_advice(stance: str, priority_clauses: List[str],
                                 leverage_count: int, walk_away_count: int) -> str:
    return (
        f"{stance} 立场: 重点关注条款 {', '.join(priority_clauses[:3])}, "
        f"建议优先协商 {leverage_count} 个杠杆条款。"
        f"若对方拒绝修改红线条款 ({walk_away_count} 项), 建议评估签约风险。"
    )


def template_diff_summary(baseline: str, compared: str,
                          added: int, removed: int, modified: int) -> str:
    return (
        f"对比版本 {baseline} 与版本 {compared}, "
        f"共新增 {added} 个条款, 删除 {removed} 个条款, 修改 {modified} 个条款。"
        f"建议结合具体变化评估风险等级变化。"
    )


# ===== UI 底部免责声明 =====

DISCLAIMER_FULL = (
    "本审查仅为基于合同文本的客观风险标注与法律依据提示, 不构成法律意见, "
    "更不替代律师的专业判断。"
    "LexPrime 合同风险审查 Skill 输出仅供执业律师研究参考, 不构成对合同效力或案件结果的任何承诺或预测。"
)

DISCLAIMER_SHORT = "本审查为客观风险标注, 不构成法律意见, 不替代律师判断。"


# ===== 风险等级 (constants) =====

RISK_LEVEL_FATAL = "fatal"
RISK_LEVEL_MAJOR = "major"
RISK_LEVEL_ADVISORY = "advisory"
RISK_LEVEL_OK = "ok"

RISK_LEVEL_DISPLAY = {
    RISK_LEVEL_FATAL: ("致命", "red"),
    RISK_LEVEL_MAJOR: ("重大", "yellow"),
    RISK_LEVEL_ADVISORY: ("建议", "blue"),
    RISK_LEVEL_OK: ("合规", "green"),
}


# ===== 风险分类 (constants) =====

RISK_CATEGORIES = [
    "显失公平",
    "违法条款",
    "重大遗漏",
    "隐含义务",
    "争议管辖不利",
    "表述模糊",
    "可优化",
    "金额异常",
    "期限异常",
    "举证困难",
    "解除权失衡",
    "违约金过高",
    "管辖连接点异常",
    "其他",
]


# ===== CLI =====

if __name__ == "__main__":
    samples = [
        # PASS
        "该条款逾期违约金约定为月租金 5%/日, 年化约 1825%, 超出 LPR 四倍司法保护上限, 司法实践中通常被调减。",
        "本合同共审查 7 个条款, 其中存在 1 个致命风险条款 (逾期违约金过高) 与 1 个重大风险条款。",
        # FAIL high
        "本合同必败。",
        "该条款一定无效。",
        "对方将承担全部责任。",
        "司法实践中一定会被调减。",
    ]
    for s in samples:
        r = check_narrative(s)
        print(f"{r}\n  text: {s}\n  corrected: {r.corrected_text}\n")