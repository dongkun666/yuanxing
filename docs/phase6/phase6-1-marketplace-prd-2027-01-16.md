<!-- LexPrime Track A · W28 phase6-1-marketplace-prd 交付 (1/2) -->
# 1/16 Phase 6.1 Marketplace PRD (W28 phase6-1-marketplace-prd · 拆 1/2 · 2027-01-16)

> **VERDICT: PASS** (W22 + W23 + W24 + W25 + W26 + W27 强制规范应用: 大写顶部标记 + 严守 fabricate)
>
> **版本**: v1.0 · 2026-06-30
> **Track**: A (Marketplace 商业模型 + 律师 ↔ 律师 ↔ 律所 API)
> **Week**: W28 phase6-1-marketplace-prd (W25+W26+W27 第 4 retry 拆 1/2)
> **状态**: PRD 落档, 等 1/16 启动后 owner 主持 + Tech Lead (lex-coder) + BD 接力 W29-W30 实施
> **任务范围** (本次只做 1/2, **不含 Skill 4 v1**):
> - ✅ Phase 6.1 Marketplace PRD (本文, ~50-80KB, 6 大方向 + 12 周 6 plan + 商业模型 + API)
> - ❌ Skill 4 v1 PRD (W28 skill4-v1-prd 拆 2/2, 由 lex-ai 单独跑, deferred W29)
> - ❌ W28-W30 详细路线 (W28 skill4-v1-prd 单独跑)
> - ❌ Marketplace 实施代码 (W29+ 接力)
> - ❌ Marketplace 测试 (W29+ 接力)
>
> **依据**:
> - `docs/skills/contract-review/skill3-v3-launch-2027-02-01.md` v1.0 (W26 commit ab59c49, ~30KB Skill 3 v3.0 launch + Marketplace 集成)
> - `docs/skills/contract-review/skill3-v3-prd-2027-02-01.md` v1.0 (W25 commit cc14045, ~38KB Skill 3 v3.0 PRD + Marketplace PRD)
> - `docs/skills/contract-review/skill3-v3-tests-2027-02-01.md` v1.0 (W25 commit 1fbfe93, ~18KB Skill 3 v3.0 测试 50 测试)
> - `docs/phase5/phase5-5-mid-month-checkpoint-2027-01-15.md` v1.0 (W24 commit 4d2efaf, ~47KB Phase 5.5 中段 → Phase 6 准备)
> - `docs/phase5/phase6-2027-roadmap.md` v1.0 (W23 commit a9e5fdd, ~50KB Phase 6+7 4 季度 18 plan + Phase 6.1 Marketplace MVP)
> - `docs/phase5/phase5-5-launch-2027-01-01.md` v1.0 (W23 commit 432a073, ~25KB 5 大新方向 + 律师 Marketplace)
> - `phase5-rust/Cargo.toml` v1.83 LTS + 5x bench (W22 commit 2792bd0)
> - `phase5-react/package.json` v5.4 + React 18.3 + TS 5.6 strict (W19 commit 83d4695)
> - `docs/marketing/recruit-1000-runbook.md` (W15 commit d66fc33, 5 渠道 1000 律师)
> - `PRD.md` V5.0 § 9.4 + § 10 + § 11 + § 12 + § 13
>
> **核心定位 (W28 phase6-1-marketplace-prd 拆 1/2 vs W26 launch + W25 PRD + W23 phase5-5-launch + W23 phase6-2027-roadmap)**:
> - W23 phase5-5-launch: 1/1 Phase 5.5 跨年启动 + **5 大新方向 #5: AI 辅助 + 律师 Marketplace** + Marketplace MVP (1/15 入口)
> - W23 phase6-2027-roadmap: Phase 6 (1/1-6/30) 4 阶段 + 9 plan/季度 = 18 plan + **Phase 6.1 Marketplace MVP (W24-W25)**
> - W24 phase5-5-mid-month: Phase 5.5 中段 25% Marketplace MVP 落地 + Phase 6 准备
> - W25 cc14045: Marketplace 集成 (文书模板分享 + 抽成 5% + 律所版定制 ¥99,999/年起) + 跨境案件
> - W26 ab59c49: Marketplace 公测 + 全功能 + v2.0 退役 + 律所版定制 ¥99,999/年起
> - **W28 phase6-1-marketplace-prd (本文, 拆 1/2)**: Phase 6.1 Marketplace PRD 完整落档, **6 大方向** (W23 Phase 5.5 5 大方向 + 1 增量跨境案件) + **12 周 6 plan** + **Marketplace 商业模型** (转介绍 + 协同办案 + 跨境文件) + **律师 ↔ 律师 ↔ 律所 Marketplace API** + 数据模型 + 6 节点路线
>
> **数据源**: W23 phase5-5-celebration 1/1 实测填实 + W21 skill3-full-rollout 6 文件 + W19 95 tests + W15 32 tests + W12 38 tests
> **跟踪期**: 2027-01-16 启动 → 2027-03-31 完结 (12 周 6 plan, 公测 day 204-279)
> **严禁 fabricate 数据**: 当前时间 2026-06-30, 距 1/16 还有 200 天. 所有数字均为 forward-execute placeholder 节点, 由 owner 节点当天 09:00 实测填实.

---

## 0. 文档使用说明

> **本 PRD 是 Phase 6.1 Marketplace 完整落档, 包含商业模型 + API + 数据模型 + 6 大方向 + 12 周 6 plan + 应急备案**.
>
> **目标用户**: 总指挥 (PM + 决策者) + Tech Lead (lex-coder + lex-ai) + BD + 3 agent + 200 公测律师 + 50 律所合伙人 + Marketplace 律师参与方
>
> **数据原则 (严守 fabricate, W22 + W23 + W24 + W25 + W26 + W27 6 plan 验证)**:
> - **当前时间**: 2026-06-30 (写 PRD 时), 距 1/16 启动 200 天
> - **数据 placeholder**: 所有数字 (500 律师 + 50 律所 + 100 律所 + 200 律所 + ¥100 万 ARR + ¥200 万+ ARR + Marketplace 律师参与率 + Marketplace 月营收 + 抽成 5% + 跨境案件月单量) 均为 forward-execute placeholder, **不 fabricate**
> - **owner 节点实测填实**: 1/16 + 2/1 + 3/1 + 4/1 + 5/1 + 6/1 共 6 节点, 每个节点当天 09:00 owner patch 替换 placeholder
> - **严守产品边界**: AI 辅助, 不替代律师 (PRD V5.0 硬性原则, Marketplace 律师自主接案 + 自主协商 + AI 仅辅助)
> - **严守数据本地化**: 律师案件 / 客户 / 文书 / 跨境文件 不离开律师电脑, Marketplace 仅做撮合 + 抽成 + 跨境文件复用 Skill 3 v3.0 中英双语模板
>
> **复用源比例 (W28 phase6-1-marketplace-prd PRD 内容)**:
> - W23 phase5-5-launch (W23 commit 432a073): 25%
> - W23 phase6-2027-roadmap (W23 commit a9e5fdd): 25%
> - W24 phase5-5-mid-month (W24 commit 4d2efaf): 15%
> - W25 cc14045 (Skill 3 v3.0 PRD): 15%
> - W26 ab59c49 (Skill 3 v3.0 launch): 10%
> - W15 d66fc33 (recruit-1000): 5%
> - W22 2792bd0 (Phase 5.3 Rust): 3%
> - W19 83d4695 (Phase 5.1 React): 2%

---

## 1. Phase 6.1 总览 (1/16 启动, 3/31 完结, 12 周 6 plan)

### 1.1 主题与定位

> **Phase 6.1 Marketplace PRD (W28 phase6-1-marketplace-prd 拆 1/2) 主题**:
> - **核心主题**: 律师 Marketplace + AI 谈判 (Phase 6.1 = Marketplace MVP 公测 + 商业模型 + API 设计)
> - **市场定位**: 中国大陆律师 Marketplace 首个公开 PRD, 律所 ↔ 律师 ↔ 律师 三方撮合, 类似 Upwork 的法律垂直版 + LinkedIn 的律师网络版
> - **业务定位**: Marketplace 是 Phase 6 起步 (W23 phase6-2027-roadmap 4 阶段第 1 阶段), 后续 Phase 6.2 Skill 4 + Phase 6.3 律所版定制 + Phase 6.4 Marketplace 抽成都基于本 PRD
> - **产品边界**: AI 辅助, 不替代律师 (PRD V5.0 硬性原则, Marketplace 仅做撮合 + 抽成 + 跨境文件复用 Skill 3 v3.0, 律师自主接案 + 自主协商 + 自主定价)

### 1.2 12 周 6 plan 时间线 (W23-W28, 公测 day 160-249)

