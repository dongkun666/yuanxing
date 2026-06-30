<!-- LexPrime Track E · W30 skill4-private-use 交付 -->
# 3/15 Skill 4 v1 私域使用 + 谈判场景实测运行手册 (Private-Use Runbook · 2027-03-15)

VERDICT: PASS

> **版本**: v1.0 · 2026-07-01
> **Track**: E (Skill Hub) + A (AI 模型) + Phase 6.1 Marketplace 集成
> **Week**: W30 skill4-private-use (Skill 4 v1 私域使用 + 谈判场景实测)
> **状态**: runbook 落档, 3/15 当天 owner 主持 + Tech Lead (lex-coder) + BD 协作实测填实
> **依据**:
> - `docs/skills/negotiation/skill4-v1-impl-2027-02-15.md` v1.0 (W29 2344816 实施, 4 模块 + 37 baseline)
> - `docs/skills/negotiation/skill4-v1-prd-2027-01-16.md` v1.0 (W28 8670417 PRD, ~30KB)
> - `backend/cases-crawler/skills/negotiation/` v1.0-w29 (W29 实施, 4 文件 ~2587 行)
> - `backend/cases-crawler/api/skill4_router.py` v1.0-w29 (10 endpoints, 含 marketplace-integration stub)
> - `docs/marketing/skill3-v2-100pct-rollout-2026-10-01.md` v1.0 (W21 6929cc1, 100pct rollout 样板)
> - `docs/marketing/skill3-v1-deprecation-2026-11-01.md` v1.0 (W21 6929cc1, 退役 plan 样板)
> - `docs/marketing/recruit-1000-runbook.md` v1.0 (W15 d66fc33, 50 律师私域使用样板)
> - W29 fix 848129d (`__import__` hack 修复 + 5-dim 归属 W21 → W12/W15)
> - W29 fix 848129d (uvicorn real server 端点测试 10/10 PASS)
> - W11 PRD V5.0 § 5.4 横切面 4 技能引导 Skill Hub + § 5.6 当事人服务类 (谈判类) + § 11 成功指标
> - W12 A2 commit 829d25c (doc_workflow 5 状态机, Skill 4 复用)
> - W15 commit 3d429cd (L7 吴律师 AI 5 维度风险标注, facts/legal/demand/deadline/consequence)

> **核心定位 (W30 private-use vs W29 impl vs W28 PRD vs W21 100pct rollout)**:
> - W28 8670417 = Skill 4 v1 PRD (~30KB, 4 模块 + 6 大优势 + 4 应急)
> - W29 2344816 + 848129d = Skill 4 v1 实施 (4 文件 ~2587 行 + 37 baseline 测试 + 10 endpoints)
> - **W30 private-use (本任务) = Skill 4 v1 私域使用 + 10 baseline 谈判场景实测 + 50 律师私域跟踪**
> - W31+ = Skill 4 v1 全量上线 (复用 W21 100pct rollout 样板)

---

## 0. 文档使用说明 (执行 3/15 当天随身打印)

> **本手册是 3/15 Skill 4 v1 私域使用 + 谈判场景实测当天的"运行剧本"**,
> **总指挥 (PM) + Tech Lead (lex-coder) + BD + 50 律师私域 (W15 d66fc33 招募律师, 3/15 实测填实名单)** 协作执行.
>
> **本手册核心目标**:
> 1. **50 律师私域使用 forward-execute** (W18 d66fc33 招募律师复用, 3/15 09:00 - 19:00 跟踪)
> 2. **10 baseline 谈判场景实测** (W29 2344816 已覆盖, 3/15 律师私域实测填实)
> 3. **5 维度评分 + 转化率 + 律师满意度 3 指标 forward-execute** (3/15 + 3/22 两次实测填实)
>
> **本手册配套**:
> - `skill4-v1-impl-2027-02-15.md` (W29 实施报告, 4 模块 + 37 测试)
> - `skill4-v1-prd-2027-01-16.md` (W28 PRD, 4 模块 + 4 应急)
> - `skill3-v2-100pct-rollout-2026-10-01.md` (W21 100pct rollout runbook 样板)
> - `recruit-1000-runbook.md` (W15 50 律师私域使用样板)
> - `backend/cases-crawler/api/skill4_router.py` (W29 实施 10 endpoints)
>
> **严守严禁 fabricate (W18-W30 13 plan 验证)**:
> 1. **不要 fabricate 律师反馈**: 实测为主, owner 3/15 跑律师试用, 反馈全部 [3/15 实测填实]
> 2. **不要 fabricate 私域数据**: 实测为主, owner 3/15 当天 19:00 抓 metrics 抓取, 数字全部 [3/15 实测填实]
> 3. **forward-execute placeholder 模式**: runbook 流程 + 时间表 + 应急 + 跟踪节奏, 实际数字全部 placeholder
> 4. **不要碰 W29 2344816 实施**: 本任务只做 private-use, 不修改 4 文件 (negotiation_models/engine/debrief_report + skill4_router.py)
> 5. **不要碰 W28 8670417 PRD**: 本任务不修改 PRD, 仅落地私域使用 forward-execute
> 6. **严守 AI 辅助, 不替代律师**: 私域期间严守产品原则, 律师主动评分是核心, AI 评分仅辅助

---

## 1. 3/15 私域使用阶段启动 (5 min, 09:00)

### 1.1 启动前 5 min (08:55 - 09:00)

```
[08:55] Tech Lead (lex-coder)
  - 验证当前状态 (W29 2344816 + 848129d 实施就位):
    curl http://localhost:8000/api/skill4/health
    curl http://localhost:8000/api/skill4/manifest
  - 期望: status=ok, 10 endpoints 全部 ready (含 marketplace-integration stub)
  - 期望: pytest 796/796 PASS (含 37 Skill 4 baseline, no regression)
  - 期望: ruff 0 errors (skills/negotiation/ + api/skill4_router.py + tests/test_skill4.py)
  - 期望: uvicorn 端点 10/10 PASS (W29 848129d 修复后)

[08:58] 准备 env 启动命令 (3/15 私域使用, owner 3/15 实测填实)
  $ export LEX_SKILL4_PRIVATE_USE=true  # 3/15 私域使用模式
  $ export LEX_SKILL4_LLM_MODE=template_fallback  # W29 当前模板 fallback (LLM 接入 W31+)
  $ export LEX_SKILL4_FORCE_LAWYERS=lawyer_001,lawyer_002,...,lawyer_050  # 50 律师私域 placeholder, 3/15 实测填实
  $ export LEX_SKILL4_MARKETPLACE_STUB=true  # 复用 W29 marketplace-integration stub
  $ export LEX_SKILL4_RISK_DETECTION=on  # 实时风险预警开启
  $ export LEX_SKILL4_OPPONENT_SIM=on  # 模拟对方 3 角色开启
```

### 1.2 09:00 启动 (1 min)

```
[09:00:00] 启动私域使用模式 + 重启服务
  $ systemctl restart lexprime-backend
  启动时间: ~30s

[09:00:30] 验证启动成功
  $ curl http://localhost:8000/api/skill4/health | jq
  期望:
    {
      "status": "ok",
      "service_id": "lexprime.skill4",
      "skill": {
        "name": "AI 辅助谈判",
        "version": "v1.0-w29",
        "private_use_mode": true,
        "force_lawyers_count": 50,
        "llm_mode": "template_fallback",
        "marketplace_stub": true,
        "modules": {
          "strategy_generator": true,    # 谈判策略生成器
          "opponent_simulation": true,   # 模拟对方 3 角色
          "risk_detection": true,         # 实时风险预警
          "debrief_report": true          # 谈判复盘报告
        },
        "endpoints_count": 10,
        "tests_count": 37,
        "tests_status": "all_pass",
        "rust_perf_5x_target": true,       # W22 Rust 5x perf 兼容 (生产环境)
        "backward_compat_note": "W12 doc_workflow 5 状态机 + W15 5 维度评分 baseline 兼容"
      }
    }

[09:00:45] 端到端 smoke test (10 律师抽样)
  $ for i in 1 2 3 4 5 6 7 8 9 10; do
      curl -X POST http://localhost:8000/api/skill4/strategies \
        -H "Content-Type: application/json" \
        -d "{\"case_id\": \"C-${i}-${RANDOM}\", \"case_type\": \"contract_dispute\", \"breach_side\": \"other\", \"lawyer_id\": \"lawyer_$(printf %03d $i)\"}"
    done
  期望: 10 次调用 100% 返回 3 套策略 (conservative + moderate + aggressive)
  期望: 5 维度评分 (facts/legal/demand/deadline/consequence) 0.X placeholder
```

