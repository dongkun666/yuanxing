//! 上游 (Python backend 8000) HTTP 客户端 — 复用现有业务逻辑
//!
//! W21 启动范围: Rust 路由接住请求,转发到 Python backend 执行业务逻辑,
//! 拿回响应后原样回吐 (path + JSON shape 100% 兼容).
//!
//! 后续 W22+ 再逐步把业务逻辑搬到 Rust 实现 (5x 性能目标).

use actix_web::{http::Method, web, HttpRequest, HttpResponse};
use serde_json::Value;

use crate::{state::AppState, LexResult};

/// 通用 upstream 代理 — 把请求转发到 Python backend
///
/// path: e.g. "/api/contract-review/health"
/// method/body/query: 透传
pub async fn proxy(state: &AppState, req: HttpRequest, path: &str, body: Option<Value>) -> LexResult<HttpResponse> {
    let url = format!("{}{}", state.config.python_upstream, path);

    let method = req.method().clone();
    let query = req.query_string();

    let full_url = if query.is_empty() {
        url
    } else {
        format!("{url}?{query}")
    };

    let mut builder = state.http.request(method, &full_url);
    if let Some(b) = body {
        builder = builder.json(&b);
    }

    // 透传部分关键 header (auth, content-type 已在 builder 里覆盖)
    for (k, v) in req.headers() {
        if let Ok(s) = v.to_str() {
            let key = k.as_str().to_lowercase();
            // 跳过 hop-by-hop header + host
            if matches!(key.as_str(),
                "host" | "connection" | "keep-alive" | "proxy-authenticate"
                | "proxy-authorization" | "te" | "trailers"
                | "transfer-encoding" | "upgrade" | "content-length"
            ) {
                continue;
            }
            builder = builder.header(k.as_str(), s);
        }
    }

    let resp = builder.send().await?;
    let status = resp.status();
    let bytes = resp.bytes().await?;

    let mut response = HttpResponse::build(actix_web::http::StatusCode::from_u16(status.as_u16()).unwrap());
    Ok(response.body(bytes))
}

/// 便捷 helper: GET 代理
pub async fn proxy_get(state: &AppState, req: HttpRequest, path: &str) -> LexResult<HttpResponse> {
    proxy(state, req, path, None).await
}

/// 便捷 helper: POST 代理 (JSON body)
pub async fn proxy_post(
    state: &AppState,
    req: HttpRequest,
    path: &str,
    body: web::Json<Value>,
) -> LexResult<HttpResponse> {
    proxy(state, req, path, Some(body.into_inner())).await
}

#[allow(dead_code)]
fn _silence_method_unused(_m: Method) {}