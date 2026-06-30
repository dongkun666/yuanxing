<!-- LexPrime Track B · W17 phase4-close-831 -->
# Phase 5 准备文档 (Phase 5 Prep 2026-09-01)

> **版本**: v1.0 · 2026-06-30
> **Track**: B (Phase 5 准备 + 9/1-9/30 启动)
> **Week**: W17 phase4-close-831 配套
> **状态**: Phase 5 准备就绪, 9/1 owner 启动 W18 plan YAML
> **依据**:
> - `phase4-final-report.md` v1.1 (W17 83613c4, 12 周回顾 + KPI 验证)
> - `phase4-roadmap.md` v1.0 (12 周 + Phase 5 衔接)
> - PRD V5.0 § 12 Phase 5 计划 (W11 4910305)
> - plan-16-w16-final-report.md §4 W17 接力
> - plan-15-w15-final-report.md §4 W16 计划
> - plan-14-w14-final-report.md §4 W15 计划
> - W15 900948f (L4/L5 转化 9/15 延期)
> - W11 4910305 (5 律师付费触发 + PRD v0.7.4)
> - W11 8208143 (邀请码 1115 + L4/L5 邀请码 0119/0120)

> **核心定位 (Phase 5 prep vs Phase 4 final vs W11 PRD V5.0)**:
> - Phase 4 final (W17 v1.1) 写"Phase 4 完结 + 8/31 月底 50 律师付费 / ¥5 万+ ARR 验证" (8/31 节点)
> - **Phase 5 prep (W17 v1.0) 写"Phase 5 启动准备 + React 18 + TS + Electron + Rust + L4/L5 企业版 + 3 agent 招聘" (9/1-9/30 节点)**
> - 增量: 4 个 Phase 5 阶段 (5.1 React 18 + 5.2 Electron + 5.3 Rust + 5.4 L4/L5) + 3 agent 招聘 (lex-security + lex-electron + lex-mobile) + 9/1-9/30 时间线 + 关键里程碑 + 风险评估

---

## 0. 文档使用说明 (Phase 5 启动准备)

> **本准备文档是 Phase 5 (2026-09-01 ~ 2026-12-31, 4 个月) 启动前的总览**:
> - 4 个 Phase 5 阶段 (5.1-5.4) 完整规划
> - 3 个新 agent 招聘 (lex-security + lex-electron + lex-mobile)
> - 9/1-9/30 关键时间线 (W18-W21)
> - 10/1-12/31 后续时间线 (W22-W35)
> - 关键里程碑 + 风险评估 + 关联文档

> **本准备文档配套**:
> - `phase4-final-report.md` v1.1 (W17, 12 周回顾 + KPI 验证)
> - `phase4-roadmap.md` v1.0 (12 周 + Phase 5 衔接)
> - PRD V5.0 § 12 Phase 5 计划 (W11 4910305)
> - W15 900948f (L4/L5 转化 9/15 延期)
> - W11 8208143 (L4/L5 邀请码 0119/0120)

> **数据 placeholder**: 9/1-12/31 期间所有数字 placeholder, owner 9/1 实测填实.
> **严禁 fabricate**: 当前时间 2026-06-30, 距 9/1 还有 63 天. 全部 runbook / 模板 / 应急备案 / 跟踪节奏可以写, 实际数字必须 placeholder.

---


## 1. Phase 5 总览 (2026-09-01 ~ 2026-12-31)

### 1.1 Phase 5 时间窗口

| 阶段 | 时间 | 核心目标 | 关键交付 | 负责 agent |
|------|------|---------|---------|-----------|
| **Phase 5.1** | 9/1-9/15 (2 周) | React 18 + TypeScript 重构 | yuanxing 桌面端重构 + 组件库迁移 + 单元测试 80%+ | lex-coder + lex-design |
| **Phase 5.2** | 9/16-10/15 (4 周) | Electron 打包正式上线 | electron-builder 配置 + Win/macOS/Linux 安装包 + 公测安装 | lex-electron (新) + lex-coder |
| **Phase 5.3** | 10/16-11/30 (6 周) | Rust 核心模块迁移 | OCR / PaddleEngine / FTS5 / LanceDB 核心转 Rust + 性能提升 3-5x | lex-coder (Rust 子模块) + lex-ai |
| **Phase 5.4** | 9/15 (启动) ~ 12/31 (完结) | L4/L5 企业版上线 | 企业版 PRD v1.0 + ¥1,500-2,000/律师/年定价 + 10+ 企业签约 | lex-bd + lex-pm + lex-security (新) |

> **Phase 5 4 个月总览 (2026-09-01 ~ 2026-12-31)**:
> - 9 月 (W18-W21, 4 周): Phase 5.1 React 18 + TS 重构 + Phase 5.4 L4/L5 9/15 预登记启动
> - 10 月 (W22-W26, 4 周): Phase 5.2 Electron 打包 + Phase 5.4 企业版 1.0 上线
> - 11 月 (W27-W30, 4 周): Phase 5.3 Rust 核心 OCR / PaddleEngine 迁移
> - 12 月 (W31-W35, 4 周): Phase 5.3 Rust 核心 FTS5 / LanceDB 迁移 + Phase 5.4 10+ 企业签约

### 1.2 Phase 5 关键 KPI

| KPI | 9/30 目标 | 12/31 目标 | 关联阶段 |
|-----|----------|-----------|---------|
| **付费律师总数** | 80 (50 + 30 L4/L5) | 200 (50 创史 + 80 月度 + 70 L4/L5) | 5.4 |
| **企业版签约** | 5 (L4/L5 9/15 预登记启动) | 10+ (¥1,500-2,000/律师/年) | 5.4 |
| **月营收** | ¥15,000 (80 律师) | ¥40,000 (200 律师) | 5.4 |
| **ARR** | ¥180,000 (¥15,000 × 12) | ¥480,000 (¥40,000 × 12) | 5.4 |
| **桌面端安装包** | Win 安装包 (Phase 5.2) | Win/macOS/Linux 三端安装包 | 5.2 |
| **Rust 核心覆盖率** | 0% (启动) | 60%+ (OCR + PaddleEngine + FTS5 + LanceDB) | 5.3 |
| **React 18 重构覆盖率** | 50%+ (核心组件) | 90%+ (全组件库) | 5.1 |
| **单元测试覆盖率** | 80%+ | 90%+ | 5.1 + 5.3 |
| **3 新 agent 招聘** | 1 (lex-electron) | 3 (lex-security + lex-electron + lex-mobile) | 启动 |

