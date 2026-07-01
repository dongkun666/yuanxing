<!-- LexPrime Track B · W19 skill3-gradual 交付 -->
# 8/15 Skill 3 律师函 v2.0 10% 灰度 + A/B Test 运行手册 (A/B Test Runbook · 2026-08-15)

> **版本**: v1.0 · 2026-06-30
> **Track**: A (AI 模型 + Skill Hub 灰度层)
> **Week**: W19 skill3-gradual (Skill 3 律师函 v2.0 灰度)
> **状态**: runbook 落档, 等 8/15 当天 owner 主持 + BD 协作实测填实
> **依据**:
> - `prompts/skill3_letter_v2.yaml` v2.0-w15 (W15 commit e3f0940, 5 维度深度推理 + 阈值 0.6)
> - `templates/docs/letter_v2.md` v2.0-w15 (W15 commit 3d429cd, 8 律师 mock 反馈驱动)
> - `core/rollout.py` v1.0-w19 (本次新增, 灰度配置 + hash 分配 + metrics 跟踪)
> - `api/doc_gen_router.py` v0.3.0-w19 (本次升级, /letter 自动路由 + /rollout/status + /metrics)
> - W15 l4l5 commit 900948f (8/25 L4/L5 律师试用反馈)
> - W11 PRD V5.0 § 11 法务自检 (4 文书类型 + 5 维度风险标注)
> - W12 A2 commit 829d25c (doc_workflow 状态机 + 4 文书风险标注)

> **核心定位 (W19 skill3-gradual vs W15 skill3-iterate vs W18 l4l5-execute-825)**:
> - W15 skill3-iterate = 律师函 v2.0 模板 + prompt 优化 (开发完)
> - W19 skill3-gradual = **v2.0 8/15 灰度 10% + A/B test** (本次)
> - 9/1 v2.0 全量 50% 灰度 (本次 deliverable 同伴)

---

## 0. 文档使用说明 (执行日 8/15 当天随身打印)

> 本手册是 8/15 Skill 3 律师函 v2.0 10% 灰度 + A/B test 当天的"运行剧本",
> **总指挥 (PM) + Tech Lead (lex-coder/lex-ai) + BD + 5 律师 L1-L5 (灰度 10% 抽样) + 5 律师 control 组 (灰度外)** 协作执行.
> 本手册 **核心目标**: 验证 v2.0 在真实律师场景下是否优于 v1.0, 跟踪 3 指标 (5 维度评分 + 转化率 + 律师满意度).
> 本手册 **配套**: `core/rollout.py` v1.0-w19 (灰度配置 + 分配) + `api/doc_gen_router.py` v0.3.0-w19 (端点 + 自动路由) + `test_skill3_ab_rollout.py` v1.0-w19 (35 测试).
> **严守严禁 fabricate**:
> 1. **不要 fabricate 律师反馈** (实测为主, owner 8/9 跑律师试用)
> 2. **不要 fabricate A/B test 数据** (实测为主, owner 8/15 + 9/1 跑灰度)
> 3. **数字全部 [8/15 实测填实]**, owner 8/15 当天 19:00 patch 替换 placeholder

---

## 1. 灰度时间线 + 阶段切换

| 阶段 | 启动时间 | 配置 (env) | 灰度范围 | A/B 分配 |
|------|---------|------------|----------|----------|
| **灰度前** | W18 (6/30) - 8/14 | `LEX_SKILL3_ROLLOUT_PHASE=disabled`, `LEX_SKILL3_ROLLOUT_PCT=0` | 全 v1.0 | 不适用 |
| **8/15 灰度** | 2026-08-15 09:00 | `LEX_SKILL3_ROLLOUT_PHASE=ab_10pct`, `LEX_SKILL3_ROLLOUT_PCT=10` | 10% 律师走 v2.0 | treatment_a 50% + treatment_b 50% (50/50) |
| **9/1 全量 50%** | 2026-09-01 09:00 | `LEX_SKILL3_ROLLOUT_PHASE=rollout_50pct`, `LEX_SKILL3_ROLLOUT_PCT=50` | 50% 律师走 v2.0 | treatment_a 50% + treatment_b 50% (50/50) |
| **未来 W20+ 全量** | TBD | `LEX_SKILL3_ROLLOUT_PHASE=rollout_100pct`, `LEX_SKILL3_ROLLOUT_PCT=100` | 全 v2.0 | 不适用 |

