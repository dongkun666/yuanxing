//! Phase 5.3 LexPrime Rust 核心 — 库入口
//!
//! 11/1 W21 phase5-rust-core 启动 (Mavis owner + lex-coder)
//! 重构 backend (FastAPI → Rust actix-web)
//!
//! 模块:
//! - contract_review: W5 合同审查 (Skill 2) + W5 OCR 上传
//! - full_workflow:   W10 一体化 (案件+证据+文书生成 pipeline)
//! - skill:           W3 Skill 2/3 入口 (合同审查 + 文书生成 manifest/search)
//! - doc_gen:         W9 Skill 3 文书生成 (4 文书类型 + 灰度 rollout 状态)
//!
//! 设计原则 (W21 启动边界):
//! - 不重写业务逻辑, 通过 Python subprocess 复用现有 backend 业务逻辑
//! - Rust 侧只承担: HTTP 路由 + JSON 反序列化 + 业务转发 + 健康检查
//! - 4 模块 path 与 Python backend 一致, 前端可无侵入切换 (env: LEXPRIME_BACKEND=rust|python)
//! - 5 大价值主张 + 6 大模块不变 (PRD V5.0 维持)

pub mod config;
pub mod errors;
pub mod handlers;
pub mod routes;
pub mod state;
pub mod upstream;

pub use errors::{LexError, LexResult};
pub use state::AppState;

/// Library version string.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Default HTTP bind address (overridable via LEXPRIME_BIND env var).
pub const DEFAULT_BIND: &str = "127.0.0.1:8001";

/// Phase 5.3 启动版本标签
pub const PHASE_TAG: &str = "phase5.3-rust-core/w21-scaffold";