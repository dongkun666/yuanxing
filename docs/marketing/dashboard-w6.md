<!-- LexPrime Track D · W6 Day 3 交付 -->
# 公测期 4 指标日看板 (Dashboard W6)

> **版本**: v0.1 · 2026-06-29
> **Track**: D (公测预热 + 数据看板)
> **Week**: W6 Day 3 启动, 每日 23:00 更新
> **目标**: 跟踪 PRD § 10 4 个核心指标 (WAU / 漏斗 / 留存 / 付费) + 邀请码状态 + 公测期 30 天节奏
> **配套**: `tracking-events.md` (埋点) · `funnel-data-w6.md` (漏斗数据) · `outreach-log-w6.md` (触达) · `prd/10-success-metrics.md` § 11.2.1
>
> **使用说明**: 本文档是 **公测期 30 天 (7/26 - 8/23) 的「日看板」**, 4 指标 + 邀请码状态 + 当日数据 + 当周复盘.
> 更新责任: Mavis 每天 23:00 跑数据, BD 当晚 23:30 回填到本文档; 周日 23:00 出周报.

---

## 1. 4 指标总览 (PRD § 10.2)

### 1.1 4 指标定义 (复述 tracking-events.md § 2)

| 指标 | 定义 | 数据源 | 目标 | 频率 |
|------|------|--------|------|------|
| **WAU** (周活) | 自然周内至少 1 次 login/skill_run 的独立用户 | tracking_events | W6 末 50, W7 末 100 | 每日 |
| **漏斗** (Funnel) | 访问 → 试用 → 7 日 → 30 日 → 付费, 5 步 | tracking_events + 邀请码 | 5% 总转化 | 每日 |
| **留存** (Retention) | 注册后 Day 7 / Day 30 活跃率 | tracking_events | Day 7 ≥ 60%, Day 30 ≥ 30% | 每日 |
| **付费** (Payment) | 试用 → 付费转化率 | payment_success | 30%+ (激活律师) | 每日 |

### 1.2 4 指标 → 5 事件 映射

| 4 指标 | 关联 5 事件 | 计算公式 |
|--------|------------|----------|
| WAU | login + skill_run | 独立 user_id 数 / 周 |
| 漏斗 | trial_landing_pv + trial_register_submit + login + skill_run + payment_success | 5 步转化率 |
| 留存 | login + skill_run (注册后 N 日) | 注册后 N 日活跃 / 注册数 |
| 付费 | payment_success (注册后 60 日内) | 付费律师 / 试用律师 |

---

## 2. 4 指标日看板 (主表, 30 天 30 行)

> **W6 末交付时为空表**, 7/26 公测启动后由 Mavis 每日 23:00 跑数据, BD 23:30 回填.
> **数据查询**: 见 `tracking-events.md` § 3.4 GET /api/tracking/stats 接口

### 2.1 4 指标日数据 (W6 末 - W8 末, 共 30 天)

| 日期 | WAU (本周累计) | step1 访问 | step2 试用 | step3 7日活跃 | step4 30日活跃 | step5 付费 | 访问→试用 | 试用→7日 | 7日→30日 | 30日→付费 | 试用→付费 |
|------|----------------|-----------|-----------|---------------|----------------|-----------|-----------|---------|---------|---------|---------|
| 2026-07-26 | (待填) | | | | | | | | | | |
| 2026-07-27 | | | | | | | | | | | |
| ... | | | | | | | | | | | |
| 2026-08-23 | | | | | | | | | | | |
| **累计 (W8 末)** | | | | | | | | | | | |

### 2.2 4 指标周度对比 (4 周 4 行)

| 周次 | 日期范围 | WAU 目标 | WAU 实际 | 漏斗总转化 | Day 7 留存 | Day 30 留存 | 累计付费 |
|------|----------|----------|----------|------------|------------|------------|----------|
| W0 (公测首周) | 07-26 - 08-01 | 50 | | | (待填) | - | - |
| W1 | 08-02 - 08-08 | 100 | | | | - | - |
| W2 | 08-09 - 08-15 | 150 | | | | (待填) | 0 |
| W3 | 08-16 - 08-23 | 200 | | | | | **5+** |

