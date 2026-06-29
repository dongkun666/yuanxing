<!-- LexPrime Track D · W5 Day 1 交付 -->
# 试用注册流程设计 (Trial Registration Flow)

> **版本**: v1.0 · 2026-06-29
> **Track**: D (30 天免费试用 + Stripe 接入)
> **Week**: W5 Day 1
> **状态**: PM 设计稿, 等 W6 lex-coder 接入实现
> **配套**: `paywall-design.md` (Day 4) · `onboarding-flow.md` (Day 3) · `beta-invitation.md` (Day 3)

---

## 0. 文档使用说明

- 本文档面向 **PM + lex-coder + lex-bd**: PM 用来对齐产品逻辑 + 用户体验, coder 用来落地 API + UI, BD 用来给律师答疑
- W5 Day 1 交付, 不包括 Stripe 接入 (Stripe 在 W7); Day 1 只交付 **试用开通逻辑 + UI**
- 数据契约 (DB schema + 接口字段) 见 §6, coder 落库时按此对
- W5 Day 4 付费墙规则见 `paywall-design.md`, 本文档 §7 只列触发节点, 详细锁定策略不在本文档

---

## 1. 试用目标

### 1.1 一句话定位

> **30 天全功能免费试用, 无信用卡, 注册即用**——让律师 0 摩擦体验 LexPrime 全部 4 大 Skill (类案 / 合同 / 文书 / 庭审), 30 天后凭价值感付费, 而不是被营销页说服付费.

### 1.2 设计原则

| 原则 | 体现 | 反例 |
|------|------|------|
| **0 摩擦注册** | 邮箱/手机号 + 验证码 30s 内完成 | 不要执业证 OCR (W3 已闭环, 但不是试用前置) |
| **无信用卡** | 试用期不收集支付信息 | 不要绑卡才能试用 |
| **全部 Skill 开放** | 类案 + 合同 + 文书 + 庭审 试用期内不锁 | 不要「试用只能看不能跑」 |
| **时间透明** | 工作台顶部 + 个人中心 实时倒计时 | 不要「到期才告知」 |
| **升级不强制** | 试用结束不锁账号, 仅锁定高级 Skill | 不要「黑屏, 必须付费用」 |

### 1.3 试用期内 vs 试用期外 (核心区别)

| 维度 | 试用期内 (0-30 天) | 试用期结束 (Day 31+) |
|------|---------------------|----------------------|
| 基础 Skill | ✅ 全部开放 | ✅ 仍开放 (类案 + 文书) |
| 高级 Skill | ✅ 全部开放 | 🔒 锁定 (庭审准备 + 批量合同) |
| 案件数 | 不限 | 不限 (不限制客户) |
| 存储 | 5 GB | 500 MB |
| AI 调用 | 1000 次/月 | 200 次/月 |
| 多端同步 | ✅ | ✅ |
| 数据导出 | ✅ | ✅ (Markdown / PDF) |
| 客服支持 | 邮件 (48h) | 邮件 (48h) |

> **关键**: 试用期结束 **不删数据, 不黑屏**, 律师可以继续免费用基础功能, 但高级 Skill (庭审/批量) 锁住, 引导升级.

---

## 2. 注册流程 (3 步法)

### 2.1 流程总览

```
[落地页] → [注册页] → [邮箱验证] → [首次登录] → [Onboarding 引导] → [工作台]
   ↓           ↓            ↓              ↓              ↓              ↓
 landing     /register    邮箱/手机      /welcome       5 步引导      trial_started
 .html       表单         6 位验证码      欢迎页         可跳过        (开始 30 天倒计时)
```

### 2.2 步骤 1: 落地页点击「免费试用 30 天」

**触发场景**:
- 律师从 landing.html `#trial` CTA 进入
- 律师从微信公测邀请函 (beta-invitation.md) 的专属链接进入
- 律师从老用户推荐链接进入 (referral_code 埋点)
- 律师从律协沙龙活动现场扫码进入

**URL 设计**:
```
https://yuanxing.app/register?trial=1&utm_source={source}&ref={code}
```

**关键字段**:
- `trial=1`: 标记试用注册入口 (vs 已注册用户的「续费」入口)
- `utm_source`: 渠道标记 (wechat / email / qr / referral)
- `ref`: 推荐码 (W6 设计推荐奖励计划, W5 仅埋点)