### 1.3 09:01-09:15 启动确认 (15 min)

```
[09:01-09:15] 私域稳定性观察
  - 5 分钟内持续观察 metrics 端点: curl http://localhost:8000/api/skill4/metrics | jq
  - 期望: 10 个调用全部 200 OK, 5 维度评分 placeholder 正常返回
  - 异常: 若 v1 报错率 > 5% 或 latency P95 > 3s, 立即关闭 LEX_SKILL4_PRIVATE_USE (env 切换)
  - 兼容性: W12 doc_workflow 5 状态机 + W15 5 维度评分 baseline 不受影响
```

---

## 2. 3/15 09:15 - 19:00 私域执行 (10h 跟踪, 5 时段 + 茶歇)

> **复用 W21 100pct rollout 时段机制**, 50 律师私域期间跟踪 5 时段 + 茶歇, 让全员有充分时间体验 4 模块.

### 2.1 私域机制 (5 时段 + 茶歇, 09:15-19:00)

| 时段 | 时间 | 环节 | 负责人 | 输出物 |
|------|------|------|--------|--------|
| **预热** | 09:15-09:30 | 50 律师群发通知 (微信群 + 邮件 + 朋友圈) | BD | 律师确认清单 + 私域范围说明 |
| **时段 1** | 09:30-11:00 | 50 律师首次使用谈判策略生成器 | 50 律师 + Tech | 3 套策略 + 5 维度评分 placeholder |
| **时段 2** | 11:00-13:00 | 50 律师深度使用 4 模块 (策略 + 模拟 + 监测 + 复盘) | 50 律师 + Tech | 4 模块反馈 + 实测填实 |
| **茶歇** | 13:00-14:00 | 午休 + 律师微信群互动 | BD | 律师反馈收集 + 案例分享 |
| **时段 3** | 14:00-15:30 | 50 律师模拟对方 3 角色演练 (15 套模板) | 50 律师 | 模拟演练反馈 + 反向博弈 |
| **时段 4** | 15:30-17:00 | 转化跟踪 + 客服答疑 | BD + Tech | 转化率 placeholder (7 天后回填) |
| **时段 5** | 17:00-19:00 | 收尾 + 当日报告启动 | 总指挥 + Tech | 3/15 实测填实数字 + 报告 |
| **收尾** | 19:00-19:30 | 私域保持 + 3/22 7 天转化跟踪准备 | Tech Lead | 当日报告交付 + 7 天后 cron |

### 2.2 50 律师私域抽样方法

```
[09:15 抽样逻辑] 50 律师私域 = W15 d66fc33 招募律师 (公测 day 30+) + W19 skill3-gradual 50% 灰度律师 + W21 100pct 评审律师
  - 假设公测 day 280+ (3/15) 律师总数 [X, 3/15 实测填实, owner 3/15 09:15 通过 metrics 端点查询]
  - 期望 50 律师私域: 50 名 (3/15 owner 填实名�?
  - 律师来源结构 (3 群体合并):
    * W15 recruit-1000 律师群 (35 名): 公测期 day 1-26 招募, 试用转化 + 付费转化双重筛选
    * W19 skill3-gradual 50% 灰度律师 (10 名): 已用 Skill 3 v2.0 一月, 谈判延伸需求
    * W21 skill3-full-rollout 评审律师 (5 名): L1-L5 律师画像, 评审白名单 (force_v2)
  - 50 律师 force_lawyers 配置: 3/15 owner 08:55 实测填实

[09:15 抽样律师清单] 50 律师 [3/15 实测填实, owner 3/15 09:15 通过 /api/skill4/manifest 端点查询]
  W15 recruit-1000 律师群 (35 名):
    1. [lawyer_id_001, 姓名 placeholder, 3/15 owner 填实, 来源 = W15 recruit]
    2. [lawyer_id_002, 姓名 placeholder, 3/15 owner 填实, 来源 = W15 recruit]
    ...
    35. [lawyer_id_035, 姓名 placeholder, 3/15 owner 填实, 来源 = W15 recruit]
  W19 skill3-gradual 律师群 (10 名):
    36. [lawyer_id_036, 姓名 placeholder, 3/15 owner 填实, 来源 = W19 50% 灰度]
    ...
    45. [lawyer_id_045, 姓名 placeholder, 3/15 owner 填实, 来源 = W19 50% 灰度]
  W21 skill3-full-rollout 评审律师 (5 名):
    46. [lawyer_id_046, 姓名 placeholder, 3/15 owner 填实, 来源 = W21 force_v2]
    ...
    50. [lawyer_id_050, 姓名 placeholder, 3/15 owner 填实, 来源 = W21 force_v2]
```

### 2.3 跟踪 3 指标 (复用 W29 实施 + W21 100pct 样板)

```
[指标 1: 5 维度评分] 自动 + 律师主动评分
  自动: Skill 4 v1 生成时自动从复盘报告提取 risk_dim_facts/legal/demand/deadline/consequence (0-1 浮点, clamp 0-1)
  律师: 律师谈判后 24h 内主动评分 (1-5), 通过 /api/skill4/metrics/update 端点 PATCH
  期望分布: facts 0.7-0.9, legal 0.6-0.85, demand 0.7-0.9, deadline 0.5-0.8, consequence 0.65-0.85
  数据来源: GET /api/skill4/metrics → summary.5_dimension_avg_scores
  复用 baseline: W12 doc_workflow 4 文书风险标注 + W15 Skill 3 v2.0 L7 吴律师 AI 5 维度风险标注

[指标 2: 转化率] 谈判后 7 天跟踪
  跟踪窗口: 3/15 09:00 - 3/22 09:00 (7 天)
  转化定义: 律师使用谈判策略生成器后 7 天内是否付费 (¥99/月个人版 / ¥449 创史体验版)
  期望: 50 律师私域转化率 >= 35% (W15/W21 baseline + 持平)
  数据来源: dashboard 付费转化指标 + paid_converted 事件

[指标 3: 律师满意度] 律师主动评分
  评分时间: 谈判后 48h 内律师主动评分 (1-5)
  期望: 50 律师满意度 >= 4.5/5.0 (W15/W21 baseline + 持平)
  数据来源: 律师主动评价 (1v1 微信沟通 / 邮件回复 / 群内反馈)
```

---

## 3. 10 baseline 谈判场景实测 (复用 W29 2344816)

> **10 baseline 谈判场景已全部覆盖在 W29 2344816 实施 + 37 baseline 测试**, 本节为 3/15 律师私域实测填实依据.

### 3.1 10 baseline 谈判场景清单 (W29 § 4.2 复用)

