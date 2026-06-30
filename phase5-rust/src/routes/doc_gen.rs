//! Doc Gen Router — W9 Skill 3 文书生成 (4 文书类型 + 灰度 rollout 状态)

use actix_web::{web, HttpRequest, HttpResponse};

use crate::{handlers, state::AppState, upstream::proxy_get, LexResult};

pub fn register(cfg: &mut web::ServiceConfig) {
    cfg.route("/health", web::get().to(health_local))
        .route("/metrics", web::get().to(metrics_local))
        .route("/rollout/status", web::get().to(rollout_status_local))
        .route("/complaint", web::post().to(complaint_proxy))
        .route("/defense", web::post().to(defense_proxy))
        .route("/contract", web::post().to(contract_proxy))
        .route("/letter", web::post().to(letter_proxy))
        .route("/letter-v2", web::post().to(letter_v2_proxy));
}

async fn health_local(data: web::Data<AppState>) -> LexResult<HttpResponse> {
    handlers::health(data).await
}

async fn metrics_local() -> LexResult<HttpResponse> {
    Ok(HttpResponse::Ok().json(serde_json::json!({
        "ok": true,
        "phase": crate::PHASE_TAG,
        "metrics": {
            "rust_uptime_secs": 0,
            "requests_total": 0,
            "module": "doc_gen",
        }
    })))
}

async fn rollout_status_local() -> LexResult<HttpResponse> {
    Ok(HttpResponse::Ok().json(serde_json::json!({
        "ok": true,
        "phase": crate::PHASE_TAG,
        "skill3_letter_v2": {
            "rollout_pct": 100,
            "target_date": "2026-10-01",
            "deprecated_v1_date": "2026-11-01",
            "current": "v2"
        }
    })))
}

async fn complaint_proxy(
    data: web::Data<AppState>,
    req: HttpRequest,
    body: web::Json<serde_json::Value>,
) -> LexResult<HttpResponse> {
    crate::upstream::proxy_post(&data, req, "/api/doc-gen/complaint", body).await
}

async fn defense_proxy(
    data: web::Data<AppState>,
    req: HttpRequest,
    body: web::Json<serde_json::Value>,
) -> LexResult<HttpResponse> {
    crate::upstream::proxy_post(&data, req, "/api/doc-gen/defense", body).await
}

async fn contract_proxy(
    data: web::Data<AppState>,
    req: HttpRequest,
    body: web::Json<serde_json::Value>,
) -> LexResult<HttpResponse> {
    crate::upstream::proxy_post(&data, req, "/api/doc-gen/contract", body).await
}

async fn letter_proxy(
    data: web::Data<AppState>,
    req: HttpRequest,
    body: web::Json<serde_json::Value>,
) -> LexResult<HttpResponse> {
    crate::upstream::proxy_post(&data, req, "/api/doc-gen/letter", body).await
}

async fn letter_v2_proxy(
    data: web::Data<AppState>,
    req: HttpRequest,
    body: web::Json<serde_json::Value>,
) -> LexResult<HttpResponse> {
    crate::upstream::proxy_post(&data, req, "/api/doc-gen/letter-v2", body).await
}