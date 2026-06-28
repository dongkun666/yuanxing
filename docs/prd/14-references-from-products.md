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

---

## 14.2 共性能力矩阵

| 能力 | Claude Code | MiniMax | Kimi Code | AutoClaw | Codex | WorkBuddy | TRAE Work |
|---|---|---|---|---|---|---|---|
| 终端 CLI | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (IDE) |
| 桌面客户端 | ❌ | ❌ | ❌ | ✅ | ✅ (macOS) | ✅ | ✅ |
| Skills/Plugins 系统 | ✅ (SkillTool) | ✅ (bundled + user) | ✅ | ✅ (50+) | ✅ | ✅ (20+) | ✅ |
| MCP 协议 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 子智能体 / 多 Agent | ✅ (AgentTool + Coordinator) | ⚠️ 内部 | ✅ (千级) | ⚠️ 内部 | ✅ (并行) | ✅ (并行) | ✅ (自定义 Agent) |
| 记忆系统 | ✅ (memdir) | ✅ 三层 | ✅ 长上下文 | ⚠️ | ⚠️ | ✅ (SOUL.md) | ✅ (Trae Rules) |
| 反思 / 复盘 | ⚠️ | ✅ (每日 cron) | ❌ | ⚠️ | ❌ | ❌ | ❌ |
| 权限 / 风险评估 | ✅ (4 档 + LLM 守门) | ✅ (四级 + LLM) | ⚠️ | ⚠️ | ✅ (3 档) | ⚠️ | ⚠️ |
| IM 远程接入 | ❌ | ❌ | ❌ | ✅ (飞书/钉钉/微信) | ❌ | ✅ (微信/企微/QQ) | ❌ |
| LSP / IDE Bridge | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| 本地优先 | ⚠️ | ✅ | ✅ | ✅ | ❌ (云端) | ✅ | ⚠️ |
| 视觉编程 (图→码) | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 跨平台 (Win/Mac) | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ |

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
| P1 | 4. 三层记忆架构 | §5.5 §5.6 | Phase 5 |
| P1 | 5. 每日反思 / 复盘 | §5.6 | Phase 5 |
| P1 | 6. Working Memory 上下文压缩 | §6 §7.5 | Phase 5 |
| P1 | 9. Ask/Plan/Craft 三模式 | §3 | Phase 4 (Track D + E) |
| P1 | 10. Builder 模式 | §3 | Phase 5 |
| P2 | 11. CLI ↔ Desktop Bridge | §6 §7.5 | Phase 5 |
| P2 | 13. Sub-Agent 派发 | §4 §7.5 | Phase 5 |
| P2 | 14. Team 多智能体协作 | §4 | Phase 5 (企业版) |
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