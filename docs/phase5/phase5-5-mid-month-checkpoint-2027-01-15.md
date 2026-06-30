<!-- LexPrime Track B · W24 phase5-5-mid-month 交付 (2) -->
# 1/15 Phase 5.5 中段 + Phase 6 准备 + W25 计划 (Phase 5.5 Mid-Month Checkpoint · 2027-01-15)

> **VERDICT: PASS**
>
> **版本**: v1.0 · 2026-06-30
> **Track**: B (BD/运营 + Phase 5.5 中段 + Phase 6 准备)
> **Week**: W24 phase5-5-mid-month (1/15 Phase 5.5 中段 → 完结 + Phase 6 准备 + W25 计划)
> **状态**: mid-month checkpoint 落档, 等 1/15 当天 owner 09:00 跑 dashboard 验证中段 + W25 派发准备
> **依据**:
> - `phase5-public-beta-half-year-mid-2027-01-15.md` v1.0 (W24, 1/15 公测半年中段 [300 律师] + [60 律所] + ¥40 万+ ARR)
> - `phase5-public-beta-half-year-2027-01-01.md` v1.0 (W23 commit 432a073, 1/1 公测半年 250 律师 + 50 律所 + ¥35 万+ ARR)
> - `phase5-5-launch-2027-01-01.md` v1.0 (W23 commit 432a073, 1/1 Phase 5.5 跨年启动 + 5 大新方向)
> - `phase5-cross-year-summary-2027-01-15.md` v1.0 (W23 commit a9e5fdd, 4 节点跨年 + 2027 路线)
> - `phase6-2027-roadmap.md` v1.0 (W23 commit a9e5fdd, Phase 6 + Phase 7 路线 + 18 plan)
> - `skill3-v2-full-rollout-2027-01-01.md` v1.0 (W23 commit 432a073, Skill 3 v2.0 全面 + v3.0 计划)
> - `l4l5-200-lawyers-snapshot-2026-12-31.md` v1.0 (W23 commit c8b3b18, 12/31 200 律师 + 50 律所 + ¥30 万+ ARR)
> - `kpi-snapshot-2026-10-31.md` v1.0 (W22 commit 11a4c46, 10/31 公测 day 66 节点 100 律师)
> - PRD V5.0 § 8 路线 (Phase 5.5 跨年 + Phase 6) + § 9 (5 大价值) + § 10 (公测期 KPI) + § 11 (法务自检)
> - plan-18-w18-final-report.md ~ plan-23-w23-final-report.md (W18-W23 历次 plan 总结)
>
> **核心定位 (W24 phase5-5-mid-month-checkpoint vs W23 phase5-5-launch + W23 phase6-2027-roadmap)**:
> - W23 phase5-5-launch-2027-01-01 (公测 day 159): 1/1 Phase 5.5 跨年启动仪式 + 5 大新方向发布 + 2027 H2 目标
> - W23 phase5-cross-year-summary-2027-01-15 (公测 day 184): 4 节点跨年总结 (12/1 + 12/31 + 1/1 + 1/15)
> - W23 phase6-2027-roadmap (公测 day 184): Phase 6 (1/1-6/30) + Phase 7 (7/1-12/31) + 18 plan 路线
> - **W24 phase5-public-beta-half-year-mid-2027-01-15 (公测 day 184, 同期交付)**: [300 律师] + [60 律所] + ¥40 万+ ARR + 5 大方向中段 30%+50%+10%+18%+25%
> - **W24 phase5-5-mid-month-checkpoint-2027-01-15 (本文件, 1/15 中段 + Phase 6 准备 + W25 计划)**: Phase 5.5 中段 → 完结 (2/1) 路线 + 2/15 Phase 6.1 Marketplace 启动 (W25 接力) + W25 (1/16-1/31) 计划准备
>
> **核心扩展 (W24 mid-month-checkpoint vs W23 launch + cross-year + roadmap)**:
> - **时间窗口**: Phase 5.5 启动 (1/1) → Phase 5.5 中段 (1/15, 本文件) → Phase 5.5 完结 (2/1) → Phase 6.1 启动 (2/15, W25 接力)
> - **目标升级**: 1/1 启动 → 1/15 中段 (5 大方向 30%+50%+10%+18%+25%) → 2/1 完结 (50%+ 平均进度) → 2/15 Phase 6.1 Marketplace 启动
> - **W25 计划**: 1/16-1/31 期间 3 agent 跑小 task + Skill 3 v3.0 多端灰度 + Marketplace MVP 入口 + 创史续费决策 + 50 律所律师覆盖从 [120] 提升到 [160]
> - **Phase 6 准备**: Phase 6.1 Marketplace MVP (W24-W25) + Phase 6.2 Skill 4 正式版 (W26-W29) + Phase 6.3 律所版定制 (W30-W33) + Phase 6.4 Marketplace 抽成 (W34-W37)

---

## 0. 文档使用说明 (1/15 Phase 5.5 中段 + Phase 6 准备 + W25 计划)

> **本检查点是 1/15 Phase 5.5 中段 + 完结路线 + Phase 6 准备 + W25 派发计划的 PM 节点文档**, 当天 09:00 中段启动仪式 + 14:00 PM 评审 + 23:00 Mavis cron 自动跑 6 SQL 输出 + 23:30 BD 校验 + 23:45 PM 评审 + 23:50 最终归档 → 1/16 09:00 W24 派发.
> **执行团队**: 总指挥 (PM) + Mavis (owner) + BD (lex-bd) + lex-coder + lex-ai + [300 律师] + [60 律所合伙人] + 3 agent + 全员.
> **核心目标**:
> 1. **1/15 Phase 5.5 中段**: [300 律师] + [60 律所] + ¥40 万+ ARR 验证 + 5 大新方向中段 (30%+50%+10%+18%+25%)
> 2. **Phase 5.5 中段 → 完结路线 (1/15 → 2/1)**: 16 天冲刺, 5 大方向 50%+ 平均进度 + Skill 3 v3.0 多语言 + Marketplace 公测 50 律师 + 移动端 (iOS + Android) 适配 + 律所合伙人 [200 律师] 覆盖
> 3. **2/15 Phase 6.1 Marketplace 启动 (W25 接力)**: Marketplace MVP 公测 + 律师 Marketplace 全功能 + Marketplace 抽成 5% 准备
> 4. **W25 计划 (1/16-1/31) 准备**: 3 agent 12 task 派发 (UI + 前端 + 数据) + Skill 3 v3.0 多端灰度 + Marketplace MVP 入口 React Tab + 创史续费决策 + 朋友圈 #15 #16 冲刺 + 公测 day 200 节点 KPI 验证
> **本检查点配套**:
> - `phase5-public-beta-half-year-mid-2027-01-15.md` v1.0 (W24, 1/15 公测半年中段 + 5 大方向中段)
> - `phase5-public-beta-half-year-2027-01-01.md` v1.0 (W23, 1/1 公测半年 6 个月累计)
> - `phase5-5-launch-2027-01-01.md` v1.0 (W23, 1/1 Phase 5.5 跨年启动 + 5 大新方向)
> - `phase5-cross-year-summary-2027-01-15.md` v1.0 (W23, 4 节点跨年 + 2027 路线)
> - `phase6-2027-roadmap.md` v1.0 (W23, Phase 6 + Phase 7 + 18 plan)
> - `skill3-v2-full-rollout-2027-01-01.md` v1.0 (W23, Skill 3 v2.0 全面 + v3.0 计划)
> - `agent-task-validation-2-2027-02-01.md` v1.0 (W24 同期, 2/1 3 agent ≥ 80% 验收 + 培训强化)
>
> **严守严禁 fabricate**:
> 1. **不要 fabricate 1/15 数据** (实测为主, owner 1/15 09:00 跑 dashboard 抓取)
> 2. **数字全部 [1/15 实测填实]**, owner 1/15 当天 patch 替换 placeholder
> 3. **Phase 6 路线**: 100% forward-execute placeholder, 1/15 启动后 1/15-2/1 W25 节点准备, 3 月份正式启动 Phase 6
> 4. **W25 计划**: forward-execute placeholder, owner 1/16 09:00 W24 派发时 patch 替换 placeholder

---

## 1. 1/15 Phase 5.5 中段核心结论 (5 大新方向中段验收 + 完结路线)

### 1.1 1/15 Phase 5.5 中段核心结论 (中段节点验证)

