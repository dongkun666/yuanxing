# 15. 附录: 借鉴实施任务拆分 (Tasks from References)

> **章节定位**: 基于 [`14-references-from-products.md`](./14-references-from-products.md) 的借鉴清单, 按 LexPrime 团队分工 (lex-coder/lex-design/lex-ai/lex-data/lex-pm) 拆任务, 供下个 plan 启动时 Mavis 调度参考。
> **拆分日期**: 2026-06-28
> **作者**: lex-coder (调研) + 待 Mavis/lex-pm 复核

---

## 15.1 任务拆分总览

按借鉴清单 16 个点 → 收敛成 **12 个可执行任务** (P0 5 个 + P1 4 个 + P2 3 个)。

| 编号 | 借鉴源 | 任务标题 | 分配 agent | 优先级 | 估时 | 依赖 |
|---|---|---|---|---|---|---|
| T-REF-01 | 借鉴 7+8 | 四级授权 + LLM 风险评估 + Permission Hook | lex-coder | P0 | 2 周 | Track A W2 |
| T-REF-02 | 借鉴 1+2+3 | Skill 系统 v1 (官方 9 Skill + 律所私有仓库) | lex-ai + lex-coder | P0 | 4 周 | Track A |
| T-REF-03 | 借鉴 8 | 律所自定义 Hook 规则 | lex-coder + lex-ai | P0 | 2 周 | T-REF-01 |
| T-REF-04 | 借鉴 9 | Ask/Plan/Craft 三模式切换 UI | lex-design + lex-coder | P0 | 2 周 | Track D (试用版) |
| T-REF-05 | 借鉴 5+6 | Memory 三层架构 (Working/Session/Persistent) | lex-ai + lex-coder | P1 | 4 周 | Track J (知识库) |
| T-REF-06 | 借鉴 6 | microCompact 上下文压缩 | lex-ai | P1 | 1 周 | T-REF-05 |
| T-REF-07 | 借鉴 5 | 每日反思 / 风格学习引擎 | lex-ai + lex-pm | P1 | 4 周 | T-REF-05 |
| T-REF-08 | 借鉴 13 | Sub-Agent 派发 (类案并行检索) | lex-data + lex-ai | P1 | 3 周 | Track J |
| T-REF-09 | 借鉴 10 | Builder 模式 (律所新人 onboarding) | lex-design + lex-ai | P2 | 3 周 | T-REF-04 |
| T-REF-10 | 借鉴 11 | Desktop ↔ Word/WPS 剪贴板 Bridge | lex-coder + lex-design | P2 | 3 周 | Track A |
| T-REF-11 | 借鉴 14 | Team 多智能体 (企业版 5+ 人协作) | lex-ai + lex-pm | P2 | 6 周 | T-REF-08 |
| T-REF-12 | 借鉴 1 | Skill 商店 (律所级私有 Skill 审核/发布) | lex-pm + lex-coder | P2 | 4 周 | T-REF-02 |

---

## 15.2 任务详细说明

### T-REF-01: 四级授权 + LLM 风险评估 + Permission Hook  ← lex-coder

**借鉴源**: MiniMax Code `AutonomyController` + Claude Code `hooks/toolPermission`

**描述**:
- 落地 PRD §8.3 风险等级策略 (低/中/高/关键)
- 实现 `assessRiskWithLLM()`: 给定操作类型 + 上下文, LLM 评估风险等级
- `PreToolUse` Hook 系统: 文件写 / 文书导出 / 数据删除等敏感操作走 Hook 拦截
- LLM 不可用时 fail-closed, 高风险操作强制升级用户确认

**验收**:
- pytest 覆盖 4 档 × 5 类操作 (20 个组合)
- LLM 风险评估延迟 < 500ms (缓存 + 启发式 fallback)
- 律师可上传自定义 Hook 规则 (JSON 格式)

**依赖**: Track A (Auth JWT 签发)
**借鉴源文件** (MiniMax Code):
- `src/core/autonomyController.ts`
- `src/core/autonomyLLM.ts`
- `src/hooks/engine.ts`
**借鉴源文件** (Claude Code):
- `src/hooks/toolPermission/`

---

### T-REF-02: Skill 系统 v1 (官方 9 Skill + 律所私有仓库)  ← lex-ai + lex-coder

**借鉴源**: AutoClaw Skills 大杂烩 (反向借鉴) + Claude Code SkillTool + WorkBuddy 20+ Skills

