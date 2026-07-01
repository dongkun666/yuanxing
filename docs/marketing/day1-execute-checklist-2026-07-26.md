<!-- LexPrime Track B · W16 day1-execute-726 交付 -->
# 7/26 公测 day 1 执行检查表 (Day 1 Execute Checklist · 2026-07-26)

> **版本**: v1.0 · 2026-06-30
> **Track**: B (公测启动执行层)
> **Week**: W16 day1-execute-726
> **状态**: 公测前 26 天准备就位 (06-30), 7/26 当天打印随身执行
> **执行人**: 总指挥 (主持+颁奖) + 5 律师嘉宾 + BD (物料+邀请入群) + Coder (埋点验证) + Designer (PPT+证书)
> **配套** (W14 已交付):
> - `launch-runbook-final-2026-07-26.md` v2.0 (主持稿+嘉宾+物料+应急, 504 行)
> - `first-scan-tracking.md` v1.0 (5 律师扫码落地+公测 day 1-26 跟进)
> - `day1-report-2026-07-26.md` v1.0 (19:00 收尾报告模板, 公测当天填实)
> - `day1-dashboard-monitoring-2026-07-26.md` v1.0 (实时监控机制)
>
> **核心定位**: 本文档是 **执行日的快查清单** (轻量版), 详细主持稿走 launch-runbook-final-2026-07-26.md v2.0. 验收节点以 checkbox 形式呈现, 现场打勾即可.

---

## 0. 文档使用说明 (执行日 7/26 当天随身打印 1 份)

> 本表是 7/26 当天 09:00-19:00 **10h 执行流水**的快查版.
> 详细主持稿用 launch-runbook-final-2026-07-26.md, 详细物料清单用 launch-materials.md.
> **本表设计**: 9 个时段 (09:00 / 13:00 / 14:00 / 14:15 / 14:30 / 15:00 / 15:30 / 16:00 / 17:00 / 19:00), 每个时段 5-10 个 checkbox, 1 人主负责, 1-2 人协作.
> **总原则**: AI 辅助不替代律师, 数据本地化, 律师独立审查 + 签字才生效.

---

## 1. 09:00 招募页上线确认 — Mavis owner + Coder

> **目标**: 招募页 (templates/views/founding/index.html, 路由 `/founding`) 公测当天正式上线
> **责任人**: Coder (主) + Mavis owner (审核) + BD (朋友圈预告)

- [ ] **Coder 09:00 启动 dev server** (端口 8080, yuanxing 前端)
  ```bash
  cd E:\元枢法智前端\yuanxing
  python -m http.server 8080
  ```
- [ ] **Coder curl `/founding` 路由 200**
  ```bash
  curl -I http://127.0.0.1:8080/templates/views/founding/index.html?dev=1
  # 期望: HTTP/1.0 200 OK
  ```
- [ ] **Coder 浏览器打开 `/founding`** (zoom 100%) 验证 6 模块可见
  - 模块 1: Hero 价值主张 (¥449/年 5 折, 全球仅 100 席, 剩 80 席)
  - 模块 2: 名额倒计时 (距 8/23 截止还有 XX 天)
  - 模块 3: 已加入律师头像 (首批 20 席 L1-L6 + WX + BA)
  - 模块 4: 7/26 启动预告 (14:00-14:40 时段表)
  - 模块 5: 立即加入按钮 (申请表单 + 邀请码 BETA2025-XXXX)
  - 模块 6: 创始群二维码 (创史律师群 + 客服专属群 + 投票权通道)
- [ ] **Coder Chrome DevTools → Console 验证 `founding_viewed` 事件触发**
  ```javascript
  // 期望日志: [track] founding_viewed {user_id: "anonymous_...", session_id: "sess_..."}
  ```
- [ ] **Coder 移动端响应式检查** (375x812 iPhone 13 mini 视口)
  ```bash
  node scripts/founding-screenshots.js  # 已 commit (W11 B2)
  # 期望产物: tests/screenshots/founding-mobile-{ts}.png
  ```