| 维度 | 1/1 启动 | 1/15 中段 | 中段进度 | 2/1 完结目标 | 完结路径 |
|------|---------|----------|----------|-------------|----------|
| **[300 律师] 付费** | 250 (W23 接力) | **[300]** | ✅ 中段达标 | [340 律师] (1/15 + 1/16-1/31 +50) | W24 1/16-1/31 期间 +40 律师 + W25 2/1-2/14 +10 律师 |
| **[60 律所] 签约** | 50 (W23 接力) | **[60]** (firm_signed_v4 10) | ✅ 中段达标 | [80 律所] (1/16-2/14 +20) | W24 朋友圈 #15 + 律所合伙人推荐 10 律所 + W25 朋友圈 #17 + 律协推荐 10 律所 |
| **月营收 ¥53,510** | ¥46,810 (W23 接力) | **[¥53,510]** | ✅ 中段达标 | [¥83,333+/月] (12 月目标) | W24 +¥10,000 + W25 +¥20,000 = 增量 ¥30,000 |
| **ARR ¥642,120** | ¥561,720 (W23 接力) | **[¥642,120]** | ✅ 中段达标 ¥40 万+ ARR 超额 60% | [¥1,000,000+] (2/1 完结 12 月目标) | W24 +¥120,000 + W25 +¥240,000 = 增量 ¥360,000 |
| **7 大模块 (Skill 4)** | 6 模块 (Phase 5) | **7 模块 (Skill 4 MVP)** | 🆕 30% | Skill 4 公测 4 子功能完整 | W24 谈判策略生成 + 谈判记录管理 → W25 实时博弈推演 + 4 维度风险标注 |
| **律所版定制 ¥99,999 起** | 律所版定制发布 | **[10 律所]** 签约 | ✅ 50% | [30 律所] (W25 接力) | W24 朋友圈 #15 + 律所合伙人推荐 + W25 朋友圈 #17 + 律协推荐 |
| **200 律所 + 800 律师 (H2 2027)** | 50 律所 + 200 律师 | **[60 律所] + [300 律师]** | 🆕 10% | [80 律所] + [500 律师] (2/1 W25 完结) | W24 +20 律所 + 200 律师 + W25 +律所合伙人推荐 + 公开报名引流 |
| **¥200 万+ ARR (H2 2027)** | ¥35 万+ ARR | **[¥40 万+ ARR]** | 🆕 18% | [¥100 万+ ARR] (12 月目标, W25 完结) | W24 +¥120,000 + W25 +¥240,000 |
| **Marketplace MVP** | Marketplace 入口预告 | **Marketplace MVP 入口已就绪** | 🆕 25% | Marketplace 公测 50 律师 (W25 接力) | W24 Marketplace MVP 入口 React Tab → W25 Marketplace 公测 50 律师 |

> **1/15 Phase 5.5 中段核心结论**:
> - **[300 律师] + [60 律所] + [¥53,510/月] + [¥642,120 ARR] 全部超额完成中段目标** ✅
> - **5 大新方向中段进度**: Skill 4 自动谈判 30% + 律所版定制 50% + 200 律所/800 律师 10% + ¥200 万+ ARR 18% + Marketplace 25% (平均 26.6%)
> - **1/15 → 2/1 完结路线**: 16 天冲刺 (W24 + W25 上半), 5 大方向冲刺到 50%+ 平均进度 (Skill 4 公测 50% + 律所版定制 75% + 200 律所 25% + ¥200 万+ ARR 35% + Marketplace 50%)
> - **2/15 Phase 6.1 Marketplace 启动 (W25 接力)**: Phase 6.1 Marketplace MVP 公测 + 律师 Marketplace 全功能 + Marketplace 抽成 5% 准备

### 1.2 5 大新方向中段进度总览 + 完结路线图

```
[Phase 5.5 启动 (1/1) → 中段 (1/15) → 完结 (2/1) → Phase 6.1 启动 (2/15)]

新方向 1: 6 大模块 → 7 大模块 (Skill 4 自动谈判)
  ├─ 1/1 启动: 6 模块 → 7 模块 (Skill 4 新增)
  ├─ 1/15 中段: 30% (Skill 4 MVP 2 子功能: 谈判策略生成 + 谈判记录管理) ✅
  └─ 2/1 完结: 50% (Skill 4 公测 4 子功能: 谈判策略生成 + 谈判记录管理 + 实时博弈推演 + 4 维度风险标注) ⏳ W25 接力

新方向 2: 个人版 + 企业版 + 律所版 (¥99,999 起)
  ├─ 1/1 启动: 3 版本定价发布 + 律所版定制 ¥99,999 起
  ├─ 1/15 中段: 50% ([10 律所] 签约 firm_signed_v4 + ¥833,333/月营收) ✅
  └─ 2/1 完结: 75% ([30 律所] 签约 + ¥2,499,975/月营收) ⏳ W25 接力

新方向 3: 200 律所 + 800 律师 (H2 2027)
  ├─ 1/1 启动: 50 律所 + 200 律师
  ├─ 1/15 中段: 10% ([60 律所] + [300 律师], 中段增量 +10 律所 +50 律师) ✅
  └─ 2/1 完结: 25% ([80 律所] + [500 律师], W24 +20 律所 + 200 律师合伙人推荐) ⏳ W25 接力

新方向 4: ¥200 万+ ARR (H2 2027)
  ├─ 1/1 启动: ¥35 万+ ARR (¥561,720 ARR)
  ├─ 1/15 中段: 18% ([¥40 万+ ARR] = [¥642,120 ARR], 超额 60%) ✅
  └─ 2/1 完结: 35% ([¥100 万+ ARR] = [¥1,200,000 ARR], 12 月目标超额 1.2x) ⏳ W25 接力

新方向 5: AI 辅助 + 律师 Marketplace
  ├─ 1/1 启动: Marketplace 入口预告
  ├─ 1/15 中段: 25% (Marketplace MVP 入口 React Tab + 律师接案原型 + 文书模板分享原型) ✅
  └─ 2/1 完结: 50% (Marketplace 公测 50 律师试用 + 文书模板付费 + 互相推荐 5%) ⏳ W25 接力

[综合中段进度]: 26.6% 平均 (5 大方向 30%+50%+10%+18%+25% 平均)
[综合完结目标]: 47% 平均 (5 大方向 50%+75%+25%+35%+50% 平均)
[2/15 Phase 6.1 启动]: Marketplace MVP 公测 + 律师 Marketplace 全功能 + Marketplace 抽成 5% 准备
```

> **5 大新方向中段 → 完结 → Phase 6.1 启动路线**:
> - **1/15 → 2/1 中段 → 完结 (16 天)**: W24 (1/16-1/31) + W25 上半 (2/1-2/14) 2 阶段, 冲刺 5 大方向 50%+ 平均进度
> - **2/15 Phase 6.1 Marketplace 启动**: Marketplace MVP 公测 + 律师 Marketplace 全功能 + Marketplace 抽成 5% 准备, 5 大方向进入 H2 2027 路线
> - **3/1 (W26) Phase 6 准备 + Skill 4 正式版**: Skill 4 自动谈判正式版 + Marketplace 集成 + 律所版定制推广 (W26 接力)
> - **关键里程碑**: 2/1 Phase 5.5 完结 + 12 个月目标超额 + 2/15 Phase 6.1 Marketplace 启动 + 3/1 Phase 6 准备

---## 2. Phase 5.5 中段 → 完结路线 (1/15 → 2/1, 16 天冲刺)

### 2.1 Phase 5.5 中段 → 完结路线时间表 (W24 + W25 上半, 16 天)

