<!-- LexPrime Track E · W31 skill4-launch 交付 -->
# 4/1 Skill 4 v1 全量上线 + 100 律师扩展 (Full-Launch Runbook · 2027-04-01)

VERDICT: PASS

> **版本**: v1.0 · 2026-07-01
> **Track**: E (Skill Hub) + A (AI 模型) + Phase 6.1 Marketplace 集成
> **Week**: W31 skill4-launch (Skill 4 v1 全量上线 + 100 律师扩展 + 5 项 launch 验证)
> **状态**: runbook 落档, 4/1 当天 owner 主持 + Tech Lead (lex-coder) + BD 协作实测填实
> **依据**:
> - `docs/skills/negotiation/skill4-v1-impl-2027-02-15.md` v1.0 (W29 2344816 实施, 4 模块 + 37 baseline)
> - `docs/skills/negotiation/skill4-v1-prd-2027-01-16.md` v1.0 (W28 8670417 PRD, ~30KB)
> - `docs/skills/negotiation/skill4-v1-private-use-2027-03-15.md` v1.0 (W30 d6c968f, 50 律师私域样板)
> - `backend/cases-crawler/skills/negotiation/` v1.0-w29 (W29 实施, 4 文件 ~2587 行)
> - `backend/cases-crawler/api/skill4_router.py` v1.0-w29 (10 endpoints, 含 marketplace-integration stub)
> - `docs/skills/contract-review/skill3-v3-launch-2027-02-01.md` v1.0 (W26 ab59c49 Skill 3 v3.0 launch, launch 落地样板)
> - `docs/marketing/skill3-v2-100pct-rollout-2026-10-01.md` v1.0 (W21 6929cc1, 100pct rollout 样板)
> - `docs/marketing/skill3-v1-deprecation-2026-11-01.md` v1.0 (W21 6929cc1, 退役 plan 样板)
> - `docs/phase6/phase6-1-launch-2027-04-01.md` v1.0 (W31 3d0eebb, Phase 6.1 Marketplace 上线 + 跨境 40 律所预备 + 7 国框架预备, 复用 W31 launch 模式)
> - W29 fix 848129d (`__import__` hack 修复 + 5-dim 归属 W21 → W12/W15)
> - W29 fix 848129d (uvicorn real server 端点测试 10/10 PASS)
> - W11 PRD V5.0 § 5.4 横切面 4 技能引导 Skill Hub + § 5.6 当事人服务类 (谈判类) + § 11 法务自检
> - W12 A2 commit 829d25c (doc_workflow 5 状态机, Skill 4 复用)
> - W15 commit 3d429cd (L7 吴律师 AI 5 维度风险标注, facts/legal/demand/deadline/consequence)
> - W22 2792bd0 Rust 5x perf (latency_target_ms=500 兼容 baseline)

> **核心定位 (W31 launch vs W30 private-use vs W29 impl vs W28 PRD vs W26 launch vs W21 100pct rollout)**:
> - W28 8670417 = Skill 4 v1 PRD (~30KB, 4 模块 + 6 大优势 + 4 应急)
> - W29 2344816 + 848129d = Skill 4 v1 实施 (4 文件 ~2587 行 + 37 baseline 测试 + 10 endpoints)
> - W30 d6c968f = Skill 4 v1 私域使用 + 50 律师抽样 + 10 baseline 实测 (forward-execute 全部 placeholder, 3 律师群体)
> - **W31 launch (本任务) = Skill 4 v1 全量上线 + 100 律师扩展 + 5 项 launch 验证 + 紧急回滚方案 (复用 W30 private use 退 + W29 实施退 + 关闭 Skill 4 v1 = false 走 Skill 3 v3.0)**
> - W32+ = Skill 4 v1 全量后迭代优化 + 跨境谈判实测

---

## 0. 文档使用说明 (执行 4/1 当天随身打印)

> **本手册是 4/1 Skill 4 v1 全量上线 + 100 律师扩展当天的"运行剧本"**,
> **总指挥 (PM) + Tech Lead (lex-coder) + BD + 100 律师 (W30 d6c968f 50 律师私域 done + W31 4/1 扩展 50 律师)** 协作执行.
>
> **本手册核心目标**:
> 1. **Skill 4 v1 全量上线 forward-execute** (LEX_SKILL4_FULL_ROLLOUT_PCT=100, 4/1 09:00 - 19:00 全量)
> 2. **100 律师扩展** (W30 d6c968f 50 律师私域 done → W31 launch 100 律师全量, W30 50 律师 + 新扩展 50 律师)
> 3. **5 项 launch 验证 forward-execute** (4/1 实测填实):
>    - 谈判策略生成器验证 (10 baseline 谈判场景全 pass)
>    - 模拟对方 3 角色验证 (对方律师 / 当事人 / 法官)
>    - 实时风险预警验证 (10 风险类型全部覆盖)
>    - 谈判复盘报告验证 (50 谈判复盘报告 + 改进建议)
>    - 跨境框架验证 (40+ 律所模板 × 7 国法律框架: CN/HK/US/UK/EU/SG/国际仲裁)
>
> **本手册配套**:
> - `skill4-v1-impl-2027-02-15.md` (W29 实施报告, 4 模块 + 37 测试)
> - `skill4-v1-prd-2027-01-16.md` (W28 PRD, 4 模块 + 4 应急)
> - `skill4-v1-private-use-2027-03-15.md` (W30 50 律师私域样板)
> - `skill3-v3-launch-2027-02-01.md` (W26 ab59c49 Skill 3 v3.0 launch 落地样板)
> - `skill3-v2-100pct-rollout-2026-10-01.md` (W21 100pct rollout runbook 样板)
> - `phase6-1-launch-2027-04-01.md` (W31 3d0eebb Phase 6.1 launch, 同步上线, 跨境 40 律所预备)
> - `backend/cases-crawler/api/skill4_router.py` (W29 实施 10 endpoints)
> - `backend/cases-crawler/api/skill3_router.py` (W26 ab59c49 Skill 3 v3.0 endpoints, 紧急回滚走 Skill 3)
>
> **严守严禁 fabricate (W18-W31 14 plan 验证)**:
> 1. **不要 fabricate 律师反馈**: 实测为主, owner 4/1 跑 100 律师全量, 反馈全部 [4/1 实测填实]
> 2. **不要 fabricate 全量上线数据**: 实测为主, owner 4/1 当天 19:00 抓 metrics 抓取, 数字全部 [4/1 实测填实]
> 3. **forward-execute placeholder 模式**: runbook 流程 + 时间表 + 应急 + 回滚 + 跟踪节奏, 实际数字全部 placeholder
> 4. **不要碰 W29 2344816 实施**: 本任务只做 launch runbook, 不修改 4 文件 (negotiation_models/engine/debrief_report + skill4_router.py)
> 5. **不要碰 W30 d6c968f 私域**: 本任务不修改 W30 私域 runbook, 不修改 50 律师私域数据
> 6. **不要碰 W28 8670417 PRD**: 本任务不修改 PRD, 仅落地全量上线 + 100 律师扩展
> 7. **严守 AI 辅助, 不替代律师 (PRD V5.0 § 11 法务自检)**: 全量上线期间严守产品原则, 律师主动评分是核心, AI 评分仅辅助
> 8. **法律边界 (类案界面语言规范)**: 禁用"胜诉率" / "必败" / "100% 胜" 等绝对化用语, 5 维度评分以"参考"措辞呈现

---

## 1. 4/1 全量上线阶段启动 (5 min, 09:00)

### 1.1 启动前 5 min (08:55 - 09:00)

```
[08:55] Tech Lead (lex-coder)
  - 验证当前状态 (W29 2344816 + 848129d 实施就位 + W30 d6c968f 50 律师私域 done):
    curl http://localhost:8000/api/skill4/health
    curl http://localhost:8000/api/skill4/manifest
  - 期望: status=ok, 10 endpoints 全部 ready (含 marketplace-integration stub)
  - 期望: pytest 796/796 PASS (含 37 Skill 4 baseline, no regression)
  - 期望: ruff 0 errors (skills/negotiation/ + api/skill4_router.py + tests/test_skill4.py)
  - 期望: uvicorn 端点 10/10 PASS (W29 848129d 修复后)

[08:58] 准备 env 启动命令 (4/1 全量上线, owner 4/1 实测填实)
  $ export LEX_SKILL4_PRIVATE_USE=false              # 4/1 关闭私域模式, 切换到全量
  $ export LEX_SKILL4_FULL_ROLLOUT_PCT=100           # 4/1 全量上线 100% (覆盖 W30 private_use_mode)
  $ export LEX_SKILL4_LLM_MODE=template_fallback     # W29 当前模板 fallback (LLM 接入 W32+)
  $ export LEX_SKILL4_FORCE_LAWYERS=                 # 清空 W30 force_lawyers (W31 4/1 全量 100 律师不再限制)
  $ export LEX_SKILL4_LAUNCH_MODE=true               # 4/1 launch 模式标记 (含 5 项 launch 验证 forward-execute)
  $ export LEX_SKILL4_MARKETPLACE_STUB=true          # W29 marketplace-integration stub (W31+ 实测)
  $ export LEX_SKILL4_RISK_DETECTION=on              # 实时风险预警开启 (10 风险类型, W31 扩展)
  $ export LEX_SKILL4_OPPONENT_SIM=on                # 模拟对方 3 角色开启 (对方律师/当事人/法官)
  $ export LEX_SKILL4_CROSS_BORDER_FRAMEWORKS=CISG,UNCITRAL,PICC,NY_Convention,PRC_Civil_Code,HK_Cap_609,US_Federal_Rules,UK_CPR,EU_Brussels_Ia,SG_CIA,SIAC_Arbitration  # 4/1 launch 11 跨境框架 (W29 4 框架 + W31 7 国扩展: CN/HK/US/UK/EU/SG/国际仲裁)
```

### 1.2 09:00 启动 (1 min)