> **Phase 5 KPI 任务定义**:
> - 9/30: 80 律师 + ¥15,000 月营收 + ¥18 万 ARR (Phase 4 8/31 50 律师接力)
> - 12/31: 200 律师 + ¥40,000 月营收 + ¥48 万 ARR (Phase 5 完结)
> - Win/macOS/Linux 三端安装包 (Phase 5.2)
> - Rust 核心 60%+ 覆盖率 (Phase 5.3)
> - 3 新 agent 全部就位 (Phase 5 配套)

### 1.3 Phase 5 与 Phase 4 关系

| 维度 | Phase 4 (8/31 完结) | Phase 5 (12/31 完结) |
|------|-------------------|---------------------|
| **产品形态** | Web 桌面端 + 5 律师评审 | Electron 桌面端 + L4/L5 企业版 |
| **技术栈** | Vue 3 + Element Plus | React 18 + TypeScript + Electron + Rust |
| **定价** | 个人版 ¥99/月 + 创史 ¥449/年 | 个人版 ¥99/月 + 创史 ¥449/年 + 企业版 ¥1,500-2,000/律师/年 |
| **客户规模** | 50 律师 (8/31) | 200 律师 (12/31) |
| **营收规模** | ¥8,450 月营收 / ¥10 万+ ARR | ¥40,000 月营收 / ¥48 万 ARR |
| **价值主张** | 5 大价值主张 (落地) | 5 大价值主张 + 企业版场景扩展 |

> **Phase 4 → Phase 5 衔接**:
> - **产品形态**: Web 桌面端 (Phase 4) → Electron 桌面端 (Phase 5.2) 正式打包
> - **技术栈升级**: Vue 3 → React 18 + TS (Phase 5.1) + Rust 核心 (Phase 5.3)
> - **客户扩展**: 50 律师 (8/31) → 200 律师 (12/31) 4x 增长
> - **营收扩展**: ¥10 万 ARR (8/31) → ¥48 万 ARR (12/31) 4.8x 增长

---


## 2. Phase 5.1 React 18 + TypeScript 重构 (9/1-9/15)

### 2.1 重构目标

| 维度 | Phase 4 (Vue 3) | Phase 5.1 (React 18 + TS) | 提升 |
|------|----------------|--------------------------|------|
| **前端框架** | Vue 3 + Composition API | React 18 + TypeScript | 类型安全 + 组件复用 |
| **状态管理** | Pinia | Zustand + React Query | 简化 + 异步优化 |
| **路由** | Vue Router 4 | React Router 6 | - |
| **UI 库** | Element Plus | Ant Design 5 / shadcn/ui | - |
| **构建工具** | Vite 4 | Vite 5 + Rspack (可选) | 性能 + 生态 |
| **类型系统** | JavaScript + JSDoc | TypeScript 5.0+ | 强类型 |
| **测试** | Vitest + Vue Test Utils | Vitest + React Testing Library | - |
| **SSR (可选)** | - | Next.js 14 App Router | SEO + 性能 |

### 2.2 重构范围

| 模块 | Phase 4 组件 | Phase 5.1 重构后 | 优先级 |
|------|------------|------------------|-------|
| **一体化工作站** | Workstation.vue | Workstation.tsx | P0 |
| **合同审查 (Skill 2)** | ContractReview.vue | ContractReview.tsx | P0 |
| **OCR 证据目录** | EvidenceList.vue | EvidenceList.tsx | P0 |
| **类案检索 (Skill 1)** | CaseSearch.vue | CaseSearch.tsx | P0 |
| **文书生成 (Skill 3)** | DocumentGen.vue | DocumentGen.tsx | P0 |
| **A2 双审工作流** | DocReview.vue | DocReview.tsx | P0 |
| **招募页** | FoundingPage.vue | FoundingPage.tsx | P1 |
| **Dashboard** | Dashboard.vue | Dashboard.tsx | P1 |
| **Onboarding 5 步** | Onboarding.vue | Onboarding.tsx | P1 |
| **付费墙** | Paywall.vue | Paywall.tsx | P1 |

> **重构覆盖率**: 9/15 完成 50% (核心组件 Workstation + 4 Skill + A2 双审) + 9/30 完成 80% (招募 + Dashboard) + 12/31 完成 90%+ (剩余 Onboarding + Paywall)

### 2.3 关键里程碑

| 里程碑 | 日期 | 验证 | 负责 agent |
|--------|------|------|-----------|
| **W18 启动 + 设计系统迁移** | 9/1-9/7 | design tokens + 组件库 v2.0 (Ant Design 5 / shadcn/ui) | lex-design + lex-coder |
| **W19 核心组件 50%** | 9/8-9/15 | Workstation + 4 Skill + A2 双审 (5 组件) | lex-coder |
| **W20 招募 + Dashboard 80%** | 9/16-9/22 | FoundingPage + Dashboard + Onboarding | lex-coder |
| **W21 单元测试 80%+** | 9/23-9/30 | Vitest 单元测试 + React Testing Library | lex-coder |

> **Phase 5.1 关键风险**:
> - React 18 SSR + Suspense 兼容 (Mavis cron self 验证)
> - 状态管理迁移数据丢失 (lex-coder 写迁移脚本)
> - 单元测试覆盖率 80% 门槛 (lex-coder 写测试模板)
> - TypeScript 严格模式 strict: true (lex-coder 写 .eslintrc + tsconfig)

### 2.4 关联任务

| Task | 派发 | 期望耗时 | 备注 |
|------|------|---------|------|
| `react18-migration` | lex-coder + lex-design | 2 周 (W18-W19) | 组件库迁移 + 设计系统 v2.0 |
| `core-components-50%` | lex-coder | 1 周 (W19) | Workstation + 4 Skill + A2 双审 |
| `dashboards-onboarding` | lex-coder | 1 周 (W20) | 招募 + Dashboard + Onboarding |
| `unit-tests-80%` | lex-coder | 1 周 (W21) | Vitest + RTL 单元测试 |
| `w21-integration` | verifier | 1 天 | 4 task deliverable 无冲突 + git log 4+ commit |

> **W18-W21 期望 commit**: 20+ commits 累计 (4 周 × 5 commits/周)

---


## 3. Phase 5.2 Electron 打包 (9/16-10/15)

### 3.1 打包目标

| 维度 | Phase 4 (Web 桌面端) | Phase 5.2 (Electron 桌面端) | 提升 |
|------|-------------------|--------------------------|------|
| **打包工具** | 浏览器访问 | electron-builder | 离线可用 |
| **跨平台** | Web 浏览器 | Win/macOS/Linux 三端安装包 | 全平台 |
| **本地存储** | localStorage / IndexedDB | SQLite + 文件系统 (本地化) | 数据自主 |
| **离线运行** | 必须联网 | 完全离线可用 | 律师工作流不中断 |
| **自动更新** | - | electron-updater (Squirrel) | 自动升级 |
| **安装包大小** | 0 (Web) | 80-150 MB (含 PaddleEngine) | - |
| **冷启动时间** | 2-3s (浏览器) | 1-2s (Electron) | 性能 +30% |

