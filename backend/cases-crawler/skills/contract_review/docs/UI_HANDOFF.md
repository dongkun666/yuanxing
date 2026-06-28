# Skill 2 (合同风险审查) UI Hand-off Spec · 给 lex-design 的对接文档

> **Status**: W3 草稿, 等候 lex-design 评审 + 律师顾问 review (W6)
> **Owner**: lex-ai (data + algorithm) → **lex-design** (UI implementation)
> **关联 Track**: E-skills · T-REF-22 subagent RPC · T-REF-25 trajectory compression

---

## 1. Skill 入口 (在 Skill Hub 中)

```
Skill Hub > 官方技能 > 合同风险审查
```

### 入口卡片
- **图标**: 紫色盾牌 + 文档 + 高亮笔 (建议 SVG icon, 区别于 Skill 1 蓝色)
- **标题**: "合同风险审查"
- **副标题**: "逐条审查 · 三级风险 · 修改建议 · 谈判策略"
- **描述**: 1 句话: "对律师上传的合同文本进行逐条审查, 输出三级风险标注 (致命/重大/建议) + 修改建议 + 谈判策略。**仅呈现客观风险描述, 不做任何确定性判断或预测**。"
- **加载时间**: < 3s (W5 实测)
- **点击行为**: 跳转到 Skill 详情页 (上传区 + 输入表单 + 最近审查)

---

## 2. 上传区 + 输入表单 (左栏)

### 2.1 上传区
| UI 控件 | 行为 | 限制 |
|---|---|---|
| 拖拽上传 | PDF / Word / 图片 (jpg/png) | ≤ 10MB |
| 粘贴文本 | 直接粘贴合同文本 | ≤ 50000 字 |
| OCR 识别 | 图片自动 OCR → 文本 (复用 Track B) | 律师可手动校正 |

### 2.2 输入字段 (input_schema 映射)

| UI 控件 | input_schema 字段 | 必填 | 校验 |
|---|---|---|---|
| 下拉选 (合同类型) | `contract_type` | ✓ | 8 大类 |
| 4 选 1 (立场) | `stance` |   | 甲方/乙方/丙方/审查方 (默认审查方) |
| 搜索框 (行业) | `industry` |   | 自动补全 |
| 数字框 (标的金额) | `amount` |   | 元 |
| 搜索框 (管辖地) | `jurisdiction` |   | 31 省/直辖市 |
| 多选 chip (关注领域) | `focus_areas` |   | 10 大领域 |
| 复选框 (生成建议) | `include_suggestion` |   | 默认开 |
| 复选框 (生成策略) | `include_negotiation_strategy` |   | 默认开 |
| 复选框 (版本比对) | `include_version_diff` |   | 需历史版本 |

### 2.3 提交按钮
- 主按钮: "审查合同" (紫色, 圆角 8px)
- 次按钮: "清空" (灰色文字按钮)
- Loading 状态: 进度条 + "审查中... (P95 < 2s, 含 LLM 调用)" 字样

---

## 3. 审查结果展示 (右栏 / 移动端底部)

### 3.1 顶部: 红黄蓝绿灯 + 风险计数
```
[🔴] 致命 1 · 重大 1 · 建议 2 · 合规 3
```
- `traffic_light` = red (fatal) / yellow (major) / green (advisory only) / gray (无审查)
- 颜色规则见 `language_guard.py` 注释 + `reviewer.py:compute_traffic_light`

### 3.2 合同原文区 + 风险高亮 (核心交互)

按条款顺序排列, 每条款卡片:

| 风险等级 | 卡片颜色 | 边框 | 标签 |
|---|---|---|---|
| fatal | 红色 | 红色实线 2px | "致命" |
| major | 黄色 | 黄色实线 2px | "重大" |
| advisory | 蓝色 | 蓝色虚线 1px | "建议" |
| ok | 绿色 | 无边框 | "合规" |

每条款卡片内容:
- 条款序号 + 标题 (粗体)
- 条款原文 (≤ 1000 字)
- 风险分类标签 (彩色 chip)
- 法律依据 (法条列表, 灰色小字)
- 风险描述 (≤ 800 字, **强制 language_guard 合规**)
- 修改建议 (致命/重大必填, 折叠展开)
- 修改后条款模板 (致命必填, "一键替换" 按钮)
- 立场影响评估 (彩色 chip: 不利红 / 中性灰 / 有利绿)
- 审查置信度 (0-100% 进度条)
- 操作按钮: "📌 收藏" + "📋 加入证据" + "🔗 查看法条"

### 3.3 整体风险汇总 (顶部固定)

