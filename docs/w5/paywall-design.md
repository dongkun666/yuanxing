<!-- LexPrime Track D · W5 Day 4 交付 -->
# 付费墙设计 (Paywall Design)

> **版本**: v1.0 · 2026-06-29
> **Track**: D (30 天试用 + 个人版 ¥99/月 + 付费墙)
> **Week**: W5 Day 4
> **状态**: PM 设计稿, 等 W6 coder 接入
> **配套**: `trial-registration-flow.md` · `onboarding-flow.md` · `beta-invitation.md`

---

## 0. 文档使用说明

- 本文档面向 **PM + lex-coder + lex-bd**: PM 定规则 + 文案 + 触发逻辑, coder 落代码 + 弹窗, BD 答疑
- 付费墙的**核心原则**: **不强制, 不黑屏, 给替代方案** — 律师群体对"付费墙"反感, 任何"必须付费才能用"的设计都会流失
- 锁定策略: 试用期内全开放 → 试用期结束后**只锁高级 Skill**, **基础 Skill 永远免费** (类案 + 文书)
- 数据沉淀: 律师试用期内的案件 / 客户 / 文书数据**永久保留**, 不删数据
- 跟 §11 PRD 法务自检一致: 数据本地化 + AI 辅助 + 不替代律师

---

## 1. 付费墙目标

### 1.1 一句话定位

> **试用期内让律师充分体验全部 Skill, 试用期结束后用「高级 Skill 锁定 + 基础功能永久免费」引导付费, 而不是「黑屏必须付费用」。**

### 1.2 关键设计原则

| 原则 | 体现 | 反例 |
|------|------|------|
| **基础永远免费** | 类案 + 文书 永久开放 | 不要「试用期外全锁」 |
| **不黑屏** | 工作台永远可进, 高级 Skill 单独锁定 | 不要「Day 31 全屏锁」 |
| **数据保留** | 律师案件 / 客户 / 文书 永久保留 | 不要「删数据逼付费」 |
| **3 渠道触达** | 站内通知 + 邮件 + 微信公众号 | 不要「只发邮件」 |
| **替代方案** | 给创始体验官 5 折 / 学生免费 / 公益援助 | 不要「只有付费用 / 离开」 |
| **不骚扰** | Day 23 / 29 / 31 三段提醒, 中间静默 | 不要「每天弹窗」 |

---

## 2. Skill 分级 (免费 vs 锁定)

### 2.1 免费 Skill (永久开放, 试用期内不限次数)

| Skill | 试用期内 | 试用期后 | 限制 |
|-------|----------|----------|------|
| **Skill 1 类案检索** | ✅ 不限 | ✅ 仍开放 | 20 次/月 (新增限制) |
| **Skill 3 文书生成** (基础) | ✅ 不限 | ✅ 仍开放 | 100 次/月 (新增限制) |
| **案件 / 客户 / 日程 / 模板** | ✅ 完整功能 | ✅ 完整功能 | 不限 |
| **本地知识库** | ✅ 完整 | ✅ 完整 | 不限 |
| **数据导出** | ✅ 完整 | ✅ 完整 | 不限 |

> **关键**: 基础 Skill 试用期外仍开放, 但**增加次数限制**. 这是律师付费心理转化的关键 — 律师发现"快超了, 升个级吧".

### 2.2 高级 Skill (试用期外锁定, 付费解锁)

| Skill | 试用期内 | 试用期后 (个人基础版) | 试用期后 (个人专业版) |
|-------|----------|----------------------|----------------------|
| **Skill 2 合同审查** (高级版) | ✅ 不限 | 🔒 锁定 (可预览, 不能保存) | ✅ 20 次/月 |
| **Skill 3 文书生成** (高级版) | ✅ 不限 | 🔒 锁定 | ✅ 无限 |
| **Skill 4 庭审准备** (Skill 4) | ✅ 50 次/月 | 🔒 锁定 | ✅ 50 次/月 |
| **批量合同审查** (Skill 2 高级) | ✅ 20 次/月 | 🔒 锁定 | ✅ 20 次/月 |

> **关键**: 高级 Skill 试用期内**全开放**, 这是让律师形成依赖的关键. 试用期外按订阅版本解锁.

### 2.3 资源限制 (试用期外)

