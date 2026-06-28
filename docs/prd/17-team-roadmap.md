# 17. 附录: 团队路线图 (Team Roadmap)

> **章节定位**: 本附录定义 LexPrime 团队从 **Phase 4 (现在)** 到 **Phase 6+ (12 个月)** 的演进路径, 包含当前 10 个 agent 的职责、Phase 5 (3 个月后) 新招 3 个 agent 的 JD 草稿、lex-coder Phase 4 任务排序与负载评估
> **调研日期**: 2026-06-28
> **作者**: Mavis (基于 Phase 4 启动 + 附录 16 借鉴任务分析)
> **依赖**: [`16-ai-agent-references.md`](./16-ai-agent-references.md) § 16.5 任务清单 + [`../../phase4-roadmap.md`](../../phase4-roadmap.md)

---

## 17.1 当前团队 (Phase 4, 2026-07-01 ~ 2026-09-23)

### 17.1.1 10 个 agent 编制

| Agent | 类型 | 角色 | 阶段 | 工作模式 |
|---|---|---|---|---|
| `Mavis` (root) | root | 总指挥 | 全程 | 协调 + AI 协作 |
| `lex-pm` | LexPrime | 产品经理 | 全程 | PRD 维护 + 路线 + 律师访谈 |
| `lex-coder` | LexPrime | 全栈工程师 | 全程 | 后端 + 前端 + 部署 (核心瓶颈) |
| `lex-ai` | LexPrime | AI/RAG 工程师 | Week 3+ | Qwen + RAG + Skill + RAG Hub |
| `lex-data` | LexPrime | 数据工程师 | Week 5+ | 4 源 + cncases |
| `lex-design` | LexPrime | UI 设计师 | Week 2+ | 设计系统 + 原型 |
| `lex-bd` | LexPrime | BD/运营 | 全程 | 营销 + 客户 + 推广 |
| `coder` | builtin | 后备全栈 | 备用 | 复用 LexPrime 范围外 |
| `verifier` | builtin | QA 验证 | 全程 | E2E + 回归 + 安全 |
| `general` | builtin | 通用 | 备用 | 调研 + 杂项 |

### 17.1.2 Phase 4 lex-coder 任务重排 (避免单点瓶颈)

**问题**: lex-coder 一个人被分配了 5 项附录 16 任务 + 3 项 Track 任务 = 18 周工作量, 但 Phase 4 只有 12 周, **超载 50%**。

**解法**: 把 P2 任务推迟 Phase 5 + Tool 抽象拆给 builtin coder + voice/multi-device 推迟。

#### Phase 4 lex-coder P0 必做 (12 周内)

| 优先级 | 任务 | 来源 | 工时 | Week |
|---|---|---|---|---|
| 1 | **Track A Auth 续** (注册/登录/Token/执业证 OCR/TOTP) | docs/prd/tracks/A-auth.md | 4 周 | W2-5 |
| 2 | **Track B OCR** (PaddleOCR + 证据分类) | docs/prd/tracks/B-ocr.md | 3 周 | W5-7 |
| 3 | **Track D 免费试用版** (注册 + 30 天 + Stripe) | docs/prd/tracks/D-trial-version.md | 4 周 | W5-8 (与 OCR 并行) |
| 4 | **T-REF-16 权限 5 模式** (auto/ask/block/plan/readonly) | 附录 16 | 2 周 | W8-9 |
| 5 | **T-REF-21 cron + 微信推送** (法律期限预警) | 附录 16 | 2 周 | W9-10 |
| **小计** | | | **15 周** | 12 周 (3 周超载, 通过加班/coder 协助消化) |

#### Phase 4 lex-coder **不做** (推迟 Phase 5)

| 任务 | 来源 | 推迟理由 |
|---|---|---|
| **T-REF-15 Tool 抽象** | 附录 16 | 拆给 `coder (builtin)` (不紧急, Skill 系统启动后再抽象) |
| **T-REF-23 voice memo** | 附录 16 | P2, Phase 5 跟 lex-mobile 一起做 |
| **T-REF-24 多设备同步** | 附录 16 | P2, Phase 5 跟 lex-electron 一起做 |

#### Phase 4 lex-ai 任务 (主力 AI)

