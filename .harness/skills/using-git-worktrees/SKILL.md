---
name: using-git-worktrees
description: 在开始 Plan track、跨服务改动或多文件功能开发前，使用 git worktree 进行物理隔离，避免并行 subagent 互相覆盖工作目录，确保每条开发线独立、可验证、可回溯。
---

# 使用 Git Worktree 进行开发隔离

**核心理念（Superpowers）：** 每个任务都有自己的物理工作目录，就像给每个开发者配了一台独立的机器——不会互相踩文件、不会有 phantom diff、不会因为上下文切换搞乱状态。

## 何时使用

**强制使用（LexPrime 项目规则）：**

- 每个 Plan track / 子任务开始前
- 多个 subagent 并行执行时
- 跨服务改动（frontend + backend + AI service 同时改）
- 需要同时对比多个分支的代码时
- 跑实验性改动，不想污染主工作区时

**可以跳过（直接在 main 上改）：**

- 单文件 typo / 注释 / 文档微调
- `.harness/` / `docs/plans/` / `AGENTS.md` 这类元数据
- 紧急 hotfix（事后补建分支记录）

**红线：** 绝对不要让两个并行 subagent 共享同一个 working tree——`.worktrees/` 目录是隔离的物理保证。

## 完整工作流程

### 第一步：创建分支

从最新的 main 拉出特性分支，命名清晰可追溯：

```bash
git checkout main
git pull origin main
```

### 第二步：创建 Worktree

在 `.worktrees/` 目录下创建隔离的工作目录：

```bash
BRANCH="w<N>-<track>-<short-desc>"   # 例: w10-a1-frontend-auth-reconnect
git worktree add ".worktrees/$BRANCH" -b "$BRANCH"
```

参数说明：
- `.worktrees/$BRANCH` — worktree 的物理路径
- `-b "$BRANCH"` — 同时创建并切换到新分支

### 第三步：进入目录并设置环境

```bash
cd ".worktrees/$BRANCH"
```

**重要：** 进入 worktree 目录后，所有操作都在这个独立工作区进行。如果项目需要安装依赖、启动服务，确保在对应 worktree 目录下操作。

### 第四步：验证基线

开工前先确认环境没问题：

```bash
git status          # 应该是干净的，在正确的分支上
git log --oneline -5  # 确认基于最新的 main
```

如果项目有构建/测试步骤，建议先跑一遍基线，确保不是从一个坏的起点开始。

## LexPrime 项目适配

### 分支命名规范

```
w<周数>-<track编号>-<简短描述>
```

示例：
- `w10-a1-frontend-auth-reconnect`
- `w9-b3-backend-contract-ocr`
- `w8-c2-ai-service-prompt-tuning`

**为什么这样命名：**
- `w<N>` 快速定位到哪个 Plan
- `<track>` 对应 plan yaml 里的 track 编号
- `<short-desc>` 让人一眼知道在做什么

### `.worktrees/` 目录约定

- 所有 worktree 统一放在项目根的 `.worktrees/` 下
- `.gitignore` 里已经忽略 `.worktrees/` 目录，不会被提交
- 删除 worktree 时用 `git worktree remove <path>`，不要手动删目录
- 任务完成后及时清理，避免堆积

### 例外情况详细说明

**可以不用 worktree 的场景：**

| 场景 | 原因 |
|---|---|
| 单文件 typo 修复 | 改动极小，不存在并行冲突风险 |
| 注释补充 / 文档微调 | 不会影响运行时行为 |
| `.harness/skills/` 新增或修改 | 元数据层，不影响代码运行 |
| `docs/plans/` 写 plan 或 final report | 文档类工作，串行执行 |
| 紧急线上 hotfix | 时间优先，事后补建分支保留记录 |

**判断口诀：** 会不会有另一个 agent 同时改同一个文件？会 → 用 worktree；不会 → 可以直接改。

## 常用 Worktree 命令

### 列出所有 worktree

```bash
git worktree list
```

输出示例：
```
/path/to/main       abc1234 [main]
/path/to/.worktrees/w10-a1-feature def5678 [w10-a1-feature]
```

### 切换到已有的 worktree

不用 `git checkout`，直接 `cd` 过去就行——每个 worktree 是独立目录，自带分支状态。

### 删除 worktree

```bash
git worktree remove .worktrees/w10-a1-feature
```

如果 worktree 里有未提交的改动，会提示。确认要丢弃的话加 `-f`：

```bash
git worktree remove -f .worktrees/w10-a1-feature
```

### 清理已失效的 worktree 引用

如果手动删了目录，git 里还留着记录：

```bash
git worktree prune
```

## 多 Track 并行工作模式

配合 `dispatching-parallel-agents` skill 使用时的标准流程：

```
main (干净状态)
├── .worktrees/w10-a1-frontend/   ← subagent A 负责
├── .worktrees/w10-a2-backend/    ← subagent B 负责
└── .worktrees/w10-a3-ai/         ← subagent C 负责
```

每个 subagent 在自己的 worktree 里：
1. 独立开发
2. 独立测试
3. 独立 commit
4. 互不干扰

最后在 main 上逐个 merge，做集成验证。

## 注意事项与陷阱

### ❌ 常见错误

1. **在 main 上直接改，同时派了 subagent**
   - 后果：两边改到同一个文件，merge 时一头包
   - 正确做法：主 agent 待在 main 不动，所有开发工作都在 worktree 里做

2. **手动 rm -rf 删除 worktree 目录**
   - 后果：git 里还留着引用，list 的时候会看到乱码
   - 正确做法：用 `git worktree remove`

3. **两个 worktree 跑同一个端口的服务**
   - 后果：端口冲突
   - 正确做法：要么只启动一个，要么改配置用不同端口

4. **在 worktree 里 git push 后忘了 main 还没更新**
   - 后果：回到 main 发现已经落后了
   - 正确做法：merge 回 main 之后记得 pull 或在 main 上 merge

### ✅ 最佳实践

1. **开工前先列一下 worktree** — `git worktree list`，心里有数
2. **命名和分支名保持一致** — 看目录名就知道对应哪个分支
3. **任务完成立即清理** — 不要让 `.worktrees/` 变成垃圾场
4. **主 agent 待在 main** — 做调度和集成，不直接改代码
5. **每个 worktree 单独装依赖** — 如果改了 package.json/requirements.txt，各装各的

## 与其他 Skill 的配合

- **`dispatching-parallel-agents`** — 并行调度的每个 task 都应该在独立 worktree 中执行
- **`requesting-code-review`** — 在 worktree 里开发完，review 通过后再合并回 main
- **`finishing-a-development-branch`** — 任务完成后，用这个 skill 做 merge / PR / cleanup

## 参考

- LexPrime 项目规则：`.harness/AGENTS.md` "Track 隔离 — Worktree 强制" 章节
- Git 官方文档：`git worktree --help`