### 2.3 步骤 2: 注册表单 (3 字段)

**设计原则**: 3 字段就够了, **不要超过 4 个**

| # | 字段 | 类型 | 必填 | 校验 |
|---|------|------|------|------|
| 1 | 姓名 | text | ✅ | 2-20 字 (中文/英文) |
| 2 | 邮箱 | email | ✅ | RFC 5322 + 唯一性 |
| 3 | 验证码 | text | ✅ | 6 位数字, 5 分钟有效 |
| 4 | (可选) 律所 | text | ⛔ | W8 后启用 |

> **不要的字段**: 律师执业证号 / 身份证号 / 手机号 (W5 不强制, W6 可选手机号做 TOTP 二次验证)

**UI 布局** (跟 W1 设计系统一致, 居中卡片 + 紫色 AI 角标):
- 顶部: Logo + "LexPrime 元枢法智" + 副标题 "律师的第二大脑"
- 中部: 3 字段表单 + "获取验证码" 按钮 (60s 倒计时)
- 底部: 协议勾选 (《用户协议》+ 《隐私政策》, 必须勾选才能注册)
- CTA: "立即注册, 30 天免费试用" (主色按钮)

### 2.4 步骤 3: 邮箱验证

**触发**: 注册表单提交后, 后端发送 6 位验证码到邮箱

**UI**:
- 顶部提示: "验证码已发送至 xxx@lawfirm.com, 请在 5 分钟内输入"
- 中部: 6 个独立输入框 (每个 1 位, 自动跳下一位)
- 底部: "没收到? 60s 后重发" + "换一种方式注册 (微信扫码, W6 接入)"

**后端逻辑**:
- 验证码错误: 提示「验证码错误或已过期」, 60s 后允许重发
- 验证码错误 5 次: 锁定 10 分钟 (防爆破)
- 验证成功: 创建 user 记录 + trial 记录, 自动登录

### 2.5 注册成功 (auto-login)

- 后端返回: `{ user_id, trial_id, trial_started_at, trial_expires_at, access_token, refresh_token }`
- 前端: 跳转 `/welcome` 首次登录欢迎页
- 同时发送: 欢迎邮件 (含工作台链接 + 5 步引导说明)

---

## 3. 首次登录欢迎页 (`/welcome`)

### 3.1 页面布局 (顶部欢迎 + 底部 CTA)

```
+------------------------------------------------+
|                                                |
|  🎉 欢迎加入 LexPrime 元枢法智!                  |
|                                                |
|  您的 30 天免费试用已开启                        |
|  到期日: 2026-07-29 (还有 30 天)                  |
|                                                |
|  +---------------------------+                |
|  | 1. 上传首个案件  📂       |                |
|  | 2. 跑类案检索    🔍       |                |
|  | 3. 跑合同审查    📑       |                |
|  | 4. 邀请同行      👥       |                |
|  | 5. 关注公众号    📱       |                |
|  +---------------------------+                |
|                                                |
|  [ 开始 5 步引导 → ]   [ 跳过, 进入工作台 ]      |
|                                                |
+------------------------------------------------+
```

### 3.2 设计要点

- **5 步引导的入口**在这里, 不是第一次登录就强制弹窗, 而是给律师选择权 (符合"律师时间宝贵, 不能强制"原则)
- **倒计时**展示, 让律师心理有数
- **跳过按钮**: 律师可以点跳过, 直接进工作台; 后续 7 天内任何时候点工作台右上角的"?"都能重新进引导
- **CTA 主色**: "开始 5 步引导 →" 用主色 brand; "跳过" 用次色 fg-secondary

---

## 4. 试用期管理 (后端逻辑)

### 4.1 试用周期定义

```
trial_started_at = 用户注册成功时刻 (后端服务器时间, UTC+8)
trial_expires_at = trial_started_at + 30 天
trial_status ∈ { active, expired, converted, cancelled }
```

### 4.2 试用状态机

```
            注册成功
              ↓
          [active]
              ↓ (Day 30 24:00 自动)
          [expired] ────→ 升级付费 ────→ [converted]
              ↓                            ↑
          锁定高级 Skill                取消订阅
              ↓                            ↓
        持续基础功能                  [cancelled]
        引导升级 CTA
```