```
致命 1 · 重大 1 · 建议 2 · 合规 3
高频风险: 违约金过高 · 显失公平 · 解除权失衡
```
- 点击"整体风险汇总"展开 narrative (≤ 800 字, **强制 language_guard 合规**)

### 3.4 谈判策略弹窗 (点击"查看策略" 触发)

| 模块 | 内容 |
|---|---|
| 优先谈判条款 | 按 fatal > major > advisory 排序的条款 ID 列表 |
| 谈判筹码 | 每个杠杆条款的谈判筹码 + 让步方向 |
| 红线条款 | 致命风险中律师无法通过谈判弥补的条款 |
| 立场建议 | 基于立场的策略 (甲方/乙方/丙方/审查方), 强制 language_guard |

### 3.5 版本比对面板 (include_version_diff=true 时显示)

| 模块 | 内容 |
|---|---|
| 对比基线 | baseline_version_id + compared_version_id |
| 新增条款 | 列表 (风险等级 + 条款标题 + 文本) |
| 删除条款 | 列表 (条款标题 + 删除文本) |
| 修改条款 | 列表 (diff_type + 旧/新文本 + 风险等级变化) |
| 比对摘要 | ≤ 500 字, 强制 language_guard |

### 3.6 强制免责声明 (页面底部固定)
> 本审查仅为基于合同文本的客观风险标注与法律依据提示, 不构成法律意见, 更不替代律师的专业判断。

- 桌面端: 灰色小字 + 顶部细线分隔
- 移动端: 折叠版: "本审查为客观风险标注, 不构成法律意见, 不替代律师判断。"
- 谈判策略弹窗: 简短版本
- 导出 Word/PDF: 完整声明 (页脚)

---

## 4. 错误状态

| 场景 | UI 表现 |
|---|---|
| 合同类型无法识别 | 自动归类到"其他", 提示"合同未匹配到标准类型, 已按'其他'审查" |
| 合同无标号 | 按段落拆分, 提示"合同未使用'第X条'标准标号, 已按段落拆分" |
| LLM narrative 违规 3 次 | 静默使用降级模板, UI 不显示 |
| 合同文本 > 50000 字 | 自动截断, 提示"合同文本超过 50000 字, 已截取前 50000 字审查" |
| 审查超时 (>2s) | Toast: "审查超时, 已返回部分结果, 请稍后重试或缩短合同。" |

---

## 5. 性能预算

| 指标 | 目标 | 实测 |
|---|---|---|
| 页面打开到可输入 | < 500ms | W5 实测 |
| 上传到 OCR 完成 | < 1s (PDF) / < 3s (图片) | 复用 Track B |
| 点击"审查合同"到结果展示 | < 2.5s (含 P95 < 2s 后端) | W5 实测 |
| 滚动 50 件条款流畅度 | 60fps |  |
| 风险高亮渲染 | < 100ms |  |

---

## 6. 与 Skill Hub 的集成

- 入口: Skill Hub > 我的 Skill > 已启用 (默认启用, 可手动关闭)
- 历史: Skill Hub > 合同风险审查 > 审查历史 (最近 20 条)
- 收藏: 跨 contracts / risk_annotations 库, 用现有 favorites API
- 与 Skill 1 类案检索的关联: 致命/重大风险条款可一键跳转到类案检索 (查询同类合同纠纷)

---

## 7. 关联文档

- `manifest.json` (agentskills.io 标准)
- `schemas/input.json` / `schemas/output.json`
- `prompt.md` (LLM system prompt)
- `language_policy.md` (界面语言规范)
- `disclaimer.md` (强制免责声明)
- `reviewer.py` (后端算法)
- `language_guard.py` (语言守卫)
- `tests/test_contract_review_skill.py` (15 项测试)
- Skill 1 类案检索 (`skills/caselaw/docs/UI_HANDOFF.md`) — UI 设计参考

---

## 8. 待办

| # | 项 | 负责人 | 截止 |
|---|---|---|---|
| 1 | UI 设计稿 (Figma) | lex-design | W5 Day 2 |
| 2 | OCR 集成 (复用 Track B) | lex-coder | W5 Day 3 |
| 3 | Word / PDF 导出 (复用 Track H) | lex-coder | W5 Day 4 |
| 4 | 律师顾问评审 (≥ 3 人) | lex-pm + 律师 | W6 |
| 5 | UI 端语言规范自检 (集成 test_language_guard) | lex-coder | W5 Day 4 |
| 6 | 移动端适配 | lex-design | W5 Day 5 |
| 7 | 与 Skill 1 类案检索的跨 Skill 跳转 | lex-design + lex-coder | W5 Day 5 |

---

> **最后更新**: 2026-06-29 · lex-ai · 等待 lex-design 反馈