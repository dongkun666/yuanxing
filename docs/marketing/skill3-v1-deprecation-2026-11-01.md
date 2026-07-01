<!-- LexPrime Track B · W21 skill3-full-rollout 交付 -->
# 11/1 Skill 3 律师函 v1.0 退役计划 (Letter v1.0 Deprecation Plan · 2026-11-01)

> **版本**: v1.0 · 2026-06-30
> **Track**: A (AI 模型 + Skill Hub 灰度层)
> **Week**: W21 skill3-full-rollout (Skill 3 律师函 v1.0 退役)
> **状态**: plan 落档, 等 11/1 当天 owner 主持 + Tech Lead (lex-ai) 协作执行
> **依据**:
> - `docs/marketing/skill3-v2-100pct-rollout-2026-10-01.md` v1.0 (10/1 全量 runbook, 同期)
> - `docs/marketing/skill3-v2-50pct-rollout-2026-09-01.md` v1.0 (9/1 50% 灰度报告)
> - `core/rollout.py` v2.0-w21 (新增 letter_v1_deprecated 11/1 退役开关)
> - `api/doc_gen_router.py` v0.4.0-w21 (端点 + 自动路由 + 退役开关报告)
> - `tests/test_skill3_full_rollout.py` v1.0-w21 (新增, 36 测试覆盖 11/1 退役逻辑)
> - `templates/docs/letter_v1.md` v1.0-w21 (顶部加 deprecated banner)
> - W12 A2 commit 829d25c (doc_workflow 状态机, 5 状态保留)
> - W11 PRD V5.0 § 5.4 横切面 4 技能引擎 Skill Hub + § 5.6 当事人服务类文书

> **核心定位 (W21 11/1 退役)**:
> - 8/15 律师函 v2.0 10% 灰度 + A/B test (W19 skill3-gradual)
> - 9/1 律师函 v2.0 50% 灰度 (W19 skill3-gradual)
> - 10/1 律师函 v2.0 100% 全量 (W21 skill3-full-rollout)
> - **11/1 letter v1.0 退役, letter_v1_deprecated=true** (W21 skill3-full-rollout, 同期)

---

## 0. 文档使用说明 (执行日 11/1 当天随身打印)

> 本计划是 11/1 Skill 3 律师函 v1.0 退役当天的"运行剧本",
> **总指挥 (PM) + Tech Lead (lex-ai/lex-coder) + BD + 100% 律师 (200 名, 全量用户)** 协作执行.
> 本计划 **核心目标**: 验证 10/1 全量 100% 期间 v2.0 稳定性后, 正式退役 v1.0, 全员 v2.0 生成.
> 本计划 **配套**:
> - `skill3-v2-100pct-rollout-2026-10-01.md` (10/1 全量 runbook)
> - `core/rollout.py` v2.0-w21 (灰度配置 + letter_v1_deprecated 开关)
> - `api/doc_gen_router.py` v0.4.0-w21 (端点 + 退役开关报告)
>
> **严守严禁 fabricate**:
> 1. **不要 fabricate 10/1 数据** (实测为主, owner 11/1 09:00 跑 metrics 抓取)
> 2. **不要 fabricate 退役数据** (实测为主, owner 11/1 当天 19:00 跑 metrics 抓取)
> 3. **数字全部 [10/1 实测填实] / [11/1 实测填实]**, owner 11/1 当天 patch 替换 placeholder

---

## 1. 11/1 v1.0 退役时间表 (5 阶段)

### 1.1 退役时间表总览

| 阶段 | 日期 | 灰度阶段 | 退役开关 | 说明 |
|------|------|----------|----------|------|
| **预热** | 10/1 - 10/25 | rollout_100pct | false | 100% 全量 v2.0, letter_v1 仍可用 (force_v1 律师兼容) |
| **预通知** | 10/25 - 10/31 | rollout_100pct | false | BD 通知律师 11/1 v1 退役 (邮件 + 微信群 + 朋友圈) |
| **退役日** | 11/1 09:00 | rollout_100pct | **true** | 切换 letter_v1_deprecated=true, 全员 v2.0 |
| **保持** | 11/1 - 11/30 | rollout_100pct | true | 全员 v2.0, 持续跟踪 metrics |
| **彻底清理** | 12/1 | rollout_100pct | true | v1.0 模板文件归档 (W22+ 决定) |

