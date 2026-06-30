<!-- LexPrime Track B · W16 day1-execute-726 交付 -->
# 7/26 公测 day 1 dashboard 实时监控机制 (Day 1 Dashboard Monitoring · 2026-07-26)

> **版本**: v1.0 · 2026-06-30
> **Track**: B (公测启动执行层)
> **Week**: W16 day1-execute-726
> **状态**: 公测前 26 天准备就位 (06-30), 7/26 当天 Coder + 5 律师 + BD 实时监控
> **配套**:
> - `dashboard_w11.md` v1.0 (W11 B2 commit a10aecc, 4 业务 + 3 创史专属指标)
> - `templates/views/dashboard/index.html` (W13 commit c62877c, 7 指标视图)
> - `day1-report-2026-07-26.md` v1.0 (19:00 收尾报告 § 6 dashboard 数据 placeholder)
> - `first-scan-tracking.md` v1.0 (§ 1.2 dashboard 7 指标验证占位符)
>
> **核心定位**: 公测 day 1 (7/26) 09:00-19:00 实时监控 dashboard 7 指标 + 应急备案 + 公测 day 1-30 跟踪

---

## 0. 文档使用说明

> 本表是公测 day 1 (7/26) 当天 **dashboard 实时监控机制 + 5min 刷新 + 7 SQL 验证 + 4 应急备案**.
> 数据源: Mavis cron 23:00 跑 7 SQL + trial_expired SQL (W11 C1 commit 4910305) + 5min 实时刷新 (browser `setInterval` 5min fetch).
> Fallback: dashboard_w11.md 静态版本 (W11 B2 已 commit), 紧急时由 Coder 切静态.
> **严守**: AI 辅助不替代律师, 数据本地化, 7 指标对公测律所透明, 不虚报不漏报.

---

## 1. dashboard 5min 实时刷新机制 (7/26 09:00-19:00 Coder 启)

### 1.1 dashboard 路由 + 视图

- **路由**: `/dashboard` (yuanxing 前端 dev server `http://127.0.0.1:8080/templates/views/dashboard/index.html`)
- **视图**: `templates/views/dashboard/index.html` (W13 commit c62877c, 39KB)
- **7 指标**: 注册 CVR + 试用 CVR + 付费 CVR + 创史 CVR + 招募进度 + 群活跃 + 创史付费率 (W11 B2)
- **3 chart.js**: 公测期 day 1-30 trial_started 趋势线 + paid_converted 漏斗 + advocate_promoted 转化堆叠柱

### 1.2 5min 实时刷新 (browser `setInterval`)

```javascript
// 已 commit, W13 dashboard 视图内置
function refreshDashboard() {
  Promise.all([
    fetch('/api/metrics/registration'),
    fetch('/api/metrics/trial'),
    fetch('/api/metrics/payment'),
    fetch('/api/metrics/advocate'),
    fetch('/api/metrics/recruitment'),
    fetch('/api/metrics/group-activity'),
    fetch('/api/metrics/advocate-payment')
  ])
  .then(responses => Promise.all(responses.map(r => r.json())))
  .then(data => updateMetrics(data))
  .catch(err => console.error('[dashboard] 5min 刷新失败', err));
}

setInterval(refreshDashboard, 5 * 60 * 1000);  // 5min
```

- **09:00 启动**: Coder 在公测 day 1 09:00 启动 dev server 后打开 `/dashboard`
- **09:00-19:00 实时**: dashboard 5min 自动刷新, Coder 监控 Console 无异常
- **16:00 演示**: 仪式时段 6 Coder 屏幕共享给律师朋友看实时数据
- **19:00 收尾**: Coder 截图 (PC + 移动) → `docs/marketing/screenshots/founding-2026-07-26/dashboard-pc-{ts}.png`

### 1.3 7 指标实时数据流 (09:00-19:00 Coder 监控)

