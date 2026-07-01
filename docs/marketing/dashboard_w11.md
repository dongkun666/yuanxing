<!-- LexPrime Track B · W11 B2 交付 -->
# 公测期 4 业务 + 3 创史专属指标看板 (Dashboard W11)

> 版本: v1.0 · 2026-06-29
> Track: B (公测启动期 + 创史招募期双重跟踪)
> Week: W11 B2 Day 1-2
> 状态: 4 业务指标 + 3 创史专属指标已就位, 等 7/26 启动仪式触发
> 上一版: dashboard_w6.md v0.1 (W6 Day 3, commit f47db65, 已归档基线)
> 配套: launch_funnel.md v2.0 (5 事件 + 4 指标) · founding_member_recruit.md v2.0 (80 席招募) · beta_launch_event_2026_07_26.md (60 min 启动仪式) · beta_launch_1000_invitation.md (1000 公测邀请函)

## 0.5 自动 dashboard 说明 (W11 C1 新增)

> 配套: `../marketing/first-paid-triggers.md` v1.0 (W11 C1, 5 律师 L1-L5 转化触发) · `../marketing/launch-runbook-2026-07-26.md` v1.0 (W11 C1, 启动仪式执行运行手册)
> 引用 commit: W11 C1 (本节) · W11 B2 a10aecc (dashboard 4+3 指标 v1.0) · W10 B1 ce98f64 (4 指标业务漏斗 v2.0)

### 0.5.1 数据源 (6 事件: 5 事件 + 1 trial_expired 事件)

> 6 事件数据源 (W11 C1 v0.7.4 PRD § 11.6.2): landing_viewed / invite_redeemed / trial_started / trial_expired (新增) / paid_converted / advocate_promoted
> 5 渠道: 评审律师 / 微信群律师 / 创始体验官 (公开) / 律协推荐 / 公开报名
> 跟踪期: 7/26 - 8/31 (37 天, 公测期 + 8 月底冲刺)

### 0.5.2 自动 dashboard 跑数据流程 (Mavis cron)

```
[每日 22:55] Mavis cron 启动 (mavis team plan dry-run 模式, 不污染 owner 队列)
  |
  | 23:00 - 23:15 (15 min) Mavis 跑 7 SQL (launch-funnel.md §6 + dashboard_w11.md §6)
  | - 4 业务指标 SQL: 注册/试用/付费/创史 转化率
  | - 3 创史专属 SQL: 招募率/群活跃/付费转化
  | - 1 trial_expired SQL (W11 C1 新增): 5 律师首批 7/29 触达率 + 25 名新律师 8/9 触达率
  | 写入 SQLite 本地表 `daily_metrics_2026_07_26_to_08_31`
[每日 23:15 - 23:30] (15 min) Mavis 生成 dashboard JSON
  | 输出: `data/dashboard_w11_auto_2026-07-26.json` (每日增量更新)
  | 字段: date, 4 业务指标, 3 创史指标, trial_expired 5 律师触达率
[每日 23:30 - 23:45] (15 min) BD 人工回填
  | - 跑 SQL 校验 Mavis 数据 (防止自动跑偏差)
  | - 写 docs/marketing/dashboard_w11_daily_review.md (15 min 写日报)
  | - 异常预警响应 (red 异常 12h 内, yellow 异常 24h 内)
[每日 23:59] 朋友圈 9 宫格 + 公众号日报 (BD)
```

### 0.5.3 自动 dashboard 数据流 (跟 prd_backlog 集成)

> W11 C1 自动 dashboard 数据源 = `tracking_events` (5 事件) + `trial_expired` 表 (W11 C1 新增) + `invite_codes` 表 + `prd_backlog` 公开 P0/P1 ticket (供 dashboard 推荐律师关注点)
> prd_backlog 集成: `docs/prd/backlog-w8.md` (W8 评审真数据, A1) + `docs/prd/tracks/` (W10 A2 自动调度器) - 拉取 P0/P1 律师关注问题作为 dashboard 底部推荐
> 公开数据源: invite_codes_list.csv (W11 B2 1115 码) + tracking_events 表 (W10 B1 5 事件) + advocate 表 (W11 B2 创史状态机)

### 0.5.4 自动 dashboard 触发 (3 场景)

