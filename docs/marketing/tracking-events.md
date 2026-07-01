<!-- LexPrime Track D · W6 Day 3 交付 -->
# 5 事件埋点规范 (Tracking Events W6)

> **版本**: v0.1 · 2026-06-29
> **Track**: D (公测预热 + 埋点规范)
> **Week**: W6 Day 3
> **目标**: PRD § 10 成功指标 4 个指标 (WAU / 漏斗 / 留存 / 付费) 的埋点落地
> **配套**: `funnel-data-w6.md` (5 步漏斗) · `dashboard-w6.md` (日看板) · `prd/10-success-metrics.md` § 11.2.1
>
> **使用说明**: 本文档是 **5 个核心 event 字段的埋点契约**, 律 B/PM/coder 共用.
> 落地方式: lex-coder W6 Day 3 在 backend/cases-crawler/api/tracking_router.py 实现 POST /api/tracking/event, 5 个 event 名严格按本文 § 1.

---

## 1. 5 个核心 Event 字段定义

> **5 个 event 名严格不变**, 埋点代码 (前端 + 后端) 引用, 漏斗查询 (SQL) 引用.
> **每个 event 必填字段**: `event` (枚举), `user_id` (UUID), `created_at` (timestamp UTC+8), `session_id` (string).

### 1.1 Event 1: `trial_landing_pv` (访问)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `event` | string | ✅ | 固定 `trial_landing_pv` |
| `user_id` | string | ✅ | 用户 UUID (未登录时填 `anonymous_<ip>`) |
| `session_id` | string | ✅ | 会话 UUID (前端生成, 30 min 内同会话) |
| `created_at` | timestamp | ✅ | UTC+8 时间戳 |
| `page_url` | string | ✅ | landing 页面 URL (例: `/beta`) |
| `referrer` | string | ⛔ | 来源 URL (例: 微信, 朋友圈) |
| `invite_code` | string | ⛔ | URL 邀请码 (BETA2025-XXXX), 渠道归因 |
| `utm_source` | string | ⛔ | 渠道 (wechat / email / qr / referral / bar-association) |
| `device_type` | string | ⛔ | mobile / desktop / tablet (前端 UA 解析) |

**触发位置**: 公测 landing 7 大模块任一 PV (templates/views/beta/index.html, W6 lex-design 落地)
**触发代码** (前端):
```js
track('trial_landing_pv', { page_url: location.pathname, invite_code: getQueryParam('ref') });
```

### 1.2 Event 2: `trial_register_submit` (试用)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `event` | string | ✅ | 固定 `trial_register_submit` |
| `user_id` | string | ✅ | 新注册用户 UUID |
| `session_id` | string | ✅ | 会话 UUID |
| `created_at` | timestamp | ✅ | UTC+8 时间戳 |
| `email` | string | ✅ | 注册邮箱 (RFC 5322 校验) |
| `invite_code` | string | ✅ | 邀请码 (BETA2025-XXXX), 必须合法 |
| `channel` | string | ✅ | 渠道 (review / wechat-group / founding-member / bar-association / public) |
| `form_fields` | json | ⛔ | 表单字段 (例: `{"name": "张律师", "firm": "金杜"}`) |

**触发位置**: 注册表单提交成功后, 后端自动记录 (POST /api/trial/start)
**触发代码** (后端):
```python
# backend/cases-crawler/api/trial_router.py
async def start_trial(req: TrialStartRequest, db: AsyncSession = Depends(get_db)):
    # 验证邀请码
    invite = await db.scalar(select(InviteCode).where(InviteCode.code == req.invite_code))
    if not invite or invite.status != "unused":
        raise HTTPException(400, "邀请码无效或已使用")
    # 创建用户 + 试用记录
    user = await create_user(db, req.email, req.name)
    trial = await create_trial(db, user.id, duration_days=30)
    # 更新邀请码状态
    invite.status = "redeemed"
    invite.redeemed_at = datetime.now(CST)
    invite.assigned_to = req.name
    # 触发埋点 event
    await track_event(db, event="trial_register_submit", user_id=user.id,
                      email=req.email, invite_code=req.invite_code,
                      channel=invite.channel,
                      form_fields={"name": req.name, "firm": req.firm})
    return {"user_id": user.id, "trial_id": trial.id, "trial_expires_at": trial.expires_at}
```

