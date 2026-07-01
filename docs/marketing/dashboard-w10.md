<!-- LexPrime Track B · W10 B2 交付 -->
# 公测期 4 + 3 指标日看板 (Dashboard W10)

> **版本**: v2.0 · 2026-06-30
> **Track**: B (公测启动期 4+3 指标看板)
> **Week**: W10 B2 Day 1-2 起草, 7/26 公测启动后每日 23:00 更新
> **目标**: 跟踪 PRD §11.6.3 v0.7.3 公测期小目标 (4 业务指标) + W10 B2 创史专属 3 指标
> **配套**: `launch-funnel.md` (5 事件+4 指标) · `founding-member-recruit.md` (80 创史招募) · `beta-launch-1000-invitation.md` (5 渠道漏斗) · `funnel-data-w6.md` (历史漏斗)
> **引用 commit**: W6 f47db65 (5 事件埋点 v0.1) · W6 081031a (创史招募 v0.1) · W10 B1 ce98f64 (4 指标漏斗 v2.0) · W10 B2 (本文档)
>
> **核心升级 (v2.0 vs W6 v0.1)**:
> - **业务漏斗 vs 技术漏斗**: W6 v0.1 是技术埋点 (WAU / 留存 / 漏斗 / 付费), W10 v2.0 是业务漏斗 (注册转化率 / 试用转化率 / 付费转化率 / 创史转化率)
> - **新增 3 创史专属指标**: 创史招募率 / 创史群活跃 / 创史付费转化, 跟踪 80 席招满过程
> - **30 天公测期 (7/26 - 8/23) 日看板**: 4 + 3 = 7 指标每日追踪
> - **渠道 × 指标 矩阵**: 5 渠道 × 7 指标, 每日 23:00 自动跑数据, BD 当晚 23:30 回填

---

## 1. 4 + 3 指标总览 (PRD §11.6.3 v0.7.3 + W10 B2 创史专属)

### 1.1 4 业务指标定义 (W10 B1 launch-funnel.md §3.2 复用)

| 指标 | 定义 | 公式 | 数据源 | 目标 | 频率 |
|------|------|------|--------|------|------|
| **注册转化率** | landing_viewed → invite_redeemed | redeemed / landing_viewed | landing_viewed + invite_redeemed 事件 | ≥ 60% (210/350) | 每日 |
| **试用转化率** | invite_redeemed → active (7 日内首次 Skill) | active / redeemed | invite_redeemed + skill_run 事件 | ≥ 50% (105/210) | 每日 |
| **付费转化率** | active → paid (30 日内转化付费) | paid / active | skill_run + paid_converted 事件 | ≥ 30% (50/105) (W10 B2) | 每日 |
| **创史转化率** | redeemed → advocate_promoted (30 日内创史激活) | advocate / redeemed | invite_redeemed + advocate_promoted 事件 | ≥ 38% (80/210) (W10 B2) | 每日 |

### 1.2 3 创史专属指标定义 (W10 B2 新增)

| 指标 | 定义 | 公式 | 数据源 | 目标 | 频率 |
|------|------|------|--------|------|------|
| **创史招募率** | 创史段 (0016-0115) 实际招募 / 80 剩余名额 | advocate_count / 80 | advocate_promoted 事件 + invite_redeemed 创史段 | 100% (8/23 截止) | 每日 |
| **创史群活跃** | 创始律师群月活 / 80 创史总数 | 群月活律师 / 80 | 微信群 + 客服系统 + feedback 反馈 | ≥ 60% (48/80) | 每周 |
| **创史付费转化** | 创史律师中付费 / 80 创史总数 | 创史付费 / 80 | paid_converted 事件 (创史段邀请码) | ≥ 80% (64/80, 5 折自动续费) | 每月 |

### 1.3 4 + 3 = 7 指标 → 5 事件 映射

| 指标 | 关联事件 | 计算公式 |
|------|----------|----------|
| 注册转化率 | landing_viewed + invite_redeemed | redeemed / viewed |
| 试用转化率 | invite_redeemed + skill_run (注册后 7 日内) | active / redeemed |
| 付费转化率 | skill_run + paid_converted (注册后 30 日内) | paid / active |
| 创史转化率 | invite_redeemed + advocate_promoted (注册后 30 日内) | advocate / redeemed |
| 创史招募率 | advocate_promoted (创史段) | advocate_count / 80 |
| 创史群活跃 | skill_run + feedback_submit (创史律师, 月活) | 群月活 / 80 |
| 创史付费转化 | paid_converted (创史段) | 创史付费 / 80 |

