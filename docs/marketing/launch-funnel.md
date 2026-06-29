<!-- LexPrime Track B · W10 B1 交付 -->
# 公测期 5 事件埋点 + 4 指标转化漏斗 (Launch Funnel)

> **版本**: v2.0 · 2026-06-29
> **Track**: B (公测启动漏斗)
> **Week**: W10 B1 Day 1
> **目标**: 公测期 30 天 (7/26 - 8/24) 5 事件埋点 + 4 指标日看板
> **上一版**: `dashboard-w6.md` v0.1 (W6 Day 3, commit f47db65) + `tracking-events.md` v0.1
> **配套**: `beta-launch-event-2026-07-26.md` (60 min 流程) · `launch-invitation.md` (邀请函) · `launch-materials.md` (物料)
>
> **核心升级** (v2.0 vs v0.1):
> - 5 事件从 W6 的 trial_landing_pv/trial_register_submit/onboarding_complete_3_step/login/skill_run 升级为 **landing_viewed / invite_redeemed / trial_started / paid_converted / advocate_promoted**
> - 5 事件严格对应公测启动漏斗 (W6 是技术埋点, W10 是公测期业务漏斗)
> - 4 指标从 W6 的 WAU/漏斗/留存/付费 简化为 **注册转化率 / 试用转化率 / 付费转化率 / 创史转化率**
> - 公测期 30 天 (7/26 - 8/24) 日看板 + 4 周周报
> - 评审律师 L1 BETA2025-0001 已 redeem (W7 commit 5437535), 创史转化率 100% 计入

---

## 1. 5 事件定义 (W10 B1 公测期业务漏斗)

> **核心原则**: 5 事件严格对应公测启动漏斗的业务节点, 不重复 W6 技术埋点.
> **数据流**: 5 事件 → 4 指标 → 30 天日看板 → 4 周周报 → 公测报告 (W11 末)
> **落地方式**: lex-coder W10 B1 末 (7/25 前) 在 backend/cases-crawler/api/tracking_router.py 落地 5 个 event 名严格按本文 § 1

### 1.0 5 事件 vs W6 5 事件 对照表

| W10 B1 (本文) | W6 v0.1 (tracking-events.md) | 关系 | 升级原因 |
|---------------|------------------------------|------|----------|
| `landing_viewed` | `trial_landing_pv` | 重命名 + 扩展 | 公测 landing 7 大模块 PV, 扩展到公测期所有页面 |
| `invite_redeemed` | (无, 走 invite 状态机) | 新增 | 公测期业务关键节点, 邀请码兑换 = 激活律师进入试用 |
| `trial_started` | `trial_register_submit` | 重命名 | 公测期正式业务事件名, 试用开始 |
| `paid_converted` | `payment_success` (非 5 事件) | 提升为 5 事件 | 公测期关键转化, 付费转化是核心业务节点 |
| `advocate_promoted` | (无, 走创史状态机) | 新增 | 公测期核心业务事件, 创史体验官晋升 (80 席剩 80) |

> **总结**: W10 B1 5 事件 = 公测期业务漏斗, W6 5 事件 = 技术埋点. W10 优先业务, W6 仍保留作为技术埋点.

---

### 1.1 Event 1: `landing_viewed` (访问, 漏斗 step 1)

> **触发位置**: 公测 landing 7 大模块 + 公测期所有页面 (公众号文章 / 朋友圈 9 宫格 / 律师群)
> **触发代码** (前端):
> ```js
> track('landing_viewed', { page_url: location.pathname, invite_code: getQueryParam('ref'), utm_source: getQueryParam('utm_source') });
> ```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `event` | string | ✅ | 固定 `landing_viewed` |
| `user_id` | string | ✅ | 用户 UUID (未登录时填 `anonymous_<ip>`) |
| `session_id` | string | ✅ | 会话 UUID (前端生成, 30 min 内同会话) |
| `created_at` | timestamp | ✅ | UTC+8 时间戳 |
| `page_url` | string | ✅ | landing 页面 URL (例: `/beta`, `/founding-member`) |
| `referrer` | string | ⛔ | 来源 URL (微信, 朋友圈, 公众号, 邮件) |
| `invite_code` | string | ⛔ | URL 邀请码 (BETA2025-XXXX), 渠道归因 |
| `utm_source` | string | ⛔ | 渠道 (wechat / email / qr / referral / bar-association / public) |
| `device_type` | string | ⛔ | mobile / desktop / tablet |

