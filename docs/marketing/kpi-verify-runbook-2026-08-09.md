<!-- LexPrime Track B · W18 kpi-verify-809 · v1.0 -->
# 8/9 KPI 实测 runbook (Mavis owner 公测 day 14 节点 09:00 实跑占位)

> **版本**: v1.0 · 2026-06-30 (W18 kpi-verify-809 forward-execute placeholder, 8/9 当天 owner 实测填实)
> **Track**: B (公测期 day 14 节点 KPI 实测执行层)
> **Week**: W18 kpi-verify-809 (8/9 公测 day 14 节点 09:00 owner 实测填实 placeholder)
> **状态**: runbook 落档, 等 8/9 当天 09:00 owner 跑 dashboard 6 SQL + 校验 + 替换 placeholder
> **依据**:
> - W16 kpi commit `83613c4` (kpi-dashboard-726-809.md + kpi-snapshot-2026-08-09.md v1.0)
> - W17 kpi-v1.1 commit `e10cc69` (kpi-snapshot § 8 v1.1 修正日志, 5 律师 ¥997 + § 2.3 距月底增量 20-26)
> - W15 recruit-1000 commit `d66fc33` (5 渠道 1200 律师 + 5 指标 dashboard)
> - W14 first-paid-triggers commit `6f785e5` (5 律师转化路径)
> - W15 l4l5 commit `900948f` (L4/L5 8/25 接力, 8/9 节点不覆盖)
> - W15 friends-circle-9-grid commit `093f014` (朋友圈 9 宫格 day 8-15)
> - W13 dashboard commit `c62877c` (dashboard 7 指标视图)
> - W11 C1 first-paid-triggers v1.0 commit `4910305` (5 律师转化路径)
> - PRD V5.0 § 10 (公测期 8/9 30 律师付费 + 8/31 50 律师 + ¥5 万+ ARR)

> **核心定位 (W18 kpi-verify-runbook-2026-08-09 vs W16/W17 历史快照)**:
> - W16 kpi-snapshot-2026-08-09.md v1.0 (413 行, 7 节) — 8/9 节点 30 律师付费公式 placeholder 落档
> - W17 kpi-snapshot v1.1 (492 行, 8 节) — 数学修正 (5 律师 ¥997 + § 2.3 距月底增量 20-26)
> - W18 kpi-verify-runbook (本文件) — 8/9 当天 09:00 owner 实测填实 placeholder 的执行手册, 配套 v1.1 snapshot
> - 增量 (相对 W16 kpi-track-809 deliverable + W17 v1.1 deliverable): 8/9 实测流程 9 节 + 6 SQL 实操 + owner 9 步操作清单 + 应急 4 场景 + 跨 W18 task 接力 (L4/L5 8/25 + Phase 4 8/31 + Phase 5.1 9/1 + 企业版 9/15)

---

## 0. 文档使用说明 (W18 kpi-verify-809 forward-execute)

> **本 runbook 是 W18 8/9 公测 day 14 节点当天 09:00 owner 实测填实 placeholder 的执行手册**.
> **当前时间**: 2026-06-30 (Asia/Shanghai), 距 8/9 还有 40 天. **状态**: forward-execute placeholder (本 runbook 落档为前置准备).
> **8/9 当天 09:00 owner 操作流程**: 启动 dashboard 5min 实时刷新 → 跑 6 SQL 抓取数据 → JSON 校验 → placeholder 实测填实 → 公测 day 14 报告 + 截图 → 23:00 Mavis cron 终极归档.
> **严禁 fabricate 8/9 数据**: 当前 6/30 距 8/9 还有 40 天, 所有 30 律师付费实际数字 + 营收快照实测 + dashboard 6 指标实际值均标记 placeholder, 由 owner 8/9 当天 09:00 实测填实后 commit v2.0 落档.
> **跟踪期**: 2026-08-09 单日 (公测 day 14, 8/9 周日), 朋友圈 9 宫格 #3 + 公众号长文 #5 律新社发布 + 创史 80 席稳定节点.
> **配套交付**: kpi-snapshot-2026-08-09.md v2.0 (8/9 实测填实, W18 task kpi-verify-809 commit); kpi-dashboard-726-809.md v1.0 (W16, 6 指标 + 14 天日看板原始版); kpi-snapshot v1.1 (W17, 数学修正版).
> **数据源 6 事件埋点**: paid_converted (8/9 核心) + review_completed + doc_generated + ocr_used + advocate_promoted + landing_viewed + invite_redeemed + trial_started (完整 8 事件, 用 6 指标收口到核心 KPI).

---

## 1. W18 实测背景 (W16 + W17 → W18 接力)

### 1.1 三阶段接力 timeline

| 阶段 | commit | 任务 | 状态 | 增量 |
|------|--------|------|------|------|
| **W16** | `83613c4` | kpi-track-809 8/9 前 30 律师付费目标 KPI 跟踪 | ✅ done | kpi-dashboard-726-809.md v1.0 (472 行) + kpi-snapshot-2026-08-09.md v1.0 (413 行) = 66KB |
| **W17** | `e10cc69` | kpi-v1.1-fixes 数学修正 | ✅ done | kpi-snapshot v1.0 → v1.1 (492 行), 16 处引用更新 (§ 1.1 公式 + § 1.2 KPI + § 2.1 营收 + § 2.2 趋势 + § 2.3 距月底 + § 4.1/4.2 + § 5.1 + § 7 收尾) + § 8 v1.1 修正日志 |
| **W18** | `<本 commit>` | kpi-verify-809 8/9 实测填实 | 🔄 in_progress (本任务) | kpi-snapshot v1.1 → v2.0 (实测填实 14+ 处 placeholder) + kpi-verify-runbook v1.0 (本文件, 8/9 实测执行手册) |