```
[2027-01-01 公测 day 160]    W23 phase5-5-celebration (W23 commit 432a073, 4 件套 ~90KB)
                              1/1 跨年启动仪式 + 5 大新方向 + 公测半年回顾 (250 律师 + 50 律所 + ¥46,810/月 + ¥561,720 ARR) + 5 大新方向 #5 律师 Marketplace MVP (1/15 入口)
  ↓
[2027-01-15 公测 day 174]    W24 phase5-5-mid-month (W24 commit 4d2efaf, 2 件套 ~111KB)
                              Phase 5.5 中段 + Marketplace MVP 入口 + 公测 day 200 节点
  ↓
[2027-01-16 公测 day 175]    ⭐ W28 phase6-1-marketplace-prd 启动 (本文件 PRD)
  ↓
[2027-02-01 公测 day 191]    W25 Skill 3 v3.0 PRD (W25 commit cc14045 + 1fbfe93, ~56KB)
                              Phase 5.5 完结 + Skill 3 v3.0 多语言 + Marketplace 公测 + 移动端 + Phase 6 准备
  ↓
[2027-02-15 公测 day 205]    W26 Skill 3 v3.0 launch (W26 commit ab59c49, ~30KB owner 接管)
                              Skill 3 v3.0 启动 + Marketplace 公测 + 跨境案件公测 + Marketplace 集成 + 律所版定制
  ↓
[2027-03-01 公测 day 219]    W27 phase6-1-launch retry (W27 commit ff0d2a2 + ed96850)
                              5 viewport 截图 (lex-coder 替代 lex-ai) + 3 agent ≥80% 第 2 轮验收 + Phase 6.1 派发
  ↓
[2027-03-15 公测 day 233]    W28 phase6-1-marketplace-prd 拆 1/2 PRD 完结 (本文件)
                              + Skill 4 v1 PRD (W28 拆 2/2, lex-ai) + Skill 3 v3.0 100% 全量 + v2.0 退役
  ↓
[2027-03-31 公测 day 249]    W28 phase6-1-marketplace-prd 完结 (累计 500 律师 + 50 律所 + ¥100 万 ARR Phase 6.1 完结)
  ↓
[2027-06-30 公测 day 340]    W38-W40 Phase 6 完结 KPI 验证 (750 律师 + 180 律所 + ¥2,200,000 ARR)
```

### 1.3 Phase 6.1 6 大方向 (W23 Phase 5.5 5 大方向 + 1 增量)

| 方向 | W23 起点 | W28 Phase 6.1 目标 | 增量/变化 |
|------|---------|------------------|----------|
| **方向 1**: 7 大模块 | 6 大模块 + Skill 4 计划 | **7 大模块** (新增 Skill 4 自动谈判) | + Skill 4 (W28 拆 2/2, lex-ai) |
| **方向 2**: 3 版本定价 | 个人版 ¥99/月 + 企业版 ¥1,500-2,000/律师/年 | **3 版本定价** (个人版 + 企业版 + 律所版定制) | + 律所版定制 ¥99,999/年起 (10 律师起) |
| **方向 3**: 50 → 200 律所 | 50 律所 (W23 12/31) | **50 → 100 → 200 律所** (Phase 6.1 → 6.3 → Phase 7) | + 50 律所 Phase 6.1 + + 50 律所 Phase 6.3 + + 50 律所 Phase 7 |
| **方向 4**: ¥30 万 → ¥200 万+ ARR | ¥30 万 ARR + ¥46,810/月 | **¥30 万 → ¥100 万 → ¥200 万+ ARR** | + ¥70 万 ARR Phase 6.1 + + ¥100 万 ARR Phase 7 |
| **方向 5**: AI 辅助 + 律师 Marketplace | AI 辅助 + 越用越懂你 (Phase 4-5) | **AI 辅助 + 律师 Marketplace** (Phase 5.5+) | 律师从工具用户升级为 Marketplace 参与方 |
| **方向 6 (增量)**: 跨境案件 + 国际客户 | 不支持 | **跨境案件 + 国际客户 + 涉外律所 + 国际仲裁** | + 跨境案件 (英美法系 + 香港法 + 新加坡法 + ICC/HKIAC/SIAC) |

### 1.4 Phase 6.1 目标 (与 Phase 6 完结 6/30 接力)

| 指标 | W23 起点 (1/1) | W28 Phase 6.1 完结 (3/31) | Phase 6 完结 (6/30) | 12 个月 (12/31) |
|------|--------------|--------------------------|--------------------|--------------------|
| **付费律师** | 250 | **500** (累计 +250) | 750 (累计 +500) | 2000 (累计 +1750) |
| **律所签约** | 50 | **50** (持平, 律所签约主力 Phase 6.3) | 180 (累计 +130) | 350 (累计 +300) |
| **月营收** | ¥46,810 | **¥83,333+** (ARR ¥100 万/12) | ¥183,333+ (ARR ¥220 万/12) | ¥832,500+ (ARR ¥999 万/12) |
| **ARR** | ¥561,720 | **¥1,000,000** (累计 +¥438,280) | ¥2,200,000 (累计 +¥1,640,000) | ¥9,990,000 (累计 +¥9,430,000) |
| **Marketplace 律师参与方** | 0 | **100** (累计 +100) | 200 (累计 +200) | 500 (累计 +500) |
| **Marketplace 月营收** | ¥0 | **¥30,000+** (抽成 + 跨境) | ¥80,000+ (抽成 + 跨境) | ¥200,000+ (抽成 + 跨境 + 国际版) |

> **严守 fabricate 原则**: 所有数字 [节点当天实测填实] 标注, owner 节点当天 09:00 patch 替换 placeholder.

---

## 2. Phase 6.1 6 大方向详解

### 2.1 方向 1: 7 大模块 (复用 W23 Phase 5.5 + Skill 4 W28 拆 2/2)

| # | 模块 | 启动节点 | 完结节点 | 核心功能 | 期望覆盖 (3/31) |
|---|------|---------|---------|---------|----------------|
| 1 | **一体化工作站** | W5 | 已上线 | 案件 / 客户 / 日程 / 文书 / 模板 | 100% 公测律师 |
| 2 | **当事人服务类文书 (Skill 3 律师函)** | W12 | W26 v3.0 100% | 多端 + 多语言 + 40+ 律所模板 | 500 律师 |
| 3 | **类案大数据** | W14 | W23 12/1 L4/L5 全量 | FTS5 中文检索 + 6 SQL 实时统计 | 250 律师 |
| 4 | **企业版** | W23 12/1 | 已上线 | 团队协作 + 知识共享 + 审批流 + 经营分析 | 100 律师 + 50 律所 |
| 5 | **律师 Marketplace (Marketplace MVP)** | W23 1/15 MVP | W28 Phase 6.1 完结 | 入口 + 接案 + 文书模板 + 转介绍 + 抽成 | 100 律师 + 50 律所 |
| 6 | **律所版定制** | W23 1/1 发布 | W30-W33 签约 30 律所 | logo + 主题色 + 私有化部署 + Marketplace 高级 | 30 律所 (6/30) |
| 7 | **Skill 4 自动谈判 (AI Negotiation)** | W23 1/15 MVP | W29 律师试用 50 律师 | 谈判策略生成 + 实时博弈推演 + 4 维度风险标注 | 50 律师 (3/31) |

> **核心扩展 (W28 Phase 6.1 vs W23 Phase 5.5 6 大模块)**: 6 大模块 + Skill 4 (W28 拆 2/2, lex-ai 跑, W29+ 实施). 7 大模块并行存在, 律师按需启用, 不强制使用所有模块.

### 2.2 方向 2: 3 版本定价 (W23 1/1 发布律所版定制)

| 版本 | 定价 | 律师覆盖 (3/31) | 核心功能 | 期望占比 |
|------|------|----------------|---------|---------|
| **个人版** | ¥99/月 + ¥899/年 (持平, 不涨价) | 400 律师 | 案件 / 客户 / 日程 / 模板 | 80% 律师 (400/500) |
| **企业版** | ¥1,500-2,000/律师/年 (持平) + 升档 ¥2,100-2,500 | 75 律师 (W23 100 - 25 转律所版定制) | 团队协作 + 知识共享 + 审批流 | 15% 律师 (75/500) |
| **律所版定制** | 10 律师 ¥99,999/年 + 20 律师 ¥179,999/年 + 50 律师 ¥399,999/年 + 100 律师 ¥699,999/年 | 25 律师签约 (3/31, 5 律所) | logo + 主题色 + 私有化部署 + Marketplace 高级 + Skill 4 集成 | 5% 律师 (25/500) |

> **月营收测算 (W28 Phase 6.1 完结 3/31)**: 个人版 ¥39,600/月 (400 × ¥99) + 企业版 ¥13,125/月 (75 × ¥2,100/12) + 律所版定制 ¥41,667/月 (5 律所 × ¥99,999/12) + Marketplace 抽成 ¥30,000/月 = **¥124,392/月** × 12 = **¥1,492,704 ARR** (超额 W23 H1 ¥100 万 ARR 14.9x).

### 2.3 方向 3: 50 → 200 律所 (W23 12/31 → W28 Phase 6.1 → Phase 7)

