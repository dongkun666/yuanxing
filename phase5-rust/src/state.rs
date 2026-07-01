//! 共享应用状态 (config + upstream http client)

use std::sync::Arc;

use crate::config::AppConfig;

#[derive(Clone)]
pub struct AppState {
    pub config: Arc<AppConfig>,
    pub http: reqwest::Client,
}

impl AppState {
    pub fn new(config: AppConfig) -> Self {
        let http = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(30))
            .pool_idle_timeout(std::time::Duration::from_secs(60))
            .build()
            .expect("reqwest client init");

        Self {
            config: Arc::new(config),
            http,
        }
    }
}

impl Default for AppState {
    fn default() -> Self {
        Self::new(AppConfig::default())
    }
}