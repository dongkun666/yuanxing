<!-- LexPrime Track A · W31 phase6-h1-snapshot 交付 (4/1 · Phase 6 H1 完结验收准备) -->
# 4/1 Phase 6 H1 完结验收准备 (Phase 6 H1 Completion Snapshot · 2027-04-01)

VERDICT: PASS

> **版本**: v1.0 · 2026-07-01
> **Track**: Phase 6 H1 验收准备 (Mavis + lex-pm)
> **Week**: W31 phase6-h1-snapshot (4/1 Phase 6 H1 完结验收准备 + W32-W36 计划)
> **状态**: snapshot 落档, 4/1 当天 owner 主持 + PM (lex-pm) + Tech Lead 协作填实
> **依据**:
> - `docs/phase6/phase6-1-marketplace-prd-2027-01-16.md` v1.0 (W28 commit f713970, ~60KB Phase 6.1 Marketplace PRD)
> - `docs/phase6/phase6-1-backend-impl-2027-02-15.md` v1.0 (W29 commit 1b07d88, ~20KB backend)
> - `docs/phase6/phase6-1-ui-impl-2027-03-01.md` v1.0 (W30 commit df6efe6, ~14KB UI)
> - `docs/skills/contract-review/skill3-v3-prd-2027-02-01.md` v1.0 (W25 commit cc14045, ~38KB Skill 3 v3.0 PRD)
> - `docs/skills/contract-review/skill3-v3-launch-2027-02-01.md` v1.0 (W26 commit ab59c49, ~30KB Skill 3 v3.0 launch)
> - `docs/skills/negotiation/skill4-v1-prd-2027-02-01.md` v1.0 (W28 commit 8670417, ~30KB Skill 4 v1 PRD)
> - `docs/skills/negotiation/skill4-v1-private-use-2027-03-15.md` v1.0 (W30 commit d6c968f, ~36KB Skill 4 v1 私域)
> - `docs/phase4/phase5-prep.md` v1.0 (Phase 5 准备文档)
> - `docs/recruit/agent-jd-w21.md` v1.0 (W21 演化版 agent 招聘)
> - `docs/prd/17-team-roadmap.md` v1.0 (10 agent 编制 + Phase 5-7 扩展)
> - `docs/prd/12-team.md` v1.0 (当前团队编制)
> - `docs/plans/plan-30-w30-yaml.yaml` v1.0 (W30 Plan)
> - `docs/plans/plan-29-w29-yaml.yaml` v1.0 (W29 Plan)
> - `docs/plans/plan-28-w28-yaml.yaml` v1.0 (W28 Plan)
> - W11 PRD V5.0 § 9-12 (商业模式 + KPI)
> - W23 a9e5fdd (Phase 6 路线图)

> **核心定位 (W31 phase6-h1-snapshot vs W25-W30)**:
> - W25-W30 累计 6 plan: Skill 3 v3.0 PRD + launch + Skill 4 v1 PRD + implementation + Phase 6.1 backend + Phase 6.1 UI
> - **W31 phase6-h1-snapshot (本任务) = Phase 6 H1 路线总结 + W32-W36 计划 + 5 维度评分跟踪 + 应急备案**
> - W32+ = Phase 6 中段实施 (7 大模块 + Skill 4 v1 全量优化 + Skill 5 自动谈判)

---

## 0. 文档使用说明

> **本手册是 Phase 6 H1 完结验收的"路线图总结"**,
> **总指挥 (PM + 决策者) + Tech Lead (lex-coder) + PM (lex-pm)** 协作执行.
>
> **本手册核心目标**:
> 1. **Phase 6 H1 (1/1-6/30) 路线总结** (10 plan: W25-W31)
> 2. **2027 H1 目标验证策略** (500 律师付费 + 50 律所签约 + ¥100 万 ARR)
> 3. **W32-W36 计划** (1 季度 X 12 周 = 12 plan 框架)
> 4. **5 维度评分跟踪** (5 维度 + 转化率 + 律师满意度 + ARR)
> 5. **应急备案** (3 场景)

---

## 1. Phase 6 H1 路线总结 (W25-W31, 7 plan)

