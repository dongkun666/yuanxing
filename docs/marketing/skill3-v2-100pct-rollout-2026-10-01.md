<!-- LexPrime Track B · W21 skill3-full-rollout 交付 -->
# 10/1 Skill 3 律师函 v2.0 全量 100% Rollout 运行手册 (Full Rollout Runbook · 2026-10-01)

> **版本**: v1.0 · 2026-06-30
> **Track**: A (AI 模型 + Skill Hub 灰度层)
> **Week**: W21 skill3-full-rollout (Skill 3 律师函 v2.0 全量 100%)
> **状态**: runbook 落档, 等 10/1 当天 owner 主持 + Tech Lead (lex-ai) + BD 协作实测填实
> **依据**:
> - `docs/marketing/skill3-v2-ab-test-2026-08-15.md` v1.0 (8/15 10% 灰度 + A/B test 报告)
> - `docs/marketing/skill3-v2-50pct-rollout-2026-09-01.md` v1.0 (9/1 50% 灰度报告)
> - `prompts/skill3_letter_v2.yaml` v2.0-w15 (W15 commit e3f0940, 5 维度深度推理 + 阈值 0.6)
> - `templates/docs/letter_v2.md` v2.0-w15 (W15 commit 3d429cd, 8 律师 mock 反馈驱动)
> - `core/rollout.py` v2.0-w21 (W21 新增 letter_v1_deprecated 11/1 退役开关)
> - `api/doc_gen_router.py` v0.4.0-w21 (/letter 100% v2 路由 + /rollout/status + /metrics + /health)
> - `tests/test_skill3_full_rollout.py` v1.0-w21 (新增, 36 测试)
> - W11 PRD V5.0 § 5.4 横切面 4 技能引擎 Skill Hub + § 5.6 当事人服务类文书 (律师函)
> - W12 A2 commit 829d25c (doc_workflow 状态机 + 4 文书风险标注)

> **核心定位 (W21 skill3-full-rollout vs W19 skill3-gradual vs W15 skill3-iterate)**:
> - W15 skill3-iterate = 律师函 v2.0 模板 + prompt 优化 (开发完)
> - W19 skill3-gradual 8/15 = v2.0 10% 灰度 + A/B test (W21 复用 35 测试)
> - W19 skill3-gradual 9/1 = v2.0 全量 50% 灰度 (W21 复用 50% 律师群数据)
> - **W21 skill3-full-rollout 10/1 = v2.0 全量 100% 律师试用** (本次)
> - **W21 skill3-full-rollout 11/1 = v1.0 退役** (本次, 同期)

---

## 0. 文档使用说明 (执行日 10/1 当天随身打印)

> 本手册是 10/1 Skill 3 律师函 v2.0 全量 100% rollout 当天的"运行剧本",
> **总指挥 (PM) + Tech Lead (lex-ai/lex-coder) + BD + 100% 律师 (200 名, 公测 day 68 估算)** 协作执行.
> 本手册 **核心目标**: 把 9/1 50% 灰度数据基础上扩展到 100% 律师群 (全员 v2.0), 跟踪同样 3 指标 (5 维度评分 + 转化率 + 律师满意度), 验证 v2.0 全场景效果.
> 本手册 **配套**:
> - `skill3-v2-ab-test-2026-08-15.md` (8/15 10% 灰度 runbook)
> - `skill3-v2-50pct-rollout-2026-09-01.md` (9/1 50% 灰度 runbook)
> - `skill3-v1-deprecation-2026-11-01.md` (11/1 v1.0 退役计划, 同期)
> - `core/rollout.py` v2.0-w21 (灰度配置 + hash 分配 + metrics 跟踪 + letter_v1_deprecated 开关)
> - `api/doc_gen_router.py` v0.4.0-w21 (端点 + 自动路由 + 退役开关报告)
>
> **严守严禁 fabricate**:
> 1. **不要 fabricate 律师反馈** (实测为主, owner 10/1 跑律师试用)
> 2. **不要 fabricate 全量数据** (实测为主, owner 10/1 当天 19:00 跑 metrics 抓取)
> 3. **数字全部 [10/1 实测填实]**, owner 10/1 当天 19:00 patch 替换 placeholder
> 4. **A/B test 关闭**: 10/1 全量 100% 期间不再做 A/B split, treatment_a/b 概念仅用于 ab_split 50/50 hash 桶报告