### 2.3 渠道转化对比 (W7 末 BD 出表, 见 funnel-data-w6.md § 2.3)

> **首次出表**: W7 末 (08-09 周日 23:00)
> **更新频率**: 每周日 23:00
> **维度**: 评审律师 / 微信群律师 / 创史 / 律协推荐 / 公开报名

| 渠道 | 邀请数 | 注册数 | 注册率 | 7 日活跃 | 7 日活跃率 | 30 日付费 | 付费率 |
|------|--------|--------|--------|----------|------------|-----------|--------|
| 评审律师 (5) | 5 | (待填) | | | | | |
| 微信群律师 (10) | 10 | | | | | | |
| 创史体验官 (100) | 100 | | | | | | |
| 律协推荐 (估 30) | 30 | | | | | | |
| 公开报名 (估 20) | 20 | | | | | | |
| **合计** | 165 | | | | | | |

---

## 3. 邀请码状态跟踪 (W6 Day 1 启动, 实时)

> **数据源**: `docs/marketing/invite-codes-list.csv` (115 行, 实时更新 status 字段)
> **更新方式**: BD 每 24h 跑一次, status 状态机: unused → redeemed → active → converted / expired

### 3.1 邀请码状态机

```
[unused]      生成, 待触达
    ↓ 总指挥微信 1v1 / 邮件 / 朋友圈 / 律协推荐
[redeemed]    律师点击邀请链接, 完成注册表单 (trial_register_submit 触发)
    ↓ 后端自动激活
[active]      律师开始 30 天试用 (注册成功)
    ↓ (30 天后)
[converted]   律师完成支付 (payment_success 触发, 创史自动享 5 折)
[expired]     律师未付费, 高级 Skill 锁定 (W8 末未转化)
```

### 3.2 邀请码实时分布 (公测首日空白, 后续每日更新)

| 状态 | 评审律师 (5) | 微信群律师 (10) | 创史体验官 (100) | 总计 (115) | 比例 |
|------|--------------|------------------|------------------|------------|------|
| **unused** | 5 (初始) | 10 (初始) | 100 (初始) | 115 (初始) | 100% |
| **redeemed** | 0 | 0 | 0 | 0 | 0% |
| **active** | 0 | 0 | 0 | 0 | 0% |
| **converted** | 0 | 0 | 0 | 0 | 0% |
| **expired** | 0 | 0 | 0 | 0 | 0% |
| **总激活率 (active + converted)** | - | - | - | - | - |

> **目标 (W6 末, 7/19 周日)**:
> - 评审律师: 5/5 redeemed (100%) + 5/5 active (100%)
> - 微信群律师: 6/10 redeemed (60%+) + 5/10 active (50%+)
> - 创史体验官: 15/100 redeemed (15%+, 律协推荐中)

> **目标 (W7 末, 8/9 周日)**:
> - 评审律师: 5/5 active
> - 微信群律师: 8/10 active (80%+)
> - 创史体验官: 80/100 redeemed (80%) + 60/100 active (60%)

> **目标 (W8 末, 8/23 周日)**:
> - 评审律师: 5/5 converted
> - 微信群律师: 6/10 converted (60%+, 创史 5 折激励)
> - 创史体验官: 30/100 converted (30%+, 创史身份)

---

## 4. 公测期运营节奏 (30 天)

> 每日 BD + 总指挥协作, 跟踪 4 指标 + 邀请码状态 + 触达 / 反馈.

### 4.1 每日动作清单 (BD + 总指挥)