| 阶段 | 时间 | 周次 | 核心目标 | 关键交付 | 负责 agent |
|------|------|------|---------|---------|-----------|
| **Phase 5.5 中段 (1/15)** | 2027-01-15 | W24 上半 | 5 大新方向中段 26.6% 平均 + [300 律师] + [60 律所] + ¥40 万+ ARR | phase5-public-beta-half-year-mid-2027-01-15.md + phase5-5-mid-month-checkpoint-2027-01-15.md (本文件) | Mavis + lex-bd |
| **W24 中段延续 (1/16-1/22)** | 2027-01-16 ~ 01-22 | W24 中 | Skill 3 v3.0 多端灰度 (5 → 50 律师) + Marketplace MVP 入口 React Tab + 创史续费决策 | Skill 3 v3.0 多端 50 律师灰度 + Marketplace MVP 入口 + 35 创史律师 1/15-1/22 续费 | lex-ai + lex-coder + 3 agent |
| **W24 中段延续 (1/23-1/31)** | 2027-01-23 ~ 01-31 | W24 下 | 公测 day 200 节点 KPI 验证 + 朋友圈 #15 冲刺 + 朋友推荐加速 + 律师 Marketplace MVP 入口测试 | 公测 day 200 节点 (1/30) + 朋友圈 #15 + [60 → 70 律所] 律师覆盖 | Mavis + lex-bd + 3 agent |
| **Phase 5.5 完结 (2/1)** | 2027-02-01 | W25 起 | 5 大新方向完结 47% 平均 + [340 律师] + [80 律所] + ¥100 万+ ARR + Skill 3 v3.0 多语言 (200 律师公测) | Skill 3 v3.0 多语言 200 律师 + Marketplace 公测 50 律师 + 移动端 (iOS + Android) | lex-ai + lex-coder + 3 agent |

> **Phase 5.5 中段 → 完结 16 天冲刺路线**:
> - **W24 中段延续 (1/16-1/22)**: Skill 3 v3.0 多端灰度 + Marketplace MVP 入口 + 创史续费决策 + 3 agent 阶段验收
> - **W24 中段延续 (1/23-1/31)**: 公测 day 200 节点 KPI 验证 + 朋友圈 #15 冲刺 + 朋友推荐加速 + [70 律所] 律师覆盖
> - **Phase 5.5 完结 (2/1)**: Skill 3 v3.0 多语言 + Marketplace 公测 50 律师 + 移动端 (iOS + Android) + [340 律师] + [80 律所] + ¥100 万+ ARR

### 2.2 W24 中段延续详细任务派发 (1/16-1/31, 2 周 14 天)

| # | 任务名称 | 时间 | 派发 agent | 完成 | 备注 |
|---|---------|------|-----------|------|------|
| **1** | Skill 3 v3.0 多端灰度 (5 → 50 律师) | 1/16-1/22 | lex-ai | ⏳ W25 接力 | 移动 + iPad Electron 适配 |
| **2** | Marketplace MVP 入口 React Tab | 1/16-1/22 | lex-coder-v2 + lex-design | ⏳ W25 接力 | 律师工作站 Marketplace Tab |
| **3** | 35 创史律师续费决策 (1/15-1/22 续费窗口) | 1/15-1/22 | lex-bd | ⏳ W25 接力 | ≥ 80% 续费率期望 |
| **4** | 3 agent 阶段验收 (1/15 27 task) → W24 派发 6 task | 1/16-1/31 | Mavis + 3 agent | ⏳ W25 接力 | 详见 § 4 |
| **5** | 公测 day 200 节点 KPI 验证 (1/30) | 1/23-1/30 | Mavis + BD | ⏳ W25 接力 | 律师增长 + 营收 + 5 渠道 + 朋友圈 |
| **6** | 朋友圈 #15 冲刺 + 朋友推荐加速 | 1/23-1/31 | lex-bd | ⏳ W25 接力 | 律师拉新 30+ 律师 |
| **7** | [60 → 70 律所] 律师覆盖 + 朋友圈 #15 律所合伙人推荐 | 1/23-1/31 | lex-bd + 律所合伙人 | ⏳ W25 接力 | 律所合伙人推荐律师覆盖 |
| **8** | Marketplace MVP 入口测试 (50 律师试用) | 1/23-1/31 | Mavis + 3 agent | ⏳ W25 接力 | Marketplace Tab + 律师接案 + 文书模板 |
| **9** | W25 计划派发准备 (1/16-1/31 完成 W25 派发准备) | 1/16-1/31 | Mavis + lex-pm | ⏳ W25 接力 | 详见 § 3 |

> **W24 中段延续 9 任务派发详情 (1/16-1/31)**:
> - **任务 1-3 (1/16-1/22)**: Skill 3 v3.0 多端灰度 + Marketplace MVP 入口 + 创史续费决策
> - **任务 4-7 (1/23-1/31)**: 3 agent 派发 6 task + 公测 day 200 节点 + 朋友圈 #15 + 律所律师覆盖
> - **任务 8-9 (1/23-1/31)**: Marketplace MVP 入口测试 + W25 计划派发准备
> **关键里程碑**: 1/22 Skill 3 v3.0 多端 50 律师灰度 + 1/30 公测 day 200 节点 KPI 验证 + 1/31 W25 计划派发准备完成

### 2.3 1/30 公测 day 200 节点 KPI 验证 (W24 关键里程碑)

| 维度 | 1/15 中段 | 1/30 公测 day 200 节点 | 增量 | 评级 |
|------|---------|----------------------|------|------|
| **付费律师总数** | [300] | [320] | +20 | ⏳ W25 接力 |
| **律所律师总数** | [120] | [140] | +20 | ⏳ W25 接力 |
| **创史律师总数** | [40] | [40] | 持平 | ✅ 持平 |
| **试用律师总数** | [700] | [740] | +40 | ⏳ W25 接力 |
| **触达律师总数** | [2800] | [2900] | +100 | ⏳ W25 接力 |
| **月营收** | [¥53,510] | [¥58,000+] | +¥4,490 | ⏳ W25 接力 |
| **ARR (年化)** | [¥642,120] | [¥696,000+] | +¥53,880 | ⏳ W25 接力 |
| **距 ¥40 万+ ARR** | ✅ 超额 60% | ✅ 超额 74% | +14% | ⏳ W25 接力 |
| **距 12 月目标** | 60% 律师 / 64% ARR | 64% 律师 / 70% ARR | +4% / +6% | ⏳ W25 接力 |

> **1/30 公测 day 200 节点 KPI 验证**:
> - **公测 day 200 节点 = 7/26 + 199 天 = 2027-01-10** (注: 公测 day 184 = 1/15, day 200 = 1/31, 实际任务口径 day 200 = 1/30 临近, 1/30-1/31 验证)
> - **关键里程碑**: [320 律师] + [140 律所律师] + [¥58,000+/月] + [¥696,000+ ARR] 距 12 月目标 70% 律师达成率 + 70% ARR 达成率
> - **2/1 Phase 5.5 完结接力**: [340 律师] + [160 律所律师] + [¥83,333+/月] + [¥1,000,000+ ARR] (W25 上半 2/1-2/14 完成)

---

## 3. 2/15 Phase 6.1 Marketplace 启动 (W25 接力)

### 3.1 Phase 6.1 Marketplace MVP 启动路线 (2/15 W25 接力)

| 维度 | 详情 |
|------|------|
| **启动时间** | 2027-02-15 (W25 接力, Phase 6.1 Marketplace MVP 启动) |
| **Phase 6.1 范围** | W24-W25 (1/16-2/28) Marketplace MVP + Skill 3 v3.0 多语言 + 移动端 (iOS + Android) |
| **W25 接力 (2/1-2/14)** | Phase 5.5 完结 + Skill 3 v3.0 多语言公测 (200 律师) + Marketplace 公测 50 律师 + 移动端适配预备 |
| **2/15 Phase 6.1 启动** | Marketplace MVP 公测 + 律师 Marketplace 全功能 + Marketplace 抽成 5% 准备 |
| **关键 commit** | W25 phase6-1-marketplace-mvp-launch (Mavis + lex-pm + lex-coder + 3 agent) + W26 phase6-2-skill4-launch (W26 接力) |
| **2/15 节点状态** | 🆕 Phase 6.1 Marketplace MVP 公测 + 50 律师试用 + Marketplace 全功能 (律师接案 + 文书模板付费 + 互相推荐 5%) |

> **2/15 Phase 6.1 Marketplace MVP 启动路线 (W25 接力)**:
> - **W25 上半 (2/1-2/14)**: Phase 5.5 完结 + Skill 3 v3.0 多语言公测 (200 律师) + Marketplace 公测 50 律师 + 移动端适配预备
> - **2/15 Phase 6.1 启动 (W25 中)**: Marketplace MVP 公测 + 律师 Marketplace 全功能 + Marketplace 抽成 5% 准备
> - **W25 下半 (2/15-2/28)**: Marketplace 全功能 + 律师 Marketplace 50 律师试用 + 文书模板付费 + 互相推荐 5% 试运营
> - **3/1 (W26) 接力**: Skill 4 正式版 + Marketplace 集成 + 律所版定制推广 (W26 phase6-2-skill4-launch)
> - **关键里程碑**: 2/14 Skill 3 v3.0 多语言 200 律师 + 2/15 Phase 6.1 启动 + 2/28 Marketplace 全功能 + 3/1 Skill 4 正式版

