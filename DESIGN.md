<!-- Do not edit directly. Run `bun run spec:gen` to regenerate. -->
---
version: "1.0"
name: LexPrime 元枢法智
description: AI 赋能诉讼案件管理系统设计规范
colors:
  primary: "#165DFF"
  primary-light: "#4080FF"
  primary-bg: "#E8F3FF"
  secondary: "#4E5969"
  neutral: "#F2F3F5"
  neutral-light: "#F7F8FA"
  neutral-border: "#E5E6EB"
  text-primary: "#1D2129"
  text-secondary: "#4E5969"
  text-muted: "#86909C"
  success: "#00B42A"
  warning: "#FF7D00"
  danger: "#F5222D"
  danger-bg: "#FFF7F8"
typography:
  font-sans:
    fontFamily: "PingFang SC, SF Pro Text, Helvetica Neue, Helvetica, Arial, sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.6
  font-heading:
    fontFamily: "PingFang SC, SF Pro Text, Helvetica Neue, Helvetica, Arial, sans-serif"
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1.4
  font-label:
    fontFamily: "PingFang SC, SF Pro Text, Helvetica Neue, Helvetica, Arial, sans-serif"
    fontSize: 13px
    fontWeight: 500
    lineHeight: 1.4
  font-small:
    fontFamily: "PingFang SC, SF Pro Text, Helvetica Neue, Helvetica, Arial, sans-serif"
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.5
  font-micro:
    fontFamily: "PingFang SC, SF Pro Text, Helvetica Neue, Helvetica, Arial, sans-serif"
    fontSize: 11px
    fontWeight: 400
    lineHeight: 1.4
  font-editor:
    fontFamily: "Inter, sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.6
rounded:
  none: 0px
  sm: 4px
  md: 8px
  lg: 12px
  xl: 16px
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
  xxl: 32px
  sidebar-width: 240px
  header-height: 48px
  footer-height: 28px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: "8px 16px"
    fontSize: 14px
    fontWeight: 500
  button-primary-hover:
    backgroundColor: "{colors.primary-light}"
  button-secondary:
    backgroundColor: "#FFFFFF"
    borderColor: "{colors.neutral-border}"
    textColor: "{colors.secondary}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  button-secondary-hover:
    backgroundColor: "{colors.neutral}"
  card:
    backgroundColor: "#FFFFFF"
    borderColor: "{colors.neutral-border}"
    borderRadius: "{rounded.lg}"
    padding: 24px
  card-hover:
    boxShadow: "0 4px 10px rgba(0, 0, 0, 0.06)"
  sidebar-item:
    height: 40px
    padding: "0 16px"
    borderRadius: "{rounded.sm}"
    textColor: "{colors.secondary}"
    backgroundColor: "transparent"
  sidebar-item-hover:
    backgroundColor: "{colors.neutral}"
  sidebar-item-active:
    backgroundColor: "{colors.primary-bg}"
    textColor: "{colors.primary}"
    fontWeight: 500
  tab-btn:
    padding: "6px 0"
    fontSize: 13px
    fontWeight: 500
    borderRadius: "{rounded.md}"
    textColor: "{colors.text-muted}"
  tab-btn-active:
    backgroundColor: "#FFFFFF"
    textColor: "{colors.primary}"
    boxShadow: "0 1px 2px rgba(0,0,0,0.06)"
---

# LexPrime 元枢法智 - 设计规范

## Overview

LexPrime 元枢法智是一款面向律师和法律从业者的 AI 赋能诉讼案件管理系统。设计风格以**专业、高效、可信赖**为核心价值，采用现代简洁的界面设计，通过清晰的色彩层次和结构化的布局帮助用户高效管理案件、文档和日程。

**品牌调性**：专业权威、技术先进、简洁高效
**目标用户**：律师、法律助理、当事人
**情感定位**：值得信赖的法律科技助手

## Colors

系统采用 Arco Design 设计语言，主色调为蓝色系，辅以中性灰和语义色，整体风格清新专业。

### 主色（Primary）

