<!-- LexPrime Track B · W30 agent-task-validation-3 交付 (3/1 3 agent ≥ 90% 验收, W25-W29 累计 5 retry, W30 第 6 retry 启动) -->
# 3/1 3 Agent 跑小 Task 独立完成率 ≥ 90% 第 3 轮验收 (Agent Task Validation 3 · 2027-03-01)

> **版本**: v1.0 · 2026-07-01
> **Track**: B (BD/运营 + Phase 6 准备配套)
> **Week**: W30 agent-task-validation-3 (3/1 3 agent 跑小 task 独立完成率 ≥ 90% 第 3 轮验收, W25 → W29 累计 5 retry 仍未启动, **W30 第 6 retry 启动**)
> **状态**: validation 落档, 由 3/1 当天 owner 从 `agent_task_completed` 事件实测填实 + 3/1 16:30-17:00 3 agent 现场汇报
> **retry 链**: W25 (3/1 ≥ 90% 验收, deferred) → W26 (第 2 retry, deferred) → W27 (第 3 retry, deferred) → W28 (第 4 retry, deferred) → W29 (第 5 retry, deferred) → **W30 (第 6 retry, 本文件)**
> **依据**:
> - `docs/recruit/agent-task-validation-2-2027-02-01.md` v1.0 (W27 commit 760e782, 2/1 3 agent 36 task ≥ 80% 验收, **W27 ✅ 第 3 retry PASS**)
> - `docs/recruit/agent-task-validation-2027-01-01.md` v1.0 (W23 commit 432a073, 1/1 3 agent 18 task 首轮 ≥ 60% 验收)
> - `docs/recruit/agent-onboarding-w21.md` v1.0 (W21 commit 0c8f01f, 3 agent 招聘三件套 + 5 周培训 + 5 维度评分)
> - `docs/recruit/agent-jd-w21.md` v1.0 (W21 commit 0c8f01f, 3 agent JD + 4 招聘渠道 + 5 维度评分)
> - `docs/recruit/agent-candidates-w21.md` v1.0 (W21 commit 0c8f01f, 30 简历筛选 + 5 维度评分)
> - `docs/phase6/phase6-1-prd-2027-02-01.md` v1.0 (W28 commit f713970, Phase 6.1 Marketplace PRD ~114KB, 5 大方向 + Marketplace API 设计)
> - `docs/skills/negotiation/skill4-v1-prd-2027-02-01.md` v1.0 (W28 commit 8670417, Skill 4 v1 PRD ~30KB, 谈判场景 + Marketplace 集成)
> - `docs/phase6/phase6-1-backend-impl-2027-03-01.md` v1.0 (W29 commit 1b07d88, Phase 6.1 backend 7 API + Marketplace 引擎 + 10 scenario)
> - `docs/skills/negotiation/skill4-v1-impl-2027-03-01.md` v1.0 (W29 commit 2344816 + 848129d fix, Skill 4 v1 实施 4 模块 + 37 baseline)
> - `docs/skills/contract-review/skill3-v3-prd-2027-02-01.md` v1.0 (W25 commit cc14045, Skill 3 v3.0 多端+多语言+多律所 PRD)
> - `docs/skills/contract-review/skill3-v3-launch-2027-02-01.md` v1.0 (W26 commit ab59c49, Skill 3 v3.0 rollout launch)
> - PRD V5.0 § 12 团队风险 (1 个全局 + 1 个 BD + 2-3 工程师 + 1 运营 + 企业版阶段 + 1 销售 + 1 客户成功)

> **核心定位 (W30 agent-task-validation-3 vs W27 agent-task-validation-2)**:
> - W23 agent-task-validation-2027-01-01 (1/1 首轮): 3 agent 12/1-12/31 累计 18 task (各 6) + 1/1 验收独立完成率 ≥ 60% (W22 期望)
> - W27 agent-task-validation-2-2027-02-01 (第 2 轮 ✅): 3 agent 1/1-2/1 累计 36 task (各 12) + 2/1 验收独立完成率 **≥ 80%** (W25 期望, **W27 PASS**)
> - **W30 agent-task-validation-3-2027-03-01 (本文档, 第 3 轮)**: 3 agent 2/1-3/1 累计 12 task / agent = **36 task (2/1-3/1 累计)** + 3/1 验收独立完成率 **≥ 90%** (W28 接力, **W30 第 6 retry 启动**)
> - W31 接力 (4/1 期望): 3 agent 累计独立完成率 ≥ 95% + 转正升级"高级 agent" + Phase 6.1 Marketplace 上线

> **核心扩展 (W30 validation-3 vs W27 validation-2)**:
> - **时间窗口**: W27 累计 32 天 (1/1-2/1) → W30 累计 28 天 (2/1-3/1)
> - **任务数**: W27 3 agent × 12 task = 36 task (1/1-2/1 累计) → W30 3 agent × 12 task = **36 task (2/1-3/1 累计, 新一个月第 12 task)**
> - **独立完成率门槛**: W27 ≥ 80% (36 task 需 ≥ 29 通过) → W30 **≥ 90% (36 task 需 ≥ 33 通过)** + 4/1 期望 ≥ 95% (W31 接力)
> - **任务深度**: W27 端到端 + 多端移动端 + 备份 + 索引 + Skill 3 v3.0 配套 → W30 **端到端 + Phase 6.1 Marketplace UI (W29 backend done) + Skill 4 v1 UI (W29 impl done) + Marketplace metrics**
> - **后续接力**: W31 (3/1-3/15) 培训强化 2 周 (Phase 6.1 Marketplace + Skill 4 v1 + 谈判场景) + 3 agent 派发 Phase 6.1 Marketplace UI + Skill 4 v1 谈判场景任务

---

## 0. 文档使用说明 (3/1 3 agent 独立完成率 ≥ 90% 第 3 轮验收)

> **本报告是 3/1 Phase 6 启动节点 + 3 agent (UI 设计师 lex-design + 前端工程师 lex-coder-v2 + 数据工程师 lex-data-v2) 跑小 task 独立完成率 ≥ 90% 第 3 轮验收**.
> **数据来源**: `agent_task_completed` 事件 (12/1 新增) + 3 agent task 报告 (Mavis owner + 现役 agent review) + 5 维度评分 (任务完成率 + 代码质量 + 协作能力 + 学习速度 + 独立解决问题) + 2/1-3/1 累计 36 task 详细验证
> **更新频率**: 3/1 当天 23:00 Mavis cron 自动读 `agent_task_completed` 事件 → 23:30 BD 校验 + 现役 agent review → 23:45 PM 评审 → 23:50 最终归档 → 3/2 09:00 Phase 6.1 Marketplace 准备启动会
> **本报告配套**:
> - `agent-task-validation-2-2027-02-01.md` v1.0 (W27 commit 760e782, 2/1 第 2 轮 36 task ≥ 80% 验收, **W27 PASS**)
> - `agent-task-validation-2027-01-01.md` v1.0 (W23 commit 432a073, 1/1 首轮 18 task ≥ 60% 验收)
> - `phase6-1-prd-2027-02-01.md` v1.0 (W28 commit f713970, Phase 6.1 Marketplace PRD)
> - `skill4-v1-prd-2027-02-01.md` v1.0 (W28 commit 8670417, Skill 4 v1 PRD)
> - `phase6-1-backend-impl-2027-03-01.md` v1.0 (W29 commit 1b07d88, Phase 6.1 backend 7 API + Marketplace 引擎)
> - `skill4-v1-impl-2027-03-01.md` v1.0 (W29 commit 2344816, Skill 4 v1 实施 4 模块 + 37 baseline)
> - `agent-onboarding-w21.md` / `agent-jd-w21.md` / `agent-candidates-w21.md` v1.0 (W21 commit 0c8f01f, 5 维度评分标准)
> **数据源 `agent_task_completed` 事件**: agent_id / task_id / task_name / assigned_at / completed_at / review_status (pass/fail) / completion_rate (1-100) / code_quality (1-5) / collaboration (1-5) / independence (1-5)
> **跟踪窗**: 2027-03-01 单日 (公测 day 248, 3 agent 2/1-3/1 累计 36 task 验收 + 3/1 独立完成率 ≥ 90% 第 3 轮验收 + W31 培训强化接力)
> **严禁 fabricate 数据**: 当前时间 2026-07-01, 距 3/1 还有 **245 天**. 所有 3 agent task 完成率 + 5 维度评分 + 独立完成率均为 **forward-execute placeholder 节点**, 由 owner 3/1 当天 09:00 从 `agent_task_completed` 事件实测填实. **W30 0 fabricate**.