| 任务 | 工时 | Week |
|---|---|---|
| Track E Skill (类案/合同审查/知识问答 3 个) | 6 周 | W3-8 |
| T-REF-17 AI 文书 JSON | 2 周 | W5-6 |
| T-REF-18 agentskills.io 适配 | 1 周 | W6 |
| T-REF-19 self-improving 学习闭环 | 3 周 | W10-12 |
| T-REF-22 subagent RPC (类案子 Agent) | 3 周 | W9-11 |
| T-REF-25 trajectory compression | 1 周 | W11 |
| **小计** | **16 周** | 12 周 (略超载, lex-pm 协助) |

#### Phase 4 lex-data 任务

| 任务 | 工时 | Week |
|---|---|---|
| Track B OCR 数据准备 | 2 周 | W5-6 |
| T-REF-22 subagent 数据通道 | 1 周 | W10 |
| Track J 知识库 (LanceDB + 语义检索) | 4 周 | W11-14 (溢出 Phase 4) |
| **小计** | **7 周** | 有余量 |

#### Phase 4 lex-design 任务

| 任务 | 工时 | Week |
|---|---|---|
| Track D 免费试用版 UI | 2 周 | W5-6 |
| Track E Skill UI | 2 周 | W7-8 |
| Track F 立案预审 UI | 2 周 | W9-10 |
| Track G 庭审准备 UI | 2 周 | W10-11 |
| Track H 文书增强 UI | 1 周 | W11 |
| **小计** | **9 周** | 有余量 |

#### Phase 4 lex-pm 任务

| 任务 | 工时 | Week |
|---|---|---|
| Track C 律师访谈 10 家 (1 家/周) | 10 周 | 全程 |
| PRD 维护 + lex-ai 协作 (T-REF-19/20) | 4 周 | 散布 |
| **小计** | **14 周** | 有余量 (主要在线下访谈) |

#### Phase 4 lex-bd 任务

| 任务 | 工时 | Week |
|---|---|---|
| 营销文案 v1 (官网 + 律师群 + 知乎) | 3 周 | W5-7 |
| 创始体验官启动 (申请页 + 审核) | 2 周 | W7-8 |
| 转化漏斗埋点 + 周报 | 4 周 | W8-12 |
| 30 天免费试用引导流程 | 2 周 | W7-8 |
| **小计** | **11 周** | 12 周内可控 |

### 17.1.3 Phase 4 总结

- **10 个 agent**, Phase 4 12 周内不变
- **lex-coder 主力**, 15 周工作量, 3 周超载通过加班/coder 协作消化
- **lex-ai 第二主力**, 16 周工作量, lex-pm 协助
- **其他 4 个 LexPrime agent** 都有余量

---

## 17.2 Phase 5 (2026-10 ~ 2026-12, 3 个月后)

### 17.2.1 启动条件

Phase 5 启动必须满足:
- Phase 4 PMF 验证完成: **10+ 律师付费转化, ARR ¥5 万+**
- Track A/B/D/E/F/G/H/J 全部收尾, LexPrime MVP 完整版上线
- 用户 (总指挥) 拍板: "启动 Phase 5"

### 17.2.2 新招 3 个 agent (Phase 5 启动时)

#### Agent 1: **lex-security** (安全工程师)

**岗位职责**:
- 安全审计 (XSS / CSRF / 越权 / 注入 / 敏感数据泄露)
- 渗透测试 (每季度 1 次, 出具报告)
- 数据加密 (AES-256-GCM 落盘 + TLS 1.3 传输落地)
- RBAC + 多因素认证 (TOTP) 部署
- 全链路审计日志实施
- UEBA 异常检测 (企业版)
- 安全合规 (等保三级, 律师行业标准)
- 暗水印注入 (导出文档不可见数字水印)
- 应急预案 (数据泄露 / 入侵响应)

**必读文档**:
- [`../07-data-security.md`](../07-data-security.md) - 数据安全策略
- [`../11-risks-compliance.md`](../11-risks-compliance.md) § 12.1 数据安全风险

