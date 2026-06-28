"""
LexPrime 合同风险审查 Skill — 审查算法参考实现 (v0.1.0-draft)

T-REF-22: 类案子 Agent RPC 模式 (审查 + 风险分类 + 策略生成, 不污染主上下文)
T-REF-25: RAG 上下文压缩 (Token 超 8000 自动压)

W4 升级 (LanceDB + BGE 双路召回):
- 致命/重大风险条款 → 检索历史风险样本 (top 5), 引用为 retrieval_evidence
- 检索走本地 LanceDB (data/lancedb/), 零联网
- 降级: 索引未就位时, retrieval_evidence = []

设计原则:
1. **零联网**: 全部走本地 contracts + risk_annotations 数据
2. **条款优先**: 按"第X条"标号拆分条款, 每条款独立审查
3. **三级分类**: 致命 / 重大 / 建议 / 合规
4. **立场感知**: 律师立场 (甲方/乙方/丙方/审查方) 影响风险等级和策略方向
5. **Token 预算**: 全链路 8000 token 硬上限
6. **语言规范**: 任何 narrative 字段必须通过 language_guard
7. **双路召回 (W4)**: LLM 规则审查 + LanceDB 相似风险样本

依赖 (见 requirements.txt):
- lancedb>=0.6
- sentence-transformers>=2.7
- tiktoken>=0.7
- numpy>=1.26
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Tuple

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False

try:
    import tiktoken
    _ENC = tiktoken.get_encoding("cl100k_base")
except Exception:  # 离线兜底
    _ENC = None


def _percentile(values: List[float], p: float) -> float:
    """纯 Python percentile 实现 (numpy 不可用时降级)。"""
    if not values:
        return 0.0
    if _HAS_NUMPY:
        return float(np.percentile(values, p))
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return float(s[f])
    return float(s[f] + (s[c] - s[f]) * (k - f))


from skills.contract_review.language_guard import (  # noqa: E402
    check_narrative,
    DISCLAIMER_FULL,
    template_risk_summary,
    template_negotiation_advice,
    sanitize_input,
    assert_no_bypass,
    RISK_LEVEL_FATAL,
    RISK_LEVEL_MAJOR,
    RISK_LEVEL_ADVISORY,
    RISK_LEVEL_OK,
)


# ===== W4: 索引懒加载 =====

_RISK_INDEX_SINGLETON: Optional[Any] = None
_RISK_INDEX_FAILED: bool = False


def _get_risk_index():
    """懒加载合同风险索引 (W4 LanceDB)。

    Returns:
        ContractRiskIndex 实例, 或 None (索引未就位 / 加载失败)
    """
    global _RISK_INDEX_SINGLETON, _RISK_INDEX_FAILED
    if _RISK_INDEX_SINGLETON is not None:
        return _RISK_INDEX_SINGLETON
    if _RISK_INDEX_FAILED:
        return None
    try:
        # 相对路径 (从 cases-crawler/ 启)
        from core.lancedb_index import (  # noqa: PLC0415
            IndexConfig,
            get_contract_index,
        )
        cfg = IndexConfig(
            lancedb_path="data/lancedb",
            default_top_k=5,
            max_top_k=10,
        )
        idx = get_contract_index(cfg)
        if idx.has_risks():
            _RISK_INDEX_SINGLETON = idx
            return idx
        # 索引为空, 标记失败, 后续 fallback
        _RISK_INDEX_FAILED = True
        return None
    except Exception:  # noqa: BLE001
        _RISK_INDEX_FAILED = True
        return None


def reset_risk_index() -> None:
    """重置风险索引单例 (测试用)。"""
    global _RISK_INDEX_SINGLETON, _RISK_INDEX_FAILED
    _RISK_INDEX_SINGLETON = None
    _RISK_INDEX_FAILED = False
    try:
        from core.lancedb_index import reset_index as _reset  # noqa: PLC0415
        _reset()
    except Exception:  # noqa: BLE001
        pass


def set_risk_index(idx: Any) -> None:
    """强制设置索引 (测试注入)。"""
    global _RISK_INDEX_SINGLETON, _RISK_INDEX_FAILED
    _RISK_INDEX_SINGLETON = idx
    _RISK_INDEX_FAILED = False


# ===== Token 计数 (T-REF-25) =====

def count_tokens(text: str) -> int:
    """统计 token 数。优先 tiktoken, 否则按 1.5 字符/token 估算 (中文)。"""
    if _ENC is not None:
        return len(_ENC.encode(text))
    return max(1, int(len(text) / 1.5))


# ===== 配置 =====

@dataclass
class ReviewerConfig:
    model: str = "qwen2.5:7b"
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    context_token_budget: int = 8000
    latency_p95_target_ms: int = 2000
    max_clauses: int = 200
    use_compression_threshold: float = 0.9
    # W4: 相似风险样本检索 top_k (双路召回)
    retrieval_top_k: int = 5
    retrieval_enabled: bool = True


# ===== 输入 =====

CONTRACT_TYPES = ["房屋租赁", "借款合同", "劳动合同", "服务合同",
                   "销售合同", "合伙协议", "委托代理", "其他"]
STANCES = ["甲方", "乙方", "丙方", "审查方"]


@dataclass
class ReviewerInput:
    contract_type: str
    contract_text: str = ""
    stance: str = "审查方"
    industry: str = ""
    amount: Optional[float] = None
    jurisdiction: str = ""
    focus_areas: List[str] = field(default_factory=list)
    include_suggestion: bool = True
    include_negotiation_strategy: bool = True
    include_version_diff: bool = False
    language: str = "zh-CN"
    case_id: Optional[str] = None


# ===== 风险关键词库 (规则层兜底) =====

# 致命风险关键词 (出现即标记 fatal, 置信度高)
FATAL_KEYWORDS = {
    "违约金过高": [
        r"违约金.{0,5}(?:月|年|日|百分之|万分之).{0,15}",
        r"逾期.{0,5}按.{0,20}加收.{0,10}违约金",
    ],
    "违法条款": [
        r"(?:本|该)\s*合同.{0,5}不得.{0,10}解除",
        r"(?:违反|违背).{0,10}无效",
    ],
    "重大遗漏": [
        r"(?:争议|管辖).{0,3}(?:条款)?(?:未)?(?:约定|规定|写明|明确)",
    ],
    "显失公平": [
        # "单方解除权" / "一方解除权" / "单方终止"
        r"(?:单方|一方)\s*(?:解除|终止)\s*(?:权|合同|本协议)?",
        # "甲方可单方解除合同"
        r"(?:甲方|乙方|丙方)\s*可\s*(?:单方|一方)\s*(?:解除|终止)",
    ],
}

# 重大风险关键词
MAJOR_KEYWORDS = {
    "争议管辖不利": [
        r"(?:甲方|乙方|丙方)\s*住所地",
        r"(?:甲方|乙方|丙方)\s*所在地\s*(?:法院|人民法院)",
    ],
    "隐含义务": [
        r"(?:配合|协助|支持).{0,10}(?:义务|责任)",
        r"(?:排他|独家).{0,10}(?:供应|代理|合作)",
    ],
}

# 建议风险关键词
ADVISORY_KEYWORDS = {
    "表述模糊": [
        r"合理期限",
        r"(?:尽快|及时|立即|马上)",
        r"(?:协商|友好协商)\s*解决",
    ],
    "可优化": [
        r"(?:未尽|未尽事宜).{0,5}(?:事宜|事项)",
    ],
}


# ===== 条款数据 =====

@dataclass
class Clause:
    clause_id: str
    clause_index: int
    clause_title: str
    clause_text: str


@dataclass
class ClauseReview:
    clause_id: str
    clause_index: int
    clause_title: str
    clause_text: str
    risk_level: str  # fatal / major / advisory / ok
    risk_categories: List[str]
    legal_basis: List[str]
    risk_description: str
    modification_suggestion: str = ""
    modified_clause_template: str = ""
    stance_impact: str = "中性"
    reviewer_confidence: float = 0.5


# ===== 条款拆分 (Clause Segmentation) =====

CLAUSE_PATTERN = re.compile(
    r"第\s*[一二三四五六七八九十百千零\d]+\s*[条章节]\s*([^\n]{0,80}?)(?:\n|$)",
    re.MULTILINE
)


def split_clauses(contract_text: str) -> List[Clause]:
    """按 '第X条' / '第X章' 标号拆分条款。

    兼容:
    - 第X条 / 第X章 / 第X节
    - 阿拉伯数字 (第一条) 与中文数字 (第一条)
    - 无标号合同: 按段落拆分 (fallback)
    """
    if not contract_text or not contract_text.strip():
        return []

    # 1) 按"第X条"标号拆分
    matches = list(CLAUSE_PATTERN.finditer(contract_text))
    clauses: List[Clause] = []

    if matches:
        for i, m in enumerate(matches):
            title = m.group(1).strip() if m.group(1) else f"条款{i+1}"
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(contract_text)
            text = contract_text[start:end].strip()
            # 限制单条长度
            text = text[:1000] if len(text) > 1000 else text
            clauses.append(Clause(
                clause_id=f"clause-{i+1}",
                clause_index=i+1,
                clause_title=title[:64],
                clause_text=text,
            ))
    else:
        # 2) Fallback: 按段落拆分
        paragraphs = [p.strip() for p in contract_text.split("\n\n") if p.strip()]
        for i, p in enumerate(paragraphs):
            clauses.append(Clause(
                clause_id=f"clause-{i+1}",
                clause_index=i+1,
                clause_title=f"段落{i+1}",
                clause_text=p[:1000],
            ))

    return clauses


# ===== 风险分类 (规则层 + LLM 层) =====

def classify_clause_risk(clause: Clause, ri: ReviewerInput) -> Tuple[str, List[str]]:
    """对单条条款做规则层风险分类 (LLM 失败时的兜底)。

    Returns:
        (risk_level, risk_categories)
    """
    text = clause.clause_text
    fatal_cats: List[str] = []
    major_cats: List[str] = []
    advisory_cats: List[str] = []

    # 致命关键词扫描
    for cat, patterns in FATAL_KEYWORDS.items():
        for p in patterns:
            if re.search(p, text):
                fatal_cats.append(cat)
                break

    # 重大关键词扫描
    for cat, patterns in MAJOR_KEYWORDS.items():
        for p in patterns:
            if re.search(p, text):
                major_cats.append(cat)
                break

    # 建议关键词扫描
    for cat, patterns in ADVISORY_KEYWORDS.items():
        for p in patterns:
            if re.search(p, text):
                advisory_cats.append(cat)
                break

    if fatal_cats:
        return RISK_LEVEL_FATAL, fatal_cats
    if major_cats:
        return RISK_LEVEL_MAJOR, major_cats
    if advisory_cats:
        return RISK_LEVEL_ADVISORY, advisory_cats
    return RISK_LEVEL_OK, []


# ===== 法条关联 (Legal Basis Lookup) =====

LEGAL_BASIS_MAP = {
    "违约金过高": [
        "《民法典》第五百八十五条",
        "《最高人民法院关于适用〈中华人民共和国民法典〉合同编通则若干问题的解释》第六十五条",
    ],
    "显失公平": [
        "《民法典》第一百五十一条",
    ],
    "违法条款": [
        "《民法典》第一百五十三条",
        "《民法典》第一百五十四条",
    ],
    "重大遗漏": [
        "《民法典》第四百七十条",
    ],
    "隐含义务": [
        "《民法典》第五百零九条",
    ],
    "争议管辖不利": [
        "《民事诉讼法》第二十四条",
        "《民事诉讼法》第三十五条",
    ],
    "表述模糊": [
        "《民法典》第四百六十六条",
    ],
    "解除权失衡": [
        "《民法典》第五百六十二条",
        "《民法典》第五百六十三条",
    ],
}


def lookup_legal_basis(risk_categories: List[str]) -> List[str]:
    """根据风险分类返回法条列表 (去重)。"""
    seen = set()
    out: List[str] = []
    for cat in risk_categories:
        for law in LEGAL_BASIS_MAP.get(cat, []):
            if law not in seen:
                seen.add(law)
                out.append(law)
    return out[:5]


# ===== W4: 相似风险样本检索 (双路召回) =====

@dataclass
class RetrievalEvidence:
    """相似风险样本引用 (W4 双路召回的输出)。"""
    sample_id: str               # 历史样本 ID (例: house-rent-residential-01::clause-3::ann-0)
    contract_id: str             # 历史合同 ID
    contract_type: str
    clause_id: str
    clause_title: str
    risk_level: str
    risk_categories: List[str]
    risk_description: str
    modification_suggestion: str
    similarity: float            # cosine 相似度 (0-1)
    source: str = "contract_risks_index"   # 数据源: contract_risks_index / fallback

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def retrieve_similar_risks(clause: Clause,
                              ri: ReviewerInput,
                              top_k: int = 5,
                              same_contract_type: bool = True) -> List[RetrievalEvidence]:
    """检索与某条新条款相似的历史风险样本 (W4)。

    用途: 致命/重大风险条款需要 "双路召回" ——
    - LLM 规则审查 (FATAL_KEYWORDS / MAJOR_KEYWORDS 正则) → 主结论
    - LanceDB 相似样本召回 (BGE embedding + cosine 距离) → 旁证

    Args:
        clause: 目标条款
        ri: 输入
        top_k: 返回 top_k
        same_contract_type: 是否只检索同合同类型 (默认 True, metadata 过滤)

    Returns:
        List[RetrievalEvidence] (按 similarity 降序, 0 条表示索引未就位)
    """
    idx = _get_risk_index()
    if idx is None:
        return []

    contract_type = ri.contract_type if same_contract_type else None
    try:
        hits = idx.search_similar_risks(
            clause.clause_text,
            top_k=top_k,
            risk_level=None,  # 不过滤, 让 fatal/major 都能召回
            contract_type=contract_type,
        )
    except Exception:  # noqa: BLE001
        return []

    out: List[RetrievalEvidence] = []
    for h in hits:
        out.append(RetrievalEvidence(
            sample_id=h.id,
            contract_id=h.contract_id,
            contract_type=h.contract_type,
            clause_id=h.clause_id,
            clause_title=h.clause_title,
            risk_level=h.risk_level,
            risk_categories=h.risk_categories,
            risk_description=h.risk_description,
            modification_suggestion=h.modification_suggestion,
            similarity=h.similarity,
        ))
    return out


# ===== 风险描述生成 =====

def generate_risk_description(clause: Clause, ri: ReviewerInput,
                               risk_categories: List[str]) -> str:
    """生成 risk_description (LLM 层骨架 + 模板降级)。

    Args:
        clause: 条款
        ri: 输入
        risk_categories: 风险分类标签
    """
    # 提取条款关键摘要 (前 80 字)
    summary = clause.clause_text[:80].replace("\n", " ").strip()
    if len(clause.clause_text) > 80:
        summary += "..."

    # 提取法条
    legal_basis_list = lookup_legal_basis(risk_categories)
    legal_basis = legal_basis_list[0] if legal_basis_list else "《民法典》相关条款"

    # 风险模式描述 (基于分类)
    risk_pattern_map = {
        "违约金过高": "约定金额过高, 超出司法保护上限 (LPR 四倍)",
        "显失公平": "权利义务严重失衡, 存在显失公平情形",
        "违法条款": "可能违反法律强制性规定, 存在效力瑕疵",
        "重大遗漏": "必备条款缺失, 易引发履行争议",
        "隐含义务": "暗含不利于合同方的不利义务",
        "争议管辖不利": f"管辖约定对 {ri.stance} 不利, 增加应诉成本",
        "表述模糊": "用语不精确, 易引发履行争议",
        "可优化": "条款可更专业 / 完整 / 平衡",
        "金额异常": "金额约定异常, 偏离市场水平",
        "期限异常": "期限约定异常, 显失公平",
        "举证困难": "条款设计导致举证困难",
        "解除权失衡": "解除权约定失衡, 一方权利义务不对等",
        "管辖连接点异常": "管辖连接点选择异常, 存在被驳回风险",
    }
    patterns = [risk_pattern_map.get(c, "存在相应法律风险") for c in risk_categories[:2]]

    # 立场影响
    stance_note = ""
    if ri.stance in ("甲方", "乙方", "丙方"):
        stance_note = f"对 {ri.stance} 立场而言, "
    risk_pattern = "; ".join(patterns)

    text = (
        f"{stance_note}该条款约定 {summary}。"
        f"在 {legal_basis} 框架下, 此类约定 {risk_pattern}。"
        f"具体后果取决于履行情况、双方证据及司法裁判, 建议结合个案评估。"
    )

    # 强制 language_guard 检查
    r = check_narrative(text)
    if not r.passed:
        text = r.corrected_text

    return text


def generate_modification_suggestion(clause: Clause, ri: ReviewerInput,
                                       risk_categories: List[str]) -> str:
    """生成修改建议。"""
    if not risk_categories:
        return ""

    cat = risk_categories[0]
    suggestion_map = {
        "违约金过高": (
            "建议修改违约金计算方式为 '逾期 × LPR × 1.5 倍' 或 '逾期 × 万分之五/日' 等司法保护上限内表述, "
            "避免约定过高金额导致司法调减。"
        ),
        "显失公平": (
            "建议区分法定解除与违约解除, 增加 '因对方违约导致守约方行使法定解除权的, 不承担解约违约金' 条款, "
            "平衡双方权利义务。"
        ),
        "违法条款": (
            "建议删除违反法律强制性规定的表述, 或调整为符合《民法典》相关条款的合规表述, "
            "避免条款被认定无效。"
        ),
        "重大遗漏": (
            "建议补充缺失的必备条款 (如价款 / 履行期限 / 违约责任 / 争议解决), "
            "降低履行争议风险。"
        ),
        "争议管辖不利": (
            "建议修改为 '房屋所在地' / '合同签订地' 或约定仲裁条款, "
            "降低应诉成本。"
        ),
        "表述模糊": (
            "建议将模糊表述 (如 '合理期限') 替换为具体数值 (如 '30 日内'), "
            "避免履行争议。"
        ),
        "解除权失衡": (
            "建议增加法定解除权与违约解除权的区分, 平衡双方解除权, "
            "避免单方权利过大。"
        ),
    }
    return suggestion_map.get(cat, "建议结合具体情况, 优化条款表述。")


def generate_modified_clause_template(clause: Clause, ri: ReviewerInput,
                                       risk_categories: List[str]) -> str:
    """生成修改后的条款模板 (LexPrime 文书生成器格式)。"""
    if RISK_LEVEL_FATAL not in (RISK_LEVEL_FATAL,):  # 仅致命必填
        return ""
    if not risk_categories:
        return ""

    cat = risk_categories[0]
    template_map = {
        "违约金过高": (
            f"{clause.clause_title}: 乙方应按约定时间支付租金 / 价款。"
            f"逾期支付的, 自逾期之日起, 按当期应付金额为基数, "
            f"按全国银行间同业拆借中心公布的同期 LPR 的 1.5 倍计算逾期违约金, "
            f"直至实际清偿之日止。"
        ),
        "争议管辖不利": (
            f"{clause.clause_title}: 因本合同发生的争议, 双方协商不成的, "
            f"任何一方均可向房屋所在地或合同签订地人民法院提起诉讼, "
            f"或向上海仲裁委员会申请仲裁。"
        ),
        "解除权失衡": (
            f"{clause.clause_title}: 因一方违约导致对方行使法定解除权的, "
            f"守约方有权要求违约方赔偿实际损失, 但不承担本合同约定的解约违约金。"
            f"因不可归责于双方的事由导致合同无法履行的, 双方互不承担违约责任。"
        ),
    }
    return template_map.get(cat, "")


def calculate_stance_impact(clause: Clause, ri: ReviewerInput,
                              risk_categories: List[str]) -> str:
    """基于立场评估风险影响。"""
    if not risk_categories:
        return "中性"

    # 管辖不利 / 违约金过高 对乙方通常不利
    unfavorable_to_乙方 = {"争议管辖不利", "违约金过高", "解除权失衡", "显失公平", "重大遗漏"}
    if ri.stance == "乙方" and any(c in unfavorable_to_乙方 for c in risk_categories):
        return "不利"
    if ri.stance == "甲方" and any(c in unfavorable_to_乙方 for c in risk_categories):
        return "有利"

    return "需结合上下文判断"


# ===== 上下文压缩 (T-REF-25) =====

@dataclass
class CompressionTrace:
    raw_token_count: int
    compressed_token_count: int
    compression_strategy: str  # none / top_k_truncate / summary_extract / hierarchical
    compression_ratio: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def compress_clauses(clauses: List[Clause], budget: int = 8000) -> tuple[List[Clause], CompressionTrace]:
    """如果条款序列化后 token > budget, 自动压缩。

    策略优先级:
    1. top_k_truncate: 截取前 N 条 (优先)
    2. summary_extract: 截断 clause_text 到 200 字
    3. hierarchical: 按风险等级保留 (致命 > 重大 > 建议 > 合规)
    """
    def clause_to_text(c: Clause) -> str:
        return f"{c.clause_id} {c.clause_title} {c.clause_text}"

    raw_tokens = sum(count_tokens(clause_to_text(c)) for c in clauses)
    if raw_tokens <= budget:
        return clauses, CompressionTrace(raw_tokens, raw_tokens, "none", 1.0)

    # 策略 1: top_k_truncate
    halved = clauses[: max(50, len(clauses) // 2)]
    truncated_tokens = sum(count_tokens(clause_to_text(c)) for c in halved)
    if truncated_tokens <= budget:
        return halved, CompressionTrace(raw_tokens, truncated_tokens, "top_k_truncate",
                                          truncated_tokens / raw_tokens)

    # 策略 2: summary_extract
    for c in halved:
        if len(c.clause_text) > 200:
            c.clause_text = c.clause_text[:200] + "…"
    extracted_tokens = sum(count_tokens(clause_to_text(c)) for c in halved)
    if extracted_tokens <= budget:
        return halved, CompressionTrace(raw_tokens, extracted_tokens, "summary_extract",
                                          extracted_tokens / raw_tokens)

    # 策略 3: hierarchical — 按风险等级保留 (此处因为还没审查, 按 clause_index 保留代表性)
    keep: List[Clause] = []
    step = max(1, len(halved) // 50)
    for i in range(0, len(halved), step):
        keep.append(halved[i])
    hier_tokens = sum(count_tokens(clause_to_text(c)) for c in keep)
    return keep, CompressionTrace(raw_tokens, hier_tokens, "hierarchical",
                                    hier_tokens / raw_tokens)


# ===== 风险汇总 =====

def compute_risk_summary(clause_reviews: List[ClauseReview]) -> Dict[str, Any]:
    """生成 risk_summary。"""
    fatal_count = sum(1 for r in clause_reviews if r.risk_level == RISK_LEVEL_FATAL)
    major_count = sum(1 for r in clause_reviews if r.risk_level == RISK_LEVEL_MAJOR)
    advisory_count = sum(1 for r in clause_reviews if r.risk_level == RISK_LEVEL_ADVISORY)
    ok_count = sum(1 for r in clause_reviews if r.risk_level == RISK_LEVEL_OK)

    if fatal_count > 0:
        overall = "high"
    elif major_count > 0:
        overall = "medium"
    else:
        overall = "low"

    # top_risk_categories
    cat_count: Dict[str, int] = {}
    for r in clause_reviews:
        for c in r.risk_categories:
            cat_count[c] = cat_count.get(c, 0) + 1
    top_cats = [{"category": k, "count": v} for k, v in
                sorted(cat_count.items(), key=lambda x: -x[1])[:5]]

    # narrative (LLM 生成, 强制 language_guard)
    top_cat_names = [c["category"] for c in top_cats[:3]]
    narrative = template_risk_summary(
        total=len(clause_reviews),
        fatal=fatal_count,
        major=major_count,
        advisory=advisory_count,
        top_categories=top_cat_names,
    )

    # 强制 language_guard 检查 (≤ 3 次重试)
    for _ in range(3):
        chk = check_narrative(narrative)
        if chk.passed:
            break
        narrative = chk.corrected_text
    if not check_narrative(narrative).passed:
        narrative = template_risk_summary(
            len(clause_reviews), fatal_count, major_count, advisory_count, top_cat_names
        )

    # 强校验
    try:
        assert_no_bypass(narrative, source_fields={"contract_type": clause_reviews[0].clause_title if clause_reviews else ""})
    except ValueError:
        narrative = f"样本 {len(clause_reviews)} 条, 致命 {fatal_count} 条, 重大 {major_count} 条。"

    return {
        "fatal_count": fatal_count,
        "major_count": major_count,
        "advisory_count": advisory_count,
        "ok_count": ok_count,
        "overall_risk_level": overall,
        "narrative": narrative,
        "top_risk_categories": top_cats,
    }


# ===== 谈判策略生成 =====

def compute_negotiation_strategy(clause_reviews: List[ClauseReview],
                                   ri: ReviewerInput) -> Dict[str, Any]:
    """生成谈判策略。"""
    # priority_clauses: 按 fatal > major > advisory 排序
    priority: List[str] = []
    for r in clause_reviews:
        if r.risk_level == RISK_LEVEL_FATAL:
            priority.append(r.clause_id)
    for r in clause_reviews:
        if r.risk_level == RISK_LEVEL_MAJOR:
            priority.append(r.clause_id)
    for r in clause_reviews:
        if r.risk_level == RISK_LEVEL_ADVISORY:
            priority.append(r.clause_id)
    priority = priority[:10]

    # leverage_points: 仅 fatal/major 条款
    leverage_points: List[Dict[str, Any]] = []
    for r in clause_reviews:
        if r.risk_level not in (RISK_LEVEL_FATAL, RISK_LEVEL_MAJOR):
            continue
        leverage_points.append({
            "clause_id": r.clause_id,
            "leverage": f"该条款{r.risk_categories[0] if r.risk_categories else '存在风险'}, 司法实践中通常被调减 / 修正, 对方实际收益与约定差距大",
            "trade_off": "可承诺按时履行换取条款修改",
        })
        if len(leverage_points) >= 5:
            break

    # walk_away_signals: 仅 fatal 条款
    walk_away: List[str] = []
    for r in clause_reviews:
        if r.risk_level == RISK_LEVEL_FATAL and "违法" in (r.risk_categories[0] if r.risk_categories else ""):
            walk_away.append(r.clause_id)
    walk_away = walk_away[:3]

    # stance_specific_advice
    stance_advice = template_negotiation_advice(
        stance=ri.stance,
        priority_clauses=priority,
        leverage_count=len(leverage_points),
        walk_away_count=len(walk_away),
    )

    # 强制 language_guard
    for _ in range(3):
        chk = check_narrative(stance_advice)
        if chk.passed:
            break
        stance_advice = chk.corrected_text
    if not check_narrative(stance_advice).passed:
        stance_advice = template_negotiation_advice(ri.stance, priority, len(leverage_points), len(walk_away))

    return {
        "priority_clauses": priority,
        "leverage_points": leverage_points,
        "walk_away_signals": walk_away,
        "stance_specific_advice": stance_advice,
    }


# ===== UI 提示 =====

def compute_traffic_light(risk_summary: Dict[str, Any]) -> str:
    if risk_summary["fatal_count"] > 0:
        return "red"
    if risk_summary["major_count"] > 0:
        return "yellow"
    if risk_summary["advisory_count"] > 0 or risk_summary.get("ok_count", 0) > 0:
        return "green"
    return "gray"


# ===== 主审查入口 =====

@dataclass
class ReviewerOutput:
    query_meta: Dict[str, Any]
    clause_reviews: List[Dict[str, Any]]
    risk_summary: Dict[str, Any]
    negotiation_strategy: Dict[str, Any]
    version_diff: Optional[Dict[str, Any]]
    trajectory: Dict[str, Any]
    disclaimer: str
    ui_hints: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_meta": self.query_meta,
            "clause_reviews": self.clause_reviews,
            "risk_summary": self.risk_summary,
            "negotiation_strategy": self.negotiation_strategy,
            "version_diff": self.version_diff,
            "trajectory": self.trajectory,
            "disclaimer": self.disclaimer,
            "ui_hints": self.ui_hints,
        }


def run_skill(ri: ReviewerInput,
              config: Optional[ReviewerConfig] = None) -> ReviewerOutput:
    """合同风险审查 Skill 主入口 (子 Agent RPC 调用)。"""
    if config is None:
        config = ReviewerConfig()

    # 校验 contract_type
    if ri.contract_type not in CONTRACT_TYPES:
        ri.contract_type = "其他"

    # 校验 stance
    if ri.stance not in STANCES:
        ri.stance = "审查方"

    # 截断 contract_text
    if len(ri.contract_text) > 50000:
        ri.contract_text = ri.contract_text[:50000]

    # 输入消毒 (防止 user input 携带禁用词污染 narrative)
    ri.contract_text = sanitize_input(ri.contract_text)
    ri.industry = sanitize_input(ri.industry)

    t0 = time.time()

    # Step 1: 条款拆分
    raw_clauses = split_clauses(ri.contract_text)
    if len(raw_clauses) > config.max_clauses:
        raw_clauses = raw_clauses[:config.max_clauses]

    # Step 2: 上下文压缩
    clauses, trace = compress_clauses(raw_clauses, budget=config.context_token_budget)

    # Step 3: 条款级审查
    clause_reviews: List[ClauseReview] = []
    retrieval_total = 0
    retrieval_used = 0
    for clause in clauses:
        risk_level, risk_categories = classify_clause_risk(clause, ri)

        # 生成 risk_description (强制 language_guard)
        risk_desc = generate_risk_description(clause, ri, risk_categories)

        # 生成修改建议 (致命/重大必填)
        mod_suggestion = ""
        mod_template = ""
        if risk_level in (RISK_LEVEL_FATAL, RISK_LEVEL_MAJOR):
            mod_suggestion = generate_modification_suggestion(clause, ri, risk_categories)
            if risk_level == RISK_LEVEL_FATAL:
                mod_template = generate_modified_clause_template(clause, ri, risk_categories)

        # 法条关联
        legal_basis = lookup_legal_basis(risk_categories)

        # 立场影响
        stance_impact = calculate_stance_impact(clause, ri, risk_categories)

        # 置信度 (基于关键词命中数)
        confidence = min(1.0, 0.5 + 0.1 * len(risk_categories))

        # W4: 致命/重大风险条款 → 检索相似历史风险样本 (双路召回)
        retrieval_evidence: List[Dict[str, Any]] = []
        if config.retrieval_enabled and risk_level in (RISK_LEVEL_FATAL, RISK_LEVEL_MAJOR):
            retrieval_total += 1
            evidences = retrieve_similar_risks(
                clause, ri, top_k=config.retrieval_top_k, same_contract_type=True
            )
            if evidences:
                retrieval_used += 1
                # 保留 top 3, 避免 narrative 冗长
                retrieval_evidence = [e.to_dict() for e in evidences[:3]]
                # 提升 confidence (有旁证)
                confidence = min(1.0, confidence + 0.1 * len(retrieval_evidence))

        clause_reviews.append(ClauseReview(
            clause_id=clause.clause_id,
            clause_index=clause.clause_index,
            clause_title=clause.clause_title,
            clause_text=clause.clause_text,
            risk_level=risk_level,
            risk_categories=risk_categories,
            legal_basis=legal_basis,
            risk_description=risk_desc,
            modification_suggestion=mod_suggestion,
            modified_clause_template=mod_template,
            stance_impact=stance_impact,
            reviewer_confidence=confidence,
        ))
        # 把 retrieval_evidence 挂到 review 上 (动态属性, 不破坏 ClauseReview schema)
        clause_reviews[-1].retrieval_evidence = retrieval_evidence  # type: ignore[attr-defined]

    t_review_ms = int((time.time() - t0) * 1000)

    # Step 4: 风险汇总
    risk_summary = compute_risk_summary(clause_reviews)

    # Step 5: 谈判策略
    neg_strategy = compute_negotiation_strategy(clause_reviews, ri)

    # Step 6: 版本比对 (可选)
    version_diff = None
    if ri.include_version_diff:
        version_diff = {
            "baseline_version_id": None,
            "compared_version_id": None,
            "added_clauses": [],
            "removed_clauses": [],
            "modified_clauses": [],
            "summary": "版本比对需要历史版本数据, 当前未提供。",
        }

    # Step 7: UI 提示
    traffic = compute_traffic_light(risk_summary)

    # Step 8 (W4): 整体检索统计
    retrieval_stats = {
        "index_enabled": _get_risk_index() is not None,
        "embedding_model": config.embedding_model,
        "fatal_major_clauses": retrieval_total,
        "clauses_with_evidence": retrieval_used,
        "recall_pct": round(retrieval_used / retrieval_total * 100, 2) if retrieval_total else 0.0,
    }

    return ReviewerOutput(
        query_meta={
            "contract_type": ri.contract_type,
            "stance": ri.stance,
            "industry": ri.industry,
            "jurisdiction": ri.jurisdiction,
            "searched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime()),
            "latency_ms": t_review_ms,
            "total_clauses": len(raw_clauses),
            "returned_count": len(clauses),
            "model_used": config.model,
            "embedding_model": config.embedding_model,
        },
        clause_reviews=[_serialize_review(r) for r in clause_reviews],
        risk_summary=risk_summary,
        negotiation_strategy=neg_strategy,
        version_diff=version_diff,
        trajectory=trace.to_dict(),
        disclaimer=DISCLAIMER_FULL,
        ui_hints={
            "traffic_light": traffic,
            "show_diff_panel": ri.include_version_diff,
            "show_strategy_modal": ri.include_negotiation_strategy,
            "highlight_clauses": [r.clause_id for r in clause_reviews
                                   if r.risk_level in (RISK_LEVEL_FATAL, RISK_LEVEL_MAJOR)][:10],
            "export_format": ["word", "pdf", "markdown"],
            "retrieval_stats": retrieval_stats,
        },
    )


def _serialize_review(r: ClauseReview) -> Dict[str, Any]:
    """把 ClauseReview 转 dict, 附带 retrieval_evidence 字段 (W4)。"""
    d = asdict(r)
    # 动态属性 (W4 双路召回) 不会进 asdict, 手动补
    d["retrieval_evidence"] = getattr(r, "retrieval_evidence", [])
    return d


# ===== CLI =====

if __name__ == "__main__":
    # 自检: 用示例合同跑一遍
    sample_contract = """
第一条 租赁标的
甲方将位于上海市浦东新区某某路 123 号 1502 室房屋出租给乙方使用。

第二条 租赁期限
租赁期自 2026 年 7 月 1 日起至 2027 年 6 月 30 日止。

第三条 租金及支付
月租金为人民币 5000 元整, 逾期支付的, 每逾期一天, 按月租金的 5% 加收违约金。

第四条 押金
乙方向甲方支付押金人民币 10000 元整, 30 日内无息退还。

第五条 提前解约
任何一方提前解除合同的, 须向守约方支付相当于 6 个月租金的违约金。

第六条 争议管辖
因本合同发生的争议, 双方协商不成的, 任何一方均可向甲方住所地人民法院提起诉讼。
"""

    ri = ReviewerInput(
        contract_type="房屋租赁",
        contract_text=sample_contract,
        stance="乙方",
        jurisdiction="上海",
    )
    out = run_skill(ri)
    import json
    print(json.dumps(out.to_dict(), ensure_ascii=False, indent=2)[:3500])