| 资源 | 试用期内 | 试用期后 (基础) | 试用期后 (专业) |
|------|----------|----------------|----------------|
| 存储 | 5 GB | 500 MB | 20 GB |
| AI 调用 | 1000 次/月 | 200 次/月 | 5000 次/月 |
| 多端同步 | ✅ | ✅ | ✅ |
| 客户支持 | 邮件 48h | 邮件 48h | 优先客服 4h |

---

## 3. 触发节点 + 3 渠道触达

### 3.1 三段提醒节奏

| 时间 | 触发条件 | 渠道 | 内容 | 触发动作 |
|------|----------|------|------|----------|
| **Day 23** (-7 天) | trial_days_left == 7 | 站内通知 + 邮件 | "您的 30 天试用还剩 7 天, 升级个人版 ¥99/月 立享 8 折首年" | 无 (静默提醒) |
| **Day 29** (-1 天) | trial_days_left == 1 | 站内通知 + 邮件 + 微信公众号 (W6 接入) | "明天是试用最后一天, 锁定核心功能前升级仅 ¥99/月" | 无 |
| **Day 31** (+1 天) | trial_status → expired | 站内通知 + 邮件 | "您的试用期已结束, 高级 Skill 已锁定. 升级个人版 ¥99/月, 立即解锁" | 高级 Skill 锁定 |

### 3.2 触达内容模板 (跟设计系统一致)

**站内通知 (Dock 顶部条 / 工作台顶部条)**:
```
[品牌色 brand] ⚡ 您的 30 天试用还剩 7 天. 升级个人版 ¥99/月, 锁定高级 Skill 不中断. 
              [立即升级]  [稍后再说]
```

**邮件主题**: 「LexPrime · 您的 30 天试用还剩 X 天」
**邮件正文**: 跟 trial-registration-flow.md §4.3 一致

**微信公众号 (W6 接入)**: 模板消息, 跟邮件内容一致, 但加 1 个跳转按钮

### 3.3 不刷屏原则

- Day 23 / 29 / 31 是**硬规则**, 中间不打扰律师
- 不弹窗, 不强制, 不锁工作台
- 律师可以随时点工作台顶部条 [稍后再说] 关闭本次提醒, 下次提醒照样触发
- 律师可以"关闭试用提醒" (永久关闭), 但默认开启

---

## 4. 锁定后的 UI 设计

### 4.1 工作台顶部条 (Trial Status Bar)

**试用期内 (Day 1-30)**:
```
[品牌色 bg-brand-tint3] 📅 试用中 · 还剩 23 天  [升级个人版 →]
```
- 颜色: brand-tint3 (浅蓝), 不打扰
- 点击 [升级] 跳转 `/pricing`

**试用到期 (Day 31+)**:
```
[urgent 色 bg-urgent-tint] ⚠ 高级 Skill 已锁定 · 基础功能永久免费  [查看套餐]  [稍后再说]
```
- 颜色: urgent-tint (浅橙), 提示但不刺眼
- 点击 [查看套餐] 跳转 `/pricing`
- 点击 [稍后再说] 关闭本次, 不再显示 (下次主动回访工作台再显示)

**已付费**:
```
不显示 trial bar (避免付费用户被骚扰)
```

### 4.2 高级 Skill 锁定 UI (Skill 2 / 3 高级版 / 4)

**当律师点击被锁定的高级 Skill 时**:
```
+----------------------------------+
|                                  |
|   [大锁图标 + 模糊背景预览]        |
|                                  |
|   🔒 庭审准备 (Skill 4)          |
|   已锁定 · 升级解锁               |
|                                  |
|   ✨ 个人专业版包含 50 次/月       |
|   ✨ 团队协作 + 共享知识库         |
|   ✨ 4h 优先客服                  |
|                                  |
|   [ 立即升级 - ¥199/月 ]          |
|   [ 查看所有套餐 ]                |
|                                  |
+----------------------------------+
```

**关键设计**:
- 模糊背景预览 (从真实 Skill 截 1 张图, CSS blur), 让律师看到"它长什么样"
- 不弹 modal 拦截 (避免律师烦躁)
- 替代方案: 提供「预览版」让律师看 1-2 行 AI 输出 (30 字内), 引起兴趣
- CTA 主色: brand 立即升级; 次色: text-fg-secondary 查看套餐

### 4.3 升级后对比 (Before / After)

