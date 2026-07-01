# LexPrime 设计系统 v1

> 元枢法智 (LexPrime) · 桌面端 MVP 设计规范 · v1.0 · 2026-06-28
> 适用范围: Web 端 + 桌面端 (Electron) + 内部演示原型
> 实现底座: Tailwind CSS 3 + `tailwind.config.js` 自定义 token

---

## 0. 设计原则

| # | 原则 | 体现 |
|---|------|------|
| 1 | **律师专业感** | 深蓝主色 + 灰阶中性 + 克制用色, 避免娱乐化 |
| 2 | **降低案牍焦虑** | 大量留白 + 信息密度分级 + 红黄绿灯辅助决策 |
| 3 | **现代化但不炫技** | 圆角 8px 为主 + 阴影克制 + 卡片化布局 |
| 4 | **AI 边界明示** | AI 输出必带"AI 生成"角标, 不替代律师判断 |
| 5 | **桌面优先** | 1280px+ 设计基准, 关键模块 1440px 宽屏优化 |

---

## 1. 品牌色 (Brand Colors)

### 1.1 主品牌色 — 深蓝 (Primary)

| Token | HEX | 用途 |
|-------|-----|------|
| `brand` | `#165DFF` | 主操作色 / 选中态 / 主按钮 / 主链接 |
| `brand-hover` | `#4080FF` | hover 态 |
| `brand-active` | `#0E4AD8` | active / focus 态 |
| `brand-tint` | `#E8F3FF` | 弱化背景 / 选中行底色 |
| `brand-tint2` | `#EEF3FF` | 极浅背景 |
| `brand-tint3` | `#F2F7FF` | 更浅背景 / hover 弱提示 |
| `brand-tint4` | `#E5EBFF` | hover 态浅背景 |

> **铁律**: 选中态 = `bg-brand text-white` (深蓝底白字), 不得使用浅蓝底深蓝字模拟"选中"。

### 1.2 辅助品牌色 — 浅蓝 (Accent)

`brand-tint` 是浅蓝弱化色, 用于:
- 次要按钮底色
- 信息卡片背景
- 标签 (Tag) 弱化版
- 当前选中行底色 (如案件列表第一行)

---

## 2. 中性色 (Neutral / Gray Scale)

### 2.1 灰阶 5 级 (从浅到深)

| Level | Token | HEX | 用途 |
|-------|-------|-----|------|
| G1 | `bg-subtle` | `#F7F8FA` | 页面背景 / 二级底色 |
| G2 | `bg` | `#F2F3F5` | 分组底色 / 卡片悬浮 |
| G3 | `bg-border` | `#E5E6EB` | 分割线 / 边框 / 输入框 |
| G4 | `fg-disabled` | `#C9CDD4` | 禁用文字 / 占位符 |
| G5 | `fg-tertiary` | `#86909C` | 辅助说明文字 |
| G6 | `fg-secondary` | `#4E5969` | 次要正文 |
| G7 | `fg-primary` | `#1D2129` | 主要正文 / 标题 |

> 灰阶不是简单线性, 而是按视觉权重 (font-size + line-height + 字重) 反向校准的"功能性灰阶"。

---

## 3. 状态色 (Status Colors)

| 语义 | Token | HEX | 浅底 |
|------|-------|-----|------|
| 成功 | `success` | `#00B42A` | `success-tint` `#E8FFEA` |
| 警告 | `warning` | `#FF7D00` | `warning-tint` `#FFF7E6` |
| 危险 | `danger` | `#F5222D` | `danger-tint` `#FFF1F0` |
| 紧急 | `urgent` | `#FA8C16` | `urgent-tint` `#FFF3E0` |

**使用规则**:
- 红 = 法定红线 (上诉期 / 答辩期 / 执行时效届满)
- 黄 = 重要节点 (开庭前 7/3/1 天)
- 橙 = 待办超期
- 绿 = 完成 / 归档

---

## 4. 业务色 (Domain Colors)

| Token | HEX | 用途 |
|-------|-----|------|
| `wiki` | `#9333EA` | 知识库模块 |
| `ai` | `#6C5CE7` | AI 对话 / 生成内容标识 |
| `wechat` | `#07C160` | 微信登录 / 社交分享 |

---

## 5. 字体体系 (Typography)

### 5.1 字体栈

```css
font-family: -apple-system, BlinkMacSystemFont, "PingFang SC",
             "Microsoft YaHei", "Segoe UI", Roboto, sans-serif;
```