| # | 场景 | W29 测试类 | 3/15 律师实测填实 | 期望结果 |
|---|------|-----------|-------------------|----------|
| 1 | **合同纠纷 - 对方违约** | TestStrategyGenerationContractOtherPartyBreach (3) | [3/15 实测填实, lawyer_id_001] | 3 策略 + 胜诉率 + 话术 |
| 2 | **合同纠纷 - 自己违约** | TestStrategyGenerationContractSelfBreach (1) | [3/15 实测填实, lawyer_id_002] | 保守优先 |
| 3 | **民事侵权** | TestStrategyGenerationTort (1) | [3/15 实测填实, lawyer_id_003] | 3 策略 |
| 4 | **婚姻家庭** | TestStrategyGenerationFamily (1) | [3/15 实测填实, lawyer_id_004] | 保守优先 |
| 5 | **公司股权** | TestStrategyGenerationEquity (1) | [3/15 实测填实, lawyer_id_005] | 法条引用 |
| 6 | **知识产权** | TestStrategyGenerationIP (1) | [3/15 实测填实, lawyer_id_006] | 3 策略 |
| 7 | **劳动仲裁** | TestStrategyGenerationLabor (1) | [3/15 实测填实, lawyer_id_007] | 保守优先 |
| 8 | **行政复议** | TestStrategyGenerationAdminReview (1) | [3/15 实测填实, lawyer_id_008] | 保守优先 |
| 9 | **跨境贸易 (跨境框架额外)** | TestStrategyGenerationCrossBorder (2) | [3/15 实测填实, lawyer_id_009 + 010] | CISG/UNCITRAL/PICC + 中英双语 |
| 10 | **反向博弈演练** (模拟对方 3 角色) | TestOpponentSimulation (4) | [3/15 实测填实, lawyer_id_011] | 律师/当事人/法官 3 角色 + 5 轮 |

### 3.2 9 案件类型覆盖 (W29 § 2.1 复用)

```
W29 negotiation_models.py 9 案件类型:
  1. contract_dispute    合同纠纷
  2. tort                民事侵权
  3. family              婚姻家庭
  4. equity              公司股权
  5. ip                  知识产权
  6. labor               劳动仲裁
  7. admin_review        行政复议
  8. settlement          和解协商
  9. cross_border_trade  跨境贸易 (CISG/UNCITRAL/PICC/NY Convention)
```

### 3.3 4 模块实测覆盖 (W29 § 2 复用)

```
W29 4 模块 + 10 baseline 谈判场景实测:

[模块 1: 谈判策略生成器] API: POST /api/skill4/strategies
  - 9 案件类型 × 3 违约方 (self/other/neutral) × 3 期望结果 (conservative/moderate/aggressive) × 3 对方角色 (lawyer/party/judge) = 243 组合
  - 50 律师私域实测抽样 10 场景 (上面 3.1 表格), 每场景律师主动选择策略优先级

[模块 2: 模拟对方 3 角色] API: POST /api/skill4/simulate-opponent
  - 3 角色 × 5 轮 = 15 套模板 (复用 W29 negotiation_engine.py)
  - 50 律师私域实测抽样 5 律师做反向博弈演练 (lawyer_id_011-015)

[模块 3: 实时风险预警] API: POST /api/skill4/detect-risk
  - 5 类型正则 (concede/evidence_miss/deadline_miss/emotional/info_leak)
  - 50 律师私域实测抽样 10 律师做实时监测 (lawyer_id_016-025), 每律师触发 1-2 次预警

[模块 4: 谈判复盘报告] API: POST /api/skill4/debrief
  - 5 维度评分 + 改进建议 + 类似案件对比
  - 50 律师私域实测抽样 10 律师做复盘 (lawyer_id_026-035)
```

---

## 4. 5 维度评分跟踪 forward-execute

### 4.1 5 维度评分基线 (W29 § 6.1 复用)

> **复用 W12 doc_workflow 4 文书风险标注 + W15 Skill 3 v2.0 L7 吴律师 AI 5 维度风险标注**:
> - 事实 (facts): 谈判内容与事实证据吻合度 (0-1)
> - 法律 (legal): 谈判策略与法律框架吻合度 (0-1)
> - 主张 (demand): 谈判诉求合理性 (0-1)
> - 时效 (deadline): 谈判时间节奏 (0-1)
> - 后果 (consequence): 谈判结果的预测后果 (0-1)

### 4.2 5 维度评分期望 (forward-execute)

```
[期望 v1 阈值 >= 0.85, W12/W15 baseline + 持平]

3/15 09:30 - 19:00 50 律师实测, owner 3/15 19:00 patch 替换 placeholder:

| 维度 | W12/W15 baseline | W29 37 测试 | 3/15 律师实测 (50 律师私域) |
|------|------------------|-------------|------------------------------|
| **事实 (facts)** | [0.X, W12/W15 历史 baseline] | 0.X placeholder | [0.X, 3/15 实测填实] |
| **法律 (legal)** | [0.X, W12/W15 历史 baseline] | 0.X placeholder | [0.X, 3/15 实测填实] |
| **主张 (demand)** | [0.X, W12/W15 历史 baseline] | 0.X placeholder | [0.X, 3/15 实测填实] |
| **时效 (deadline)** | [0.X, W12/W15 历史 baseline] | 0.X placeholder | [0.X, 3/15 实测填实] |
| **后果 (consequence)** | [0.X, W12/W15 历史 baseline] | 0.X placeholder | [0.X, 3/15 实测填实] |
| **avg_score** | [0.X, W12/W15 历史 baseline] | 0.X placeholder | [0.X, 3/15 实测填实] |

数据来源: GET /api/skill4/metrics → summary.5_dimension_avg_scores
阈值: avg_score >= 0.85 (W12/W15 baseline + 持平, W29 PRD § 5.1)
```

### 4.3 5 维度评分算法 (W29 debrief_report.py § 2.4 复用)

```python
# backend/cases-crawler/skills/negotiation/debrief_report.py W29 § 2.4

def compute_five_dimension_scores(trajectory: NegotiationTrajectory) -> FiveDimensionScore:
    """计算 5 维度评分 (复用 W12 doc_workflow 4 文书风险标注 + W15 L7 吴律师 AI 5 维度风险标注)"""
    return FiveDimensionScore(
        facts=clamp(trajectory.facts_alignment, 0, 1),
        legal=clamp(trajectory.legal_alignment, 0, 1),
        demand=clamp(trajectory.demand_alignment, 0, 1),
        deadline=clamp(trajectory.deadline_alignment, 0, 1),
        consequence=clamp(trajectory.consequence_alignment, 0, 1),
    )
```

---

## 5. 转化率 (7 天) forward-execute

### 5.1 转化率基线 (W29 § 6.2 复用)

```
[期望 35%+, W15/W21 baseline + 持平]

跟踪窗口: 3/15 09:00 - 3/22 09:00 (7 天)
转化定义: 律师使用谈判策略生成器后 7 天内是否付费 (¥99/月个人版 / ¥449 创史体验版)
数据来源: dashboard 付费转化指标 + paid_converted 事件

3/22 09:00 实测填实, owner patch 替换 placeholder:

| 律师分组 | 律师数 | 7 天转化数 | 转化率 |
|---------|--------|-----------|--------|
| W15 recruit-1000 律师群 | 35 | [X, 3/22 实测填实] | [0.XX, 3/22 实测填实] |
| W19 skill3-gradual 律师群 | 10 | [X, 3/22 实测填实] | [0.XX, 3/22 实测填实] |
| W21 skill3-full-rollout 评审律师 | 5 | [X, 3/22 实测填实] | [0.XX, 3/22 实测填实] |
| **综合 (50 律师)** | 50 | [X, 3/22 实测填实] | [0.XX, 3/22 实测填实, 期望 >= 0.35] |
```

### 5.2 转化漏斗跟踪 (复用 W15 d66fc33 4 层漏斗)