### 3.2 electron-builder 配置

```json
{
  "appId": "cn.lexprime.desktop",
  "productName": "LexPrime 元枢法智",
  "directories": {
    "output": "dist-electron"
  },
  "files": [
    "dist/**/*",
    "node_modules/**/*",
    "package.json"
  ],
  "win": {
    "target": ["nsis", "portable"],
    "icon": "assets/icon.ico"
  },
  "mac": {
    "target": ["dmg", "zip"],
    "icon": "assets/icon.icns",
    "category": "public.app-category.productivity"
  },
  "linux": {
    "target": ["deb", "rpm", "AppImage"],
    "icon": "assets/icon.png",
    "category": "Office"
  },
  "nsis": {
    "oneClick": false,
    "perMachine": false,
    "allowElevation": true,
    "allowToChangeInstallationDirectory": true
  }
}
```

### 3.3 关键里程碑

| 里程碑 | 日期 | 验证 | 负责 agent |
|--------|------|------|-----------|
| **W22 electron-builder 集成** | 9/16-9/22 | package.json + electron-builder.yml + Win 调试包 | lex-electron (新) |
| **W23 Win/macOS/Linux 三端打包** | 9/23-9/30 | 三端安装包 + 自动更新配置 | lex-electron |
| **W24 公测安装 200 律师** | 10/1-10/7 | 50 律师首批安装 + 反馈收集 | lex-electron + lex-bd |
| **W25 离线模式 + 本地存储** | 10/8-10/15 | SQLite + 文件系统 + 离线运行 | lex-electron + lex-coder |

> **Phase 5.2 关键风险**:
> - electron-builder 跨平台签名 (Apple Developer ID + Windows EV Code Sign)
> - 自动更新服务器 (lex-coder 写 update server)
> - 安装包大小优化 (lex-electron 用 asar 打包 + tree-shaking)
> - 冷启动性能 (lex-electron 用 V8 snapshot + lazy load)

### 3.4 关联任务

| Task | 派发 | 期望耗时 | 备注 |
|------|------|---------|------|
| `electron-builder-setup` | lex-electron (新) | 1 周 (W22) | electron-builder 配置 + Win 调试包 |
| `cross-platform-build` | lex-electron | 1 周 (W23) | Win/macOS/Linux 三端打包 + 签名 |
| `public-beta-200` | lex-electron + lex-bd | 1 周 (W24) | 50 律师首批安装 + 反馈 |
| `offline-mode` | lex-electron + lex-coder | 1 周 (W25) | SQLite + 离线运行 |
| `w25-integration` | verifier | 1 天 | 4 task deliverable + git log 4+ commit |

> **W22-W25 期望 commit**: 16+ commits 累计 (4 周 × 4 commits/周)

---


## 4. Phase 5.3 Rust 核心 (10/16-11/30)

### 4.1 Rust 核心目标

| 模块 | Phase 4 (Python) | Phase 5.3 (Rust) | 性能提升 |
|------|-----------------|-----------------|---------|
| **OCR (PaddleEngine 8089)** | Python + PaddleOCR | Rust + tract-onnx | 3-5x |
| **FTS5 (jieba)** | Python + jieba | Rust + tantivy (含 jieba 分词) | 5-10x |
| **LanceDB (RAG)** | Python + lancedb | Rust + lancedb (官方) | 2-3x |
| **PaddleEngine 调度** | Python + asyncio | Rust + tokio | 3-5x |
| **SQLite 缓存** | Python + sqlite3 | Rust + rusqlite + r2d2 | 2-3x |

### 4.2 Rust 工具链

| 工具 | 用途 | 备注 |
|------|------|------|
| **Rust 1.75+** | 编译器 | 2026-09 稳定版 |
| **Cargo** | 包管理 | - |
| **PyO3** | Python ↔ Rust FFI | 渐进式迁移 |
| **tokio** | 异步运行时 | - |
| **tract** | ONNX 推理 | PaddleOCR 替代 |
| **tantivy** | 全文检索 | FTS5 替代 |
| **lancedb (Rust)** | 向量数据库 | RAG 存储 |
| **rusqlite** | SQLite 绑定 | 本地缓存 |

### 4.3 关键里程碑

| 里程碑 | 日期 | 验证 | 负责 agent |
|--------|------|------|-----------|
| **W26 Rust 工具链 + PyO3 集成** | 10/16-10/22 | Cargo workspace + PyO3 FFI + 1 模块迁移 | lex-coder (Rust 子模块) |
| **W27 OCR + PaddleEngine 迁移** | 10/23-10/30 | PaddleEngine 8089 转 Rust + tract-onnx | lex-coder + lex-ai |
| **W28 FTS5 + jieba 迁移** | 10/31-11/6 | FTS5 转 tantivy + jieba-rs | lex-coder |
| **W29 LanceDB (RAG) 迁移** | 11/7-11/13 | lancedb (Rust) + RAG 性能测试 | lex-ai + lex-coder |
| **W30 集成验证 + 60% 覆盖率** | 11/14-11/30 | 4 模块迁移 + 性能基准 3-5x | verifier |

> **Phase 5.3 关键风险**:
> - PyO3 跨语言调用开销 (lex-coder benchmark 验证 < 5%)
> - tract-onnx PaddleOCR 兼容 (lex-ai 跑 5 律师函数样例)
> - tantivy 中文分词 (lex-coder 写 jieba-rs FFI)
> - lancedb Rust SDK 稳定性 (lex-ai 评估 v0.5+)

### 4.4 关联任务

| Task | 派发 | 期望耗时 | 备注 |
|------|------|---------|------|
| `rust-toolchain-pyo3` | lex-coder | 1 周 (W26) | Cargo + PyO3 + 1 模块迁移 |
| `paddle-rust` | lex-coder + lex-ai | 1 周 (W27) | PaddleEngine Rust 迁移 |
| `tantivy-jieba` | lex-coder | 1 周 (W28) | FTS5 → tantivy 迁移 |
| `lancedb-rust` | lex-ai + lex-coder | 1 周 (W29) | LanceDB Rust 迁移 |
| `rust-integration` | verifier | 2 周 (W29-W30) | 4 模块 + 性能基准 |
| `w30-integration` | verifier | 1 天 | 5 task deliverable + git log 5+ commit |

> **W26-W30 期望 commit**: 25+ commits 累计 (5 周 × 5 commits/周)

---


