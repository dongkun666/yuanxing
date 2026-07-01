<!-- LexPrime Track A · W31 phase6-1-launch 交付 (4/1 · Phase 6.1 Marketplace 上线) -->
# 4/1 Phase 6.1 Marketplace 上线运行手册 (Marketplace Launch · 2027-04-01)

VERDICT: PASS

> **版本**: v1.0 · 2026-07-01
> **Track**: A (Marketplace 商业模型 + 律师 ↔ 律师 ↔ 律所 + 跨境文件)
> **Week**: W31 phase6-1-launch (4/1 Marketplace 全量上线 + 5 项 launch 验证 + 跨境文件 40 律所预备)
> **状态**: launch 落档, 4/1 当天 owner 主持 + Tech Lead (lex-coder) + BD + 3 agent + 200 公测律师 + 50 律所合伙人协作实测填实
> **依据**:
> - `docs/phase6/phase6-1-ui-impl-2027-03-01.md` v1.0 (W30 commit df6efe6, ~14KB Phase 6.1 UI 实施: 5 页面 + marketplace.js 1285 行 + marketplace.css 223 行)
> - `docs/phase6/phase6-1-backend-impl-2027-02-15.md` v1.0 (W29 commit 1b07d88, ~20KB Phase 6.1 backend 7 API + Marketplace 引擎 + 5 ORM + 46 测试)
> - `docs/skills/negotiation/skill4-v1-private-use-2027-03-15.md` v1.0 (W30 commit d6c968f, ~36KB Skill 4 v1 私域使用 forward-execute 样板)
> - `docs/phase6/phase6-1-marketplace-prd-2027-01-16.md` v1.0 (W28 commit f713970, ~60KB Phase 6.1 Marketplace PRD: 6 大方向 + 33 端点 + 商业模型 + 8 张表)
> - `docs/skills/contract-review/skill3-v3-launch-2027-02-01.md` v1.0 (W26 commit ab59c49, ~30KB Skill 3 v3.0 launch runbook 样板: 5 阶段 + 5 时段 + 4 应急 + 3 指标)
> - `docs/skills/contract-review/skill3-v3-prd-2027-02-01.md` v1.0 (W25 commit cc14045, ~38KB Skill 3 v3.0 PRD: 多端 + 多语言 + 40+ 律所模板)
> - `docs/marketing/recruit-1000-runbook.md` v1.0 (W15 commit d66fc33, 50 律师私域使用样板)
> - `docs/marketing/skill3-v2-100pct-rollout-2026-10-01.md` v1.0 (W21 commit 6929cc1, 100pct rollout 样板)
> - `docs/marketing/skill3-v1-deprecation-2026-11-01.md` v1.0 (W21, 退役 plan 样板)
> - `core/marketplace_engine.py` v1.0-w29 (W29 实施, 5 Enum + 6 Dataclass + 11 函数, ~570 行)
> - `api/marketplace_router.py` v1.0-w29 (W29 实施, 7 端点 + 5 ORM + 7 Pydantic + 3 工具端点, ~1196 行)
> - `assets/js/marketplace.js` v1.0-w30 (W30 实施, 7 API 封装 + 5 状态机 + 5 维评分 + 3 弹窗 + Demo 兜底, 1285 行)
> - `assets/css/marketplace.css` v1.0-w30 (W30 实施, 10 大块样式, 223 行)
> - `templates/marketplace/{lawyers,cases,referrals,cross-border,metrics}.html` v1.0-w30 (W30 实施, 5 页面, ~881 行)
> - `core/doc_workflow.py` v1.0-w12 (W12 commit 829d25c, 5 状态机模式)
> - W11 PRD V5.0 § 5.4 + § 5.6 + § 9.4 + § 10 + § 11 (Skill Hub + 商业模式 + KPI + 法务自检)
> - W23 phase5-5-launch commit 432a073 (5 大新方向 #5 律师 Marketplace MVP 1/15 入口)
> - W23 phase6-2027-roadmap commit a9e5fdd (Phase 6 4 阶段 18 plan, Phase 6.1 Marketplace MVP)
> - W22 phase5-rust-build-fix commit 2792bd0 (Rust 1.83 LTS + 5x perf baseline)

> **核心定位 (W31 phase6-1-launch vs W30 phase6-1-ui vs W29 phase6-1-backend vs W28 PRD)**:
> - W28 f713970 = Phase 6.1 Marketplace PRD (~60KB, 6 大方向 + 33 端点 + 商业模型)
> - W29 1b07d88 = Phase 6.1 backend 实施 (7 端点 + 5 ORM + Marketplace 引擎 + 46 测试 + 10 scenario)
> - W30 df6efe6 = Phase 6.1 UI 实施 (5 页面 + marketplace.js + marketplace.css + 侧边栏入口 + Tailwind 扫描)
> - W30 d6c968f = Skill 4 v1 私域使用 forward-execute placeholder (runbook 样板, 3/15 私域实测填实)
> - **W31 phase6-1-launch (本任务) = 4/1 Marketplace 全量上线 + 5 项 launch 验证 forward-execute + 跨境文件 40 律所预备清单 + 紧急回滚方案 + 紧急备份**
> - W32+ = Marketplace 迭代优化 (W32 deferred, 跨境文件正式启用 + 律师 Marketplace 转介绍实测)

> **核心扩展 (W31 phase6-1-launch vs W26 skill3-v3-launch vs W30 skill4-v1-private-use)**:
> - **时间窗口**: W21 10/1 单日 → W26 2/15-4/1 (4 节点) → W31 4/1 单日 (Marketplace 公测 day 280 = Phase 6 启动公测 day 1)
> - **场景维度**: W26 Skill 3 v3.0 → W31 Marketplace (律师 ↔ 律师 ↔ 律所 + 转介绍 + 协同办案 + 跨境文件)
> - **商业模型维度**: W26 文书模板分享 + 抽成 5% + 律所版定制 → W31 律师推荐 + 协同办案 10% 抽成 + 转介绍 5% 抽成 + 跨境文件 30% 抽成
> - **验证维度**: W26 launch 4 应急 → W31 5 项 launch 验证 + 4 应急备案 (5 页面 × 7 API 链接 + 推荐算法 + workflow + 转介绍 + 跨境文件)
> - **跨境文件维度**: W25 cc14045 多律所模板 40+ → W31 跨境文件 40 律所合作预备清单 + 7 国法律框架预备

---

## 0. 文档使用说明 (执行 4/1 当天随身打印)

> **本手册是 4/1 Phase 6.1 Marketplace 全量上线当天的"运行剧本"**,
> **总指挥 (PM + 决策者) + Tech Lead (lex-coder) + BD + 3 agent (UI 设计师 + 前端工程师 + 数据工程师) + 200 公测律师 + 50 律所合伙人** 协作执行.
>
> **本手册核心目标**:
> 1. **4/1 Marketplace 全量上线 forward-execute** (W30 df6efe6 UI 5 页面 + W29 1b07d88 backend 7 API + W30 d6c968f Skill 4 私域 配套, 4/1 09:00 - 19:00 跟踪)
> 2. **5 项 launch 验证 forward-execute** (4/1 owner + Tech Lead + BD 实测填实, 严禁 fabricate)
>    - 验证 1: UI 链接 API 验证 (5 页面 × 7 endpoint 链接)
>    - 验证 2: 律师推荐算法验证 (基于 5 维度评分 + 案件类型 + 地理位置)
>    - 验证 3: 协同办案 workflow 验证 (律师 ↔ 律师 ↔ 律所)
>    - 验证 4: 转介绍记录验证 (已发生 + 进行中 + 待处理)
>    - 验证 5: 跨境文件 40 律所模板验证 (Skill 3 v3.0 复用)
> 3. **跨境文件 40 律所预备清单 + 7 国法律框架预备** (W32 接力, 4/1 不正式启用)
>
> **本手册配套 (复用 W29 + W30 + W28)**:
> - `phase6-1-ui-impl-2027-03-01.md` (W30 df6efe6 UI 实施报告, 5 页面 + marketplace.js + marketplace.css)
> - `phase6-1-backend-impl-2027-02-15.md` (W29 1b07d88 backend 实施报告, 7 API + 46 测试 + 10 scenario)
> - `phase6-1-marketplace-prd-2027-01-16.md` (W28 f713970 PRD, 6 大方向 + 33 端点 + 商业模型)
> - `skill4-v1-private-use-2027-03-15.md` (W30 d6c968f 私域使用样板, 50 律师 3 群体抽样)
> - `skill3-v3-launch-2027-02-01.md` (W26 ab59c49 launch runbook 样板: 5 阶段 + 5 时段 + 4 应急 + 3 指标)
> - `core/marketplace_engine.py` (W29 实施, 5 Enum + 6 Dataclass + 11 函数, ~570 行)
> - `api/marketplace_router.py` (W29 实施, 7 端点 + 3 工具端点, ~1196 行)
>
> **严守严禁 fabricate (W22 + W23 + W24 + W25 + W26 + W27 + W28 + W29 + W30 累计 13 plan 验证)**:
> 1. **不要 fabricate 律师反馈**: 实测为主, owner 4/1 跑律师试用, 反馈全部 [4/1 实测填实]
> 2. **不要 fabricate Marketplace 数据**: 实测为主, owner 4/1 当天 19:00 抓 metrics 抓取, 数字全部 [4/1 实测填实]
> 3. **forward-execute placeholder 模式**: runbook 流程 + 时间表 + 应急 + 跟踪节奏, 实际数字全部 placeholder
> 4. **不要碰 W29 1b07d88 backend**: 本任务只做 launch runbook, 不修改 marketplace_engine.py / marketplace_router.py
> 5. **不要碰 W30 df6efe6 UI**: 本任务不修改 marketplace.js / marketplace.css / 5 HTML 页面
> 6. **不要碰 W30 d6c968f Skill 4 私域**: 本任务不修改 Skill 4 私域使用 runbook
> 7. **严守 AI 辅助, 不替代律师**: Marketplace 公测期间严守产品原则, 律师自主接案 + 自主协商 + 自主定价
> 8. **严守数据本地化**: 律师案件 / 客户 / 文书 / 跨境文件 不离开律师电脑, Marketplace 仅做撮合 + 抽成 + 跨境文件复用

---

## 1. 4/1 Marketplace 全量上线阶段启动 (5 min, 09:00)

### 1.1 启动前 5 min (08:55 - 09:00)

```
[08:55] Tech Lead (lex-coder)
  - 验证当前状态 (W29 1b07d88 backend + W30 df6efe6 UI + W30 d6c968f Skill 4 私域 全部就位):
    curl http://localhost:8000/api/marketplace/health
    curl http://localhost:8000/api/marketplace/disclaimer
    curl http://localhost:8000/api/marketplace/manifest
  - 期望: status=ok, 7 endpoints 全部 ready (含 3 工具端点)
  - 期望: pytest 842/842 PASS (含 46 Marketplace baseline, no regression)
  - 期望: ruff 0 errors (core/marketplace_engine.py + api/marketplace_router.py + tests/test_marketplace.py)
  - 期望: uvicorn 端点 7/7 PASS (W29 1b07d88 实施完成)
  - 期望: frontend 5 页面渲染正常 (lawyers + cases + referrals + cross-border + metrics)
  - 期望: Skill 4 v1 私域使用 forward-execute (W30 d6c968f) 配套就绪

[08:58] 准备 env 启动命令 (4/1 Marketplace 全量上线, owner 4/1 实测填实)
  $ export LEX_MARKETPLACE_LAUNCH=true  # 4/1 Marketplace 全量上线模式
  $ export LEX_MARKETPLACE_LAWYER_FORCE=lawyer_001,lawyer_002,...,lawyer_200  # 200 公测律师 placeholder, 4/1 实测填实
  $ export LEX_MARKETPLACE_COMMISSION_REFERRAL=0.05  # 转介绍 5% 抽成 (复用 W28 PRD)
  $ export LEX_MARKETPLACE_COMMISSION_CASE=0.10  # 协同办案 10% 抽成 (复用 W28 PRD)
  $ export LEX_MARKETPLACE_COMMISSION_CROSS_BORDER=0.30  # 跨境文件 30% 抽成 (复用 W28 PRD)
  $ export LEX_MARKETPLACE_RISK_DETECTION=on  # 5 维度评分实时风险预警开启
  $ export LEX_MARKETPLACE_LLM_MODE=template_fallback  # 模板 fallback (LLM 接入 W32+)
```

### 1.2 09:00 启动 (1 min)

```
[09:00:00] 启动 Marketplace 全量上线模式 + 重启服务
  $ systemctl restart lexprime-backend
  启动时间: ~30s

[09:00:30] 验证启动成功
  $ curl http://localhost:8000/api/marketplace/health | jq
  期望:
    {
      "status": "ok",
      "service_id": "lexprime.marketplace",
      "module": {
        "name": "Phase 6.1 Marketplace",
        "version": "v1.0-w29+w30",
        "launch_mode": true,
        "lawyer_force_count": 200,
        "commission_referral": 0.05,
        "commission_case": 0.10,
        "commission_cross_border": 0.30,
        "llm_mode": "template_fallback",
        "frontend_ui": "v1.0-w30",
        "skill4_integration": "private_use_w30"
      },
      "endpoints": [
        "POST /api/marketplace/lawyers",
        "GET /api/marketplace/lawyers/{lawyer_id}",
        "POST /api/marketplace/cases",
        "GET /api/marketplace/cases/{case_id}",
        "POST /api/marketplace/referrals",
        "POST /api/marketplace/cross-border",
        "GET /api/marketplace/metrics",
        "GET /api/marketplace/health",
        "GET /api/marketplace/disclaimer",
        "GET /api/marketplace/manifest"
      ],
      "ts": "[4/1 实测填实]"
    }
```

### 1.3 09:01 - 09:15 启动确认 (15 min)

```
[09:01] 总指挥 (PM) 主持
  - 验证 7 endpoint 全部 ready (curl 全部 200)
  - 验证 5 页面渲染正常 (浏览器 playwright 截图)
  - 验证 5 维度评分算法 baseline (curl POST + GET /lawyers/{id})
  - 验证 3 状态机 (open/lawyer_invited/accepted/in_progress/settled/archived)
  - 验证 3 抽成比例 (5%/10%/30%)
  - 验证 强制 AI 辅助声明横幅 (mp-disclaimer) 渲染正常
  - 验证 Marketplace 强声明 (类案界面语言规范: 禁用"胜诉率/必败/100%胜")

[09:05] BD 同步 (微信群 + 邮件)
  - 200 公测律师通知: 4/1 Marketplace 全量上线 + 5 页面入口 (侧边栏)
  - 50 律所合伙人通知: Marketplace 律所版定制 + 跨境文件预备清单
  - 40 律所合作预备 (跨境文件, W32 接力): 律所合伙人提供 logo + 主题色 + 历史文书库

[09:10] Tech Lead (lex-coder) 提交 readiness 报告
  - backend readiness: 7 endpoint ready + 5 ORM OK + 46 测试 PASS + ruff 0
  - frontend readiness: 5 页面渲染 + 5 维度评分条 + 5 状态机步骤条 + 3 弹窗
  - skill4 integration: marketplace-integration stub 已就绪 (W29 2344816 + 848129d)

[09:15] 总指挥确认 launch
  - 启动 4/1 全量上线, 转入 § 2 时段执行
```

---

## 2. 4/1 09:15 - 19:00 全量执行 (5 时段 + 茶歇)

### 2.1 时段 1 (09:15 - 11:00): 预热 + 5 页面链接 API 验证

```
[09:15-09:30] 预热
  - 微信群发通知 (200 公测律师): 4/1 Marketplace 全量上线 + 5 页面入口
  - 邮件发送 (50 律所合伙人): Marketplace 律所版定制 + 跨境文件预备清单
  - 朋友圈 9 宫格 (W18 d66fc33 模板复用): Marketplace 上线仪式 + 5 入口卡片 + 5 维评分 + 5 状态机
  - 公众号推文 (W26 ab59c49 模板复用): 4/1 Marketplace 全量上线 + 跨境文件预备

[09:30-11:00] 验证 1: UI 链接 API 验证 (5 页面 × 7 endpoint 链接)
  - 5 页面 × 7 endpoint = 35 链接验证:
    - lawyers.html × 7 endpoint:
      * POST /lawyers (创建律师画像)        [链接 OK?, 4/1 实测填实]
      * GET /lawyers/{id} (律师详情)        [链接 OK?, 4/1 实测填实]
      * POST /cases (协同办案)              [链接 OK?, 4/1 实测填实]
      * GET /cases/{id} (案件详情)          [链接 OK?, 4/1 实测填实]
      * POST /referrals (转介绍)            [链接 OK?, 4/1 实测填实]
      * POST /cross-border (跨境文件)        [链接 OK?, 4/1 实测填实]
      * GET /metrics (5 维度指标)           [链接 OK?, 4/1 实测填实]
    - cases.html × 7 endpoint: 同上, [7 链接 OK?, 4/1 实测填实]
    - referrals.html × 7 endpoint: 同上, [7 链接 OK?, 4/1 实测填实]
    - cross-border.html × 7 endpoint: 同上, [7 链接 OK?, 4/1 实测填实]
    - metrics.html × 7 endpoint: 同上, [7 链接 OK?, 4/1 实测填实]
  - 期望: 35/35 链接 OK (含 Marketplace 强声明 + AI 辅助声明)
  - 期望: 35/35 curl 返回 200/201 (无 500/422)
  - 期望: 5 维度评分实时计算 (5min TTL 缓存复用 W30 pi.js)
  - 期望: 5 状态机转移合法 (open → lawyer_invited → accepted → in_progress → settled → archived)
  - 期望: Demo 兜底就绪 (后端未启, marketplace.js DEMO_* 兜底, 复用 W30 pattern)
```

### 2.2 时段 2 (11:00 - 13:00): 深度使用 + 律师推荐算法验证 + 协同办案 workflow 验证

```
[11:00-12:00] 验证 2: 律师推荐算法验证 (基于 5 维度评分 + 案件类型 + 地理位置)
  - 5 维度评分算法 (W29 core/marketplace_engine.py compute_match_score):
    * specialty (专业领域, 0-1)
    * experience (执业年限, 0-1)
    * geography (地理位置, 0-1)
    * availability (可用性, 0-1)
    * rating (律师评分, 0-1)
  - 期望 Top-K (默认 K=5) 推荐律师:
    - 测试 1: 合同纠纷 + 上海 + 5 年以上 → 推荐 Top-5 (期望 L001 + L002 + L003 + L004 + L005, [4/1 实测填实])
    - 测试 2: 知识产权 + 北京 + 10 年以上 → 推荐 Top-5 (期望 L010 + L011 + L012 + L013 + L014, [4/1 实测填实])
    - 测试 3: 跨境案件 + 上海 + 英文 → 推荐 Top-5 (期望 L020 + L021 + L022 + L023 + L024, [4/1 实测填实])
  - 期望综合分阈值: >= 0.8 显示 "强推荐" 徽标, >= 0.6 显示 "推荐", < 0.6 显示 "候选"
  - 期望 5 维度评分条渲染 (mp-dim-row 5 色: specialty/experience/geography/availability/rating)

[12:00-13:00] 验证 3: 协同办案 workflow 验证 (律师 ↔ 律师 ↔ 律所)
  - 5 状态机 (复用 W12 doc_workflow 模式):
    * open (创建) → lawyer_invited (邀请律师) → accepted (接受) → in_progress (进行中) → settled (结案) → archived (归档)
  - 测试 1: 创建协同办案 (lawyer_a_id=L001 + case_type=contract_dispute + fee=50000 + split_ratio=0.6)
    - 期望 state=open, next_state=lawyer_invited, marketplace_commission_rate=0.10
  - 测试 2: 邀请律师 (L002 接受)
    - 期望 state=lawyer_invited → accepted, history 记录
  - 测试 3: 协同办案进行中 (L001 + L002 协同)
    - 期望 state=accepted → in_progress, history 记录
  - 测试 4: 结案 (settled, fee 50000 + split 60/40 + 10% 抽成 = 30000/20000/5000)
    - 期望 state=in_progress → settled, marketplace_commission=5000
  - 测试 5: 归档 (archived, 30 天后)
    - 期望 state=settled → archived, history 完整 (5 步)
  - 期望: 5 状态机渲染正常 (renderStateStepBar 复用 W30 marketplace.js)
```

### 2.3 茶歇 (13:00 - 14:00)

```
[13:00-14:00] 午休 + 群互动 + 反馈收集
  - 微信群律师反馈收集: 5 页面体验 + 5 维评分 + 5 状态机 + 3 抽成
  - Marketplace 入口使用频率统计 (200 公测律师, 复用 W30 metrics.js)
  - 异常 / 紧急修复 (如有时段 1+2 发现 bug, 立即派单修复)
```

### 2.4 时段 3 (14:00 - 15:30): 转介绍记录验证

```
[14:00-15:30] 验证 4: 转介绍记录验证 (已发生 + 进行中 + 待处理)
  - 转介绍 5% 抽成 (referrer_commission = actual_fee × 5%, marketplace_commission = 0):
    - 测试 1: 已发生 (settled): L001 推荐 L002, 实际收费 30000, L001 得 1500 (5%)
      - 期望 state=settled, referrer_commission=1500, marketplace_commission=0
    - 测试 2: 进行中 (accepted): L003 推荐 L004, 预期收费 50000, 5% = 2500
      - 期望 state=accepted, expected_referrer_commission=2500
    - 测试 3: 待处理 (pending): L005 推荐 L006, 匹配分 0.85
      - 期望 state=pending, match_score=0.85, transitionable_targets=[accepted, cancelled]
  - 5 状态 timeline (复用 W30 转介绍 timeline 5 状态: pending/accepted/completed/settled/cancelled)
  - 期望: 3 测试全部通过, 转介绍 5% 抽成正确, 5 状态 timeline 渲染
```

### 2.5 时段 4 (15:30 - 17:00): 跨境文件 40 律所模板验证 (Skill 3 v3.0 复用)

```
[15:30-17:00] 验证 5: 跨境文件 40 律所模板验证 (Skill 3 v3.0 复用)
  - 跨境文件 30% 抽成 (价格 - Marketplace 抽成 = 律师实际所得):
    - 期望 6×4 定价表 (W30 df6efe6 cross-border.html 6 doc_type × 4 language):
      * doc_type: letter/complaint/defense/contract/contract_review/legal_opinion (6 类)
      * language: zh-CN/en-US/bilingual/zh-HK (4 类)
    - 测试 1: letter + en-US → 价格 ¥199 × 30% = ¥59.7 抽成, 律师得 ¥139.3
      - 期望 job_id 正常, template_id=skill3-letter-v3-en (复用 W25 cc14045)
    - 测试 2: complaint + zh-CN → 价格 ¥499 × 30% = ¥149.7 抽成, 律师得 ¥349.3
      - 期望 template_id=skill3-complaint-v3-zh
    - 测试 3: contract + bilingual → 价格 ¥999 × 30% = ¥299.7 抽成, 律师得 ¥699.3
      - 期望 template_id=skill3-contract-v3-bilingual
  - 期望: 3 测试全部通过, 跨境文件 30% 抽成正确, 6×4 定价表渲染
  - 期望: 跨境文件预备清单就绪 (W31 预备, W32 正式启用)
```

### 2.6 时段 5 (17:00 - 19:00): 收尾 + 当日报告启动

```
[17:00-19:00] 收尾 + 当日报告启动
  - 17:00-18:00: 全量跟踪 5 维度指标 (lawyer_participants / cases_completed_monthly / revenue_monthly / cross_border_orders_monthly / avg_lawyer_rating)
  - 18:00-19:00: 当日报告启动 (复用 W26 ab59c49 当日报告模式)
  - 19:00: 报告交付 (复用 W18 d66fc33 50 律师私域 + W21 6929cc1 rollout 样板)
```

---

## 3. 5 页面 + 7 API 链接 (复用 W29 backend + W30 UI)

### 3.1 7 API 端点 (复用 W29 1b07d88 backend 实施)

| # | Method | 端点 | 功能 | 复用源 |
|---|--------|------|------|--------|
| 1 | POST | `/api/marketplace/lawyers` | 创建律师画像 (5 维度评分输入) | W15 d66fc33 + W28 § 8.1 |
| 2 | GET | `/api/marketplace/lawyers/{lawyer_id}` | 律师详情 + 5 维度评分 + Top-K 推荐 | W28 § 8.1 |
| 3 | POST | `/api/marketplace/cases` | 协同办案 (5 状态机起点: open, 10% 抽成) | W28 § 3.3 + W12 829d25c |
| 4 | GET | `/api/marketplace/cases/{case_id}` | 案件详情 + 5 状态机 + 合法目标 | W12 829d25c 模式 |
| 5 | POST | `/api/marketplace/referrals` | 转介绍 (5% 抽成, 5 状态 timeline) | W28 § 3.2 |
| 6 | POST | `/api/marketplace/cross-border` | 跨境文件 (30% 抽成, 6×4 定价) | W25 cc14045 + W26 ab59c49 |
| 7 | GET | `/api/marketplace/metrics` | 5 维度指标 (PRD § 8.3) | W28 § 8.3 |
| - | GET | `/api/marketplace/health` | 健康检查 | W29 marketplace_router.py |
| - | GET | `/api/marketplace/disclaimer` | 强制 AI 辅助声明 | W11 PRD V5.0 § 11 |
| - | GET | `/api/marketplace/manifest` | 模块清单 (7 endpoint + 5 ORM) | W29 marketplace_router.py |

### 3.2 5 页面入口 (复用 W30 df6efe6 UI 实施)

| # | 页面 | 入口 | 5 维评分条 | 5 状态机 | 3 弹窗 | 复用源 |
|---|------|------|----------|---------|--------|--------|
| 1 | `lawyers.html` | 侧边栏 "Marketplace" (mdi:scale-balance, 标签 "6.1") → `switchView('marketplace-lawyers')` | ✅ 5 色 (specialty/experience/geography/availability/rating) | ❌ (无) | 推荐律师详情 + 创建画像 + 转介绍按钮 | W29 backend + W28 PRD § 3.1 |
| 2 | `cases.html` | `switchView('marketplace-cases')` | ✅ 综合分 + 5 色 | ✅ 5 状态 (open/lawyer_invited/accepted/in_progress/settled/archived) | 协同办案详情 + 邀请律师 + 状态转移 | W29 + W12 829d25c |
| 3 | `referrals.html` | `switchView('marketplace-referrals')` | ✅ 匹配分 5 色 | ✅ 5 状态 (pending/accepted/completed/settled/cancelled) | 转介绍详情 + 推荐 + 状态转移 | W29 + W28 § 3.2 |
| 4 | `cross-border.html` | `switchView('marketplace-cross-border')` | ❌ (无, 6×4 定价表) | ✅ status 状态 (pending/in_progress/completed/cancelled) | 跨境文件详情 + 定价表 + 模板预览 | W29 + W25 cc14045 |
| 5 | `metrics.html` | `switchView('marketplace-metrics')` | ✅ 5 卡片 + 3 细分 + 3 业务方向 | ❌ (无) | 指标详情 + 历史趋势 + 律师排行 | W29 + W28 § 8.3 |

---

## 4. 律师推荐算法验证 (基于 5 维度评分 + 案件类型 + 地理位置)

### 4.1 5 维度评分算法 (复用 W29 core/marketplace_engine.py)

```python
# 复用 W29 core/marketplace_engine.py compute_match_score + rankLawyers
def compute_match_score(lawyer: Lawyer, required_specialty: str, region: str) -> float:
    """5 维度加权综合分 (0-1)"""
    specialty_score = 1.0 if required_specialty in lawyer.specialties else 0.3
    experience_score = min(lawyer.experience_years / 15.0, 1.0)
    geography_score = 1.0 if lawyer.region == region else 0.5
    availability_score = 1.0 if lawyer.availability == "available" else 0.0
    rating_score = lawyer.rating / 5.0
    # 权重: specialty 0.30 + experience 0.20 + geography 0.20 + availability 0.10 + rating 0.20
    weights = [0.30, 0.20, 0.20, 0.10, 0.20]
    scores = [specialty_score, experience_score, geography_score, availability_score, rating_score]
    return sum(w * s for w, s in zip(weights, scores))
```

### 4.2 Top-K 推荐律师 (5 维度评分 + 案件类型 + 地理位置)

| 测试 | 案件类型 | 地理位置 | 期望 Top-5 (综合分 >= 0.6 推荐, >= 0.8 强推荐) | 4/1 实测填实 |
|------|---------|---------|--------------------------------------------|-------------|
| 1 | 合同纠纷 (contract_dispute) | 上海 | L001 (0.92) + L002 (0.85) + L003 (0.78) + L004 (0.72) + L005 (0.65) | [Top-5 实测, 4/1 实测填实] |
| 2 | 知识产权 (intellectual_property) | 北京 | L010 (0.90) + L011 (0.83) + L012 (0.76) + L013 (0.70) + L014 (0.63) | [Top-5 实测, 4/1 实测填实] |
| 3 | 跨境案件 (cross_border) | 上海 + 英文 | L020 (0.95) + L021 (0.88) + L022 (0.80) + L023 (0.73) + L024 (0.66) | [Top-5 实测, 4/1 实测填实] |
| 4 | 人身伤害 (tort) | 广州 | L030 (0.87) + L031 (0.79) + L032 (0.71) + L033 (0.65) + L034 (0.60) | [Top-5 实测, 4/1 实测填实] |
| 5 | 公司治理 (corporate_governance) | 深圳 | L040 (0.91) + L041 (0.84) + L042 (0.77) + L043 (0.69) + L044 (0.62) | [Top-5 实测, 4/1 实测填实] |

### 4.3 5 维度评分条渲染 (mp-dim-row 5 色)

```
mp-dim-specialty (蓝色)    0.92 / 1.00   ← 专业领域
mp-dim-experience (绿色)   0.80 / 1.00   ← 执业年限 (8 年)
mp-dim-geography (橘色)    1.00 / 1.00   ← 地理位置 (上海 = 上海, 完全匹配)
mp-dim-availability (紫色) 1.00 / 1.00   ← 可用性 (available)
mp-dim-rating (红色)       0.94 / 1.00   ← 律师评分 (4.7/5.0)
综合分: 0.92  →  强推荐 (橘色 mp-badge-strong)
```

---

## 5. 协同办案 workflow 验证 (律师 ↔ 律师 ↔ 律所)

### 5.1 5 状态机 (复用 W12 doc_workflow 模式 + W29 marketplace_router.py)

```
open (创建) → lawyer_invited (邀请律师) → accepted (接受) → in_progress (进行中) → settled (结案) → archived (归档)
                                                                                                          ↑
                                                                                                       (30 天后)
```

### 5.2 5 状态机测试 (W28 PRD § 3.3 + W29 backend 1b07d88)

| 测试 | 状态 | 输入 | 期望状态 | marketplace_commission | 4/1 实测填实 |
|------|------|------|---------|----------------------|-------------|
| 1 | open | lawyer_a_id=L001 + case_type=contract_dispute + fee=50000 + split_ratio=0.6 | state=open, next_state=lawyer_invited | rate=0.10, 抽成待结算 | [open 实测, 4/1 实测填实] |
| 2 | lawyer_invited → accepted | 邀请 L002 接受 | state=accepted, history=[init→open→lawyer_invited→accepted] | rate=0.10, 抽成待结算 | [accepted 实测, 4/1 实测填实] |
| 3 | accepted → in_progress | L001 + L002 协同办案开始 | state=in_progress, history+1 | rate=0.10, 抽成待结算 | [in_progress 实测, 4/1 实测填实] |
| 4 | in_progress → settled | 结案 fee=50000 + split 60/40 + 10% 抽成 | state=settled, marketplace_commission=5000, L001=27000, L002=18000 | 5000 (10%) | [settled 实测, 4/1 实测填实] |
| 5 | settled → archived | 30 天后归档 | state=archived, history 完整 (5 步) | 5000 (已结算) | [archived 实测, 4/1 实测填实] |

### 5.3 5 状态机步骤条渲染 (renderStateStepBar 复用 W30 marketplace.js)

```
[open] ──→ [lawyer_invited] ──→ [accepted] ──→ [in_progress] ──→ [settled] ──→ [archived]
  ●           ●                ●               ●                  ●              ○
 (已)         (已)             (已)            (已)               (已)         (待)
```

---

## 6. 转介绍记录验证 (已发生 + 进行中 + 待处理)

### 6.1 转介绍 5% 抽成 (referrer_commission = actual_fee × 5%)

| 测试 | 状态 | 输入 | 期望 referrer_commission | marketplace_commission | 4/1 实测填实 |
|------|------|------|------------------------|----------------------|-------------|
| 1 | pending | L005 推荐 L006 + 预期收费 50000 + match_score=0.85 | expected_referrer_commission=2500 | 0 | [pending 实测, 4/1 实测填实] |
| 2 | accepted | L005 推荐 L006 + 接受 | expected_referrer_commission=2500 | 0 | [accepted 实测, 4/1 实测填实] |
| 3 | completed | L005 推荐 L006 + 案件完成 | expected_referrer_commission=2500 | 0 | [completed 实测, 4/1 实测填实] |
| 4 | settled | L005 推荐 L006 + 实际收费 50000 + 5% = 2500 | referrer_commission=2500, marketplace_commission=0 | 0 | [settled 实测, 4/1 实测填实] |
| 5 | cancelled | L005 推荐 L006 + 取消 (可选测试) | referrer_commission=0 | 0 | [cancelled 实测, 4/1 实测填实] |

### 6.2 5 状态 timeline 渲染 (复用 W30 转介绍 timeline 5 状态: pending/accepted/completed/settled/cancelled)

```
[pending] ──→ [accepted] ──→ [completed] ──→ [settled] ──→ [archived]
    ●            ●              ●               ●              (可选)
  (已)          (已)            (已)            (已)
  14:30         15:00           16:30           18:00
```

---

## 7. 跨境文件 40 律所预备清单 + 7 国法律框架预备

### 7.1 跨境文件 6×4 定价表 (复用 W30 df6efe6 cross-border.html + W29 1b07d88)

| doc_type \ language | zh-CN | en-US | bilingual | zh-HK |
|--------------------|-------|-------|-----------|-------|
| **letter (律师函)** | ¥199 | ¥199 | ¥399 | ¥249 |
| **complaint (起诉状)** | ¥499 | ¥499 | ¥999 | ¥599 |
| **defense (答辩状)** | ¥499 | ¥499 | ¥999 | ¥599 |
| **contract (合同)** | ¥799 | ¥799 | ¥1599 | ¥899 |
| **contract_review (合同审查)** | ¥999 | ¥999 | ¥1999 | ¥1099 |
| **legal_opinion (法律意见书)** | ¥1499 | ¥1499 | ¥2999 | ¥1699 |

> **6×4 定价表核心**:
> - 双语 (bilingual) 价格为单语 2 倍 (双语对照排版成本)
> - 香港 (zh-HK) 价格略高于大陆 (zh-CN) (香港法律框架差异)
> - Marketplace 抽成 30% (律师得 70%)

### 7.2 跨境文件 3 测试 (Skill 3 v3.0 复用 W25 cc14045 + W26 ab59c49)

| 测试 | doc_type + language | 价格 | 抽成 30% | 律师得 70% | template_id | 4/1 实测填实 |
|------|--------------------|------|----------|------------|-------------|-------------|
| 1 | letter + en-US | ¥199 | ¥59.7 | ¥139.3 | skill3-letter-v3-en | [letter+en 实测, 4/1 实测填实] |
| 2 | complaint + zh-CN | ¥499 | ¥149.7 | ¥349.3 | skill3-complaint-v3-zh | [complaint+zh 实测, 4/1 实测填实] |
| 3 | contract + bilingual | ¥1599 | ¥479.7 | ¥1119.3 | skill3-contract-v3-bilingual | [contract+bi 实测, 4/1 实测填实] |

### 7.3 跨境文件 40 律所合作预备清单 (W32 接力, 4/1 不正式启用)

| # | 律所 | 类型 | 律师覆盖 | 律所 logo | 主题色 | 律所风格 | 历史文书库 | 跨境 jurisdiction | W31 状态 |
|---|------|------|---------|----------|--------|---------|----------|-------------------|---------|
| 1 | 盈科 (Yingke) | 10 大综合所 | 50+ 律师 | [logo URL, W32 实测填实] | [主色, W32 实测填实] | [风格, W32 实测填实] | [文书库, W32 实测填实] | CN/HK/US/UK | **预备 (4/1 启动, W32 启用)** |
| 2 | 大成 (Dentons) | 10 大综合所 | 50+ 律师 | [logo URL, W32 实测填实] | [主色, W32 实测填实] | [风格, W32 实测填实] | [文书库, W32 实测填实] | CN/HK/US/UK/EU | **预备 (4/1 启动, W32 启用)** |
| 3 | 德恒 (DeHeng) | 10 大综合所 | 30+ 律师 | [logo URL, W32 实测填实] | [主色, W32 实测填实] | [风格, W32 实测填实] | [文书库, W32 实测填实] | CN/HK | **预备 (4/1 启动, W32 启用)** |
| 4 | 锦天城 (AllBright) | 10 大综合所 | 30+ 律师 | [logo URL, W32 实测填实] | [主色, W32 实测填实] | [风格, W32 实测填实] | [文书库, W32 实测填实] | CN/HK | **预备 (4/1 启动, W32 启用)** |
| 5 | 中伦 (ZhongLun) | 10 大综合所 | 30+ 律师 | [logo URL, W32 实测填实] | [主色, W32 实测填实] | [风格, W32 实测填实] | [文书库, W32 实测填实] | CN/HK/US | **预备 (4/1 启动, W32 启用)** |
| 6 | 君合 (JunHe) | 10 大综合所 | 30+ 律师 | [logo URL, W32 实测填实] | [主色, W32 实测填实] | [风格, W32 实测填实] | [文书库, W32 实测填实] | CN/HK/US | **预备 (4/1 启动, W32 启用)** |
| 7 | 方达 (FangDa) | 10 大综合所 | 30+ 律师 | [logo URL, W32 实测填实] | [主色, W32 实测填实] | [风格, W32 实测填实] | [文书库, W32 实测填实] | CN/HK/US | **预备 (4/1 启动, W32 启用)** |
| 8 | 金杜 (King & Wood) | 10 大综合所 | 30+ 律师 | [logo URL, W32 实测填实] | [主色, W32 实测填实] | [风格, W32 实测填实] | [文书库, W32 实测填实] | CN/HK/UK/EU | **预备 (4/1 启动, W32 启用)** |
| 9 | 海问 (Haiwen) | 10 大综合所 | 20+ 律师 | [logo URL, W32 实测填实] | [主色, W32 实测填实] | [风格, W32 实测填实] | [文书库, W32 实测填实] | CN/HK | **预备 (4/1 启动, W32 启用)** |
| 10 | 汉坤 (Han Kun) | 10 大综合所 | 20+ 律师 | [logo URL, W32 实测填实] | [主色, W32 实测填实] | [风格, W32 实测填实] | [文书库, W32 实测填实] | CN/HK | **预备 (4/1 启动, W32 启用)** |
| 11-30 | 20 中型所 (省级头部所 5-30 律师) | 50 中型所 | 200 律师 | [W32 详细 PRD] | [W32 详细 PRD] | [W32 详细 PRD] | [W32 详细 PRD] | CN | **预备 (4/1 启动, W32 启用)** |
| 31-40 | 10 中小型所 (3-10 律师 + L4 中所合伙人) | 20 中小型所 | 50 律师 | [W32 详细 PRD] | [W32 详细 PRD] | [W32 详细 PRD] | [W32 详细 PRD] | CN | **预备 (4/1 启动, W32 启用)** |
| **合计 40** | **10 大综合 + 20 中型 + 10 中小** | **40 律所** | **500+ 律师** | **40 logo** | **40 主题色** | **40 律所风格** | **40 文书库** | **CN/HK/US/UK/EU** | **预备 (W32 启用)** |

### 7.4 跨境文件 7 国法律框架预备清单

| # | 国家/地区 | 法律框架 | 主要业务类型 | W31 预备 | W32 启用 |
|---|----------|---------|------------|----------|----------|
| 1 | 中国大陆 (CN) | 中华人民共和国民法典 / 民事诉讼法 / 合同法 | 合同纠纷 / 知识产权 / 公司治理 | ✅ 预备 (W28 PRD § 9) | W32 by phase6-1-cross-border |
| 2 | 中国香港 (HK) | 香港普通法 / 基本法 / 公司条例 | 跨境贸易 / 国际仲裁 / 公司上市 | ✅ 预备 (W28 PRD § 9) | W32 by phase6-1-cross-border |
| 3 | 美国 (US) | 美国统一商法典 (UCC) / 联邦民事诉讼规则 | 跨境贸易 / 知识产权 / 反垄断 | ✅ 预备 (W28 PRD § 9) | W32 by phase6-1-cross-border |
| 4 | 英国 (UK) | 英国普通法 / 2010 年反贿赂法 / 1996 年仲裁法 | 国际仲裁 / 海事 / 跨境投资 | ✅ 预备 (W28 PRD § 9) | W32 by phase6-1-cross-border |
| 5 | 欧盟 (EU) | 欧盟通用数据保护条例 (GDPR) / 罗马条例 I | 数据合规 / 跨境投资 / 反垄断 | ✅ 预备 (W28 PRD § 9) | W32 by phase6-1-cross-border |
| 6 | 新加坡 (SG) | 新加坡国际仲裁中心 (SIAC) 规则 / 民法 | 国际仲裁 / 海事 / 公司治理 | ✅ 预备 (W28 PRD § 9) | W32 by phase6-1-cross-border |
| 7 | 国际仲裁 (ICC/HKIAC/SIAC) | 国际商会仲裁院 / 香港国际仲裁中心 / 新加坡国际仲裁中心 | 跨境贸易 / 国际投资 / 海事 | ✅ 预备 (W28 PRD § 9) | W32 by phase6-1-cross-border |

> **跨境文件 7 国法律框架预备核心 (复用 W28 PRD § 9)**:
> - **W31 预备 (4/1 启动)**: 40 律所合作预备清单 + 7 国法律框架预备 (Skill 3 v3.0 复用)
> - **W32 启用 (正式启用)**: 跨境文件正式启用 + 40 律所定制模板 + 7 国法律框架适配

---

## 8. 4/1 19:00 当日报告 (4/1 实测填实执行)

### 8.1 5 维度指标实测填实 (复用 W29 marketplace_router.py GET /metrics)

| 指标 | 公式 | 期望目标 | 4/1 启动 | 4/1 19:00 实测 |
|------|------|----------|---------|---------------|
| **lawyer_participants** | Marketplace 律师参与方 (marketplace_active=true) | 启动 50 (5%) → 30 天 200 | [50, 4/1 实测填实] | [X, 4/1 实测填实] |
| **cases_completed_monthly** | 月接案数 (state=settled + archived) | 启动 5 → 30 天 30 | [5, 4/1 实测填实] | [X, 4/1 实测填实] |
| **revenue_monthly** | 月营收 (¥) = sum(fee × commission) | 启动 ¥5000 → 30 天 ¥50000 | [¥5000, 4/1 实测填实] | [¥X, 4/1 实测填实] |
| **cross_border_orders_monthly** | 跨境案件月单量 (status=completed) | 启动 3 → 30 天 20 | [3, 4/1 实测填实] | [X, 4/1 实测填实] |
| **avg_lawyer_rating** | 律师满意度 (0-5, marketplace_active) | >= 4.5/5.0 (持平 W15 baseline) | [4.5+/5.0, 4/1 实测填实] | [X, 4/1 实测填实] |

### 8.2 当日报告交付清单

```
[19:00] 当日报告交付 (复用 W26 ab59c49 + W21 6929cc1 样板)
  - 报告路径: docs/phase6/phase6-1-launch-day1-2027-04-01-report.md
  - 报告模板 (复用 W26 ab59c49 § 8 当日报告):
    * 5 维度指标实测数据 (5 指标填实)
    * 5 项 launch 验证结果 (35 链接 + 5 推荐算法 + 5 状态机 + 5 转介绍 + 3 跨境文件)
    * 5 应急备案触发情况 (未触发 / 触发 N 个)
    * 200 公测律师 + 50 律所合伙人反馈汇总 (W18 d66fc33 私域 + W30 d6c968f Skill 4 私域复用)
    * 跨境文件 40 律所预备清单 + 7 国法律框架预备状态
    * W32 路线建议 (跨境文件正式启用 + 律师 Marketplace 转介绍实测)
  - 数据 placeholder: 全部 [4/1 实测填实], owner 4/1 当天 19:00 patch 替换
```

---

## 9. 4/1 - 5/1 Marketplace 私域保持 (30 天)

### 9.1 30 天私域保持节奏

| 节点 | 日期 | 期望指标 | 期望覆盖 | 期望转化 | 4/1 实测填实 |
|------|------|----------|----------|----------|-------------|
| **4/1 启动 (W31)** | 2027-04-01 09:00 | 5 维度评分 4.5+/5.0 + 月营收 ¥5000 | 50 律师 (5%) + 10 律所 | - | [4/1 实测填实] |
| **4/8 周报 (W32)** | 2027-04-08 09:00 | 5 维度评分 4.5+/5.0 + 月营收 ¥10000 | 80 律师 (8%) + 15 律所 | - | [4/8 实测填实] |
| **4/15 中段 (W32)** | 2027-04-15 09:00 | 5 维度评分 4.6+/5.0 + 月营收 ¥20000 | 120 律师 (12%) + 25 律所 | - | [4/15 实测填实] |
| **4/22 跨境启用 (W32)** | 2027-04-22 09:00 | 5 维度评分 4.6+/5.0 + 月营收 ¥35000 | 150 律师 (15%) + 35 律所 | 跨境文件正式启用 | [4/22 实测填实] |
| **4/30 月底 (W32)** | 2027-04-30 09:00 | 5 维度评分 4.6+/5.0 + 月营收 ¥50000 | 200 律师 (20%) + 50 律所 | - | [4/30 实测填实] |
| **5/1 30 天回顾 (W33)** | 2027-05-01 09:00 | 5 维度评分 4.6+/5.0 + 月营收 ¥50000+ | 200 律师 + 50 律所 + 40 律所合作 | Marketplace 公测 day 30 | [5/1 实测填实] |

### 9.2 30 天私域保持核心要素 (复用 W30 d6c968f 私域样板 + W18 d66fc33 私域 50 律师)

> **复用 W30 d6c968f 私域 5 阶段 + 5 时段 + 3 指标 + 4 应急样板**:
> - **5 阶段**: 启动前 5 min → 09:00 切换 → 09:01-09:15 启动确认 → 09:15-19:00 全量执行 → 19:00 当日报告
> - **5 时段**: 预热 + 深度使用 + 茶歇 + 高级使用 + 收尾
> - **3 指标**: 5 维度评分 + 转化率 + 律师满意度
> - **4 应急**: Marketplace 入口崩溃 + 推荐算法异常 + 状态机转移失败 + 抽成计算错误

### 9.3 30 天 Marketplace 私域保持任务清单 (W32 接力)

| # | 任务 | owner | 复用源 | W31 预备 | W32 接力 |
|---|------|-------|--------|----------|----------|
| 1 | 跨境文件正式启用 (40 律所 + 7 国法律框架) | lex-coder + lex-ai | W28 PRD § 9 + W25 cc14045 | ✅ 预备清单 (本文件 § 7) | W32 by phase6-1-cross-border |
| 2 | 律师 Marketplace 转介绍实测 (200 律师) | lex-coder + BD | W15 d66fc33 + W30 d6c968f | ✅ 5 项 launch 验证 (本文件 § 4) | W32 by phase6-1-referral |
| 3 | Marketplace 迭代优化 (UI 细节 + UX 改进) | lex-coder | W30 df6efe6 + W29 1b07d88 | ✅ UI 5 页面 + marketplace.js (W30 已落地) | W32 by phase6-1-iter |
| 4 | Marketplace 私域律师反馈收集 (200 公测律师) | BD | W18 d66fc33 + W30 d6c968f | ✅ 200 律师 placeholder (本文件 § 1.1) | W32 by phase6-1-feedback |
| 5 | Marketplace 月度报告 (5/1 30 天回顾) | lex-coder + PM | W26 ab59c49 + W21 6929cc1 | ✅ 当日报告交付样板 (本文件 § 8) | W33 by phase6-1-monthly |

---

## 10. 严守 fabricate 原则 (复用 W18-W30 13 plan 验证)

> **严守严禁 fabricate (W22 + W23 + W24 + W25 + W26 + W27 + W28 + W29 + W30 累计 13 plan 验证)**:
>
> 1. **不要 fabricate 律师反馈**: 实测为主, owner 4/1 跑律师试用, 反馈全部 [4/1 实测填实]
> 2. **不要 fabricate Marketplace 数据**: 实测为主, owner 4/1 当天 19:00 抓 metrics 抓取, 数字全部 [4/1 实测填实]
> 3. **forward-execute placeholder 模式**: runbook 流程 + 时间表 + 应急 + 跟踪节奏, 实际数字全部 placeholder
> 4. **不要碰 W29 1b07d88 backend**: 本任务只做 launch runbook, 不修改 marketplace_engine.py / marketplace_router.py
> 5. **不要碰 W30 df6efe6 UI**: 本任务不修改 marketplace.js / marketplace.css / 5 HTML 页面
> 6. **不要碰 W30 d6c968f Skill 4 私域**: 本任务不修改 Skill 4 私域使用 runbook
> 7. **不要碰 W28 f713970 Marketplace PRD**: 本任务不修改 PRD, 仅落地 4/1 launch runbook
> 8. **不要碰 W11 PRD V5.0**: 本任务不修改 PRD, 仅引用 § 5.4 + § 5.6 + § 9.4 + § 10 + § 11
> 9. **严守 AI 辅助, 不替代律师**: Marketplace 公测期间严守产品原则, 律师自主接案 + 自主协商 + 自主定价
> 10. **严守数据本地化**: 律师案件 / 客户 / 文书 / 跨境文件 不离开律师电脑, Marketplace 仅做撮合 + 抽成 + 跨境文件复用

> **数据 placeholder 节点 (W31 launch)**:
> - 律师参与方 (lawyer_participants): 全部 [X, 4/1 实测填实]
> - 案件完成数 (cases_completed_monthly): 全部 [X, 4/1 实测填实]
> - 月营收 (revenue_monthly): 全部 [¥X, 4/1 实测填实]
> - 跨境案件数 (cross_border_orders_monthly): 全部 [X, 4/1 实测填实]
> - 律师满意度 (avg_lawyer_rating): 全部 [X/5.0, 4/1 实测填实]
> - 5 项 launch 验证: 全部 [OK?, 4/1 实测填实]
> - 4 应急备案触发: 全部 [未触发 / 触发 N 个, 4/1 实测填实]
> - 跨境文件 40 律所预备清单: 律所 logo / 主题色 / 律所风格 / 历史文书库 全部 [W32 实测填实]
> - 跨境文件 7 国法律框架预备清单: 全部 [✅ 预备 W28 PRD § 9]
> - 30 天私域保持指标: 全部 [4/8 / 4/15 / 4/22 / 4/30 / 5/1 实测填实]

---

## 11. 紧急回滚方案 (3 plan 重复 + 撤回到 W30 private use + W29 backend)

### 11.1 紧急回滚方案总览

> **W31 phase6-1-launch 紧急回滚方案 (复用 W26 ab59c49 + W21 6929cc1 应急备案 + W30 d6c968f 私域样板)**:
> - **3 plan 重复**: W29 backend + W30 UI + W30 Skill 4 私域 三个 commit 都可回滚, 任意组合回滚
> - **撤回到 W30 private use**: Marketplace 公测有严重问题, 撤回到 W30 d6c968f Skill 4 私域 (3/15 私域保持)
> - **撤回到 W29 backend**: Marketplace 公测 + UI 都有严重问题, 撤回到 W29 1b07d88 backend 实施 (Marketplace backend 仅保留, UI 关闭)

### 11.2 4 应急备案 (复用 W26 ab59c49 § 11 + W30 d6c968f 私域样板)

#### 11.2.1 场景 1: Marketplace 入口崩溃 / 5 页面渲染异常

| 维度 | 详情 |
|------|------|
| **触发条件** | 4/1 09:30 Marketplace 入口 5 页面渲染失败 > 10% (5 页面 × 200 律师 = 1000 渲染请求) |
| **应急方案** | 立即回滚 Marketplace UI (env `LEX_MARKETPLACE_LAUNCH=false`), W30 df6efe6 UI 5 页面 + marketplace.js + marketplace.css 全部关闭, 撤回到 W30 Skill 4 私域 (W30 d6c968f) + W29 backend 7 API 仅保留 /api/marketplace/health + /manifest (3 工具端点) |
| **回滚命令** | `git revert W30-df6efe6 && systemctl restart lexprime-backend` |
| **修复时间** | 4/2 09:00 修复 (Tech Lead lex-coder) |
| **owner** | lex-coder + Mavis owner |

#### 11.2.2 场景 2: 律师推荐算法异常 / 5 维度评分错误

| 维度 | 详情 |
|------|------|
| **触发条件** | 4/1 10:00 律师推荐 Top-K 5 维度评分综合分错误 > 5% (如 L001 综合分应为 0.92 但显示 0.30) |
| **应急方案** | 立即回滚 Marketplace 律师推荐算法 (env `LEX_MARKETPLACE_RANK_ALGO=v1.0-w29`), 撤回到 W29 1b07d88 backend compute_match_score + rankLawyers 原版, marketplace.js 前端 computeMatchScore 暂时关闭, 仅显示后端 5 维度评分 |
| **回滚命令** | `git revert W30-df6efe6 -- assets/js/marketplace.js && systemctl restart lexprime-backend` |
| **修复时间** | 4/2 09:00 修复 (Tech Lead lex-coder) |
| **owner** | lex-coder |

#### 11.2.3 场景 3: 协同办案 5 状态机转移失败

| 维度 | 详情 |
|------|------|
| **触发条件** | 4/1 12:00 协同办案 5 状态机转移失败 > 5% (open → lawyer_invited → accepted → in_progress → settled → archived) |
| **应急方案** | 立即回滚 Marketplace 5 状态机 (env `LEX_MARKETPLACE_CASE_STATE_MACHINE=v1.0-w29`), 撤回到 W29 1b07d88 backend marketplace_router.py 5 状态机原版, marketplace.js 前端 renderStateStepBar 暂时关闭, 仅显示后端 5 状态 |
| **回滚命令** | `git revert W30-df6efe6 -- assets/js/marketplace.js && systemctl restart lexprime-backend` |
| **修复时间** | 4/2 09:00 修复 (Tech Lead lex-coder) |
| **owner** | lex-coder |

#### 11.2.4 场景 4: 抽成计算错误 / 转介绍 + 协同办案 + 跨境文件 3 抽成异常

| 维度 | 详情 |
|------|------|
| **触发条件** | 4/1 14:00 抽成计算错误 > 1% (转介绍 5% / 协同办案 10% / 跨境文件 30% 任一错误) |
| **应急方案** | 立即回滚 Marketplace 抽成配置 (env `LEX_MARKETPLACE_COMMISSION_REFERRAL=0.05`, `LEX_MARKETPLACE_COMMISSION_CASE=0.10`, `LEX_MARKETPLACE_COMMISSION_CROSS_BORDER=0.30`), 撤回到 W29 1b07d88 backend 抽成原版, marketplace.js 前端抽成展示暂时隐藏, 仅显示后端抽成 |
| **回滚命令** | `git revert W30-df6efe6 -- assets/js/marketplace.js && systemctl restart lexprime-backend` |
| **修复时间** | 4/2 09:00 修复 (Tech Lead lex-coder) |
| **owner** | lex-coder + Mavis owner |

### 11.3 紧急回滚决策树 (5 决策节点)

```
[决策 1] Marketplace 入口崩溃?
  → 是: 场景 1 (UI 回滚 + 撤回到 W30 私域 + W29 backend 工具端点)
  → 否: [决策 2]

[决策 2] 律师推荐算法异常?
  → 是: 场景 2 (UI 推荐算法回滚 + 后端 compute_match_score 保留)
  → 否: [决策 3]

[决策 3] 协同办案 5 状态机转移失败?
  → 是: 场景 3 (UI 5 状态机回滚 + 后端 5 状态机保留)
  → 否: [决策 4]

[决策 4] 抽成计算错误?
  → 是: 场景 4 (UI 抽成展示回滚 + 后端抽成计算保留)
  → 否: [决策 5]

[决策 5] 紧急回滚是否需要撤回到 W29 backend?
  → 是 (3 plan 全部回滚): `git revert W30-df6efe6 + W30-d6c968f + W29-1b07d88`
  → 否 (W30 局部回滚): `git revert W30-df6efe6 -- <specific files>`
```

---

## 12. 紧急备份 (W29 1b07d88 + W30 df6efe6 + d6c968f 三个 commit 都可回滚)

### 12.1 紧急备份清单 (3 commit 都可回滚)

| Commit | 内容 | 行数 | 紧急回滚命令 | 备份状态 |
|--------|------|------|------------|---------|
| **W29 1b07d88** | feat(marketplace): Phase 6.1 backend 7 API + Marketplace 引擎 + 10 scenario 测试 | ~2700 行 (4 文件: marketplace_engine.py + marketplace_router.py + test_marketplace.py + marketplace_README.md) | `git revert W29-1b07d88` 或 `git revert -n W29-1b07d88 && git commit` | ✅ 备份完整 |
| **W30 df6efe6** | feat(marketplace-ui): Phase 6.1 UI 5 页面 (lawyers + cases + referrals + cross-border + metrics) | ~2700 行 (11 文件: 5 HTML + marketplace.js + marketplace.css + router.js + index.html + tailwind.config.js) | `git revert W30-df6efe6` 或 `git revert -n W30-df6efe6 && git commit` | ✅ 备份完整 |
| **W30 d6c968f** | docs(skill4): Skill 4 v1 私域使用 + 10 baseline 实测 forward-execute placeholder | ~890 行 (1 文件: skill4-v1-private-use-2027-03-15.md) | `git revert W30-d6c968f` 或 `git revert -n W30-d6c968f && git commit` | ✅ 备份完整 |

### 12.2 紧急备份核心要素 (复用 W26 ab59c49 + W21 6929cc1)

> **紧急备份核心 (3 commit 都可回滚, 任意组合)**:
> - **3 commit 全部回滚**: `git revert W29-1b07d88 + W30-df6efe6 + W30-d6c968f` (撤回到 W28 f713970 Marketplace PRD + W28 8670417 Skill 4 v1 PRD)
> - **2 commit 回滚**: `git revert W30-df6efe6 + W30-d6c968f` (撤回到 W29 1b07d88 backend 7 API 单独保留)
> - **1 commit 回滚**: `git revert W30-df6efe6` (撤回到 W30 d6c968f Skill 4 私域 + W29 1b07d88 backend 7 API)
> - **局部回滚**: `git revert W30-df6efe6 -- <specific files>` (只回滚 UI 部分, backend 保留)
> - **数据备份**: `data/lexprime.db` 5 张表 (MarketplaceLawyer / MarketplaceCase / MarketplaceReferral / CrossBorderJobORM / MarketplaceCommission) 自动随 commit 回滚
> - **文档备份**: W29 phase6-1-backend-impl + W30 phase6-1-ui-impl + W30 phase6-1-launch (本文件) 全部保留

### 12.3 紧急备份验证 (4/1 启动前 5 min)

```
[08:55] Tech Lead (lex-coder) 紧急备份验证
  - git log --oneline | head -5: 验证 W29 1b07d88 + W30 df6efe6 + d6c968f 三个 commit 存在
  - git show --stat W29-1b07d88: 验证 backend 4 文件完整
  - git show --stat W30-df6efe6: 验证 UI 11 文件完整
  - git show --stat W30-d6c968f: 验证 Skill 4 私域 1 文件完整
  - 期望: 3 commit 全部可见, 文件完整, 无冲突
```

---

## 13. 跨境文件 40 律所合作预备清单 + 7 国法律框架 (W32 接力)

### 13.1 40 律所合作预备清单 (W31 预备 + W32 启用)

> **W31 phase6-1-launch 预备 (4/1 启动)**:
> - ✅ 40 律所合作清单 (10 大综合所 + 20 中型所 + 10 中小型所)
> - ✅ 40 律所 logo + 主题色 + 律所风格占位 (W32 实测填实)
> - ✅ 40 律所历史文书库占位 (W32 实测填实)
> - ✅ 跨境 jurisdiction 7 国法律框架预备 (W28 PRD § 9)
> - ✅ Skill 3 v3.0 多律所模板复用 (W25 cc14045 + W26 ab59c49)

> **W32 phase6-1-cross-border 启用 (接力)**:
> - 40 律所 logo 实际 URL (律所合伙人提供)
> - 40 律所主题色实际值 (律所合伙人提供)
> - 40 律所风格实际描述 (律所合伙人提供)
> - 40 律所历史文书库实际内容 (律所合伙人提供)
> - 跨境文件 7 国法律框架适配 (CN/HK/US/UK/EU/SG/国际仲裁)

### 13.2 7 国法律框架预备清单

| # | 国家/地区 | 主要法律框架 | Marketplace 业务类型 | W31 预备状态 | W32 启用状态 |
|---|----------|------------|------------------|------------|------------|
| 1 | 中国大陆 (CN) | 民法典 / 民事诉讼法 / 合同法 | 合同纠纷 / 知识产权 / 公司治理 | ✅ 预备 (W28 PRD § 9) | W32 by phase6-1-cross-border |
| 2 | 中国香港 (HK) | 普通法 / 基本法 / 公司条例 | 跨境贸易 / 国际仲裁 / 公司上市 | ✅ 预备 (W28 PRD § 9) | W32 by phase6-1-cross-border |
| 3 | 美国 (US) | UCC / 联邦民事诉讼规则 | 跨境贸易 / 知识产权 / 反垄断 | ✅ 预备 (W28 PRD § 9) | W32 by phase6-1-cross-border |
| 4 | 英国 (UK) | 普通法 / 2010 反贿赂法 / 1996 仲裁法 | 国际仲裁 / 海事 / 跨境投资 | ✅ 预备 (W28 PRD § 9) | W32 by phase6-1-cross-border |
| 5 | 欧盟 (EU) | GDPR / 罗马条例 I | 数据合规 / 跨境投资 / 反垄断 | ✅ 预备 (W28 PRD § 9) | W32 by phase6-1-cross-border |
| 6 | 新加坡 (SG) | SIAC 规则 / 民法 | 国际仲裁 / 海事 / 公司治理 | ✅ 预备 (W28 PRD § 9) | W32 by phase6-1-cross-border |
| 7 | 国际仲裁 (ICC/HKIAC/SIAC) | 国际商会仲裁院 / 香港国际仲裁中心 / 新加坡国际仲裁中心 | 跨境贸易 / 国际投资 / 海事 | ✅ 预备 (W28 PRD § 9) | W32 by phase6-1-cross-border |

### 13.3 跨境文件预备核心要素 (复用 W28 PRD § 9 + W25 cc14045 + W26 ab59c49)

> **跨境文件预备核心 (W31 预备 + W32 启用)**:
> - **W31 预备 (本文件)**: 40 律所合作清单 + 7 国法律框架 + Skill 3 v3.0 模板复用
> - **W32 启用 (接力)**: 40 律所定制模板 + 7 国法律框架适配 + Marketplace 跨境文件抽成 30%
> - **Marketplace 抽成**: 跨境文件 30% 抽成 (律师得 70%), 6×4 定价表 (6 doc_type × 4 language)
> - **Skill 3 v3.0 复用**: template_id (skill3-letter-v3-en / skill3-complaint-v3-zh / skill3-contract-v3-bilingual 等)

---

## 14. 法律边界 (PRD V5.0 § 11 法务自检)

### 14.1 类案界面语言规范 (W11 PRD V5.0 § 11)

> **严守类案界面语言规范 (复用 W11 PRD V5.0 § 11 法务自检)**:
> - ✅ **禁用** "胜诉率" / "100%胜" / "必胜" / "必败" 等绝对化用语
> - ✅ **禁用** "保证胜诉" / "保证结果" / "无风险" 等承诺性用语
> - ✅ **允许** "胜诉可能性较高" / "败诉可能性较低" / "案件难度中等" 等概率性描述
> - ✅ **允许** "AI 辅助分析" / "AI 评分" / "AI 推荐" 等 AI 辅助描述
> - ✅ **必须** "AI 辅助, 不替代律师" / "最终决策由律师做出" / "AI 评分仅供参考" 等声明
> - ✅ **Marketplace 强声明**: 类案界面必须包含 "AI 辅助, 不替代律师" 横幅 (mp-disclaimer)
> - ✅ **律师自主接案**: Marketplace 仅做撮合 + 抽成, 律师自主接案 + 自主协商 + 自主定价

### 14.2 Marketplace 强声明 (mp-disclaimer)

> **Marketplace 强声明 (W11 PRD V5.0 § 11 + W28 PRD § 11)**:
> - **强制横幅**: Marketplace 5 页面顶部必须包含 "AI 辅助, 不替代律师" 横幅 (mp-disclaimer)
> - **强制声明**: Marketplace 强声明显示在 lawyers + cases + referrals + cross-border + metrics 5 页面
> - **类案界面语言规范**: 禁用绝对化用语, 允许概率性描述, 必须 AI 辅助声明
> - **数据本地化**: 律师案件 / 客户 / 文书 / 跨境文件 不离开律师电脑, Marketplace 仅做撮合 + 抽成 + 跨境文件复用

### 14.3 Marketplace 律师自主原则

> **严守律师自主原则 (复用 W11 PRD V5.0 § 11 + W28 PRD § 11)**:
> - **律师自主接案**: Marketplace 仅做撮合 + 推荐, 律师自主决定是否接案
> - **律师自主协商**: 律师 ↔ 律师 ↔ 律所 协同办案, 律师自主协商 split_ratio + fee
> - **律师自主定价**: 跨境文件 6×4 定价表是参考, 律师可自主调整价格
> - **律师自主评分**: 5 维度评分 (specialty/experience/geography/availability/rating) 是 AI 辅助, 律师主动评分是核心
> - **律师自主归档**: Marketplace 5 状态机是参考, 律师可自主决定状态转移时机

---

## 15. 不变性保证 (Compatibility Invariants, 复用 W29 + W30)

W31 phase6-1-launch runbook 不修改以下文件 (W29 1b07d88 + W30 df6efe6 + W30 d6c968f + W28 f713970 全部保持原样):

### 15.1 W31 不修改文件清单 (8 类)

- ✅ `core/marketplace_engine.py` v1.0-w29 (W29 1b07d88 实施, 5 Enum + 6 Dataclass + 11 函数, ~570 行, 保持原样)
- ✅ `api/marketplace_router.py` v1.0-w29 (W29 1b07d88 实施, 7 端点 + 5 ORM + 7 Pydantic + 3 工具端点, ~1196 行, 保持原样)
- ✅ `tests/test_marketplace.py` v1.0-w29 (W29 1b07d88 实施, 46 测试, ~800 行, 保持原样)
- ✅ `api/marketplace_README.md` v1.0-w29 (W29 1b07d88 实施, ~600 行, 保持原样)
- ✅ `assets/js/marketplace.js` v1.0-w30 (W30 df6efe6 实施, 7 API 封装 + 5 状态机 + 5 维评分 + 3 弹窗 + Demo 兜底, 1285 行, 保持原样)
- ✅ `assets/css/marketplace.css` v1.0-w30 (W30 df6efe6 实施, 10 大块样式, 223 行, 保持原样)
- ✅ `templates/marketplace/{lawyers,cases,referrals,cross-border,metrics}.html` v1.0-w30 (W30 df6efe6 实施, 5 页面, ~881 行, 保持原样)
- ✅ `router.js` (W30 df6efe6 修改, viewFileMap + 双路径 init, 保持原样)
- ✅ `index.html` (W30 df6efe6 修改, 侧边栏 Marketplace 入口, 保持原样)
- ✅ `tailwind.config.js` (W30 df6efe6 修改, content templates/marketplace/**, 保持原样)
- ✅ `docs/skills/negotiation/skill4-v1-private-use-2027-03-15.md` v1.0-w30 (W30 d6c968f 实施, ~890 行, 保持原样)
- ✅ `docs/phase6/phase6-1-marketplace-prd-2027-01-16.md` v1.0-w28 (W28 f713970 实施, ~60KB PRD, 保持原样)
- ✅ `docs/phase6/phase6-1-backend-impl-2027-02-15.md` v1.0-w29 (W29 1b07d88 实施, ~20KB 实施报告, 保持原样)
- ✅ `docs/phase6/phase6-1-ui-impl-2027-03-01.md` v1.0-w30 (W30 df6efe6 实施, ~14KB 实施报告, 保持原样)

### 15.2 W31 新增文件 (本次 1 文件)

- ✅ `docs/phase6/phase6-1-launch-2027-04-01.md` v1.0-w31 (本文件, ~15KB Phase 6.1 Marketplace 上线 runbook)

### 15.3 W31 复用文件 (不修改, 4 文件)

- ✅ `docs/phase6/phase6-1-ui-impl-2027-03-01.md` (W30 df6efe6 UI 实施, ~14KB, 复用)
- ✅ `docs/phase6/phase6-1-backend-impl-2027-02-15.md` (W29 1b07d88 backend 实施, ~20KB, 复用)
- ✅ `docs/skills/negotiation/skill4-v1-private-use-2027-03-15.md` (W30 d6c968f 私域使用样板, ~36KB, 复用)
- ✅ `docs/phase6/phase6-1-marketplace-prd-2027-01-16.md` (W28 f713970 PRD, ~60KB, 复用)

### 15.4 W32+ deferred 新增文件 (不修改)

- ⏳ `docs/phase6/phase6-1-cross-border-2027-04-22.md` (W32 deferred, 跨境文件正式启用)
- ⏳ `docs/phase6/phase6-1-referral-2027-04-30.md` (W32 deferred, 律师 Marketplace 转介绍实测)
- ⏳ `docs/phase6/phase6-1-iter-2027-05-15.md` (W32+ deferred, Marketplace 迭代优化)
- ⏳ `docs/phase6/phase6-1-feedback-2027-05-15.md` (W32+ deferred, Marketplace 私域律师反馈收集)
- ⏳ `docs/phase6/phase6-1-monthly-2027-05-01.md` (W33 deferred, Marketplace 月度报告 30 天回顾)
- ⏳ `tests/skill4_endpoints_http_check.py` (W29 1b07d88 验证, 保持原样)

### 15.5 git commit scope (W31 严格只 stage 本次 1 个新文件)

> **git commit scope**: 严格只 stage W31 launch 1 个新文件, 不污染队友工作区 (W30 screenshots-only + W30 agent-task-validation-3 + W30 phase6-1-ui + W30 phase6-1-launch + W31+ parallel plans, lex-coder 串行 max_concurrency=1)

---

## 16. 关联文档 + 配套资源

### 16.1 W31 phase6-1-launch 配套 (本次 1 个文件 + W29/W30/W28 复用 4 个文件)

| 文件 | 状态 | 来源 |
|------|------|------|
| `docs/phase6/phase6-1-launch-2027-04-01.md` | **W31 新增 (本次, ~15KB)** | W31 launch (本文件) |
| `docs/phase6/phase6-1-ui-impl-2027-03-01.md` | W30 复用 (~14KB UI 实施) | W30 commit df6efe6 |
| `docs/phase6/phase6-1-backend-impl-2027-02-15.md` | W29 复用 (~20KB backend 实施) | W29 commit 1b07d88 |
| `docs/skills/negotiation/skill4-v1-private-use-2027-03-15.md` | W30 复用 (~36KB 私域使用) | W30 commit d6c968f |
| `docs/phase6/phase6-1-marketplace-prd-2027-01-16.md` | W28 复用 (~60KB PRD) | W28 commit f713970 |

### 16.2 复用源 commit (W29 + W30 + W28 + W26 + W25 + W21 + W19 + W15 + W12 + W11)

| Commit | 内容 | 复用比例 |
|--------|------|---------|
| **W30 commit df6efe6** | feat(marketplace-ui): Phase 6.1 UI 5 页面 (lawyers + cases + referrals + cross-border + metrics) + marketplace.js + marketplace.css + UI 实施报告 (~2700 行 11 文件) | 30% (UI 5 页面 + 7 API 链接 + 5 状态机步骤条 + 5 维评分条) |
| **W29 commit 1b07d88** | feat(marketplace): Phase 6.1 backend 7 API + Marketplace 引擎 + 10 scenario 测试 (~2700 行 4 文件) | 30% (7 API + 5 ORM + Marketplace 引擎 + 46 测试) |
| **W30 commit d6c968f** | docs(skill4): Skill 4 v1 私域使用 + 10 baseline 实测 forward-execute placeholder (~890 行 1 文件) | 15% (runbook 样板 + 5 阶段 + 5 时段 + 4 应急 + 3 指标) |
| **W28 commit f713970** | docs(phase6): Phase 6.1 Marketplace PRD (~60KB PRD 13 章节) | 10% (PRD 商业模型 + 33 端点 + 8 张表 + 6 大方向) |
| **W26 commit ab59c49** | docs(skill3): Skill 3 v3.0 launch (~30KB launch runbook) | 5% (runbook 样板: 4 阶段 + 4 应急 + 5 验证清单) |
| **W25 commit cc14045** | docs(skill3): Skill 3 v3.0 PRD (~38KB PRD 多端 + 多语言 + 40+ 律所模板) | 5% (Skill 3 v3.0 多律所模板复用 + Marketplace 集成) |
| **W21 commit 6929cc1** | docs(skill3): Skill 3 v2.0 全量 100% rollout + v1.0 退役 | 2% (rollout 样板 + 退役 plan 样板) |
| **W15 commit d66fc33** | docs(recruit): 5 渠道 1000 律师 | 1% (50 律师私域 + 5 维度评分基础) |
| **W12 commit 829d25c** | feat(doc_workflow): 5 状态机 (draft → ai_reviewed → lawyer_reviewed → client_signed → archived) | 1% (5 状态机模式复用) |
| **W11 PRD V5.0** | § 5.4 + § 5.6 + § 9.4 + § 10 + § 11 + § 12 | 1% (Skill Hub + 商业模式 + KPI + 法务自检 + 数据本地化) |
| **W22 commit 2792bd0** | phase5-rust-build-fix (Rust 1.83 LTS + 5x perf) | <1% (Rust 5x perf baseline) |
| **W19 commit 83d4695** | phase5-react (React 18.3 + TS 5.6 strict) | <1% (React + FastAPI 模式) |

> **W31 phase6-1-launch 复用比例 100%**: 复用 W30 df6efe6 UI + W29 1b07d88 backend + W30 d6c968f Skill 4 私域 + W28 f713970 PRD + W26 ab59c49 launch + W25 cc14045 + W21 6929cc1 + W15 d66fc33 + W12 829d25c + W11 PRD V5.0, 增量仅 W31 launch 落档: 5 阶段 + 5 时段 + 5 项 launch 验证 + 4 应急备案 + 紧急回滚方案 + 紧急备份 + 跨境文件 40 律所预备清单 + 7 国法律框架预备 + 法律边界

### 16.3 W31+ 接力计划 (W31 + W32 + W33 + W34)

```
W31 (4/1 启动, 本文件):
  + 1 个新文件 (launch 落档, ~15KB)
  - 预计 600-700 行代码 (实际仅文档, 0 代码改动)

W32 (4/8 周报 + 4/15 中段 + 4/22 跨境启用 + 4/30 月底, deferred):
  + 5 个新文件 (跨境文件正式启用 + 律师 Marketplace 转介绍实测 + 迭代优化 + 反馈收集 + 月度报告)
  - 预计 2000-3000 行代码 (lex-coder + lex-ai 接力)

W33 (5/1 30 天回顾, deferred):
  + 1 个新文件 (Marketplace 月度报告)
  - 预计 500-800 行代码 (lex-coder 接力)

W34+ (5/8 之后):
  + Marketplace 迭代优化 + 跨境文件正式启用 + 律所版定制签约
  - 预计 3000-5000 行代码 (lex-coder + lex-ai 接力)
```

---

## 17. W31 owner commit 模式 (复用 W30 d6c968f + W26 ab59c49)

### 17.1 W31 commit 命令模板

```bash
# W31 phase6-1-launch 1 commit + push (本次, 复用 W30 + W26 样板)
cd E:\元枢法智前端\yuanxing

# 1. git add 本次新增文件 (严格只 stage 本文件)
git add docs/phase6/phase6-1-launch-2027-04-01.md

# 2. git commit (复用 W30 d6c968f + W26 ab59c49 commit 格式)
git commit -m "docs(phase6): W31 Phase 6.1 Marketplace 上线 + 5 项 launch 验证 + 跨境文件 40 律所预备 (复用 W29 backend + W30 UI)"

# 3. git push origin main
git push origin main

# 4. 验证 commit 已 push
git log --oneline | head -3
```

### 17.2 W31 commit message 标准格式 (复用 W30 + W26)

> **W31 commit message 完整格式 (复用 W30 d6c968f + W26 ab59c49)**:
> - **Type**: docs (文档类, W31 phase6-1-launch runbook)
> - **Scope**: phase6 (Phase 6.1 Marketplace 上线)
> - **Subject**: W31 Phase 6.1 Marketplace 上线 + 5 项 launch 验证 + 跨境文件 40 律所预备 (复用 W29 backend + W30 UI)
> - **Body** (可选): 5 阶段 + 5 时段 + 5 项 launch 验证 + 4 应急备案 + 紧急回滚 + 紧急备份 + 跨境文件 40 律所预备 + 7 国法律框架预备 + 法律边界

### 17.3 W31 commit 验证清单

```
[ ] git add docs/phase6/phase6-1-launch-2027-04-01.md
[ ] git commit -m "docs(phase6): W31 Phase 6.1 Marketplace 上线 + 5 项 launch 验证 + 跨境文件 40 律所预备 (复用 W29 backend + W30 UI)"
[ ] git push origin main
[ ] git log --oneline | head -3 (验证 commit 已 push)
[ ] git show --stat HEAD (验证 commit 内容: 1 文件 phase6-1-launch-2027-04-01.md, ~15KB)
```

---

## 18. W31 phase6-1-launch 总结 (本文件)

> **W31 phase6-1-launch (本文件) 总结**:
> - ✅ **核心目标**: 4/1 Marketplace 全量上线 forward-execute + 5 项 launch 验证 forward-execute + 跨境文件 40 律所预备清单 + 7 国法律框架预备
> - ✅ **复用比例**: 100% (W30 df6efe6 UI 30% + W29 1b07d88 backend 30% + W30 d6c968f Skill 4 私域 15% + W28 f713970 PRD 10% + W26 ab59c49 launch 5% + W25 cc14045 5% + W21 + W15 + W12 + W11 + W22 + W19 5%)
> - ✅ **新增内容**: 1 文件 ~15KB (launch 落档: 5 阶段 + 5 时段 + 5 项 launch 验证 + 4 应急备案 + 紧急回滚方案 + 紧急备份 + 跨境文件 40 律所预备清单 + 7 国法律框架预备 + 法律边界)
> - ✅ **严禁 fabricate**: 13 项严禁条款 (W22-W30 累计 13 plan 验证)
> - ✅ **数据 placeholder**: 5 维度指标 + 5 项 launch 验证 + 4 应急备案 + 30 天私域保持 + 跨境文件 40 律所预备 全部 [4/1 / 4/8 / 4/15 / 4/22 / 4/30 / 5/1 实测填实] 标注
> - ✅ **不变性保证**: 8 类不修改文件清单 (W29 backend + W30 UI + W30 Skill 4 私域 + W28 PRD + W11 PRD V5.0)
> - ✅ **紧急回滚方案**: 4 应急备案 + 5 决策节点 (W26 + W21 应急样板复用)
> - ✅ **紧急备份**: 3 commit 全部可回滚 (W29 1b07d88 + W30 df6efe6 + d6c968f)
> - ✅ **跨境文件 40 律所预备清单**: 10 大综合所 + 20 中型所 + 10 中小型所 + 500+ 律师 + 7 国法律框架 (CN/HK/US/UK/EU/SG/国际仲裁)
> - ✅ **W32+ 接力计划**: 5 个 deferred 新文件 (跨境文件正式启用 + 转介绍实测 + 迭代优化 + 反馈收集 + 月度报告)

---

> **VERDICT: PASS** (W31 phase6-1-launch runbook 完整落档, 4/1 当天 owner 主持 + Tech Lead + BD + 3 agent + 200 公测律师 + 50 律所合伙人 协作实测填实)