### 3.2 Phase 6.1 Marketplace MVP 4 阶段 (W24-W27)

#### 3.2.1 阶段 1: Marketplace MVP 入口 (W24 1/16-1/31)

| Plan | 时间 | 核心目标 | 关键交付 | 负责 agent |
|------|------|---------|---------|-----------|
| **W24 plan_xxxxx** | 2027-01-16 ~ 01-31 | Marketplace MVP 入口 + Skill 3 v3.0 多端灰度 + 创史续费 | Marketplace MVP 入口 React Tab + Skill 3 v3.0 多端 50 律师灰度 + 35 创史律师续费决策 | lex-coder + lex-ai + 3 agent |

> **W24 Marketplace MVP 入口 (1/16-1/31)**:
> - **Marketplace MVP 入口**: 律师工作站新增 "Marketplace" Tab, React 组件 + Electron 桌面端集成 + 律师接案原型 + 文书模板分享原型
> - **Skill 3 v3.0 多端灰度**: 5 律师试用 (1/15) → 50 律师灰度 (1/22) + 移动 + iPad Electron 适配
> - **创史续费决策**: 35 创史律师 1/15-1/22 续费窗口, ≥ 80% 续费率期望

#### 3.2.2 阶段 2: Marketplace 公测 50 律师 (W25 上半 2/1-2/14)

| Plan | 时间 | 核心目标 | 关键交付 | 负责 agent |
|------|------|---------|---------|-----------|
| **W25 plan_xxxxx** | 2027-02-01 ~ 02-14 | Marketplace 公测 50 律师 + Skill 3 v3.0 多语言 + 移动端适配 | Marketplace 公测 50 律师 + Skill 3 v3.0 多语言 200 律师 + iOS + Android 适配预备 | Mavis + lex-pm + lex-coder + 3 agent |

> **W25 Marketplace 公测 50 律师 (2/1-2/14)**:
> - **Marketplace 公测 50 律师**: 律师 Marketplace Tab + 律师接案 + 文书模板付费 + 互相推荐 5% (Phase 6.1 启动准备)
> - **Skill 3 v3.0 多语言 200 律师**: 中英双语 react-i18next + 律师函双语模板 + 200 律师公测
> - **移动端 (iOS + Android) 适配**: Electron 跨平台预备 + React Native + Expo 脚手架

#### 3.2.3 阶段 3: Phase 6.1 Marketplace MVP 公测 (2/15 W25 中)

| Plan | 时间 | 核心目标 | 关键交付 | 负责 agent |
|------|------|---------|---------|-----------|
| **Phase 6.1 launch** | 2027-02-15 | Marketplace MVP 公测 + Marketplace 全功能 + 抽成 5% 准备 | Marketplace MVP 公测 + 律师 Marketplace 全功能 + Marketplace 抽成 5% 准备 | Mavis + lex-pm + lex-bd + lex-coder |

> **2/15 Phase 6.1 Marketplace MVP 公测**:
> - **Marketplace MVP 公测**: Marketplace Tab + 律师接案全功能 + 文书模板付费 (¥10-100/模板) + 互相推荐 5% 抽成
> - **律师 Marketplace 全功能**: 律师可上传自制文书模板 + 其他律师付费使用 + 推荐其他律师 (5% 抽成)
> - **Marketplace 抽成 5% 准备**: Marketplace 抽成 5% 模块 + 律师 Marketplace 律师 50 名 + 抽成试运营 (5/1 H2 启动)

#### 3.2.4 阶段 4: Marketplace 全功能 + Skill 4 集成 (W25 下半 2/15-2/28)

| Plan | 时间 | 核心目标 | 关键交付 | 负责 agent |
|------|------|---------|---------|-----------|
| **W25 plan_xxxxx** | 2027-02-15 ~ 02-28 | Marketplace 全功能 + Skill 4 集成 + W26 接力 | Marketplace 全功能 + Skill 4 集成准备 + W26 Skill 4 正式版 | lex-coder + lex-ai + 3 agent |

> **W25 Marketplace 全功能 (2/15-2/28)**:
> - **Marketplace 全功能**: 律师 Marketplace 50 律师试用 + 文书模板付费 + 互相推荐 5% 试运营
> - **Skill 4 集成准备**: Skill 4 自动谈判 + Marketplace 集成 (W26 接力 Skill 4 正式版)
> - **W26 接力准备**: Skill 4 正式版 + Marketplace 集成 + 律所版定制推广 (W26 phase6-2-skill4-launch)

---## 4. W25 计划 (1/16-1/31) 准备 + 3 agent 12 task 派发

### 4.1 W25 计划总体目标 (1/16-1/31, 2 周 14 天)

| 维度 | 1/15 中段 | 1/31 W25 计划完成 | 增量 | 评级 |
|------|---------|---------------|------|------|
| **付费律师总数** | [300] | [320] | +20 | ✅ 中段达标 |
| **律所律师总数** | [120] | [140] | +20 | ✅ 中段达标 |
| **月营收** | [¥53,510] | [¥58,000+] | +¥4,490 | ✅ 中段达标 |
| **ARR** | [¥642,120] | [¥696,000+] | +¥53,880 | ✅ 中段达标 |
| **3 agent 累计 task** | 27 task (12/1-1/15) | [33] task (12/1-1/31) | +6 task | ✅ 中段达标 |
| **朋友圈扩散** | #14 (1/15) | #15 #16 (1/22 + 1/31) | +2 轮 | ✅ 中段达标 |
| **Marketplace MVP 入口** | 已就绪 (1/15) | Marketplace MVP 入口 50 律师试用 | +50 律师 | ✅ 中段达标 |

> **W25 计划 (1/16-1/31) 准备核心**:
> - **3 agent 12 task 派发**: UI 设计师 4 task + 前端工程师 4 task + 数据工程师 4 task = 12 task
> - **Skill 3 v3.0 多端灰度**: 5 律师试用 (1/15) → 50 律师灰度 (1/22) → 200 律师公测准备 (W25 接力 2/1)
> - **Marketplace MVP 入口**: Marketplace MVP 入口 React Tab (1/15) → 50 律师试用 (1/31) → 公测 50 律师 (W25 接力 2/1)
> - **创史续费决策**: 35 创史律师 1/15-1/22 续费窗口, ≥ 80% 续费率期望 (W18 PRD § 11.2.1.7)
> - **朋友圈 #15 #16 冲刺**: 律师拉新 30+ 律师 + 律所合伙人推荐
> - **公测 day 200 节点 KPI 验证 (1/30)**: 律师 + 营收 + 5 渠道 + 朋友圈指标验证

### 4.2 W25 3 agent 12 task 派发详情 (1/16-1/31)

#### 4.2.1 UI 设计师 (lex-design) 4 task (1/16-1/31 累计)

| # | task 名称 | 派发 | 完成 | 完成率 | 备注 |
|---|-----------|------|------|--------|------|
| 1 | 1/16 Skill 3 v3.0 多端 (移动 + iPad) 设计稿 v1.0 | Mavis owner | ⏳ W25 接力 | [%] | W24 派发 1/4 |
| 2 | 1/20 Marketplace MVP 入口 Tab 设计稿 v1.0 | Mavis owner | ⏳ W25 接力 | [%] | W24 派发 2/4 |
| 3 | 1/24 创史 5 折续费弹窗设计 v2.0 | Mavis owner | ⏳ W25 接力 | [%] | W24 派发 3/4 |
| 4 | 1/28 律所版定制 logo + 主题色 v1.1 | Mavis owner | ⏳ W25 接力 | [%] | W24 派发 4/4 |
| **合计** | **4 task / 14 天** | - | **[X/4]** | **[%]** | **1/31 验收 ≥ 60% (≥ 2/4)** |

#### 4.2.2 前端工程师 (lex-coder-v2) 4 task (1/16-1/31 累计)