**漏斗角色**: 5 步漏斗 step 1, 公测期所有访问的基线
**目标**: 公测期 30 天累计 1000+ 访问 (评审律师 5 + 微信群 10 + 创史 80 + 公开 905)

### 1.2 Event 2: `invite_redeemed` (兑换, 漏斗 step 2)

> **触发位置**: 律师点击邀请链接, 完成邀请码兑换 + 注册表单 (后端自动记录)
> **触发代码** (后端):
> ```python
> async def redeem_invite(req: InviteRedeemRequest, db: AsyncSession = Depends(get_db)):
>     invite = await db.scalar(select(InviteCode).where(InviteCode.code == req.invite_code))
>     if not invite or invite.status != "unused":
>         raise HTTPException(400, "邀请码无效或已使用")
>     invite.status = "redeemed"
>     invite.redeemed_at = datetime.now(CST)
>     invite.assigned_to = req.name
>     await track_event(db, event="invite_redeemed", user_id=req.user_id,
>                       invite_code=req.invite_code, channel=invite.channel,
>                       form_fields={"name": req.name, "firm": req.firm})
>     return {"invite_id": invite.id}
> ```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `event` | string | ✅ | 固定 `invite_redeemed` |
| `user_id` | string | ✅ | 用户 UUID (注册成功后填充) |
| `session_id` | string | ✅ | 会话 UUID |
| `created_at` | timestamp | ✅ | UTC+8 时间戳 |
| `invite_code` | string | ✅ | 邀请码 (BETA2025-XXXX) |
| `channel` | string | ✅ | 渠道 (review / wechat-group / founding-member / bar-association / public) |
| `form_fields` | json | ⛔ | 表单字段 (例: `{"name": "张律师", "firm": "金杜"}`) |
| `ip_address` | string | ⛔ | 兑换 IP (防刷, 1 IP / 1h / 3 次) |

**漏斗角色**: 5 步漏斗 step 2, 关键业务节点 = 邀请码激活 = 进入试用阶段
**目标**: 公测期 30 天累计 150+ 兑换 (评审 5 + 微信群 8 + 创史 80 + 公开 60, 评审律师 L1 BETA2025-0001 已 redeem 计入 W7)

### 1.3 Event 3: `trial_started` (试用, 漏斗 step 3)

> **触发位置**: 律师完成邮箱验证 + 创建账号 + 30 天试用生效 (后端自动记录)
> **触发代码** (后端):
> ```python
> async def start_trial(req: TrialStartRequest, db: AsyncSession = Depends(get_db)):
>     user = await create_user(db, req.email, req.name)
>     trial = await create_trial(db, user.id, duration_days=30)
>     await track_event(db, event="trial_started", user_id=user.id,
>                       email=req.email, invite_code=req.invite_code,
>                       channel=invite.channel, trial_id=trial.id,
>                       trial_expires_at=trial.expires_at)
>     return {"user_id": user.id, "trial_id": trial.id, "trial_expires_at": trial.expires_at}
> ```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `event` | string | ✅ | 固定 `trial_started` |
| `user_id` | string | ✅ | 用户 UUID |
| `session_id` | string | ✅ | 会话 UUID |
| `created_at` | timestamp | ✅ | UTC+8 时间戳 |
| `email` | string | ✅ | 注册邮箱 (RFC 5322 校验) |
| `invite_code` | string | ✅ | 邀请码 (BETA2025-XXXX) |
| `channel` | string | ✅ | 渠道 |
| `trial_id` | string | ✅ | 试用记录 ID |
| `trial_expires_at` | timestamp | ✅ | 试用到期时间 (注册 + 30 天) |

