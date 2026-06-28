"""
LexPrime 配置加载
2026-06-28
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


# 项目根目录: 这个文件 (core/config.py) 的父目录的父目录
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DB_PATH = _PROJECT_ROOT / "data" / "lexprime.db"
_DEFAULT_DB_URL = f"sqlite+aiosqlite:///{_DEFAULT_DB_PATH.as_posix().lstrip('/')}"


class Settings(BaseSettings):
    """应用配置 - 全部从 .env 加载"""

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "lexprime"
    postgres_user: str = "lexprime"
    postgres_password: str = "lexprime_dev_pwd"
    # 默认 SQLite dev (零依赖); 生产用 PG: postgresql+asyncpg://...
    database_url: str = _DEFAULT_DB_URL

    # Elasticsearch
    es_host: str = "localhost"
    es_port: int = 9200
    es_scheme: str = "http"
    es_user: str = "elastic"
    es_password: str = "elastic_dev_pwd"
    es_index_cases: str = "cases"
    es_index_laws: str = "laws"
    es_index_companies: str = "companies"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4j_dev_pwd"

    # 4 个免费数据源
    npc_laws_base_url: str = "https://flk.npc.gov.cn"
    npc_laws_api_url: str = "https://flk.npc.gov.cn/api/"
    court_cases_base_url: str = "https://rmfyalk.court.gov.cn"
    court_cases_api_url: str = "https://rmfyalk.court.gov.cn/api/"
    zhixing_base_url: str = "https://zxgk.court.gov.cn"
    gsxt_base_url: str = "https://www.gsxt.gov.cn"
    gsxt_api_url: str = "https://www.gsxt.gov.cn/api/"

    # cncases
    cncases_raw_path: str = "./data/raw/cncases"
    cncases_batch_size: int = 5000

    # 爬虫
    crawler_concurrent: int = 10
    crawler_delay_ms: int = 1000
    crawler_timeout: int = 30
    crawler_max_retries: int = 3
    crawler_user_agent: str = "Mozilla/5.0 (LexPrime Bot; +https://lexprime.com/bot)"

    # 代理
    proxy_enabled: bool = False
    proxy_pool: str = ""

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = True
    api_cors_origins: str = "http://localhost:8080,http://127.0.0.1:8080"

    # 日志
    log_level: str = "INFO"
    log_file: str = "./logs/crawler.log"

    # Auth (Track A W2: JWT + bcrypt)
    # JWT secret 默认 dev 用, 生产必须从 env 覆盖 (auth_secret_key)
    auth_secret_key: str = "lexprime-dev-secret-please-change-in-production-32chars"
    auth_jwt_algorithm: str = "HS256"
    auth_access_token_ttl_min: int = 15   # access 15 min
    auth_refresh_token_ttl_days: int = 7  # refresh 7 days
    auth_bcrypt_rounds: int = 12          # bcrypt cost factor
    auth_max_failed_logins: int = 5       # 5 次/小时锁定
    auth_lock_minutes: int = 15           # 锁定 15 min

    # Auth W3: TOTP + Email verify + License OCR
    auth_totp_issuer: str = "LexPrime"           # TOTP QR code issuer name
    auth_totp_window: int = 1                    # TOTP 时间窗 ±1 (允许客户端时钟漂移)
    auth_totp_backup_codes_count: int = 10       # 一次性恢复码 10 个
    auth_email_verify_ttl_hours: int = 24        # 邮箱验证 token 24h 过期
    auth_license_ai_min_score: float = 0.7       # AI 初审通过阈值 (0-1)
    auth_license_ocr_engine: str = "mock"        # OCR 引擎: mock / paddle / aliyun (W4+ 真接)

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