| 场景 | 触发 | 应对 |
|------|------|------|
| 正常 cron | 每日 23:00 Mavis 跑成功 | BD 23:30 校验 + 回填日报, 0 异常 |
| Mavis 失败 | 23:00 cron 没产出 (15 min 内) | Coder 12:00 排查 + 手动跑 SQL + 15:00 补发日报 |
| 数据异常 | 4 业务指标 < 红色阈值 (转化率 < 10%) | BD 24h 内 + 总指挥拍板 + 紧急修复 + 7d 周报复盘 |

### 0.5.5 自动 dashboard vs 手动 dashboard

| 维度 | 自动 dashboard (W11 C1) | 手动 dashboard (W11 B2 已有) |
|------|--------------------------|------------------------------|
| 数据源 | Mavis cron 跑 SQL (每日 23:00) | BD 手动 23:30 回填 |
| 频率 | 每日 23:00 自动 + 异常预警 | 每日 23:30 手动 |
| 延迟 | < 30 min | 1h+ (手动延迟) |
| 准确度 | 高 (Mavis SQL 校验) | 中 (BD 经验估算) |
| 可扩展 | 高 (加指标 = 加 SQL) | 低 (改指标 = 改文档) |
| Mavis 依赖 | 是 (W11 C1 首次集成) | 否 |

> W11 C1 自动 dashboard 升级: 跟 W11 B2 手动 dashboard 兼容, 7 SQL 共享 (dashboard_w11.md §6), Mavis 跑 SQL + 写入 SQLite + 生成 JSON + BD 23:30 校验.
> 首跑日期: 2026-07-26 (公测启动仪式当天 23:00 首次自动跑, 含 0 基础数据, 用于 7/27 起 4 业务指标基线)

---

> 引用 commit: W6 f47db65 (首月漏斗 v0.1) · W10 B1 ce98f64 (4 指标业务漏斗 v2.0) · W10 B1 0df6a74 (启动仪式 60 min) · W11 B2 (本看板)

---

## 1. 看板总览 (公测期 7/26 - 8/24, 30 天日看板 + 4 周周报)

### 1.1 7 大指标看板

| 指标 | 类型 | 业务节点 | 计算公式 | 目标 | 计算窗口 | 数据源 |
|------|------|----------|----------|------|----------|--------|
| **注册转化率** | 4 业务指标 #1 | 邀请码兑换 -> 试用 | trial_started / invite_redeemed | >= 80% | 每日 23:00 | 5 事件 invite_redeemed + trial_started |
| **试用转化率** | 4 业务指标 #2 | 公测 landing 访问 -> 兑换 | invite_redeemed / landing_viewed | >= 15% | 每日 23:00 | 5 事件 landing_viewed + invite_redeemed |
| **付费转化率** | 4 业务指标 #3 | 试用律师 -> 付费 | paid_converted / trial_started | >= 25% | 每周 | 5 事件 trial_started + paid_converted |
| **创史转化率** | 4 业务指标 #4 | 试用律师 -> 创史晋升 | advocate_promoted / trial_started | >= 60% (公测平均) / >= 100% (创史场景) | 每日 23:00 | 5 事件 trial_started + advocate_promoted |
| **创史招募率** | 3 创史专属 #1 | 招募进度 | advocate_promoted / 80 席目标 | 100% (8/23 周日前) | 每日 23:00 | 5 事件 advocate_promoted + 渠道目标 |
| **创史群活跃** | 3 创史专属 #2 | Day 7 / 14 / 30 反馈率 | feedback_completed / advocate_promoted | >= 80% (Day 30) | 每周 | 问卷提交 + 反馈时间戳 |
| **创史付费转化** | 3 创史专属 #3 | 创史律师付费率 | paid_converted (is_founding_member=True) / advocate_promoted | >= 30% (首年 5 折激励) | 每周 | 5 事件 paid_converted (is_founding_member 字段) |

> 4 业务指标继承自 PRD §11.6.1 (v0.7.3 公测期业务漏斗), 3 创史专属指标来自 W11 B2 创史招募场景下的运营重点.

### 1.2 30 天数据汇总 (公测期累计目标)

| 指标 | Day 0 起点 | 7/26 | 8/02 | 8/09 | 8/16 | 8/23 (截止) | 最终 |
|------|------------|------|------|------|------|-------------|------|
| landing_viewed | 0 | 100+ | 500+ | 800+ | 1000+ | 1025+ | 1025+ |
| invite_redeemed | 0 | 30+ | 80+ | 120+ | 140+ | 235+ | 235+ |
| trial_started | 0 | 25+ | 65+ | 100+ | 120+ | 199+ | 199+ |
| paid_converted | 0 | 0 | 0 | 5+ | 15+ | 51+ | 51+ |
| advocate_promoted | 0 | 25+ | 50+ | 70+ | 95+ | 191+ | 191+ (含 80 创史目标) |