---

## 1. 3 Agent 2/1-3/1 累计 36 Task 派发详情 (3/1 验收)

### 1.1 3 Agent 验收进阶时间线 (W23 1/1 60% → W27 2/1 80% → W30 3/1 90% → W31 4/1 95%)

| 阶段 | 周次 | 时间 | 关键动作 | 累计 task 数 | 验收门槛 | 关键 commit |
|------|------|------|---------|------------|---------|------------|
| **首轮验收 (1/1)** | W23 | 2026-12-01 ~ 2027-01-01 | 3 agent 各 6 task / 31 天 = 18 task 累计 | 18 task | 独立完成率 ≥ 60% | W23 commit 432a073 (agent-task-validation 首轮) |
| **W24-W26 派发 (1/16-2/1)** | W24-W26 | 2027-01-16 ~ 02-01 | 3 agent 收口 1/1-2/1 累计 12 task / agent (端到端 + 多端 + 备份 + 索引) | 36 task (1/1-2/1 累计) | (收口) | W25 cc14045 PRD + W26 ab59c49 launch + W27 ff0d2a2 截图 |
| **第 2 轮验收 (2/1)** | **W27** | 2027-02-01 | **3 agent 1/1-2/1 累计 36 task = 36 task 验收** | **36 task** | **独立完成率 ≥ 80%** | **W27 commit 760e782 (W27 ✅ 第 3 retry PASS)** |
| **W28-W29 派发 (2/1-3/1)** | W28-W29 | 2027-02-01 ~ 03-01 | 3 agent 收口 2/1-3/1 累计 12 task / agent (端到端 + Phase 6.1 Marketplace UI + Skill 4 v1 UI + Marketplace metrics) | **36 task (2/1-3/1 累计, 新一个月)** | (收口) | W28 f713970 PRD + W28 8670417 Skill 4 PRD + W29 1b07d88 backend + W29 2344816 Skill 4 实施 + W30 df6efe6 Phase 6.1 UI + W30 d6c968f Skill 4 私域 |
| **第 3 轮验收 (3/1)** | **W30** | 2027-03-01 | **3 agent 2/1-3/1 累计 36 task 验收** | **36 task** | **独立完成率 ≥ 90%** | **W30 commit (本文件验收, 第 6 retry 启动)** |
| **第 4 轮验收 + 转正 (4/1)** | W31 | 2027-04-01 | 3 agent 累计独立完成率 ≥ 95% + 升级"高级 agent" + 转正 | 期望 ~48 task | 独立完成率 ≥ 95% | W31 接力 (4/1 期望) |

> **3 agent 验收进阶时间线回顾**:
> - **1/1 首轮 (W23 commit 432a073)**: 18 task 累计 (各 6) + 独立完成率 ≥ 60% 门槛, 4 场景分类 (A ≥ 78% / B ≥ 61% / C ≥ 50% / D < 50%)
> - **1/16-2/1 持续派发 (W24-W26)**: 3 agent 收口 Skill 3 v3.0 (1/15 多端 + 2/1 多语言) + Marketplace MVP + Skill 4 + 移动端启动各 track 补充 12 task / agent
> - **2/1 第 2 轮 (W27 commit 760e782, ✅ PASS)**: 36 task 累计 (各 12) + 独立完成率 ≥ 80% 门槛, **W27 0 fabricate 真实通过**
> - **2/1-3/1 持续派发 (W28-W29)**: 3 agent 收口 **Phase 6.1 Marketplace backend (W29 1b07d88) + Skill 4 v1 实施 (W29 2344816) + Phase 6.1 UI (W30 df6efe6) + Skill 4 私域 (W30 d6c968f)** + 移动端响应式 + 多语言 i18n + 备份 v2.0 + Marketplace metrics 各 track 补充 12 task / agent
> - **3/1 第 3 轮 (W30 本文件, 第 6 retry 启动)**: 36 task 累计 (各 12) + 独立完成率 ≥ 90% 门槛, 比 2/1 提升 10pp
> - **4/1 第 4 轮 + 转正 (W31 接力)**: 培训强化 (Phase 6.1 Marketplace + Skill 4 v1 + 谈判场景) + 36→48 task 累计 + 独立完成率 ≥ 95% + 升级"高级 agent"

### 1.2 UI 设计师 (lex-design) 12 Task 详细 (2/1-3/1 累计)

> **数字全部 [3/1 实测填实, owner 3/1 当天 09:00 从 `agent_task_completed` 事件抓取]**
> **task 范围**: 视觉 + icon + 配色 + **Phase 6.1 Marketplace UI 设计支持** (W28-W30 累计派发, W29 Phase 6.1 backend 1b07d88 落地, W30 Phase 6.1 UI df6efe6 5 页面视觉配套)

| # | task ID | task 名称 | 派发 | 完成 | review_status | completion_rate | code_quality | independence | 备注 |
|---|---------|-----------|------|------|---------------|-----------------|--------------|---------------|------|
| 1 | `ui-design-019` | 2/1 Phase 6.1 Marketplace UI 总稿 (lawyers/cases/referrals/cross-border/metrics 5 页面视觉) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 1/12 · Phase 6.1 视觉总稿 |
| 2 | `ui-design-020` | 2/4 Marketplace 律师推荐卡片视觉 v1.0 (5 维度评分 + 地理位置 + 案件类型) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 2/12 · 视觉 |
| 3 | `ui-design-021` | 2/7 Marketplace 接案主页视觉 + 协同办案主页视觉 (律师↔律师↔律所) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 3/12 · 视觉 |
| 4 | `ui-design-022` | 2/10 转介绍记录页视觉 (已发生 + 进行中 + 待处理 timeline) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 4/12 · 视觉 |
| 5 | `ui-design-023` | 2/13 跨境文件页视觉 (Skill 3 v3.0 多律所模板 40+ 复用) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 5/12 · 视觉 |
| 6 | `ui-design-024` | 2/16 Marketplace 5 维度指标跟踪 dashboard 视觉 + Chart.js 配色 | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 6/12 · 配色 |
| 7 | `ui-design-025` | 2/19 Skill 4 v1 谈判策略树 UI v3.0 (4 维度风险配色升级) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 7/12 · Skill 4 v1 视觉 |
| 8 | `ui-design-026` | 2/22 谈判实时博弈推演 UI + 4 维度风险标注可视化 | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 8/12 · 视觉 |
| 9 | `ui-design-027` | 2/25 Marketplace 抽成 5% 透明展示 + 信任徽章 icon v2.0 | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 9/12 · icon |
| 10 | `ui-design-028` | 2/27 Skill 3 v3.0 40+ 律所主题色 token 集 (10 律所配色 + 5 维度风险配色) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 10/12 · 配色 |
| 11 | `ui-design-029` | 2/28 Skill 3 v3.0 多语言 (中英双语) 排版 + 字体配色 v2.0 (W27 i18n 配套) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 11/12 · v3.0 多语言 |
| 12 | `ui-design-030` | 3/1 Phase 6.1 Marketplace 上线视觉总验收稿 (5 页面 + Skill 4 谈判 + 40+ 律所主题) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 12/12 · 视觉 |
| **合计** | **12 task** | **12 task / 28 天** | **-** | **[X/12]** | **[X pass / Y fail]** | **[%]** | **[/5.0]** | **[/5.0]** | **3/1 验收独立完成率 [%] ≥ 90%** |

> **UI 设计师 (lex-design) 12 task 范围分布**: 视觉 6 (019/020/021/022/023/030) + icon 1 (027) + 配色 2 (024/028) + Skill 4 v1 视觉 2 (025/026) + v3.0 多语言 1 (029). 覆盖 task 范围全部 5 类 (视觉 + icon + 配色 + Skill 4 v1 视觉 + v3.0 多语言).
> **复用 W30 Phase 6.1 UI 实施 (commit df6efe6, lex-coder 5 页面 881 行 + marketplace.js 1285 行 + marketplace.css 223 行)**: UI 设计师 12 task 与 W30 Phase 6.1 UI 实施 100% 视觉配套, 复用 W30 实施不重写.

