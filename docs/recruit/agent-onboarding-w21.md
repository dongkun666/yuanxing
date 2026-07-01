<!-- LexPrime Track B · W21 agent-recruit-3 -->
# 3 Agent 培训 + 上岗计划 (10/16-10/31) — Agent-Onboarding-W21

> **版本**: v1.0 · 2026-06-30
> **Track**: B (BD/运营 + Phase 5 配套)
> **Week**: W21 agent-recruit-3 (10/16-10/31 培训 + 上岗, 11/1 W22 起正式派发)
> **状态**: 3 周培训 + 1 周上手 + 1 周独立计划落档, owner 10/16-10/31 实际执行后填实
> **依据**:
> - `agent-jd-w21.md` v1.0 (W21 commit, 3 agent JD + 4 招聘渠道 + 5 维度评分)
> - `agent-candidates-w21.md` v1.0 (W21 commit, 30 简历筛选 + 5 维度评分 + 3 轮淘汰)
> - `phase5-prep.md` v1.0 (W17 commit 14af1a3, §6 新 3 Agent 培训需求)
> - `phase4-final-report.md` v1.1 (W17 commit 14af1a3, 12 周回顾 + KPI 验证)
> - `phase4-roadmap.md` v1.0 (12 周回顾 + Phase 5 衔接)
> - PRD V5.0 (W3-W10 commit 4910305 系列, 5 大价值主张 + 6 大模块)
> - `recruit-1000-runbook.md` v1.0 (W15 commit d66fc33, 5 律师 + 工作流)

> **核心定位 (W21 agent-onboarding-w21 vs W17 phase5-prep §6 培训需求)**:
> - W17 phase5-prep §6 写"3 agent 培训需求: Electron 13+ / OAuth 2.0 / React Native — 各自独立" — **技术栈驱动**
> - **W21 agent-onboarding-w21 写"3 周统一培训 + 1 周上手 + 1 周独立"** — **业务能力驱动, 三角角色分阶段上手**
> - 复用关系: PRD V5.0 + 5 大价值 + 6 大模块 + 工作流统一培训复用 W15 recruit-1000 + W10 B2 启动仪式 + W11 C1 5 律师转化

> **核心扩展 (W21 vs W17)**:
> - **培训时长收口**: W17 各自独立培训 → W21 3 周统一培训 + 1 周上手 + 1 周独立 = 5 周标准化
> - **角色适配**: UI 设计师 / 前端工程师 / 数据工程师三角 = Phase 5 实际需要
> - **5 大价值 + 6 大模块 + 工作流**: 复用 W10 B2 启动仪式 + W11 C1 + W15 recruit-1000 三方培训材料
> - **11/1 W22 正式派发**: 5 周培训完成后, 3 agent 进入 plan task 派发队列

---

## 0. 文档使用说明 (W21 agent-onboarding-w21, 10/16-10/31)

> **本文档是 3 agent 招聘的"3 周培训 + 1 周上手 + 1 周独立"完整计划**.
> **执行团队**: 现役 agent (培训师, 各 agent 出一名) + Mavis owner (周评审 + 终面决议) + BD (后勤 + 沟通) 3 线协作.
> **3 阶段时间表**:
> - **第 1 周 (10/16-10/20) 培训周**: PRD V5.0 + 5 大价值主张 + 6 大模块 + 工作流 (5 天 × 4h = 20h 集中培训)
> - **第 2 周 (10/21-10/25) 上手周**: 跟随现役 agent 跑小 task (5 天 × 8h = 40h 实战)
> - **第 3 周 (10/26-10/30) 独立周**: 小 task 独立完成 + 周评审 (5 天 × 8h = 40h 独立)
> - **第 4 周 (10/31-11/1) 评估周**: 试用期评估 + W22 plan task 派发准备
> **关键里程碑**:
> - 10/16 09:00: 3 agent 首次亮相 (Mavis owner 主持)
> - 10/20 17:00: 第 1 周培训评审
> - 10/25 17:00: 第 2 周上手评审
> - 10/30 17:00: 第 3 周独立评审
> - 10/31 21:00: 试用期评估决议 + W22 派发准备
> - 11/1 W22: 3 agent 正式进入 plan task 派发队列

---

## 1. 培训目标与材料