- [ ] **Coder 截图 2 张** (PC 1440x900 + 移动 375x812) → `docs/marketing/screenshots/founding-2026-07-26/`
- [ ] **BD 09:30 朋友圈预告** (5 律师朋友圈 + 创始律师群, 公测启动倒计时)
- [ ] **Mavis owner 10:00 公众号"公测今天开放"推送** (Designer 排期 14:45, 提前 5h)

---

## 2. 13:00-13:30 仪式预热 — 总指挥 + 5 律师 + Coder

> **目标**: 14:00 启动仪式前的彩排 + 物料分发
> **责任人**: 总指挥 (主持) + 5 律师 (彩排) + BD (物料) + Coder (录屏测试) + Designer (录屏调试)

- [ ] **BD 13:00 分发物料** (5 律师各 1 份, 总指挥 1 份)
  - 邀请函 30 份 (W11 B2 beta-invitation.md 模板打印)
  - 招募页打印 30 张 (A4 黑白)
  - dashboard A4 截图 (W13 dashboard-view, 7 指标版本)
  - 创始群二维码 15 张 (W14 launch-materials.md §3)
- [ ] **Coder 13:00 腾讯会议入会 + 录屏调试** (5 律师 + 总指挥 + Designer 6 人入会)
- [ ] **Coder 13:10 主持稿试念** (3min 主持稿 §2.1 + §2.2, 总指挥走读)
- [ ] **Coder 13:15 5 律师视频测试** (60s 体验视频, 5 段拼 5 min)
- [ ] **Designer 13:20 录屏调试** (录屏软件 + 屏幕共享 + 麦克风 + 投影)
- [ ] **BD 13:25 公众号推送排期验证** (14:45 推送预排定, BD 二次确认)
- [ ] **总指挥 13:28 主持稿最后通读** (2 min 默读, 节奏 + 重点)

---

## 3. 14:00-17:00 启动仪式 60min — 总指挥 (主持人)

> **目标**: 7 段主持稿完整执行, 5 律师对话 + dashboard 演示 + KPI 公告 + 答疑
> **责任人**: 总指挥 (主持) + 5 律师 (对话) + Coder (dashboard 实时屏) + Designer (录屏)

### 3.1 14:00 时段 1 开场 (5 min) — 总指挥 + 5 律师嘉宾

- [ ] **00:00-01:30 自我介绍 + 评审 #2 致谢** (90s)
- [ ] **01:30-03:00 AI 辅助工具声明** (90s, 紫色 AI 角标 + 数据本地化)
- [ ] **03:00-05:00 5 律师 30 天试用回顾** (120s, 引用 L1-L5 真实使用场景)

### 3.2 14:15 时段 2 5 律师首批扫码 (15 min) — 总指挥 + 5 律师 + BD + Coder

> **5 律师邀请码** (W14 first-scan-tracking.md §1):
> - L1 单飞律师 BETA2025-0116 / L2 小所合伙 BETA2025-0117 / L3 婚姻家事 BETA2025-0118
> - L4 中所合伙 BETA2025-0119 / L5 企业法务 BETA2025-0120

- [ ] **00:00-02:00 5 律师介绍** (2 min, 总指挥邀请 5 律师现场扫码加入创始律师群)
- [ ] **02:00-08:00 5 律师现场扫码** (6 min, 屏幕共享显示)
  - [ ] L1 扫码: BETA2025-0116 → trial_started 事件触发
  - [ ] L2 扫码: BETA2025-0117 → trial_started 事件触发
  - [ ] L3 扫码: BETA2025-0118 → trial_started 事件触发
  - [ ] L4 扫码: BETA2025-0119 → trial_started 事件触发
  - [ ] L5 扫码: BETA2025-0120 → trial_started 事件触发
- [ ] **08:00-12:00 BD 邀请入群** (4 min, 创始律师群二维码 15 张分发)
- [ ] **12:00-15:00 5 律师朋友圈帮转** (3 min, BD 已准备 9 宫格文案 W15 093f014)