### 1.3 4 指标周度对比 (4 周 4 行)

| 周次 | 日期范围 | landing | redeemed | trial | paid | advocate | 试用 CVR | 注册 CVR | 付费 CVR | 创史 CVR |
|------|----------|---------|----------|-------|------|----------|----------|----------|----------|----------|
| **W10 末** | 07-26 - 08-01 | 1000+ | 80+ | 60+ | 0 | 30+ | 8% | 75% | 0% | 50% |
| **W11 前半** | 08-02 - 08-08 | 1500+ | 120+ | 100+ | 0 | 50+ | 8% | 83% | 0% | 50% |
| **W11 后半** | 08-09 - 08-15 | 2000+ | 140+ | 115+ | 5+ | 70+ | 7% | 82% | 4% | 56% |
| **W12** | 08-16 - 08-23 | 2500+ | 150+ | 120+ | 30+ | 95+ | 6% | 80% | 25% | 67% |
| **目标加权** | 30 天 | **2500+** | **150+** | **120+** | **30+** | **80+** | **6%** | **80%** | **25%** | **67%** |

> 注: advocate_promoted 目标 80 是公测期小目标 (PRD §11.6.3 v0.7.3). 实际加权计算按 5 渠道转化路径 (founding_member_recruit.md §6.2) 加权.

## 2. 4 业务指标细化 (PRD §11.6.1 + launch_funnel.md §2)

### 2.1 注册转化率 (Registration CVR)

> 定义: 邀请码兑换 -> 试用注册的转化率
> 公式: trial_started / invite_redeemed × 100%
> 目标: 公测期 >= 80% (兑换 150 -> 试用 120)

| 维度 | 目标 | 监控节奏 | 异常预警阈值 |
|------|------|----------|--------------|
| 评审律师 | 100% (5/5 已 redeem L1, 4 待) | 每日 | < 80% (启动后 7 天) 红色预警 |
| 微信群律师 | 80%+ (8/10) | 每日 | < 70% (8/9 前) 黄色预警 |
| 创始体验官 | 90%+ (72/80, 5 折激励) | 每日 | < 80% (8/16 前) 黄色预警 |
| 律协推荐 | 90%+ (72/80 律协名额) | 每日 | < 80% (8/20 前) 黄色预警 |
| 公开报名 | 70%+ (42/60) | 每日 | < 60% (8/23 前) 红色预警 |
| **加权** | **>= 80%** | **每日** | **< 70% (启动后 14 天) 红色预警** |

### 2.2 试用转化率 (Trial Activation CVR)

> 定义: 公测 landing 访问 -> 邀请码兑换的转化率
> 公式: invite_redeemed / landing_viewed × 100%
> 目标: 公测期 >= 15% (访问 1000 -> 兑换 150)

| 维度 | 目标 | 监控节奏 | 异常预警阈值 |
|------|------|----------|--------------|
| 评审律师 | 100% (5/5) | 每日 | < 90% (启动后 3 天) 黄色预警 |
| 微信群律师 | 50%+ (10/20, 朋友圈 + 群内) | 每日 | < 30% (8/9 前) 黄色预警 |
| 创始体验官 | 80%+ (80/100, 律协 + 朋友圈) | 每日 | < 60% (8/16 前) 红色预警 |
| 律协推荐 | 80%+ (80/100 律协名额) | 每日 | < 60% (8/20 前) 红色预警 |
| 公开报名 | 6%+ (60/1000, 公众号 + 公测 landing) | 每日 | < 4% (8/23 前) 黄色预警 |
| **加权** | **>= 15%** | **每日** | **< 10% (启动后 14 天) 红色预警** |

### 2.3 付费转化率 (Payment CVR)

> 定义: 试用律师 -> 付费律师的转化率
> 公式: paid_converted / trial_started × 100%
> 目标: 公测期 >= 25% (试用 120 -> 付费 30)