**升级前 (基础版, 试用到期)**:
```
案件: 12 个 (新建不限制, 但 AI 调用 200 次/月)
类案检索: 20 次/月
AI 文书: 100 次/月
高级 Skill: 🔒 锁定
存储: 500 MB
```
**升级后 (专业版)**:
```
案件: 不限制
类案检索: 不限制
AI 文书: 不限制
高级 Skill: ✅ 全部解锁
存储: 20 GB
```
**对比价值点**: 让律师直观看到"我升级后能用更多", 而不是"我必须付费"

---

## 5. 替代方案 (不止「付费用」)

### 5.1 4 个替代方案 (按优先级)

| 替代方案 | 适用律师 | 触发位置 | 价值 |
|----------|----------|----------|------|
| **1. 创始体验官申请** | 执业 5+ 年 | 付费墙弹窗 + 个人中心 | 5 折购买 1 年个人版 (¥449), 享终身优先客服 |
| **2. 学生律师免费** | 法学在读 / 实习律师 | 注册时勾选 "我是学生" | 1 年免费专业版 (需学校邮箱验证) |
| **3. 公益法律援助** | 公益律师 / 法援中心 | 客服申请 | 永久免费 (审批制, 需提供工作证明) |
| **4. 数据导出 + 离开** | 决定离开的律师 | 个人中心 "导出我的数据" | 30 天数据保留期, 律师随时离开 |

### 5.2 设计要点

- **不强迫付费**: 4 个替代方案都摆在付费墙弹窗, 让律师有选择
- **不道德绑架**: "创始体验官" 不是"不付费就被鄙视", 而是"您执业 5+ 年值得 5 折"
- **公益通道保密**: 公益律师往往不希望公开身份, 走客服 1v1 申请, 不公开名单

---

## 6. 付费墙 API 契约 (PM 设计, coder 落)

### 6.1 `GET /api/trial/paywall`

**请求**: Header `Authorization: Bearer <access_token>`

**响应 (200)**:
```json
{
  "is_paywall_active": true,            // 当前是否触发付费墙
  "trial_status": "expired",            // 'active' / 'expired' / 'converted'
  "trial_days_left": -5,                // 负数 = 已过 N 天
  "locked_skills": [                     // 锁定的 Skill 列表
    {
      "skill_id": "trial_prep",
      "skill_name": "庭审准备",
      "preview_available": true,         // 是否有预览版
      "upgrade_plan": "professional"     // 解锁需要的套餐
    },
    {
      "skill_id": "batch_review",
      "skill_name": "批量合同审查",
      "preview_available": false,
      "upgrade_plan": "professional"
    }
  ],
  "current_limits": {
    "skill_1_calls_per_month": 20,       // 类案检索 20 次/月
    "skill_3_calls_per_month": 100,      // AI 文书 100 次/月
    "ai_calls_per_month": 200,
    "storage_gb": 0.5
  },
  "upgrade_options": [
    {
      "plan_id": "basic",
      "plan_name": "个人基础版",
      "monthly_price": 99,
      "yearly_price": 899,
      "yearly_discount_pct": 20,
      "url": "/pricing?plan=basic"
    },
    {
      "plan_id": "pro",
      "plan_name": "个人专业版",
      "monthly_price": 199,
      "yearly_price": 1910,
      "yearly_discount_pct": 20,
      "recommended": true,
      "url": "/pricing?plan=pro"
    }
  ],
  "alternative_offers": [
    {
      "offer_id": "founder",
      "title": "申请创始体验官 (5 折 + 终身优先客服)",
      "url": "/founder-apply"
    },
    {
      "offer_id": "student",
      "title": "学生律师免费 (需学校邮箱验证)",
      "url": "/student-verify"
    },
    {
      "offer_id": "public_interest",
      "title": "公益法律援助 (审批制)",
      "url": "/contact"
    },
    {
      "offer_id": "export_data",
      "title": "导出我的数据 (30 天保留)",
      "url": "/account/export"
    }
  ]
}
```

### 6.2 `POST /api/trial/dismiss-reminder`

律师点击 [稍后再说] 时调用, 不再显示当前 trial bar, 但下次提醒照样触发 (Day 23 → 29 → 31 三段).

```json
// 请求
{ "dismissed_until": "2026-07-08T00:00:00+08:00" }   // 7 天内不再显示

// 响应
{ "success": true, "next_show_at": "2026-07-08T00:00:00+08:00" }
```