### 3.3 14:30 时段 3 7 大价值主张 (30 min) — 总指挥

- [ ] **第 1 大价值主张: 本地化** (4 min) — SQLite 案件本地存储
- [ ] **第 2 大价值主张: 智能非替代** (4 min) — AI 角标 + 律师独立审查
- [ ] **第 3 大价值主张: 越用越懂你** (4 min) — 本地化 RAG, 不上传污染
- [ ] **第 4 大价值主张: 立案前预审** (4 min) — 4 Skill 一体化
- [ ] **第 5 大价值主张: 类案只做参考** (4 min) — AI 不下结论, 律师下结论
- [ ] **第 6 大价值主张: 数据本地化** (4 min, 重申) — 律所合规 + 客户保密
- [ ] **第 7 大价值主张: 端到端加密** (6 min) — AES-256, 客户端密钥

### 3.4 15:00 时段 4 5 律师对话 (30 min, 每位 5 min) — 5 律师 L1-L5

- [ ] **L1 单飞律师** (5 min) — 类案检索 + 合同审查 + 文书生成 + 庭审准备 4 Skill 真实使用 + 5 折创史
- [ ] **L2 小所合伙人** (5 min) — 3 人小所批量处理体验, 5x 提效
- [ ] **L3 婚姻家事律师** (5 min) — 婚姻案件类案检索 30 秒出 10 个
- [ ] **L4 中所合伙人** (5 min) — 50 页合同 5 分钟报告, 致命条款不漏
- [ ] **L5 企业法务总监** (5 min) — 合规风险命中率高, 法务部 5x 提效
- [ ] **5 律师 + 主持人串讲** (5 min) — 全球 100 席已发 5 席, 剩 95 席公测开放

### 3.5 15:30 时段 5 30 律师付费 + 100 创史 + 5 渠道漏斗 (30 min) — 总指挥 + BD

- [ ] **30 律师付费目标** (8 min) — day 1-15 (7/26-8/9) 30 律师, 8/31 50 律师
- [ ] **100 创史招募** (8 min) — 全球 100 席, 招满 80 席 8/23 截止, 剩 20 席 9 月
- [ ] **创史 5 大权益** (4 min) — ¥449 5 折 + 终身优先客服 + 产品投票权 + 联合署名 + 创始群终身席位
- [ ] **5 渠道漏斗** (10 min) — 律协 100 + 创史 100 + 公测开放 1100 + 微信 100 + 朋友圈 9 宫格

### 3.6 16:00 时段 6 实时 dashboard 演示 (30 min) — 总指挥 + Coder

- [ ] **Coder 实时屏共享** (`templates/views/dashboard/index.html`, 路由 `/dashboard`)
- [ ] **总指挥讲解 7 指标**:
  - 注册 CVR (5 律师首批当天 5/5 = 100%)
  - 试用 CVR (5 律师首批当天 5/5 = 100%)
  - 付费 CVR (5 律师首批当天 0/5 = 0%, 待 7/29)
  - 创史 CVR (5 律师首批当天 5/5 = 100%)
  - 招募进度 (5/100 = 5%)
  - 群活跃 (5 律师 + 微信群 10 = 15)
  - 创史付费率 (0/5 = 0%, 待 7/29)
- [ ] **Coder 5min 实时刷新** (Mavis cron + 7 SQL, dashboard 5min 重新 fetch)
- [ ] **track event `dashboard_viewed`** 触发 (Coder 验证 Console 日志)

### 3.7 16:30 时段 7 答疑 + 互动 (30 min) — 总指挥 + 5 律师

- [ ] **高频 Q&A 卡片** (4 张, launch-materials.md §5):
  - "AI 是不是替代律师?" → 不替代, AI 辅助, 律师独立审查
  - "数据会不会上传服务器?" → 默认本地化, 服务器只存匿名统计
  - "¥449 跟 ¥899 个人版区别?" → 5 折 + 终身优先客服 + 投票权
  - "公测结束定价?" → ¥99/月或¥899/年, 创史锁价终身不变