### 5.2 字号体系 (6 档)

| Token | Size | Line-height | 字重 | 用途 |
|-------|------|-------------|------|------|
| `xs` | 12px | 20px | 400 | 辅助说明 / 标签 / 占位符 |
| `sm` | 14px | 22px | 400 | 正文 (默认) |
| `base` | 16px | 24px | 500 | 强调正文 / 重要表单 |
| `lg` | 20px | 28px | 600 | 小标题 / 卡片标题 |
| `xl` | 24px | 32px | 600 | 模块大标题 |
| `2xl` | 32px | 40px | 700 | 数据数字 / 统计 |

### 5.3 字重

| Token | Weight | 用途 |
|-------|--------|------|
| `font-normal` | 400 | 正文 |
| `font-medium` | 500 | 强调正文 / 按钮 |
| `font-semibold` | 600 | 标题 |
| `font-bold` | 700 | 大数字 / 重要标识 |

---

## 6. 间距体系 (Spacing)

### 6.1 基础间距 (8 档, 4px 基线)

| Token | px | 用途 |
|-------|----|----|
| `1` | 4 | 极小间距 (图标内边距) |
| `2` | 8 | 紧凑间距 (标签内) |
| `3` | 12 | 表单内元素 |
| `4` | 16 | 卡片内边距 (标准) |
| `6` | 24 | 模块内边距 / 卡片间 |
| `8` | 32 | 大模块间距 |
| `12` | 48 | 页面区块 |
| `18` | 72 | 巨型留白 (hero / 欢迎页) |

### 6.2 圆角 (Border Radius)

| Token | px | 用途 |
|-------|----|----|
| `rounded-sm` | 4 | 标签 / 徽章 |
| `rounded` (default) | 6 | 输入框 / 小按钮 |
| `rounded-md` | 8 | 按钮 / 卡片 (默认) |
| `rounded-lg` | 12 | 大卡片 / 模态框 |
| `rounded-xl` | 16 | Hero / 欢迎区 |
| `rounded-full` | 9999 | 头像 / 状态点 |

---

## 7. 阴影 (Shadow)

| Token | CSS | 用途 |
|-------|-----|------|
| `shadow-sm` | `0 1px 2px rgba(29,33,41,0.04)` | 输入框 / 静态悬浮 |
| `shadow` | `0 2px 8px rgba(29,33,41,0.06)` | 卡片默认 |
| `shadow-md` | `0 4px 12px rgba(29,33,41,0.08)` | 卡片悬浮 / 下拉 |
| `shadow-lg` | `0 8px 24px rgba(29,33,41,0.12)` | 模态框 / 弹层 |
| `shadow-xl` | `0 16px 48px rgba(29,33,41,0.16)` | 重要弹窗 (立案预审报告) |

---

## 8. 组件规范

### 8.1 按钮 (Button)

```
主按钮: bg-brand text-white hover:bg-brand-hover active:bg-brand-active
次按钮: bg-white text-fg-primary border border-bg-border hover:border-brand hover:text-brand
危险按钮: bg-danger text-white hover:opacity-90
文字按钮: text-brand hover:bg-brand-tint px-2 py-1
图标按钮: w-8 h-8 rounded-md hover:bg-brand-tint text-fg-secondary hover:text-brand

尺寸: sm h-7 px-2 text-xs / md h-9 px-4 text-sm / lg h-11 px-6 text-base
圆角: rounded-md (8px)
禁用: opacity-50 cursor-not-allowed
```

### 8.2 输入框 (Input)

```
默认:  h-9 px-3 text-sm bg-white border border-bg-border rounded-md
聚焦:  ring-2 ring-brand/20 border-brand
错误:  border-danger focus:ring-danger/20
占位符: text-fg-tertiary
前缀/后缀图标: text-fg-tertiary, h-9 w-9 flex items-center justify-center
```

### 8.3 卡片 (Card / arco-card)

```
基础:  bg-white rounded-md shadow p-4
悬浮:  hover:shadow-md transition-shadow
带标题: 顶部 px-4 py-3 border-b border-bg-border, 底部 px-4 py-3
内嵌: bg-bg-subtle rounded-md p-3 (嵌套卡片用浅底)
```

### 8.4 模态框 (Modal)