### 6.3 `POST /api/trial/disable-reminders` (永久关闭)

律师可永久关闭试用提醒 (但律师不会主动用, 主要是给「反复提醒」律师的逃生通道).

```json
// 请求
{ "disabled": true }

// 响应
{ "success": true, "reminders_disabled": true }
```

---

## 7. 数据库 Schema (PM 设计, coder 落)

### 7.1 `trial_reminders` 表 (新增)

```sql
CREATE TABLE trial_reminders (
  reminder_id VARCHAR(50) PRIMARY KEY,
  user_id VARCHAR(50) NOT NULL,

  reminder_type VARCHAR(20) NOT NULL,    -- 'd7' / 'd1' / 'd_plus_1'
  channel VARCHAR(20) NOT NULL,           -- 'in_app' / 'email' / 'wechat'
  sent_at TIMESTAMP NOT NULL,

  status VARCHAR(20) NOT NULL,            -- 'sent' / 'dismissed' / 'clicked'
  clicked_at TIMESTAMP,
  converted_at TIMESTAMP,                -- 律师在 7 天内升级 = 转化

  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_reminders_user_type ON trial_reminders(user_id, reminder_type);
```

### 7.2 `paywall_events` 表 (新增)

```sql
CREATE TABLE paywall_events (
  event_id VARCHAR(50) PRIMARY KEY,
  user_id VARCHAR(50) NOT NULL,

  event_type VARCHAR(50) NOT NULL,
  -- 'shown' / 'clicked_upgrade' / 'clicked_alternative' / 'dismissed' / 'converted'

  event_at TIMESTAMP NOT NULL,
  trigger_skill_id VARCHAR(50),           -- 触发的 Skill ID (e.g. 'trial_prep')
  alternative_id VARCHAR(50),             -- 选择的替代方案 (e.g. 'founder')

  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_paywall_user_type_at ON paywall_events(user_id, event_type, event_at);
```

---

## 8. 转化漏斗埋点 (PM 关键设计)

### 8.1 付费墙漏斗

```
[Day 31 触发付费墙]           paywall_shown          100%   基线
      ↓
[查看替代方案]                paywall_alternative_view  30%   (替代方案吸引力)
      ↓
[点击「立即升级」]           paywall_upgrade_click     25%
      ↓
[进入 /pricing 页面]         pricing_view              95%
      ↓
[选择套餐 + 跳转支付]        payment_init              70%
      ↓
[支付成功]                   payment_success           85%
      ↓
[转化为付费]                 trial_converted           60%
```

### 8.2 关键埋点事件

| 事件名 | 触发时机 | 关键字段 |
|--------|----------|----------|
| `paywall_shown` | Day 31 工作台顶部条出现 / 高级 Skill 锁定弹窗 | trigger_type, skill_id |
| `paywall_upgrade_click` | 点击 [立即升级] | trigger_skill_id |
| `paywall_alternative_click` | 点击替代方案 | alternative_id (founder/student/...) |
| `paywall_dismissed` | 点击 [稍后再说] | dismiss_duration_days |
| `paywall_re_shown` | 7 天后再次显示 | days_since_last |
| `pricing_view` | 进入 `/pricing` 页 | utm_source |
| `payment_init` | 进入支付页 | plan_type |
| `payment_success` | Stripe 回调成功 | plan_type, amount |
| `trial_converted` | trial_status → converted | trial_days_used, plan_type |

---

## 9. UI 设计要点 (跟 W1 设计系统一致)

### 9.1 颜色映射

| 状态 | 颜色 | Token | 用途 |
|------|------|-------|------|
| 试用期内 | 浅蓝 | `bg-brand-tint3` | 顶部条 (不打扰) |
| 试用到期 (Day 31+) | 浅橙 | `bg-urgent-tint` | 顶部条 (提示但不刺眼) |
| 高级 Skill 锁定 | 主色 | `bg-brand` | 弹窗主 CTA |
| 替代方案 | 浅灰 | `bg-bg-subtle` | 弱化展示 |
| 紧迫感 (Day 29) | 红 | `bg-danger-tint` | 倒计时 1 天 |

### 9.2 文案规范

