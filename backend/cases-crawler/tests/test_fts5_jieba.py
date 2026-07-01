"""
W7: FTS5 中文分词 (jieba) 单元测试

覆盖:
- _pre_tokenize 中英混合分词正确
- _pre_tokenize_query 与 _pre_tokenize 对称
- _to_or_match 多 token 转 OR
- 中文检索命中数 (vs W4 unicode61)
- 索引元信息 (contract_fts_zh.meta.json)
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

CASES_CRAWLER = Path(__file__).parent.parent.parent
sys.path.insert(0, str(CASES_CRAWLER))

from scripts.w4.rebuild_fts5_index import (  # noqa: E402
    _pre_tokenize,
    _pre_tokenize_query,
    _to_or_match,
    DB_PATH,
)


# ===== 预分词 =====

class TestPreTokenize:
    def test_simple_chinese(self):
        """纯中文应切分为多 token"""
        out = _pre_tokenize("房屋租赁合同")
        assert "房屋" in out.split()
        assert "租赁" in out.split()
        assert "合同" in out.split()

    def test_english_digit_preserved(self):
        """英文/数字应作为独立 token 保留"""
        out = _pre_tokenize("Article 5 of the Civil Code 第 585 条")
        tokens = out.split()
        assert "article" in tokens or "Article".lower() in tokens
        assert "5" in tokens
        assert "civil" in tokens
        assert "code" in tokens
        # 中文部分被切
        assert "585" in tokens

    def test_empty_input(self):
        assert _pre_tokenize("") == ""
        assert _pre_tokenize(None) == ""

    def test_dedup(self):
        """重复 token 应去重"""
        out = _pre_tokenize("合同合同合同合同合同")
        assert out.split().count("合同") == 1


class TestQueryHelpers:
    def test_query_matches_tokenize(self):
        """查询侧与索引侧分词应对称"""
        q = "房屋租赁合同"
        assert _pre_tokenize_query(q) == _pre_tokenize(q)

    def test_to_or_match(self):
        """多 token 转 OR"""
        assert _to_or_match("管辖 不利") == "管辖 OR 不利"
        assert _to_or_match("房屋 租赁 合同") == "房屋 OR 租赁 OR 合同"
        assert _to_or_match("") == ""
        assert _to_or_match("合同") == "合同"


# ===== 集成: 数据库 FTS 验证 (需 jieba + 已重建索引) =====

@pytest.fixture(scope="module")
def db_conn():
    if not DB_PATH.exists():
        pytest.skip(f"DB 不存在: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    yield conn
    conn.close()


class TestFtsIntegration:
    def test_fts_table_exists(self, db_conn):
        """contract_fts_zh 表存在"""
        cur = db_conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='contract_fts_zh'"
        )
        assert cur.fetchone() is not None

    def test_fts_row_count_matches_templates(self, db_conn):
        """FTS 行数应与 templates 一致"""
        cur = db_conn.cursor()
        cur.execute("SELECT COUNT(*) FROM contract_templates")
        n_templates = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM contract_fts_zh")
        n_fts = cur.fetchone()[0]
        assert n_fts >= n_templates, f"FTS {n_fts} < templates {n_templates}"

    @pytest.mark.parametrize("query,min_hits", [
        ("房屋租赁合同", 10),   # W4: 0 → W7: 284
        ("借款合同", 50),       # W4: 3 → W7: 692
        ("劳动合同", 50),       # W4: 0 → W7: 412
        ("知识产权", 50),       # W4: 0 → W7: 446
        ("管辖", 100),          # W4: 1 → W7: 12050
        ("合同", 100),          # W4: 20 → W7: 12118
    ])
    def test_chinese_query_hits(self, db_conn, query, min_hits):
        """中文检索命中 (W4 unicode61 0 hits, W7 jieba 命中 N 条)"""
        cur = db_conn.cursor()
        # 用预分词 + OR 语义 (召回更宽容)
        seg = _to_or_match(_pre_tokenize_query(query))
        cur.execute(
            "SELECT COUNT(*) FROM contract_fts_zh WHERE contract_fts_zh MATCH ?",
            (seg,),
        )
        n = cur.fetchone()[0]
        assert n >= min_hits, f"{query!r} (seg={seg!r}) only {n} hits, expected >= {min_hits}"


# ===== 元信息 =====

class TestMetaJson:
    def test_meta_exists(self):
        """rebuild 脚本应写 contract_fts_zh.meta.json"""
        meta_path = DB_PATH.parent / "contract_fts_zh.meta.json"
        if not meta_path.exists():
            pytest.skip("Meta 文件不存在 (未跑过 rebuild)")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert meta["status"] == "ok"
        assert meta["tokenizer"].startswith("unicode61")
        assert "jieba" in meta["tokenizer"]
        assert meta["fts_rows"] > 0
        assert "房屋租赁合同" in meta["compare_queries"]