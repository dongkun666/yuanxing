# cncases 判例数据下载与导入指南

> LexPrime 判例库建设核心文档 · 2026-06-28 · Phase 1.2

## 为什么用 cncases

[cncases/cases](https://github.com/cncases/cases) 是中国裁判文书网（公开数据）的**本地搜索项目**，
1 ⭐ 1000+ / 124 forks / MPL-2.0 协议，**8500 万+ 判例**（来源：马克数据网），
**102GB ZIP 压缩包**。

| 数据维度 | 规模 | 说明 |
|---|---|---|
| 判例总数 | 8500 万+ | 1.4 亿中国裁判文书网公开数据子集 |
| 原始大小 | 102 GB | BT 种子下载 |
| 数据库转换后 | ~200 GB | cncases 用 fjall (RocksDB) |
| 全文索引 | ~150 GB | cncases 用 Tantivy |

我们 LexPrime 用 **PostgreSQL + Elasticsearch** 替代 cncases 的 fjall + Tantivy，字段直接对齐 cncases 的 `Case` struct。

---

## 第一步：下载 BT 种子

### 选项 A：从 GitHub release（推荐）

```bash
# 1. 访问 cncases releases
# https://github.com/cncases/cases/releases

# 2. 下载最新种子
# v0.2.11 包含 810air.torrent

# 3. 用 qBittorrent / Transmission / 迅雷 打开种子
# 保存到: E:/data/cncases/
mkdir -p E:/data/cncases
# 把 810air.torrent 拖入 qBittorrent，下载路径设为 E:/data/cncases
```

### 选项 B：直接下载 torrent 文件

```bash
# 浏览器直接下载
curl -L -o E:/data/cncases/810air.torrent \
  https://files.catbox.moe/810air.torrent

# 或用 PowerShell
Invoke-WebRequest -Uri "https://files.catbox.moe/810air.torrent" \
  -OutFile "E:/data/cncases/810air.torrent"
```

### 速度预期

| 网络 | 预计时间 |
|---|---|
| 1 Gbps 专线 | 1-2 小时 |
| 100 Mbps 家庭 | 8-16 小时 |
| 50 Mbps | 16-32 小时 |

> ⚠️ **不要解压 ZIP 文件！** cncases 工具链直接读 ZIP（流式处理，节省 100GB 磁盘空间）。

---

## 第二步：配置 LexPrime

### 2.1 编辑 .env

```bash
cd E:\元枢法智前端\yuanxing\backend\cases-crawler
cp .env.example .env

# 关键配置
CNCASES_RAW_PATH=E:/data/cncases
CNCASES_BATCH_SIZE=5000
```

### 2.2 验证数据下载

```bash
ls -lah E:/data/cncases/
# 应该看到类似:
# 裁判文书全量数据（已完成 - 副本 (1).zip  ~ 2GB
# 裁判文书全量数据（已完成 - 副本 (2).zip  ~ 2GB
# ...
# 裁判文书全量数据（已完成 - 副本 (N).zip
```

cncases 数据按**分卷 ZIP**组织，每个 ZIP ~2GB，共约 50 个 ZIP 文件。

### 2.3 数据结构 (cncases Case struct)

cncases CSV 字段（**GBK 编码**，**中文列名**）：

| 列名 | 类型 | 说明 |
|---|---|---|
| 原始链接 | string | 裁判文书网 URL (含 docId) |
| 案号 | string | 如 (2023) 京01民终 1234 号 |
| 案件名称 | string | |
| 法院 | string | |
| 案件类型 | string | 民事/刑事/行政/执行 |
| 审理程序 | string | 一审/二审/再审 |
| 裁判日期 | string | YYYY-MM-DD |
| 公开日期 | string | YYYY-MM-DD |
| 当事人 | string | |
| 案由 | string | 130+ 二级案由 |
| 法律依据 | string | 引用法条 |
| 全文 | string | HTML 格式 |

我们的 LexPrime `cases` 表字段**完全对齐**这 12 字段 + LexPrime 增强（cause_category / cause_color / lex_score / lex_tags / view_count 等）。

---

## 第三步：跑导入器

### 3.1 全量导入（8500 万判例，~6-12 小时）

```bash
cd E:\元枢法智前端\yuanxing\backend\cases-crawler

# 推荐: 限制条数先测试
python -m importers.cncases_importer --raw-path E:/data/cncases --limit 10000

# 验证数据
python -c "
import asyncio
from core.db import Database
from core.models import Case
from sqlalchemy import select, func

async def check():
    await Database.init()
    async with Database.session() as s:
        c = await s.execute(select(func.count(Case.id)))
        print('Cases:', c.scalar())
        c = await s.execute(select(Cause.cause, func.count(Cause.id)).group_by(Cause.cause).limit(10)) if False else None
    await Database.close()

asyncio.run(check())
"
```

### 3.2 增量导入（只导入未导入的判例）

```bash
# LexPrime 的 cncases_importer 已经实现幂等:
# - doc_id 是 UNIQUE, 已存在的会跳过
# - 中途中断重跑会从断点继续

# 完整跑
python -m importers.cncases_importer --raw-path E:/data/cncases
```

### 3.3 只导入精选类别（加速 + 实用）

cncases 数据按 ZIP 分卷，每个 ZIP 是**混合**案件类型。LexPrime 提供筛选：

```python
# 改 importers/cncases_importer.py 的 parse_row 添加过滤:
def parse_row(self, row):
    case = ... # 标准解析
    # 筛选: 只导入民商事 + 刑事
    if case['case_type'] not in ['民事', '刑事', '行政']:
        return None
    return case
```

或者**按年份**筛选（如 2020-2024）：

```python
if not case['judgment_date'] or case['judgment_date'].year < 2020:
    return None
```

### 3.4 进度监控

```bash
# SQLite: 直接查
python -c "
import sqlite3
c = sqlite3.connect('data/lexprime.db')
print('Total cases:', c.execute('SELECT COUNT(*) FROM cases').fetchone()[0])
print('By year:', c.execute('SELECT year, COUNT(*) FROM cases GROUP BY year ORDER BY year').fetchall())
"

# PostgreSQL: 用 psql
psql -U lexprime -d lexprime -c "SELECT year, COUNT(*) FROM cases GROUP BY year ORDER BY year;"
```

---

## 第四步：导入后 Elasticsearch 索引

默认 `cncases_importer` 已经同时写 ES。如果跳过：

```bash
# 单独跑 ES 索引
python -c "
import asyncio
from core.db import Database, ESClient
from core.models import Case
from sqlalchemy import select
from core.config import settings

async def reindex():
    await Database.init()
    await ESClient.init()
    if ESClient.is_mock():
        print('ES not available, in-memory only')
        return
    async with Database.session() as s:
        cases = (await s.execute(select(Case))).scalars().all()
        for c in cases:
            await ESClient.index_doc(
                settings.es_index_cases,
                str(c.id),
                {'id': c.id, 'case_name': c.case_name, 'cause': c.cause, ...}
            )
    print('Indexed', len(cases), 'cases')
    await Database.close()
    await ESClient.close()

asyncio.run(reindex())
"
```

---

## 第五步：律师自加判例（内部数据护城河）

cncases 是公开数据，**律师自己的判例才是 LexPrime 的护城河**。

LexPrime 提供 `lawyer_added_cases` 表 + 前端「+ 内部判例」入口：

```sql
-- 律师上传
INSERT INTO lawyer_added_cases (lawyer_id, firm_id, title, full_text, cause, visibility, notes)
VALUES ('u-1', 'firm-demo-001', '我代理的 XX 案', '...', '合同纠纷', 'firm', '案号 (2024) 京01民初 1234');
```

`visibility`:
- `private` — 仅自己可见
- `firm` — 律所共享（**核心功能**, 同事可搜索）
- `public` — 公开（成为 LexPrime 知识库一部分）

---

## 数据合规边界

⚠️ **重要**: LexPrime 自建判例库严格遵循以下原则：

1. **只爬公开数据** — 裁判文书网公开页 / 人民法院案例库 / 律师自加
2. **自动脱敏** — 身份证 / 手机号 / 银行卡 / 详细住址全部 `***` 替换
3. **不存储未公开判决理由** — 裁判文书网只公开"判决书正文", 内部合议庭笔录不公开
4. **标注来源** — 每条判例 `source` 字段标注: cncases / court_cases / lawyer_added
5. **律师自加归律师所有** — 离开 LexPrime 时, 律师可导出所有自己加的判例

---

## 替代方案

如果不想下载 102GB BT 种子（占磁盘 + 8-24h 慢），可以先用 4 个免费数据源：

| 数据源 | 规模 | 速度 | 适用场景 |
|---|---|---|---|
| 人民法院案例库 | 数千精选 | 1-2 小时 | 律师日常足够 |
| 中国裁判文书网 | 1.4 亿 | 反爬严 | 增量爬取（数月）|
| 国家法律法规数据库 | 6,000+ | 1 小时 | 法规覆盖 |
| 国家企业信用 | 5000 万 | 1-2 天 | 企业征信 |
| cncases 102GB | 8500 万 | 8-24h | 一次性全量 |

**建议路径**:
- 第 1 周: 跑 4 个免费源（快速上线）
- 第 2-4 周: 增量爬裁判文书网（每日 5000-10000 条）
- 第 3-6 月: 下载 cncases 全量（背景任务）

---

## 故障排查

### Q1: 导入中断了怎么办？

cncases_importer 幂等，重跑会跳过已导入的：

```bash
# 中断后直接重跑
python -m importers.cncases_importer --raw-path E:/data/cncases
# 不会重复导入（doc_id UNIQUE 约束）
```

### Q2: SQLite 太慢怎么办？

SQLite 适合 < 100 万判例。超过 100 万建议切换到 PostgreSQL：

```bash
# docker-compose up -d
# 修改 .env: DATABASE_URL=postgresql+asyncpg://...
python -m scripts.init_db --backend postgres
python -m importers.cncases_importer --raw-path E:/data/cncases
```

### Q3: 内存不够？

cncases_importer 一次处理 5000 条（默认 `CNCASES_BATCH_SIZE`）。内存不足时：

```bash
python -m importers.cncases_importer --raw-path E:/data/cncases --batch-size 1000
```

### Q4: 想跳过全文 (full_text) 节省空间？

```python
# cncases_importer.py 改 parse_row:
case['full_text'] = None
case['full_text_plain'] = None
```

全文占 80% 空间，跳过后判例数据从 200GB 降到 40GB。

---

## 法律声明

- cncases 数据是**裁判文书网公开数据**的再分发，遵循中国《最高人民法院关于人民法院在互联网公布裁判文书的规定》
- LexPrime 不对原始数据再分发，仅供内部律师查询使用
- 律师自加判例由律师个人承担合规责任
- MPL-2.0 协议要求保留 cncases 原始版权声明

---

## 相关链接

- cncases 仓库: https://github.com/cncases/cases
- cncases 演示: https://caseopen.org/
- 裁判文书网: https://wenshu.court.gov.cn/
- 人民法院案例库: https://rmfyalk.court.gov.cn/
- 国家法律法规数据库: https://flk.npc.gov.cn/
- 国家企业信用: https://www.gsxt.gov.cn/

---

_最后更新: 2026-06-28 · LexPrime 0.7.0_