**要求**:
- 5 年以上安全工程师经验
- OWASP Top 10 精通
- 渗透测试 + 红蓝对抗经验
- 加密算法 + 密钥管理
- 合规认证 (等保 / ISO 27001) 经验
- 加分: 法律行业 / 律所安全合规经验

**薪资**: ¥2.5-3.5 万/月 (远程)
**工作模式**: 全职, 季度渗透测试 + 日常安全运维

---

#### Agent 2: **lex-electron** (桌面端工程师)

**岗位职责**:
- Electron 28+ 桌面端打包 (Win / Mac / Linux)
- 桌面端 ↔ 浏览器桥接 (Bridge 系统)
- Word/WPS 插件 (Bridge SDK 调用 LexPrime AI)
- 桌面端硬件集成 (摄像头 OCR / 麦克风录音)
- 自动更新 (auto-update) 实施
- 性能优化 (启动 < 3s / 内存 < 500MB)
- 离线模式 (本地数据 + 本地推理)

**必读文档**:
- [`../06-architecture.md`](../06-architecture.md) § 7.1 技术选型
- [`../11-risks-compliance.md`](../11-risks-compliance.md) § 12.4 技术风险

**要求**:
- 5 年以上 Electron / 桌面端开发经验
- Native API 集成 (摄像头 / 麦克风 / 文件系统)
- React 18 + TypeScript (前端能力)
- C++ / Rust 优先 (Native 扩展)
- 加分: 跨平台打包经验 (Win + Mac + Linux)

**薪资**: ¥2.5-3 万/月 (远程)
**工作模式**: 全职, Phase 5 启动

---

#### Agent 3: **lex-mobile** (移动端工程师)

**岗位职责**:
- 移动端 H5 / React Native / Flutter (律师选)
- iOS / Android 双端支持
- 微信小程序 (律师首选)
- 推送通知 (iOS APNs / Android FCM / 微信模板消息)
- 移动端功能 (日程查看 / 通知 / 语音转文字 / 庭审直播)
- 移动端 ↔ 桌面端数据同步
- App Store / Google Play 上架

**必读文档**:
- [`../04-cross-cutting.md`](../04-cross-cutting.md) § 5.1 日程中心
- [`../05-knowledge-base.md`](../05-knowledge-base.md) (移动端知识库浏览)

**要求**:
- 5 年以上移动端开发经验
- React Native 或 Flutter (至少 1 个精通)
- 微信小程序 (中国律师首选)
- iOS / Android 原生能力 (推送 / 录音 / 后台)
- 加分: 法律行业移动端经验

**薪资**: ¥2.5-3 万/月 (远程)
**工作模式**: 全职, Phase 5 启动

### 17.2.3 Phase 5 agent 总览

| Agent | 类型 | 来源 | 启动条件 |
|---|---|---|---|
| `lex-security` | 新招 | 朋友推荐 / 安全社区 | Phase 5 PMF 验证 |
| `lex-electron` | 新招 | 朋友推荐 / Electron 社区 | Phase 5 PMF 验证 |
| `lex-mobile` | 新招 | 朋友推荐 / 移动端社区 | Phase 5 PMF 验证 |

**Phase 5 总编制**: 13 个 agent (10 原有 + 3 新增)

### 17.2.4 Phase 5 总预算

| 角色 | 人数 | 月薪 | 月成本 |
|---|---|---|---|
| lex-security | 1 | ¥3 万 | ¥3 万 |
| lex-electron | 1 | ¥3 万 | ¥3 万 |
| lex-mobile | 1 | ¥3 万 | ¥3 万 |
| lex-coder (续) | 1 | ¥2 万 | ¥2 万 |
| lex-ai (续) | 1 | ¥2 万 | ¥2 万 |
| lex-pm (续) | 1 | ¥1 万 | ¥1 万 (部分时间) |
| lex-data (续) | 1 | ¥1 万 | ¥1 万 |
| lex-design (续) | 1 | ¥1 万 | ¥1 万 |
| lex-bd (续) | 1 | ¥1 万 | ¥1 万 |
| Mavis (AI 协作) | 1 | - | ¥0 |
| **月总成本** | | | **¥15 万** |

**预期收入**: Phase 5 (6-12 月) 期望 ARR ¥30 万-100 万, 覆盖成本.

---