### 1.2 退役前 7 天预通知 (10/25 - 10/31)

```
[10/25] BD 邮件 + 微信群 + 朋友圈 通知
  标题: "重要通知: 11/1 起 LexPrime 律师函 v1.0 模板正式退役, 全员切换 v2.0"

  内容:
    - 退役时间: 2026-11-01 09:00 (公测 day 99)
    - 退役内容: 律师函 v1.0 (W9 v1.0-w9) 模板不再生成新文书
    - 影响范围: 仅律师函 (letter) 类型, 其他 3 文书类型 (complaint/defense/contract) 不变
    - 兼容性:
      * 现有 v1.0 文书数据保留 (W12 A2 doc_workflow 状态机不动)
      * 历史 v1.0 文书可继续查看/编辑/签字
      * 新生成律师函全部走 v2.0 (W15 v2.0-w15, 5 维度深度推理)
    - 升级要点 (W15 skill3-iterate 8 律师 mock 反馈驱动):
      * L1 王律师 → 时限梯度
      * L2 李律师 → 法条引用
      * L3 张律师 → 三段式事实
      * L4 赵律师 → 后果量化
      * L5 陈律师 → 履行步骤细化
      * L6 周律师 → 客户签字栏 + 律师执业证号
      * L7 吴律师 → AI 5 维度风险标注
      * L8 郑律师 → doc_workflow + signature_router 集成
    - 文档: docs/marketing/skill3-v2-100pct-rollout-2026-10-01.md (10/1 全量 runbook)

[10/26-10/31] 持续提醒
  - 微信群每日 1 次 (BD)
  - 邮件 1 次 (10/30, 周四)
  - 朋友圈 1 次 (10/31, 周日晚)
```

---

## 2. 11/1 09:00 退役切换 (5 min)

### 2.1 切换前 5 min (08:55 - 09:00)

```
[08:55] Tech Lead (lex-ai)
  - 验证当前状态 (10/1 全量 100% 保持期, 30 天后):
    curl http://localhost:8000/api/doc-gen/rollout/status
  - 期望: phase=rollout_100pct, rollout_pct=100, letter_v1_deprecated=false
  - 10/1 - 10/31 期间 metrics 累计: [X, 11/1 实测填实, owner 11/1 08:55 抓取]
  - 10/1 全量 100% 结论: [稳定/波动/异常, 11/1 实测填实]
  - 10/31 月度决策: [按计划 11/1 退役 / 推迟退役, 11/1 实测填实]

[08:58] 准备 env 切换命令 (W21 新增 letter_v1_deprecated 开关)
  $ export LEX_SKILL3_ROLLOUT_PHASE=rollout_100pct  # 保持
  $ export LEX_SKILL3_ROLLOUT_PCT=100  # 保持
  $ export LEX_SKILL3_LETTER_V1_DEPRECATED=true  # W21 新增: 11/1 退役开关
  $ export LEX_SKILL3_FORCE_V1=  # 清空 force_v1 (退役后无意义)
  $ export LEX_SKILL3_FORCE_V2=lawyer_001,lawyer_011,lawyer_020  # placeholder, 保留评审律师白名单
```

### 2.2 09:00 切换 (1 min)

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
        "letter_v1_deprecated": true,  # W21 新增字段
        "deprecated_after_date": "2026-11-01",
        "backward_compat_note": "现有 v1.0 文书数据保留 (W12 A2 doc_workflow 不动), 11/1 之后只支持 v2.0 生成"
      }
    }