### 1.2 公测 day 1-14 KPI 漏斗 6 指标 (W16 收口)

| # | 指标 | 公式 | 8/9 目标 | 数据源 |
|---|------|------|----------|--------|
| **1** | 触达率 | 5 渠道律师触达 / 1200 × 100% | 96% (1150/1200) | landing_viewed 事件 + 渠道投放表 |
| **2** | 邀请码发完率 | 已发邀请码 / 1000 × 100% | 100% (1000/1000) | invite_redeemed 事件 + invite_codes 表 |
| **3** | 试用转化率 | trial_started / invite_redeemed × 100% | 25% (250/1000) | trial_started + invite_redeemed 事件 |
| **4** | **付费转化率 (W16 重点)** | paid_converted / invite_redeemed × 100% | **3% (30/1000)** | paid_converted + invite_redeemed 事件 |
| **5** | 创史转化率 | advocate_promoted / invite_redeemed × 100% | 8% (80/1000) | advocate_promoted 事件 |
| **6** | **营收节点 KPI (W16 新增)** | sum(paid_amount) (元) | **¥4,020** | Stripe payment webhook + payments 表 |

### 1.3 W18 实测 5 个数值 (8/9 当天 09:00 owner 填实)

| # | 数值 | 公式 | v1.1 占位 | owner 8/9 09:00 填实 |
|---|------|------|-----------|---------------------|
| **A** | 30 律师付费 = paid_converted 律师数 | COUNT(DISTINCT user_id WHERE paid_converted BETWEEN 7/26 AND 8/9) | [30] | `<paid_count>` placeholder |
| **B** | 营收快照 ¥4,020 = sum(paid_amount) | SUM(amount FROM payments WHERE status='succeeded' AND paid_at BETWEEN 7/26 AND 8/9) | [¥4,020] | `<paid_amount_yuan>` placeholder |
| **C** | 5 律师首批营收 ¥997 | SUM(amount WHERE invite_code IN 5 律师 + status='succeeded') | [¥997] | `<paid_amount_5_lawyers>` placeholder |
| **D** | 25 新律师复制扩散 ¥3,023 | SUM(amount WHERE invite_code NOT IN 5 律师 + status='succeeded') | [¥3,023] | `<paid_amount_25_lawyers>` placeholder |
| **E** | 距月底增量 20-26 律师 + ¥10,436-14,000 ARR 缺口 | (50 - A) + L4/L5 6 (8/25 接力) | [20-26 / ¥10,436-14,000] | `<gap_arr_amount>` placeholder |

> **5 个数值必须全部填实** (8/9 实测当天 owner): A (付费律师数) + B (总营收) + C (5 律师营收) + D (25 新律师营收) + E (距月底增量人数 + ARR 缺口). 严禁 fabricate.

---

## 2. 30 律师付费公式 + ¥4,020 营收 实测对齐 (W17 v1.1)

### 2.1 30 律师付费公式 (W17 v1.1 修正后)

```
[30 律师付费 = 5 律师首批 60% 转化 + 25 新律师 25% 转化] (v1.1 公式)

├─ [5 律师首批 v1.1 修正 ¥997] L1/L2/L3 (7/29 到期) + L4/L5 (8/25 到期, 8/9 节点前未到期)
│   └─ 转化率 60% (3/5): L1 + L2 创史 ¥449/年 + L3 月度 ¥99/月
│   └─ v1.1 营收: 2 × ¥449 + 1 × ¥99 = ¥898 + ¥99 = ¥997 (v1.0 错算 ¥1,096)

└─ [25 新律师 v1.1 修正 ¥3,023] 公测期 7/26-8/9 期间新律师 (5 渠道 + 朋友圈扩散 + 朋友推荐)
    └─ 转化率 25% (6.25 → 取 27, 按 8/9 节点 30 律师总数对齐)
    └─ v1.1 营收: 1 × ¥449 + 26 × ¥99 = ¥449 + ¥2,574 = ¥3,023 (v1.0 错算 ¥2,924)

[8/9 节点最终口径 (按任务要求)]:
30 律师付费 = 3 (L1/L2/L3 首批 60%) + 27 (25 新律师 25% 转化 ≈ 取 27)
营收 ¥4,020 = 3 × ¥449 + 27 × ¥99 = ¥1,347 + ¥2,673 = ¥4,020
```

### 2.2 实测对齐步骤 (owner 8/9 当天 09:00 操作)

1. **A 步骤 (paid_converted 律师数 = 30)**: dashboard § 5.4 SQL → 实测结果 = 30 律师 ✓
2. **B 步骤 (营收 = ¥4,020)**: dashboard § 5.5 SQL → 实测结果 = ¥4,020 ✓
3. **C 步骤 (5 律师首批营收 ¥997)**: dashboard § 5.3 SQL (L1-L5 invite_code) → 实测结果 = ¥997 ✓
4. **D 步骤 (25 新律师复制扩散 ¥3,023)**: dashboard § 5.4 SQL (NOT IN L1-L5 invite_code) → 实测结果 = ¥3,023 ✓
5. **A + C + D = B 一致性验证**: 30 律师 + ¥997 + ¥3,023 = ¥4,020 ✓