---

## 1. 10/1 全量 100% rollout 阶段切换 (5 min, 09:00)

### 1.1 切换前 5 min (08:55 - 09:00)

```
[08:55] Tech Lead (lex-ai)
  - 验证当前状态 (9/1 50% 灰度保持期, 30 天后):
    curl http://localhost:8000/api/doc-gen/rollout/status
  - 期望: phase=rollout_50pct, rollout_pct=50
  - 9/1 - 9/30 期间 metrics 累计: [X, 10/1 实测填实, owner 10/1 08:55 抓取]
  - 9/1 大样本 50% 灰度结论: [treatment_a/treatment_b/control/tie, 9/1 19:00 实测填实]

[08:58] 准备 env 切换命令
  $ export LEX_SKILL3_ROLLOUT_PHASE=rollout_100pct
  $ export LEX_SKILL3_ROLLOUT_PCT=100
  $ export LEX_SKILL3_AB_SPLIT=50,50  # 全量 100% 时 bucket 仍 50/50 hash 划分, 用于分桶报告
  # force_v2 强制列表: 9/1 winner 律师进 force_v2 (评审 #N 关键律师)
  $ export LEX_SKILL3_FORCE_V2=lawyer_001,lawyer_011,lawyer_020  # placeholder, 9/1 实测填实
  $ export LEX_SKILL3_FORCE_V1=
  # W21 新增: 10/1 全量期间 letter_v1 仍可用 (兼容 force_v1 律师)
  $ export LEX_SKILL3_LETTER_V1_DEPRECATED=false  # 11/1 之后改为 true
```

### 1.2 09:00 切换 (1 min)

```
[09:00:00] 切换 env + 重启服务
  $ systemctl restart lexprime-backend
  启动时间: ~30s

[09:00:30] 验证切换成功
  $ curl http://localhost:8000/api/doc-gen/rollout/status | jq
  期望:
    {
      "rollout": {
        "phase": "rollout_100pct",
        "rollout_pct": 100,
        "ab_split_within_v2": [50, 50],
        "force_v2_lawyers_count": 3,
        "letter_v1_deprecated": false,  # W21 新增
        "deprecated_after_date": "2026-11-01",
        "backward_compat_note": "现有 v1.0 文书数据保留..."
      }
    }

[09:00:45] 端到端 smoke test (10 律师抽样)
  $ for i in 1 2 3 4 5 6 7 8 9 10; do
      curl -X POST http://localhost:8000/api/doc-gen/letter \
        -H "Content-Type: application/json" \
        -d "{\"lawyer_id\": \"lawyer_${i}_${RANDOM}\", \"fields\": {\"sender\": \"张律师\", \"recipient\": \"李四\"}}"
    done
  期望: 10 次调用中 100% 返回 served_version=letter_v2 + bucket=treatment_a/b (不再有 letter_v1 / control)
```

### 1.3 09:01-09:15 启动确认 (15 min)

```
[09:01-09:15] 全量 100% 稳定性观察
  - 5 分钟内持续观察 metrics 端点: curl http://localhost:8000/api/doc-gen/metrics | jq
  - 期望: 30-50 个新 metric record, by_version 100% letter_v2 (不再有 letter_v1)
  - 异常: 若 v2 报错率 > 5% 或 latency P95 > 3s, 立即回滚到 rollout_50pct (env 切换)
  - 兼容性: 现有 v1.0 文书数据 (W12 A2 doc_workflow) 不受影响
```

---

## 2. 10/1 09:15 - 19:00 全量执行 (10h 跟踪)

### 2.1 全量机制 (5 时段 + 茶歇, 09:15-19:00)

> **复用 8/15 + 9/1 灰度机制**, 全量 100% 期间 100% 律师群体验 v2.0, 时段式设计让全员有充分时间体验