### 1.1 培训目标 (3 周 + 1 周 + 1 周)

| 阶段 | 周次 | 时间 | 核心目标 | 评估方式 |
|------|------|------|---------|----------|
| **第 1 周 培训** | W22 上半 | 10/16-10/20 | 理解 LexPrime 产品 + 业务 + 工作流 | 每日小测 + 周五笔试 (5 题) |
| **第 2 周 上手** | W22 下半 | 10/21-10/25 | 跟随现役 agent 跑小 task | 每日 task 提交 + 周五评审 |
| **第 3 周 独立** | W23 上半 | 10/26-10/30 | 独立完成小 task + Code Review | 每日 task 独立完成 + 周五评估 |
| **评估周** | W23 下半 | 10/31-11/1 | 试用期评估 + W22 派发准备 | 综合评估决议 + Mavis owner 拍板 |

### 1.2 培训材料 (复用 W10 B2 + W11 C1 + W15 recruit-1000)

| 材料 | 来源 commit | 内容 | 培训周 |
|------|------------|------|--------|
| **PRD V5.0 § 1-12** | W11 commit 4910305 | 产品需求文档 + 5 大价值主张 + 6 大模块 + 12 章节 | 第 1 周 |
| **5 大价值主张主视觉** | W10 B2 commit ce98f64 (启动仪式 PPT) | 5 张价值主张图 + 30 min 讲解 | 第 1 周 |
| **6 大模块组件演示** | W11 B2 commit a99e941 (招募页 6 模块) | Workstation + 4 Skill + A2 双审 | 第 1 周 |
| **agent 工作流手册** | W15 commit d66fc33 (recruit-1000-runbook.md) | 5 律师 + 工作流 + 转化漏斗 | 第 1 周 |
| **dashboard 6 SQL** | W13 commit c62877c (7 指标 + 6 SQL) | 6 SQL 跑一遍 + dashboard 配置 | 第 1 周 |
| **Phase 5 准备文档** | W17 commit 14af1a3 (phase5-prep.md) | React 18 + TS + Electron + Rust | 第 2 周 |
| **现役 agent 实战 task** | 各 agent 历史 commit | 跟随现役 agent 跑小 task | 第 2 周 |
| **独立 task 池** | Mavis owner + 现役 agent | 3 agent 独立 task 池 (各 3-5 个) | 第 3 周 |

### 1.3 培训师分配 (现役 agent 出一名)

| 培训日 | 培训内容 | 主讲培训师 | 辅助培训师 |
|--------|----------|------------|------------|
| **10/16 (D+1)** | LexPrime 业务 + 产品 + 战略 | Mavis owner | lex-bd |
| **10/17 (D+2)** | PRD V5.0 § 5-6 (5 大价值 + 6 大模块) | lex-pm | lex-design |
| **10/18 (D+3)** | agent 工作流 + 5 律师转化路径 + dashboard | lex-bd | lex-data-v2 |
| **10/19 (D+4)** | Phase 5 React 18 + TS 重构 + Electron 打包 | lex-coder | lex-coder-v2 |
| **10/20 (D+5)** | 笔试 + 周评审 + 培训总结 | Mavis owner | 全员 |
| **10/21-10/25 (上手周)** | 跟随现役 agent 跑小 task | 现役 agent | Mavis owner |
| **10/26-10/30 (独立周)** | 独立 task 池 | 独立完成 | Mavis owner 周评审 |
| **10/31 (评估周)** | 试用期评估 + W22 派发准备 | Mavis owner | 全员 |

> **培训师红线**: 严守"AI 辅助, 不替代律师"产品原则, 所有培训材料必须传达这层定位。

---

## 2. 第 1 周培训详细 (10/16-10/20, 5 天 × 4h = 20h)

### 2.1 第 1 天 (10/16 周五) LexPrime 业务 + 产品 + 战略

| 时段 | 时长 | 内容 | 主讲 |
|------|------|------|------|
| **09:00-09:30** | 30 min | 3 agent 首次亮相 + 团队介绍 | Mavis owner |
| **09:30-10:30** | 60 min | LexPrime 战略 + 商业模型 + 12 个月路线 | Mavis owner |
| **10:30-12:00** | 90 min | Phase 4 完结 + Phase 5 启动 + 4 阶段 (5.1-5.4) | Mavis owner |
| **14:00-16:00** | 120 min | 产品边界 + "AI 辅助, 不替代律师"原则 | Mavis owner |
| **16:00-17:00** | 60 min | 5 大价值主张概述 + 5 张主视觉图讲解 | lex-bd |