| 时间 | 动作 | 频率 | 责任人 |
|------|------|------|--------|
| **09:00** | 查 dashboard-w6.md 4 指标 (昨日) | 每天 | BD |
| **09:30** | 异常预警响应 (见 funnel-data-w6.md § 4.1) | 每天 | BD + 总指挥 |
| **10:00** | 监控邀请码状态 (status 变化) | 每天 | BD |
| **10:30** | 律师群发反馈 (1 条朋友圈 / 1 条群内, 不刷屏) | 每天 | 总指挥 |
| **12:00** | 评审律师 1v1 微信回访 (1-2 位/天) | 每天 | 总指挥 |
| **15:00** | 创史意向跟进 (新入申请 5-10 位/天) | 每天 | BD |
| **18:00** | 律师 1v1 答疑 (微信咨询) | 每天 | BD + 总指挥 |
| **21:00** | 朋友圈 / 公众号内容发布 (1 条) | 每天 | 总指挥 + BD |
| **23:00** | Mavis 跑日报 (4 指标 + 邀请码状态) | 每天 | Mavis |
| **23:30** | BD 回填 dashboard-w6.md § 2.1 + § 3.2 | 每天 | BD |

### 4.2 4 个关键节点 (运营重点)

| 节点 | 日期 | 关键动作 | 目标 |
|------|------|----------|------|
| **公测启动** | 07-26 周日 | 评审 #2 收尾 + 启动仪式 + 邮件群发 115 邀请码 | 评审律师全激活 + 微信群 6+ 启动 |
| **Day 7 留存** | 08-02 周日 | 7 日留存观察 + 创史招满 85 + 公众号长文 | 7 日留存 60%+ |
| **Day 14 反馈** | 08-09 周日 | Day 14 反馈 + 中期报告 + 创史招满 100 | 创史 100 名 |
| **Day 30 付费** | 08-23 周日 | Day 30 付费墙触发 + 首批 5 付费律师 + 公测报告 | 30 日付费 5+ |

### 4.3 3 个里程碑 (D-day)

| 里程碑 | 触发条件 | 动作 |
|--------|----------|------|
| **M1: 评审律师 5 全到** | 07-19 评审 #1 前, 5/5 评审律师确认 | 致谢 + 评审卡 + 创史候选 |
| **M2: 创史体验官 100 满** | 08-09 周日前, 100/100 创史招满 | 出「创史名单」+ 致谢 + 律协公告 |
| **M3: 首批 5 付费律师** | 08-23 周日前, 5+ 律师转化付费 | 出公测报告 + 给团队 + 给投资人 |

---

## 5. 当日数据回填区 (W6 末空白, 7/26 起每日更新)

### 5.1 当日数据 (2026-MM-DD)

```
日期: _______________
WAU (本周累计): _______________
当日 step1 访问: _______________
当日 step2 试用: _______________
当日 step3 7日活跃 (新): _______________
当日 step5 付费 (新): _______________
访问 → 试用 CVR: _______________%
试用 → 7 日活跃 CVR: _______________%
邀请码 unused → redeemed: _______________ (例: +5)
邀请码 redeemed → active: _______________ (例: +3)
今日异常事件: _______________
今日 BD 动作: _______________
```

### 5.2 当周复盘 (周日 23:00)

```
周次: _______________
本周 WAU 累计: _______________ (目标: _______)
本周 step2 试用累计: _______________ (目标: _______)
本周 step3 7日活跃新增: _______________ (目标: _______)
本周 step5 付费新增: _______________ (目标: _______)
本周创史意向确认: _______________ (目标: _______)
本周 Day 7 留存率: _______________% (目标: ≥60%)
本周 Day 30 留存率: _______________% (目标: ≥30%)
本周异常: _______________
本周优化项: _______________
下周重点: _______________
```

### 5.3 W6 末预填 (启动前基线)

> **W6 末交付时, 4 指标全部为 0** (公测未启动), 但本节为「启动前基线」.

