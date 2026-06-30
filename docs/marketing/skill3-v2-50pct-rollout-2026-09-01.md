<!-- LexPrime Track B · W19 skill3-gradual 交付 -->
# 9/1 Skill 3 律师函 v2.0 全量 50% 灰度 运行手册 (50% Rollout Runbook · 2026-09-01)

> **版本**: v1.0 · 2026-06-30
> **Track**: A (AI 模型 + Skill Hub 灰度层)
> **Week**: W19 skill3-gradual (Skill 3 律师函 v2.0 灰度)
> **状态**: runbook 落档, 等 9/1 当天 owner 主持 + BD 协作实测填实
> **依据**:
> - `docs/marketing/skill3-v2-ab-test-2026-08-15.md` v1.0 (本次同伴, 8/15 10% 灰度 + A/B test 报告)
> - `prompts/skill3_letter_v2.yaml` v2.0-w15 (W15 commit e3f0940, 5 维度深度推理 + 阈值 0.6)
> - `templates/docs/letter_v2.md` v2.0-w15 (W15 commit 3d429cd, 8 律师 mock 反馈驱动)
> - `core/rollout.py` v1.0-w19 (灰度配置 + hash 分配 + metrics 跟踪)
> - `api/doc_gen_router.py` v0.3.0-w19 (/letter 自动路由 + /rollout/status + /metrics)
> - W11 PRD V5.0 § 11 法务自检 (4 文书类型 + 5 维度风险标注)
> - W12 A2 commit 829d25c (doc_workflow 状态机 + 4 文书风险标注)

> **核心定位 (W19 skill3-gradual vs W15 skill3-iterate vs W18 l4l5-execute-825)**:
> - W15 skill3-iterate = 律师函 v2.0 模板 + prompt 优化 (开发完)
> - W19 skill3-gradual 8/15 = v2.0 10% 灰度 + A/B test (本次同伴)
> - **W19 skill3-gradual 9/1 = v2.0 全量 50% 灰度** (本次)
> - W20+ 计划: 10/1 v2.0 全量 100% 灰度 (视 8/15 + 9/1 数据)

---

## 0. 文档使用说明 (执行日 9/1 当天随身打印)

> 本手册是 9/1 Skill 3 律师函 v2.0 全量 50% 灰度当天的"运行剧本",
> **总指挥 (PM) + Tech Lead (lex-coder/lex-ai) + BD + 50% 律师 (100 名, 灰度内) + 50% 律师 (100 名, control 组)** 协作执行.
> 本手册 **核心目标**: 在 8/15 10% A/B test 基础上扩大到 50% 律师, 跟踪同样 3 指标 (5 维度评分 + 转化率 + 律师满意度), 验证 v2.0 全场景效果.
> 本手册 **配套**: `skill3-v2-ab-test-2026-08-15.md` (8/15 runbook) + `core/rollout.py` v1.0-w19 (灰度配置) + `api/doc_gen_router.py` v0.3.0-w19 (端点 + 自动路由).
> **严守严禁 fabricate**:
> 1. **不要 fabricate 律师反馈** (实测为主, owner 8/9 跑律师试用)
> 2. **不要 fabricate A/B test 数据** (实测为主, owner 8/15 + 9/1 跑灰度)
> 3. **数字全部 [9/1 实测填实]**, owner 9/1 当天 19:00 patch 替换 placeholder

---

## 1. 9/1 灰度阶段切换 (5 min, 09:00)

### 1.1 切换前 5 min (08:55 - 09:00)