| 时段 | 时间 | 环节 | 负责人 | 输出物 |
|------|------|------|--------|--------|
| **预热** | 09:15-09:30 | 100% 律师群发通知 (微信群 + 邮件 + 朋友圈) | BD | 律师确认清单 + 全量范围说明 |
| **时段 1** | 09:30-11:00 | 全量律师首次使用 v2.0 (生成 10+ 律师函) | 全量律师 + Tech | v2.0 生成记录 + 5 维度评分 |
| **时段 2** | 11:00-13:00 | 全量律师对比 50% 灰度数据 (50% 律师已用 v2.0 一月) | 全量律师 + 9/1 老用户 | 全量切换平滑度 + 老用户反馈 |
| **茶歇** | 13:00-14:00 | 午休 + 律师微信群互动 | BD | 律师反馈收集 + 案例分享 |
| **时段 3** | 14:00-15:30 | 全量律师深度使用 (合同审查 + 文书生成联动) | 全量律师 | Skill 1+2+3 联动数据 |
| **时段 4** | 15:30-17:00 | 转化跟踪 + 客服答疑 | BD + Tech | 转化率数据 (7 天后回填) |
| **时段 5** | 17:00-19:00 | 收尾 + 当日报告启动 | 总指挥 + Tech | 10/1 实测填实数字 + 报告 |
| **收尾** | 19:00-19:30 | 全量保持 + 11/1 v1 退役准备 | Tech Lead | 当日报告交付 + 11/1 cron |

### 2.2 全量 100% 律师抽样方法

```
[09:15 抽样逻辑] 100% 律师 = 所有律师, 全部走 v2.0
  - 假设公测 day 68 (10/1) 律师总数 200 (按 W18 kpi-snapshot-2026-08-09 + W19 9/1 50% 灰度推算)
  - 期望全量律师: 200 名 (100% 全员)
  - A/B test 已关闭, bucket 仍按 hash 50/50 划分 (treatment_a / treatment_b) 用于分桶报告
  - treatment_a / treatment_b 在全量后只是 hash 桶标签, 不再是 A/B 对照组

[09:15 抽样律师清单] 10/1 全量律师 [实测填实, owner 10/1 09:15 通过 metrics 端点查询]
  treatment_a (100 名):
    1. [lawyer_id_001, 姓名 placeholder, 10/1 owner 填实]
    2. [lawyer_id_002, 姓名 placeholder, 10/1 owner 填实]
    ...
    100. [lawyer_id_100, 姓名 placeholder, 10/1 owner 填实]
  treatment_b (100 名):
    1. [lawyer_id_101, 姓名 placeholder, 10/1 owner 填实]
    2. [lawyer_id_102, 姓名 placeholder, 10/1 owner 填实]
    ...
    100. [lawyer_id_200, 姓名 placeholder, 10/1 owner 填实]
  letter_v1 用户: 0 名 (10/1 全量后全部 v2.0, 除非 force_v1 特殊配置)
```

### 2.3 跟踪 3 指标 (与 8/15 + 9/1 一致)

```
[指标 1: 5 维度评分] 自动 + 律师主动评分
  自动: v2.0 生成时自动从 prompt 提取 risk_dim_facts/legal/demand/deadline/consequence (0-1 浮点)
  律师: 律师生成后 24h 内主动评分 (1-5), 通过 /api/doc-gen/metrics/update 端点 PATCH
  期望分布: facts 0.7-0.9, legal 0.6-0.85, demand 0.7-0.9, deadline 0.5-0.8, consequence 0.65-0.85
  数据来源: GET /api/doc-gen/metrics → summary.5_dimension_avg_scores

[指标 2: 转化率] 生成后 7 天跟踪
  跟踪窗口: 10/1 09:00 - 10/8 09:00 (7 天)
  转化定义: 律师生成律师函后 7 天内是否付费 (¥99/月个人版 / ¥449 创史体验官)
  期望: 全量 100% 律师转化率 >= 35% (9/1 baseline + 持平)
  数据来源: dashboard 付费转化指标 + paid_converted 事件

[指标 3: 律师满意度] 律师主动评分
  评分时间: 生成后 48h 内律师主动评分 (1-5)
  期望: 全量律师满意度 >= 4.5/5.0 (9/1 baseline + 持平)
  数据来源: 律师主动评价 (1v1 微信沟通 / 邮件回复 / 群内反馈)
```

---

## 3. 10/1 19:00 当日报告 (10/1 实测填实执行)

### 3.1 3 指标实测数据

> **数字全部 [10/1 实测填实, owner 10/1 19:00 patch 替换 placeholder]**