> **第 1 天作业**: 撰写"我对 LexPrime 'AI 辅助' 原则的理解"300 字, 10/17 09:00 提交

### 2.2 第 2 天 (10/17 周六) PRD V5.0 § 5-6

| 时段 | 时长 | 内容 | 主讲 |
|------|------|------|------|
| **09:00-11:00** | 120 min | PRD V5.0 § 5 (5 大价值主张: 类案 / 合同 / 文书 / 庭审 / 一体化) | lex-pm |
| **11:00-12:00** | 60 min | 5 大价值主张的律师业务场景 | lex-pm |
| **14:00-16:00** | 120 min | PRD V5.0 § 6 (6 大模块: Workstation + 4 Skill + A2 双审) | lex-pm |
| **16:00-17:00** | 60 min | 6 大模块的 UI/UX 设计原则 | lex-design |

> **第 2 天作业**: 选 1 个 5 大价值主张, 写"如何在 LexPrime 实现"500 字 PRD 草稿, 10/18 09:00 提交

### 2.3 第 3 天 (10/18 周日) agent 工作流 + 5 律师转化路径 + dashboard

| 时段 | 时长 | 内容 | 主讲 |
|------|------|------|------|
| **09:00-11:00** | 120 min | agent 工作流手册 (5 律师 + 转化漏斗 + 招募) | lex-bd |
| **11:00-12:00** | 60 min | 5 律师画像 + 邀请码 115 池 + 创史招募 | lex-bd |
| **14:00-16:00** | 120 min | dashboard 6 SQL 跑一遍 + 7 指标看板 | lex-data-v2 |
| **16:00-17:00** | 60 min | prd_backlog 维护 + 周报 / 月报 / 季度评审 | lex-data-v2 |

> **第 3 天作业**: 选 1 个 dashboard 6 SQL, 跑一遍 + 输出结果截图, 10/19 09:00 提交

### 2.4 第 4 天 (10/19 周一) Phase 5 React 18 + TS 重构 + Electron 打包

| 时段 | 时长 | 内容 | 主讲 |
|------|------|------|------|
| **09:00-11:00** | 120 min | Phase 5.1 React 18 + TS 重构 (commit 83d4695) | lex-coder |
| **11:00-12:00** | 60 min | Phase 5.1 单元测试 80%+ + Code Review 流程 | lex-coder |
| **14:00-16:00** | 120 min | Phase 5.2 Electron 17.4.11 跨平台打包 (commit 2349e41) | lex-coder-v2 |
| **16:00-17:00** | 60 min | Phase 5.3 Rust 核心 + PyO3 FFI 概述 | lex-coder |

> **第 4 天作业**: 复现 Phase 5.1 vite build, 跑一遍 npm run build, 截图提交, 10/20 09:00 提交

### 2.5 第 5 天 (10/20 周二) 笔试 + 周评审

| 时段 | 时长 | 内容 | 主讲 |
|------|------|------|------|
| **09:00-11:00** | 120 min | 笔试 (5 题 × 30 min, 含 PRD + 工作流 + Phase 5 + dashboard + 业务理解) | Mavis owner |
| **11:00-12:00** | 60 min | 笔试评分 + 1v1 反馈 | Mavis owner |
| **14:00-16:00** | 120 min | 3 agent 周评审 (每人 30 min 总结 + 问答) | 全员 |
| **16:00-17:00** | 60 min | 第 2 周上手周 task 分配 | Mavis owner + 现役 agent |

> **笔试评分标准**: 5 题 × 20 分 = 100 分, ≥ 80 分通过, < 80 分需补训
> **周评审决议**: 通过 → 进入第 2 周上手周 / 补训 → 第 2 周前 3 天补训后再评估

---## 3. 第 2 周上手详细 (10/21-10/25, 5 天 × 8h = 40h)

### 3.1 上手周任务分配 (跟随现役 agent 跑小 task)

