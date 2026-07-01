//! Phase 5.3 LexPrime Rust 核心 — main 入口
//!
//! 启动 actix-web HttpServer, 挂载 4 模块路由 + 健康检查.
//!
//! 默认端口: 127.0.0.1:8001 (跟 Python backend 8000 区分)
//! 可通过 LEXPRIME_BIND 环境变量覆盖.

use actix_web::{middleware, web, App, HttpServer};
use lexprime_rust_core::{config::AppConfig, routes, state::AppState};
use tracing::{info, warn};
use tracing_subscriber::EnvFilter;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // 初始化 tracing
    let env_filter =
        EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info,actix_web=info"));
    tracing_subscriber::fmt()
        .with_env_filter(env_filter)
        .with_target(false)
        .init();

    let config = AppConfig::from_env();
    let bind = config.bind_addr.clone();
    let state = AppState::new(config.clone());

    info!(
        "LexPrime Rust Core v{} starting | phase={} | bind={} | upstream={} | mode={}",
        lexprime_rust_core::VERSION,
        lexprime_rust_core::PHASE_TAG,
        bind,
        config.python_upstream,
        config.lexprime_mode
    );

    // 上游探测 — 启动时不阻塞, 仅 warning
    match reqwest::get(format!("{}/health", config.python_upstream)).await {
        Ok(r) if r.status().is_success() => {
            info!("upstream Python backend reachable at {}", config.python_upstream);
        }
        Ok(r) => {
            warn!(
                "upstream Python backend returned {}, will run in degraded mode",
                r.status()
            );
        }
        Err(e) => {
            warn!(
                "upstream Python backend unreachable ({}), running in degraded mode",
                e
            );
        }
    }

    let app_state = web::Data::new(state);
    let server = HttpServer::new(move || {
        App::new()
            .app_data(app_state.clone())
            .app_data(web::JsonConfig::default().limit(50 * 1024 * 1024)) // 50 MB (合同上传)
            .wrap(middleware::Compress::default())
            .wrap(middleware::Logger::default())
            .route("/health", web::get().to(lexprime_rust_core::handlers::health))
            .route("/ready", web::get().to(lexprime_rust_core::handlers::ready))
            .route(
                "/manifest",
                web::get().to(lexprime_rust_core::handlers::manifest),
            )
            .configure(routes::register)
    })
    .bind(&bind)?
    .workers(num_cpus_guess())
    .run();

    info!("LexPrime Rust Core listening on http://{bind}");
    server.await
}

fn num_cpus_guess() -> usize {
    std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(4)
}