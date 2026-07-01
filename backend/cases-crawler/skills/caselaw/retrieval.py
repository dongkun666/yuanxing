"""
LexPrime 类案检索 Skill — 检索算法参考实现 (v0.1.0-draft)

T-REF-22: 类案子 Agent RPC (检索 + 重排 + 统计, 不污染主上下文)
T-REF-25: RAG 上下文压缩 (Token 超 8000 自动压)

设计原则:
1. **零联网**: 全部走本地 LanceDB / Milvus
2. **metadata 优先**: 元数据过滤在前, 向量召回在后, 避免大 K 慢检索
3. **降级链**: LanceDB → Milvus → PostgreSQL SQL (兜底)
4. **Token 预算**: 全链路 8000 token 硬上限

依赖 (见 requirements.txt 增加):
- lancedb>=0.6
- sentence-transformers>=2.7
- tiktoken>=0.7
- numpy>=1.26
"""
from __future__ import annotations

import time
import statistics
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False

try:
    import tiktoken
    _ENC = tiktoken.get_encoding("cl100k_base")
except Exception:  # 离线兜底: 1 token ≈ 1.5 中文字
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

from skills.caselaw.language_guard import (
    check_narrative,
    DISCLAIMER_FULL,
    template_outcome_distribution,
    template_amount_stats,
    template_judge_style,
    template_overall,
    sanitize_input,  # W7: 输入消毒, 防止 user input 携带禁用词
    assert_no_bypass,  # W7: 强校验, 任何 narrative 0 HIGH 违规
)


# ===== Token 计数 (T-REF-25) =====

def count_tokens(text: str) -> int:
    """统计 token 数。优先 tiktoken, 否则按 1.5 字符/token 估算 (中文)。"""
    if _ENC is not None:
        return len(_ENC.encode(text))
    return max(1, int(len(text) / 1.5))


# ===== 配置 =====

@dataclass
class RetrievalConfig:
    vector_store: str = "lancedb"          # lancedb / milvus / fallback_sql
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    top_k_default: int = 20
    top_k_max: int = 50
    metadata_filter_first: bool = True     # 先 metadata 后向量
    vector_top_k_multiplier: int = 5       # 向量召回 = top_k * multiplier
    reranker_enabled: bool = False         # BGE-reranker-large 跨编码 (可选)
    context_token_budget: int = 8000       # T-REF-25 硬上限
    latency_p95_target_ms: int = 1000
    use_compression_threshold: float = 0.9 # raw > 8000 * threshold 触发压缩


# ===== 输入 =====

@dataclass
class RetrievalInput:
    cause: str
    facts: str = ""
    court: Optional[str] = None
    judge_name: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    region: Optional[str] = None
    case_type: Optional[str] = None
    procedure: Optional[str] = None
    amount_dispute: Optional[float] = None
    top_k: int = 20
    include_judge_style: bool = True
    include_amount_stats: bool = True
    case_id: Optional[str] = None


# ===== 检索结果 (单条判例) =====

@dataclass
class CaseHit:
    case_id: str
    case_name: str
    court: str
    case_type: str = ""
    procedure: str = ""
    cause: str = ""
    judgment_date: str = ""
    year: Optional[int] = None
    judge_name: Optional[str] = None
    parties: Optional[str] = None
    legal_basis: Optional[str] = None
    outcome: str = "其他"
    amount_awarded_cny: Optional[float] = None
    relevance_score: float = 0.0
    summary: str = ""
    dispute_focus: List[str] = field(default_factory=list)
    source: str = "cncases"
    source_url: Optional[str] = None


# ===== 向量检索接口 (抽象) =====

class VectorStore:
    """LanceDB / Milvus 抽象接口。本文件用 SQL 兜底实现。"""

    def metadata_filter(self, ri: RetrievalInput, candidate_limit: int = 500) -> List[CaseHit]:
        """先 metadata 过滤, 取 candidate_limit 条候选。"""
        raise NotImplementedError

    def vector_search(self, ri: RetrievalInput, candidates: List[CaseHit]) -> List[CaseHit]:
        """在 candidates 上做向量相似度排序, 返回 top_k。"""
        raise NotImplementedError