### 4.3 提醒节点 (3 次, 不刷屏)

| 时间 | 渠道 | 内容 |
|------|------|------|
| Day 23 (-7 天) | 站内通知 + 邮件 | "您的 30 天试用还剩 7 天, 升级个人版 ¥99/月 立享 8 折首年" |
| Day 29 (-1 天) | 站内通知 + 邮件 + 微信公众号 | "明天是试用最后一天, 锁定核心功能前升级仅 ¥99/月" |
| Day 31 (+1 天) | 站内通知 + 邮件 | "您的试用期已结束, 高级 Skill 已锁定. 升级个人版 ¥99/月, 立即解锁" |

**不刷屏原则**: Day 23/29/31 这 3 次是硬规则, 中间不打扰; 让律师静默使用.

---

## 5. 试用 API 契约 (PM 设计, coder 落)

### 5.1 `POST /api/trial/start`

**请求体**:
```json
{
  "name": "王律师",
  "email": "wang@lawfirm.com",
  "verify_code": "123456",
  "ref_code": "WANG2026"   // 可选, W6 启用
}
```

**响应 (200)**:
```json
{
  "user_id": "u_abc123",
  "trial_id": "t_xyz789",
  "trial_started_at": "2026-06-29T08:00:00+08:00",
  "trial_expires_at": "2026-07-29T08:00:00+08:00",
  "trial_days_left": 30,
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi..."
}
```

**错误**:
- 400 验证码错误
- 409 邮箱已注册 (提示「该邮箱已注册, 直接登录」)
- 429 1 分钟内请求过多

### 5.2 `GET /api/trial/status`

**请求**: Header `Authorization: Bearer <access_token>`

**响应 (200)**:
```json
{
  "trial_status": "active",
  "trial_started_at": "2026-06-29T08:00:00+08:00",
  "trial_expires_at": "2026-07-29T08:00:00+08:00",
  "trial_days_left": 23,
  "trial_reminder_count": 1,         // 已发送提醒次数 (最多 3)
  "is_locked_skill": {                // 当前是否锁定高级 Skill
    "trial_prep": false,              // 庭审准备 (Skill 4) 试用期内开放
    "batch_review": false             // 批量合同审查 (Skill 2 高级版) 试用期内开放
  },
  "upgrade_url": "/pricing"
}
```

**前端使用**:
- 工作台顶部条 (workstation.html 已有入口)
- 个人中心 trial 状态卡片
- Onboarding step 5 的「升级提示」

### 5.3 `POST /api/trial/cancel` (可选, W6 启用)

律师主动取消试用, 试用期内仍可用至到期日, 到期后锁定.

---

## 6. 数据库 Schema (PM 设计)

### 6.1 `users` 表 (扩展 W3 字段)

```sql
ALTER TABLE users ADD COLUMN
  trial_status VARCHAR(20) DEFAULT 'none' NOT NULL,
  -- 'none' / 'active' / 'expired' / 'converted' / 'cancelled'

  trial_started_at TIMESTAMP,
  trial_expires_at TIMESTAMP,
  trial_reminder_count INT DEFAULT 0,

  -- 来源追踪 (W5 Day 3 公测邀请函用到)
  utm_source VARCHAR(50),
  ref_code VARCHAR(50),
  ref_lawyer_id VARCHAR(50),         -- 推荐人 ID (W6 启用)

  created_via VARCHAR(20) DEFAULT 'web'
  -- 'web' / 'wechat' / 'referral' / 'qr'
;
```

### 6.2 `trial_events` 表 (新增)

```sql
CREATE TABLE trial_events (
  event_id VARCHAR(50) PRIMARY KEY,
  user_id VARCHAR(50) NOT NULL,
  event_type VARCHAR(50) NOT NULL,
  -- 'started' / 'reminder_sent' / 'expired' / 'converted' / 'cancelled' / 'skill_locked'

  event_at TIMESTAMP NOT NULL,
  event_meta JSONB,

  FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX idx_trial_events_user ON trial_events(user_id);
CREATE INDEX idx_trial_events_type_at ON trial_events(event_type, event_at);
```