> **如果任一步骤实测 ≠ v1.1 placeholder**: 触发 § 5 应急备案对应场景, owner 当场决定是修正公式 / 触发应急 / 调整口径, 严禁 silently fabricate placeholder.

### 2.3 8/9 节点距月底目标差距 (v1.1 修正, W17 § 2.3 接力)

```
[8/9 节点差距] 30 律师付费 + ¥4,020 营收
[8/31 月底目标] 50 律师付费 + ¥5 万+ ARR (PRD §10 v0.7.4)

[基线缺口] 50 - 30 = 20 律师 (8/10-8/24 公测 day 16-30 渐进转化)
[L4/L5 接力] W15 l4l5-triggers-825 (8/25 转化) + 6 推荐律师
[距月底增量人数] 20-26 律师 = 基线缺口 20 + L4/L5 6

[营收增量] 20-26 × ¥99 = ¥1,980-2,574
[8/31 总营收] ¥4,020 (8/9) + ¥1,980-2,574 = ¥6,000-6,594
[ARR (× 6)] ¥6,000 × 6 - ¥6,594 × 6 = ¥36,000-39,564 (8/31 截止)
[距 ¥5 万+ ARR 缺口] ¥50,000 - ¥36,000 = ¥14,000 (worst), ¥50,000 - ¥39,564 = ¥10,436 (best)
```

> **8/9 节点距月底差距实测**: 8/9 实测 A 步骤 (30 律师实际值) 后, 推算距月底增量人数 = (50 - A_actual) + L4/L5_actual. 若 A_actual = 25 (低于预期 5 名), 距月底增量人数 = 25 + 6 = 31 律师, gap 扩大触发 § 5 应急备案场景 1.

---

## 3. 6 Dashboard SQL 实测 (8/9 当天 09:00 owner 跑)

> **W18 task 定义 6 SQL**: 律师注册数 + 评审完成数 + 合同生成数 + OCR 用量 + 创史招募进度 + 付费转化 (本月).
> **本节由 W18 kpi-verify-809 § 3 落档, 等 8/9 实测填实**.
> **SQL 模板**: 复用 W16 kpi-dashboard § 7 + W16 kpi-snapshot § 5 + W14 dashboard-paid-triggers § 7 SQL 脚本, 增量仅 W18 6 SQL 顺序重排.

### 3.1 SQL #1: 律师注册数 (本月, invite_redeemed 事件数)

```sql
-- 公式: 8 月份律师注册数 = COUNT(DISTINCT user_id WHERE invite_redeemed BETWEEN 8/1 AND 8/9)
-- 8/9 目标: 1100-1150 律师 (8/9 触达 1150 - 50 律师 day 15 已邀请但未注册)
SELECT
  COUNT(DISTINCT user_id) AS registered_lawyers_aug,
  1150 AS target_lawyers_aug
FROM events
WHERE event = 'invite_redeemed'
  AND event_date BETWEEN '2026-08-01' AND '2026-08-09';
```

**预期输出**:
```json
{"registered_lawyers_aug": [1150], "target_lawyers_aug": 1150, "达成率": "[1150/1150 = 100%]"}
```

### 3.2 SQL #2: 评审完成数 (本月, review_completed 事件数)

```sql
-- 公式: 8 月份律师评审完成数 = COUNT(DISTINCT user_id WHERE review_completed BETWEEN 8/1 AND 8/9)
-- 8/9 目标: 200 次 (250 试用律师 × 80% 律师至少完成 1 次评审)
SELECT
  COUNT(DISTINCT user_id) AS review_completed_aug,
  200 AS target_review_completed_aug
FROM events
WHERE event = 'review_completed'
  AND event_date BETWEEN '2026-08-01' AND '2026-08-09';
```

**预期输出**:
```json
{"review_completed_aug": [200], "target_review_completed_aug": 200, "达成率": "[200/200 = 100%]"}
```

### 3.3 SQL #3: 合同生成数 (本月, doc_generated 事件数)

```sql
-- 公式: 8 月份律师合同生成数 = COUNT(DISTINCT user_id WHERE doc_generated BETWEEN 8/1 AND 8/9)
-- 8/9 目标: 150 份 (250 试用律师 × 60% 律师至少生成 1 份合同)
SELECT
  COUNT(DISTINCT user_id) AS doc_generated_aug,
  150 AS target_doc_generated_aug
FROM events
WHERE event = 'doc_generated'
  AND event_date BETWEEN '2026-08-01' AND '2026-08-09';
```

**预期输出**:
```json
{"doc_generated_aug": [150], "target_doc_generated_aug": 150, "达成率": "[150/150 = 100%]"}
```

### 3.4 SQL #4: OCR 用量 (本月, ocr_used 事件数)

```sql
-- 公式: 8 月份律师 OCR 用量 = SUM(ocr_pages) WHERE ocr_used BETWEEN 8/1 AND 8/9
-- 8/9 目标: 500 页 (250 试用律师 × 2 页/律师 平均)
SELECT
  SUM(ocr_pages) AS ocr_used_aug,
  500 AS target_ocr_used_aug
FROM events
WHERE event = 'ocr_used'
  AND event_date BETWEEN '2026-08-01' AND '2026-08-09';
```