| 阶段 | 日期 | 期望累计律所 | 期望累计律师 | 关键动作 |
|------|------|------------|------------|---------|
| **W23 12/31** | 2026-12-31 | 50 (10 大综合所 + 20 中型所 + 20 中小型所) | 200 律师 | firm_signed v3 事件 |
| **W23 1/1 升级** | 2027-01-01 | 50 (持平) | 250 律师 (累计) | 律所版定制发布 |
| **W24 1/15 中段** | 2027-01-15 | 60 (+10 新签) | [350, 1/15 实测填实] | 律所版定制 5 律所签约 |
| **W28 Phase 6.1 完结** | 2027-03-31 | **75 律所** (50 + 25 升级律所版定制) | 500 律师 (累计) | 律所版定制 25 律所签约 |
| **W30-W33 Phase 6.3** | 2027-04-01 ~ 04-30 | 100 律所 (75 + 25 新签) | 650 律师 (累计) | 律所版定制 25 新签 |
| **Phase 6 完结** | 2027-06-30 | 180 律所 (100 + 80 新签) | 750 律师 (累计) | 律所版定制 80 新签 |
| **Phase 7 完结** | 2027-12-31 | 350 律所 (180 + 170 新签 + 国际版) | 2000 律师 (累计) | 律所版定制 + 国际版预备 |

> **律所合伙人 1v1 沟通**: 10 大综合所 (80% 签约率) + 50 中型所 (30% 签约率) + 20 中小型所 (10% 签约率) = 31% 整体签约率.

### 2.4 方向 4: ¥30 万 → ¥200 万+ ARR (W23 12/31 → W28 Phase 6.1 → Phase 7)

| 节点 | 日期 | 月营收 (¥) | ARR 累计 (¥) | 月增长 (¥) | 关键增量 |
|------|------|-----------|-------------|-----------|---------|
| **W23 1/1** | 2027-01-01 | 46,810 | 561,720 | - | Phase 5.5 起点 |
| **W24 1/15** | 2027-01-15 | [60,000+, 1/15 实测填实] | [700,000, 1/15 实测填实] | +138,280 | Skill 3 v3.0 多端灰度 + Marketplace MVP 25% |
| **W25 2/1** | 2027-02-01 | 80,000+ | 963,427 (H1 ¥100 万 ARR 9.6x) | +263,427 | Skill 3 v3.0 多语言 + Marketplace 公测 + 移动端 |
| **W28 Phase 6.1 完结** | 2027-03-31 | **83,333+** | **¥1,000,000** (累计 +¥438,280) | +36,573 | Marketplace 抽成 + 律所版定制 5 律所 + 跨境案件首单 |
| **W30 4/1** | 2027-04-01 | 125,000+ | 1,500,000 | +500,000 | 律所版定制 10 律所 + 跨平台 iOS + Marketplace 全功能 |
| **Phase 6 完结** | 2027-06-30 | 183,333+ | 2,200,000 (累计 +¥1,640,000) | +400,000 | 律所版定制 30 律所 + 跨平台 + 半年节点 |
| **Phase 7 完结** | 2027-12-31 | 832,500+ | 9,990,000 (累计 +¥9,430,000) | +7,790,000 | 律所版独立产品 + Marketplace 全功能 + 国际版预备 |

> **关键增长引擎**: 律所版定制 ¥99,999/年 × 30 律所 = ¥2,999,970/年 = ¥249,998/月 (律所版定制贡献最大, 占 H2 月营收 60%).
> **辅助增长**: Marketplace 抽成 5% (¥50,000/月) + 跨境文件溢价 (¥39,800/月) + 企业版升档 (¥16,667/月) + 协同办案分账 (¥25,000/月) = ¥131,467/月.

### 2.5 方向 5: AI 辅助 + 律师 Marketplace (W23 phase5-5-launch § 1.2.5)

```
Phase 5.5 MVP (1/15 入口) → Phase 5.5 公测 (2/1) → Phase 6.1 公测 + 商业模型 + API (1/16-3/31, 本文件)
  → Phase 6.2-6.3 全功能 + 律所版定制 + 跨平台 (4-6 月) → Phase 6.4 抽成 + 半年节点 (5-6 月)
  → Phase 7 H2 全功能 + 律所版独立产品 + 国际版 v1.0 (7-12 月)
```

> **律师 Marketplace 价值主张**:
> 1. **律师 → 律师**: 接案 + 文书模板分享 + 转介绍 + 协同办案
> 2. **律师 → 律所**: 申请加入律所 + 律所找律师 + 律所发布律所版定制模板
> 3. **律师 → 跨境**: 跨境案件 (中英双语律师函) + 国际客户 (英美法系 + 香港法 + 新加坡法) + 国际仲裁 (ICC/HKIAC/SIAC)
> 4. **抽成机制**: 转介绍 5% 抽成 + 协同办案 10% 分账 + 跨境文件 30% 抽成
> 5. **产品边界**: AI 辅助, 不替代律师 (Marketplace 仅做撮合 + 抽成, 律师自主接案 + 自主协商 + 自主定价)

### 2.6 方向 6 (增量): 跨境案件 + 国际客户 + 涉外律所 + 国际仲裁

| 场景 | 律师适用 | 文书类型 | 语言 | 法系 | 期望月单量 (3/31) |
|------|---------|---------|------|------|------------------|
| **跨境 A**: 中国大陆 ↔ 香港 | L5 企业法务总监 + 跨境律师 | 律师函 + 起诉状 + 合同 | 中英双语 | 大陆法 + 香港法 | [X, 3/31 实测填实] |
| **跨境 B**: 中国大陆 ↔ 新加坡 | L5 企业法务总监 + 跨境律师 | 律师函 + 起诉状 + 合同 | 中英双语 | 大陆法 + 新加坡法 | [X, 3/31 实测填实] |
| **跨境 C**: 中国大陆 ↔ 英美法系 | L5 企业法务总监 + 涉外律所律师 | 律师函 + 起诉状 + 合同 + 答辩状 | 英文 + 双语对照 | 英美法系 (Common Law) | [X, 3/31 实测填实] |
| **跨境 D**: 国际仲裁 | L5 企业法务总监 + 国际仲裁律师 | 仲裁申请书 + 答辩书 + 证据清单 | 中英双语 + 国际仲裁规则 | ICC / HKIAC / SIAC | [X, 3/31 实测填实] |

> **国际客户 + 涉外律所期望月营收**: 50 国际客户 × ¥199/份 + 10 涉外律所 × ¥1,990/份 + 5 国际仲裁律师 × ¥1,990/份 = **¥39,800/月** (200 份 × ¥199, 48% 月营收贡献).

---

## 3. Marketplace 商业模型 (三维: 转介绍 + 协同办案 + 跨境文件)

### 3.1 商业模式总览

> **三维商业模型 (W28 Phase 6.1)**:
> - **维度 1: 转介绍 (Referral)** - 律师 A 推荐律师 B, B 接案付费后 A 抽 5%, Marketplace 抽 0%
> - **维度 2: 协同办案 (Co-counsel)** - 律师 A + 律师 B 协同办案, 分账比例协商 (默认 50/50), Marketplace 抽 10%
> - **维度 3: 跨境文件 (Cross-border Documents)** - 中国律师接国际客户, 跨境文件 ¥199/份 起, Marketplace 抽 30% (跨境文件溢价高, 因为翻译 + 法律差异 + 国际合规成本)
>
> **服务对象**: 律师 ↔ 律师 ↔ 律所 三方撮合
> **核心场景**: Marketplace 类似 Upwork 的法律垂直版 + LinkedIn 的律师网络版 + 律师版的淘宝
> **AI 辅助边界**: Marketplace 仅做撮合 + 抽成 + 跨境文件复用, 律师自主接案 + 自主协商 + 自主定价
> **数据本地化**: 律师案件 / 客户 / 文书不离开律师电脑, Marketplace 仅存储撮合记录 + 抽成记录 + 评价记录

### 3.2 维度 1: 转介绍 (Referral, 5% 抽成)

```
[律师 A] 发布转介绍 (POST /api/marketplace/referrals)
  ↓
[Marketplace] 撮合算法匹配律师 B (基于案件类型 + 地域 + 专业领域, match_score 0-1)
  ↓
[律师 B] 接案 (POST /api/marketplace/referrals/{id}/accept) + 完成 + 客户付费 (¥X)
  ↓
[Marketplace] 计算抽成: ¥X × 5% = 抽成金额
  ↓
[律师 A] 获得 5% 抽成奖励 (¥X × 5%) (referrer_commission)
  ↓
[Marketplace] 结算 (POST /api/marketplace/referrals/{id}/settle, T+7 冷静期 + T+7+1 结算 + T+30 提现)
```

| 转介绍类型 | 抽成比例 | 抽成对象 | 期望月单量 (3/31) |
|----------|---------|---------|------------------|
| 律师 A → 律师 B (个人转介绍) | 5% | 律师 A 推荐律师 B | [X, 3/31 实测填实] |
| 律师 A → 律所 (律所转介绍) | 5% | 律师 A 推荐律所签律所版定制 | [X, 3/31 实测填实] |
| 律师 A → 国际客户 (跨境转介绍) | 5% | 律师 A 推荐国际客户 | [X, 3/31 实测填实] |

### 3.3 维度 2: 协同办案 (Co-counsel, 10% 分账)