[09:00:45] 端到端 smoke test (10 律师抽样)
  $ for i in 1 2 3 4 5 6 7 8 9 10; do
      curl -X POST http://localhost:8000/api/doc-gen/letter \
        -H "Content-Type: application/json" \
        -d "{\"lawyer_id\": \"lawyer_${i}_${RANDOM}\", \"fields\": {\"sender\": \"张律师\", \"recipient\": \"李四\"}}"
    done
  期望: 10 次调用 100% 返回 served_version=letter_v2 + bucket=treatment_a/b
  重要: 退役后即使 force_v1_lawyers 列表里的律师也强制 v2.0 (assign_version letter_v1_deprecated 优先级最高)
```

### 2.3 09:01-09:15 启动确认 (15 min)

```
[09:01-09:15] 退役稳定性观察
  - 5 分钟内持续观察 metrics 端点: curl http://localhost:8000/api/doc-gen/metrics | jq
  - 期望: 退役前 5 分钟 metrics 累计与切换后 5 分钟累计持平 (无新增 letter_v1 记录)
  - 异常: 若发现 letter_v1 记录新增 (>0), 立即排查 assign_version (letter_v1_deprecated 应被检查)
  - 兼容性: 现有 v1.0 文书数据查询/编辑/签字不受影响 (W12 A2 doc_workflow 不动)
```

---

## 3. 11/1 09:15 - 19:00 退役执行 (10h 跟踪)

### 3.1 退役机制 (5 时段 + 茶歇, 09:15-19:00)

> **复用 10/1 全量机制**, 退役当日验证 letter_v1_deprecated 开关生效 + 兼容性

| 时段 | 时间 | 环节 | 负责人 | 输出物 |
|------|------|------|--------|--------|
| **预热** | 09:15-09:30 | 100% 律师群发通知 (微信群 + 邮件 + 朋友圈) | BD | 律师确认清单 + 退役说明 |
| **时段 1** | 09:30-11:00 | 退役日验证 (10 律师抽样测 force_v1 律师强制 v2.0) | Tech | 退役验证 + v1 数据完整性 |
| **时段 2** | 11:00-13:00 | 律师新旧切换 (老用户对比 10/1 全量体验) | 全量律师 + Tech | 切换反馈 + 老用户满意度 |
| **茶歇** | 13:00-14:00 | 午休 + 律师微信群互动 | BD | 律师反馈收集 + 案例分享 |
| **时段 3** | 14:00-15:30 | v1.0 历史文书查询测试 (兼容性验证) | 律师 + Tech | doc_workflow 兼容性确认 |
| **时段 4** | 15:30-17:00 | 转化跟踪 + 客服答疑 (退役后律师投诉) | BD + Tech | 投诉数据 + 应急处理 |
| **时段 5** | 17:00-19:00 | 收尾 + 当日报告启动 | 总指挥 + Tech | 11/1 实测填实数字 + 报告 |
| **收尾** | 19:00-19:30 | 退役保持 + 12/1 准备 | Tech Lead | 当日报告交付 + 12/1 cron |

### 3.2 退役验证清单 (5 项)

```
[验证 1: 路由验证] 10:00 抽样 10 律师, 全部走 v2.0
  - 即使 force_v1_lawyers 配置里的律师也强制 v2.0
  - by_version: 100% letter_v2
  - by_bucket: 50/50 hash 桶 (treatment_a/b)

[验证 2: 兼容性验证] 10:30 抽样 5 律师, 查询 v1.0 历史文书
  - GET /api/doc-gen/{doc_id} 历史 v1.0 文书可正常返回
  - doc_workflow 状态机可继续推进 (draft → ai_reviewed → lawyer_reviewed → client_signed → archived)
  - signature_router 可继续上传签字 (历史 v1.0 + 新 v2.0 都支持)
  - 风险标注端点可继续调用 (POST /api/doc-gen/{doc_id}/risk-annotation)

[验证 3: 模板加载验证] 11:00 验证 letter_v1.md 模板仍可加载 (供历史数据查询)
  - GET /api/doc-gen/health 报告 letter_v1.md loaded=true
  - 历史 v1.0 文书重新渲染时仍可读 (不删除模板文件)
  - 但新增生成请求全部走 letter_v2.md (letter_v1 模板不再用于新生成)