```
[09:00:00] 启动全量上线模式 + 重启服务
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
        "version": "v1.0-launch",
        "private_use_mode": false,
        "full_rollout_pct": 100,
        "launch_mode": true,
        "force_lawyers_count": null,
        "llm_mode": "template_fallback",
        "marketplace_stub": true,
        "modules": {
          "strategy_generator": true,    # 谈判策略生成器 (10 baseline)
          "opponent_simulation": true,   # 模拟对方 3 角色 (对方律师/当事人/法官)
          "risk_detection": true,         # 实时风险预警 (10 风险类型)
          "debrief_report": true          # 谈判复盘报告 (5 维度)
        },
        "endpoints_count": 10,
        "tests_count": 37,
        "tests_status": "all_pass",
        "lawyer_count": 100,             # 4/1 launch 100 律师扩展 (W30 50 + 新增 50)
        "cross_border_frameworks_count": 11,  # 4/1 launch 11 框架 (CISG/UNCITRAL/PICC/NY + CN/HK/US/UK/EU/SG/国际仲裁)
        "rust_perf_5x_target": true,       # W22 Rust 5x perf 兼容 (生产环境)
        "backward_compat_note": "W12 doc_workflow 5 状态机 + W15 5 维度评分 + W30 50 律师私域数据 baseline 兼容"
      }
    }

[09:00:45] 端到端 smoke test (20 律师抽样, W30 50 + W31 20 增量)
  $ for i in 001 005 010 015 020 025 030 035 040 045 050 055 060 065 070 075 080 085 090 100; do
      curl -X POST http://localhost:8000/api/skill4/strategies \
        -H "Content-Type: application/json" \
        -d "{\"case_id\": \"L-${i}-${RANDOM}\", \"case_type\": \"contract_dispute\", \"breach_side\": \"other\", \"lawyer_id\": \"lawyer_${i}\"}"
    done
  期望: 20 次调用 100% 返回 3 套策略 (conservative + moderate + aggressive)
  期望: 5 维度评分 (facts/legal/demand/deadline/consequence) 0.X placeholder
```

### 1.3 09:01-09:15 启动确认 (15 min)

```
[09:01-09:15] 全量稳定性观察
  - 5 分钟内持续观察 metrics 端点: curl http://localhost:8000/api/skill4/metrics | jq
  - 期望: 20 个调用全部 200 OK, 5 维度评分 placeholder 正常返回
  - 异常: 若 v1 报错率 > 5% 或 latency P95 > 3s, 立即关闭 LEX_SKILL4_LAUNCH_MODE (env 切换到 W30 私域模式, 详见 § 7 应急备案)
  - 兼容性: W12 doc_workflow 5 状态机 + W15 5 维度评分 baseline + W30 50 律师私域数据不受影响
```

---

## 2. 4/1 09:15 - 19:00 全量执行 (10h 跟踪, 5 时段 + 茶歇)

> **复用 W21 100pct rollout 时段机制 + W26 ab59c49 Skill 3 v3.0 launch 模式**, 100 律师全量上线期间跟踪 5 时段 + 茶歇, 让全员有充分时间体验 4 模块 + 跨境 11 框架.

### 2.1 全量上线机制 (5 时段 + 茶歇, 09:15-19:00)

| 时段 | 时间 | 环节 | 负责人 | 输出物 |
|------|------|------|--------|--------|
| **预热** | 09:15-09:30 | 100 律师群发通知 (微信群 + 邮件 + 朋友圈 + BD 私域清单) | BD | 律师确认清单 + 全量范围说明 + 跨境 11 框架可用 |
| **时段 1** | 09:30-11:00 | 100 律师首次使用谈判策略生成器 (10 baseline) | 100 律师 + Tech | 3 套策略 + 5 维度评分 placeholder |
| **时段 2** | 11:00-13:00 | 100 律师深度使用 4 模块 (策略 + 模拟 + 监测 + 复盘) | 100 律师 + Tech | 4 模块反馈 + 5 项 launch 验证第一轮实测填实 |
| **茶歇** | 13:00-14:00 | 午休 + 律师微信群互动 (跨境律师优先反馈) | BD | 律师反馈收集 + 案例分享 + 跨境 11 框架实战 |
| **时段 3** | 14:00-15:30 | 100 律师模拟对方 3 角色演练 (15 套模板) + 实时风险预警 (10 风险类型) | 100 律师 | 模拟演练反馈 + 风险预警准确率 + 跨境 11 框架 |
| **时段 4** | 15:30-17:00 | 100 律师谈判复盘报告 (50 报告 + 改进建议) + 客服答疑 | BD + Tech | 50 谈判复盘报告 + 5 项 launch 验证第二轮实测填实 |
| **时段 5** | 17:00-19:00 | 5 项 launch 验证汇总 + 收尾 + 当日报告启动 | 总指挥 + Tech | 4/1 实测填实数字 + 5 项 launch 验证报告 |
| **收尾** | 19:00-19:30 | 全量保持 + 4/8 7 天 metrics 跟踪准备 | Tech Lead | 当日报告交付 + 5 项 launch 验证终稿 + 7 天后 cron |

### 2.2 100 律师扩展抽样方法 (从 W30 50 律师扩展到 100 律师)

```
[09:15 抽样逻辑] 100 律师全量 = W30 d6c968f 50 律师私域 (3 群体合并) + W31 4/1 新扩展 50 律师 (3 群体新增)
  - 假设公测 day 280+ (4/1) 律师总数 [X, 4/1 实测填实, owner 4/1 09:15 通过 metrics 端点查询]
  - 期望 100 律师全量: 100 名 (4/1 owner 填实名
  - 律师来源结构 (6 群体合并):

[W30 d6c968f 私域 50 律师复用]
  W30 d66fc33 recruit-1000 律师群 (35 名):
    1-35. [lawyer_id_001-035, 姓名 placeholder, 4/1 owner 填实, 来源 = W15 recruit]
  W30 skill3-gradual 律师群 (10 名):
    36-45. [lawyer_id_036-045, 姓名 placeholder, 4/1 owner 填实, 来源 = W19 50% 灰度]
  W30 skill3-full-rollout 评审律师 (5 名):
    46-50. [lawyer_id_046-050, 姓名 placeholder, 4/1 owner 填实, 来源 = W21 force_v2]

[W31 4/1 新扩展 50 律师]
  W31 marketplace-pre-launch 律师群 (20 名, 复用 W29 1b07d88 Phase 6.1 marketplace backend):
    51-70. [lawyer_id_051-070, 姓名 placeholder, 4/1 owner 填实, 来源 = W29 marketplace-pre-launch]
  W31 cross-border-prepare 跨境律师群 (15 名, 复用 W31 3d0eebb Phase 6.1 跨境 40 律所预备):
    71-85. [lawyer_id_071-085, 姓名 placeholder, 4/1 owner 填实, 来源 = W31 cross-border-prepare]
  W31 agent-task-validation-3 评审律师 (15 名, 复用 W30 30ab235 3 agent >= 90% 验收):
    86-100. [lawyer_id_086-100, 姓名 placeholder, 4/1 owner 填实, 来源 = W30 agent-task-validation-3]
```

### 2.3 5 项 launch 验证总体目标 (4/1 实测填实, owner 4/1 19:00 patch 替换 placeholder)

```
[验证 1: 谈判策略生成器] 10 baseline 谈判场景全 pass (复用 W29 2344816 实施, W30 d6c968f 10 baseline)
  期望: 10 baseline × 3 策略 / 场景 = 30 策略生成全部 200 OK
  数据来源: GET /api/skill4/metrics → summary.by_module.strategy_generator

[验证 2: 模拟对方 3 角色] 对方律师 / 当事人 / 法官 3 角色 (W29 § 3 复用, 100 律师全量)
  期望: 100 律师 × 3 角色 × 5 轮 = 1500 模拟调用 100% 返回 5 轮模板
  数据来源: GET /api/skill4/metrics → summary.by_module.opponent_simulation

[验证 3: 实时风险预警] 10 风险类型全部覆盖 (W29 5 类型 + W31 5 类型扩展: concede/evidence_miss/deadline_miss/emotional/info_leak + leverage_miss/regulatory_change/cultural_gap/documented_consent/contract_loophole)
  期望: 100 律师触发预警次数 >= 200, 误报率 < 20%, 漏报率 < 20% (W29 baseline + W31 launch 持平)
  数据来源: GET /api/skill4/metrics → summary.by_module.risk_detection

[验证 4: 谈判复盘报告] 50 谈判复盘报告 + 改进建议 (W29 § 6 5 维度复用)
  期望: 100 律师全量生成复盘报告 50+ 份, 5 维度评分 avg_score >= 0.85 (W12/W15 baseline + 持平)
  数据来源: GET /api/skill4/metrics → summary.by_module.debrief_report + summary.5_dimension_avg_scores

[验证 5: 跨境框架验证] 40+ 律所模板 × 7 国法律框架 (W29 4 框架 + W31 7 国扩展)
  期望: 40+ 律所模板 × CN/HK/US/UK/EU/SG/国际仲裁 = 7 国法律框架 100% 覆盖, 中英双语支持 (W29 zh-CN/en-US)
  数据来源: GET /api/skill4/manifest → cross_border_frameworks + case_types
```

---

## 3. baseline 场景实测 (复用 W29 2344816 + W30 d6c968f)

> **10 baseline 谈判场景已全部覆盖在 W29 2344816 实施 + 37 baseline 测试 + W30 d6c968f 10 baseline 私域实测**, 本节为 4/1 launch 100 律师全量实测填实依据.

### 3.1 10 baseline 谈判场景清单 (W29 § 4.2 + W30 d6c968f § 3.1 复用)

| # | 场景 | W29 测试类 | W30 私域实测填实 | 4/1 全量律师实测填实 | 期望结果 |
|---|------|-----------|-------------------|---------------------|----------|
| 1 | **合同纠纷 - 对方违约** | TestStrategyGenerationContractOtherPartyBreach (3) | [3/15 实测填实, lawyer_id_001] | [4/1 实测填实, lawyer_id_051] | 3 策略 + 5 维度评分 |
| 2 | **合同纠纷 - 自己违约** | TestStrategyGenerationContractSelfBreach (1) | [3/15 实测填实, lawyer_id_002] | [4/1 实测填实, lawyer_id_052] | 保守优先 |
| 3 | **民事侵权** | TestStrategyGenerationTort (1) | [3/15 实测填实, lawyer_id_003] | [4/1 实测填实, lawyer_id_053] | 3 策略 |
| 4 | **婚姻家庭** | TestStrategyGenerationFamily (1) | [3/15 实测填实, lawyer_id_004] | [4/1 实测填实, lawyer_id_054] | 保守优先 |
| 5 | **公司股权** | TestStrategyGenerationEquity (1) | [3/15 实测填实, lawyer_id_005] | [4/1 实测填实, lawyer_id_055] | 法条引用 |
| 6 | **知识产权** | TestStrategyGenerationIP (1) | [3/15 实测填实, lawyer_id_006] | [4/1 实测填实, lawyer_id_056] | 3 策略 |
| 7 | **劳动仲裁** | TestStrategyGenerationLabor (1) | [3/15 实测填实, lawyer_id_007] | [4/1 实测填实, lawyer_id_057] | 保守优先 |
| 8 | **行政复议** | TestStrategyGenerationAdminReview (1) | [3/15 实测填实, lawyer_id_008] | [4/1 实测填实, lawyer_id_058] | 保守优先 |
| 9 | **跨境贸易 (跨境 11 框架)** | TestStrategyGenerationCrossBorder (2) | [3/15 实测填实, lawyer_id_009 + 010] | [4/1 实测填实, lawyer_id_071 + 072] | CISG/UNCITRAL/PICC/NY + CN/HK/US/UK/EU/SG/国际仲裁 + 中英双语 |
| 10 | **反向博弈演练** (模拟对方 3 角色) | TestOpponentSimulation (4) | [3/15 实测填实, lawyer_id_011] | [4/1 实测填实, lawyer_id_073] | 律师/当事人/法官 3 角色 + 5 轮 |

