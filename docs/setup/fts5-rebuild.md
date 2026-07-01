# FTS5 中文分词重建 (jieba pre-tokenizer) 操作手册

> W8 D2 · 2026-06-29 · `lex-ai`
> 替代 W4 unicode61 单字粒度, 让 SQLite FTS5 中文中长关键词召回 > 0 hits

---

## 1. 背景: W4 unicode61 为什么 0 hits

LexPrime W4 第一次扩到 6076 合同模板, 用 SQLite FTS5 默认 `unicode61` tokenizer 建全文索引:

```sql
CREATE VIRTUAL TABLE contract_fts USING fts5(
    template_id UNINDEXED,
    title, content, applicable_scenarios, lawyer_notes,
    tokenize = 'unicode61'
);
```

`unicode61` 是 ASCII 字母/数字友好的分词器, **CJK 字符无词边界** → 整个长句被切成单 token:

| 查询 | unicode61 命中 | 期望 |
|---|---|---|
| `房屋租赁合同` | 0 | ≥ 1 |
| `劳动合同` | 0 | ≥ 1 |
| `股权转让` | 0 | ≥ 1 |
| `管辖` | 1 | ≥ 1 |
| `合同` | 20 | ≥ 1 |

→ 多字词 = 单 token, 不存在"匹配"概念, 召回 0。

## 2. 方案: jieba 预分词 + FTS5 unicode61

### 2.1 为什么是"预分词 + unicode61"而不是真·custom tokenizer

SQLite FTS5 自定义 tokenizer 需要 C 层 `sqlite3_db_config(SQLITE_CONFIG_FTS5_TOKENIZER)`,
Python stdlib `sqlite3` 模块不暴露此 API。要走原生 jieba tokenizer 必须:

- 方案 A: 编译 C 扩展 (jieba-c 绑定 FTS5 tokenizer), 工作量大 + 维护难
- 方案 B: 把 jieba 用 PyO3 包成 .pyd, FTS5 tokenize 调用 ↔ 跨语言封送 ↔ 高频抖动
- **方案 C (本项目采用)**: 写入 FTS5 前 jieba 预分词, 查询时同样 jieba 切 → unicode61 索引已切好的 tokens

方案 C 的优势:

- ✅ 纯 Python, 无 C 扩展负担
- ✅ 索引体积可控 (去重 + 长度过滤)
- ✅ 重启/Rebuild 即用
- ✅ FTS5 MATCH 表达式仍可用 (OR/AND 显式)

API 等价 tokenize='jieba', 但运行机制走 unicode61 → 文档中明示此 caveat.

### 2.2 调用契约

#### 写入侧

```python
from core.fts5_tokenizer import jieba_tokenize

original_text = "出租人张三, 承租人李四, 租期 12 个月"
indexed_text  = jieba_tokenize(original_text)
# indexed_text = "出租人 张三 承租人 李四 租期 12 个月"

cur.execute("INSERT INTO contracts_fts (contract_id, content) VALUES (?, ?)",
            (template_id, indexed_text))
```

#### 查询侧

```python
from core.fts5_tokenizer import tokenize_query, to_or_match

user_query = "房屋租赁合同"
match_expr = to_or_match(tokenize_query(user_query))
# match_expr = "房屋 OR 租赁 OR 合同"

cur.execute("SELECT * FROM contracts_fts WHERE contracts_fts MATCH ?",
            (match_expr,))
```

| 召回策略 | 函数 | 表达式 |
|---|---|---|
| 严格 AND (默认) | `to_and_match` | `"房屋 租赁 合同"` |
| 宽容 OR (推荐) | `to_or_match` | `"房屋 OR 租赁 OR 合同"` |

### 2.3 limitations (重要)

FTS5 是 **token-based** 索引 (不是 substring). 以下两种情况**不会召回**:

1. **多字词切分不一致**: 用户输入 `'房屋出租'` → jieba 切成 `['房屋出租']` 单 token; 但有些模板 content 中是 `'房屋 出租'` 两个独立 token → 两边 token 集不一致, MATCH 不命中
2. **词含子串**: 表里有 `'合同纠纷'` token, 查询 `'合同'` token → 不命中 (因为 FTS5 unicode61 token 不分解)

**对应缓解**:

- 业务侧统一调用 `to_or_match` (宽容召回) 而非 `to_and_match`
- 检索 UI 上让用户搜索 "主要成分词" 而非 "长复合词"
- 后续迭代可考虑改成 MeCab / HanLP 等更短词粒度分词

## 3. 一键重建流程

### 3.1 依赖

```powershell
# venv312 已包含 jieba==0.42.1 (D1 已装, 见 docs/setup/venv312-setup.md)
# 如果是新环境:
backend\venv312\Scripts\pip install jieba==0.42.1
```