| 维度 | 目标 | 监控节奏 | 异常预警阈值 |
|------|------|----------|--------------|
| 评审律师 | 50%+ (5 -> 2-3 付费, 1v1 微信强) | 每周 | < 30% (8/16 前) 黄色预警 |
| 微信群律师 | 20%+ (8 -> 1-2 付费) | 每周 | < 10% (8/16 前) 黄色预警 |
| 创始体验官 | 30%+ (72 -> 21-22 付费, 5 折激励大) | 每周 | < 20% (8/23 前) 红色预警 |
| 律协推荐 | 30%+ (72 -> 21-22 付费, 律协背书强) | 每周 | < 20% (8/23 前) 红色预警 |
| 公开报名 | 5%+ (42 -> 2 付费, 渠道长尾) | 每周 | < 2% 黄色预警 |
| **加权** | **>= 25%** | **每周** | **< 15% (8/23 前) 红色预警** |

### 2.4 创史转化率 (Advocate CVR)

> 定义: 试用律师 -> 创始体验官的晋升率
> 公式: advocate_promoted / trial_started × 100%
> 目标: 公测期 >= 60% (试用 120 -> 创史 80) · 创史场景下 >= 100% (创史目标即试用启动)

| 维度 | 目标 | 监控节奏 | 异常预警阈值 |
|------|------|----------|--------------|
| 评审律师 | 100% (5/5 自动晋升, 评审 + 微信群种子) | 每日 | < 90% (8/2 前) 红色预警 |
| 微信群律师 | 60%+ (8 -> 5 创史) | 每日 | < 50% (8/9 前) 黄色预警 |
| 创始体验官 (公开) | 50%+ (42 -> 21 创史) | 每日 | < 40% (8/16 前) 黄色预警 |
| 律协推荐 | 100%+ (80/80 律协名额直达创史) | 每日 | < 90% (8/23 前) 红色预警 |
| **加权** | **>= 60% (公测平均)** / **>= 100% (创史场景)** | **每日** | **< 50% (8/16 前) 红色预警** |

### 2.5 4 指标 -> 5 事件映射 (W10 B1 launch_funnel.md §2.5)

| 4 指标 | 关联 5 事件 | 计算公式 |
|--------|------------|----------|
| 注册转化率 | invite_redeemed + trial_started | trial_started / invite_redeemed |
| 试用转化率 | landing_viewed + invite_redeemed | invite_redeemed / landing_viewed |
| 付费转化率 | trial_started + paid_converted | paid_converted / trial_started |
| 创史转化率 | trial_started + advocate_promoted | advocate_promoted / trial_started |

---

## 3. 3 创史专属指标细化 (W11 B2 新增)

### 3.1 创史招募率 (Founding Recruitment Rate)

> 定义: 公测期招募到位的创史律师占 80 席目标的百分比
> 公式: advocate_promoted (创史段 0016-0115) / 80 × 100%
> 目标: 100% (8/23 周日前招满 80)

| 周次 | 日期 | 关键动作 | 累计目标 | 占比 | 异常预警阈值 |
|------|------|----------|----------|------|--------------|
| W10 末 (公测 W0) | 07-26 - 08-01 | 启动仪式颁奖 + 朋友圈预热 + 5 律师视频 | 30 席 | 38% | < 25 席 (8/2 前) 黄色预警 |
| W11 前半 (公测 W1) | 08-02 - 08-08 | 1v1 微信 + 律师群发 + 公众号 #1 | 50 席 | 63% | < 45 席 黄色预警 |
| W11 后半 (公测 W2) | 08-09 - 08-15 | 公众号 #2-#3 + 律协沙龙 #1 | 70 席 | 88% | < 65 席 黄色预警 |
| W12 前半 (公测 W3) | 08-16 - 08-22 | 公众号 #4-#5 + 律协沙龙 #2 | 95 席 | 119% (超目标) | < 80 席 (8/23 前) 红色预警 |
| W12 后半 (公测 W4) | 08-23 | 收尾 + 公测报告 | **80 席满** | **100%** | < 80 席 (8/23 截止) 红色预警 |

> **数据源**: 5 事件 advocate_promoted (channel=founding_member 过滤) + 邀请码 redeem 状态 (BETA2025-0016 ~ 0115 = 100 创史段)。
> **配套指标**: 7 渠道转化率 (5 律所 + 100 律师私域 + 10 微信群 + 5 公众号 + 1 律协 + 公开报名, 见 founding_member_recruit.md §6.6).

### 3.2 创史群活跃 (Founding Member Engagement)

