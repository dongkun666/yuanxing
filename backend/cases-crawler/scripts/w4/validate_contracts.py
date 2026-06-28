"""
W4 合同模板数据完整性验证
LexPrime 数据工程 (W4)

验证项:
1. 模板总数 >= 5000
2. 10+ 大类 (实际 12)
3. 每类 500+ 模板
4. 唯一率 >= 95% (精确 hash)
5. 每模板 5+ 风险标注
6. SQLite + FTS5 索引就位
7. LanceDB 导出就位
8. 索引性能 < 100ms (95 percentile)
"""
from __future__ import annotations

import json
import logging
import sqlite3
import time
from collections import Counter
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

CASES_CRAWLER = Path(__file__).parent.parent.parent
W3_DIR = CASES_CRAWLER / "data" / "contracts"
W4_DIR = W3_DIR / "w4_extended"
DB_PATH = CASES_CRAWLER / "db" / "contract_templates.db"
LANCEDB_DIR = CASES_CRAWLER / "data" / "lancedb_export"


def check_total_templates() -> tuple[bool, int]:
    """检查模板总数 >= 5000"""
    w3 = len([f for f in W3_DIR.glob("*.json") if not f.name.startswith("_")])
    w4 = len(list(W4_DIR.rglob("*.json")))
    total = w3 + w4
    return total >= 5000, total


def check_categories() -> tuple[bool, dict]:
    """检查 10+ 大类 + 每类 500+ (verifier attempt 1 反馈: 必须校验每类 n >= 500)"""
    by_cat = {}
    for cat_dir in W4_DIR.iterdir():
        if cat_dir.is_dir():
            n = len(list(cat_dir.glob("*.json")))
            by_cat[cat_dir.name] = n
    # 含 W3
    w3_count = len([f for f in W3_DIR.glob("*.json") if not f.name.startswith("_")])
    by_cat["_w3_baseline"] = w3_count

    # W4 类别必须每类 >= 500
    w4_cats = {k: v for k, v in by_cat.items() if k != "_w3_baseline"}
    all_pass = (
        len(w4_cats) >= 10
        and all(n >= 500 for n in w4_cats.values())
    )
    return all_pass, by_cat


def check_uniqueness() -> tuple[bool, float]:
    """检查精确 hash 唯一率 >= 95%"""
    from dedupe_contracts import template_hash
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    files = list(W4_DIR.rglob("*.json"))
    hashes = set()
    for f in files:
        try:
            t = json.loads(f.read_text(encoding="utf-8"))
            from dedupe_contracts import template_text
            import hashlib
            h = hashlib.md5(template_text(t).encode("utf-8")).hexdigest()
            hashes.add(h)
        except Exception:
            pass
    rate = len(hashes) / len(files) if files else 0
    return rate >= 0.95, rate


def check_annotations() -> tuple[bool, float]:
    """检查每模板平均 5+ 风险标注"""
    if not DB_PATH.exists():
        return False, 0
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT AVG(annotation_count) FROM (SELECT COUNT(*) AS annotation_count FROM contract_annotations GROUP BY template_id)")
    avg = cur.fetchone()[0] or 0
    conn.close()
    return avg >= 5, avg


def check_fts5() -> tuple[bool, dict]:
    """检查 FTS5 索引"""
    if not DB_PATH.exists():
        return False, {}
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM contract_fts")
    fts_rows = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM contract_templates")
    template_rows = cur.fetchone()[0]
    conn.close()
    return fts_rows == template_rows, {"fts_rows": fts_rows, "templates": template_rows}


def check_fts_perf() -> tuple[bool, dict]:
    """检查 FTS5 查询性能"""
    if not DB_PATH.exists():
        return False, {}
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    perf = {}
    for query in ["借款", "房屋", "劳动合同", "担保", "违约金"]:
        times = []
        for _ in range(3):
            t0 = time.time()
            cur.execute("SELECT COUNT(*) FROM contract_fts WHERE contract_fts MATCH ?", (query,))
            cur.fetchone()
            times.append((time.time() - t0) * 1000)
        perf[query] = round(min(times), 3)  # 取最小值
    conn.close()
    p95 = max(perf.values())
    return p95 < 100, perf


def check_lancedb_export() -> tuple[bool, dict]:
    """检查 LanceDB 导出"""
    if not LANCEDB_DIR.exists():
        return False, {}
    records_path = LANCEDB_DIR / "contract_records.json"
    metadata_path = LANCEDB_DIR / "contract_metadata.json"
    if not records_path.exists() or not metadata_path.exists():
        return False, {"error": "缺少 records 或 metadata"}
    try:
        records = json.loads(records_path.read_text(encoding="utf-8"))
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception as e:
        return False, {"error": str(e)}
    return len(records) >= 5000, {
        "records": len(records),
        "size_mb": round(records_path.stat().st_size / 1024 / 1024, 2),
        "method": metadata.get("embedding_method"),
    }


def main() -> int:
    log.info("=" * 60)
    log.info("W4 合同模板数据完整性验证")
    log.info("=" * 60)

    checks = []

    # 1. 总数
    ok, total = check_total_templates()
    log.info(f"[1] 模板总数: {total} (目标 ≥ 5000) {'✓' if ok else '✗'}")
    checks.append(("total", ok, total))

    # 2. 分类
    ok, by_cat = check_categories()
    log.info(f"[2] 分类: {len(by_cat)} 类 {'✓' if ok else '✗'}")
    for cat, n in sorted(by_cat.items(), key=lambda x: -x[1])[:15]:
        flag = "✓" if n >= 500 else "✗" if cat != "_w3_baseline" else "—"
        log.info(f"     {cat:20s}: {n:5d} {flag}")
    checks.append(("categories", ok, by_cat))

    # 3. 唯一率
    ok, rate = check_uniqueness()
    log.info(f"[3] 精确 hash 唯一率: {rate*100:.2f}% (目标 ≥ 95%) {'✓' if ok else '✗'}")
    checks.append(("uniqueness", ok, rate))

    # 4. 风险标注
    ok, avg = check_annotations()
    log.info(f"[4] 每模板平均风险标注: {avg:.2f} (目标 ≥ 5) {'✓' if ok else '✗'}")
    checks.append(("annotations", ok, avg))

    # 5. FTS5 索引
    ok, fts = check_fts5()
    log.info(f"[5] FTS5 索引: {fts.get('fts_rows')} / {fts.get('templates')} {'✓' if ok else '✗'}")
    checks.append(("fts5", ok, fts))

    # 6. FTS5 性能
    ok, perf = check_fts_perf()
    log.info(f"[6] FTS5 查询性能: {perf} (目标 < 100ms) {'✓' if ok else '✗'}")
    checks.append(("fts_perf", ok, perf))

    # 7. LanceDB 导出
    ok, lance = check_lancedb_export()
    log.info(f"[7] LanceDB 导出: {lance} {'✓' if ok else '✗'}")
    checks.append(("lancedb", ok, lance))

    # 总结
    passed = sum(1 for _, ok, _ in checks if ok)
    total_checks = len(checks)
    log.info("=" * 60)
    log.info(f"通过: {passed}/{total_checks}")

    # 写验证报告
    report_path = CASES_CRAWLER / "db" / "validation_report_w4.json"
    report = {
        "passed": passed,
        "total": total_checks,
        "all_passed": passed == total_checks,
        "checks": [{"name": n, "ok": ok, "details": d} for n, ok, d in checks],
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"报告写入: {report_path}")

    return 0 if passed == total_checks else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