### 1.3 Event 3: `onboarding_complete_3_step` (激活)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `event` | string | ✅ | 固定 `onboarding_complete_3_step` |
| `user_id` | string | ✅ | 用户 UUID |
| `session_id` | string | ✅ | 会话 UUID |
| `created_at` | timestamp | ✅ | UTC+8 时间戳 |
| `step_completed` | int | ✅ | 完成步骤数 (3 / 4 / 5) |
| `step1_done` | bool | ⛔ | "上传首个案件" 是否完成 |
| `step2_done` | bool | ⛔ | "跑类案检索" 是否完成 |
| `step3_done` | bool | ⛔ | "跑合同审查" 是否完成 |
| `step4_done` | bool | ⛔ | "邀请同行" 是否完成 |
| `step5_done` | bool | ⛔ | "关注公众号" 是否完成 |

**触发位置**: 用户完成第 3 步 / 第 4 步 / 第 5 步引导时
**激活定义**: 完成 ≥3 步 = 已激活 (PRD § 10.2.1.3 激活律师定义)
**触发代码** (前端):
```js
function trackOnboarding(step, total) {
  if ([3, 4, 5].includes(total)) {
    track('onboarding_complete_3_step', {
      step_completed: total,
      step1_done: step >= 1,
      step2_done: step >= 2,
      step3_done: step >= 3,
      step4_done: step >= 4,
      step5_done: step >= 5
    });
  }
}
```

### 1.4 Event 4: `login` (登录活跃)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `event` | string | ✅ | 固定 `login` |
| `user_id` | string | ✅ | 用户 UUID |
| `session_id` | string | ✅ | 新会话 UUID |
| `created_at` | timestamp | ✅ | UTC+8 时间戳 |
| `login_method` | string | ⛔ | 登录方式 (email / wechat / oauth) |
| `device_type` | string | ⛔ | mobile / desktop / tablet |
| `last_active_at` | timestamp | ⛔ | 上次活跃时间 (计算 DAU/MAU 用) |

**触发位置**: 用户登录成功后 (后端 session 创建时)
**活跃定义**: 登录后 30 min 内任何操作算「本次活跃」
**触发代码** (后端):
```python
# backend/cases-crawler/api/auth_router.py
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate(db, req.email, req.password)
    if not user:
        raise HTTPException(401)
    session = await create_session(db, user.id)
    # 触发埋点
    await track_event(db, event="login", user_id=user.id,
                      login_method=req.method, device_type=req.device_type)
    return {"access_token": session.access_token}
```

### 1.5 Event 5: `skill_run` (Skill 调用活跃)

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `event` | string | ✅ | 固定 `skill_run` |
| `user_id` | string | ✅ | 用户 UUID |
| `session_id` | string | ✅ | 会话 UUID |
| `created_at` | timestamp | ✅ | UTC+8 时间戳 |
| `skill_id` | string | ✅ | Skill 标识 (skill1_case / skill2_contract / skill3_document / skill4_court) |
| `skill_name` | string | ⛔ | Skill 名称 (类案检索 / 合同审查 / 文书生成 / 庭审准备) |
| `input_size` | int | ⛔ | 输入大小 (例: 合同字数, 案件数) |
| `output_size` | int | ⛔ | 输出大小 (例: 审查报告字数) |
| `duration_ms` | int | ⛔ | Skill 执行耗时 (ms) |
| `success` | bool | ✅ | Skill 是否执行成功 |

**触发位置**: 4 大 Skill 任一执行 (前端 + 后端)
**活跃定义**: 4 大 Skill 调用成功算「1 次活跃」
**触发代码** (后端):
```python
# backend/cases-crawler/skills/{skill_id}/router.py
async def run_skill(req: SkillRequest, user_id: str = Depends(get_current_user),
                    db: AsyncSession = Depends(get_db)):
    start = time.time()
    try:
        result = await execute_skill(req, user_id)
        duration = int((time.time() - start) * 1000)
        # 触发埋点
        await track_event(db, event="skill_run", user_id=user_id,
                          skill_id=req.skill_id, success=True,
                          duration_ms=duration,
                          input_size=len(req.input_text),
                          output_size=len(result.output_text))
        return result
    except Exception as e:
        await track_event(db, event="skill_run", user_id=user_id,
                          skill_id=req.skill_id, success=False)
        raise
```

---

## 2. 4 个跟踪指标 (PRD § 10.2 + § 11.2.1)

### 2.1 指标 1: WAU (Weekly Active Users, 北极星)

**定义**: 自然周内 (周一 00:00 - 周日 23:59) 至少 1 次 `login` 或 `skill_run` 的独立用户数.
**跟踪 SQL**:
```sql
SELECT DATE_TRUNC('week', created_at) AS week, COUNT(DISTINCT user_id) AS wau
FROM tracking
WHERE event IN ('login', 'skill_run')
  AND created_at >= '2026-07-26'
GROUP BY week
ORDER BY week;
```
**目标**: W6 末 50, W7 末 100 (PRD § 10.2.5 公测期目标)

