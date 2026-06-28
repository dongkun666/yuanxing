"""
LexPrime Auth FastAPI Skeleton
2026-06-28 · W1 脚手架

W1 范围:
- FastAPI app 启动
- 4 张表自动创建 (init_auth_tables)
- /api/auth/health 健康检查 (验证表是否就位)
- 业务端点 (注册/登录/OTP/Token) 留给 W2

W2+ 计划:
- POST /api/auth/register       注册
- POST /api/auth/login          登录 (密码 + 可选 2FA)
- POST /api/auth/refresh        Token 刷新
- POST /api/auth/logout         登出 (撤销 refresh token)
- POST /api/auth/otp/send       发送 OTP (邮箱/手机)
- POST /api/auth/otp/verify     验证 OTP
- POST /api/auth/password/reset 密码重置
- GET  /api/auth/me             当前用户信息
- POST /api/auth/license/upload 执业证上传 (W3)

启动方式:
    uvicorn auth.main:app --host 0.0.0.0 --port 8001
    或: python -m auth.main
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from auth.db import init_auth_tables
from auth.schemas import HealthOut
from core.config import settings
from core.db import Database, ESClient, Neo4jClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App 生命周期: 启动建表, 关闭释放连接"""
    # 启动
    logger.info("Auth module starting...")
    await Database.init()
    await ESClient.init()
    await Neo4jClient.init()
    tables_ready = await init_auth_tables()
    if not tables_ready:
        logger.warning("⚠️  Auth tables not ready, but app will continue (W1 skeleton)")
    logger.info("Auth module started")
    yield
    # 关闭
    await Database.close()
    await ESClient.close()
    await Neo4jClient.close()
    logger.info("Auth module stopped")


app = FastAPI(
    title="LexPrime Auth API",
    description="LexPrime Auth Module · W1 脚手架 (Phase 4 P0)",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS (复用主 API 配置)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== W1 健康检查 (验证 scaffold 就位) ==========
@app.get("/api/auth/health", response_model=HealthOut)
async def health():
    """
    W1 健康检查

    返回:
    - status: ok / degraded
    - tables_ready: 4 张 auth_* 表是否创建成功
    """
    from sqlalchemy import inspect
    from core.db import Database as Db

    tables_ready = False
    if Db._engine is not None:
        try:
            async with Db._engine.connect() as conn:
                # SQLite 走 sync inspector; PG 同样
                def check_tables(sync_conn):
                    insp = inspect(sync_conn)
                    expected = {"auth_users", "auth_lawyer_profiles", "auth_tokens", "auth_otp_logs"}
                    existing = set(insp.get_table_names())
                    missing = expected - existing
                    return len(missing) == 0

                tables_ready = await conn.run_sync(check_tables)
        except Exception as e:
            logger.error(f"Health check failed: {e}")

    return HealthOut(
        status="ok" if tables_ready else "degraded",
        tables_ready=tables_ready,
    )


# ========== W2+ 业务端点 (预留, 暂不实现) ==========
# @app.post("/api/auth/register", response_model=UserOut)
# async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
#     """W2: 注册 + 邮箱验证"""
#     raise NotImplementedError("W2 实施")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "auth.main:app",
        host=settings.api_host,
        port=8001,  # 独立端口, 不冲撞主 API 8000
        reload=True,
    )