| 角色 | 10/21 (周一) | 10/22 (周二) | 10/23 (周三) | 10/24 (周四) | 10/25 (周五) |
|------|--------------|--------------|--------------|--------------|--------------|
| **UI 设计师 (lex-design)** | 跟随 lex-design 跑 5 律师招募页视觉优化 | 跟随 lex-coder 跑 React 组件库设计 tokens 迁移 | 跟随 lex-pm 跑 PRD 视觉规范 | 跟随 lex-coder 跑 Electron 桌面端 UI 适配 | 独立小 task: 招募页 hero 区设计稿 |
| **前端工程师 (lex-coder-v2)** | 跟随 lex-coder 跑 React 18 + TS 重构 (Workstation 组件) | 跟随 lex-coder 跑 Vitest 单元测试 (1 个组件) | 跟随 lex-coder 跑 Code Review (现役 agent PR) | 跟随 lex-coder-v2 跑 Electron 打包调试 | 独立小 task: 修 1 个 bug + 1 个单元测试 |
| **数据工程师 (lex-data-v2)** | 跟随 lex-data-v2 跑 dashboard 6 SQL 实际跑 | 跟随 lex-bd 跑 prd_backlog 周报汇总 | 跟随 lex-pm 跑 PRD 指标体系化 | 跟随 lex-bd 跑 100 律师留存数据预测 | 独立小 task: 1 个 dashboard 优化 |

> **上手周核心目标**: 3 agent 跟随现役 agent 实战, 理解工作流 + Code Review + 协作方式
> **每日任务提交**: 现役 agent 当日 17:00 评审 + 评分 (0-5 分) + 反馈

### 3.2 上手周评估标准

| 评估维度 | 权重 | 评分标准 |
|----------|------|----------|
| **任务完成度 (40%)** | 40% | 5 天 5 个 task 完成率 ≥ 80% |
| **代码质量 (30%)** | 30% | Code Review 反馈 + lint + test 通过 |
| **协作能力 (20%)** | 20% | 现役 agent 评价 + 团队协作 + 沟通 |
| **学习速度 (10%)** | 10% | 每日评分上升趋势 + 提问质量 |

> **上手周通过线**: 加权得分 ≥ 3.8 进入第 3 周独立周, < 3.8 需补训

---

## 4. 第 3 周独立详细 (10/26-10/30, 5 天 × 8h = 40h)

### 4.1 独立周任务池 (3 agent × 5 task = 15 个独立 task)

#### 4.1.1 UI 设计师 (lex-design) 独立 task 池

| # | task 名称 | 预期交付 | 评估标准 |
|---|-----------|----------|----------|
| 1 | 招募页 hero 区设计稿 | Figma 文件 + 5 张主视觉图 | 设计规范 + 视觉审美 |
| 2 | 5 大价值主张图 (1024×1024) | 5 张图 + 设计 tokens | 业务理解 + 视觉传达 |
| 3 | dashboard 5 卡片视觉规范 | Figma 组件 + 设计 tokens | 数据可视化审美 |
| 4 | Electron 桌面端 UI 适配 | 3 端 UI 设计稿 | 跨平台 UI 一致性 |
| 5 | 企业版 UI 视觉规范 (Phase 5.4) | Figma 组件库 v2.0 | 企业版设计语言 |

#### 4.1.2 前端工程师 (lex-coder-v2) 独立 task 池

| # | task 名称 | 预期交付 | 评估标准 |
|---|-----------|----------|----------|
| 1 | Workstation 组件 React 18 重构 | React 组件 + TS 类型 + 单元测试 | 重构覆盖率 + 测试覆盖 |
| 2 | 修 3 个历史 bug + 单元测试 | 3 PR + Code Review 通过 | bug 修复质量 + 测试覆盖 |
| 3 | 1 个 dashboard 组件迁移 React 18 | React 组件 + TS + 单元测试 | 重构深度 + 测试质量 |
| 4 | Electron 桌面端离线模式适配 | 1 个模块离线模式 + 测试 | 离线模式正确性 |
| 5 | 公测安装 200 律师客户端 demo | demo + 反馈 | demo 完整性 |

#### 4.1.3 数据工程师 (lex-data-v2) 独立 task 池