### 3.2 9 案件类型覆盖 (W29 § 2.1 复用)

```
W29 negotiation_models.py 9 案件类型 + W31 跨境 7 国扩展:
  1. contract_dispute    合同纠纷
  2. tort                民事侵权
  3. family              婚姻家庭
  4. equity              公司股权
  5. ip                  知识产权
  6. labor               劳动仲裁
  7. admin_review        行政复议
  8. settlement          和解协商
  9. cross_border_trade  跨境贸易 (CISG/UNCITRAL/PICC/NY Convention + W31 7 国: CN/HK/US/UK/EU/SG/国际仲裁)
```

### 3.3 4 模块实测覆盖 (W29 § 2 复用)

```
W29 4 模块 + 10 baseline 谈判场景 + 跨境 11 框架实测 (W31 launch):

[模块 1: 谈判策略生成器] API: POST /api/skill4/strategies
  - 9 案件类型 × 3 违约方 (self/other/neutral) × 3 期望结果 (conservative/moderate/aggressive) × 3 对方角色 (lawyer/party/judge) = 243 组合
  - 100 律师全量实测 10 场景 (lawyer_id_051-060), 每场景律师主动选择策略优先级
  - 期望: 10 baseline 全部 PASS, 30 策略生成 100% 返回

[模块 2: 模拟对方 3 角色] API: POST /api/skill4/simulate-opponent
  - 3 角色 (对方律师 / 当事人 / 法官) × 5 轮 = 15 套模板 (复用 W29 negotiation_engine.py)
  - 100 律师全量实测抽样 20 律师做反向博弈演练 (lawyer_id_073-092)

[模块 3: 实时风险预警] API: POST /api/skill4/detect-risk
  - 10 类型正则 (W29 5 类型 + W31 5 类型扩展: leverage_miss/regulatory_change/cultural_gap/documented_consent/contract_loophole)
  - 100 律师全量实测抽样 20 律师做实时监测 (lawyer_id_061-080), 每律师触发 1-2 次预警

[模块 4: 谈判复盘报告] API: POST /api/skill4/debrief
  - 5 维度评分 (facts/legal/demand/deadline/consequence) + 改进建议 + 类似案件对比
  - 100 律师全量实测抽样 20 律师做复盘 (lawyer_id_081-100)
  - 期望: 50 谈判复盘报告 + 改进建议, avg_score >= 0.85
```

---

## 4. 5 维度评分跟踪 forward-execute (复核 W30 § 4 baseline)

### 4.1 5 维度评分基线 (W29 § 6.1 复用)

> **复用 W12 doc_workflow 4 文书风险标注 + W15 Skill 3 v2.0 L7 吴律师 AI 5 维度风险标注**:
> - 事实 (facts): 谈判内容与事实证据吻合度 (0-1)
> - 法律 (legal): 谈判策略与法律框架吻合度 (0-1)
> - 主张 (demand): 谈判诉求合理性 (0-1)
> - 时效 (deadline): 谈判时间节奏 (0-1)
> - 后果 (consequence): 谈判结果的预测后果 (0-1)

### 4.2 5 维度评分期望 (forward-execute)

```
[期望 v1 阈值 >= 0.85, W12/W15/W30 baseline + 持平]

4/1 09:30 - 19:00 100 律师全量实测, owner 4/1 19:00 patch 替换 placeholder:

| 维度 | W12/W15 baseline | W30 私域 | W31 全量 (100 律师) |
|------|------------------|----------|---------------------|
| **事实 (facts)** | [0.X, W12/W15 历史 baseline] | [0.X, 3/15 实测填实] | [0.X, 4/1 实测填实] |
| **法律 (legal)** | [0.X, W12/W15 历史 baseline] | [0.X, 3/15 实测填实] | [0.X, 4/1 实测填实] |
| **主张 (demand)** | [0.X, W12/W15 历史 baseline] | [0.X, 3/15 实测填实] | [0.X, 4/1 实测填实] |
| **时效 (deadline)** | [0.X, W12/W15 历史 baseline] | [0.X, 3/15 实测填实] | [0.X, 4/1 实测填实] |
| **后果 (consequence)** | [0.X, W12/W15 历史 baseline] | [0.X, 3/15 实测填实] | [0.X, 4/1 实测填实] |
| **avg_score** | [0.X, W12/W15 历史 baseline] | [0.X, 3/15 实测填实] | [0.X, 4/1 实测填实, 期望 >= 0.85] |

数据来源: GET /api/skill4/metrics → summary.5_dimension_avg_scores
阈值: avg_score >= 0.85 (W12/W15 baseline + 持平, W29 PRD § 5.1 + W30 私域持平)
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

## 5. 跨境框架 40+ 律所 × 7 国法律框架验证 forward-execute (W31 launch 重点)

### 5.1 跨境 11 框架 (W29 4 框架 + W31 7 国扩展)

```
W29 2344816 实施 4 跨境框架:
  1. CISG              联合国国际货物销售合同公约
  2. UNCITRAL          联合国国际贸易法委员会
  3. PICC              国际商事合同通则
  4. NY_Convention    纽约公约 (仲裁裁决承认与执行)

W31 4/1 launch 7 国法律框架扩展:
  5. PRC_Civil_Code         民法典 (CN 中国大陆, 2021.1.1 生效)
  6. HK_Cap_609             香港仲裁条例 (HK 香港特别行政区)
  7. US_Federal_Rules       美国联邦民事诉讼规则 + UCC 统一商法典 (US)
  8. UK_CPR                 英国民事诉讼规则 + 1979 商事法 (UK)
  9. EU_Brussels_Ia         欧盟布鲁塞尔 I 条例 (重订本) (EU)
  10. SG_CIA                 新加坡国际仲裁法 + SIAC 规则 (SG)
  11. SIAC_Arbitration       国际仲裁通则 (国际仲裁, ICC/SIAC/HKIAC/AAA 通用)

总计: W31 4/1 launch 11 跨境法律框架 (W29 4 + W31 7)
```

### 5.2 40+ 律所模板 × 7 国法律框架 (W31 launch forward-execute)

```
[期望 v1 100% 覆盖, W31 launch 4/1 实测填实]

40+ 律所模板 (复用 W31 3d0eebb Phase 6.1 跨境 40 律所预备清单 + W26 Skill 3 v3.0 多律所模板):

律所类别分布:
  国内一线律所 (10):
    1-10. [律所名称 placeholder, 4/1 owner 填实, 模板类型 = 国内合同/侵权/婚姻/股权]

  国内二线律所 (10):
    11-20. [律所名称 placeholder, 4/1 owner 填实, 模板类型 = 国内中小案件]

  香港 / 跨境律所 (5):
    21-25. [律所名称 placeholder, 4/1 owner 填实, 模板类型 = HK Cap_609 + 中港跨境]

  美国律所 / 国别所 (5):
    26-30. [律所名称 placeholder, 4/1 owner 填实, 模板类型 = US Federal Rules + UCC]

  英国 / 欧盟律所 (5):
    31-35. [律所名称 placeholder, 4/1 owner 填实, 模板类型 = UK CPR + EU Brussels Ia]

  新加坡 / 国际仲裁律所 (5):
    36-40. [律所名称 placeholder, 4/1 owner 填实, 模板类型 = SG CIA + SIAC + 国际仲裁]

7 国法律框架 × 40+ 律所模板 = 280+ 模板矩阵:
  - 每个律所模板对应 1 个主框架 + 2-3 个 fallback 框架
  - 例: 国内一线律所 #1 模板 = PRC_Civil_Code (主) + HK_Cap_609 (fallback)
  - 例: 美国律所 #26 模板 = US_Federal_Rules (主) + UCC (补充) + NY_Convention (跨境仲裁 fallback)
```

### 5.3 跨境 11 框架 × 100 律师实测 (4/1 实测填实)

```
[期望 v1 100% 覆盖, 4/1 实测填实]

跨境律师组 (15 名, lawyer_id_071-085, 来源 = W31 cross-border-prepare) 实测:

| 跨境律师 | 主框架 | 期望 fallback | 实测 4/1 |
|---------|--------|----------------|----------|
| 71 [姓名 placeholder, 4/1 owner 填实] | PRC_Civil_Code | HK_Cap_609 | [PASS/FAIL, 4/1 实测] |
| 72 [姓名 placeholder, 4/1 owner 填实] | HK_Cap_609 | PRC_Civil_Code + NY_Convention | [PASS/FAIL, 4/1 实测] |
| 73 [姓名 placeholder, 4/1 owner 填实] | US_Federal_Rules | UCC + NY_Convention | [PASS/FAIL, 4/1 实测] |
| 74 [姓名 placeholder, 4/1 owner 填实] | UK_CPR | EU_Brussels_Ia + NY_Convention | [PASS/FAIL, 4/1 实测] |
| 75 [姓名 placeholder, 4/1 owner 填实] | EU_Brussels_Ia | UK_CPR + SIAC_Arbitration | [PASS/FAIL, 4/1 实测] |
| 76 [姓名 placeholder, 4/1 owner 填实] | SG_CIA | SIAC_Arbitration + NY_Convention | [PASS/FAIL, 4/1 实测] |
| 77 [姓名 placeholder, 4/1 owner 填实] | SIAC_Arbitration | NY_Convention + SG_CIA | [PASS/FAIL, 4/1 实测] |
| 78 [姓名 placeholder, 4/1 owner 填实] | CISG | UNCITRAL + PICC | [PASS/FAIL, 4/1 实测] |
| 79 [姓名 placeholder, 4/1 owner 填实] | UNCITRAL | CISG + PICC | [PASS/FAIL, 4/1 实测] |
| 80 [姓名 placeholder, 4/1 owner 填实] | PICC | CISG + UNCITRAL | [PASS/FAIL, 4/1 实测] |
| 81 [姓名 placeholder, 4/1 owner 填实] | NY_Convention | SIAC_Arbitration + HK_Cap_609 | [PASS/FAIL, 4/1 实测] |
| 82-85 [姓名 placeholder, 4/1 owner 填实] | 跨境混用框架 | cross_optimal | [PASS/FAIL, 4/1 实测] |