**描述**:
- 9 个官方 Skill 首批 3 个 (类案 / 合同审查 / 知识问答), 见 Track E
- Skill 文件格式: `SKILL.md` frontmatter (name/description/version/dependencies/inputs/outputs)
- Skill 注册中心: 类似 Claude Code 的 `Tool.ts` 抽象, 每个 Skill 是独立 tool
- 律所级 Skill 仓库: 律所管理员可上传私有 Skill 到律所, 不进入官方仓库

**验收**:
- 首批 3 个 Skill 可加载 + 调用
- Skill 输入输出 schema 走 Pydantic v2 校验
- 律所仓库跟官方仓库权限隔离
- Skill 启用/禁用 UI (lex-design 配合)

**依赖**: Track A (Auth)
**借鉴源文件**:
- Claude Code `src/tools/SkillTool.ts`
- Claude Code `src/skills/`
- AutoClaw `plugin.json` 格式

---

### T-REF-03: 律所自定义 Hook 规则  ← lex-coder + lex-ai

**借鉴源**: Claude Code `hooks/` (prompt 类型 LLM 守门人)

**描述**:
- 律所可上传 Hook 规则 (JSON / YAML), 定义"文书导出前检查当事人姓名/身份证号"
- Hook 触发时机: `PreToolUse` / `PostToolUse`
- Hook 类型: `command` (shell 脚本) / `prompt` (LLM 守门人) / `agent` (子 Agent 验证)
- 律所级 vs 全局级 hook 分级

**验收**:
- 律所可上传 5 条自定义 hook
- Hook 触发延迟 < 200ms
- Hook 失败时 fail-closed

**依赖**: T-REF-01

---

### T-REF-04: Ask/Plan/Craft 三模式切换 UI  ← lex-design + lex-coder

**借鉴源**: WorkBuddy Ask/Plan/Craft + TRAE Work Builder

**描述**:
- 顶部 Tab 切换: Ask (问答) / Plan (立案预审) / Craft (文书生成)
- Ask: 类案/法规检索, 不修改文件, 最低积分消耗
- Plan: 多步任务, 先生成执行计划 → 律师确认 → 执行
- Craft: 全权执行, 高积分消耗, 高风险操作要求二次确认
- 三模式积分差异化定价

**验收**:
- 三模式可平滑切换, 不重载 context
- Plan 模式的"确认"对话框可视化执行步骤
- Craft 模式敏感操作触发 T-REF-01 的 LLM 风险评估

**依赖**: Track D (试用版订阅系统)
**借鉴源**: WorkBuddy `Ask/Plan/Craft` 模式定义

---

### T-REF-05: Memory 三层架构  ← lex-ai + lex-coder

**借鉴源**: MiniMax Code 三层记忆 (WorkingMemory → SessionMemory → PersistentMemory)

**描述**:
- WorkingMemory: Map, 当前会话, 内存常驻
- SessionMemory: JSON, 历史会话, 落 SQLite
- PersistentMemory: SQLite + FTS5 + 中文 trigram + BM25
- "Relevant Memory" 预取: 关键词提取 + 并行搜索 + 上下文注入
- 律师个人风格学习: PersistentMemory 记录"这位律师喜欢在第 3 段加风险提示"

**验收**:
- 三层记忆读写延迟 < 50ms
- FTS5 中文分词 trigram 准确率 > 90%
- 律师查询历史模板响应 < 200ms

**依赖**: Track J (知识库)
**借鉴源文件**: MiniMax Code `src/memory/`

---

### T-REF-06: microCompact 上下文压缩  ← lex-ai

**借鉴源**: MiniMax Code `microCompact` 两段式

**描述**:
- 60% 阈值: zero-LLM 替换白名单工具 (类案检索/文书生成/Skill 调用) 的旧 tool_result 为占位符
- 93% 阈值: LLM 全量摘要兜底
- 保留最近 5 个 tool_result 不压缩
- 工具调用 pairing 100% 保持

**验收**:
- 20 轮文书迭代场景 context 增长 < 50%
- LLM 摘要延迟 < 2s
- 压缩后律师感知无信息丢失

**依赖**: T-REF-05
**借鉴源文件**: MiniMax Code `src/core/compact/`

---

### T-REF-07: 每日反思 / 风格学习引擎  ← lex-ai + lex-pm