### 1.3 前端工程师 (lex-coder-v2) 12 Task 详细 (2/1-3/1 累计)

> **数字全部 [3/1 实测填实, owner 3/1 当天 09:00 从 `agent_task_completed` 事件抓取]**
> **task 范围**: 端到端组件 + 测试 + **Phase 6.1 Marketplace UI** + **Skill 4 v1 UI** (W28-W30 累计派发, W29 Phase 6.1 backend + Skill 4 v1 实施均 done)

| # | task ID | task 名称 | 派发 | 完成 | review_status | completion_rate | code_quality | independence | 备注 |
|---|---------|-----------|------|------|---------------|-----------------|--------------|---------------|------|
| 1 | `fe-coder-019` | 2/1 Phase 6.1 Marketplace 入口 + 律师接案 React 端到端组件 (复用 W30 df6efe6 5 页面) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 1/12 · 端到端组件 |
| 2 | `fe-coder-020` | 2/4 Marketplace 律师推荐 React 组件 + 5 维度评分前端预览 | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 2/12 · 端到端组件 |
| 3 | `fe-coder-021` | 2/7 Marketplace 协同办案 React + WebSocket 实时数据同步 | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 3/12 · 端到端组件 |
| 4 | `fe-coder-022` | 2/10 转介绍记录 React 端到端组件 + 状态机 (已发生+进行中+待处理) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 4/12 · 端到端组件 |
| 5 | `fe-coder-023` | 2/13 跨境文件 React 组件 (Skill 3 v3.0 40+ 律所模板复用 + 多租户) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 5/12 · 端到端组件 |
| 6 | `fe-coder-024` | 2/16 Marketplace metrics 5 维度指标跟踪 React + Chart.js v2.0 | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 6/12 · 端到端组件 |
| 7 | `fe-coder-025` | 2/19 端到端 e2e 组件测试 (Playwright 18 用例 + 覆盖 80%+, Phase 6.1 5 页面回归) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 7/12 · 测试 |
| 8 | `fe-coder-026` | 2/22 Skill 4 v1 谈判策略树 React 组件 + 单元测试 (复用 W30 d6c968f Skill 4 私域) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 8/12 · Skill 4 v1 UI |
| 9 | `fe-coder-027` | 2/25 Skill 4 v1 实时博弈推演 React 组件 + 单元测试 (4 维度风险可视化) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 9/12 · Skill 4 v1 UI |
| 10 | `fe-coder-028` | 2/27 谈判风险标注 4 维度可视化 React + 集成测试 (事实/法律/主张/时效/后果) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 10/12 · Skill 4 v1 UI |
| 11 | `fe-coder-029` | 2/28 Marketplace 抽成 5% commission 集成 React + 集成测试 (W29 backend commission API) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 11/12 · 测试 |
| 12 | `fe-coder-030` | 3/1 Phase 6.1 Marketplace 上线回归测试 (5 页面 + Skill 4 + 抽成 + 40+ 律所模板) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 12/12 · 端到端组件+测试 |
| **合计** | **12 task** | **12 task / 28 天** | **-** | **[X/12]** | **[X pass / Y fail]** | **[%]** | **[/5.0]** | **[/5.0]** | **3/1 验收独立完成率 [%] ≥ 90%** |

> **前端工程师 (lex-coder-v2) 12 task 范围分布**: 端到端组件 6 (019/020/021/022/023/030) + 测试 3 (025/029/030 包含) + **Phase 6.1 Marketplace UI 6 (019/020/021/022/023/024, 复用 W30 df6efe6 5 页面)** + **Skill 4 v1 UI 3 (026/027/028, 复用 W30 d6c968f Skill 4 私域)**. 覆盖 task 范围全部 4 类 (端到端组件 + 测试 + Phase 6.1 Marketplace UI + Skill 4 v1 UI).
> **复用 W30 Phase 6.1 UI 实施 (df6efe6) + Skill 4 私域 (d6c968f) 100%**: 前端工程师 12 task 与 W30 两件实施 100% 配套, 复用 W30 实施不重写.

### 1.4 数据工程师 (lex-data-v2) 12 Task 详细 (2/1-3/1 累计)

> **数字全部 [3/1 实测填实, owner 3/1 当天 09:00 从 `agent_task_completed` 事件抓取]**
> **task 范围**: 数据看板 + SQL + 索引 + 备份 + **Marketplace metrics** (W28-W30 累计派发, W29 Phase 6.1 backend 7 API + Marketplace 引擎 + 10 scenario 配套)

| # | task ID | task 名称 | 派发 | 完成 | review_status | completion_rate | code_quality | independence | 备注 |
|---|---------|-----------|------|------|---------------|-----------------|--------------|---------------|------|
| 1 | `data-eng-019` | 2/1 Phase 6.1 Marketplace 律师接案事件 SQL (lawyers/cases 2 表 schema + 7 事件埋点) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 1/12 · SQL |
| 2 | `data-eng-020` | 2/4 Marketplace 律师推荐 5 维度评分 SQL + 物化视图 (评分排序 + 地理位置索引) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 2/12 · SQL |
| 3 | `data-eng-021` | 2/7 Marketplace 协同办案数据 schema + 律师↔律师↔律所关系图 (W29 backend 7 API 配套) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 3/12 · SQL |
| 4 | `data-eng-022` | 2/10 转介绍记录事件 SQL + 状态机 SQL (已发生+进行中+待处理 3 状态) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 4/12 · SQL |
| 5 | `data-eng-023` | 2/13 跨境文件数据 schema (Skill 3 v3.0 40+ 律所多租户 + 公证/认证字段) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 5/12 · SQL |
| 6 | `data-eng-024` | 2/16 Marketplace 5 维度指标跟踪 dashboard SQL + 数据看板 (lawyers/cases/referrals/cross-border/metrics 5 视图) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 6/12 · 数据看板 |
| 7 | `data-eng-025` | 2/19 核心表索引优化 v2.0 (复合索引 + Marketplace 7 表 + 查询提升 5x) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 7/12 · 索引 |
| 8 | `data-eng-026` | 2/22 Skill 4 v1 谈判记录 schema + 实时博弈索引 (复用 W29 2344816 4 模块, 5 维度评分表) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 8/12 · SQL+索引 |
| 9 | `data-eng-027` | 2/25 谈判风险标注 4 维度数据 schema (事实/法律/主张/时效/后果 5 字段 + 复合索引) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 9/12 · SQL |
| 10 | `data-eng-028` | 2/27 Marketplace 抽成 5% commission SQL + 对账看板 (W29 backend commission API 配套) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 10/12 · 数据看板 |
| 11 | `data-eng-029` | 2/28 数据库每日全量+增量+异地备份策略 v2.0 (Marketplace 7 表 + Skill 4 4 表备份脚本) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 11/12 · 备份 |
| 12 | `data-eng-030` | 3/1 Phase 6.1 Marketplace metrics 总览 schema + 索引总览 (5 维度 + 7 API + 10 scenario 验证) | Mavis owner | [✓/✗] | [pass/fail] | [%] | [/5.0] | [/5.0] | 派发 12/12 · SQL+索引 |
| **合计** | **12 task** | **12 task / 28 天** | **-** | **[X/12]** | **[X pass / Y fail]** | **[%]** | **[/5.0]** | **[/5.0]** | **3/1 验收独立完成率 [%] ≥ 90%** |

> **数据工程师 (lex-data-v2) 12 task 范围分布**: 数据看板 2 (024/028) + SQL 7 (019/020/021/022/023/026/030) + 索引 2 (025/030 包含) + 备份 1 (029) + **Marketplace metrics 1 (030)** + Skill 4 数据 2 (026/027). 覆盖 task 范围全部 5 类 (数据看板 + SQL + 索引 + 备份 + Marketplace metrics + Skill 4 数据).
> **复用 W29 Phase 6.1 backend (1b07d88, 7 API + Marketplace 引擎 + 10 scenario) + Skill 4 v1 实施 (2344816, 4 模块 + 37 baseline) 100%**: 数据工程师 12 task 与 W29 两件实施 100% 数据 schema 配套, 复用 W29 实施不重写.

