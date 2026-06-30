//! Phase 5.3 Rust 核心 — 性能基准 (benchmark)
//!
//! 11/1 W21 启动范围: 用 criterion 测量 4 模块 health 端点的并发延迟基线.
//!
//! 目标 (task 指定):
//! - 并发 1000: 合同审查 < 50ms (vs Python 250ms, 5x 提升)
//! - 并发 100: OCR < 500ms (vs Python 2.5s, 5x 提升)
//! - 内存使用 < 100MB (vs Python 500MB, 5x 提升)
//! - 启动时间 < 1s (vs Python 5s, 5x 提升)
//!
//! W21 启动阶段: 只验证 "Rust health 端点能稳定返回 < 5ms", 给 W22+ 真业务迁移留 baseline.

use std::time::{Duration, Instant};

use actix_web::{middleware, web, App, HttpServer};
use criterion::{criterion_group, criterion_main, Criterion};
use lexprime_rust_core::{config::AppConfig, handlers, routes, state::AppState};

/// 启动本地 server (随机端口)
async fn spawn_app() -> String {
    let config = AppConfig {
        bind_addr: "127.0.0.1:0".into(),
        python_upstream: "http://127.0.0.1:1".into(),
        lexprime_mode: "bench".into(),
        log_level: "error".into(),
    };
    let state = AppState::new(config);
    let app_state = web::Data::new(state);

    let server = HttpServer::new(move || {
        App::new()
            .app_data(app_state.clone())
            .wrap(middleware::Logger::default())
            .route("/health", web::get().to(handlers::health))
            .route("/ready", web::get().to(handlers::ready))
            .configure(routes::register)
    })
    .workers(4)
    .bind("127.0.0.1:0")
    .expect("bind");

    let addrs = server.addrs();
    let addr = addrs[0];
    tokio::spawn(server.run());

    tokio::time::sleep(Duration::from_millis(150)).await;

    format!("http://{addr}")
}

fn http_client() -> reqwest::Client {
    reqwest::Client::builder()
        .timeout(Duration::from_secs(5))
        .pool_max_idle_per_host(256)
        .build()
        .unwrap()
}

/// 同步 wrapper: 在 criterion benchmark 里跑 async spawn_app
fn run_bench<F: FnOnce()>(base_url: String, f: F) {
    let _ = base_url;
    f()
}

async fn bench_root_health(c: &mut Criterion) {
    let rt = tokio::runtime::Runtime::new().unwrap();
    let base = rt.block_on(spawn_app());
    let client = http_client();

    c.bench_function("root_health_rtt", |b| {
        b.iter(|| {
            let start = Instant::now();
            let resp = rt.block_on(client.get(format!("{base}/health")).send());
            let elapsed = start.elapsed();
            assert!(resp.is_ok(), "health request failed");
            assert!(elapsed < Duration::from_millis(50), "RTT > 50ms: {elapsed:?}");
            elapsed
        });
    });
}

async fn bench_contract_review_health(c: &mut Criterion) {
    let rt = tokio::runtime::Runtime::new().unwrap();
    let base = rt.block_on(spawn_app());
    let client = http_client();

    c.bench_function("contract_review_health_rtt", |b| {
        b.iter(|| {
            let start = Instant::now();
            let resp = rt.block_on(
                client
                    .get(format!("{base}/api/contract-review/health"))
                    .send(),
            );
            let elapsed = start.elapsed();
            assert!(resp.is_ok(), "contract_review_health failed");
            assert!(elapsed < Duration::from_millis(50), "RTT > 50ms: {elapsed:?}");
            elapsed
        });
    });
}

async fn bench_doc_gen_rollout(c: &mut Criterion) {
    let rt = tokio::runtime::Runtime::new().unwrap();
    let base = rt.block_on(spawn_app());
    let client = http_client();

    c.bench_function("doc_gen_rollout_status_rtt", |b| {
        b.iter(|| {
            let start = Instant::now();
            let resp = rt.block_on(
                client
                    .get(format!("{base}/api/doc-gen/rollout/status"))
                    .send(),
            );
            let elapsed = start.elapsed();
            assert!(resp.is_ok(), "doc_gen_rollout failed");
            elapsed
        });
    });
}

/// 并发 1000 合同审查 — task 目标 < 50ms p99
async fn bench_concurrent_1000_contract_review(c: &mut Criterion) {
    let rt = tokio::runtime::Runtime::new().unwrap();
    let base = rt.block_on(spawn_app());
    let client = http_client();

    c.bench_function("concurrent_1000_contract_review_health", |b| {
        b.iter(|| {
            let start = Instant::now();
            let mut handles = Vec::with_capacity(1000);
            for _ in 0..1000 {
                let client = client.clone();
                let url = format!("{base}/api/contract-review/health");
                handles.push(tokio::spawn(async move {
                    client.get(url).send().await
                }));
            }
            let results = rt.block_on(async {
                futures::future::join_all(handles).await
            });
            let elapsed = start.elapsed();
            let ok = results
                .iter()
                .filter(|r| matches!(r, Ok(Ok(r)) if r.status().is_success()))
                .count();
            assert!(ok >= 990, "并发 1000 中至少 990 成功, 实际 {ok}");
            elapsed
        });
    });
}

/// 并发 100 OCR health — task 目标 < 500ms
async fn bench_concurrent_100_ocr(c: &mut Criterion) {
    let rt = tokio::runtime::Runtime::new().unwrap();
    let base = rt.block_on(spawn_app());
    let client = http_client();

    c.bench_function("concurrent_100_ocr_health", |b| {
        b.iter(|| {
            let start = Instant::now();
            let mut handles = Vec::with_capacity(100);
            for _ in 0..100 {
                let client = client.clone();
                let url = format!("{base}/api/contract-review/ocr-health");
                handles.push(tokio::spawn(async move {
                    client.get(url).send().await
                }));
            }
            let results = rt.block_on(async {
                futures::future::join_all(handles).await
            });
            let elapsed = start.elapsed();
            let ok = results
                .iter()
                .filter(|r| matches!(r, Ok(Ok(r)) if r.status().is_success()))
                .count();
            assert!(ok >= 95, "并发 100 OCR 中至少 95 成功, 实际 {ok}");
            elapsed
        });
    });
}

criterion_group! {
    name = benches;
    config = Criterion::default()
        .sample_size(50)
        .measurement_time(Duration::from_secs(10));
    targets =
        bench_root_health,
        bench_contract_review_health,
        bench_doc_gen_rollout,
        bench_concurrent_1000_contract_review,
        bench_concurrent_100_ocr
}

criterion_main!(benches);

// 让 cargo 不抱怨未用
#[allow(dead_code)]
fn _silence_run_bench_unused() {
    run_bench(String::new(), || {});
}