```
[08:55] Tech Lead (lex-ai)
  - 验证当前状态 (8/15 灰度保持期, 16 天后):
    curl http://localhost:8000/api/doc-gen/rollout/status
  - 期望: phase=ab_10pct, rollout_pct=10
  - 8/15 - 8/31 期间 metrics 累计: ~X 条 [8/15-8/31 实测填实]
  - 8/15 A/B test 结论: [treatment_a/treatment_b/control/tie, 8/15 19:00 实测填实]

[08:58] 准备 env 切换命令
  $ export LEX_SKILL3_ROLLOUT_PHASE=rollout_50pct
  $ export LEX_SKILL3_ROLLOUT_PCT=50
  $ export LEX_SKILL3_AB_SPLIT=50,50
  # force_v2 强制列表: 8/15 winner 律师进 force_v2 (加速验证)
  $ export LEX_SKILL3_FORCE_V2=lawyer_001,lawyer_011,lawyer_020  # placeholder
  $ export LEX_SKILL3_FORCE_V1=
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
        "phase": "rollout_50pct",
        "rollout_pct": 50,
        "ab_split_within_v2": [50, 50],
        "force_v2_lawyers_count": 3
      }
    }

[09:00:45] 端到端 smoke test (10 律师抽样)
  $ for i in 1 2 3 4 5 6 7 8 9 10; do
      curl -X POST http://localhost:8000/api/doc-gen/letter \
        -H "Content-Type: application/json" \
        -d "{\"lawyer_id\": \"lawyer_${i}_${RANDOM}\", \"fields\": {\"sender\": \"张律师\", \"recipient\": \"李四\"}}"
    done
  期望: 10 次调用中 ~50% (4-6 次) 返回 served_version=letter_v2 + bucket=treatment_a/b
```

### 1.3 09:01-09:15 启动确认 (15 min)

```
[09:01-09:15] 灰度稳定性观察
  - 5 分钟内持续观察 metrics 端点: curl http://localhost:8000/api/doc-gen/metrics | jq
  - 期望: 10-20 个新 metric record, by_version 约 50% letter_v1 + 50% letter_v2
  - 异常: 若 v2 报错率 > 5% 或 latency P95 > 3s, 立即回滚到 ab_10pct (env 切换)
```

---

## 2. 9/1 09:15 - 19:00 灰度执行 (10h 跟踪)

### 2.1 灰度机制 (5 时段 + 茶歇, 09:15-19:00)

> **复用 8/15 灰度机制**, 时段式设计让 50% 律师群有充分时间体验 v2.0

| 时段 | 时间 | 环节 | 负责人 | 输出物 |
|------|------|------|--------|--------|
| **预热** | 09:15-09:30 | 50% 律师群发通知 (微信群 + 邮件 + 朋友圈) | BD | 律师确认清单 + 灰度范围说明 |
| **时段 1** | 09:30-11:00 | 灰度律师首次使用 v2.0 (生成 10+ 律师函) | 灰度律师 + Tech | v2.0 生成记录 + 5 维度评分 |
| **时段 2** | 11:00-13:00 | 灰度律师对比 v1.0 vs v2.0 (control 组对照) | 灰度律师 + control | A/B 对比数据 + 主观反馈 |
| **茶歇** | 13:00-14:00 | 午休 + 律师微信群互动 | BD | 律师反馈收集 + 案例分享 |
| **时段 3** | 14:00-15:30 | 灰度律师深度使用 (合同审查 + 文书生成联动) | 灰度律师 | Skill 1+2+3 联动数据 |
| **时段 4** | 15:30-17:00 | 转化跟踪 + 客服答疑 | BD + Tech | 转化率数据 (7 天后回填) |
| **时段 5** | 17:00-19:00 | 收尾 + 当日报告启动 | 总指挥 + Tech | 9/1 实测填实数字 + 报告 |
| **收尾** | 19:00-19:30 | 灰度阶段保持 + 10/1 全量准备 | Tech Lead | 当日报告交付 + 10/1 cron |

### 2.2 灰度 50% 律师抽样方法