| 指标 | 期望目标 | v1.0 (历史 baseline) | treatment_a (100 名) | treatment_b (100 名) | 综合 (200 名) |
|------|----------|----------------------|----------------------|----------------------|---------------|
| **5 维度评分 - facts** | v2 > v1 | [0.X, 历史 baseline] | [0.X, 10/1 实测填实] | [0.X, 10/1 实测填实] | [0.X, 10/1 实测填实] |
| **5 维度评分 - legal** | v2 > v1 | [0.X, 历史 baseline] | [0.X, 10/1 实测填实] | [0.X, 10/1 实测填实] | [0.X, 10/1 实测填实] |
| **5 维度评分 - demand** | v2 > v1 | [0.X, 历史 baseline] | [0.X, 10/1 实测填实] | [0.X, 10/1 实测填实] | [0.X, 10/1 实测填实] |
| **5 维度评分 - deadline** | v2 > v1 | [0.X, 历史 baseline] | [0.X, 10/1 实测填实] | [0.X, 10/1 实测填实] | [0.X, 10/1 实测填实] |
| **5 维度评分 - consequence** | v2 > v1 | [0.X, 历史 baseline] | [0.X, 10/1 实测填实] | [0.X, 10/1 实测填实] | [0.X, 10/1 实测填实] |
| **转化率 (7 天)** | >= 35% v2 | [0.XX, 历史 baseline] | [0.XX, 10/8 实测填实] | [0.XX, 10/8 实测填实] | [0.XX, 10/8 实测填实] |
| **律师满意度** | >= 4.5/5 v2 | [X.X, 历史 baseline] | [X.X, 10/1 实测填实] | [X.X, 10/1 实测填实] | [X.X, 10/1 实测填实] |

### 3.2 9/1 vs 10/1 对比 (灰度扩展到大样本验证)

> **核心对比**: 9/1 50% 灰度数据 vs 10/1 100% 灰度数据, 验证 v2.0 在 100% 律师群的效果稳定性

| 指标 | 9/1 50% 灰度 | 10/1 100% 全量 | 趋势 | 备注 |
|------|--------------|----------------|------|------|
| **5 维度评分 - facts** | [0.XX, 9/1 实测填实] | [0.XX, 10/1 实测填实] | [上升/持平/下降] | 全量是否稳定 |
| **5 维度评分 - legal** | [0.XX, 9/1 实测填实] | [0.XX, 10/1 实测填实] | [上升/持平/下降] | 全量是否稳定 |
| **5 维度评分 - demand** | [0.XX, 9/1 实测填实] | [0.XX, 10/1 实测填实] | [上升/持平/下降] | 全量是否稳定 |
| **律师满意度** | [X.X, 9/1 实测填实] | [X.X, 10/1 实测填实] | [上升/持平/下降] | 大样本是否更稳定 |
| **转化率 (7 天)** | [0.XX, 9/8 实测填实] | [0.XX, 10/8 实测填实] | [上升/持平/下降] | 全量律师中转化趋势 |

### 3.3 全量决策 (10/1 19:00 决策)

> **A/B test 已在 10/1 全量时关闭**, 不再单独对比 treatment_a vs treatment_b.
> **核心决策**: 11/1 v1.0 退役 (letter_v1_deprecated=True) 是否按计划执行?

- 决策依据: [10/1 19:00 实测填实]
- v2.0 稳定性: [稳定/波动/异常, 10/1 19:00 实测填实]
- 律师反馈: [积极/中性/消极, 10/1 19:00 实测填实]
- 推荐行动: [按计划 11/1 退役 / 推迟退役 / 保持全量 100% 不变, 10/1 19:00 实测填实]

### 3.4 10/1 异常处理 (4 场景)

| 异常 | 触发条件 | 行动 |
|------|----------|------|
| v2.0 报错率 > 5% | 5xx 错误 / 1h | 立即回滚: env `LEX_SKILL3_ROLLOUT_PHASE=rollout_50pct`, 重启服务 |
| v2.0 latency P95 > 3s | 1h 监控 | 通知 Tech Lead 优化, 暂停全量 (env rollout_50pct) |
| 律师强烈负面反馈 (20+) | 1h 内 20+ 律师投诉 | 暂停全量, 收集反馈, 10/2 02:00 owner 决策 |
| 11/1 退役数据矛盾 | 9/1 vs 10/1 vs 11/1 趋势反向 | 不立即行动, 11/8 09:00 转化数据出来再决策 |

### 3.5 10/1 19:00 报告交付