## 5. Phase 5.4 L4/L5 企业版上线 (9/15 预登记, 12/31 10+ 签约)

### 5.1 企业版目标

| 维度 | 个人版 (Phase 4) | 企业版 (Phase 5.4) | 提升 |
|------|----------------|-------------------|------|
| **定价** | ¥99/月 (律师单人) | ¥1,500-2,000/律师/年 (团队) | 15-20x |
| **客户类型** | 个人律师 | 企业法务 + 中所/大所 | 团队批量 |
| **使用规模** | 1 律师 | 5-100 律师/企业 | 5-100x |
| **核心场景** | 合同审查 + 文书 | 团队批量合同 + 内部合规 | 流程化 |
| **数据隔离** | 个人数据 | 企业数据隔离 + 权限管理 | 企业级 |
| **客户支持** | 1v1 BD 7×24 | 1v1 客户经理 + 培训 | 企业级 |
| **合规** | 个人隐私 | 企业合规 + 审计日志 | 企业级 |
| **签约目标** | 50 律师 (8/31) | 10+ 企业 (12/31) | - |

### 5.2 L4/L5 律师画像 (Phase 4 W15 9/15 预登记)

| 画像 | 律所规模 | 业务场景 | 试用到期 | 9/15 转化动作 | 12/31 签约目标 |
|------|---------|---------|---------|-------------|--------------|
| **L4 高级合伙人** | 30 人律所 | 公司/诉讼 | 8/25 (W15) | 9/15 1v1 强推 + 律协沙龙 #2 | 5+ 企业 (¥1,500/律师/年) |
| **L5 企业法务总监** | 100+ 员工 | 内部合规 | 8/25 (W15) | 9/15 1v1 强推 + 律协沙龙 #2 | 5+ 企业 (¥2,000/律师/年) |
| **新企业 (L6)** | 50-200 员工 | 综合 | - | 10/1 公测邀请 + 12/31 签约 | 5+ 企业 |

> **L4/L5 9/15 预登记启动**: 9/15 1v1 强推 2 律师 + 律协沙龙 #2 (8/17 基础上加 9/15) + 9/30 完成首批 5+ 企业签约
> **新企业 (L6) 招募**: 10/1 公测邀请 + 11/30 累计 8+ 企业 + 12/31 累计 10+ 企业签约

### 5.3 企业版定价模型

| 套餐 | 律师规模 | 年费 | 月费等价 | 权益 |
|------|---------|------|---------|------|
| **企业版基础** | 5-10 律师 | ¥1,500/律师/年 | ¥125/律师/月 | 基础 6 大模块 + 1v1 客户经理 + 月度培训 |
| **企业版专业** | 10-50 律师 | ¥1,750/律师/年 | ¥146/律师/月 | 全部模块 + 团队协作 + API 接入 |
| **企业版旗舰** | 50+ 律师 | ¥2,000/律师/年 | ¥167/律师/月 | 全部模块 + 私有部署 + 数据隔离 + 7×24 支持 |

> **企业版 10+ 签约目标 (12/31)**:
> - 基础版: 5+ 企业 × 7 律师 (avg) × ¥1,500 = ¥52,500/年 = ¥4,375/月
> - 专业版: 3+ 企业 × 30 律师 (avg) × ¥1,750 = ¥157,500/年 = ¥13,125/月
> - 旗舰版: 2+ 企业 × 75 律师 (avg) × ¥2,000 = ¥300,000/年 = ¥25,000/月
> - **总营收**: ¥510,000/年 = ¥42,500/月 (12/31)
> **加个人版 80 律师 × ¥99/月 = ¥7,920/月** → **总月营收 ¥50,420/月 (12/31)**

### 5.4 关键里程碑

| 里程碑 | 日期 | 验证 | 负责 agent |
|--------|------|------|-----------|
| **W18 9/15 L4/L5 预登记启动** | 9/15 | 2 律师 1v1 强推 + 律协沙龙 #2 | lex-bd |
| **W22 企业版 PRD v1.0** | 9/16-9/22 | 企业版 PRD § 1-12 + 定价模型 + 权限管理 | lex-pm + lex-bd |
| **W26 企业版 UI + 权限管理** | 10/16-10/22 | 团队管理 + 数据隔离 + 审计日志 | lex-coder + lex-security (新) |
| **W30 首批 5+ 企业签约** | 11/14-11/30 | 5+ 企业版基础 + 2+ 专业 + 1+ 旗舰 | lex-bd + lex-pm |
| **W35 10+ 企业签约完结** | 12/17-12/31 | 10+ 企业 + ¥42,500/月营收 | lex-bd + verifier |

> **Phase 5.4 关键风险**:
> - 企业版数据隔离 (lex-security 写权限管理 + 审计日志)
> - 企业版私有部署 (lex-electron + lex-coder 写部署脚本)
> - 企业决策长 (lex-bd 1v1 强推 + 律协沙龙)
> - 企业合规要求 (lex-security + lex-pm 跑合规审计)

### 5.5 关联任务

| Task | 派发 | 期望耗时 | 备注 |
|------|------|---------|------|
| `l4l5-preheat-915` | lex-bd | 1 天 (9/15) | 2 律师 1v1 强推 + 律协沙龙 #2 |
| `enterprise-prd-v1` | lex-pm + lex-bd | 1 周 (W22) | 企业版 PRD § 1-12 + 定价 |
| `enterprise-ui-permission` | lex-coder + lex-security | 1 周 (W26) | 团队管理 + 数据隔离 |
| `enterprise-sign-5` | lex-bd + lex-pm | 2 周 (W29-W30) | 5+ 基础 + 2+ 专业 + 1+ 旗舰 |
| `enterprise-sign-10` | lex-bd + verifier | 2 周 (W34-W35) | 10+ 企业 + ¥42,500/月 |

> **W18-W35 期望 commit**: 30+ commits 累计 (18 周 × 2 commits/周)

---


## 6. 招 3 Agent (Phase 5 配套)

> **Phase 5 配套 agent 招聘**: 3 个新 agent, 9/1-9/30 启动招聘 + 培训 + 上线.

### 6.1 lex-electron (Phase 5.2 必需)

| 维度 | 详情 |
|------|------|
| **scope** | Electron 桌面端打包 + 跨平台签名 + 自动更新 + 离线模式 |
| **核心工具** | electron-builder + electron-updater + asar + electron-forge |
| **关键交付** | Win/macOS/Linux 三端安装包 + 200 律师公测安装 + 离线模式 |
| **招聘时间** | 9/1-9/7 (W18) |
| **启动时间** | 9/8 (W18 周末) |
| **首个任务** | W22 electron-builder 集成 (9/16) |
| **培训需求** | Electron 13+ + electron-builder 24+ + Win/macOS/Linux 签名 + Squirrel 自动更新 |
| **考核 KPI** | 三端安装包成功率 100% + 50 律师公测安装 + 冷启动 < 2s |