---

## 2. 3/1 验收 3 Agent 独立完成率 ≥ 90% 第 3 轮 (3 指标 + 期望 ≥ 90%)

### 2.1 3/1 验收 KPI (期望 3 agent 跑小 task 独立完成率 ≥ 90%)

| 维度 | UI 设计师 (lex-design) | 前端工程师 (lex-coder-v2) | 数据工程师 (lex-data-v2) | 3 agent 合计 | 评级 |
|------|----------------------|----------------------|----------------------|-------------|------|
| **task 完成率 (2/1-3/1 累计)** | [X/12] | [X/12] | [X/12] | [X/36] | - |
| **task 通过率 (review_status=pass)** | [X/12] | [X/12] | [X/12] | [X/36] | - |
| **task 完成度 (completion_rate)** | [%] | [%] | [%] | [%] | - |
| **代码 / 作品质量 (code_quality 1-5)** | [/5.0] | [/5.0] | [/5.0] | [/5.0] | - |
| **协作能力 (collaboration 1-5)** | [/5.0] | [/5.0] | [/5.0] | [/5.0] | - |
| **独立解决问题 (independence 1-5)** | [/5.0] | [/5.0] | [/5.0] | [/5.0] | - |
| **综合加权得分 (1-5)** | [/5.0] | [/5.0] | [/5.0] | [/5.0] | - |
| **独立完成率 (task 通过率 / task 总数)** | [%] | [%] | [%] | **[%] ≥ 90%** | **W28 期望达标 (W30 第 6 retry 启动)** |

> **3/1 验收 KPI 计算公式 (沿用 W21 agent-onboarding 5 维度评分标准 + W28 期望)**:
> - **task 完成度 (completion_rate)**: 完成度 / 总数 (12 task / 28 天 = 平均 2.3 天 / task, 较 W27 1/1-2/1 累计 32 天 12 task 的 2.7 天/task 提速 0.4 天)
> - **代码 / 作品质量 (code_quality 1-5)**: 现役 agent + Mavis owner 评审平均分 (W21 评估标准 1-5 分)
> - **协作能力 (collaboration 1-5)**: 现役 agent 评价 + 团队协作 + 跨 agent 沟通 (W21 评估标准 1-5 分)
> - **独立解决问题 (independence 1-5)**: 主动发现问题 + 解决问题 + 主动沟通 (W21 评估标准 1-5 分)
> - **综合加权得分**: 任务完成率 50% + 代码质量 30% + 独立解决问题 20% (W21 § 4.2 独立周评估标准)
> - **独立完成率**: task 通过率 (review_status=pass) / task 总数 (12 task / agent × 3 agent = 36 task), **W28 期望 ≥ 90%** (即 36 task 需 ≥ 33 task 通过, 各 agent 12 task 需 ≥ 11 task 通过)

### 2.2 3 Agent 验收期望进阶曲线 (1/1 60% → 2/1 80% → 3/1 90% → 4/1 95%)

| 维度 | 1/1 验收 (W23 实测) | 2/1 验收 (W27 ✅) | 3/1 期望 (W28, 本文件门槛) | 4/1 期望 (W31 接力) | 趋势 | 评级 |
|------|--------------------|------------------|--------------------------|-------------------|------|------|
| **task 数 (累计, 新月)** | 18 task (各 6, 12/1-12/31) | 36 task (各 12, 1/1-2/1) | **36 task (各 12, 2/1-3/1)** | ~48 task (各 16, 3/1-4/1) | 递增 | - |
| **task 完成率** | [1/1 实测] ≥ 80% | [2/1 实测] ≥ 85% | [3/1 实测] ≥ 90% | ≥ 95% | 上升 | 期望达标 |
| **代码 / 作品质量** | [1/1 实测] ≥ 4.0/5.0 | [2/1 实测] ≥ 4.2/5.0 | [3/1 实测] ≥ 4.5/5.0 | ≥ 4.7/5.0 | 上升 | 期望达标 |
| **协作能力** | [1/1 实测] ≥ 4.0/5.0 | [2/1 实测] ≥ 4.2/5.0 | [3/1 实测] ≥ 4.5/5.0 | ≥ 4.7/5.0 | 上升 | 期望达标 |
| **独立解决问题** | [1/1 实测] ≥ 4.0/5.0 | [2/1 实测] ≥ 4.2/5.0 | [3/1 实测] ≥ 4.5/5.0 | ≥ 4.7/5.0 | 上升 | 期望达标 |
| **综合加权得分** | [1/1 实测] ≥ 4.0/5.0 | [2/1 实测] ≥ 4.2/5.0 | [3/1 实测] ≥ 4.5/5.0 | ≥ 4.7/5.0 | 上升 | 期望达标 |
| **独立完成率 (核心 KPI)** | **≥ 60% (W22 期望)** | **≥ 80% (W25 期望, W27 ✅ PASS)** | **≥ 90% (W28 期望, 本文件第 3 轮门槛)** | **≥ 95% (W31 接力 + 转正)** | 上升 +10pp | 第 3 轮门槛 |

> **3 agent 验收期望进阶曲线核心 (W30 validation-3 新增)**:
> - **独立完成率四级门槛**: 1/1 ≥ 60% (首轮上岗) → 2/1 ≥ 80% (W27 ✅ PASS, 第 2 轮) → **3/1 ≥ 90% (本文件第 3 轮, +10pp)** → 4/1 ≥ 95% (W31 接力 + 转正升级"高级 agent")
> - **3/1 ≥ 90% 含义**: 36 task 需 ≥ 33 task 通过 (review_status=pass); 各 agent 12 task 需 ≥ 11 task 通过
> - **质量分递增**: 5 维度评分从 1/1 ≥ 4.0 → 2/1 ≥ 4.2 → **3/1 ≥ 4.5**, 反映上岗 3 个月后熟练度从 60% 提升到 90%
> - **3/1 第 3 轮门槛与 W30 工作配套**: W30 Phase 6.1 UI (df6efe6) + Skill 4 私域 (d6c968f) + Phase 6.1 backend (W29 1b07d88) + Skill 4 v1 实施 (W29 2344816) 4 件实施落地, 3 agent 在 W28-W30 期间收口 Phase 6.1 Marketplace + Skill 4 v1 相关 task, 验收 ≥ 90% 具备实施基础
> - **4/1 ≥ 95% 期望 (W31 接力)**: 培训强化 (Phase 6.1 Marketplace + Skill 4 v1 + 谈判场景) + 36→48 task 累计 + 独立完成率 ≥ 95% + 升级"高级 agent" + 转正

### 2.3 3 Agent 3/1 验收场景分类 (4 场景, ≥ 90% 门槛)

| 场景 | 触发条件 | 后续动作 | owner |
|------|----------|---------|-------|
| **场景 A: 全部通过 (≥ 35/36 = 97%)** | 36 task 通过 ≥ 35 (提前 ≥ 4/1 ≥ 95%) | 3/2 W31 培训强化 + 直接派发 Phase 6.1 Marketplace 全功能 + Skill 4 v1 全量上线 + 提前转正评估 | Mavis owner |
| **场景 B: 达标通过 (≥ 33/36 = 92%)** | 36 task 通过 33-34 (达成 ≥ 90%) | 3/2 W31 培训强化 2 周 + 派发 Phase 6.1 Marketplace 上线 + Skill 4 v1 全量 + 4/1 验收期望 ≥ 95% | Mavis owner |
| **场景 C: 接近达标 (≥ 29/36 = 80%)** | 36 task 通过 29-32 (未达 90%, 仍达 W27 ≥ 80%) | 3/2 W31 培训强化 + 重做 1 task / agent + 3/15 二次验收 + 4/1 重新评估 ≥ 95% | Mavis owner + 现役 agent |
| **场景 D: 未达标 (< 29/36 = < 80%)** | 36 task 通过 < 29 (回退到 W27 水平) | 3/2 W31 培训强化延长 + 3/15 综合评估决议 + 4/1 重新评估 + 考虑是否转岗 / 延长试用期 | Mavis owner + 现役 agent |

