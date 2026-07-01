"""
LexPrime Auth FastAPI Skeleton
2026-06-28 · W1 脚手架 → 2026-06-29 · W2 业务端点 → 2026-06-29 · W3 扩展端点

W1 范围:
- FastAPI app 启动
- 4 张表自动创建 (init_auth_tables)
- /api/auth/health 健康检查

W2 业务端点:
- POST /api/auth/register       注册
- POST /api/auth/login          登录
- POST /api/auth/refresh        Token 刷新
- POST /api/auth/logout         登出
- GET  /api/auth/me             当前用户

W3 扩展端点:
- POST /api/auth/email/send             发送邮箱验证邮件 (24h token)
- POST /api/auth/email/verify           验证邮箱 token
- POST /api/auth/totp/setup             TOTP 绑定 (生成 secret + QR + backup codes)
- POST /api/auth/totp/verify            TOTP 验证 (启用 2FA 或登录)
- POST /api/auth/totp/disable           TOTP 解绑
- POST /api/auth/lawyer-license/upload  律师执业证上传 + OCR + AI 初审
- GET  /api/auth/lawyer-license/status  查询审核状态
- POST /api/auth/lawyer-license/review  管理员人工复审 (admin only)

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
from auth.dependencies import get_current_admin, get_current_user
from auth.email_verify import (
    EmailRateLimitedError,
    InvalidVerificationTokenError,
    VerificationTokenExpiredError,
    VerificationTokenUsedError,
    send_email_verification,
    verify_email_token,
)
from auth.license import (
    LicenseAlreadyApprovedError,
    LicenseError,
    LicenseInvalidImageError,
    LicenseNotFoundError,
    LicenseOcrFailedError,
    admin_review_license,
    get_license_status,
    upload_license,
)
from auth.models import User
from auth.schemas import (
    EmailSendRequest,
    EmailSendResponse,
    EmailVerifyRequest,
    HealthOut,
    LicenseReviewLogOut,
    LicenseReviewRequest,
    LicenseStatusResponse,
    LicenseUploadRequest,
    LicenseUploadResponse,
    LoginRequest,
    LogoutRequest,
    MeResponse,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    TotpDisableRequest,
    TotpSetupRequest,
    TotpSetupResponse,
    TotpVerifyRequest,
    TotpVerifyResponse,
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
from auth.totp import (
    InvalidTotpCodeError,
    TotpAlreadyEnabledError,
    TotpError,
    TotpNotEnabledError,
    disable_totp,
    provisioning_uri,
    setup_totp,
    verify_and_enable_totp,
    verify_totp_for_login,
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
    description="LexPrime Auth Module · W3 扩展端点 (Phase 4 P0)",
    version="0.3.0",
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
    - tables_ready: 7 张 auth_* 表是否创建成功 (W1:4 + W3:3)
    """
    from sqlalchemy import inspect
    from core.db import Database as Db

    tables_ready = False
    if Db._engine is not None:
        try:
            async with Db._engine.connect() as conn:
                def check_tables(sync_conn):
                    insp = inspect(sync_conn)
                    expected = {
                        "auth_users",
                        "auth_lawyer_profiles",
                        "auth_tokens",
                        "auth_otp_logs",
                        # W3 新增
                        "auth_email_verifications",
                        "auth_totp_backup_codes",
                        "auth_license_review_logs",
                    }
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


# ========== W2 业务端点 (保留) ==========
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
    - 触发邮箱验证 (W3 dev: log 模式, W4 接 SendGrid)
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
    - (W3 集成提示: 用户启用 2FA 时, W4 会强制 /api/auth/totp/verify 二次验证)
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
    """登出: 撤销当前 user 的指定 refresh_token"""
    success = await logout_service(payload.refresh_token, db, user_id=current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "logout_failed", "message": "refresh_token not found or already revoked"},
        )
    return MessageResponse(message="logged out", code="ok")


