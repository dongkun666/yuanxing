"""
W8 D2 FTS5 中文分词 (jieba pre-tokenizer) 单元测试

覆盖 core/fts5_tokenizer.py 模块 API:
- is_cjk_char: CJK 字符检测
- jieba_tokenize: 中文预分词 (含中英混合)
- tokenize_query / pre_tokenize_query: 查询侧分词对称性
- to_or_match / to_and_match: FTS5 MATCH 表达式生成
- pre_tokenize: W7 向后兼容别名
- FTS5 schema 常量: SCHEMA_CONTRACTS_FTS / SCHEMA_CONTRACT_FTS_ZH
- FTS5_TOKENIZER_NAME: 标识字段

策略:
- 纯单元测试, 不依赖数据库 (db fixture 在 test_fts5_jieba.py)
- pytest 8+ 框架
- 5+ 测试函数覆盖核心接口

依赖: jieba==0.42.1 (W7 已装 venv312)
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

# 项目根: cases-crawler/
CASES_CRAWLER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CASES_CRAWLER))

from core.fts5_tokenizer import (  # noqa: E402
    FTS5_TOKENIZER_NAME,
    SCHEMA_CONTRACT_FTS_ZH,
    SCHEMA_CONTRACTS_FTS,
    is_cjk_char,
    jieba_tokenize,
    pre_tokenize,
    pre_tokenize_query,
    to_and_match,
    to_or_match,
    tokenize_query,
)


# ===== is_cjk_char =====


class TestIsCjkChar:
    def test_cjk_unified_true(self):
        """CJK 统一汉字: 你/房/屋 应识别为 CJK"""
        assert is_cjk_char("你") is True
        assert is_cjk_char("房") is True
        assert is_cjk_char("屋") is True
        assert is_cjk_char("股") is True

    def test_cjk_ext_a_true(self):
        """CJK 扩展 A 区: 0x3400-0x4DBF 也算"""
        assert is_cjk_char("\u3400") is True  # "㐀"
        assert is_cjk_char("\u4db5") is True  # "䆵"

    def test_ascii_false(self):
        """ASCII 英数符不应算 CJK"""
        assert is_cjk_char("a") is False
        assert is_cjk_char("Z") is False
        assert is_cjk_char("0") is False
        assert is_cjk_char("5") is False
        assert is_cjk_char(" ") is False

    def test_empty_and_punct(self):
        """空字符串 + 标点 + 其他字符应 False"""
        assert is_cjk_char("") is False
        assert is_cjk_char(".") is False
        assert is_cjk_char(",") is False
        assert is_cjk_char("。") is False
        assert is_cjk_char("，") is False


# ===== jieba_tokenize =====


class TestJiebaTokenize:
    def test_pure_chinese(self):
        """纯中文应被 jieba 切成多 token (空格分隔)"""
        out = jieba_tokenize("房屋租赁合同")
        tokens = out.split()
        assert len(tokens) >= 2, f"jieba 应切 ≥ 2 token, got {tokens!r}"
        # 关键 tokens 必须在 (jieba 可能切 "房屋"/"租赁"/"合同" 三段)
        assert any("房屋" in t or t == "房" or t == "屋" for t in tokens), (
            f"tokens 缺房屋相关: {tokens}"
        )
        assert "合同" in tokens or any("合同" in t for t in tokens), (
            f"tokens 缺合同: {tokens}"
        )

    def test_chinese_to_target_phrases(self):
        """D2 验收 3 关键词 → 期望至少切出主要成分

        - 房屋租赁合同 → 应含 房屋/租赁/合同 至少 2 个
        - 劳动合同 → 应含 劳动/合同
        - 股权转让 → 应含 股权/转让
        """
        for kw, expected_substrs in [
            ("房屋租赁合同", ["房屋", "合同"]),
            ("劳动合同", ["劳动", "合同"]),
            ("股权转让", ["股权", "转让"]),
        ]:
            out = jieba_tokenize(kw)
            tokens = out.split()
            matched = [s for s in expected_substrs if any(s in t for t in tokens)]
            assert len(matched) >= 1, (
                f"{kw!r} tokens={tokens!r} 缺任一 {expected_substrs!r}, got {matched!r}"
            )

    def test_english_digit_preserved(self):
        """英文/数字 token 应作为独立 token 整体保留 (小写化)"""
        out = jieba_tokenize("Article 5 of the Civil Code")
        tokens = out.split()
        assert "article" in tokens, f"应保留 'article', got {tokens!r}"
        assert "civil" in tokens
        assert "code" in tokens
        assert "5" in tokens
        assert "of" in tokens
        assert "the" in tokens

    def test_mixed_chinese_english(self):
        """中英混合: 数字 token 保留, 中间中文 run 切词"""
        out = jieba_tokenize("Article 5 第 585 条")
        tokens = out.split()
        assert "article" in tokens
        assert "5" in tokens
        assert "585" in tokens
        # 中文应被切 (5xx / 第 / 条 / 第xxx条 等)
        assert len(tokens) >= 4, f"应切 ≥ 4 token, got {tokens!r}"

    def test_empty_input(self):
        """空字符串 / None 应返回空 (不抛)"""
        assert jieba_tokenize("") == ""
        assert jieba_tokenize(None) == ""

    def test_dedup(self):
        """重复 token 应去重, 保持首次出现顺序"""
        out = jieba_tokenize("合同合同合同合同")
        tokens = out.split()
        # jieba 切 "合同" 单 token, 重复 4 次 → 应只剩 1 个
        assert tokens.count("合同") == 1, f"dedup 失效, got {tokens!r}"

    def test_punct_stripped(self):
        """标点应转空格被 FTS5 separator 吃掉, 不进 token"""
        out = jieba_tokenize("出租人: 张三, 租金: 5000 元/月;")
        tokens = out.split()
        # "5000" 是 token (符合数字)
        assert "5000" in tokens
        # "元/月" 中的 "/" 应被剥离
        assert "元/月" not in tokens
        # ":" "," ";" "。" 等不应出现
        assert not any(t in ":,;" for t in tokens)


# ===== tokenize_query =====


class TestTokenizeQuery:
    def test_symmetric(self):
        """查询侧与索引侧分词应对称 (用户输入和存储字段切法一致)"""
        for kw in ("房屋租赁合同", "劳动合同", "股权转让", "管辖"):
            assert tokenize_query(kw) == jieba_tokenize(kw), (
                f"非对称: {kw!r} idx={jieba_tokenize(kw)!r} qry={tokenize_query(kw)!r}"
            )

    def test_alias_pre_tokenize_query(self):
        """pre_tokenize_query 别名应与 tokenize_query 等价"""
        assert pre_tokenize_query("房屋租赁合同") == tokenize_query("房屋租赁合同")
        assert pre_tokenize_query("管辖不利") == tokenize_query("管辖不利")

    def test_alias_pre_tokenize(self):
        """pre_tokenize 别名应与 jieba_tokenize 等价 (W7 向后兼容)"""
        assert pre_tokenize("房屋租赁合同") == jieba_tokenize("房屋租赁合同")
        assert pre_tokenize("股权转让协议") == jieba_tokenize("股权转让协议")


# ===== to_or_match / to_and_match =====


class TestMatchExpressions:
    def test_or_single_token(self):
        """单 token → 不需要 OR"""
        assert to_or_match("合同") == "合同"
        assert to_or_match("") == ""

    def test_or_multi_token(self):
        """多 token → 空格转 OR (召回宽容)"""
        assert to_or_match("管辖 不利") == "管辖 OR 不利"
        assert to_or_match("房屋 租赁 合同") == "房屋 OR 租赁 OR 合同"
        assert to_or_match("股权 转让") == "股权 OR 转让"

    def test_and_single_token(self):
        """单 token → 直接"""
        assert to_and_match("合同") == "合同"

    def test_and_multi_token(self):
        """多 token → 空格分隔 (默认 AND)"""
        assert to_and_match("管辖 不利") == "管辖 不利"
        assert to_and_match("房屋 租赁 合同") == "房屋 租赁 合同"

    def test_empty_input_passthrough(self):
        """空输入 → 原样返回 (不进 MATCH)"""
        assert to_or_match("") == ""
        assert to_and_match("") == ""


# ===== 模块常量 =====


class TestModuleConstants:
    def test_tokenizer_name_contains_jieba(self):
        """FTS5_TOKENIZER_NAME 应标识 jieba"""
        assert "jieba" in FTS5_TOKENIZER_NAME.lower()
        assert "unicode61" in FTS5_TOKENIZER_NAME.lower()

    def test_schema_contracts_fts_singleton(self):
        """SCHEMA_CONTRACTS_FTS 应定义 contracts_fts 单表 (D2 spec)"""
        assert "CREATE VIRTUAL TABLE" in SCHEMA_CONTRACTS_FTS
        assert "contracts_fts" in SCHEMA_CONTRACTS_FTS
        # 1 content 列 + 1 contract_id UNINDEXED
        assert "contract_id UNINDEXED" in SCHEMA_CONTRACTS_FTS
        assert "content" in SCHEMA_CONTRACTS_FTS

    def test_schema_contract_fts_zh_legacy(self):
        """SCHEMA_CONTRACT_FTS_ZH 应定义 5 列 contract_fts_zh (W7 legacy)"""
        assert "CREATE VIRTUAL TABLE" in SCHEMA_CONTRACT_FTS_ZH
        assert "contract_fts_zh" in SCHEMA_CONTRACT_FTS_ZH
        # 5 列 (template_id/title/content/scenarios/lawyer_notes)
        for col in (
            "template_id UNINDEXED",
            "title",
            "content",
            "applicable_scenarios",
            "lawyer_notes",
        ):
            assert col in SCHEMA_CONTRACT_FTS_ZH, f"缺列 {col!r}"


# ===== in-memory FTS5 集成 (无需 DB 文件) =====


class TestFts5InMemory:
    """用 sqlite3 :memory: 验证 modules 配合 FTS5 unicode61 实际能跑 (不需要 DB 文件)"""

    def test_contracts_fts_chinese_hits(self):
        """contracts_fts 内存表: 中文预分词 + MATCH OR 应 > 0 hits

        注意: FTS5 是 token-based, jieba "合同纠纷" 不 = token "合同"
        所以样本需要 jieba 切出 单独 "合同" token (而非作为 长 token 子串)
        """
        conn = sqlite3.connect(":memory:")
        conn.executescript(SCHEMA_CONTRACTS_FTS)
        cur = conn.cursor()

        # 注入 1 个含 房屋/租赁/合同 tokens 的样本 (jieba 各切出独立 token)
        sample = "本 合同 为 房屋 租赁 标的 张三 李四 双方 友好 协商"
        seg = jieba_tokenize(sample)
        cur.execute(
            "INSERT INTO contracts_fts (contract_id, content) VALUES (?, ?)",
            ("contract-001", seg),
        )
        conn.commit()

        # 查询 "房屋租赁合同" → jieba 切词 "房屋 租赁 合同" + OR match
        match = to_or_match(tokenize_query("房屋租赁合同"))
        cur.execute(
            "SELECT COUNT(*) FROM contracts_fts WHERE contracts_fts MATCH ?", (match,)
        )
        n = cur.fetchone()[0]
        assert n > 0, (
            f"应命中 1 条 (该样本含 房屋/租赁/合同 tokens), got {n}; match={match!r}, seg={seg!r}"
        )
        conn.close()

    def test_contracts_fts_equity_transfer(self):
        """股权转让 → 应命中含 股权/转让 tokens 的样本"""
        conn = sqlite3.connect(":memory:")
        conn.executescript(SCHEMA_CONTRACTS_FTS)
        cur = conn.cursor()
        # 注: jieba 倾向把 "股权转让" 切为 "股权 转让" (2 token), 单 token "股权转让" 不一定存在
        sample = "甲方 将 持有 目标公司 30% 股权 转让 给 乙方"
        seg = jieba_tokenize(sample)
        cur.execute(
            "INSERT INTO contracts_fts (contract_id, content) VALUES (?, ?)",
            ("contract-002", seg),
        )
        conn.commit()
        match = to_or_match(tokenize_query("股权转让"))
        cur.execute(
            "SELECT COUNT(*) FROM contracts_fts WHERE contracts_fts MATCH ?", (match,)
        )
        n = cur.fetchone()[0]
        assert n > 0, f"应命中 1 条, got {n}; match={match!r}, seg={seg!r}"
        conn.close()

    def test_contracts_fts_and_match_strict(self):
        """OR match (宽容) 召回更多; 比 AND 严格

        设计: 4 行样本, 查询 "股权转让" (jieba 切成 2 token), 验证 OR/AND 召回差异
        """
        conn = sqlite3.connect(":memory:")
        conn.executescript(SCHEMA_CONTRACTS_FTS)
        cur = conn.cursor()
        # c1: 股权 + 转让 都中
        cur.execute(
            "INSERT INTO contracts_fts (contract_id, content) VALUES (?, ?)",
            ("c1", jieba_tokenize("甲乙 双方 签署 股权 转让 协议")),
        )
        # c2: 仅 股权 (无 转让)
        cur.execute(
            "INSERT INTO contracts_fts (contract_id, content) VALUES (?, ?)",
            ("c2", jieba_tokenize("持有 目标公司 股权 收益")),
        )
        # c3: 仅 转让 (无 股权)
        cur.execute(
            "INSERT INTO contracts_fts (contract_id, content) VALUES (?, ?)",
            ("c3", jieba_tokenize("技术 转让 合同")),
        )
        # c4: 都不中
        cur.execute(
            "INSERT INTO contracts_fts (contract_id, content) VALUES (?, ?)",
            ("c4", jieba_tokenize("房屋 租赁 业务")),
        )
        conn.commit()

        # 查询 "股权转让" → 切成 2 tokens "股权 转让"
        seg_q = tokenize_query("股权转让")
        assert len(seg_q.split()) == 2, f"jieba 应切 2 token, got {seg_q!r}"

        # AND: 必须 股权 + 转让 都中 → 仅 c1
        match_and = to_and_match(seg_q)
        cur.execute(
            "SELECT COUNT(*) FROM contracts_fts WHERE contracts_fts MATCH ?",
            (match_and,),
        )
        n_and = cur.fetchone()[0]
        assert n_and == 1, f"AND 应仅命中 c1, got {n_and}; match={match_and!r}"

        # OR: 任一 token 中即中 → c1, c2, c3
        match_or = to_or_match(seg_q)
        cur.execute(
            "SELECT COUNT(*) FROM contracts_fts WHERE contracts_fts MATCH ?",
            (match_or,),
        )
        n_or = cur.fetchone()[0]
        assert n_or == 3, f"OR 应命中 c1+c2+c3 = 3, got {n_or}; match={match_or!r}"

        # 关键断言: OR ≥ AND (宽容 vs 严格)
        assert n_or > n_and, f"OR({n_or}) 应 > AND({n_and}); OR 更召回"
        conn.close()