### 6.3 关键索引

- `users(trial_status)` - 给到期扫描用
- `users(trial_expires_at)` - 给定时任务 (Day 30 转 expired) 用
- `trial_events(event_type, event_at)` - 给转化漏斗分析用

---

## 7. 转化漏斗埋点 (PM 关键设计)

### 7.1 7 步转化漏斗

```
[落地页访问]       landing_pv          100%   基线
      ↓
[点击试用 CTA]    cta_click           ~40%   预期
      ↓
[注册表单提交]    register_submit     ~60%
      ↓
[邮箱验证成功]    verify_success      ~85%
      ↓
[首次登录]        first_login         ~95%
      ↓
[完成 Onboarding ≥ 3 步]   onboarding_3_step    ~50%   (跳过率高)
      ↓
[使用核心 Skill]  skill_use           ~70%
      ↓
[Day 7 留存]      d7_retention        ~60%
      ↓
[Day 30 转化付费] conversion          30%+  (PRD 目标)
```

### 7.2 埋点事件清单

| 事件名 | 触发时机 | 关键字段 |
|--------|----------|----------|
| `trial_landing_pv` | 落地页加载 | utm_source, ref_code |
| `trial_cta_click` | 点击「免费试用 30 天」 | utm_source, ref_code |
| `trial_register_submit` | 注册表单提交 | utm_source, ref_code |
| `trial_verify_success` | 验证码通过 | utm_source |
| `trial_first_login` | 首次登录 | trial_id |
| `trial_onboarding_step` | Onboarding 完成一步 (1-5) | step_no |
| `trial_skill_first_use` | 首次使用某个 Skill | skill_name |
| `trial_d7_active` | Day 7 当天有登录 | trial_days_left |
| `trial_reminder_sent` | 发送到期提醒 | days_before_expire |
| `trial_expired` | 试用期到期 | trial_days_used |
| `trial_converted` | 转化为付费 | plan_type |
| `trial_cancelled` | 主动取消 | reason |

### 7.3 看板 (W12 末给团队 + 投资人)

**Dashboard 链接**: `https://yuanxing.app/admin/trial-funnel` (W6 末实现)

**核心图表**:
1. 7 步漏斗柱状图 (每步转化率)
2. 注册-转化 时长分布 (注册后几天付费)
3. 渠道转化率 (微信 / 邮件 / 推荐 / 落地页)
4. Skill 使用分布 (类案 vs 合同 vs 文书 vs 庭审)
5. Day 7/14/30 留存曲线

---

## 8. UI 详细设计 (跟 W1 设计系统一致)

### 8.1 复用组件 (W1 已有)

- 工作台顶部 trial 状态条: 跟 `workstation.html` 顶部栏保持一致
- 用户区 trial 倒计时: 复用 `workstation.html` 左侧栏底部用户卡片
- 弹窗: 复用 `modals.html` 的标准 modal 样式

### 8.2 新增组件 (W5 Day 1-4)

| 组件 | 位置 | 复用模式 |
|------|------|----------|
| TrialStatusBar | 工作台顶部 | 跟 workstation 顶部栏对齐 |
| WelcomePage | `/welcome` 路由 | 跟 login.html 居中卡片风格一致 |
| TrialExpiredModal | 全屏弹窗 | 跟 modals.html 风格一致, 但更大 |
| UpgradeCTA | 多处入口 | 主色按钮 + 文案 |

### 8.3 视觉规范 (W1 设计 token)

- **主色**: `#165DFF` (brand) - "开始 30 天免费试用" CTA
- **辅色**: `#6C5CE7` (ai) - AI 试用提示角标
- **状态色**:
  - 试用期内: `#00B42A` (success) "试用中 · 还剩 23 天"
  - 试用到期 (7 天内): `#FF7D00` (warning) "试用还剩 7 天, 升级立享 8 折"
  - 已过期: `#FA8C16` (urgent) "高级 Skill 已锁定, 升级解锁"
- **背景**: `#F7F8FA` (bg-subtle) - 注册页背景
- **卡片**: `bg-white rounded-2xl shadow-xl` - 跟 login.html 一致

### 8.4 文案规范

