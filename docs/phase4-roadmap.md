# LexPrime Phase 4 全面开发 Roadmap (12 周)

> **目标**: 跑通 PMF 验证 + 30 天免费试用 + 首批付费律师, ARR ¥5 万+
> **时间**: 2026-07-01 ~ 2026-09-23 (12 周, 3 个月)
> **团队**: 6 个 LexPrime agents + builtin coder/verifier/general
> **来源**: `docs/prd/08-roadmap.md` § 9.2 Phase 4 计划 + `docs/prd/tracks/README.md`

---

## 团队编制 (10 agents)

| Agent | 角色 | 阶段 | 工作模式 |
|---|---|---|---|
| `lex-pm` | 产品经理 | 全程 | PRD 维护 + 路线 + 律师访谈 |
| `lex-coder` | 全栈工程师 | 全程 | 后端 + 前端 + 部署 |
| `lex-ai` | AI/RAG 工程师 | Week 3+ | Qwen + RAG + Skill |
| `lex-data` | 数据工程师 | Week 5+ | 4 源 + cncases |
| `lex-design` | UI 设计师 | Week 2+ | 设计系统 + 原型 |
| `lex-bd` | BD/运营 | 全程 | 营销 + 客户 + 推广 |
| `coder` (builtin) | 后备全栈 | 备用 | 复用 LexPrime 范围外工作 |
| `verifier` (builtin) | QA 验证 | 全程 | E2E + 回归 + 安全 |
| `general` (builtin) | 通用 | 备用 | 调研 + 杂项 |
| `Mavis` (root) | 总指挥 | 全程 | 协调 + AI 协作 |

---

## 12 周 Roadmap (3 个里程碑)

### 🚀 Month 1 (Week 1-4): 基础设施 + 启动

| Week | Track | 负责人 | 关键交付 |
|---|---|---|---|
| **W1** | **A: Auth** (启动) | lex-coder | 项目脚手架 + DB schema + JWT 框架 |
| | **C: 律师访谈 1** | lex-pm | 访谈大纲 + 目标律所名单 + 1 家访谈 |
| | **设计系统 v1** | lex-design | 品牌色 / 字体 / 组件库 |
| **W2** | **A: Auth** (续) | lex-coder | 注册 / 登录 / Token 刷新 |
| | **C: 律师访谈 2** | lex-pm | 第 2 家访谈 + 痛点初稿 |
| | **E: Skill 类案 (启动)** | lex-ai | 类案数据准备 + Skill 1 草稿 |
| **W3** | **A: Auth** (收尾) | lex-coder | 律师执业证 OCR + TOTP + 审计日志 |
| | **C: 律师访谈 3** | lex-pm | 第 3 家访谈 |
| | **E: Skill 类案** (续) | lex-ai | Skill 1 UI + 检索算法 |
| **W4** | **Auth E2E** | verifier | Auth 全链路测试 + 0 严重漏洞 |
| | **C: 律师访谈 4** | lex-pm | 第 4 家访谈 + 中期复盘 |
| | **B: OCR** (启动) | lex-coder | PaddleOCR 部署 + 基础接入 |
| | **D: 免费试用版** (启动) | lex-coder | 注册流程 + 试用期 schema |

**W4 里程碑**: Auth 可用 + 4 律师访谈完成 + Skill 类案 70%

---

### 💎 Month 2 (Week 5-8): 核心功能 + 试用版

| Week | Track | 负责人 | 关键交付 |
|---|---|---|---|
| **W5** | **B: OCR** (续) | lex-coder | 证据分类模型 + 自动目录 |
| | **D: 免费试用版** (续) | lex-coder | 试用到期提醒 + 付费引导 |
| | **C: 律师访谈 5-6** | lex-pm | 持续访谈 |
| | **E: Skill 合同审查** (启动) | lex-ai | Skill 2 prompt + UI |
| | **BD: 营销文案 v1** | lex-bd | 官网落地页 + 律师群帖子 |
| **W6** | **B: OCR** (收尾) | lex-coder | 失败重试 + 人工标注 |
| | **D: 免费试用版** (续) | lex-coder | Stripe 接入 + webhook |
| | **C: 律师访谈 7** | lex-pm | 持续访谈 |
| | **E: Skill 合同审查** (续) | lex-ai | Skill 2 完成 + 律师评审 |
| **W7** | **D: 免费试用版** (收尾) | lex-coder | 发票 + 订单 + 转化埋点 |
| | **E: Skill 知识问答** (启动) | lex-ai | Skill 3 + RAG 接入 |
| | **C: 律师访谈 8** | lex-pm | 持续访谈 |
| | **QA 全量回归** | verifier | 30 分钟全量回归 |
| **W8** | **免费试用版上线** | lex-coder | 律师可注册 + 30 天免费 |
| | **Skill 3 完成** | lex-ai | 3 个 Skill 全部可用 |
| | **C: 律师访谈 9** | lex-pm | 持续访谈 |
| | **BD: 创始体验官启动** | lex-bd | 申请页 + 审核 + 邀请 |

**W8 里程碑**: 免费试用版上线 + 9 律师访谈 + 3 个 Skill 发布

---

### 🎯 Month 3 (Week 9-12): 增强功能 + 闭环