```
[09:15 抽样逻辑] 50% 律师 = hash(lawyer_id) % 100 < 50
  - 假设公测 day 38 (9/1) 律师总数 200 (按 W18 kpi-snapshot-2026-08-09 推算)
  - 期望灰度律师: ~100 名 (200 * 50% = 100)
  - A/B 50/50: ~50 名 treatment_a (旧版 prompt 兼容) + ~50 名 treatment_b (新版 5 维度深度推理)

[09:15 抽样律师清单] 9/1 灰度律师 [实测填实, owner 9/1 09:15 通过 metrics 端点查询]
  treatment_a (50 名):
    1. [lawyer_id_001, 姓名 placeholder, 9/1 owner 填实]
    2. [lawyer_id_002, 姓名 placeholder, 9/1 owner 填实]
    ...
    50. [lawyer_id_050, 姓名 placeholder, 9/1 owner 填实]
  treatment_b (50 名):
    1. [lawyer_id_051, 姓名 placeholder, 9/1 owner 填实]
    2. [lawyer_id_052, 姓名 placeholder, 9/1 owner 填实]
    ...
    50. [lawyer_id_100, 姓名 placeholder, 9/1 owner 填实]
  control (100 名): hash % 100 >= 50, 继续走 v1.0 (无感知)
```

### 2.3 跟踪 3 指标 (与 8/15 一致)

```
[指标 1: 5 维度评分] 自动 + 律师主动评分
  自动: v2.0 生成时自动从 prompt 提取 risk_dim_facts/legal/demand/deadline/consequence (0-1 浮点)
  律师: 律师生成后 24h 内主动评分 (1-5), 通过 /api/doc-gen/metrics/update 端点 PATCH
  期望分布: facts 0.7-0.9, legal 0.6-0.85, demand 0.7-0.9, deadline 0.5-0.8, consequence 0.65-0.85

[指标 2: 转化率] 生成后 7 天跟踪
  跟踪窗口: 9/1 09:00 - 9/8 09:00 (7 天)
  转化定义: 律师生成律师函后 7 天内是否付费 (¥99/月个人版 / ¥449 创史体验官)
  期望: treatment_a/b 转化率 >= 30% (8/15 baseline + 5%)
  数据来源: dashboard 付费转化指标 + paid_converted 事件

[指标 3: 律师满意度] 律师主动评分
  评分时间: 生成后 48h 内律师主动评分 (1-5)
  期望: treatment_a/b 满意度 >= 4.2/5.0 (8/15 baseline + 持平)
  数据来源: 律师主动评价 (1v1 微信沟通 / 邮件回复 / 群内反馈)
```

---

## 3. 9/1 19:00 当日报告 (9/1 实测填实执行)

### 3.1 3 指标实测数据

> **数字全部 [9/1 实测填实, owner 9/1 19:00 patch 替换 placeholder]**

| 指标 | 期望目标 | v1.0 (control, 100 名) | treatment_a (~50 名) | treatment_b (~50 名) | A/B winner |
|------|----------|------------------------|----------------------|----------------------|------------|
| **5 维度评分 - facts** | v2 > v1 | [0.X, 9/1 实测填实] | [0.X, 9/1 实测填实] | [0.X, 9/1 实测填实] | t_a/b/v1 |
| **5 维度评分 - legal** | v2 > v1 | [0.X, 9/1 实测填实] | [0.X, 9/1 实测填实] | [0.X, 9/1 实测填实] | t_a/b/v1 |
| **5 维度评分 - demand** | v2 > v1 | [0.X, 9/1 实测填实] | [0.X, 9/1 实测填实] | [0.X, 9/1 实测填实] | t_a/b/v1 |
| **5 维度评分 - deadline** | v2 > v1 | [0.X, 9/1 实测填实] | [0.X, 9/1 实测填实] | [0.X, 9/1 实测填实] | t_a/b/v1 |
| **5 维度评分 - consequence** | v2 > v1 | [0.X, 9/1 实测填实] | [0.X, 9/1 实测填实] | [0.X, 9/1 实测填实] | t_a/b/v1 |
| **转化率 (7 天)** | >= 30% v2 | [0.XX, 9/8 09:00 实测填实] | [0.XX, 9/8 实测填实] | [0.XX, 9/8 实测填实] | t_a/b/v1 |
| **律师满意度** | >= 4.2/5 v2 | [X.X, 9/1 实测填实] | [X.X, 9/1 实测填实] | [X.X, 9/1 实测填实] | t_a/b/v1 |

