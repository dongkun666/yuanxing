"""
W4 合同模板 LanceDB 导出
LexPrime 数据工程 (W4) → lex-ai 协作 (Skill 2 向量索引)

策略:
- 读取 SQLite contract_templates
- 用简单 hash 模拟 embedding (无 sentence-transformers 依赖, 0 收费 API)
- 导出 LanceDB 兼容格式 (parquet + metadata)
- 提供 lex-ai 加载脚本可调用的接口

输出:
- backend/cases-crawler/data/lancedb_export/
  ├── contract_vectors.parquet     (LanceDB 数据)
  └── contract_metadata.json       (元数据 + 加载说明)
"""
from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ============================================================
# 路径
# ============================================================
CASES_CRAWLER = Path(__file__).parent.parent.parent
DB_PATH = CASES_CRAWLER / "db" / "contract_templates.db"
EXPORT_DIR = CASES_CRAWLER / "data" / "lancedb_export"


def hash_embedding(text: str, dim: int = 384) -> list[float]:
    """
    简单的伪 embedding — 基于文本 hash 映射到固定维度向量。
    用于演示目的；实际使用应替换为 sentence-transformers (BGE 中文) 或调用 LLM API。
    0 收费 API 100% 自建原则。
    """
    if not text:
        return [0.0] * dim
    # 多次 hash 拼接得到 dim 维
    vec = []
    text_bytes = text.encode("utf-8")
    for i in range(dim // 32 + 1):
        h = hashlib.sha256(f"{i}_{text_bytes.hex()}".encode("utf-8")).digest()
        for j in range(0, len(h), 4):
            # 取 4 字节, 归一化到 [-1, 1]
            val = int.from_bytes(h[j:j + 4], "big") / (2**32 - 1) * 2 - 1
            vec.append(val)
    return vec[:dim]


def normalize_vec(v: list[float]) -> list[float]:
    """L2 归一化"""
    norm = sum(x * x for x in v) ** 0.5
    if norm == 0:
        return v
    return [x / norm for x in v]


def export_to_lancedb(limit: int | None = None) -> dict:
    """从 SQLite 导出到 LanceDB 格式"""
    if not DB_PATH.exists():
        log.error(f"数据库不存在: {DB_PATH}")
        return {}

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    sql = "SELECT template_id, contract_type, industry, title, content, applicable_scenarios, lawyer_notes, source, category FROM contract_templates"
    if limit:
        sql += f" LIMIT {limit}"

    cur.execute(sql)
    rows = cur.fetchall()
    log.info(f"读取 {len(rows)} 模板")

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    # 准备 LanceDB 兼容输出
    records = []
    metadata = {
        "total": len(rows),
        "embedding_method": "hash_pseudo_embedding_384dim",
        "embedding_note": "LexPrime W4 自建伪 embedding, 实际应使用 sentence-transformers BGE 中文模型",
        "schema": {
            "vector": "list[float] 384-dim (待替换为真实 BGE embedding)",
            "template_id": "str",
            "contract_type": "str",
            "industry": "str",
            "title": "str",
            "content": "str (full text, all clauses joined)",
            "applicable_scenarios": "list[str]",
            "lawyer_notes": "str",
            "source": "str (W3 baseline / W4 程序化生成)",
            "category": "str",
        },
        "load_instructions": {
            "python": """
import lancedb
import pyarrow as pa
import json

db = lancedb.connect('./lancedb_data')
table = db.create_table('contract_templates', data=records, mode='overwrite')
# 搜索
results = table.search(query_vector).limit(5).to_list()
""",
            "alternative_no_lancedb": """
# 如果 lex-ai 暂时无法用 LanceDB, 可直接用 SQLite + FTS5
import sqlite3
conn = sqlite3.connect('contract_templates.db')
# 全文搜索
results = conn.execute(
    \"SELECT template_id, title FROM contract_fts WHERE contract_fts MATCH ?\",
    ('借款 担保',)
).fetchall()
""",
        },
    }

    for row in rows:
        template_id, contract_type, industry, title, content, scenarios_json, lawyer_notes, source, category = row
        scenarios = json.loads(scenarios_json) if scenarios_json else []

        # 生成伪 embedding (基于 title + content 的前 500 字)
        text_for_embed = (title or "") + " " + (content or "")[:500]
        vec = hash_embedding(text_for_embed, dim=384)
        vec = normalize_vec(vec)

        records.append({
            "vector": vec,
            "template_id": template_id,
            "contract_type": contract_type,
            "industry": industry,
            "title": title,
            "content": content,
            "applicable_scenarios": scenarios,
            "lawyer_notes": lawyer_notes,
            "source": source,
            "category": category,
        })

    # 写 JSON 元数据 + 记录 (LanceDB 可直接读 JSON)
    records_path = EXPORT_DIR / "contract_records.json"
    records_path.write_text(
        json.dumps(records, ensure_ascii=False),
        encoding="utf-8",
    )
    log.info(f"记录写入: {records_path} ({len(records)} 条, {records_path.stat().st_size / 1024 / 1024:.1f} MB)")

    # 元信息
    metadata["records_path"] = str(records_path)
    metadata_path = EXPORT_DIR / "contract_metadata.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"元信息写入: {metadata_path}")

    conn.close()

    # 简单验证
    sample = records[0] if records else None
    if sample:
        log.info(f"样本: {sample['template_id']} - {sample['title']}")
        log.info(f"  vector dim: {len(sample['vector'])}")
        log.info(f"  vector norm: {sum(x*x for x in sample['vector'])**0.5:.4f}")

    return {
        "total": len(records),
        "export_dir": str(EXPORT_DIR),
        "size_mb": records_path.stat().st_size / 1024 / 1024,
    }


if __name__ == "__main__":
    stats = export_to_lancedb()
    log.info(f"完成: {stats}")