**漏斗角色**: 5 步漏斗 step 3, 律师正式进入 30 天试用
**目标**: 公测期 30 天累计 120+ 试用 (兑换 150 × 80% 试用转化率)

### 1.4 Event 4: `paid_converted` (付费, 漏斗 step 4)

> **触发位置**: 律师完成支付 (Stripe webhook 接收 payment_intent.succeeded)
> **触发代码** (后端):
> ```python
> async def stripe_webhook(req: Request, db: AsyncSession = Depends(get_db)):
>     event = stripe.Webhook.construct_event(req.body, sig_header, STRIPE_WEBHOOK_SECRET)
>     if event["type"] == "payment_intent.succeeded":
>         intent = event["data"]["object"]
>         user_id = intent["metadata"]["user_id"]
>         await track_event(db, event="paid_converted", user_id=user_id,
>                           payment_intent_id=intent["id"],
>                           amount=intent["amount"] / 100,
>                           currency=intent["currency"],
>                           pricing_plan=intent["metadata"]["pricing_plan"],
>                           is_founding_member=intent["metadata"].get("is_founding_member", False))
>         # 更新用户付费状态
>         await update_user_payment_status(db, user_id, "paid")
>     return {"ok": True}
> ```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `event` | string | ✅ | 固定 `paid_converted` |
| `user_id` | string | ✅ | 用户 UUID |
| `session_id` | string | ✅ | 会话 UUID |
| `created_at` | timestamp | ✅ | UTC+8 时间戳 |
| `payment_intent_id` | string | ✅ | Stripe 支付 ID |
| `amount` | decimal | ✅ | 支付金额 (元) |
| `currency` | string | ✅ | 货币 (CNY) |
| `pricing_plan` | string | ✅ | 价格套餐 (personal_year / personal_month / pro_year / pro_month / founding_year) |
| `is_founding_member` | bool | ✅ | 是否创始体验官 (5 折 ¥449/年) |

**漏斗角色**: 5 步漏斗 step 4, 律师完成支付, 公测期核心转化
**目标**: 公测期 30 天累计 30+ 付费 (试用 120 × 25% 付费转化率)

### 1.5 Event 5: `advocate_promoted` (创史晋升, 漏斗 step 5)

> **触发位置**: 律师完成 Day 30 反馈问卷 + 创始体验官申请审核通过
> **触发代码** (后端):
> ```python
> async def promote_advocate(req: AdvocatePromoteRequest, db: AsyncSession = Depends(get_db)):
>     user = await db.scalar(select(User).where(User.id == req.user_id))
>     advocate = await create_advocate(db, user.id,
>                                      discount_plan="personal_year_5off",
>                                      lifetime_priority_support=True,
>                                      voting_rights=True,
>                                      certificate_url=req.certificate_url)
>     await track_event(db, event="advocate_promoted", user_id=user.id,
>                       advocate_id=advocate.id,
>                       is_founding_member=True,
>                       discount_plan="personal_year_5off",
>                       promote_date=advocate.promoted_at,
>                       feedback_score=req.feedback_score)
>     return {"advocate_id": advocate.id}
> ```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `event` | string | ✅ | 固定 `advocate_promoted` |
| `user_id` | string | ✅ | 用户 UUID |
| `session_id` | string | ✅ | 会话 UUID |
| `created_at` | timestamp | ✅ | UTC+8 时间戳 |
| `advocate_id` | string | ✅ | 创始体验官 ID |
| `is_founding_member` | bool | ✅ | 是否创始体验官 (固定 True) |
| `discount_plan` | string | ✅ | 折扣套餐 (personal_year_5off) |
| `promote_date` | timestamp | ✅ | 晋升时间 |
| `feedback_score` | decimal | ⛔ | Day 30 反馈评分 (1-5) |

**漏斗角色**: 5 步漏斗 step 5, 律师晋升为创始体验官, 享 5 折 + 终身客服 + 投票权
**目标**: 公测期 30 天累计 80 创史 (首批 20 已发 + 试用 120 × 50% 创史转化率)

---

## 2. 4 指标定义 (W10 B1 公测期业务漏斗)