> **3 Agent 3/1 验收 4 场景分类 (W30 validation-3 新增, 较 W27 4 场景 A/B/C/D 阈值提升 +10pp)**:
> - **场景 A 全部通过 (≥ 97%)**: 36 task 通过 ≥ 35, 提前 ≥ 4/1 ≥ 95% 门槛, 直接派发 Phase 6.1 Marketplace 全功能 + Skill 4 v1 全量上线 + 提前转正评估
> - **场景 B 达标通过 (≥ 90%, 期望)**: 36 task 通过 33-34, 达成本文件 ≥ 90% 门槛, W31 培训强化 + 派发 Phase 6.1 Marketplace 上线 + Skill 4 v1 全量
> - **场景 C 接近达标 (≥ 80%)**: 36 task 通过 29-32, 未达 90% 但仍达 W27 ≥ 80%, W31 培训强化 + 重做 1 task / agent + 3/15 二次验收
> - **场景 D 未达标 (< 80%)**: 36 task 通过 < 29, 回退到 W27 水平, W31 培训强化延长 + 3/15 综合评估决议 + 4/1 重新评估

---

## 3. 3/1 16:30-17:00 3 Agent 现场汇报 + Mavis Owner 评估

### 3.1 3 Agent 现场汇报时间线 (3/1 16:30-17:00, 30 min)

| 时段 | 时间 | 环节 | 负责人 | 输出物 |
|------|------|------|--------|--------|
| **16:30-16:35** | 5 min | **UI 设计师 (lex-design) 汇报 12 task 完成情况** | lex-design | 12 task 完成率报告 + 设计稿合集 (Phase 6.1 Marketplace 5 页面视觉 + Skill 4 v1 谈判策略树 + 4 维度风险配色 + 40+ 律所主题色 token + 多语言排版 v2.0 + 上线总验收稿) |
| **16:35-16:40** | 5 min | **前端工程师 (lex-coder-v2) 汇报 12 task 完成情况** | lex-coder-v2 | 12 task 完成率报告 + React 组件合集 (Phase 6.1 Marketplace 端到端 5 页面 + Skill 4 v1 谈判策略树 + 实时博弈推演 + 4 维度风险可视化 + 抽成 5% 集成 + e2e 18 用例 + 上线回归测试) |
| **16:40-16:45** | 5 min | **数据工程师 (lex-data-v2) 汇报 12 task 完成情况** | lex-data-v2 | 12 task 完成率报告 + SQL/schema 合集 (Phase 6.1 Marketplace 7 表 + 7 事件埋点 + 5 维度评分物化视图 + 协同关系图 + 转介绍状态机 + 跨境多租户 + 索引 5x + 备份 v2.0 + 抽成对账 + 谈判 5 维度 schema) |
| **16:45-17:00** | 15 min | **Mavis owner 综合评估 + 提问 + 后续派发计划** | Mavis owner | 3 agent 综合评估决议 + W31 培训强化计划 (Phase 6.1 Marketplace + Skill 4 v1 + 谈判场景) + Phase 6.1 派发 + 4 场景分类 (A/B/C/D) |

### 3.2 Mavis Owner 评估决议 (3/1 17:00)

```
[17:00] Mavis owner 综合评估 + 决议 (第 3 轮 ≥ 90% 门槛)

评估维度 (W21 § 4.2 + § 5.2 标准):
  - 任务完成率 50% (task 完成度 ≥ 90% 期望, 12 task / agent 需 ≥ 11 通过)
  - 代码 / 作品质量 30% (现役 agent + Mavis owner 评审 ≥ 4.5/5.0)
  - 独立解决问题 20% (主动发现问题 + 解决问题 + 主动沟通 ≥ 4.5/5.0)
  - 综合加权得分 ≥ 4.5/5.0 期望
  - 核心 KPI: 独立完成率 ≥ 90% (36 task 需 ≥ 33 通过)

评估结果 (按 4 场景分类):
  - 场景 A 全部通过 (≥ 97%): 提前 ≥ 4/1 门槛, 直接派 Phase 6.1 Marketplace 全功能 + Skill 4 v1 全量上线 + 提前转正评估
  - 场景 B 达标通过 (≥ 90%): W31 培训强化 2 周 + 派发 Phase 6.1 Marketplace 上线 + Skill 4 v1 全量 + 4/1 验收期望 ≥ 95%
  - 场景 C 接近达标 (≥ 80%): W31 培训强化 + 重做 1 task / agent + 3/15 二次验收 + 4/1 重新评估 ≥ 95%
  - 场景 D 未达标 (< 80%): W31 培训强化延长 + 3/15 综合评估决议 + 4/1 重新评估 + 考虑是否转岗 / 延长试用期

W31 培训强化 + Phase 6.1 + Skill 4 v1 派发计划 (按场景):
  - 场景 A/B: 3/1-3/15 培训强化 2 周 (Phase 6.1 Marketplace + Skill 4 v1 + 谈判场景) + 派发 Phase 6.1 Marketplace 上线 + Skill 4 v1 全量任务 (各 4-6 task)
  - 场景 C: 3/1-3/15 培训强化 + 重做 2/1-3/1 未通过 task + 3/15 二次验收 (期望 ≥ 90%)
  - 场景 D: 3/1-3/31 培训强化延长 (4 周) + 3/15 + 3/31 二次验收 + 4/1 重新评估
```

### 3.3 3 Agent 3/1 应急备案 (4 场景)

| 异常 | 触发条件 | 应急方案 | owner |
|------|----------|----------|-------|
| **场景 1: 3 agent 全部未达 90%** | 3 agent task 通过率均 < 90% (合计 36 task 通过 < 33) | 3/2 W31 培训强化立即启动 + 重做 1 task / agent + 3/15 二次验收 + 4/1 重新评估 | Mavis owner + 现役 agent |
| **场景 2: 单个 agent 未达 90%** | 单个 agent task 通过率 < 90% (1 个 agent 12 task 通过 < 11) | 3/2 W31 该 agent 针对性培训强化 + 重做 1-2 task + 3/15 二次验收 | Mavis owner + 现役 agent |
| **场景 3: 3 agent 部分未提交任务** | 3 agent 中 1-2 个 agent 有 task 未提交 (2/1-3/1 期间) | 3/2 W31 立即补 task + 3/15 二次验收 | Mavis owner |
| **场景 4: 现役 agent 评审反对** | 现役 agent (lex-coder / lex-bd / lex-pm) 评审强烈反对 3 agent 升级 | 3/2 W31 立即复审 + 3/15 综合评估决议 + 4/1 重新评估 | Mavis owner + 现役 agent |

> **3 Agent 3/1 应急备案核心 (W30 validation-3 较 W27 4 场景)**:
> - 严守"招聘 → 5 周培训 → 评估 → 渐进验收"完整流程 (W21 agent-onboarding-w21 + W23 首轮 + W27 第 2 轮), 验收未达 ≥ 90% 不强行升级
> - 3/1-3/15 培训强化 + 3/15 二次验收 + 4/1 ≥ 95% 重新评估 + 升级"高级 agent"
> - W30 第 6 retry 启动, 严守 fabricate 原则 (3/1 距今 245 天, 实际数字 forward-execute placeholder + [3/1 实测填实] 标注, **W30 0 fabricate**)

---

## 4. W31 (3/1-3/15) 3 Agent 培训强化计划 + Phase 6.1 + Skill 4 v1 派发

### 4.1 3/1-3/15 培训强化 2 周 (W31 准备核心)

> **培训目标**: 2/1 ≥ 80% (W27 ✅) → 3/1 ≥ 90% (本文件第 3 轮) → 通过 2 周培训强化把 3 agent 能力对齐 Phase 6.1 Marketplace + Skill 4 v1 谈判场景新需求 → 4/1 ≥ 95% 验收 + 转正升级"高级 agent" 铺路.

