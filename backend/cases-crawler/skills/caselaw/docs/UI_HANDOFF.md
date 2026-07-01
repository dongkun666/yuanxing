# Skill 1 (类案检索) UI Hand-off Spec · 给 lex-design 的对接文档

> **Status**: W5 草稿, 等候 lex-design 评审 + 律师顾问 review (W8)
> **Owner**: lex-ai (data + algorithm) → **lex-design** (UI implementation)
> **关联 Track**: E-skills · T-REF-22 subagent RPC · T-REF-25 trajectory compression

---

## 1. Skill 入口 (在 Skill Hub 中)

```
Skill Hub > 官方技能 > 类案检索与裁判参考
```

### 入口卡片
- **图标**: 蓝色盾牌 + 数据柱状图 (建议 SVG icon)
- **标题**: "类案检索与裁判参考"
- **副标题**: "多维度检索 · 统计参考 · 中立用语"
- **描述**: 1 句话: "在已公开裁判文书中检索与当前案件相似的判例, 输出支持率统计 / 判赔金额参考 / 主要争议焦点。**仅呈现统计数据, 不做任何确定性判断。**"
- **加载时间**: < 3s (W7 实测)
- **点击行为**: 跳转到 Skill 详情页 (输入表单 + 最近检索)

---

## 2. 检索输入表单 (左栏)

字段 → input_schema 映射:

| UI 控件 | input_schema 字段 | 必填 | 校验 |
|---|---|---|---|
| 下拉选 (案由) | `cause` | ✓ | 8 大类 + 60+ 细分 |
| 多行文本框 | `facts` |   | ≤ 4000 字 |
| 搜索框 + 自动补全 | `court` |   | 历史法院名联想 |
| 文本框 | `judge_name` |   |  |
| 双滑块 (年份) | `year_from` / `year_to` |   | 2000-2030 |
| 下拉选 | `region` (省) |   | 31 省/直辖市 |
| 4 选 1 | `case_type` |   | 民事/刑事/行政/执行 |
| 下拉选 | `procedure` |   | 一审/二审/再审/执行 |
| 数字框 | `amount_dispute` |   | 元 |
| 数字框 (默认 20) | `top_k` |   | 1-50 |

### 提交按钮
- 主按钮: "检索类案" (蓝色, 圆角 8px)
- 次按钮: "清空条件" (灰色文字按钮)
- Loading 状态: 进度条 + "检索中... (P95 < 1s)" 字样

---

## 3. 检索结果展示 (右栏 / 移动端底部)

### 3.1 顶部: 红黄绿灯 + 样本数
```
[🟢] 87 件样本 · 近 3 年 · 上海一中院
```
- `traffic_light` = green/yellow/red/gray
- 颜色规则见 `language_guard.py` 注释 + `retrieval.py:compute_traffic_light`

### 3.2 柱状图: 年份支持率 (ui_hints.show_bar_chart)
- X 轴: 年份 (2020-2025)
- Y 轴: 支持率 (%)
- 每根柱顶标: "X 件 / Y 件 (Z%)"
- hover tooltip: 显示该年完整 outcome_distribution

### 3.3 箱线图: 判赔金额 (ui_hints.show_box_plot)
- 仅在 `amount_stats.median_cny` 有值时显示
- 显示中位数 / Q1-Q3 / Min-Max 标签
- 单位: 元
- 缺失值: 灰色 "样本中无金额数据"

### 3.4 法官卡片 (ui_hints.show_judge_card)
- 仅在 judge_style.sample_size >= 5 时显示
- 显示: 法官姓名 / 样本数 / 支持率 / 平均审理周期 / 证据采信倾向
- **强制 narrative 文案以 "该法官在 N 件...样本中..." 开头**

### 3.5 判例列表 (results[])
- 按 relevance_score 降序
- 每条卡片:
  - 案号 (粗体) + 案由 (灰色小字)
  - 法院 + 程序 + 裁判日期
  - 当事人 + 标的金额
  - 裁判结果标签 (彩色 chip: 原告胜诉=绿 / 部分支持=黄 / 被告胜诉=红 / 调解=蓝)
  - 裁判摘要 (≤ 100 字, "查看全文" 按钮跳转)
  - 争议焦点 tags
  - 来源标签 (cncases=灰 / court_cases=蓝 / lawyer_added=金)
  - 底部: "📌 收藏" + "📋 加入证据" + "🔗 查看原文"

### 3.6 强制免责声明 (页面底部固定)
> 以上数据仅为已公开裁判文书的统计结果, 不代表对本案结果的任何预测或判断。

- 桌面端: 灰色小字 + 顶部细线分隔
- 移动端: 折叠版: "以上数据为已公开裁判文书的统计结果, 不代表本案预测。"

---

## 4. 错误状态

| 场景 | UI 表现 |
|---|---|
| 样本 = 0 | 灰色空状态: "未检索到匹配类案。\n建议: 扩大检索条件 / 跳转公开查询 (联邦模式)" + 跳转按钮 |
| 检索超时 | Toast: "检索超时, 已自动降级到 metadata 检索, 请稍后重试。" |
| LLM narrative 违规 3 次 | 静默使用降级模板, UI 不显示 |

---

## 5. 性能预算

| 指标 | 目标 | 实测 |
|---|---|---|
| 页面打开到可输入 | < 500ms | W7 实测 |
| 点击"检索类案"到结果展示 | < 1.5s (含 P95 < 1s 后端) | W7 实测 |
| 滚动 50 件结果流畅度 | 60fps |  |

---

## 6. 与 Skill Hub 的集成

- 入口: Skill Hub > 我的 Skill > 已启用 (默认启用, 可手动关闭)
- 历史: Skill Hub > 类案检索 > 检索历史 (最近 20 条)
- 收藏: 跨 3 库 (cases / laws / companies), 用现有 favorites API

---

## 7. 关联文档

- `manifest.json` (agentskills.io 标准)
- `schemas/input.json` / `schemas/output.json`
- `prompt.md` (LLM system prompt)
- `language_policy.md` (界面语言规范)
- `disclaimer.md` (强制免责声明)
- `retrieval.py` (后端算法)
- `tests/test_caselaw_skill.py` (13 项测试)

---

## 8. 待办

| # | 项 | 负责人 | 截止 |
|---|---|---|---|
| 1 | UI 设计稿 (Figma) | lex-design | W7 Day 2 |
| 2 | 律师顾问评审 (≥ 3 人) | lex-pm + 律师 | W8 |
| 3 | UI 端语言规范自检 (集成 test_language_guard) | lex-coder | W7 Day 4 |
| 4 | 移动端适配 | lex-design | W7 Day 5 |

---

> **最后更新**: 2026-06-29 · lex-ai · 等待 lex-design 反馈