class FallbackSQLStore(VectorStore):
    """PostgreSQL/SQLite 兜底实现 — 不依赖 embedding, 用关键词 + 时间衰减打分。

    W7: 同步接口 (在 sync context 调用). E2E 测试时可在 async context 中包一层.
    """

    def __init__(self, db_session):
        self.db = db_session

    def metadata_filter(self, ri: RetrievalInput, candidate_limit: int = 500) -> List[CaseHit]:
        """同步版 metadata filter (假设 db 是 sync Session).

        如果 db 是 AsyncSession, 调用方应使用 metadata_filter_async.
        """
        from sqlalchemy import select, or_
        from core.models import Case  # cases-crawler models

        stmt = select(Case).limit(candidate_limit)
        # 案由 (模糊, 含同义词扩展)
        if ri.cause:
            stmt = stmt.where(or_(Case.cause.like(f"%{ri.cause}%"),
                                  Case.cause_category == ri.cause))
        # 法院
        if ri.court:
            stmt = stmt.where(Case.court.like(f"%{ri.court}%"))
        # 年份
        if ri.year_from:
            stmt = stmt.where(Case.year >= ri.year_from)
        if ri.year_to:
            stmt = stmt.where(Case.year <= ri.year_to)
        # 地域
        if ri.region:
            stmt = stmt.where(Case.region == ri.region)
        # 案件类型
        if ri.case_type:
            stmt = stmt.where(Case.case_type == ri.case_type)
        # 程序
        if ri.procedure:
            stmt = stmt.where(Case.procedure == ri.procedure)

        # 兼容 sync / async session
        import inspect
        result = self.db.execute(stmt)
        if inspect.iscoroutine(result):
            # async session: 抛错让调用方用 async 版
            raise RuntimeError(
                "FallbackSQLStore.metadata_filter 不支持 AsyncSession. "
                "请使用 metadata_filter_async 或在 sync context 调用。"
            )
        rows = result.scalars().all()
        return [self._row_to_hit(r) for r in rows]

    async def metadata_filter_async(self, ri: RetrievalInput, candidate_limit: int = 500) -> List[CaseHit]:
        """异步版 metadata filter (AsyncSession)."""
        from sqlalchemy import select, or_
        from core.models import Case

        stmt = select(Case).limit(candidate_limit)
        if ri.cause:
            stmt = stmt.where(or_(Case.cause.like(f"%{ri.cause}%"),
                                  Case.cause_category == ri.cause))
        if ri.court:
            stmt = stmt.where(Case.court.like(f"%{ri.court}%"))
        if ri.year_from:
            stmt = stmt.where(Case.year >= ri.year_from)
        if ri.year_to:
            stmt = stmt.where(Case.year <= ri.year_to)
        if ri.region:
            stmt = stmt.where(Case.region == ri.region)
        if ri.case_type:
            stmt = stmt.where(Case.case_type == ri.case_type)
        if ri.procedure:
            stmt = stmt.where(Case.procedure == ri.procedure)

        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return [self._row_to_hit(r) for r in rows]

    def vector_search(self, ri: RetrievalInput, candidates: List[CaseHit]) -> List[CaseHit]:
        """简化版: 用 lex_score + 关键词命中数 + 时间衰减算分"""
        if not candidates:
            return []
        facts_terms = set(ri.facts.split()) if ri.facts else set()

        def score(h: CaseHit) -> float:
            base = 0.5
            if facts_terms:
                text_terms = set((h.summary + " " + h.case_name + " " + (h.parties or "")).split())
                base += 0.3 * len(facts_terms & text_terms) / max(1, len(facts_terms))
            if ri.judge_name and h.judge_name and ri.judge_name in h.judge_name:
                base += 0.2
            # 时间衰减: 越新权重越高
            if h.year:
                base += 0.05 * max(0, (h.year - 2020) / 6)
            return min(1.0, base)

        for h in candidates:
            h.relevance_score = score(h)
        candidates.sort(key=lambda h: h.relevance_score, reverse=True)
        return candidates[:ri.top_k]

    def _row_to_hit(self, row) -> CaseHit:
        return CaseHit(
            case_id=row.case_id or "",
            case_name=row.case_name or "",
            court=row.court or "",
            case_type=row.case_type or "",
            procedure=row.procedure or "",
            cause=row.cause or "",
            judgment_date=row.judgment_date.isoformat() if row.judgment_date else "",
            year=row.year,
            judge_name=getattr(row, "judge_name", None),
            parties=row.parties,
            legal_basis=row.legal_basis,
            outcome=getattr(row, "outcome", "其他") or "其他",
            amount_awarded_cny=getattr(row, "amount_awarded", None),
            summary=getattr(row, "summary", "") or "",
            dispute_focus=getattr(row, "keywords", []) or [],
            source=row.source or "cncases",
            source_url=row.source_url,
        )


