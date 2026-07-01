"""
W7: FTS5 中文分词升级 (jieba) — 委托给 core.fts5_tokenizer 模块
LexPrime 数据工程

W4 遗留问题:
- SQLite FTS5 默认 unicode61 tokenizer 对中文不分词
- "房屋租赁合同" / "违约金过高" 等多字词 → 0 hits
- 仅单词 "合同" "借款" 能命中 (efficiency 低)

W7 方案 (plan-07-w7-yaml § 3):
- 预分词: 用 jieba 把中文切成 tokens (空格分隔), 写入 FTS5
- 查询侧: 同理用 jieba 切 query, 再走 unicode61 (单 token 命中)
- DROP + recreate 索引 (不删 contract_templates/clauses/annotations)
- 一键 rebuild: python scripts/w4/rebuild_fts5_index.py

W8 D2 重构 (REFACTOR):
- 预分词函数下沉到 core.fts5_tokenizer (复用 + 测试覆盖)
- 本文件保留 5 列 contract_fts_zh 表 (legacy schema, 向后兼容)
- W8 D2 新路径: scripts/rebuild_fts5_index.py → 1 列 contracts_fts 表

性能对比:
- unicode61 "房屋租赁合同" → 0 hits
- jieba-segmented "房屋租赁合同" → 切为 "房屋 租赁 合同", 命中 N 条

依赖:
    pip install jieba
    # (其他依赖: sqlite3 stdlib)
"""

from __future__ import annotations

import json
import logging
import sqlite3
import sys
import time
from pathlib import Path

# 项目根 (cases-crawler/)
CASES_CRAWLER = Path(__file__).parent.parent.parent
sys.path.insert(0, str(CASES_CRAWLER))

# W8 D2 重构: 从 core.fts5_tokenizer 复用 (不再本地实现)
from core.fts5_tokenizer import (  # noqa: E402
    pre_tokenize,
    pre_tokenize_query,
    to_or_match,
    FTS5_TOKENIZER_NAME,
    _ensure_jieba as _ensure_jieba_core,
    SCHEMA_CONTRACT_FTS_ZH,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)


# ============================================================
# 路径
# ============================================================
DB_PATH = CASES_CRAWLER / "db" / "contract_templates.db"


# ============================================================
# W7 向后兼容别名 (tests/test_fts5_jieba.py 还在用旧名)
# ============================================================
def _ensure_jieba():
    return _ensure_jieba_core()


_pre_tokenize = pre_tokenize
_pre_tokenize_query = pre_tokenize_query
_to_or_match = to_or_match


# ============================================================
# FTS5 schema (含预分词字段)
# ============================================================
SCHEMA_FTS = SCHEMA_CONTRACT_FTS_ZH