```
[10/01 19:00] 全量报告启动
  - 文件: docs/marketing/skill3-v2-100pct-rollout-2026-10-01.md (本文件)
  - 数据 patch: 把 § 3.1 表格 + § 3.2 对比 + § 3.3 winner + § 3.4 异常全部 [实测填实]
  - commit: feat(marketing): W21 skill3-full-rollout 10/1 100% 全量 实测填实
  - push: origin/main

[10/01 19:30] 11/1 切换准备
  - env 保持: LEX_SKILL3_ROLLOUT_PHASE=rollout_100pct
  - cron 11/1 09:00 自动切换: scripts/trigger-skill3-rollout-1101.sh (待 W21+ 写)
    * env LEX_SKILL3_LETTER_V1_DEPRECATED=true (11/1 退役开关)
  - 通知: BD 群发 11/1 v1.0 退役预告
```

---

## 4. 10/1 全量阶段保持 (30 天, 10/1 - 10/31)

### 4.1 持续跟踪 (3 节奏)

```
[每日 09:00] 日常 metrics 汇总
  - curl http://localhost:8000/api/doc-gen/metrics | jq
  - 验证: by_version 100% letter_v2, by_bucket 50/50 hash split (treatment_a/b)
  - 异常: 立即 patch (按 4 异常处理)

[每周一 09:00] 周度报告
  - 5 维度评分周均 + 转化率周累计 + 律师满意度周均
  - 报告: docs/marketing/skill3-v2-weekly-{date}.md
  - commit: feat(marketing): W21 skill3-full-rollout 周度跟踪

[每月 1 日 09:00] 月度报告
  - 10/1 - 10/31 全量阶段汇总 + 11/1 v1 退役决策建议
  - 报告: docs/marketing/skill3-v2-monthly-2026-10.md
  - commit: feat(marketing): W21 skill3-full-rollout 月度跟踪
```

### 4.2 10/1 - 10/31 关键事件

| 事件 | 日期 | 影响 | 行动 |
|------|------|------|------|
| 10/1 切换 100% 全量 | 10/1 09:00 | 启动全量 100% | 见 § 1-3 |
| 10/8 转化数据完整 | 10/8 09:00 | 7 天转化窗口 | owner 10/8 09:00 patch 转化率 |
| 10/15 3 agent 招聘 | 10/15 | 新 agent 进入 plan task 派发 | 同期 (lex-bd owner) |
| 10/31 月度收尾 | 10/31 23:59 | 10 月结束 | 月度报告 + 11/1 退役决策 |
| 11/1 v1.0 退役 | 11/1 09:00 | letter_v1_deprecated=True | 见 skill3-v1-deprecation-2026-11-01.md |

### 4.3 11/1 切换准备 (cron 自动化)

```bash
#!/bin/bash
# scripts/trigger-skill3-rollout-1101.sh (W21 落档, 占位说明)
# 11/1 09:00 自动切换 letter_v1 退役 (视 10/1 全量数据)
export LEX_SKILL3_ROLLOUT_PHASE=rollout_100pct  # 保持
export LEX_SKILL3_ROLLOUT_PCT=100  # 保持
export LEX_SKILL3_LETTER_V1_DEPRECATED=true  # W21 新增: 退役开关
systemctl restart lexprime-backend
curl http://localhost:8000/api/doc-gen/rollout/status | jq
# 期望: phase=rollout_100pct, letter_v1_deprecated=true, deprecated_after_date="2026-11-01"
```

> **W21 占位说明**: 实际 cron 脚本 W21 已落档. 10/1 - 10/31 期间 letter_v1 仍可用 (force_v1 律师兼容), owner 手动验证.

---

## 5. 严守 fabricate 原则 (W21 复制 W18+W19+W20)

> **W18+W19+W20 严守 fabricate 原则, W21 复制**:
> 1. **不要 fabricate 律师反馈**: 实测为主, owner 10/1 跑律师试用, 反馈全部 [10/1 实测填实]
> 2. **不要 fabricate 全量数据**: 实测为主, owner 10/1 当天 19:00 跑 metrics 抓取, 数字全部 [10/1 实测填实]
> 3. **forward-execute placeholder 模式**: runbook 流程 + 时间线 + 应急 + 跟踪节奏, 实际数字全部 placeholder
> 4. **严守 AI 辅助, 不替代律师**: 全量期间严守产品原则, 律师主动评分是核心, AI 评分仅辅助
> 5. **数据本地化**: 律师案件 / 客户 / 文书不离开律师电脑, 全量 metrics in-memory 收集不持久化敏感数据

