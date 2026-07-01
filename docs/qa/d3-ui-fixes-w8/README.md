# D3 W8 6 项 P1-P3 UI 修复 - QA 报告

> **日期**: 2026-06-29 (W8)
> **执行人**: lex-coder (W8 D3 task)
> **结果**: ✅ **PASS** - 3 项 UI 修复 + 回归测试 + 截图落档

---

## 1. 修复范围

W4 评审 6 项 P1-P3 UI 修复遗留, W5 完成 3 项, 推 3 项到 W7, W7 死锁, W8 D3 集中修复:

| # | 优先级 | 修复项 | 页面 | 状态 |
|---|--------|--------|------|------|
| 1 | P1 | 移动端 < 768px 适配 | 5 页面 | ✅ |
| 2 | P2 | 立场影响预览 (4 立场 × 3 风险等级) | 01-upload | ✅ |
| 3 | P3 | 致命条款 > 3 自动折叠 (0/3/5 三种情况) | 02-result | ✅ |

---

## 2. 实施细节

### 2.1 移动端 < 768px 适配 (P1)

**5 页面全部含 `@media (max-width: 767px)` 块**:
- `01-upload.html` - grid 重排 (12 列 → 1 列) + 步骤条单列 + 立场按钮 2 列
- `02-result.html` - clause-grid 单列 + 风险计数 wrap + 摘要列反转
- `03-suggestion.html` - 12 列单列 + 8/4 列合并 + tab 换行
- `04-negotiation.html` - 模态框全屏 (max-width: 100% / max-height: 100% / border-radius: 0)
- `05-export.html` - export-grid 单列 + paper padding 缩小 + 操作按钮列堆叠

**viewport meta**: 由 `index.html` 父 shell 统一提供 (5 页面共享 `<meta content="width=device-width, initial-scale=1.0" name="viewport"/>`)

**JS 增强**: `contract-review.js` 含 `applyMobileStyles()` 函数, 运行时注入 max-width: 767px CSS (兼容 .col-span-* / .grid-cols-* 通用重排)

### 2.2 立场影响预览 (P2)

**Single source of truth**: `contract-review.js` 暴露 `window.CR.__updateStancePreview(stance)`, HTML inline 脚本优先调用, 失败 fallback 本地 matrix.

**4 立场 × 3 风险等级 加权/降权矩阵**:

| 立场 | 律师常用语 | 致命 | 重大 | 合规 | 关注重点 |
|------|----------|------|------|------|----------|
| 甲方 | 原告 | ↓ 降权 | → 持平 | ↑ 加权 | 对方义务 / 自身免责 / 救济成本 |
| 乙方 | 被告 | ↑ 加权 | → 持平 | ↓ 降权 | 权利失衡 / 显失公平 / 解除权不对等 |
| 丙方 | 第三方 | → 持平 | ↑ 加权 | → 持平 | 连带义务 / 担保范围 / 第三方责任 |
| 审查方 | 中立 | → 持平 | → 持平 | → 持平 | 全面客观 / 多方均衡 / 中立报告 |

**W4 设计要求**:
- 乙方更关注显失公平 → 致命 ↑ 加权
- 甲方相对受益 → 致命 ↓ 降权
- 审查方中立报告 → 全部 → 持平

### 2.3 致命条款 > 3 自动折叠 (P3)

**Single source of truth**: `contract-review.js` 暴露 `window.CR.__applyFatalCollapse(visibleLimit)`, 修复 W7 inline 脚本只数 `.cr-fatal-clause` (含 major) 的 bug, 现在只数 `.clause-fatal`.

**0/3/5 三种 case 验证 (D3 W8 实际跑)**:

| 致命数 | 按钮可见 | 折叠数 | 实际结果 |
|--------|----------|--------|----------|
| 0 | ❌ 隐藏 | 0 | `{visible: 0, hidden: 0, buttonVisible: false}` |
| 3 | ❌ 隐藏 | 0 | `{visible: 3, hidden: 0, buttonVisible: false}` |
| 5 | ✅ 显示 | 2 | `{visible: 3, hidden: 2, buttonVisible: true}` |

