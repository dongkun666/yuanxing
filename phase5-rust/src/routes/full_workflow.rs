//! Full Workflow Router — W10 一体化 (案件+证据+文书生成 pipeline)

use actix_web::{web, HttpRequest, HttpResponse};

use crate::{handlers, state::AppState, upstream::proxy_get, LexResult};

pub fn register(cfg: &mut web::ServiceConfig) {
    cfg.route("/full-workflow/healthz", web::get().to(healthz_local))
        .route("/full-workflow", web::post().to(full_workflow_proxy))
        .route("/full-workflow/{case_id}", web::get().to(case_proxy));
}

async fn healthz_local(data: web::Data<AppState>) -> LexResult<HttpResponse> {
    handlers::ready(data).await
}

async fn full_workflow_proxy(
    data: web::Data<AppState>,
    req: HttpRequest,
    body: web::Json<serde_json::Value>,
) -> LexResult<HttpResponse> {
    // Phase 5.3 W21 启动范围: 暂走 upstream 转发, 后续 W22+ 搬业务
    let upstream = format!("{}/api/full-workflow/full-workflow", data.config.python_upstream);
    let resp = data
        .http
        .post(&upstream)
        .json(&body.into_inner())
        .send()
        .await?;
    let status = resp.status();
    let bytes = resp.bytes().await?;
    Ok(HttpResponse::build(actix_web::http::StatusCode::from_u16(status.as_u16()).unwrap()).body(bytes))
}

async fn case_proxy(
    data: web::Data<AppState>,
    req: HttpRequest,
    path: web::Path<String>,
) -> LexResult<HttpResponse> {
    let case_id = path.into_inner();
    proxy_get(&data, req, &format!("/api/full-workflow/full-workflow/{case_id}")).await
}