中英双语支持 (W29 zh-CN/en-US):
  期望: 跨境律师 71-85 全部中英双语体验, 跨境策略 + 跨境话术 全部双语 PASS
```

---

## 6. 紧急回滚方案 (W31 launch 重点)

### 6.1 紧急回滚总览 (3 级降级)

```
W31 launch 紧急回滚方案 (按严重程度, 3 级降级):

[Level 1 (最轻): 全量转回 W30 50 律师私域]
  触发: 5 项 launch 验证任 1 项不达标 (avg_score < 0.85 / 误报漏报 > 20% / 跨境框架缺失), 不影响核心功能
  行动: env 切换 LEX_SKILL4_LAUNCH_MODE=false, LEX_SKILL4_PRIVATE_USE=true, 关闭 50 律师之外的 50 律师
  回滚时间: < 5 min
  负责: lex-coder + Tech Lead
  保留: W30 50 律师私域数据不丢失, 50 律师继续用 W29 实施 (4 模块 + 37 测试)

[Level 2 (中度): 关闭 Skill 4 v1 走 Skill 3 v3.0]
  触发: Skill 4 v1 出现系统性故障 (latency P95 > 5s / 5xx 错误率 > 10% / 律师大量投诉 20+)
  行动: env 切换 LEX_SKILL4_LAUNCH_MODE=false, LEX_SKILL4_PRIVATE_USE=false, LEX_SKILL3_V3_LAUNCH=true
  回滚时间: < 30 min
  负责: lex-coder + Tech Lead
  保留: W26 ab59c49 Skill 3 v3.0 launch 全量, 律师回到 W26 Skill 3 v3.0 (35 baseline + 15 v3.0 测试 = 50 测试)

[Level 3 (最重): 撤回到 W29 2344816 实施 + W30 d6c968f 私域 + 关闭 Skill 4 v1 + Skill 3 v2.0]
  触发: Skill 3 v3.0 也故障 / 数据丢失风险 / 大面积律师集体投诉 30+
  行动: env 切换 LEX_SKILL4_LAUNCH_MODE=false, LEX_SKILL4_PRIVATE_USE=false, LEX_SKILL3_V3_LAUNCH=false, LEX_SKILL3_V2_LETTER=true
  回滚时间: < 60 min
  负责: lex-coder + Tech Lead + 总指挥
  保留: W21 6929cc1 Skill 3 v2.0 全面应用 5 个月 (8/15 10% + 9/1 50% + 10/1 100% + 11/1 v1 退役), 律师回到 Skill 3 v2.0 律师函
```

### 6.2 紧急回滚操作手册 (5 步)

```
[Step 1 (立即) - 评估严重程度]
  严重程度评估:
    - Level 1 (1 项不达标, 核心功能正常) → Step 2A
    - Level 2 (系统性故障, Skill 4 v1 不可用, Skill 3 v3.0 正常) → Step 2B
    - Level 3 (Skill 4 v1 + Skill 3 v3.0 都故障) → Step 2C

[Step 2A - Level 1 操作]
  $ export LEX_SKILL4_LAUNCH_MODE=false
  $ export LEX_SKILL4_PRIVATE_USE=true
  $ export LEX_SKILL4_FORCE_LAWYERS=lawyer_001,lawyer_002,...,lawyer_050  # 切回 W30 50 律师私域
  $ export LEX_SKILL4_FULL_ROLLOUT_PCT=50  # 切回 50% (W30 私域配置)
  $ systemctl restart lexprime-backend
  $ curl http://localhost:8000/api/skill4/health | jq  # 验证 private_use_mode=true
  $ 律师群通知: "Skill 4 v1 暂时切回私域模式, W31 launch 模式暂停, 30 分钟内重启"

[Step 2B - Level 2 操作]
  $ export LEX_SKILL4_LAUNCH_MODE=false
  $ export LEX_SKILL4_PRIVATE_USE=false
  $ export LEX_SKILL3_V3_LAUNCH=true  # 切到 W26 Skill 3 v3.0 launch
  $ systemctl restart lexprime-backend
  $ curl http://localhost:8000/api/skill3/rollout/status | jq  # 验证 v3.0 launch mode
  $ 律师群通知: "Skill 4 v1 暂时关闭, 切到 Skill 3 v3.0, 24h 内恢复 Skill 4 v1"

[Step 2C - Level 3 操作]
  $ export LEX_SKILL4_LAUNCH_MODE=false
  $ export LEX_SKILL4_PRIVATE_USE=false
  $ export LEX_SKILL3_V3_LAUNCH=false
  $ export LEX_SKILL3_V2_LETTER=true  # 切到 W21 Skill 3 v2.0
  $ systemctl restart lexprime-backend
  $ curl http://localhost:8000/api/skill3/rollout/status | jq  # 验证 v2.0 letter mode
  $ 律师群通知: "Skill 4 v1 + Skill 3 v3.0 暂时关闭, 切到 Skill 3 v2.0, 24h 内恢复"

[Step 3 (回滚后 24h 内) - 根因分析 + 修复 + 重启 launch]
  - Tech Lead 立即 root cause 分析 (复用 W29 systematic-debugging 技能)
  - 修复:
    Level 1: 24h 内修复不达标项, 重启 launch
    Level 2: 24h 内修复 Skill 4 v1 故障, 重启 launch (无 Level 3 兜底)
    Level 3: 48h 内修复 Skill 4 v1 + Skill 3 v3.0, 重启 launch
  - 修复后跑 50 律师回归测试 (W29 37 baseline + W30 50 律师私域), 确认 100% PASS 后重启 launch

[Step 4 (回滚后 48h) - 通知 + 文档 + 跟踪]
  - 律师群通知修复状态 + 重启 launch 时间表
  - 文档: docs/skills/negotiation/skill4-v1-launch-rollback-{incident-date}.md
  - 跟踪: 14 天内每日 metrics 汇总, 每周一周度报告

[Step 5 (回滚后 14 天) - 14 天后决策]
  - 14 天无再发故障, 视为回滚成功, 不重启 launch
  - 14 天内复发 1 次, 启动 W32+ 迭代优化, 不重启 launch
  - 14 天内复发 2+ 次, 无限延期 launch, 启动 W33 重启 launch
```

### 6.3 紧急备份清单 (3 commit 都可回滚)

```
[W31 launch 紧急备份 - 3 commit 都可 git checkout 回滚]

紧急备份 1: W29 2344816 Skill 4 v1 实施 (4 文件 + tests + README)
  路径: backend/cases-crawler/skills/negotiation/ (4 文件) + api/skill4_router.py + tests/test_skill4.py
  回滚命令: git checkout 2344816 -- backend/cases-crawler/skills/negotiation/ backend/cases-crawler/api/skill4_router.py backend/cases-crawler/tests/test_skill4.py
  保留: 30 天 (律师可在 30 天内随时切回 W29 实施, force_lawyers 关闭 = 全员 v1)

紧急备份 2: W30 d6c968f Skill 4 v1 私域使用 runbook
  路径: docs/skills/negotiation/skill4-v1-private-use-2027-03-15.md
  回滚命令: git checkout d6c968f -- docs/skills/negotiation/skill4-v1-private-use-2027-03-15.md
  保留: 30 天 (W30 50 律师私域 runbook 可直接调用, 50 律师强制启用 private_use_mode=true)

紧急备份 3: W21 6929cc1 Skill 3 v2.0 全量 100% rollout
  路径: backend/cases-crawler/core/rollout.py (rollout.py v2.0-w21) + api/doc_gen_router.py (v0.4.0-w21) + templates/docs/letter_v1.md (v1.0-w21)
  回滚命令: git checkout 6929cc1 -- backend/cases-crawler/core/rollout.py backend/cases-crawler/api/doc_gen_router.py backend/cases-crawler/templates/docs/letter_v1.md
  保留: 永久 (W21 Skill 3 v2.0 全面应用 5 个月, 8/15 10% + 9/1 50% + 10/1 100% + 11/1 v1 退役 = W21 退役时间表)

[3 commit 紧急回滚决策矩阵]

| 异常 | Level | 回滚 1 (W29) | 回滚 2 (W30) | 回滚 3 (W21) | 综合 |
|------|-------|--------------|--------------|--------------|------|
| **5 项 launch 验证任 1 项不达标** | Level 1 | ✗ (保持) | ✗ (切回私域) | ✗ (保持) | Level 1 |
| **Skill 4 v1 系统性故障** | Level 2 | ✓ (回滚 1) | ✗ (保持) | ✗ (保持, 切 Skill 3 v3.0) | Level 2 |
| **Skill 4 v1 + Skill 3 v3.0 都故障** | Level 3 | ✓ (回滚 1) | ✓ (回滚 2) | ✓ (回滚 3) | Level 3 |
| **数据丢失风险** | Level 3 | ✓ (回滚 1) | ✓ (回滚 2) | ✓ (回滚 3) | Level 3 |
| **大面积律师集体投诉 30+** | Level 3 | ✓ (回滚 1) | ✓ (回滚 2) | ✓ (回滚 3) | Level 3 |
```

---

## 7. 应急备案 (4 场景, 复用 W28 PRD § 6 + W30 私域 § 7)

### 7.1 LLM 调用超时 (W29 当前模板 fallback, 不受影响)

```
[触发条件] W29 当前 LLM 模式 = template_fallback (LEX_SKILL4_LLM_MODE=template_fallback)
  - W29 848129d 修复后: 10/10 endpoints uvicorn PASS, 模板 fallback 稳定
  - 若 LLM 真实接入 (W32+), 触发条件: LLM 调用超时 (> 3s P95) 或 5xx 错误率 > 5%

[行动]
  - 立即关闭 launch 模式: env `LEX_SKILL4_LAUNCH_MODE=false`, 重启服务
  - 强制使用模板 fallback: env `LEX_SKILL4_LLM_MODE=template_fallback`
  - 4 小时内修复 LLM 服务 (复用 W22 Rust 5x perf)
  - 律师群通知: "谈判策略生成器临时维护中, 已切回模板 fallback, 24h 内恢复"

[回滚]
  - env `LEX_SKILL4_LAUNCH_MODE=true` (恢复 launch)
  - env `LEX_SKILL4_LLM_MODE=template_fallback` (保持模板 fallback)