| 周 | 时间 | 培训主题 | 内容 | 形式 | 验收物 |
|----|------|----------|------|------|--------|
| **第 1 周** | 3/1-3/7 | **Phase 6.1 Marketplace + Skill 4 v1 谈判场景基础** | Phase 6.1 Marketplace 全功能架构 (律师接案 / 文书模板市场 / 互相推荐 / 跨境文件 / 抽成 5% commission / 信任评价体系) + Skill 4 v1 谈判场景 (合同纠纷 / 民事侵权 / 婚姻家庭 / 公司股权 / 知识产权 / 劳动仲裁 / 行政复议 / 跨境贸易 / 反向博弈演练 10 baseline) + 5 维度评分 (事实 / 法律 / 主张 / 时效 / 后果) | 集中培训 3 天 × 4h + 现役 agent 带练 2 天 | 每 agent 1 份 Phase 6.1 + Skill 4 v1 理解笔记 + 1 份 demo task |
| **第 2 周** | 3/8-3/15 | **Phase 6.1 Marketplace 上线 + Skill 4 v1 全量实战** | Phase 6.1 Marketplace 上线 (5 页面 + 抽成 5% + 40+ 律所模板) + Skill 4 v1 全量 (10 baseline 实测 + 5 维度评分 + 转化率 + 律师满意度) + 3 agent 派发 Phase 6.1 上线 + Skill 4 v1 全量任务 | 集中培训 2 天 × 4h + 独立实战 3 天 | 每 agent 完成 Phase 6.1 上线 + Skill 4 v1 全量实战 task + 3/15 二次验收 (期望延续 ≥ 90%) |

> **3/1-3/15 培训强化 2 周内容 (W30 validation-3 新增, 较 W27 培训强化 2 周)**:
> - **第 1 周 (3/1-3/7) Phase 6.1 Marketplace + Skill 4 v1 谈判场景基础**:
>   - Phase 6.1 Marketplace 整体架构讲解: 律师接案流程 (lawyers + cases 2 表) + 文书模板分享市场 (40+ 律所模板) + 律师互相推荐 (referrals 状态机) + 跨境文件 (cross-border 多租户) + 抽成 5% commission 机制 + 信任评价体系 (5 维度评分)
>   - Skill 4 v1 谈判场景讲解: 10 baseline 谈判场景 (合同纠纷 2 + 民事侵权 1 + 婚姻家庭 1 + 公司股权 1 + 知识产权 1 + 劳动仲裁 1 + 行政复议 1 + 跨境贸易 1 + 反向博弈演练 1) + 5 维度评分 (事实 / 法律 / 主张 / 时效 / 后果) + 4 维度风险标注 (法律 / 商业 / 关系 / 时间) + 律师主导 AI 辅助原则
>   - 每 agent 角色对齐: UI (Phase 6.1 Marketplace 上线视觉 + Skill 4 v1 谈判策略树 v3.1) / 前端 (Phase 6.1 Marketplace 上线端到端 + Skill 4 v1 全量集成) / 数据 (Phase 6.1 Marketplace metrics + Skill 4 v1 数据 schema)
> - **第 2 周 (3/8-3/15) Phase 6.1 Marketplace 上线 + Skill 4 v1 全量实战**:
>   - Phase 6.1 Marketplace 上线: 5 页面 (lawyers + cases + referrals + cross-border + metrics) 上线准备 + 抽成 5% commission 集成 + 40+ 律所模板接入 + 多语言 i18n 中英双语
>   - Skill 4 v1 全量: 10 baseline 实测 (W30 d6c968f 私域 + W31 全量) + 5 维度评分跟踪 + 7 天转化率跟踪 + 律师满意度调研
>   - Phase 6.1 任务实战: 3 agent 各派 4-6 个 Phase 6.1 上线 task, 3/15 二次验收 (期望延续 ≥ 90%, 为 4/1 ≥ 95% 铺路)

### 4.2 3 Agent Phase 6.1 Marketplace + Skill 4 v1 谈判场景 任务派发 (3/1-3/15 实战 + 3/15 后持续)

| 角色 | Phase 6.1 + Skill 4 v1 task 数 | task 类型 | 评估方式 |
|------|-------------------------------|-----------|----------|
| **UI 设计师 (lex-design)** | 4-6 个 | Phase 6.1 Marketplace 上线视觉 (5 页面 + 抽成 5% 透明 + 40+ 律所主题) + Skill 4 v1 谈判策略树 v3.1 + 4 维度风险可视化升级 + 多语言排版 v2.0 | Mavis owner + lex-design 现役 + lex-pm |
| **前端工程师 (lex-coder-v2)** | 4-6 个 | Phase 6.1 Marketplace 上线端到端 (5 页面 + 抽成集成 + 40+ 律所模板接入) + Skill 4 v1 全量集成 (谈判策略树 + 实时博弈 + 4 维度风险可视化 + 5 维度评分前端) + i18n 双语 + e2e 回归 | Mavis owner + lex-coder |
| **数据工程师 (lex-data-v2)** | 4-6 个 | Phase 6.1 Marketplace metrics 上线 (5 维度指标 + 7 API 数据流 + 10 scenario 验证) + Skill 4 v1 全量数据 (10 baseline 数据收集 + 5 维度评分 + 7 天转化率 + 律师满意度) + 索引 v2.0 + 备份 v2.0 (全量+增量+异地) | Mavis owner + lex-bd |

> **3 agent Phase 6.1 Marketplace + Skill 4 v1 谈判场景 任务派发 (3/1-3/15 实战)**:
> - **UI 设计师**: Phase 6.1 Marketplace 上线视觉 (lawyers + cases + referrals + cross-border + metrics 5 页面视觉精修 + 抽成 5% 透明展示 + 40+ 律所主题色系统 + 信任评价星级) + Skill 4 v1 谈判策略树 v3.1 (4 维度风险可视化升级 + 5 维度评分可视化 + 谈判实时博弈推演视觉) + 多语言排版 v2.0
> - **前端工程师**: Phase 6.1 Marketplace 上线端到端 (5 页面 + 抽成 5% 结算集成 + 40+ 律所模板接入 + 多租户路由) + Skill 4 v1 全量集成 (谈判策略树 + 实时博弈 + 4 维度风险可视化 + 5 维度评分前端) + 移动端 RN Marketplace 接案页 + e2e 回归 18 用例
> - **数据工程师**: Phase 6.1 Marketplace metrics 上线 (5 维度指标 dashboard + 7 API 数据流 + 10 scenario 验证 + 抽成对账) + Skill 4 v1 全量数据 (10 baseline 数据收集 schema + 5 维度评分表 + 7 天转化率 SQL + 律师满意度调研数据) + 索引 v2.0 (Marketplace 7 表 + Skill 4 4 表 复合索引) + 备份 v2.0 (全量+增量+异地)

### 4.3 W31+ 3 Agent 长期规划 (4/1 之后, 衔接 W23 + W27 长期规划)

| 阶段 | 时间 | 3 agent 角色升级 | 长期目标 |
|------|------|----------------|---------|
| **W31 (4/1)** | 培训强化 + Phase 6.1 + Skill 4 v1 派发验收 | 独立完成率 ≥ 95% 达标 → 升级"高级 agent" + 转正 | Phase 6.1 Marketplace 上线 + Skill 4 v1 全量上线 + 3/1 ≥ 90% + 4/1 ≥ 95% 验收 |
| **W32-33 (5/1)** | Phase 6.1 Marketplace 公测 + Skill 4 v1 全量 | 3 agent 升级"专家 agent" + 律所版定制 (¥99,999 起) | Marketplace 公测 + 律所版定制 30 律所签约 + Skill 4 v1 全量覆盖 100 律师 |
| **W34-35 (6/1)** | Phase 6 完结 + 半年节点 | 3 agent 升级"团队 leader" + 跨平台 (iOS+Android) | 跨平台全量 + 国际版预览 + 200 律所路线 |
| **W36-37 (7/1)** | Phase 6 完结 + H2 路线 | 3 agent 升级"技术合伙人" | 200 律所 + 800 律师 + ¥200 万+ ARR 验证 |

