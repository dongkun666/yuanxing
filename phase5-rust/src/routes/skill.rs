//! Skill Router — W3 Skill 2/3 入口 (manifest / search / disclaimer)

use actix_web::{web, HttpRequest, HttpResponse};

use crate::{handlers, state::AppState, upstream::proxy_post, LexResult};

pub fn register(cfg: &mut web::ServiceConfig) {
    cfg.route("/health", web::get().to(health_local))
        .route("/manifest", web::get().to(manifest_local))
        .route("/disclaimer", web::get().to(disclaimer_local))
        .route("/search", web::post().to(search_proxy));
}

async fn health_local(data: web::Data<AppState>) -> LexResult<HttpResponse> {
    handlers::health(data).await
}

async fn manifest_local() -> LexResult<HttpResponse> {
    Ok(HttpResponse::Ok().json(serde_json::json!({
        "ok": true,
        "skills": [
            {
                "id": "skill_2_contract_review",
                "name": "合同审查",
                "version": "1.0.0",
                "endpoints": ["/api/contract-review/upload", "/api/contract-review/result/{id}"],
                "phase": "skill_2_v1",
            },
            {
                "id": "skill_3_doc_gen",
                "name": "文书生成",
                "version": "2.0.0",
                "endpoints": [
                    "/api/doc-gen/complaint",
                    "/api/doc-gen/defense",
                    "/api/doc-gen/contract",
                    "/api/doc-gen/letter",
                    "/api/doc-gen/letter-v2"
                ],
                "phase": "skill_3_v2_100pct",
            }
        ],
        "phase": crate::PHASE_TAG,
    })))
}

async fn disclaimer_local() -> LexResult<HttpResponse> {
    Ok(HttpResponse::Ok().json(serde_json::json!({
        "ok": true,
        "disclaimer": "LexPrime AI 辅助生成, 不替代执业律师。所有结果需经律师审核签发。",
        "version": "1.0.0",
    })))
}

async fn search_proxy(
    data: web::Data<AppState>,
    req: HttpRequest,
    body: web::Json<serde_json::Value>,
) -> LexResult<HttpResponse> {
    proxy_post(&data, req, "/api/skill/search", body).await
}