[验证 4: 指标跟踪验证] 11:30 验证 metrics 跟踪正常
  - GET /api/doc-gen/metrics 返回 rollout_phase=rollout_100pct + letter_v1_deprecated=true
  - 退役后 by_version 不再有新增 letter_v1 记录
  - 5 维度评分持续跟踪 (来自 v2.0 自动提取)
  - 转化率 + 律师满意度持续跟踪

[验证 5: 应急回滚验证] 12:00 验证应急回滚能力 (不真回滚, 只验证逻辑)
  - 关闭 letter_v1_deprecated: env LEX_SKILL3_LETTER_V1_DEPRECATED=false
  - 重启服务: systemctl restart lexprime-backend
  - 验证: phase=rollout_100pct, letter_v1_deprecated=false
  - 验证: force_v1_lawyers 律师可走 v1 (向后兼容)
  - 紧急情况下可临时关闭退役开关 (例如律师投诉)
```

### 3.3 跟踪 3 指标 (与 10/1 一致, 持续跟踪)

```
[指标 1: 5 维度评分] 自动 + 律师主动评分
  期望: 全员 v2.0, 5 维度评分 100% 来自 letter_v2
  数据来源: GET /api/doc-gen/metrics → summary.5_dimension_avg_scores

[指标 2: 转化率] 生成后 7 天跟踪
  跟踪窗口: 11/1 09:00 - 11/8 09:00 (7 天)
  转化定义: 律师生成律师函后 7 天内是否付费
  期望: 全员 v2.0 转化率 >= 35% (10/1 baseline + 持平)
  数据来源: dashboard 付费转化指标 + paid_converted 事件

[指标 3: 律师满意度] 律师主动评分
  评分时间: 生成后 48h 内律师主动评分 (1-5)
  期望: 全员 v2.0 满意度 >= 4.5/5.0 (10/1 baseline + 持平)
  数据来源: 律师主动评价 (1v1 微信沟通 / 邮件回复 / 群内反馈)