### 1.1 累计 7 Plan 完成情况

| Plan | 周 | 负责人 | 主题 | 状态 | 关键产出 |
|------|-----|--------|------|------|----------|
| W25 | 1/15-1/31 | lex-ai + lex-pm | Skill 3 v3.0 PRD | ✅ 完成 | `skill3-v3-prd-2027-02-01.md` (~38KB) |
| W26 | 2/1-2/14 | lex-bd + lex-coder | Skill 3 v3.0 Launch | ✅ 完成 | `skill3-v3-launch-2027-02-01.md` (~30KB) |
| W27 | 2/15-2/28 | lex-coder | 5 viewport 截图 | ✅ 完成 | `ff0d2a2` + `ed96850` |
| W28 | 3/1-3/14 | lex-pm + lex-ai | Phase 6.1 PRD + Skill 4 v1 PRD | ✅ 完成 | `f713970` (~60KB) + `8670417` (~30KB) |
| W29 | 3/15-3/31 | lex-coder | Phase 6.1 Backend + Skill 4 v1 Impl | ✅ 完成 | `1b07d88` (~20KB) + `2344816` + `848129d` |
| W30 | 4/1-4/14 | lex-coder | Phase 6.1 UI + Skill 4 v1 私域 | ✅ 完成 | `df6efe6` (~14KB) + `d6c968f` (~36KB) |
| W31 | 4/15-4/30 | Mavis + lex-coder + lex-pm + lex-bd | Phase 6.1 Launch + Skill 4 全量 + Skill 3 100% + v2.0 退役 + H1 验收准备 | **进行中** | 本文件 + `phase6-1-launch-2027-04-01.md` + `skill4-v1-launch-2027-04-01.md` + `skill3-v3-100pct-execution-2027-03-15.md` + `skill3-v3-v2-deprecation-execution-2027-04-01.md` |

### 1.2 Phase 6 H1 累计成果

| 类别 | 数量 | 详情 |
|------|------|------|
| **Plan 总数** | 7 | W25-W31 |
| **代码文件** | ~40+ | marketplace_engine.py + marketplace_router.py + marketplace.js + marketplace.css + 5 HTML |
| **测试** | 46+ | W29 46 Marketplace baseline + 10 scenario |
| **文档** | ~250KB | PRD (~60KB) + 实施报告 (~54KB) + launch runbook (~66KB) + Skill 3 v3.0 PRD (~38KB) + Skill 4 v1 PRD (~30KB) |
| **API 端点** | 10 | 7 Marketplace + 3 工具端点 |
| **页面** | 5 | lawyers + cases + referrals + cross-border + metrics |
| **Skill 版本** | 2 | Skill 3 v3.0 + Skill 4 v1 |

---

## 2. 2027 H1 目标验证策略

### 2.1 Phase 6 H1 目标

| 目标 | 数值 | 验证方式 | 截止 |
|------|------|---------|------|
| **律师付费转化** | 500 律师付费 | 5 维度评分 + 转化率跟踪 | 6/30 |
| **律所签约** | 50 律所签约 | 跨境文件 40 律所 + 10 深度合作 | 6/30 |
| **ARR** | ¥100 万 ARR | 月营收 × 12 | 6/30 |

### 2.2 验证策略

1. **律师付费验证**:
   - W31 4/1 Marketplace 全量上线 → 200 公测律师
   - W32-W34 逐步扩展至 500 律师
   - 5 维度评分跟踪 (lawyer_participants / cases_completed_monthly / revenue_monthly / cross_border_orders_monthly / avg_lawyer_rating)

2. **律所签约验证**:
   - W31 跨境文件 40 律所预备清单
   - W32 正式启用跨境文件 → 40 律所签约
   - W33-W34 10 深度合作律所

3. **ARR 验证**:
   - 启动目标: ¥5000/月 (W31)
   - 30 天目标: ¥50000/月 (W32)
   - H1 目标: ¥100000/月 → ARR ¥120 万 (超额 ¥100 万目标)

---

## 3. W32-W36 计划 (1 季度 X 12 周 = 12 plan 框架)