> **4 指标 = 公测期 30 天核心业务指标**, 对应 PRD § 10.2.1.1 + § 11.2
> **数据源**: 5 事件 (landing_viewed / invite_redeemed / trial_started / paid_converted / advocate_promoted)
> **更新频率**: 每日 23:00 Mavis 跑数据, BD 23:30 回填

### 2.1 指标 1: 注册转化率 (Registration CVR)

> **定义**: 邀请码兑换 → 试用注册的转化率
> **公式**: `trial_started / invite_redeemed × 100%`
> **目标**: 公测期 ≥ 80% (兑换 150 → 试用 120)

| 维度 | 目标 | 监控节奏 |
|------|------|----------|
| 评审律师 | 100% (5/5 已 redeem L1, 4 待) | 每日 |
| 微信群律师 | 80%+ (8/10) | 每日 |
| 创始体验官 | 90%+ (72/80) | 每日 |
| 公开报名 | 70%+ (42/60) | 每日 |
| **加权** | **≥ 80%** | **每日** |

### 2.2 指标 2: 试用转化率 (Trial Activation CVR)

> **定义**: 公测 landing 访问 → 邀请码兑换的转化率
> **公式**: `invite_redeemed / landing_viewed × 100%`
> **目标**: 公测期 ≥ 15% (访问 1000 → 兑换 150)

| 维度 | 目标 | 监控节奏 |
|------|------|----------|
| 评审律师 | 100% (5/5) | 每日 |
| 微信群律师 | 50%+ (10/20, 朋友圈 + 群内) | 每日 |
| 创始体验官 | 80%+ (80/100, 律协 + 朋友圈) | 每日 |
| 公开报名 | 6%+ (60/1000, 公众号 + 公测 landing) | 每日 |
| **加权** | **≥ 15%** | **每日** |

### 2.3 指标 3: 付费转化率 (Payment CVR)

> **定义**: 试用律师 → 付费律师的转化率
> **公式**: `paid_converted / trial_started × 100%`
> **目标**: 公测期 ≥ 25% (试用 120 → 付费 30)

| 维度 | 目标 | 监控节奏 |
|------|------|----------|
| 评审律师 | 50%+ (5 → 2-3 付费) | 每周 |
| 微信群律师 | 20%+ (8 → 1-2 付费) | 每周 |
| 创始体验官 | 30%+ (72 → 21-22 付费, 5 折激励大) | 每周 |
| 公开报名 | 5%+ (42 → 2 付费) | 每周 |
| **加权** | **≥ 25%** | **每周** |

### 2.4 指标 4: 创史转化率 (Advocate CVR)

> **定义**: 试用律师 → 创始体验官的晋升率
> **公式**: `advocate_promoted / trial_started × 100%`
> **目标**: 公测期 ≥ 60% (试用 120 → 创史 80)

| 维度 | 目标 | 监控节奏 |
|------|------|----------|
| 评审律师 | 100% (5/5 自动晋升, 评审 + 微信群种子) | 每日 |
| 微信群律师 | 60%+ (8 → 5 创史) | 每日 |
| 公开报名 | 50%+ (42 → 21 创史) | 每日 |
| **加权** | **≥ 60%** | **每日** |

### 2.5 4 指标 → 5 事件映射

| 4 指标 | 关联 5 事件 | 计算公式 |
|--------|------------|----------|
| 注册转化率 | invite_redeemed + trial_started | trial_started / invite_redeemed |
| 试用转化率 | landing_viewed + invite_redeemed | invite_redeemed / landing_viewed |
| 付费转化率 | trial_started + paid_converted | paid_converted / trial_started |
| 创史转化率 | trial_started + advocate_promoted | advocate_promoted / trial_started |

### 2.6 4 指标 vs W6 v0.1 4 指标对照表