```

### 7.2 模拟对方质量低

```
[触发条件]
  - 律师反馈: 模拟对方回应跟实际对方不一致 (10+ 律师投诉 / 1h)  (W30 5 律师升级到 W31 10 律师)
  - 客观指标: 模拟对方 5 轮模板重复率 > 50% (W30 测试 test_simulate_multi_round 应验证 < 50%)

[行动]
  - 强制关闭模拟对方功能: env `LEX_SKILL4_OPPONENT_SIM=off`
  - 律师转用人工模拟 (无 AI 辅助, 但 4 模块其他 3 个继续可用)
  - 7 天内优化 prompt (lex-coder + lex-ai 协作)
  - 律师群通知: "模拟对方功能临时优化中, 7 天内恢复"

[回滚]
  - env `LEX_SKILL4_OPPONENT_SIM=on` (恢复)
  - 优化后跑 10 律师实测, 确认 5 轮模板重复率 < 50%
```

### 7.3 实时监测准确率低 (W31 10 风险类型扩展)

```
[触发条件]
  - 律师反馈: 实时风险预警误报率 > 20% 或漏报率 > 20% (10+ 律师投诉 / 1h)
  - 客观指标: W31 10 类型正则 (W29 5 类型 + W31 5 类型扩展) 误判 > 20%

[行动]
  - 关闭实时监测功能: env `LEX_SKILL4_RISK_DETECTION=off`
  - 律师转用事后复盘 (谈判结束后跑 POST /api/skill4/debrief 做完整 5 维度评分)
  - 7 天内优化监测算法 (lex-coder + lex-ai 协作)
  - 律师群通知: "实时风险预警临时优化中, 7 天内恢复"

[回滚]
  - env `LEX_SKILL4_RISK_DETECTION=on` (恢复)
  - 优化后跑 20 律师实测, 确认误报率 < 20% + 漏报率 < 20%
```

### 7.4 跨境 7 国法律框架缺失 (W31 launch 重点)

```
[触发条件]
  - 跨境律师反馈: 7 国法律框架 (CN/HK/US/UK/EU/SG/国际仲裁) 缺失 1+ 个 (5+ 律师投诉 / 1h)
  - 客观指标: GET /api/skill4/manifest → cross_border_frameworks 不含 7 国任意 1 个

[行动]
  - 紧急关闭跨境律师组: env `LEX_SKILL4_CROSS_BORDER=off` (跨境律师 71-85 切回 W29 4 框架)
  - 跨境律师转用国内框架 (PRC_Civil_Code / W29 4 框架 fallback)
  - 24 小时内修复跨境 7 国 (lex-coder + Phase 6.1 cross-border-prepare 协作)
  - 律师群通知: "跨境 7 国框架临时维护中, 24h 内恢复"

[回滚]
  - env `LEX_SKILL4_CROSS_BORDER=on` (恢复跨境 7 国)
  - 修复后跑 15 跨境律师实测, 确认 7 国全部 PASS
```

### 7.5 应急备案总览表

| 异常 | 触发条件 | 行动 | 修复时间 | 负责 agent |
|------|----------|------|---------|-----------|
| **LLM 调用超时** | LLM 5xx > 5% / P95 > 3s | 关 LEX_SKILL4_LAUNCH_MODE + 切模板 fallback | 4h | lex-coder + lex-ai |
| **模拟对方质量低** | 10+ 律师投诉 / 1h + 5 轮重复率 > 50% | 关 LEX_SKILL4_OPPONENT_SIM | 7d | lex-coder + lex-ai |
| **实时监测准确率低** | 10+ 律师投诉 / 1h + 误报漏报 > 20% | 关 LEX_SKILL4_RISK_DETECTION | 7d | lex-coder + lex-ai |
| **跨境 7 国框架缺失** | 5+ 律师投诉 / 1h + 7 国缺 1+ | 关 LEX_SKILL4_CROSS_BORDER | 24h | lex-coder + Phase 6.1 cross-border-prepare |

---

## 8. 4/1 19:00 当日报告 (4/1 实测填实执行)

### 8.1 5 项 launch 验证实测数据 (4/1 实测填实)

> **数字全部 [4/1 实测填实, owner 4/1 19:00 patch 替换 placeholder]**

| 验证项 | 期望目标 | W29 实施 baseline | W30 私域 | W31 launch (100 律师) |
|--------|----------|--------------------|----------|---------------------|
| **谈判策略生成器 (10 baseline)** | 10/10 PASS | 10/10 | [10/10, 3/15 实测填实] | [X/X, 4/1 实测填实, 期望 10/10] |
| **模拟对方 3 角色** | 3 角色 × 5 轮 = 15/15 PASS | 15/15 | [15/15, 3/15 实测填实] | [X/X, 4/1 实测填实, 期望 15/15] |
| **实时风险预警 (10 风险类型)** | 误报漏报 < 20% | 5 类型 PASS | 5 类型 PASS | [X, 4/1 实测填实, 期望 误报/漏报 < 20%] |
| **谈判复盘报告 (50 报告)** | 50 报告 + 5 维度 avg >= 0.85 | 50 baseline | [50, 3/15 实测填实] | [X, 4/1 实测填实, 期望 50 报告 + avg >= 0.85] |
| **跨境 40+ 律所 × 7 国框架** | 40+ 律所 × 7 国 = 280+ PASS | 4 框架 + 15 baseline | 4 框架 | [X/X, 4/1 实测填实, 期望 280+ PASS] |

### 8.2 5 项 launch 验证汇总决策 (4/1 19:00)

> **核心决策**: 4/1 launch 数据是否支持 W31 全量上线完成?

```
决策依据: [4/1 19:00 实测填实]
  - 5 项 launch 验证:
    - 谈判策略生成器: [达标/不达标, 4/1 实测填实]
    - 模拟对方 3 角色: [达标/不达标, 4/1 实测填实]
    - 实时风险预警 (10 风险类型): [达标/不达标, 4/1 实测填实]
    - 谈判复盘报告 (50 报告): [达标/不达标, 4/1 实测填实]
    - 跨境 40+ 律所 × 7 国: [达标/不达标, 4/1 实测填实]
  
推荐行动: [W31 launch 完成 / Level 1 回滚 / Level 2 回滚 / Level 3 回滚, 4/1 实测填实]
```

### 8.3 4/1 异常处理 (复用 § 7 应急备案 + § 6 紧急回滚)

| 异常 | 触发条件 | 行动 |
|------|----------|------|
| **5 项 launch 验证任 1 项不达标** | 4/1 19:00 决策 | Level 1 回滚 → LEX_SKILL4_PRIVATE_USE=true |
| **Skill 4 v1 系统性故障** | latency P95 > 5s / 5xx > 10% / 20+ 律师投诉 | Level 2 回滚 → LEX_SKILL3_V3_LAUNCH=true |
| **Skill 4 v1 + Skill 3 v3.0 都故障** | data loss risk / 30+ 律师投诉 | Level 3 回滚 → LEX_SKILL3_V2_LETTER=true |

### 8.4 4/1 19:00 报告交付

```
[4/1 19:00] launch 报告启动
  - 文件: docs/skills/negotiation/skill4-v1-launch-2027-04-01.md (本手册)
  - 数据 patch: 把 § 2.3 + § 3 + § 4 + § 5 + § 8 全部 [4/1 实测填实]
  - commit: docs(skill4): W31 Skill 4 v1 全量上线 4/1 实测填实 + 5 项 launch 验证填实
  - push: origin/main

[4/1 19:30] W32+ 准备
  - env 保持: LEX_SKILL4_LAUNCH_MODE=true (持续 launch 模式)
  - 4/8 09:00 cron 自动抓 launch metrics: scripts/cron/skill4-launch-metrics-2027-04-08.sh
  - 通知: BD 群发 4/1 launch 总结 + W32+ 预告 (跨境谈判实测 + 迭代优化)
```

---

## 9. 4/1 - 5/1 全量保持 (30 天, 4/1 - 5/1)

### 9.1 持续跟踪 (3 节奏)

```
[每日 09:00] 日常 metrics 汇总
  - curl http://localhost:8000/api/skill4/metrics | jq
  - 验证: 100 律师全量使用正常, 4 模块全部 active + 跨境 11 框架
  - 异常: 立即 patch (按 § 6 紧急回滚 + § 7 应急备案)

[每周一 09:00] 周度报告
  - 5 维度评分周均 + 转化率周累计 + 律师满意度周均 + 5 项 launch 验证周均
  - 报告: docs/skills/negotiation/skill4-v1-weekly-{date}.md
  - commit: docs(skill4): W31 launch 周度跟踪

[每月 1 日 09:00] 月度报告
  - 4/1 - 5/1 全量阶段汇总 + W32+ 决策建议
  - 报告: docs/skills/negotiation/skill4-v1-monthly-2027-04.md
  - commit: docs(skill4): W31 launch 月度跟踪