```

---

## 4. 11/1 19:00 当日报告 (11/1 实测填实执行)

### 4.1 退役验证实测数据

> **数字全部 [11/1 实测填实, owner 11/1 19:00 patch 替换 placeholder]**

| 验证项 | 期望结果 | 实测结果 |
|--------|----------|----------|
| **路由验证** | 10 律师 100% v2.0 | [10/10 v2, 11/1 实测填实] |
| **兼容性验证** | v1.0 历史文书查询正常 | [5/5 查询成功, 11/1 实测填实] |
| **模板加载验证** | letter_v1.md 仍可加载 | [loaded=true, 11/1 实测填实] |
| **指标跟踪验证** | metrics 跟踪正常, 无新增 v1 记录 | [新增 v1 记录=0, 11/1 实测填实] |
| **应急回滚验证** | 关闭退役开关可恢复 v1 | [回滚逻辑正常, 11/1 实测填实] |

### 4.2 3 指标实测数据

> **数字全部 [11/1 实测填实, owner 11/1 19:00 patch 替换 placeholder]**

| 指标 | 期望目标 | 10/1 全量 baseline | 11/1 退役实测 | 趋势 |
|------|----------|---------------------|----------------|------|
| **5 维度评分 - facts** | v2 > v1 | [0.X, 10/1 实测填实] | [0.X, 11/1 实测填实] | [上升/持平/下降] |
| **5 维度评分 - legal** | v2 > v1 | [0.X, 10/1 实测填实] | [0.X, 11/1 实测填实] | [上升/持平/下降] |
| **5 维度评分 - demand** | v2 > v1 | [0.X, 10/1 实测填实] | [0.X, 11/1 实测填实] | [上升/持平/下降] |
| **5 维度评分 - deadline** | v2 > v1 | [0.X, 10/1 实测填实] | [0.X, 11/1 实测填实] | [上升/持平/下降] |
| **5 维度评分 - consequence** | v2 > v1 | [0.X, 10/1 实测填实] | [0.X, 11/1 实测填实] | [上升/持平/下降] |
| **转化率 (7 天)** | >= 35% v2 | [0.XX, 10/8 实测填实] | [0.XX, 11/8 实测填实] | [上升/持平/下降] |
| **律师满意度** | >= 4.5/5 v2 | [X.X, 10/1 实测填实] | [X.X, 11/1 实测填实] | [上升/持平/下降] |

### 4.3 10/1 vs 11/1 对比 (退役后稳定性验证)

> **核心对比**: 10/1 全量 100% 数据 vs 11/1 退役后数据, 验证 v1.0 退役对全员体验的影响

| 指标 | 10/1 全量 100% | 11/1 v1 退役后 | 趋势 | 备注 |
|------|----------------|----------------|------|------|
| **5 维度评分 - 综合** | [0.XX, 10/1 实测填实] | [0.XX, 11/1 实测填实] | [上升/持平/下降] | 退役后是否影响 v2 体验 |
| **律师满意度** | [X.X, 10/1 实测填实] | [X.X, 11/1 实测填实] | [上升/持平/下降] | 退役后律师是否投诉 |
| **转化率 (7 天)** | [0.XX, 10/8 实测填实] | [0.XX, 11/8 实测填实] | [上升/持平/下降] | 退役后转化趋势 |
| **律师投诉数** | [X, 10/1 实测填实] | [X, 11/1 实测填实] | [上升/持平/下降] | 退役后投诉量 |

### 4.4 11/1 异常处理 (4 场景)

| 异常 | 触发条件 | 行动 |
|------|----------|------|
| **退役开关未生效** | metrics 显示有新增 letter_v1 记录 | 立即排查 assign_version (letter_v1_deprecated 应被检查), 必要时重启服务 |
| **v1.0 历史文书查询失败** | 律师投诉历史 v1.0 文书打不开 | 检查 doc_workflow 状态机, 不动 letter_v1 模板文件 |
| **律师强烈反对退役** (20+) | 1h 内 20+ 律师投诉 v1 退役 | 临时关闭退役开关: env `LEX_SKILL3_LETTER_V1_DEPRECATED=false`, 11/2 02:00 owner 决策 |
| **W12 A2 doc_workflow 受影响** | doc_workflow 状态推进失败 | 检查 doc_workflow_router (W12 A2 commit 829d25c), 不动 letter_v1 模板 |

### 4.5 11/1 19:00 报告交付

```
[11/01 19:00] 退役报告启动
  - 文件: docs/marketing/skill3-v1-deprecation-2026-11-01.md (本文件)
  - 数据 patch: 把 § 4.1 验证表 + § 4.2 指标表 + § 4.3 对比表 全部 [实测填实]
  - commit: feat(marketing): W21 skill3-full-rollout 11/1 v1 退役 实测填实
  - push: origin/main

[11/01 19:30] 12/1 准备
  - env 保持: LEX_SKILL3_ROLLOUT_PHASE=rollout_100pct + LEX_SKILL3_LETTER_V1_DEPRECATED=true
  - cron 12/1 09:00 自动切换: scripts/trigger-skill3-v1-archive-1201.sh (待 W22+ 写)
    * 12/1 v1.0 模板文件归档 (mv letter_v1.md → letter_v1.md.deprecated)
    * 12/1 doc_gen_router.py 移除 letter_v1 模板加载逻辑 (可选)
  - 通知: BD 群发 12/1 v1 归档预告
```

---

## 5. 11/1 - 11/30 退役阶段保持 (30 天)

### 5.1 持续跟踪 (3 节奏)

```
[每日 09:00] 日常 metrics 汇总
  - curl http://localhost:8000/api/doc-gen/metrics | jq
  - 验证: letter_v1_deprecated=true, by_version 100% letter_v2, 无新增 letter_v1
  - 异常: 立即 patch (按 4 异常处理)

[每周一 09:00] 周度报告
  - 5 维度评分周均 + 转化率周累计 + 律师满意度周均
  - 报告: docs/marketing/skill3-v2-weekly-{date}.md
  - commit: feat(marketing): W21 skill3-full-rollout 周度跟踪

