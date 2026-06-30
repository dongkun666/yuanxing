# Phase 5.3 LexPrime Rust 核心 (W21 phase5-rust-core 启动)

> **11/1 W21 启动 (Mavis owner + lex-coder)**: 重构 backend (FastAPI → Rust actix-web)
> 保持 PRD V5.0 5 大价值主张 + 6 大模块不变, **实现层** Rust 重构.

## 模块清单

| 模块 | Path | 端点数 | 来源 |
|---|---|---|---|
| **contract_review** | `/api/contract-review/*` | 9 | W5 合同审查 (Skill 2) + OCR |
| **full_workflow** | `/api/full-workflow/*` | 3 | W10 一体化 (案件+证据+文书 pipeline) |
| **skill** | `/api/skill/*` | 4 | W3 Skill 2/3 入口 (manifest/search/disclaimer) |
| **doc_gen** | `/api/doc-gen/*` | 8 | W9 Skill 3 文书生成 (4 文书 + rollout) |

合计 **24 个端点**, 全部跟 Python backend (`backend/cases-crawler/api/*.py`) 路径 1:1 对齐.

## 技术栈

- **Rust** 1.83+ (实测 1.96.0, LTS stable)
- **tokio** 1.43 (async runtime, `full` features)
- **actix-web** 4.9 (web framework)
- **rusqlite** 0.32 (bundled, 零外部 sqlite 依赖)
- **serde** 1 + **serde_json** 1 (序列化)
- **tracing** 0.1 + **tracing-subscriber** 0.3 (日志)
- **chrono** 0.4, **uuid** 1, **thiserror** 1, **anyhow** 1
- dev: **criterion** 0.5 (bench), **reqwest** 0.12 (HTTP client)

## 目录结构 (借鉴 phase5-react 子目录隔离模式)

```
phase5-rust/
├── Cargo.toml
├── Cargo.lock            # 生成
├── .cargo/
│   └── config.toml       # 本地编译优化
├── src/
│   ├── main.rs           # 入口, 启动 actix-web HttpServer
│   ├── lib.rs            # 库入口, VERSION + PHASE_TAG
│   ├── config.rs         # env 加载
│   ├── state.rs          # AppState (config + http client)
│   ├── errors.rs         # LexError + ResponseError
│   ├── upstream.rs       # Python backend 8000 转发
│   ├── handlers/
│   │   └── mod.rs        # /health /ready /manifest
│   └── routes/
│       ├── mod.rs        # 4 模块 scope 注册
│       ├── contract_review.rs
│       ├── full_workflow.rs
│       ├── skill.rs
│       └── doc_gen.rs
├── tests/
│   └── integration.rs    # 9 个集成测试 (4 模块 health + manifest)
├── benches/
│   └── bench.rs          # criterion bench (4 模块并发)
├── .gitignore
└── README.md
```

## 启动

```bash
# 开发模式 (foreground)
cd yuanxing/phase5-rust
cargo run

# Release 模式
cargo build --release
./target/release/lexprime-rust-core

# 默认监听 127.0.0.1:8001 (跟 Python backend 8000 区分)
```

### 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `LEXPRIME_BIND` | `127.0.0.1:8001` | 监听地址 |
| `LEXPRIME_PYTHON_UPSTREAM` | `http://127.0.0.1:8000` | 上游 Python backend |
| `LEXPRIME_BACKEND` | `rust` | 运行模式 (`rust`/`python`/`shadow`) |
| `RUST_LOG` | `info` | tracing 级别 |

## 测试

```bash
# 9 个集成测试 (启动本地 server 验证 health/manifest)
cargo test

# Criterion bench (4 模块并发 + 单端点延迟)
cargo bench
```

## API 兼容矩阵