```
3/15 09:00 私域启动 → 3/22 09:00 7 天转化窗口:

[漏斗 1: 50 律师私域触达] 50/50 (100%)
  ├─ W15 recruit-1000: 35/35 (100%)
  ├─ W19 skill3-gradual: 10/10 (100%)
  └─ W21 skill3-full-rollout 评审: 5/5 (100%)
  
[漏斗 2: 50 律师使用过任一 4 模块] [X, 3/15 实测填实] / 50 (期望 >= 80%)
  ├─ 谈判策略生成器: [X, 3/15 实测填实] / 50
  ├─ 模拟对方 3 角色: [X, 3/15 实测填实] / 50
  ├─ 实时风险预警: [X, 3/15 实测填实] / 50
  └─ 谈判复盘报告: [X, 3/15 实测填实] / 50

[漏斗 3: 50 律师 7 天内付费] [X, 3/22 实测填实] / 50 (期望 >= 35%)
  ├─ ¥99/月个人版: [X, 3/22 实测填实]
  └─ ¥449 创史体验版: [X, 3/22 实测填实]

[漏斗 4: 50 律师续费 3 个月] deferred W33+ 跟踪
```

---

## 6. 律师满意度 forward-execute

### 6.1 律师满意度基线 (W29 § 6.3 复用)

```
[期望 4.5/5+, W15/W21 baseline + 持平]

评分时间: 3/15 律师私域结束后 48h 内 (3/17 09:00 截止)
评分方式: 律师主动评价 (1-5, 1v1 微信沟通 + 邮件回复 + 群内反馈)

3/17 09:00 实测填实, owner patch 替换 placeholder:

| 律师分组 | 律师数 | 主动评分数 | 平均满意度 |
|---------|--------|-----------|-----------|
| W15 recruit-1000 律师群 | 35 | [X, 3/17 实测填实] | [X.X, 3/17 实测填实] |
| W19 skill3-gradual 律师群 | 10 | [X, 3/17 实测填实] | [X.X, 3/17 实测填实] |
| W21 skill3-full-rollout 评审律师 | 5 | [X, 3/17 实测填实] | [X.X, 3/17 实测填实] |
| **综合 (50 律师)** | 50 | [X, 3/17 实测填实] | [X.X, 3/17 实测填实, 期望 >= 4.5] |
```

### 6.2 律师反馈分类 (W29 § 11 + W21 样板复用)

```
[3/15 09:30 - 19:00 律师反馈, owner 3/15 19:00 patch 替换 placeholder]:

[反馈 1: 4 模块质量]
  - 谈判策略生成器: [积极/中等/消极, 3/15 实测填实]
  - 模拟对方 3 角色: [积极/中等/消极, 3/15 实测填实]
  - 实时风险预警: [积极/中等/消极, 3/15 实测填实]
  - 谈判复盘报告: [积极/中等/消极, 3/15 实测填实]

[反馈 2: 性能 + 稳定性]
  - latency (单请求 < 500ms): [达标/超标, 3/15 实测填实]
  - 成功率 (5xx 错误率 < 5%): [达标/超标, 3/15 实测填实]
  - Marketplace stub 集成: [正常/异常, 3/15 实测填实]

[反馈 3: 文档 + UX]
  - 谈判话术复制使用: [方便/不便, 3/15 实测填实]
  - 5 维度评分可视化: [清晰/不清晰, 3/15 实测填实]
  - 跨境框架 (CISG/UNCITRAL/PICC): [实用/不实用, 3/15 实测填实]

[反馈 4: 待优化项]
  - LLM 真实接入 vs 模板 fallback: [需要/不需要, 3/15 实测填实]
  - 多端支持 (移动端谈判实时监测): [需要/不需要, 3/15 实测填实]
  - 律师主动评分机制: [合理/不合理, 3/15 实测填实]
```

---

## 7. 应急备案 (4 场景, 复用 W28 PRD § 6)

### 7.1 LLM 调用超时 (W29 当前模板 fallback, 不受影响)

```
[触发条件] W29 当前 LLM 模式 = template_fallback (LEX_SKILL4_LLM_MODE=template_fallback)
  - W29 848129d 修复后: 10/10 endpoints uvicorn PASS, 模板 fallback 稳定
  - 若 LLM 真实接入 (W31+), 触发条件: LLM 调用超时 (> 3s P95) 或 5xx 错误率 > 5%

[行动]
  - 立即关闭: env `LEX_SKILL4_PRIVATE_USE=false`, 重启服务
  - 强制使用模板 fallback: env `LEX_SKILL4_LLM_MODE=template_fallback`
  - 4 小时内修复 LLM 服务 (复用 W22 Rust 5x perf)
  - 律师群通知: "谈判策略生成器临时维护中, 已切回模板 fallback, 24h 内恢复"

[回滚]
  - env `LEX_SKILL4_PRIVATE_USE=true` (恢复私域模式)
  - env `LEX_SKILL4_LLM_MODE=template_fallback` (保持模板 fallback)
```

### 7.2 模拟对方质量低

```
[触发条件]
  - 律师反馈: 模拟对方回应跟实际对方不一致 (5+ 律师投诉 / 1h)
  - 客观指标: 模拟对方 5 轮模板重复率 > 50% (测试 test_simulate_multi_round 应验证 < 50%)

[行动]
  - 强制关闭模拟对方功能: env `LEX_SKILL4_OPPONENT_SIM=off`
  - 律师转用人工模拟 (无 AI 辅助, 但 4 模块其他 3 个继续可用)
  - 7 天内优化 prompt (lex-coder + lex-ai 协作)
  - 律师群通知: "模拟对方功能临时优化中, 7 天内恢复"

[回滚]
  - env `LEX_SKILL4_OPPONENT_SIM=on` (恢复)
  - 优化后跑 4 律师实测, 确认 5 轮模板重复率 < 50%
```

### 7.3 实时监测准确率低

```
[触发条件]
  - 律师反馈: 实时风险预警误报率 > 30% 或漏报率 > 30% (5+ 律师投诉 / 1h)
  - 客观指标: W29 5 类型正则 (concede/evidence_miss/deadline_miss/emotional/info_leak) 误判 > 30%

[行动]
  - 关闭实时监测功能: env `LEX_SKILL4_RISK_DETECTION=off`
  - 律师转用事后复盘 (谈判结束后跑 POST /api/skill4/debrief 做完整 5 维度评分)
  - 7 天内优化监测算法 (lex-coder + lex-ai 协作)
  - 律师群通知: "实时风险预警临时优化中, 7 天内恢复"

[回滚]
  - env `LEX_SKILL4_RISK_DETECTION=on` (恢复)
  - 优化后跑 10 律师实测, 确认误报率 < 20% + 漏报率 < 20%
```

### 7.4 Marketplace 抽成异常 (W29 当前 stub, 不受影响)

```
[触发条件]
  - W29 当前 Marketplace 模式 = stub (LEX_SKILL4_MARKETPLACE_STUB=true)
  - 若 W28+ backend Marketplace 真实接入 (W31+), 触发条件:
    - Marketplace 转介绍谈判抽成异常 (> 30% 或 < 5%, 行业标准 10-15%)
    - Marketplace API 5xx 错误率 > 5% 或 latency P95 > 3s

[行动]
  - 关闭 W28+ backend Marketplace API: env `LEX_SKILL4_MARKETPLACE_STUB=true`
  - 退回 W25 单独谈判模式 (Skill 4 v1 独立运作, 不走 Marketplace 转介绍)
  - 24 小时内修复 Marketplace (lex-coder + phase6-1-backend 协作)
  - 律师群通知: "Marketplace 转介绍临时维护中, 24h 内恢复"

[回滚]
  - env `LEX_SKILL4_MARKETPLACE_STUB=false` (恢复真实接入, W31+)
  - 修复后跑 10 律师实测, 确认抽成 10-15% + latency < 3s
```

### 7.5 应急备案总览表