### 3.2 8/15 vs 9/1 对比 (灰度扩展验证)

> **核心对比**: 8/15 10% 灰度数据 vs 9/1 50% 灰度数据, 验证 v2.0 在更大律师群的效果稳定性

| 指标 | 8/15 10% A/B | 9/1 50% 灰度 | 趋势 | 备注 |
|------|--------------|--------------|------|------|
| **treatment_a - 满意度** | [X.X, 8/15 实测填实] | [X.X, 9/1 实测填实] | [上升/持平/下降] | 大样本是否更稳定 |
| **treatment_b - 满意度** | [X.X, 8/15 实测填实] | [X.X, 9/1 实测填实] | [上升/持平/下降] | 大样本是否更稳定 |
| **v2 vs v1 - 5 维度** | [0.XX, 8/15 实测填实] | [0.XX, 9/1 实测填实] | [上升/持平/下降] | 大样本差异是否扩大 |
| **转化率 (treatment_b)** | [0.XX, 8/22 实测填实] | [0.XX, 9/8 实测填实] | [上升/持平/下降] | 50% 律师中转化趋势 |

### 3.3 A/B test 结论 (9/1 19:00 决策)

> **A/B winner 综合判定** (3 指标综合, 简化: 满意度 + 转化率):
> - winner = [treatment_a | treatment_b | control | tie, 9/1 19:00 实测填实]
> - 8/15 vs 9/1 趋势: [稳定/波动/扩大, 9/1 19:00 实测填实]
> - 推荐行动: [10/1 全量 100% / 调整 v2.0 prompt / 保持灰度, 9/1 19:00 实测填实]

### 3.4 9/1 异常处理 (4 场景)

| 异常 | 触发条件 | 行动 |
|------|----------|------|
| v2.0 报错率 > 5% | 5xx 错误 / 1h | 立即回滚: env `LEX_SKILL3_ROLLOUT_PHASE=ab_10pct`, 重启服务 |
| v2.0 latency P95 > 3s | 1h 监控 | 通知 Tech Lead 优化, 暂停灰度 (env ab_10pct) |
| 律师强烈负面反馈 (10+) | 1h 内 10+ 律师投诉 | 暂停灰度, 收集反馈, 9/2 02:00 owner 决策 |
| A/B 数据矛盾 + 大样本波动 | 8/15 vs 9/1 趋势反向 | 不立即行动, 9/8 09:00 转化数据出来再决策 |

### 3.5 9/1 19:00 报告交付

```
[09/01 19:00] 灰度报告启动
  - 文件: docs/marketing/skill3-v2-50pct-rollout-2026-09-01.md (本文件)
  - 数据 patch: 把 § 3.1 表格 + § 3.2 对比 + § 3.3 winner + § 3.4 异常全部 [实测填实]
  - commit: feat(marketing): W19 skill3-gradual 9/1 50% 灰度 实测填实
  - push: origin/main

[09/01 19:30] 10/1 切换准备
  - env 保持: LEX_SKILL3_ROLLOUT_PHASE=rollout_50pct
  - cron 10/1 09:00 自动切换: scripts/trigger-skill3-rollout-1001.sh (待 W20 写)
  - 通知: BD 群发 10/1 全量 100% 灰度预告
```

---

## 4. 9/1 灰度阶段保持 (30 天, 9/1 - 9/30)

### 4.1 持续跟踪 (3 节奏)

```
[每日 09:00] 日常 metrics 汇总
  - curl http://localhost:8000/api/doc-gen/metrics | jq
  - 验证: by_version ~50% v1 + 50% v2, by_bucket 50/50 split
  - 异常: 立即 patch (按 4 异常处理)

[每周一 09:00] 周度报告
  - 5 维度评分周均 + 转化率周累计 + 律师满意度周均
  - 报告: docs/marketing/skill3-v2-weekly-{date}.md
  - commit: feat(marketing): W19 skill3-gradual 周度跟踪

[每月 1 日 09:00] 月度报告
  - 9/1 - 9/30 灰度阶段汇总 + 10/1 全量 100% 决策建议
  - 报告: docs/marketing/skill3-v2-monthly-2026-09.md
  - commit: feat(marketing): W19/W20 skill3-gradual 月度跟踪
```