---

## 6. 关联文档 + 配套资源

### 6.1 W21 skill3-full-rollout 配套 (本次交付)

- `core/rollout.py` v2.0-w21 (升级, 新增 letter_v1_deprecated) - 全量 100% + 11/1 退役开关
- `api/doc_gen_router.py` v0.4.0-w21 (升级) - /letter 100pct 路由 + /rollout/status 含退役字段
- `templates/docs/letter_v1.md` v1.0-w21 (升级) - 顶部加 deprecated banner (11/1 退役提示)
- `tests/test_skill3_full_rollout.py` v1.0-w21 (新增, 36 tests) - 全量 + 退役逻辑验证
- `docs/marketing/skill3-v2-100pct-rollout-2026-10-01.md` (本次, 10/1 全量 runbook)
- `docs/marketing/skill3-v1-deprecation-2026-11-01.md` (本次同期, 11/1 v1 退役计划)

### 6.2 复用 W19 skill3-gradual (灰度底层)

- `core/rollout.py` v1.0-w19 (35 测试覆盖) - 灰度配置 + hash 分配 + metrics 跟踪
- `api/doc_gen_router.py` v0.3.0-w19 (升级) - /letter 自动路由 + /rollout/status + /metrics 3 端点
- `tests/test_skill3_ab_rollout.py` v1.0-w19 (35 tests) - 灰度逻辑 + 端点集成
- `docs/marketing/skill3-v2-ab-test-2026-08-15.md` (8/15 10% 灰度 runbook)
- `docs/marketing/skill3-v2-50pct-rollout-2026-09-01.md` (9/1 50% 灰度 runbook)

### 6.3 复用 W15 skill3-iterate (灰度对象)

- `prompts/skill3_letter_v2.yaml` v2.0-w15 (W15 commit e3f0940)
- `templates/docs/letter_v2.md` v2.0-w15 (W15 commit 3d429cd)
- `tests/test_skill3_letter_v2.py` v1.0-w15 (W15 commit e3f0940, 32 tests)

### 6.4 复用 W12 A2 doc_workflow (工作流集成)

- `core/doc_workflow.py` v1.0-w12 (W12 A2 commit 829d25c, 5 状态机)
- `api/doc_workflow_router.py` v1.0-w12 (W12 A2, 4 端点)
- `api/signature_router.py` v1.0-w12 (W12 A2, 签字集成)

### 6.5 复用 W11 PRD V5.0

- § 5.4 横切面 4: 技能引擎 Skill Hub (Skill 3 文书生成 v2.0 全量)
- § 5.6 当事人服务类文书 (律师函策略性, 语气可选)
- § 11 成功指标 (Phase 4 KPI 体系, 公测 day 68 验证)

---

## 7. 附录: 端点 API 参考 (W21 升级)

### 7.1 GET /api/doc-gen/rollout/status (W21 新增字段)

```bash
curl http://localhost:8000/api/doc-gen/rollout/status | jq
```

```json
{
  "status": "ok",
  "service_id": "lexprime.skill.doc-gen.rollout",
  "rollout": {
    "phase": "rollout_100pct",
    "rollout_pct": 100,
    "ab_split_within_v2": [50, 50],
    "enabled_doc_types": ["letter"],
    "force_v2_lawyers_count": 3,
    "force_v1_lawyers_count": 0,
    "force_v2_lawyers": ["lawyer_001", "lawyer_011", "lawyer_020"],
    "force_v1_lawyers": [],
    "letter_v1_deprecated": false,  // W21 新增
    "deprecated_after_date": "2026-11-01",  // W21 新增
    "backward_compat_note": "现有 v1.0 文书数据保留 (W12 A2 doc_workflow 不动), 11/1 之后只支持 v2.0 生成 (POST /api/doc-gen/letter 自动走 v2.0)",  // W21 新增
    "phases_legend": {
      "disabled": "全 v1.0 (灰度前)",
      "ab_10pct": "8/15 v2.0 10% 灰度 + A/B 50/50 split",
      "rollout_50pct": "9/1 v2.0 全量 50% 灰度",
      "rollout_100pct": "10/1 v2.0 全量 100% (W21)"
    },
    "env_overrides": {
      "LEX_SKILL3_ROLLOUT_PHASE": "rollout_100pct",
      "LEX_SKILL3_ROLLOUT_PCT": 100,
      "LEX_SKILL3_AB_SPLIT": "50,50",
      "LEX_SKILL3_FORCE_V2_count": 3,
      "LEX_SKILL3_FORCE_V1_count": 0,
      "LEX_SKILL3_LETTER_V1_DEPRECATED": false  // W21 新增
    }
  },
  "next": "GET /api/doc-gen/metrics"
}
```