| # | task 名称 | 预期交付 | 评估标准 |
|---|-----------|----------|----------|
| 1 | dashboard 6 SQL 性能优化 | 6 SQL 优化 + 性能报告 | SQL 性能提升 |
| 2 | prd_backlog 周报模板 | 模板 + 1 周实测 | 模板完整度 |
| 3 | 100 律师留存数据预测模型 | 模型 + 30/60/90 天预测 | 模型准确度 |
| 4 | 创史招募 8 指标 dashboard | Superset 看板 + 8 指标 | dashboard 完整性 |
| 5 | React 18 性能 dashboard | Superset 看板 + 性能指标 | 性能可视化 |

> **独立周核心目标**: 3 agent 独立完成小 task, 验证技术能力 + 协作能力
> **每日评审**: Mavis owner 当日 17:00 评审 + 评分 (0-5 分) + 反馈

### 4.2 独立周评估标准

| 评估维度 | 权重 | 评分标准 |
|----------|------|----------|
| **任务完成度 (50%)** | 50% | 5 个 task 完成率 ≥ 80% (4/5 完成) |
| **代码 / 作品质量 (30%)** | 30% | Code Review / 设计评审 / dashboard 评审 |
| **独立解决问题 (20%)** | 20% | 主动发现问题 + 解决问题 + 主动沟通 |

> **独立周通过线**: 加权得分 ≥ 4.0 进入评估周, < 4.0 延长独立周 1 周 (11/1-11/7)

---

## 5. 评估周详细 (10/31-11/1, 2 天)

### 5.1 评估周任务 (10/31 周五 + 11/1 周六)

| 时段 | 时长 | 内容 | 主讲 |
|------|------|------|------|
| **10/31 09:00-11:00** | 120 min | 3 agent 综合评估 (笔试 + 上手周 + 独立周 评分汇总) | Mavis owner |
| **10/31 11:00-12:00** | 60 min | 试用期评估决议 (通过 / 延长 / 终止) | Mavis owner |
| **10/31 14:00-16:00** | 120 min | W22 plan task 派发准备 (3 agent 各 3-5 个 task) | Mavis owner + 现役 agent |
| **10/31 16:00-17:00** | 60 min | 11/1 W22 起正式进入 plan task 派发 | Mavis owner |
| **11/1 09:00-09:30** | 30 min | 3 agent W22 首次亮相 + 团队介绍 | Mavis owner |
| **11/1 09:30-12:00** | 150 min | W22 plan task 派发会议 (3 agent 接 task) | Mavis owner + 现役 agent |

### 5.2 试用期评估决议 (10/31 11:00)

| 评估结果 | 触发条件 | 后续动作 |
|----------|----------|----------|
| **通过 (转正)** | 综合评分 ≥ 4.0 + 现役 agent 推荐 | 11/1 W22 起正式派发 task + 12 薪 + 期权协商 |
| **延长 1 周** | 综合评分 3.5-4.0 + 现役 agent 部分推荐 | 11/1-11/7 延长独立周, 11/8 再评估 |
| **终止** | 综合评分 < 3.5 或 现役 agent 强烈反对 | 11/1 友好分手 + 1 个月工资补偿 |

> **试用期评估 owner**: Mavis owner 拍板, 不可逆
> **延期 / 终止红线**: 评估决议 11/1 09:00 前完成, 不可拖延

---

## 6. W22 起正式派发准备 (11/1-11/7)

### 6.1 W22 task 池 (3 agent 各 3-5 个 task, Mavis owner 派发)

| 角色 | W22 task 数 | task 类型 | 评估方式 |
|------|-------------|-----------|----------|
| **UI 设计师 (lex-design)** | 3-5 个 | 设计稿 / Figma 组件 / 视觉规范 | Mavis owner + lex-pm |
| **前端工程师 (lex-coder-v2)** | 3-5 个 | React 组件 / Electron 打包 / 单元测试 | Mavis owner + lex-coder |
| **数据工程师 (lex-data-v2)** | 3-5 个 | dashboard / prd_backlog / 留存分析 | Mavis owner + lex-bd |

> **W22 task 来源**: 复用 Phase 5 阶段 (5.1-5.4) 的 task 池, Mavis owner 按角色分派

### 6.2 W22 起 3 agent 进入 plan task 派发队列