| 端点 | Python | Rust (W21) | 实现策略 |
|---|---|---|---|
| `/api/contract-review/health` | ✅ | ✅ | Rust 原生 |
| `/api/contract-review/disclaimer` | ✅ | ✅ | Rust 常量 |
| `/api/contract-review/ocr-health` | ✅ | ✅ | Rust + upstream 探测 |
| `/api/contract-review/upload` | ✅ | ✅ | upstream 转发 |
| `/api/contract-review/result/{id}` | ✅ | ✅ | upstream 转发 |
| `/api/contract-review/negotiation` | ✅ | ✅ | upstream 转发 |
| `/api/contract-review/export` | ✅ | ✅ | upstream 转发 |
| `/api/contract-review/ocr-upload` | ✅ | ✅ | upstream 转发 |
| `/api/contract-review/fixtures` | ✅ | ✅ | upstream 转发 |
| `/api/full-workflow/full-workflow` | ✅ | ✅ | upstream 转发 |
| `/api/full-workflow/full-workflow/healthz` | ✅ | ✅ | Rust 原生 |
| `/api/full-workflow/full-workflow/{id}` | ✅ | ✅ | upstream 转发 |
| `/api/skill/health` | ✅ | ✅ | Rust 原生 |
| `/api/skill/manifest` | ✅ | ✅ | Rust 常量 (Skill 2/3) |
| `/api/skill/search` | ✅ | ✅ | upstream 转发 |
| `/api/skill/disclaimer` | ✅ | ✅ | Rust 常量 |
| `/api/doc-gen/complaint` | ✅ | ✅ | upstream 转发 |
| `/api/doc-gen/defense` | ✅ | ✅ | upstream 转发 |
| `/api/doc-gen/contract` | ✅ | ✅ | upstream 转发 |
| `/api/doc-gen/letter` | ✅ | ✅ | upstream 转发 |
| `/api/doc-gen/letter-v2` | ✅ | ✅ | upstream 转发 |
| `/api/doc-gen/health` | ✅ | ✅ | Rust 原生 |
| `/api/doc-gen/rollout/status` | ✅ | ✅ | Rust 常量 (Skill 3 v2 100%) |
| `/api/doc-gen/metrics` | ✅ | ✅ | Rust 常量 (基线) |

## W21 启动边界 (硬约束)

✅ **做**:
- Rust 1.83+ + tokio 1.43 + actix-web 4 + rusqlite 0.32 脚手架
- 4 模块 path 跟 Python 一致, health/disclaimer/manifest 用 Rust 原生实现
- upstream 转发层 (upstream.rs) 复用 Python backend 业务逻辑
- 9 个集成测试 + criterion bench harness
- 1 commit + push 到 yuanxing origin/main

❌ **不做** (留给 W22+):
- 重写合同审查/OCR/文书生成业务逻辑 (保持 PRD V5.0 不变)
- 完整业务 handler 实现 (W21 是脚手架阶段)
- 生产部署 Docker / K8s 配置
- macOS / Linux .dmg / .AppImage 跨平台打包 (沿用 phase5-electron)

## 性能目标 (task W21 §3)

| 指标 | Rust 目标 | Python 基线 | 提升 |
|---|---|---|---|
| 并发 1000 合同审查 | < 50ms | 250ms | 5x |
| 并发 100 OCR | < 500ms | 2.5s | 5x |
| 内存使用 | < 100MB | 500MB | 5x |
| 启动时间 | < 1s | 5s | 5x |

W21 启动阶段不强制达成全部指标, W22+ 真业务迁移后逐项验证.

## 路线图

- **W21 (11/1 启动)**: 本 commit — 脚手架 + 4 模块骨架 + bench harness
- **W22+**: 把 4 模块业务逻辑逐步搬到 Rust (合同审查算法 → Rust native)
- **W26+ (Phase 5.4 企业版)**: 复用本子目录隔离模式 + lex-security 新 agent

## 复用 phase5-react 经验 (跨项目模式)

参考 W19 phase5-react (commit 83d4695):
- **独立子目录**: `yuanxing/phase5-rust/` 跟 `phase5-react/` 同级, 独立 `Cargo.toml` / `target/`
- **设计 token 100% 复用**: Rust 后端 path 与 Python backend 1:1 对齐, 前端可无侵入切换
- **失败可一键 revert**: `rm -rf phase5-rust/` 不影响其他模块

## 文件清单

```
phase5-rust/
├── .gitignore                                  30 lines
├── .cargo/config.toml                          15 lines
├── Cargo.toml                                  75 lines
├── README.md                                   (本文)
├── src/
│   ├── lib.rs                                  35 lines
│   ├── main.rs                                 75 lines
│   ├── config.rs                               30 lines
│   ├── state.rs                                25 lines
│   ├── errors.rs                               50 lines
│   ├── upstream.rs                             60 lines
│   ├── handlers/mod.rs                         90 lines
│   └── routes/
│       ├── mod.rs                              20 lines
│       ├── contract_review.rs                  110 lines
│       ├── full_workflow.rs                    45 lines
│       ├── skill.rs                            70 lines
│       └── doc_gen.rs                          100 lines
├── tests/integration.rs                        175 lines (9 tests)
└── benches/bench.rs                            195 lines (5 benches)
```

合计 ~1200 行 Rust 代码 (不包含 `Cargo.lock` 自动生成).