---

## 2. 4 指标日看板 (主表, 30 天 30 行)

> **W10 B2 末交付时为空表**, 7/26 公测启动后由 Mavis 每日 23:00 跑数据, BD 23:30 回填.
> **数据查询**: 见 `launch-funnel.md` §3.4 GET /api/tracking/stats 接口

### 2.1 4 指标日数据 (W10 末 - W12 末, 共 30 天)

| 日期 | WAU 累计 | landing_viewed | invite_redeemed | active | paid | advocate | 注册率 | 试用率 | 付费率 | 创史率 |
|------|----------|----------------|-----------------|--------|------|----------|--------|--------|--------|--------|
| 2026-07-26 | (待填) | | | | | | | | | |
| 2026-07-27 | | | | | | | | | | |
| ... | | | | | | | | | | |
| 2026-08-23 | | | | | | | | | | |
| **累计 (W12 末)** | | | | | | | | | | |

### 2.2 4 指标 7 日滚动平均

| 指标 | D-7 | D-6 | D-5 | D-4 | D-3 | D-2 | D-1 | 当前 7 日平均 | 趋势 |
|------|-----|-----|-----|-----|-----|-----|-----|--------------|------|
| 注册转化率 | | | | | | | | | |
| 试用转化率 | | | | | | | | | |
| 付费转化率 | | | | | | | | | |
| 创史转化率 | | | | | | | | | |

---

## 3. 3 创史专属指标看板 (主表, 30 天 30 行)

### 3.1 3 创史指标日数据

| 日期 | 创史招募 (累计) | 招募率 | 群月活 | 群活跃率 | 创史付费 | 付费转化率 | 备注 |
|------|----------------|--------|--------|----------|----------|------------|------|
| 2026-07-26 | 20 (首批已发) | 25% | - | - | - | - | 启动仪式颁奖 |
| 2026-07-27 | (待填) | | | | | | |
| ... | | | | | | | |
| 2026-08-23 | 80 (目标) | 100% | ≥48 | ≥60% | ≥64 | ≥80% | 公测期截止 |
| **W12 末** | **80** | **100%** | **48** | **60%** | **64** | **80%** | 公测期小目标 |

### 3.2 创史段 (0016-0115) redeem 监控

| 渠道 | 创史码段 | 已 redeem | 未 redeem | 招募率 |
|------|----------|-----------|-----------|--------|
| **L1-L6 评审律师** | 0016-0016 (L6 1 名) | - | - | - |
| **微信群律师** | 0006-0015 (10 名, 非创史段但保留) | - | - | - |
| **律协推荐** | 0017-0020 (4 名预留) | - | - | - |
| **公开公测创史** | 0021-0115 (95 名公开) | - | - | - |
| **小计** | 0016-0115 (100 席) | **20 (首批已发)** | **80 剩余** | **20% → 100%** |

---

## 4. 渠道 × 指标 矩阵 (5 渠道 × 7 指标, 每日 23:00 更新)

> **5 渠道**: 5 律所网络 + 100 律师朋友圈 + 10 微信群 + 5 公众号长文 + 1 律协推荐
> **7 指标**: 注册转化率 / 试用转化率 / 付费转化率 / 创史转化率 / 创史招募率 / 创史群活跃 / 创史付费转化
> **更新频率**: 每日 23:00 Mavis 自动跑数据 + BD 23:30 回填

### 4.1 渠道矩阵主表

| 渠道 | 邀请目标 | 触达 | redeem | 试用激活 | 付费 | 创史 | 注册率 | 试用率 | 付费率 | 创史率 |
|------|----------|------|--------|----------|------|------|--------|--------|--------|--------|
| 5 律所网络 | 200 | - | - | - | 10 | 25 | - | - | - | - |
| 100 律师朋友圈 | 200 | - | - | - | 8 | 15 | - | - | - | - |
| 10 微信群 | 250 | - | - | - | 15 | 10 | - | - | - | - |
| 5 公众号长文 | 250 | - | - | - | 10 | 20 | - | - | - | - |
| 1 律协推荐 | 100 | - | - | - | 7 | 10 | - | - | - | - |
| **小计** | **1000** | - | **210** | **105** | **50** | **80** | **60%** | **50%** | **30%** | **38%** |