### 2.2 指标 2: 漏斗 (Funnel Conversion)

**定义**: 5 步漏斗 (访问 → 试用 → 7 日活跃 → 30 日活跃 → 付费), 见 `funnel-data-w6.md` § 1.1.
**跟踪 SQL**: 见 `funnel-data-w6.md` § 2.1.
**目标**:
- 访问 → 试用 ≥ 30%
- 试用 → 7 日活跃 ≥ 50%
- 7 日 → 30 日活跃 ≥ 80%
- 30 日 → 付费 ≥ 10% (试用 → 付费 5%+)
- 总转化 ≥ 1.5%

### 2.3 指标 3: 留存 (Retention)

**定义**: 注册后 Day 7 / Day 30 的活跃率.
**Day 7 留存 SQL**:
```sql
SELECT
  DATE(t2.created_at) AS register_day,
  COUNT(DISTINCT t2.user_id) AS registered,
  COUNT(DISTINCT t3.user_id) AS active_7d,
  ROUND(COUNT(DISTINCT t3.user_id) * 100.0 / COUNT(DISTINCT t2.user_id), 1) AS retention_7d_pct
FROM tracking t2
LEFT JOIN tracking t3 ON t2.user_id = t3.user_id
  AND t3.event IN ('login', 'skill_run')
  AND t3.created_at > t2.created_at
  AND t3.created_at <= t2.created_at + INTERVAL '7 days'
WHERE t2.event = 'trial_register_submit'
GROUP BY DATE(t2.created_at)
ORDER BY register_day;
```
**Day 30 留存 SQL**: 同上, 改为 `INTERVAL '30 days'`.
**目标**: Day 7 ≥ 60%, Day 30 ≥ 30% (PRD § 11.4 防御性指标)

### 2.4 指标 4: 付费 (Payment / Conversion)

**定义**: 试用律师中转化为付费律师的比率.
**跟踪 SQL**:
```sql
SELECT
  DATE_TRUNC('month', t1.created_at) AS month,
  COUNT(DISTINCT t1.user_id) AS total_trial,
  COUNT(DISTINCT t2.user_id) AS converted_paid,
  ROUND(COUNT(DISTINCT t2.user_id) * 100.0 / COUNT(DISTINCT t1.user_id), 1) AS conversion_pct
FROM tracking t1
LEFT JOIN tracking t2 ON t1.user_id = t2.user_id
  AND t2.event = 'payment_success'
  AND t2.created_at > t1.created_at
  AND t2.created_at <= t1.created_at + INTERVAL '60 days'
WHERE t1.event = 'trial_register_submit'
GROUP BY DATE_TRUNC('month', t1.created_at)
ORDER BY month;
```
**目标**: 30 天试用 → 付费 30%+ (激活律师, PRD § 10.2.1.1)

### 2.5 5 事件 → 4 指标映射

| 5 事件 | 4 指标 | 关系 |
|--------|--------|------|
| `trial_landing_pv` | 漏斗 step1 + 流量来源 | 基线 |
| `trial_register_submit` | 漏斗 step2 + 试用注册数 | 关键节点 |
| `onboarding_complete_3_step` | 激活数 + 激活率 | 激活律师判定 |
| `login` | WAU + 留存 + 漏斗 step3/step4 | 活跃判定 (主) |
| `skill_run` | WAU + 留存 + 漏斗 step3/step4 | 活跃判定 (辅) |
| (无) | 漏斗 step5 付费 → 走支付系统 | 独立, 不在 5 事件中 |

> **支付系统**: 走 Stripe webhook, lex-coder 接入时单独实现 `payment_success` event (不在本文 5 事件中).

---

## 3. Event Schema 详细规范 (coder 落地用)

### 3.1 公共字段 (所有 event 必填)

```json
{
  "event": "trial_landing_pv",          // string, 5 选 1 (见 § 1)
  "user_id": "uuid-xxxx",                // string, UUID
  "session_id": "uuid-yyyy",             // string, UUID
  "created_at": "2026-07-26T14:30:00+08:00",  // timestamp, ISO 8601 UTC+8
  "app_version": "1.0.0",                // string, 客户端版本
  "platform": "web"                      // string, web / desktop / mobile
}
```

### 3.2 私有字段 (各 event 专属)

见 § 1.1-1.5 各 event 字段表.

### 3.3 数据库表设计 (lex-coder 落地)

