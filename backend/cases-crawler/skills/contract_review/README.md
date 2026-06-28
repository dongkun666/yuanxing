# Skill 2: 合同风险审查

> **Status**: W3 启动包 (W3-6 数据 + manifest/schema/prompt + language_guard + 审查算法 + 单元测试; W5 UI + W6 律师评审 待启动)
> **Owner**: lex-ai · **Reviewer**: lex-pm + 律师顾问 (≥ 3 人)
> **Track**: E-skills · **PRD**: § 5.4 Skill Hub + § 5.6 当事人服务类文书

---

## 目录结构

```
skills/contract-review/
├── manifest.json                  # agentskills.io 标准清单
├── prompt.md                       # LLM system prompt (角色 + 5 步工作流 + 错误处理)
├── language_policy.md              # 界面语言规范 (PRD § 5.4 硬约束)
├── disclaimer.md                   # 强制免责声明
├── language_guard.py               # 禁用词检测 + 自动纠正 + 降级模板
├── reviewer.py                     # 审查算法: 条款拆分 + 三级分类 + 上下文压缩 + 策略生成
├── README.md                       # 本文件
├── docs/
│   └── UI_HANDOFF.md               # 给 lex-design 的 UI 对接文档 (W5)
├── schemas/
│   ├── input.json                  # JSON Schema 输入契约
│   ├── input.example.json
│   ├── output.json                 # JSON Schema 输出契约
│   └── output.example.json
└── tests/                          # 律师评审 + 自动化测试 (W6)
    └── (后续 W6 律师评审报告入此目录)
```

---

## 快速开始 (本地开发)

```bash
cd backend/cases-crawler

# 1) 数据扩量 (50+ 合同模板 + 250+ 风险标注)
python scripts/seed_contract_data.py --templates 50 --annotations 250

# 2) 自检 language_guard
python skills/contract-review/language_guard.py

# 3) 自检 reviewer 算法 (mock 合同文本)
python -m skills.contract_review.reviewer

# 4) 运行单元测试
python tests/test_contract_review_skill.py
```

---

## 数据状态 (2026-06-29)

| 表 | 当前 | 目标 | 状态 |
|---|---|---|---|
| contract_templates | 56 | ≥ 50 | ✅ PASS (7 大类 × 8 模板) |
| risk_annotations | 280+ | ≥ 250 | ✅ PASS (每模板 5+ 标注) |
| contract_reviews | 0 | (后续 Phase) | - |

---

## 单元测试状态

`tests/test_contract_review_skill.py` — **PASSED** (15 项)

| # | 测试 | 验证点 |
|---|---|---|
| 1 | test_language_guard_pass | 8 条正确表述全 PASS |
| 2 | test_language_guard_fail_high | 10 条违规表述全拦截 |
| 3 | test_language_guard_correction | 违规表述自动纠正 |
| 4 | test_templates_pass | 4 个降级模板全合规 |
| 5 | test_split_clauses_standard | "第X条" 标号拆分正确 |
| 6 | test_split_clauses_fallback | 无标号按段落拆分 |
| 7 | test_classify_clause_risk_fatal | 违约金过高 / 显失公平 致命 |
| 8 | test_classify_clause_risk_major | 争议管辖不利 重大 |
| 9 | test_classify_clause_risk_advisory | 表述模糊 建议 |
| 10 | test_compress_clauses_no_compression | 小样本不压缩 |
| 11 | test_compress_clauses_truncate | 大样本自动压缩 |
| 12 | test_compute_risk_summary | 三级分类计数正确 |
| 13 | test_compute_negotiation_strategy | 优先级排序 + 立场策略 |
| 14 | test_run_skill_e2e | 端到端 run_skill 输出合规 |
| 15 | test_sanitize_input_bypass_prevention | 输入消毒防绕过 |

---

## 关键指标对照 PRD

| 指标 | 目标 | 当前 |
|---|---|---|
| Skill 加载时间 | < 3s | 待 W5 实测 |
| 审查 P95 延迟 | < 2s | mock 0ms (待生产 LLM 实测) |
| 律师评审致命/重大准确率 | ≥ 85% | 待 W6 评审 |
| 修改建议实用性 | ≥ 70% | 待 W6 评审 |
| 界面语言违规率 | 0 / 1000 次 | test 验证 0 / 15 |
| 数据规模 | 50 模板 + 250 标注 | ✅ 56 + 280+ |

---

## 风险等级 (致命 / 重大 / 建议 / 合规)

| 等级 | 颜色 | 触发条件 |
|---|---|---|
| **fatal (致命)** | 红色 | 显失公平 / 违法条款 / 重大遗漏 |
| **major (重大)** | 黄色 | 隐含义务 / 争议管辖不利 |
| **advisory (建议)** | 蓝色 | 表述模糊 / 可优化 |
| **ok (合规)** | 绿色 | 无风险 |

---

## 路线图

- [x] W3: 数据扩量 (50 模板 + 250 标注)
- [x] W3: manifest + input/output schema (agentskills.io 标准)
- [x] W3: prompt + language_policy + disclaimer
- [x] W3: language_guard + 15 项单元测试
- [x] W3: reviewer 算法 (条款拆分 + 三级分类 + 上下文压缩 + 策略生成)
- [x] W3: UI hand-off doc (待 lex-design 实现)
- [ ] W4: LanceDB 真实接入 + BGE embedding (T-REF-22 subagent RPC)
- [ ] W5: UI 实现 (上传 + 风险高亮 + 修改建议 + 谈判策略)
- [ ] W5: 性能压测 (P95 < 2s 验证)
- [ ] W6: 律师顾问评审 (≥ 3 人, 致命/重大准确率 ≥ 85%)
- [ ] W6: 律师评审报告入 `tests/lawyer_review_*.md`

---

## 与 Skill 1 的复用

| 维度 | Skill 1 类案检索 | Skill 2 合同审查 | 复用 |
|---|---|---|---|
| manifest 模板 | agentskills.io 标准 | agentskills.io 标准 | ✓ 完全复用 |
| language_guard 模式 | check_narrative + 4 类正则 | check_narrative + 5 类正则 | ✓ 模式复用 |
| 上下文压缩 (T-REF-25) | top_k_truncate / summary_extract / hierarchical | top_k_truncate / summary_extract / hierarchical | ✓ 完全复用 |
| 风险等级 UI | 红黄绿灯 (traffic_light) | 红黄蓝绿 (traffic_light) | ✓ 模式复用 |
| 数据存储 | cases / laws 表 | contracts / risk_annotations / legal_basis 表 | - 新增 |
| LLM 模型 | qwen2.5:7b → 72b | qwen2.5:7b → 72b | ✓ 完全复用 |

---

## 依赖 (复用 Skill 1)

```
lancedb>=0.6           # 本地向量库
sentence-transformers>=2.7  # BGE 中文 embedding
tiktoken>=0.7          # Token 计数 (T-REF-25)
numpy>=1.26            # 百分位 (可选)
```

---

## 相关引用

- PRD § 5.4 Skill Hub (`docs/prd/04-cross-cutting.md`)
- PRD § 5.6 当事人服务类文书 (`docs/prd/04-cross-cutting.md`)
- PRD § 16.5 T-REF-17/18/22/25 (`docs/prd/16-ai-agent-references.md`)
- Track E (`docs/prd/tracks/E-skills.md`)
- agentskills.io 标准: https://agentskills.io
- Skill 1 类案检索 (`skills/caselaw/`) — 启动包模板 (commit 568d817)

---

> **最后更新**: 2026-06-29 · lex-ai