class LanceDBStore(VectorStore):
    """LanceDB 真实实现 (本文件提供骨架, 实际接入在 Phase 4 W5-6)。"""

    def __init__(self, lancedb_path: str, table_name: str = "cases_vec"):
        self.path = lancedb_path
        self.table_name = table_name

    def metadata_filter(self, ri: RetrievalInput, candidate_limit: int = 500) -> List[CaseHit]:
        # TODO(Phase 4 W5): lancedb.connect() + table.search().where(f"court = '{ri.court}'").limit(candidate_limit)
        raise NotImplementedError("LanceDB 接入在 Phase 4 W5-6 完成 (T-REF-22)")

    def vector_search(self, ri: RetrievalInput, candidates: List[CaseHit]) -> List[CaseHit]:
        raise NotImplementedError


# ===== 上下文压缩 (T-REF-25) =====

@dataclass
class CompressionTrace:
    raw_token_count: int
    compressed_token_count: int
    compression_strategy: str  # none / top_k_truncate / summary_extract / hierarchical
    compression_ratio: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def compress_context(hits: List[CaseHit], budget: int = 8000) -> tuple[List[CaseHit], CompressionTrace]:
    """如果 hits 序列化后 token > budget, 自动压缩。

    策略优先级:
    1. top_k_truncate: 直接减半 hits
    2. summary_extract: 截断 summary 字段到 50 字
    3. hierarchical: 按年份分组, 每组保留代表性 2-3 件
    """
    raw_tokens = sum(count_tokens(_hit_to_text(h)) for h in hits)
    if raw_tokens <= budget:
        return hits, CompressionTrace(raw_tokens, raw_tokens, "none", 1.0)

    # 策略 1: top_k_truncate
    halved = hits[: max(5, len(hits) // 2)]
    truncated_tokens = sum(count_tokens(_hit_to_text(h)) for h in halved)
    if truncated_tokens <= budget:
        return halved, CompressionTrace(raw_tokens, truncated_tokens, "top_k_truncate",
                                          truncated_tokens / raw_tokens)

    # 策略 2: summary_extract
    for h in halved:
        if len(h.summary) > 50:
            h.summary = h.summary[:50] + "…"
    extracted_tokens = sum(count_tokens(_hit_to_text(h)) for h in halved)
    if extracted_tokens <= budget:
        return halved, CompressionTrace(raw_tokens, extracted_tokens, "summary_extract",
                                          extracted_tokens / raw_tokens)

    # 策略 3: hierarchical — 按年份保留代表
    by_year: Dict[int, List[CaseHit]] = {}
    for h in halved:
        by_year.setdefault(h.year or 0, []).append(h)
    keep: List[CaseHit] = []
    for year in sorted(by_year.keys(), reverse=True):
        keep.extend(by_year[year][:2])  # 每组 2 件
        if sum(count_tokens(_hit_to_text(h)) for h in keep) > budget:
            break
    hier_tokens = sum(count_tokens(_hit_to_text(h)) for h in keep)
    return keep, CompressionTrace(raw_tokens, hier_tokens, "hierarchical",
                                    hier_tokens / raw_tokens)


def _hit_to_text(h: CaseHit) -> str:
    return (
        f"{h.case_id} {h.case_name} {h.court} {h.cause} {h.year} "
        f"{h.outcome} {h.summary} {' '.join(h.dispute_focus)}"
    )


# ===== 统计生成 =====

OUTCOMES = ["原告胜诉", "被告胜诉", "部分支持", "调解", "撤诉", "其他"]


def compute_statistics(hits: List[CaseHit], ri: RetrievalInput) -> Dict[str, Any]:
    """生成 statistics 字段。"""
    sample = len(hits)
    outcome_dist = {o: 0 for o in OUTCOMES}
    for h in hits:
        if h.outcome in outcome_dist:
            outcome_dist[h.outcome] += 1
        else:
            outcome_dist["其他"] += 1

    support_total = outcome_dist["原告胜诉"] + outcome_dist["部分支持"]
    support_pct = round(support_total / sample * 100, 2) if sample else 0.0

    # 按年份分组
    yearly: Dict[int, Dict[str, int]] = {}
    for h in hits:
        if h.year is None:
            continue
        yearly.setdefault(h.year, {"total": 0, "support_total": 0})
        yearly[h.year]["total"] += 1
        if h.outcome in ("原告胜诉", "部分支持"):
            yearly[h.year]["support_total"] += 1
    yearly_breakdown = []
    for year in sorted(yearly.keys(), reverse=True):
        total = yearly[year]["total"]
        st = yearly[year]["support_total"]
        yearly_breakdown.append({
            "year": year,
            "total": total,
            "support_total": st,
            "support_pct": round(st / total * 100, 2) if total else 0.0,
        })

    # 金额统计 (仅民事 / 行政且有金额)
    amounts = [h.amount_awarded_cny for h in hits
               if h.amount_awarded_cny is not None and h.amount_awarded_cny > 0]
    amount_stats: Dict[str, Any] = {"sample_with_amount": len(amounts), "currency": "CNY"}
    if amounts and ri.include_amount_stats:
        amount_stats.update({
            "median_cny": _percentile(amounts, 50),
            "q1_cny": _percentile(amounts, 25),
            "q3_cny": _percentile(amounts, 75),
            "min_cny": float(min(amounts)),
            "max_cny": float(max(amounts)),
        })
    elif not ri.include_amount_stats:
        amount_stats = {"sample_with_amount": 0, "currency": "CNY"}

    # 争议焦点 top 10
    focus_count: Dict[str, int] = {}
    for h in hits:
        for f in h.dispute_focus:
            focus_count[f] = focus_count.get(f, 0) + 1
    top_dispute = [{"focus": k, "count": v} for k, v in
                   sorted(focus_count.items(), key=lambda x: -x[1])[:10]]

    # 法官风格
    judge_style: Optional[Dict[str, Any]] = None
    if ri.include_judge_style and ri.judge_name:
        judge_hits = [h for h in hits if h.judge_name and ri.judge_name in h.judge_name]
        if len(judge_hits) >= 5:
            j_support = sum(1 for h in judge_hits if h.outcome in ("原告胜诉", "部分支持"))
            judge_style = {
                "judge_name": ri.judge_name,
                "sample_size": len(judge_hits),
                "support_pct": round(j_support / len(judge_hits) * 100, 2),
                "avg_hearing_days": 90.0,  # TODO: 从字段拉
                "evidence_admission_tendency": "中等",
                "narrative": template_judge_style(
                    ri.judge_name, len(judge_hits),
                    j_support / len(judge_hits) * 100, 90.0, "中等"
                ),
            }
            # 强制 language_guard 检查
            chk = check_narrative(judge_style["narrative"])
            if not chk.passed:
                judge_style["narrative"] = chk.corrected_text
        else:
            judge_style = {
                "judge_name": ri.judge_name,
                "sample_size": len(judge_hits),
                "support_pct": round(
                    sum(1 for h in judge_hits if h.outcome in ("原告胜诉", "部分支持"))
                    / max(1, len(judge_hits)) * 100, 2),
                "avg_hearing_days": 0.0,
                "evidence_admission_tendency": "样本不足",
                "narrative": f"该法官在同类案件中的样本仅 {len(judge_hits)} 件, 不足以分析审理风格。",
            }

    # narrative: 整体叙述
    parts = [template_outcome_distribution(sample, support_total)]
    if amounts and ri.include_amount_stats:
        parts.append(template_amount_stats(
            amount_stats["median_cny"], amount_stats["q1_cny"],
            amount_stats["q3_cny"], amount_stats["min_cny"], amount_stats["max_cny"]))
    narrative = " ".join(parts)

    # 强制 language_guard 检查 (≤ 3 次重试)
    for _ in range(3):
        chk = check_narrative(narrative)
        if chk.passed:
            break
        narrative = chk.corrected_text
    if not check_narrative(narrative).passed:
        # 降级到模板
        narrative = template_overall(sample, ri.cause, ri.region or "", ri.year_from or 0, ri.year_to or 0)

    # W7: 强校验 — 即使经过重生成 + 模板降级, narrative 必须 0 HIGH 违规
    # 如果仍违规 (极端 case), fallback 到纯数字叙述 (无 subject 句, 不可能违规)
    try:
        assert_no_bypass(narrative, source_fields={
            "cause": ri.cause, "facts": ri.facts[:100],
            "court": ri.court, "judge_name": ri.judge_name,
        })
    except ValueError:
        # 兜底: 纯数字叙述 (0 文本 → 0 违规)
        narrative = f"样本 {sample} 件, 支持原告诉请 {support_total} 件 (含部分支持)。"

    return {
        "sample_size": sample,
        "outcome_distribution": outcome_dist,
        "support_rate_aggregate": {
            "support_total": support_total,
            "support_pct": support_pct,
            "yearly_breakdown": yearly_breakdown,
        },
        "amount_stats": amount_stats,
        "top_dispute_focus": top_dispute,
        "top_cited_laws": [],  # TODO: 关联 laws 表后填充
        "judge_style": judge_style,
        "narrative": narrative,
    }


# ===== UI 提示 =====

def compute_traffic_light(stats: Dict[str, Any]) -> str:
    n = stats["sample_size"]
    pct = stats["support_rate_aggregate"]["support_pct"]
    if n == 0:
        return "gray"
    if n >= 20 and pct > 60:
        return "green"
    if 10 <= n < 20 or 30 <= pct <= 60:
        return "yellow"
    return "red"


# ===== 主检索入口 (类案子 Agent RPC, T-REF-22) =====

@dataclass
class RetrievalOutput:
    query_meta: Dict[str, Any]
    results: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    trajectory: Dict[str, Any]
    disclaimer: str
    ui_hints: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_meta": self.query_meta,
            "results": self.results,
            "statistics": self.statistics,
            "trajectory": self.trajectory,
            "disclaimer": self.disclaimer,
            "ui_hints": self.ui_hints,
        }


def run_skill(ri: RetrievalInput,
              vector_store: VectorStore,
              config: Optional[RetrievalConfig] = None) -> RetrievalOutput:
    """类案检索 Skill 主入口 (子 Agent RPC 调用)。"""
    if config is None:
        config = RetrievalConfig()
    if ri.top_k > config.top_k_max:
        ri.top_k = config.top_k_max

    # W7: 输入消毒 — 防止 user input 携带禁用词污染 narrative
    ri.cause = sanitize_input(ri.cause)
    ri.facts = sanitize_input(ri.facts)
    ri.court = sanitize_input(ri.court) if ri.court else ri.court
    ri.judge_name = sanitize_input(ri.judge_name) if ri.judge_name else ri.judge_name
    ri.region = sanitize_input(ri.region) if ri.region else ri.region

    t0 = time.time()
    # Step 1: metadata filter
    candidates = vector_store.metadata_filter(ri, candidate_limit=500)
    # Step 2: vector search
    hits = vector_store.vector_search(ri, candidates)
    t_search_ms = int((time.time() - t0) * 1000)

    # Step 3: 上下文压缩
    compressed, trace = compress_context(hits, budget=config.context_token_budget)

    # Step 4: 统计
    stats = compute_statistics(compressed, ri)

    # Step 5: UI
    traffic = compute_traffic_light(stats)

    return RetrievalOutput(
        query_meta={
            "cause": ri.cause,
            "cause_category": compressed[0].case_type if compressed else None,
            "searched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime()),
            "latency_ms": t_search_ms,
            "total_candidates": len(candidates),
            "returned_count": len(compressed),
            "filters_applied": {
                k: v for k, v in asdict(ri).items()
                if v is not None and k not in ("facts", "top_k", "include_judge_style",
                                                "include_amount_stats", "case_id")
            },
            "vector_store": config.vector_store,
            "embedding_model": config.embedding_model,
        },
        results=[asdict(h) for h in compressed],
        statistics=stats,
        trajectory=trace.to_dict(),
        disclaimer=DISCLAIMER_FULL,
        ui_hints={
            "traffic_light": traffic,
            "show_bar_chart": bool(stats["support_rate_aggregate"]["yearly_breakdown"]),
            "show_box_plot": stats["amount_stats"].get("median_cny") is not None,
            "show_judge_card": stats["judge_style"] is not None and
                                stats["judge_style"].get("sample_size", 0) >= 5,
        },
    )


# ===== CLI =====

if __name__ == "__main__":
    # 自检: 不接数据库, 用模拟数据跑一遍
    mock_hits = [
        CaseHit(case_id="(2024) 沪01民终 1234 号", case_name="张某诉李某民间借贷纠纷",
                court="上海市第一中级人民法院", cause="民间借贷纠纷",
                judgment_date="2024-08-15", year=2024, judge_name="王某",
                outcome="部分支持", amount_awarded_cny=480000,
                summary="本院认为, 原被告之间借贷关系成立, 借款本金 50 万元予以支持",
                dispute_focus=["利率合规性", "本金认定"], relevance_score=0.92),
        CaseHit(case_id="(2023) 沪01民终 5678 号", case_name="王某诉赵某民间借贷纠纷",
                court="上海市第一中级人民法院", cause="民间借贷纠纷",
                judgment_date="2023-05-20", year=2023, judge_name="王某",
                outcome="原告胜诉", amount_awarded_cny=320000,
                summary="借款事实清楚, 利率合规, 全部支持原告诉请",
                dispute_focus=["利率合规性"], relevance_score=0.88),
    ] * 10  # 复制 10 份到 20 件

    class MockStore(VectorStore):
        def metadata_filter(self, ri, candidate_limit=500):
            return mock_hits[:candidate_limit]
        def vector_search(self, ri, candidates):
            for h in candidates:
                h.relevance_score = 0.8 + (hash(h.case_id) % 20) / 100
            return sorted(candidates, key=lambda h: -h.relevance_score)[:ri.top_k]

    ri = RetrievalInput(cause="民间借贷纠纷", facts="借给被告 50 万元",
                        court="上海一中院", judge_name="王某",
                        year_from=2022, year_to=2025, region="上海",
                        top_k=20)
    out = run_skill(ri, MockStore())
    import json
    print(json.dumps(out.to_dict(), ensure_ascii=False, indent=2)[:2500])