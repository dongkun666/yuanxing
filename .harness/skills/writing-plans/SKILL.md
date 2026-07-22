---
name: writing-plans
description: 设计文档确认后、写代码前必须激活——将设计拆解为 bite-sized 任务，每个任务有精确文件路径、完整代码、验证步骤。TDD 优先。
---

# Writing Plans — 详细实施计划

## 触发条件

**必须激活：**
- brainstorming 完成，设计文档已获用户确认
- 任何涉及 2+ 文件的开发任务
- 前后端联动的功能开发
- Plan / Track 级别的任务拆解

**可跳过：**
- 单文件小改动（< 20 行）
- 已有明确步骤的简单 bug 修复
- 纯文档修改

## 核心原则

> **假设执行者是零上下文、品味差、讨厌测试的初级工程师——把所有东西写死。**

- 每个任务 2-5 分钟可完成
- 精确文件路径 + 完整代码，零占位符
- TDD：先写失败测试，再写实现
- DRY / YAGNI / 频繁提交

## 步骤流程

### 第 1 步：范围检查
- 设计是否包含多个独立子系统？
- 是 → 拆分为多个 plan，每个 plan 可独立交付
- 否 → 继续

### 第 2 步：文件结构映射
在拆任务前，先列清所有涉及的文件：

**前端（原生 JS + Tailwind）：**
- `templates/views/<view>.html` — 页面 HTML
- `assets/` — 静态资源（如需要）
- Tailwind 类：直接写在 HTML 中，注意 rebuild

**后端（FastAPI）：**
- `backend/cases-crawler/app/main.py` — 路由注册
- `backend/cases-crawler/app/routers/<name>.py` — 路由实现
- `backend/cases-crawler/app/models/<name>.py` — Pydantic 模型
- `backend/cases-crawler/app/services/<name>.py` — 业务逻辑
- `backend/cases-crawler/tests/` — 测试

**数据：**
- SQLite schema 变更 →  migration 脚本
- LanceDB → 初始化逻辑

### 第 3 步：拆解任务
**任务边界原则：**
- 每个任务产出可独立测试的交付物
- 包含 setup / 配置 / 文档
- 一个任务 = 一次 review gate

**任务粒度（每个任务 5-8 个 step）：**
```
- [ ] Step 1: 写失败的测试
- [ ] Step 2: 运行测试，确认失败
- [ ] Step 3: 写最小实现代码
- [ ] Step 4: 运行测试，确认通过
- [ ] Step 5: （可选）重构
- [ ] Step 6: 提交
```

### 第 4 步：Plan 文档结构
保存到：`docs/plans/plan-NN-<feature>.yaml` 或 `docs/plans/YYYY-MM-DD-<feature>-plan.md`

**文档头：**
```markdown
# [功能名] 实施计划

**目标：** [一句话描述]
**架构：** [2-3 句话说明技术方案]
**技术栈：** 原生 JS + Tailwind / FastAPI / SQLite / LanceDB

## 全局约束
- 不引入新框架（React/Vue 等）
- 律师单人版，不涉及律所/协作功能
- 本地优先，数据不离开用户设备
- Tailwind 修改后需 rebuild
```

**任务模板：**
```markdown
### Task N: [组件名]

**文件：**
- 创建：`exact/path/to/file.py`
- 修改：`exact/path/to/existing.py:123-145`
- 测试：`tests/exact/path/test.py`

**接口：**
- 依赖：[前序任务提供的接口，精确签名]
- 产出：[后续任务依赖的接口，精确函数名/参数/返回类型]

**步骤：**

- [ ] **Step 1: 写失败的测试**
```python
# 完整测试代码
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: 运行测试，确认失败**
命令：`cd backend/cases-crawler && pytest tests/path/test.py::test_name -v`
预期：FAIL，错误信息 "function not defined"

- [ ] **Step 3: 写最小实现**
```python
# 完整实现代码
def function(input):
    return expected
```

- [ ] **Step 4: 运行测试，确认通过**
命令：`cd backend/cases-crawler && pytest tests/path/test.py::test_name -v`
预期：PASS

- [ ] **Step 5: 提交**
```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
```

### 第 5 步：Plan 自检
写完 plan 后，逐项检查：

- [ ] **Spec 覆盖**：设计文档的每个需求都对应到任务了吗？
- [ ] **占位符扫描**：有没有 TBD / TODO / "适当的错误处理" / "类似 Task N"？
- [ ] **类型一致性**：后序任务用的函数名/参数/类型和前序任务定义的一致吗？
- [ ] **前端特定**：HTML view 的 `hidden view-content` class 对吗？`switchView()` 集成了吗？
- [ ] **后端特定**：路由注册了吗？Pydantic 模型定义了吗？错误响应格式统一吗？
- [ ] **跨服务契约**：前端调用的 API 路径、请求体、响应字段和后端一致吗？

发现问题直接修复，不用再审。

### 第 6 步：交付执行选择
Plan 写完后，给用户两个选项：

```
Plan 完成，已保存到 `<path>`。两种执行方式：

1. **Subagent 驱动（推荐）** — 每个任务派一个独立 subagent，任务间 review，迭代快
2. **内联执行** — 当前会话按任务执行，批量执行 + 检查点

选哪种？
```

## 检查清单

| 检查项 | 状态 |
|--------|------|
| 范围检查：独立子系统已拆分 | ☐ |
| 文件结构映射完整（前端+后端+数据+测试） | ☐ |
| 每个任务有精确文件路径 | ☐ |
| 每个步骤有完整代码，零占位符 | ☐ |
| TDD 流程：测试→失败→实现→通过 | ☐ |
| 接口契约前后一致 | ☐ |
| 自检 6 项全部通过 | ☐ |
| 用户已选执行方式 | ☐ |

## 常见陷阱

- ❌ "这个简单，不用写 plan" → 简单功能最容易漏边界情况
- ❌ 占位符代码 "// TODO: implement" → 执行者会直接跳过
- ❌ 任务太大（>10 个 step）→ 执行者容易跑偏
- ❌ 接口定义模糊 → 前后端联调爆炸
- ❌ 忘了 Tailwind rebuild → 样式不生效以为是 bug