[每月 1 日 09:00] 月度报告
  - 11/1 - 11/30 退役阶段汇总 + 12/1 v1 归档决策建议
  - 报告: docs/marketing/skill3-v2-monthly-2026-11.md
  - commit: feat(marketing): W21 skill3-full-rollout 月度跟踪
```

### 5.2 11/1 - 11/30 关键事件

| 事件 | 日期 | 影响 | 行动 |
|------|------|------|------|
| 11/1 退役切换 | 11/1 09:00 | 启动 letter_v1_deprecated=true | 见 § 1-4 |
| 11/8 转化数据完整 | 11/8 09:00 | 7 天转化窗口 | owner 11/8 09:00 patch 转化率 |
| 11/30 月度收尾 | 11/30 23:59 | 11 月结束 | 月度报告 + 12/1 v1 归档决策 |
| 12/1 v1.0 归档 | 12/1 09:00 | letter_v1.md 归档 (可选) | W22+ 决定 |

---

## 6. 兼容性说明 (W12 A2 doc_workflow 不动)

### 6.1 现有 v1.0 文书数据保留 (向后兼容)

```
[W12 A2 doc_workflow 状态机 5 状态]
  - draft (草稿)
  - ai_reviewed (AI 风险标注完成)
  - lawyer_reviewed (律师人工复核)
  - client_signed (客户签字)
  - archived (归档)

[退役后兼容]
  - 现有 v1.0 文书可继续推进状态 (draft → ... → archived)
  - 现有 v1.0 文书可继续查看/编辑/签字/归档
  - doc_workflow_router PATCH /api/doc-gen/{doc_id}/state 不受影响
  - signature_router POST /api/signature/{doc_id} 不受影响 (历史 v1 + 新 v2 都支持)
  - risk_annotation POST /api/doc-gen/{doc_id}/risk-annotation 不受影响

[退役影响]
  - 仅影响新增生成: POST /api/doc-gen/letter 全部走 v2.0
  - 不影响: POST /api/doc-gen/letter-v2 (显式 v2, 一直走 v2)
  - 不影响: POST /api/doc-gen/complaint/defense/contract (其他 3 文书类型不变)
```

### 6.2 letter_v1.md 模板文件保留 (供历史数据查询)

```
[letter_v1.md v1.0-w21 顶部 deprecated banner]
  ⚠️ W21 skill3-full-rollout 退役公告 (lex-ai · 2026-06-30 落档)
  此模板为 letter v1.0 (W9 v1.0-w9), 2026-11-01 起正式退役。

[退役后保留 letter_v1.md 文件]
  - 理由 1: 历史 v1.0 文书查询时需要 (渲染/重读)
  - 理由 2: W12 A2 doc_workflow 状态机不影响 (template_id=letter_v1 仍存在)
  - 理由 3: 12/1 之前保留, 12/1 之后归档 (mv letter_v1.md → letter_v1.md.deprecated, W22+ 决定)

[退役后 letter_v1.md 加载逻辑]
  - GET /api/doc-gen/health 报告 letter_v1.md loaded=true (历史可读)
  - 但新增生成请求不再加载 letter_v1.md (letter_v1_deprecated=true 强制走 letter_v2.md)
