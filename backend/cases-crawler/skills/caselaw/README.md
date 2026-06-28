# Skill 1: 类案检索与裁判参考

> **Status**: W5 草稿 (W2-3 数据 + W4-5 manifest/schema/prompt + W5-6 retrieval 算法 完成; W7 UI + W8 律师评审 待启动)
> **Owner**: lex-ai · **Reviewer**: lex-pm + 律师顾问 (≥ 3 人)
> **Track**: E-skills · **PRD**: § 5.4 Skill Hub + § 5.7 类案大数据

---

## 目录结构

```
skills/caselaw/
├── manifest.json                  # agentskills.io 标准清单
├── prompt.md                       # LLM system prompt (角色 + 工作流 + 错误处理)
├── language_policy.md              # 界面语言规范 (PRD § 5.7 硬约束)
├── disclaimer.md                   # 强制免责声明
├── language_guard.py               # 禁用词检测 + 自动纠正 + 降级模板
├── retrieval.py                    # 检索算法 + 上下文压缩 + 统计生成 + UI 提示
├── README.md                       # 本文件
├── docs/
│   └── UI_HANDOFF.md               # 给 lex-design 的 UI 对接文档
├── schemas/
│   ├── input.json                  # JSON Schema 输入契约
│   ├── input.example.json
│   ├── output.json                 # JSON Schema 输出契约
│   └── output.example.json
└── tests/                          # 律师评审 + 自动化测试
    └── (后续 W8 律师评审报告入此目录)
```

---

## 快速开始 (本地开发)

```bash
cd backend/cases-crawler

# 1) 数据扩量 (cases 1200, laws 6500)
python scripts/scale_data.py --cases 1200 --laws 6500

# 2) 自检 language_guard
python skills/caselaw/language_guard.py

# 3) 自检 retrieval 算法 (mock store)
python -m skills.caselaw.retrieval

# 4) 运行单元测试
python tests/test_caselaw_skill.py
```

---

## 数据状态 (2026-06-29)

| 表 | 当前 | 目标 | 状态 |
|---|---|---|---|
| cases | 1200 | ≥ 1000 | ✅ PASS |
| laws | 6500 | ≥ 6000 | ✅ PASS |
| companies | 8 | (后续 Phase) | - |
| lawyer_added_cases | 0 | (W4+) | - |

---

## 单元测试状态

`tests/test_caselaw_skill.py` — **13/13 PASSED**

| # | 测试 | 验证点 |
|---|---|---|
| 1 | test_language_guard_pass | 5 条正确表述全 PASS |
| 2 | test_language_guard_fail_high | 8 条违规表述全拦截 |
| 3 | test_language_guard_correction | 违规表述自动纠正 |
| 4 | test_templates_pass | 4 个降级模板全合规 |
| 5 | test_compress_context_no_compression_needed | 5 件小样本不触发压缩 |
| 6 | test_compress_context_truncate | 56850 token 自动压到 820 |
| 7 | test_compute_statistics_basic | 50 件样本统计 + narrative 合规 |
| 8 | test_compute_statistics_judge_style | 8 件样本法官风格正确 |
| 9 | test_compute_statistics_judge_insufficient | 样本 < 5 标记"样本不足" |
| 10 | test_traffic_light | 4 种 traffic_light 颜色正确 |
| 11 | test_run_skill_e2e | 端到端 run_skill 输出合规 |
| 12 | test_count_tokens | tiktoken + fallback |
| 13 | test_percentile_python | numpy 不可用时纯 Python 百分位 |

---

## 关键指标对照 PRD

| 指标 | 目标 | 当前 |
|---|---|---|
| Skill 加载时间 | < 3s | 待 W7 实测 |
| 检索 P95 延迟 | < 1s | 待 W7 实测 (mock 0ms) |
| 律师评审准确率 | ≥ 80% | 待 W8 评审 |
| 界面语言违规率 | 0 / 1000 次 | test 验证 0 / 13 |
| 数据规模 | 1000 cases + 6000 laws | ✅ 1200 + 6500 |

---

## 依赖 (待加入 requirements.txt)

```
lancedb>=0.6           # 本地向量库
sentence-transformers>=2.7  # BGE 中文 embedding
tiktoken>=0.7          # Token 计数 (T-REF-25)
numpy>=1.26            # 百分位 (可选, 无 numpy 走纯 Python)
```

---

## 路线图

- [x] W2-3: 数据扩量 (1200 cases + 6500 laws)
- [x] W4: manifest + input/output schema (agentskills.io 标准)
- [x] W4-5: prompt + language_policy + disclaimer
- [x] W5-6: retrieval 算法 (metadata filter + 向量召回 + 上下文压缩 + 统计 + UI 提示)
- [x] W6: language_guard + 13 项单元测试
- [x] W7: UI hand-off doc (待 lex-design 实现)
- [ ] W7: 真实 LanceDB 接入 (T-REF-22 subagent RPC)
- [ ] W7: 性能压测 (P95 < 1s 验证)
- [ ] W8: 律师顾问评审 (≥ 3 人, 准确率 ≥ 80%)
- [ ] W8: 律师评审报告入 `tests/lawyer_review_*.md`

---

## 相关引用

- PRD § 5.4 Skill Hub (`docs/prd/04-cross-cutting.md`)
- PRD § 5.7 类案大数据 (`docs/prd/04-cross-cutting.md`)
- PRD § 16.5 T-REF-17/18/22/25 (`docs/prd/16-ai-agent-references.md`)
- Track E (`docs/prd/tracks/E-skills.md`)
- agentskills.io 标准: https://agentskills.io

---

> **最后更新**: 2026-06-29 · lex-ai