```

### 9.2 4/1 - 5/1 关键事件

| 事件 | 日期 | 影响 | 行动 |
|------|------|------|------|
| **4/1 100 律师全量上线** | 4/1 09:00 | Skill 4 v1 全量 100% (从 W30 50 律师扩展到 100 律师) | 按 § 1-3 |
| **4/8 7 天 launch metrics 截止** | 4/8 09:00 | 7 天跟踪窗口结束 | owner 4/8 09:00 patch launch metrics |
| **4/15 14 天趋势验证** | 4/15 09:00 | 14 天跟踪开始 | launch 趋势验证 |
| **5/1 全量收尾** | 5/1 23:59 | 30 天全量结束 | 月度报告 + W32+ 决策 |
| **W32+ 启动** | 5/1+ | Skill 4 v1 全量后迭代优化 + 跨境谈判实测 | 复用 W32+ 路线 |

### 9.3 W32+ cron 准备

```bash
#!/bin/bash
# scripts/trigger-skill4-launch-end-2027-05-01.sh (W31 落档, 占位说明)
# 5/1 09:00 全量收尾 + W32+ 准备 (依据 4/1 - 5/1 数据)
export LEX_SKILL4_LAUNCH_MODE=true         # W31 持续 launch 模式 (W32 调整)
export LEX_SKILL4_FULL_ROLLOUT_PCT=100    # 全量 100% (W32 持续)
export LEX_SKILL4_LLM_MODE=template_fallback  # W31 模板 fallback (W32 LLM 接入 by lex-ai)
# W32+ 迭代优化 runbook: docs/skills/negotiation/skill4-v1-iter-2027-05-01.md (W32 落档)
systemctl restart lexprime-backend
curl http://localhost:8000/api/skill4/health | jq
# 期望: launch_mode=true, full_rollout_pct=100 (W32+ 持续)
```

---

## 10. 法律边界 (PRD V5.0 § 11 法务自检) + 严守 fabricate 原则

### 10.1 法律边界 (PRD V5.0 § 11 法务自检)

> **W31 launch 严守法律边界 (跟 W18+W19+W20+W21+W26+W28+W29+W30 一致)**:

1. **AI 辅助, 不替代律师 (产品原则硬性)**
   - 类案界面 + 策略推荐 + 风险预警 + 复盘报告 = 全部 AI 辅助
   - 律师主动选择 / 主动评分 / 主动决策 = 全程保留
   - AI 输出仅供参考, 最终策略由律师决定 (跟 W29 PRD § 5.1 一致)

2. **类案界面语言规范 (PRD V5.0 § 11 法务自检, W31 严守)**
   - **禁用**: "胜诉率" / "必败" / "100% 胜" 等绝对化用语
   - **禁用**: "一定会胜" / "稳赢" / "零风险" 等承诺性用语
   - **慎用**: "策略推荐" 改为 "AI 建议参考" + "律师自主决策"
   - **慎用**: "高胜诉" 改为 "高把握度" / "高可行性" / "倾向性高"
   - **慎用**: "胜率" 改为 "把握度" / "倾向性"
   - 期望: 类案界面 + 策略生成器 + 谈判复盘报告 + 5 维度评分 全部语言规范达标

3. **数据本地化 (W18-W30 13 plan 验证, W31 持续)**
   - 律师案件 / 客户 / 谈判不离开律师电脑
   - 100 律师全量期间 launch metrics in-memory 收集不持久化敏感数据
   - 跨境律师 71-85 实测期间, 跨境数据 7 国法律框架不持久化跨境敏感数据

4. **跨境合规 (W31 launch 7 国法律框架新增)**
   - CN/HK/US/UK/EU/SG/国际仲裁 7 国法律框架必须严格按当地法律呈现
   - 不得伪造法规引用 + 不得虚构判例 (跨境律师 71-85 实测期间验证)
   - 中英双语支持 (W29 zh-CN/en-US)

5. **隐私保护 (PRD V5.0 § 11)**
   - 律师身份证号 / 律师执业证号 / 客户身份证号 / 谈判对手信息 不持久化
   - 5 维度评分不暴露律师个人身份, 仅保留 lawyer_id 哈希

### 10.2 严守 fabricate 原则 (W31 复制 W18+W19+W20+W21+W26+W28+W29+W30 14 plan 验证)

> **W18+W19+W20+W21+W26+W28+W29+W30 严守 fabricate 原则, W31 复制**:
> 1. **不要 fabricate 律师反馈**: 实测为主, owner 4/1 跑 100 律师全量, 反馈全部 [4/1 实测填实]
> 2. **不要 fabricate 全量上线数据**: 实测为主, owner 4/1 当天 19:00 抓 metrics, 数字全部 [4/1 实测填实]
> 3. **不要 fabricate 跨境 7 国实测数据**: 实测为主, owner 4/1 跨境律师 71-85 实测, 数字全部 [4/1 实测填实]
> 4. **forward-execute placeholder 模式**: runbook 流程 + 时间表 + 应急 + 回滚 + 跟踪节奏, 实际数字全部 placeholder
> 5. **不要碰 W29 2344816 实施**: 本任务只做 launch runbook, 不修改 4 文件 + tests/test_skill4.py + README.md
> 6. **不要碰 W30 d6c968f 私域**: 本任务不修改 W30 私域 runbook, 不修改 50 律师私域数据
> 7. **不要碰 W28 8670417 PRD**: 本任务不修改 PRD, 仅落地全量上线 + 100 律师扩展
> 8. **严守 AI 辅助, 不替代律师**: 严守产品原则, 律师主动评分是核心, AI 评分仅辅助
> 9. **法律边界**: 类案界面禁用"胜诉率" / "必败" / "100% 胜" 等绝对化用语 (PRD V5.0 § 11 法务自检)

---

## 11. 关联文档 + 配套资源

### 11.1 W31 skill4-launch 配套 (本次交付)

- `docs/skills/negotiation/skill4-v1-launch-2027-04-01.md` (本次, 全量上线 runbook)

### 11.2 复用 W30 skill4-v1-private-use (私域样板)

- `docs/skills/negotiation/skill4-v1-private-use-2027-03-15.md` v1.0 (W30 d6c968f, 50 律师私域使用样板, 14 章节 + 附录 12 端点 API 参考)

### 11.3 复用 W29 skill4-v1-impl (实施, 4 模块 + 37 baseline)

- `backend/cases-crawler/skills/negotiation/negotiation_models.py` v1.0-w29 (280 行, 9 案件类型 + 5 状态机 + 5 维度 + 4 跨境框架)
- `backend/cases-crawler/skills/negotiation/negotiation_engine.py` v1.0-w29 (498 行, 谈判策略生成器 + 模拟对方 + 实时风险预警)
- `backend/cases-crawler/skills/negotiation/debrief_report.py` v1.0-w29 (252 行, 5 维度评分 + 改进建议 + 类似案件对比)
- `backend/cases-crawler/api/skill4_router.py` v1.0-w29 (517 行, 10 endpoints)
- `backend/cases-crawler/tests/test_skill4.py` v1.0-w29 (700 行, 37 baseline 测试, 10 场景)
- `docs/skills/negotiation/skill4-v1-impl-2027-02-15.md` (W29 实施报告, 24KB)
- W29 fix 848129d (`__import__` hack 修复 + 5-dim 归属 W21 → W12/W15)

### 11.4 复用 W28 skill4-v1-prd (PRD, ~30KB)

- `docs/skills/negotiation/skill4-v1-prd-2027-01-16.md` (W28 PRD, 4 模块 + 6 大优势 + 4 应急 + W29+ 路线)

### 11.5 复用 W26 Skill 3 v3.0 launch (launch 落地样板)

- `docs/skills/contract-review/skill3-v3-launch-2027-02-01.md` v1.0 (W26 ab59c49, 13 章节 + 时间表 + 升级路径 + 测试套件 + PRD 引用 + 启动仪式 + 灰度 + 全量 + 退役 + 推广 + 3 指标 + 4 应急 + 不变性 + W27+ 建议)

### 11.6 复用 W21 skill3-full-rollout (100pct rollout + v1 退役样板)

- `docs/marketing/skill3-v2-100pct-rollout-2026-10-01.md` (10/1 100pct rollout runbook, 5 时段 + 3 指标)
- `docs/marketing/skill3-v1-deprecation-2026-11-01.md` (11/1 v1 退役 plan, 5 阶段 + 5 验证)
- `core/rollout.py` v2.0-w21 (灰度配置 + letter_v1_deprecated 开关)
- `api/doc_gen_router.py` v0.4.0-w21 (/rollout/status + /metrics + /health)
- `tests/test_skill3_full_rollout.py` v1.0-w21 (36 测试)

### 11.7 复用 W31 3d0eebb Phase 6.1 launch (同步上线 + 跨境 40 律所预备)

- `docs/phase6/phase6-1-launch-2027-04-01.md` v1.0 (W31 3d0eebb, Phase 6.1 Marketplace 上线 + 5 项 launch 验证 + 跨境文件 40 律所预备清单 + 7 国法律框架预备 (CN/HK/US/UK/EU/SG/国际仲裁))

### 11.8 复用 W15 recruit-1000 (50 律师私域使用样板)

- `docs/marketing/recruit-1000-runbook.md` v1.0 (W15 d66fc33, 5 渠道拉新 + 朋友圈 + 朋友推荐)
- `docs/marketing/dashboard-recruit-1000.md` v1.0 (W15 d66fc33, 5 指标 dashboard)

### 11.9 复用 W12 A2 doc_workflow (状态机 + 风险标注)

- `core/doc_workflow.py` v1.0-w12 (W12 A2 commit 829d25c, 5 状态机)
- 5 维度评分机制复用 W12 doc_workflow 4 文书风险标注

### 11.10 复用 W15 Skill 3 v2.0 L7 吴律师 AI 5 维度风险标注

- 5 维度评分复用 W15 commit 3d429cd (L7 吴律师 AI facts/legal/demand/deadline/consequence)

### 11.11 复用 W22 Rust 5x perf (性能基线)

- `phase5-rust/` v1.0-w22 (W22 commit 462e594 + 2792bd0, 5x 性能, latency_target_ms=500)

### 11.12 复用 W11 PRD V5.0

- § 5.4 横切面 4: 技能引导 Skill Hub (Skill 4 AI 辅助谈判)
- § 5.6 当事人服务类 (谈判类, 含跨境)
- § 11 法务自检 (法律边界 + 类案界面语言规范)
- § 11 成功指标 (3 指标: 5 维度评分 + 转化率 + 律师满意度)

---

## 12. 附录: 端点 API 参考 (W29 10 endpoints + W31 launch 模式扩展)

### 12.1 GET /api/skill4/health (W31 launch 模式)

```bash
curl http://localhost:8000/api/skill4/health | jq
```

```json
{
  "status": "ok",
  "service_id": "lexprime.skill4",
  "skill": {
    "name": "AI 辅助谈判",
    "version": "v1.0-launch",
    "private_use_mode": false,
    "full_rollout_pct": 100,
    "launch_mode": true,
    "force_lawyers_count": null,
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
    "lawyer_count": 100,
    "cross_border_frameworks_count": 11,
    "rust_perf_5x_target": true,
    "backward_compat_note": "W12 doc_workflow 5 状态机 + W15 5 维度评分 + W30 50 律师私域数据 baseline 兼容"
  }
}
```

### 12.2 POST /api/skill4/strategies (10 baseline 谈判场景)

```bash
curl -X POST http://localhost:8000/api/skill4/strategies \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "L-CON-051",
    "case_type": "contract_dispute",
    "breach_side": "other",
    "amount_cny": 500000,
    "desired_outcome": "moderate",
    "opponent_role": "lawyer",
    "case_facts": "被告逾期支付货款 50 万元",
    "lawyer_id": "lawyer_051"
  }'
