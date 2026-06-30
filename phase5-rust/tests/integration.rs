//! Phase 5.3 Rust 核心 — 集成测试
//!
//! 11/1 W21 启动范围: 验证 4 模块 health 端点 + manifest 都返回正确 shape.
//! 不依赖 Python upstream (用 spawn_app helper 启动本地 server).

use std::time::Duration;

use actix_web::{middleware, web, App, HttpServer};
use lexprime_rust_core::{
    config::AppConfig,
    handlers, routes,
    state::AppState,
};

/// 启动一个临时 server, 返回 base URL
async fn spawn_app() -> String {
    let config = AppConfig {
        bind_addr: "127.0.0.1:0".into(), // 让 OS 分配端口
        python_upstream: "http://127.0.0.1:1".into(), // dummy upstream
        lexprime_mode: "rust-test".into(),
        log_level: "warn".into(),
    };
    let state = AppState::new(config);
    let app_state = web::Data::new(state);

    let server = HttpServer::new(move || {
        App::new()
            .app_data(app_state.clone())
            .wrap(middleware::Logger::default())
            .route("/health", web::get().to(handlers::health))
            .route("/ready", web::get().to(handlers::ready))
            .route("/manifest", web::get().to(handlers::manifest))
            .configure(routes::register)
    })
    .workers(2)
    .bind("127.0.0.1:0")
    .expect("bind");

    let addrs = server.addrs();
    let addr = addrs[0];
    let server = server.run();

    // 后台跑
    tokio::spawn(server);

    // 等服务起来
    tokio::time::sleep(Duration::from_millis(100)).await;

    format!("http://{addr}")
}

fn http_client() -> reqwest::Client {
    reqwest::Client::builder()
        .timeout(Duration::from_secs(5))
        .build()
        .unwrap()
}

#[actix_web::test]
async fn test_root_health() {
    let base = spawn_app().await;
    let resp = http_client()
        .get(format!("{base}/health"))
        .send()
        .await
        .unwrap();
    assert_eq!(resp.status(), 200);
    let body: serde_json::Value = resp.json().await.unwrap();
    assert_eq!(body["ok"], true);
    assert_eq!(body["service"], "lexprime-rust-core");
    assert_eq!(body["phase"], "phase5.3-rust-core/w21-scaffold");
}

#[actix_web::test]
async fn test_manifest_has_4_modules() {
    let base = spawn_app().await;
    let resp = http_client()
        .get(format!("{base}/manifest"))
        .send()
        .await
        .unwrap();
    assert_eq!(resp.status(), 200);
    let body: serde_json::Value = resp.json().await.unwrap();
    let modules = body["modules"].as_array().unwrap();
    assert_eq!(modules.len(), 4, "应当挂载 4 个模块");
    let names: Vec<&str> = modules.iter().map(|m| m["name"].as_str().unwrap()).collect();
    assert!(names.contains(&"contract_review"));
    assert!(names.contains(&"full_workflow"));
    assert!(names.contains(&"skill"));
    assert!(names.contains(&"doc_gen"));
}

#[actix_web::test]
async fn test_contract_review_health() {
    let base = spawn_app().await;
    let resp = http_client()
        .get(format!("{base}/api/contract-review/health"))
        .send()
        .await
        .unwrap();
    assert_eq!(resp.status(), 200);
    let body: serde_json::Value = resp.json().await.unwrap();
    assert_eq!(body["ok"], true);
}

#[actix_web::test]
async fn test_contract_review_disclaimer() {
    let base = spawn_app().await;
    let resp = http_client()
        .get(format!("{base}/api/contract-review/disclaimer"))
        .send()
        .await
        .unwrap();
    assert_eq!(resp.status(), 200);
    let body: serde_json::Value = resp.json().await.unwrap();
    assert_eq!(body["ok"], true);
    let text = body["disclaimer"].as_str().unwrap();
    assert!(text.contains("不替代"));
}

#[actix_web::test]
async fn test_full_workflow_healthz() {
    let base = spawn_app().await;
    let resp = http_client()
        .get(format!("{base}/api/full-workflow/full-workflow/healthz"))
        .send()
        .await
        .unwrap();
    assert_eq!(resp.status(), 200);
    let body: serde_json::Value = resp.json().await.unwrap();
    assert_eq!(body["ok"], true);
    // upstream 不通, ready 应该是 false (degraded mode)
    assert_eq!(body["ready"], false);
}

#[actix_web::test]
async fn test_skill_manifest_has_2_skills() {
    let base = spawn_app().await;
    let resp = http_client()
        .get(format!("{base}/api/skill/manifest"))
        .send()
        .await
        .unwrap();
    assert_eq!(resp.status(), 200);
    let body: serde_json::Value = resp.json().await.unwrap();
    let skills = body["skills"].as_array().unwrap();
    assert_eq!(skills.len(), 2, "Skill 2 + Skill 3");
    let ids: Vec<&str> = skills.iter().map(|s| s["id"].as_str().unwrap()).collect();
    assert!(ids.contains(&"skill_2_contract_review"));
    assert!(ids.contains(&"skill_3_doc_gen"));
}

#[actix_web::test]
async fn test_doc_gen_health() {
    let base = spawn_app().await;
    let resp = http_client()
        .get(format!("{base}/api/doc-gen/health"))
        .send()
        .await
        .unwrap();
    assert_eq!(resp.status(), 200);
    let body: serde_json::Value = resp.json().await.unwrap();
    assert_eq!(body["ok"], true);
}

#[actix_web::test]
async fn test_doc_gen_rollout_status() {
    let base = spawn_app().await;
    let resp = http_client()
        .get(format!("{base}/api/doc-gen/rollout/status"))
        .send()
        .await
        .unwrap();
    assert_eq!(resp.status(), 200);
    let body: serde_json::Value = resp.json().await.unwrap();
    assert_eq!(body["skill3_letter_v2"]["rollout_pct"], 100);
    assert_eq!(body["skill3_letter_v2"]["current"], "v2");
}

#[actix_web::test]
async fn test_4_module_endpoint_count() {
    let base = spawn_app().await;
    let resp = http_client()
        .get(format!("{base}/manifest"))
        .send()
        .await
        .unwrap();
    let body: serde_json::Value = resp.json().await.unwrap();
    let modules = body["modules"].as_array().unwrap();
    let total: usize = modules
        .iter()
        .map(|m| m["endpoints"].as_array().unwrap().len())
        .sum();
    assert!(
        total >= 20,
        "4 模块端点总数 >= 20, 实际 {}",
        total
    );
}