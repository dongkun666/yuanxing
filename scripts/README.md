# LexPrime 工具脚本

> 来自 falvxiangmu/ 调试工作目录, 2026-06-26 整理。

## 目录

- `audit/` - 体检脚本 (HTML/JS/CSS/排版 + 404/console/network 错误捕获)
- `refactor/` - 重构脚本 (token 化 + 字号收敛 + 模块拆分 + KB 专用)
- `test/` - E2E 测试 + 截图脚本 (Playwright)

## 用法

```bash
# 例: 跑 E2E 测试
node scripts/test/test_modules_e2e.cjs

# 例: design token 化 (按需指定文件)
python scripts/refactor/tokenize_all.py
```

## 工具脚本统计

- audit: 6 个
- refactor: 32 个
- test: 8 个
- 总计: 46 个