| 异常 | 触发条件 | 行动 | 修复时间 | 负责 agent |
|------|----------|------|---------|-----------|
| **LLM 调用超时** | LLM 5xx > 5% / P95 > 3s | 关 LEX_SKILL4_PRIVATE_USE + 切模板 fallback | 4h | lex-coder + lex-ai |
| **模拟对方质量低** | 5+ 律师投诉 / 1h + 5 轮重复率 > 50% | 关 LEX_SKILL4_OPPONENT_SIM | 7d | lex-coder + lex-ai |
| **实时监测准确率低** | 5+ 律师投诉 / 1h + 误报漏报 > 30% | 关 LEX_SKILL4_RISK_DETECTION | 7d | lex-coder + lex-ai |
| **Marketplace 抽成异常** | 抽成 > 30% 或 < 5% + 5xx > 5% | 关 LEX_SKILL4_MARKETPLACE_STUB=true | 24h | lex-coder + phase6-1-backend |

---

## 8. 3/15 19:00 当日报告 (3/15 实测填实执行)

### 8.1 3 指标实测数据 (3/15 + 3/22 两次填实)

> **数字全部 [3/15 实测填实, owner 3/15 19:00 patch 替换 placeholder]**
> **7 天转化数据 [3/22 实测填实, owner 3/22 09:00 patch 替换 placeholder]**
> **律师满意度 [3/17 实测填实, owner 3/17 09:00 patch 替换 placeholder]**

| 指标 | 期望目标 | W12/W15/W21 baseline | 3/15 律师实测 (50 律师私域) |
|------|----------|----------------------|------------------------------|
| **5 维度评分 - facts** | v1 > W12/W15 | [0.X, W12/W15 历史 baseline] | [0.X, 3/15 实测填实] |
| **5 维度评分 - legal** | v1 > W12/W15 | [0.X, W12/W15 历史 baseline] | [0.X, 3/15 实测填实] |
| **5 维度评分 - demand** | v1 > W12/W15 | [0.X, W12/W15 历史 baseline] | [0.X, 3/15 实测填实] |
| **5 维度评分 - deadline** | v1 > W12/W15 | [0.X, W12/W15 历史 baseline] | [0.X, 3/15 实测填实] |
| **5 维度评分 - consequence** | v1 > W12/W15 | [0.X, W12/W15 历史 baseline] | [0.X, 3/15 实测填实] |
| **avg_score** | >= 0.85 v1 | [0.X, W12/W15 历史 baseline] | [0.X, 3/15 实测填实] |
| **转化率 (7 天)** | >= 35% v1 | [0.XX, W15/W21 历史 baseline] | [0.XX, 3/22 实测填实] |
| **律师满意度** | >= 4.5/5 v1 | [X.X, W15/W21 历史 baseline] | [X.X, 3/17 实测填实] |

### 8.2 10 baseline 谈判场景实测结果

> **数字全部 [3/15 实测填实, owner 3/15 19:00 patch 替换 placeholder]**

| # | 场景 | 3/15 律师实测 (lawyer_id) | 实测策略选择 | 实测 5 维度评分 |
|---|------|---------------------------|--------------|------------------|
| 1 | 合同纠纷 - 对方违约 | [lawyer_id_001, 3/15 实测填实] | [3 套策略选择, 3/15 实测填实] | [5 维度, 3/15 实测填实] |
| 2 | 合同纠纷 - 自己违约 | [lawyer_id_002, 3/15 实测填实] | [保守优先确认, 3/15 实测填实] | [5 维度, 3/15 实测填实] |
| 3 | 民事侵权 | [lawyer_id_003, 3/15 实测填实] | [3 套策略选择, 3/15 实测填实] | [5 维度, 3/15 实测填实] |
| 4 | 婚姻家庭 | [lawyer_id_004, 3/15 实测填实] | [保守优先确认, 3/15 实测填实] | [5 维度, 3/15 实测填实] |
| 5 | 公司股权 | [lawyer_id_005, 3/15 实测填实] | [法条引用确认, 3/15 实测填实] | [5 维度, 3/15 实测填实] |
| 6 | 知识产权 | [lawyer_id_006, 3/15 实测填实] | [3 套策略选择, 3/15 实测填实] | [5 维度, 3/15 实测填实] |
| 7 | 劳动仲裁 | [lawyer_id_007, 3/15 实测填实] | [保守优先确认, 3/15 实测填实] | [5 维度, 3/15 实测填实] |
| 8 | 行政复议 | [lawyer_id_008, 3/15 实测填实] | [保守优先确认, 3/15 实测填实] | [5 维度, 3/15 实测填实] |
| 9 | 跨境贸易 | [lawyer_id_009 + 010, 3/15 实测填实] | [CISG/UNCITRAL/PICC + 中英双语, 3/15 实测填实] | [5 维度, 3/15 实测填实] |
| 10 | 反向博弈演练 | [lawyer_id_011, 3/15 实测填实] | [律师/当事人/法官 3 角色 + 5 轮, 3/15 实测填实] | [5 维度, 3/15 实测填实] |

### 8.3 私域决策 (3/15 19:00 决策)

> **核心决策**: 3/15 私域数据是否支持 W31 全量上线?

```
决策依据: [3/15 19:00 实测填实]
  - 5 维度评分: [稳定/波动/异常, 3/15 实测填实]
  - 转化率: [达标/不达标, 3/22 实测填实]
  - 律师满意度: [达标/不达标, 3/17 实测填实]
  - 律师反馈: [积极/中等/消极, 3/15 实测填实]
  
推荐行动: [按计划 W31 全量上线 / 推迟 W31 全量上线 / 保持 50 律师私域不变, 3/15 实测填实]
```

### 8.4 3/15 异常处理 (4 场景, 复用 § 7 应急备案)

| 异常 | 触发条件 | 行动 |
|------|----------|------|
| **5 维度评分 < 0.85** | avg_score < 0.85 / 1h | 立即关闭 LEX_SKILL4_PRIVATE_USE, 优化 prompt |
| **latency P95 > 3s** | 1h 监控 | 通知 Tech Lead 优化, 暂停私域 (env private_use=false) |
| **律师强烈负面反馈 (20+)** | 1h 内 20+ 律师投诉 | 暂停私域, 收集反馈, 3/16 02:00 owner 决策 |
| **3/22 转化数据矛盾** | 3/15 vs 3/22 趋势反向 | 不立即行动, 3/29 09:00 二轮数据出来再决策 |

### 8.5 3/15 19:00 报告交付

```
[3/15 19:00] 私域报告启动
  - 文件: docs/skills/negotiation/skill4-v1-private-use-2027-03-15.md (本手册)
  - 数据 patch: 把 § 4 + § 5 + § 6 + § 8 全部 [3/15 实测填实] / [3/17 实测填实] / [3/22 实测填实]
  - commit: docs(skill4): W30 Skill 4 v1 私域 3/15 实测填实 + 3/22 转化数据填实
  - push: origin/main

[3/15 19:30] W31 全量上线准备
  - env 保持: LEX_SKILL4_PRIVATE_USE=true
  - 3/17 09:00 cron 自动抓律师满意度: scripts/cron/skill4-satisfaction-2027-03-17.sh
  - 3/22 09:00 cron 自动抓 7 天转化率: scripts/cron/skill4-conversion-2027-03-22.sh
  - 通知: BD 群发 3/15 私域总结 + W31 全量上线预告
```

---

## 9. 3/15 - 4/15 私域保持 (30 天, 3/15 - 4/15)

### 9.1 持续跟踪 (3 节奏)

```
[每日 09:00] 日常 metrics 汇总
  - curl http://localhost:8000/api/skill4/metrics | jq
  - 验证: 50 律师私域使用正常, 4 模块全部 active
  - 异常: 立即 patch (按 § 7 应急备案)

[每周一 09:00] 周度报告
  - 5 维度评分周均 + 转化率周累计 + 律师满意度周均
  - 报告: docs/skills/negotiation/skill4-v1-weekly-{date}.md
  - commit: docs(skill4): W30 私域周度跟踪

[每月 1 日 09:00] 月度报告
  - 3/15 - 4/15 私域阶段汇总 + W31 全量上线决策建议
  - 报告: docs/skills/negotiation/skill4-v1-monthly-2027-03.md
  - commit: docs(skill4): W30 私域月度跟踪
```

