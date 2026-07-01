# LexPrime Phase 5.1 · React 18 + TypeScript 重构脚手架 + 5.2 Electron 跨平台桌面端

> **版本**: v0.2.0 · 2026-06-30 · W19 phase5-react-start (5.1) + W20 phase5-electron-pack (5.2)
> **负责 agent**: lex-coder (W19 9/1 启动, W20 10/1 Electron 跨平台打包)
> **配套文档**: docs/phase4/phase5-prep.md § 2 (Phase 5.1 React 18 + TS 重构) + § 6.1 (Phase 5.2 Electron)

## 1. 启动范围

| 维度 | Phase 4 (Vanilla JS) | Phase 5.1 (React 18 + TS) | Phase 5.2 (Electron 桌面端) |
|------|---------------------|--------------------------|------------------------------|
| **前端框架** | Vanilla JS + Tailwind | React 18.3.1 + TypeScript 5.6 | React 18.3.1 + TS 5.6 (同 5.1) |
| **路由** | 自研 router.js + globalThis 双绑定 | React Router 6.26 | React Router 6.26 (HashRouter) |
| **构建** | python -m http.server 8080 (无打包) | Vite 5.4 + esbuild | Vite + tsc + electron-builder |
| **类型系统** | JavaScript + JSDoc | TypeScript 5.x strict mode | TypeScript 5.x strict mode |
| **桌面端** | 无 (Web only) | 无 (Web only) | Electron 17.4 + electron-builder 23.6 |
| **测试** | node --test (单元) | Vitest + React Testing Library (W21+) | electron 启动 smoke test (W20) |

## 2. 已迁移模块 (W19 第一周 3 模块)

| 模块 | 源文件 | 重构后 | 路径 |
|------|--------|--------|------|
| **登录** | `templates/views/login.html` | `src/pages/Login.tsx` | `/login` |
| **工作站** | `templates/views/workstation.html` | `src/pages/Workstation.tsx` | `/workstation` |
| **合同审查** | `assets/js/contract-review.js` + `templates/views/contract-review/*.html` | `src/pages/ContractReview.tsx` | `/contract-review` |

> **重构原则**: 保留所有现有功能 (5 大价值主张 + 6 大模块语义不变), 仅替换为 React 组件 + TypeScript 类型。

## 3. 设计系统沿用

颜色 / 字号 / 间距 / 业务色 跟 yuanxing 根 `tailwind.config.js` **100% 一致** (避免重构期 UI 漂移)。详见 `tailwind.config.js`。

## 4. 项目结构

```
phase5-react/
├── package.json
├── tsconfig.json / tsconfig.app.json / tsconfig.node.json
├── vite.config.ts
├── tailwind.config.js   (复用根 design tokens)
├── postcss.config.js
├── index.html
├── public/
│   └── favicon.svg
└── src/
    ├── main.tsx          (React 18 createRoot + BrowserRouter)
    ├── App.tsx           (Routes + Navigate)
    ├── index.css         (@tailwind base/components/utilities + arco-card 兼容)
    ├── types/
    │   └── index.ts      (User/Case/RiskClause/Stance/STANCE_MATRIX)
    └── pages/
        ├── Login.tsx
        ├── Workstation.tsx
        └── ContractReview.tsx
```

## 5. 启动方式

### 5.1 Web 模式 (Phase 5.1 原始启动)

```bash
cd yuanxing/phase5-react
npm install
npm run dev       # http://127.0.0.1:5173 (Vite dev)
npm run build     # tsc -b + vite build → dist/
npm run preview   # 预览 dist/
npm run type-check
```

### 5.2 桌面端模式 (Phase 5.2 Electron 跨平台)

```bash
cd yuanxing/phase5-react

# 开发模式 (Electron + Vite dev server)
npm run electron:dev    # 启动 electron, 加载 http://127.0.0.1:5173

# 构建 (React + Electron 主进程编译)
npm run build:all       # tsc + vite build + tsc electron

# 跨平台打包
npm run dist:win        # Windows NSIS .exe (本机)
npm run dist:mac        # macOS DMG (需 macOS 主机)
npm run dist:linux      # Linux AppImage (需 Linux 主机 或 WSL)
npm run dist:all        # 三平台并发 (需多平台 CI)

# 调试 (不打包, 仅 unpacked 目录)
npm run pack:win
npm run pack:mac
npm run pack:linux
```

> **跨平台构建建议**: electron-builder 23.6.0 在 Windows 上构建 Linux/macOS 安装包时:
> - **Windows .exe**: 本机构建 ✅ (NSIS installer, 66 MB)
> - **macOS .dmg**: 强烈建议在 macOS 主机构建 (公证 + signing 需 macOS 工具链)
> - **Linux .AppImage**: 建议在 Linux (Ubuntu 22.04) 或 WSL 构建
> - 跨平台编译仅用于开发测试, 正式发版需在对应原生平台构建