- **品牌蓝 (#165DFF)**：用于主要按钮、链接、选中状态和重点强调
- **浅蓝 (#4080FF)**：用于悬停状态和次要强调
- **蓝色背景 (#E8F3FF)**：用于选中项背景、标签背景等

### 中性色（Neutral）

- **页面背景 (#F2F3F5)**：页面背景色，营造层次感
- **卡片背景 (#FFFFFF)**：内容卡片纯白背景
- **边框色 (#E5E6EB)**：卡片、按钮、输入框边框
- **深色文字 (#1D2129)**：标题、重要文字
- **正文文字 (#4E5969)**：正文内容
- **次要文字 (#86909C)**：辅助说明、时间戳等

### 语义色（Semantic）

- **成功 (#00B42A)**：完成状态、正确操作
- **警告 (#FF7D00)**：待处理、提醒
- **危险 (#F5222D)**：错误、删除、冲突

## Typography

系统采用 **PingFang SC** 作为默认中文字体，**Inter** 用于代码编辑器区域。

### 字体层级

- **标题 (16px/600)**：卡片标题、模块标题
- **正文 (14px/400)**：主要内容、按钮文字
- **标签 (13px/500)**：侧边栏菜单、Tab 切换
- **辅助 (12px/400)**：表格内容、说明文字
- **微文 (11px/400)**：时间戳、元数据

### 字体族

```yaml
fontFamily: "PingFang SC, SF Pro Text, Helvetica Neue, Helvetica, Arial, sans-serif"
```

编辑器区域使用 Inter 字体以提高代码可读性。

## Layout

系统采用经典的三栏布局：顶部导航 + 左侧边栏 + 主内容区 + 底部状态栏。

### 页面结构

| 区域 | 尺寸 | 说明 |
|------|------|------|
| 顶部导航 | 48px 固定高度 | Logo、搜索、通知、用户信息 |
| 左侧边栏 | 240px 固定宽度 | 标签切换 + 导航菜单 |
| 主内容区 | flex-1 自适应 | 视图内容区域 |
| 底部状态栏 | 28px 固定高度 | 同步状态、版本信息 |

### 间距系统

基于 4px 基准网格的 8px 间距系统：

- `xs`: 4px - 微调间距
- `sm`: 8px - 紧凑间距
- `md`: 12px - 标准间距
- `lg`: 16px - 宽松间距
- `xl`: 24px - 卡片内边距
- `xxl`: 32px - 区块间距

### 容器最大宽度

内容区域使用 `max-w-5xl` (1024px) 或 `max-w-4xl` (896px) 限制最大宽度，保证阅读舒适性。

## Elevation & Depth

系统采用**轻量阴影**实现层次感，阴影柔和且不突兀。

### 卡片阴影

```css
/* 默认卡片 */
box-shadow: none;

/* 悬停状态 */
box-shadow: 0 4px 10px rgba(0, 0, 0, 0.06);
```

### 弹出层阴影

菜单、下拉框等使用轻微阴影：

```css
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
```

### 玻璃态效果

部分场景使用毛玻璃效果：

```css
background: rgba(255, 255, 255, 0.8);
backdrop-filter: blur(10px);
```

## Shapes

系统采用统一的圆角系统，从锐利到圆润分为多个层级。

### 圆角规范

| 级别 | 尺寸 | 适用场景 |
|------|------|----------|
| none | 0px | 无圆角 |
| sm | 4px | 侧边栏选中指示器 |
| md | 8px | 按钮、输入框、小卡片 |
| lg | 12px | 主卡片、模态框 |
| xl | 16px | 大型容器 |
| full | 9999px | 头像、标签 |

### 形状设计原则

- **卡片**：12px 圆角，营造温和友好的视觉感受
- **按钮**：8px 圆角，与卡片保持一致的圆润感
- **输入框**：8px 圆角，与按钮风格统一
- **头像**：完全圆形 (full)，突出人物标识

## Components

### 按钮

#### 主按钮

```html
<button class="bg-[#165DFF] text-white px-4 py-2 rounded-lg">
  主操作
</button>
```

- 背景：#165DFF
- 文字：白色
- 圆角：8px
- 内边距：8px 16px
- 悬停：背景变浅 (#4080FF)

#### 次要按钮

```html
<button class="bg-white border border-[#E5E6EB] text-[#4E5969] px-4 py-2 rounded-lg">
  次要操作
</button>
```

- 背景：白色
- 边框：#E5E6EB
- 文字：#4E5969
- 悬停：背景变灰 (#F2F3F5)

#### 文字按钮

```html
<button class="text-[#165DFF] hover:bg-blue-50 px-3 py-1.5">
  文字链接
</button>
```

### 卡片

```html
<div class="bg-white rounded-xl border border-[#E5E6EB] p-6">
  卡片内容
</div>
```

- 背景：白色
- 边框：1px solid #E5E6EB
- 圆角：12px
- 内边距：24px
- 悬停：添加轻微阴影

### 侧边栏菜单项

```html
<div class="sidebar-item active">
  <iconify-icon icon="mdi:xxx"></iconify-icon>
  <span>菜单文字</span>
</div>
```

- 高度：40px
- 内边距：0 16px
- 圆角：4px
- 选中态：左侧 3px 蓝色指示条 + 浅蓝背景

### Tab 切换

```html
<button class="tab-btn active">标签1</button>
<button class="tab-btn">标签2</button>
```

- 选中态：白色背景 + 蓝色文字 + 轻微阴影
- 未选中：透明背景 + 灰色文字
- 圆角：6px

### 输入框

```html
<input class="w-full bg-[#F2F3F5] border-transparent focus:bg-white focus:border-[#165DFF] rounded-lg py-1.5 px-4">
```

- 背景：#F2F3F5
- 聚焦：背景变白 + 蓝色边框
- 圆角：8px
- 内边距：6px 16px

### 表格

```html
<table class="w-full text-sm">
  <thead class="bg-[#F7F8FA]">
    <th>表头</th>
  </thead>
  <tbody>
    <tr class="border-b border-[#E5E6EB]">
      <td>内容</td>
    </tr>
  </tbody>
</table>
```

- 表头：#F7F8FA 背景
- 边框：1px solid #E5E6EB
- 行高：44px（紧凑）
- 悬停：整行背景变灰

### 模态框

```html
<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
  <div class="bg-white rounded-xl w-full max-w-lg p-6">
    模态框内容
  </div>
</div>
```

- 遮罩：黑色 50% 透明度
- 容器：白色背景、12px 圆角
- 最大宽度：lg (672px) 或 md (512px)
- 内边距：24px

### Toast 提示

```html
<div class="fixed top-4 right-4 bg-white rounded-lg shadow-lg p-4 animate-slide-in">
  提示内容
</div>
```

- 位置：右上角
- 动画：从右侧滑入 (0.3s ease-out)

## Do's and Don'ts

### Do

- ✅ 使用品牌蓝 (#165DFF) 作为主要交互元素
- ✅ 保持卡片内边距一致 (24px)
- ✅ 按钮和输入框使用统一的 8px 圆角
- ✅ 使用语义色表达状态（成功=绿、警告=橙、危险=红）
- ✅ 侧边栏菜单使用 40px 标准高度
- ✅ 使用 4px 基准网格的间距系统
- ✅ 重要操作使用主按钮样式

### Don't

- ❌ 不要混用不同的蓝色调，只使用规范的两种蓝色
- ❌ 不要在页面背景上直接放内容，使用卡片容器
- ❌ 不要使用过大的阴影，保持轻量感
- ❌ 不要混用不同的圆角级别
- ❌ 不要在正文中使用纯黑色 (#000000)
- ❌ 不要过度使用危险色，仅用于删除等不可逆操作
- ❌ 不要在表格中使用过小的字体（最小 12px）

## Iconography

系统使用 **Iconify** 图标库，配合 **Material Design Icons (MDI)** 图标集。

### 常用图标

| 场景 | 图标名称 | 示例 |
|------|----------|------|
| 首页/工作台 | `mdi:view-dashboard-outline` | 首页入口 |
| 案件管理 | `mdi:briefcase-outline` | 案件列表 |
| 日程管理 | `mdi:calendar-month-outline` | 日历视图 |
| 客户管理 | `mdi:account-group-outline` | 客户列表 |
| 文档 | `mdi:file-document-outline` | 文档管理 |
| 知识库 | `mdi:bookshelf` | 知识库 |
| 添加 | `mdi:plus` | 新增按钮 |
| 编辑 | `mdi:pencil-outline` | 编辑操作 |
| 删除 | `mdi:delete-outline` | 删除操作 |
| 预览 | `mdi:eye-outline` | 预览操作 |
| 下载 | `mdi:download-outline` | 下载操作 |
| 搜索 | `mdi:magnify` | 搜索框 |
| 通知 | `mdi:bell-outline` | 通知图标 |
| 设置 | `mdi:cog-outline` | 设置入口 |

### 图标使用规范

- 图标尺寸统一为 20-24px
- 图标颜色与文字颜色保持一致
- 重要图标可使用品牌蓝 (#165DFF)
- 辅助图标使用中性灰 (#86909C)

## Animation

系统使用微妙的过渡动画提升用户体验，但不追求过度动画效果。

### 过渡时长

| 类型 | 时长 | 适用场景 |
|------|------|----------|
| 快速 | 0.15s | 悬停状态、按钮点击 |
| 标准 | 0.2s | 卡片悬停、菜单展开 |
| 缓慢 | 0.3s | 页面切换、提示出现 |

### 缓动函数

```css
transition: all 0.2s ease-in-out;
```

### 常用动画

- **菜单滑入**：`translateY(4px)` → `translateY(0)`，0.15s
- **Toast 提示**：`translateX(100%)` → `translateX(0)`，0.3s ease-out
- **卡片悬停**：轻微上移 + 阴影加深

