# Skill 2 合同风险审查 · UI v1 设计

> **LexPrime · 合同风险审查 Skill 2 (Track E) · UI v1 设计稿**
> **Owner**: lex-design · **Reviewer**: lex-pm + 律师顾问 (内部 v1, 律师 W6 实地评审)
> **Status**: W4 设计交付 (W5 lex-coder 实施, W6 律师实地评审)
> **更新**: 2026-06-29

---

## 1. 设计目标

### 1.1 业务目标

**Skill 2 (合同风险审查)** 是 LexPrime Skill Hub 中的核心 Track E Skill, 对律师上传的合同文本进行:

1. **逐条审查** + **三级风险标注** (致命 / 重大 / 建议)
2. **法条关联** (30+ 条 民法典 / 民诉法 / 司法解释)
3. **修改建议** (致命/重大必填, 含修改后条款模板)
4. **谈判策略** (优先级 + 杠杆 + 红线 + 立场建议)
5. **导出 / 发送** (Word / PDF / 邮件)

### 1.2 UI 设计目标

| # | 目标 | 体现 |
|---|------|------|
| 1 | **降低案牍焦虑** | 红黄蓝绿灯 (4 灯) + 风险条可视化, 律师一眼判断风险等级 |
| 2 | **律师专业感** | 风险条款级高亮 + 法条引用 + 历史样本, 体现严谨 |
| 3 | **AI 边界明示** | 所有 AI 生成内容带紫色 `mdi:sparkles` 角标 + 强制免责声明 |
| 4 | **立场感知** | 4 立场 (甲方/乙方/丙方/审查方) 切换, 风险等级 + 策略方向动态调整 |
| 5 | **降低误判风险** | 0 禁用词 (必败/必胜), 客观风险描述, 强制 disclaimer 兜底 |

---

## 2. 设计交付物 (5 页面 + 1 README + 1 评审)

| # | 文件 | 角色 | 行数 | 状态 |
|---|------|------|------|------|
| 1 | `01-upload.html` | 上传页 (上传合同 + 立场 + 启动) | ~430 行 | ✅ |
| 2 | `02-review-result.html` | 审查结果页 (风险高亮 + 条款定位) | ~700 行 | ✅ |
| 3 | `03-suggestion-detail.html` | 修改建议详情 (条款级 + 法条 + 历史) | ~530 行 | ✅ |
| 4 | `04-negotiation.html` | 谈判策略弹窗 (4 大策略 + 历史案例) | ~480 行 | ✅ |
| 5 | `05-export.html` | 导出报告 (Word/PDF + 邮件律师) | ~520 行 | ✅ |
| 6 | `README.md` | 设计说明 (本文) | - | ✅ |
| 7 | `review-by-lawyer.md` | 律师评审反馈整理 | - | ✅ |

**总计**: 5 HTML 高保真原型 (Tailwind CDN 单文件) + 2 Markdown 文档

---

## 3. 信息架构 (5 页面流程)

```
[01-upload] (上传合同 + 选择立场)
    ↓
[02-review-result] (审查结果 · 红黄蓝绿 4 灯 + 三级高亮)
    ├─→ [03-suggestion-detail] (修改建议详情 · 条款级)
    │       └─→ 法条 + 历史样本 + Diff 视图
    └─→ [04-negotiation] (谈判策略弹窗 · 4 大策略)
            └─→ 红线条款 + 立场建议 + 历史案例
    ↓
[05-export] (导出报告 · Word/PDF + 邮件律师)
```

### 3.1 5 页面职责

| 页面 | 核心职责 | 关键交互 |
|------|----------|----------|
| **01-upload** | 收集合同输入 (文件/文本/OCR/URL) + 8 大类合同类型 + 4 立场 + 可选字段 | 拖拽上传 + 立场选择 + 高级选项 |
| **02-review-result** | 4 灯 + 风险条 + 整体汇总 + 6 项风险条款卡片 | 条款级颜色高亮 + 悬浮提示 + 锚点导航 |
| **03-suggestion-detail** | 原始条款 vs AI 修改建议 + Diff + 法条 + 历史样本 | 采用 / 编辑后采用 / 忽略 + 关联类案 |
| **04-negotiation** | 优先条款 + 谈判筹码 + 红线 + 立场建议 + 历史案例 | 应用到报告 + 保存为方案 |
| **05-export** | Word 预览 + 格式选择 + 报告配置 + 邮件律师 | 下载 / 发送 / 保存到案件 |