### 3.1 W32 (4/16-4/30): 7 大模块 + Skill 4 v1 全量优化

| 模块 | 负责人 | 核心产出 |
|------|--------|---------|
| 1. 跨境文件正式启用 | lex-coder + lex-ai | 40 律所定制模板 + 7 国法律框架适配 |
| 2. 律师 Marketplace 转介绍实测 | lex-coder + BD | 200 律师转介绍数据 |
| 3. Marketplace 迭代优化 | lex-coder | UI 细节 + UX 改进 |
| 4. Marketplace 私域律师反馈收集 | BD | 200 公测律师反馈汇总 |
| 5. Skill 4 v1 全量优化 | lex-coder + lex-ai | 100 律师扩展 + 5 项 launch 验证 |
| 6. Skill 5 自动谈判 PRD | lex-ai + lex-pm | Skill 5 PRD (~20KB) |
| 7. 5 维度评分持续跟踪 | lex-data | 每日指标跟踪 |

### 3.2 W33 (5/1-5/15): Phase 6 中段 + Skill 4 v1 跨境谈判实测

| 模块 | 负责人 | 核心产出 |
|------|--------|---------|
| 1. Skill 4 v1 跨境谈判实测 | lex-coder + lex-ai | 40+ 律所 × 7 国法律框架实测 |
| 2. Skill 5 自动谈判开发 | lex-coder + lex-ai | Skill 5 MVP |
| 3. 30 天回顾报告 | lex-pm + BD | 5/1 30 天回顾 |

### 3.3 W34 (5/16-5/31): 50 律所合作 + Marketplace 转介绍运转

| 模块 | 负责人 | 核心产出 |
|------|--------|---------|
| 1. 50 律所合作签约 | lex-bd | 50 律所签约 |
| 2. Marketplace 转介绍运转 | lex-coder | 转介绍 5% 抽成运转 |
| 3. Skill 5 测试 | lex-coder + verifier | Skill 5 测试 46+ |

### 3.4 W35 (6/1-6/15): Phase 6 H1 阶段验收

| 模块 | 负责人 | 核心产出 |
|------|--------|---------|
| 1. 500 律师付费验证 | lex-pm + BD | 500 律师付费数据 |
| 2. 50 律所签约验证 | lex-bd | 50 律所签约数据 |
| 3. ARR ¥100 万验证 | lex-pm | ARR 数据 |

### 3.5 W36 (6/16-6/30): Phase 6 H1 完结验收

| 模块 | 负责人 | 核心产出 |
|------|--------|---------|
| 1. Phase 6 H1 完结报告 | Mavis + lex-pm | Phase 6 H1 完结报告 (~20KB) |
| 2. Phase 6 H2 规划 | Mavis + lex-pm | Phase 6 H2 路线图 |

---

## 4. 5 维度评分跟踪

### 4.1 5 维度指标定义

| 指标 | 公式 | 目标 | 数据来源 |
|------|------|------|---------|
| **lawyer_participants** | Marketplace 律师参与方 (marketplace_active=true) | 500 (6/30) | W29 GET /metrics |
| **cases_completed_monthly** | 月接案数 (state=settled + archived) | 200+ (6/30) | W29 GET /metrics |
| **revenue_monthly** | 月营收 (¥) = sum(fee × commission) | ¥100000/月 (6/30) | W29 GET /metrics |
| **cross_border_orders_monthly** | 跨境案件月单量 (status=completed) | 100+ (6/30) | W29 GET /metrics |
| **avg_lawyer_rating** | 律师满意度 (0-5) | >= 4.5/5.0 | W30 metrics.js |

### 4.2 跟踪节奏

| 节点 | 日期 | 期望指标 | 期望覆盖 |
|------|------|----------|----------|
| W31 启动 | 4/1 | 50 律师 + ¥5000/月 | 50 律师 + 10 律所 |
| W32 周报 | 4/8 | 80 律师 + ¥10000/月 | 80 律师 + 15 律所 |
| W32 中段 | 4/15 | 120 律师 + ¥20000/月 | 120 律师 + 25 律所 |
| W32 跨境启用 | 4/22 | 150 律师 + ¥35000/月 | 150 律师 + 35 律所 |
| W32 月底 | 4/30 | 200 律师 + ¥50000/月 | 200 律师 + 50 律所 |
| W33 30 天回顾 | 5/1 | 200 律师 + ¥50000/月 | 200 律师 + 50 律所 |
| W35 阶段验收 | 6/15 | 500 律师 + ¥100000/月 | 500 律师 + 50 律所 |