> **关键技术决策**:
> - **env 切换而非代码部署**: 8/15 + 9/1 灰度阶段切换走 cron + env, 不需要重启后端服务
> - **hash(lawyer_id) 分配**: SHA-256 稳定 hash, 同一律师永远同 bucket (deterministic, 防止串扰)
> - **强制列表覆盖**: `LEX_SKILL3_FORCE_V2` / `LEX_SKILL3_FORCE_V1` 支持白名单/黑名单 (评审 #N 关键律师)
> - **in-memory metrics**: 3 指标 in-memory 收集, 重启清零 (生产应接 Prometheus / OpenTelemetry)

---

## 2. 8/15 09:00 灰度启动 (5 min 切换)

### 2.1 启动前 5 min (08:55 - 09:00)

```
[08:55] Tech Lead (lex-ai)
  - 打开后端进程终端, 准备切换 env
  - 验证当前状态: curl http://localhost:8000/api/doc-gen/rollout/status
  - 期望: phase=disabled, rollout_pct=0

[08:58] 准备 env 切换命令 (避免手抖)
  $ export LEX_SKILL3_ROLLOUT_PHASE=ab_10pct
  $ export LEX_SKILL3_ROLLOUT_PCT=10
  $ export LEX_SKILL3_AB_SPLIT=50,50
  $ export LEX_SKILL3_FORCE_V2=  # 空 (无强制 v2 律师)
  $ export LEX_SKILL3_FORCE_V1=  # 空 (无强制 v1 律师)
```

### 2.2 09:00 切换 (1 min)

```
[09:00:00] 切换 env + 重启服务
  $ systemctl restart lexprime-backend
  $ # OR python -m uvicorn api.main:app --reload (dev)
  启动时间: ~30s (uvicorn + reload)

[09:00:30] 验证切换成功
  $ curl http://localhost:8000/api/doc-gen/rollout/status | jq
  期望: 
    {
      "status": "ok",
      "rollout": {
        "phase": "ab_10pct",
        "rollout_pct": 10,
        "ab_split_within_v2": [50, 50],
        "force_v2_lawyers_count": 0,
        "force_v1_lawyers_count": 0
      }
    }

[09:00:45] 端到端 smoke test (5 律师抽样)
  $ for i in 1 2 3 4 5; do
      curl -X POST http://localhost:8000/api/doc-gen/letter \
        -H "Content-Type: application/json" \
        -d "{\"lawyer_id\": \"lawyer_${i}_${RANDOM}\", \"fields\": {\"sender\": \"张律师\", \"recipient\": \"李四\"}}"
    done
  期望: 5 次调用中 ~10% (0-1 次) 返回 served_version=letter_v2 + bucket=treatment_a/b, 其余 letter_v1 + control
```

### 2.3 09:01-09:15 启动确认 (15 min)

```
[09:01-09:15] 灰度稳定性观察
  - 5 分钟内持续观察 metrics 端点: curl http://localhost:8000/api/doc-gen/metrics | jq
  - 期望: 5-10 个新 metric record, by_version 约 90% letter_v1 + 10% letter_v2
  - 异常: 若 v2 报错率 > 5% 或 latency P95 > 3s, 立即回滚到 disabled (env 切换)
```

---

## 3. 8/15 09:15 - 19:00 灰度执行 (10h 跟踪)

### 3.1 灰度机制 (1 段 + 5 时段, 09:15-19:00)

| 时段 | 时间 | 环节 | 负责人 | 输出物 |
|------|------|------|--------|--------|
| **预热** | 09:15-09:30 | 5 律师灰度抽样通知 (微信群 + 邮件) | BD | 律师确认清单 + 灰度范围说明 |
| **时段 1** | 09:30-11:00 | 灰度律师首次使用 v2.0 (生成 5+ 律师函) | 灰度律师 + Tech | v2.0 生成记录 + 5 维度评分 |
| **时段 2** | 11:00-13:00 | 灰度律师对比 v1.0 vs v2.0 (control 组对照) | 灰度律师 + control | A/B 对比数据 + 主观反馈 |
| **时段 3** | 13:00-15:00 | 中段检查 (Tech Lead 跑 metrics 汇总) | Tech Lead | 中段 3 指标快照 + 异常处理 |
| **时段 4** | 15:00-17:00 | 灰度律师深度使用 + 转化跟踪 | 灰度律师 + BD | 转化率数据 (7 天后回填) |
| **时段 5** | 17:00-19:00 | 收尾 + 当日报告启动 | 总指挥 + Tech | 8/15 实测填实数字 + 报告 |
| **收尾** | 19:00-19:30 | 灰度阶段保持 + cron 9/1 切换准备 | Tech Lead | 当日报告交付 + 9/1 cron |

### 3.2 灰度 10% 律师抽样方法

```
[09:15 抽样逻辑] 10% 律师 = hash(lawyer_id) % 100 < 10
  - 假设公测 day 21 (8/15) 律师总数 200 (按 W17 kpi-snapshot-2026-08-09 推算)
  - 期望灰度律师: ~20 名 (200 * 10% = 20)
  - A/B 50/50: ~10 名 treatment_a (旧版 prompt 兼容) + ~10 名 treatment_b (新版 5 维度深度推理)

[09:15 抽样律师清单] 8/15 灰度律师 [实测填实, owner 8/15 09:15 通过 metrics 端点查询]
  treatment_a (10 名):
    1. [lawyer_id_001, 姓名 placeholder, 8/15 owner 填实]
    2. [lawyer_id_002, 姓名 placeholder, 8/15 owner 填实]
    ...
    10. [lawyer_id_010, 姓名 placeholder, 8/15 owner 填实]
  treatment_b (10 名):
    1. [lawyer_id_011, 姓名 placeholder, 8/15 owner 填实]
    2. [lawyer_id_012, 姓名 placeholder, 8/15 owner 填实]
    ...
    10. [lawyer_id_020, 姓名 placeholder, 8/15 owner 填实]
  control (180 名): hash % 100 >= 10, 继续走 v1.0 (无感知)
```

### 3.3 3 指标跟踪机制

```
[指标 1: 5 维度评分] 自动 + 律师主动评分
  自动: v2.0 生成时自动从 prompt 提取 risk_dim_facts/legal/demand/deadline/consequence (0-1 浮点)
  律师: 律师生成后 24h 内主动评分 (1-5), 通过 /api/doc-gen/metrics/update 端点 PATCH
  期望分布: facts 0.7-0.9, legal 0.6-0.85, demand 0.7-0.9, deadline 0.5-0.8, consequence 0.65-0.85

[指标 2: 转化率] 生成后 7 天跟踪
  跟踪窗口: 8/15 09:00 - 8/22 09:00 (7 天)
  转化定义: 律师生成律师函后 7 天内是否付费 (¥99/月个人版 / ¥449 创史体验官)
  期望: treatment_a/b 转化率 >= 30% (优于 v1.0 baseline 25%)
  数据来源: dashboard 付费转化指标 + paid_converted 事件

[指标 3: 律师满意度] 律师主动评分
  评分时间: 生成后 48h 内律师主动评分 (1-5)
  期望: treatment_a/b 满意度 >= 4.2/5.0 (优于 v1.0 baseline 3.8/5.0)
  数据来源: 律师主动评价 (1v1 微信沟通 / 邮件回复)
```

---

## 4. 8/15 19:00 当日报告 (8/15 实测填实执行)

### 4.1 3 指标实测数据

> **数字全部 [8/15 实测填实, owner 8/15 19:00 patch 替换 placeholder]**

| 指标 | 期望目标 | v1.0 (control, 180 名) | treatment_a (~10 名) | treatment_b (~10 名) | A/B winner |
|------|----------|------------------------|----------------------|----------------------|------------|
| **5 维度评分 - facts** | v2 > v1 | [0.X, 8/15 实测填实] | [0.X, 8/15 实测填实] | [0.X, 8/15 实测填实] | t_a/b/v1 |
| **5 维度评分 - legal** | v2 > v1 | [0.X, 8/15 实测填实] | [0.X, 8/15 实测填实] | [0.X, 8/15 实测填实] | t_a/b/v1 |
| **5 维度评分 - demand** | v2 > v1 | [0.X, 8/15 实测填实] | [0.X, 8/15 实测填实] | [0.X, 8/15 实测填实] | t_a/b/v1 |
| **5 维度评分 - deadline** | v2 > v1 | [0.X, 8/15 实测填实] | [0.X, 8/15 实测填实] | [0.X, 8/15 实测填实] | t_a/b/v1 |
| **5 维度评分 - consequence** | v2 > v1 | [0.X, 8/15 实测填实] | [0.X, 8/15 实测填实] | [0.X, 8/15 实测填实] | t_a/b/v1 |
| **转化率 (7 天)** | >= 30% v2 | [0.XX, 8/22 09:00 实测填实] | [0.XX, 8/22 实测填实] | [0.XX, 8/22 实测填实] | t_a/b/v1 |
| **律师满意度** | >= 4.2/5 v2 | [X.X, 8/15 实测填实] | [X.X, 8/15 实测填实] | [X.X, 8/15 实测填实] | t_a/b/v1 |

### 4.2 A/B test 结论 (8/15 19:00 决策)

> **A/B winner 综合判定** (3 指标综合, 简化: 满意度 + 转化率):
> - winner = [treatment_a | treatment_b | control | tie, 8/15 19:00 实测填实]
> - 推荐行动: [全量 v2.0 / 调整 v2.0 prompt / 保持灰度, 8/15 19:00 实测填实]

### 4.3 8/15 异常处理 (4 场景)

| 异常 | 触发条件 | 行动 |
|------|----------|------|
| v2.0 报错率 > 5% | 5xx 错误 / 1h | 立即回滚: env `LEX_SKILL3_ROLLOUT_PHASE=disabled`, 重启服务 |
| v2.0 latency P95 > 3s | 1h 监控 | 通知 Tech Lead 优化, 暂停灰度 (env disabled) |
| 律师强烈负面反馈 | 1+ 律师投诉 | 暂停灰度, 收集反馈, 8/16 02:00 owner 决策 |
| A/B test 数据矛盾 | 满意度高但转化低 | 不立即行动, 继续跟踪 7 天, 8/22 09:00 再决策 |

### 4.4 8/15 19:00 报告交付

```
[08/15 19:00] 灰度报告启动
  - 文件: docs/marketing/skill3-v2-ab-test-2026-08-15.md (本文件)
  - 数据 patch: 把 § 4.1 表格 + § 4.2 winner + § 4.3 异常全部 [实测填实]
  - commit: feat(marketing): W19 skill3-gradual 8/15 A/B test 实测填实
  - push: origin/main

[08/15 19:30] 9/1 切换准备
  - env 保持: LEX_SKILL3_ROLLOUT_PHASE=ab_10pct
  - cron 9/1 09:00 自动切换: scripts/trigger-skill3-rollout-901.sh (待 W20 写)
  - 通知: BD 群发 9/1 50% 灰度预告
```

---

## 5. 9/1 灰度阶段切换准备 (cron 自动化)

### 5.1 9/1 09:00 cron 自动切换 (W20+ 实现)

```bash
#!/bin/bash
# scripts/trigger-skill3-rollout-901.sh (W20+ 待写, 占位说明)
# 9/1 09:00 自动切换到 50% 灰度
export LEX_SKILL3_ROLLOUT_PHASE=rollout_50pct
export LEX_SKILL3_ROLLOUT_PCT=50
systemctl restart lexprime-backend
# 验证
curl http://localhost:8000/api/doc-gen/rollout/status | jq
# 期望: phase=rollout_50pct, rollout_pct=50
```

> **W19 占位说明**: 实际 cron 脚本 W20+ 实现. 8/15 - 8/31 期间 env 保持 ab_10pct, owner 手动验证.

### 5.2 8/15 灰度阶段保持 (16 天)

```
[8/15 09:00 - 8/31 23:59] 灰度阶段保持 ab_10pct
  - env: LEX_SKILL3_ROLLOUT_PHASE=ab_10pct, LEX_SKILL3_ROLLOUT_PCT=10
  - 7 天转化跟踪: 8/15 - 8/22 09:00 跟踪转化率
  - 14 天满意度跟踪: 8/15 - 8/29 09:00 跟踪律师满意度
  - 16 天异常监控: 8/15 - 8/31 09:00 持续监控 3 指标 + 异常处理

[9/1 09:00] 切换到 rollout_50pct
  - 自动 (cron) 或手动 (env 切换)
  - 验证: /api/doc-gen/rollout/status phase=rollout_50pct
  - 进入 9/1 灰度阶段 (见 9/1 runbook)
```

---

## 6. 严守 fabricate 原则 (W19 复制 W18)

> **W18 严守 fabricate 原则, W19 复制**:
> 1. **不要 fabricate 律师反馈**: 实测为主, owner 8/9 跑律师试用, 反馈全部 [8/9 实测填实]
> 2. **不要 fabricate A/B test 数据**: 实测为主, owner 8/15 + 9/1 跑灰度, 数字全部 [8/15 实测填实] / [9/1 实测填实]
> 3. **forward-execute placeholder 模式**: runbook 流程 + 时间线 + 应急 + 跟踪节奏, 实际数字全部 placeholder
> 4. **严守 AI 辅助, 不替代律师**: 灰度期间严守产品原则, 律师主动评分是核心, AI 评分仅辅助
> 5. **数据本地化**: 律师案件 / 客户 / 文书不离开律师电脑, 灰度 metrics in-memory 收集不持久化敏感数据

---

## 7. 关联文档 + 配套资源

### 7.1 W19 skill3-gradual 配套 (本次交付)

- `core/rollout.py` v1.0-w19 (新增, 35 测试) - 灰度配置 + hash 分配 + metrics 跟踪
- `api/doc_gen_router.py` v0.3.0-w19 (升级) - /letter 自动路由 + /rollout/status + /metrics 3 端点
- `tests/test_skill3_ab_rollout.py` v1.0-w19 (新增, 35 tests) - 灰度逻辑 + 端点集成
- `docs/marketing/skill3-v2-ab-test-2026-08-15.md` (本次, 8/15 runbook)
- `docs/marketing/skill3-v2-50pct-rollout-2026-09-01.md` (同伴, 9/1 runbook)

### 7.2 复用 W15 skill3-iterate (灰度对象)

- `prompts/skill3_letter_v2.yaml` v2.0-w15 (W15 commit e3f0940)
- `templates/docs/letter_v2.md` v2.0-w15 (W15 commit 3d429cd)
- `tests/test_skill3_letter_v2.py` v1.0-w15 (W15 commit e3f0940, 32 tests)

### 7.3 复用 W12 A2 doc_workflow (工作流集成)

- `core/doc_workflow.py` v1.0-w12 (W12 A2 commit 829d25c, 5 状态机)
- `api/doc_workflow_router.py` v1.0-w12 (W12 A2, 4 端点)
- `api/signature_router.py` v1.0-w12 (W12 A2, 签字集成)

### 7.4 复用 W11 PRD V5.0

- § 5.4 Skill Hub (Skill 3 文书生成)
- § 5.6 当事人服务类文书
- § 11 法务自检 (4 文书类型 + 5 维度风险标注)

---

## 8. 附录: 端点 API 参考 (W19 新增)

### 8.1 GET /api/doc-gen/rollout/status

```bash
curl http://localhost:8000/api/doc-gen/rollout/status | jq
```

```json
{
  "status": "ok",
  "service_id": "lexprime.skill.doc-gen.rollout",
  "rollout": {
    "phase": "ab_10pct",
    "rollout_pct": 10,
    "ab_split_within_v2": [50, 50],
    "enabled_doc_types": ["letter"],
    "force_v2_lawyers_count": 0,
    "force_v1_lawyers_count": 0,
    "force_v2_lawyers": [],
    "force_v1_lawyers": [],
    "phases_legend": {
      "disabled": "全 v1.0 (灰度前)",
      "ab_10pct": "8/15 v2.0 10% 灰度 + A/B 50/50 split",
      "rollout_50pct": "9/1 v2.0 全量 50% 灰度",
      "rollout_100pct": "全 v2.0 (未来 W20+)"
    },
    "env_overrides": {
      "LEX_SKILL3_ROLLOUT_PHASE": "ab_10pct",
      "LEX_SKILL3_ROLLOUT_PCT": 10,
      "LEX_SKILL3_AB_SPLIT": "50,50",
      "LEX_SKILL3_FORCE_V2_count": 0,
      "LEX_SKILL3_FORCE_V1_count": 0
    }
  },
  "next": "GET /api/doc-gen/metrics"
}
```

### 8.2 GET /api/doc-gen/metrics

```bash
curl http://localhost:8000/api/doc-gen/metrics | jq
```

```json
{
  "status": "ok",
  "service_id": "lexprime.skill.doc-gen.metrics",
  "rollout_phase": "ab_10pct",
  "summary": {
    "total_records": 42,
    "by_version": {"letter_v1": 38, "letter_v2": 4},
    "by_bucket": {"control": 38, "treatment_a": 2, "treatment_b": 2},
    "5_dimension_avg_scores": {
      "facts": 0.78, "legal": 0.72, "demand": 0.81, "deadline": 0.65, "consequence": 0.74
    },
    "conversion_rate_by_bucket": {
      "control": 0.25, "treatment_a": 0.30, "treatment_b": 0.35
    },
    "lawyer_satisfaction_avg": {
      "control": 3.8, "treatment_a": 4.2, "treatment_b": 4.5
    },
    "ab_test_winner": "treatment_b",
    "note": "实测为主, owner 8/15 + 9/1 跑灰度后填实"
  },
  "next": "GET /api/doc-gen/rollout/status"
}
```

### 8.3 POST /api/doc-gen/letter (W19 自动路由)

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
  "template_id": "letter_v1",
  "template_version": "v1.0-w9",
  "lawyer_id": "L001",
  "served_version": "letter_v1",  // 自动路由结果
  "bucket": "control",              // A/B test bucket
  "rollout_phase": "ab_10pct",     // 当前灰度阶段
  ...
}
```

---

> **W19 skill3-gradual 8/15 10% 灰度 + A/B test 完整 runbook 落档**.
> 数字全部 [8/15 实测填实], owner 8/15 当天 19:00 patch 替换 placeholder.
> 9/1 50% 全量灰度 runbook 见 `skill3-v2-50pct-rollout-2026-09-01.md` (同伴).