```

---

## 7. 严守 fabricate 原则 (W21 复制 W18+W19+W20)

> **W18+W19+W20 严守 fabricate 原则, W21 复制**:
> 1. **不要 fabricate 律师反馈**: 实测为主, owner 11/1 跑律师试用, 反馈全部 [11/1 实测填实]
> 2. **不要 fabricate 退役数据**: 实测为主, owner 11/1 当天 19:00 跑 metrics 抓取, 数字全部 [11/1 实测填实]
> 3. **不要 fabricate 兼容性问题**: 实测为主, owner 11/1 当天验证 W12 A2 doc_workflow 不受影响
> 4. **forward-execute placeholder 模式**: runbook 流程 + 时间线 + 应急 + 跟踪节奏, 实际数字全部 placeholder
> 5. **严守 AI 辅助, 不替代律师**: 退役期间严守产品原则, 律师主动评分是核心, AI 评分仅辅助
> 6. **数据本地化**: 律师案件 / 客户 / 文书不离开律师电脑, 退役 metrics in-memory 收集不持久化敏感数据

---

## 8. 关联文档 + 配套资源

### 8.1 W21 skill3-full-rollout 配套 (本次交付)

- `core/rollout.py` v2.0-w21 (升级, letter_v1_deprecated 开关) - 11/1 退役开关
- `api/doc_gen_router.py` v0.4.0-w21 (升级) - 端点 + 退役开关报告
- `templates/docs/letter_v1.md` v1.0-w21 (升级) - 顶部加 deprecated banner
- `tests/test_skill3_full_rollout.py` v1.0-w21 (新增, 36 tests) - 退役逻辑验证
- `docs/marketing/skill3-v2-100pct-rollout-2026-10-01.md` (同期, 10/1 全量 runbook)
- `docs/marketing/skill3-v1-deprecation-2026-11-01.md` (本次, 11/1 v1 退役计划)

### 8.2 复用 W19 skill3-gradual (灰度底层)

- `core/rollout.py` v1.0-w19 (35 测试覆盖) - 灰度配置 + hash 分配 + metrics 跟踪
- `api/doc_gen_router.py` v0.3.0-w19 (升级) - /letter 自动路由 + /rollout/status + /metrics 3 端点
- `tests/test_skill3_ab_rollout.py` v1.0-w19 (35 tests) - 灰度逻辑 + 端点集成
- `docs/marketing/skill3-v2-ab-test-2026-08-15.md` (8/15 10% 灰度 runbook)
- `docs/marketing/skill3-v2-50pct-rollout-2026-09-01.md` (9/1 50% 灰度 runbook)

### 8.3 复用 W15 skill3-iterate (灰度对象)

- `prompts/skill3_letter_v2.yaml` v2.0-w15 (W15 commit e3f0940)
- `templates/docs/letter_v2.md` v2.0-w15 (W15 commit 3d429cd)
- `tests/test_skill3_letter_v2.py` v1.0-w15 (W15 commit e3f0940, 32 tests)

### 8.4 复用 W12 A2 doc_workflow (工作流集成, 不动)

- `core/doc_workflow.py` v1.0-w12 (W12 A2 commit 829d25c, 5 状态机)
- `api/doc_workflow_router.py` v1.0-w12 (W12 A2, 4 端点)
- `api/signature_router.py` v1.0-w12 (W12 A2, 签字集成)

### 8.5 复用 W11 PRD V5.0

- § 5.4 横切面 4: 技能引擎 Skill Hub (Skill 3 文书生成 v2.0 全量 + v1 退役)
- § 5.6 当事人服务类文书 (律师函策略性, 语气可选)
- § 11 成功指标 (Phase 4 KPI 体系, 公测 day 99 验证)

---

## 9. 附录: 退役配置参考

### 9.1 env 变量 (W21 新增 letter_v1_deprecated)

```bash
# 10/1 - 10/31 全量 100% 期间 (letter_v1 仍可用)
export LEX_SKILL3_ROLLOUT_PHASE=rollout_100pct
export LEX_SKILL3_ROLLOUT_PCT=100
export LEX_SKILL3_LETTER_V1_DEPRECATED=false  # W21 新增
export LEX_SKILL3_FORCE_V1=
export LEX_SKILL3_FORCE_V2=lawyer_001,lawyer_011,lawyer_020