**借鉴源**: MiniMax Code `ReflectionEngine` + `analyzeFeedbackWithLLM`

**描述**:
- 每日 23:00 cron 触发 `generateDailyReview()` (律师可配置时间)
- LLM 反思今天修改的文书 vs AI 初稿, 提取风格信号
- 多偏好识别 (速度 / 详细度 / 风格 / 引用偏好)
- 启发式 fallback: LLM 不可用时, 至少提取基础统计 (字数 / 修改次数 / 常用类案)
- `/feedback` 触发深度反思: 用户主动反馈, 多维偏好识别

**验收**:
- 每日 cron 准确触发率 > 99%
- 风格信号在 7 天后能体现在 AI 初稿生成
- 律师可关闭反思 (隐私选项)

**依赖**: T-REF-05
**借鉴源文件**: MiniMax Code `src/core/reflection/`

---

### T-REF-08: Sub-Agent 派发 (类案并行检索)  ← lex-data + lex-ai

**借鉴源**: Claude Code `AgentTool` + `coordinator/`

**描述**:
- 主 Agent (类案检索 Skill) 派发 3 个 Sub-Agent 并行:
  - 中国裁判文书网 (lex-data 已接入)
  - 最高院指导案例
  - 律协典型案例
- Sub-Agent 独立 context, 完成后回传结果
- 主 Agent 结果合并 + 去重 + 排序
- 借鉴 Claude Code `coordinator/`, 但 LexPrime 3-5 个 Agent 足够, 不需要 1000 集群

**验收**:
- 3 路并行检索 < 5s (单路 < 3s)
- 结果合并去重准确率 > 95%
- Sub-Agent 失败 graceful degrade (不阻塞主流程)

**依赖**: Track J (知识库)
**借鉴源文件**: Claude Code `src/coordinator/`

---

### T-REF-09: Builder 模式 (律所新人 onboarding)  ← lex-design + lex-ai

**借鉴源**: TRAE Work Builder 模式 + WorkBuddy Craft 模式

**描述**:
- 律师一句话任务: "建一个交通事故案件模板"
- Builder 自动拆解: 选案由 → 拉取模板 → 关联案件字段 → 生成文书框架
- 全流程可视化, 每步可暂停 + 律师修改
- 用 T-REF-04 的 Craft 模式底层 + Sub-Agent 派发 (T-REF-08)

**验收**:
- 一句话任务自动拆解成功率 > 80%
- 律师可手动打断修改任意步骤
- 复杂度评分: 简单 (3 步内) / 中等 (5-10 步) / 复杂 (10+ 步)

**依赖**: T-REF-04, T-REF-08
**借鉴源**: TRAE Work Builder 拆解逻辑

---

### T-REF-10: Desktop ↔ Word/WPS 剪贴板 Bridge  ← lex-coder + lex-design

**借鉴源**: Claude Code `bridgeMain.ts` + `bridgeMessaging.ts`

**描述**:
- 系统剪贴板监听 (本地 IPC, 不上云)
- 律师在 Word/WPS 复制文本 → LexPrime 桌面端弹出 "AI 帮你提取要素表?"
- IPC 推送 + 弹窗 + 一键采纳
- 借鉴 Claude Code bridge 架构, 但走本地 socket

**验收**:
- 剪贴板监听延迟 < 100ms
- 弹窗可关闭 + 5 分钟内不重复提示同文本
- 完全本地, 0 网络请求

**依赖**: Track A
**借鉴源文件**: Claude Code `src/bridge/`

---

### T-REF-11: Team 多智能体 (企业版 5+ 人协作)  ← lex-ai + lex-pm

**借鉴源**: Claude Code `TeamCreateTool` + `SendMessageTool`

**描述**:
- 企业版律所 5+ 人协作场景
- Team Agent (主办律师) + Assistant Agent (律师助理) + Review Agent (AI 审查)
- 中央协调器动态分配任务 (借鉴 Claude Code coordinator)
- 共享 context, 实时同步文书修改

**验收**:
- 3-5 个 Agent 并行协作, 端到端延迟 < 10s
- 文书修改冲突解决: CRDT 或 last-write-wins
- 企业版订阅独立计费 (PRD §9 商业模型)

**依赖**: T-REF-08
**借鉴源文件**: Claude Code `src/coordinator/` + `src/services/teamMemorySync/`

---

### T-REF-12: Skill 商店 (律所级私有 Skill 审核/发布)  ← lex-pm + lex-coder

