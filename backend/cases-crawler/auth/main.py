"""
LexPrime Auth FastAPI Skeleton
2026-06-28 · W1 脚手架 → 2026-06-29 · W2 业务端点实施

W1 范围:
- FastAPI app 启动
- 4 张表自动创建 (init_auth_tables)
- /api/auth/health 健康检查 (验证表是否就位)

W2 实施 (本文件):
- POST /api/auth/register       注册 (bcrypt + email verify + 律师档案)
- POST /api/auth/login          登录 (bcrypt verify + JWT 签发 + 失败锁定)
- POST /api/auth/refresh        Token 刷新 (refresh_token 轮转, 防重放)
- POST /api/auth/logout         登出 (撤销 refresh_token) - Bonus
- GET  /api/auth/me             当前用户信息

W3+ 计划:
- POST /api/auth/otp/send       发送 OTP (邮箱/手机, W4 接 SendGrid)
- POST /api/auth/otp/verify     验证 OTP
- POST /api/auth/password/reset 密码重置
- POST /api/auth/license/upload 执业证上传 (W3 PaddleOCR)

启动方式:
    uvicorn auth.main:app --host 0.0.0.0 --port 8001
    或: python -m auth.main
"""
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from auth.db import get_db, init_auth_tables
from auth.dependencies import get_current_user
from auth.models import User
from auth.schemas import (
    HealthOut,
    LoginRequest,
    LogoutRequest,
    MeResponse,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
)
from auth.security import (
    AccountLockedError,
    AuthError,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError,
)
from auth.services import (
    EmailAlreadyRegisteredError,
    LicenseAlreadyRegisteredError,
    authenticate_user,
    logout as logout_service,
    refresh_tokens as refresh_service,
    register_user,
)
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
    description="LexPrime Auth Module · W2 业务端点 (Phase 4 P0)",
    version="0.2.0",
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


# ========== 客户端信息提取 ==========
def _client_meta(request: Request) -> dict[str, Optional[str]]:
    """从 request 提 ip / user_agent, 给 service 层审计用"""
    # X-Forwarded-For 优先 (反代场景), 否则 client.host
    xff = request.headers.get("x-forwarded-for")
    ip = xff.split(",")[0].strip() if xff else (request.client.host if request.client else None)
    return {
        "ip_address": ip,
        "user_agent": request.headers.get("user-agent"),
        "device_info": request.headers.get("x-device-info"),
    }


# ========== W1 健康检查 (保留) ==========
@app.get("/api/auth/health", response_model=HealthOut, tags=["meta"])
async def health():
    """
    健康检查

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


# ========== W2 业务端点 ==========
@app.post(
    "/api/auth/register",
    response_model=MeResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
    summary="注册律师账号",
)
async def register(
    payload: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    注册律师账号

    - 邮箱 + 密码 + 律师姓名 + 执业证号 (可选)
    - 服务端 bcrypt 哈希密码
    - 自动建 LawyerProfile (license_status=pending, W3 审核)
    - 触发邮箱验证 OTP (W4 接 SendGrid, 当前 dev 仅 log)
    - 返回当前用户信息 (不签 token, 注册后让前端引导登录)
    """
    meta = _client_meta(request)
    try:
        user = await register_user(payload, db, **meta)
    except EmailAlreadyRegisteredError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": e.code, "message": e.message},
        )
    except LicenseAlreadyRegisteredError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": e.code, "message": e.message},
        )
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )

    # Profile 已在 register_user 同 session 内 commit, refresh 一次以确保可读
    await db.refresh(user, attribute_names=["profile"])
    return MeResponse(
        id=user.id,
        email=user.email,
        phone=user.phone,
        role=user.role,
        subscription_tier=user.subscription_tier,
        is_active=user.is_active,
        is_email_verified=user.is_email_verified,
        is_phone_verified=user.is_phone_verified,
        is_2fa_enabled=user.is_2fa_enabled,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        profile=user.profile,
    )


@app.post(
    "/api/auth/login",
    response_model=TokenPair,
    tags=["auth"],
    summary="登录 (邮箱 + 密码)",
)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    登录

    - 邮箱 + 密码
    - 5 次/小时失败 → 账号锁定 15 分钟
    - 成功 → access (15min) + refresh (7d) token 对
    """
    meta = _client_meta(request)
    try:
        user, access_token, refresh_token, expires_in = await authenticate_user(
            payload, db, **meta
        )
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )
    except AccountLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={"code": e.code, "message": e.message},
        )
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


@app.post(
    "/api/auth/refresh",
    response_model=TokenPair,
    tags=["auth"],
    summary="刷新 access token",
)
async def refresh(
    payload: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    刷新 access token (refresh_token 轮转)

    - 提交上一次的 refresh_token
    - 服务端验证 + 撤销旧 token + 签发新 (access + refresh)
    - 重放检测: 已撤销的 refresh_token 再次使用 → 撤销该 user 所有 token
    """
    meta = _client_meta(request)
    try:
        new_access, new_refresh, expires_in = await refresh_service(
            payload.refresh_token, db, **meta
        )
    except TokenExpiredError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )
    except TokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )

    return TokenPair(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=expires_in,
    )


@app.get(
    "/api/auth/me",
    response_model=MeResponse,
    tags=["auth"],
    summary="当前用户信息",
)
async def me(current_user: User = Depends(get_current_user)):
    """
    当前登录用户信息

    - 需 Authorization: Bearer <access_token>
    - 返回 User + 关联 LawyerProfile (selectinload 一次拿全)
    """
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        phone=current_user.phone,
        role=current_user.role,
        subscription_tier=current_user.subscription_tier,
        is_active=current_user.is_active,
        is_email_verified=current_user.is_email_verified,
        is_phone_verified=current_user.is_phone_verified,
        is_2fa_enabled=current_user.is_2fa_enabled,
        last_login_at=current_user.last_login_at,
        created_at=current_user.created_at,
        profile=current_user.profile,
    )


# ========== Bonus: 登出 ==========
@app.post(
    "/api/auth/logout",
    response_model=MessageResponse,
    tags=["auth"],
    summary="登出 (撤销 refresh_token)",
)
async def logout(
    payload: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    登出: 撤销当前 user 的指定 refresh_token
    - 必须先登录 (携带 access_token)
    - access_token 短期有效, 等自然过期
    """
    success = await logout_service(payload.refresh_token, db, user_id=current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "logout_failed", "message": "refresh_token not found or already revoked"},
        )
    return MessageResponse(message="logged out", code="ok")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "auth.main:app",
        host=settings.api_host,
        port=8001,  # 独立端口, 不冲撞主 API 8000
        reload=True,
    )