### 4.2 9/1 - 9/30 关键事件

| 事件 | 日期 | 影响 | 行动 |
|------|------|------|------|
| 9/1 切换 50% 灰度 | 9/1 09:00 | 启动 50% 灰度 | 见 § 1-3 |
| 9/8 转化数据完整 | 9/8 09:00 | 7 天转化窗口 | owner 9/8 09:00 patch 转化率 |
| 9/15 L4/L5 企业版上线 | 9/15 09:00 | 企业版律师进入 | W19 l4l5-enterprise-915 任务 (同期) |
| 9/30 月度收尾 | 9/30 23:59 | 9 月结束 | 月度报告 + 10/1 切换决策 |

### 4.3 10/1 切换准备 (cron 自动化, W20+)

```bash
#!/bin/bash
# scripts/trigger-skill3-rollout-1001.sh (W20+ 待写, 占位说明)
# 10/1 09:00 自动切换到 100% 全量 (视 8/15 + 9/1 数据)
export LEX_SKILL3_ROLLOUT_PHASE=rollout_100pct
export LEX_SKILL3_ROLLOUT_PCT=100
systemctl restart lexprime-backend
curl http://localhost:8000/api/doc-gen/rollout/status | jq
# 期望: phase=rollout_100pct, rollout_pct=100
```

> **W19 占位说明**: 实际 cron 脚本 W20+ 实现. 9/1 - 9/30 期间 env 保持 rollout_50pct, owner 手动验证.

---

## 5. 严守 fabricate 原则 (W19 复制 W18)

> **W18 严守 fabricate 原则, W19 复制**:
> 1. **不要 fabricate 律师反馈**: 实测为主, owner 8/9 跑律师试用, 反馈全部 [8/9 实测填实]
> 2. **不要 fabricate A/B test 数据**: 实测为主, owner 8/15 + 9/1 跑灰度, 数字全部 [8/15 实测填实] / [9/1 实测填实]
> 3. **forward-execute placeholder 模式**: runbook 流程 + 时间线 + 应急 + 跟踪节奏, 实际数字全部 placeholder
> 4. **严守 AI 辅助, 不替代律师**: 灰度期间严守产品原则, 律师主动评分是核心, AI 评分仅辅助
> 5. **数据本地化**: 律师案件 / 客户 / 文书不离开律师电脑, 灰度 metrics in-memory 收集不持久化敏感数据

---

## 6. 关联文档 + 配套资源

### 6.1 W19 skill3-gradual 配套 (本次交付)

- `core/rollout.py` v1.0-w19 (新增, 35 测试) - 灰度配置 + hash 分配 + metrics 跟踪
- `api/doc_gen_router.py` v0.3.0-w19 (升级) - /letter 自动路由 + /rollout/status + /metrics 3 端点
- `tests/test_skill3_ab_rollout.py` v1.0-w19 (新增, 35 tests) - 灰度逻辑 + 端点集成
- `docs/marketing/skill3-v2-ab-test-2026-08-15.md` (同伴, 8/15 10% 灰度 runbook)
- `docs/marketing/skill3-v2-50pct-rollout-2026-09-01.md` (本次, 9/1 50% 灰度 runbook)

### 6.2 复用 W15 skill3-iterate (灰度对象)

- `prompts/skill3_letter_v2.yaml` v2.0-w15 (W15 commit e3f0940)
- `templates/docs/letter_v2.md` v2.0-w15 (W15 commit 3d429cd)
- `tests/test_skill3_letter_v2.py` v1.0-w15 (W15 commit e3f0940, 32 tests)

### 6.3 复用 W12 A2 doc_workflow (工作流集成)

