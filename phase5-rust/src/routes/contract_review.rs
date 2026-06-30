//! Contract Review Router — W5 合同审查 (Skill 2) + OCR
//!
//! 路径跟 Python backend/cases-crawler/api/contract_review_router.py 完全一致,
//! handler 默认转发 upstream, 11/1 W21 启动范围不重写业务逻辑.

use actix_web::{web, HttpRequest, HttpResponse};

use crate::{
    handlers,
    state::AppState,
    upstream::{proxy, proxy_get, proxy_post},
    LexResult,
};

pub fn register(cfg: &mut web::ServiceConfig) {
    cfg.route("/health", web::get().to(health_local))
        .route("/disclaimer", web::get().to(disclaimer_local))
        .route("/ocr-health", web::get().to(ocr_health_local))
        .route("/fixtures", web::get().to(fixtures_proxy))
        .route("/upload", web::post().to(upload_proxy))
        .route("/result/{review_id}", web::get().to(result_proxy))
        .route("/negotiation", web::post().to(negotiation_proxy))
        .route("/export", web::post().to(export_proxy))
        .route("/ocr-upload", web::post().to(ocr_upload_proxy));
}

/// /api/contract-review/health — 本地实现, 验证 Rust 进程存活
async fn health_local(data: web::Data<AppState>) -> LexResult<HttpResponse> {
    handlers::health(data).await
}

/// /api/contract-review/disclaimer — 本地常量 (AI 辅助不替代律师)
async fn disclaimer_local() -> LexResult<HttpResponse> {
    Ok(HttpResponse::Ok().json(serde_json::json!({
        "ok": true,
        "disclaimer": "本服务由 LexPrime AI 辅助生成, 不替代执业律师专业意见。律师函/合同审查结果仅供律师参考, 最终决策与签发由执业律师负责。",
        "version": "1.0.0",
        "phase": crate::PHASE_TAG,
    })))
}

/// /api/contract-review/ocr-health — 本地 + 上游探测
async fn ocr_health_local(data: web::Data<AppState>) -> LexResult<HttpResponse> {
    let upstream_ok = data
        .http
        .get(format!(
            "{}/api/contract-review/ocr-health",
            data.config.python_upstream
        ))
        .timeout(std::time::Duration::from_secs(2))
        .send()
        .await
        .map(|r| r.status().is_success())
        .unwrap_or(false);

    Ok(HttpResponse::Ok().json(serde_json::json!({
        "ok": true,
        "engine": "paddle_ocr",
        "available": upstream_ok,
        "upstream_ok": upstream_ok,
        "phase": crate::PHASE_TAG,
    })))
}

/// /api/contract-review/fixtures — 转发 upstream
async fn fixtures_proxy(
    data: web::Data<AppState>,
    req: HttpRequest,
) -> LexResult<HttpResponse> {
    proxy_get(&data, req, "/api/contract-review/fixtures").await
}

async fn upload_proxy(
    data: web::Data<AppState>,
    req: HttpRequest,
    body: web::Json<serde_json::Value>,
) -> LexResult<HttpResponse> {
    proxy_post(&data, req, "/api/contract-review/upload", body).await
}

async fn result_proxy(
    data: web::Data<AppState>,
    req: HttpRequest,
    path: web::Path<String>,
) -> LexResult<HttpResponse> {
    let p = path.into_inner();
    proxy_get(&data, req, &format!("/api/contract-review/result/{p}")).await
}

async fn negotiation_proxy(
    data: web::Data<AppState>,
    req: HttpRequest,
    body: web::Json<serde_json::Value>,
) -> LexResult<HttpResponse> {
    proxy_post(&data, req, "/api/contract-review/negotiation", body).await
}

async fn export_proxy(
    data: web::Data<AppState>,
    req: HttpRequest,
    body: web::Json<serde_json::Value>,
) -> LexResult<HttpResponse> {
    proxy_post(&data, req, "/api/contract-review/export", body).await
}

async fn ocr_upload_proxy(
    data: web::Data<AppState>,
    req: HttpRequest,
    body: web::Json<serde_json::Value>,
) -> LexResult<HttpResponse> {
    proxy_post(&data, req, "/api/contract-review/ocr-upload", body).await
}