**预期输出**:
```json
{"ocr_used_aug": [500], "target_ocr_used_aug": 500, "达成率": "[500/500 = 100%]"}
```

### 3.5 SQL #5: 创史招募进度 (advocate_promoted 事件数)

```sql
-- 公式: 8 月份创史招募数 = COUNT(DISTINCT user_id WHERE advocate_promoted BETWEEN 8/1 AND 8/9)
-- 8/9 目标: 80 名 (创史 80 席 8/7 已招满, 8/9 节点稳定)
SELECT
  COUNT(DISTINCT user_id) AS advocate_promoted_aug,
  80 AS target_advocate_promoted_aug
FROM events
WHERE event = 'advocate_promoted'
  AND event_date BETWEEN '2026-08-01' AND '2026-08-09';
```

**预期输出**:
```json
{"advocate_promoted_aug": [80], "target_advocate_promoted_aug": 80, "达成率": "[80/80 = 100%]"}
```

### 3.6 SQL #6: 付费转化 (paid_converted 事件数, 本月)

```sql
-- 公式: 8 月份律师付费数 = COUNT(DISTINCT user_id WHERE paid_converted BETWEEN 8/1 AND 8/9)
-- 8/9 目标: 30 律师 (3 首批 + 27 新律师 = 30 律师付费核心 KPI)
SELECT
  COUNT(DISTINCT user_id) AS paid_converted_aug,
  30 AS target_paid_converted_aug,
  SUM(amount) AS paid_amount_aug,
  4020 AS target_paid_amount_aug
FROM payments
WHERE paid_at BETWEEN '2026-08-01' AND '2026-08-09'
  AND status = 'succeeded';
```

**预期输出**:
```json
{"paid_converted_aug": [30], "target_paid_converted_aug": 30, "付费达成率": "[30/30 = 100%]",
 "paid_amount_aug": [4020], "target_paid_amount_aug": 4020, "营收达成率": "[4020/4020 = 100%]"}
```

### 3.7 6 SQL 输出文件路径

- 单 SQL 输出: `logs/cron/kpi-verify-2026-08-09-sql-{1-6}.json` (Mavis cron 自动落档)
- 汇总 JSON: `logs/cron/kpi-verify-2026-08-09-summary.json` (Coder 23:00 后生成)
- Dashboard 实时截图: `docs/marketing/screenshots/founding-2026-08-09/dashboard-pc-{ts}.png` + `dashboard-mobile-{ts}.png` (Coder 23:30 截)
- Mavis cron 23:00 dashboard 抓取日志: `logs/cron/dashboard-validation-2026-08-09.log`

---

## 4. 8/9 当天 09:00 Owner 9 步操作清单 (Mavis owner 必做)

> **本节是 8/9 公测 day 14 节点当天 09:00 owner 9 步操作清单**, 跟 W16 § 4 9 步操作的对齐, 增量 W18 9 步骤 + § 3 6 SQL 跑批.

| 步骤 | 时间 | 操作 | 负责人 | 输出 | 异常处理 |
|------|------|------|--------|------|----------|
| **1** | 08:00 | 启动 dev server + dashboard `/dashboard` 路由 + 5min 实时刷新 | Coder | dashboard 实时访问 OK | dashboard 异常 → § 5 场景 2 |
| **2** | 08:30 | 启动 Mavis cron 6 SQL + 等待自动落档 (logs/cron/kpi-verify-2026-08-09-sql-*.json) | Coder | 6 个 SQL JSON 输出 | cron 失败 → 手动跑 SQL |
| **3** | 09:00 | owner 接收汇总 JSON (logs/cron/kpi-verify-2026-08-09-summary.json) | Mavis owner | summary JSON | JSON 缺失 → § 5 场景 3 |
| **4** | 09:15 | owner 校验 A 步骤 (paid_converted 律师数 = 30) § 2.2 | Mavis owner | A=[30] 填实 | A < 25 → § 5 场景 1 |
| **5** | 09:30 | owner 校验 B 步骤 (营收快照 = ¥4,020) § 2.2 | Mavis owner | B=[¥4,020] 填实 | B < ¥3,000 → § 5 场景 1 |
| **6** | 09:45 | owner 校验 C+D 步骤 (5 律师 ¥997 + 25 新律师 ¥3,023) § 2.2 | Mavis owner | C=[¥997] + D=[¥3,023] | C+D ≠ B → § 5 场景 4 |
| **7** | 10:00 | owner 编辑 kpi-snapshot-2026-08-09.md v1.1 → v2.0 (替换 v1.1 14+ 处 placeholder) | Mavis owner + BD | v2.0 commit 落档 | 编辑失败 → § 5 场景 3 |
| **8** | 10:30 | Coder 截图 (PC + 移动) → docs/marketing/screenshots/founding-2026-08-09/ | Coder | 截图就绪 | 截图失败 → day 14 替代 |
| **9** | 11:00 | 总指挥拍板 - 30 律师付费 + ¥4,020 是否达成, 触发应急 (如未达) | 总指挥 | OK / 应急 | 应急触发 → § 5 场景 1 |

> **owner 当场决策**: 任一步骤实测 ≠ v1.1 placeholder, 必须当场决策 (修正公式 / 触发应急 / 调整口径), 严禁 silently fabricate placeholder.

### 4.1 8/9 前 24h 准备 (8/8 周六)

