//! 路由注册 — 4 模块 scope 挂载

use actix_web::web;

pub mod contract_review;
pub mod doc_gen;
pub mod full_workflow;
pub mod skill;

/// 4 模块路由总注册
pub fn register(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/api/contract-review")
            .configure(contract_review::register),
    )
    .service(
        web::scope("/api/full-workflow").configure(full_workflow::register),
    )
    .service(web::scope("/api/skill").configure(skill::register))
    .service(web::scope("/api/doc-gen").configure(doc_gen::register));
}