- **不写**: "立即购买" / "限时折扣" / "错过不再有"
- **写**: "30 天免费试用" / "无信用卡" / "随时取消" / "数据可导出"
- **AI 边界**: 不出现 "AI 自动办案" / "替代律师" 等措辞, 一律用 "AI 辅助"
- **律师称呼**: 用「您」不用「你」, 体现专业感

---

## 9. 法务 & 合规自检 (§11 PRD)

### 9.1 个人信息保护

- 邮箱 + 姓名: 注册必须, 加密存储, 用户可见可改可删
- 验证码: 5 分钟过期, 60s 限流 1 次, 不复用
- IP 地址: 注册日志记录 90 天 (合规要求), 之后脱敏
- 隐私政策: 注册前必须勾选, 单独写《隐私政策》v1.0 (W6 起草)

### 9.2 反滥用机制

- 同一邮箱: 只能注册 1 次, 注销后可重新注册 (W6)
- 同一 IP: 1 小时内最多注册 3 次 (防刷)
- 同一设备指纹: 最多注册 5 次 (防恶意)
- 验证码爆破: 5 次错误锁定 10 分钟

### 9.3 退款与争议

- 试用期内: **不收费**, 无退款问题
- 试用期后付费: W6 接 Stripe 后写退款政策 (PRD §11.3 待补)

---

## 10. 验收标准 (W5 Day 1 + 整体 W5)

### 10.1 Day 1 单点验收

- [x] 注册流程文档完整 (本文档)
- [ ] API 契约设计完成 (本文档 §5)
- [ ] DB schema 设计完成 (本文档 §6)
- [ ] UI 视觉规范对齐 W1 设计系统 (本文档 §8)

### 10.2 W5 整体验收 (Day 4 末)

- [ ] 律师可注册 + 30 天免费使用 (Day 1+ 后续 coder 落)
- [ ] 试用期到期前 7/1 天提醒 (Day 4 提醒逻辑)
- [ ] 转化漏斗埋点完整 (Day 1 埋点清单已出)
- [ ] 付费墙设计就位 (见 paywall-design.md)
- [ ] 定价页就位 (见 templates/views/pricing.html)
- [ ] Onboarding 就位 (见 onboarding-flow.md)
- [ ] 公测邀请函就位 (见 beta-invitation.md)
- [ ] PRD §10 转化漏斗指标已更新 (见 10-success-metrics.md)

### 10.3 W7 末 (Track D 收尾)

- [ ] Stripe 接入成功 + 自动续费
- [ ] 发票可下载 (PDF)
- [ ] 转化漏斗看板上线 (W6 末实现, W7 验证)

---

## 11. 风险与应对

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| 律师不愿注册 (邮箱门槛) | 中 | 中 | W6 加微信扫码注册, 降低门槛 |
| 验证码被刷 | 中 | 低 | 60s 限流 + 5 次锁定 + IP 限流 |
| 注册后不激活 (高跳出) | 高 | 高 | Onboarding 5 步引导 + Day 1 / Day 3 邮件提醒 |
| 试用期内大量用, 到期全流失 | 中 | 高 | Day 23/29/31 三段提醒 + 数据导出 (降低流失焦虑) |
| 高级律师不愿试用 (嫌功能少) | 低 | 中 | 公测邀请函定向给单飞/小所, 高级律师走 Track E 评审 + 企业版 |
| 邮箱验证失败 (邮件被拦截) | 中 | 中 | W6 备用短信验证 (阿里云 / 腾讯云短信) |

---

## 12. 整理人备注 (PM)

- 本文档 PM 预填 v1.0, W6 coder 落库 + 接 API 后, **本节追加 "v1.1 实测数据"** 记录实际转化率
- W7 末接 Stripe 后, 在 §5.1 / §5.2 补充 `subscription_id` / `plan_type` 字段
- 字段命名遵循 W3 已有的 snake_case (跟 Track A auth 8 endpoint 一致)
- 文案口径跟 Track C 律师访谈时用的一致 ("AI 辅助、不替代律师")
- W8 启动创始体验官计划时, trial_status 新增 'founder' 值 (免费 1 年), 单独走 invite code

> **PM 责任**: W5 文档完整, W6 跟踪 coder 实现进度, W7 末实测转化率, W12 出转化漏斗报告给总指挥 + 投资人.