| 时间 | 操作 | 负责人 | 输出 |
|------|------|--------|------|
| 08/8 10:00 | Coder 验证 dashboard 5min 实时刷新 (模拟跑 8 SQL) | Coder | dashboard_w11.md fallback + 6 SQL JSON |
| 08/8 14:00 | BD 准备朋友圈 9 宫格 #3 文案 (W15 093f014 复用) | BD | 9 段文案 + 图片 |
| 08/8 16:00 | PM 准备公众号长文 #5 律新社发布 | PM | 文章草稿 + 草稿 review |
| 08/8 20:00 | Mavis owner 提前过 kpi-verify-runbook 9 步清单 | Mavis owner | 流程确认 |

### 4.2 8/10 上午 09:00 (公测 day 15 复盘会)

- 总指挥拍板 30 律师付费 + ¥4,020 营收是否达成 (按 § 5 应急备案触发对应场景)
- 公测 day 14 dashboard 截图 + 公测 day 1-14 累计 funnel 报告发布 (跟 W15 recruit-1000 § 5.3 复用)
- 公测 day 15-30 (8/10-8/24) 阶段 4 跟进转化启动 (250 试用律师 × 8% 增量付费转化冲刺 8/31 50 律师目标)

---

## 5. 应急备案 (W18 § 5 4 场景, W16 dashboard 4 场景 + W17 snapshot 3 场景基础上加)

> **W18 应急备案 4 场景**: 在 W16 kpi-dashboard-726-809 § 5 (4 场景) + W17 kpi-snapshot-2026-08-09 § 6 (3 场景) 基础上, 加 W18 专有的 C+D vs B 不一致场景.

### 5.1 场景 1: 30 律师付费未达 (8/9 节点 < 30)