### 4.2 渠道健康度评分 (BD 每周日 23:00 出)

| 渠道 | 健康度 | 评分 | 关键问题 | 下周动作 |
|------|--------|------|----------|----------|
| 5 律所网络 | (待填) | /100 | | |
| 100 律师朋友圈 | (待填) | /100 | | |
| 10 微信群 | (待填) | /100 | | |
| 5 公众号长文 | (待填) | /100 | | |
| 1 律协推荐 | (待填) | /100 | | |

---

## 5. 邀请码统计 (W10 B2 升级, 1115 邀请码)

> **数据源**: `invite-codes-list.csv` (W6 115 + W10 B2 1000)
> **更新频率**: 每日 23:00 自动同步 (从 SQLite invite_codes 表)

### 5.1 邀请码总览 (W10 B2 末)

| 批次 | 码段 | 总数 | 已发 | 已 redeem | 兑换率 | 未 redeem | 备注 |
|------|------|------|------|-----------|--------|-----------|------|
| **W6 评审律师** | 0001-0005 | 5 | 5 | 1 | 20% | 4 | L1-L5 |
| **W6 微信群律师** | 0006-0015 | 10 | 10 | 0 | 0% | 10 | 私域律师群 |
| **W6 创史公开段** | 0016-0115 | 100 | 100 | 0 | 0% | 80 (剩余) | 80 席剩余招募 |
| **W6 admin 测试段** | 7410/1491/2876/2543/2929 | 5 | 5 | 0 | 0% | 5 | admin 测试用 |
| **W10 B2 5 律所** | 0116-0315 | 200 | - | - | - | - | 5 律所网络 |
| **W10 B2 朋友圈** | 0316-0515 | 200 | - | - | - | - | 100 律师私域 |
| **W10 B2 微信群** | 0516-0765 | 250 | - | - | - | - | 10 律师群 |
| **W10 B2 公众号** | 0766-1015 | 250 | - | - | - | - | 5 公众号长文 |
| **W10 B2 律协** | 1016-1115 | 100 | - | - | - | - | 1 律协推荐 |
| **总计** | - | **1115** | **120** | **1** | **0.83%** | **1099** | W6 + W10 B2 |

### 5.2 邀请码状态日变化 (W10 B2 末 - W12 末, 30 天)

| 日期 | 总码 | 已发 | 已 redeem | 兑换率 | 备注 |
|------|------|------|-----------|--------|------|
| 2026-07-26 | 1115 | 120 | 1 | 0.08% | 启动仪式 D-Day |
| 2026-07-27 | 1115 | (待填) | (待填) | (待填) | 公测 W0 Day 2 |
| ... | | | | | |
| 2026-08-23 | 1115 | (待填) | (待填) | (待填) | 公测期截止 |
| **W12 末** | **1115** | **1115** | **≥ 210** | **≥ 18.8%** | 公测期小目标 |

---

## 6. 4 周节奏表 (W10 B2 - W12 公测期)

### 6.1 公测期 4 周节奏 (7/26 - 8/23)

| 周次 | 日期范围 | 重点动作 | 指标目标 |
|------|----------|----------|----------|
| **W10 B2 末 (D-1)** | 07-25 周六 | 招募计划 + 1000 邀请函 + 招募页 + dashboard 落地 | - |
| **W11 公测 W0** | 07-26 - 08-01 | 启动仪式 + 5 渠道首轮 + D-Day 200 邀请 | 注册率 60% / 试用率 50% / 创史招 25 |
| **W12 公测 W1** | 08-02 - 08-09 | 5 渠道持续 + 公众号预热 + D-7 律协沙龙 | 累计 600 邀请 / 创史招 50 / 付费 10 |
| **W13 公测 W2** | 08-10 - 08-16 | 5 公众号长文 + 律协沙龙 + 私域补位 | 累计 850 邀请 / 创史招 70 / 付费 30 |
| **W14 公测 W3** | 08-17 - 08-23 | 律协沙龙收尾 + 反馈问卷 + 创史正式激活 | 累计 1000 / 创史招 80 / 付费 50 |

### 6.2 关键里程碑 (PRD §11.6.3 v0.7.3 公测期小目标)

