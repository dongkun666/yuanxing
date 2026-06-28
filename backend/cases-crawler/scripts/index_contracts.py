"""
LexPrime 合同风险索引 - 一次性灌库脚本 (W4)

从 backend/cases-crawler/data/contracts/{template_id}.json 加载所有 56+ 模板,
转成 ContractClause + RiskAnnotation 灌入 LanceDB (data/lancedb/).

运行:
    cd backend/cases-crawler
    python scripts/index_contracts.py

输出:
    backend/cases-crawler/data/lancedb/
    ├── contract_clauses.lance/   (56 模板 × 7-8 条 ≈ 400+ 条款)
    └── contract_risks.lance/     (56 模板 × 5 标注 = 280+ 风险样本)

性能:
    - 56 模板灌库 ≈ 5-15s (BGE 推理 5-10ms/条 + 写盘)
    - 灌完检索 P95 < 100ms
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import List

# 路径设置
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
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


def load_contracts(contracts_dir: Path) -> List[dict]:
    """加载所有合同模板 JSON。"""
    files = sorted(contracts_dir.glob("*.json"))
    files = [f for f in files if not f.name.startswith("_")]
    print(f"[load] 发现 {len(files)} 个合同模板")
    out: List[dict] = []
    for f in files:
        with f.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
            data["_file"] = f.name
            out.append(data)
    return out


def to_clauses(contract: dict) -> List[ContractClause]:
    """从合同模板提取所有条款。"""
    contract_id = contract.get("template_id") or contract.get("_file", "").replace(".json", "")
    contract_type = contract.get("contract_type", "其他")
    industry = contract.get("industry", "")

    # 按 annotation 索引风险等级 (clause_index -> max risk)
    risk_by_clause: dict = {}
    for ann in contract.get("annotations", []):
        idx = ann.get("clause_index")
        if idx is None:
            continue
        lvl = ann.get("risk_level", "ok")
        if lvl not in ("fatal", "major", "advisory", "ok"):
            lvl = "major"
        if idx not in risk_by_clause:
            risk_by_clause[idx] = {"risk_level": lvl, "categories": []}
        prev = risk_by_clause[idx]
        # 升级到最高等级
        rank = {"fatal": 3, "major": 2, "advisory": 1, "ok": 0}
        if rank.get(lvl, 0) > rank.get(prev["risk_level"], 0):
            prev["risk_level"] = lvl
        for c in ann.get("risk_categories", []):
            if c not in prev["categories"]:
                prev["categories"].append(c)

    out: List[ContractClause] = []
    for c in contract.get("clauses", []):
        idx = c.get("index", 0)
        risk_info = risk_by_clause.get(idx, {"risk_level": "ok", "categories": []})
        out.append(ContractClause(
            clause_id=f"{contract_id}::clause-{idx}",
            contract_id=contract_id,
            contract_type=contract_type,
            industry=industry,
            clause_index=idx,
            clause_title=c.get("title", "") or "",
            clause_text=c.get("text", "") or "",
            risk_level=risk_info["risk_level"],
            risk_categories=json.dumps(risk_info["categories"], ensure_ascii=False),
        ))
    return out


def to_risks(contract: dict) -> List[RiskAnnotation]:
    """从合同模板提取所有风险标注。"""
    contract_id = contract.get("template_id") or contract.get("_file", "").replace(".json", "")
    contract_type = contract.get("contract_type", "其他")

    # 索引 clause 文本
    clause_text_map = {c.get("index"): c.get("text", "") for c in contract.get("clauses", [])}
    clause_title_map = {c.get("index"): c.get("title", "") for c in contract.get("clauses", [])}

    out: List[RiskAnnotation] = []
    for i, ann in enumerate(contract.get("annotations", [])):
        idx = ann.get("clause_index", 0)
        lvl = ann.get("risk_level", "major")
        if lvl not in ("fatal", "major", "advisory"):
            continue
        out.append(RiskAnnotation(
            id=f"{contract_id}::clause-{idx}::ann-{i}",
            contract_id=contract_id,
            contract_type=contract_type,
            clause_id=f"{contract_id}::clause-{idx}",
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


def main(overwrite: bool = True) -> int:
    """灌库主函数。

    Args:
        overwrite: True 重建索引, False 增量

    Returns:
        0=成功, 1=失败
    """
    print("=" * 60)
    print("LexPrime 合同风险索引灌库 (W4)")
    print("=" * 60)

    # 1) 加载数据
    if not CONTRACTS_DIR.exists():
        print(f"❌ 合同数据目录不存在: {CONTRACTS_DIR}")
        return 1
    contracts = load_contracts(CONTRACTS_DIR)
    if not contracts:
        print("❌ 未发现任何合同模板")
        return 1

    all_clauses: List[ContractClause] = []
    all_risks: List[RiskAnnotation] = []
    for c in contracts:
        all_clauses.extend(to_clauses(c))
        all_risks.extend(to_risks(c))
    print(f"[stats] 模板: {len(contracts)}, 条款: {len(all_clauses)}, "
          f"风险标注: {len(all_risks)}")
    by_type: dict = {}
    for c in all_clauses:
        by_type[c.contract_type] = by_type.get(c.contract_type, 0) + 1
    print(f"[stats] 合同类型分布: {dict(sorted(by_type.items()))}")
    by_risk: dict = {}
    for r in all_risks:
        by_risk[r.risk_level] = by_risk.get(r.risk_level, 0) + 1
    print(f"[stats] 风险等级分布: {dict(sorted(by_risk.items()))}")

    # 2) Embedder
    print("\n[embedder] 加载 ...")
    embedder = get_embedder()
    print(f"[embedder] {embedder.model_name} (dim={embedder.dim})")

    # 3) 索引
    cfg = IndexConfig(lancedb_path=str(INDEX_DIR), verbose=True)
    idx = ContractRiskIndex(cfg, embedder=embedder)
    if overwrite:
        print("\n[reset] 清空旧索引 ...")
        idx.reset()

    print("\n[clause] 灌入条款 (clause_id 主键) ...")
    t0 = time.time()
    n_clauses = idx.add_clauses(all_clauses)
    print(f"  -> 入库 {n_clauses} 条款, 耗时 {(time.time()-t0):.1f}s")

    print("\n[risk] 灌入风险标注 (id 主键) ...")
    t0 = time.time()
    n_risks = idx.add_risks(all_risks)
    print(f"  -> 入库 {n_risks} 风险标注, 耗时 {(time.time()-t0):.1f}s")

    # 4) 检索基准
    print("\n[benchmark] 检索延迟 ...")
    stats = idx.benchmark(n=20, top_k=5)
    print(f"  {stats}")

    # 5) 检索样例
    print("\n[smoke test] 检索样例 ...")
    samples = [
        ("逾期按 5%/日加收违约金", "fatal", None),
        ("约定甲方住所地管辖", "major", None),
        ("合理期限内履行", "advisory", None),
        ("乙方可随时解除合同", "fatal", None),
    ]
    for q, lvl, ct in samples:
        hits = idx.search_similar_risks(q, top_k=3, risk_level=lvl, contract_type=ct)
        print(f"  Q: {q} (filter={lvl}/{ct})")
        for h in hits:
            print(f"    - {h.id} sim={h.similarity:.3f} [{h.risk_level}] "
                  f"{h.clause_title}: {h.clause_text[:50]}")

    print("\n✅ 灌库完成")
    print(f"  - 索引路径: {INDEX_DIR}")
    print(f"  - 条款: {idx.clauses_count()}")
    print(f"  - 风险: {idx.risks_count()}")
    return 0


if __name__ == "__main__":
    import argparse  # noqa: PLC0415
    parser = argparse.ArgumentParser(description="LexPrime 合同风险索引灌库")
    parser.add_argument("--append", action="store_true",
                        help="增量灌库 (默认覆盖)")
    args = parser.parse_args()
    sys.exit(main(overwrite=not args.append))