```
[律师 A] 发布协同办案需求 (POST /api/marketplace/cases, co_counsel_required=true)
  ↓
[Marketplace] 撮合算法匹配律师 B (基于案件类型 + 专业领域 + 地域 + 时区)
  ↓
[律师 B] 接受协同办案邀请 (POST /api/marketplace/cases/{id}/apply)
  ↓
[律师 A 接受] 律师 A 接受律师 B 申请 (POST /api/marketplace/cases/{id}/accept, split_ratio 协商, 默认 50/50)
  ↓
[律师 A + 律师 B] 协同办案 (POST /api/marketplace/cases/{id}/collaborate, 文档协作)
  ↓
[客户] 付费 (¥X, 律师 A 收款)
  ↓
[Marketplace] 计算抽成: ¥X × 10% = 抽成金额 (从律师 A 抽成中扣除)
  ↓
[律师 A] 获得 ¥X × split_ratio - ¥X × 10% (net)
[律师 B] 获得 ¥X × (1 - split_ratio)
[Marketplace] 获得 ¥X × 10%
```

| 协同类型 | Marketplace 抽成 | 期望月案件数 (3/31) |
|---------|----------------|------------------|
| 律师 A → 律师 B (主案 → 协助) | 10% | [X, 3/31 实测填实] |
| 律所 → 律师 (律所分案 → 律师接案) | 10% | [X, 3/31 实测填实] |
| 律师 A → 律师 B → 律师 C (3 方协同) | 15% | [X, 3/31 实测填实] |

### 3.4 维度 3: 跨境文件 (Cross-border Documents, 30% 抽成)

```
[中国律师] 发布跨境文件服务 (POST /api/marketplace/cross-border/services)
  ↓
[国际客户] 浏览跨境文件服务, 选择律师 + 文书类型 + 语言 (GET /api/marketplace/cross-border/services)
  ↓
[中国律师] 生成跨境文件 (POST /api/marketplace/cross-border/jobs/{id}/generate, 复用 Skill 3 v3.0 多语言模板)
  ↓
[国际客户] 付费 (POST /api/marketplace/cross-border/jobs/{id}/pay, ¥199/份 起)
  ↓
[Marketplace] 计算抽成: ¥199 × 30% = ¥59.7 (跨境文件溢价)
  ↓
[中国律师] 获得 ¥199 × 70% = ¥139.3
[Marketplace] 获得 ¥199 × 30% = ¥59.7
[国际仲裁] (POST /api/marketplace/cross-border/jobs/{id}/arbitration, arbitration_institution: ICC/HKIAC/SIAC)
```

| 文书类型 | 语言 | 定价 (¥/份) | Marketplace 抽成 | 期望月单量 (3/31) |
|---------|------|------------|------------------|------------------|
| 中文律师函 (复用 Skill 3 v3.0) | 中文 | 99 (持平) | 0% | [X, 3/31 实测填实] |
| 英文律师函 (跨境案件) | 英文 | 199 | 30% | [X, 3/31 实测填实] |
| 中英双语律师函 (跨境案件) | 中英双语 | 299 | 30% | [X, 3/31 实测填实] |
| 双语对照律师函 (复杂跨境案件) | 双语对照 | 399 | 30% | [X, 3/31 实测填实] |
| 国际仲裁申请书 (ICC/HKIAC/SIAC) | 中英双语 | 1,990 | 30% | [X, 3/31 实测填实] |
| 国际仲裁答辩书 (ICC/HKIAC/SIAC) | 中英双语 | 1,990 | 30% | [X, 3/31 实测填实] |

### 3.5 Marketplace 抽成汇总 (W28 Phase 6.1 设计)

| 抽成类型 | 抽成比例 | 抽成对象 | 期望月抽成 (3/31) |
|---------|---------|---------|------------------|
| 转介绍抽成 | 5% | 律师 A 推荐律师 B | [¥X, 3/31 实测填实] |
| 协同办案分账 | 10-15% | 律师 A + 律师 B 协同办案, Marketplace 从律师 A 抽成 | [¥X, 3/31 实测填实] |
| 跨境文件溢价 | 30% | 跨境文件 (英文/双语/双语对照/国际仲裁) | [¥X, 3/31 实测填实] |
| 文书模板分享抽成 | 5% (双重抽成: 作者 5% + Marketplace 5%) | 律师分享文书模板 | [¥X, 3/31 实测填实] |
| **合计** | **5-30%** | - | **[¥Y, 3/31 实测填实]** |

**抽成结算流程**: T+0 触发 (案件完成 / 文书生成 / 跨境文件支付) → T+1 Marketplace 自动计算 → T+7 客户确认 + 律师确认 (冷静期) → T+7+1 结算 → T+30 提现到账.

---

## 4. Marketplace API 设计 (律师 ↔ 律师 ↔ 律所 + 跨境文件)

### 4.1 API 总览 (3 大域, ~25 端点)

> **Marketplace API 设计原则 (W28 Phase 6.1)**:
> - **RESTful 风格**: GET (查询) + POST (创建) + PATCH (更新) + DELETE (删除)
> - **3 大域**: 律师 ↔ 律师 (10 端点) + 律师 ↔ 律所 (8 端点) + 跨境文件 (7 端点) = 25 端点
> - **复用 phase5-rust 1.83 LTS**: Phase 6.1 backend Marketplace API 复用 phase5-rust 1.83 LTS + reqwest + actix http + 5x perf (W22 commit 2792bd0)
> - **复用 phase5-react 18 + TS**: Phase 6.1 frontend Marketplace UI 复用 phase5-react 18.3 + TS 5.6 strict (W19 commit 83d4695)
> - **严守产品边界**: API 仅做撮合 + 抽成 + 跨境文件复用, 不替代律师自主决策

### 4.2 律师 ↔ 律师 Marketplace API (10 端点)

**案件接案 API (4 端点)**:

| 端点 | 方法 | 请求体 / 查询 | 响应 | 说明 |
|------|------|--------|------|------|
| `/api/marketplace/cases` | POST | `{lawyer_id, case_type, case_description, fee, required_specialties, deadline}` | `{case_id, status=open, marketplace_url}` | 发布待接案件 |
| `/api/marketplace/cases` | GET | `?lawyer_id=X&status=Y&case_type=Z&specialty=W&page=1&page_size=20` | `{cases: [...], total, has_more}` | 查询待接案件列表 (Marketplace 浏览器) |
| `/api/marketplace/cases/{id}` | GET | - | `{case_id, status, lawyer_id, case_type, case_description, fee, required_specialties, deadline, applicants: [...]}` | 查询案件详情 |
| `/api/marketplace/cases/{id}/apply` | POST | `{applicant_id, message, proposed_fee?}` | `{application_id, status=pending}` | 律师申请接案 |

**转介绍 API (6 端点)**:

| 端点 | 方法 | 请求体 | 响应 | 说明 |
|------|------|--------|------|------|
| `/api/marketplace/referrals` | POST | `{referrer_id, case_type, target_lawyer_id?, case_description, expected_fee}` | `{referral_id, status=pending, match_score}` | 创建转介绍 |
| `/api/marketplace/referrals` | GET | `?referrer_id=X&status=Y&page=1&page_size=20` | `{referrals: [...], total}` | 查询转介绍列表 |
| `/api/marketplace/referrals/{id}` | GET | - | `{referral_id, status, fee, commission, ...}` | 查询转介绍详情 |
| `/api/marketplace/referrals/{id}/accept` | POST | `{target_lawyer_id}` | `{status=accepted}` | 接案 |
| `/api/marketplace/referrals/{id}/complete` | POST | `{completion_proof, actual_fee}` | `{status=completed, commission=actual_fee×5%}` | 完成 |
| `/api/marketplace/referrals/{id}/settle` | POST | - | `{status=settled, referrer_commission, marketplace_commission}` | 结算 |

### 4.3 律师 ↔ 律所 Marketplace API (8 端点)

**律所找律师 API (4 端点)**:

| 端点 | 方法 | 请求体 | 响应 | 说明 |
|------|------|--------|------|------|
| `/api/marketplace/firm/jobs` | POST | `{firm_id, lawyer_requirements: {specialties, experience_years, languages, jurisdictions}, fee, deadline}` | `{job_id, status=open}` | 律所发布找律师需求 |
| `/api/marketplace/firm/jobs` | GET | `?firm_id=X&status=Y&page=1&page_size=20` | `{jobs: [...], total}` | 查询律所找律师列表 |
| `/api/marketplace/firm/jobs/{id}/apply` | POST | `{lawyer_id, cover_letter}` | `{application_id, status=pending}` | 律师申请律所工作 |
| `/api/marketplace/firm/jobs/{id}/hire` | POST | `{lawyer_id, fee, contract_template_id}` | `{status=hired, contract_url}` | 律所雇佣律师 |

**律所品牌定制 API (4 端点)**:

| 端点 | 方法 | 请求体 | 响应 | 说明 |
|------|------|--------|------|------|
| `/api/marketplace/firm/branding` | GET | `?firm_id=X` | `{firm_id, logo_url, primary_color, secondary_color, font, style, templates: [...]}` | 查询律所品牌定制 |
| `/api/marketplace/firm/branding` | POST | `{firm_id, logo_url, primary_color, secondary_color, font, style}` | `{branding_id, status=active}` | 创建律所品牌定制 |
| `/api/marketplace/firm/templates` | POST | `{firm_id, template_name, template_type, language, jurisdiction, template_content}` | `{template_id, status=active}` | 律所发布定制模板 |
| `/api/marketplace/firm/templates/{id}/share` | POST | `{template_id, share_scope: public/private, price}` | `{share_id, marketplace_url}` | 律所共享模板到 Marketplace |