| Week | Track | 负责人 | 关键交付 |
|---|---|---|---|
| **W9** | **F: 立案预审** (启动) | lex-coder | 标准库 + 完整性检查 + 格式校验 |
| | **G: 庭审准备** (启动) | lex-coder + lex-ai | 质证提纲 + 发问提纲 |
| | **C: 律师访谈 10** | lex-pm | 10 家访谈完成 + 报告 |
| | **J: 知识库** (启动) | lex-ai | LanceDB 部署 + 存储 schema |
| **W10** | **F: 立案预审** (续) | lex-coder | 预审报告 UI + 红黄绿灯 |
| | **G: 庭审准备** (续) | lex-coder + lex-ai | 代理词 + 庭审剧本优化 |
| | **H: 文书增强** (启动) | lex-coder | 校对引擎 (错别字 + 法律术语) |
| | **J: 知识库** (续) | lex-ai | 语义检索 + 知识沉淀 UI |
| **W11** | **F: 立案预审** (收尾) | lex-coder | 一键补全 + 律师反馈通道 |
| | **G: 庭审准备** (收尾) | lex-coder + lex-ai | 律师顾问评审通过 |
| | **H: 文书增强** (续) | lex-coder | 排版模板 (10+ 法院) |
| | **I: 法规监控** (启动) | lex-coder | 法规订阅 + 推送通道 |
| **W12** | **Phase 4 收尾** | 全员 | 全功能回归 + 收尾报告 |
| | **H: 文书增强** (收尾) | lex-coder | 一键排版套用 |
| | **I: 法规监控** (续) | lex-coder | 影响分析 + 政策周报 |
| | **J: 知识库** (续) | lex-ai | 跨案件关联 + 导出/删除 |
| | **BD: 转化漏斗周报** | lex-bd | 注册/试用/付费 数据 |

**W12 里程碑**: Phase 4 收尾, 10+ 律师付费转化, ARR ¥5 万+

---

## 12 个 Plan (mavis team plan run)

每个 Plan 是一周的工作单元, 启动时由 Mavis 路由到对应 agent.

| Plan # | 启动时间 | Track | 负责 agent | 验证 |
|---|---|---|---|---|
| **Plan 01** | W1 | A: Auth 启动 + 设计系统 v1 | lex-coder + lex-design | verifier |
| **Plan 02** | W2 | A: Auth 续 + 律师访谈 #2 | lex-coder + lex-pm | verifier |
| **Plan 03** | W3 | A: Auth 收尾 + Skill 类案 | lex-coder + lex-ai | verifier |
| **Plan 04** | W4 | Auth E2E + OCR 启动 + 免费试用启动 | verifier + lex-coder | verify-as-task |
| **Plan 05** | W5 | OCR 续 + 免费试用续 + Skill 合同审查 | lex-coder + lex-ai + lex-bd | verifier |
| **Plan 06** | W6 | OCR 收尾 + Skill 合同审查完成 | lex-coder + lex-ai | verifier |
| **Plan 07** | W7 | 免费试用收尾 + Skill 知识问答 | lex-coder + lex-ai | verifier |
| **Plan 08** | W8 | 免费试用上线 + Skill 全部完成 | lex-coder + lex-ai + lex-bd | verify-as-task |
| **Plan 09** | W9 | 立案预审启动 + 庭审启动 + 知识库启动 | lex-coder + lex-ai | verifier |
| **Plan 10** | W10 | 立案预审续 + 庭审续 + 文书增强 | lex-coder | verifier |
| **Plan 11** | W11 | 立案预审收尾 + 庭审收尾 + 法规监控 | lex-coder | verifier |
| **Plan 12** | W12 | Phase 4 收尾 + 全功能回归 | 全员 | verify-as-task |

---

## 启动规则 (用户拍)

每个 Plan 启动前, 用户 (总指挥) 拍板:
- **Plan 01**: 启动 A 启动 + 设计系统 v1 (建议立即启动)
- 后续 Plan: 每周五晚启动下一周 Plan, 周报评审通过

---

## 风险与缓冲

| 风险 | 缓冲方案 |
|---|---|
| 全栈工程师 1 人不够 (并行 4 个 Track) | UI 设计师 + AI 工程师 + 数据工程师 分担; 我 (Mavis) 协助 |
| 律师访谈时间难约 | 提前 2 周约 + 灵活时间; 备份名单 20 家 |
| Stripe 国内访问 | 备用: 微信支付 / 支付宝 (Phase 4.5) |
| cncases 102GB 下载慢 | 备选: 中国裁判文书网爬虫 (慢但稳) |
| 跨 Track 依赖阻塞 | Plan 内 verify-as-task 提前发现, 调整下周 Plan |
| AI 输出不稳 | 律师顾问评审 + 持续微调 |
| 付费转化率低 | 创始体验官 + 5 折首年激励 |

---

## 关键决策 (用户拍)

| # | 决策点 | 我推荐 | 备选 |
|---|---|---|---|
| 1 | **Plan 01 立即启动** | ✅ 是 | 再细化 1 周 |
| 2 | **Plan 节奏** | 1 周 1 个 plan | 2 周 1 个 plan (缓冲) |
| 3 | **OCR 启动时间** | W4 (Track A 完成后) | W1 (并行) |
| 4 | **Skill 启动** | W2 (类案) | W4 (等 Auth) |
| 5 | **律师访谈节奏** | 1 家/周 (10 周 10 家) | 2 家/周 (5 周) |
| 6 | **付费转化目标** | 10 律师 / ¥5 万 ARR | 5 律师 / ¥3 万 ARR |
| 7 | **Phase 4.5 提前启动** | 否 (Phase 5 一起) | 是 (Phase 4 完成 70% 时) |

---

## 必读 PRD 文档

- 主文档: `../../PRD.md` (42KB)
- 导航: `../00-index.md`
- Phase 4 计划: `../08-roadmap.md` § 9.2
- Tracks 任务: `./README.md` + `./A-auth.md` ... `./J-knowledge-base.md`

---

> **"12 周 Phase 4, 把 LexPrime 从 MVP 推向可付费的 PMF 验证产品。"**
>
> *—— LexPrime 团队, 2026-06-28*