### 6.2 lex-security (Phase 5.4 必需)

| 维度 | 详情 |
|------|------|
| **scope** | 企业版安全 + 权限管理 + 数据隔离 + 审计日志 + 合规审计 |
| **核心工具** | OAuth 2.0 + JWT + RBAC + audit log + SOC 2 + 等保 2.0 |
| **关键交付** | 企业版权限管理 + 数据隔离 + 审计日志 + 合规审计报告 |
| **招聘时间** | 9/8-9/14 (W19) |
| **启动时间** | 9/15 (W19 周末) |
| **首个任务** | W26 企业版权限管理 (10/16) |
| **培训需求** | OAuth 2.0 + JWT + RBAC + 审计日志 + 等保 2.0 三级 + SOC 2 Type I |
| **考核 KPI** | 企业版 10+ 签约 + 等保 2.0 三级认证 + SOC 2 Type I 报告 |

### 6.3 lex-mobile (Phase 6 储备, W35 启动)

| 维度 | 详情 |
|------|------|
| **scope** | 移动端 (iOS + Android) 律师 App + 微信小程序 + 钉钉/企业微信 集成 |
| **核心工具** | React Native 0.74+ / Flutter 3.16+ / 微信原生 / 钉钉开放平台 |
| **关键交付** | iOS + Android App + 微信小程序 + 钉钉集成 (Phase 6) |
| **招聘时间** | 12/1-12/14 (W33-W34) |
| **启动时间** | 12/15 (W34 周末) |
| **首个任务** | Phase 6.1 移动端 v1.0 (2027 Q1) |
| **培训需求** | React Native / Flutter + iOS/Android 商店上架 + 微信小程序审核 |
| **考核 KPI** | 移动端 100+ 律师激活 + App Store 4.5+ 评分 |

> **3 agent 招聘优先级**:
> - 9/1-9/7 招 lex-electron (Phase 5.2 必需, W22 启动)
> - 9/8-9/14 招 lex-security (Phase 5.4 必需, W26 启动)
> - 12/1-12/14 招 lex-mobile (Phase 6 储备, 2027 Q1 启动)
> **招聘平台**: 智联 + BOSS 直聘 + LinkedIn + 内推 (lex-bd 主导)

---

## 7. Phase 5 风险评估 + 应急备案

### 7.1 风险评估矩阵

| 风险 | 影响 | 概率 | 优先级 | 应急备案 |
|------|------|------|-------|---------|
| **React 18 重构延期** | 高 | 中 | P0 | 渐进式迁移 + Vue 3 保留兜底 |
| **Electron 跨平台签名失败** | 中 | 中 | P1 | 公测先发 Win 调试包 + macOS/Linux 延后 |
| **Rust 性能不达 3-5x** | 中 | 低 | P1 | 保留 Python 实现 + Rust 异步优化 |
| **企业版 10+ 签约不达标** | 高 | 中 | P0 | L4/L5 9/15 强推 + 律协沙龙 #2 + 10 月降级 ¥1,200/律师/年 |
| **lex-electron 招聘延期** | 中 | 中 | P1 | lex-coder 兼管 + 10 月内部转岗 |
| **lex-security 招聘延期** | 中 | 中 | P1 | lex-pm 兼管 + 等保 2.0 延后申请 |
| **3 new agent 培训失败** | 低 | 中 | P2 | 内部 mentor 1v1 + 1 周密集培训 |
| **Phase 5 KPI 不达标** | 高 | 中 | P0 | 12/31 目标延后 2027 Q1 + 关键路径加速 |

### 7.2 应急备案详情

| 备案 | 触发条件 | 启动时间 | 应急负责人 |
|------|---------|---------|-----------|
| **备案 1: Vue 3 保留** | React 18 重构延期 2 周+ | W19 评审 | lex-coder |
| **备案 2: Win 优先** | macOS/Linux 签名失败 | W23 评审 | lex-electron |
| **备案 3: Python 保留** | Rust 性能不达 3x | W28 评审 | lex-coder + lex-ai |
| **备案 4: 企业版降级** | 企业版 10+ 签约 < 5 | W30 评审 | lex-bd + lex-pm |
| **备案 5: 内部转岗** | lex-electron 招聘失败 | W20 评审 | Mavis (owner) |
| **备案 6: 等保延后** | lex-security 招聘失败 | W25 评审 | Mavis (owner) |
| **备案 7: KPI 延后** | 12/31 KPI < 80% | W34 评审 | 总指挥 |

> **风险评估原则**: Phase 5 4 个月 35 周, 7 个 P0/P1 风险, 7 个应急备案, 评审节点 (W19/W23/W25/W28/W30/W34) 提前 1 周评估.

---

## 8. 关联文档 + 数据 placeholder

### 8.1 关联文档

| 文档 | 路径 | 用途 |
|------|------|------|
| **Phase 4 完结报告** | `docs/phase4/phase4-final-report.md` v1.1 | 12 周回顾 + KPI 验证 |
| **Phase 4 Roadmap** | `docs/phase4-roadmap.md` v1.0 | 12 周 + Phase 5 衔接 |
| **PRD V5.0** | `PRD.md` v0.7.4 | § 5-12 模块 + KPI + Phase 5 |
| **W16 final report** | `docs/plans/plan-16-w16-final-report.md` | §4 W17 接力 |
| **W15 final report** | `docs/plans/plan-15-w15-final-report.md` | §4 W16 计划 |
| **W14 final report** | `docs/plans/plan-14-w14-final-report.md` | §4 W15 计划 |
| **W11 final report** | `docs/plans/plan-11-w11-final-report.md` | PRD v0.7.4 8 月底目标 |
| **kpi-snapshot-2026-08-09** | `docs/marketing/kpi-snapshot-2026-08-09.md` v1.0/v1.1 | 8/9 节点 30 律师验证 |
| **kpi-dashboard-726-809** | `docs/marketing/kpi-dashboard-726-809.md` v1.0 | 7/26-8/9 KPI 9 节 |
| **l4l5-triggers-runbook** | `docs/marketing/l4l5-triggers-runbook.md` v1.0 | 8/25 L4/L5 转化 + 9/15 延期 |
| **recruit-1000-runbook** | `docs/marketing/recruit-1000-runbook.md` v1.0 | 5 渠道 1200 律师 |
| **launch-runbook-final** | `docs/marketing/launch-runbook-final-2026-07-26.md` v1.0 | 7/26 启动仪式 535 行 |