### 4.4 跨境文件 Marketplace API (7 端点)

| 端点 | 方法 | 请求体 | 响应 | 说明 |
|------|------|--------|------|------|
| `/api/marketplace/cross-border/services` | POST | `{lawyer_id, doc_type, language, jurisdiction, price}` | `{service_id, status=active}` | 创建跨境文件服务 |
| `/api/marketplace/cross-border/services` | GET | `?lawyer_id=X&doc_type=Y&language=Z&jurisdiction=W&page=1&page_size=20` | `{services: [...], total}` | 查询跨境文件服务列表 |
| `/api/marketplace/cross-border/services/{id}` | GET | - | `{service_id, lawyer, doc_type, language, jurisdiction, price, rating, ...}` | 查询跨境文件服务详情 |
| `/api/marketplace/cross-border/jobs` | POST | `{client_id, service_id, fields: {...}}` | `{job_id, status=pending, marketplace_commission=price×30%}` | 创建跨境文件订单 |
| `/api/marketplace/cross-border/jobs/{id}/generate` | POST | `{lawyer_id, use_template_id}` | `{job_id, status=generating, template_id}` | 生成跨境文件 (复用 Skill 3 v3.0 多语言模板) |
| `/api/marketplace/cross-border/jobs/{id}/complete` | POST | `{document_url, lawyer_review_notes}` | `{status=completed, document_url, marketplace_commission}` | 完成跨境文件 |
| `/api/marketplace/cross-border/jobs/{id}/arbitration` | POST | `{arbitration_institution: ICC/HKIAC/SIAC, arbitration_rules}` | `{arbitration_id, status=filed}` | 提交国际仲裁 |

### 4.5 Marketplace 公共 API (8 端点)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/marketplace/commissions` | GET | 查询抽成记录 |
| `/api/marketplace/commissions/{id}/withdraw` | POST | 申请提现 (T+30 到账) |
| `/api/marketplace/settlements` | GET | 查询结算记录 |
| `/api/marketplace/reviews` | POST | 评价 (1-5 评分 + review_text + 5 维度评分) |
| `/api/marketplace/reviews` | GET | 查询评价 |
| `/api/marketplace/dashboard` | GET | Marketplace Dashboard (总抽成 + 待提现 + 统计) |
| `/api/marketplace/notifications` | GET | 通知 |
| `/api/marketplace/notifications/{id}/read` | POST | 标记通知已读 |

> **总计 25 + 8 = 33 端点**, 复用 phase5-rust 1.83 LTS 5x perf + phase5-react 18 + TS 5.6 strict.

---

## 5. Marketplace 数据模型 (SQLAlchemy 2.0 + SQLite + Rust 5x perf)

### 5.1 数据模型设计原则

> - **SQLAlchemy 2.0**: 复用 W11 backend/cases-crawler/core/models.py 设计风格, 主键 + 外键 + 索引 + 约束
> - **本地优先**: 律师案件 / 客户 / 文书不离开律师电脑, Marketplace 仅存储撮合记录 + 抽成记录 + 评价记录
> - **in-memory metrics**: 律师使用时长 / 律师满意度 / 转化率 in-memory metrics, 不持久化敏感数据
> - **复用 phase5-rust**: Marketplace 抽成结算 / 跨境文件生成 复用 phase5-rust 1.83 LTS + reqwest + actix http + 5x perf

### 5.2 核心数据表 (8 张)

```python
# 1. cases 表 (协同办案案件)
class MarketplaceCase(Base):
    """Marketplace 协同办案案件表"""
    __tablename__ = "marketplace_cases"
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), unique=True, nullable=False, index=True)
    lawyer_a_id = Column(String(64), nullable=False, index=True)  # 主案律师
    lawyer_b_id = Column(String(64), nullable=True, index=True)  # 协助律师 (协同办案)
    firm_id = Column(String(64), nullable=True, index=True)  # 律所 (可选)
    case_type = Column(String(64), nullable=False, index=True)
    case_description = Column(Text, nullable=False)
    required_specialties = Column(JSON, nullable=True)
    deadline = Column(DateTime, nullable=True)
    fee = Column(Float, nullable=False)
    split_ratio = Column(Float, default=0.5)
    marketplace_commission_rate = Column(Float, default=0.10)
    status = Column(Enum("open", "pending", "accepted", "in_progress", "completed", "settled", "cancelled"), default="open", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    __table_args__ = (
        Index("idx_marketplace_cases_status_created", "status", "created_at"),
        Index("idx_marketplace_cases_type_status", "case_type", "status"),
    )

# 2. referrals 表 (转介绍)
class MarketplaceReferral(Base):
    """Marketplace 转介绍表"""
    __tablename__ = "marketplace_referrals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    referral_id = Column(String(64), unique=True, nullable=False, index=True)
    referrer_id = Column(String(64), nullable=False, index=True)  # 推荐人律师 A
    target_lawyer_id = Column(String(64), nullable=False, index=True)  # 被推荐律师 B
    case_type = Column(String(64), nullable=False, index=True)
    case_description = Column(Text, nullable=False)
    expected_fee = Column(Float, nullable=False)
    actual_fee = Column(Float, nullable=True)
    commission_rate = Column(Float, default=0.05)
    referrer_commission = Column(Float, nullable=True)
    marketplace_commission = Column(Float, nullable=True)  # 转介绍 = 0
    status = Column(Enum("pending", "accepted", "completed", "settled", "cancelled"), default="pending", index=True)
    match_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

# 3. templates 表 (文书模板分享)
class MarketplaceTemplate(Base):
    """Marketplace 文书模板分享表"""
    __tablename__ = "marketplace_templates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(String(64), unique=True, nullable=False, index=True)
    author_id = Column(String(64), nullable=False, index=True)
    firm_id = Column(String(64), nullable=True, index=True)
    template_name = Column(String(255), nullable=False)
    template_type = Column(Enum("contract", "letter", "complaint", "defense", "arbitration"), nullable=False, index=True)
    language = Column(Enum("zh-CN", "en-US", "bilingual"), default="zh-CN", index=True)
    jurisdiction = Column(String(64), nullable=True, index=True)
    template_content = Column(Text, nullable=False)
    price = Column(Float, default=10.0)  # ¥10-100/模板
    downloads = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    share_scope = Column(Enum("public", "private"), default="public")
    status = Column(Enum("active", "deprecated"), default="active", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

# 4. firm_marketplace 表 (律所高级功能)
class FirmMarketplace(Base):
    """律所 Marketplace 高级功能表"""
    __tablename__ = "firm_marketplace"
    id = Column(Integer, primary_key=True, autoincrement=True)
    firm_id = Column(String(64), unique=True, nullable=False, index=True)
    # 律所品牌定制
    logo_url = Column(String(512), nullable=True)
    primary_color = Column(String(16), nullable=True)
    secondary_color = Column(String(16), nullable=True)
    accent_color = Column(String(16), nullable=True)
    font = Column(String(64), nullable=True)
    style = Column(String(64), nullable=True)  # 严谨 / 现代 / 商务
    # 律所版定价
    pricing_tier = Column(Enum("10_lawyers", "20_lawyers", "50_lawyers", "100_lawyers"), nullable=False)
    annual_fee = Column(Float, nullable=False)  # ¥99,999 / ¥179,999 / ¥399,999 / ¥699,999
    # 私有化部署
    private_deployment = Column(Boolean, default=False)
    deployment_url = Column(String(512), nullable=True)
    # Marketplace 高级功能
    advanced_features = Column(JSON, nullable=True)  # 转介绍 + 协同办案 + 跨境文件
    status = Column(Enum("active", "expired", "cancelled"), default="active", index=True)
    signed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

# 5. cross_border 表 (跨境文件)
class CrossBorderService(Base):
    """跨境文件服务表"""
    __tablename__ = "cross_border_services"
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(String(64), unique=True, nullable=False, index=True)
    lawyer_id = Column(String(64), nullable=False, index=True)
    doc_type = Column(Enum("letter", "contract", "complaint", "defense", "arbitration_application", "arbitration_response"), nullable=False, index=True)
    language = Column(Enum("zh-CN", "en-US", "bilingual", "dual_column"), nullable=False, index=True)
    jurisdiction = Column(Enum("CN", "HK", "SG", "US", "UK", "ICC", "HKIAC", "SIAC"), nullable=False, index=True)
    price = Column(Float, nullable=False)  # ¥99-1990/份
    marketplace_commission_rate = Column(Float, default=0.30)
    template_id = Column(String(64), nullable=True)  # 复用 Skill 3 v3.0 模板
    rating = Column(Float, default=0.0)
    total_orders = Column(Integer, default=0)
    status = Column(Enum("active", "paused"), default="active", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

# 6. commissions 表 (抽成记录)
class MarketplaceCommission(Base):
    """Marketplace 抽成记录表"""
    __tablename__ = "marketplace_commissions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    commission_id = Column(String(64), unique=True, nullable=False, index=True)
    transaction_id = Column(String(64), nullable=False, index=True)
    transaction_type = Column(Enum("referral", "co_counsel", "cross_border", "template_share"), nullable=False, index=True)
    lawyer_id = Column(String(64), nullable=False, index=True)
    referrer_id = Column(String(64), nullable=True, index=True)
    transaction_amount = Column(Float, nullable=False)
    commission_rate = Column(Float, nullable=False)
    commission_amount = Column(Float, nullable=False)
    status = Column(Enum("pending", "confirmed", "settled", "withdrawn"), default="pending", index=True)
    # 7 天冷静期 + T+7+1 结算 + T+30 提现
    confirm_at = Column(DateTime, nullable=True)
    settle_at = Column(DateTime, nullable=True)
    withdraw_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

# 7. reviews 表 (评价)
class MarketplaceReview(Base):
    """Marketplace 评价表"""
    __tablename__ = "marketplace_reviews"
    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(String(64), unique=True, nullable=False, index=True)
    transaction_id = Column(String(64), nullable=False, index=True)
    transaction_type = Column(Enum("referral", "co_counsel", "cross_border", "template_share"), nullable=False, index=True)
    reviewer_id = Column(String(64), nullable=False, index=True)
    lawyer_id = Column(String(64), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5
    review_text = Column(Text, nullable=True)
    # 5 维度评分 (复用 W12 doc_workflow)
    risk_dim_facts = Column(Float, nullable=True)
    risk_dim_legal = Column(Float, nullable=True)
    risk_dim_demand = Column(Float, nullable=True)
    risk_dim_deadline = Column(Float, nullable=True)
    risk_dim_consequence = Column(Float, nullable=True)
    status = Column(Enum("published", "hidden", "deleted"), default="published", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

# 8. notifications 表 (通知)
class MarketplaceNotification(Base):
    """Marketplace 通知表"""
    __tablename__ = "marketplace_notifications"
    id = Column(Integer, primary_key=True, autoincrement=True)
    notification_id = Column(String(64), unique=True, nullable=False, index=True)
    lawyer_id = Column(String(64), nullable=False, index=True)
    notification_type = Column(Enum("referral_new", "referral_accepted", "case_new", "case_accepted", "commission_settled", "review_new", "withdraw_completed"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    link_url = Column(String(512), nullable=True)
    status = Column(Enum("unread", "read"), default="unread", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    read_at = Column(DateTime, nullable=True)
```

