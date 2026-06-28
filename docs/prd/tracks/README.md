<!-- Auto-split from PRD.md v0.7.0 on 2026-06-28 -->
> 本文档为 LexPrime 全面 PRD 的分章节版本, 供各 agent 独立阅读
> 主文档: `PRD.md` · 完整 15 章节 42KB · 各章节交叉引用见 `00-index.md`

# Phase 4 Track 任务分派 (Tracks)
> 来源: PRD § 9.2 Phase 4 计划 · 12 周 10 个 Track 并行推进

---

## Track 总览

| Track | 模块 | 负责人 | 工时 | 优先级 | 依赖 | 文档 |
|---|---|---|---|---|---|---|
| A | Auth 后端 (Rust + JWT) | 全栈 | 4 周 | P0 | - | [`A-auth.md`](./A-auth.md) |
| B | OCR 闭环 (PaddleOCR + 证据分类) | 全栈 + AI | 3 周 | P0 | A | [`B-ocr.md`](./B-ocr.md) |
| C | 律师访谈 10 家 PMF 验证 | 创始人 | 10 周 (1 家/周) | P0 | - | [`C-lawyer-interview.md`](./C-lawyer-interview.md) |
| D | 30 天免费试用版 + Stripe | 全栈 + Mavis | 4 周 | P0 | A | [`D-trial-version.md`](./D-trial-version.md) |
| E | 9 个官方 Skill 首批 3 个 (类案/合同审查/知识问答) | 全栈 + AI + 律师顾问 | 6 周 | P1 | A | [`E-skills.md`](./E-skills.md) |
| F | 立案预审 3.5 步 | 全栈 | 4 周 | P1 | A | [`F-filing-review.md`](./F-filing-review.md) |
| G | 庭审准备 (质证/发问/代理词) | 全栈 + AI | 4 周 | P1 | E | [`G-trial-prep.md`](./G-trial-prep.md) |
| H | 文书智能增强 (校对/排版) | 全栈 | 2 周 | P1 | - | [`H-doc-enhance.md`](./H-doc-enhance.md) |
| I | 法规监控 + 政策周报 | 全栈 | 3 周 | P2 | A | [`I-regulation-monitor.md`](./I-regulation-monitor.md) |
| J | 个人知识库 (LanceDB + 语义检索) | 全栈 + AI | 4 周 | P2 | - | [`J-knowledge-base.md`](./J-knowledge-base.md) |

## 推荐排期 (12 周 Phase 4)

### Month 1 (Week 1-4): 基础设施 + 启动
- Week 1-2: **Track A (Auth)** + **Track C 启动 (访谈 1-2 家)**
- Week 3-4: **Track E 启动 (类案 Skill)** + Track C 持续

### Month 2 (Week 5-8): 核心功能 + 试用版
- Week 5-6: **Track B (OCR)** + **Track D (免费试用版)**
- Week 7-8: Track E 持续 (合同审查 + 知识问答) + Track C 持续

### Month 3 (Week 9-12): 增强功能 + 闭环
- Week 9-10: **Track F (立案预审)** + **Track G (庭审准备)**
- Week 11-12: **Track H (文书增强)** + Track I + Track J 启动

## 关键里程碑

| Week | 里程碑 | 验收标准 |
|---|---|---|
| W2 | Auth 可用 | 律师可注册 / 登录 / 刷新 token |
| W4 | 第一批律师访谈完成 | 至少 3 家律所完成深度访谈, 痛点验证 |
| W6 | OCR 可用 | 律师可扫描证据, 自动分类 + 目录 |
| W8 | 免费试用版上线 | 律师可注册 + 30 天免费使用 |
| W10 | 首批 Skill 发布 | 类案 / 合同审查 / 知识问答 3 个可用 |
| W12 | Phase 4 收尾 | 10 律师付费转化, ARR ¥5 万+ |



---

**相关章节**:
- 主文档: `../../PRD.md`
- 导航: `./00-index.md`
- 路线: `./08-roadmap.md` · 商业: `./09-business-model.md` · 风险: `./11-risks-compliance.md`
- Track 任务: `./tracks/README.md`