# ========== W3 端点: Email Verification ==========
@app.post(
    "/api/auth/email/send",
    response_model=EmailSendResponse,
    tags=["auth-w3"],
    summary="发送邮箱验证邮件",
)
async def email_send(
    payload: EmailSendRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    发送邮箱验证邮件 (24h token)

    - 需登录
    - dev 模式: token 直接出现在响应 + loguru.info (W4 接 SendGrid 改为只发邮件)
    - 重复发送会撤销旧 token
    - 限流: 5 次/小时/IP (settings.auth_max_failed_logins)
    """
    meta = _client_meta(request)
    try:
        token = await send_email_verification(current_user, db, purpose=payload.purpose, **meta)
    except EmailRateLimitedError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": e.code, "message": e.message},
        )
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )

    return EmailSendResponse(
        message="verification email sent (dev mode: token returned below)",
        code="ok",
        dev_only_token=token,
    )


@app.post(
    "/api/auth/email/verify",
    response_model=MeResponse,
    tags=["auth-w3"],
    summary="验证邮箱 token",
)
async def email_verify(
    payload: EmailVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    验证邮箱 token (来自邮件链接)

    - 不需登录 (邮件链接无登录态)
    - token 一次性, 用后失效
    - 24h 过期
    - 成功 -> user.is_email_verified = True
    """
    meta = _client_meta(request)
    try:
        user = await verify_email_token(payload.token, db, **meta)
    except InvalidVerificationTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )
    except VerificationTokenExpiredError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )
    except VerificationTokenUsedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )
    except EmailRateLimitedError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": e.code, "message": e.message},
        )

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


# ========== W3 端点: TOTP ==========
@app.post(
    "/api/auth/totp/setup",
    response_model=TotpSetupResponse,
    tags=["auth-w3"],
    summary="TOTP 2FA 绑定 (第一步)",
)
async def totp_setup(
    payload: TotpSetupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    TOTP setup - 第一步: 生成 secret + QR + backup codes

    - 需登录 + 当前密码二次确认
    - 返回: secret (手动输入), qr_code_data_uri (扫码), backup_codes (10 个, 一次性)
    - 不立即启用, 用户在 authenticator 看到 code 后还需 /totp/verify
    """
    try:
        secret, qr_uri, codes = await setup_totp(current_user, payload.password, db)
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )
    except TotpAlreadyEnabledError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": e.code, "message": e.message},
        )
    except TotpError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )

    return TotpSetupResponse(
        secret=secret,
        qr_code_data_uri=qr_uri,
        provisioning_uri=provisioning_uri(secret, current_user.email),
        backup_codes=codes,
        is_2fa_enabled=current_user.is_2fa_enabled,
    )


@app.post(
    "/api/auth/totp/verify",
    response_model=TotpVerifyResponse,
    tags=["auth-w3"],
    summary="TOTP 验证 (启用 2FA 或登录验证)",
)
async def totp_verify(
    payload: TotpVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    TOTP verify:

    - 场景 A (启用 2FA): is_2fa_enabled=False 但 totp_secret 已存 (刚 setup 过)
      -> verify + 设 is_2fa_enabled=True
    - 场景 B (登录后验证): is_2fa_enabled=True
      -> verify code (TOTP 或 backup)
    """
    code = payload.code.strip()
    is_setup_stage = (
        not current_user.is_2fa_enabled
        and bool(current_user.totp_secret)
        and len(code) == 6
        and code.isdigit()
    )

    if is_setup_stage:
        try:
            await verify_and_enable_totp(current_user, code, db)
        except InvalidTotpCodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": e.code, "message": e.message},
            )
        except TotpNotEnabledError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": e.code, "message": e.message},
            )
        return TotpVerifyResponse(
            verified=True,
            is_2fa_enabled=True,
            method="totp",
        )

    # 场景 B: 登录后验证 (TOTP 6 位 或 backup 8 位)
    try:
        await verify_totp_for_login(current_user, code, db)
    except TotpNotEnabledError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )
    except InvalidTotpCodeError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )

    method = "totp" if len(code) == 6 else "backup_code"
    return TotpVerifyResponse(
        verified=True,
        is_2fa_enabled=current_user.is_2fa_enabled,
        method=method,
    )