**借鉴源**: AutoClaw 50+ Skills 商店 + WorkBuddy Skill 管理

**描述**:
- 律所管理员可上传私有 Skill 到律所仓库
- 官方审核流程: 律所提交 → LexPrime 官方 review → 通过后进入律所可用列表
- Skill 市场: 跨律所共享 (脱敏后), 类似 npm 私有仓库
- 计费: 部分 Skill 一次性买断, 部分订阅制 (走 PRD §10 商业模型)

**验收**:
- 律所可发布私有 Skill 5 个
- 官方审核 SLA < 7 天
- Skill 商店 UI: 浏览 / 搜索 / 试用 / 购买

**依赖**: T-REF-02
**借鉴源**: AutoClaw Skill 市场 + WorkBuddy 插件商店

---

## 15.3 任务依赖图

```
Track A (Auth W2)
  ↓
T-REF-01 (四级授权) ──→ T-REF-03 (Hook 规则)
  ↓                        ↓
Track D (试用版) ──→ T-REF-04 (三模式)
  ↓                        ↓
Track J (知识库) ──→ T-REF-05 (Memory) ──→ T-REF-06 (microCompact)
                            ↓
                          T-REF-07 (反思引擎)

Track E (Skill) ──→ T-REF-02 (Skill 系统) ──→ T-REF-12 (Skill 商店)
                                            ↓
                                          T-REF-08 (Sub-Agent) ──→ T-REF-11 (Team)
                                                                       ↑
T-REF-04 ──→ T-REF-09 (Builder) ───────────────────────────────┘
T-REF-01 ──→ T-REF-10 (剪贴板 Bridge)
```

---

## 15.4 推荐排期 (Phase 4 剩余 + Phase 5)

### Phase 4 剩余 (Week 5-12)
- W5-6: T-REF-01 (P0 权限) 并行 Track B/D
- W7-8: T-REF-02 (P0 Skill 系统 v1) 并行 Track E
- W9-10: T-REF-03 (P0 Hook 规则) + T-REF-04 (P0 三模式 UI)
- W11-12: T-REF-05 (P1 Memory) 启动

### Phase 5 (Week 13-24)
- W13-16: T-REF-06 (microCompact) + T-REF-07 (反思引擎)
- W17-20: T-REF-08 (Sub-Agent) + T-REF-09 (Builder) + T-REF-10 (剪贴板)
- W21-24: T-REF-11 (Team) + T-REF-12 (Skill 商店) — 企业版

---

## 15.5 风险与依赖

| 风险 | 影响 | 缓解 |
|---|---|---|
| LLM 风险评估延迟高 | T-REF-01 UX 卡顿 | 启发式 fallback + 缓存同类操作 |
| 反射式学习误判 | T-REF-07 错误提取风格 | 律师可视化反馈 + 关闭选项 |
| Sub-Agent 失败连锁 | T-REF-08 主流程阻塞 | graceful degrade + 重试 + 跳过 |
| Skill 商店合规 | T-REF-12 律所上传恶意 Skill | 官方审核 + 沙箱运行 + 律所信用分 |
| 本地 IPC 安全 | T-REF-10 剪贴板隐私 | 加密 socket + 律所白名单 |

---

## 15.6 跨 agent 协作要点

- **lex-coder**: 负责 T-REF-01/03/10 的 backend 实现, 提供 API 给其他 agent
- **lex-design**: 负责 T-REF-04/09/10 的 UI 设计, 跟 v1 设计系统对齐
- **lex-ai**: 负责 T-REF-02/05/06/07/08 的 LLM/RAG 实现, Memory + Skill 核心
- **lex-data**: 负责 T-REF-08 的 Sub-Agent 数据源接入
- **lex-pm**: 负责 T-REF-07/11/12 的产品验证 + PMF 反馈

每个任务开始前, owner agent 拉一个 1-page 实施 spec (从本附录展开), 提交到 plan workspace。

---

## 15.7 相关文档

- 借鉴清单: [`14-references-from-products.md`](./14-references-from-products.md)
- 主 PRD: [`../../PRD.md`](../../PRD.md)
- Track 任务: [`../tracks/README.md`](../tracks/README.md)
- 数据安全: [`07-data-security.md`](../07-data-security.md)

---

**附录状态**: 任务拆分完成, 待 Mavis 在下个 plan 调度。