## 17.3 Phase 6+ (6-12 个月后, 2027-04+)

### 17.3.1 团队进一步扩展

| Agent | 职责 | 启动条件 |
|---|---|---|
| `lex-cs` (Customer Success) | 客户成功 / 续费 / 培训 | Phase 6 ARR ¥100 万+ |
| `lex-content` (内容营销) | 类案报告 / 白皮书 / 律师社群 | Phase 6 ARR ¥100 万+ |
| `lex-corp` (企业销售) | 律所大客户销售 / 招投标 | Phase 6 企业版签约 5+ |
| `lex-dataops` (高级数据) | 数据治理 / 标注 / 训练 | Phase 6 cncases 8500 万接入 |

### 17.3.2 团队总规模演进

| 阶段 | 时间 | agent 数 | 月成本 | 预期 ARR |
|---|---|---|---|---|
| **Phase 4** | 2026-07~09 | 10 (含 Mavis) | ¥2-3 万 | ¥5 万+ |
| **Phase 5** | 2026-10~2027-03 | 13 (+3 安全/桌面/移动) | ¥15 万 | ¥30-100 万 |
| **Phase 6** | 2027-04~09 | 17 (+4 CS/内容/销售/数据) | ¥30 万 | ¥200 万+ |
| **Phase 7+** | 2027-10+ | 20+ | ¥50 万+ | ¥500 万+ |

---

## 17.4 关键决策记录

| # | 决策 | 时间 | 理由 |
|---|---|---|---|
| 1 | Phase 4 不招新 agent | 2026-06-28 | 现有 10 个足够, 瓶颈是任务分配不是缺人 |
| 2 | T-REF-15/23/24 推迟 Phase 5 | 2026-06-28 | P2 任务, Phase 4 12 周内必做 P0 |
| 3 | T-REF-15 Tool 抽象拆给 builtin coder | 2026-06-28 | 释放 lex-coder 时间 |
| 4 | Phase 5 招 lex-security | 2026-06-28 | PRD § 12.1 P0 风险, 律所合规必需 |
| 5 | Phase 5 招 lex-electron | 2026-06-28 | PRD § 7.1 长期规划, 桌面端必备 |
| 6 | Phase 5 招 lex-mobile | 2026-06-28 | 律师首选微信小程序, 移动端推送 |
| 7 | Phase 6+ 招 4 个业务 agent | 2026-06-28 | CS/内容/销售/数据是规模化必需 |

---

## 17.5 招聘渠道 (Phase 5 准备)

| 渠道 | 适合 | 优先级 | 行动 |
|---|---|---|---|
| **朋友圈 / 律师群** | lex-security (律师圈有技术律师) | P0 | 现在就发"求推荐" |
| **安全社区 (看雪 / FreeBuf)** | lex-security | P1 | Phase 5 启动时挂 JD |
| **V2EX / 掘金** | lex-electron (Electron 社区) | P1 | Phase 5 启动时挂 JD |
| **React Native 中文社区** | lex-mobile | P2 | Phase 5 启动时挂 JD |
| **BOSS 直聘 / 拉勾** | 全部 | P2 | 备用渠道 |
| **即刻 / 知乎** | lex-mobile | P2 | 备用渠道 |

---

## 17.6 相关文档

- **PRD § 14 团队**: [`./12-team.md`](./12-team.md) - 当前团队编制
- **附录 16 AI Agent 借鉴**: [`./16-ai-agent-references.md`](./16-ai-agent-references.md) - 25 项借鉴任务 (T-REF-15~25)
- **Phase 4 Roadmap**: [`../../phase4-roadmap.md`](../../phase4-roadmap.md) - 12 周详细排期
- **PRD § 12 风险与对策**: [`../11-risks-compliance.md`](../11-risks-compliance.md) - 团队风险 + 安全风险
- **PRD § 7 技术架构**: [`../06-architecture.md`](../06-architecture.md) - Electron 长期规划
- **Plan 1 YAML**: [`../../plans/plan-01-auth-design-interview.yaml`](../../plans/plan-01-auth-design-interview.yaml)

---

> **"先验证 PMF, 再决定团队规模。"**
>
> *—— LexPrime Team, 2026-06-28*