@app.post(
    "/api/auth/totp/disable",
    response_model=MessageResponse,
    tags=["auth-w3"],
    summary="关闭 TOTP 2FA",
)
async def totp_disable(
    payload: TotpDisableRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    关闭 TOTP 2FA

    - 需密码 + 当前 code (TOTP 或 backup) 二次确认
    - 清空 secret + 撤销所有 backup codes
    """
    try:
        await disable_totp(current_user, payload.password, payload.code.strip(), db)
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )
    except InvalidTotpCodeError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )
    except TotpNotEnabledError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )

    return MessageResponse(message="2FA disabled", code="ok")


# ========== W3 端点: Lawyer License ==========
@app.post(
    "/api/auth/lawyer-license/upload",
    response_model=LicenseUploadResponse,
    tags=["auth-w3"],
    summary="上传律师执业证 (OCR + AI 初审)",
)
async def license_upload(
    payload: LicenseUploadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    上传律师执业证图片/PDF

    - base64 编码 + 文件名
    - dev 模式: OCR + AI 都走 mock (deterministic)
    - W4+ 接真 PaddleOCR / 阿里云 OCR
    - 状态机: pending → ai_reviewing → human_reviewing | rejected
    - 限流: 5 次/小时/user
    """
    try:
        profile, ai_score, ai_reason = await upload_license(
            current_user, payload.image_base64, payload.filename, db
        )
    except LicenseInvalidImageError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )
    except LicenseOcrFailedError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": e.code, "message": e.message},
        )
    except LicenseAlreadyApprovedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": e.code, "message": e.message},
        )
    except LicenseNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message},
        )
    except LicenseError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": e.code, "message": e.message},
        )

    ocr_data = profile.license_ocr_data or {}

    return LicenseUploadResponse(
        license_status=profile.license_status,
        ai_score=ai_score,
        reason=ai_reason,
        ocr_confidence=ocr_data.get("confidence"),
        extracted_fields={
            k: ocr_data.get(k)
            for k in ("name", "license_no", "firm", "practice_areas")
            if k in ocr_data
        },
    )


@app.get(
    "/api/auth/lawyer-license/status",
    response_model=LicenseStatusResponse,
    tags=["auth-w3"],
    summary="查询律师执业证审核状态",
)
async def license_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    查询当前律师执业证审核状态 + 完整审核历史
    """
    try:
        profile, logs = await get_license_status(current_user, db)
    except LicenseNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message},
        )

    return LicenseStatusResponse(
        license_status=profile.license_status,
        license_image_url=profile.license_image_url,
        license_reject_reason=profile.license_reject_reason,
        license_submitted_at=profile.license_submitted_at,
        license_reviewed_at=profile.license_reviewed_at,
        ocr_data=profile.license_ocr_data,
        review_logs=[LicenseReviewLogOut.model_validate(log) for log in logs],
    )


@app.post(
    "/api/auth/lawyer-license/review",
    response_model=MessageResponse,
    tags=["auth-w3"],
    summary="管理员人工复审 (admin only)",
)
async def license_review(
    payload: LicenseReviewRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    管理员人工复审 (admin role only)

    - 决策: approved / rejected
    - 状态机: human_reviewing → approved | rejected
    - 写审核日志 (actor=admin, 留 reason)
    """
    try:
        await admin_review_license(
            payload.profile_id,
            payload.decision,
            payload.reason,
            admin,
            db,
        )
    except LicenseNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message},
        )
    except LicenseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": e.code, "message": e.message},
        )

    return MessageResponse(
        message=f"license {payload.decision}",
        code="ok",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "auth.main:app",
        host=settings.api_host,
        port=8001,  # 独立端口, 不冲撞主 API 8000
        reload=True,
    )
