# AGENTS.md — LexPrime Frontend (yuanxing)

## 项目定位

**元枢法智 (LexPrime)** — 律师单人版法律 AI Agent 平台，桌面端 MVP。

- **核心原则**: "AI 辅助、不替代律师"——所有改动维护这条边界
- **产品形态**: 律师个人工具（不是律所 SaaS），用自己的案件数据 + AI 辅助
- **工作区**: `E:\元枢法智前端\yuanxing\`（主）/`E:\falvxiangmu`（legacy, 文档/截图）
- **已删除模块**（不要恢复）:律所 dashboard、`cases-db` / `laws-db` / `companies-db` / `zhixing` 4 个公开数据 view
- **基础设施保留**:`backend/cases-crawler/`（未来律所版复用）

## Tech Stack

- **前端**: 原生 JavaScript（无框架）+ Tailwind CSS + 静态 HTML（多 view 切换）
- **后端**: FastAPI（Python, 端口 3847）
- **AI 服务**: Python（端口 8088）
- **OCR**: Paddle（端口 8089，LEX_OCR_ENGINE=paddle）
- **数据存储**: 本地优先（律师案件数据）+ SQLite + FTS5 + LanceDB
- **没有构建工具链**——Tailwind 改完必须手动 rebuild

## Quick Orientation

```
yuanxing/
├── index.html            # 主入口，多 view 容器
├── assets/               # 静态资源
├── backend/              # FastAPI 后端 + cases-crawler + OCR
├── docs/
│   ├── skills/           # 产品功能文档（合同审查等）
│   ├── prd/              # PRD 历史
│   ├── plans/            # 周计划 yaml + final report + decision
│   └── *.md              # 设计系统 / 部署 / 路线图
├── templates/            # 文书模板
├── scripts/              # 工具脚本
├── data/                 # 本地数据
├── .harness/             # 项目级 agent 配置 + skills
└── AGENTS.md             # 本文件
```

## 项目专属 Skills

放在 `.harness/skills/` 下。

| Skill | 用途 |
|---|---|
| `using-git-worktrees` | Plan track / 跨服务改动 / 多文件功能开发前先建 worktree 隔离（避免并行 subagent 冲突） |
| `dispatching-parallel-agents` | Plan 多 track 并行 / 多 service 体检（frontend ↔ backend:3847 ↔ ai-service:8088 ↔ OCR:8089）/ 多视角代码考古 时,**单 message 发多个 task tool 调用**,每个 subagent 独立上下文（配合 `using-git-worktrees` 做物理隔离） |
| `receiving-code-review` | 接 review 反馈时的思考纪律（验证 → 复述 → push back） |
| `finishing-a-development-branch` | 任务完成后 merge / PR / cleanup 的选项编排 |
| `requesting-code-review` | 提交前 dispatch reviewer 做单 task 级别的快速审查 |
| `contract_review` | W3-W6 产品级合同审查 skill（在 `backend/cases-crawler/skills/`，非 .harness 下） |

需要新增项目专属技能时：建 `.harness/skills/<name>/SKILL.md`，frontmatter 写 `name` + `description`。

## 工作模式 — Plan-Driven

每个 W1/W2/.../W9 是一个 Plan，流程：

1. `docs/plans/plan-NN-*.yaml` — Plan 定义 + track 拆分
2. Subagent 并行执行 tracks
3. **`docs/plans/plan-NN-final-report.md`** — 集成验证 + 决策（**已内置 review 文档**）
4. `docs/plans/plan-NN-decision.json` — plan 级 verdict

**Final report 不重复 review**——它是 plan 级集成验证报告，不替代单 task 级别的 code review。

### Track 隔离 — Worktree 强制

**每个 Plan track / sub-task 必须先建 worktree**——多 subagent 并行时,在 `main` 上直接改会互相覆盖、产生 phantom diff 让你误以为进度在涨。

参考 `.harness/skills/using-git-worktrees/SKILL.md` 的 LexPrime 适配版。核心 3 步:

```bash
BRANCH="w<N>-<track>-<short-desc>"   # 例: w10-a1-frontend-auth-reconnect
git worktree add ".worktrees/$BRANCH" -b "$BRANCH"
cd ".worktrees/$BRANCH"
```

**例外**(可跳过 worktree,在 main 直接改):
- 单文件 typo / 注释 / 文档微调
- `.harness/` / `docs/plans/` / `AGENTS.md` 这类元数据
- 紧急 hotfix(事后补建分支记录)

**红线**:不要在并行 subagent 共享同一 working tree——`.worktrees/` 目录是隔离的物理保证。

## Code Review 纪律（强制）

> 工具：`requesting-code-review` skill（`.harness/skills/requesting-code-review/`，dispatch 模板在 `code-reviewer.md`）。

### 触发场景

| 场景 | 范围 | 强制? |
|---|---|---|
| Subagent 跑完单个 track / sub-task 后，commit 前 | 单 task 改动 `BASE..HEAD` | **强制** |
| 修完复杂 bug（跨服务类型契约、并发、时序、UTF-8 编码回归） | 单 commit / 修复 PR | **强制** |
| 跨 track 集成前 | 涉及 2+ service 的改动 | **强制** |
| 重构 / 性能改动 | `BASE..HEAD` | 建议 |
| 单文件 typo / 注释 / 文档微调 | n/a | 跳过（owner 人工审） |
| Plan 结尾的 `plan-NN-final-report.md` | n/a | **跳过**（它本身就是 review） |

### Dispatch 流程

1. 拿 SHA：
   ```bash
   BASE_SHA=$(git rev-parse HEAD~1)
   HEAD_SHA=$(git rev-parse HEAD)
   ```
2. 读模板：`.harness/skills/requesting-code-review/code-reviewer.md`
3. 填 `[DESCRIPTION]` / `[PLAN_OR_REQUIREMENTS]` / `[BASE_SHA]` / `[HEAD_SHA]`
4. Dispatch `general-purpose` subagent（**只读**，不得修改 working tree / HEAD / branch）
5. 收到意见：
   - **Critical** → 立即修
   - **Important** → 修完再继续
   - **Minor** → 记 TODO，不阻塞

### 红线

- ❌ 不要跳过 review 因为"改动小"——**类型契约错配、IIFE 初始化顺序、Tailwind silent fail 这种坑改 1 行也能爆**
- ❌ 不要让 reviewer subagent 修改 working tree（必须只读）
- ❌ 评审意见与实现冲突时，不要 performative 同意——**带技术依据（测试/复现）反驳**
- ❌ Subagent 不要 `cd` 切到 `yuanxing/` 根之外（`E:\元枢法智前端\` 是 staging 层）

## Critical Project Quirks

详细陷阱 → `~/.mavis/agents/mavis/memory/lexprime-frontend.md`
产品决策 → `~/.mavis/agents/mavis/memory/lexprime-decisions.md`

**核心告诫**：

1. **静态验证抓不到跨服务类型契约错配**——必须真启进程跑 e2e
2. **View 闪现问题**：HTML view 默认 `hidden view-content`，由 `switchView()` 控制
3. **Tailwind silent fail**: `bg-brand/25` opacity 在 hex 无 alpha-value 时失效；arbitrary value 改完必须 rebuild
4. **IIFE + globalThis 桥接失败 = 静默**（不像 throw）——必须放在能访问 X 的同一闭包内
5. **跨文件模块初始化顺序敏感**：A 启动时不能依赖 typeof B 兜底
6. **律师单人版 = 主产品**——不要被引导加律所管理、公开数据库、协作功能

## Working With the User

- **沟通**：中文，快节奏，不问每个细节
- **决策**：关键节点用户拍板，给 3 选项 + 推荐 + 风险点
- **验证**：用户自己跑 cURL / e2e，subagent 不跑 long-running 进程
- **Commit**：不主动 commit，等用户明确要求
- **收工信号**："今天就先到这里" / "push 上去收工" → 立即停新工作，git status 干净 → 更新 memory → 简短汇报

## Hard Rules

- ❌ 不引入框架（React/Vue/Angular）——项目架构决策是原生 JS
- ❌ 不公开律师案件数据——单人本地工具
- ❌ 不越过"AI 辅助"边界——不输出"可替代律师"的承诺
- ❌ 不恢复已删除的 4 个公开数据 view
- ❌ 不在用户面向文案写"代替律师"
- ❌ 修改 `data/` SQLite schema 时跳过 `data/fts5-zh-hit-w8.md` 兼容性说明