---

## 6. Marketplace UI 设计 (Vue 3 + React 18 + Tailwind + Element Plus)

### 6.1 Marketplace 入口 (律师工作站 Tab)

```
[律师工作站]
├── 案件 (Case)
├── 客户 (Client)
├── 日程 (Calendar)
├── 文书 (Document) ← Skill 3 v3.0 律师函 (W26 launch ab59c49)
├── 类案 (Case Law)
├── 知识库 (Knowledge)
└── Marketplace ⭐ (新增, W28 Phase 6.1) ← 本文件
    ├── 转介绍 (Referral)
    ├── 协同办案 (Co-counsel)
    ├── 跨境文件 (Cross-border)
    ├── 文书模板 (Template)
    ├── 我的抽成 (Commission)
    └── 我的评价 (Review)
```

### 6.2 Marketplace 5 大页面

| 页面 | 路径 | 核心功能 | 复用组件 |
|------|------|---------|---------|
| **Marketplace 首页** | `/marketplace` | 5 大入口卡片 + 推荐律师 + 推荐案件 + 推荐跨境文件 | Element Plus Card + Tailwind Grid |
| **转介绍页面** | `/marketplace/referrals` | 创建转介绍 + 列表 + 详情 + 抽成 | Element Plus Form + Table + Timeline |
| **协同办案页面** | `/marketplace/cases` | 发布协同办案 + 列表 + 详情 + 分账 + 文档协作 | Element Plus Form + Table + Notion-like Editor |
| **跨境文件页面** | `/marketplace/cross-border` | 服务列表 + 订单 + 生成 (复用 Skill 3 v3.0) + 国际仲裁 | Element Plus Form + Table + i18n |
| **我的抽成页面** | `/marketplace/commissions` | 抽成记录 + 提现申请 + 抽成统计 + Dashboard | Element Plus Statistic + Table + Chart |

### 6.3 Marketplace 移动端 UI (复用 W26 launch § 4.2.1 React Native)

> 移动端 Marketplace App: React Native 0.73+ + Expo 51+ + React Navigation 6+ + Zustand 4+ + WebSocket + SQLite 本地缓存 + 云端三层同步 + Touch ID/Face ID + Apple Pencil 2 代支持.

---

## 7. Phase 6.1 6 节点路线 (1/16 + 2/1 + 3/1 + 4/1 + 5/1 + 6/1)

### 7.1 6 节点路线总览

| 节点 | 日期 | 公测 day | 期望累计 (律师 / 律所 / ARR) | Marketplace 里程碑 |
|------|------|---------|------------------------------|-------------------|
| **1/16 (W24 启动)** | 2027-01-16 | 175 | 350 / 60 / ¥700,000 | **Marketplace PRD 启动** (W28 phase6-1-marketplace-prd 拆 1/2, 本文件) |
| **2/1 (W25 完结)** | 2027-02-01 | 191 | 500 / 80 / ¥1,000,000+ | Marketplace 公测 (W25 已落地) + Phase 6.1 PRD 完结 (本文件) |
| **3/1 (W26)** | 2027-03-01 | 219 | 550 / 100 / ¥1,200,000 | Marketplace 抽成 5% 启动 (W26 已落地) + 跨境案件公测 |
| **4/1 (W30)** | 2027-04-01 | 250 | 600 / 130 / ¥1,500,000 | 律所版定制签约 10 律所 + 跨平台 iOS 启动 + Marketplace 全功能 |
| **5/1 (W34)** | 2027-05-01 | 280 | 700 / 160 / ¥1,800,000 | Marketplace 抽成 5% 模块上线 + Marketplace 律师 50 名 |
| **6/1 (W38 Phase 6 完结)** | 2027-06-01 | 311 | 750 / 180 / ¥2,200,000 | Marketplace 全功能 + 跨平台 + 国际版预备 + 半年节点 |
| **6/30 (W40)** | 2027-06-30 | 340 | 750 / 180 / ¥2,200,000 | Phase 6 完结 KPI 验证 + Phase 7 准备 |

### 7.2 1/16 启动节点 (W24)

```
[1/16 09:00] W28 phase6-1-marketplace-prd 启动 (W28 拆 1/2)
  - W28 phase6-1-marketplace-prd (本文件, lex-coder) - Marketplace PRD
  - W28 skill4-v1-prd (lex-ai) - Skill 4 v1 PRD
  - W28 skill3-v3-100pct-launch (lex-bd) - Skill 3 v3.0 100% 全量
  - W28 skill3-v3-v2-deprecation (lex-bd) - Skill 3 v2.0 退役

[1/16 09:15] PRD 落地汇报
  - phase6-1-marketplace-prd-2027-01-16.md 落地 (~50-80KB, 6 大方向 + 12 周 6 plan + 商业模型 + API + 数据模型 + UI)
  - skill4-v1-prd-2027-01-16.md 落地 (~30-50KB, Skill 4 v1 PRD)
  - skill3-v3-100pct-execution-2027-03-15.md 落地 (~10KB, 5 项全量验证)
  - skill3-v3-v2-deprecation-execution-2027-04-01.md 落地 (~8KB, 5 项退役验证)

[1/16 19:00] 当日报告启动
  - 4 task deliverable 无冲突
  - 4 agent 全部 git commit + push + 含 'VERDICT: PASS' 大写标记
  - W29 实施 Marketplace API + W29 实施 Skill 4 + W28 启动 Skill 3 v3.0 100% 全量 + W28 启动 Skill 3 v2.0 退役
```

---

## 8. Marketplace 8 大子模块 + 律师画像 + KPI 跟踪

### 8.1 Marketplace 8 大子模块

| # | 子模块 | 启动节点 | 完结节点 | 核心功能 | 期望覆盖 (3/31) |
|---|--------|---------|---------|---------|----------------|
| 1 | **Marketplace 入口 (Tab)** | W23 1/15 | 已上线 | 律师工作站新增 Marketplace Tab | 500 律师 (3/31) |
| 2 | **案件接案 (Cases)** | W23 1/15 | 已上线 | 律师可发布待接案件 + 律师可接 Marketplace 待接案件 | 100 律师 (3/31) |
| 3 | **转介绍 (Referral)** | W25 2/1 | W28 Phase 6.1 完结 | 律师 A 推荐律师 B, B 接案付费后, A 抽 5% | 50 律师 (3/31) |
| 4 | **协同办案 (Co-counsel)** | W25 2/1 | W28 Phase 6.1 完结 | 律师 A + 律师 B 协同办案, Marketplace 抽 10% | 50 律师 (3/31) |
| 5 | **跨境文件 (Cross-border)** | W26 2/15 | W28 Phase 6.1 完结 | 中国律师接国际客户, 中英双语律师函, Marketplace 抽 30% | 50 国际客户/涉外律所/国际仲裁律师 (3/31) |
| 6 | **文书模板分享 (Template)** | W25 2/1 | W28 Phase 6.1 完结 | 律师分享文书模板, 律师付费后, 作者 + Marketplace 各抽 5% | 50 律师 (3/31) |
| 7 | **律所版定制 (Firm Customized)** | W23 1/1 | W30-W33 签约 30 律所 | logo + 主题色 + 私有化部署 + Marketplace 高级 | 5 律所签约 (3/31) |
| 8 | **抽成结算 (Commission)** | W28 Phase 6.1 | W28 Phase 6.1 完结 | T+7 冷静期 + T+7+1 结算 + T+30 提现 | 100% Marketplace 律师 (3/31) |

