"""
LexPrime FTS5 中文分词模块 (jieba pre-tokenizer)
2026-06-29 · W8 D2

W4 遗留问题:
- SQLite FTS5 默认 unicode61 tokenizer 对中文不分词
- "房屋租赁合同" / "违约金过高" / "股权转让" 等多字词 → 0 hits
- 仅单词 "合同" "借款" "管辖" 能命中 (召回效率低)

W8 D2 解法 (模块化重构):
- 把 W7 scripts/w4/rebuild_fts5_index.py 里散落的 _pre_tokenize 系列函数
  提取到 core/ 可复用模块
- 提供面向 SQLite FTS5 的语义化 API (jieba_tokenize, tokenize_query, to_or_match)
- 与 FTS5 原生 tokenizer 接口对齐 (命名/返回值), 实际是预分词 + unicode61 兜底

设计要点:
1. **预分词前置**: jieba 在写入 FTS5 之前对中文字符 run 切词, 英文/数字保留原 token
2. **FTS5 内部仍用 unicode61**: 因为预先切好的 tokens 之间有空格, unicode61 不会越权
3. **查询侧对称**: 用户输入 query → 同样 jieba 切词 → 转 OR 表达式 → MATCH
4. **失败兜底**: jieba 缺失时退化为单字粒度 (仍优于 unicode61 0 hits)

限制说明 (重要):
- 真正的 SQLite FTS5 自定义 tokenizer (含 xTokenize callback) 需要 C 扩展,
  Python stdlib sqlite3 模块不暴露 sqlite3_db_config(SQLITE_CONFIG_FTS5_TOKENIZER)
- 项目用 "预分词 + FTS5 unicode61" 等价方案, 对调用方 API 一致
- 性能: 预分词是 O(N) 一次性开销, 查询侧开销可忽略 (毫秒级)

依赖: jieba==0.42.1 (W7 已装 venv312, 系统 Python 3.14 需 pip install jieba 兜底)

用法:
    from core.fts5_tokenizer import jieba_tokenize, tokenize_query, to_or_match

    # 写入侧
    indexed = jieba_tokenize(long_chinese_text)  # → "房屋 租赁 合同"

    # 查询侧
    match_expr = to_or_match(tokenize_query("房屋租赁合同"))
    # → "房屋 OR 租赁 OR 合同"
"""

from __future__ import annotations

import logging
import re
from typing import Optional

log = logging.getLogger(__name__)

# 模块级常量 (CJK Unified Ideographs 范围 + ASCII 英数字段)
_CJK_RANGE = "\u4e00-\u9fff"  # CJK 统一
_CJK_EXT_A = "\u3400-\u4dbf"  # CJK 扩展 A

# 切词正则: (1) 英文/数字/下划线串 (2) CJK 串 (其余字符视为分隔符)
_TOKEN_PATTERN = re.compile(rf"([A-Za-z0-9_]+)|([{_CJK_RANGE}{_CJK_EXT_A}]+)")

# 单 token 最大长度 (过滤噪声: 极端长中文+英数混排误命中)
_MAX_TOKEN_LEN = 30

# 最小 jieba 可用性缓存 (避免每次调用都 import)
_JIEBA_AVAILABLE: Optional[bool] = None


def _ensure_jieba() -> bool:
    """懒加载 jieba, 不存在则 False (调用方退化为单字粒度)"""
    global _JIEBA_AVAILABLE
    if _JIEBA_AVAILABLE is not None:
        return _JIEBA_AVAILABLE
    try:
        import jieba  # noqa: F401  # pylint: disable=import-outside-toplevel
        import jieba.posseg  # noqa: F401  # pylint: disable=import-outside-toplevel

        jieba.setLogLevel(logging.WARNING)
        _JIEBA_AVAILABLE = True
    except ImportError:
        log.warning(
            "jieba 未安装, FTS5 tokenize 退化为单字粒度. "
            "建议: backend/venv312/Scripts/pip install jieba==0.42.1"
        )
        _JIEBA_AVAILABLE = False
    return _JIEBA_AVAILABLE


def is_cjk_char(ch: str) -> bool:
    """判断是否为中日韩字符 (CJK Unified + 扩展 A)"""
    if not ch:
        return False
    code = ord(ch)
    return 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF


def jieba_tokenize(text: str) -> str:
    """中文预分词 + 保留英文/数字 token

    算法:
    1. 用正则把 text 切成 CJK 段 和 英数字段 两类
    2. CJK 段 → jieba.cut() 切词, 输出多 token
    3. 英数字段 → 小写化作为单 token (匹配时不区分大小写)
    4. 结果合并去重, 空格分隔 (FTS5 token separator)

    Args:
        text: 原始文本 (可含中文/英文/数字/标点混合)

    Returns:
        空格分隔的 tokens 字符串 (FTS5 内容字段直接 MATCH)

    Examples:
        >>> jieba_tokenize("房屋租赁合同")
        '房屋 租赁 合同'  # jieba 实际切法可能略有不同
        >>> jieba_tokenize("Article 5 第 585 条")
        'article 5 第 585 条'
        >>> jieba_tokenize("")
        ''
    """
    if not text:
        return ""

    parts: list[str] = []
    if _ensure_jieba():
        import jieba  # pylint: disable=import-outside-toplevel

        for m in _TOKEN_PATTERN.finditer(text):
            if m.group(1):
                # 英数字段: 整体小写作为单 token
                parts.append(m.group(1).lower())
            elif m.group(2):
                # CJK 段: jieba 切词
                for tok in jieba.cut(m.group(2)):
                    tok = tok.strip()
                    if tok and len(tok) <= _MAX_TOKEN_LEN:
                        parts.append(tok)
    else:
        # jieba 缺失退化: 单字粒度 (仍优于 unicode61 0 hits)
        for ch in text:
            if is_cjk_char(ch):
                parts.append(ch)
            # 标点/空白跳过 (FTS5 unicode61 默认 separator)

    # 去重保序 (FTS5 MATCH 默认 OR, 重复 token 浪费索引空间)
    seen: set[str] = set()
    deduped: list[str] = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            deduped.append(p)
    return " ".join(deduped)


def tokenize_query(query: str) -> str:
    """查询侧预分词 (与 jieba_tokenize 对称)

    用户输入 "房屋租赁合同" → "房屋 租赁 合同"
    输出直接 MATCH 即可 (FTS5 默认空格为 AND 关系)

    Args:
        query: 原始查询字符串 (中文/英文)

    Returns:
        空格分隔的 tokens 字符串, 与索引字段分词结果对齐
    """
    return jieba_tokenize(query)


def to_or_match(segmented: str) -> str:
    """把空格分隔的多 token 转成 FTS5 OR 表达式 (召回宽容)

    用例: 用户希望召回更宽容, 而非严格 AND (默认):
    - "管辖 不利" → "管辖 OR 不利" (任一命中)
    - "房屋 租赁 合同" → "房屋 OR 租赁 OR 合同"

    Args:
        segmented: jieba_tokenize() / tokenize_query() 的输出

    Returns:
        OR 表达式, 可直接传给 FTS5 MATCH
    """
    tokens = [t for t in segmented.split() if t]
    if not tokens:
        return segmented
    if len(tokens) == 1:
        return tokens[0]
    return " OR ".join(tokens)


def to_and_match(segmented: str) -> str:
    """FTS5 AND 显式表达 (严格召回)

    Args:
        segmented: jieba_tokenize() / tokenize_query() 的输出

    Returns:
        AND 表达式, 可直接传给 FTS5 MATCH (默认空格也是 AND, 此处显式表达)
    """
    tokens = [t for t in segmented.split() if t]
    if not tokens:
        return segmented
    return " ".join(tokens)


# ============================================================
# 高层 API: 面向业务方调用 (与 W7 行为兼容)
# ============================================================


def pre_tokenize(text: str) -> str:
    """别名 jieba_tokenize (兼容 W7 scripts/w4/rebuild_fts5_index.py)"""
    return jieba_tokenize(text)


def pre_tokenize_query(query: str) -> str:
    """别名 tokenize_query (兼容 W7 scripts/w4/rebuild_fts5_index.py)"""
    return tokenize_query(query)


# ============================================================
# FTS5 schema 常量 (供 rebuild 脚本/测试统一引用)
# ============================================================

# 注意: SQLite FTS5 实际不可能直接 tokenize='jieba'
# (Python sqlite3 不暴露 sqlite3_db_config 启用自定义 tokenizer)
# 这里保留符号名 + 注释说明, 让调用方代码语义清晰
FTS5_TOKENIZER_NAME = "unicode61 + jieba-pre-segmentation"

# contracts_fts (D2 新表) schema: 1 content 列 + contract_id UNINDEXED
SCHEMA_CONTRACTS_FTS = """
-- W8 D2: jieba 预分词版 contracts_fts 表
-- 内容字段已预分词, FTS5 内部仍用 unicode61 (空格分隔单 token 即可索引)
-- 替换或共存于 W7 contract_fts_zh 表 (5 列版本)
CREATE VIRTUAL TABLE IF NOT EXISTS contracts_fts USING fts5(
    contract_id UNINDEXED,
    content,
    tokenize = 'unicode61 remove_diacritics 2'
);
"""

# contract_fts_zh (W7 旧表) schema: 5 列版本 (向后兼容, 仅供 refactor 调用)
SCHEMA_CONTRACT_FTS_ZH = """
-- W7 jieba 预分词版 contract_fts_zh 表 (5 列)
CREATE VIRTUAL TABLE IF NOT EXISTS contract_fts_zh USING fts5(
    template_id UNINDEXED,
    title,
    content,
    applicable_scenarios,
    lawyer_notes,
    tokenize = 'unicode61 remove_diacritics 2'
);
"""


__all__ = [
    "FTS5_TOKENIZER_NAME",
    "SCHEMA_CONTRACTS_FTS",
    "SCHEMA_CONTRACT_FTS_ZH",
    "is_cjk_char",
    "jieba_tokenize",
    "pre_tokenize",
    "pre_tokenize_query",
    "tokenize_query",
    "to_and_match",
    "to_or_match",
]