> 定义: 创史律师在 30 天试用期内, Day 7 / Day 14 / Day 30 反馈问卷的提交率
> 公式: feedback_completed (Day N) / advocate_promoted × 100%
> 目标: Day 7 >= 70% (激活) / Day 14 >= 75% (中期反馈) / Day 30 >= 80% (创史正式资格)

| 节点 | 时间 | 目标 | 监控节奏 | 异常预警阈值 | 配套动作 |
|------|------|------|----------|--------------|----------|
| **Day 7** | 试用 1 周 | 70%+ | 每日 | < 50% 黄色预警 | BD 1v1 跟进首周使用情况 |
| **Day 14** | 试用 2 周 | 75%+ | 每周 | < 60% 黄色预警 | BD 推送中期反馈问卷 |
| **Day 23** | 试用 23 天 (-7 天付费) | 80%+ | 每日 | < 70% 红色预警 | BD 推送「反馈问卷预告 + 付费提醒」 |
| **Day 30** | 试用 30 天 | 80%+ | 每日 (D-2 起每小时) | < 70% 红色预警 | BD 推送「创史正式资格激活」+ 5 折生效 |

> **数据源**: 站内 10 题反馈问卷 (founding_member_recruit.md §4.3) + 问卷提交时间戳。
> **关联**: 创史群活跃 = 创史律师留存的前置信号, 跟 §1 4 指标的 7 日留存 (PRD §11.2.1.10) 强相关。

### 3.3 创史付费转化 (Founding Member Payment Rate)

> 定义: 创史律师中完成付费 (含 5 折 ¥449/年) 的比例
> 公式: paid_converted (is_founding_member=True) / advocate_promoted × 100%
> 目标: 公测期 >= 30% (首年 5 折激励大 + 终身客服绑定)

| 维度 | 目标 | 监控节奏 | 异常预警阈值 |
|------|------|----------|--------------|
| 评审律师 (5 创史) | 50%+ (5 -> 2-3 付费, 评审强 + 1v1 微信) | 每周 | < 30% (8/16 前) 黄色预警 |
| 微信群律师 (5 创史) | 30%+ (5 -> 1-2 付费) | 每周 | < 20% (8/16 前) 黄色预警 |
| 公众号 / 朋友圈 (60 创史) | 30%+ (60 -> 18-20 付费, 5 折激励) | 每周 | < 20% (8/23 前) 红色预警 |
| 律协沙龙 (10 创史) | 50%+ (10 -> 5 付费, 律协背书强) | 每周 | < 30% (8/23 前) 红色预警 |
| **加权** | **>= 30% (创史 80 -> 24-30 付费)** | **每周** | **< 20% (8/23 前) 红色预警** |

> **配套营收**: 80 创史律师中, 30% 付费转化 = 24 名付费律师, 创史 5 折 ¥449/年 × 24 = ¥10,776 首年营收 (按创史专属)。80 创史 + 普通付费 = 30+ 付费律师 (PRD §11.6.3 v0.7.3 公测期小目标)。
> **续费指标 (公测期外)**: 创史续费率 (W12+ 跟踪, 目标 >= 90%, PRD §11.2.1.7)。

### 3.4 3 创史专属指标 -> 5 事件映射 (W11 B2 新增字段)

| 3 创史专属指标 | 关联事件 + 字段 | 计算公式 |
|----------------|------------------|----------|
| 创史招募率 | advocate_promoted (channel=founding_member) | advocate_promoted_channel_founding / 80 |
| 创史群活跃 | feedback_completed (channel=foundin_member) + 时间戳 | feedback_count_day_N / advocate_promoted |
| 创史付费转化 | paid_converted (is_founding_member=True) | paid_count_is_founding / advocate_promoted |

> **数据落地**: launch_funnel.md §1.5 已定义 advocate_promoted 的 channel 字段 (默认 founding_member), paid_converted 已定义 is_founding_member 字段 (默认 False, 创史律师自动为 True), feedback_completed 是 W11 B2 新增的客户端埋点事件。

### 3.5 3 创史专属指标 vs 4 业务指标关系

| 3 创史专属 | 关联 4 业务指标 | 关系 |
|-------------|----------------|------|
| 创史招募率 | 创史转化率 | 创史招募率 = 创史转化率 * 80 (分子) · 创史转化率 = 创史晋升率 (周度%) |
| 创史群活跃 | (无直接对应) | 创史群活跃是创史律师 30 天试用期内的运营指标, 不是业务漏斗节点, 是漏斗外的留存和活跃度指标 |
| 创史付费转化 | 付费转化率 | 创史付费转化是付费转化率的子集, 仅统计 is_founding_member=True 的律师 |

