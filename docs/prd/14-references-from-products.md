# 14. 附录: 借鉴参考 (References from comparable products)

> **章节定位**: 本附录调研 6 个对标 AI Agent 产品, 提炼可借鉴 / 反借鉴的设计点, 作为 LexPrime Phase 4+ 实施的参考。
> **调研日期**: 2026-06-28
> **作者**: lex-coder (调研) + 待 lex-pm 复核

---

## 14.1 调研对象

| # | 产品 | 厂商 | 一句话定位 | 链接 |
|---|---|---|---|---|
| 1 | **Claude Code** | Anthropic | 终端 AI 编程助手, Agent + Skills + MCP 全栈范式 | [GitHub 镜像](https://github.com/beilingcc/claude-code) (研究快照) |
| 2 | **Minimax Code** (MiniMax) | MiniMax | 中文原生终端 AI 编程助手, 三层记忆 + 反思引擎 + 每日复盘 | [GitHub](https://github.com/MaxHou-infinity/maxcode) |
| 3 | **Kimi Code** | Moonshot AI | Kimi K2.5/K2.6 驱动, 长链路编程 + 千级子智能体集群 + 视觉编程 | [官网](https://www.kimi.com/code) |
| 4 | **AutoClaw (澳龙)** | 智谱 | OpenClaw 简化版, 1 分钟本地部署, 50+ Skills + 飞书 IM 接入 | [官网](https://autoglm.zhipuai.cn/autoclaw) |
| 5 | **Codex** | OpenAI | 云端沙箱 + GPT-5 编程 Agent, 多任务并行 + 自动 PR + 三档风险 | [官网](https://openai.com/codex/) |
| 6 | **WorkBuddy** | 腾讯云 CodeBuddy | 腾讯版 OpenClaw, 桌面客户端, Ask/Plan/Craft 三模式 + IM 远程 | [官网](https://workbuddy.tencent.com) |
| 7 | **TRAE Work** | 字节跳动 | 原 TRAE SOLO 升级, "AI Coding → AI Working", Builder 模式 + Trae Rules | [官网](https://www.trae.com.cn) |
| 8 | **Hermes Agent** | Nous Research | **"self-improving" 闭环** — Agent 任务后自动创建 Skill / Skill 使用中自我改进 / FTS5 跨 session 检索 + LLM 摘要 / Honcho 对话式用户建模 / 兼容 agentskills.io 开放标准 / 6 个 terminal backend (local/Docker/SSH/Singularity/Modal/Daytona) / OpenClaw 一键迁移 | [GitHub](https://github.com/NousResearch/hermes-agent) (205k ⭐ / 36.9k forks) |

---

## 14.2 共性能力矩阵

| 能力 | Claude Code | MiniMax | Kimi Code | AutoClaw | Codex | WorkBuddy | TRAE Work | Hermes Agent |
|---|---|---|---|---|---|---|---|---|
| 终端 CLI | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (IDE) | ✅ |
| 桌面客户端 | ❌ | ❌ | ❌ | ✅ | ✅ (macOS) | ✅ | ✅ | ✅ (Hermes Desktop) |
| Skills/Plugins 系统 | ✅ (SkillTool) | ✅ (bundled + user) | ✅ | ✅ (50+) | ✅ | ✅ (20+) | ✅ | ✅ (autonomous creation + self-improve + agentskills.io) |
| MCP 协议 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 子智能体 / 多 Agent | ✅ (AgentTool + Coordinator) | ⚠️ 内部 | ✅ (千级) | ⚠️ 内部 | ✅ (并行) | ✅ (并行) | ✅ (自定义 Agent) | ✅ (RPC 子智能体 + 零 context 协作) |
| 记忆系统 | ✅ (memdir) | ✅ 三层 | ✅ 长上下文 | ⚠️ | ⚠️ | ✅ (SOUL.md) | ✅ (Trae Rules) | ✅ (agent-curated + FTS5 + Honcho) |
| 反思 / 复盘 | ⚠️ | ✅ (每日 cron) | ❌ | ⚠️ | ❌ | ❌ | ❌ | ✅ (autonomous skill creation + dialectic) |
| 权限 / 风险评估 | ✅ (4 档 + LLM 守门) | ✅ (四级 + LLM) | ⚠️ | ⚠️ | ✅ (3 档) | ⚠️ | ⚠️ | ✅ (command approval + container isolation) |
| IM 远程接入 | ❌ | ❌ | ❌ | ✅ (飞书/钉钉/微信) | ❌ | ✅ (微信/企微/QQ) | ❌ | ✅ (Telegram/Discord/Slack/WhatsApp/Signal/Email) |
| LSP / IDE Bridge | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ |
| 本地优先 | ⚠️ | ✅ | ✅ | ✅ | ❌ (云端) | ✅ | ⚠️ | ✅ (本地/容器/serverless 可选) |
| 视觉编程 (图→码) | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| 跨平台 (Win/Mac) | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ (含 PowerShell 原生) |
| 自我进化 / learning loop | ❌ | ⚠️ (反思) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅✅ (核心卖点, 唯一拥有) |
| 标准化 Skill 格式 | ❌ | ❌ | ❌ | ⚠️ (plugin.json) | ❌ | ❌ | ❌ | ✅ (agentskills.io open standard) |
| 跨 session 检索 + LLM 摘要 | ⚠️ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (FTS5 + LLM summarization) |
| 案件级 context 文件 | ✅ (AGENTS.md) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (Context Files 自动注入) |
| 语音转写 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (voice memo transcription) |
| Docker 镜像 / 离线包 | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ (含 MinGit 隔离 + uv 包管理) |
| OpenClaw 一键迁移 | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ (hermes claw migrate) |

✅ = 主打, ⚠️ = 部分支持, ❌ = 无

---

## 14.3 借鉴清单 (按 PRD 章节分类)

### 14.3.1 Skill 系统 ([PRD §4-cross-cutting §5.4 Skill Hub](../04-cross-cutting.md))

**借鉴点 (优先级 P0)**:

1. **官方 Skill 严控 + 律所私有 Skill 仓库** (来源: AutoClaw/WorkBuddy 通用 Agent 思路 → 反向差异化)
   - AutoClaw/WorkBuddy 是 Skills 大杂烩, 任何开发者都可发布, 质量参差
   - LexPrime 战略原则 "AI 辅助、不替代律师" 要求官方严控 Skill 质量
   - **LexPrime 设计**: 9 个官方 Skill (类案/民间借贷/劳动/离婚/合同审查/遗嘱/刑事/研究备忘录/知识问答) + 律所可上传私有 Skill 到律所仓库
   - **借鉴实现**: AutoClaw 的 Skill 启用/禁用管理 UI + 律所级权限隔离

2. **Skill 版本管理 + 热加载** (来源: Claude Code `SkillTool`)
   - Claude Code 的 Skill 通过 `SKILL.md` 文件描述, 可热加载
   - LexPrime W3+ Skill Hub 需要: Skill 安装 → 版本号 → 启用/禁用 → 一键更新
   - **借鉴实现**: Claude Code 的 `SKILL.md` frontmatter 格式 (name/description/dependencies) 跟 AutoClaw 的 `plugin.json` 混合

3. **Skill 工具调用 + 输入输出 schema** (来源: Claude Code Tool 抽象)
   - 每个 Skill 是个独立工具, 有 `input_schema` + `permission` 模型
   - LexPrime Skill Hub: 类案 Skill 接收 `case_facts` + `cause_category`, 输出 `relevant_cases[]`
   - **借鉴实现**: Claude Code `Tool.ts` 的 `inputSchema + permission + progress_state` 三段式

---

### 14.3.2 Memory / 个人风格学习 ([PRD §5.5 AI 对话 + §5.6 越用越懂你](../04-cross-cutting.md))

**借鉴点 (优先级 P1)**:

4. **三层记忆架构** (来源: MiniMax Code)
   - WorkingMemory (Map, 当前会话) → SessionMemory (JSON, 历史会话) → PersistentMemory (SQLite + FTS5 + 中文 trigram + BM25)
   - **LexPrime 应用**: 律师历史文书风格 / 案由偏好 / 引用案例倾向
   - **借鉴实现**: PersistentMemory 用 SQLite + 中文 trigram (`ChineseTrigramTokenizer`), 支持按"起草借款纠纷起诉状"检索历史模板

5. **每日反思 / 复盘** (来源: MiniMax Code `ReflectionEngine`)
   - 默认 23:00 cron 触发 `generateDailyReview()`, 写入 PersistentMemory
   - **LexPrime 应用**: 每天律师下班后, 系统总结今天修改的文书 vs AI 初稿, 提取"这位律师喜欢在第 3 段加风险提示"等风格信号
   - **借鉴实现**: `ReflectionEngine` + 启发式 fallback (LLM 不可用时仍能提取基础统计)

6. **Working Memory 上下文压缩** (来源: MiniMax Code `microCompact` 两段式)
   - 60% 阈值 zero-LLM 替换 + 93% 阈值 LLM 全量摘要
   - **LexPrime 应用**: 长案件对话 / 长文书迭代 (起草诉状改 20 轮) 时压缩 context
   - **借鉴实现**: microCompact 替换工具结果为占位符, 保留最近 5 个; LLM 兜底

---

### 14.3.3 权限 / 风险评估 ([PRD §7-data-security §8.3 深度护城河系统](../07-data-security.md))

**借鉴点 (优先级 P0)**:

7. **四级授权 + LLM 风险评估** (来源: MiniMax Code `AutonomyController`)
   - Level 0-3 按操作类型 (file/git/system/web/destructive/scheduled) 分别配置
   - LLM 风险评估自动升降级 (`assessRiskWithLLM`)
   - **LexPrime 应用**: PRD §8.3 风险等级策略 (低/中/高/关键) 落地
     - 低 (查询类案) → 自动
     - 中 (生成文书初稿) → 律师确认
     - 高 (导出当事人隐私文档) → 手机验证码
     - 关键 (撤销执业证 / 删除案件) → TOTP + 双人复核 (企业版)
   - **借鉴实现**: LLM 不可用时 fail-closed, 高风险操作强制升级用户确认

8. **Permission Hook 系统** (来源: Claude Code `hooks/toolPermission`)
   - `PreToolUse` Hook + `prompt` 类型 (LLM 守门人) + fallback 三档 (passthrough / deny / ask)
   - **LexPrime 应用**: 文书生成 Skill 调用前, Hook 检查"是否涉及当事人姓名/身份证号", 命中则要求脱敏
   - **借鉴实现**: 律所可上传自定义 Hook 规则 (类似 AutoClaw 的 Rule 插件)

---

### 14.3.4 三模式切换 ([PRD §3 核心场景](../03-core-steps.md))

**借鉴点 (优先级 P1)**:

9. **Ask / Plan / Craft 三模式** (来源: WorkBuddy)
   - Ask = 问答 (查法规/类案), 不修改文件
   - Plan = 创建多步骤执行计划, 用户确认后执行
   - Craft = 全权执行 (生成文书/立案材料)
   - **LexPrime 应用**: 对齐 PRD §3 核心场景
     - Ask → §5.5 AI 对话 (查类案/法规)
     - Plan → §3 立案预审 3.5 步 (拆解 → 确认 → 预审报告)
     - Craft → §3 文书生成 + 庭审准备
   - **借鉴实现**: 三模式切换在 LexPrime 主 UI 顶部加 tab + 不同积分消耗

10. **Builder 模式 (端到端项目生成)** (来源: TRAE Work)
    - 拆需求 → 定功能 → 写文档 → 画页面 → 做原型, 一气呵成
    - **LexPrime 应用**: 律所版 0.1 律所新人 onboarding, 一句话"建一个交通事故案件模板" 自动建案由模板
    - **借鉴实现**: 复杂度高的多步任务走 Builder, 简化版走 Ask (避免给律师过载)

---

### 14.3.5 IDE / Desktop Bridge ([PRD §6-architecture §7.5](../06-architecture.md))

**借鉴点 (优先级 P2)**:

11. **CLI ↔ Desktop Bridge** (来源: Claude Code `bridgeMain.ts`)
    - 双向通信: VS Code / JetBrains IDE ↔ Claude Code CLI
    - **LexPrime 应用**: LexPrime 是桌面 SaaS, 律师在 word/excel 里复制文本, 桌面端弹出 "AI 帮你提取要素表?" 提示
    - **借鉴实现**: 系统剪贴板监听 + IPC 推送 (不上云, 本地 socket)

12. **LSP 集成 (代码补全/跳转)** (来源: Claude Code `LSPTool`)
    - **LexPrime 不适用**: 我们不是 IDE, 不需要 LSP
    - **借鉴原则**: 律师文书编辑走 Word/WPS 插件, 不重新造编辑器

---

### 14.3.6 多 Agent 协作 ([PRD §4 横切面](../04-cross-cutting.md))

**借鉴点 (优先级 P2)**:

13. **Sub-Agent 派发** (来源: Claude Code `AgentTool` + `coordinator/`)
    - 主 Agent 把子任务派发给 Sub-Agent, Sub-Agent 独立 context, 完成后回传结果
    - **LexPrime 应用**: 类案检索时, 主 Agent 派发 3 个 Sub-Agent 并行 (中国裁判文书网 + 最高院指导案例 + 律协典型案例), 结果合并去重
    - **借鉴实现**: LexPrime 不需要 1000 子智能体 (Kimi Code 集群), 3-5 个并行足够律师场景

14. **Team 多智能体协作** (来源: Claude Code `TeamCreateTool` + `SendMessageTool`)
    - 多个 Agent 共享 context, 中央协调器动态分配任务
    - **LexPrime 应用**: 企业版 5+ 人律所, 团队 Agent 协同起草答辩状 (主办律师 + 律师助理 + AI 审查)
    - **借鉴实现**: Phase 5 企业版上线时再做, Phase 4 不优先

---

### 14.3.7 视觉编程 ([PRD §6-architecture](../06-architecture.md))

**借鉴点 (优先级 P2)**:

15. **设计图/截图 → 代码** (来源: TRAE Work + Kimi K2.5)
    - 律师拍照法院传票/判决书 → 自动 OCR + 要素提取 + 入卷
    - **LexPrime 应用**: PRD §9.2 P0 "OCR 闭环" 已经在 Track B, 不重复借鉴
    - **借鉴原则**: LexPrime OCR 走 PaddleOCR (中文专精), 不走通用视觉模型

---

### 14.3.8 IM 远程接入 ([PRD §4 §5.10 横切面](../04-cross-cutting.md))

**借鉴点 (优先级 P3)**:

16. **飞书/钉钉机器人** (来源: AutoClaw + WorkBuddy)
    - 律师在外, 用飞书跟 LexPrime 机器人对话 "查一下王某某案最新进展"
    - **LexPrime 不借鉴**: 本地优先 + 数据不上云是硬约束 (§8.1 第一性原则), 飞书通道意味着数据过云, 律师执业合规风险
    - **借鉴原则**: 律所版 0.1 阶段不考虑 IM 接入, 企业版可走私有化部署的飞书机器人

---

### 14.3.9 Hermes Agent 核心借鉴 ([PRD §1.2 战略原则 #3](../01-product-positioning.md))

**借鉴点 (优先级 P0-P2)**:

17. **"self-improving" 闭环 — Agent 任务后自动创建 Skill + Skill 使用中自我改进** (来源: Hermes Agent 核心, **优先级 P0**)
    - Hermes Agent 的 "closed learning loop" 是其唯一差异化卖点
    - 4 个组件: ① Agent-curated memory with periodic nudges ② Autonomous skill creation after complex tasks ③ Skills self-improve during use ④ FTS5 session search with LLM summarization
    - **LexPrime 应用** (升级 T-REF-07): 反思引擎不仅 "总结今天改了哪些文书", 而是 **"识别今天反复处理的案由, 提议自动生成一个 Skill"** — 律师处理 5 次以上"民间借贷起诉状", AI 自动提议 "民间借贷起诉状 Skill v0.1" (输入: 借款合同 + 当事人信息 → 输出: 标准化起诉状 + 证据清单)
    - 律师可批准 / 修改 / 拒绝 — 不强制生成, 律师掌控权

18. **agentskills.io 开放标准 + Honcho dialectic 用户建模** (来源: Hermes Agent, **优先级 P1**)
    - Hermes 兼容 [agentskills.io](https://agentskills.io) 开放 Skill 格式标准, 跟 OpenClaw/AutoClaw 互通
    - [Honcho](https://github.com/plastic-labs/honcho) dialectic 用户建模: 不是 AI 单方面提取律师偏好, 而是 **AI 主动 push 律师"您是不是在第 3 段总是加风险提示? 我下次会自动加"** + 律师确认 / 反驳
    - **LexPrime 应用** (升级 T-REF-02 + T-REF-07):
      - 9 个官方 Skill 走 agentskills.io 格式 (frontmatter: name/description/version/inputs/outputs/dependencies)
      - 反思引擎不只是 LLM 反思, 而是 **dialectic 双向**: 律师给反馈 + AI 主动确认 + 律师可反驳
    - 借鉴价值: 开放标准让律所上传的私有 Skill 跟生态互通, dialectic 提升风格学习准确率

19. **Context Files (案件级 AGENTS.md) 自动注入** (来源: Hermes Agent + Claude Code, **优先级 P1**)
    - Hermes 在每个项目根目录找 `AGENTS.md`, 自动注入 context
    - **LexPrime 应用** (升级 T-REF-05 Memory): 每个案件文件夹自动有 `case-notes.md` (律师写案情 + AI 摘要), 律师跟 AI 对话时自动注入对应 case 的 context
    - 借鉴价值: 律师不用每次重复 "这个案子的背景是..." — AI 自动从案件级 context 文件读取

20. **多设备同步 (Mac/Win/iPad) — 不走云端, 走本地同步** (来源: Hermes Agent "Runs anywhere, not just your laptop", **优先级 P2**)
    - Hermes 通过云 VM (Modal/Daytona) 跑, Telegram 远程访问
    - **LexPrime 反借鉴云端**, 但借鉴 "Runs anywhere": 律所律师有 Mac 笔记本 + iPad + Win 台式机, 通过**本地网络** (律所 WiFi / 飞秋 / 内网 SMB) 同步案件数据
    - 数据不上公网, 律所 IT 完全掌控
    - **LexPrime 应用** (新任务 T-REF-16): LexPrime Agent + 案件数据 + Memory 三层走 **局域网同步**, 类似 Git 但只同步案件 metadata (不强同步大文件)

21. **语音转写 (Voice memo transcription)** (来源: Hermes Agent, **优先级 P2**)
    - 律师开车 / 通勤时口述案情, 自动转文字入档
    - **LexPrime 应用** (新任务 T-REF-15): 律师在 LexPrime 桌面端按录音键, Whisper 本地推理转中文, 存入案件 notes.md
    - 完全本地推理 (Whisper.cpp 或 sherpa-onnx), 不上云
    - 借鉴价值: 律师通勤时间可入档, **提升用户粘性 + 律师满意度**

22. **Docker 镜像 + 离线包 (律所私有部署)** (来源: Hermes Agent (含 MinGit 隔离 + uv) + AutoClaw (一键安装), **优先级 P1**)
    - Hermes 的 PowerShell 一行安装包: 自动装 uv + Python 3.11 + Node.js + ripgrep + ffmpeg + MinGit (~45MB)
    - AutoClaw 1 分钟本地部署
    - **LexPrime 应用** (升级 T-DEV 现有 Docker Compose): 律所 IT 可一键部署 LexPrime Agent + LexPrime Backend + LexPrime DB 到律所内网服务器, 律师客户端走浏览器访问
    - **借鉴实现**: 类似 AutoClaw 的 1 分钟安装, 但走 Docker Compose + 离线依赖 (Python wheels + Node modules + 模型权重)
    - 注: 这是 PRD §7.5 已有规划, 升级现有实施, 不新增任务

23. **Trajectory compression (执行轨迹压缩, 喂给反思引擎)** (来源: Hermes Agent, **优先级 P1**)
    - Hermes `trajectory_compressor.py` 把 agent 执行轨迹压缩, 既能喂下代模型训练, 也用于反思引擎数据源
    - **LexPrime 应用** (升级 T-REF-06 microCompact): 不仅是压缩 context, 而是 **把轨迹结构化落盘** (tool name / args / result / latency / success), 反思引擎从中提取 "律师在哪步经常手动修改 AI 输出"
    - 借鉴价值: 反思引擎有结构化数据源, 不用 LLM 全文反思, 启发式 fallback 也能跑

---

## 14.4 反借鉴 (LexPrime 不学什么)

| 来源 | 反借鉴理由 |
|---|---|
| **Codex 云端沙箱** | LexPrime 本地优先 (§8.1 第一性原则), 数据不上云是硬约束, 不能用云端执行 |
| **Kimi Code 千级子智能体集群** | 律师单兵作战, 不需要 1000 Agent 协作; 集群调度复杂度溢出律师场景需求 |
| **Codex GitHub PR workflow** | LexPrime 不是开源协作场景, 律师文书不走 PR review |
| **WorkBuddy/Codex 多平台 IM 远程** | 本地优先约束, 飞书/微信通道意味着数据过云, 律师执业合规风险 |
| **AutoClaw 50+ Skills 大杂烩** | 战略原则 "AI 辅助、不替代律师" 要求官方严控 Skill 质量, 律所私有 Skill 走审核制 |
| **Kimi Code 视觉编程 (图→码)** | LexPrime OCR 走 PaddleOCR (中文专精), 通用视觉模型精度不够, 工程上不划算 |
| **Codex 三档风险分级 (Suggest/Auto Edit/Full Auto)** | LexPrime 风险等级是 4 档 (低/中/高/关键), 跟 PRD §8.3 对齐; Codex 的 3 档不够细 |
| **Hermes 6 个 terminal backend 含 Modal/Daytona serverless** | LexPrime 本地/律所私有部署, 不用 serverless 唤醒; Modal/Daytona 意味着依赖云厂商 |
| **Hermes 跨 Telegram/Discord/Slack/WhatsApp/Signal/Email gateway** | LexPrime 数据不上公网 (§8.1 第一性原则), IM 通道过云违反本地优先; LexPrime 走局域网同步 (T-REF-16) |
| **Hermes Nous Portal 一站式云订阅 (300+ 模型 + Tool Gateway)** | LexPrime 模型本地推理 (Qwen2.5-72B 本地化), 不用云模型订阅; Tool Gateway 走公网违反本地优先 |
| **Hermes voice memo transcription 默认走 OpenAI Whisper API** | LexPrime 走 Whisper.cpp / sherpa-onnx 本地推理 (T-REF-15), 律师案件录音不上云 |
| **Hermes autonomous skill creation 默认自动** | LexPrime 反思引擎提议 Skill 后, **必须律师批准** 才生成 (律师掌控权, 不能让 AI 自动产生新 Skill 绕过"AI 辅助不替代律师"原则) |

---

## 14.5 借鉴实施原则

1. **不破坏 PRD 既有战略原则**: 本地优先 / 数据不上云 / AI 辅助不替代律师 / 越用越懂你
2. **不重造轮子**: 借鉴的是设计模式 (Skill 系统 / Memory / Permission Hook), 不是具体代码
3. **小步迭代**: Phase 4 (12 周) 优先 P0 (Skill 系统 + 权限), P1 (Memory + 三模式) 排到 Phase 5
4. **律师优先**: 借鉴点必须能映射到律师实际场景 (查类案 / 起草文书 / 立案), 不能为了"功能对齐"而硬塞
5. **本地实现**: 所有借鉴点都要本地化实现 (SQLite / 本地 LLM / 本地向量), 不能依赖云服务

---

## 14.6 借鉴优先级汇总

| 优先级 | 借鉴点 | PRD 关联 | 预计 Phase |
|---|---|---|---|
| P0 | 1. 官方 Skill 严控 + 律所私有仓库 | §4 §5.4 Skill Hub | Phase 4 (Track E) |
| P0 | 2. Skill 版本管理 + 热加载 | §4 §5.4 | Phase 4 |
| P0 | 3. Skill 工具调用 schema | §4 §5.4 | Phase 4 |
| P0 | 7. 四级授权 + LLM 风险评估 | §7 §8.3 | Phase 4 (Track A + F) |
| P0 | 8. Permission Hook 系统 | §7 §8.3 | Phase 4 |
| P0 | **17. Self-improving 闭环 (Agent 任务后提议自动生成 Skill)** | §1.2 #3 §5.6 | **Phase 4 (升级 T-REF-07)** |
| P1 | 4. 三层记忆架构 | §5.5 §5.6 | Phase 5 |
| P1 | 5. 每日反思 / 复盘 | §5.6 | Phase 5 |
| P1 | 6. Working Memory 上下文压缩 | §6 §7.5 | Phase 5 |
| P1 | 9. Ask/Plan/Craft 三模式 | §3 | Phase 4 (Track D + E) |
| P1 | 10. Builder 模式 | §3 | Phase 5 |
| P1 | **18. agentskills.io 开放标准 + Honcho dialectic 用户建模** | §4 §5.6 | **Phase 5 (升级 T-REF-02 + T-REF-07)** |
| P1 | **19. Context Files 案件级 AGENTS.md 自动注入** | §5.6 | **Phase 5 (升级 T-REF-05)** |
| P1 | **22. Docker 镜像 + 离线包律所私有部署** | §7.5 | **Phase 4 (升级现有, 不新增任务)** |
| P1 | **23. Trajectory compression 结构化反思数据源** | §5.6 | **Phase 5 (升级 T-REF-06)** |
| P2 | 11. CLI ↔ Desktop Bridge | §6 §7.5 | Phase 5 |
| P2 | 13. Sub-Agent 派发 | §4 §7.5 | Phase 5 |
| P2 | 14. Team 多智能体协作 | §4 | Phase 5 (企业版) |
| P2 | **15. 语音转写 (Whisper 本地推理)** | §4 | **Phase 5 (新任务 T-REF-15)** |
| P2 | **20. 多设备局域网同步 (Mac/Win/iPad)** | §7.5 | **Phase 5 (新任务 T-REF-16)** |
| P3 | 16. IM 远程接入 | §4 | 暂缓 / 不做 |

---

## 14.7 相关文档

- 任务拆分: [`15-tasks-from-references.md`](./15-tasks-from-references.md)
- 主 PRD: [`../../PRD.md`](../../PRD.md)
- 路线: [`08-roadmap.md`](../08-roadmap.md)
- 数据安全: [`07-data-security.md`](../07-data-security.md)
- Skill Hub (横切面): [`04-cross-cutting.md` §5.4](../04-cross-cutting.md)

---

**附录状态**: 调研完成, 待 lex-pm 复核 + 拍板借鉴优先级。