- [ ] **Coder 答疑技术问题** (产品 bug / Skill 使用 / 邀请码问题)
- [ ] **BD 答疑商务问题** (发票 / 合同 / 退款 / 律所合作)

### 3.8 17:00 仪式正式收尾 (仪式 3h 收尾) — 总指挥

- [ ] **总指挥致辞感谢** (3-5 min, 引用 5 律师 + 律协代表 + 评审律师 + BD + Designer + Coder)
- [ ] **公众号"公测正式开放"推送** (Designer 14:45 排期, 当前自动推送)
- [ ] **朋友圈 9 宫格扩散** (5 律师 + BD + 总指挥 + 律协代表同步)
- [ ] **track event `ceremony_ended`** 触发 (Coder 验证 Console 日志)

---

## 4. 17:00-19:00 律师交流 + 首批扫码 — BD + 5 律师 + Coder

> **目标**: 仪式后 2h 律师深度 1v1 + 公测期 day 1-26 新律师扫码落地
> **责任人**: BD (1v1 微信) + 5 律师 (深度交流) + Coder (新律师扫码事件)

- [ ] **BD 17:30 创始律师群扩列** (5 律师 + 微信群律师 10 + 评审律师 = 15 人, 公测 day 1)
- [ ] **Coder 17:30 trial_started 事件验证** (5 律师首批 + 公测开放扫码律师, dashboard 5min 刷新)
- [ ] **BD 18:00 1v1 微信 5 律师** (5 位创始律师各 10 min, 体验回访 + 朋友圈邀评)
- [ ] **BD 18:30 公测开放首批律师扫码落地** (招募页 `/founding` 公测开放 1100 邀请码 0216-1115 段)
- [ ] **Coder 18:30 dashboard 公测 day 1 数据截图** (注册 + 试用 + 群活跃 3 块)
- [ ] **Coder 18:45 公测期 day 1 follow-up 日历** (7/27-7/30 节奏, W14 follow-up.md 落地)

---

## 5. 19:00 收尾 + 公测 day 1 报告 — 总指挥 + BD + Coder

> **目标**: 物料回收 + 当日复盘 + 公测期 day 1 报告 commit
> **责任人**: 总指挥 (复盘) + BD (1v1 跟进) + Coder (dashboard 数据 + 报告)

- [ ] **BD 19:00 物料回收** (邀请函草稿 + 招募页草稿 + 5 律师朋友圈帮转截图)
- [ ] **Coder 19:00 公测 day 1 dashboard 数据汇总** (5 律师首批 + 公测开放首批)
- [ ] **总指挥 19:10 当日复盘** (10 min, 5 分钟律反馈 + 应急处理 + 朋友圈转发)
- [ ] **Coder 19:20 公测 day 1 报告填实**:
  - 5 律师首批扫码时间戳 (first-scan-tracking.md §1 表格)
  - trial_started 事件数 (dashboard 23:00 cron 抓取)
  - 公测开放首批律师注册数 (招募页 `/founding` founding_joined 事件)
  - 群活跃 (创始律师群 + 公测律师微信群)
  - 营收快照 (5 律师首批 ¥449 创史 × 5 = ¥2245, 公测开放首批 30 天试用不营收)
- [ ] **Coder 19:30 公测 day 1 follow-up 日历填实** (W14 first-scan-tracking §2 day 2-7 节奏)
- [ ] **Coder 19:45 git commit + push** (W16 day1 commit = day1-report + first-scan-tracking + dashboard 截图)
- [ ] **总指挥 20:00 致谢短信** (5 律师 + 律协代表 + 评审律师, 复制 launch-runbook-final §5 模板)

---

## 6. 应急备案 (W14 launch-runbook-final §4)

### 6.1 招募页 09:00 上线失败
- **现象**: curl `/founding` 返回 5xx 或页面空白
- **响应**: Coder 立即看 dev server 日志 → 修复 → 09:30 重启 → 09:45 二次验证
- **回退**: 切到 `templates/views/beta/index.html` (W11 B2 老版本) 公测 landing, BD 朋友圈通知