```
背景遮罩: bg-black/40 backdrop-blur-sm
容器: bg-white rounded-lg shadow-xl max-w-lg mx-auto
头部: px-6 py-4 border-b border-bg-border flex justify-between items-center
正文: px-6 py-4
底部: px-6 py-4 border-t border-bg-border flex justify-end gap-2
```

### 8.5 标签 (Tag)

```
默认:  inline-flex items-center px-2 py-0.5 rounded-sm text-xs font-medium
普通:  bg-bg-subtle text-fg-secondary
品牌:  bg-brand-tint text-brand
成功:  bg-success-tint text-success
警告:  bg-warning-tint text-warning
危险:  bg-danger-tint text-danger
可关闭: 加 × icon, hover 整 tag 变深
```

### 8.6 选中态 (Active State) — 全局铁律

**任何列表 / 菜单 / Tab 的选中态, 统一使用深蓝底白字**:

```
选中:   bg-brand text-white shadow-sm
未选中: text-fg-secondary hover:bg-brand-tint hover:text-brand
```

> **禁止**用浅蓝底深蓝字 (如 `bg-brand-tint text-brand`) 模拟选中——那只是"hover 预览",不是真选中。

---

## 9. 图标 (Icons)

- **来源**: Iconify (`https://api.iconify.design`)
- **风格**: Material Design Icons (`mdi:*`) 为主
- **尺寸**: `text-base` (16) 默认 / `text-sm` (14) 紧凑 / `text-xl` (20) 强调
- **颜色**: 继承文字颜色 (`currentColor`)

---

## 10. 布局基线

| 维度 | 值 |
|------|-----|
| 桌面最小宽度 | 1280px |
| 标准设计基准 | 1440px |
| 左侧栏宽度 | 220px (展开) / 64px (折叠) |
| 顶部栏高度 | 56px |
| 内容区内边距 | 24px |
| 卡片间距 | 12px |
| 栅格 | 12 列, gap 12px |

---

## 11. 动效 (Motion)

| 场景 | 时长 | 缓动 |
|------|------|------|
| hover 过渡 | 150ms | ease-out |
| 模态框进入 | 200ms | ease-out |
| 抽屉滑入 | 250ms | ease-out |
| 数字滚动 | 600ms | ease-in-out |
| 列表项进入 | 200ms + 50ms*index | ease-out |

---

## 12. AI 内容标识 (LexPrime 差异化)

任何 AI 生成的内容, **必须**带 `ai` 紫色角标:

```html
<div class="flex items-center gap-1">
  <iconify-icon icon="mdi:sparkles" class="text-ai"></iconify-icon>
  <span class="text-xs text-ai font-medium">AI 生成</span>
</div>
```

底部强制免责声明: "AI 生成内容仅供参考, 不构成法律意见, 最终判断以执业律师为准。"

---

## 13. 适配检查清单

设计交付前, 自查:

- [ ] 主色仅用 `#165DFF`, 无第二主色
- [ ] 选中态统一深蓝底白字
- [ ] 灰阶只用 5-7 级
- [ ] 字号只用 6 档 (`xs/sm/base/lg/xl/2xl`)
- [ ] 圆角三档 (`sm/md/lg`)
- [ ] 阴影 5 档, 不滥用
- [ ] AI 内容带角标 + 免责声明
- [ ] 红黄绿三色仅用于状态语义, 不作装饰
- [ ] 信息密度: 桌面端卡片内边距 ≥ 16px
- [ ] 所有交互元素键盘可达 (Tab 顺序 + focus ring)

---

**附录: Tailwind 集成示例**

```js
// tailwind.config.js (已落地)
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: '#165DFF', hover: '#4080FF', active: '#0E4AD8',
                 tint: '#E8F3FF', tint2: '#EEF3FF', tint3: '#F2F7FF', tint4: '#E5EBFF' },
        bg: { DEFAULT: '#F2F3F5', subtle: '#F7F8FA', border: '#E5E6EB' },
        fg: { primary: '#1D2129', secondary: '#4E5969', tertiary: '#86909C', disabled: '#C9CDD4' },
        success: '#00B42A', warning: '#FF7D00', danger: '#F5222D', urgent: '#FA8C16',
      },
      fontSize: { xs: '12px', sm: '14px', base: '16px', lg: '20px', xl: '24px', '2xl': '32px' },
    },
  },
}
```

---

> 维护人: lex-design (UI 设计师) · 协作: lex-coder / lex-pm
> 评审节奏: 双周 1 次, 律师顾问 3-5 人
> v1.0 评审目标: 2026-07 中