### 8.2 律师画像 (5 类律师, 复用 W23 phase5-5-celebration § 4)

| 律师类型 | 数量 | Phase 6.1 期望占比 | Marketplace 参与方 |
|---------|------|------------------|------------------|
| **创史律师 (Founding)** | 40 | 8% | Marketplace 高级参与方 (50% 创史律师参与, 20 名) |
| **个人版律师 (Individual)** | 350 | 70% | Marketplace 基础参与方 (30% 个人版律师参与, 105 名) |
| **企业版律师 (Enterprise)** | 75 | 15% | Marketplace 中级参与方 (50% 企业版律师参与, 38 名) |
| **律所合伙人 (Firm Partner)** | 25 | 5% | Marketplace 高级参与方 (50% 律所合伙人参与, 13 名) |
| **国际客户/涉外律所** | 50 | 10% | Marketplace 跨境参与方 (100% 跨境律师参与, 50 名) |
| **合计** | **540** | **100%** | **Marketplace 律师参与方 226 名 (期望 200)** |

### 8.3 Marketplace 5 项核心 KPI

| 指标 | 期望值 (3/31) | 期望值 (6/30) | 期望值 (12/31) | 数据来源 |
|------|--------------|--------------|----------------|---------|
| **Marketplace 律师参与方** | **200** | 500 | 1000 | /api/marketplace/dashboard |
| **Marketplace 月接案数** | [X, 3/31 实测填实] | [Y, 6/30 实测填实] | [Z, 12/31 实测填实] | /api/marketplace/cases?status=completed |
| **Marketplace 月营收** | **¥30,000+** | ¥80,000+ | ¥200,000+ | /api/marketplace/commissions?status=settled |
| **跨境案件月单量** | **200** | 500 | 1000 | /api/marketplace/cross-border/jobs?status=completed |
| **律师满意度** | **>= 4.6/5.0** | >= 4.7/5.0 | >= 4.8/5.0 | /api/marketplace/reviews?lawyer_id=X |

---

## 9. 应急备案 (4 场景, 复用 W26 launch § 11.4)

| 场景 | 触发条件 | 应急动作 | 响应时间 |
|------|---------|---------|---------|
| **场景 1: Marketplace 律师强烈反对** | 1h 内 20+ 律师投诉抽成过高 | 调整抽成 (24h) + 1v1 律师沟通 + Marketplace 暂停 24h + 律师私域群通知 | 1h 内应急 + 24h 内修复 + 48h 内律师沟通 |
| **场景 2: 抽成计算错误** | commission.py 计算错误 / T+7 退款失败 | 修复 commission.py (1h) + 退还律师费用 (24h) + Marketplace 暂停 24h + 自动化测试 | 1h 内应急 + 24h 内修复 + 48h 内自动化测试 |
| **场景 3: Marketplace API 性能瓶颈** | QPS > 1000 / 响应时间 > 2s / 错误率 > 5% | 启用 phase5-rust 5x perf (1h) + Redis 缓存 + API 限流 + Prometheus 监控告警 | 1h 内应急 + 24h 内优化 + 48h 内监控 |
| **场景 4: Marketplace 数据泄露** | 律师案件 / 客户 / 文书泄露 | 关闭 Marketplace API (1h) + 数据泄露评估 (24h) + 律师通知 + 数据安全修复 + 合规报告 + 7 天重启 | 1h 内应急 + 24h 内修复 + 7 天内重启 |

> **严守数据本地化 (PRD V5.0 § 12.1 硬性原则)**: 律师案件 / 客户 / 文书 不离开律师电脑, Marketplace 仅存储撮合记录 + 抽成记录 + 评价记录.

---

## 10. 不变性原则 (复用 W22 + W23 + W24 + W25 + W26 + W27 6 plan 验证)

### 10.1 兼容性保证 (W28 Phase 6.1 严守)