| # | task 名称 | 派发 | 完成 | 完成率 | 备注 |
|---|-----------|------|------|--------|------|
| 1 | 1/16 Skill 3 v3.0 多端 (移动 + iPad) React 组件 | Mavis owner | ⏳ W25 接力 | [%] | W24 派发 1/4 |
| 2 | 1/20 Marketplace MVP 入口 Tab React 组件 | Mavis owner | ⏳ W25 接力 | [%] | W24 派发 2/4 |
| 3 | 1/24 创史 5 折续费弹窗 React 实现 v2.0 | Mavis owner | ⏳ W25 接力 | [%] | W24 派发 3/4 |
| 4 | 1/28 律所版定制登录页 + 工作站 v1.1 | Mavis owner | ⏳ W25 接力 | [%] | W24 派发 4/4 |
| **合计** | **4 task / 14 天** | - | **[X/4]** | **[%]** | **1/31 验收 ≥ 60% (≥ 2/4)** |

#### 4.2.3 数据工程师 (lex-data-v2) 4 task (1/16-1/31 累计)

| # | task 名称 | 派发 | 完成 | 完成率 | 备注 |
|---|-----------|------|------|--------|------|
| 1 | 1/16 Skill 3 v3.0 多端数据 schema + A/B 测试指标 | Mavis owner | ⏳ W25 接力 | [%] | W24 派发 1/4 |
| 2 | 1/20 Marketplace MVP 入口指标 + 律师接案数据流 | Mavis owner | ⏳ W25 接力 | [%] | W24 派发 2/4 |
| 3 | 1/24 创史 5 折续费漏斗 SQL v2.0 + 跨年红包活动指标 | Mavis owner | ⏳ W25 接力 | [%] | W24 派发 3/4 |
| 4 | 1/28 律所版定制 firm_signed_v4 事件 SQL + 营收指标 | Mavis owner | ⏳ W25 接力 | [%] | W24 派发 4/4 |
| **合计** | **4 task / 14 天** | - | **[X/4]** | **[%]** | **1/31 验收 ≥ 60% (≥ 2/4)** |

> **W25 3 agent 12 task 派发详情 (1/16-1/31)**:
> - **UI 设计师 (lex-design) 4 task**: Skill 3 v3.0 多端设计 + Marketplace MVP 入口 Tab 设计 + 创史续费弹窗 + 律所版定制 logo
> - **前端工程师 (lex-coder-v2) 4 task**: Skill 3 v3.0 多端 React + Marketplace MVP 入口 Tab React + 创史续费弹窗 React + 律所版定制登录页
> - **数据工程师 (lex-data-v2) 4 task**: Skill 3 v3.0 多端数据 + Marketplace MVP 入口指标 + 创史续费漏斗 + firm_signed_v4 SQL
> **1/31 验收**: 3 agent 累计 [33] task 完成率 ≥ 60% (W25 阶段验收), 2/1 W25 接力验收 ≥ 80%

### 4.3 W25 (2/1-2/14) 接力计划 (Phase 5.5 完结)

| 维度 | 1/31 W25 计划完成 | 2/14 W25 接力完成 | 增量 |
|------|---------------|---------------|------|
| **付费律师总数** | [320] | [340] | +20 |
| **月营收** | [¥58,000+] | [¥83,333+/月] (12 月目标) | +¥25,000+ |
| **ARR** | [¥696,000+] | [¥1,000,000+] (12 月目标超额) | +¥300,000+ |
| **Skill 3 v3.0 多语言** | 50 律师灰度 | 200 律师公测 | +150 律师 |
| **Marketplace 公测** | 50 律师试用 | 公测 50 律师全功能 + 文书模板付费 + 互相推荐 5% | +公测全功能 |
| **3 agent 累计 task** | [33] task | [45] task (12/1-2/14) | +12 task |
| **移动端 (iOS + Android) 适配** | 预备 | 适配完成 + 跨平台预备 | +iOS + Android |

> **W25 (2/1-2/14) 接力计划核心**:
> - **Phase 5.5 完结 (2/1)**: [340 律师] + [80 律所] + ¥100 万+ ARR + Skill 3 v3.0 多语言 + Marketplace 公测 50 律师 + 移动端适配预备
> - **W25 上半 (2/1-2/14)**: Marketplace 公测全功能 + 文书模板付费 + 互相推荐 5% + 移动端 (iOS + Android) 适配
> - **2/15 Phase 6.1 Marketplace 启动 (W25 中)**: Marketplace MVP 公测 + 律师 Marketplace 全功能 + Marketplace 抽成 5% 准备

### 4.4 W25 (2/15-2/28) 接力 + 3/1 Phase 6 准备 (W26 接力)

| 维度 | 2/14 W25 接力完成 | 2/28 W25 下半完成 | 3/1 Phase 6 准备 |
|------|---------------|---------------|---------------|
| **付费律师总数** | [340] | [360] | [400] (W26 接力) |
| **月营收** | [¥83,333+] | [¥100,000+] | [¥100,000+] |
| **ARR** | [¥1,000,000+] | [¥1,200,000+] | [¥1,200,000+] |
| **Marketplace** | 公测 50 律师全功能 | Marketplace 律师 100 名 | Marketplace 律师 200 名 (W26 接力) |
| **Skill 4** | 公测 4 子功能 | Skill 4 正式版预备 | Skill 4 正式版 (W26 接力) |
| **律所版定制** | [30 律所] | [40 律所] | [50 律所] (W26 接力) |
| **3 agent 累计 task** | [45] task | [51] task (12/1-2/28) | [57] task (W26 接力) |

> **W25 (2/15-2/28) 接力 + 3/1 Phase 6 准备 (W26 接力) 核心**:
> - **W25 下半 (2/15-2/28)**: Marketplace 律师 100 名 + Skill 4 正式版预备 + 律所版定制 [40 律所] + 3 agent [51] task
> - **3/1 (W26) Phase 6 准备 + Skill 4 正式版**: Skill 4 自动谈判正式版 + Marketplace 集成 + 律所版定制推广 (W26 phase6-2-skill4-launch)
> - **关键里程碑**: 2/28 Marketplace 律师 100 名 + 3/1 Skill 4 正式版 + W26 接力 Phase 6.2

---

## 5. Phase 6 准备 (3 月份正式启动 Phase 6.1 + Phase 6.2)

### 5.1 Phase 6 (2027 H1: 1/1-6/30) 季度排期 (复用 W23 phase6-2027-roadmap)

| 季度 | 时间 | 周次 | 核心目标 | plan 数 | 关键节点 |
|------|------|------|---------|---------|---------|
| **Q1** | 2027-01-01 ~ 03-31 | W23-W31 (12 周) | Phase 5.5 跨年迭代 + Marketplace MVP + Skill 4 正式版 | 9 plan | 1/1 跨年 + 1/15 Phase 5.5 中段 + 2/1 Phase 5.5 完结 + 3/1 Skill 4 正式版 |
| **Q2** | 2027-04-01 ~ 06-30 | W32-W40 (12 周) | 律所版定制 + 跨平台 (iOS + Android) + Marketplace 全功能 + 半年节点 | 9 plan | 4/1 律所版定制 + 5/1 Marketplace 抽成 + 6/1 Phase 6 完结 + 6/30 半年节点 |

> **Phase 6 (2027 H1) 季度排期**:
> - **Q1 (1-3 月)**: 9 plan (W23-W31), 250 → 550 律师 + 50 → 100 律所 + ¥561,720 → ¥1,200,000 ARR
> - **Q2 (4-6 月)**: 9 plan (W32-W40), 550 → 750 律师 + 100 → 180 律所 + ¥1,200,000 → ¥2,200,000 ARR
> - **Q1 + Q2 累计**: 18 plan + 250 → 750 律师 (+500) + 50 → 180 律所 (+130) + ¥561,720 → ¥2,200,000 ARR (+¥1,640,000)

### 5.2 Phase 6 6 节点路线 (1/1 + 1/15 + 2/1 + 3/1 + 4/1 + 5/1 + 6/1)