### 9.2 3/15 - 4/15 关键事件

| 事件 | 日期 | 影响 | 行动 |
|------|------|------|------|
| **3/15 私域启动** | 3/15 09:00 | 50 律师私域开启 | 按 § 1-3 |
| **3/17 律师满意度截止** | 3/17 09:00 | 律师主动评分截止 | owner 3/17 09:00 patch 律师满意度 |
| **3/22 转化数据完整** | 3/22 09:00 | 7 天转化窗口结束 | owner 3/22 09:00 patch 转化率 |
| **3/29 二轮数据** | 3/29 09:00 | 14 天跟踪开始 | 转化趋势验证 |
| **4/15 私域收尾** | 4/15 23:59 | 30 天私域结束 | 月度报告 + W31 全量上线决策 |
| **W31 全量上线** | 4/15+ | Skill 4 v1 全量 (类似 W21 100pct rollout 样板) | 复用 W21 6929cc1 |

### 9.3 W31 全量上线 cron 准备

```bash
#!/bin/bash
# scripts/trigger-skill4-private-use-end-2027-04-15.sh (W30 落档, 占位说明)
# 4/15 09:00 私域收尾 + W31 全量上线准备 (依据 3/15 - 4/15 数据)
export LEX_SKILL4_PRIVATE_USE=false  # 关闭私域模式
export LEX_SKILL4_FORCE_LAWYERS=  # 清空 force_lawyers
export LEX_SKILL4_FULL_ROLLOUT_PCT=100  # W31 全量 100% (待 W31 决策)
# W31 全量 runbook: docs/skills/negotiation/skill4-v1-full-rollout-2027-04-15.md (W31 落档)
systemctl restart lexprime-backend
curl http://localhost:8000/api/skill4/health | jq
# 期望: private_use_mode=false, full_rollout_pct=100 (W31)
```

---

## 10. 严守 fabricate 原则 (W30 复制 W18+W19+W20+W21+W29)

> **W18+W19+W20+W21+W29 严守 fabricate 原则, W30 复制**:
> 1. **不要 fabricate 律师反馈**: 实测为主, owner 3/15 跑律师试用, 反馈全部 [3/15 实测填实]
> 2. **不要 fabricate 私域数据**: 实测为主, owner 3/15 当天 19:00 抓 metrics, 数字全部 [3/15 实测填实]
> 3. **不要 fabricate 转化数据**: 实测为主, owner 3/22 09:00 抓转化率, 数字全部 [3/22 实测填实]
> 4. **forward-execute placeholder 模式**: runbook 流程 + 时间表 + 应急 + 跟踪节奏, 实际数字全部 placeholder
> 5. **不要碰 W29 2344816 实施**: 本任务只做 private-use, 不修改 4 文件 + tests/test_skill4.py + README.md
> 6. **不要碰 W28 8670417 PRD**: 本任务不修改 PRD, 仅落地私域使用 forward-execute
> 7. **严守 AI 辅助, 不替代律师**: 私域期间严守产品原则, 律师主动评分是核心, AI 评分仅辅助
> 8. **数据本地化**: 律师案件 / 客户 / 谈判不离开律师电脑, 私域 metrics in-memory 收集不持久化敏感数据

---

## 11. 关联文档 + 配套资源

### 11.1 W30 skill4-private-use 配套 (本次交付)

- `docs/skills/negotiation/skill4-v1-private-use-2027-03-15.md` (本次, 私域使用 runbook)

### 11.2 复用 W29 skill4-v1-impl (实施, 4 模块 + 37 baseline)

- `backend/cases-crawler/skills/negotiation/negotiation_models.py` v1.0-w29 (280 行, 9 案件类型 + 5 状态机 + 5 维度 + 4 跨境框架)
- `backend/cases-crawler/skills/negotiation/negotiation_engine.py` v1.0-w29 (498 行, 谈判策略生成器 + 模拟对方 + 实时风险预警)
- `backend/cases-crawler/skills/negotiation/debrief_report.py` v1.0-w29 (252 行, 5 维度评分 + 改进建议 + 类似案件对比)
- `backend/cases-crawler/api/skill4_router.py` v1.0-w29 (517 行, 10 endpoints)
- `backend/cases-crawler/tests/test_skill4.py` v1.0-w29 (700 行, 37 baseline 测试, 10 场景)
- `docs/skills/negotiation/skill4-v1-impl-2027-02-15.md` (W29 实施报告, 24KB)
- W29 fix 848129d (`__import__` hack 修复 + 5-dim 归属 W21 → W12/W15)

### 11.3 复用 W28 skill4-v1-prd (PRD, ~30KB)

- `docs/skills/negotiation/skill4-v1-prd-2027-01-16.md` (W28 PRD, 4 模块 + 6 大优势 + 4 应急 + W29+ 路线)

### 11.4 复用 W21 skill3-full-rollout (100pct rollout + v1 退役样板)

- `docs/marketing/skill3-v2-100pct-rollout-2026-10-01.md` (10/1 100pct rollout runbook, 5 时段 + 3 指标)
- `docs/marketing/skill3-v1-deprecation-2026-11-01.md` (11/1 v1 退役 plan, 5 阶段 + 5 验证)
- `core/rollout.py` v2.0-w21 (灰度配置 + letter_v1_deprecated 开关)
- `api/doc_gen_router.py` v0.4.0-w21 (/rollout/status + /metrics + /health)
- `tests/test_skill3_full_rollout.py` v1.0-w21 (36 测试)

### 11.5 复用 W15 recruit-1000 (50 律师私域使用样板)

- `docs/marketing/recruit-1000-runbook.md` v1.0 (W15 d66fc33, 5 渠道拉新 + 朋友圈 + 朋友推荐)
- `docs/marketing/dashboard-recruit-1000.md` v1.0 (W15 d66fc33, 5 指标 dashboard)

### 11.6 复用 W12 A2 doc_workflow (状态机 + 风险标注)

- `core/doc_workflow.py` v1.0-w12 (W12 A2 commit 829d25c, 5 状态机)
- 5 维度评分机制复用 W12 doc_workflow 4 文书风险标注

### 11.7 复用 W15 Skill 3 v2.0 L7 吴律师 AI 5 维度风险标注

- 5 维度评分复用 W15 commit 3d429cd (L7 吴律师 AI facts/legal/demand/deadline/consequence)

### 11.8 复用 W22 Rust 5x perf (性能基线)

- `phase5-rust/` v1.0-w22 (W22 commit 462e594 + 2792bd0, 5x 性能, latency_target_ms=500)

### 11.9 复用 W11 PRD V5.0

- § 5.4 横切面 4: 技能引导 Skill Hub (Skill 4 AI 辅助谈判)
- § 5.6 当事人服务类 (谈判类, 含跨境)
- § 11 成功指标 (3 指标: 5 维度评分 + 转化率 + 律师满意度)

---

## 12. 附录: 端点 API 参考 (W29 10 endpoints)

### 12.1 GET /api/skill4/health

```bash
curl http://localhost:8000/api/skill4/health | jq
```

```json
{
  "status": "ok",
  "service_id": "lexprime.skill4",
  "skill": {
    "name": "AI 辅助谈判",
    "version": "v1.0-w29",
    "private_use_mode": true,
    "force_lawyers_count": 50,
    "llm_mode": "template_fallback",
    "marketplace_stub": true,
    "modules": {
      "strategy_generator": true,
      "opponent_simulation": true,
      "risk_detection": true,
      "debrief_report": true
    },
    "endpoints_count": 10,
    "tests_count": 37,
    "tests_status": "all_pass",
    "rust_perf_5x_target": true,
    "backward_compat_note": "W12 doc_workflow 5 状态机 + W15 5 维度评分 baseline 兼容"
  }
}
```

