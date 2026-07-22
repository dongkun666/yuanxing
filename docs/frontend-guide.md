# LexPrime 元枢法智 — 前端开发文档

> 版本: v0.7.0  
> 构建日期: 2026-06-28  
> 技术栈: ES5 JavaScript (IIFE) + Tailwind CSS + GSAP 动画 + Chart.js 图表

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术栈](#2-技术栈)
3. [目录结构](#3-目录结构)
4. [页面加载流程](#4-页面加载流程)
5. [核心模块详解](#5-核心模块详解)
6. [视图导航系统](#6-视图导航系统)
7. [API 客户端层](#7-api-客户端层)
8. [认证系统](#8-认证系统)
9. [工具函数库](#9-工具函数库)
10. [动画系统](#10-动画系统)
11. [数据可视化](#11-数据可视化)
12. [移动端适配](#12-移动端适配)
13. [主题系统](#13-主题系统)
14. [插件系统](#14-插件系统)
15. [构建与部署](#15-构建与部署)
16. [开发规范](#16-开发规范)

---

## 1. 项目概述

LexPrime 元枢法智是一个 AI 赋能的法律科技平台，前端采用**传统多页面 + SPA 路由**架构。所有页面通过 `index.html` 作为唯一入口，利用 JavaScript 动态加载视图模板（HTML 片段）实现页面切换，无需刷新浏览器。

### 核心设计理念

- **IIFE 模块化**: 所有 JS 文件采用 IIFE（立即执行函数表达式）模式，通过 `globalThis` 暴露公共 API，避免全局变量污染
- **按需加载**: 视图 HTML 和 JS 脚本在切换页面时才加载，减少首屏体积
- **渐进增强**: 基础功能不依赖外部库，高级功能（动画、图表）在库可用时才启用
- **ES5 兼容**: 全部使用 ES5 语法，兼容旧浏览器

### 页面数量

| 分类 | 数量 |
|------|------|
| 视图页面 (HTML) | 81 个 |
| JS 业务模块 | 47 个 |
| CSS 样式文件 | 3 个 (tailwind.css + styles.css + marketplace.css) |

---

## 2. 技术栈

### 核心依赖

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| CSS 框架 | Tailwind CSS | 3.4.14 | 原子化 CSS 样式 |
| 图标 | Iconify (MDI) | - | 本地离线图标库 |
| 动画 | GSAP | 3.12.5 | 高性能动画引擎 |
| 动画插件 | ScrollTrigger | 3.12.5 | 滚动触发动画 |
| 图表 | Chart.js | 4.x | 数据可视化图表 |

### 开发依赖

| 类别 | 技术 | 用途 |
|------|------|------|
| 代码检查 | ESLint | JS 代码质量检查 |
| 代码格式化 | Prettier | 自动格式化代码 |
| CSS 压缩 | clean-css | 生产环境 CSS 压缩 |
| JS 压缩 | terser | 生产环境 JS 压缩 |
| 静默压缩 | gzip/brotli | 生产环境资源压缩 |

---

## 3. 目录结构

```
/workspace/
├── index.html                         # 唯一入口页面
├── index.prod.html                    # 生产环境入口（构建生成）
├── package.json                       # 项目配置
├── manifest.json                      # PWA 清单
├── service-worker.js                  # Service Worker (PWA)
├── offline.html                       # 离线回退页面
├── nginx.conf                         # Nginx 配置
├── docker-compose.yml                 # Docker 编排
├── Dockerfile.frontend                # 前端 Docker 镜像
│
├── assets/
│   ├── css/
│   │   ├── tailwind.css               # Tailwind 编译产物
│   │   ├── tailwind-input.css         # Tailwind 源文件
│   │   ├── styles.css                 # 全局自定义样式
│   │   ├── marketplace.css            # Marketplace 模块样式
│   │   └── dist/                      # 生产构建产物目录
│   │       ├── tailwind.min.css       # 压缩版 Tailwind
│   │       ├── styles.min.css         # 压缩版自定义样式
│   │       └── marketplace.min.css    # 压缩版 Marketplace 样式
│   │
│   ├── js/
│   │   ├── iconify-icon.min.js        # 图标库
│   │   ├── app-state.js               # 全局状态管理
│   │   ├── utils.js                   # 工具函数库
│   │   ├── api.js                     # API 客户端
│   │   ├── auth.js                    # 认证模块
│   │   ├── router.js                  # 路由系统
│   │   ├── script.js                  # 主业务脚本
│   │   ├── bootstrap.js               # 启动流程
│   │   ├── animations.js              # 动画系统
│   │   ├── charts.js                  # 图表组件
│   │   ├── touch.js                   # 移动端触摸
│   │   ├── onboarding.js              # 新手引导
│   │   ├── monitoring.js              # 前端监控
│   │   ├── plugin-loader.js           # 插件系统
│   │   ├── recommendation.js          # 个性化推荐
│   │   ├── marketplace.js             # Marketplace 模块
│   │   ├── contract-review.js         # 合同审查模块
│   │   ├── cases-db.js               # 判例库模块
│   │   ├── laws-db.js                # 法规库模块
│   │   ├── companies-db.js           # 企业库模块
│   │   ├── clients.js                # 客户管理模块
│   │   ├── schedule.js               # 日程管理模块
│   │   ├── archive.js                # 归档管理模块
│   │   ├── attention-list.js         # 关注列表模块
│   │   ├── attachment-list.js        # 附件列表模块
│   │   ├── templates.js              # 模板管理模块
│   │   ├── case-dynamics.js          # 案件动态模块
│   │   ├── case-progress.js          # 案件进度模块
│   │   ├── cases-list.js            # 案件列表模块
│   │   ├── cases-detail.js          # 案件详情模块
│   │   ├── cases-tabs.js            # 案件标签页模块
│   │   ├── knowledge.js             # 知识库模块
│   │   ├── ai.js                    # AI 对话模块
│   │   ├── ai-doc.js                # AI 文书模块
│   │   ├── deadline.js              # 法律期限模块
│   │   ├── zhixing.js               # 执行管理模块
│   │   ├── judicial.js              # 司法数据模块
│   │   ├── judicial-data.js         # 司法数据模块
│   │   ├── firm.js                  # 律所管理模块
│   │   ├── score-app.js             # 评审评分模块
│   │   ├── member-center.js         # 个人中心模块
│   │   ├── account-profile.js       # 账户资料模块
│   │   ├── account-subscription.js  # 账户订阅模块
│   │   ├── account-notifications.js # 账户通知模块
│   │   ├── orders.js                # 订单管理模块
│   │   ├── developer.js             # 开发者平台模块
│   │   └── dist/                     # 生产构建产物目录
│   │
│   ├── icons/
│   │   ├── mdi.json                  # Material Design 图标集
│   │   └── pwa/                      # PWA 图标 (6 种尺寸)
│   │
│   └── images/
│       └── avatar.jpg                # 默认头像
│
├── templates/
│   └── views/
│       ├── login.html                # 登录页
│       ├── workstation.html          # 工作台
│       ├── case-list.html            # 案件列表
│       ├── case-detail.html          # 案件详情
│       ├── case-analysis.html        # 案件分析
│       ├── case-dynamics.html        # 案件动态
│       ├── case-progress.html        # 案件进度
│       ├── client.html               # 客户管理
│       ├── client-detail.html        # 客户详情
│       ├── schedule-list.html        # 日程列表
│       ├── schedule-calendar.html    # 日程日历
│       ├── attention-list.html       # 关注列表
│       ├── attachment-list.html      # 附件列表
│       ├── template.html             # 模板管理
│       ├── knowledge.html            # 知识库
│       ├── ai.html                   # AI 对话
│       ├── ai-doc.html               # AI 文书
│       ├── archive.html              # 归档管理
│       ├── notifications.html        # 通知中心
│       ├── deadline.html             # 法律期限
│       ├── zhixing.html              # 执行管理
│       ├── judicial.html             # 司法数据
│       ├── firm.html                 # 律所管理
│       ├── cases-db.html             # 判例库
│       ├── laws-db.html              # 法规库
│       ├── companies-db.html         # 企业库
│       ├── onboarding.html           # 新手引导
│       ├── pricing.html              # 定价页面
│       ├── subscription.html         # 订阅管理
│       ├── payment.html              # 支付页面
│       ├── payment-success.html      # 支付成功
│       ├── orders.html               # 订单记录
│       ├── member-center.html        # 个人中心
│       ├── account-settings.html     # 账号设置
│       ├── backlog/index.html        # 待办事项
│       ├── doc-gen/index.html        # 文书生成
│       ├── doc-review/index.html     # 文书审查
│       ├── founding/index.html       # 创始体验官
│       ├── dashboard/index.html      # 运营 Dashboard
│       ├── marketplace/              # Marketplace 模块 (5 页面)
│       │   ├── lawyers.html
│       │   ├── cases.html
│       │   ├── referrals.html
│       │   ├── cross-border.html
│       │   └── metrics.html
│       ├── contract-review/          # 合同审查模块 (5 页面)
│       │   ├── contract-review-upload.html
│       │   ├── contract-review-result.html
│       │   ├── contract-review-suggestion.html
│       │   ├── contract-review-negotiation.html
│       │   └── contract-review-export.html
│       ├── review/                   # 评审模块 (2 页面)
│       │   ├── board.html
│       │   └── score-app.html
│       ├── ai-qa/index.html          # AI 法律问答
│       ├── graph/index.html          # 法律关系图谱
│       ├── risk-prediction/index.html # 风险预测
│       ├── contract-gen/index.html   # 智能合同生成
│       ├── doc-compare/index.html    # 文档对比
│       ├── collaboration/index.html  # 协作中心
│       ├── user-profile/index.html   # 用户画像
│       ├── rag-admin/index.html      # RAG 管理
│       ├── agent-playground/index.html # Agent 测试
│       ├── multimodal/index.html     # 多模态测试
│       ├── evaluation/index.html     # 模型评测
│       ├── pricing/index.html        # 定价页
│       ├── payment/index.html        # 支付页
│       ├── invite/index.html         # 邀请裂变
│       ├── growth/index.html         # 增长分析
│       ├── developer/index.html      # 开发者平台
│       ├── template-market/index.html # 模板市场
│       ├── data-market/index.html    # 数据市场
│       ├── community/index.html      # 社区
│       ├── tenant-admin/index.html   # 租户管理
│       ├── sso-settings/index.html   # SSO 设置
│       ├── audit-logs/index.html     # 审计日志
│       ├── org-admin/index.html      # 组织架构
│       ├── sla/index.html            # SLA 监控
│       ├── sla-admin/index.html      # SLA 管理
│       ├── knowledge-graph/index.html # 知识图谱
│       ├── case-db-admin/index.html  # 判例库管理
│       ├── law-db-admin/index.html   # 法规库管理
│       ├── company-db-admin/index.html # 企业库管理
│       └── lawyer-db-admin/index.html # 律师库管理
│
├── scripts/
│   ├── build.js                      # 构建脚本
│   ├── deploy.sh                     # 部署脚本
│   ├── start-frontend.sh             # 前端启动脚本
│   ├── start.sh                      # 一键启动脚本
│   ├── benchmark/                    # 性能测试工具
│   ├── security/                     # 安全测试工具
│   ├── chaos/                        # 混沌工程工具
│   ├── backup/                       # 备份恢复工具
│   ├── private-deploy/               # 私有化部署工具
│   └── data-import/                  # 数据导入工具
│
├── tests/
│   ├── utils.test.cjs               # 工具函数测试
│   ├── templates.test.cjs           # 模板测试
│   ├── schedule.test.cjs            # 日程测试
│   ├── marketplace.test.cjs         # Marketplace 测试
│   └── e2e/                          # E2E 测试
│       ├── case-lifecycle.test.js
│       ├── user-journey.test.js
│       └── collaboration-flow.test.js
│
├── docs/                             # 文档目录
│   ├── frontend-guide.md            # 本文档
│   ├── architecture.md              # 架构文档
│   ├── api.md                       # API 文档
│   ├── user-guide.md                # 用户手册
│   ├── development.md               # 开发文档
│   ├── deployment.md                # 部署文档
│   ├── domain-setup.md              # 域名配置
│   ├── performance-optimization.md  # 性能优化
│   └── private-deployment.md        # 私有化部署
│
├── marketing/
│   └── landing.html                 # 营销落地页
│
├── miniprogram/                     # 微信小程序
├── mobile-app/                      # React Native 移动应用
├── browser-extension/               # 浏览器扩展
├── integrations/                    # 企业微信/钉钉集成
├── plugins/                         # 插件系统
└── phase5-react/                    # Electron 桌面应用
```

---

## 4. 页面加载流程

### 4.1 资源加载顺序

```
index.html
├── 1. 防闪烁脚本 (内联)           — 设置 data-theme 属性
├── 2. tailwind.css                — Tailwind 原子类
├── 3. 预加载 link (preload)       — 关键 JS 文件
├── 4. DNS 预解析 (dns-prefetch)   — 后端 API 地址
├── 5. APP_VERSION 等元数据 (内联)  — 全局变量
├── 6. Iconify 本地配置 (内联)     — 图标库配置
├── 7. iconify-icon.min.js         — 图标库
├── 8. 图标集加载 (内联)           — mdi.json
├── 9. GSAP 核心库 (CDN)           — gsap.min.js
├── 10. GSAP ScrollTrigger (CDN)   — 滚动触发插件
├── 11. styles.css                 — 自定义样式
├── 12. marketplace.css            — Marketplace 样式
│
├── body > header                   — 顶部导航栏 (内联 HTML)
├── body > sidebar                  — 左侧导航栏 (内联 HTML)
├── body > main-content             — 动态内容区域 <div id="main-content">
│
├── 13. app-state.js (defer)        — 全局状态
├── 14. api.js (defer)              — API 客户端
├── 15. auth.js (defer)             — 认证模块
├── 16. utils.js (defer)            — 工具函数
├── 17. router.js (defer)           — 路由系统
├── 18. animations.js (defer)       — 动画系统
├── 19. charts.js (defer)           — 图表组件
├── 20. touch.js (defer)            — 移动端触摸
├── 21. 业务模块 (defer)            — 各业务 JS 文件
├── 22. script.js (defer)           — 主业务脚本
├── 23. 更多业务模块 (defer)        — 其余 JS 文件
├── 24. bootstrap.js (defer)        — 启动流程 (最后加载)
│
└── footer                          — 版本号显示
```

### 4.2 启动流程

```
bootstrapApp()
├── Auth.restore()                  — 从 localStorage 恢复 token 和用户信息
├── Utils._initThemeSystem()        — 初始化主题系统
├── renderAppVersion()              — 渲染底部版本号
├── switchView(getStartView())      — 根据登录状态切换到初始视图
│   ├── 已登录 → workstation
│   └── 未登录 → login
├── updateNotificationBadgeState()  — 更新通知红点
├── Utils.initShortcuts()           — 初始化全局快捷键
├── registerServiceWorker()         — 注册 Service Worker (PWA)
└── initOnlineStatus()              — 初始化在线状态检测
```

### 4.3 视图切换流程

```
switchView(viewId, el)
├── Utils.closeAllModals()          — 关闭所有打开的模态框
├── loadViewScripts(viewId)         — 按需加载视图对应的 JS 脚本
├── 检查 DOM 中是否已有 view-{viewId} 元素
│   ├── 有 → 显示该元素，隐藏其他
│   └── 无 → loadView(viewId)       — fetch HTML 模板并插入
│       ├── fetch templates/views/{fileName}
│       ├── 提取 <script> 标签单独执行
│       ├── 插入 HTML 到 main-content
│       └── 执行视图初始化函数
├── initView(viewId)                — 执行视图特定的初始化
├── initViewAnimations(target)      — 触发页面入场动画
└── smartPreload(viewId)            — 智能预加载下一个可能的视图
```

---

## 5. 核心模块详解

### 5.1 app-state.js — 全局状态管理

**文件路径**: `assets/js/app-state.js`  
**加载顺序**: 第 1 个业务 JS  
**依赖**: 无  
**暴露**: `globalThis.AppState`

```javascript
var AppState = {
    // 业务状态
    isYearly: false,              // 是否年付
    selectedPayment: 'alipay',    // 支付方式
    selectedDynamicType: '紧急',  // 动态类型筛选
    selectedExtractSource: 'case', // 提取来源
    batchFiles: [],               // 批量文件列表
    dynamicsViewData: [],         // 动态视图数据
    autoSaveTimer: null,          // 自动保存定时器
    dynamicAttachments: [],       // 动态附件
    notificationsFilter: 'all',   // 通知筛选

    // Auth 状态
    user: null,                   // 当前用户信息
    token: null,                  // JWT token

    // 错误日志
    errorLog: []                  // 全局错误日志 (上限 50 条)
};
```

### 5.2 bootstrap.js — 启动流程

**文件路径**: `assets/js/bootstrap.js`  
**加载顺序**: 最后一个业务 JS  
**依赖**: Auth, AppState, Utils, router  
**暴露**: `bootstrapApp`, `renderAppVersion`, `updateNotificationBadgeState`, `recordError`, `registerServiceWorker`, `checkSWUpdate`, `isOnline`, `showUpdateNotification`

核心函数：

| 函数 | 说明 |
|------|------|
| `bootstrapApp()` | 应用启动入口，执行 Auth 恢复、主题初始化、视图切换、通知红点、快捷键、SW 注册 |
| `getStartView()` | 根据登录状态返回初始视图 (workstation 或 login) |
| `renderAppVersion()` | 渲染底部版本号 |
| `updateNotificationBadgeState()` | 更新通知铃铛红点 |
| `recordError(type, msg, file, line, stack)` | 记录全局错误到 AppState.errorLog |
| `registerServiceWorker()` | 注册 PWA Service Worker |
| `checkSWUpdate()` | 检查 SW 更新 |
| `isOnline()` | 检测在线状态 |

### 5.3 router.js — 路由系统

**文件路径**: `assets/js/router.js`  
**加载顺序**: 在 app-state.js 之后  
**依赖**: AppState, Utils (可选)  
**暴露**: `viewCache`, `viewFileMap`, `viewScriptMap`, `isDevMode`, `loadView`, `switchView`, `switchSidebarTab`, `preloadView`, `preloadViews`, `smartPreload`

#### 视图文件名映射 (viewFileMap)

| 视图 ID | HTML 文件路径 |
|---------|-------------|
| login | `templates/views/login.html` |
| workstation | `templates/views/workstation.html` |
| case-list | `templates/views/case-list.html` |
| case | `templates/views/case-detail.html` |
| schedule-calendar | `templates/views/schedule-calendar.html` |
| schedule-list | `templates/views/schedule-list.html` |
| client | `templates/views/client.html` |
| client-detail | `templates/views/client-detail.html` |
| template | `templates/views/template.html` |
| knowledge | `templates/views/knowledge.html` |
| ai | `templates/views/ai.html` |
| archive | `templates/views/archive.html` |
| notifications | `templates/views/notifications.html` |
| deadline | `templates/views/deadline.html` |
| zhixing | `templates/views/zhixing.html` |
| case-progress | `templates/views/case-progress.html` |
| case-dynamics | `templates/views/case-dynamics.html` |
| attention-list | `templates/views/attention-list.html` |
| attachment-list | `templates/views/attachment-list.html` |
| ai-doc | `templates/views/ai-doc.html` |
| firm | `templates/views/firm.html` |
| cases-db | `templates/views/cases-db.html` |
| laws-db | `templates/views/laws-db.html` |
| companies-db | `templates/views/companies-db.html` |
| subscription | `templates/views/subscription.html` |
| payment | `templates/views/payment.html` |
| payment-success | `templates/views/payment-success.html` |
| orders | `templates/views/orders.html` |
| member-center | `templates/views/member-center.html` |
| account-settings | `templates/views/account-settings.html` |
| backlog | `templates/views/backlog/index.html` |
| doc-gen | `templates/views/doc-gen/index.html` |
| doc-review | `templates/views/doc-review/index.html` |
| founding | `templates/views/founding/index.html` |
| dashboard | `templates/views/dashboard/index.html` |
| marketplace-lawyers | `templates/views/marketplace/lawyers.html` |
| marketplace-cases | `templates/views/marketplace/cases.html` |
| marketplace-referrals | `templates/views/marketplace/referrals.html` |
| marketplace-cross-border | `templates/views/marketplace/cross-border.html` |
| marketplace-metrics | `templates/views/marketplace/metrics.html` |
| contract-review-upload | `templates/views/contract-review/contract-review-upload.html` |
| contract-review-result | `templates/views/contract-review/contract-review-result.html` |
| contract-review-suggestion | `templates/views/contract-review/contract-review-suggestion.html` |
| contract-review-negotiation | `templates/views/contract-review/contract-review-negotiation.html` |
| contract-review-export | `templates/views/contract-review/contract-review-export.html` |
| review-score-app | `templates/views/review/score-app.html` |
| review-board | `templates/views/review/board.html` |
| onboarding | `templates/views/onboarding.html` |
| pricing | `templates/views/pricing.html` |

#### 视图脚本映射 (viewScriptMap)

每个视图有对应的 JS 业务模块，切换视图时按需加载。例如：

| 视图 ID | JS 文件 |
|---------|---------|
| schedule-calendar | `./assets/js/schedule.js` |
| case | `./assets/js/cases-detail.js` |
| client | `./assets/js/clients.js` |
| template | `./assets/js/templates.js` |
| knowledge | `./assets/js/knowledge.js` |
| ai | `./assets/js/ai.js` |
| archive | `./assets/js/archive.js` |
| deadline | `./assets/js/deadline.js` |
| case-progress | `./assets/js/case-progress.js` |
| contract-review-* | `./assets/js/contract-review.js` |
| marketplace-* | `./assets/js/marketplace.js` |
| cases-db | `./assets/js/cases-db.js` |
| laws-db | `./assets/js/laws-db.js` |
| companies-db | `./assets/js/companies-db.js` |

#### 视图初始化映射 (viewInitMap)

部分视图需要特殊的初始化逻辑，统一在 `initView()` 函数中调度：

| 视图 ID | 初始化逻辑 |
|---------|----------|
| template | `fixTemplateViewDOM()` + `renderPersonalTemplates()` |
| schedule-calendar | `renderScheduleList()` + `filterScheduleByDate()` |
| schedule-list | 同上 |
| notifications | `setNotificationsFilter()` |
| review-board | `__loadReviewBoard()` |
| backlog | `__loadBacklogBoard()` |
| doc-gen | `__loadDocGenHealth()` |
| founding | `__loadFoundingView()` + `__initFoundingCountdown()` |

#### 预加载机制

```javascript
preloadView(viewId)       // 预加载单个视图 HTML + JS
preloadViews(viewIds)     // 批量预加载多个视图
smartPreload(viewId)      // 根据当前视图智能预测下一个视图并预加载
preloadCriticalResources() // 预加载首屏关键资源
```

---

## 6. 视图导航系统

### 6.1 侧边栏结构

侧边栏有两个标签页：**工作** 和 **AI 对话**

#### 工作标签页

| 菜单项 | 视图 ID | 图标 |
|--------|---------|------|
| 工作台 | workstation | mdi:view-dashboard-outline |
| 案件管理 | case-list | mdi:briefcase-outline |
| 日程管理 | schedule-calendar | mdi:calendar-month-outline |
| 客户管理 | client | mdi:account-group-outline |
| 归档管理 | archive | mdi:archive-outline |
| 模板管理 | template | mdi:file-document-outline |
| 知识库管理 | knowledge | mdi:bookshelf |
| 法律期限 | deadline | mdi:clock-alert-outline |
| 案件进度 | case-progress | mdi:gavel-clock |
| AI 文书 | ai-doc | mdi:file-document-edit-outline |
| 创始体验官 | founding | mdi:crown |
| 运营 Dashboard | dashboard | mdi:chart-line |
| Marketplace | marketplace-lawyers | mdi:scale-balance |

#### AI 对话标签页

| 菜单项 | 视图 ID | 说明 |
|--------|---------|------|
| 合同审查 | contract-review-upload | 上传合同进行审查 |
| 文书生成 | doc-gen | AI 驱动文书生成 |
| 文书审查 | doc-review | AI 文书质量审查 |
| AI 法律问答 | 跳转 ai-qa | 智能法律问答系统 |
| 法律关系图谱 | 跳转 graph | 案件关系可视化 |
| 案件风险预测 | 跳转 risk-prediction | 胜诉率风险分析 |
| 合同智能生成 | 跳转 contract-gen | 需求描述生成合同 |
| 文档对比 | 跳转 doc-compare | 多文档对比分析 |

### 6.2 顶部导航栏

```
[Logo] LexPrime 元枢法智 | [搜索框] | [帮助] [通知] | [用户头像] [用户名]
```

- **搜索框**: 全局搜索案件、文书或证据
- **帮助按钮**: 跳转到新手引导 (onboarding)
- **通知按钮**: 显示通知弹窗，支持全部已读
- **用户菜单**: 个人中心、账号设置、会员订阅、订单记录、使用引导、退出登录

### 6.3 底部状态栏

显示应用版本号 `v0.7.0`，hover 时显示构建日期和 Git SHA。

---

## 7. API 客户端层

**文件路径**: `assets/js/api.js`  
**依赖**: Auth (auth.js), Utils (utils.js)  
**暴露**: `globalThis.API`

### 7.1 后端服务配置

```javascript
const CONFIG = {
    backend: 'http://127.0.0.1:3847',    // Rust Actix-web
    aiService: 'http://127.0.0.1:8088',   // Python FastAPI
    timeoutMs: 30000,                      // 30 秒超时
    uploadTimeoutMs: 60000,                // 上传 60 秒超时
    retryCount: 2,                         // 重试次数
    retryDelayMs: 1000                     // 重试间隔
};
```

### 7.2 Loading 状态管理

`LoadingManager` 对象管理全局加载状态：

- `show()` / `hide()` — 显示/隐藏全局 loading 遮罩层
- `setButtonLoading(btn, loading)` — 设置按钮加载状态
- `getActiveCount()` — 获取当前活跃请求数

### 7.3 请求去重

`RequestDeduplicator` 对象防止重复请求：

- `check(url, options)` — 检查是否有相同请求正在执行
- `register(url, options, promise)` — 注册新请求

### 7.4 核心请求函数

`request(url, options)` — 通用请求函数，自动处理：

- Bearer Token 注入 (从 Auth.getToken())
- CSRF Token 注入 (非 GET 请求)
- 401 自动刷新 token (调用 Auth.onUnauthorized())
- 超时控制
- 幂等请求重试 (GET/HEAD/OPTIONS)
- 请求去重
- 统一错误处理

### 7.5 API 命名空间

#### API.auth — 认证相关

| 方法 | 说明 |
|------|------|
| `login(email, password)` | 邮箱密码登录 |
| `register(data)` | 用户注册 |
| `logout()` | 退出登录 |
| `demo()` | Demo 模式登录 |
| `refresh(refreshToken)` | 刷新 token |
| `me()` | 获取当前用户信息 |

#### API.cases — 案件管理

| 方法 | 说明 |
|------|------|
| `list(params)` | 案件列表 |
| `get(caseId)` | 案件详情 |
| `create(data)` | 创建案件 |
| `update(caseId, data)` | 更新案件 |
| `delete(caseId)` | 删除案件 |
| `search(query)` | 搜索案件 |

#### API.clients — 客户管理

| 方法 | 说明 |
|------|------|
| `list(params)` | 客户列表 |
| `get(clientId)` | 客户详情 |
| `create(data)` | 创建客户 |
| `update(clientId, data)` | 更新客户 |
| `delete(clientId)` | 删除客户 |

#### API.contractReview — 合同审查

| 方法 | 说明 |
|------|------|
| `upload(file)` | 上传合同文件 |
| `review(contractId)` | 审查合同 |
| `getResult(reviewId)` | 获取审查结果 |
| `getSuggestions(reviewId)` | 获取修改建议 |
| `export(reviewId, format)` | 导出审查报告 |

#### API.marketplace — 律师匹配

| 方法 | 说明 |
|------|------|
| `searchLawyers(params)` | 搜索律师 |
| `getLawyer(lawyerId)` | 律师详情 |
| `matchLawyer(caseId, criteria)` | 匹配律师 |
| `searchReferrals(params)` | 搜索案件转介 |
| `getMetrics()` | 获取市场数据 |

#### API.ai — AI 服务

| 方法 | 说明 |
|------|------|
| `summarize(text)` | 案件摘要 |
| `polish(text)` | 文书润色 |
| `fillForm(formData)` | 智能填空 |
| `qa(question)` | 法律问答 |
| `generateContract(requirements)` | 生成合同 |
| `predictRisk(caseInfo)` | 风险预测 |
| `compareDocuments(docs)` | 文档对比 |
| `extractEntities(text)` | 实体提取 |

#### API.schedule — 日程管理

| 方法 | 说明 |
|------|------|
| `list(params)` | 日程列表 |
| `create(data)` | 创建日程 |
| `update(id, data)` | 更新日程 |
| `delete(id)` | 删除日程 |

#### API.analytics — 数据分析

| 方法 | 说明 |
|------|------|
| `getDashboard()` | 仪表盘数据 |
| `getTrends(params)` | 趋势数据 |
| `getLawyerProfile(id)` | 律师画像 |
| `getCaseTypes()` | 案件类型分布 |
| `getHeatmap()` | 时间分布热力图 |

#### API.collaboration — 协作功能

| 方法 | 说明 |
|------|------|
| `getMembers()` | 团队成员列表 |
| `inviteMember(data)` | 邀请成员 |
| `getTasks()` | 任务列表 |
| `createTask(data)` | 创建任务 |
| `updateTask(id, data)` | 更新任务 |
| `getComments(targetId)` | 评论列表 |
| `addComment(data)` | 添加评论 |
| `getFiles()` | 文件列表 |
| `getPermissions()` | 权限列表 |
| `updatePermissions(data)` | 更新权限 |

#### API.recommendation — 个性化推荐

| 方法 | 说明 |
|------|------|
| `getCases()` | 推荐案件 |
| `getLawyers()` | 推荐律师 |
| `getTemplates()` | 推荐模板 |
| `feedback(data)` | 推荐反馈 |
| `refresh()` | 刷新推荐 |

#### API.subscription — 订阅管理

| 方法 | 说明 |
|------|------|
| `getPlans()` | 套餐列表 |
| `getCurrent()` | 当前订阅 |
| `subscribe(planId)` | 订阅套餐 |
| `cancel()` | 取消订阅 |
| `getInvoices()` | 账单列表 |

#### API.payment — 支付

| 方法 | 说明 |
|------|------|
| `create(data)` | 创建支付订单 |
| `getStatus(id)` | 查询支付状态 |
| `mockConfirm(id)` | Mock 支付确认 |

---

## 8. 认证系统

**文件路径**: `assets/js/auth.js`  
**依赖**: API (api.js), AppState (app-state.js)  
**暴露**: `globalThis.Auth`

### 8.1 Token 存储

```javascript
localStorage 键名:
  lexprime.token         — access_token
  lexprime.refresh_token — refresh_token
  lexprime.token_expire  — token 过期时间戳
  lexprime.auth          — 用户信息 JSON
```

### 8.2 核心方法

| 方法 | 说明 |
|------|------|
| `Auth.getToken()` | 获取当前 token |
| `Auth.getUser()` | 获取当前用户信息 |
| `Auth.isLoggedIn()` | 检查是否已登录 |
| `Auth.login(email, password)` | 邮箱密码登录 |
| `Auth.demoLogin()` | Demo 模式登录 (跳过密码) |
| `Auth.logout()` | 退出登录，清除所有 token |
| `Auth.restore()` | 从 localStorage 恢复 session |
| `Auth.register(data)` | 用户注册 |
| `Auth.refreshToken()` | 刷新 token |
| `Auth.setupAutoRefresh()` | 启动自动刷新定时器 |
| `Auth.onUnauthorized()` | 401 拦截器 |

### 8.3 自动刷新机制

- 每分钟检查一次 token 是否在 5 分钟内过期
- 过期前 5 分钟自动调用 `refreshToken()`
- 刷新成功后显示 "登录已自动续期" 提示
- 刷新失败或 token 已过期，跳转到登录页

### 8.4 401 拦截

API 层在收到 401 响应时自动调用 `Auth.onUnauthorized()`：
1. 尝试用 refresh_token 刷新 access_token
2. 刷新成功 → 重试原请求
3. 刷新失败 → 清除 session，跳转登录页

---

## 9. 工具函数库

**文件路径**: `assets/js/utils.js`  
**依赖**: 无  
**暴露**: `globalThis.Utils`

### 9.1 安全相关

| 函数 | 说明 |
|------|------|
| `Utils.escapeHtml(text)` | HTML 转义，防止 XSS (使用 DOM textContent) |
| `Utils.sanitizeHtml(html)` | HTML 净化，白名单过滤危险标签和属性 |

### 9.2 模态框

| 函数 | 说明 |
|------|------|
| `Utils.showModal(options)` | 显示统一模态框 (支持焦点陷阱、ARIA 标签、ESC 关闭) |
| `Utils.closeModal(modalId)` | 关闭指定模态框 |
| `Utils.closeAllModals()` | 关闭所有打开的模态框 |
| `Utils.showPrompt(title, content)` | 显示提示框 |
| `Utils.showConfirm(title, message, onConfirm)` | 显示确认框 |

### 9.3 通知提示

| 函数 | 说明 |
|------|------|
| `Utils.showToast(message, type)` | 显示 Toast 通知 (success/warning/error/info) |
| `Utils.showError(message)` | 显示错误提示 |

### 9.4 性能优化

| 函数 | 说明 |
|------|------|
| `Utils.debounce(fn, delay, immediate)` | 防抖函数 |
| `Utils.throttle(fn, delay)` | 节流函数 |

### 9.5 加载状态

| 函数 | 说明 |
|------|------|
| `Utils.showLoading()` | 显示全局加载状态 |
| `Utils.hideLoading()` | 隐藏全局加载状态 |

### 9.6 主题系统

| 函数 | 说明 |
|------|------|
| `Utils.setTheme(theme)` | 设置主题 (light/dark/auto) |
| `Utils.toggleTheme()` | 切换主题 |
| `Utils.getTheme()` | 获取当前主题 |
| `Utils._initThemeSystem()` | 初始化主题系统 (应用启动时调用) |

### 9.7 全局快捷键

| 函数 | 说明 |
|------|------|
| `Utils.registerShortcut(keys, handler)` | 注册快捷键 |
| `Utils.initShortcuts()` | 初始化全局快捷键 (Ctrl+K 命令面板等) |

### 9.8 移动端适配

| 函数 | 说明 |
|------|------|
| `Utils.isMobile()` | 检测是否为移动设备 |
| `Utils.preventClickDelay()` | 去除 300ms 点击延迟 |
| `Utils.optimizeMobileScroll()` | 优化移动端滚动流畅度 |
| `Utils.adjustForKeyboard()` | 适配软键盘弹出 |
| `Utils.initMobileOptimizations()` | 统一初始化移动端优化 |

### 9.9 图片懒加载

| 函数 | 说明 |
|------|------|
| `Utils.initImageLazyLoad()` | 初始化图片懒加载 (Intersection Observer) |

### 9.10 空状态 / 错误状态 / 骨架屏

| 函数 | 说明 |
|------|------|
| `Utils.renderEmptyState(options)` | 渲染空状态 HTML (支持 5 种类型: default/search/data/error/loading) |
| `Utils.renderErrorState(options)` | 渲染错误状态 HTML (支持重试按钮) |
| `Utils.renderSkeleton(options)` | 渲染骨架屏 HTML (支持 3 种类型: list/card/detail) |

### 9.11 新手引导

| 函数 | 说明 |
|------|------|
| `Utils.showOnboarding()` | 显示新手引导 |
| `Utils.checkFirstVisit()` | 检查是否首次访问 |

### 9.12 缓存管理

| 函数 | 说明 |
|------|------|
| `Utils.cache.get(key)` | 从缓存读取 |
| `Utils.cache.set(key, value, ttl)` | 写入缓存 (支持 TTL) |
| `Utils.cache.remove(key)` | 删除缓存 |
| `Utils.cache.clear()` | 清空所有缓存 |

---

## 10. 动画系统

**文件路径**: `assets/js/animations.js`  
**依赖**: GSAP (gsap.min.js), ScrollTrigger (CDN)  
**暴露**: `globalThis.Animations`

### 10.1 动画函数

| 函数 | 说明 | 默认参数 |
|------|------|---------|
| `Animations.fadeInUp(selector, options)` | 淡入上移 | y:20, duration:0.6s |
| `Animations.staggerFadeIn(selector, options)` | 错落淡入 | stagger:0.08s |
| `Animations.scaleIn(selector, options)` | 缩放进入 | scale:0.95 |
| `Animations.slideInLeft(selector, options)` | 左侧滑入 | x:30 |
| `Animations.slideInRight(selector, options)` | 右侧滑入 | x:30 |
| `Animations.initPageAnimations(scope)` | 初始化页面动画 | scope: document |

### 10.2 声明式动画 (data-animate)

在 HTML 元素上添加 `data-animate` 属性即可触发动画：

```html
<div data-animate="fade-in-up" data-delay="0.1" data-duration="0.5">
  内容区域
</div>
```

支持的动画类型：
- `fade-in-up` — 淡入上移
- `scale-in` — 缩放进入
- `stagger-fade-in` — 错落淡入 (用于列表项)
- `slide-in-left` — 左侧滑入
- `slide-in-right` — 右侧滑入

---

## 11. 数据可视化

**文件路径**: `assets/js/charts.js`  
**依赖**: Chart.js (4.x, 可选)  
**暴露**: `globalThis.Charts`

### 11.1 图表类型

| 函数 | 说明 |
|------|------|
| `Charts.createLineChart(canvasId, data, options)` | 折线图 (案件趋势) |
| `Charts.createPieChart(canvasId, data, options)` | 饼图/环形图 (胜诉率) |
| `Charts.createRadarChart(canvasId, data, options)` | 雷达图 (律师能力画像) |
| `Charts.createBarChart(canvasId, data, options)` | 柱状图 (案件类型分布) |
| `Charts.createHeatmap(canvasId, data, options)` | 热力图 (时间分布) |
| `Charts.destroyChart(canvasId)` | 销毁图表实例 |

### 11.2 默认颜色

```javascript
brand: '#165DFF'    // 品牌蓝
success: '#07C160'  // 成功绿
warning: '#FA8C16'  // 警告橙
danger: '#F53F3F'   // 危险红
wiki: '#6C5CE7'     // 紫色
ai: '#0EA5E9'       // 青色
```

---

## 12. 移动端适配

**文件路径**: `assets/js/touch.js`  
**依赖**: 无  
**暴露**: `globalThis.TouchHandler`, `globalThis.MobileTouch`

### 12.1 TouchHandler 类

手势处理类，支持：

| 手势 | 事件名 | 说明 |
|------|--------|------|
| 滑动 | `swipeleft`, `swiperight`, `swipeup`, `swipedown` | 快速滑动 |
| 长按 | `longpress` | 500ms 长按 |
| 双指缩放 | `pinch` | 双指缩放 |
| 双指旋转 | `rotate` | 双指旋转 |

### 12.2 MobileTouch 组件

| 组件 | 说明 |
|------|------|
| `MobileTouch.BottomNavigation` | 底部导航栏 |
| `MobileTouch.PullToRefresh` | 下拉刷新 |
| `MobileTouch.InfiniteScroll` | 上滑加载更多 |
| `MobileTouch.SideMenu` | 侧滑菜单 |
| `MobileTouch.SwipeBack` | 左滑返回 |

---

## 13. 主题系统

### 13.1 主题模式

支持三种主题模式：
- `light` — 浅色模式
- `dark` — 深色模式
- `auto` — 跟随系统

### 13.2 实现方式

1. 防闪烁脚本 (内联在 `<head>` 中) 在页面渲染前设置 `data-theme` 属性
2. `localStorage` 存储用户选择的主题 (`lexprime-theme`)
3. CSS 变量实现主题切换，所有颜色通过 CSS 变量引用
4. `Utils.setTheme()` / `Utils.toggleTheme()` / `Utils.getTheme()` 提供主题操作 API

### 13.3 切换入口

- 右上角用户菜单 → 主题切换
- 快捷键 (待实现)
- 系统设置页面

---

## 14. 插件系统

**文件路径**: `assets/js/plugin-loader.js`  
**暴露**: `globalThis.PluginLoader`

### 14.1 插件结构

每个插件至少包含 `manifest.json` 和 `plugin.js`：

```
plugins/
└── example-plugin/
    ├── manifest.json      # 插件配置
    ├── plugin.js          # 前端插件代码
    ├── plugin.py          # 后端插件代码 (可选)
    └── README.md
```

### 14.2 manifest.json 示例

```json
{
  "name": "example-plugin",
  "version": "1.0.0",
  "description": "示例插件",
  "author": "LexPrime",
  "main": "plugin.js",
  "extensions": ["sidebar", "workstation", "case.detail"]
}
```

### 14.3 扩展点

支持 10+ 个 UI 扩展点：
- `sidebar` — 侧边栏
- `workstation` — 工作台
- `case.detail` — 案件详情
- `case.list` — 案件列表
- `client.detail` — 客户详情
- `contract.review` — 合同审查
- `ai` — AI 对话
- `dashboard` — 仪表盘
- `header` — 顶部导航
- `footer` — 底部

### 14.4 API

| 方法 | 说明 |
|------|------|
| `PluginLoader.load(pluginPath)` | 加载插件 |
| `PluginLoader.enable(name)` | 启用插件 |
| `PluginLoader.disable(name)` | 禁用插件 |
| `PluginLoader.getPlugins()` | 获取已加载插件列表 |
| `PluginLoader.on(event, callback)` | 监听事件 |
| `PluginLoader.emit(event, data)` | 触发事件 |

---

## 15. 构建与部署

### 15.1 npm scripts

```json
{
  "test": "node --test \"tests/**/*.test.cjs\"",       // 运行单元测试
  "test:watch": "node --test --watch \"tests/**/*.test.cjs\"",  // 监听模式
  "lint": "npx eslint assets/js/*.js --quiet",         // 代码检查
  "lint:fix": "npx eslint assets/js/*.js --fix --quiet", // 自动修复
  "format": "npx prettier --write assets/js/*.js assets/css/*.css",  // 格式化
  "format:check": "npx prettier --check assets/js/*.js assets/css/*.css", // 格式检查
  "build": "node scripts/build.js",                    // 生产构建
  "start": "bash scripts/start-frontend.sh",           // 启动开发服务器
  "deploy": "bash scripts/deploy.sh"                   // 一键部署
}
```

### 15.2 构建流程 (build.js)

```
1. buildTailwind()
   └── npx tailwindcss -i tailwind-input.css -o dist/tailwind.min.css --minify

2. buildCustomCSS()
   └── clean-css 压缩 styles.css / marketplace.css → dist/*.min.css

3. buildJS()
   └── terser 压缩所有 JS 文件 → dist/*.min.js

4. compressAssets()
   ├── gzip 压缩 (可选)
   └── brotli 压缩 (可选)

5. buildIndexHTML()
   └── 生成 index.prod.html (JS/CSS 引用切换到 dist/*.min.* 并添加内容哈希)
```

### 15.3 生产环境切换

构建完成后，将 `index.prod.html` 替换为 `index.html`：

```bash
# 构建
npm run build

# 切换到生产环境
cp index.prod.html index.html
```

### 15.4 启动方式

```bash
# 方式 1: npm 脚本
npm start

# 方式 2: 直接启动
python3 -m http.server 8080 --bind 0.0.0.0

# 方式 3: http-server (需要安装)
http-server -p 8080 -a 0.0.0.0 -c-1 -g

# 方式 4: Docker
docker-compose up -d
```

### 15.5 Docker 部署

```yaml
# docker-compose.yml
services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      backend:
        condition: service_healthy

  backend:
    build:
      context: backend/cases-crawler
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
```

---

## 16. 开发规范

### 16.1 代码风格

- **语言**: ES5 JavaScript (不使用 ES6+ 语法)
- **模块化**: IIFE 模式，通过 `globalThis` 暴露公共 API
- **命名规范**:
  - 函数: `camelCase` (如 `switchView`, `loadUserData`)
  - 全局变量: `PascalCase` 或 `UPPER_SNAKE_CASE` (如 `AppState`, `CONFIG`)
  - 私有函数: `_` 前缀 (如 `_initThemeSystem`)
  - 事件处理: `on` 前缀 (如 `onLoginClick`, `onFileUpload`)
  - DOM 元素 ID: `kebab-case` (如 `main-content`, `user-menu-name`)

### 16.2 新增视图页面

1. 创建 HTML 模板: `templates/views/{module}/{name}.html`
2. 在 `router.js` 的 `viewFileMap` 中添加映射
3. 如需 JS 逻辑，创建 `assets/js/{name}.js` 并在 `viewScriptMap` 中添加映射
4. 如需特殊初始化，在 `viewInitMap` 中添加初始化逻辑
5. 在 `index.html` 侧边栏中添加菜单项

### 16.3 新增 API 接口

1. 在 `api.js` 的 `API` 对象中添加命名空间和方法
2. 使用 `request()` 通用函数 (自动处理 token、CSRF、401 等)
3. 后端路由: `backend/cases-crawler/api/{name}_router.py`
4. 在 `backend/cases-crawler/api/main.py` 中注册路由

### 16.4 模态框规范

统一使用 `Utils.showModal()` 方法：

```javascript
// 关闭函数变量
var _closeMyModal = null;

// 显示模态框
_closeMyModal = Utils.showModal({
    id: 'my-modal',
    title: '标题',
    content: buildFormHtml(),
    size: 'md',           // sm / md / lg / xl
    showFooter: true,
    onConfirm: function() {
        // 确认回调
    },
    onClose: function() {
        _closeMyModal = null;
    }
});
```

### 16.5 空状态/错误状态规范

统一使用 Utils 工具函数：

```javascript
// 空状态
container.innerHTML = Utils.renderEmptyState({
    type: 'search',           // default / search / data / error / loading
    title: '未找到案件',
    description: '请尝试修改搜索条件',
    actionText: '清除筛选',
    actionHandler: 'clearFilters()'
});

// 错误状态
container.innerHTML = Utils.renderErrorState({
    message: '加载失败',
    onRetry: function() { loadData(); }
});

// 骨架屏
container.innerHTML = Utils.renderSkeleton({
    type: 'list',             // list / card / detail
    count: 5                  // 骨架项数量
});
```

### 16.6 动画规范

使用声明式 `data-animate` 属性：

```html
<!-- 标题区 -->
<div data-animate="fade-in-up" data-delay="0">
  <h2>页面标题</h2>
</div>

<!-- 卡片容器 -->
<div data-animate="scale-in" data-delay="0.1">
  <div class="card">...</div>
</div>

<!-- 列表项 (父容器) -->
<div data-animate="stagger-fade-in" data-delay="0.2">
  <div class="list-item">项目 1</div>
  <div class="list-item">项目 2</div>
  <div class="list-item">项目 3</div>
</div>
```

### 16.7 ESLint 规则

- 使用 `var` 声明变量 (ES5)
- 禁止 `console.log` (允许 `warn` 和 `error`)
- 使用 `===` 严格比较
- 2 空格缩进
- 行长度限制 120 字符

### 16.8 常用命令

```bash
# 开发
npm run lint          # 代码检查
npm run lint:fix      # 自动修复
npm run test          # 运行测试
npm start             # 启动开发服务器

# 构建
npm run build         # 生产构建

# 部署
npm run deploy        # 一键部署
```

---

## 附录

### A. 全局变量速查表

| 变量 | 来源 | 说明 |
|------|------|------|
| `AppState` | app-state.js | 全局应用状态 |
| `API` | api.js | API 客户端 |
| `Auth` | auth.js | 认证模块 |
| `Utils` | utils.js | 工具函数 |
| `Animations` | animations.js | 动画系统 |
| `Charts` | charts.js | 图表组件 |
| `TouchHandler` | touch.js | 触摸处理 |
| `MobileTouch` | touch.js | 移动端组件 |
| `PluginLoader` | plugin-loader.js | 插件加载器 |
| `viewCache` | router.js | 视图缓存 |
| `viewFileMap` | router.js | 视图文件映射 |
| `viewScriptMap` | router.js | 视图脚本映射 |
| `switchView` | router.js | 视图切换 |
| `switchSidebarTab` | router.js | 侧边栏切换 |
| `bootstrapApp` | bootstrap.js | 启动入口 |
| `showToast` | script.js | Toast 通知 |

### B. 浏览器兼容性

| 浏览器 | 最低版本 |
|--------|---------|
| Chrome | 80+ |
| Firefox | 75+ |
| Safari | 13+ |
| Edge | 80+ |

### C. 相关文档

- [系统架构文档](./architecture.md)
- [API 接口文档](./api.md)
- [用户使用手册](./user-guide.md)
- [开发指南](./development.md)
- [部署文档](./deployment.md)
- [性能优化指南](./performance-optimization.md)
- [私有化部署文档](./private-deployment.md)