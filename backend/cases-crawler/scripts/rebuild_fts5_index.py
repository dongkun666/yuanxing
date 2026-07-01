"""
W8 D2 FTS5 中文分词重建脚本 (jieba pre-tokenizer)
LexPrime 数据工程 (W8 D2)

W4 + W7 遗留问题:
- SQLite FTS5 默认 unicode61 tokenizer 对中文不分词
- "房屋租赁合同" / "劳动合同" / "股权转让" 等多字词 → 0 hits
- unicode61 时代 12152 行索引, 但查询 "房屋租赁合同" 必须用 _to_or_match(_pre_tokenize_query(...))
  才能拿到召回 (任一 token 命中)

W8 D2 方案:
- 提取 W7 scripts/w4/rebuild_fts5_index.py 的预分词函数到 core/fts5_tokenizer 模块
- 新建本脚本: 用 core 模块在 contract_templates.db 里建 contracts_fts (D2 spec 表名)
- 1 content 列 + contract_id UNINDEXED (D2 spec: 简洁 schema, 适合任意单字段全文索引)
- 重建 + 验证 3 关键词 (房屋租赁合同 / 劳动合同 / 股权转让) → 期望 > 0 hits

Differences vs W7 (scripts/w4/rebuild_fts5_index.py):
- 表名: contract_fts_zh (W7) vs contracts_fts (W8 D2)
- 字段: 5 列 (W7) vs 1 content + contract_id (W8 D2)
- 路径: scripts/w4/ (W7 legacy) vs scripts/ (W8 D2 new path)
- API: 内部 _pre_tokenize 系列 (W7) vs from core.fts5_tokenizer import (W8 D2)

依赖:
    backend/venv312/Scripts/python.exe -m pip install jieba==0.42.1
"""

from __future__ import annotations

import json
import logging
import sqlite3
import sys
import time
from pathlib import Path

# 项目根
CASES_CRAWLER = Path(__file__).parent.parent
sys.path.insert(0, str(CASES_CRAWLER))

from core.fts5_tokenizer import (  # noqa: E402
    SCHEMA_CONTRACTS_FTS,
    jieba_tokenize,
    to_or_match,
    tokenize_query,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("fts5.w8d2")


DB_PATH = CASES_CRAWLER / "db" / "contract_templates.db"
META_PATH = DB_PATH.parent / "contracts_fts.meta.json"

# D2 验收关键词 (vs W4 unicode61 0 hits 缺陷)
VERIFY_QUERIES = [
    "房屋租赁合同",  # W4: 0 hits → D2 验证 > 0
    "劳动合同",  # W4: 0 hits → D2 验证 > 0
    "股权转让",  # W4: 0 hits → D2 验证 > 0
]


def rebuild_contracts_fts(db_path: Path = DB_PATH, meta_path: Path = META_PATH) -> dict:
    """重建 contracts_fts (jieba 预分词) 索引

    步骤:
    1. DROP TABLE IF EXISTS contracts_fts
    2. CREATE VIRTUAL TABLE contracts_fts USING fts5(...)
    3. 从 contract_templates 重读 6076 行, jieba 预分词后 INSERT
    4. ANALYZE + 验证 3 关键词查询 (期望 > 0 hits)
    5. 写 meta.json
    """
    if not db_path.exists():
        log.error(f"数据库不存在: {db_path}")
        return {"status": "error", "reason": "db_missing"}

    start = time.time()
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # 1. 旧索引存在? (W7 W4 contract_fts 已 drop, 应为 None)
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='contracts_fts'"
    )
    exists = cur.fetchone() is not None
    log.info(f"contracts_fts 当前存在: {exists}")

    # 2. DROP (如存在)
    if exists:
        cur.execute("DROP TABLE contracts_fts")
        log.info("DROP contracts_fts OK")

    # 3. CREATE (schema from core/fts5_tokenizer)
    cur.executescript(SCHEMA_CONTRACTS_FTS)
    log.info("CREATE contracts_fts OK (tokenize='unicode61 remove_diacritics 2')")

    # 4. 从 contract_templates 重读 + jieba 预分词 + INSERT
    cur.execute("SELECT template_id, content FROM contract_templates")
    rows = cur.fetchall()
    log.info(f"重读 {len(rows)} 模板")

    inserted = 0
    failed = 0
    t0 = time.time()
    for i, (tid, content) in enumerate(rows, 1):
        try:
            seg_content = jieba_tokenize(content or "")
            cur.execute(
                "INSERT INTO contracts_fts (contract_id, content) VALUES (?, ?)",
                (tid, seg_content),
            )
            inserted += 1
            if i % 1000 == 0:
                log.info(
                    f"  进度: {i}/{len(rows)} (inserted={inserted}, failed={failed})"
                )
        except Exception as e:
            failed += 1
            log.warning(f"  插入失败 {tid}: {e}")
    insert_elapsed = time.time() - t0
    log.info(
        f"INSERT 完成: inserted={inserted}, failed={failed}, 耗时 {insert_elapsed:.2f}s"
    )
    conn.commit()

    # 5. ANALYZE + VACUUM
    cur.execute("ANALYZE")
    conn.commit()
    cur.execute("VACUUM")
    conn.commit()

    # 6. 索引健康
    cur.execute("SELECT COUNT(*) FROM contracts_fts")
    total_fts = cur.fetchone()[0]
    log.info(f"contracts_fts 总行数: {total_fts}")

    # 7. 验证 3 关键词 (D2 验收目标)
    log.info("--- 中文检索验证 (D2 验收) ---")
    verify_results: dict[str, dict] = {}
    for q in VERIFY_QUERIES:
        seg_q = tokenize_query(q)
        match_expr = to_or_match(seg_q)
        t_q = time.time()
        cur.execute(
            "SELECT COUNT(*) FROM contracts_fts WHERE contracts_fts MATCH ?",
            (match_expr,),
        )
        n = cur.fetchone()[0]
        elapsed_ms = round((time.time() - t_q) * 1000, 2)
        verify_results[q] = {
            "segmented": seg_q,
            "match_expr": match_expr,
            "hits": n,
            "elapsed_ms": elapsed_ms,
            "passed": n > 0,
        }
        status = "PASS" if n > 0 else "FAIL"
        log.info(
            f"  [{status}] {q!r} → seg={seg_q!r} → {match_expr!r} → {n} hits ({elapsed_ms}ms)"
        )

    # 8. 元信息落盘
    all_passed = all(r["passed"] for r in verify_results.values())
    stats = {
        "status": "ok" if all_passed else "verify_failed",
        "version": "w8-d2-v1",
        "tokenizer": "unicode61 + jieba-pre-segmentation",
        "fts_table": "contracts_fts",
        "templates_total": len(rows),
        "templates_inserted": inserted,
        "templates_failed": failed,
        "fts_rows": total_fts,
        "verify_queries": verify_results,
        "verify_all_passed": all_passed,
        "elapsed_sec": round(time.time() - start, 2),
    }
    meta_path.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info(f"元信息写入: {meta_path}")

    conn.close()
    log.info(f"重建完成: {stats['elapsed_sec']}s, verify_all_passed={all_passed}")
    return stats


if __name__ == "__main__":
    log.info("=== W8 D2 FTS5 中文分词 (jieba) 重建 ===")
    log.info(f"DB: {DB_PATH}")
    stats = rebuild_contracts_fts()
    log.info("--- 摘要 ---")
    log.info(json.dumps(stats, ensure_ascii=False, indent=2))
    if not stats.get("verify_all_passed"):
        log.error("D2 验证未全部通过, 需排查")
        sys.exit(1)
    log.info("D2 验证全部 PASS")