# 11/1 - 退役后 (letter_v1 强制 v2.0)
export LEX_SKILL3_ROLLOUT_PHASE=rollout_100pct  # 保持
export LEX_SKILL3_ROLLOUT_PCT=100  # 保持
export LEX_SKILL3_LETTER_V1_DEPRECATED=true  # W21 新增: 11/1 退役开关
export LEX_SKILL3_FORCE_V1=  # 清空 (退役后无意义)
export LEX_SKILL3_FORCE_V2=lawyer_001,lawyer_011,lawyer_020  # 保留评审律师白名单
```

### 9.2 RolloutConfig 新增字段 (Python)

```python
@dataclass
class RolloutConfig:
    phase: RolloutPhase = RolloutPhase.DISABLED
    rollout_pct: int = 0
    ab_split_within_v2: Tuple[int, int] = (50, 50)
    force_v2_lawyers: List[str] = field(default_factory=list)
    force_v1_lawyers: List[str] = field(default_factory=list)
    enabled_doc_types: List[str] = field(default_factory=lambda: ["letter"])
    # W21 skill3-full-rollout 新增
    letter_v1_deprecated: bool = False  # 11/1 后 = True
```

### 9.3 assign_version 算法 (W21 更新)

```python
def assign_version(lawyer_id: str, doc_type: str = "letter") -> Tuple[LetterVersion, str]:
    cfg = get_rollout_config()

    # 1. 灰度范围外
    if doc_type not in cfg.enabled_doc_types:
        return LetterVersion.V1, "control"

    # 2. W21 新增: 11/1 v1.0 退役开关 (优先级最高)
    if cfg.letter_v1_deprecated and doc_type == "letter":
        bucket_num = _hash_lawyer(lawyer_id)
        threshold_a = cfg.ab_split_within_v2[0]
        bucket = "treatment_a" if bucket_num < threshold_a else "treatment_b"
        return LetterVersion.V2, bucket

    # 3-4. 强制列表 (W19)
    if lawyer_id in cfg.force_v2_lawyers:
        return LetterVersion.V2, "treatment_a"
    if lawyer_id in cfg.force_v1_lawyers:
        return LetterVersion.V1, "control"

    # 5. rollout_pct 灰度判定 (W19)
    bucket_num = _hash_lawyer(lawyer_id)
    if bucket_num >= cfg.rollout_pct:
        return LetterVersion.V1, "control"

    # 6. v2.0 内 A/B 分组 (W19)
    threshold_a = cfg.ab_split_within_v2[0]
    if bucket_num < threshold_a:
        return LetterVersion.V2, "treatment_a"
    return LetterVersion.V2, "treatment_b"
```

### 9.4 端点参考

```bash
# 退役日 11/1 09:00 验证
curl http://localhost:8000/api/doc-gen/rollout/status | jq .rollout.letter_v1_deprecated
# 期望: true

# 验证 force_v1 律师强制 v2.0
curl -X POST http://localhost:8000/api/doc-gen/letter \
  -H "Content-Type: application/json" \
  -d '{"lawyer_id": "L999", "fields": {}}'  # L999 假设在 force_v1
# 期望: served_version=letter_v2 (退役开关优先级最高)

# 验证历史 v1.0 文书查询 (兼容性)
curl http://localhost:8000/api/doc-gen/{doc_id}  # doc_id 为历史 v1.0 文书
# 期望: 正常返回 (doc_workflow 不受影响)
```

---

## 10. W22+ 建议 (一句话)

> **W22+ 建议 (12/1 Phase 5.4 L4/L5 企业版)**: 视 11/1 退役数据, 若退役后律师满意度仍 >= 4.5/5 + 转化率仍 >= 35% + 无重大投诉, 推荐 12/1 v1.0 模板归档 (mv letter_v1.md → letter_v1.md.deprecated) + 进入 Phase 5.4 L4/L5 企业版 (200 律师付费 + 50 律师企业版签约 + 10+ 律所 + Skill 3 v2.0 100% 全量 + v1.0 退役完成 + 3 agent 跑小 task 独立完成).

---

> **W21 skill3-full-rollout 11/1 v1.0 退役 完整 plan 落档**.
> 数字全部 [10/1 实测填实] / [11/1 实测填实], owner 11/1 当天 19:00 patch 替换 placeholder.
> 10/1 全量 runbook 见 `skill3-v2-100pct-rollout-2026-10-01.md` (同期).
> 兼容性: 现有 v1.0 文书数据保留 (W12 A2 doc_workflow 不动).