| 指标 | 启动前基线 (W6 末) | 备注 |
|------|---------------------|------|
| **WAU** | 0 | 公测 7/26 启动 |
| **试用律师总数** | 0 | 邀请码已生成 115 个, 未激活 |
| **创史体验官** | 0 / 100 | 7/19 启动招募 |
| **付费律师** | 0 | 8/23 前首批 5 |
| **邀请码激活** | 0 / 115 (0%) | 7/26 后开始激活 |
| **评审律师 5** | 0 / 5 (0%) | 7/19 评审 #1 前激活 |
| **微信群律师 10** | 0 / 10 (0%) | 7/15 朋友圈预热 |

---

## 6. 异常处理 SOP (BD + 总指挥)

### 6.1 异常检测 (Mavis 跑日报时)

| 异常 | 触发条件 | 预警级别 | 响应时间 |
|------|----------|----------|----------|
| **WAU < 目标 50%** | 周日 23:00 WAU 累计 < 目标 50% | 红色 | 24h 内 |
| **访问 → 试用 < 20%** | 单日 step2 / step1 < 20% (目标 30%) | 红色 | 12h 内 |
| **试用 → 7 日活跃 < 40%** | 单日 step3 / step2 < 40% (目标 50%) | 黄色 | 24h 内 |
| **Day 7 留存 < 50%** | 注册后 7 日, step3 / step2 < 50% (目标 60%) | 黄色 | 24h 内 |
| **邀请码激活停滞** | 单日邀请码 status 变化 < 2 (连续 3 天) | 黄色 | 12h 内 |
| **评审律师失约** | 评审会前 1 天 评审律师未确认 | 红色 | 1h 内 |
| **创史招满延迟** | 08-09 创史未招满 80 名 (目标 100) | 黄色 | 24h 内 |

### 6.2 异常处理流程

```
异常检测 (Mavis 跑数据) → 红色预警
  ↓ 1h 内
BD 初步诊断 (邀请码状态 / 落地页 / onboarding 步骤)
  ↓ 24h 内
总指挥拍板 (调整策略 / 紧急修复)
  ↓ 48h 内
修复 + 二次数据验证
  ↓ 7d 内
周报复盘 (写入 dashboard-w6.md § 5.2)
```

### 6.3 5 个高风险场景 (预案)

| 场景 | 触发 | 应对 |
|------|------|------|
| **场景 1: 公测启动日 (7/26) 注册 < 30** | 当日 step2 < 30 | 朋友圈追加 1 条限时福利, 评审律师朋友圈帮转 |
| **场景 2: Day 7 留存 < 40%** | W7 末 step3 / step2 < 40% | 紧急修复 onboarding (lex-coder P0), BD 1v1 微信回访激活律师 |
| **场景 3: 创史体验官招满 100 但激活 < 50%** | W7 末 FM 注册 / FM 邀请码 < 50% | 创史正式资格延后到反馈, 加强客服群 (BD 1v1) |
| **场景 4: Day 30 付费转化 < 3%** | W8 末 step5 / step2 < 3% | 调整定价 (W9 折上折), 延后公测期 (8/30 截止) |
| **场景 5: 律协不批 100 席位** | 06-30 - 07-12 无批复 | 降级「律协背书 + 自营 60 创史」, W7 律协沙龙补足 |

---

## 7. 4 指标数据查询 (Mavis 跑日报 SQL)

### 7.1 WAU

```sql
SELECT
  DATE_TRUNC('week', created_at AT TIME ZONE 'Asia/Shanghai') AS week,
  COUNT(DISTINCT user_id) AS wau
FROM tracking_events
WHERE event IN ('login', 'skill_run')
  AND created_at >= '2026-07-26'
GROUP BY week
ORDER BY week;
```

### 7.2 漏斗 (5 步)