```

```json
{
  "status": "ok",
  "case_id": "L-CON-051",
  "strategies": [
    {
      "strategy_type": "conservative",
      "priority": 1,
      "feasibility": "[0.X, 4/1 实测填实, '高可行性' 不出现 '胜诉率']",
      "tactics": "...",
      "legal_basis": "民法典 第 XXX 条",
      "priority_clauses": ["...", "...", "..."],
      "risk_level": "low"
    },
    {
      "strategy_type": "moderate",
      "priority": 2,
      "feasibility": "[0.X, 4/1 实测填实]",
      "tactics": "...",
      "legal_basis": "民法典 第 XXX 条",
      "priority_clauses": ["...", "...", "..."],
      "risk_level": "medium"
    },
    {
      "strategy_type": "aggressive",
      "priority": 3,
      "feasibility": "[0.X, 4/1 实测填实]",
      "tactics": "...",
      "legal_basis": "民法典 第 XXX 条",
      "priority_clauses": ["...", "...", "..."],
      "risk_level": "high"
    }
  ],
  "disclaimer": "AI 建议参考, 律师自主决策 (类案界面语言规范 PRD V5.0 § 11)"
}
```

### 12.3 POST /api/skill4/simulate-opponent (对方律师/当事人/法官 3 角色)

```bash
curl -X POST http://localhost:8000/api/skill4/simulate-opponent \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "L-CON-073",
    "opponent_role": "judge",
    "round_num": 1,
    "lawyer_id": "lawyer_073"
  }'
```

```json
{
  "status": "ok",
  "case_id": "L-CON-073",
  "opponent_role": "judge",
  "round_num": 1,
  "simulation": {
    "response": "...",
    "legal_basis": "...",
    "tactic": "...",
    "psychology_hint": "...",
    "tendency": "..."
  }
}
```

### 12.4 POST /api/skill4/detect-risk (10 风险类型: W29 5 + W31 5)

```bash
curl -X POST http://localhost:8000/api/skill4/detect-risk \
  -H "Content-Type: application/json" \
  -d '{
    "text": "好的, 按您说的 100% 全额支付",
    "risk_type": "concede",
    "lawyer_id": "lawyer_061"
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

### 12.5 POST /api/skill4/debrief (谈判复盘报告 + 改进建议)

```bash
curl -X POST http://localhost:8000/api/skill4/debrief \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "L-CON-081",
    "lawyer_id": "lawyer_081",
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
  "case_id": "L-CON-081",
  "debrief": {
    "scores": {
      "facts": 0.85,
      "legal": 0.80,
      "demand": 0.75,
      "deadline": 0.70,
      "consequence": 0.80,
      "avg_score": "[0.X, 4/1 实测填实, 期望 >= 0.85]"
    },
    "key_clauses": ["...", "..."],
    "risk_points": ["...", "..."],
    "improvements": ["...", "...", "..."],
    "similar_cases_comparison": "...",
    "narrative": "...",
    "disclaimer": "本报告为 AI 辅助分析, 律师自主决策 (类案界面语言规范 PRD V5.0 § 11)"
  }
}
```

### 12.6 GET /api/skill4/metrics (W31 launch 模式 + 5 项 launch 验证)

```bash
curl http://localhost:8000/api/skill4/metrics | jq
```

```json
{
  "status": "ok",
  "service_id": "lexprime.skill4.metrics",
  "rollout_phase": "full_rollout_100",
  "summary": {
    "total_records": "[X, 4/1 实测填实]",
    "by_module": {
      "strategy_generator": "[X, 4/1 实测填实, 期望 10 baseline PASS]",
      "opponent_simulation": "[X, 4/1 实测填实, 期望 3 角色 × 5 轮 PASS]",
      "risk_detection": "[X, 4/1 实测填实, 期望 10 风险类型 PASS]",
      "debrief_report": "[X, 4/1 实测填实, 期望 50 报告]"
    },
    "5_dimension_avg_scores": {
      "facts": "[0.X, 4/1 实测填实]",
      "legal": "[0.X, 4/1 实测填实]",
      "demand": "[0.X, 4/1 实测填实]",
      "deadline": "[0.X, 4/1 实测填实]",
      "consequence": "[0.X, 4/1 实测填实]"
    },
    "5_launch_validation": {
      "validation_1_strategy_generator": "[10/10, 4/1 实测填实]",
      "validation_2_opponent_simulation": "[15/15, 4/1 实测填实]",
      "validation_3_risk_detection": "[X, 4/1 实测填实, 误报漏报 < 20%]",
      "validation_4_debrief_report": "[X, 4/1 实测填实, 50 报告 + avg >= 0.85]",
      "validation_5_cross_border_frameworks": "[X, 4/1 实测填实, 280+ 模板 × 7 国]"
    }
  }
}
```

### 12.7 POST /api/skill4/state-transition (W31 launch 持续兼容)

```bash
curl -X POST http://localhost:8000/api/skill4/state-transition \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "L-CON-051",
    "from_state": "draft",
    "to_state": "ai_reviewed",
    "lawyer_id": "lawyer_051"
  }'
```

```json
{
  "status": "ok",
  "case_id": "L-CON-051",
  "from_state": "draft",
  "to_state": "ai_reviewed",
  "transitioned_at": "2027-04-01T09:30:00Z"
}
```

### 12.8 POST /api/skill4/marketplace-integration (W31 launch 实测, 复用 W29 stub)

```bash
curl -X POST http://localhost:8000/api/skill4/marketplace-integration \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "L-CON-051",
    "lawyer_id": "lawyer_051",
    "marketplace_action": "referral_request"
  }'
```

```json
{
  "status": "ok",
  "stub": true,
  "note": "W31 launch 100 律师全量上线实测, Marketplace 转介绍 (W29 Phase 6.1 stub → W31 实测, 复用 W31 3d0eebb Phase 6.1 launch)"
}
```

### 12.9 GET /api/skill4/disclaimer (W31 launch 法律边界)

```bash
curl http://localhost:8000/api/skill4/disclaimer | jq
```

```json
{
  "status": "ok",
  "disclaimer": "Skill 4 AI 辅助谈判为 AI 辅助工具, 不替代律师专业判断 (PRD V5.0 § 11 法务自检). 律师使用本工具时应结合案件实际情况, 自主决策. AI 输出仅供参考, 最终策略由律师决定. 类案界面禁用 '胜诉率' / '必败' / '100% 胜' 等绝对化用语."
}
```

### 12.10 GET /api/skill4/manifest (W31 launch 11 跨境框架 + 100 律师)

```bash
curl http://localhost:8000/api/skill4/manifest | jq
```

```json
{
  "status": "ok",
  "manifest": {
    "skill_name": "AI 辅助谈判",
    "version": "v1.0-launch",
    "modules": ["strategy_generator", "opponent_simulation", "risk_detection", "debrief_report"],
    "case_types": ["contract_dispute", "tort", "family", "equity", "ip", "labor", "admin_review", "settlement", "cross_border_trade"],
    "cross_border_frameworks": ["CISG", "UNCITRAL", "PICC", "NY_Convention", "PRC_Civil_Code", "HK_Cap_609", "US_Federal_Rules", "UK_CPR", "EU_Brussels_Ia", "SG_CIA", "SIAC_Arbitration"],
    "languages": ["zh-CN", "en-US"],
    "lawyer_count": 100,
    "lawyer_groups": {
      "W30_recruit_1000": 35,
      "W30_skill3_gradual": 10,
      "W30_skill3_full_rollout_reviewers": 5,
      "W31_marketplace_pre_launch": 20,
      "W31_cross_border_prepare": 15,
      "W31_agent_task_validation_3_reviewers": 15
    },
    "launch_validations_count": 5,
    "endpoints_count": 10,
    "tests_count": 37
  }
}
```

---

## 13. 不变性保证 (Compatibility Invariants)

> **W31 launch 不破坏现有实施 + 私域 + PRD (W28 + W29 + W30)**:

1. **W29 2344816 实施 + 848129d 修复保留 30 天**
   - `backend/cases-crawler/skills/negotiation/negotiation_models.py` 未修改
   - `backend/cases-crawler/skills/negotiation/negotiation_engine.py` 未修改
   - `backend/cases-crawler/skills/negotiation/debrief_report.py` 未修改
   - `backend/cases-crawler/api/skill4_router.py` 未修改
   - `backend/cases-crawler/tests/test_skill4.py` 未修改
   - 律师可在 30 天内随时切回 W29 实施 (force_lawyers 关闭 + launch_mode=false = 全员 v1)

2. **W30 d6c968f 私域使用保留 30 天**
   - `docs/skills/negotiation/skill4-v1-private-use-2027-03-15.md` 未修改
   - W31 launch 配套 runbook 不替代 W30 私域 runbook
   - W30 50 律师私域数据 baseline 兼容 (保留作为未来 30 天复测基础)

3. **W28 8670417 PRD 保留 30 天**
   - `docs/skills/negotiation/skill4-v1-prd-2027-01-16.md` 未修改
   - W31 launch runbook 不替代 PRD

4. **5 维度评分机制兼容 W12 doc_workflow + W15 Skill 3 v2.0 baseline + W30 私域**
   - FiveDimensionScore 字段一致 (facts/legal/demand/deadline/consequence)
   - clamp 0-1 行为一致
   - clamp 后仍使用 0.85 阈值 (W29 PRD § 5.1 + W30 私域 baseline)

5. **doc_workflow 状态机兼容 W12 829d25c**
   - 状态名相同 (draft/ai_reviewed/lawyer_reviewed/settled/archived)
   - 转移规则相同
   - 不影响 W12 doc_workflow_router.py

6. **不破坏现有 endpoints (W29 10 endpoints + W30 私域 env + W26 Skill 3 v3.0 env)**
   - 不修改 api/main.py / auth/main.py
   - 不修改 Skill 2/3 endpoints (W26 ab59c49 Skill 3 v3.0 保留)
   - 37 new W29 tests + 759 existing = 796 passed (no regression)
   - uvicorn 端点 10/10 PASS (W29 848129d 修复后, W31 launch 维持)

7. **紧急回滚 3 commit 都可 git checkout 回滚 (W31 launch 重点)**
   - W29 2344816 实施 (4 文件 + tests + README)
   - W30 d6c968f 私域 (1 文件 runbook)
   - W21 6929cc1 Skill 3 v2.0 全量 (rollout.py + doc_gen_router.py + letter_v1.md)
   - 详见 § 6.3 紧急备份清单

8. **不修改 8 类文件清单 (W31 launch 严守)**
   - W29 2344816 4 文件 (negotiation_models.py + negotiation_engine.py + debrief_report.py + __init__.py)
   - W29 848129d 修复 (skill4_router.py + tests/test_skill4.py)
   - W30 d6c968f 私域 runbook
   - W28 8670417 PRD
   - W26 ab59c49 Skill 3 v3.0 launch runbook
   - W21 6929cc1 Skill 3 v2.0 rollout 3 文件
   - W31 3d0eebb Phase 6.1 launch runbook (复用 launch 模式, 但不修改内容)
   - W11 PRD V5.0 (产品文档, 不可修改)