### 3.2 重建 contracts_fts (W8 D2 spec 表)

```powershell
cd E:\元枢法智前端\yuanxing\backend\cases-crawler
.\venv312\Scripts\python.exe scripts\rebuild_fts5_index.py
```

预期输出 (D2 验收):

```
contracts_fts 当前存在: False
CREATE contracts_fts OK (tokenize='unicode61 remove_diacritics 2')
重读 6076 模板
INSERT 完成: inserted=6076, failed=0, 耗时 2.32s
contracts_fts 总行数: 6076
[PASS] '房屋租赁合同' → seg='房屋 租赁 合同' → '房屋 OR 租赁 OR 合同' → 2213 hits
[PASS] '劳动合同'   → seg='劳动合同' → '劳动合同' → 202 hits
[PASS] '股权转让'   → seg='股权 转让' → '股权 OR 转让' → 707 hits
D2 验证全部 PASS
```

元信息写入: `db/contracts_fts.meta.json`

### 3.3 重建 contract_fts_zh (W7 旧表)

```powershell
.\venv312\Scripts\python.exe scripts\w4\rebuild_fts5_index.py
```

> 注: W7 表 5 列, W8 D2 表 1 列 content + contract_id. 共存于同一 DB, 各用各的 schema.

## 4. 索引健康自检

```powershell
.\venv312\Scripts\python.exe -c "
import sqlite3
conn = sqlite3.connect(r'E:\元枢法智前端\yuanxing\backend\cases-crawler\db\contract_templates.db')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM contracts_fts')
print('contracts_fts rows:', cur.fetchone()[0])
cur.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'contracts_fts%'\")
for r in cur.fetchall(): print(' ', r[0])
cur.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'contract_fts%'\")
for r in cur.fetchall(): print('  legacy:', r[0])
conn.close()
"
```

应输出:

```
contracts_fts rows: 6076
  contracts_fts
  contracts_fts_config / content / data / docsize / idx
  legacy: contract_fts_zh
  legacy: contract_fts_zh_config / content / data / docsize / idx
```

## 5. 回归测试

```powershell
cd E:\元枢法智前端\yuanxing\backend\cases-crawler
.\venv312\Scripts\pytest.exe tests/test_fts5_tokenizer.py -v
.\venv312\Scripts\pytest.exe tests/test_fts5_jieba.py -v
```

预期:

- `test_fts5_tokenizer.py`: **25 passed** (W8 D2 新增, 覆盖 core 模块 API + in-memory FTS5)
- `test_fts5_jieba.py`: **15 passed** (W7 旧, 已 refactor 共用 core 模块, 仍 PASS)

合计 **40 passed**.

## 6. 性能基准 (W4 unicode61 vs W8 jieba)

| 查询 | unicode61 hits | jieba OR hits | 提升 | jieba AND hits |
|---|---|---|---|---|
| 房屋租赁合同 | 0 | 2213 | ∞ | 70 |
| 劳动合同 | 0 | 202 | ∞ | - |
| 股权转让 | 0 | 707 | ∞ | - |
| 借款合同 | 3 | 692+ | 230x | - |
| 管辖 | 1 | 12050 | 12000x | - |
| 合同 | 20 | 12118 | 600x | - |

(查询耗时 < 1ms P95, 见 `db/contracts_fts.meta.json`.)

## 7. 相关文档

- `docs/qa/fts5-zh-hit-w8.md` — D2 中文检索命中实测日志
- `docs/setup/venv312-setup.md` — jieba 装包 (D1 已落地)
- `backend/cases-crawler/core/fts5_tokenizer.py` — 核心 API 源码
- `backend/cases-crawler/scripts/rebuild_fts5_index.py` — 一键重建
- `backend/cases-crawler/scripts/w4/rebuild_fts5_index.py` — W7 旧表 (5 列 contract_fts_zh)
- `backend/cases-crawler/tests/test_fts5_tokenizer.py` — D2 单元测试 (25)
- `backend/cases-crawler/tests/test_fts5_jieba.py` — W7 单元测试 (15)

## 8. 历史版本

| 版本 | 日期 | 提交 | 表 | 列数 |
|---|---|---|---|---|
| W4 初始 | 2026-06 | (W4 follow-up) | `contract_fts` unicode61 | 5 |
| W7 升级 | 2026-06-28 | `aa8a85e` | `contract_fts_zh` jieba-pre | 5 |
| **W8 D2** | **2026-06-29** | **(本次)** | **`contracts_fts` jieba-pre** | **1+1** |

D2 在 W7 基础上做:
1. 模块化重构: `core/fts5_tokenizer.py` 暴露可复用 API
2. 新建 `contracts_fts` 表 (D2 spec: 1 content 列 + contract_id UNINDEXED)
3. 25 pytest 测试覆盖 core 模块
4. ruff 0 (check + format)