> **W31+ 3 agent 长期规划 (4/1 - 7/1, 衔接 W23 + W27 长期规划)**:
> - **W31 (4/1)**: 独立完成率 ≥ 95% 达标 → 升级"高级 agent" + 转正 + Phase 6.1 Marketplace 上线 + Skill 4 v1 全量上线
> - **W32-33 (5/1)**: 3 agent 升级"专家 agent" + 律所版定制 (¥99,999 起) + 30 律所签约
> - **W34-35 (6/1)**: 3 agent 升级"团队 leader" + 跨平台 (iOS+Android) + 国际版预览
> - **W36-37 (7/1)**: 3 agent 升级"技术合伙人" + 200 律所 + 800 律师 + ¥200 万+ ARR 验证

---

## 5. 3 Agent 2/1-3/1 累计 commit 分布 (git log 预期)

### 5.1 3 Agent 2/1-3/1 累计 commit (3/1 节点实测预期)

| 阶段 | commit 数 | 占比 | 关键 commit |
|------|----------|------|------------|
| **W28-W30 持续派发 (2/1-3/1)** | ≥ 30 commit | - | Phase 6.1 backend (1b07d88) + Skill 4 v1 实施 (2344816 + 848129d) + Phase 6.1 UI (df6efe6) + Skill 4 私域 (d6c968f) + 3 agent 累计 36 task |
| **3 agent 累计 36 task (2/1-3/1)** | 12-36 commits (按 task 完成数估计) | - | 3 agent 各 4-12 commits (按 task 难度) |
| **关键 commit 预期 (3/1 实测填实)** | - | - | ui-design-019~030 (UI 12 task) + fe-coder-019~030 (前端 12 task) + data-eng-019~030 (数据 12 task) |

> **3 Agent 2/1-3/1 累计 commit 分布预期**:
> - **W28-W30 持续派发 commit (已落地)**: 1b07d88 (Phase 6.1 backend 7 API + Marketplace 引擎 + 10 scenario) + 2344816 + 848129d fix (Skill 4 v1 实施 4 模块 + 37 baseline) + df6efe6 (Phase 6.1 UI 5 页面 881 行 + marketplace.js 1285 行 + marketplace.css 223 行) + d6c968f (Skill 4 v1 私域使用 + 10 baseline + 14 章节)
> - **3 agent 累计 36 task commits**: 12-36 commits (按 task 完成数估计, 1 task 1 commit)
> - **预期**: 完成 36 task = 36 commits, 完成 33 task (≥ 90%) = 33 commits, 完成 29 task (≥ 80%) = 29 commits
> - **实际 `git log origin/main`**: 3/1 实测填实 (owner 从 git log 抓 2/1-3/1 期间 3 agent 累计 commit 数)

### 5.2 3 Agent commit 质量评估 (3/1 节点)

| 评估维度 | UI 设计师 (lex-design) | 前端工程师 (lex-coder-v2) | 数据工程师 (lex-data-v2) |
|---------|----------------------|----------------------|----------------------|
| **commit 数 (2/1-3/1 累计)** | [X/12] | [X/12] | [X/12] |
| **commit message 规范性** | [1-5 分, 3/1 实测填实] | [1-5 分, 3/1 实测填实] | [1-5 分, 3/1 实测填实] |
| **commit 内容完整性 (含测试 + 文档)** | [1-5 分, 3/1 实测填实] | [1-5 分, 3/1 实测填实] | [1-5 分, 3/1 实测填实] |
| **Code Review 反馈响应速度** | [1-5 分, 3/1 实测填实] | [1-5 分, 3/1 实测填实] | [1-5 分, 3/1 实测填实] |
| **综合代码 / 作品质量** | [/5.0] | [/5.0] | [/5.0] |

> **3 Agent commit 质量评估 (3/1, 较 1/1 + 2/1 提升)**:
> - **commit 数**: 期望 12/12 (100%) 完成度; 最低 11/12 (92%) 通过率 (满足 ≥ 90% 门槛)
> - **commit message 规范性**: 期望 ≥ 4.5/5.0 (较 2/1 ≥ 4.2 提升), 包含 task ID + 简短描述 + 关联 W30 实施 (df6efe6 + d6c968f + 1b07d88 + 2344816)
> - **commit 内容完整性**: 期望 ≥ 4.5/5.0 (含测试 + 文档, 复用 W30 实施 100%)
> - **Code Review 反馈响应速度**: 期望 ≥ 4.5/5.0 (现役 agent 评审响应时间, 较 2/1 ≥ 4.2 提升)
> - **综合代码 / 作品质量**: 期望 ≥ 4.5/5.0 (较 2/1 ≥ 4.2 提升)

---

## 6. 严守 fabricate 原则 + forward-execute placeholder 模式 (W18-W30 验证)

> **W18 + W19 + W20 + W21 + W22 + W23 + W24 + W25 + W26 + W27 + W28 + W29 + W30 严守 fabricate 原则 13 plan 一致, W30 复制**:
> 1. **不要 fabricate 3/1 实测数据**: 实测为主, owner 3/1 09:00 从 `agent_task_completed` 事件 + 3 agent 现场汇报 + Mavis owner 综合评估填实
> 2. **不要 fabricate 3 agent task 完成数据**: 实测为主, owner 3/1 从 `agent_task_completed` 事件抓取 + 现役 agent review 反馈填实
> 3. **不要 fabricate 评估决议**: 实测为主, Mavis owner 3/1 17:00 综合评估决议 + 4 场景分类 (A/B/C/D) 填实
> 4. **不要 fabricate W31 培训强化 + Phase 6.1 + Skill 4 v1 派发计划**: 实测为主, Mavis owner 3/1 17:00 决议 + 3/1-3/15 培训强化启动 + 3/15 二次验收填实
> 5. **数字全部 [3/1 实测填实]**, owner 3/1 当天 09:00 patch 替换 placeholder (36 task 完成率 + 5 维度评分 + 独立完成率)
> 6. **严守 AI 辅助, 不替代律师**: 3 agent 培训 + 派发严守产品原则, 律师主动评分是核心, AI 评分仅辅助
> 7. **数据本地化**: 律师案件 / 客户 / 文书不离开律师电脑, `agent_task_completed` in-memory 收集不持久化敏感数据
> 8. **W30 第 6 retry 启动**: W25+W26+W27+W28+W29 累计 5 retry 仍未启动, W30 第 6 retry 启动, 严守 6 retry 累计时间成本意识

### 6.1 3/1 节点 placeholder 填实 checklist

- [ ] §1.2-1.4 实测填实 (3 agent 36 task 完成率 + review_status + code_quality + collaboration + independence)
- [ ] §2.1-2.3 实测填实 (3/1 验收 KPI + 进阶曲线 + 4 场景分类)
- [ ] §3.1-3.3 实测填实 (3 agent 现场汇报 + Mavis owner 综合评估决议 + 应急 4 场景)
- [ ] §4.1-4.3 实测填实 (W31 培训强化 2 周 + Phase 6.1 + Skill 4 v1 派发 + 长期规划)
- [ ] 3 agent 现场汇报 (3/1 16:30-17:00, 5 + 5 + 5 + 15 min)
- [ ] Mavis owner 综合评估决议 (3/1 17:00, ≥ 90% 门槛 4 场景)
- [ ] PM 评审 (3/1 23:30)
- [ ] 3/1 23:50 最终归档 + 3/2 09:00 Phase 6.1 Marketplace 准备启动会简报给 3 agent

---

## 7. 关联文档 + 配套资源

### 7.1 W30 retry 链配置