```sql
-- tracking event 表
CREATE TABLE tracking_events (
  id BIGSERIAL PRIMARY KEY,
  event VARCHAR(50) NOT NULL,                -- trial_landing_pv / trial_register_submit / ...
  user_id VARCHAR(64) NOT NULL,
  session_id VARCHAR(64) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL,
  app_version VARCHAR(20),
  platform VARCHAR(20),
  -- 私有字段 (jsonb 灵活存储)
  properties JSONB NOT NULL DEFAULT '{}',
  -- 索引
  INDEX idx_event_created (event, created_at),
  INDEX idx_user_event (user_id, event),
  INDEX idx_session (session_id)
);
```

### 3.4 API 设计

#### POST /api/tracking/event (埋点入口)

**请求体**:
```json
{
  "event": "trial_landing_pv",
  "user_id": "uuid-xxxx",
  "session_id": "uuid-yyyy",
  "created_at": "2026-07-26T14:30:00+08:00",
  "app_version": "1.0.0",
  "platform": "web",
  "properties": {                          // 私有字段
    "page_url": "/beta",
    "invite_code": "BETA2025-0001",
    "utm_source": "wechat"
  }
}
```

**响应** (200):
```json
{ "ok": true, "id": 12345 }
```

**频率限制**: 1 user / 100 events / min (防刷)
**批量上报**: 支持 1 次提交多 event (前端缓冲 10s 批量上报)

#### GET /api/tracking/stats (后台查询, Mavis 跑日报用)

**入参** (query string):
- `metric`: wau / funnel / retention / conversion (4 选 1)
- `start_date`: 2026-07-26
- `end_date`: 2026-08-23
- `channel`: (可选) review / wechat-group / founding-member / bar-association / public

**响应** (200):
```json
{
  "metric": "funnel",
  "period": "2026-07-26 - 2026-08-23",
  "data": {
    "step1_visit": 1500,
    "step2_trial": 120,
    "step3_active_7d": 60,
    "step4_active_30d": 50,
    "step5_paid": 8,
    "conversion": {
      "step1_to_step2": 8.0,
      "step2_to_step3": 50.0,
      "step3_to_step4": 83.3,
      "step4_to_step5": 16.0,
      "step1_to_step5": 0.53
    }
  }
}
```

---

## 4. 前端 SDK 设计 (lex-design 落地)

### 4.1 极简 SDK (~50 行 JS, 内嵌在 landing / 工作台)

```javascript
// assets/js/tracking.js
(function() {
  const ENDPOINT = '/api/tracking/event';
  const BATCH_INTERVAL = 10 * 1000;  // 10s 批量上报
  const queue = [];

  function getSessionId() {
    let sid = localStorage.getItem('lp_session_id');
    if (!sid) {
      sid = crypto.randomUUID();
      localStorage.setItem('lp_session_id', sid);
    }
    return sid;
  }

  function getUserId() {
    return localStorage.getItem('lp_user_id') || `anonymous_${location.hostname}`;
  }

  function track(event, properties = {}) {
    queue.push({
      event,
      user_id: getUserId(),
      session_id: getSessionId(),
      created_at: new Date().toISOString(),
      app_version: '1.0.0',
      platform: 'web',
      properties
    });
    if (queue.length >= 10) flush();
  }

  function flush() {
    if (queue.length === 0) return;
    const batch = queue.splice(0, 10);
    fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ events: batch })
    }).catch(() => {
      // 网络失败, 放回队列
      queue.unshift(...batch);
    });
  }

  // 10s 定时上报
  setInterval(flush, BATCH_INTERVAL);
  // 页面关闭前上报
  window.addEventListener('beforeunload', flush);

  // 暴露全局
  window.lexTrack = track;
})();
```

### 4.2 集成示例 (landing / beta / workstation)

```html
<!-- templates/views/beta/index.html -->
<script src="/assets/js/tracking.js"></script>
<script>
  // 访问时
  document.addEventListener('DOMContentLoaded', () => {
    lexTrack('trial_landing_pv', {
      page_url: location.pathname,
      invite_code: new URLSearchParams(location.search).get('ref') || null,
      utm_source: new URLSearchParams(location.search).get('utm_source') || 'direct'
    });
  });

  // CTA 点击
  document.querySelector('#trial-cta').addEventListener('click', () => {
    lexTrack('trial_cta_click', {
      page_url: location.pathname,
      cta_text: '免费试用 30 天'
    });
  });
</script>
```

### 4.3 工作台 / Skill 调用 (track skill_run)