### 7.2 GET /api/doc-gen/metrics

```bash
curl http://localhost:8000/api/doc-gen/metrics | jq
```

```json
{
  "status": "ok",
  "service_id": "lexprime.skill.doc-gen.metrics",
  "rollout_phase": "rollout_100pct",
  "summary": {
    "total_records": [X, 10/1 实测填实],
    "by_version": {"letter_v1": 0, "letter_v2": [X, 10/1 实测填实]},
    "by_bucket": {"control": 0, "treatment_a": [X, 10/1 实测填实], "treatment_b": [X, 10/1 实测填实]},
    "5_dimension_avg_scores": {
      "facts": [0.X, 10/1 实测填实],
      "legal": [0.X, 10/1 实测填实],
      "demand": [0.X, 10/1 实测填实],
      "deadline": [0.X, 10/1 实测填实],
      "consequence": [0.X, 10/1 实测填实]
    },
    "conversion_rate_by_bucket": {
      "control": [0.XX, 10/8 实测填实],
      "treatment_a": [0.XX, 10/8 实测填实],
      "treatment_b": [0.XX, 10/8 实测填实]
    },
    "lawyer_satisfaction_avg": {
      "control": [X.X, 10/1 实测填实],
      "treatment_a": [X.X, 10/1 实测填实],
      "treatment_b": [X.X, 10/1 实测填实]
    },
    "ab_test_winner": null,  // 10/1 全量后 A/B test 关闭, winner 概念废弃
    "note": "10/1 全量 100% rollout, A/B test 已关闭, owner 10/1 19:00 实测填实"
  },
  "next": "GET /api/doc-gen/rollout/status"
}
```

### 7.3 POST /api/doc-gen/letter (W21 全量路由)

```bash
# 自动按 rollout 100pct 路由 v2.0 (不再有 v1.0 分配, 除非 letter_v1_deprecated=false + force_v1)
curl -X POST http://localhost:8000/api/doc-gen/letter \
  -H "Content-Type: application/json" \
  -d '{
    "lawyer_id": "L001",
    "case_id": "CASE-2026-001",
    "fields": {
      "sender": "张律师",
      "recipient": "李四",
      "subject": "货款催收"
    }
  }'
```

```json
{
  "gen_id": "dg-abc123def456",
  "doc_type": "letter",
  "doc_type_label": "律师函",
  "template_id": "letter_v2",
  "template_version": "v2.0-w15",
  "lawyer_id": "L001",
  "served_version": "letter_v2",  // 10/1 全量 100% 后全部 v2.0
  "bucket": "treatment_a",          // 50/50 hash 桶, 仅用于分桶报告
  "rollout_phase": "rollout_100pct",
  ...
}
```

---

## 8. W22+ 建议 (一句话)

> **W22+ 建议 (12/1 Phase 5.4 L4/L5 企业版)**: 视 10/1 全量 + 11/1 v1 退役数据, 若全量律师满意度 >= 4.5/5 + 转化率 >= 35%, 推荐 11/1 自动切 letter_v1_deprecated=true, 12/1 进入 Phase 5.4 L4/L5 企业版 (200 律师付费 + 50 律师企业版签约 + 10+ 律所 + Skill 3 v2.0 全量 + 3 agent 跑小 task 独立完成).

---

> **W21 skill3-full-rollout 10/1 全量 100% rollout 完整 runbook 落档**.
> 数字全部 [10/1 实测填实], owner 10/1 当天 19:00 patch 替换 placeholder.
> 8/15 10% 灰度 runbook 见 `skill3-v2-ab-test-2026-08-15.md` (同伴).
> 9/1 50% 灰度 runbook 见 `skill3-v2-50pct-rollout-2026-09-01.md` (同伴).
> 11/1 v1 退役计划见 `skill3-v1-deprecation-2026-11-01.md` (同期).