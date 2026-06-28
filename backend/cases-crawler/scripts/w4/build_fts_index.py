"""
W4 合同模板 SQLite 入库 + FTS5 全文索引
LexPrime 数据工程 (W4)

输入: backend/cases-crawler/data/contracts/ (W3 + W4) + _index_w4_unique.json
输出: backend/cases-crawler/db/contract_templates.db

表结构:
- contract_templates (id, template_id, contract_type, industry, title, content,
  applicable_scenarios, lawyer_notes, source, created_at, updated_at)
- contract_clauses (id, template_id FK, idx, title, text)
- contract_annotations (id, template_id FK, clause_index, clause_title,
  risk_level, risk_categories JSON, legal_basis JSON, risk_description,
  modification_suggestion, stance_impact)
- FTS5 索引: contract_fts (title, content, applicable_scenarios, lawyer_notes)
"""
from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ============================================================
# 路径
# ============================================================
CASES_CRAWLER = Path(__file__).parent.parent.parent
W3_DIR = CASES_CRAWLER / "data" / "contracts"
W4_DIR = W3_DIR / "w4_extended"
DB_DIR = CASES_CRAWLER / "db"
DB_PATH = DB_DIR / "contract_templates.db"

SCHEMA = """
-- 合同模板主表
CREATE TABLE IF NOT EXISTS contract_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id TEXT UNIQUE NOT NULL,
    contract_type TEXT NOT NULL,
    industry TEXT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,                  -- 全文 (所有条款拼接)
    applicable_scenarios TEXT,              -- JSON array
    lawyer_notes TEXT,
    source TEXT,                            -- W3 baseline / W4 程序化生成
    category TEXT,                          -- 子目录 (loan/house/labor/...)
    skeleton TEXT,
    variant_idx INTEGER,
    generated_at TEXT,
    created_at TEXT,
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_templates_type ON contract_templates(contract_type);
CREATE INDEX IF NOT EXISTS idx_templates_industry ON contract_templates(industry);
CREATE INDEX IF NOT EXISTS idx_templates_category ON contract_templates(category);
CREATE INDEX IF NOT EXISTS idx_templates_source ON contract_templates(source);

-- 条款表 (一对多)
CREATE TABLE IF NOT EXISTS contract_clauses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id TEXT NOT NULL,
    clause_index INTEGER NOT NULL,
    clause_title TEXT NOT NULL,
    clause_text TEXT NOT NULL,
    FOREIGN KEY (template_id) REFERENCES contract_templates(template_id)
);
CREATE INDEX IF NOT EXISTS idx_clauses_template ON contract_clauses(template_id);

-- 风险标注表 (一对多)
CREATE TABLE IF NOT EXISTS contract_annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id TEXT NOT NULL,
    clause_index INTEGER NOT NULL,
    clause_title TEXT,
    risk_level TEXT NOT NULL,              -- fatal / major / advisory / ok
    risk_categories TEXT,                  -- JSON array
    legal_basis TEXT,                      -- JSON array
    risk_description TEXT,
    modification_suggestion TEXT,
    stance_impact TEXT,
    FOREIGN KEY (template_id) REFERENCES contract_templates(template_id)
);
CREATE INDEX IF NOT EXISTS idx_annotations_template ON contract_annotations(template_id);
CREATE INDEX IF NOT EXISTS idx_annotations_risk ON contract_annotations(risk_level);

-- FTS5 全文索引
CREATE VIRTUAL TABLE IF NOT EXISTS contract_fts USING fts5(
    template_id UNINDEXED,
    title,
    content,
    applicable_scenarios,
    lawyer_notes,
    tokenize = 'unicode61'
);
"""