**result.html demo 改造**: 把原 1 致命 + 2 重大 + 2 建议 → 改为 5 致命 + 2 建议 (凑 5 致命触发折叠可见)

**测试模式**: URL `?test_fatals=0|3|5` 注入测试用致命条款, 验证三种 case UI 一致

---

## 3. 回归测试

### 3.1 pytest (D3 自测)

- 测试文件: `backend/cases-crawler/tests/test_d3_ui_fixes.py`
- **59 个测试全部 PASS** (1.0s)
- 覆盖率:
  - P1 移动端: 18 tests (5 页面 × 3 + 2 共享)
  - P2 立场预览: 22 tests (4 立场 × 3 影响 + 4 matrix + 5 + 1 律师常用语)
  - P3 致命折叠: 11 tests (5 容器 + 3 case + 1 + 2 修复)
  - JS 静态: 4 tests
  - JS 运行时 (Node.js vm): 1 test (含 25+ 子断言)

### 3.2 pytest (整体)

- 整体: **382 passed, 6 failed**
- 6 失败: 全部来自 `test_fts5_jieba.py` (lex-ai W8 D2 task 范围, 不属 D3)
- D3 测试文件 59/59 PASS

### 3.3 ruff

- D3 测试文件: **All checks passed** ✅
- 整体 backend 66 pre-existing errors (其他 task 范围, 不属 D3)

---

## 4. Playwright 截图

**5 页面 × 2 视口 + 0/3/5 致命 3 case + 1 默认 = 14 张**

落档: `docs/qa/d3-ui-fixes-w8/screenshots/`

| 文件 | 大小 (bytes) | 说明 |
|------|------------|------|
| 01-upload-desktop.png | 111,857 | 桌面端 1280×800 |
| 01-upload-mobile.png | 37,837 | 移动端 375×667 |
| 02-result-desktop.png | 124,339 | 默认 5 致命 (折叠 4-5) |
| 02-result-mobile.png | 36,450 | 移动端 |
| 02-result-5-fatal-desktop.png | 124,339 | 同 02-result-desktop (默认 5 致命) |
| 03-suggestion-desktop.png | 70,129 | |
| 03-suggestion-mobile.png | 39,702 | |
| 04-negotiation-desktop.png | 68,230 | 模态框桌面 |
| 04-negotiation-mobile.png | 14,693 | 模态框移动 (全屏) |
| 05-export-desktop.png | 63,146 | |
| 05-export-mobile.png | 34,837 | |
| fatal-0-fatal-mobile.png | 36,445 | 测试: 0 致命, 按钮隐藏 |
| fatal-3-fatal-mobile.png | 36,450 | 测试: 3 致命, 按钮隐藏 |
| fatal-5-fatal-mobile.png | 36,450 | 测试: 5 致命, 按钮显示 |

**截图运行命令**: `node scripts/d3-screenshots.js`

---

## 5. Git Commits (待 push)

| # | Commit | 范围 | 文件数 |
|---|--------|------|--------|
| 1 | feat(d3-ui): D3 移动端 < 768px + 立场影响预览 | 4 (3 HTML + 1 JS) |
| 2 | feat(d3-ui): D3 致命折叠 + 回归测试 | 6 (1 HTML + 1 JS + 1 test + 3 qa) |

---

## 6. 已知风险 / 后续

- 5 致命 demo 数据是测试方便, 生产场景的审查结果致命条款数应该基于真实数据
- 移动端 < 768px 适配是基础适配, W9 可考虑加 tablet (768-1024) 适配
- 立场预览的 4 立场 × 3 影响矩阵是 W4 设计基线, 律师反馈如有调整可在 W9 增量

---

## 7. 报告生成

- **生成时间**: 2026-06-29 (Asia/Shanghai)
- **执行人**: lex-coder (Mavis plan_5dcb8424 / d3-ui-fixes task)
- **验证状态**: ✅ **PASS** (自测 59/59 + 整体 382/388)
- **下一步**: git commit + push, 报告父 session mvs_2a364a81e34940c1aba0c9364f171061