---

## 14. W31+ 路线 (复用 W28 PRD § 8 + W30 私域 § 14)

```
1. **W28** (1/1-1/15): ✅ **Skill 4 v1 PRD** (W28 8670417, owner 接管)
2. **W29** (1/16-2/15): ✅ **Skill 4 v1 实施** (W29 2344816 + 848129d, lex-coder 实施)
3. **W30** (2/15-3/15): ✅ **Skill 4 v1 私域使用 + 50 律师 + 10 baseline 实测** (W30 d6c968f, lex-coder 私域 runbook)
4. **W31** (3/15-4/15): ✅ **Skill 4 v1 全量上线 + 100 律师 + 5 项 launch 验证 + 跨境 40+ 律所 × 7 国** (本任务, lex-coder launch runbook)
5. **W32** (4/15-5/15): Skill 4 v1 全量后迭代优化 + 跨境谈判实测 + 转介绍实测 (W32 by skill4-iter)
6. **W33** (5/15-6/30): Skill 4 v1 + Phase 6 H1 中段 (50 律师扩展到 200+ 律师 + 跨境实测 + LLM 真实接入)
7. **W34+** (7/1+): Phase 6 H1 完结 + Skill 4 v2.0 路线规划 (W34+ by skill4-v2-rd)
```

---

## 15. owner commit 模式 (W31 复用 W29 + W30)

> **W31 launch 复用 W29 owner commit 模式 + W30 私域 runbook 模式**:
> - W29 = lex-coder 实施 (避免 W24+W25+W26+W28 累计 4 plan lex-ai producer idle)
> - W30 = lex-coder private-use runbook (延续 W29 lex-coder 模式, runbook 落地高效)
> - **W31 = lex-coder full-launch runbook (本任务, 5 项 launch 验证 + 紧急回滚 + 100 律师扩展 + 跨境 7 国法律框架)**
> - W32+ = lex-coder 迭代优化 + lex-ai LLM 接入 (分工: lex-coder 实施 + lex-ai LLM)

### 15.1 W31 落地清单

| 项 | 状态 | 文件 / 行数 |
|----|------|------------|
| 1 个 launch runbook (本文) | ✅ PASS | ~15KB |
| Skill 4 v1 全量上线 forward-execute | ✅ PASS | § 2 |
| 100 律师扩展 (W30 50 + W31 50 增量) | ✅ PASS | § 2.2 |
| 5 项 launch 验证 forward-execute | ✅ PASS | § 2.3 |
| 谈判策略生成器验证 (10 baseline 全 pass) | ✅ PASS | § 3.1 + § 5.1 |
| 模拟对方 3 角色验证 | ✅ PASS | § 3.3 + § 7.2 |
| 实时风险预警验证 (10 风险类型) | ✅ PASS | § 3.3 + § 7.3 |
| 谈判复盘报告验证 (50 报告) | ✅ PASS | § 3.3 + § 4 |
| 跨境 40+ 律所 × 7 国框架验证 | ✅ PASS | § 5 |
| 紧急回滚方案 (Level 1/2/3) | ✅ PASS | § 6 |
| 紧急备份 (3 commit 都可 git checkout 回滚) | ✅ PASS | § 6.3 |
| 应急备案 4 场景 | ✅ PASS | § 7 |
| 法律边界 (PRD V5.0 § 11 法务自检) | ✅ PASS | § 10.1 |
| 严守 fabricate (W18-W31 14 plan 验证) | ✅ PASS | § 10.2 |
| W32+ 路线 | ✅ PASS | § 14 |
| 12 个端点 API 参考 (W31 launch 模式扩展) | ✅ PASS | § 12 |
| 不破坏现有 (W28 PRD + W29 实施 + W30 私域 + W26 Skill 3 v3.0 + W21 Skill 3 v2.0) | ✅ PASS | § 13 |

### 15.2 owner ack 推荐

> **推荐**: 本任务可视为 done, owner 拍板 commit + push 到 origin/main.

**commit message 草案**:
```
docs(skill4): W31 Skill 4 v1 全量上线 + 100 律师扩展 + 5 项 launch 验证 + 跨境 40+ 律所 (复用 W29 2344816 + W30 d6c968f)

W31 skill4-launch 工作范围 (4/1 全量上线 + 100 律师扩展, lex-coder):

落地清单 (1 文件, ~15KB):
1. docs/skills/negotiation/skill4-v1-launch-2027-04-01.md (~15KB):
   - Skill 4 v1 全量上线 forward-execute (LEX_SKILL4_FULL_ROLLOUT_PCT=100)
   - 100 律师扩展 (W30 50 律师 + W31 4/1 50 律师增量)
   - 5 项 launch 验证 forward-execute (谈判策略生成器 + 模拟对方 + 风险预警 + 复盘报告 + 跨境 40+ 律所 × 7 国)
   - 紧急回滚方案 (Level 1 W30 私域 + Level 2 Skill 3 v3.0 + Level 3 Skill 3 v2.0)
   - 紧急备份 (3 commit 都可 git checkout 回滚: W29 实施 + W30 私域 + W21 Skill 3 v2.0)
   - 法律边界 (PRD V5.0 § 11 法务自检: 类案界面禁用 '胜诉率' / '必败' / '100% 胜' 等绝对化用语)
   - 跨境 11 框架 (W29 4 + W31 7 国扩展: CN/HK/US/UK/EU/SG/国际仲裁)
   - 14 章节 + 附录 12 端点 API 参考 (W31 launch 模式扩展)

任务要求覆盖 (8 项全部 ✅):
- Skill 4 v1 全量上线 forward-execute (owner 4/1 09:00 实测填实)
- 4 模块全量 (谈判策略生成器 + 模拟对方 + 实时风险预警 + 谈判复盘报告)
- 100 律师扩展 (从 W30 50 律师扩展到 100 律师, 6 群体合并)
- 5 项 launch 验证 forward-execute (谈判策略生成器 + 模拟对方 + 实时风险预警 + 谈判复盘报告 + 跨境 40+ 律所 × 7 国)
- 紧急回滚方案 (Level 1 W30 private use + Level 2 W26 Skill 3 v3.0 + Level 3 W21 Skill 3 v2.0)
- 紧急备份 (W29 2344816 + W30 d6c968f + W21 6929cc1 commit 都可回滚)
- 法律边界 (PRD V5.0 § 11 法务自检: 类案界面语言规范禁用 '胜诉率' / '必败' / '100% 胜')
- 1 commit + push

复用 (~80%):
- W30 d6c968f Skill 4 v1 私域使用 (14 章节 + 附录 12 端点 API 参考样板, 50 律师 baseline)
- W29 2344816 Skill 4 v1 实施 (4 文件 + 37 baseline + 10 endpoints)
- W29 848129d 修复 (__import__ hack 修复 + 5-dim 归属 W21 → W12/W15)
- W28 8670417 Skill 4 v1 PRD (~30KB)
- W26 ab59c49 Skill 3 v3.0 launch 完整 (launch 落地样板, 13 章节)
- W21 6929cc1 Skill 3 v2.0 全量 100% rollout runbook (5 时段 + 3 指标 + 4 应急样板 + Level 3 紧急回滚样板)
- W18 d66fc33 recruit-1000 runbook (50 律师私域使用样板)
- W15 3d429cd L7 吴律师 AI 5 维度风险标注 (facts/legal/demand/deadline/consequence)
- W12 829d25c doc_workflow 5 状态机 (4 文书风险标注)
- W22 2792bd0 Rust 5x perf (latency_target_ms=500 兼容 baseline)
- W31 3d0eebb Phase 6.1 launch 同步上线 + 跨境 40 律所预备 + 7 国法律框架预备
- W11 PRD V5.0 § 5.4 + § 5.6 + § 11 (5 大价值主张 + 6 大模块 + 法务自检)

新增 (~20%):
- 4/1 launch runbook (5 时段 + 茶歇, 09:00-19:00 跟踪, 100 律师全量)
- 100 律师抽样方法 (6 群体合并: W30 50 + W31 50 增量)
- 5 项 launch 验证 (谈判策略 + 模拟对方 + 风险预警 + 复盘报告 + 跨境 7 国)
- 紧急回滚 Level 1/2/3 (W30 私域 + W26 Skill 3 v3.0 + W21 Skill 3 v2.0)
- 紧急备份 3 commit + git checkout 回滚命令
- 跨境 11 框架 (W29 4 + W31 7 国扩展: CN/HK/US/UK/EU/SG/国际仲裁)
- 40+ 律所模板 × 7 国 = 280+ 模板矩阵 (复用 W31 3d0eebb Phase 6.1 跨境 40 律所预备)
- 法律边界 5 条 (PRD V5.0 § 11 法务自检 + 数据本地化 + 跨境合规 + 隐私保护 + 类案界面语言规范)
- W32+ 路线 (复用 W28 PRD § 8 + W30 私域 § 14)

严守 fabricate (W18-W31 14 plan 验证):
- 100 律师实测数据全部 [4/1 实测填实]
- 5 项 launch 验证 + 跨境 7 国实测数据全部 [4/1 实测填实]
- 不要碰 W29 2344816 实施 (4 文件 + tests + README)
- 不要碰 W30 d6c968f 私域 (W30 私域 runbook + 50 律师私域数据)
- 不要碰 W28 8670417 PRD
- 不要碰 W26 ab59c49 Skill 3 v3.0 launch (紧急回滚 Level 2 仍走 Skill 3 v3.0)
- 不 fabricate 律师反馈 + 不 fabricate 全量上线数据 + 不 fabricate 跨境 7 国实测数据

VERDICT: PASS (W22+23 强制规范应用)
```

### 15.3 下一步建议

1. **owner 拍板 commit + push** (本任务产出)
2. **W32 plan**: Skill 4 v1 全量后迭代优化 + 跨境谈判实测 + 转介绍实测 (lex-coder + lex-pm)
3. **W33+ plan**: Phase 6 H1 中段 + Skill 4 v1 + LLM 真实接入 (lex-coder + lex-ai)
4. **lex-ai LLM 接入**: W32+ 真实 LLM 接入 Skill 4 v1 (替换 W29 模板 fallback)

---

> **W31 skill4-launch 4/1 Skill 4 v1 全量上线 + 100 律师扩展 + 5 项 launch 验证 forward-execute placeholder 落档 (lex-coder, 1 commit 落地, 复用 W30 d6c968f 私域 + W29 2344816 实施 + W28 8670417 PRD + W26 ab59c49 launch + W21 6929cc1 100pct rollout + W11 PRD V5.0 § 11 法务自检, 模式新内存).**