---

## 4. 风险高亮规范 (核心)

### 4.1 三级 + 合规 配色

| 风险等级 | Token | 边框 | 卡片背景 | 标签色 | Icon |
|----------|-------|------|----------|--------|------|
| **致命 fatal** | `danger` (#F5222D) | 3px solid #F5222D | `linear-gradient(to right, #FFF1F0 0%, #FFFFFF 30%)` | bg-danger text-white | `mdi:alert-octagon` |
| **重大 major** | `warning` (#FF7D00) | 3px solid #FF7D00 | `linear-gradient(to right, #FFF7E6 0%, #FFFFFF 30%)` | bg-warning text-white | `mdi:alert-circle` |
| **建议 advisory** | `brand` (#165DFF) | 3px solid #165DFF | `linear-gradient(to right, #E8F3FF 0%, #FFFFFF 30%)` | bg-brand text-white | `mdi:lightbulb-on-outline` |
| **合规 ok** | `success` (#00B42A) | 3px solid #00B42A | 透明 / 极浅 | bg-success-tint text-success | `mdi:check-circle` |

### 4.2 条款内文字级高亮 (悬浮提示)

- **致命文字**: `bg-danger/20 border-b-2 border-danger` (深红实下划线)
- **重大文字**: `bg-warning/20 border-b-2 border-warning` (橙色实下划线)
- **建议文字**: `bg-brand/20 border-b-2 border-dotted border-brand` (深蓝虚线下划线)

鼠标悬浮 → Tooltip 显示风险类型 + 法条引用 + 风险描述 (前 100 字)

### 4.3 红黄蓝绿 4 灯 (顶部固定)

- **🔴 致命 (1)**: 红点 + 红色 2xl 数字
- **🟡 重大 (2)**: 橙点 + 橙色 2xl 数字
- **🔵 建议 (3)**: 蓝点 + 蓝色 2xl 数字
- **🟢 合规 (10)**: 绿点 + 绿色 2xl 数字

可视化: 风险条按比例显示 4 灯宽度, 律师一眼看出风险占比。

---

## 5. AI 内容标识 (强制)

### 5.1 AI 角标规范

```html
<span class="inline-flex items-center gap-1 text-[10px] text-ai font-medium px-1.5 py-0.5 bg-ai-tint rounded-sm">
  <iconify-icon icon="mdi:sparkles"></iconify-icon> AI 生成
</span>
```

### 5.2 出现位置

| 页面 | AI 角标位置 |
|------|-------------|
| 02 | 整体风险汇总 + 修改建议 |
| 03 | AI 修改建议 + Diff 视图 + 法条引用 + 历史样本 |
| 04 | 策略框架 + 立场建议 (4 块) + 历史案例 |
| 05 | 谈判策略摘要 |

### 5.3 强制免责声明 (5 个页面)

```html
<div class="text-[10px] text-fg-tertiary text-center py-3">
  <iconify-icon icon="mdi:alert-circle-outline" class="text-warning"></iconify-icon>
  本审查仅为基于合同文本的客观风险标注与法律依据提示,
  <strong>不构成法律意见, 更不替代律师的专业判断</strong>。
</div>
```

---

## 6. 与 W1 设计系统的一致性

| 维度 | W1 规范 | Skill 2 UI 体现 |
|------|---------|-----------------|
| 品牌色 | `#165DFF` (深蓝主) | ✅ 全部用 `bg-brand` (选中态 / 主按钮 / 风险条"建议") |
| 选中态 | `bg-brand text-white` | ✅ Tab / 立场按钮 / 合同类型 |
| 风险色 | danger/warning/success 状态色 | ✅ 致命/重大/合规 配色 (扩展 brand 给"建议"做风险色) |
| AI 色 | `ai #6C5CE7` | ✅ 紫色角标 + 谈判策略主色 |
| 字体 | PingFang SC / Microsoft YaHei | ✅ 全部页面用同一字体栈 |
| 间距 | 4/8/12/16/24/32/48px | ✅ Tailwind spacing 一致 |
| 圆角 | sm/md/lg 3 档 | ✅ 标签=sm / 按钮=md / 卡片=md / 模态框=lg |
| 阴影 | card / card-hover / lg / xl | ✅ 卡片默认 card, 悬浮 card-hover, 模态框用 shadow-xl |
| Icon | Iconify mdi:* | ✅ 全部用 mdi 系列 |
| 布局 | 1280px+ / 12 列 / 220px 左侧栏 / 56px 顶部 | ✅ 全部 5 页面统一 |
| Tailwind | CDN + 内联 config | ✅ 5 页面统一配置, 可直接复制到 lex-coder 实施 |

### 6.1 与 W1 三个原型的关系

| W1 原型 | Skill 2 复用 |
|---------|--------------|
| `workstation.html` | 左侧栏 + 顶部栏 + 内容区基础结构 |
| `case-list.html` | 列表项 + 状态 tag + 风险条样式 |
| `case-detail.html` | 5 步进度条 + Tab 切换 + 折叠详情 |

**W4 5 个页面直接基于 W1 的视觉语言**, 律师在原型评审时不会感到"突兀"。

---

## 7. 关键交互 (W5 实施重点)

### 7.1 风险高亮 (02-review-result)

- **条款级高亮**: 致命/重大/建议 三色卡片 + 左边框
- **文字级高亮**: 段落内风险关键词带下划线 + 悬浮提示
- **锚点导航**: 右侧栏"风险条款导航"快速跳转到具体条款
- **悬浮 Tooltip**: 显示风险类型 + 法条 + 风险描述 (前 100 字)

### 7.2 修改建议 (03-suggestion-detail)

- **原文 vs AI 建议**: 红色高亮原文问题段, 绿色高亮修改建议
- **Diff 视图**: `-` 删除 (红色删除线) / `+` 添加 (绿色背景)
- **采用流程**: 一键采用 / 编辑后采用 / 忽略 / 查看策略
- **关联跳转**: 法条 / 历史样本 (3 条) / 关联类案检索

### 7.3 谈判策略 (04-negotiation)

- **模态弹窗**: 1280px 宽, 90vh 高, 4 大策略分块
- **4 大策略**: 优先条款 / 谈判筹码 / 红线条款 / 立场建议
- **优先级排序**: P1 (致命) → P2/P3 (重大) → P4 (建议)
- **历史案例**: 3 条相似案例 (成功/成功/放弃), 提供数据支撑

### 7.4 导出报告 (05-export)

- **3 格式**: Word (.docx 推荐) / PDF / Markdown
- **报告配置**: 6 项可选 (含修改模板 / 含策略 / 含历史样本 / 含 Diff / 页脚 / 水印)
- **邮件律师**: 多选收件人 (chip) + 主题 + 正文 + 附件
- **预览**: Word 样式 A4 纸张, 含封面 + 风险总览 + 条款详述 + 免责声明

---

## 8. 性能预算 (W5 实施基准)

| 指标 | 目标 | 设计稿体现 |
|------|------|------------|
| 页面打开到可输入 | < 500ms | 单页 < 800 行, Tailwind CDN 内联, 首屏 < 200ms |
| 上传到 OCR 完成 | < 1s (PDF) / < 3s (图片) | 复用 Track B |
| 点击"审查合同"到结果 | < 2.5s (含 P95 < 2s 后端) | 02 头部显示"审查耗时 1.8s" |
| 滚动 50 条款流畅度 | 60fps | 虚拟滚动 / 折叠合规条款 (避免长列表) |
| 风险高亮渲染 | < 100ms | CSS 渐变 + 静态 HTML, 无 JS 计算 |
| 模态弹窗进入 | 200ms | `fade-in` 250ms 动画 (scale 0.96 → 1.0) |

---

## 9. 错误状态设计 (5 场景)

| 场景 | UI 表现 | 出现位置 |
|------|---------|----------|
| 合同类型无法识别 | 自动归类"其他" + 提示 | 01 |
| 合同无标号 | 按段落拆分 + 提示 | 02 顶部 |
| LLM narrative 违规 3 次 | 静默使用降级模板 | (后端处理) |
| 合同文本 > 50000 字 | 自动截断 + 提示 | 01 上传后 |
| 审查超时 (>2.5s) | Toast: 审查超时, 返回部分结果 | 02 加载 |

---

## 10. 移动端适配 (W5 Day 5)

- **桌面端 (1280px+)**: 7+5 / 8+4 双栏布局 (现设计稿)
- **平板 (768-1279px)**: 单栏堆叠, 右侧栏折叠到顶部
- **移动端 (<768px)**: 底部 Tab 切换 (上传 / 结果 / 策略 / 导出)

**当前 v1 优先桌面端, 移动端 W5 Day 5 适配** (与 UI_HANDOFF.md 一致)

---

## 11. 律师评审 (内部 v1, 实地 W6)

- **内部评审 (本 commit)**:
  - 评审反馈 → `review-by-lawyer.md` (整理)
  - 5 项核心问题 + 调整方案
- **实地评审 (W6)**:
  - 3-5 位律师 (单飞 1 + 小所 2 + 中所 1 + 企业法务 1)
  - 7/19-7/26 期间 (lex-pm 排期, 总指挥 42081 协调)
  - 致命/重大准确率 ≥ 85% / 修改建议实用性 ≥ 70%
  - 评审框架: `docs/skills/contract-review/review-template.md` (W4 lex-pm 交付)

---

## 12. 交付清单 (W4 末)

| 类别 | 文件 | 状态 |
|------|------|------|
| 设计稿 | `01-upload.html` | ✅ |
| 设计稿 | `02-review-result.html` | ✅ |
| 设计稿 | `03-suggestion-detail.html` | ✅ |
| 设计稿 | `04-negotiation.html` | ✅ |
| 设计稿 | `05-export.html` | ✅ |
| 设计说明 | `README.md` (本文) | ✅ |
| 律师评审 | `review-by-lawyer.md` | ✅ |
| Git commits | 3+ W4 commits | ⏳ 待 commit |

---

## 13. W5 实施交接 (给 lex-coder)

### 13.1 实施建议

1. **复用 W1 Tailwind config**: 直接复制 `tailwind.config.js` (已落地)
2. **Iconify 统一**: `mdi:*` 系列, 通过 CDN 引入
3. **5 页面组件化**:
   - 左侧栏 + 顶部栏 → 复用 W1 `workstation.html` / `case-detail.html`
   - 风险条款卡片 → 抽象为 `<ClauseCard :level="fatal|major|advisory|ok" />` 组件
   - 风险高亮 → CSS class (`.clause-fatal/major/advisory/ok`)
4. **状态管理**: 审查结果用 Pinia / Vuex, 5 页面共享 `contractId` / `clauseReviews[]`
5. **API 对接**: `output.json` schema 直接对应后端 contract_review skill

### 13.2 优先实施

1. **02-review-result.html** (核心, 三级高亮 + 条款定位)
2. **01-upload.html** (入口, 收集输入)
3. **05-export.html** (出口, Word/PDF 导出)
4. **03-suggestion-detail.html** (深度交互, 修改建议)
5. **04-negotiation.html** (弹窗, 策略展示)

### 13.3 注意事项

- **AI 角标**: 所有 AI 生成内容带紫色 `mdi:sparkles` 角标
- **强制 disclaimer**: 5 个页面底部均显示
- **风险色严格**: 致命=红 / 重大=黄 / 建议=蓝 / 合规=绿, 不可混淆
- **选中态**: `bg-brand text-white`, 不可用浅蓝底深蓝字模拟
- **可访问性**: Tab 顺序 + focus ring + 键盘可达

---

> **维护人**: lex-design (UI 设计师) · **协作**: lex-coder (W5 实施) / lex-pm (评审) / 律师 (W6 实地)
> **评审节奏**: 内部 v1 评审 (本 commit) → W5 lex-coder 实施 → W6 律师实地评审
> **v1.0 评审目标**: 2026-07 中 (W6 末)
