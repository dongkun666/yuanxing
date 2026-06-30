//! LexPrime Rust 核心错误类型

use actix_web::{HttpResponse, ResponseError};
use serde_json::json;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum LexError {
    #[error("upstream error: {0}")]
    Upstream(String),

    #[error("not implemented yet: {0}")]
    NotImplemented(&'static str),

    #[error("bad request: {0}")]
    BadRequest(String),

    #[error("not found: {0}")]
    NotFound(String),

    #[error("internal error: {0}")]
    Internal(String),
}

impl From<reqwest::Error> for LexError {
    fn from(e: reqwest::Error) -> Self {
        LexError::Upstream(e.to_string())
    }
}

impl From<std::io::Error> for LexError {
    fn from(e: std::io::Error) -> Self {
        LexError::Internal(e.to_string())
    }
}

impl From<serde_json::Error> for LexError {
    fn from(e: serde_json::Error) -> Self {
        LexError::Internal(format!("serde_json: {e}"))
    }
}

pub type LexResult<T> = Result<T, LexError>;

impl ResponseError for LexError {
    fn error_response(&self) -> HttpResponse {
        let (status, code) = match self {
            LexError::BadRequest(_) => (400, "bad_request"),
            LexError::NotFound(_) => (404, "not_found"),
            LexError::Upstream(_) => (502, "upstream_error"),
            LexError::NotImplemented(_) => (501, "not_implemented"),
            LexError::Internal(_) => (500, "internal_error"),
        };

        HttpResponse::build(actix_web::http::StatusCode::from_u16(status).unwrap()).json(json!({
            "ok": false,
            "code": code,
            "error": self.to_string(),
            "phase": "5.3-rust-core",
        }))
    }
}