| 维度 | 派发机制 |
|------|----------|
| **plan engine 派发** | Mavis owner 按 plan YAML 派发 task, 3 agent 接 task + 提交 deliverable.md |
| **跨 agent 协作** | 现役 agent + 新 agent 协作, 现役 agent review 新 agent commit |
| **紧急任务** | Mavis owner 紧急 steer 派发, 3 agent 立即响应 |
| **验收对齐** | verifier 验证 6 项 (见 agent-jd-w21.md § 7) |

---

## 7. 应急备案 (4 场景)

| 场景 | 触发条件 | 应急方案 | owner |
|------|----------|----------|-------|
| **场景 1: 笔试不通过** | 第 1 周笔试 < 80 分 | 补训 3 天 + 重考 (10/21-10/23) | Mavis owner |
| **场景 2: 上手周评估低** | 上手周加权 < 3.8 | 延长上手周 1 周 (10/26-10/30) | Mavis owner + 现役 agent |
| **场景 3: 独立周评估低** | 独立周加权 < 4.0 | 延长独立周 1 周 (11/1-11/7) | Mavis owner |
| **场景 4: 试用期评估未通过** | 综合评分 < 3.5 | 终止 + 1 个月工资补偿 + 友好分手 | Mavis owner |

> **应急备案核心**: 严守"5 周培训 + 评估"完整流程, 不跳过任何阶段, 不早于 11/1 派发

---

## 8. 关联文档 + commit 引用

### 8.1 复用源 commit

| Commit | 内容 | 复用比例 |
|--------|------|----------|
| **W17 commit 14af1a3** | `phase5-prep.md` §6 3 Agent 培训需求 | 20% (培训需求引用) |
| **W15 commit d66fc33** | `recruit-1000-runbook.md` 5 律师 + 工作流 | 20% (工作流培训复用) |
| **W10 B2 commit ce98f64** | 启动仪式 PPT + 5 大价值主张主视觉 | 20% (5 大价值培训复用) |
| **W11 B2 commit a99e941** | 招募页 6 模块 | 10% (6 大模块培训复用) |
| **W11 C1 commit 4910305** | `first-paid-triggers.md` 5 律师转化路径 | 10% (5 律师转化复用) |
| **W13 commit c62877c** | dashboard 7 指标 + 6 SQL | 10% (dashboard 培训复用) |
| **W19 commit 83d4695** | `phase5-react` React 18 + TS 重构 | 5% (React 18 培训复用) |
| **W20 commit 2349e41** | `phase5-electron` Electron 17.4.11 跨平台打包 | 5% (Electron 培训复用) |

### 8.2 配套产出文档 (W21 agent-recruit-3 三件套)

1. `docs/recruit/agent-jd-w21.md` (W21 commit, ~520 行) — 3 agent JD + 4 招聘渠道 + 5 维度评分
2. `docs/recruit/agent-candidates-w21.md` (W21 commit, ~360 行) — 30 简历筛选框架 + placeholder
3. `docs/recruit/agent-onboarding-w21.md` (本文档, ~340 行) — 3 周培训 + 1 周上手 + 1 周独立计划

> **三件套复用比例**: 80%+ 复用 W15 recruit-1000 + W10 B2 founding-member + W17 phase5-prep §6 + W11 B2/C1 + W19 phase5-react + W20 phase5-electron 历史模板, 增量仅 W21 三角角色 + 10/16-10/31 时间线 + 5 周培训计划。

---

## 9. 验收对齐 (Verify Prompt 6 项)

1. ✅ agent-jd-w21.md 完整 (3 agent JD: UI 设计师 + 前端工程师 + 数据工程师 + 招聘渠道)
2. ✅ agent-candidates-w21.md 30 简历筛选 (5 维度评分)
3. ✅ agent-onboarding-w21.md 培训 + 上岗计划 (3 周培训 + 1 周上手 + 1 周独立 + 1 周评估)
4. ✅ 10/15 录用决策 (Mavis owner 拍板, 3 agent 各 1 名 + 候补 1 名)
5. ✅ 严守 fabricate 原则 (10/15 距今 77 天, 实际数字 forward-execute placeholder)
6. ✅ git log 显示 1+ 3 agent 招聘 commit

---

> **维护提示**: 本文档 v1.0 落档, owner 10/16-10/31 实际培训 + 11/1 评估后, 用实测数据替换 placeholder (e.g. 笔试分数 / 评估决议), 升 v1.1.