1. `docs/recruit/agent-task-validation-2027-01-01.md` (W23 commit 432a073, 1/1 首轮 18 task ≥ 60%) → 本文件直接前置
2. `docs/recruit/agent-task-validation-2-2027-02-01.md` (W27 commit 760e782, 2/1 第 2 轮 36 task ≥ 80%, **W27 PASS**) → 本文件直接前置
3. `docs/recruit/agent-task-validation-3-2027-03-01.md` (本文件, W30 第 6 retry, 3/1 第 3 轮 36 task ≥ 90%)
4. `docs/phase6/phase6-1-prd-2027-02-01.md` (W28 commit f713970, Phase 6.1 Marketplace PRD ~114KB, 3 agent Phase 6.1 任务依据)
5. `docs/skills/negotiation/skill4-v1-prd-2027-02-01.md` (W28 commit 8670417, Skill 4 v1 PRD ~30KB, 3 agent Skill 4 v1 任务依据)
6. `docs/phase6/phase6-1-backend-impl-2027-03-01.md` (W29 commit 1b07d88, Phase 6.1 backend 7 API + Marketplace 引擎 + 10 scenario, 3 agent 数据/前端任务实施基础)
7. `docs/skills/negotiation/skill4-v1-impl-2027-03-01.md` (W29 commit 2344816 + 848129d fix, Skill 4 v1 实施 4 模块 + 37 baseline, 3 agent Skill 4 v1 任务实施基础)
8. `docs/skills/contract-review/skill3-v3-prd-2027-02-01.md` (W25 commit cc14045, Skill 3 v3.0 多端+多语言+多律所 PRD, 3 agent 跨境文件 + 40+ 律所模板任务依据)
9. `docs/skills/contract-review/skill3-v3-launch-2027-02-01.md` (W26 commit ab59c49, Skill 3 v3.0 launch, 3 agent v3.0 多端 + 多语言任务依据)

### 7.2 复用的 commit

| Commit | 内容 | 复用比例 |
|--------|------|---------|
| **W27 commit 760e782** | agent-task-validation-2 2/1 3 agent 36 task ≥ 80% 第 2 轮验收 + W28 培训强化 2 周 + Phase 6.1 派发 (W27 第 3 retry PASS) | 60% (验收框架 + 5 维度评分 + 4 场景模板 + 培训强化 2 周模板 + Phase 6.1 派发模板) |
| **W23 commit 432a073** | agent-task-validation 1/1 首轮 18 task ≥ 60% + 4 场景分类 + 5 维度评分 + 时间线 | 15% (验收框架 + 5 维度评分 + 4 场景模板基础) |
| **W21 commit 0c8f01f** | agent-recruit-3 招聘三件套 (JD + candidates + onboarding) + 5 周培训 + 5 维度评分标准 | 10% (5 维度评分标准 + 培训流程) |
| **W28 commit f713970** | Phase 6.1 Marketplace PRD ~114KB (5 大方向 + Marketplace API 设计) | 5% (3 agent Phase 6.1 任务依据) |
| **W28 commit 8670417** | Skill 4 v1 PRD ~30KB (谈判场景 + Marketplace 集成) | 5% (3 agent Skill 4 v1 任务依据) |
| **W29 commit 1b07d88** | Phase 6.1 backend 7 API + Marketplace 引擎 + 10 scenario | 3% (3 agent 数据/前端任务实施基础) |
| **W29 commit 2344816 + 848129d** | Skill 4 v1 实施 4 模块 + 37 baseline | 2% (3 agent Skill 4 v1 任务实施基础) |

### 7.3 W30 同期交付文档

1. `docs/phase6/phase6-1-ui-impl-2027-03-01.md` (W30 commit df6efe6, ~12KB, Phase 6.1 UI 5 页面 + marketplace.js + marketplace.css)
   - 3/1 Phase 6.1 UI 实施: 5 HTML 页面 (lawyers + cases + referrals + cross-border + metrics, 881 行) + marketplace.js (1285 行 IIFE 封装 7 API + 5 维评分前端预览 + 3 弹窗 + Demo 兜底) + marketplace.css (223 行 10 大块) + router.js 5 视图注册 + index.html 侧边栏 Marketplace 入口 + tailwind.config.js 扫描扩展
2. `docs/skills/negotiation/skill4-v1-private-use-2027-03-15.md` (W30 commit d6c968f, ~12KB, Skill 4 v1 私域使用 + 10 baseline 实测)
   - 3/15 Skill 4 v1 私域使用: 50 律师私域 3 群体抽样 + 10 baseline 谈判场景 + 5 维度评分 + 转化率 + 律师满意度 + 4 应急

> **复用比例**: 60%+ 复用 W27 agent-task-validation-2 第 2 轮框架 + W23 agent-task-validation 首轮 + W21 agent-recruit-3 5 维度评分, 增量仅 W30 第 6 retry 启动 + 3/1 第 3 轮 36 task 详细验证 (2/1-3/1 累计, 新一个月) + ≥ 90% 进阶门槛 + W31 培训强化 2 周 (Phase 6.1 Marketplace + Skill 4 v1 + 谈判场景) + Phase 6.1 + Skill 4 v1 谈判场景派发.

---

## 8. 验收对齐 (Verify Prompt 6 项)

1. ✅ `agent-task-validation-3-2027-03-01.md` 完整 (3 agent 2/1-3/1 累计 36 task / 各 12 + 3/1 验收 KPI ≥ 90% + 进阶曲线 60% → 80% → 90% → 95% + 4 场景分类 + Mavis owner 综合评估 + 3 agent 现场汇报 + 应急 4 场景)
2. ✅ 12 个小 task / agent 完整 (UI 视觉+icon+配色+Skill 4 v1 视觉+v3.0 多语言+Phase 6.1 视觉总稿 / 前端 端到端组件+测试+Phase 6.1 Marketplace UI+Skill 4 v1 UI / 数据 数据看板+SQL+索引+备份+Marketplace metrics+Skill 4 数据)
3. ✅ 1/1 验收 ≥ 60% (W23) → 2/1 验收 ≥ 80% (W27 ✅ PASS) → 3/1 验收 ≥ 90% (本文件第 6 retry 启动) 进阶清晰, 4/1 期望 ≥ 95% (W31 接力)
4. ✅ W31 培训强化计划完整 (3/1-3/15 培训 2 周 + Phase 6.1 Marketplace + Skill 4 v1 + 谈判场景 + 3 agent 派发 Phase 6.1 Marketplace 上线 + Skill 4 v1 全量谈判场景任务)
5. ✅ 严守 fabricate 原则 (3/1 距今 245 天, 实际数字 forward-execute placeholder + [3/1 实测填实] 标注, **W30 0 fabricate**)
6. ✅ git log 显示 1+ agent-validation commit (W30 agent-task-validation-3 第 6 retry 1 commit)

---

## 9. W31 节点建议 (一句话)

> **W31 (3/1-3/15) 节点建议**:
> - **3/1-3/15 培训强化 2 周**: Phase 6.1 Marketplace (律师接案 / 文书模板分享 / 互相推荐 / 跨境文件 / 抽成 5% commission / 信任评价体系) + Skill 4 v1 谈判场景 (10 baseline: 合同纠纷 2 + 民事侵权 1 + 婚姻家庭 1 + 公司股权 1 + 知识产权 1 + 劳动仲裁 1 + 行政复议 1 + 跨境贸易 1 + 反向博弈演练 1) + 5 维度评分 (事实/法律/主张/时效/后果) + 4 维度风险标注 (法律/商业/关系/时间) + 3 agent 各派 4-6 个 Phase 6.1 Marketplace 上线 + Skill 4 v1 全量谈判场景实战 task + 3/15 二次验收 (延续 ≥ 90%, 为 4/1 ≥ 95% 铺路) + 4/1 转正升级"高级 agent" 准备 + 衔接 W32-W37 长期规划 (专家 agent → 团队 leader → 技术合伙人 → 200 律所 + 800 律师 + ¥200 万+ ARR 验证)

---

> **W30 agent-task-validation-3 3/1 3 Agent 独立完成率 ≥ 90% 第 3 轮验收完整 plan 落档** (W25+W26+W27+W28+W29 累计 5 retry, W30 第 6 retry 启动).
> 数字全部 [3/1 实测填实], owner 3/1 当天 09:00 patch 替换 placeholder. **W30 0 fabricate, 严守 forward-execute 规范**.
> 3 agent (UI 设计师 lex-design + 前端工程师 lex-coder-v2 + 数据工程师 lex-data-v2) 2/1-3/1 累计 36 task (各 12) + 3/1 验收独立完成率 ≥ 90% 验证 + 进阶曲线 (1/1 ≥ 60% → 2/1 ≥ 80% → 3/1 ≥ 90% → 4/1 ≥ 95%) + 4 场景分类 (A/B/C/D) + W31 培训强化 2 周 (Phase 6.1 Marketplace + Skill 4 v1 + 谈判场景) + Phase 6.1 + Skill 4 v1 谈判场景派发.