- 注册 CVR → /api/metrics/registration (Mavis cron + Apache 后端)
- 试用 CVR → /api/metrics/trial (同上)
- 付费 CVR → /api/metrics/payment (L1/L2/L3 试用 7/29 到期前 = 0, 转化后递增)
- 创史 CVR → /api/metrics/advocate (5 律师首批 + 招募页申请)
- 招募进度 → /api/metrics/recruitment (advocate_promoted / 100 席)
- 群活跃 → /api/metrics/group-activity (创始律师群 + 公测律师微信群)
- 创史付费率 → /api/metrics/advocate-payment (待 7/29 L1/L2/L3 转化后)

---

## 2. Mavis cron 23:00 dashboard 抓取 (7/26 23:00 自动)

### 2.1 Mavis cron 23:00 自动 fire

```bash
# Mavis cron 配置 (W11 C1 commit 4910305)
# cron job: 23:00 CST 每日自动 fire
0 23 * * *  mavis cron self dashboard-validation \
  --every 86400 \
  --prompt "执行 dashboard 7 SQL 验证 + 输出指标 JSON + 异常预警: docs/marketing/day1-report-2026-07-26.md § 6 公测 day 1 数据 placeholder 填实"
```

- **23:00 CST**: 每日 23:00 Mavis cron 自动跑 7 SQL
- **23:30 BD 校验**: BD 人工校验 dashboard 数据与 JSON 输出一致
- **23:30 异常预警**: 任何指标 > 1.5x 或 < 0.5x 平均 → 自动报警到 owner 微信

### 2.2 7 SQL 验证 (W11 C1 commit 4910305 + W13 dashboard 视图)

| SQL | 指标 | 计算公式 | 公测 day 1 预期 |
|-----|------|----------|----------------|
| `count_registration` | 注册 CVR | trial_started / landing_viewed | 5/50 = 10% |
| `count_trial` | 试用 CVR | trial_started / invite_redeemed | 5/5 = 100% |
| `count_payment` | 付费 CVR | paid_converted / trial_started | 0/5 = 0% (待 7/29) |
| `count_advocate` | 创史 CVR | advocate_promoted / trial_started | 5/5 = 100% |
| `count_recruitment` | 招募进度 | advocate_promoted / 100 席 | 5/100 = 5% |
| `count_group_activity` | 群活跃 | DAU 创始律师群 | 5 (5 律师) |
| `count_advocate_payment` | 创史付费率 | paid_converted / advocate_promoted | 0/5 = 0% (待 7/29) |

### 2.3 dashboard 抓取产物 (7/26 23:00 → day 1-30 持续)

- `docs/marketing/screenshots/founding-2026-07-26/dashboard-pc-{ts}.png` (Coder 截)
- `docs/marketing/screenshots/founding-2026-07-26/dashboard-mobile-{ts}.png`
- `logs/cron/dashboard-validation-2026-07-26.log` (Mavis cron 自动落档)
- `logs/cron/dashboard-validation-2026-07-26.json` (Mavis cron 7 SQL 输出)

---

## 3. 7 指标计算公式 + SQL 详解

### 3.1 注册 CVR (Registration CVR)

```sql
-- 公式: trial_started / landing_viewed
SELECT
  (SELECT COUNT(DISTINCT user_id) FROM events WHERE event = 'trial_started' AND ts >= '2026-07-26') AS trial,
  (SELECT COUNT(DISTINCT session_id) FROM events WHERE event = 'landing_viewed' AND ts >= '2026-07-26') AS landing,
  CAST((SELECT COUNT(DISTINCT user_id) FROM events WHERE event = 'trial_started' AND ts >= '2026-07-26') AS REAL) /
  NULLIF((SELECT COUNT(DISTINCT session_id) FROM events WHERE event = 'landing_viewed' AND ts >= '2026-07-26'), 0) AS cvr;
```

- **公测 day 1 预期**: 5/50 = 10% (5 律师首批 + 招募页访问 50)
- **数据源**: events table (`trial_started` + `landing_viewed` events)
- **计算口径**: 7/26 00:00-23:59 (CST)