def rebuild_fts_index(db_path: Path = DB_PATH) -> dict:
    """重建 FTS5 索引 (含 jieba 预分词)

    步骤:
    1. DROP 旧 contract_fts (W4 unicode61 版本)
    2. CREATE 新的 contract_fts_zh (5 列预分词, W7 spec)
    3. 从 contract_templates 重读全部行, jieba 切词后写入
    4. ANALYZE + 性能对比 (unicode61 vs jieba)
    """
    if not _ensure_jieba():
        log.error("jieba 未安装, 请 pip install jieba")
        return {"status": "error", "reason": "jieba_missing"}

    if not db_path.exists():
        log.error(f"数据库不存在: {db_path}")
        return {"status": "error", "reason": "db_missing"}

    start = time.time()
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # 1. 检查旧索引
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='contract_fts'"
    )
    has_old_fts = cur.fetchone() is not None
    log.info(f"旧 contract_fts 存在: {has_old_fts}")

    # 2. DROP 旧 FTS
    if has_old_fts:
        cur.execute("DROP TABLE contract_fts")
        log.info("DROP contract_fts OK")

    # 3. CREATE 新 FTS (中文预分词)
    cur.execute(SCHEMA_FTS)
    log.info("CREATE contract_fts_zh OK")

    # 4. 重读 templates + jieba 预分词 + 写 FTS
    cur.execute("""
        SELECT template_id, title, content,
               applicable_scenarios, lawyer_notes
        FROM contract_templates
    """)
    rows = cur.fetchall()
    log.info(f"重读 {len(rows)} 模板")

    inserted = 0
    failed = 0
    for i, (tid, title, content, scenarios_json, lawyer_notes) in enumerate(rows, 1):
        try:
            scenarios_text = ""
            if scenarios_json:
                try:
                    scenarios_list = json.loads(scenarios_json)
                    if isinstance(scenarios_list, list):
                        scenarios_text = " ".join(str(s) for s in scenarios_list)
                except Exception:
                    scenarios_text = str(scenarios_json)

            t_title = _pre_tokenize(title or "")
            t_content = _pre_tokenize(content or "")
            t_scenarios = _pre_tokenize(scenarios_text)
            t_lawyer = _pre_tokenize(lawyer_notes or "")

            cur.execute(
                """
                INSERT INTO contract_fts_zh (
                    template_id, title, content, applicable_scenarios, lawyer_notes
                ) VALUES (?, ?, ?, ?, ?)
            """,
                (tid, t_title, t_content, t_scenarios, t_lawyer),
            )
            inserted += 1
            if i % 500 == 0:
                log.info(
                    f"  进度: {i}/{len(rows)} (inserted={inserted}, failed={failed})"
                )
        except Exception as e:
            failed += 1
            log.warning(f"  插入失败 {tid}: {e}")

    conn.commit()
    log.info(f"INSERT 完成: inserted={inserted}, failed={failed}")

    # 5. ANALYZE
    cur.execute("ANALYZE")
    cur.execute("VACUUM")
    conn.commit()

    # 6. 性能对比 (关键: 验证 W4 unicode61 缺陷已修复)
    log.info("--- 性能对比 (W4 unicode61 vs W7 jieba) ---")
    compare_queries = [
        "房屋租赁合同",  # W4: 0 hits (修复目标)
        "违约金过高",  # W4: 0 hits
        "管辖不利",  # W4: 0 hits
        "排他义务",  # W4: 0 hits
        "单方解除",  # W4: 0 hits
        "借款合同",  # W4: 0 hits
        "劳动合同",  # W4: 0 hits
        "知识产权",  # W4: 0 hits
        "管辖",  # W4: 1 hits
        "合同",  # W4: 20 hits
    ]
    results = {"queries": {}}
    for q in compare_queries:
        seg_q = _pre_tokenize_query(q)
        t0 = time.time()
        cur.execute(
            "SELECT COUNT(*) FROM contract_fts_zh WHERE contract_fts_zh MATCH ?",
            (seg_q,),
        )
        n = cur.fetchone()[0]
        elapsed = (time.time() - t0) * 1000
        results["queries"][q] = {
            "segmented": seg_q,
            "hits": n,
            "elapsed_ms": round(elapsed, 2),
        }
        log.info(f"  {q!r} → {seg_q!r} → {n} hits ({elapsed:.2f}ms)")

    # 7. 索引健康
    cur.execute("SELECT COUNT(*) FROM contract_fts_zh")
    total_fts = cur.fetchone()[0]
    log.info(f"contract_fts_zh 总行数: {total_fts}")

    # 8. 落盘元信息
    stats = {
        "status": "ok",
        "version": "w8-d2-refactor (core.fts5_tokenizer)",
        "tokenizer": FTS5_TOKENIZER_NAME,
        "templates_total": len(rows),
        "templates_inserted": inserted,
        "templates_failed": failed,
        "fts_rows": total_fts,
        "compare_queries": results["queries"],
        "elapsed_sec": round(time.time() - start, 2),
    }
    meta_path = db_path.parent / "contract_fts_zh.meta.json"
    meta_path.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info(f"元信息写入: {meta_path}")

    conn.close()
    log.info(f"重建完成: {stats['elapsed_sec']}s")
    return stats


if __name__ == "__main__":
    log.info("=== W7 FTS5 中文分词 (jieba) 重建 ===")
    log.info(f"DB: {DB_PATH}")
    stats = rebuild_fts_index()
    log.info("--- 摘要 ---")
    log.info(json.dumps(stats, ensure_ascii=False, indent=2))
