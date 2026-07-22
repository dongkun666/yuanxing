# LexPrime 元枢法智

> AI 赋能诉讼案件管理系统 — 律师的第二大脑

[![License: ISC](https://img.shields.io/badge/License-ISC-blue.svg)](https://opensource.org/licenses/ISC)
[![Frontend: ES5+Tailwind](https://img.shields.io/badge/Frontend-ES5%20%2B%20Tailwind-165DFF.svg)](https://tailwindcss.com/)
[![Backend: Python FastAPI](https://img.shields.io/badge/Backend-Python%20FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests: 129 passing](https://img.shields.io/badge/Tests-129%20passing-success.svg)](#测试)
[![PWA](https://img.shields.io/badge/PWA-ready-5A0FC8.svg)](#pwa)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](#docker-部署)

---

## 简介

LexPrime 元枢法智是一个 **AI 赋能的法律科技平台**，为律师和律所提供智能化的案件管理、合同审查、文书生成、法律研究、律师匹配等全流程服务。

系统采用 **前端 SPA + 后端微服务** 架构，覆盖 Web、PWA、桌面端（Electron）、移动端（React Native）、微信小程序、浏览器扩展、企业微信/钉钉集成等多端场景。

---

## 核心功能

### 案件管理
- 案件全生命周期管理（录入 → 审查 → 匹配 → 进行中 → 结案 → 归档）
- 案件时间线、动态追踪、进度可视化
- 批量导入导出（Excel/PDF/JSON/Word）
- 法律期限提醒与执行管理

### AI 能力
- **智能法律问答** — 基于 RAG 的法律知识问答系统
- **合同智能审查** — 25 条内置规则引擎，风险分级，修改建议
- **智能合同生成** — 基于需求描述自动生成合同文本
- **案件风险预测** — 基于历史案例预测胜诉率和风险点
- **文书智能生成** — AI 驱动的法律文书生成与润色
- **法律关系图谱** — 实体关系挖掘与可视化
- **多文档摘要对比** — 多文档自动摘要与差异分析

### 数据资产
- **判例库** — 结构化解析，标签体系，全文检索（FTS5 + jieba 分词）
- **法规库** — 层级结构，版本管理，效力关联分析
- **企业库** — 股权穿透，风险画像，关联企业发现
- **律师库** — 能力画像，胜诉分析，专长匹配
- **知识图谱** — 法律实体关系图谱，路径推理

### Marketplace
- 律师匹配（多维度评分算法）
- 案件转介
- 跨境协作
- 市场数据分析

### 企业级能力
- 多租户架构（SaaS 化，数据隔离）
- SSO 集成（SAML 2.0 / OIDC / LDAP）
- 审计日志（操作审计、合规报告）
- 组织架构管理（部门、团队、角色、权限层级）
- 私有化部署（离线激活，机器指纹）

### 商业化
- 订阅计费（免费/基础/专业/企业版）
- 支付集成（支付宝/微信支付）
- 邀请裂变
- 增长分析仪表盘

---

## 技术栈

### 前端

| 技术 | 用途 |
|------|------|
| ES5 JavaScript (IIFE) | 业务逻辑（兼容旧浏览器） |
| Tailwind CSS 3.4 | 原子化样式 |
| GSAP 3.12 | 高性能动画引擎 |
| Chart.js 4.x | 数据可视化图表 |
| Iconify (MDI) | 本地离线图标库 |
| Service Worker | PWA 离线支持 |

### 后端

| 技术 | 用途 |
|------|------|
| Python 3.11 | 运行时 |
| FastAPI | Web 框架 |
| SQLAlchemy ORM | 数据库 ORM |
| Alembic | 数据库迁移 |
| PyJWT | JWT 认证 |
| bcrypt | 密码哈希 |
| loguru | 结构化日志 |
| PaddleOCR | OCR 文字识别 |

### 基础设施

| 技术 | 用途 |
|------|------|
| PostgreSQL 16 | 生产数据库 |
| Redis 7 | 缓存 + 会话 |
| Elasticsearch 8 | 全文检索 |
| Nginx | 反向代理 + 静态资源 |
| Docker | 容器化部署 |
| GitHub Actions | CI/CD |

---

## 项目结构

```
yuanxing/
├── index.html                    # 前端入口
├── assets/
│   ├── css/                      # 样式文件 (tailwind + 自定义)
│   ├── js/                       # 47 个 JS 业务模块
│   ├── icons/                    # 图标资源
│   └── images/                   # 图片资源
├── templates/views/              # 81 个视图页面模板
├── backend/cases-crawler/
│   ├── api/                      # 48 个 API 路由
│   ├── auth/                     # 认证模块 (JWT/SSO/TOTP)
│   ├── core/                     # 核心业务逻辑
│   ├── skills/                   # 技能模块 (合同审查/判例/谈判)
│   ├── crawlers/                 # 数据爬虫
│   ├── ai/                       # AI 模型训练与评测
│   └── tests/                    # 后端测试
├── scripts/                      # 构建/部署/测试脚本
├── tests/                        # 前端单元测试
├── docs/                         # 项目文档
├── phase5-react/                 # Electron 桌面应用
├── miniprogram/                  # 微信小程序
├── mobile-app/                   # React Native 移动应用
├── browser-extension/            # 浏览器扩展
├── integrations/                 # 企业微信/钉钉集成
├── plugins/                      # 插件系统
├── docker-compose.yml            # Docker 编排
├── Dockerfile.frontend           # 前端 Docker 镜像
├── nginx.conf                    # Nginx 配置
├── manifest.json                 # PWA 清单
├── service-worker.js             # Service Worker
└── package.json                  # 项目配置
```

---

## 快速开始

### 环境要求

- Node.js >= 18
- Python >= 3.11
- Docker >= 24.0（可选）

### 方式一：本地开发

```bash
# 1. 克隆仓库
git clone https://github.com/dongkun666/yuanxing.git
cd yuanxing

# 2. 安装前端依赖
npm install

# 3. 启动前端服务
npm start
# 前端运行在 http://localhost:8080

# 4. 启动后端服务
cd backend/cases-crawler
pip install -r requirements.txt
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
# 后端运行在 http://localhost:8000
```

### 方式二：Docker 部署

```bash
# 一键启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

服务端口：

| 服务 | 端口 |
|------|------|
| 前端 | 80 (HTTP) / 443 (HTTPS) |
| 后端 API | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| Elasticsearch | 9200 |

### 方式三：一键启动脚本

```bash
# 开发模式
./start.sh --dev

# 生产模式
./start.sh --prod

# Docker 模式
./start.sh --docker
```

---

## 使用指南

### 首次访问

1. 打开 http://localhost:8080
2. 点击底部 **Demo 模式进入** 可免登录体验
3. 或注册新账号 / 使用已有账号登录

### 快捷操作

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + K` | 打开命令面板 |
| `ESC` | 关闭模态框 |

### 主题切换

- 右上角用户菜单 → 主题切换
- 支持浅色 / 深色 / 跟随系统三种模式

---

## 开发

### 常用命令

```bash
# 代码检查
npm run lint

# 自动修复
npm run lint:fix

# 格式化代码
npm run format

# 运行测试
npm test

# 监听模式测试
npm run test:watch

# 生产构建
npm run build

# 部署
npm run deploy
```

### 构建产物

```bash
npm run build
```

构建后生成：

| 产物 | 路径 | 说明 |
|------|------|------|
| 压缩 CSS | `assets/css/dist/*.min.css` | clean-css 压缩 |
| 压缩 JS | `assets/js/dist/*.min.js` | terser 压缩 |
| 生产入口 | `index.prod.html` | 引用压缩产物 + 内容哈希 |

### 新增页面

1. 创建 HTML 模板：`templates/views/{module}/{name}.html`
2. 在 `assets/js/router.js` 的 `viewFileMap` 中添加映射
3. 如需 JS 逻辑，创建 `assets/js/{name}.js` 并在 `viewScriptMap` 中添加映射
4. 在 `index.html` 侧边栏中添加菜单项

详见 [前端开发文档](docs/frontend-guide.md)

---

## 测试

### 前端测试

```bash
npm test
```

| 测试文件 | 覆盖范围 | 测试数 |
|---------|---------|--------|
| utils.test.cjs | 工具函数（HTML转义、模态框、主题、缓存等） | 61 |
| templates.test.cjs | 模板管理（CRUD、分类、搜索） | 13 |
| schedule.test.cjs | 日程管理（日历、筛选、排序） | 22 |
| marketplace.test.cjs | Marketplace（律师匹配、评分、过滤） | 33 |

**总计：129 个测试，全部通过**

### 后端测试

```bash
cd backend/cases-crawler
python -m pytest tests/ -v
```

---

## PWA

项目已支持 PWA（渐进式 Web 应用）：

- **离线访问**：Service Worker 缓存静态资源，离线时可访问已缓存页面
- **安装到桌面**：浏览器地址栏点击安装图标，可添加到桌面/主屏幕
- **自动更新**：Service Worker 检测更新并提示用户刷新
- **推送通知**：支持 Web Push 通知（需配置推送服务）

配置文件：

| 文件 | 说明 |
|------|------|
| `manifest.json` | PWA 应用清单 |
| `service-worker.js` | Service Worker 注册脚本 |
| `offline.html` | 离线回退页面 |
| `assets/icons/pwa/` | 6 种尺寸 PWA 图标 |

---

## 多端支持

| 平台 | 路径 | 技术栈 |
|------|------|--------|
| Web | `/` | ES5 + Tailwind + GSAP |
| PWA | `/` | Service Worker + Web App Manifest |
| 桌面端 | `phase5-react/` | Electron + React + TypeScript |
| 移动端 | `mobile-app/` | React Native + Expo |
| 微信小程序 | `miniprogram/` | 原生小程序 |
| 浏览器扩展 | `browser-extension/` | Chrome Extension (Manifest V3) |
| 企业微信 | `integrations/wecom/` | 企业微信应用 |
| 钉钉 | `integrations/dingtalk/` | 钉钉应用 |

---

## 安全

- **JWT 认证**：access_token + refresh_token，自动续期
- **CSRF 防护**：非 GET 请求自动携带 X-CSRF-Token
- **XSS 防护**：HTML 转义 + 白名单净化
- **速率限制**：API 请求频率限制
- **安全头**：HSTS、CSP、X-Frame-Options 等
- **密码哈希**：bcrypt
- **多因素认证**：TOTP 支持
- **审计日志**：全操作审计追踪

---

## 监控

- **前端监控**：全局异常捕获、Promise 未处理拒绝、Core Web Vitals（LCP/FID/CLS）
- **后端日志**：loguru 结构化 JSON 日志，按天滚动，自动压缩
- **请求日志**：中间件记录请求耗时、状态码、路径
- **健康检查**：`GET /api/health` 检查数据库、ES、Redis 连接状态
- **性能监控**：Server-Timing 响应头、慢查询告警（>500ms）

---

## 文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 前端开发文档 | [docs/frontend-guide.md](docs/frontend-guide.md) | 前端架构、模块、API、开发规范 |
| 系统架构文档 | [docs/architecture.md](docs/architecture.md) | 系统架构、技术栈、数据流 |
| API 接口文档 | [docs/api.md](docs/api.md) | API 接口说明、认证、错误码 |
| 用户使用手册 | [docs/user-guide.md](docs/user-guide.md) | 产品功能、操作教程 |
| 开发指南 | [docs/development.md](docs/development.md) | 开发流程、代码规范 |
| 部署文档 | [docs/deployment.md](docs/deployment.md) | 部署方式、环境配置 |
| 域名配置 | [docs/domain-setup.md](docs/domain-setup.md) | DNS、HTTPS、CDN 配置 |
| 性能优化 | [docs/performance-optimization.md](docs/performance-optimization.md) | 性能调优指南 |
| 私有化部署 | [docs/private-deployment.md](docs/private-deployment.md) | 离线部署、激活 |

---

## CI/CD

| 工作流 | 文件 | 触发条件 | 功能 |
|--------|------|---------|------|
| CI | `.github/workflows/ci.yml` | push/PR | 前端测试 + 构建 + ESLint，后端测试 |
| CD | `.github/workflows/cd.yml` | push to main | 构建 Docker 镜像并推送 |
| Release | `.github/workflows/release.yml` | tag push | 创建 GitHub Release |

---

## 项目统计

| 指标 | 数量 |
|------|------|
| 视图页面 | 81 |
| JS 业务模块 | 47 |
| API 路由 | 48 |
| 后端 Python 文件 | 150+ |
| 单元测试 | 129 |
| 文档 | 9 |
| 支持平台 | 8 |

---

## License

[ISC](https://opensource.org/licenses/ISC)

---

## 相关链接

- **GitHub**: [https://github.com/dongkun666/yuanxing](https://github.com/dongkun666/yuanxing)
- **Issues**: [https://github.com/dongkun666/yuanxing/issues](https://github.com/dongkun666/yuanxing/issues)
