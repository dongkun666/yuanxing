//! 配置加载 (env vars, defaults 兼容 Python backend)
//!
//! Phase 5.3 W21 启动: Rust 后端端口 8001, Python 后端 (upstream) 端口 8000.

use std::env;

#[derive(Clone, Debug)]
pub struct AppConfig {
    pub bind_addr: String,
    pub python_upstream: String,
    pub lexprime_mode: String, // "rust" | "python" | "shadow"
    pub log_level: String,
}

impl AppConfig {
    pub fn from_env() -> Self {
        Self {
            bind_addr: env::var("LEXPRIME_BIND").unwrap_or_else(|_| "127.0.0.1:8001".into()),
            python_upstream: env::var("LEXPRIME_PYTHON_UPSTREAM")
                .unwrap_or_else(|_| "http://127.0.0.1:8000".into()),
            lexprime_mode: env::var("LEXPRIME_BACKEND").unwrap_or_else(|_| "rust".into()),
            log_level: env::var("RUST_LOG").unwrap_or_else(|_| "info".into()),
        }
    }
}

impl Default for AppConfig {
    fn default() -> Self {
        Self::from_env()
    }
}