> 4 业务指标是全漏斗核心转化, 3 创史专属是创史场景下的运营深度指标, 两者互补 (业务漏斗看大盘, 创史专属看创史 100 席的健康度).

---
## 4. 7 渠道转化对比 (W11 B2 公测期 30 天加权)

> Mavis 跑每日数据 (23:00), BD 23:30 回填, weighted 加权按 5 渠道律师场景转化率计算

| 渠道 | 邀请数 | landing | redeemed | trial | paid | advocate | 试用 CVR | 注册 CVR | 付费 CVR | 创史 CVR |
|------|--------|---------|----------|-------|------|----------|----------|----------|----------|----------|
| **评审律师** (5) | 5 | 5 | 5 | 5 | 2-3 | 5 | 100% | 100% | 50% | 100% |
| **微信群律师** (10) | 10 | 20 | 10 | 8 | 1-2 | 5 | 50% | 80% | 20% | 60% |
| **创始体验官 (公开段)** (95) | 95 | 95 | 76 | 68 | 20-22 | 76 | 80% | 90% | 30% | 100% |
| **律协推荐** (100) | 100 | 100 | 80 | 72 | 21-22 | 80 | 80% | 90% | 30% | 100% |
| **公开报名** (800+) | 800+ | 800+ | 60 | 42 | 2 | 21 | 7.5% | 70% | 5% | 50% |
| **合计 / 加权** | **1010+** | **1020+** | **231+** | **195+** | **46-51** | **187+** | **23%** | **85%** | **25%** | **96%** |

> **注**: 评审律师 L1 (BETA2025-0001) 已 redeem (W9 commit 5437535), 计入 W7 (公测前), W10 B1 启动后 4 位评审律师待 redeem.

---

## 5. 30 天异常预警 SOP (BD + 总指挥)

### 5.1 异常检测 (Mavis 跑日报时)

| 异常 | 触发条件 | 预警级别 | 响应时间 |
|------|----------|----------|----------|
| **试用转化率 < 10%** | 单日 invite_redeemed / landing_viewed < 10% (目标 15%) | 红色 | 12h 内 |
| **注册转化率 < 60%** | 单日 trial_started / invite_redeemed < 60% (目标 80%) | 红色 | 12h 内 |
| **付费转化率 < 15%** | 单日 paid_converted / trial_started < 15% (目标 25%) | 黄色 | 24h 内 |
| **创史转化率 < 40%** | 单日 advocate_promoted / trial_started < 40% (目标 60%) | 黄色 | 24h 内 |
| **创史招募率 < 80%** (8/23 前) | 单日 cumulative advocate_promoted / 80 < 80% | 红色 | 12h 内 |
| **创史群活跃 < 50%** | 单日 feedback_completed_day_N / advocate_promoted < 50% (Day 7/14/23/30) | 黄色 | 24h 内 |
| **创史付费转化 < 15%** | 单周 paid_converted (is_founding_member=True) / advocate_promoted < 15% (目标 30%) | 红色 | 24h 内 |
| **邀请码激活停滞** | 单日 invite_redeemed 变化 < 5 (连续 3 天) | 黄色 | 12h 内 |
| **评审律师失约** | 评审会前 1 天 评审律师未确认 | 红色 | 1h 内 |
| **创史招满延迟** | 08-23 创史未招满 60 席 (目标 80) | 黄色 | 24h 内 |

### 5.2 异常处理流程

`
异常检测 (Mavis 跑数据) -> 红色预警
  | 1h 内
BD 初步诊断 (邀请码状态 / 落地页 / onboarding 步骤)
  | 24h 内
总指挥拍板 (调整策略 / 紧急修复)
  | 48h 内
修复 + 二次数据验证
  | 7d 内
周报复盘 (写入 dashboard_w11.md § 5.2)
`

### 5.3 5 个高风险场景 (预案)