| 日期 | 里程碑 | 指标状态 |
|------|--------|----------|
| **7/26 (D-Day)** | 启动仪式颁奖 + 1000 邀请函公测开放 | 创史 20 (首批) + 邀请 200 |
| **8/1 (公测 W0 末)** | 5 渠道首轮覆盖 | 邀请 600 (60% 进度) |
| **8/9 (公测 W1 末)** | 律协沙龙首场 + 公众号预热 | 邀请 1000 (100%) + 创史 70 + 付费 10 |
| **8/16 (公测 W2 末)** | 5 公众号长文 + 律协沙龙收尾 | 创史 70 + 付费 30 |
| **8/23 (公测 W3 末)** | 公测期截止 + 反馈问卷 + 创史激活 | **创史 80 (满) + 付费 50** |

---

## 7. 异常告警 + 高风险场景 (W10 B2 升级)

### 7.1 7 异常告警 (BD 实时监控)

| 异常 | 阈值 | 触发条件 | 告警渠道 | 责任人 |
|------|------|----------|----------|--------|
| 注册转化率 < 50% | 50% (7 日平均) | 7 日平均 < 50% | 短信 + 微信 | 总指挥 |
| 试用转化率 < 40% | 40% (7 日平均) | 7 日平均 < 40% | 短信 + 微信 | lex-pm |
| 付费转化率 < 20% | 20% (7 日平均) | 7 日平均 < 20% | 短信 + 微信 | lex-bd |
| 创史转化率 < 30% | 30% (7 日平均) | 7 日平均 < 30% | 短信 + 微信 | lex-bd |
| 创史招募率 < 60% | 60% (8/9 截止) | 8/9 < 60% (48 席) | 短信 + 微信 | lex-bd |
| 创史群活跃 < 40% | 40% (周末统计) | 周末 < 40% (32 律师) | 短信 + 微信 | lex-cs |
| 邀请码兑换异常 | 同 IP 1h ≥ 5 次 | 防刷触发 | 自动风控 | lex-coder |

### 7.2 5 高风险场景 + 应对

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| 8/1 仅邀 300 名 (目标 600) | 中 | 高 | 启动公众号加推 2 篇, 律协沙龙延期到 8/3 |
| 8/9 仅邀 700 名 (目标 1000) | 中 | 中 | 公众号 + 朋友圈加推 1 周, 目标 8/16 完成 |
| 8/9 创史仅招 50 名 (目标 70) | 中 | 高 | 启动律协 80 席位加速审批, 朋友圈追加 1 条限时福利 |
| 8/23 创史仅招 60 名 (目标 80) | 中 | 高 | 公众号长文加 2 篇, 律协沙龙延期到 8/30 |
| 8/23 付费仅 30 名 (目标 50) | 中 | 高 | 启动仪式 1v1 邀请评审律师帮转, 公众号推「试用真实报告」 |

---

## 8. 7 指标 SQL 查询 (Mavis 每日 23:00 自动跑)

### 8.1 4 业务指标 SQL (复用 launch-funnel.md §4)

```sql
-- 注册转化率 (D 日)
SELECT
  '注册转化率' AS metric,
  COUNT(DISTINCT CASE WHEN event = 'invite_redeemed' THEN user_id END) AS numerator,
  COUNT(DISTINCT CASE WHEN event = 'landing_viewed' THEN user_id END) AS denominator,
  ROUND(COUNT(DISTINCT CASE WHEN event = 'invite_redeemed' THEN user_id END) * 100.0 /
    NULLIF(COUNT(DISTINCT CASE WHEN event = 'landing_viewed' THEN user_id END), 0), 2) AS rate_pct
FROM tracking_events
WHERE event IN ('landing_viewed', 'invite_redeemed')
  AND DATE(timestamp) = '2026-07-26';

-- 试用转化率
SELECT
  '试用转化率' AS metric,
  COUNT(DISTINCT CASE WHEN event = 'skill_run' AND timestamp BETWEEN register_time AND register_time + INTERVAL '7 days' THEN user_id END) AS numerator,
  COUNT(DISTINCT CASE WHEN event = 'invite_redeemed' THEN user_id END) AS denominator,
  ROUND(COUNT(DISTINCT CASE WHEN event = 'skill_run' AND timestamp BETWEEN register_time AND register_time + INTERVAL '7 days' THEN user_id END) * 100.0 /
    NULLIF(COUNT(DISTINCT CASE WHEN event = 'invite_redeemed' THEN user_id END), 0), 2) AS rate_pct
FROM tracking_events
WHERE event IN ('invite_redeemed', 'skill_run');

-- 付费转化率
SELECT
  '付费转化率' AS metric,
  COUNT(DISTINCT CASE WHEN event = 'paid_converted' AND timestamp BETWEEN register_time AND register_time + INTERVAL '30 days' THEN user_id END) AS numerator,
  COUNT(DISTINCT CASE WHEN event = 'skill_run' THEN user_id END) AS denominator,
  ROUND(COUNT(DISTINCT CASE WHEN event = 'paid_converted' AND timestamp BETWEEN register_time AND register_time + INTERVAL '30 days' THEN user_id END) * 100.0 /
    NULLIF(COUNT(DISTINCT CASE WHEN event = 'skill_run' THEN user_id END), 0), 2) AS rate_pct
FROM tracking_events
WHERE event IN ('skill_run', 'paid_converted');

-- 创史转化率
SELECT
  '创史转化率' AS metric,
  COUNT(DISTINCT CASE WHEN event = 'advocate_promoted' THEN user_id END) AS numerator,
  COUNT(DISTINCT CASE WHEN event = 'invite_redeemed' THEN user_id END) AS denominator,
  ROUND(COUNT(DISTINCT CASE WHEN event = 'advocate_promoted' THEN user_id END) * 100.0 /
    NULLIF(COUNT(DISTINCT CASE WHEN event = 'invite_redeemed' THEN user_id END), 0), 2) AS rate_pct
FROM tracking_events
WHERE event IN ('invite_redeemed', 'advocate_promoted');
```

