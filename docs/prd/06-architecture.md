<!-- Auto-split from PRD.md v0.7.0 on 2026-06-28 -->
> 本文档为 LexPrime 全面 PRD 的分章节版本, 供各 agent 独立阅读
> 主文档: `PRD.md` · 完整 15 章节 42KB · 各章节交叉引用见 `00-index.md`


# 技术架构

> LexPrime PRD v0.7.0 · 2026-06-28

---


## 7. 技术架构


### 7.1 技术选型总览

| 层面 | 选型 | 理由 |
|---|---|---|
| **桌面框架** | **Electron 28+** | 跨平台, 一套代码出 Win / Mac / Linux |
| **前端** | **React 18 + TypeScript** | 生态大, 社区活跃, 与 Electron 完全复用 |
| **文书编辑器** | **Slate.js + 自研法律插件** | 基于 OT 的操作序列存储, 支持修订模式 |
| **移动端** | React Native / Flutter | 复用业务逻辑, UI 独立适配 |
| **鸿蒙端** | ArkUI | 华为生态兼容 |
| **后台服务** | **Rust (核心) + Python (AI 服务)** | 高性能安全 + AI 生态丰富 |
| **API 通信** | JSON-RPC (IPC) + REST + WebSocket | 高效本地 + 通用云端 + 实时推送 |
| **本地数据库** | **SQLite** | 零配置, 个人版数据存储 |
| **云端数据库** | PostgreSQL (企业版云端) | 高性能, 多用户 |
| **向量数据库** | **LanceDB (本地) / Milvus (云端)** | 语义索引和类案检索 |
| **大模型路由** | LiteLLM 或自研网关 | 统一 API, 多模型切换, 故障转移 |
| **OCR** | PaddleOCR (本地) + 云端备份 | 离线优先, 复杂件上云 |
| **语音** | Whisper (本地转写) + 声纹识别 | 会议纪要场景, 隐私优先 |

### 7.2 当前 MVP 状态 (v0.7.0, 2026-06-28)

> **注**: 当前 MVP 已实现**核心工作流前端** (12 view, 24 JS 模块, 25 HTML 模板), 但**技术栈是过渡方案**:

| 维度 | 当前实现 | 长期规划 |
|---|---|---|
| 前端框架 | **Vanilla JS + Tailwind CSS** (IIFE 拆分 24 模块) | React 18 + TypeScript |
| 桌面形态 | **浏览器访问** (无 Electron 包装) | Electron 28+ 桌面应用 |
| 后端 | FastAPI (Python) + SQLite dev (100 判例 + 10 公司 + 6 控股边) | Rust (核心) + Python (AI) |
| AI | 待接入 Qwen2.5-72B (本地化) | Qwen2.5-72B + LiteLLM 路由 |
| 数据 | 4 公开源 + cncases 8500 万判例 (基础设施已建) | 全部向量化 + RAG |

**过渡策略**:
- Phase 4 完成核心功能 (auth / OCR / 律所访谈)
- Phase 5 启动 React 18 + TS 重构 (按模块渐进迁移, 不重写)
- Phase 6 Electron 打包 + Rust 核心

### 7.3 核心机制

- **上下文语义索引**: 材料段落向量化, AI 对话时检索最相关段落注入 Prompt, Token 预算 ≤8000
- **统一工具注册中心**: 所有功能和 Skill 实现统一 Tool 接口, AI 可动态发现和组合调用
- **自主办案循环**: 复杂任务 AI 生成计划步骤, 逐步执行观察, 关键决策点暂停确认, FSM 状态管理
- **法务级修订审批流**: 文书基于操作序列 (OT) 存储, 逐条接受 / 拒绝; 企业版审批链
- **深度记忆**: 三层记忆系统 (事实 / 风格 / 策略), 注入每次 Prompt
- **SOP 工作流引擎**: YAML 定义, 自动推进, 联动日程任务

### 7.4 核心模块 (24 个 JS, 25 HTML View)

**前端核心**:
- 核心: api.js, auth.js, app-state.js, router.js, bootstrap.js, script.js
- 业务: cases-list / detail / tabs, clients, schedule, knowledge, templates
- AI: ai.js, ai-doc.js
- 司法: judicial.js, judicial-data.js
- 工具: deadline.js, case-progress.js
- 账户: account-profile / subscription / notifications
- 视图: 25 个 (working / case-list / case-detail / client / schedule / archive / template / knowledge / ai / ai-doc / judicial / deadline / case-progress / login / workstation / subscription / orders / payment 等)

**设计系统**: 选中态统一深蓝 `bg-brand text-white` (#165DFF)

### 7.5 后端架构

- **框架**: FastAPI (Python 3.11+) + **未来** Rust (核心) + Python (AI 服务)
- **数据库**:
  - **PostgreSQL 16** (主存储, 案件 / 客户 / 日程)
  - **Elasticsearch 8.15** (全文检索, 法规 / 判例)
  - **Neo4j 5.25** (股权穿透 / 关系图)
  - **LanceDB / Milvus** (本地 / 云端向量)
- **AI**:
  - **Qwen2.5-72B** 本地化部署 (法律问答 / 文书生成)
  - **RAG 架构**: 法规 / 判例 / 客户档案 全部向量化
- **数据采集**:
  - 4 公开源: npc_laws + court_cases + zhixing + gsxt
  - cncases 8500 万判例 (BT 下载 + libtorrent)

### 7.6 API 路由 (FastAPI 当前实现)

```
GET  /api/cases                    案件列表 (含筛选)
GET  /api/cases/{doc_id}           案件详情
POST /api/cases/search             全文搜索
GET  /api/laws                     法规列表
GET  /api/laws/{law_id}            法规详情
GET  /api/companies                企业列表
GET  /api/companies/{unified_id}   企业详情
POST /api/cases/{doc_id}/favorite  收藏
POST /api/firm/lawyers             律师列表
POST /api/firm/time-entries        工时记录
GET  /api/health                   健康检查
```

### 7.7 数据原则

> **0 收费 API, 100% 自建数据**

| 数据 | 来源 | 规模 |
|---|---|---|
| 法规 | flk.npc.gov.cn (全国人大法律法规数据库) | 6000+ 部 |
| 判例 | 中国裁判文书网 + cncases 8500 万 | 8500 万 |
| 失信 | zxgk.court.gov.cn (中国执行信息公开网) | 千万级 |
| 企业 | gsxt.gov.cn (国家企业信用信息公示系统) | 5000 万+ |
| 司法观点 | 最高院指导案例 + 公报案例 | 数千 |

**为什么不接收费 API**:
- 成本: 元典智库 ¥5 万/年起, 中小所负担不起
- 数据受制于人, 商业模式不可持续
- 100% 自建, 数据所有权在自己手里, 长期价值大

---





---

**相关章节**:
- 主文档: `../../PRD.md`
- 导航: `./00-index.md`
- 路线: `./08-roadmap.md` · 商业: `./09-business-model.md` · 风险: `./11-risks-compliance.md`
- Track 任务: `./tracks/README.md`