### 3.2 试用 CVR (Trial CVR)

```sql
-- 公式: trial_started / invite_redeemed
SELECT
  (SELECT COUNT(*) FROM events WHERE event = 'trial_started' AND ts >= '2026-07-26') AS trial,
  (SELECT COUNT(*) FROM invite_codes WHERE redeemed_at >= '2026-07-26') AS redeemed,
  CAST((SELECT COUNT(*) FROM events WHERE event = 'trial_started' AND ts >= '2026-07-26') AS REAL) /
  NULLIF((SELECT COUNT(*) FROM invite_codes WHERE redeemed_at >= '2026-07-26'), 0) AS cvr;
```

- **公测 day 1 预期**: 5/5 = 100% (5 律师首批全部 redeem)
- **数据源**: events table + invite_codes table
- **计算口径**: 7/26 00:00-23:59 (CST)

### 3.3 付费 CVR (Payment CVR)

```sql
-- 公式: paid_converted / trial_started
SELECT
  (SELECT COUNT(*) FROM events WHERE event = 'paid_converted' AND ts >= '2026-07-26') AS paid,
  (SELECT COUNT(*) FROM events WHERE event = 'trial_started' AND ts >= '2026-07-26') AS trial,
  CAST((SELECT COUNT(*) FROM events WHERE event = 'paid_converted' AND ts >= '2026-07-26') AS REAL) /
  NULLIF((SELECT COUNT(*) FROM events WHERE event = 'trial_started' AND ts >= '2026-07-26'), 0) AS cvr;
```

- **公测 day 1 预期**: 0/5 = 0% (L1/L2/L3 7/29 到期前不付费)
- **数据源**: events table
- **计算口径**: 7/26 00:00-23:59 (CST)

### 3.4 创史 CVR (Advocate CVR)

```sql
-- 公式: advocate_promoted / trial_started
SELECT
  (SELECT COUNT(*) FROM events WHERE event = 'advocate_promoted' AND ts >= '2026-07-26') AS advocate,
  (SELECT COUNT(*) FROM events WHERE event = 'trial_started' AND ts >= '2026-07-26') AS trial,
  CAST((SELECT COUNT(*) FROM events WHERE event = 'advocate_promoted' AND ts >= '2026-07-26') AS REAL) /
  NULLIF((SELECT COUNT(*) FROM events WHERE event = 'trial_started' AND ts >= '2026-07-26'), 0) AS cvr;
```

