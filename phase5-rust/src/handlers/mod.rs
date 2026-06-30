//! 公共 handler: /health, /version, /ready
//!
//! Phase 5.3 W21 启动: 健康检查端点用 Rust 原生实现, 不转发 upstream,
//! 这样 4 个 health 端点能独立验证 Rust 后端存活.

use actix_web::{web, HttpResponse};
use serde_json::json;

use crate::{state::AppState, LexResult};

/// Liveness probe — 进程存活即可
pub async fn health(data: web::Data<AppState>) -> LexResult<HttpResponse> {
    Ok(HttpResponse::Ok().json(json!({
        "ok": true,
        "service": "lexprime-rust-core",
        "version": crate::VERSION,
        "phase": crate::PHASE_TAG,
        "bind": data.config.bind_addr,
        "upstream": data.config.python_upstream,
        "mode": data.config.lexprime_mode,
    })))
}

/// Readiness probe — 包含 upstream 探测
pub async fn ready(data: web::Data<AppState>) -> LexResult<HttpResponse> {
    let upstream_ok = data
        .http
        .get(format!("{}/health", data.config.python_upstream))
        .timeout(std::time::Duration::from_secs(2))
        .send()
        .await
        .map(|r| r.status().is_success())
        .unwrap_or(false);

    Ok(HttpResponse::Ok().json(json!({
        "ok": true,
        "ready": upstream_ok,
        "upstream_ok": upstream_ok,
    })))
}

/// Phase 5.3 manifest — 暴露已挂载的 4 模块 + 端点数量
pub async fn manifest() -> LexResult<HttpResponse> {
    Ok(HttpResponse::Ok().json(json!({
        "phase": "5.3-rust-core",
        "scaffold": "w21-2026-11-01",
        "modules": [
            {
                "name": "contract_review",
                "prefix": "/api/contract-review",
                "endpoints": [
                    "POST /upload",
                    "GET /result/{review_id}",
                    "POST /negotiation",
                    "POST /export",
                    "GET /health",
                    "GET /fixtures",
                    "GET /disclaimer",
                    "GET /ocr-health",
                    "POST /ocr-upload"
                ]
            },
            {
                "name": "full_workflow",
                "prefix": "/api/full-workflow",
                "endpoints": [
                    "POST /full-workflow",
                    "GET /full-workflow/healthz",
                    "GET /full-workflow/{case_id}"
                ]
            },
            {
                "name": "skill",
                "prefix": "/api/skill",
                "endpoints": [
                    "GET /health",
                    "GET /manifest",
                    "POST /search",
                    "GET /disclaimer"
                ]
            },
            {
                "name": "doc_gen",
                "prefix": "/api/doc-gen",
                "endpoints": [
                    "POST /complaint",
                    "POST /defense",
                    "POST /contract",
                    "POST /letter",
                    "POST /letter-v2",
                    "GET /health",
                    "GET /rollout/status",
                    "GET /metrics"
                ]
            }
        ]
    })))
}