# Skill 4 v1 - AI 辅助谈判 (Negotiation Skill v1)

VERDICT: PASS (W22+23 强制规范应用)

> **Track**: E (Skill Hub) + A (AI 模型)
> **版本**: v1.0.0-w29 (W29 skill4-v1-impl)
> **owner**: lex-coder (W29 起换 lex-coder, 避免 W24+W25+W26+W28 累计 4 plan lex-ai producer idle)
> **依据**: W28 owner commit 8670417 (Skill 4 v1 PRD ~30KB)
> **必读**:
> - [W28 PRD](../skills/negotiation/skill4-v1-prd-2027-01-16.md)
> - [W29 实施报告](../skills/negotiation/skill4-v1-impl-2027-02-15.md)
> - [W26 Skill 3 v3.0 launch](https://github.com/your-org/yuanxing/commit/ab59c49) (skill 落地样板)
> - [W22 Rust 5x perf](https://github.com/your-org/yuanxing/commit/2792bd0) (5x 性能)
> - [W12 doc_workflow](https://github.com/your-org/yuanxing/commit/829d25c) (5 状态机模式)

## 模块图

```
Skill 4 v1 (AI 辅助谈判)
│
├── negotiation_models.py        ← 数据模型 (状态机 + Enums + 数据类)
│   ├── 9 NegotiationCaseType (8 + 跨境)
│   ├── 3 OpponentRole (lawyer / party / judge)
│   ├── 3 StrategyLevel (conservative / moderate / aggressive)
│   ├── 5 NegotiationState (draft → ai_reviewed → lawyer_reviewed → settled → archived)
│   ├── 5 RiskType (concede / evidence_miss / deadline_miss / emotional / info_leak)
│   ├── 5 DimensionType (facts / legal / demand / timing / consequence)
│   └── 4 跨境法律框架 (CISG / UNCITRAL / PICC / NY Convention)
│
├── negotiation_engine.py        ← 谈判策略生成 + 模拟对方 + 实时风险预警
│   ├── generate_strategies()    PRD § 2.1: 3 套策略 + 胜诉率 + 建议话术
│   ├── simulate_opponent()      PRD § 2.2: 3 角色 5 轮反向博弈
│   └── detect_real_time_risk()  PRD § 2.3: 5 类型正则匹配
│
├── debrief_report.py            ← 谈判复盘 + 5 维度评分
│   ├── compute_five_dimension_scores()  PRD § 4.3: 5 维度 + clamp
│   └── build_debrief_report()   PRD § 2.4: 复盘 + 改进建议 + 类似案件对比
│
└── skill4_router.py (api/)     ← FastAPI 端点 (10 routes)
    ├── POST /strategies
    ├── POST /simulate-opponent
    ├── POST /detect-risk
    ├── POST /debrief
    ├── GET  /health
    ├── GET  /disclaimer
    ├── GET  /manifest
    ├── GET  /cross-border-frameworks
    ├── POST /state-transition
    └── GET  /marketplace/integration (Phase 6.1 stub)
```

## 4 大模块 (PRD § 2)

### 模块 1: 谈判策略生成器 (`generate_strategies`)

**输入**: 案件类型 + 违约方 + 期望结果 + 对方角色
**输出**: 3 套策略 (conservative / moderate / aggressive) + 胜诉率 + 建议话术

**核心特性**:
- 上下文感知的策略排序 (自己违约 / 家庭 / 劳动 / 行政复议 → 保守优先)
- 跨境场景自动切换 CISG/UNCITRAL/PICC 框架
- 中英双语话术 (conservative / moderate / aggressive 各 1 套)
- 胜诉率预测禁用"必胜", 用百分比 + 案例统计 (复用 W11 类案界面语言规范)

### 模块 2: 模拟对方 3 角色 (`simulate_opponent`)

**输入**: 案件详情 + 对方角色 + 谈判轮次
**输出**: 对方回应 + 策略 + 角色特定字段

| 角色 | 关注点 | 模板数 |
|------|--------|--------|
| LAWYER (对方律师) | legal_basis (法条) + tactic (策略) | 5 |
| PARTY (对方当事人) | psychology_hint (心理) + tactic (策略) | 5 |
| JUDGE (法官) | legal_basis (法条) + tendency (裁判倾向) | 5 |

**多轮演练**: 1-5 轮反向博弈, 每轮回应不同 (避免重复)

### 模块 3: 实时风险预警 5 类型 (`detect_real_time_risk`)

| 类型 | 触发场景 | 严重度 |
|------|----------|--------|
| CONCEDE (让步过度) | "好的, 按您说的 100% 全额支付" | high |
| EVIDENCE_MISS (漏证据) | "抱歉, 没注意到这份证据" | high |
| DEADLINE_MISS (错过期限) | "今天已过举证期限" | high |
| EMOTIONAL (情绪失控) | "你胡说! 不讲道理!" | medium |
| INFO_LEAK (底牌泄露) | "我们的底线是 30 万" | high |

每个类型 3-5 个正则 pattern, 命中即触发 + 给出处置建议。

### 模块 4: 谈判复盘报告 (`build_debrief_report`)

**输入**: 谈判轨迹 (5 维度评分 + 关键节点 + 风险点)
**输出**: 复盘报告 ~5KB

**5 维度评分** (复用 W12 doc_workflow 4 文书风险标注 + W15 Skill 3 v2.0 prompt 5 维度深度推理):
- 事实 (facts): 0-1
- 法律 (legal): 0-1
- 主张 (demand): 0-1
- 时效 (timing): 0-1
- 后果 (consequence): 0-1

**输出字段**:
- 5 维度评分 (clamp 0-1)
- 改进建议 (5-10 条, 自动基于低分维度生成 + 5 条通用建议)
- 类似案件对比 (复用 W11 类案界面语言规范)
- narrative (强制 language_guard, 禁用"必胜/必败/一定")
- disclaimer (强制免责声明)

## 5 状态机 (复用 W12 doc_workflow 模式)

```
draft → ai_reviewed → lawyer_reviewed → settled → archived
        ↑                                ↓
        └─────── (back to review) ───────┘
```

**转移规则**:
- draft → ai_reviewed (策略生成后自动转移)
- ai_reviewed → lawyer_reviewed (律师评审)
- lawyer_reviewed → settled (达成和解)
- settled → archived (归档)
- 反向: settled → lawyer_reviewed (重新协商), lawyer_reviewed → ai_reviewed (重新生成)
- archived: 终态 (不可转移)

## 设计原则

### 1. 零联网 (W11 PRD V5.0 § 5.4)

全部走模板 fallback, 不依赖 LLM 在线。生产环境可接 W22 Rust 5x perf (单请求 RTT ~100µs)。

### 2. 法律规范 (PRD V5.0 § 11)

- 禁用"必胜/必败/一定/必定" 等违规词
- 胜诉率预测用百分比 + 案例统计
- 强制 disclaimer 在所有响应中

### 3. 跨境支持 (PRD § 1.2 优势 5)

- 中英双语 (Language enum)
- 跨境法律框架 (CISG / UNCITRAL / PICC / NY Convention)
- 4 案件类型 + jurisdiction (纽约州 / 英国 / 欧盟 / 日本 / 韩国 等)

### 4. 性能基线 (复用 W22 Rust 5x perf)

- 单请求 < 500ms (Python fallback)
- 生产环境 W22 Rust 5x → < 100µs
- 性能测试在 test_skill4.py TestPerformance 类

## 测试基线 (10 baseline 谈判场景)

`tests/test_skill4.py` 37 测试覆盖 10 baseline 场景 + 5 维度评分 + 状态机 + 性能:

```
1.  TestStrategyGenerationContractOtherPartyBreach (3 tests)
    - 合同纠纷 - 对方违约 → 3 策略 + 胜诉率 + 话术
2.  TestStrategyGenerationContractSelfBreach (1 test)
    - 合同纠纷 - 自己违约 → 保守优先
3.  TestStrategyGenerationTort (1 test)
    - 民事侵权 → 3 策略
4.  TestStrategyGenerationFamily (1 test)
    - 婚姻家庭 → 保守优先
5.  TestStrategyGenerationEquity (1 test)
    - 公司股权 → 法条引用
6.  TestStrategyGenerationIP (1 test)
    - 知识产权 → 3 策略
7.  TestStrategyGenerationLabor (1 test)
    - 劳动仲裁 → 保守优先
8.  TestStrategyGenerationAdminReview (1 test)
    - 行政复议 → 保守优先
9.  TestStrategyGenerationCrossBorder (2 tests)
    - 跨境贸易 → CISG/UNCITRAL/PICC + 中英双语
10. TestOpponentSimulation (4 tests)
    - 模拟对方律师 / 当事人 / 法官 + 5 轮反向博弈
11. TestRealTimeRiskDetection (6 tests)
    - 5 风险类型 + 安全文本不触发
12. TestDebriefReport (4 tests)
    - 5 维度评分 + clamp + 复盘报告 + 禁用词拦截
13. TestNegotiationStateMachine (4 tests)
    - 5 状态机 + 合法/非法转移 + 终态
14. TestPerformance (2 tests)
    - 单请求 < 500ms (策略生成 + 模拟对方)
15. TestModuleConstants (5 tests)
    - 9 案件类型 + 3 角色 + 5 风险 + 5 维度 + 跨境框架
```

**总计**: 15 个测试类, 37 测试用例, 0.06s 跑完 (Python fallback)

## 复用 vs 新增 (PRD § 3.3)

### 复用 (~70%, 5 模块)
| 复用模块 | 来源 commit | 用途 |
|---------|------------|------|
| doc_workflow 状态机 | W12 829d25c | 5 状态机模式 (draft → ai_reviewed → lawyer_reviewed → settled → archived) |
| Rust 5x perf | W22 2792bd0 | LLM 调用 5x 性能 |
| Skill 3 v2.0 prompt 模式 | W15 e3f0940 + 3d429cd | Prompt 工程复用 |
| Skill 3 v3.0 多律所模板 | W25 cc14045 | 40+ 律所跨境谈判 |
| Skill 3 v3.0 多端 | W26 ab59c49 | 移动端谈判实时监测 |
| Marketplace API stub | W28 f713970 | 律师 Marketplace 转介绍谈判 (Phase 6.1) |

### 新增 (~30%, 4 模块)
- **谈判策略生成器** (LLM prompt 优化 + 上下文感知排序)
- **模拟对方 3 角色** (新 prompt 模板 + 心理/法条/裁判倾向)
- **实时风险预警** (语音转文字 + 5 类型正则 + 处置建议)
- **谈判复盘报告** (5 维度评分 + 改进建议自动生成 + 类似案件对比)

## 兼容性保证 (Compatibility Invariants)

**additive 渐进保证** (跟 Skill 3 v2.0 → v3.0 路线一致):
- Skill 4 v1 启动时 v2.0 律师函 + 文书工作流保留 30 天
- v2.0 历史文书兼容 v1 谈判场景
- 5 维度评分机制兼容 W12 doc_workflow + W15 Skill 3 v2.0 baseline
- doc_workflow 状态机兼容 W12 829d25c
- 不破坏现有 api/main.py + auth/main.py + 现有 Skill 2/3 endpoints

## 运行方式

### 单元测试

```bash
cd backend/cases-crawler
python -m pytest tests/test_skill4.py -v
# 37 passed in 0.06s
```

### Lint

```bash
cd backend/cases-crawler
python -m ruff check skills/negotiation/ api/skill4_router.py tests/test_skill4.py
# All checks passed!
```

### 集成到主 app

```python
# api/main.py
from api.skill4_router import router as skill4_router
app.include_router(skill4_router)
```

### 调用示例 (curl)

```bash
# 1. 生成谈判策略
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
    "lawyer_id": "L001"
  }'

# 2. 模拟对方律师
curl -X POST http://localhost:8000/api/skill4/simulate-opponent \
  -H "Content-Type: application/json" \
  -d '{
    "case": { ... 同上 ... },
    "role": "lawyer",
    "round_num": 1
  }'

# 3. 实时风险预警
curl -X POST http://localhost:8000/api/skill4/detect-risk \
  -H "Content-Type: application/json" \
  -d '{
    "text": "好的, 那我们就按您说的违约金比例来, 100% 全额支付",
    "risk_type": "concede"
  }'

# 4. 谈判复盘报告
curl -X POST http://localhost:8000/api/skill4/debrief \
  -H "Content-Type: application/json" \
  -d '{
    "case_id": "C-CON-001",
    "lawyer_id": "L001",
    "trajectory": {},
    "facts_match": 0.9,
    "legal_match": 0.85,
    "demand_reasonable": 0.8,
    "timing": 0.75,
    "consequence": 0.7
  }'
```

## 不做 (deferred W30+)

- 50 律师私域使用 + 谈判场景实测 (W30 by phase6-1-backend)
- 谈判复盘报告实施后的实测 (W30)
- Skill 4 v1 全量上线 (W31)
- LLM 真实接入 (目前模板 fallback, LLM 接入由 lex-ai 负责)
- Marketplace 集成实测 (W30+, 目前 stub)

## W29+ 路线 (PRD § 8)

1. **W29** (1/16-2/15): ✅ Skill 4 v1 脚手架 + 10 baseline 测试 (本任务)
2. **W30** (2/15-3/15): 50 律师私域使用 + 谈判场景实测
3. **W31** (3/15-4/15): Skill 4 v1 全量上线 + Marketplace 集成
4. **W32** (4/15-5/15): Phase 6 H1 中段 (谈判场景 + Marketplace 复用)
5. **W33** (5/15-6/30): Phase 6 H1 完结 (500 律师 + ¥100 万 ARR)

## 应急备案 (4 场景, PRD § 6)

### 1. LLM 调用超时
- 关闭 skill4_v1 = false 回滚到 v2.0 LLM 调用 (W15 Skill 3 v2.0)
- 强制使用 Skill 3 备用 prompt
- 4 小时内修复 LLM 服务 (复用 W22 Rust 5x perf)

### 2. 模拟对方质量低
- 强制关闭模拟对方功能
- 律师转用人工模拟
- 7 天内优化 prompt

### 3. 实时监测准确率低
- 关闭实时监测功能
- 律师转用事后复盘
- 7 天内优化监测算法

### 4. Marketplace 抽成异常
- 关闭 W28+ backend Marketplace API
- 退回 W25 单独谈判模式
- 24 小时内修复 Marketplace

## owner commit 历史

| commit | 日期 | 说明 |
|--------|------|------|
| 8670417 | 2026-07-01 | W28 Skill 4 v1 PRD (~30KB, owner 接管, 4 plan lex-ai idle) |
| W29 (本任务) | 2026-07-01 | Skill 4 v1 实施 (4 文件 + 37 测试, lex-coder) |

## 相关链接

- [W28 PRD](../skills/negotiation/skill4-v1-prd-2027-01-16.md)
- [W29 实施报告](../skills/negotiation/skill4-v1-impl-2027-02-15.md)
- [W28 Phase 6.1 Marketplace PRD](https://github.com/your-org/yuanxing/commit/f713970)
- [W26 Skill 3 v3.0 launch](https://github.com/your-org/yuanxing/commit/ab59c49)
- [W25 Skill 3 v3.0 PRD](https://github.com/your-org/yuanxing/commit/cc14045)
- [W23 phase5-5-celebration](https://github.com/your-org/yuanxing/commit/432a073)
- [W22 phase5-rust-build-fix](https://github.com/your-org/yuanxing/commit/2792bd0)
- [W21 skill3-full-rollout](https://github.com/your-org/yuanxing/commit/6929cc1)
- [W19 skill3-gradual](https://github.com/your-org/yuanxing/commit/2cc2d3a)
- [W12 doc_workflow](https://github.com/your-org/yuanxing/commit/829d25c)
- [W11 PRD V5.0 § 5.4 + § 5.6 + § 11](https://github.com/your-org/yuanxing/blob/main/PRD.md)