### 8.2 数据 placeholder (9/1-12/31 期间)

> **严禁 fabricate**: 当前时间 2026-06-30, 距 9/1 还有 63 天. 所有 9/1-12/31 期间实际数字 placeholder, owner 9/1 当天实测填实.
>
> **placeholder 内容**:
> - 9/30 80 律师付费 + ¥15,000 月营收 + ¥18 万 ARR
> - 10/31 120 律师付费 + ¥25,000 月营收 + ¥30 万 ARR
> - 11/30 160 律师付费 + ¥33,000 月营收 + ¥40 万 ARR
> - 12/31 200 律师付费 + ¥40,000 月营收 + ¥48 万 ARR (10+ 企业签约)
> - 3 agent 招聘时间 + 培训时间 + 上线时间
> - React 18 重构覆盖率 + Electron 安装包 + Rust 核心覆盖率

> **owner 填实节奏**:
> - 9/1 W18 启动: 9 月目标 + W18-W21 计划
> - 10/1 W22 启动: 10 月目标 + W22-W26 计划
> - 11/1 W27 启动: 11 月目标 + W27-W30 计划
> - 12/1 W31 启动: 12 月目标 + W31-W35 计划
> - 12/31 W35 完结: 4 个月累计 + Phase 5 KPI 验证

### 8.3 更新频率

- **Phase 5 prep 文档 v1.0 (W17)**: 完结报告 + 启动准备, 2026-06-30 owner 拍板
- **Phase 5 prep 文档 v1.1 (W18)**: 9/1 W18 启动后, 9 月目标 + W18-W21 计划填实
- **Phase 5 prep 文档 v1.2 (W22)**: 10/1 W22 启动后, 10 月目标 + W22-W26 计划填实
- **Phase 5 prep 文档 v1.3 (W27)**: 11/1 W27 启动后, 11 月目标 + W27-W30 计划填实
- **Phase 5 prep 文档 v1.4 (W31)**: 12/1 W31 启动后, 12 月目标 + W31-W35 计划填实
- **Phase 5 完结报告 (W35)**: 12/31 完结, 4 个月累计 + Phase 5 KPI 验证

---

## 9. 文档版本与归档

- **版本**: v1.1 (W17 v1.0 基础 + W18 接力增量 § 10-12, 2026-06-30)
- **W17 v1.0 状态**: Phase 5 准备就绪, 4 个阶段 + 3 agent 招聘 + 9/1-12/31 时间线 + 风险评估
- **W18 v1.1 增量**: 补充 § 10 W18 l4l5-enterprise-915 接力 (9/15 Phase 5.4 L4/L5 企业版上线) + § 11 W18 phase5-react-start 接力 (9/1 Phase 5.1 React 18 + TS + 3 模块) + § 12 3 agent 招聘时间表 (W18 9/1 招 lex-electron + W19 招 lex-security + W33 招 lex-mobile)
- **状态**: Phase 5 准备就绪 + W18 接力链路对齐, 9/1 owner 启动 W19 plan YAML
- **归档路径**: `docs/phase4/phase5-prep.md`
- **数据 placeholder**: 9/1-12/31 期间所有数字 placeholder, owner 9/1 实测填实
- **更新频率**: 每月 1 号更新当月目标 + 计划 + W18 6 task 整体 (kpi-verify-809 + l4l5-execute-825 + phase4-final-831 + l4l5-enterprise-915 + skill3-gradual + phase5-react-start) 跨 plan 接力
- **关联文档**: phase4-final-report.md v1.1 (W18 接力) + phase4-roadmap.md v1.0 + PRD V5.0 § 12 + W18 6 task YAML (5ac2adb) + W18 kpi-verify-runbook-2026-08-09.md v1.0 (fe0ef99) + W18 l4l5-execute-runbook-2026-08-25.md v1.0 (083cf0b) + W18 phase4-final-runbook-2026-08-31.md v1.0 (本 commit)

> **Phase 5 准备文档 v1.1 完整归档**. W17 接力 W16 phase4-close-831 retry + W18 接力 W17 增量 § 10-12 (W18 6 task 整体 + W19 3 task 接力 + 3 agent 招聘时间表).

---

## 10. W18 接力 (W18 6 task 整体 + 跨 plan 链接)

> **W18 (Plan 18) 6 task 整体 (W18 YAML 5ac2adb 落档, 8/9 + 8/25 + 8/31 实测 + 9/1 Phase 5.1 + 9/15 Phase 5.4)**, W17 v1.0 升级到 v1.1 后跟 W18 6 task 完整对接.

### 10.1 W18 6 task 接力链路

| # | Task | 负责 agent | 关键时间 | 关键交付 | 接力到 |
|---|------|----------|---------|---------|-------|
| 1 | **kpi-verify-809** | lex-bd | 8/9 09:00 owner 实测 | 30 律师 + ¥4,020 实测填实 + 6 SQL + runbook 450 行 | W18 l4l5-execute-825 + W18 phase4-final-831 |
| 2 | **l4l5-execute-825** | lex-bd | 8/25 14:00-19:00 owner 主持 | L4/L5 2 律师付费落地 + 公测 day 23 报告 + 9/15 企业版预登记 waitlist | W18 phase4-final-831 + W19 l4l5-enterprise-915 |
| 3 | **phase4-final-831** | lex-bd | 8/31 09:00 owner 实测 | 50 律师 + ¥5 万+ ARR 实测 + 公测 day 37 报告 + Phase 4 完结归档 | W19 phase5-react-start + W19 l4l5-enterprise-915 |
| 4 | **l4l5-enterprise-915** | lex-bd | 9/15 L5 1v1 微信强推 + 企业版上线 | L4/L5 9/15 企业版预登记 + ¥1,500-2,000/律师/年签约 5+ | W19 Phase 5.4 (10+ 企业签约 12/31) |
| 5 | **skill3-gradual** | lex-ai | 8/15 v2.0 10% 灰度 → 9/1 50% 灰度 | Skill 3 律师函 v2.0 灰度 (W15 commit 3d429cd + W15 commit e3f0940) | W21 80%+ 灰度 + W23 100% 灰度 |
| 6 | **phase5-react-start** | lex-coder | 9/1 启动 + 9/15 完成 50% | React 18 + TS + 3 模块 (Workstation + ContractReview + EvidenceList) | W20 80% + W21 单元测试 80%+ |