### 8.2 3 创史专属指标 SQL (W10 B2 新增)

```sql
-- 创史招募率 (累计, 创史段邀请码)
SELECT
  '创史招募率' AS metric,
  COUNT(DISTINCT user_id) AS advocate_count,
  80 AS target_count,
  ROUND(COUNT(DISTINCT user_id) * 100.0 / 80, 2) AS rate_pct
FROM invite_codes ic
JOIN tracking_events te ON ic.code = te.invite_code
WHERE ic.channel = 'founding-member'  -- 创史段 0016-0115
  AND te.event = 'advocate_promoted'
  AND ic.code BETWEEN 'BETA2025-0016' AND 'BETA2025-0115';

-- 创史群活跃 (月活, 月度统计)
SELECT
  '创史群活跃' AS metric,
  COUNT(DISTINCT te.user_id) AS mau_count,
  80 AS target_count,
  ROUND(COUNT(DISTINCT te.user_id) * 100.0 / 80, 2) AS rate_pct
FROM invite_codes ic
JOIN tracking_events te ON ic.code = te.invite_code
WHERE ic.channel = 'founding-member'
  AND te.event IN ('skill_run', 'feedback_submit')
  AND te.timestamp >= DATE('now', '-30 days')
  AND ic.code BETWEEN 'BETA2025-0016' AND 'BETA2025-0115';

-- 创史付费转化 (累计)
SELECT
  '创史付费转化' AS metric,
  COUNT(DISTINCT te.user_id) AS paid_count,
  80 AS target_count,
  ROUND(COUNT(DISTINCT te.user_id) * 100.0 / 80, 2) AS rate_pct
FROM invite_codes ic
JOIN tracking_events te ON ic.code = te.invite_code
WHERE ic.channel = 'founding-member'
  AND te.event = 'paid_converted'
  AND ic.code BETWEEN 'BETA2025-0016' AND 'BETA2025-0115';
```

---

## 9. 验收标准 (W10 B2 末)

- [x] `dashboard-w10.md` v2.0 起草 (本文档, 4 业务指标 + 3 创史专属 = 7 指标)
- [ ] 7 指标 SQL 查询验证 (Mavis 7/26 启动后跑)
- [ ] 7 异常告警阈值设定 (短信 + 微信通知)
- [ ] 4 周节奏表更新 (W10 B2 末 → W14 公测 W3 末)
- [ ] 邀请码统计日变化表 (W10 B2 末 → W12 末)
- [ ] git log 显示 3+ B2 commit

---

> **整理人**: lex-bd (BD/运营) · 协作: 总指挥 (指标目标拍板 + 风险应对决策) · lex-pm (创史正式资格激活 + 反馈问卷) · lex-coder (7 指标 SQL + 自动化跑数) · lex-ai (skill_run 埋点对接) · 文档版本: v2.0 (2026-06-30)
> **下一步**: W10 B2 收尾: 3 git commits push origin/main + deliverable.md + 报告 parent