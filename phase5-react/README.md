# LexPrime Phase 5.1 · React 18 + TypeScript 重构脚手架

> **版本**: v0.1.0 · 2026-06-30 · W19 phase5-react-start 启动
> **负责 agent**: lex-coder (W19 9/1 启动, Mavis owner 协同)
> **配套文档**: docs/phase4/phase5-prep.md § 2 (Phase 5.1 React 18 + TS 重构)

## 1. 启动范围

| 维度 | Phase 4 (Vanilla JS) | Phase 5.1 (React 18 + TS) |
|------|---------------------|--------------------------|
| **前端框架** | Vanilla JS + Tailwind | React 18.3.1 + TypeScript 5.6 |
| **路由** | 自研 router.js + globalThis 双绑定 | React Router 6.26 |
| **构建** | python -m http.server 8080 (无打包) | Vite 5.4 + esbuild |
| **类型系统** | JavaScript + JSDoc | TypeScript 5.x strict mode |
| **测试** | node --test (单元) | Vitest + React Testing Library (W21+) |

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

```bash
cd yuanxing/phase5-react
npm install
npm run dev       # http://127.0.0.1:5173
npm run build     # tsc -b + vite build → dist/
npm run preview   # 预览 dist/
npm run type-check
```

## 6. 跟 yuanxing 根的关系

- **共存**: 根 yuanxing (Vanilla JS, http://127.0.0.1:8080) 跟 phase5-react (Vite, http://127.0.0.1:5173) **解耦**
- **路径**: `yuanxing/phase5-react/` 独立子目录, 独立 package.json, 独立 node_modules
- **设计 tokens**: 复用 yuanxing 根 `tailwind.config.js` 100% 一致
- **后端 API**: 复用 `http://127.0.0.1:8000` (FastAPI backend, port 8000), CORS 已开

## 7. 后续计划 (W20+)

| 周 | 任务 | 增量 |
|----|------|------|
| **W20** | Dashboard + Founding + Onboarding 迁移 | 招募页 + 7 指标 dashboard + 5 步引导 |
| **W21** | Vitest + RTL 单元测试 | 80%+ 覆盖率 + 关键组件测试 |
| **W22-W25** | Phase 5.2 Electron 打包 (lex-electron 新 agent) | Win/macOS/Linux 三端安装包 |

> **完整 35 周计划**: 详见 `docs/phase4/phase5-prep.md` § 1-7

## 8. 关键约束 (W17 phase5-prep § 2)

- ✅ 不重写功能逻辑 (5 大价值主张 + 6 大模块语义不变)
- ✅ 不修改 PRD V5.0 (Phase 5 是实现层重构)
- ✅ 复用 yuanxing 根 design tokens (避免 UI 漂移)
- ✅ 保留 vanilla 跟 React 双轨 (W20+ 渐进迁移)

---

**Phase 5.1 9/1 启动就绪 (W19 phase5-react-start 完成 1 commit + push)**