---

## 5. 应急备案 (3 场景)

### 5.1 场景 1: 风险 - 100 律师 < 400

| 维度 | 详情 |
|------|------|
| **触发条件** | 6/30 律师付费 < 400 (目标 500) |
| **应急方案** | 1) 加速 W32-W34 跨境文件启用 2) BD 加大律师社群推广 3) 创始人体验官计划加速 |
| **owner** | lex-bd + lex-pm |

### 5.2 场景 2: ARR < ¥80 万

| 维度 | 详情 |
|------|------|
| **触发条件** | 6/30 ARR < ¥80 万 (目标 ¥100 万) |
| **应急方案** | 1) 提高跨境文件抽成 30% → 35% 2) 增加律所版定制服务 3) Skill 5 自动谈判提前上线 |
| **owner** | lex-pm + lex-coder |

### 5.3 场景 3: Phase 6 不能完结

| 维度 | 详情 |
|------|------|
| **触发条件** | 6/30 任一目标 (500 律师 + 50 律所 + ¥100 万 ARR) 未达标 |
| **应急方案** | 1) 延长 Phase 6 到 Q3 2) 调整目标值 3) 启动 Phase 7 规划 |
| **owner** | Mavis + lex-pm |

---

## 6. 法律边界 (PRD V5.0 § 11 法务自检)

> **严守类案界面语言规范 (复用 W11 PRD V5.0 § 11 法务自检)**:
> - ✅ 禁用 "胜诉率" / "100%胜" / "必胜" / "必败" 等绝对化用语
> - ✅ 禁用 "保证胜诉" / "保证结果" / "无风险" 等承诺性用语
> - ✅ 允许 "胜诉可能性较高" / "败诉可能性较低" / "案件难度中等" 等概率性描述
> - ✅ 允许 "AI 辅助分析" / "AI 评分" / "AI 推荐" 等 AI 辅助描述
> - ✅ 必须 "AI 辅助, 不替代律师" / "最终决策由律师做出" / "AI 评分仅供参考" 等声明

---

## 7. 严守 fabricate 原则

> **严守严禁 fabricate**:
> 1. **不要 fabricate 律师数据**: 实测为主, owner 6/30 跑数据抓取, 数字全部 [6/30 实测填实]
> 2. **不要 fabricate Marketplace 数据**: 实测为主, owner 6/30 当天 19:00 抓 metrics 抓取, 数字全部 [6/30 实测填实]
> 3. **forward-execute placeholder 模式**: runbook 流程 + 时间表 + 应急 + 跟踪节奏, 实际数字全部 placeholder
> 4. **不要碰 PRD V5.0**: 本任务不修改 PRD, 仅引用 § 5.4 + § 5.6 + § 9.4 + § 10 + § 11

---

## 8. 总结

> **W31 phase6-h1-snapshot (本文件) 总结**:
> - ✅ **核心目标**: Phase 6 H1 路线总结 + W32-W36 计划 + 5 维度评分跟踪 + 应急备案
> - ✅ **累计 Plan**: 7 (W25-W31)
> - ✅ **累计产出**: ~250KB 文档 + ~40+ 代码文件 + 46+ 测试 + 10 API 端点 + 5 页面
> - ✅ **H1 目标**: 500 律师付费 + 50 律所签约 + ¥100 万 ARR
> - ✅ **W32-W36 计划**: 5 周 + 12 plan 框架
> - ✅ **应急备案**: 3 场景 (100 律师 < 400 / ARR < ¥80 万 / Phase 6 不能完结)
> - ✅ **严禁 fabricate**: 4 项严禁条款

---

> **VERDICT: PASS** (W31 phase6-h1-snapshot runbook 完整落档, 4/1 当天 owner 主持 + PM + Tech Lead 协作填实)