| 场景 | 触发 | 应对 |
|------|------|------|
| **场景 1: 公测启动日 (7/26) redeem < 30** | 当日 invite_redeemed < 30 | 朋友圈追加 1 条限时福利, 评审律师朋友圈帮转 |
| **场景 2: Day 7 留存 < 40%** | W11 末 trial_started / invite_redeemed < 40% | 紧急修复 onboarding (lex-coder P0), BD 1v1 微信回访激活律师 |
| **场景 3: 创史体验官招满 80 但激活 < 50%** | W12 末 advocate_promoted / invite_redeemed < 50% | 创史正式资格延后到反馈, 加强客服群 (BD 1v1) |
| **场景 4: Day 30 付费转化 < 15%** | W12 末 paid_converted / trial_started < 15% | 调整定价 (W13 折上折), 延后公测期 (8/30 截止) |
| **场景 5: 律协不批 80 席位** | 07-12 - 07-20 无批复 | 降级「律协背书 + 自营 50 创史」, W11 律协沙龙补足 |

---

## 6. 4 + 3 指标 SQL (Mavis 跑日报用)

### 6.1 注册转化率 (trial_started / invite_redeemed)

`sql
SELECT DATE(t2.created_at) AS day,
  COUNT(DISTINCT t2.user_id) AS invite_redeemed,
  COUNT(DISTINCT t3.user_id) AS trial_started,
  ROUND(COUNT(DISTINCT t3.user_id) * 100.0 / COUNT(DISTINCT t2.user_id), 1) AS reg_cvr_pct
FROM tracking_events t2
LEFT JOIN tracking_events t3 ON t2.user_id = t3.user_id
  AND t3.event = \'trial_started\'
  AND t3.created_at >= t2.created_at
WHERE t2.event = \'invite_redeemed\'
  AND t2.created_at >= \'2026-07-26\'
GROUP BY DATE(t2.created_at);
`

### 6.2 试用转化率 (invite_redeemed / landing_viewed)

`sql
SELECT DATE(t1.created_at) AS day,
  COUNT(DISTINCT t1.user_id) AS landing_viewed,
  COUNT(DISTINCT t2.user_id) AS invite_redeemed,
  ROUND(COUNT(DISTINCT t2.user_id) * 100.0 / COUNT(DISTINCT t1.user_id), 1) AS trial_cvr_pct
FROM tracking_events t1
LEFT JOIN tracking_events t2 ON t1.user_id = t2.user_id
  AND t2.event = \'invite_redeemed\'
  AND t2.created_at >= t1.created_at
WHERE t1.event = \'landing_viewed\'
  AND t1.created_at >= \'2026-07-26\'
GROUP BY DATE(t1.created_at);
`

### 6.3 付费转化率 (paid_converted / trial_started)

`sql
SELECT DATE_TRUNC(\'month\', t3.created_at) AS month,
  COUNT(DISTINCT t3.user_id) AS total_trial,
  COUNT(DISTINCT t4.user_id) AS paid_converted,
  ROUND(COUNT(DISTINCT t4.user_id) * 100.0 / COUNT(DISTINCT t3.user_id), 1) AS paid_cvr_pct
FROM tracking_events t3
LEFT JOIN tracking_events t4 ON t3.user_id = t4.user_id
  AND t4.event = \'paid_converted\'
  AND t4.created_at >= t3.created_at
WHERE t3.event = \'trial_started\'
  AND t3.created_at >= \'2026-07-26\'
GROUP BY DATE_TRUNC(\'month\', t3.created_at);
`

### 6.4 创史转化率 (advocate_promoted / trial_started)

`sql
SELECT DATE(t3.created_at) AS day,
  COUNT(DISTINCT t3.user_id) AS trial_started,
  COUNT(DISTINCT t5.user_id) AS advocate_promoted,
  ROUND(COUNT(DISTINCT t5.user_id) * 100.0 / COUNT(DISTINCT t3.user_id), 1) AS advocate_cvr_pct
FROM tracking_events t3
LEFT JOIN tracking_events t5 ON t3.user_id = t5.user_id
  AND t5.event = \'advocate_promoted\'
  AND t5.created_at >= t3.created_at
WHERE t3.event = \'trial_started\'
  AND t3.created_at >= \'2026-07-26\'
GROUP BY DATE(t3.created_at);
`

### 6.5 创史招募率 (advocate_promoted / 80 席目标)

`sql
SELECT DATE(t5.created_at) AS day,
  COUNT(DISTINCT t5.user_id) AS cumulative_advocate,
  ROUND(COUNT(DISTINCT t5.user_id) * 100.0 / 80, 1) AS recruitment_rate_pct
FROM tracking_events t5
WHERE t5.event = \'advocate_promoted\'
  AND t5.created_at >= \'2026-07-26\'
  AND t5.form_fields->>\'\'\'channel\'\'\' = \'\'\'founding_member\'\'\'
GROUP BY DATE(t5.created_at);
`

