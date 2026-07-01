<!-- Auto-split from PRD.md v0.7.0 on 2026-06-28 -->
> 本文档为 LexPrime 全面 PRD 的分章节版本, 供各 agent 独立阅读
> 主文档: `PRD.md` · 完整 15 章节 42KB · 各章节交叉引用见 `00-index.md`

# LexPrime PRD 导航 (Index)
> 全面 PRD V5.0 已按章节拆分, 每份独立可读
> **主文档**: `../../PRD.md` (42KB / 859 行 / 15 章节 完整版)

---

## 章节总览

| # | 文档 | 内容 | 来源章节 | 行数估算 |
|---|---|---|---|---|
| 01 | [`01-product-positioning.md`](./01-product-positioning.md) | 产品定位与市场背景 | §0, 1, 2 | ~50-200 |
| 02 | [`02-target-users.md`](./02-target-users.md) | 目标用户 | §3 | ~50-200 |
| 03 | [`03-core-steps.md`](./03-core-steps.md) | 核心场景: 5 大核心步骤 + 1 立案预审 | §4 | ~50-200 |
| 04 | [`04-cross-cutting.md`](./04-cross-cutting.md) | 横切面模块: 9 大模块 | §5 | ~50-200 |
| 05 | [`05-knowledge-base.md`](./05-knowledge-base.md) | 个人知识库 (LexPrime 核心差异化) | §6 | ~50-200 |
| 06 | [`06-architecture.md`](./06-architecture.md) | 技术架构 | §7 | ~50-200 |
| 07 | [`07-data-security.md`](./07-data-security.md) | 数据安全策略 (本地优先) | §8 | ~50-200 |
| 08 | [`08-roadmap.md`](./08-roadmap.md) | 产品路线 | §9 | ~50-200 |
| 09 | [`09-business-model.md`](./09-business-model.md) | 商业模式 | §10 | ~50-200 |
| 10 | [`10-success-metrics.md`](./10-success-metrics.md) | 成功指标 | §11 | ~50-200 |
| 11 | [`11-risks-compliance.md`](./11-risks-compliance.md) | 风险与合规 + 法律免责声明 | §12, 13 | ~50-200 |
| 12 | [`12-team.md`](./12-team.md) | 团队 | §14 | ~50-200 |
| 13 | [`13-appendix.md`](./13-appendix.md) | 附录 (版本/决策/相关文档/核心机制) | §15 | ~50-200 |
| 14 | [`14-references-from-products.md`](./14-references-from-products.md) | 附录: 借鉴 6 个 AI Agent 产品 (Claude Code / MiniMax Code / Kimi Code / AutoClaw / Codex / WorkBuddy / TRAE Work) | 2026-06-28 新增 | ~250 |
| 15 | [`15-tasks-from-references.md`](./15-tasks-from-references.md) | 附录: 借鉴实施任务拆分 (T-REF-01~14, P0/P1/P2 分级, 跨 5 agent 协作) | 2026-06-28 新增 | ~250 |
| 16 | [`16-ai-agent-references.md`](./16-ai-agent-references.md) | **附录: AI Agent 借鉴与实施 (8 产品真实架构 + T-REF-15~25)** | 2026-06-28 新增 | ~350 |
| 17 | [`17-team-roadmap.md`](./17-team-roadmap.md) | **附录: 团队路线图 (Phase 4 P0 排序 + Phase 5 招 3 agent JD)** | 2026-06-28 新增 | ~400 |

## 按 Track 拆分 (开发任务)

Phase 4 任务分派按 Track 拆, 详见 [`./tracks/README.md`](./tracks/README.md)

| Track | 模块 | 负责人 | 优先级 | 文档 |
|---|---|---|---|---|
| A | A-auth | 全栈 / 创始人 | P0-P1 | [`./tracks/A-auth.md`](./tracks/A-auth.md) |
| B | B-ocr | 全栈 / 创始人 | P0-P1 | [`./tracks/B-ocr.md`](./tracks/B-ocr.md) |
| C | C-lawyer-interview | 全栈 / 创始人 | P0-P1 | [`./tracks/C-lawyer-interview.md`](./tracks/C-lawyer-interview.md) |
| D | D-trial-version | 全栈 / 创始人 | P0-P1 | [`./tracks/D-trial-version.md`](./tracks/D-trial-version.md) |
| E | E-skills | 全栈 / 创始人 | P0-P1 | [`./tracks/E-skills.md`](./tracks/E-skills.md) |
| F | F-filing-review | 全栈 / 创始人 | P0-P1 | [`./tracks/F-filing-review.md`](./tracks/F-filing-review.md) |
| G | G-trial-prep | 全栈 / 创始人 | P0-P1 | [`./tracks/G-trial-prep.md`](./tracks/G-trial-prep.md) |
| H | H-doc-enhance | 全栈 / 创始人 | P0-P1 | [`./tracks/H-doc-enhance.md`](./tracks/H-doc-enhance.md) |
| I | I-regulation-monitor | 全栈 / 创始人 | P0-P1 | [`./tracks/I-regulation-monitor.md`](./tracks/I-regulation-monitor.md) |
| J | J-knowledge-base | 全栈 / 创始人 | P0-P1 | [`./tracks/J-knowledge-base.md`](./tracks/J-knowledge-base.md) |

## 怎么用这套文档

1. **战略 / 市场 / 投资人** → `01-product-positioning.md` + `02-target-users.md` + `09-business-model.md`
2. **产品经理 / 律师顾问** → `02-target-users.md` + `03-core-steps.md` + `04-cross-cutting.md` + `08-roadmap.md` + `16-ai-agent-references.md` + `17-team-roadmap.md` (Phase 4 P0 排序 + Phase 5 招聘 JD)
3. **全栈工程师** → `06-architecture.md` + `07-data-security.md` + `tracks/*.md` + `16-ai-agent-references.md` (T-REF-16/21) + `17-team-roadmap.md` § 17.1.2 Phase 4 lex-coder P0 排序
4. **UI 设计师** → `02-target-users.md` + `03-core-steps.md` + `04-cross-cutting.md` + `16-ai-agent-references.md` (T-REF-04/09/24)
5. **AI / RAG 工程师** → `05-knowledge-base.md` + `04-cross-cutting.md` § 5.4-5.7 + `06-architecture.md` + `16-ai-agent-references.md` (T-REF-17~20/22/25)
6. **数据工程师** → `06-architecture.md` § 7.7 + `04-cross-cutting.md` § 5.7 + `16-ai-agent-references.md` (T-REF-22)
9. **HR / 招聘** (Phase 5+) → `17-team-roadmap.md` § 17.2 Phase 5 招聘 3 agent JD (lex-security / lex-electron / lex-mobile)
7. **BD / 运营** → `02-target-users.md` + `09-business-model.md` § 10.3 推广策略 + `10-success-metrics.md`
8. **测试 / QA** → `11-risks-compliance.md` § 12.2 合规风险 + `04-cross-cutting.md` § 5.7 类案界面语言规范


---

**相关章节**:
- 主文档: `../../PRD.md`
- 导航: `./00-index.md`
- 路线: `./08-roadmap.md` · 商业: `./09-business-model.md` · 风险: `./11-risks-compliance.md`
- Track 任务: `./tracks/README.md`