### 6.2 5 律师 14:15 扫码仪式中断
- **现象**: 至少 1 位律师扫码失败 / 网络中断 / trial_started 未触发
- **响应**: BD 立即同步微信群其他律师备用码 (BETA2025-0121~0130)
- **回退**: Coder 强制重发邀请码邮件 (smtp-credentials.env 已就位), 14:30 仪式继续

### 6.3 16:00 dashboard 演示失败
- **现象**: dashboard `/dashboard` 5min 刷新异常 / 7 指标 fetch 失败
- **响应**: Coder 立即切到 dashboard_w11.md 静态版本 (W11 B2 commit a10aecc), 总指挥口述 7 指标
- **回退**: 截图 dashboard 历史快照 (W13 commit c62877c), 16:15 重新演示

### 6.4 17:00 收尾时网络中断
- **现象**: 录屏中断 / 公众号推送失败 / 朋友圈帮转未发
- **响应**: Designer 立即重发录屏 + 公众号推送, BD 微信群通知补发朋友圈 9 宫格
- **回退**: 公测期 day 2 7/27 补发朋友圈 9 宫格 (W14 first-scan-tracking.md §2 day 2)

---

## 7. 验收清单 (公测 day 1 19:00 收尾时核对)

- [ ] 9 个时段全部走完 (09:00-19:00, 10h)
- [ ] 招募页 6 模块 + 2 个 track event (`founding_viewed` + `founding_joined`) 验证
- [ ] 5 律师首批扫码落地 (BETA2025-0116~0120, 5 个 trial_started 事件)
- [ ] 60min 启动仪式完整 (7 段主持稿 + 5 律师对话 + 30 律师付费目标 + dashboard 演示)
- [ ] 公测 day 1 trial_started 事件数 = 5 (5 律师首批)
- [ ] dashboard 实时截图 (PC + 移动各 1 张, `docs/marketing/screenshots/founding-2026-07-26/`)
- [ ] day1-report-2026-07-26.md 完整 (5 律师扫码 + 试用事件 + 群活跃 + 应急备案)
- [ ] git commit + push 1 commit (W16 day1 commit)

---

## 8. 公测 day 1 当日 SOP 链接 (7/26 当天执行者随身打印)

| 文档 | 用途 | 行数 |
|------|------|------|
| `day1-execute-checklist-2026-07-26.md` (本表) | 09:00-19:00 快查清单 | - |
| `launch-runbook-final-2026-07-26.md` v2.0 | 详细主持稿+嘉宾+物料+应急 | 504 |
| `launch-materials.md` v2.0 | 73 件物料清单 (易拉宝+海报+证书) | 73 |
| `launch-funnel.md` v2.0 | 5 事件 + 4 指标 (W10 B1) | - |
| `first-scan-tracking.md` v1.0 | 5 律师扫码落地+公测 day 1-26 跟进 | 174 |
| `day1-dashboard-monitoring-2026-07-26.md` v1.0 | 实时监控机制 + 7 SQL 验证 | - |
| `day1-report-2026-07-26.md` v1.0 | 19:00 收尾报告模板 | placeholder |
| `dashboard_w11.md` v1.0 | 7 指标 fallback (W11 B2) | - |
| `invite-codes-list.csv` | 1115 邀请码池 (6 渠道) | - |
| `lawyer-emails.json` | 5 律师邮箱 placeholder | - |

---

> **整理人**: lex-bd (BD/运营)
> **协作**: 总指挥 (主持+颁奖) · 5 律师嘉宾 (扫码+对话) · BD (物料+邀请) · Coder (埋点+dashboard) · Designer (PPT+证书+录屏)
> **文档版本**: v1.0 (2026-06-30)
> **7/26 当天使用**: 总指挥 + 5 律师 + BD + Coder + Designer 各打印 1 份, 09:00 仪式前 5min 集合对齐