| ❌ 禁用 | ✅ 推荐 |
|---------|---------|
| "您必须升级才能继续使用" | "高级 Skill 已锁定, 升级解锁" |
| "立即购买, 限时 7 折" | "升级个人版 ¥99/月, 锁定高级 Skill" |
| "试用期已结束, 请付费" | "您的试用期已结束, 基础功能永久免费" |
| "离开 LexPrime" | "导出我的数据 (30 天保留)" |
| "AI 自动办案更高效" | "AI 辅助您办案" |

### 9.3 不弹窗原则

- **付费墙弹窗**只在律师**主动点击被锁定的高级 Skill** 时才出现
- **不主动拦截律师**进入工作台 / 基础 Skill
- **顶部条**是软提示, 律师可随时 [稍后再说] 关闭

---

## 10. 法务 & 合规自检

### 10.1 用户协议 + 隐私政策

- 注册时勾选《用户协议》+《隐私政策》(W6 起草完整版)
- 付费墙弹窗加 1 行: "升级即表示同意《订阅协议》, 您可随时取消"

### 10.2 退款政策 (W6 起草)

- 月付: 随时取消, 当月不退
- 年付: 30 天内全额退款, 之后按月折算
- 取消后数据保留 90 天可下载期
- 退款走 Stripe 客服, 1-3 个工作日到账

### 10.3 数据导出权利

- 任何时候律师可导出自己的数据 (案件 / 客户 / 文书 / Wiki)
- 导出格式: Markdown / PDF / Word
- 取消订阅后保留 90 天
- 90 天后律师可申请延期 (一次性, 30 天)

---

## 11. 验收标准 (W5 Day 4)

### 11.1 Day 4 单点验收

- [x] Skill 分级设计完成 (§2)
- [x] 触发节点 + 3 渠道触达设计完成 (§3)
- [x] 锁定 UI 设计完成 (§4)
- [x] 替代方案设计完成 (§5)
- [x] API 契约 + DB schema 设计完成 (§6 §7)
- [x] 转化漏斗埋点完成 (§8)

### 11.2 W6 coder 接入验收

- [ ] 顶部 Trial Status Bar 组件
- [ ] 高级 Skill 锁定弹窗
- [ ] 4 个替代方案入口
- [ ] Day 23/29/31 定时提醒 (后台 cron)
- [ ] 微信模板消息接入 (W6 公众号上线后)
- [ ] 付费墙漏斗埋点

### 11.3 W7 末验证

- [ ] 实测 Day 23 提醒触达率 ≥ 95%
- [ ] 实测 Day 31 触发付费墙的律师, 30% 选择替代方案
- [ ] 实测付费墙 → 升级转化率 ≥ 15%
- [ ] 实测 [稍后再说] 律师 7 天后再触达率 ≥ 60%

---

## 12. 风险与应对

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| 律师感到被骚扰 (3 段提醒太多) | 中 | 中 | Day 23 默认提醒, Day 29 / 31 律师可手动关闭 |
| 锁定弹窗过于频繁 | 中 | 中 | 每个锁定 Skill 7 天内最多弹 1 次 |
| 律师直接离开 (LTV = 0) | 中 | 高 | 数据导出通道 + 邮件召回 (W8 / W12) |
| 高级律师不愿付费 (嫌功能少) | 低 | 中 | 公测邀请函定向给单飞 / 小所, 高级律师走 Track E 评审 + 企业版 |
| 替代方案被滥用 (学生免费通道) | 低 | 低 | 学校邮箱验证 + 学年限制 (1 年免费) |
| Stripe 接入延迟 (W7) | 中 | 中 | 备用: 微信支付 / 支付宝 (Phase 4.5) |

---

## 13. 整理人备注 (PM)

- 付费墙是 **PM 商业逻辑**的核心体现: 试用期外**不黑屏, 基础功能永久免费**, 这是 LexPrime 跟竞品的最大差异化
- 替代方案 4 个 (创始体验官 / 学生免费 / 公益援助 / 数据导出) 体现**律师行业特殊性**, 不照搬 SaaS 通用付费墙
- W6 coder 落库时, 注意 **trial_status → expired** 的状态机转换不能太早 (Day 30 23:59 才转, 不要 Day 30 00:00 误转)
- W7 末接 Stripe 后, 在 §6.1 响应补充 `subscription_id` `next_billing_at` 字段
- W12 末出 **付费墙转化漏斗报告**, 给团队 + 投资人 + 创始体验官候选名单

> **PM 责任**: W5 文档交付, W6 跟踪 coder 实现, W7 末实测付费墙转化漏斗, W12 出报告.