| W10 B1 (本文) | W6 v0.1 (dashboard-w6.md) | 关系 | 升级原因 |
|---------------|---------------------------|------|----------|
| **注册转化率** | 漏斗 step2 (试用 → 注册) | 重命名 + 简化 | W6 漏斗太复杂 (5 步), W10 简化为业务漏斗 4 指标 |
| **试用转化率** | 漏斗 step1 (访问 → 试用) | 重命名 + 简化 | 同上, 业务口径统一 |
| **付费转化率** | 漏斗 step5 + 4 指标 (付费) | 保留 | W6 已对齐, 命名简化 |
| **创史转化率** | (无, 走创史状态机) | 新增 | 公测期核心业务指标, 80 席剩 80 是核心目标 |
| (无) | WAU (W6 4 指标 #1) | 删除 | 业务漏斗不需要 WAU, WAU 仍在 dashboard-w6 跟踪 |
| (无) | 留存 (W6 4 指标 #3) | 删除 | 业务漏斗不需要留存, 留存仍在 dashboard-w6 跟踪 |

> **总结**: W10 B1 4 指标 = 公测期业务漏斗核心指标, W6 v0.1 4 指标 = 全量跟踪 (WAU + 漏斗 + 留存 + 付费). W10 简化业务指标, W6 保留技术指标.

---

## 3. 公测期 30 天日看板 (W10 B1)

> **更新方式**: 每日 23:00 Mavis 跑数据, BD 23:30 回填
> **数据查询**: 见 § 6 SQL

### 3.1 4 指标日数据 (W10 末 - W12 末, 共 30 天)

| 日期 | landing_viewed | invite_redeemed | trial_started | paid_converted | advocate_promoted | 试用CVR | 注册CVR | 付费CVR | 创史CVR |
|------|----------------|-----------------|---------------|----------------|-------------------|---------|---------|---------|---------|
| 2026-07-26 | (待填) | | | | | | | | |
| 2026-07-27 | | | | | | | | | |
| 2026-07-28 | | | | | | | | | |
| ... | | | | | | | | | |
| 2026-08-23 | | | | | | | | | |
| **累计** | | | | | | | | | |

### 3.2 4 指标周度对比 (4 周 4 行)

| 周次 | 日期范围 | landing | redeemed | trial | paid | advocate | 试用CVR | 注册CVR | 付费CVR | 创史CVR |
|------|----------|---------|----------|-------|------|----------|---------|---------|---------|---------|
| **W10 末 (公测 W0)** | 07-26 - 08-01 | 1000+ | 80+ | 60+ | 0 | 30+ | 8% | 75% | 0% | 50% |
| **W11 (公测 W1)** | 08-02 - 08-08 | 1500+ | 120+ | 100+ | 0 | 50+ | 8% | 83% | 0% | 50% |
| **W11 末 (公测 W2)** | 08-09 - 08-15 | 2000+ | 140+ | 115+ | 5+ | 65+ | 7% | 82% | 4% | 56% |
| **W12 (公测 W3)** | 08-16 - 08-23 | 2500+ | 150+ | 120+ | 30+ | 80 | 6% | 80% | 25% | 67% |
| **目标** | - | **2500+** | **150+** | **120+** | **30+** | **80** | **6%** | **80%** | **25%** | **67%** |

### 3.3 渠道转化对比 (W11 末 BD 出表)

| 渠道 | 邀请数 | landing | redeemed | trial | paid | advocate | 试用CVR | 注册CVR | 付费CVR | 创史CVR |
|------|--------|---------|----------|-------|------|----------|---------|---------|---------|---------|
| **评审律师** (5) | 5 | 5 | 5 | 5 | 2-3 | 5 | 100% | 100% | 50% | 100% |
| **微信群律师** (10) | 10 | 20 | 10 | 8 | 1-2 | 5 | 50% | 80% | 20% | 60% |
| **创始体验官** (100, 80 剩) | 100 | 100 | 80 | 72 | 21-22 | 80 | 80% | 90% | 30% | 100% |
| **律协推荐** (估 100) | 100 | 100 | 80 | 72 | 21-22 | 80 | 80% | 90% | 30% | 100% |
| **公开报名** (估 800+) | 800+ | 800+ | 60 | 42 | 2 | 21 | 7.5% | 70% | 5% | 50% |
| **合计** | **1015+** | **1025+** | **235+** | **199+** | **48-51** | **191+** | **23%** | **85%** | **25%** | **96%** |

> **注**: 评审律师 L1 BETA2025-0001 已 redeem (W7 commit 5437535), 计入 W7 (公测前), W10 B1 启动后 4 位评审律师待 redeem.

---

## 4. 公测期 30 天节奏 (W10 B1)

### 4.1 4 周节奏表

| 周次 | 日期 | 漏斗状态 | 关键动作 | 责任人 |
|------|------|----------|----------|--------|
| **W10 末 (公测 W0)** | 07-26 - 08-01 | step1-3 跑数据 | 公测启动 + 评审律师激活 + 微信群律师启动 + 创史招满 30 | BD + 总指挥 |
| **W11 前半 (公测 W1)** | 08-02 - 08-08 | step3 跟踪 | Day 7 留存观察 + 创史招满 50 + 朋友圈 push | BD + PM |
| **W11 后半 (公测 W2)** | 08-09 - 08-15 | step3-4 | Day 14 反馈 + 中期报告 + 创史招满 65 + 公众号长文 | BD + 总指挥 |
| **W12 前半 (公测 W3)** | 08-16 - 08-22 | step4-5 | Day 23 提醒 (-7 天付费) + 创史正式资格激活 + 客服群 | 系统 + BD |
| **W12 后半 (公测 W4)** | 08-23 - 08-23 | step5 | Day 29/31 付费墙 + 首批 30 付费律师 + 公测报告 | 系统 + BD + PM |

### 4.2 4 个关键节点 (运营重点)

| 节点 | 日期 | 关键动作 | 目标 |
|------|------|----------|------|
| **公测启动** | 07-26 周日 | 评审 #2 收尾 + 启动仪式 + 邮件群发 150 邀请码 | 评审律师全激活 + 微信群 8+ 启动 |
| **Day 7 留存** | 08-02 周日 | 7 日留存观察 + 创史招满 50 + 公众号长文 | 7 日留存 60%+ |
| **Day 14 反馈** | 08-09 周日 | Day 14 反馈 + 中期报告 + 创史招满 65 | 创史 65 席 |
| **Day 30 付费** | 08-23 周日 | Day 30 付费墙触发 + 首批 30 付费律师 + 公测报告 | 30 日付费 30+ |

### 4.3 3 个里程碑 (D-day)

| 里程碑 | 触发条件 | 动作 |
|--------|----------|------|
| **M1: 评审律师 5 全到** | 07-26 启动仪式前, 5/5 评审律师确认 | 致谢 + 评审卡 + 创史候选 + 启动仪式颁奖 |
| **M2: 创史体验官 80 满** | 08-23 周日前, 80/80 创史招满 | 出「创史名单」+ 致谢 + 律协公告 |
| **M3: 首批 30 付费律师** | 08-23 周日前, 30+ 律师转化付费 | 出公测报告 + 给团队 + 给投资人 |

---

## 5. 公测期 4 指标异常处理 (BD + 总指挥)

### 5.1 异常检测 (Mavis 跑日报时)

| 异常 | 触发条件 | 预警级别 | 响应时间 |
|------|----------|----------|----------|
| **试用转化率 < 10%** | 单日 invite_redeemed / landing_viewed < 10% (目标 15%) | 红色 | 12h 内 |
| **注册转化率 < 60%** | 单日 trial_started / invite_redeemed < 60% (目标 80%) | 红色 | 12h 内 |
| **付费转化率 < 15%** | 单日 paid_converted / trial_started < 15% (目标 25%) | 黄色 | 24h 内 |
| **创史转化率 < 40%** | 单日 advocate_promoted / trial_started < 40% (目标 60%) | 黄色 | 24h 内 |
| **邀请码激活停滞** | 单日 invite_redeemed 变化 < 5 (连续 3 天) | 黄色 | 12h 内 |
| **评审律师失约** | 评审会前 1 天 评审律师未确认 | 红色 | 1h 内 |
| **创史招满延迟** | 08-23 创史未招满 60 席 (目标 80) | 黄色 | 24h 内 |

### 5.2 异常处理流程

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

### 5.3 5 个高风险场景 (预案)

| 场景 | 触发 | 应对 |
|------|------|------|
| **场景 1: 公测启动日 (7/26) redeem < 30** | 当日 invite_redeemed < 30 | 朋友圈追加 1 条限时福利, 评审律师朋友圈帮转 |
| **场景 2: Day 7 留存 < 40%** | W11 末 trial_started / invite_redeemed < 40% | 紧急修复 onboarding (lex-coder P0), BD 1v1 微信回访激活律师 |
| **场景 3: 创史体验官招满 80 但激活 < 50%** | W12 末 advocate_promoted / invite_redeemed < 50% | 创史正式资格延后到反馈, 加强客服群 (BD 1v1) |
| **场景 4: Day 30 付费转化 < 15%** | W12 末 paid_converted / trial_started < 15% | 调整定价 (W13 折上折), 延后公测期 (8/30 截止) |
| **场景 5: 律协不批 80 席位** | 07-12 - 07-20 无批复 | 降级「律协背书 + 自营 50 创史」, W11 律协沙龙补足 |

---

## 6. 公测期 4 指标 SQL (Mavis 跑日报用)

### 6.1 试用转化率 (landing_viewed → invite_redeemed)

```sql
SELECT
  DATE(t1.created_at) AS day,
  COUNT(DISTINCT t1.user_id) AS landing_viewed,
  COUNT(DISTINCT t2.user_id) AS invite_redeemed,
  ROUND(COUNT(DISTINCT t2.user_id) * 100.0 / COUNT(DISTINCT t1.user_id), 1) AS trial_cvr_pct
FROM tracking_events t1
LEFT JOIN tracking_events t2 ON t1.user_id = t2.user_id
  AND t2.event = 'invite_redeemed'
  AND t2.created_at >= t1.created_at
WHERE t1.event = 'landing_viewed'
  AND t1.created_at >= '2026-07-26'
GROUP BY DATE(t1.created_at)
ORDER BY day;
```

### 6.2 注册转化率 (invite_redeemed → trial_started)

```sql
SELECT
  DATE(t2.created_at) AS day,
  COUNT(DISTINCT t2.user_id) AS invite_redeemed,
  COUNT(DISTINCT t3.user_id) AS trial_started,
  ROUND(COUNT(DISTINCT t3.user_id) * 100.0 / COUNT(DISTINCT t2.user_id), 1) AS reg_cvr_pct
FROM tracking_events t2
LEFT JOIN tracking_events t3 ON t2.user_id = t3.user_id
  AND t3.event = 'trial_started'
  AND t3.created_at >= t2.created_at
WHERE t2.event = 'invite_redeemed'
  AND t2.created_at >= '2026-07-26'
GROUP BY DATE(t2.created_at)
ORDER BY day;
```

### 6.3 付费转化率 (trial_started → paid_converted)

```sql
SELECT
  DATE(t3.created_at) AS month,
  COUNT(DISTINCT t3.user_id) AS total_trial,
  COUNT(DISTINCT t4.user_id) AS paid_converted,
  ROUND(COUNT(DISTINCT t4.user_id) * 100.0 / COUNT(DISTINCT t3.user_id), 1) AS paid_cvr_pct
FROM tracking_events t3
LEFT JOIN tracking_events t4 ON t3.user_id = t4.user_id
  AND t4.event = 'paid_converted'
  AND t4.created_at >= t3.created_at
WHERE t3.event = 'trial_started'
  AND t3.created_at >= '2026-07-26'
GROUP BY DATE_TRUNC('month', t3.created_at)
ORDER BY month;
```

### 6.4 创史转化率 (trial_started → advocate_promoted)

```sql
SELECT
  DATE(t3.created_at) AS day,
  COUNT(DISTINCT t3.user_id) AS trial_started,
  COUNT(DISTINCT t5.user_id) AS advocate_promoted,
  ROUND(COUNT(DISTINCT t5.user_id) * 100.0 / COUNT(DISTINCT t3.user_id), 1) AS advocate_cvr_pct
FROM tracking_events t3
LEFT JOIN tracking_events t5 ON t3.user_id = t5.user_id
  AND t5.event = 'advocate_promoted'
  AND t5.created_at >= t3.created_at
WHERE t3.event = 'trial_started'
  AND t3.created_at >= '2026-07-26'
GROUP BY DATE(t3.created_at)
ORDER BY day;
```

---

## 7. 公测期 BD 每日动作 (W10 B1)

| 时间 | 动作 | 频率 | 责任人 |
|------|------|------|--------|
| **09:00** | 查 dashboard-w6.md 4 指标 (昨日) | 每天 | BD |
| **09:30** | 异常预警响应 (见 § 5.1) | 每天 | BD + 总指挥 |
| **10:00** | 监控邀请码状态 (status: unused → redeemed → active) | 每天 | BD |
| **10:30** | 律师群发反馈 (1 条朋友圈 / 1 条群内, 不刷屏) | 每天 | 总指挥 |
| **12:00** | 评审律师 1v1 微信回访 (1-2 位/天) | 每天 | 总指挥 |
| **15:00** | 创史意向跟进 (新入申请 5-10 位/天) | 每天 | BD |
| **18:00** | 律师 1v1 答疑 (微信咨询) | 每天 | BD + 总指挥 |
| **21:00** | 朋友圈 / 公众号内容发布 (1 条) | 每天 | 总指挥 + BD |
| **23:00** | Mavis 跑日报 (4 指标 + 邀请码状态) | 每天 | Mavis |
| **23:30** | BD 回填 dashboard-w6.md § 2.1 + launch-funnel.md § 3.1 | 每天 | BD |

---

## 8. 公测期 W10 B1 与 PRD § 10.2.1 对齐

### 8.1 4 指标对齐

| W10 B1 (本文) | PRD § 10.2.1 (v0.7.2) | 关系 |
|---------------|------------------------|------|
| **注册转化率** (80%+) | § 10.2.1.1 step 3 注册表单提交 60%+ | 升级 (注册 = 试用) |
| **试用转化率** (15%+) | § 10.2.1.1 step 2 点击 CTA 40%+ + step 1 访问 100% | 合并简化 |
| **付费转化率** (25%+) | § 10.2.1.1 step 7 Day 30 转化 30%+ (激活律师) | 升级 (试用 → 付费 25%) |
| **创史转化率** (60%+) | § 11.2.1.7 创始体验官通过 → 付费率 80%+ | 新增 (试用 → 创史 60%) |

### 8.2 5 事件对齐

| W10 B1 (本文) | PRD § 10.2.1 (v0.7.2) | 关系 |
|---------------|------------------------|------|
| `landing_viewed` | `trial_landing_pv` (W6 埋点) | 重命名 + 扩展 |
| `invite_redeemed` | (无, W6 走 invite 状态机) | 新增 (业务漏斗) |
| `trial_started` | `trial_register_submit` (W6 埋点) | 重命名 |
| `paid_converted` | `payment_success` (W6 走 Stripe webhook) | 提升为 5 事件 |
| `advocate_promoted` | (无, W6 走创史状态机) | 新增 (业务漏斗) |

---

## 9. 验收标准 (W10 B1)

- [x] 5 事件定义 (landing_viewed / invite_redeemed / trial_started / paid_converted / advocate_promoted) — § 1
- [x] 4 指标定义 (注册转化率 / 试用转化率 / 付费转化率 / 创史转化率) — § 2
- [x] 公测期 30 天日看板 (4 周 4 行 + 4 指标 4 列) — § 3
- [x] 公测期 30 天节奏表 + 4 关键节点 + 3 里程碑 — § 4
- [x] 4 指标异常处理 SOP (7 个异常 + 5 个高风险场景) — § 5
- [x] 4 指标 SQL (Mavis 跑日报用) — § 6
- [x] 公测期 BD 每日动作清单 — § 7
- [x] 跟 PRD § 10.2.1 对齐 (4 指标 + 5 事件) — § 8

> **整理人**: lex-bd (BD/运营) · 数据来源: Mavis 跑 SQL (W10 末接入数据库后) · 文档版本: v2.0 (06-29)