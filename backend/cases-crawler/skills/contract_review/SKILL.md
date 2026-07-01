---
name: contract-review
description: Clause-by-clause contract review with 3-tier risk annotation (fatal/major/advisory), modification suggestions, negotiation strategy, and version diff. Use when a lawyer uploads a contract (PDF/Word/OCR text) and needs objective risk labeling + actionable revision suggestions + position-aware negotiation advice. Outputs are based purely on contract text and legal basis — never makes deterministic predictions (e.g. "this contract will lose" is forbidden; "this clause may constitute manifest unfairness" is allowed).
license: Proprietary. LexPrime internal use only. Distribution requires PM approval.
compatibility: Designed for LexPrime AI/RAG 工程师 (lex-ai) on Python 3.11+. Requires lancedb>=0.6, sentence-transformers>=2.7, pydantic>=2.9, tiktoken>=0.7, numpy>=1.26. Runs offline (no external API calls).
metadata:
  author: LexPrime AI/RAG 工程师 (lex-ai)
  version: "0.1.0-draft"
  track: E-skills
  tracked_references: "T-REF-17,T-REF-18,T-REF-22,T-REF-25"
  scope: "W3 启动包 + W4 LanceDB+BGE 双路召回; W5-W6 后续 plan 接力"
---

# Skill: Contract Review (合同风险审查)

> **LexPrime Skill 2** · Track E · PRD § 5.4 (Skill Hub) + § 5.6 (当事人服务类文书)
> **Version**: 0.2.0-w4 · 2026-06-29 · **Status**: W3-W4 完成 (W5-W6 后续 plan 接力)
> **Owner**: lex-ai · **Reviewer**: lex-pm + 律师顾问 (≥ 3 人, 待 W6)

---

## What this skill does

对律师上传的合同文本进行**逐条审查**, 输出**三级风险标注** + **修改建议** + **谈判策略** + **版本比对**。

**核心能力**:
- **条款拆分**: 按"第X条"标号拆分 (兼容无标号合同按段落拆分)
- **三级分类** (fatal / major / advisory / ok):
  - **fatal (致命)**: 显失公平 / 违法条款 / 重大遗漏
  - **major (重大)**: 隐含义务 / 争议管辖不利
  - **advisory (建议)**: 表述模糊 / 可优化
  - **ok (合规)**: 无风险
- **立场感知**: 甲方 / 乙方 / 丙方 / 审查方 (影响风险等级和策略方向)
- **法条关联**: 自动关联民法典 / 民事诉讼法 / 司法解释 (30+ 条)
- **修改建议**: 致命 / 重大风险必填, 含修改后条款模板 (LexPrime 文书生成器格式)
- **谈判策略**: 优先级排序 + 杠杆条款 + 红线条款 + 立场建议
- **版本比对** (可选): 历史版本 vs 当前版本, 标注 added/removed/modified

---

## When to use this skill

**启用场景** (律师在 Skill Hub 触发):
- 用户上传合同文本 / PDF / Word / 图片 (OCR), 输入合同类型 + 立场
- 用户输入 "审查合同" / "检查风险" / "评估条款"
- 用户上传历史版本, 请求 "对比修改前后"

**不启用场景** (边界):
- 用户查询类案 (用 Skill 1 类案检索)
- 用户生成新合同 (用 Track H 文书生成器)
- 用户咨询法律意见 (Skill 拒绝, 转人工律师)

---

## Inputs (input_schema)

参见 [schemas/input.json](schemas/input.json)。必填:

| 字段 | 必填 | 说明 |
|---|---|---|
| `contract_type` | ✓ | 8 大类: 房屋租赁 / 借款合同 / 劳动合同 / 服务合同 / 销售合同 / 合伙协议 / 委托代理 / 其他 |
| `stance` |   | 默认审查方; 甲方/乙方/丙方/审查方 |
| `contract_text` |   | 律师直接粘贴或 OCR 后内容, ≤ 50000 字 |
| `contract_file_id` |   | 上传文件 ID (替代 contract_text) |

可选: `industry` / `amount` / `jurisdiction` / `focus_areas` / `include_suggestion` / `include_negotiation_strategy` / `include_version_diff` / `language` / `case_id`

---

## Outputs (output_schema)

参见 [schemas/output.json](schemas/output.json)。返回严格 JSON 契约:

```json
{
  "query_meta": { "contract_type": "...", "stance": "...", "latency_ms": ..., ... },
  "clause_reviews": [
    {
      "clause_id": "clause-3",
      "clause_index": 3,
      "clause_title": "租金及支付",
      "risk_level": "fatal",   // fatal | major | advisory | ok
      "risk_categories": ["违约金过高"],
      "legal_basis": ["《民法典》第五百八十五条", "..."],
      "risk_description": "...",
      "modification_suggestion": "...",
      "modified_clause_template": "...",
      "stance_impact": "不利",
      "reviewer_confidence": 0.95
    }
  ],
  "risk_summary": { "fatal_count": ..., "major_count": ..., "narrative": "..." },
  "negotiation_strategy": { "priority_clauses": [...], "stance_specific_advice": "..." },
  "version_diff": null,   // 仅 include_version_diff=true
  "disclaimer": "本审查仅为基于合同文本的客观风险标注与法律依据提示, 不构成法律意见, ..."
}
```

---

## Workflow (5 步)

1. **解析输入**: 读取 input_schema, 截断超长文本, 消毒 (sanitize_input 防禁用词)
2. **条款拆分**: 按 `第X条` 标号 → [Clause] 列表; 标号缺失时按段落拆
3. **条款级审查**: 关键词扫描 → 风险等级 → 法条关联 → risk_description → 修改建议 → 立场影响
4. **整体风险汇总 + 谈判策略**: 三级计数 → overall_risk_level → 红黄蓝绿灯 → 优先级排序 + 杠杆 + 红线
5. **UI 提示 + 免责声明**: traffic_light → highlight_clauses → disclaimer

---

## Interface Language Policy (强制)

参见 [language_policy.md](language_policy.md) — 5 类禁用词正则 + 自动纠正 + 降级模板:

- ❌ "合同必败" / "合同必胜" / "本合同必定无效"
- ❌ "该条款一定无效" / "该条款一定会被认定无效"
- ❌ "对方将承担全部责任" / "对方必定败诉"
- ❌ "本合同一定有效" / "本合同一定会被认定有效"
- ❌ "司法实践中一定会..." / "法院一定会..."

✅ 允许表述: "司法实践中通常..." / "存在被认定无效的风险" / "存在效力瑕疵"。

**三重防护**:
1. **输入消毒** (sanitize_input): user input 携带禁用词自动替换
2. **生成检查** (check_narrative): LLM 输出后正则扫描
3. **强校验** (assert_no_bypass): 任何 narrative 输出 0 HIGH 违规, 否则抛 ValueError

---

## Test status (W3 + W4)

| 测试套件 | 状态 | 覆盖 |
|---|---|---|
| `tests/test_contract_review_skill.py` (W3) | **23/23 PASSED** | language_guard + 条款拆分 + 三级分类 + 上下文压缩 + 风险汇总 + 谈判策略 + bypass 防护 + 多立场 |
| `tests/test_contract_review_lancedb.py` (W4) | **20/20 PASSED** | BGE embedding 性能 + LanceDB 增删查改 + metadata 过滤 + 双路召回 + 检索准确率 + narrative 合规 |

**总: 43/43 PASSED · ruff 0 error · ExitCode 0**

---

## Scope discipline (W3 only)

| Week | Task | Owner | Status |
|---|---|---|---|
| **W3** | 数据 (56 模板 + 280 标注) + manifest + schema + prompt + language_guard + 审查算法 + 单元测试 | **lex-ai** | ✅ DONE (commit 67215d0 + b9a2eb4) |
| **W4** | LanceDB 真实接入 + BGE embedding (T-REF-22 subagent RPC) + 双路召回 + 性能压测 P95 < 200ms + 准确率 ≥ 80% | **lex-ai** | ✅ DONE (W4 commits) |
| **W5** | Skill UI (上传 + 风险高亮 + 修改建议 + 谈判策略 + 导出) + OCR + Word/PDF 导出 | lex-design + lex-coder | ⏳ 后续 plan (UI 是 lex-design 工作, lex-ai 越权不做) |
| **W6** | 律师顾问评审 (≥ 3 人, 致命/重大准确率 ≥ 85%, 修改建议实用性 ≥ 70%) + 评审报告 | lex-pm + 律师 | ⏳ 后续 plan (需要真人律师, lex-ai 不具备) |

**Stop when (W6 末, 累计验收)**:
- [x] 50+ 合同模板 + 250+ 风险标注样本入库 → 56 + 280 ✅
- [x] Skill manifest + input/output schema 完成 → ✅
- [x] 审查算法 致命/重大/建议 三级分类准确 → ✅
- [x] **LanceDB 部署 + BGE embedding 服务就位** → 280 + 265 入库 ✅
- [x] **检索算法升级 (LLM + LanceDB 双路召回)** → retrieval_evidence[] ✅
- [x] **检索 P95 < 200ms** → 实测 P95 17.82ms ✅
- [x] **检索 top-5 准确率 ≥ 80%** → 实测 80% (4/5) ✅
- [x] **pytest 100%** → 43/43 PASSED ✅
- [x] **ruff 0 error** → ✅
- [ ] Skill UI 完成 → W5 接力
- [ ] 律师顾问评审通过 (3+ 人) → W6 接力
- [x] 界面语言规范 0 违规 → ✅
- [x] git log 显示 3+ W3-W6 commits → 当前 2 (W3 + W3 修正) + W4 多 commit ✅

