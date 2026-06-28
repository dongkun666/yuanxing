# 16. 附录: AI Agent 产品借鉴与 LexPrime 实施 (AI Agent References & Implementation)

> **章节定位**: 本附录基于 8 个 AI Agent 产品 (Claude Code / MiniMax Code / Kimi Code / AutoClaw / Codex / WorkBuddy / TRAE Work / Hermes Agent) 的**真实架构与功能**, 整理可复刻、学习、增加和优化的方向, 作为 LexPrime Phase 4+ 实施的参考
> **调研日期**: 2026-06-28
> **调研者**: Mavis (基于 lex-coder 附录 14+15 越权工作 + GitHub webfetch 真实细节)
> **依赖**: [`13-appendix.md`](./13-appendix.md) § 15.4 Skill 系统 + [`04-cross-cutting.md`](../04-cross-cutting.md) § 5.4 Skill Hub

---

## 16.1 8 个产品调研对象

| # | 产品 | 公司/作者 | GitHub / 官网 | 关键特点 |
|---|---|---|---|---|
| 1 | **Claude Code** | Anthropic (镜像: beilingcc) | [GitHub 镜像](https://github.com/beilingcc/claude-code) (研究) | 终端 AI 编程助手, 1900 文件 / 512K 行 TypeScript, **Bun + React + Ink**, 25+ 工具 + 21+ 命令 + 权限系统 |
| 2 | **MiniMax Code** | MiniMax | [GitHub](https://github.com/MaxHou-infinity/maxcode) | 极简终端 AI 编程助手, 多模型切换 + 反思机制 + 每日改进 |
| 3 | **Kimi Code** | Moonshot AI | [官网](https://www.kimi.com/code) | Kimi K2.5/K2.6 驱动, 智能路由 + 千级并发集群 + 视觉理解 |
| 4 | **AutoClaw (智谱)** | 智谱 | [官网](https://autoglm.zhipuai.cn/autoclaw) | OpenClaw 简化版, 1 分钟本地部署, **50+ Skills** + 国产 IM 集成 |
| 5 | **Codex** | OpenAI | [官网](https://openai.com/codex/) | 移动沙盒 + GPT-5 编码 Agent, 多模态 + 自动 PR + 移动端 |
| 6 | **WorkBuddy** | 腾讯 CodeBuddy | [官网](https://workbuddy.tencent.com) | 腾讯版 OpenClaw, 客户端/服务端架构, **Ask/Plan/Craft 3 模式** + IM 远程 |
| 7 | **TRAE Work** | 字节跳动 | [官网](https://www.trae.com.cn) | 原 TRAE SOLO 改名, "AI Coding → AI Working", **Builder 模式** + Trae Rules |
| 8 | **Hermes Agent** | Nous Research | [GitHub](https://github.com/NousResearch/hermes-agent) (205k ⭐ / 36.9k fork) | **"self-improving" 闭环** + 自主创建 Skill / Skill 使用时自我改进 / FTS5 + LLM 摘要 / Honcho dialectic / agentskills.io 开放标准 / 6 terminal backend / **OpenClaw 一键迁移** |

---

## 16.2 Claude Code 真实架构 (基于镜像 beilingcc/claude-code)

> **注意**: 该仓库是 **Claude Code 源码泄露的镜像** (2026-03-31 通过 npm source map 暴露), 由 beilingcc 维护用于学术/安全研究, **不是 Anthropic 官方仓库**。但它暴露了 Claude Code 的真实架构。

### 16.2.1 规模与技术栈

- **~1900 文件 / 512,000+ 行代码** (TypeScript 100%)
- **运行时**: Bun (含 bun:bundle 编译时 dead code elimination)
- **语言**: TypeScript (strict 模式)
- **CLI**: Commander.js
- **Terminal UI**: React + Ink
- **Schema 验证**: Zod v4
- **代码搜索**: ripgrep
- **协议**: MCP SDK + LSP
- **API**: Anthropic SDK
- **遥测**: OpenTelemetry + gRPC
- **Feature Flags**: GrowthBook
- **认证**: OAuth 2.0 + JWT + macOS Keychain

### 16.2.2 目录结构 (核心)

```
src/
├── main.tsx                 # Entrypoint (Commander.js + Ink renderer)
├── commands.ts              # 命令注册 (~25 命令)
├── tools.ts                 # 工具注册 (~25 工具)
├── Tool.ts                  # 工具类型定义 (inputSchema + permission + progress)
├── QueryEngine.ts           # LLM 查询引擎 (~46K 行)
├── context.ts               # 系统/用户上下文
├── cost-tracker.ts          # Token 成本
├── commands/                # ~50 slash 命令
├── tools/                   # ~40 工具实现
├── components/              # Ink UI (~140)
├── services/                # api/mcp/oauth/lsp/analytics/plugins/compact
├── bridge/                  # IDE ↔ CLI 双向通信 (VS Code/JetBrains)
├── coordinator/             # 多 Agent 协调
├── plugins/                 # 插件系统
├── skills/                  # Skill 系统
├── memdir/                  # 持久内存目录
├── tasks/                   # 任务管理
└── ...
```

### 16.2.3 25+ 工具清单 (可复刻)

| 工具 | 描述 | LexPrime 借鉴 |
|---|---|---|
| **BashTool** | Shell 命令执行 | ⚠️ 律师工具不需要 shell, 跳过 |
| **FileReadTool** | 文件读取 (图片/PDF/笔记本) | ✓ 借鉴 (庭审录音 + 证据 PDF) |
| **FileWriteTool** | 文件创建/覆盖 | ✓ 借鉴 (AI 文书生成) |
| **FileEditTool** | 文件局部修改 | ✓ 借鉴 (律师微调 AI 文书) |
| **GlobTool** | 文件模式匹配 | ⚠️ 不直接需要 |
| **GrepTool** | ripgrep 内容搜索 | ✓ 借鉴 (法条/案例全文检索) |
| **WebFetchTool** | URL 内容抓取 | ✓ 借鉴 (4 公开源数据采集) |
| **WebSearchTool** | Web 搜索 | ✓ 借鉴 (类案检索) |
| **AgentTool** | 子 Agent 派发 | ✓ **强借鉴** (LexPrime sub-agent 类案分析) |
| **SkillTool** | Skill 执行 | ✓ **强借鉴** (Skill Hub) |
| **MCPTool** | MCP 服务器工具调用 | ✓ 借鉴 (未来) |
| **LSPTool** | Language Server Protocol | ⚠️ 不需要 |
| **NotebookEditTool** | Jupyter notebook | ⚠️ 不需要 |
| **TaskCreateTool/TaskUpdateTool** | 任务创建/管理 | ✓ **强借鉴** (LexPrime 任务系统) |
| **SendMessageTool** | 跨 Agent 消息 | ✓ 借鉴 (企业版) |
| **TeamCreateTool/TeamDeleteTool** | 团队管理 | ✓ 借鉴 (企业版 Phase 5) |
| EnterPlanMode/ExitPlanMode | Plan 模式 | ✓ **强借鉴** (Skill 实施前确认) |
| EnterWorktreeTool/ExitWorktreeTool | Git worktree 隔离 | ⚠️ 不需要 (LexPrime 浏览器 SaaS) |
| ToolSearchTool | 延迟工具发现 | ✓ 借鉴 (Skill 按需加载) |
| CronCreateTool | 定时触发 | ✓ 借鉴 (日程中心) |
| RemoteTriggerTool | 远程触发 | ✓ 借鉴 (律师微信推送) |
| SleepTool | 主动模式等待 | ⚠️ 不需要 |
| SyntheticOutputTool | 结构化输出 | ✓ **强借鉴** (AI 文书 JSON 结构) |

### 16.2.4 21+ 命令清单 (借鉴)

- `/commit` / `/review` / `/compact` / `/mcp` / `/config` / `/doctor` / `/login` / `/logout`
- `/memory` / `/skills` / `/tasks` / `/vim` / `/diff` / `/cost` / `/theme` / `/context`
- `/pr_comments` / `/resume` / `/share` / `/desktop` / `/mobile`

### 16.2.5 服务层 (借鉴)

- **api/** - Anthropic API 客户端
- **mcp/** - MCP 服务器连接
- **oauth/** - OAuth 2.0 流程 (LexPrime 律师执业证认证可借鉴)
- **lsp/** - LSP 管理
- **analytics/** - GrowthBook feature flags
- **plugins/** - 插件加载
- **compact/** - 上下文压缩 (LexPrime Token ≤ 8000 机制)
- **policyLimits/** - 组织策略限制 (LexPrime 律师 vs 律所限制)
- **remoteManagedSettings/** - 远程托管设置
- **extractMemories/** - **自动内存提取** (LexPrime 律师经验沉淀)
- **tokenEstimation.ts** - Token 估算
- **teamMemorySync/** - **团队内存同步** (LexPrime 企业版)

### 16.2.6 权限系统 (核心借鉴)

**5 个权限模式** (toolPermission hooks):
- `default` - 每次询问
- `plan` - 只读, 不能改
- `bypassPermissions` - 全部放行 (律师确认)
- `auto` - 智能判断
- 等等

**LexPrime 律师工具权限模型** (借鉴):
- `auto`: 自动执行 (类案检索, AI 文书草稿)
- `ask`: 律师确认后执行 (删除案件, 发送客户消息)
- `block`: 禁止 (上传案件数据到云端)

---

## 16.3 Hermes Agent 真实架构 (NousResearch/hermes-agent, v0.17.0)

### 16.3.1 规模

- **GitHub**: 205k ⭐ / 36.9k fork (2026 年规模)
- **License**: MIT
- **最新版本**: v0.17.0 (2026-06-19)
- **语言**: Python 82.1% + TypeScript 14.0% + JavaScript 1.4%

### 16.3.2 目录结构 (核心)

```
agent/                # 核心 Agent 循环
skills/               # Skills Hub + agent 创建的 skills
tools/                # 40+ tools + toolset system
providers/            # Nous Portal / OpenRouter / OpenAI / 自定义
plugins/              # 插件系统
apps/                 # TUI / Desktop / Web
cron/                 # 定时调度
docker/               # Docker 部署
gateway/              # Telegram/Discord/Slack/WhatsApp/Signal gateway
hermes_cli/           # CLI
ui-tui/               # Full TUI (multiline editing / autocomplete / interrupt)
web/                  # Web UI
acp_adapter/          # Agent Communication Protocol
acp_registry/         # ACP 注册
optional-skills/      # 可选 Skills
optional-mcps/        # 可选 MCP
.plans/               # 计划文件 (.plans)
hermes_bootstrap.py   # 启动引导
hermes_state.py       # 状态管理
run_agent.py          # 主入口
trajectory_compressor.py  # 轨迹压缩 (训练用)
```

### 16.3.3 8 大核心特性 (强借鉴)

1. **Self-improving learning loop** (唯一个) - 创建 skills / 使用时改进 / 主动 persist 知识
2. **Agent-curated memory + periodic nudges** - 自动整理记忆 + 定期提醒
3. **Autonomous skill creation** - 任务完成后**自动创建 Skill** (LexPrime 律师经验沉淀)
4. **Skills self-improve during use** - Skill 使用时自我改进 (LexPrime 律师风格学习)
5. **FTS5 session search + LLM summarization** - 全文本搜索 + LLM 摘要
6. **Honcho dialectic user modeling** - 对话式用户建模
7. **agentskills.io open standard** - 开放 Skill 标准
8. **Trajectory compression** - 用于训练下一代 tool-calling 模型

### 16.3.4 6 terminal backends (借鉴部署)

- **local** - 本地终端
- **Docker** - Docker 容器
- **SSH** - 远程 SSH
- **Singularity** - HPC 容器
- **Modal** - serverless
- **Daytona** - serverless 持久化 (休眠→唤醒)

**LexPrime 借鉴**: Phase 5 企业版按部署形态可选 (个人 SaaS / 律所私有云 / 律所内网)

### 16.3.5 Multi-platform gateway (借鉴)

- Telegram / Discord / Slack / WhatsApp / Signal / **Email**
- Voice memo transcription (语音转文字)
- Cross-platform conversation continuity (跨平台连续)

**LexPrime 借鉴**:
- **微信小程序** (中国律师首选)
- **律师 App 推送** (法律期限预警, 庭审提醒)
- **语音转文字** (庭审录音, 律师口述 → 起诉状草稿)

### 16.3.6 Cron 调度 (强借鉴)

- 定时任务 + 平台分发
- 每日报告, 夜间备份, 周审计

**LexPrime 借鉴**: 法律期限预警 (上诉期/举证期前 7/3/1 天)

### 16.3.7 Subagent RPC (借鉴)

- 隔离子 Agent + 并行工作流
- Python 脚本通过 RPC 调用工具
- 多步流水线压成零上下文回合

**LexPrime 借鉴**: 类案分析 sub-agent (不污染主上下文)

---

## 16.4 借鉴清单 (按 PRD 章节分类)

> **借鉴策略**: 复刻核心架构 + 学习产品哲学 + 增加差异化 + 优化用户体验

### 16.4.1 Skill 系统 (PRD § 5.4 Skill Hub) — **P0**

| # | 来源 | 借鉴方向 | LexPrime 实现 |
|---|---|---|---|
| 1 | AutoClaw / WorkBuddy / Hermes | **官方 Skill 库 + 律师私有 Skill 仓库** | 9 官方 + 律所内自定义 |
| 2 | Claude Code `SkillTool` | **Skill 版本管理 + 优先级** | 律师可强制使用某个版本 |
| 3 | Hermes **agentskills.io** | **开放标准 Skill 格式** | LexPrime Skill 用同一标准 (SKILL.md + manifest) |
| 4 | Claude Code `Tool.ts` | **统一 Tool 抽象 (inputSchema + permission)** | LexPrime Tool 与 Skill 同 schema |
| 5 | Hermes **autonomous skill creation** | **任务后自动生成 Skill** (律师经验沉淀) | 律师结案后 AI 提示"是否沉淀到知识库" |

### 16.4.2 Tool / Permission 系统 — **P0**

| # | 来源 | 借鉴方向 | LexPrime 实现 |
|---|---|---|---|
| 1 | Claude Code 25+ tools | **统一 Tool 抽象** | 类案 / 证据 / 文书 / 法规 / 客户 / 日程 Tool |
| 2 | Claude Code 5 个权限模式 | **律师工具权限模型** | auto / ask / block / plan / readonly |
| 3 | Claude Code `SyntheticOutputTool` | **AI 文书 JSON 结构** | 起诉状/答辩状结构化字段 |
| 4 | Hermes **40+ tools + toolset** | **律师工具集 (toolset 系统)** | 立案 toolset + 庭审 toolset + 结案 toolset |

### 16.4.3 Memory / 个人风格学习 (PRD § 5.5 + § 6) — **P1**

| # | 来源 | 借鉴方向 | LexPrime 实现 |
|---|---|---|---|
| 1 | Hermes **self-improving learning loop** | **律师办案经验自动沉淀** | 结案后 AI 提示"沉淀经验" |
| 2 | Hermes **agent-curated memory** | **律师个人风格学习** | 学习律师文书风格 + 策略偏好 |
| 3 | Hermes **periodic nudges** | **主动 persist 知识** | 律师空闲时 AI 主动整理 |
| 4 | Hermes **Honcho dialectic** | **对话式用户建模** | AI 跟律师对话学习偏好 |
| 5 | Claude Code `memdir/` | **持久内存目录** | LexPrime `~/.lexprime/memory/` |
| 6 | Hermes **extractMemories service** | **自动内存提取** | 从办案历史自动抽取经验 |

### 16.4.4 反思 / 每日改进 (PRD § 3.21 自适应引擎) — **P1**

| # | 来源 | 借鉴方向 | LexPrime 实现 |
|---|---|---|---|
| 1 | MiniMax Code **每日反思** | **每日律师办案复盘** | 每日报告"今天办了 3 案, 用了 6 次 AI, 节省 4h" |
| 2 | Hermes **skills self-improve** | **Skill 使用时自我改进** | 律师用 3 次后 AI 自动优化 Skill 模板 |
| 3 | Hermes **dialectic 反思** | **双 Agent 辩论反思** | "如果你是对方律师, 会怎么攻击?" |
| 4 | Hermes **trajectory compression** | **RAG 上下文压缩** | Token 超 8000 自动压缩 |

### 16.4.5 子 Agent / 团队管理 (PRD § 5.9 团队协作) — **P1**

| # | 来源 | 借鉴方向 | LexPrime 实现 |
|---|---|---|---|
| 1 | Claude Code `AgentTool` | **类案子 Agent** | 类案分析不污染主上下文 |
| 2 | Claude Code `TeamCreateTool` | **企业版律所团队** | Phase 5 多律师协同 |
| 3 | Hermes **subagent RPC** | **Python RPC 调用工具** | LexPrime Python 后端可调用 |
| 4 | Claude Code `SendMessageTool` | **跨 Agent 消息** | 律师 ↔ 律师沟通 |

### 16.4.6 IDE / Bridge 双向通信 — **P2**

| # | 来源 | 借鉴方向 | LexPrime 实现 |
|---|---|---|---|
| 1 | Claude Code `bridge/` | **Word/WPS Bridge** | 律师在 Word 里直接调 LexPrime AI |
| 2 | Claude Code `/desktop` `/mobile` | **桌面/移动端切换** | Phase 5 Electron + 移动 H5 |

### 16.4.7 Ask/Plan/Craft 3 模式 (WorkBuddy) — **P1**

| # | 来源 | 借鉴方向 | LexPrime 实现 |
|---|---|---|---|
| 1 | WorkBuddy **Ask 模式** | **律师只问问题, 不动手** | "AI 文书" tab 答疑 |
| 2 | WorkBuddy **Plan 模式** | **AI 输出方案, 律师确认执行** | "立案预审" tab 报告 |
| 3 | WorkBuddy **Craft 模式** | **律师指挥 AI 执行** | "AI 文书生成" tab |

### 16.4.8 Builder 模式 (TRAE Work) — **P2**

| # | 来源 | 借鉴方向 | LexPrime 实现 |
|---|---|---|---|
| 1 | TRAE **Builder 模式** | **新律师 onboarding** | 首次登录引导式 7 天 |

### 16.4.9 Cron + 跨平台分发 — **P1**

| # | 来源 | 借鉴方向 | LexPrime 实现 |
|---|---|---|---|
| 1 | Hermes **cron + platform delivery** | **法律期限预警 + 微信/邮件** | 上诉期前 7/3/1 天推送 |
| 2 | Hermes **voice memo transcription** | **律师口述 → 起诉状** | 手机录音 → AI 文书 |

### 16.4.10 多设备 / 跨平台同步 — **P2**

| # | 来源 | 借鉴方向 | LexPrime 实现 |
|---|---|---|---|
| 1 | Hermes **cross-platform conversation continuity** | **Mac/Win/iPad 多设备同步** | Phase 5 企业版 Syncthing |
| 2 | Claude Code `/desktop` `/mobile` | **桌面 ↔ 移动切换** | Electron + H5 |

---

## 16.5 LexPrime 实施任务清单 (T-REF-15 ~ T-REF-25)

> 承接 [`15-tasks-from-references.md`](./15-tasks-from-references.md) T-REF-01~14 (lex-coder 越权初版), 本附录补充 T-REF-15~25 (基于真实架构深化)

### 16.5.1 任务表

| 编号 | 借鉴源 | 任务描述 | 负责 agent | 优先级 | 工时 | 依赖 |
|---|---|---|---|---|---|---|
| T-REF-15 | Claude Code `Tool.ts` | **Tool 抽象层 v1** (inputSchema + permission + progress) | **lex-coder** + lex-ai | P0 | 3 周 | Track A (Auth) |
| T-REF-16 | Claude Code 权限系统 | **律师工具权限 5 模式** (auto / ask / block / plan / readonly) | **lex-coder** + lex-pm | P0 | 2 周 | T-REF-15 |
| T-REF-17 | Claude Code `SyntheticOutputTool` | **AI 文书 JSON 结构化输出** | **lex-ai** + lex-coder | P0 | 2 周 | Track E (Skill) |
| T-REF-18 | Hermes `agentskills.io` | **LexPrime Skill 用 agentskills.io 标准** | **lex-ai** + lex-pm | P0 | 1 周 | T-REF-02 (T-REF-15) |
| T-REF-19 | Hermes `self-improving` | **结案后 AI 提示沉淀 Skill** (律师经验自动沉淀) | **lex-ai** + lex-pm | P1 | 3 周 | Track J (知识库) |
| T-REF-20 | Hermes `Honcho dialectic` | **对话式用户建模** (AI 跟律师对话学偏好) | **lex-ai** + lex-pm | P1 | 3 周 | T-REF-19 |
| T-REF-21 | Hermes `cron + platform` | **法律期限预警 + 微信推送** | **lex-coder** + lex-bd | P1 | 2 周 | Track A (Auth) |
| T-REF-22 | Hermes `subagent RPC` | **类案子 Agent RPC** (类案分析不污染主上下文) | **lex-ai** + lex-data | P1 | 3 周 | Track E (Skill) |
| T-REF-23 | Hermes `voice memo` | **律师口述录音 → 起诉状草稿** | **lex-ai** + lex-coder | P2 | 3 周 | T-REF-17 |
| T-REF-24 | Hermes `cross-platform` | **多设备同步 (Mac/Win/iPad)** | **lex-coder** + lex-design | P2 | 4 周 | T-REF-15 + T-REF-19 |
| T-REF-25 | Hermes `trajectory compression` | **RAG 上下文压缩** (Token 超 8000 自动压) | **lex-ai** | P1 | 1 周 | Track E (Skill) |

### 16.5.2 优先级排序

**P0 (12 项任务, Phase 4 必做)**:
- T-REF-15 Tool 抽象
- T-REF-16 权限 5 模式
- T-REF-17 AI 文书 JSON
- T-REF-18 agentskills.io
- (T-REF-01 ~ T-REF-04 from 附录 15)

**P1 (10 项, Phase 4 关键功能)**:
- T-REF-19 self-improving
- T-REF-20 dialectic
- T-REF-21 cron + 微信
- T-REF-22 subagent RPC
- T-REF-25 trajectory compression
- (T-REF-05 ~ T-REF-08 from 附录 15)

**P2 (6 项, Phase 5+ 增强)**:
- T-REF-23 voice memo
- T-REF-24 多设备同步
- (T-REF-09 ~ T-REF-14 from 附录 15)

---

## 16.6 实施建议

### 16.6.1 不要 1:1 复刻

- **避免**: 直接复制 Claude Code 25+ 工具清单 (LexPrime 律师只需要 8-10 个核心 Tool)
- **避免**: Hermes 的 self-improving 复杂度 (LexPrime MVP 阶段简化)
- **避免**: 6 terminal backend (LexPrime 是 SaaS, 不需要)

### 16.6.2 LexPrime 差异化

| 维度 | 借鉴产品 | LexPrime 差异化 |
|---|---|---|
| **数据原则** | 都接云端模型 | **本地优先 + 0 收费 API + 100% 自建数据** |
| **用户** | 程序员 / 通用 | **律师专业场景** (立案 / 证据 / 文书 / 庭审 / 结案) |
| **AI 边界** | 通用 AI | **"AI 辅助, 不替代律师"** 第一性原则 + 类案界面语言规范 |
| **商业模式** | 月订阅 $20 | **¥99/月 (5x 便宜)** + 30 天免费试用 + 终身免费专业版 (创始体验官) |

### 16.6.3 Phase 4 实施节奏 (调整)

基于本附录, Phase 4 排期微调:
- **W2-3**: Auth (Track A) + Tool 抽象 (T-REF-15) + 权限 5 模式 (T-REF-16)
- **W4-6**: 9 个官方 Skill (Track E) + agentskills.io 适配 (T-REF-18) + AI 文书 JSON (T-REF-17)
- **W7-9**: 30 天免费试用 + Stripe + Cron 微信 (T-REF-21)
- **W10-12**: self-improving (T-REF-19) + dialectic (T-REF-20) + trajectory compression (T-REF-25)

---

## 16.7 相关文档

- **附录 13**: [`13-appendix.md`](./13-appendix.md) § 15.4 Skill 系统 (lex-coder 调研 + 9 个官方 Skill 列表)
- **附录 14**: [`14-references-from-products.md`](./14-references-from-products.md) (lex-coder 越权: 8 产品清单 + 功能对比, 整合基础)
- **附录 15**: [`15-tasks-from-references.md`](./15-tasks-from-references.md) (lex-coder 越权: T-REF-01~14 初版任务, 本附录 T-REF-15~25 深化)
- **PRD § 5.4 Skill Hub**: [`../04-cross-cutting.md`](../04-cross-cutting.md)
- **PRD § 6 个人知识库**: [`../05-knowledge-base.md`](../05-knowledge-base.md)
- **Phase 4 Roadmap**: [`../../phase4-roadmap.md`](../../phase4-roadmap.md)

---

> **"借鉴是为了差异化, 不是为了模仿。"**
>
> *—— Mavis 2026-06-28*