> **W18 6 task 接力链路**: kpi-verify-809 (8/9) → l4l5-execute-825 (8/25) → phase4-final-831 (8/31) + skill3-gradual (8/15-9/1) → l4l5-enterprise-915 (9/15) + phase5-react-start (9/1)
> **W18 6 task 完整接力**: 3 个公测期节点 (8/9 + 8/25 + 8/31) + 3 个 Phase 5 启动任务 (9/1 Phase 5.1 + 9/1 skill3 50% 灰度 + 9/15 Phase 5.4 企业版)
> **W18 6 task 跟 W19 3 task 接力**: W18 phase4-final-831 → W19 phase5-prep (本 v1.1 文档) + W19 phase5-react-start + W19 l4l5-enterprise-915

### 10.2 W18 6 task vs W19 3 task 跨 plan 接力清单

| W18 task | W18 接力到 W19 task | 关键交付 | 截止时间 |
|---------|---------------------|---------|----------|
| kpi-verify-809 (8/9 09:00) | W18 l4l5-execute-825 + W18 phase4-final-831 | 30 律师 + ¥4,020 实测填实 + 6 SQL + 距月底增量 20-26 律师 + ¥10,436-14,000 ARR 缺口 | 8/9 当天 23:00 |
| l4l5-execute-825 (8/25 14:00-19:00) | W18 phase4-final-831 + W19 l4l5-enterprise-915 | L4/L5 2 律师付费落地 + 9/15 企业版预登记 waitlist + 朋友推荐 6 名新律师 | 8/25 19:00 + 8/31 24:00 |
| phase4-final-831 (8/31 09:00) | W19 phase5-prep (本 v1.1) + W19 phase5-react-start + W19 l4l4-enterprise-915 | 50 律师 + ¥5 万+ ARR 实测 + Phase 4 完结归档 | 8/31 23:45 |
| skill3-gradual (8/15 v2.0 10% → 9/1 50%) | W19 skill3-50pct-gradual | Skill 3 律师函 v2.0 50% 灰度 + 反馈驱动 v2.1 | 9/1 9:00 |
| l4l5-enterprise-915 (9/15 L5 1v1 强推 + 企业版上线) | W19 Phase 5.4 接力 (10+ 企业签约) | L5 9/15 1v1 微信强推 + 企业版上线 + ¥1500-2000/律师/年 + 首批 5 企业签约 | 9/15 19:00 + 10/31 |
| phase5-react-start (9/1 启动 + 9/15 50%) | W19 phase5-react-50pct + W19 phase5-react-80pct | React 18 + TS 3 模块 (Workstation + ContractReview + EvidenceList) + 50% 重构覆盖 | 9/15 + 9/30 |

> **W18 6 task 跨 plan 接力 6 接点点** (W18 6 → W19 3 + W19 3 task 接力):
> - (1) W18 kpi-verify-809 (8/9) → W18 l4l5-execute-825 (8/25) + W18 phase4-final-831 (8/31)
> - (2) W18 l4l5-execute-825 (8/25) → W18 phase4-final-831 (8/31) + W19 l4l5-enterprise-915 (9/15)
> - (3) W18 phase4-final-831 (8/31) → W19 phase5-prep (本 v1.1) + W19 phase5-react-start (9/1) + W19 l4l5-enterprise-915 (9/15)
> - (4) W18 skill3-gradual (8/15-9/1) → W19 skill3-50pct-gradual (9/1-9/30)
> - (5) W18 l4l5-enterprise-915 (9/15) → W19 Phase 5.4 接力 (10+ 企业签约 12/31)
> - (6) W18 phase5-react-start (9/1-9/15) → W19 phase5-react-50pct + 80pct (9/15-9/30)

### 10.3 W18 6 task 跟 PRD V5.0 § 12 Phase 5 计划对应

| PRD § 12 Phase 5 阶段 | 截止 | W18 6 task 接力 | W19 接力 |
|----------------------|------|----------------|---------|
| Phase 5.1 React 18 + TS | 9/15 (50%) + 9/30 (80%) + 12/31 (90%) | W18 phase5-react-start (9/1 启动 + 9/15 50%) | W19 phase5-react-50pct + 80pct |
| Phase 5.2 Electron 打包 | 9/16 (W22) + 9/30 (W23) + 10/15 (W25) | W19 phase5-electron-setup (W22 9/16 启动) | W19 phase5-electron-cross + offline |
| Phase 5.3 Rust 核心 | 10/16 (W26) + 11/30 (W30) | W19 phase5-rust-toolchain (W26 10/16 启动) | W19 phase5-rust-paddle + fts5 + lancedb |
| Phase 5.4 L4/L5 企业版 | 9/15 预登记 + 10/31 首批 5 签约 + 12/31 10+ 签约 | W18 l4l5-enterprise-915 (9/15) | W19 phase5-enterprise-5 + 10 |

> **W18 6 task 完整覆盖 PRD § 12 全部 4 个 Phase 5 阶段**, 跟 W17 v1.0 § 1.1 Phase 5 时间窗口表 (Phase 5.1-5.4) 100% 对齐.

---

## 11. W18 phase5-react-start + l4l5-enterprise-915 接力细节

### 11.1 W18 phase5-react-start (9/1 启动 + 9/15 50%)

> **Phase 5.1 React 18 + TS 重构启动 (W18 task phase5-react-start, lex-coder 主导 + lex-design 协作)**:

| 维度 | Phase 4 (Vue 3) | Phase 5.1 (React 18 + TS) | 9/1 启动 | 9/15 50% 截止 |
|------|----------------|--------------------------|---------|--------------|
| **3 模块首批迁移** | Workstation.vue + ContractReview.vue + EvidenceList.vue | Workstation.tsx + ContractReview.tsx + EvidenceList.tsx | 9/1 启动 | 9/15 完成 50% |
| **设计系统迁移** | Element Plus | Ant Design 5 / shadcn/ui | 9/1 设计 tokens | 9/7 完成 |
| **类型系统** | JavaScript + JSDoc | TypeScript 5.0+ strict | 9/1 tsconfig + .eslintrc | 9/15 严格模式 |
| **状态管理** | Pinia | Zustand + React Query | 9/8 集成 | 9/15 状态管理迁移 |
| **路由** | Vue Router 4 | React Router 6 | 9/8 集成 | 9/15 路由迁移 |
| **测试** | Vitest + Vue Test Utils | Vitest + React Testing Library | 9/15 起步 | 9/22 完成 50% |

> **W18 phase5-react-start 关键里程碑 (W18 task)**:
> - W18-W19 (9/1-9/15): 3 模块 (Workstation + ContractReview + EvidenceList) 完成迁移 + 设计系统 v2.0
> - W20 (9/16-9/22): 招募 + Dashboard + Onboarding 模块迁移
> - W21 (9/23-9/30): 单元测试 80% + React Testing Library 集成

### 11.2 W18 l4l5-enterprise-915 (9/15 L5 1v1 微信强推 + 企业版上线)