```html
<!-- templates/views/workstation.html -->
<script>
  function callSkill(skillId, input) {
    return fetch(`/api/skills/${skillId}/run`, {
      method: 'POST',
      body: JSON.stringify({ input })
    })
    .then(r => r.json())
    .then(result => {
      lexTrack('skill_run', {
        skill_id: skillId,
        skill_name: result.skill_name,
        input_size: JSON.stringify(input).length,
        output_size: result.output.length,
        duration_ms: result.duration_ms,
        success: true
      });
      return result;
    })
    .catch(err => {
      lexTrack('skill_run', {
        skill_id: skillId,
        success: false
      });
      throw err;
    });
  }
</script>
```

---

## 5. 埋点接入清单 (W6 Day 3-5 落地)

| 接入点 | 文件 | 触发 event | 优先级 | 责任人 |
|--------|------|-----------|--------|--------|
| **公测 landing 7 大模块** | templates/views/beta/index.html | `trial_landing_pv` | P0 | lex-design |
| **注册表单** | templates/views/register.html + backend/cases-crawler/api/trial_router.py | `trial_register_submit` | P0 | lex-coder |
| **5 步 onboarding** | templates/views/onboarding.html | `onboarding_complete_3_step` | P0 | lex-design |
| **登录** | backend/cases-crawler/api/auth_router.py | `login` | P0 | lex-coder |
| **4 大 Skill 调用** | backend/cases-crawler/skills/*/router.py | `skill_run` | P0 | lex-coder |
| **支付成功 (Stripe)** | backend/cases-crawler/api/payment_router.py | `payment_success` (非 5 事件) | P1 | lex-coder (W7 接入) |
| **dashboard-w6.md 4 指标查询** | scripts/daily-stats.py | (查询, 不埋点) | P0 | lex-bd + Mavis |

### 5.1 P0 落地时间表

| 时间 | 接入点 | 验证 |
|------|--------|------|
| **W6 Day 3 (07-15)** | 邀请码系统 + 注册 API (trial_register_submit) | curl 验证 |
| **W6 Day 3 (07-15)** | 公测 landing (trial_landing_pv) | 浏览器 devtools 验证 |
| **W6 Day 4 (07-22)** | 5 步 onboarding (onboarding_complete_3_step) | 浏览器走完 5 步验证 |
| **W6 Day 4 (07-22)** | 登录 (login) | curl 验证 |
| **W6 Day 5 (07-25)** | 4 大 Skill 调用 (skill_run) | curl 验证 |
| **W7 Day 1 (07-29)** | 4 指标 dashboard 查询 | Mavis 跑日报验证 |

### 5.2 验证标准

- [ ] 5 个 event 全部有 backend 入口 (POST /api/tracking/event)
- [ ] 5 个 event 全部有前端触发点 (埋点 SDK)
- [ ] 数据库表 tracking_events 创建 + 索引就位
- [ ] 频率限制 1 user / 100 events / min 生效
- [ ] 批量上报 (10s) 正常
- [ ] 4 指标 SQL 跑通 (Mavis 跑日报)

---

## 6. 风险与回退

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| 埋点漏报 (前端 SDK 加载失败) | 中 | 中 | 降级: 走 noscript 像素 + 后端强制埋点 (登录 + Skill 调用) |
| 埋点误报 (测试数据 / 内部用户) | 中 | 中 | 内置 `is_internal` 字段, 内部用户 (reviewer@lexprime.com) 排除 |
| 埋点性能 (前端卡顿) | 低 | 中 | 10s 批量上报 + Web Worker, 不阻塞主线程 |
| 数据库写入压力 (日均 1 万 event) | 中 | 中 | 7d 后归档冷数据 (S3), 热数据保留近 30d |
| 隐私合规 (PII 字段) | 低 | 高 | PII 字段 (邮箱 / 姓名) 单独 hash 存储, 不在 properties jsonb 中明文 |

---

## 7. 验收标准 (W6 末)

- [x] tracking-events.md v0.1 起草 (本文档, 5 事件 + 4 指标定义)
- [ ] 5 个 event backend 入口跑通 (lex-coder W6 Day 3-5 落地)
- [ ] 5 个 event 前端触发点就位 (lex-design W6 Day 3-4 落地)
- [ ] 数据库 tracking_events 表 + 索引就位
- [ ] 4 指标 SQL 跑通 (Mavis W7 Day 1 验证)
- [ ] 公测期 4 指标日看板就绪 (dashboard-w6.md)

> **整理人**: lex-bd (BD/运营) · 协作: lex-coder (backend) · lex-design (前端 SDK) · Mavis (4 指标 SQL) · 文档版本: v0.1 (06-29)

---
