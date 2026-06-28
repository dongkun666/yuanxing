# LexPrime Cases Crawler · 自建数据基础设施

> LexPrime 律所版 0.1 的数据基座 · 2026-06-28

## 战略定位

**0 收费 API，100% 自建壁垒**。LexPrime 不依赖任何收费 API，所有核心数据都自己爬、自己存、自己索引。

4 个**免费**公开数据源 + 1 个**开源种子**（cncases 8500 万判例）+ 1 个**自部署大模型**（Qwen2.5-72B）。

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│         LexPrime 主前端 (yuanxing)  v0.7                 │
│  sidebar 加 "判例库" "法规库" "企业征信" "律所管理" 入口   │
└──────────────────┬──────────────────────────────────────┘
                   │ REST API (FastAPI)
                   ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI  (api/main.py)                      │
│  /api/cases · /api/laws · /api/companies · /api/search  │
│  /api/firm/lawyers · /api/firm/time-entries             │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┼──────────┬──────────┐
        ▼          ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │Postgres│ │  ES    │ │ Neo4j  │ │  LLM   │
   │  16    │ │  8.15  │ │  5.25  │ │Qwen72B │
   │ (主存储)│ │(全文检索)│ │(股权穿透)│ │(自部署)│
   └────┬───┘ └────┬───┘ └────┬───┘ └────────┘
        │          │          │
        │          │          │
   ┌────┴──────────┴──────────┴────────────────┐
   │       4 个免费数据源爬虫 + cncases 导入     │
   │  npc_laws · court_cases · zhixing · gsxt  │
   │  + cncases_importer (8500 万判例)          │
   └────────────────────────────────────────────┘
```

## 4 个免费数据源

| 数据源 | URL | 字段数 | 规模 | LexPrime 用途 |
|---|---|---|---|---|
| 国家法律法规数据库 | flk.npc.gov.cn | 12 | 6,000+ 部 | 法规主源 |
| 人民法院案例库 | rmfyalk.court.gov.cn | 12 | 数千案例 | 司法观点 + 判例 |
| 中国执行信息公开网 | zxgk.court.gov.cn | 8 | 千万级 | 失信查询主源 |
| 国家企业信用 | gsxt.gov.cn | 14 | 5000 万+ | 企业征信主源 |

## 快速开始

### 1. 启动基础设施

```bash
cd E:\元枢法智前端\yuanxing\backend\cases-crawler

# 复制环境变量
cp .env.example .env

# 启动 PG / ES / Neo4j
docker-compose up -d

# 等待健康 (约 30 秒)
docker-compose ps
```

### 2. 安装 Python 依赖

```bash
# 创建虚拟环境
python -m venv venv
.\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 初始化数据库

```bash
python scripts/init_db.py --seed
# 创建 schema + ES 索引 + Neo4j 约束 + 律所 demo 数据
```

### 4. 下载 cncases 数据 (可选)

cncases 8500 万判例 102GB，BT 下载 8-24 小时。**不下载全量也可运行 LexPrime**（4 个免费源已经够用）。

```bash
# 下载种子
# 1. 访问 https://github.com/cncases/cases/releases
# 2. 下载 810air.torrent
# 3. 用 qBittorrent / Transmission 下载
# 4. 解压种子得到 "裁判文书全量数据（已完成..." 文件夹
# 5. 不要解压 ZIP，把文件夹路径填到 .env 的 CNCASES_RAW_PATH

# 导入
python -m importers.cncases_importer --raw-path /path/to/zip
```

### 5. 跑 4 个免费数据源

```bash
python -m crawlers.dispatcher
```

### 6. 启动 API

```bash
python -m api.main
# API 监听 http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

## 目录结构

```
cases-crawler/
├── core/                   # 配置 + DB 连接 + ORM + 脱敏
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   └── sanitize.py
├── db/
│   ├── schema.sql          # PG 表 + 索引
│   ├── elasticsearch_indices.json  # ES mappings
│   └── neo4j_constraints.cypher    # Neo4j 约束
├── crawlers/
│   ├── sources/            # 4 个免费数据源
│   │   ├── base.py
│   │   ├── npc_laws.py
│   │   ├── court_cases.py
│   │   ├── zhixing.py
│   │   └── gsxt.py
│   ├── middlewares/
│   │   └── anti_ban.py
│   └── dispatcher.py
├── importers/
│   └── cncases_importer.py # 8500 万判例导入器
├── api/
│   └── main.py             # FastAPI
├── scripts/
│   └── init_db.py          # 一键初始化
├── tests/
├── data/                   # 原始数据 (gitignore)
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md
```

## 数据库表

- **cases** (判例) — cncases 兼容 + LexPrime 增强 (12 字段 + 标签/评分/计数)
- **laws** (法规) — 国家库 + 自建司法解释
- **companies** (企业) — 国家库 + 启信宝/天眼查公开数据
- **lawyer_added_cases** (律师自加判例) — 内部数据护城河
- **favorites** (收藏) — 跨 3 库
- **firms** + **lawyers** + **firm_case_assignments** + **firm_time_entries** — 律所版 0.1 基础

## 合规边界

- ✅ 只爬**公开**数据
- ✅ 自动脱敏: 身份证 / 手机号 / 银行卡 / 详细住址 / 人名
- ✅ 标注数据来源 + 抓取时间
- ✅ 律所数据隔离 (multi-tenant)
- ❌ 不存储未公开判决理由
- ❌ 不绕过登录/付费墙/验证码

## 性能预期

- 100 万判例: ~30GB 存储 (PG 5GB + ES 25GB)
- 6 千万企业: ~15GB
- 全文检索 (1 亿文档): < 100ms
- 单爬虫节点: 1000-5000 判例/小时 (看目标网站)

## 后续 Roadmap

- **Q3 2026**: 跑通 4 源 + 100 万判例 (cncases 子集)
- **Q4 2026**: 判例库 1000 万 + 企业库 500 万
- **2027 H1**: 自部署 Qwen2.5-72B (1-3M 投资) + 法律微调
- **2027 H2**: 电子签 v2 (CA 牌照) + 律所版市占前三

## License

MPL-2.0 (借鉴 cncases/cases 仓库)