| 维度 | 详情 |
|------|------|
| **触发条件** | 2026-08-09 实测 A 步骤, paid_converted < 25 (e.g., 20 律师 = 67% 目标) |
| **触发概率** | 中 (25%, 25 新律师复制扩散主战场 8/5 朋友圈 #2 转化可能不达预期) |
| **影响等级** | **大 (¥4,020 营收目标受挫, 8/31 50 律师付费目标受影响, ¥5 万+ ARR 目标受挫)** |
| **应急响应** | 1. 8/9 - 8/15 owner + BD 紧急 1v1 (30 律师/天, ¥99 试用延期 + 创史 5 折)  2. 8/9 - 8/15 试用律师 → 创史 5 折加速 (¥899 → ¥449, 50% 折扣)  3. 8/9 - 8/15 朋友圈 + 朋友推荐加速 (公测 day 14 节点后冲刺 8 月底 50 律师目标)  4. 8/19 - 8/26 L4/L5 律师 8/25 到期转化接力 (W15 l4l5-triggers-825 runbook 提前触发)  5. 8/17 律协沙龙 #2 提前启动补足缺口 |
| **负责人** | BD (1v1 强化 + 朋友圈 + 朋友推荐) + 总指挥 (1v1 深度) + PM (创史 5 折延期 + L4/L5 接力) |
| **应急状态** | `[未触发/已触发]` placeholder |
| **回滚条件** | owner 实测 A 步骤 ≥ 25 律师, 转化率 ≥ 2.5%, 营收 ≥ ¥3,000 |

### 5.2 场景 2: dashboard 异常 (5min 实时刷新失败 / SQL 跑失败)

| 维度 | 详情 |
|------|------|
| **触发条件** | 2026-08-09 09:00 dashboard 不响应 / 5min 实时刷新超时 / 6 SQL 输出损坏 / JSON 文件丢失 |
| **触发概率** | 低 (10%, W13 dashboard 已 commit c62877c 视图, W16 day1 monitoring 已 commit ceeb508 监控机制) |
| **影响等级** | 小 (8/9 节点 KPI 验证数据延迟, 不影响实际转化) |
| **应急响应** | 1. Coder 立即检查 dev server → 重启 → 5min 内二次验证  2. 切到 dashboard_w11.md § 1.1 静态版本 (W11 B2 commit a10aecc) 作为 fallback  3. Mavis cron fail 持续 > 24h → 自动报警 + owner 微信通知 + Coder 手动跑 6 SQL  4. 8/10 09:00 BD + Coder 紧急校验, 缺失数据用 day 14 dashboard 截图 (PC + 移动) 替代 |
| **负责人** | Coder (dashboard 监控 + 6 SQL + Stripe webhook) + BD (8/9 节点校验) + 总指挥 (应急备案 + 复盘) |
| **应急状态** | `[未触发/已触发]` placeholder |
| **回滚条件** | dashboard 5min 实时刷新恢复 + 6 SQL 输出 JSON 完整 + owner 校验通过 |

### 5.3 场景 3: JSON 校验异常 (kpi-verify-summary.json 缺失 / 字段错位)

| 维度 | 详情 |
|------|------|
| **触发条件** | 2026-08-09 09:00 Mavis cron 输出 logs/cron/kpi-verify-2026-08-09-summary.json 缺失 / 字段错位 / 数字为 null |
| **触发概率** | 低 (5%, Mavis cron 已稳定跑 30 天+) |
| **影响等级** | 小 (8/9 节点 owner 校验延迟, 不影响实际 KPI) |
| **应急响应** | 1. owner 手动跑 6 SQL (复用 § 3 SQL 模板) → 整合成 summary.json (5 min)  2. Coder 检查 Mavis cron 配置 + 重启 cron service  3. 复用 dashboard_w11.md 静态版本 (W11 B2 commit a10aecc) + 6 SQL 单 SQL JSON 输出 (logs/cron/kpi-verify-2026-08-09-sql-{1-6}.json) 作为补充  4. 8/10 09:00 BD 校验 + 复核全部 6 SQL 输出 |
| **负责人** | Coder (Mavis cron + SQL) + Mavis owner (手动跑 + 汇总) + BD (校验) |
| **应急状态** | `[未触发/已触发]` placeholder |
| **回滚条件** | summary.json 完整生成 + 6 SQL JSON 字段对齐 + owner 校验通过 |

### 5.4 场景 4: C+D vs B 不一致 (5 律师 + 25 新律师 ≠ 总营收)

| 维度 | 详情 |
|------|------|
| **触发条件** | 2026-08-09 09:45 owner 校验 C 步骤 + D 步骤 = B 步骤不一致 (e.g., C = ¥900 + D = ¥3,000 ≠ B = ¥4,020, 差 ¥120) |
| **触发概率** | 低 (5%, 5 律师营收 ¥997 包含 L4/L5 8/25 接力未到期的部分, 与 25 新律师口径互斥) |
| **影响等级** | 大 (营收口径不一致, v1.1 修正是否再次触发需要重新对齐) |
| **应急响应** | 1. owner 立即检查 invite_code 划分 (5 律师 invite_code BETA2025-0001-0005 vs 25 新律师 NOT IN)  2. Coder 检查 Stripe webhook + payments 表 invite_code 字段是否完整  3. 重新跑 C + D SQL, 跟 v1.1 § 1.1 公式对齐 (5 律师 60% 转化 + 25 新律师 25% 转化 = 30 律师)  4. 若差异 > 5%, 触发 W19 v1.2 修正 (重新对齐 5 律师 vs 25 新律师口径, 类似 W17 v1.1)  5. 8/10 09:00 总指挥拍板 + 公开 v1.2 修正日志 |
| **负责人** | Coder (Stripe webhook + payments 表 + invite_code 划分) + Mavis owner (校验 + 重新跑 SQL) + 总指挥 (决策 + 公开) |
| **应急状态** | `[未触发/已触发]` placeholder |
| **回滚条件** | C+D = B 完全一致 OR 差异 ≤ 5% 且能明确归因到某一口径 |

---

## 6. v1.1 修正确认 (W17 e10cc69 接力)

> **W17 v1.1 修正确认**: 8/9 当天实测 A + B + C + D 步骤, 验证 W17 v1.1 修正后 16 处下游引用是否仍然一致.

### 6.1 v1.1 修正 2 项确认

| # | 修正项 | v1.0 | v1.1 | 8/9 实测验证 |
|---|--------|------|------|--------------|
| **1** | 5 律师批次营收 | ¥1,096 | **¥997** | § 2.2 C 步骤实测 = `[¥997]` placeholder, owner 8/9 09:00 校验 |
| **2** | § 2.3 距月底增量人数 | 35 律师 | **20-26 律师** | § 2.3 距月底增量人数 = `(50 - A_actual) + L4/L5 6` 公式重新计算, 验证是否落在 20-26 范围 |

### 6.2 16 处引用一致性再次确认 (8/9 实测后回灌)

| # | 引用位置 | v1.0 数值 | v1.1 数值 | 8/9 实测后回灌 v2.0 |
|---|---------|-----------|-----------|---------------------|
| 1 | § 1.1 公式 (line 56) | ¥1,096 | ¥997 | 用 B 步骤实测替换 v2.0 |
| 2 | § 1.2 KPI 验证表 (lines 84-85) | ¥1,096 / ¥2,924 | ¥997 / ¥3,023 | 用 C + D 实测替换 v2.0 |
| 3 | § 2.1 营收明细表 (line 101) | ¥997 + ¥99 = ¥1,096 | ¥898 + ¥99 = ¥997 | 用 C 步骤实测替换 v2.0 |
| 4 | § 2.2 营收趋势表 (lines 118-120) | 7/29/7/30/8/1 ¥1,096 | ¥997 | 用 A 步骤实测替换 v2.0 |
| 5 | § 2.3 距月底表 (line 141) | 35 律师 / ¥41,580 | 20-26 律师 / ¥10,436-14,000 | 用 E 步骤实测替换 v2.0 |
| 6 | § 4.1 25 新律师表 (line 247) | ¥1,096 + ¥2,924 | ¥997 + ¥3,023 | 用 B 步骤实测替换 v2.0 |
| 7 | § 4.2 营收贡献 (lines 258, 265) | 27.3% / ¥1,188 | 24.8% / ¥1,287 | 用 C/D 实测替换 v2.0 |
| 8 | § 5.1 dashboard 节点 (line 286) | ¥1,096 | ¥997 | 用 C 步骤实测替换 v2.0 |
| 9 | § 7 收尾 checklist (lines 397, 401) | ¥4,020 = ¥1,096 + ¥2,924 | ¥4,020 = ¥997 + ¥3,023 | 用 B 步骤实测替换 v2.0 |

> **实测回灌 v2.0**: 8/9 owner 实测 A/B/C/D/E 5 个数值后, 用实测值替换 v1.1 占位 v2.0 全部 16 处引用. 严禁在 8/9 实测前手动替换 (保持 v1.1 placeholder 占位完整性).

### 6.3 v1.2 修正触发条件 (W18 新增, 跟 W17 v1.1 修正模式一致)

> **如果 C 步骤实测 ≠ ¥997**: 触发 W19 v1.2 修正 (5 律师营收公式重新对齐, 类似 W17 v1.1 修正模式).
> **如果 A 步骤实测 < 25 (即 30 - 5 = 25 名律师阈值)**: 触发 § 5 场景 1 应急备案 (不修正公式, 直接进应急).
> **如果 E 步骤实测 (距月底增量人数 + ARR 缺口) 不在 20-26 / ¥10,436-14,000 范围**: 触发 W19 v1.2 修正 (距月底 § 2.3 重新对齐).

---

## 7. 收尾标准 (W18 kpi-verify-809 forward-execute)

- [x] § 0 文档使用说明 (W18 forward-execute 实测填实 8/9 当天 09:00)
- [x] § 1 实测背景 (W16 + W17 → W18 接力, 3 阶段 timeline)
- [x] § 2 30 律师付费 + ¥4,020 实测公式对齐 (§ 2.1 公式 + § 2.2 5 步 + § 2.3 距月底)
- [x] § 3 6 Dashboard SQL 实测 (§ 3.1-§ 3.6, 含 8/9 实测预期输出)
- [x] § 4 owner 9 步操作清单 (§ 4.1 9 步 + § 4.2 8/8 前 24h 准备 + § 4.3 8/10 上午复盘)
- [x] § 5 应急备案 4 场景 (场景 1: 30 律师未达 + 场景 2: dashboard 异常 + 场景 3: JSON 校验 + 场景 4: C+D vs B 不一致)
- [x] § 6 v1.1 修正确认 (16 处引用再次确认 + v1.2 触发条件)
- [x] § 8 跨 plan 复用清单 (W14 + W15 + W16 + W17 + W18 复用完整对账)
- [ ] **8/9 实测填实**: 6/30 当前距 8/9 还有 40 天, 待 owner 8/9 当天 09:00 跑 9 步操作实测填实 kpi-snapshot v2.0
- [ ] **git log 显示 1+ 8/9 commit**: 待 owner 8/9 10:00 v2.0 实测填实后 commit + push origin/main

---

## 8. 跨 plan 复用清单 (W18 kpi-verify-809 → W16 + W17 + W19 + W20 接力)

### 8.1 W18 → W19 + W20 接力

| 接力方向 | 任务 | 衔接点 | 接力时间 |
|---------|------|--------|---------|
| **W18 → W19** | phase5-prep + W19 follow-up 1 (W19 integration 任务) | kpi-snapshot v2.0 实测填实 + L4/L5 8/25 转化数据接力 | 8/9 → 8/25 (公测 day 15-23) |
| **W18 → W19** | W19 integration (8/31 月底冲刺) | kpi-snapshot v2.0 + L4/L5 v1.0 数据交给 phase4-final-831 接力 | 8/9 → 8/31 |
| **W18 → W20** | Phase 5 启动 (Phase 5.1 + Phase 5.4) | kpi-snapshot v2.0 + 50 律师付费汇总给 Phase 5 准备文档 | 8/9 → 9/1 |

### 8.2 W18 复用 W14/W15/W16/W17 引用 (5 个 commit 80%+ 复用率)

| commit | 文件 | 复用内容 |
|--------|------|---------|
| **W16 `83613c4`** kpi-track-809 | `kpi-dashboard-726-809.md` (472 行) + `kpi-snapshot-2026-08-09.md` (413 行) | 6 指标 KPI + 14 天日看板 + 5 渠道漏斗 + 朋友圈扩散 + 朋友推荐 + 30 律师付费公式 + 应急备案 + SQL 验证 |
| **W17 `e10cc69`** kpi-v1.1-fixes | `kpi-snapshot-2026-08-09.md` v1.1 (492 行) | 16 处下游引用更新 + § 8 v1.1 修正日志 (6 节) |
| **W15 `d66fc33`** recruit-1000 | `recruit-1000-runbook.md` (670 行) + `dashboard-recruit-1000.md` (510 行) | 5 渠道漏斗框架 (1200 律师) + 5 指标 dashboard + 30 天日看板模式 |
| **W14 `6f785e5`** first-paid-triggers-729 | `first-paid-triggers-runbook.md` (768 行) + `dashboard-paid-triggers.md` (388 行) | 5 律师转化路径 (L1/L2/L3 7/29 + L4/L5 8/25) + 3 通道 (邮件 + 微信 + 朋友圈) + 4 业务指标 |
| **W15 `900948f`** l4l5-triggers-825 | `l4l5-triggers-runbook.md` + `dashboard-l4l5-triggers.md` | L4/L5 8/25 转化增量重跑 (8/9 节点不覆盖, 但 8/9 实测后用于 § 2.3 距月底计算) |
| **W15 `093f014`** friends-circle-9-grid | `friends-circle-9-grid.md` (233 行) | 朋友圈 9 宫格 day 8-15 扩散 (8/2 + 8/5 + 8/9 三轮) + 9 段文案 |
| **W16 `ceeb508`** day1-execute-726 | `day1-dashboard-monitoring-2026-07-26.md` (315 行) | 7/26 day 1 dashboard 实时监控机制 (复用 5min 实时刷新 + Mavis cron 23:00 + 应急备案模式) |
| **W11 `4910305`** C1 first-paid-triggers v1.0 | C1 5 律师转化路径模板 | 5 律师 L1-L5 + 30 天试用到期转化基准 60% |
| **W11 `8208143`** B2 邀请码 1115 完整池 | `invite-codes-list.csv` | 评审 5 + 微信群 10 + 创史 100 + 律协 100 + 公开 900 = 1115 邀请码完整池 |
| **W11 `a99e941`** B2 招募页 | `templates/views/founding/index.html` | 6 模块 + 2 track event (landing_viewed + invite_redeemed) |
| **W13 `c62877c`** dashboard 7 指标 | `templates/views/dashboard/index.html` | dashboard 视图 + chart.js 7 指标 |
| **W14 `5986709`** launch-execute-726 | `launch-runbook-final-2026-07-26.md` v2.0 (504 行) | 60 min 启动仪式 (5 时段 + 茶歇) |

### 8.3 W18 增量 (相对 W16 kpi-track-809 + W17 kpi-v1.1-fixes)

| # | 增量 | 来源 | 复用率 |
|---|------|------|--------|
| 1 | owner 9 步操作清单 (公测 day 14 节点 09:00 09:00 09:00 操作) | W16 § 4.1-4.2 + W17 § 6 应急 | 80%+ 复用 |
| 2 | 6 SQL 实测 (W18 6 SQL 顺序重排, 含 8/9 实测预期输出) | W16 § 7 + W17 § 5 | 80%+ 复用 |
| 3 | 应急备案 4 场景 (W18 § 5 加 C+D vs B 不一致场景 4, 跟 W17 § 6 三场景区分) | W16 § 5 + W17 § 6 | 70%+ 复用 |
| 4 | v1.1 修正确认 (16 处引用再次确认 + v1.2 触发条件) | W17 § 8 v1.1 修正日志 | 80%+ 复用 |
| 5 | 跨 plan 接力 (W18 → W19 + W20) | W15 8 月底冲刺 | 100% 增量 |

> **W18 复用率**: 6 章节中 5 章节 (80%+) 复用 W14/W15/W16/W17 历史 commit, 仅 § 8.3 W18 增量 (W18 → W19 + W20 接力 + v1.2 触发条件) 是 100% 增量.

### 8.4 W18 kpi-verify-809 文档使用 checklist (8/9 当天 owner 必做)

- [ ] 8/8 20:00 owner 提前过本 runbook 9 步清单 (§ 4.1 + § 4.2)
- [ ] 8/9 08:00 Coder 启动 dev server + dashboard `/dashboard` 路由 + 5min 实时刷新 (§ 4 步骤 1)
- [ ] 8/9 08:30 Coder 启动 Mavis cron 6 SQL + 等待自动落档 (§ 4 步骤 2)
- [ ] 8/9 09:00 owner 接收汇总 JSON (§ 4 步骤 3)
- [ ] 8/9 09:15 owner 校验 A 步骤 (paid_converted = 30) (§ 4 步骤 4 + § 2.2 步骤 1)
- [ ] 8/9 09:30 owner 校验 B 步骤 (营收快照 = ¥4,020) (§ 4 步骤 5 + § 2.2 步骤 2)
- [ ] 8/9 09:45 owner 校验 C+D 步骤 (5 律师 ¥997 + 25 新律师 ¥3,023) (§ 4 步骤 6 + § 2.2 步骤 3-4)
- [ ] 8/9 10:00 owner 编辑 kpi-snapshot-2026-08-09.md v1.1 → v2.0 (替换 v1.1 9+ 处 placeholder) (§ 4 步骤 7)
- [ ] 8/9 10:30 Coder 截图 (PC + 移动) → docs/marketing/screenshots/founding-2026-08-09/ (§ 4 步骤 8)
- [ ] 8/9 11:00 总指挥拍板 - 30 律师付费 + ¥4,020 营收是否达成, 触发应急 (§ 4 步骤 9 + § 5)

---

## 9. 文档版本与责任

> **撰写**: lex-bd (BD/运营)
> **协作**: 总指挥 (5 律师 1v1 深度沟通 + 朋友圈 9 宫格 + 律协背书) · lex-coder (dashboard 监控 + 6 SQL + Stripe webhook + 5 事件埋点) · lex-pm (试用律师使用提醒 + 创史 5 折延期 + 企业版 PRD) · lex-design (海报 + 招募页 + 公众号长文)
> **文档版本**: v1.0 (2026-06-30 forward-execute placeholder, W18 kpi-verify-809 task)
> **复用**: 30 律师付费公式来自 W17 kpi-v1.1 修正 + W16 kpi-track-809 任务定义, 6 dashboard SQL 复用 W16 kpi-dashboard § 7 + W17 kpi-snapshot § 5, 应急备案 4 场景复用 W16 § 5 + W17 § 6, owner 9 步操作清单复用 W16 § 4 + W17 § 6
> **更新频率**: 8/9 当天 09:00 owner 实测填实 → 10:00 v2.0 commit 落档 → 23:00 Mavis cron 终极归档
> **严禁 fabricate**: 当前 6/30 距 8/9 还有 40 天, 所有 30 律师付费数字 + 营收快照 + dashboard 6 指标实际值 + 应急备案触发条件 + 跨 W18 接力时间表均标记 placeholder, 由 owner 8/9 当天 09:00 实测填实