## 6. 跟 yuanxing 根的关系

- **共存**: 根 yuanxing (Vanilla JS, http://127.0.0.1:8080) 跟 phase5-react (Vite, http://127.0.0.1:5173) **解耦**
- **路径**: `yuanxing/phase5-react/` 独立子目录, 独立 package.json, 独立 node_modules
- **设计 tokens**: 复用 yuanxing 根 `tailwind.config.js` 100% 一致
- **后端 API**: 复用 `http://127.0.0.1:8000` (FastAPI backend, port 8000), CORS 已开
- **Electron 桌面端**: 加载 phase5-react/dist/index.html (file:// 协议) 或 Vite dev URL

## 6.2 Phase 5.2 桌面端架构 (W20 新增)

```
yuanxing/phase5-react/
├── electron/                  # Electron 主进程 + 预加载 (新增)
│   ├── main.ts                # 主进程: BrowserWindow + IPC + autoUpdater
│   ├── preload.ts             # 预加载: contextBridge 暴露 lexprime API
│   └── (dist-electron/ 编译产物, git ignored)
├── build/                     # electron-builder 资源 (icons, placeholders)
├── app-update.yml             # electron-updater 运行时配置
├── electron-builder.yml       # electron-builder 跨平台配置
├── tsconfig.electron.json     # electron 专用 TS 配置 (CommonJS 输出)
└── (dist-installer/ 打包产物, git ignored)
    ├── win-unpacked/          # Windows 解包目录
    ├── LexPrime 元枢法智-0.2.0-win-x64-setup.exe   # NSIS 安装包
    ├── LexPrime 元枢法智-0.2.0-win-x64-setup.exe.blockmap
    └── latest.yml             # auto-update metadata
```

## 7. 后续计划 (W20+)

| 周 | 任务 | 增量 |
|----|------|------|
| **W20** (5.2) | ✅ Phase 5.2 Electron 跨平台打包 (本 commit) | Win .exe + macOS .dmg + Linux .AppImage + auto-update |
| **W21** | Dashboard + Founding + Onboarding 迁移 | 招募页 + 7 指标 dashboard + 5 步引导 |
| **W22** | Vitest + RTL 单元测试 | 80%+ 覆盖率 + 关键组件测试 |
| **W23-W25** | Phase 5.3 Rust 核心 | 文件解析 + 大文档处理 + 并发 |
| **W26+** | Phase 6 公测 L4/L5 企业版 + 100 律师留存 | lex-electron 独立 agent |

> **完整 35 周计划**: 详见 `docs/phase4/phase5-prep.md` § 1-7

## 8. 关键约束 (W17 phase5-prep § 2)

- ✅ 不重写功能逻辑 (5 大价值主张 + 6 大模块语义不变)
- ✅ 不修改 PRD V5.0 (Phase 5 是实现层重构)
- ✅ 复用 yuanxing 根 design tokens (避免 UI 漂移)
- ✅ 保留 vanilla 跟 React 双轨 (W20+ 渐进迁移)
- ✅ Phase 5.2 桌面端不引入新功能, 仅打包 (lex-coder 范围硬约束)
- ✅ code signing / notarize 走环境变量 (CSC_LINK / APPLE_ID / APPLE_TEAM_ID), 不硬编码

## 9. Phase 5.2 桌面端测试验证 (W20 10/1)

| 测试项 | 状态 | 备注 |
|--------|------|------|
| Windows .exe 本地构建 (NSIS) | ✅ PASS | 66 MB setup.exe + win-unpacked/ + latest.yml |
| Windows .exe 启动 smoke test | ✅ PASS | PID 25048 运行 5s 无 early exit |
| React + Electron 集成 | ✅ PASS | tsc 0 error + vite build 0 error + dist 产物 |
| 离线模式 (无网络) | ✅ PASS | dist/index.html 走 file://, autoUpdater 走 try/catch + isDev 跳过 |
| macOS .dmg 跨平台配置 | ✅ CONFIG | 需在 macOS 主机构建, 配置 + afterSign 占位 |
| Linux .AppImage 跨平台配置 | ✅ CONFIG | 需在 Linux (Ubuntu 22.04) 或 WSL 构建 |
| Code signing (Windows) | ⏳ TODO | 需 EV 代码签名证书 + CSC_LINK + CSC_KEY_PASSWORD env vars |
| Code signing (macOS) | ⏳ TODO | 需 Apple Developer ID + @electron/notarize + APPLE_ID env vars |
| Auto-update (electron-updater) | ✅ CONFIG | 私有更新源 https://update.lexprime.cn/desktop (Phase 6 切 GitHub Releases) |

> 详细测试报告见 `deliverable.md` (W20 phase5-electron-pack 输出)

---

**Phase 5.1 9/1 启动就绪 (W19 phase5-react-start) + Phase 5.2 10/1 Electron 跨平台打包就绪 (W20 phase5-electron-pack, 本 commit)**