def init_db() -> sqlite3.Connection:
    """初始化数据库"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        log.info(f"删除旧数据库: {DB_PATH}")
        DB_PATH.unlink()
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript(SCHEMA)
    conn.commit()
    log.info(f"数据库初始化: {DB_PATH}")
    return conn


def load_template(file_path: Path) -> dict | None:
    """加载合同模板 JSON"""
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as e:
        log.warning(f"加载失败 {file_path}: {e}")
        return None


def insert_template(conn: sqlite3.Connection, t: dict, source: str, category: str | None = None) -> bool:
    """插入一份合同模板"""
    try:
        # 拼接全文
        content_parts = []
        for c in t.get("clauses", []):
            content_parts.append(f"{c.get('title', '')}: {c.get('text', '')}")
        content = "\n".join(content_parts)

        meta = t.get("metadata", {})
        cur = conn.cursor()

        # 主表
        cur.execute("""
            INSERT OR IGNORE INTO contract_templates (
                template_id, contract_type, industry, title, content,
                applicable_scenarios, lawyer_notes, source, category,
                skeleton, variant_idx, generated_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            t.get("template_id"),
            t.get("contract_type"),
            t.get("industry"),
            t.get("title"),
            content,
            json.dumps(t.get("applicable_scenarios", []), ensure_ascii=False),
            t.get("lawyer_notes"),
            source,
            category or meta.get("category"),
            meta.get("skeleton"),
            meta.get("variant_idx"),
            meta.get("generated_at"),
            t.get("created_at"),
            t.get("updated_at"),
        ))

        # 条款
        for c in t.get("clauses", []):
            cur.execute("""
                INSERT INTO contract_clauses (
                    template_id, clause_index, clause_title, clause_text
                ) VALUES (?, ?, ?, ?)
            """, (
                t.get("template_id"),
                c.get("index"),
                c.get("title"),
                c.get("text"),
            ))

        # 风险标注
        for a in t.get("annotations", []):
            cur.execute("""
                INSERT INTO contract_annotations (
                    template_id, clause_index, clause_title, risk_level,
                    risk_categories, legal_basis, risk_description,
                    modification_suggestion, stance_impact
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t.get("template_id"),
                a.get("clause_index"),
                a.get("clause_title"),
                a.get("risk_level"),
                json.dumps(a.get("risk_categories", []), ensure_ascii=False),
                json.dumps(a.get("legal_basis", []), ensure_ascii=False),
                a.get("risk_description"),
                a.get("modification_suggestion"),
                a.get("stance_impact"),
            ))

        # FTS5
        scenarios = " ".join(t.get("applicable_scenarios", []))
        cur.execute("""
            INSERT INTO contract_fts (
                template_id, title, content, applicable_scenarios, lawyer_notes
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            t.get("template_id"),
            t.get("title"),
            content,
            scenarios,
            t.get("lawyer_notes") or "",
        ))

        return True
    except sqlite3.IntegrityError as e:
        log.debug(f"已存在: {t.get('template_id')}: {e}")
        return False
    except Exception as e:
        log.error(f"插入失败 {t.get('template_id', '?')}: {e}")
        return False


def build_index() -> dict:
    """建索引"""
    start = time.time()
    conn = init_db()
    cur = conn.cursor()

    stats = {"w3": 0, "w4": 0, "errors": 0}

    # W3 baseline
    log.info("导入 W3 baseline...")
    for f in W3_DIR.glob("*.json"):
        if f.name.startswith("_"):
            continue
        t = load_template(f)
        if not t:
            stats["errors"] += 1
            continue
        if insert_template(conn, t, source="W3 baseline"):
            stats["w3"] += 1
    log.info(f"W3: {stats['w3']} 模板")

    # W4 扩展
    log.info("导入 W4 扩展...")
    w4_files = sorted(W4_DIR.rglob("*.json"))
    for i, f in enumerate(w4_files, 1):
        t = load_template(f)
        if not t:
            stats["errors"] += 1
            continue
        # category 从相对路径提取
        rel = f.relative_to(W4_DIR)
        category = rel.parts[0] if len(rel.parts) > 1 else None
        if insert_template(conn, t, source="W4 程序化生成", category=category):
            stats["w4"] += 1
        if i % 500 == 0:
            log.info(f"  W4 进度: {i}/{len(w4_files)}")
    log.info(f"W4: {stats['w4']} 模板")

    conn.commit()

    # ANALYZE 优化
    cur.execute("ANALYZE")
    conn.commit()

    # VACUUM 压缩
    cur.execute("VACUUM")
    conn.commit()

    elapsed = time.time() - start
    stats["elapsed_sec"] = round(elapsed, 2)

    # 索引信息
    cur.execute("SELECT COUNT(*) FROM contract_templates")
    stats["total_templates"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM contract_clauses")
    stats["total_clauses"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM contract_annotations")
    stats["total_annotations"] = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM contract_fts")
    stats["total_fts_rows"] = cur.fetchone()[0]

    # 性能基准
    log.info("性能基准测试...")
    perf = {}
    for query, label in [
        ("借款", "FTS5 借款"),
        ("房屋", "FTS5 房屋"),
        ("劳动合同", "FTS5 劳动合同"),
        ("担保", "FTS5 担保"),
        ("违约金过高", "FTS5 违约金过高"),
    ]:
        t0 = time.time()
        cur.execute("SELECT COUNT(*) FROM contract_fts WHERE contract_fts MATCH ?", (query,))
        n = cur.fetchone()[0]
        perf[label] = {"query": query, "results": n, "elapsed_ms": round((time.time() - t0) * 1000, 2)}
    stats["fts_perf"] = perf

    conn.close()

    # 写元信息
    meta_path = DB_DIR / "contract_templates.meta.json"
    meta_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"元信息写入: {meta_path}")

    return stats


if __name__ == "__main__":
    stats = build_index()
    log.info(f"完成: {stats}")
