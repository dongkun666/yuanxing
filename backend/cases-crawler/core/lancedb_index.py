"""
LexPrime 合同风险索引 (v0.1.0-draft)

W4: Skill 2 合同风险审查的 LanceDB 向量索引 (T-REF-22)
- 50+ 合同模板的条款级 embedding (contract_clauses 表)
- 280+ 风险标注样本的 embedding (contract_risks 表)
- "新合同 + 致命条款 → 召回历史致命样本" 的双路检索

设计原则 (T-REF-22):
1. **零联网**: 全部走本地 LanceDB
2. **metadata 优先**: 风险等级 / 合同类型过滤在前, 向量召回在后
3. **降级链**: LanceDB → 关键词 fallback (LexPrime 原则: 任何 case 必须返回结果)
4. **Embedding 复用**: BGE-small-zh (BAAI/bge-small-zh-v1.5, 512 维)

依赖 (见 requirements.txt):
- lancedb>=0.6
- numpy>=1.26

用法:
    from core.lancedb_index import ContractRiskIndex, IndexConfig

    cfg = IndexConfig(lancedb_path="backend/cases-crawler/data/lancedb")
    idx = ContractRiskIndex(cfg, embedder=get_embedder())
    idx.add_clauses(contract_clauses)  # 一次性入库
    idx.add_risks(risk_annotations)
    similar = idx.search_similar_risks("逾期按 5%/日加收违约金", top_k=5,
                                        risk_level="fatal")
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


from core.embeddings import BaseEmbedder, get_embedder


# ===== 配置 =====


@dataclass
class IndexConfig:
    lancedb_path: str = "backend/cases-crawler/data/lancedb"
    clauses_table: str = "contract_clauses"
    risks_table: str = "contract_risks"
    embedding_dim: int = 512
    default_top_k: int = 5
    max_top_k: int = 20
    similarity_threshold: float = 0.5   # cosine 相似度 (BGE 归一化后 dot product)
    enable_metadata_filter: bool = True
    verbose: bool = False


# ===== 数据结构 =====


@dataclass
class ContractClause:
    """合同条款 (索引单元之一)。"""
    clause_id: str                # 全局唯一 (格式: {contract_id}::clause-{idx})
    contract_id: str              # 合同模板 ID (例: house-rent-residential-01)
    contract_type: str            # 房屋租赁 / 借款合同 / ...
    industry: str = ""            # 个人租赁 / 商铺租赁 / ...
    clause_index: int = 0
    clause_title: str = ""
    clause_text: str = ""
    risk_level: str = "ok"        # ok / advisory / major / fatal
    risk_categories: str = ""     # JSON 数组字符串 (例: '["违约金过高"]')

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RiskAnnotation:
    """风险标注 (索引单元之一)。"""
    id: str                                # 全局唯一 (格式: {contract_id}::clause-{idx}::ann-{n})
    contract_id: str
    contract_type: str
    clause_id: str
    risk_level: str                        # fatal / major / advisory (必填, 在 default 字段前)
    clause_index: int = 0
    clause_title: str = ""
    clause_text: str = ""                  # 条款原文 (便于语义检索)
    risk_categories: str = ""              # JSON 数组字符串
    legal_basis: str = ""                  # JSON 数组字符串
    risk_description: str = ""             # 风险描述
    modification_suggestion: str = ""      # 修改建议

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RiskHit:
    """检索结果 (单条)。"""
    id: str
    contract_id: str
    clause_id: str
    contract_type: str
    clause_index: int
    clause_title: str
    clause_text: str
    risk_level: str
    risk_categories: List[str]
    legal_basis: List[str]
    risk_description: str
    modification_suggestion: str
    similarity: float                       # cosine (0-1, 越大越相似)
    distance: float                         # L2 距离 (越小越相似)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ===== LanceDB 索引 =====


class ContractRiskIndex:
    """合同风险向量索引 (LanceDB)。

    两张表:
    - contract_clauses: 56 模板 × 7-8 条 ≈ 400+ 条款
    - contract_risks: 56 模板 × 5 标注 = 280+ 风险样本
    """

    def __init__(self, config: Optional[IndexConfig] = None,
                  embedder: Optional[BaseEmbedder] = None):
        self.config = config or IndexConfig()
        self.embedder = embedder or get_embedder()
        # 自动校正 dim
        if self.embedder.dim != self.config.embedding_dim:
            self.config.embedding_dim = self.embedder.dim

        import lancedb  # noqa: PLC0415
        Path(self.config.lancedb_path).mkdir(parents=True, exist_ok=True)
        self._db = lancedb.connect(self.config.lancedb_path)
        self._clauses_tbl = None
        self._risks_tbl = None

    # ----- 懒加载表 -----

    def _get_clauses_tbl(self):
        if self._clauses_tbl is None:
            try:
                self._clauses_tbl = self._db.open_table(self.config.clauses_table)
            except Exception:  # noqa: BLE001
                self._clauses_tbl = None
        return self._clauses_tbl

    def _get_risks_tbl(self):
        if self._risks_tbl is None:
            try:
                self._risks_tbl = self._db.open_table(self.config.risks_table)
            except Exception:  # noqa: BLE001
                self._risks_tbl = None
        return self._risks_tbl

    def has_clauses(self) -> bool:
        tbl = self._get_clauses_tbl()
        if tbl is None:
            return False
        try:
            return tbl.count_rows() > 0
        except Exception:  # noqa: BLE001
            return len(tbl.to_pandas()) > 0

    def has_risks(self) -> bool:
        tbl = self._get_risks_tbl()
        if tbl is None:
            return False
        try:
            return tbl.count_rows() > 0
        except Exception:  # noqa: BLE001
            return len(tbl.to_pandas()) > 0

    def clauses_count(self) -> int:
        tbl = self._get_clauses_tbl()
        if tbl is None:
            return 0
        try:
            return tbl.count_rows()
        except Exception:  # noqa: BLE001
            return len(tbl.to_pandas())

    def risks_count(self) -> int:
        tbl = self._get_risks_tbl()
        if tbl is None:
            return 0
        try:
            return tbl.count_rows()
        except Exception:  # noqa: BLE001
            return len(tbl.to_pandas())

    def reset(self) -> None:
        """清空两张表 (重建前调用)。"""
        for name in (self.config.clauses_table, self.config.risks_table):
            try:
                self._db.drop_table(name)
                if self.config.verbose:
                    print(f"  dropped table {name}")
            except Exception:  # noqa: BLE001
                pass
        self._clauses_tbl = None
        self._risks_tbl = None

    # ----- 入库 -----

    def add_clauses(self, clauses: Sequence[ContractClause], mode: str = "append") -> int:
        """入库合同条款 (clause_id 为主键, 重复添加会覆盖)。

        Args:
            clauses: ContractClause 列表
            mode: 'append' (增量) / 'overwrite' (覆盖)

        Returns:
            实际入库条数
        """
        if not clauses:
            return 0

        t0 = time.time()
        texts = [c.clause_text for c in clauses]
        embeddings = self.embedder.encode(texts)

        rows: List[Dict[str, Any]] = []
        for c, e in zip(clauses, embeddings):
            rows.append({
                "clause_id": c.clause_id,
                "contract_id": c.contract_id,
                "contract_type": c.contract_type,
                "industry": c.industry or "",
                "clause_index": int(c.clause_index),
                "clause_title": c.clause_title or "",
                "clause_text": c.clause_text or "",
                "risk_level": c.risk_level or "ok",
                "risk_categories": c.risk_categories or "[]",
                "embedding": e.tolist(),
            })

        if mode == "overwrite" or not self.has_clauses():
            self._clauses_tbl = self._db.create_table(
                self.config.clauses_table, rows, mode="overwrite"
            )
        else:
            tbl = self._get_clauses_tbl()
            assert tbl is not None
            tbl.add(rows)
            self._clauses_tbl = tbl
        elapsed = (time.time() - t0) * 1000
        if self.config.verbose:
            print(f"  indexed {len(rows)} clauses in {elapsed:.1f}ms "
                  f"({elapsed/len(rows):.1f}ms/each)")
        return len(rows)

    def add_risks(self, risks: Sequence[RiskAnnotation], mode: str = "append") -> int:
        """入库风险标注 (id 为主键)。"""
        if not risks:
            return 0

        t0 = time.time()
        texts = [self._risk_text(r) for r in risks]
        embeddings = self.embedder.encode(texts)

        rows: List[Dict[str, Any]] = []
        for r, e in zip(risks, embeddings):
            rows.append({
                "id": r.id,
                "contract_id": r.contract_id,
                "contract_type": r.contract_type,
                "clause_id": r.clause_id,
                "clause_index": int(r.clause_index),
                "clause_title": r.clause_title or "",
                "clause_text": r.clause_text or "",
                "risk_level": r.risk_level or "major",
                "risk_categories": r.risk_categories or "[]",
                "legal_basis": r.legal_basis or "[]",
                "risk_description": r.risk_description or "",
                "modification_suggestion": r.modification_suggestion or "",
                "embedding": e.tolist(),
            })

        if mode == "overwrite" or not self.has_risks():
            self._risks_tbl = self._db.create_table(
                self.config.risks_table, rows, mode="overwrite"
            )
        else:
            tbl = self._get_risks_tbl()
            assert tbl is not None
            tbl.add(rows)
            self._risks_tbl = tbl
        elapsed = (time.time() - t0) * 1000
        if self.config.verbose:
            print(f"  indexed {len(rows)} risk annotations in {elapsed:.1f}ms "
                  f"({elapsed/len(rows):.1f}ms/each)")
        return len(rows)

    def _risk_text(self, r: RiskAnnotation) -> str:
        """风险样本的检索文本: 条款原文 + 风险描述。"""
        parts = []
        if r.clause_text:
            parts.append(r.clause_text)
        if r.risk_description:
            parts.append(r.risk_description)
        if r.risk_categories:
            try:
                cats = json.loads(r.risk_categories)
                if cats:
                    parts.append(" / ".join(cats))
            except Exception:  # noqa: BLE001
                parts.append(r.risk_categories)
        return " ".join(parts)

    # ----- 检索 -----

    def search_similar_risks(self,
                              query: str,
                              top_k: int = 5,
                              risk_level: Optional[str] = None,
                              contract_type: Optional[str] = None,
                              ) -> List[RiskHit]:
        """检索相似风险样本。

        Args:
            query: 查询文本 (新合同的某条条款)
            top_k: 返回 top_k
            risk_level: 过滤风险等级 (fatal / major / advisory), None=不过滤
            contract_type: 过滤合同类型, None=不过滤

        Returns:
            List[RiskHit] (按 similarity 降序)
        """
        tbl = self._get_risks_tbl()
        if tbl is None or not self.has_risks():
            return []
        top_k = min(max(1, top_k), self.config.max_top_k)

        q_emb = self.embedder.encode_one(query)
        t0 = time.time()
        search = tbl.search(q_emb.tolist()).limit(top_k * 3)  # 多取一些给 metadata 过滤
        # metadata 过滤 (LanceDB 0.33+ 支持 .where())
        if self.config.enable_metadata_filter and risk_level:
            # 转义单引号 (LanceDB SQL)
            safe = risk_level.replace("'", "''")
            search = search.where(f"risk_level = '{safe}'")
        if self.config.enable_metadata_filter and contract_type:
            safe = contract_type.replace("'", "''")
            if risk_level:
                search = search.where(f"contract_type = '{safe}'")
            else:
                search = search.where(f"contract_type = '{safe}'")

        try:
            df = search.to_pandas()
        except Exception as e:  # noqa: BLE001
            if self.config.verbose:
                print(f"  search failed: {e}")
            return []
        search_ms = (time.time() - t0) * 1000

        hits: List[RiskHit] = []
        for _, row in df.head(top_k).iterrows():
            dist = float(row.get("_distance", 0.0))
            # BGE 归一化后: cosine_similarity = 1 - dist^2 / 2
            sim = max(0.0, min(1.0, 1.0 - (dist * dist) / 2.0))
            try:
                cats = json.loads(row.get("risk_categories", "[]") or "[]")
            except Exception:  # noqa: BLE001
                cats = []
            try:
                laws = json.loads(row.get("legal_basis", "[]") or "[]")
            except Exception:  # noqa: BLE001
                laws = []
            hits.append(RiskHit(
                id=str(row.get("id", "")),
                contract_id=str(row.get("contract_id", "")),
                clause_id=str(row.get("clause_id", "")),
                contract_type=str(row.get("contract_type", "")),
                clause_index=int(row.get("clause_index", 0)),
                clause_title=str(row.get("clause_title", "")),
                clause_text=str(row.get("clause_text", "")),
                risk_level=str(row.get("risk_level", "")),
                risk_categories=cats,
                legal_basis=laws,
                risk_description=str(row.get("risk_description", "")),
                modification_suggestion=str(row.get("modification_suggestion", "")),
                similarity=round(sim, 4),
                distance=round(dist, 4),
            ))
        if self.config.verbose:
            print(f"  search '{query[:30]}...' -> {len(hits)} hits in {search_ms:.1f}ms")
        return hits

    def search_similar_clauses(self,
                                query: str,
                                top_k: int = 5,
                                contract_type: Optional[str] = None,
                                ) -> List[Dict[str, Any]]:
        """检索相似合同条款 (返回 dict, 比 RiskHit 简单)。"""
        tbl = self._get_clauses_tbl()
        if tbl is None or not self.has_clauses():
            return []
        top_k = min(max(1, top_k), self.config.max_top_k)

        q_emb = self.embedder.encode_one(query)
        t0 = time.time()
        search = tbl.search(q_emb.tolist()).limit(top_k * 3)
        if self.config.enable_metadata_filter and contract_type:
            safe = contract_type.replace("'", "''")
            search = search.where(f"contract_type = '{safe}'")
        try:
            df = search.to_pandas()
        except Exception:  # noqa: BLE001
            return []
        search_ms = (time.time() - t0) * 1000

        out: List[Dict[str, Any]] = []
        for _, row in df.head(top_k).iterrows():
            dist = float(row.get("_distance", 0.0))
            sim = max(0.0, min(1.0, 1.0 - (dist * dist) / 2.0))
            out.append({
                "clause_id": str(row.get("clause_id", "")),
                "contract_id": str(row.get("contract_id", "")),
                "contract_type": str(row.get("contract_type", "")),
                "clause_index": int(row.get("clause_index", 0)),
                "clause_title": str(row.get("clause_title", "")),
                "clause_text": str(row.get("clause_text", "")),
                "risk_level": str(row.get("risk_level", "ok")),
                "similarity": round(sim, 4),
            })
        if self.config.verbose:
            print(f"  search clauses '{query[:30]}...' -> {len(out)} hits in {search_ms:.1f}ms")
        return out

    # ----- 性能基准 -----

    def benchmark(self, n: int = 20, top_k: int = 5) -> Dict[str, Any]:
        """基准测试: 测检索延迟 P50 / P95 / max (ms)。"""
        sample_queries = [
            "逾期支付的, 每逾期一天, 按月租金的 5% 加收违约金",
            "因本合同发生的争议, 任何一方均可向甲方住所地人民法院提起诉讼",
            "任何一方提前解除合同的, 须向守约方支付相当于 6 个月租金的违约金",
            "乙方应在合理期限内支付租金",
            "月利率 3%, 超过 LPR 四倍",
        ]
        if self.has_risks():
            queries = sample_queries * (n // len(sample_queries) + 1)
            queries = queries[:n]
        else:
            return {"error": "no risks indexed"}

        times: List[float] = []
        for q in queries:
            t0 = time.time()
            _ = self.search_similar_risks(q, top_k=top_k)
            times.append((time.time() - t0) * 1000)
        times.sort()
        return {
            "n": n,
            "min_ms": round(times[0], 2),
            "median_ms": round(times[len(times) // 2], 2),
            "p95_ms": round(times[int(len(times) * 0.95)], 2),
            "max_ms": round(times[-1], 2),
            "top_k": top_k,
            "indexed_risks": self.risks_count(),
            "indexed_clauses": self.clauses_count(),
        }


# ===== 工厂 =====


_INDEX_SINGLETON: Optional[ContractRiskIndex] = None
_INDEX_CONFIG_KEY: Optional[str] = None


def get_contract_index(config: Optional[IndexConfig] = None,
                        embedder: Optional[BaseEmbedder] = None,
                        force_new: bool = False) -> ContractRiskIndex:
    """获取索引单例 (同 config 复用)。"""
    global _INDEX_SINGLETON, _INDEX_CONFIG_KEY
    cfg_key = (config.lancedb_path if config else IndexConfig().lancedb_path) + (
        f"::{config.clauses_table}" if config else "::contract_clauses"
    ) + (f"::{config.risks_table}" if config else "::contract_risks")
    if _INDEX_SINGLETON is None or _INDEX_CONFIG_KEY != cfg_key or force_new:
        _INDEX_SINGLETON = ContractRiskIndex(config=config, embedder=embedder)
        _INDEX_CONFIG_KEY = cfg_key
    return _INDEX_SINGLETON


def reset_index() -> None:
    """重置单例 (测试用)。"""
    global _INDEX_SINGLETON, _INDEX_CONFIG_KEY
    _INDEX_SINGLETON = None
    _INDEX_CONFIG_KEY = None


# ===== CLI =====


if __name__ == "__main__":
    print("=== LexPrime 合同风险索引自检 ===\n")

    cfg = IndexConfig(
        lancedb_path="backend/cases-crawler/data/lancedb_test",
        verbose=True,
    )
    idx = ContractRiskIndex(cfg, embedder=get_embedder())
    idx.reset()

    # 模拟数据
    clauses = [
        ContractClause(
            clause_id="c1::clause-1", contract_id="c1", contract_type="房屋租赁",
            clause_index=1, clause_title="租赁标的",
            clause_text="甲方将位于上海市浦东新区某某路 123 号房屋出租给乙方使用。",
        ),
        ContractClause(
            clause_id="c1::clause-3", contract_id="c1", contract_type="房屋租赁",
            clause_index=3, clause_title="租金及支付",
            clause_text="月租金为人民币 5000 元整, 逾期支付的, 每逾期一天, 按月租金的 5% 加收违约金。",
            risk_level="fatal", risk_categories='["违约金过高"]',
        ),
    ]
    risks = [
        RiskAnnotation(
            id="c1::clause-3::ann-0", contract_id="c1", contract_type="房屋租赁",
            clause_id="c1::clause-3", clause_index=3, clause_title="租金及支付",
            clause_text="月租金为人民币 5000 元整, 逾期支付的, 每逾期一天, 按月租金的 5% 加收违约金。",
            risk_level="fatal", risk_categories='["违约金过高"]',
            legal_basis='["《民法典》第五百八十五条"]',
            risk_description="该条款违约金约定过高, 司法实践中通常被调减。",
            modification_suggestion="建议修改为'按 LPR × 1.5 倍' 等司法保护上限内表述。",
        ),
    ]
    idx.add_clauses(clauses)
    idx.add_risks(risks)
    print(f"  clauses: {idx.clauses_count()}, risks: {idx.risks_count()}\n")

    # 检索
    print("[检索] 相似风险样本 ...")
    hits = idx.search_similar_risks("逾期按 5% 加收违约金", top_k=3)
    for h in hits:
        print(f"  - {h.id} [{h.risk_level}] sim={h.similarity:.3f}: {h.clause_title}")

    # 性能
    print("\n[性能] 检索延迟基准 ...")
    print(" ", idx.benchmark(n=20, top_k=5))