### 6.6 创史群活跃 (feedback_completed_day_N / advocate_promoted)

`sql
SELECT DATE(t7.created_at) AS day,
  t7.form_fields->>\'\'\'feedback_day\'\'\' AS day_label,
  COUNT(DISTINCT t7.user_id) AS feedback_completed,
  COUNT(DISTINCT t5.user_id) AS advocate_promoted_total,
  ROUND(COUNT(DISTINCT t7.user_id) * 100.0 / COUNT(DISTINCT t5.user_id), 1) AS engagement_rate_pct
FROM tracking_events t7
LEFT JOIN tracking_events t5 ON t7.user_id = t5.user_id
  AND t5.event = \'advocate_promoted\'
WHERE t7.event = \'feedback_completed\'
  AND t7.form_fields->>\'\'\'channel\'\'\' = \'\'\'founding_member\'\'\'
  AND t7.created_at >= \'2026-07-26\'
GROUP BY DATE(t7.created_at), t7.form_fields->>\'\'\'feedback_day\'\'\';
`

### 6.7 创史付费转化 (paid_converted is_founding_member=True / advocate_promoted)

`sql
SELECT DATE_TRUNC(\'week\', t4.created_at) AS week,
  COUNT(DISTINCT t4.user_id) AS founding_paid,
  COUNT(DISTINCT t5.user_id) AS total_founding,
  ROUND(COUNT(DISTINCT t4.user_id) * 100.0 / COUNT(DISTINCT t5.user_id), 1) AS founding_paid_rate_pct
FROM tracking_events t4
LEFT JOIN tracking_events t5 ON t5.event = \'advocate_promoted\'
  AND t5.user_id = t4.user_id
WHERE t4.event = \'paid_converted\'
  AND t4.form_fields->>\'\'\'is_founding_member\'\'\' = \'\'\'true\'\'\'
  AND t4.created_at >= \'2026-07-26\'
GROUP BY DATE_TRUNC(\'week\', t4.created_at);
`

---

## 7. 公测期 BD 每日动作 (W11 B2)

| 时间 | 动作 | 频率 | 责任人 |
|------|------|------|--------|
| 09:00 | 查 dashboard_w11.md 4+3 指标 (昨日) | 每天 | BD |
| 09:30 | 异常预警响应 (见 § 5.1) | 每天 | BD + 总指挥 |
| 10:00 | 监控邀请码状态 (unused -> redeemed -> active) | 每天 | BD |
| 10:30 | 律师群发反馈 (1 条朋友圈 / 1 条群内, 不刷屏) | 每天 | 总指挥 |
| 12:00 | 评审律师 1v1 微信回访 (1-2 位/天) | 每天 | 总指挥 |
| 15:00 | 创史意向跟进 (新入申请 5-10 位/天) | 每天 | BD |
| 18:00 | 律师 1v1 答疑 (微信咨询) | 每天 | BD + 总指挥 |
| 19:00 | 创史群公告 (创始律师群每日 1 条, 不刷屏) | 每天 | BD |
| 21:00 | 朋友圈 / 公众号内容发布 (1 条) | 每天 | 总指挥 + BD |
| 23:00 | Mavis 跑日报 (4 业务 + 3 创史 + 邀请码状态) | 每天 | Mavis |
| 23:30 | BD 回填 dashboard_w11.md § 1.1 + 邀请码状态 | 每天 | BD |

---

## 8. 验收标准 (W11 B2)

- [x] 4 业务指标定义 (注册 / 试用 / 付费 / 创史转化率) 跟 W10 B1 launch_funnel.md §2 对齐 - § 2
- [x] 3 创史专属指标新增 (招募率 / 群活跃 / 付费转化) - § 3
- [x] 7 渠道转化对比 (5 律所 + 微信群 + 创史 + 律协 + 公开) - § 4
- [x] 30 天异常预警 SOP (10 个异常 + 5 个高风险场景) - § 5
- [x] 4 + 3 = 7 个指标 SQL (Mavis 跑日报用) - § 6
- [x] 公测期 BD 每日动作清单 (11 个时点) - § 7
- [x] 引用 W6 f47db65 (首月漏斗 v0.1) + W10 B1 ce98f64 (4 指标 v2.0) - 文档头
- [x] 跟 dashboard_w6.md (W6 v0.1) 互补关系 - 文档头