- **公测 day 1 预期**: 5/5 = 100% (5 律师首批全部 is_founding_member=True, 创史 #16-20)
- **数据源**: events table (advocate_promoted = W11 B2 founding_joined)
- **计算口径**: 7/26 00:00-23:59 (CST)

### 3.5 招募进度 (Recruitment Progress)

```sql
-- 公式: advocate_promoted / 100 席
SELECT
  (SELECT COUNT(*) FROM events WHERE event = 'advocate_promoted' AND ts >= '2026-06-30') AS advocate,
  100 AS target,
  CAST((SELECT COUNT(*) FROM events WHERE event = 'advocate_promoted' AND ts >= '2026-06-30') AS REAL) / 100 AS progress;
```

- **公测 day 1 预期**: 5/100 = 5% (5 律师首批 + 之前 15 律师预留, 但数据统计从 6/30)
- **数据源**: events table (6/30 公测开放邀请码起算)
- **计算口径**: 6/30 00:00 - 8/23 23:59 (CST, 8/23 招满 80 席截止)

### 3.6 群活跃 (Group Activity)

```sql
-- 公式: DAU 创始律师群 (有聊天记录)
SELECT COUNT(DISTINCT user_id) FROM events
WHERE event = 'group_message_sent'
  AND group_id = 'founding-lawyer-group'
  AND ts >= date('now', '-1 day');
```

- **公测 day 1 预期**: 5 (5 律师首批 + 微信群律师 10 = 15, 但 dashboard 显示新加入律师)
- **数据源**: events table (group_message_sent)
- **计算口径**: 7/26 00:00-23:59 (CST)

### 3.7 创史付费率 (Advocate Payment Rate)

```sql
-- 公式: paid_converted / advocate_promoted
SELECT
  (SELECT COUNT(*) FROM events WHERE event = 'paid_converted' AND user_id IN (SELECT user_id FROM events WHERE event = 'advocate_promoted') AND ts >= '2026-07-26') AS paid_advocate,
  (SELECT COUNT(*) FROM events WHERE event = 'advocate_promoted' AND ts >= '2026-06-30') AS advocate,
  CAST((SELECT COUNT(*) FROM events WHERE event = 'paid_converted' AND user_id IN (SELECT user_id FROM events WHERE event = 'advocate_promoted') AND ts >= '2026-07-26') AS REAL) /
  NULLIF((SELECT COUNT(*) FROM events WHERE event = 'advocate_promoted' AND ts >= '2026-06-30'), 0) AS rate;
```

- **公测 day 1 预期**: 0/5 = 0% (待 7/29 L1/L2/L3 转化)
- **数据源**: events table
- **计算口径**: 7/26 00:00-23:59 (CST, 转化后递增)

---

## 4. 应急备案 (4 场景, 7/26 09:00-23:00 Coder 监控)

### 4.1 dashboard 5min 实时刷新失败

- **现象**: dashboard `/dashboard` Console 报错 / setInterval 停止
- **响应** (Coder): 检查 dev server → 重启 → 09:30 二次验证
- **回退**: 切到 dashboard_w11.md § 1.1 静态版本 (W11 B2 commit a10aecc), 总指挥口述 7 指标
- **异常预警**: Mavis cron 23:00 自动报警 (任何指标异常)

### 4.2 trial_started 事件未触发

- **现象**: 5 律师首批扫码后, dashboard 试用 CVR 仍是 0%
- **响应** (Coder): 检查 `/api/metrics/trial` → 重启 backend → 14:30 重试
- **回退**: 律师改用备用邀请码 (BETA2025-0121~0130), BD 微信群同步
- **异常预警**: dashboard trial CVR = 0% 持续 > 1h → 自动报警

### 4.3 Mavis cron 23:00 dashboard 抓取失败

- **现象**: cron job 未自动 fire / 7 SQL 失败 / JSON 输出损坏
- **响应** (Coder): 7/27 09:00 手动重跑 7 SQL → 补抓公测 day 1 数据
- **回退**: 用 day 1 19:00 dashboard 截图 (PC + 移动) 替代
- **异常预警**: cron fail 持续 > 24h → 自动报警 + owner 微信通知

### 4.4 16:00 仪式时段 6 dashboard 演示网络中断

- **现象**: 16:00-16:30 dashboard 屏幕共享失败 / 律师朋友无法看到
- **响应** (Coder): 立即切到 dashboard_w11.md 静态截图 → 总指挥口述
- **回退**: 16:15 重新演示 / 16:30 答疑延后
- **异常预警**: 仪式现场应急备案 (W14 launch-runbook § 4.3)

---

## 5. 公测 day 1-30 跟踪节奏 (W14 first-scan-tracking.md § 2-4 + W16 多 plan)

### 5.1 公测 day 1-7 (7/26-8/1): 招募 + 5 渠道密集投放 + 朋友圈扩散

- day 1 (7/26): 招募页上线 + 5 律师首批扫码 + 公测 14:40 开放
- day 2-7 (7/27-8/1): BD 1v1 微信 + 公众号推文 + 朋友圈 9 宫格
- 公测 day 1-7 dashboard 跟踪: 招募进度 5/100 → 25/100 (5 律师首批 + 20 律师试用)

### 5.2 公测 day 8-14 (8/2-8/9): 朋友圈 9 宫格 + 朋友推荐

- day 8-14 (8/2-8/9): 朋友圈 9 宫格 + 朋友推荐 + 创史律师群互推
- 公测 day 8-14 dashboard 跟踪: 招募进度 25/100 → 60/100 (35 律师试用 + 创史群互推)

### 5.3 公测 day 15 (8/9): 30 律师付费目标截止 (W16 kpi-track-809 plan)

- day 15 (8/9): 30 律师付费目标 (公测 day 1-15, 25% 转化率)
- 公测 day 15 dashboard 验证: 付费 CVR 30/100 = 30% (W14 first-scan-tracking § 5 公式)

### 5.4 公测 day 16-30 (8/10-8/24): 创史招募冲刺 + L4/L5 评审前导

- day 16-26 (8/10-8/20): 公测期 day 16-26 收尾 + 创史招募冲刺
- day 27-30 (8/21-8/24): L4/L5 评审 #2 律师到期前导 (W16 l4l5-preheat-819 plan)
- 公测 day 16-30 dashboard 跟踪: 招募进度 60/100 → 80/100 (8/23 招满截止)

### 5.5 公测 day 30+ (8/25+): L4/L5 转化 + 8 月底冲刺 (W15 l4l5 + W16 phase4-close-831)

- day 31 (8/25): L4/L5 评审 #2 律师试用到期 (W15 l4l5 commit 900948f)
- day 32-37 (8/26-8/31): L4/L5 转化 + 8 月底冲刺
- day 37 (8/31): 50 律师付费 / 月 ¥5 万+ ARR 截止 (W16 phase4-close-831 plan)

---

## 6. 公测 day 1 dashboard 验收清单 (7/26 19:00 Coder 核对)

- [ ] 9 个时段 dashboard 5min 实时刷新 0 异常 (09:00-19:00)
- [ ] 5 律师首批 trial_started 5/5 = 100% (14:15-14:30)
- [ ] 公测 day 1 founding_joined __ (招募页公测 14:40 开放后 0-4h)
- [ ] 公测 day 1 advocate_promoted 5 (5 律师首批, 创史 #16-20)
- [ ] 公测 day 1 群活跃 5-15 (5 律师 + 微信群律师)
- [ ] dashboard 截图 PC + 移动各 1 张 (`docs/marketing/screenshots/founding-2026-07-26/`)
- [ ] Mavis cron 23:00 dashboard 抓取成功 (7 SQL + JSON 输出)
- [ ] 4 应急备案 0 触发 (招募页 / 5 律师 / Mavis cron / 16:00 演示)
- [ ] day1-report-2026-07-26.md § 6 dashboard 数据填实 (23:30 BD 校验)

---

## 7. 公测 day 1-30 dashboard 监控 SOP 链接

| 文档 | 用途 | 行数 |
|------|------|------|
| `day1-dashboard-monitoring-2026-07-26.md` (本表) | dashboard 实时监控机制 + 7 SQL | - |
| `dashboard_w11.md` v1.0 | 7 指标 fallback (W11 B2) | - |
| `dashboard_w10.md` v1.0 | W10 5 业务事件原始定义 (W10 B1) | - |
| `dashboard-recruit-1000.md` v1.0 | 5 渠道漏斗 dashboard (W15 d66fc33) | - |
| `dashboard-l4l5-triggers.md` v1.0 | L4/L5 触发 dashboard (W15 900948f) | - |
| `dashboard-paid-triggers.md` v1.0 | 付费触发 dashboard (W14 6f785e5) | - |
| `templates/views/dashboard/index.html` | 7 指标视图 (W13 c62877c) | 39KB |
| `scripts/validate_dashboard_sql.py` | 7 SQL 验证脚本 (W11 C1 4910305) | - |

---

> **整理人**: lex-bd (BD/运营)
> **协作**: Coder (dashboard 监控 + 7 SQL) · BD (公测 day 1 校验) · 总指挥 (应急备案+复盘)
> **文档版本**: v1.0 (2026-06-30)
> **7/26 当天使用**: Coder 09:00 启动 dashboard 5min 实时刷新, 23:00 Mavis cron 自动抓 7 SQL, 公测 day 1-30 持续跟踪.