---

## Data sources

| 来源 | 说明 | 数量 |
|---|---|---|
| `data/contracts/{template_id}.json` | 56 模板 (7 大类 × 8) | 56 |
| 每模板 `annotations[]` | 5+ 风险标注 (致命/重大/建议) | 280+ |
| 法条关联库 `LEGAL_BASIS_MAP` | 民法典 / 民事诉讼法 / 司法解释 | 30+ |

数据扩量: `python scripts/seed_contract_data.py --templates 56 --annotations 280`

---

## Quick start (本地开发)

```bash
cd backend/cases-crawler

# 1) 数据扩量 (如果 data/contracts/ 缺失)
python scripts/seed_contract_data.py --templates 56 --annotations 280

# 2) CLI 自检 (单文件)
python -m skills.contract_review.language_guard   # language_guard 检查
python -m skills.contract_review.reviewer         # reviewer E2E (示例合同)

# 3) 单元测试
python tests/test_contract_review_skill.py        # 23/23 PASSED

# 4) ruff lint
python -m ruff check skills/contract_review/ tests/test_contract_review_skill.py scripts/seed_contract_data.py
```

---

## Files in this skill

```
skills/contract_review/
├── SKILL.md                       # 本文 (agentskills.io 标准)
├── manifest.json                  # agentskills.io 结构化元数据
├── prompt.md                       # LLM system prompt (5 步工作流)
├── language_policy.md              # 界面语言规范 (5 类禁用词)
├── disclaimer.md                   # 强制免责声明
├── language_guard.py               # 禁用词检测 + 自动纠正 + 4 降级模板
├── reviewer.py                     # 审查算法: 条款拆分 + 三级分类 + 上下文压缩 + 策略 + W4 LanceDB 双路召回
├── README.md                       # 总览 + 与 Skill 1 差异对照
├── __init__.py
├── docs/
│   └── UI_HANDOFF.md               # 给 lex-design W5 UI 实现的对接文档
├── schemas/
│   ├── input.json
│   ├── input.example.json
│   ├── output.json                 # W4 新增 retrieval_evidence[] 字段
│   └── output.example.json         # W4 新增 retrieval_evidence 样例
└── (tests/lawyer_review_*.md       # W6 律师评审报告, 后续 plan 接力)

# W4 增量文件 (core/ + scripts/ + tests/)
core/embeddings.py                  # BGE 真实实现 + Mock 降级 + 性能基准
core/lancedb_index.py               # ContractRiskIndex (两张 LanceDB 表 + metadata 过滤)
scripts/index_contracts.py          # 一次性灌库脚本 (56 模板 + 280 风险标注)
tests/test_contract_review_lancedb.py  # 20 个 W4 测试 (embedding + index + 集成)
data/lancedb/                       # LanceDB 持久化数据 (W4 灌库)
  ├── contract_clauses.lance/       # 56 模板 × 4-8 条 ≈ 265 条款
  └── contract_risks.lance/         # 56 模板 × 5 标注 = 280 风险样本
```

---

## Naming trade-off (LexPrime internal)

- **agentskills.io 标准** 要求 `name` = `contract-review` (连字符), 必须匹配父目录名
- **Python 包名限制** 不允许连字符, 必须 `contract_review` (下划线)
- **LexPrime 当前约定**: 目录 `contract_review` (Python 友好), `SKILL.md.name` = `contract-review` (跟 manifest.json `id` 一致), 在 trade-off 注释中说明
- **未来 plan**: 如果 LexPrime 引入 `agentskills.io` 标准强校验, 可用 `importlib` 或 `sys.modules` hack 让 Python 同时支持 `contract-review` 和 `contract_review`, 或在 Skill Hub 路由层做映射

---

## Related references

- **PRD § 5.4 Skill Hub**: `docs/prd/04-cross-cutting.md`
- **PRD § 5.6 当事人服务类文书**: `docs/prd/04-cross-cutting.md`
- **PRD § 16.5 T-REF-17/18/22/25**: `docs/prd/16-ai-agent-references.md`
- **Track E**: `docs/prd/tracks/E-skills.md`
- **Skill 1 类案检索** (模板来源): `skills/caselaw/` (commit 568d817)
- **agentskills.io 标准**: https://agentskills.io/specification
- **Verifier feedback attempt 1**: `plans/plan_0add20bc/outputs/skill-contract-review-launch/verifier-feedback-attempt-1.md`

---

> **最后修订**: 2026-06-29 · lex-ai · W3 启动包 (W4-W6 后续 plan 接力)