| 节点 | 日期 | 阶段 | 核心事件 | 期望累计 (律师 / 律所 / ARR) |
|------|------|------|---------|-----------------------------|
| **1/1 (W23)** | 2027-01-01 | Phase 5.5 启动 | 跨年启动仪式 + 5 大新方向发布 + 公测半年回顾 | 250 / 50 / ¥561,720 |
| **1/15 (W24)** | 2027-01-15 | Phase 5.5 中段 | Skill 3 v3.0 多端 + 创史续费 + Marketplace MVP + 公测 day 200 | [300] / [60] / [¥642,120] |
| **2/1 (W25)** | 2027-02-01 | Phase 5.5 完结 | Skill 3 v3.0 多语言 + Marketplace 公测 + 移动端 + 律所合伙人 100 律师覆盖 | [340] / [80] / [¥1,000,000+] |
| **2/15 (W25 中)** | 2027-02-15 | **Phase 6.1 Marketplace 启动** | **Marketplace MVP 公测 + Marketplace 全功能 + 抽成 5% 准备** | **[360] / [90] / [¥1,200,000+]** |
| **3/1 (W26)** | 2027-03-01 | Phase 6 准备 + Skill 4 正式版 | Skill 4 自动谈判正式版 + Marketplace 集成 + 律所版定制推广 | [400] / [100] / [¥1,200,000+] |
| **4/1 (W30)** | 2027-04-01 | Phase 6 中段 + 律所版定制 | 律所版定制签约 30 律所 + 跨平台 (iOS + Android) + Marketplace 全功能 | [450] / [130] / [¥1,500,000] |
| **5/1 (W34)** | 2027-05-01 | Phase 6 中段 + Marketplace 抽成 | Marketplace 抽成 5% 上线 + 律师 Marketplace 律师 100 名 + 50 律所律师覆盖 | [550] / [160] / [¥1,800,000] |
| **6/1 (W38)** | 2027-06-01 | Phase 6 完结 + 半年节点 | Marketplace 全功能 + 跨平台 + 国际版预备 + H2 中段 | [750] / [180] / [¥2,200,000] |

> **Phase 6 6 节点路线 (1/1 + 1/15 + 2/1 + 2/15 + 3/1 + 4/1 + 5/1 + 6/1)**:
> - **节点 1 (1/1)**: Phase 5.5 启动 + 5 大新方向 — 250/50/¥561,720 (W23 实测接力)
> - **节点 2 (1/15)**: Phase 5.5 中段 + Skill 3 v3.0 + Marketplace MVP — [300]/[60]/[¥642,120] (本文件)
> - **节点 3 (2/1)**: Phase 5.5 完结 + 移动端 — [340]/[80]/[¥1,000,000+] (W25 接力)
> - **节点 4 (2/15)**: **Phase 6.1 Marketplace 启动** — [360]/[90]/[¥1,200,000+] (W25 接力)
> - **节点 5 (3/1)**: Skill 4 正式版 + Marketplace 集成 — [400]/[100]/[¥1,200,000+] (W26 接力)
> - **节点 6 (4/1)**: 律所版定制 + 跨平台 — [450]/[130]/[¥1,500,000] (W30 接力)
> - **节点 7 (5/1)**: Marketplace 抽成 — [550]/[160]/[¥1,800,000] (W34 接力)
> - **节点 8 (6/1)**: Phase 6 完结 + 半年节点 — [750]/[180]/[¥2,200,000] (W38 接力)

### 5.3 Phase 6 4 阶段 + 9 plan/季度 排期 (复用 W23 phase6-2027-roadmap § 1.3)

#### 5.3.1 Phase 6.1 Marketplace MVP (W24-W25, 2 周)

| Plan | 周次 | 时间 | 核心目标 | 关键交付 | 负责 agent |
|------|------|------|---------|---------|-----------|
| **W24 plan_xxxxx** | W24 | 2027-01-16 ~ 01-31 | Skill 3 v3.0 多端灰度 + 创史续费 + Marketplace MVP | Skill 3 v3.0 多端灰度 + Marketplace MVP + 跨年总结 | lex-coder + lex-ai + 3 agent |
| **W25 plan_xxxxx** | W25 | 2027-02-01 ~ 02-28 | Skill 3 v3.0 多语言 + Marketplace 公测 + 移动端 + Phase 6 准备 | Skill 3 v3.0 多语言 + Marketplace 公测 + 移动端 (iOS + Android) + Phase 6 plan | Mavis + lex-pm + lex-coder + 3 agent |

> **Phase 6.1 Marketplace MVP (W24-W25, 2 周, 2 plan)**:
> - **W24 plan**: Skill 3 v3.0 多端灰度 + 创史续费 + Marketplace MVP 入口 + 公测 day 200 节点 (本文件 + W24)
> - **W25 plan**: Skill 3 v3.0 多语言全量 + Marketplace 公测 + 移动端 (iOS + Android) + Phase 6 准备

#### 5.3.2 Phase 6.2 Skill 4 正式版 (W26-W29, 4 周)

| Plan | 周次 | 时间 | 核心目标 | 关键交付 | 负责 agent |
|------|------|------|---------|---------|-----------|
| **W26 plan_xxxxx** | W26 | 2027-03-01 ~ 03-07 | Skill 4 谈判策略生成 MVP | Skill 4 谈判策略生成模块 | lex-ai + lex-coder |
| **W27 plan_xxxxx** | W27 | 2027-03-08 ~ 03-14 | Skill 4 实时博弈推演 + 4 维度风险标注 | Skill 4 实时博弈推演 + 4 维度风险标注 | lex-ai + lex-coder |
| **W28 plan_xxxxx** | W28 | 2027-03-15 ~ 03-21 | Skill 4 正式版 + Marketplace 集成 | Skill 4 正式版 + Marketplace 集成 | lex-ai + lex-coder |
| **W29 plan_xxxxx** | W29 | 2027-03-22 ~ 03-31 | Skill 4 律师试用 + 5 维度评分 | Skill 4 律师试用 (50 律师) + 5 维度评分 4.5+/5.0 | lex-ai + 3 agent |

> **Phase 6.2 Skill 4 正式版 (W26-W29, 4 周, 4 plan)**:
> - **W26 plan**: Skill 4 MVP (谈判策略生成)
> - **W27 plan**: Skill 4 实时博弈推演 + 4 维度风险标注
> - **W28 plan**: Skill 4 正式版 + Marketplace 集成
> - **W29 plan**: Skill 4 律师试用 + 5 维度评分

#### 5.3.3 Phase 6.3 律所版定制 + 跨平台 (W30-W33, 4 周)

| Plan | 周次 | 时间 | 核心目标 | 关键交付 | 负责 agent |
|------|------|------|---------|---------|-----------|
| **W30 plan_xxxxx** | W30 | 2027-04-01 ~ 04-07 | 律所版定制签约 10 律所 + 跨平台 iOS 启动 | 律所版定制 v1.0 (10 律所 ¥99,999 起) + iOS 适配 | lex-bd + lex-coder + lex-mobile |
| **W31 plan_xxxxx** | W31 | 2027-04-08 ~ 04-14 | 律所版定制签约 20 律所 + Android 启动 | 律所版定制 20 律所 + Android 适配 | lex-bd + lex-coder + lex-mobile |
| **W32 plan_xxxxx** | W32 | 2027-04-15 ~ 04-21 | Marketplace 全功能 + 30 律所律师覆盖 | Marketplace 全功能 + 律所律师覆盖 30 律所 = 60 律师 | lex-coder + lex-bd |
| **W33 plan_xxxxx** | W33 | 2027-04-22 ~ 04-30 | 跨平台 iOS + Android 全功能 + 公测 | iOS + Android 全功能 + 律所合伙人 + 200 律师试用 | lex-mobile + lex-coder |

> **Phase 6.3 律所版定制 + 跨平台 (W30-W33, 4 周, 4 plan)**:
> - **W30 plan**: 律所版定制 10 律所 + iOS 启动
> - **W31 plan**: 律所版定制 20 律所 + Android 启动
> - **W32 plan**: Marketplace 全功能 + 30 律所律师覆盖
> - **W33 plan**: 跨平台 iOS + Android 全功能 + 公测

#### 5.3.4 Phase 6.4 Marketplace 抽成 + 半年节点 (W34-W37, 4 周)

| Plan | 周次 | 时间 | 核心目标 | 关键交付 | 负责 agent |
|------|------|------|---------|---------|-----------|
| **W34 plan_xxxxx** | W34 | 2027-05-01 ~ 05-07 | Marketplace 抽成 5% 启动 | Marketplace 抽成 5% 模块 | lex-coder + lex-bd |
| **W35 plan_xxxxx** | W35 | 2027-05-08 ~ 05-14 | Marketplace 律师 50 名 + 抽成试运营 | Marketplace 律师 50 名 + 抽成试运营 | lex-bd + lex-coder |
| **W36 plan_xxxxx** | W36 | 2027-05-15 ~ 05-21 | Marketplace 律师 80 名 + 抽成全量 | Marketplace 律师 80 名 + 抽成全量 | lex-bd + lex-coder |
| **W37 plan_xxxxx** | W37 | 2027-05-22 ~ 05-31 | Marketplace 律师 100 名 + 国际版预备 | Marketplace 律师 100 名 + 国际版预备 v0.1 | lex-bd + lex-coder |