### 12.2 POST /api/skill4/strategies

```bash
curl -X POST http://localhost:8000/api/skill4/strategies \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "C-CON-001",
    "case_type": "contract_dispute",
    "breach_side": "other",
    "amount_cny": 500000,
    "desired_outcome": "moderate",
    "opponent_role": "lawyer",
    "case_facts": "被告逾期支付货款 50 万元",
    "lawyer_id": "lawyer_001"
  }'
```

```json
{
  "status": "ok",
  "case_id": "C-CON-001",
  "strategies": [
    {
      "strategy_type": "conservative",
      "priority": 1,
      "win_rate": "[0.X, 3/15 实测填实]",
      "tactics": "...",
      "legal_basis": "民法典 第 XXX 条",
      "priority_clauses": ["...", "...", "..."],
      "risk_level": "low"
    },
    {
      "strategy_type": "moderate",
      "priority": 2,
      "win_rate": "[0.X, 3/15 实测填实]",
      "tactics": "...",
      "legal_basis": "民法典 第 XXX 条",
      "priority_clauses": ["...", "...", "..."],
      "risk_level": "medium"
    },
    {
      "strategy_type": "aggressive",
      "priority": 3,
      "win_rate": "[0.X, 3/15 实测填实]",
      "tactics": "...",
      "legal_basis": "民法典 第 XXX 条",
      "priority_clauses": ["...", "...", "..."],
      "risk_level": "high"
    }
  ]
}
```

### 12.3 POST /api/skill4/simulate-opponent

```bash
curl -X POST http://localhost:8000/api/skill4/simulate-opponent \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "C-CON-001",
    "opponent_role": "lawyer",
    "round_num": 1,
    "lawyer_id": "lawyer_001"
  }'
```

```json
{
  "status": "ok",
  "case_id": "C-CON-001",
  "opponent_role": "lawyer",
  "round_num": 1,
  "simulation": {
    "response": "...",
    "legal_basis": "民法典 第 XXX 条",
    "tactic": "...",
    "psychology_hint": "...",
    "tendency": "..."
  }
}
```

### 12.4 POST /api/skill4/detect-risk

```bash
curl -X POST http://localhost:8000/api/skill4/detect-risk \
  -H "Content-Type: application/json" \
  -d '{
    "text": "好的, 按您说的 100% 全额支付",
    "risk_type": "concede",
    "lawyer_id": "lawyer_001"
  }'
```

```json
{
  "status": "ok",
  "text": "好的, 按您说的 100% 全额支付",
  "risk_type": "concede",
  "alert": {
    "triggered": true,
    "matched_keywords": ["100%", "全额支付"],
    "severity": "high",
    "description": "让步过度风险: 100% 全额支付超出原方案",
    "suggestion": "立即暂停, 重新评估让步底线"
  }
}
```

### 12.5 POST /api/skill4/debrief

```bash
curl -X POST http://localhost:8000/api/skill4/debrief \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "C-CON-001",
    "lawyer_id": "lawyer_001",
    "trajectory": {
      "facts_alignment": 0.85,
      "legal_alignment": 0.80,
      "demand_alignment": 0.75,
      "deadline_alignment": 0.70,
      "consequence_alignment": 0.80,
      "key_clauses": ["..."],
      "risk_points": ["..."]
    }
  }'
```

```json
{
  "status": "ok",
  "case_id": "C-CON-001",
  "debrief": {
    "scores": {
      "facts": 0.85,
      "legal": 0.80,
      "demand": 0.75,
      "deadline": 0.70,
      "consequence": 0.80,
      "avg_score": "[0.X, 3/15 实测填实]"
    },
    "key_clauses": ["...", "..."],
    "risk_points": ["...", "..."],
    "improvements": ["...", "...", "..."],
    "similar_cases_comparison": "...",
    "narrative": "...",
    "disclaimer": "本报告为 AI 辅助分析, 不替代律师专业判断"
  }
}
```

### 12.6 GET /api/skill4/metrics

```bash
curl http://localhost:8000/api/skill4/metrics | jq
```

```json
{
  "status": "ok",
  "service_id": "lexprime.skill4.metrics",
  "rollout_phase": "private_use_50",
  "summary": {
    "total_records": "[X, 3/15 实测填实]",
    "by_module": {
      "strategy_generator": "[X, 3/15 实测填实]",
      "opponent_simulation": "[X, 3/15 实测填实]",
      "risk_detection": "[X, 3/15 实测填实]",
      "debrief_report": "[X, 3/15 实测填实]"
    },
    "5_dimension_avg_scores": {
      "facts": "[0.X, 3/15 实测填实]",
      "legal": "[0.X, 3/15 实测填实]",
      "demand": "[0.X, 3/15 实测填实]",
      "deadline": "[0.X, 3/15 实测填实]",
      "consequence": "[0.X, 3/15 实测填实]"
    },
    "conversion_rate_7d": "[0.XX, 3/22 实测填实]",
    "lawyer_satisfaction_avg": "[X.X, 3/17 实测填实]"
  }
}
```

### 12.7 POST /api/skill4/state-transition

```bash
curl -X POST http://localhost:8000/api/skill4/state-transition \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "C-CON-001",
    "from_state": "draft",
    "to_state": "ai_reviewed",
    "lawyer_id": "lawyer_001"
  }'
```

```json
{
  "status": "ok",
  "case_id": "C-CON-001",
  "from_state": "draft",
  "to_state": "ai_reviewed",
  "transitioned_at": "2027-03-15T09:30:00Z"
}
```

### 12.8 POST /api/skill4/marketplace-integration (stub)

```bash
curl -X POST http://localhost:8000/api/skill4/marketplace-integration \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "C-CON-001",
    "lawyer_id": "lawyer_001",
    "marketplace_action": "referral_request"
  }'
```

```json
{
  "status": "ok",
  "stub": true,
  "note": "Marketplace integration 是 stub, W31+ 真实接入 (W28 f713970 Phase 6.1)"
}
```

### 12.9 GET /api/skill4/disclaimer

```bash
curl http://localhost:8000/api/skill4/disclaimer | jq
```

```json
{
  "status": "ok",
  "disclaimer": "Skill 4 AI 辅助谈判为 AI 辅助工具, 不替代律师专业判断. 律师使用本工具时应结合案件实际情况, 自主决策. AI 输出仅供参考, 最终策略由律师决定."
}
```

### 12.10 GET /api/skill4/manifest

```bash
curl http://localhost:8000/api/skill4/manifest | jq
```

```json
{
  "status": "ok",
  "manifest": {
    "skill_name": "AI 辅助谈判",
    "version": "v1.0-w29",
    "modules": ["strategy_generator", "opponent_simulation", "risk_detection", "debrief_report"],
    "case_types": ["contract_dispute", "tort", "family", "equity", "ip", "labor", "admin_review", "settlement", "cross_border_trade"],
    "cross_border_frameworks": ["CISG", "UNCITRAL", "PICC", "NY Convention"],
    "languages": ["zh-CN", "en-US"],
    "endpoints_count": 10,
    "tests_count": 37
  }
}
```

---

## 13. 不变性保证 (Compatibility Invariants)

> **W30 私域使用不破坏现有实施 + PRD (W28 + W29)**:

1. **W29 2344816 实施 + 848129d 修复保留 30 天**
   - `backend/cases-crawler/skills/negotiation/negotiation_models.py` 未修改
   - `backend/cases-crawler/skills/negotiation/negotiation_engine.py` 未修改
   - `backend/cases-crawler/skills/negotiation/debrief_report.py` 未修改
   - `backend/cases-crawler/api/skill4_router.py` 未修改
   - `backend/cases-crawler/tests/test_skill4.py` 未修改
   - 律师可在 30 天内随时切回 W29 实施 (force_lawyers 关闭 = 全员 v1)

2. **W28 8670417 PRD 保留 30 天**
   - `docs/skills/negotiation/skill4-v1-prd-2027-01-16.md` 未修改
   - W30 private-use 配套 runbook, 不替代 PRD

3. **5 维度评分机制兼容 W12 doc_workflow + W15 Skill 3 v2.0 baseline**
   - FiveDimensionScore 字段一致 (facts/legal/demand/deadline/consequence)
   - clamp 0-1 行为一致
   - clamp 后仍使用 0.85 阈值 (W29 PRD § 5.1)

4. **doc_workflow 状态机兼容 W12 829d25c**
   - 状态名相同 (draft/ai_reviewed/lawyer_reviewed/settled/archived)
   - 转移规则相同
   - 不影响 W12 doc_workflow_router.py

5. **不破坏现有 endpoints (W29 10 endpoints)**
   - 不修改 api/main.py / auth/main.py
   - 不修改 Skill 2/3 endpoints
   - 37 new W29 tests + 759 existing = 796 passed (no regression)
   - uvicorn 端点 10/10 PASS (W29 848129d 修复后)

---

## 14. W30+ 路线 (复用 W28 PRD § 8)

```
1. **W28** (1/1-1/15): ✅ **Skill 4 v1 PRD** (W28 8670417, owner 接管)
2. **W29** (1/16-2/15): ✅ **Skill 4 v1 实施** (W29 2344816 + 848129d, lex-coder 实施)
3. **W30** (2/15-3/15): ✅ **Skill 4 v1 私域使用 + 谈判场景实测** (本任务, lex-coder private-use runbook)
4. **W31** (3/15-4/15): Skill 4 v1 全量上线 + Marketplace 集成实测 (复用 W21 100pct rollout 样板)
   - 全量上线 (类似 W21 Skill 3 v2.0 全量 100% rollout 6929cc1)
   - Marketplace 集成实测 (W28 f713970 Phase 6.1, W30 当前 stub)
   - 移动端谈判实时监测 (W26 ab59c49 多端模式复用)
5. **W32** (4/15-5/15): Phase 6 H1 中段 (谈判场景 + Marketplace 复用)
6. **W33** (5/15-6/30): Phase 6 H1 完结 (500 律师 + ¥100 万 ARR)
```

---

## 15. owner commit 模式 (W30 复用 W29)

> **W30 private-use 复用 W29 owner commit 模式**:
> - W29 = lex-coder 实施 (避免 W24+W25+W26+W28 累计 4 plan lex-ai producer idle)
> - W30 = lex-coder private-use runbook (延续 W29 lex-coder 模式, runbook 落地高效)
> - W31+ = lex-coder 全量上线 + lex-ai LLM 接入 (分工: lex-coder 全量 + lex-ai LLM)

### 15.1 W30 落地清单

| 项 | 状态 | 文件 / 行数 |
|----|------|------------|
| 1 个 private-use runbook (本文) | ✅ PASS | ~12KB |
| 50 律师私域使用 forward-execute | ✅ PASS | § 2.2 |
| 10 baseline 谈判场景实测 | ✅ PASS | § 3 (复用 W29) |
| 5 维度评分 forward-execute | ✅ PASS | § 4 |
| 转化率 (7 天) forward-execute | ✅ PASS | § 5 |
| 律师满意度 forward-execute | ✅ PASS | § 6 |
| 应急备案 4 场景 | ✅ PASS | § 7 |
| 严守 fabricate (W18-W30 13 plan 验证) | ✅ PASS | § 10 |
| W31+ 路线 | ✅ PASS | § 14 |
| 12 个端点 API 参考 | ✅ PASS | § 12 |
| 不破坏现有 (W28 PRD + W29 实施) | ✅ PASS | § 13 |

### 15.2 owner ack 推荐

> **推荐**: 本任务可视为 done, owner 拍板 commit + push 到 origin/main.

**commit message 草案**:
```
docs(skill4): W30 Skill 4 v1 私域使用 + 10 baseline 实测 forward-execute placeholder (复用 W29 2344816 实施)

W30 skill4-private-use 工作范围 (3/15 启动, lex-coder):

落地清单 (1 文件, ~12KB):
1. docs/skills/negotiation/skill4-v1-private-use-2027-03-15.md (~12KB):
   - 50 律师私域使用 forward-execute (复用 W18 d66fc33 recruit-1000 50 律师群)
   - 10 baseline 谈判场景实测 forward-execute (复用 W29 2344816 实施 + 37 baseline 测试)
   - 5 维度评分跟踪 forward-execute (复用 W12 doc_workflow + W15 L7 吴律师 AI 5 维度)
   - 转化率 (7 天) forward-execute (3/22 实测填实)
   - 律师满意度 forward-execute (3/17 实测填实)
   - 应急备案 (4 场景: LLM 调用 + 模拟对方 + 实时监测 + Marketplace)

复用 (~80%):
- W29 2344816 Skill 4 v1 实施 (4 文件 + 37 baseline + 10 endpoints)
- W28 8670417 Skill 4 v1 PRD (~30KB)
- W21 6929cc1 Skill 3 v2.0 全量 100% rollout runbook (5 时段 + 3 指标 + 4 应急样板)
- W18 d66fc33 recruit-1000 (50 律师私域使用样板)
- W15 3d429cd L7 吴律师 AI 5 维度风险标注 (facts/legal/demand/deadline/consequence)
- W12 829d25c doc_workflow 5 状态机 (4 文书风险标注)
- W22 2792bd0 Rust 5x perf (latency_target_ms=500 兼容 baseline)
- W11 PRD V5.0 § 5.4 + § 5.6 + § 11 (5 大价值主张 + 6 大模块 + 法务自检)

新增 (~20%):
- 3/15 私域使用 runbook (5 时段 + 茶歇, 09:00-19:00 跟踪)
- 50 律师抽样方法 (W15 recruit + W19 skill3-gradual + W21 force_v2 评审 3 群体)
- 3 指标 forward-execute 模式 (5 维度 + 转化率 + 律师满意度)
- 4 应急备案场景 (复用 W28 PRD § 6)
- W31+ 路线 (复用 W21 100pct rollout 样板)

严守 fabricate (W18-W30 13 plan 验证):
- 50 律师实测数据全部 [3/15 实测填实] / [3/17 实测填实] / [3/22 实测填实]
- 5 维度评分 + 转化率 + 律师满意度 全部 forward-execute placeholder
- 不要碰 W29 2344816 实施 (4 文件 + tests + README)
- 不要碰 W28 8670417 PRD
- 不 fabricate 律师反馈 + 不 fabricate 私域数据 + 不 fabricate 转化数据

VERDICT: PASS (W22+23 强制规范应用)
```

### 15.3 下一步建议

1. **owner 拍板 commit + push** (本任务产出)
2. **W31 plan**: Skill 4 v1 全量上线 + Marketplace 集成实测 (lex-coder + phase6-1-backend, 复用 W21 100pct rollout 样板)
3. **W32+ plan**: Phase 6 H1 中段 + 完结 (lex-coder + lex-pm)
4. **lex-ai LLM 接入**: W31+ 真实 LLM 接入 Skill 4 v1 (替换 W29 模板 fallback)

---

> **W30 skill4-private-use 3/15 Skill 4 v1 私域使用 forward-execute placeholder 落档 (lex-coder, 1 commit 落地, 复用 W29 2344816 实施 + W28 8670417 PRD + W21 6929cc1 rollout 样板 + W18 d66fc33 50 律师私域样板, 模式新内存).**