> **Phase 5.4 L4/L5 企业版上线 (W18 task l4l5-enterprise-915, lex-bd 主导 + lex-pm 协作 + lex-security 配套)**:

| 维度 | L4/L5 8/25 转化 (W18 l4l5-execute-825) | L4/L5 9/15 企业版上线 (W18 l4l5-enterprise-915) | 9/15 截止 |
|------|----------------------------------------|------------------------------------------------|----------|
| **企业版 PRD v1.0** | - | PRD § 1-12 (W19 9/16-9/22) + 定价模型 + 权限管理 | 9/15 完成 |
| **企业版 UI + 权限管理** | - | 团队管理 + 数据隔离 + 审计日志 (W26 10/16-10/22) | 10/22 完成 |
| **L4/L5 1v1 微信强推** | L4/L5 8/25 14:00-19:00 主持 (W18 l4l5-execute-825 083cf0b) | L5 9/15 14:00-19:00 强推 + L4 9/15 1v1 微信 | 9/15 当天 |
| **企业版首批 5+ 签约** | - | 首批 5+ 企业版基础 (¥1,500/律师/年) + 2+ 专业 (¥1,750) + 1+ 旗舰 (¥2,000) | 10/31 截止 |
| **企业版 10+ 签约完结** | - | 10+ 企业签约 + ¥42,500/月营收 | 12/31 截止 |

> **W18 l4l5-enterprise-915 关键里程碑 (W18 task)**:
> - 9/15 L5 1v1 微信强推 (L5 未转化 8/25 之前) + L4 9/15 1v1 微信 (W19 phase5-enterprise-prep 接力)
> - 9/15 企业版上线 (W19 l4l5-enterprise-online 接力)
> - 9/30 首批 5+ 企业签约 (W19 phase5-enterprise-sign-5 接力)
> - 12/31 10+ 企业签约 + ¥42,500/月 (W19 phase5-enterprise-sign-10 接力)

---

## 12. 3 agent 招聘时间表 (W18 9/1 + W19 + W33)

> **Phase 5 配套 3 agent 招聘时间表** (复用 W17 v1.0 § 6 3 agent 招聘 + W18 6 task 接力):

### 12.1 lex-electron (Phase 5.2 必需, W18 9/1 启动招聘)

| 维度 | W17 v1.0 计划 | W18 v1.1 实际 | 差距 |
|------|--------------|---------------|------|
| **招聘时间** | 9/1-9/7 (W18) | 9/1-9/7 (W18, 跟 W18 phase5-react-start 并行) | ✅ 一致 |
| **启动时间** | 9/8 (W18 周末) | 9/8 (W18 周末) | ✅ 一致 |
| **首个任务** | W22 electron-builder 集成 (9/16) | W19 phase5-electron-setup (W22 9/16) | ✅ 一致 |
| **考核 KPI** | 三端安装包成功率 100% + 50 律师公测安装 + 冷启动 < 2s | 同 + 9/15 L4/L5 9/15 企业版上线 (W18 l4l5-enterprise-915) | ✅ 升级 (新增企业版上线) |
| **W18 接力** | - | W18 phase4-final-831 → W19 phase5-electron-setup 接力 3 接点点 | 🆕 W18 v1.1 新增 |

### 12.2 lex-security (Phase 5.4 必需, W19 招 + 启动)

| 维度 | W17 v1.0 计划 | W18 v1.1 实际 | 差距 |
|------|--------------|---------------|------|
| **招聘时间** | 9/8-9/14 (W19) | 9/8-9/14 (W19) | ✅ 一致 |
| **启动时间** | 9/15 (W19 周末) | 9/15 (W19 周末, 跟 W18 l4l5-enterprise-915 同期) | ✅ 一致 |
| **首个任务** | W26 企业版权限管理 (10/16) | W19 phase5-enterprise-permission (W26 10/16) | ✅ 一致 |
| **考核 KPI** | 企业版 10+ 签约 + 等保 2.0 三级认证 + SOC 2 Type I 报告 | 同 + W18 l4l5-enterprise-915 企业版上线 9/15 | ✅ 升级 (新增企业版上线) |
| **W18 接力** | - | W18 l4l5-enterprise-915 (9/15) → W19 lex-security-招聘 → W19 phase5-enterprise-permission | 🆕 W18 v1.1 新增 |

### 12.3 lex-mobile (Phase 6 储备, W33-W34 招 + 启动)

| 维度 | W17 v1.0 计划 | W18 v1.1 实际 | 差距 |
|------|--------------|---------------|------|
| **招聘时间** | 12/1-12/14 (W33-W34) | 12/1-12/14 (W33-W34) | ✅ 一致 |
| **启动时间** | 12/15 (W34 周末) | 12/15 (W34 周末, 跟 W19 phase5-enterprise-sign-10 同期) | ✅ 一致 |
| **首个任务** | Phase 6.1 移动端 v1.0 (2027 Q1) | W35 phase6-mobile-v1-setup (2027 Q1) | ✅ 一致 |
| **考核 KPI** | 移动端 100+ 律师激活 + App Store 4.5+ 评分 | 同 + W19 phase5-enterprise-sign-10 12/31 10+ 企业签约 | ✅ 升级 (新增企业签约 12/31) |
| **W18 接力** | - | W18 phase4-final-831 (8/31) → W35 phase6-mobile 接力 1 接点点 | 🆕 W18 v1.1 新增 |

> **3 agent 招聘时间表 (W18 v1.1 升级)**:
> - 9/1-9/7 (W18) 招 lex-electron (跟 phase5-react-start 并行) → 9/8 启动 → W22 首个任务
> - 9/8-9/14 (W19) 招 lex-security (跟 l4l5-enterprise-915 同期) → 9/15 启动 → W26 首个任务
> - 12/1-12/14 (W33-W34) 招 lex-mobile (跟 phase5-enterprise-sign-10 同期) → 12/15 启动 → W35 首个任务
>
> **W18 v1.1 增量**: 3 agent 招聘跟 W18 6 task 整体对齐, 跟 W17 v1.0 计划一致 + 新增 W18 6 task 接力 (W18 phase4-final-831 + l4l5-enterprise-915 + phase5-react-start)。

---

**Phase 5 准备文档 v1.1 完结 (W17 v1.0 基础 + W18 接力增量 § 10-12). W19 (Plan 19) 启动由 owner 主动调度 (9/1) 准备 Phase 5.1 React 18 + TS 重构 + Phase 5.2 Electron 打包 + Phase 5.3 Rust 核心 + Phase 5.4 L4/L5 企业版上线 + 3 agent 招聘 (lex-electron 9/1 + lex-security 9/8 + lex-mobile 12/1).**