```sql
-- 累计漏斗 (从公测启动到当前)
WITH
  step1 AS (SELECT COUNT(DISTINCT user_id) AS n FROM tracking_events WHERE event = 'trial_landing_pv'),
  step2 AS (SELECT COUNT(DISTINCT user_id) AS n FROM tracking_events WHERE event = 'trial_register_submit'),
  step3 AS (SELECT COUNT(DISTINCT t2.user_id) AS n
            FROM tracking_events t2
            JOIN tracking_events t3 ON t2.user_id = t3.user_id
            WHERE t2.event = 'trial_register_submit'
              AND t3.event IN ('login', 'skill_run')
              AND t3.created_at > t2.created_at
              AND t3.created_at <= t2.created_at + INTERVAL '7 days'),
  step4 AS (SELECT COUNT(DISTINCT t2.user_id) AS n
            FROM tracking_events t2
            JOIN tracking_events t4 ON t2.user_id = t4.user_id
            WHERE t2.event = 'trial_register_submit'
              AND t4.event IN ('login', 'skill_run')
              AND t4.created_at > t2.created_at
              AND t4.created_at <= t2.created_at + INTERVAL '30 days'),
  step5 AS (SELECT COUNT(DISTINCT user_id) AS n FROM tracking_events WHERE event = 'payment_success')
SELECT
  step1.n AS step1_visit,
  step2.n AS step2_trial,
  step3.n AS step3_active_7d,
  step4.n AS step4_active_30d,
  step5.n AS step5_paid,
  ROUND(step2.n * 100.0 / step1.n, 1) AS cvr_1_to_2,
  ROUND(step3.n * 100.0 / step2.n, 1) AS cvr_2_to_3,
  ROUND(step4.n * 100.0 / step3.n, 1) AS cvr_3_to_4,
  ROUND(step5.n * 100.0 / step2.n, 1) AS cvr_2_to_5
FROM step1, step2, step3, step4, step5;
```

### 7.3 留存 (Day 7 / Day 30)

```sql
-- Day 7 留存
SELECT
  DATE(t2.created_at) AS register_day,
  COUNT(DISTINCT t2.user_id) AS registered,
  COUNT(DISTINCT t3.user_id) AS active_7d,
  ROUND(COUNT(DISTINCT t3.user_id) * 100.0 / COUNT(DISTINCT t2.user_id), 1) AS retention_7d_pct
FROM tracking_events t2
LEFT JOIN tracking_events t3 ON t2.user_id = t3.user_id
  AND t3.event IN ('login', 'skill_run')
  AND t3.created_at > t2.created_at
  AND t3.created_at <= t2.created_at + INTERVAL '7 days'
WHERE t2.event = 'trial_register_submit'
GROUP BY DATE(t2.created_at)
ORDER BY register_day;
```

### 7.4 付费转化

```sql
SELECT
  DATE_TRUNC('month', t1.created_at) AS month,
  COUNT(DISTINCT t1.user_id) AS total_trial,
  COUNT(DISTINCT t2.user_id) AS converted_paid,
  ROUND(COUNT(DISTINCT t2.user_id) * 100.0 / COUNT(DISTINCT t1.user_id), 1) AS conversion_pct
FROM tracking_events t1
LEFT JOIN tracking_events t2 ON t1.user_id = t2.user_id
  AND t2.event = 'payment_success'
  AND t2.created_at > t1.created_at
  AND t2.created_at <= t1.created_at + INTERVAL '60 days'
WHERE t1.event = 'trial_register_submit'
GROUP BY DATE_TRUNC('month', t1.created_at)
ORDER BY month;
```

---

## 8. 验收标准 (W6 末)

- [x] dashboard-w6.md v0.1 起草 (本文档, 4 指标 + 邀请码状态 + 30 天节奏)
- [ ] 公测期 4 指标日看板就绪 (W7 Day 1, Mavis 跑通 SQL)
- [ ] 邀请码状态机实时跟踪 (BD 每日 23:30 回填)
- [ ] 30 天节奏表 + 4 关键节点 + 5 高风险场景预案就绪
- [ ] 4 指标 SQL 跑通 (Mavis W7 Day 1 验证)
- [ ] 每日 23:00 自动跑数据 (Mavis 定时任务)
- [ ] 周日 23:00 出周报 (BD + PM)

> **整理人**: lex-bd (BD/运营) · 数据来源: Mavis 跑 SQL (W7 接入数据库后) · 文档版本: v0.1 (06-29)

---