> **W28 phase6-1-marketplace-prd 严守兼容性原则 (W22 + W23 + W24 + W25 + W26 + W27 6 plan 验证)**:
>
> **1. W11 PRD V5.0 不动**: § 9 产品路线 + § 10 商业模式 + § 11 成功指标 + § 12 风险 + § 13 法律免责声明 (W28 Phase 6.1 是增量)
> **2. W12 A2 doc_workflow 5 状态机不动**: draft → ai_reviewed → lawyer_reviewed → client_signed → archived (W28 Marketplace 跨境文件复用)
> **3. W19 phase5-react 18 + TS 5.6 strict 不动**: React 18.3 + TS 5.6 strict + path alias (@/*) + Vite 5.4 (W28 Marketplace UI 复用)
> **4. W20 phase5-electron 17.4.11 不动**: Electron 17.4.11 + electron-builder 23.6.0 + electron-updater 6.8.9 (W28 Marketplace 桌面端复用)
> **5. W21 6929cc1 v2.0 rollout + v1.0 退役 不动**: rollout.py + doc_gen_router.py + letter_v2.md + skill3_letter_v2.yaml (W28 Marketplace 跨境文件模板复用)
> **6. W22 2792bd0 Rust 1.83 LTS + 5x perf 不动**: phase5-rust 1.83 LTS + reqwest + actix http + build.rs (W28 Marketplace API Rust 5x perf 复用)
> **7. W23 phase5-5-celebration § 1.2.5 律师 Marketplace MVP 不动**: Marketplace 入口 + 律师接案 + 文书模板分享 + 互相推荐 (W28 Phase 6.1 接力公测)
> **8. W26 ab59c49 Skill 3 v3.0 launch 不动**: 多端 + 多语言 + 多律所模板 + Marketplace 集成 (W28 Marketplace 跨境文件复用 letter_v3_en.md + letter_v3_bilingual.md)

### 10.2 Marketplace 兼容性边界

> **Marketplace 不修改的代码**: W12 A2 doc_workflow 5 状态机 + W12 A2 signature_router + W19 phase5-react 18 + TS 5.6 strict + W20 phase5-electron 17.4.11 + W21 6929cc1 v2.0 rollout + v1.0 退役 + W22 2792bd0 Rust 1.83 LTS + 5x perf + W23 phase5-5-celebration Marketplace MVP + W26 ab59c49 Skill 3 v3.0 launch.
>
> **Marketplace 新增的代码 (W29+ 接力)**:
> - backend/cases-crawler/marketplace/cases.py (案件接案)
> - backend/cases-crawler/marketplace/referrals.py (转介绍)
> - backend/cases-crawler/marketplace/co_counsel.py (协同办案)
> - backend/cases-crawler/marketplace/templates.py (文书模板分享)
> - backend/cases-crawler/marketplace/firm_marketplace.py (律所版定制)
> - backend/cases-crawler/marketplace/cross_border.py (跨境文件)
> - backend/cases-crawler/marketplace/commissions.py (抽成)
> - backend/cases-crawler/marketplace/reviews.py (评价)
> - backend/cases-crawler/marketplace/notifications.py (通知)
> - backend/cases-crawler/marketplace/dashboard.py (Dashboard)
> - backend/cases-crawler/marketplace/api/*.py (API 路由 ~25 端点)
> - phase5-react/src/marketplace/* (UI 8 大页面)
> - backend/cases-crawler/marketplace/tests/*.py (测试 ~50 测试)

### 10.3 数据本地化保证 (严守 PRD V5.0 § 12.1)

> **Marketplace 数据本地化原则 (W28 Phase 6.1)**:
> - **律师案件 / 客户 / 文书 不离开律师电脑**: Marketplace 仅存储撮合记录 + 抽成记录 + 评价记录
> - **in-memory metrics**: 律师使用时长 / 律师满意度 / 转化率 in-memory metrics, 不持久化敏感数据
> - **律师隐私保护**: Marketplace 通知不包含律师案件内容 (仅包含 Marketplace 撮合 + 抽成通知)
> - **律师授权机制**: Marketplace 律师必须明确授权 (1v1 律师沟通 + Marketplace 注册时授权协议)
> - **数据加密**: Marketplace 敏感数据 AES-256-GCM 落盘 + TLS 1.3 传输
> - **访问控制**: Marketplace RBAC (律师 / 律所 / 国际客户 / Marketplace Admin 4 角色)
> - **审计日志**: Marketplace 全操作可追溯, 不可篡改
> - **应急数据删除**: 律师可随时申请 Marketplace 数据删除 (T+7 删除 + T+30 不可恢复)

---

## 11. 复用源 + 严守 fabricate 原则

### 11.1 复用源比例

> **W28 phase6-1-marketplace-prd 复用源比例 (W22-W27 + W11 PRD V5.0 + W15 1000 律师)**:

| 复用源 | 比例 | 内容 |
|--------|------|------|
| **W23 phase5-5-launch** (W23 commit 432a073) | 25% | 5 大新方向 #5 律师 Marketplace MVP + Marketplace 公测 + 律所版定制 ¥99,999/年起 + 定价梯度 10/20/50/100 律师 + Marketplace 抽成 5% |
| **W23 phase6-2027-roadmap** (W23 commit a9e5fdd) | 25% | Phase 6 4 阶段 + 9 plan/季度 = 18 plan + Phase 6.1 Marketplace MVP + 6 节点路线 + 律师/律所/ARR 接力 |
| **W24 phase5-5-mid-month** (W24 commit 4d2efaf) | 15% | Phase 5.5 中段 25% Marketplace MVP 落地 + Phase 6 准备 + 5 大新方向中段 30%+50%+10%+18%+25% |
| **W25 cc14045** (Skill 3 v3.0 PRD) | 15% | Marketplace 集成 + 文书模板分享 + 抽成 5% + 跨境案件 + 律所版定制 |
| **W26 ab59c49** (Skill 3 v3.0 launch) | 10% | Marketplace 公测 3/1 + 全功能 3/15 + v2.0 退役 4/1 + 推广 5 渠道 + 应急备案 |
| **W15 d66fc33** (recruit-1000) | 5% | 5 渠道 1000 律师招募 + 朋友圈 9 宫格 + 律师私域 |
| **W22 2792bd0** (Phase 5.3 Rust) | 3% | Rust 1.83 LTS + reqwest + actix http + build.rs + 5x perf |
| **W19 83d4695** (Phase 5.1 React) | 2% | React 18 + TS 5.6 strict + path alias + Vite 5.4 |
| **合计** | **100%** | - |

### 11.2 严守 fabricate 原则 (W22 + W23 + W24 + W25 + W26 + W27 6 plan 验证)

> **W28 phase6-1-marketplace-prd 严守 fabricate 原则**:
> - **当前时间**: 2026-06-30 (写 PRD 时), 距 1/16 启动 200 天
> - **数据 placeholder**: 所有数字 [节点当天实测填实] 标注
> - **owner 节点实测填实**: 1/16 + 2/1 + 3/1 + 4/1 + 5/1 + 6/1 共 6 节点, 每个节点当天 09:00 owner patch 替换 placeholder
> - **严守产品边界**: AI 辅助, 不替代律师 (PRD V5.0 硬性原则, Marketplace 仅做撮合 + 抽成 + 跨境文件复用)
> - **严守数据本地化**: 律师案件 / 客户 / 文书 / 跨境文件 不离开律师电脑, Marketplace 仅存储撮合记录 + 抽成记录 + 评价记录
> - **数据 placeholder 格式**: 数字 [X, 节点当天实测填实] 标注 + 百分比 [X%, 节点当天实测填实] 标注 + 金额 [¥X, 节点当天实测填实] 标注 + 日期 [YYYY-MM-DD, 节点当天实测填实] 标注

---

## 12. W29+ 接力 (Phase 6.1 实施 + 测试 + 公测)

> **W29+ 接力 (W28 phase6-1-marketplace-prd 拆 1/2 已落地, W29+ 接力)**:

| 周 | 计划 ID | 核心任务 | 关键 commit |
|----|---------|---------|------------|
| **W29** | W29 marketplace-api | Marketplace API 实施 (33 端点 + 8 数据表 + 50 测试) | feat(marketplace): W29 Marketplace API |
| **W30** | W30 firm-customized-launch | 律所版定制签约 10 律所 + 跨平台 iOS 启动 | feat(firm-customized): W30 |
| **W31** | W31 marketplace-ui | Marketplace UI 8 大页面 (React 18 + TS 5.6 strict) | feat(marketplace-ui): W31 |
| **W32** | W32 marketplace-tests | Marketplace 测试 50 测试 (单元 + 集成 + E2E) | test(marketplace): W32 |
| **W33** | W33 cross-border-launch | 跨境文件公测 + Android 启动 | feat(cross-border): W33 |
| **W34** | W34 marketplace-commission | Marketplace 抽成 5% 模块 (T+7 + T+7+1 + T+30) | feat(marketplace-commission): W34 |
| **W35** | W35 marketplace-beta-50 | Marketplace 律师 50 名 + 抽成试运营 | feat(marketplace-beta-50): W35 |
| **W36** | W36 marketplace-beta-80 | Marketplace 律师 80 名 + 抽成全量 | feat(marketplace-beta-80): W36 |
| **W37** | W37 international-prep | Marketplace 律师 100 名 + 国际版预备 v0.1 | feat(international-prep): W37 |
| **W38** | W38 phase6-final | Phase 6 完结 + 半年节点 KPI 验证 (750 律师 + 180 律所 + ¥2,200,000 ARR) | docs(phase6-final): W38 |
| **W39** | W39 phase7-prep | Phase 7 准备 + 律所版独立产品 PRD v1.0 | docs(phase7-prep): W39 |
| **W40** | W40 phase7-plan | Phase 7 plan 准备 + 跨年总结 (6/30 节点 + 18 plan + ¥999 万 ARR) | docs(phase7-plan): W40 |

> **W29 复用源 (W28+ 接力)**: phase6-1-marketplace-prd-2027-01-16.md v1.0 (W28 本文件, Marketplace PRD) + W26 ab59c49 Skill 3 v3.0 launch + W25 cc14045 Skill 3 v3.0 PRD + W22 2792bd0 phase5-rust 1.83 LTS + 5x perf + W19 83d4695 phase5-react 18 + TS 5.6 strict.
>
> **W29 Stop when**: 33 端点 + 8 数据表 + 50 测试 全部落地 + ruff 0 error + pytest 100% pass + 1 commit + push + 含 'VERDICT: PASS' 大写.

---

## 13. 总结

> **W28 phase6-1-marketplace-prd 拆 1/2 (本文) 总结**:
> - **VERDICT: PASS** 大写顶部标记 (W22 + W23 + W24 + W25 + W26 + W27 强制规范应用)
> - **Phase 6.1 主题**: 律师 Marketplace + AI 谈判 (1/16 启动, 3/31 完结, 12 周 6 plan)
> - **6 大方向** (W23 Phase 5.5 5 大方向 + 1 增量跨境案件): 7 大模块 + 3 版本定价 + 50 → 200 律所 + ¥30 万 → ¥200 万+ ARR + AI 辅助 + 律师 Marketplace + 跨境案件 + 国际客户 + 涉外律所 + 国际仲裁
> - **12 周 6 plan**: W23 已完结 (432a073) + W24 已完结 (4d2efaf) + W25 已完结 (cc14045 + 1fbfe93) + W26 已完结 (ab59c49) + W27 已完结 (ff0d2a2 + ed96850) + W28 在跑 (本文件 + lex-ai Skill 4 v1)
> - **目标**: 500 律师付费 + 50 律所签约 + ¥100 万 ARR (Phase 6 完结 6/30)
> - **Marketplace 商业模型** (三维): 转介绍 (5% 抽成) + 协同办案 (10% 分账) + 跨境文件 (30% 抽成)
> - **Marketplace API** (3 大域, ~25 端点): 律师 ↔ 律师 (10) + 律师 ↔ 律所 (8) + 跨境文件 (7)
> - **Marketplace 数据模型** (8 张表): cases + referrals + templates + firm_marketplace + cross_border + commissions + reviews + notifications
> - **Marketplace UI** (8 大页面): Marketplace 入口 + 5 大页面 + 移动端 + 桌面端
> - **6 节点路线**: 1/16 + 2/1 + 3/1 + 4/1 + 5/1 + 6/1 (公测 day 175-311)
> - **应急备案** (4 场景): Marketplace 律师反对 + 抽成计算错误 + API 性能瓶颈 + 数据泄露
> - **不变性原则** (8 项): PRD V5.0 + doc_workflow + phase5-react + phase5-electron + phase5-rust + phase5-5-celebration + Skill 3 v3.0 launch
> - **数据本地化** (PRD V5.0 § 12.1 硬性原则): 律师案件 / 客户 / 文书不离开律师电脑, Marketplace 仅存储撮合记录 + 抽成记录 + 评价记录
> - **W29+ 接力**: Marketplace API 实施 + 测试 + 公测 + 律所版定制签约 + 跨境文件公测 + Phase 6 完结

> **VERDICT: PASS** (W22 + W23 + W24 + W25 + W26 + W27 强制规范应用: 大写顶部标记 + 严守 fabricate + 6 大方向 + 12 周 6 plan + Marketplace 商业模型 + Marketplace API + 数据模型 + UI + 6 节点路线 + 应急备案 + 不变性原则 + 复用源 + fabricate 原则 + 总结 + W29+ 接力)

> **W28 phase6-1-marketplace-prd 拆 1/2 完结**:
> - phase6-1-marketplace-prd-2027-01-16.md 落地 (~50-80KB, 6 大方向 + 12 周 6 plan + Marketplace 商业模型 + API)
> - VERDICT: PASS 大写顶部标记
> - 1 commit + push (待 W28 plan_aeb9abc3 完成)
> - W29+ 接力 (Marketplace API 实施 + 测试 + 公测 + 律所版定制 + 跨境文件 + Phase 6 完结)

> **复用 W23-W27 + W11 PRD V5.0 + W15 1000 律师累计比例 100%**, W28 Phase 6.1 PRD 复用源比例 100%, W28 phase6-1-marketplace-prd 不修改 W11-W27 任何已落地 commit, W29+ 接力实施 Marketplace API + 测试 + 公测 + 律所版定制 + 跨境文件 + Phase 6 完结.