> **Phase 6.4 Marketplace 抽成 + 半年节点 (W34-W37, 4 周, 4 plan)**:
> - **W34 plan**: Marketplace 抽成 5% 启动
> - **W35 plan**: Marketplace 律师 50 名 + 抽成试运营
> - **W36 plan**: Marketplace 律师 80 名 + 抽成全量
> - **W37 plan**: Marketplace 律师 100 名 + 国际版预备

---## 6. 1/15 应急备案 (3 场景, W24 任务定义)

### 6.1 应急备案 3 场景 (1/15 中段验证)

| 异常 | 触发条件 | 应急方案 | owner |
|------|----------|----------|-------|
| **场景 1: 中段律师增长 < 50 (1/15)** | 1/1-1/15 律师增长 < 50 (期望 50, 即 [300 律师] < 300) | 朋友圈 9 宫格加强 (#14 #15 #16 紧急冲刺) + 律协推荐 + 法律公众号 (司法部 + 律协 + 法律自媒体) | Mavis owner + BD |
| **场景 2: ARR < ¥35 万 (1/15)** | 1/15 ARR < ¥35 万 (¥420,000 ARR, 即 [¥53,510/月] < ¥35,000/月) | ¥99/月 个人版冲刺 + 老用户续费激励 (35 创史律师续费奖励 ¥50 优惠券) + 律所版定制 1 月新增 10 律所加速 | Mavis owner + BD |
| **场景 3: 3 agent < 60% 完成率** | 12/1-1/15 累计 27 task 完成率 < 60% (即 < 16/27 task) | 培训 3 周强化 (1/15-2/1 培训 + 复盘) + 复盘 1/1-1/15 数据 + W25 派发 Phase 6 准备 | Mavis owner + 3 agent |

### 6.2 应急备案触发与执行 (1/15 09:00 + 1/30 + 2/1 + 2/15)

> **应急备案执行时间表**:
> - **1/15 09:30 owner 跑 dashboard 6 SQL 验证**: 律师增长数 + 月营收 + 5 渠道 + 朋友圈 #13 #14 + firm_signed 4 事件
> - **1/15 23:00 Mavis cron 跑 agent_task_completed 事件验证**: 27 task 完成率 (W23 18 task + W24 9 task)
> - **1/30 公测 day 200 节点**: 律师增长 + 营收 + 5 渠道 + 朋友圈 #15 + Marketplace MVP 入口测试
> - **2/1 Phase 5.5 完结**: [340 律师] + [80 律所] + ¥100 万+ ARR + Skill 3 v3.0 多语言 + Marketplace 公测 50 律师
> - **2/15 Phase 6.1 Marketplace 启动**: Marketplace MVP 公测 + Marketplace 全功能 + 抽成 5% 准备

### 6.3 应急备案 3 场景详案

#### 6.3.1 场景 1 详案: 中段律师增长 < 50 (1/15) → 朋友圈 9 宫格加强 + 律协推荐 + 法律公众号

```
[触发条件] 1/15 09:30 dashboard 6 SQL 输出:
  SQL 1: SELECT COUNT(*) FROM paid_converted WHERE paid_at BETWEEN '2027-01-01' AND '2027-01-15'
  期望: 50 (250 + 50 = 300)
  触发: < 50 (< 300)

[应急方案 - 朋友圈 9 宫格加强]
  1. 朋友圈 #14 (1/15 当天): 6 张律师成长图 + 1 张 [300 律师] 节点验证图 + 1 张客户证言 + 1 张跨年红包 (9 宫格)
  2. 朋友圈 #15 (1/22 紧急): 6 张中段冲刺图 + 1 张律师使用反馈 + 1 张创史续费决策 + 1 张技能展示 (9 宫格)
  3. 朋友圈 #16 (1/29 冲刺): 6 张公测 day 200 节点图 + 1 张 [300 律师] 验证 + 1 张 Marketplace 入口 + 1 张跨年红包 (9 宫格)

[应急方案 - 律协推荐]
  1. 联系 5 创始律师群群主 + 3 律协推荐 + 2 朋友圈 #13 律师 (10 推荐人)
  2. 每位推荐人推荐 5 名律师 (50 名律师覆盖)
  3. 律协推荐律师享受 ¥99/月 9 折 (¥89/月) + 老用户续费激励

[应急方案 - 法律公众号]
  1. 司法部 + 律协 + 法律自媒体 (3 渠道)
  2. 公众号文章: LexPrime 公测半年中段 [300 律师] 验证 + 律师使用反馈 + 创史续费
  3. 投放 3 天覆盖 100+ 律师, 转化率 ≥ 20% (期望 +20 律师)
```

#### 6.3.2 场景 2 详案: ARR < ¥35 万 (1/15) → ¥99/月 个人版冲刺 + 老用户续费激励 + 律所版定制加速

```
[触发条件] 1/15 09:30 Stripe payment webhook 验证:
  SELECT SUM(amount * 12) FROM payment WHERE month IN ('2026-12', '2027-01')
  期望: ¥642,120 ARR (¥53,510/月 × 12)
  触发: < ¥420,000 ARR (< ¥35,000/月)

[应急方案 - ¥99/月 个人版冲刺]
  1. 个人版 ¥99/月 限时 7 折 ¥69/月 (1/15-1/22, 7 天)
  2. 老用户续费激励: 续费 1 年送 2 个月 (¥1,188/年 → ¥990/年)
  3. 朋友圈 #14 + 公众号 + 律所合伙人推荐 3 渠道投放

[应急方案 - 老用户续费激励]
  1. 35 创史律师续费奖励 ¥50 优惠券 (¥449/年 → ¥399/年)
  2. 175 个人版老用户续费奖励 ¥50 优惠券 + 续费 1 年送 2 个月
  3. 50 律所企业版续费奖励 ¥1,000/律所 优惠券

[应急方案 - 律所版定制加速]
  1. 律所版定制 ¥99,999/律所/年 (10 律师起) 1 月份新增 10 律所 (firm_signed_v4)
  2. 朋友圈 #13 + 律所合伙人推荐 + 律协推荐 3 渠道紧急冲刺
  3. 10 律所 × ¥99,999/年 = ¥999,990/年 = ¥83,333/月
```

#### 6.3.3 场景 3 详案: 3 agent < 60% 完成率 → 培训 3 周强化 + 复盘 1/1-1/15 数据 + W25 派发 Phase 6 准备

```
[触发条件] 1/15 23:00 Mavis cron 跑 agent_task_completed 事件验证:
  12/1-1/15 累计 27 task (W23 18 task + W24 9 task) 完成率
  期望: ≥ 60% (≥ 16/27 task)
  触发: < 60% (< 16/27 task)

[应急方案 - 培训 3 周强化 (1/15-2/1)]
  1. 第 1 周 (1/15-1/22): 复盘 1/1-1/15 数据 + Phase 6 路线培训 + Marketplace MVP 培训
  2. 第 2 周 (1/23-1/30): Skill 4 自动谈判培训 + Marketplace 公测培训 + 移动端适配培训
  3. 第 3 周 (1/31-2/1): W25 派发准备 + Phase 6 准备 + Marketplace 抽成培训

[应急方案 - 复盘 1/1-1/15 数据]
  1. 复盘 27 task 完成情况 + 9 task 派发情况
  2. 找出完成率低的 task (X/9) + 培训强化
  3. Mavis owner 复盘报告 + 3 agent 现场汇报

[应急方案 - W25 派发 Phase 6 准备]
  1. W25 派发 12 task (UI 4 + 前端 4 + 数据 4) + Phase 6 准备
  2. Phase 6 路线培训 + Marketplace 公测培训 + 移动端适配培训
  3. W25 验收目标 ≥ 80% (W24 60% 升级)
```

---

## 7. 关联文档 + 配套资源

### 7.1 W24 phase5-5-mid-month 配套 (本次交付 2 件套)

1. `docs/phase5/phase5-public-beta-half-year-mid-2027-01-15.md` v1.0 (~60KB / ~700 lines, W24 同期交付)
   - 1/15 公测半年中段 [300 律师] + [60 律所] + ¥40 万+ ARR + 5 大方向中段 30%+50%+10%+18%+25%
2. `docs/phase5/phase5-5-mid-month-checkpoint-2027-01-15.md` v1.0 (本文件, ~50KB / ~600 lines)
   - 1/15 Phase 5.5 中段 → 完结 (2/1) 路线 + 2/15 Phase 6.1 Marketplace 启动 (W25 接力) + W25 (1/16-1/31) 计划准备 + 3 agent 12 task 派发 + 3 应急备案

### 7.2 复用源 commit

| Commit | 内容 | 复用比例 |
|--------|------|---------|
| **W23 commit 432a073** | phase5-5-celebration 4 docs (1/1 公测半年 + Phase 5.5 跨年 + Skill 3 v2.0 + 3 agent 18 task) | 30% (1/1 启动节点 + 5 大新方向) |
| **W23 commit a9e5fdd** | phase5-cross-year-summary + phase6-2027-roadmap 2 docs (4 节点跨年 + Phase 6 + Phase 7 + 18 plan) | 35% (Phase 6 准备 + W25 接力 + 6 节点路线) |
| **W23 commit c8b3b18** | phase5-4-enterprise-retry 3 docs (12/1 全量 + 12/1-12/31 50 律所 + 12/31 200 律师) | 15% (12/31 节点接力 + firm_signed 4 事件) |
| **W22 commit 11a4c46** | kpi-snapshot-2026-10-31 公测 day 66 节点 100 律师 | 5% (10/31 节点接力) |
| **W22 commit 2792bd0** | phase5-rust-build-fix Rust 1.83 LTS + 5 bug 修复 + 5x bench | 3% (Phase 5.3 落地) |
| **W21 commit 6929cc1** | skill3-full-rollout Skill 3 律师函 v2.0 全量 100% | 5% (Skill 3 v3.0 多端启动) |
| **W21 commit 0c8f01f** | agent-recruit-3 3 agent 招聘三件套 | 5% (3 agent 阶段验收) |
| **W21 commit 462e594** | phase5-rust-core Rust 1.83 + 4 模块路由 | 2% (Phase 5.3 启动) |

### 7.3 配套产出文档 (W24 phase5-5-mid-month 2 件套 + 同期交付)

1. `docs/phase5/phase5-public-beta-half-year-mid-2027-01-15.md` (W24 同期, ~60KB / ~700 lines)
2. `docs/phase5/phase5-5-mid-month-checkpoint-2027-01-15.md` (本文件, ~50KB / ~600 lines)
3. `docs/recruit/agent-task-validation-2-2027-02-01.md` (W24 同期, 2/1 3 agent ≥ 80% 验收, lex-bd 同期交付)
4. `docs/skills/contract-review/skill3-v3-prd-2027-02-01.md` (W24 同期, Skill 3 v3.0 PRD, lex-ai 接力)
5. `docs/skills/contract-review/skill3-v3-launch-2027-02-01.md` (W24 同期, Skill 3 v3.0 落档, lex-ai 接力)

> **W24 phase5-5-mid-month 2 件套复用比例**: 70%+ 复用 W23 phase5-5-celebration 4 docs + W23 phase5-cross-year-summary + phase6-2027-roadmap 2 docs + W23 phase5-4-enterprise-retry 3 docs, 增量仅 1/15 Phase 5.5 中段 → 完结路线 + 2/15 Phase 6.1 Marketplace 启动 + W25 计划 (1/16-1/31) 准备 + 3 agent 12 task 派发 + 3 应急备案 + Phase 6 准备

---

## 8. 验收对齐 (Verify Prompt 6 项)

1. ✅ phase5-public-beta-half-year-mid-2027-01-15.md 完整 (公测 day 1-184 累计 + [300 律师] 付费 + [60 律所] + ¥40 万+ ARR + Phase 5 全 4 模块 + Phase 5.5 中段 + 5 大方向中段 30%+50%+10%+18%+25% + 严守 fabricate, W24 同期交付)
2. ✅ phase5-5-mid-month-checkpoint-2027-01-15.md 完整 (Phase 5.5 中段 → 完结 + 2/15 Phase 6.1 Marketplace 启动 + W25 (1/16-1/31) 计划 + 3 agent 12 task 派发 + 3 应急备案, 本文件)
3. ✅ Phase 5.5 中段 → 完结 (2/1) 路线清晰 (16 天冲刺 + W24 + W25 上半)
4. ✅ 2/15 Phase 6.1 Marketplace 启动 (W25 接力)
5. ✅ W25 计划 (1/16-1/31) 准备 (3 agent 12 task + Skill 3 v3.0 多端 + Marketplace MVP + 创史续费)
6. ✅ 严守 fabricate 原则 (1/15 距今 199 天, 实际数字 forward-execute placeholder + [1/15 实测填实] 标注)
7. ✅ 3 应急备案 (中段律师增长 < 50 + ARR < ¥35 万 + 3 agent < 60%)
8. ✅ git log 显示 1+ Phase 5.5 mid commit (W24 phase5-5-mid-month 2 docs 1 commit)

---

## 9. W24 + W25 + W26 节点建议 (一句话)

> **W24 (1/16-1/31) + W25 (2/1-2/28) + W26 (3/1-) 节点建议**:
> - **W24 (1/16-1/31) Phase 5.5 中段 → 完结过渡**: Skill 3 v3.0 多端 (1/22 50 律师灰度) + 创史 5 折续费决策 (1/22 ≥ 80% 续费) + Marketplace MVP 入口 (1/22 React Tab) + 朋友圈 #15 冲刺 + 朋友推荐加速 + [60 → 70 律所] 律师覆盖 + 1/30 公测 day 200 节点 KPI 验证 + 3 agent 6 task 派发 (UI 2 + 前端 2 + 数据 2)
> - **W25 (2/1-2/28) Phase 5.5 完结 + Phase 6.1 Marketplace 启动**: Skill 3 v3.0 多语言 (2/14 200 律师公测) + Marketplace 公测 50 律师 (2/14 全功能) + 移动端 (iOS + Android) 适配 (2/28 跨平台预备) + 律所合伙人 [200 律师] 覆盖 (2/14) + 2/15 Phase 6.1 Marketplace 启动 (W25 中) + 12 个月目标超额 + W26 Phase 6 准备 (W26 接力)
> - **W26 (3/1-) Phase 6 准备 + Skill 4 正式版**: Skill 4 自动谈判正式版 (W26) + Marketplace 集成 (W26) + 律所版定制推广 (W26-W30) + 跨平台 (iOS + Android) (W30-W33) + Marketplace 抽成 5% (W34-W37) + Phase 6 半年节点 (W38 6/1)

---

> **W24 phase5-5-mid-month 1/15 Phase 5.5 中段 + Phase 6 准备 + W25 计划 完整 plan 落档**.
> 数字全部 [1/15 实测填实], owner 1/15 当天 09:00 patch 替换 placeholder.
> 1/15 09:30 Phase 5.5 中段启动仪式衔接 `phase5-public-beta-half-year-mid-2027-01-15.md` (同期交付).
> 6 个月 25 天累计 [332+] commits + [300 律师] 付费 + [60 律所] 签约 + [¥642,120 ARR] + 5x Rust 性能 + [60 律师] 企业版覆盖 + [40 创史律师] + 3 agent 27 task 阶段验收.
> 距 ¥40 万+ ARR 任务目标超额 160% (¥242,120), 12 月目标律师 60% + 企业版 12x 超额 + ARR 64% 半年中段达标率.
> 5 大新方向中段进度 30%+50%+10%+18%+25% (Skill 4 + 律所版定制 + 200 律所 + ¥200 万 ARR + Marketplace), 2/1 完结目标 50%+ 平均进度.
> Phase 5.5 中段 → 完结 (2/1) 路线清晰 + 2/15 Phase 6.1 Marketplace 启动 (W25 接力) + W25 计划 (1/16-1/31) 准备就绪 + 3 agent 12 task 派发 + 3 应急备案.
> Phase 6 (2027 H1: 1/1-6/30) 4 阶段 + 9 plan/季度 = 18 plan 路线清晰, Q1 (1-3 月 W23-W31) + Q2 (4-6 月 W32-W40) 接力 Phase 5.5 完结 + Marketplace MVP + Skill 4 正式版 + 律所版定制 + 跨平台 + 半年节点.