- `core/doc_workflow.py` v1.0-w12 (W12 A2 commit 829d25c, 5 状态机)
- `api/doc_workflow_router.py` v1.0-w12 (W12 A2, 4 端点)
- `api/signature_router.py` v1.0-w12 (W12 A2, 签字集成)

### 6.4 复用 W11 PRD V5.0

- § 5.4 Skill Hub (Skill 3 文书生成)
- § 5.6 当事人服务类文书
- § 11 法务自检 (4 文书类型 + 5 维度风险标注)

---

## 7. 附录: 端点 API 参考 (W19 新增, 与 8/15 runbook 共享)

### 7.1 GET /api/doc-gen/rollout/status

```bash
curl http://localhost:8000/api/doc-gen/rollout/status | jq
```

```json
{
  "status": "ok",
  "service_id": "lexprime.skill.doc-gen.rollout",
  "rollout": {
    "phase": "rollout_50pct",
    "rollout_pct": 50,
    "ab_split_within_v2": [50, 50],
    "enabled_doc_types": ["letter"],
    "force_v2_lawyers_count": 3,
    "force_v1_lawyers_count": 0,
    "force_v2_lawyers": ["lawyer_001", "lawyer_011", "lawyer_020"],
    "force_v1_lawyers": [],
    "phases_legend": {
      "disabled": "全 v1.0 (灰度前)",
      "ab_10pct": "8/15 v2.0 10% 灰度 + A/B 50/50 split",
      "rollout_50pct": "9/1 v2.0 全量 50% 灰度",
      "rollout_100pct": "全 v2.0 (未来 W20+)"
    },
    "env_overrides": {
      "LEX_SKILL3_ROLLOUT_PHASE": "rollout_50pct",
      "LEX_SKILL3_ROLLOUT_PCT": 50,
      "LEX_SKILL3_AB_SPLIT": "50,50",
      "LEX_SKILL3_FORCE_V2_count": 3,
      "LEX_SKILL3_FORCE_V1_count": 0
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
  "rollout_phase": "rollout_50pct",
  "summary": {
    "total_records": 187,
    "by_version": {"letter_v1": 95, "letter_v2": 92},
    "by_bucket": {"control": 95, "treatment_a": 48, "treatment_b": 44},
    "5_dimension_avg_scores": {
      "facts": 0.79, "legal": 0.73, "demand": 0.82, "deadline": 0.67, "consequence": 0.75
    },
    "conversion_rate_by_bucket": {
      "control": 0.26, "treatment_a": 0.32, "treatment_b": 0.38
    },
    "lawyer_satisfaction_avg": {
      "control": 3.9, "treatment_a": 4.3, "treatment_b": 4.5
    },
    "ab_test_winner": "treatment_b",
    "note": "实测为主, owner 8/15 + 9/1 跑灰度后填实"
  },
  "next": "GET /api/doc-gen/rollout/status"
}
```

### 7.3 POST /api/doc-gen/letter (W19 自动路由)

```bash
# 自动按 rollout 配置路由 v1.0 / v2.0
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
  "served_version": "letter_v2",  // 50% 灰度路由结果
  "bucket": "treatment_b",          // A/B test bucket
  "rollout_phase": "rollout_50pct",
  ...
}
```

---

## 8. W20+ 建议 (一句话)

> **W20+ 建议 (10/1 Phase 5.2)**: 视 8/15 + 9/1 灰度数据, 若 treatment_b 满意度 >= 4.5/5 + 转化率 >= 35%, 推荐 10/1 自动切换到 rollout_100pct (全量 v2.0);
> 若数据有波动, 保持 rollout_50pct 30 天, 11/1 再决策. Phase 5.2 Electron 打包 + 早期用户 1000+ 100 律师付费 + Skill 3 v2.0 全量 + 招 3 agent 启动.

---

> **W19 skill3-gradual 9/1 全量 50% 灰度 完整 runbook 落档**.
> 数字全部 [9/1 实测填实], owner 9/1 当天 19:00 patch 替换 placeholder.
> 8/15 10% 灰度 runbook 见 `skill3-v2-ab-test-2026-08-15.md` (同伴).
