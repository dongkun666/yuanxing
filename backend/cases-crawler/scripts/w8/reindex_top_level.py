"""
W8 D4: 顶层 56 合同快速 reindex (W8 D4 E2E 验收用)

W4 全量 6076 合同 reindex 约 10-15 min (BGE 推理 + 写盘)。
W8 D4 E2E 只需要 contract_risks.lance 顶层 56 模板 (280 风险标注) 就够
retrieval_evidence 双路召回测试。本脚本只灌顶层 .json, 跳过 w4_extended/。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import List

SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from core.embeddings import get_embedder  # noqa: E402
from core.lancedb_index import (  # noqa: E402
    ContractClause,
    ContractRiskIndex,
    IndexConfig,
    RiskAnnotation,
)

CONTRACTS_DIR = BACKEND_DIR / "data" / "contracts"
INDEX_DIR = BACKEND_DIR / "data" / "lancedb"


def load_top_level(contracts_dir: Path) -> List[dict]:
    """只加载顶层 .json (56 模板), 跳过 w4_extended/ w4_skeletons/ 子目录"""
    files = sorted(contracts_dir.glob("*.json"))  # 不递归
    files = [f for f in files if not f.name.startswith("_")]
    print(f"[load] 顶层 {len(files)} 模板 (W8 D4 mini reindex)")
    return [json.load(open(f, encoding="utf-8")) for f in files]


def to_clauses(contract: dict) -> List[ContractClause]:
    cid = contract.get("template_id") or contract.get("contract_id", "")
    ctype = contract.get("contract_type", "其他")
    industry = contract.get("industry", "")
    risk_by_clause = {}
    for ann in contract.get("annotations", []):
        idx = ann.get("clause_index")
        if idx is None:
            continue
        lvl = ann.get("risk_level", "ok")
        if lvl not in ("fatal", "major", "advisory", "ok"):
            lvl = "major"
        if idx not in risk_by_clause:
            risk_by_clause[idx] = {"risk_level": lvl, "categories": []}
        rank = {"fatal": 3, "major": 2, "advisory": 1, "ok": 0}
        if rank.get(lvl, 0) > rank.get(risk_by_clause[idx]["risk_level"], 0):
            risk_by_clause[idx]["risk_level"] = lvl
        for c in ann.get("risk_categories", []):
            if c not in risk_by_clause[idx]["categories"]:
                risk_by_clause[idx]["categories"].append(c)
    out = []
    for c in contract.get("clauses", []):
        idx = c.get("index", 0)
        risk_info = risk_by_clause.get(idx, {"risk_level": "ok", "categories": []})
        out.append(ContractClause(
            clause_id=f"{cid}::clause-{idx}",
            contract_id=cid,
            contract_type=ctype,
            industry=industry,
            clause_index=idx,
            clause_title=c.get("title", "") or "",
            clause_text=c.get("text", "") or "",
            risk_level=risk_info["risk_level"],
            risk_categories=json.dumps(risk_info["categories"], ensure_ascii=False),
        ))
    return out


def to_risks(contract: dict) -> List[RiskAnnotation]:
    cid = contract.get("template_id") or contract.get("contract_id", "")
    ctype = contract.get("contract_type", "其他")
    clause_text_map = {c.get("index"): c.get("text", "") for c in contract.get("clauses", [])}
    clause_title_map = {c.get("index"): c.get("title", "") for c in contract.get("clauses", [])}
    out = []
    for i, ann in enumerate(contract.get("annotations", [])):
        idx = ann.get("clause_index", 0)
        lvl = ann.get("risk_level", "major")
        if lvl not in ("fatal", "major", "advisory"):
            continue
        out.append(RiskAnnotation(
            id=f"{cid}::clause-{idx}::ann-{i}",
            contract_id=cid,
            contract_type=ctype,
            clause_id=f"{cid}::clause-{idx}",
            risk_level=lvl,
            clause_index=idx,
            clause_title=ann.get("clause_title") or clause_title_map.get(idx, ""),
            clause_text=clause_text_map.get(idx, ""),
            risk_categories=json.dumps(ann.get("risk_categories", []), ensure_ascii=False),
            legal_basis=json.dumps(ann.get("legal_basis", []), ensure_ascii=False),
            risk_description=ann.get("risk_description", ""),
            modification_suggestion=ann.get("modification_suggestion", ""),
        ))
    return out


def main() -> int:
    print("=" * 60)
    print("W8 D4 mini reindex (顶层 56 模板, ~1-2 min)")
    print("=" * 60)
    contracts = load_top_level(CONTRACTS_DIR)
    all_clauses: List[ContractClause] = []
    all_risks: List[RiskAnnotation] = []
    for c in contracts:
        all_clauses.extend(to_clauses(c))
        all_risks.extend(to_risks(c))
    print(f"[stats] 模板: {len(contracts)}, 条款: {len(all_clauses)}, "
          f"风险标注: {len(all_risks)}")
    by_type = {}
    for c in all_clauses:
        by_type[c.contract_type] = by_type.get(c.contract_type, 0) + 1
    print(f"[stats] 类型分布: {dict(sorted(by_type.items()))}")
    by_risk = {}
    for r in all_risks:
        by_risk[r.risk_level] = by_risk.get(r.risk_level, 0) + 1
    print(f"[stats] 风险分布: {dict(sorted(by_risk.items()))}")

    print("\n[embedder] 加载...")
    t0 = time.time()
    embedder = get_embedder()
    print(f"[embedder] {embedder.model_name} (dim={embedder.dim}), "
          f"load_time={time.time()-t0:.1f}s")

    cfg = IndexConfig(lancedb_path=str(INDEX_DIR), verbose=False)
    idx = ContractRiskIndex(cfg, embedder=embedder)

    print("\n[clause] 灌入条款 ...")
    t0 = time.time()
    n_clauses = idx.add_clauses(all_clauses)
    print(f"  -> {n_clauses} 条款, {time.time()-t0:.1f}s")

    print("\n[risk] 灌入风险标注 ...")
    t0 = time.time()
    n_risks = idx.add_risks(all_risks)
    print(f"  -> {n_risks} 风险标注, {time.time()-t0:.1f}s")

    print("\n[smoke test] 检索样例 ...")
    for q, lvl in [
        ("逾期按 5% 加收违约金", "fatal"),
        ("约定甲方住所地管辖", "major"),
        ("单方解除合同", "fatal"),
    ]:
        hits = idx.search_similar_risks(q, top_k=3, risk_level=lvl)
        print(f"  Q: {q} (filter={lvl})")
        for h in hits:
            print(f"    - {h.id} sim={h.similarity:.3f} [{h.risk_level}] "
                  f"{h.clause_title}")

    print("\n✅ mini reindex 完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())