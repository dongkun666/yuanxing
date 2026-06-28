"""
LexPrime Auth Pydantic Schemas
2026-06-28 · W1 脚手架 (基础 schema 定义, 业务端点 W2 接)

设计原则:
- 请求/响应严格分离 (In/Out)
- 密码字段绝不返回 (response_model 排除)
- 统一用 pydantic v2 (BaseModel + ConfigDict)
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ========== User ==========
class UserBase(BaseModel):
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=32)
    role: str = "lawyer"
    subscription_tier: str = "trial"


class UserCreate(UserBase):
    """W2 注册时用, 密码由调用方传, 后端 bcrypt"""

    password: str = Field(..., min_length=8, max_length=128)


class UserOut(UserBase):
    """响应模型, 永远不返回 password_hash"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    is_email_verified: bool
    is_phone_verified: bool
    is_2fa_enabled: bool
    last_login_at: Optional[datetime]
    created_at: datetime


# ========== LawyerProfile ==========
class LawyerProfileBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    license_no: Optional[str] = Field(None, max_length=64)
    firm_id: Optional[str] = None
    firm_role: str = "lawyer"
    specialties: Optional[List[str]] = None
    bio: Optional[str] = None
    region: Optional[str] = Field(None, max_length=32)


class LawyerProfileOut(LawyerProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    license_status: str
    license_submitted_at: Optional[datetime]
    license_reviewed_at: Optional[datetime]
    created_at: datetime


# ========== Token ==========
class TokenOut(BaseModel):
    """响应模型, 永远不返回 token_hash"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    token_type: str
    device_info: Optional[str]
    ip_address: Optional[str]
    issued_at: datetime
    expires_at: datetime
    revoked_at: Optional[datetime]


# ========== OTP ==========
class OTPSendRequest(BaseModel):
    """W2 用, 申请发送 OTP"""

    target: EmailStr | str = Field(..., description="邮箱或手机号")
    target_type: str = Field("email", pattern="^(email|phone)$")
    purpose: str = Field(..., pattern="^(register|login|reset_password|verify_email|verify_phone|2fa|license_verify)$")


class OTPVerifyRequest(BaseModel):
    """W2 用, 提交 OTP 验证"""

    target: EmailStr | str
    target_type: str = Field("email", pattern="^(email|phone)$")
    purpose: str = Field(..., pattern="^(register|login|reset_password|verify_email|verify_phone|2fa|license_verify)$")
    code: str = Field(..., min_length=4, max_length=8)


# ========== Health / Skeleton ==========
class HealthOut(BaseModel):
    """健康检查响应"""

    status: str = "ok"
    module: str = "auth"
    version: str = "0.2.0"
    tables_ready: bool


# ========== W2 业务端点 ==========
class RegisterRequest(BaseModel):
    """
    注册请求

    - email: 邮箱 (主账号, 唯一)
    - password: 明文密码 (min 8, 服务端 bcrypt 后存 hash)
    - name: 律师姓名 (同时建 LawyerProfile)
    - license_no: 律师执业证号 (可选, W3 审核)
    - phone: 手机号 (可选)
    """

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=1, max_length=64)
    license_no: Optional[str] = Field(None, max_length=64)
    phone: Optional[str] = Field(None, max_length=32)


class LoginRequest(BaseModel):
    """
    登录请求

    - email + password 验证
    - 返回 access_token (15min) + refresh_token (7d)
    """

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class TokenPair(BaseModel):
    """access + refresh token 配对"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="access token TTL, 秒")


class RefreshRequest(BaseModel):
    """
    Token 刷新请求

    - 提交 refresh_token (上一次登录/刷新时拿到的)
    - 服务端验证 + 轮转 (旧 token 撤销)
    - 返回新 access + 新 refresh
    """

    refresh_token: str = Field(..., min_length=10)


class LogoutRequest(BaseModel):
    """
    登出请求 (Bonus, W2 不在 task list)

    - 提交 refresh_token 撤销
    - access_token 短期有效 (15min), 等自然过期
    """

    refresh_token: str = Field(..., min_length=10)


class MessageResponse(BaseModel):
    """通用消息响应"""

    message: str
    code: str = "ok"


class MeResponse(BaseModel):
    """
    当前用户信息 (GET /api/auth/me)

    - User 基础字段 (不返 password_hash)
    - 关联的 LawyerProfile (如有)
    - W3 还会加 license_status / 审核信息
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    phone: Optional[str]
    role: str
    subscription_tier: str
    is_active: bool
    is_email_verified: bool
    is_phone_verified: bool
    is_2fa_enabled: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    profile: Optional[LawyerProfileOut] = None


# ========== W3: Email Verification ==========
class EmailSendRequest(BaseModel):
    """
    POST /api/auth/email/send - 触发发送邮箱验证邮件

    - user 必须已登录
    - purpose 默认 verify_email (后续扩展 reset_password / change_email)
    """

    purpose: str = Field(
        "verify_email",
        pattern="^(verify_email|reset_password|change_email)$",
        description="用途",
    )


class EmailSendResponse(BaseModel):
    """发送响应 (dev mode: 返回 dev_only_token 用于测试)"""

    message: str
    code: str = "ok"
    dev_only_token: Optional[str] = Field(
        None,
        description="开发模式 token 明文 (生产应改为邮件链接, 不返回)",
    )


class EmailVerifyRequest(BaseModel):
    """POST /api/auth/email/verify - 验证 token"""

    token: str = Field(..., min_length=32, max_length=128)


# ========== W3: TOTP ==========
class TotpSetupRequest(BaseModel):
    """POST /api/auth/totp/setup - 启动 2FA 绑定"""

    password: str = Field(..., min_length=1, max_length=128, description="当前密码二次确认")


class TotpSetupResponse(BaseModel):
    """TOTP setup 响应 (前端展示 QR + 提示用户保存 backup codes)"""

    secret: str = Field(..., description="base32 secret, 用户可手动输入 authenticator")
    qr_code_data_uri: str = Field(..., description="QR code data URI, <img src=...>")
    provisioning_uri: str = Field(..., description="otpauth:// URI")
    backup_codes: List[str] = Field(..., description="10 个一次性恢复码, 仅本次返回")
    is_2fa_enabled: bool = Field(False, description="setup 后为 False, verify 后才 True")


class TotpVerifyRequest(BaseModel):
    """POST /api/auth/totp/verify - 启用 2FA (setup 后用) 或 登录验证"""

    code: str = Field(..., min_length=6, max_length=8, description="6 位 TOTP 或 8 位 backup code")


class TotpVerifyResponse(BaseModel):
    """TOTP verify 响应"""

    verified: bool
    is_2fa_enabled: bool
    method: str = Field(..., description="totp / backup_code")


class TotpDisableRequest(BaseModel):
    """POST /api/auth/totp/disable - 关闭 2FA"""

    password: str = Field(..., min_length=1, max_length=128)
    code: str = Field(..., min_length=6, max_length=8)


# ========== W3: Lawyer License ==========
class LicenseUploadRequest(BaseModel):
    """POST /api/auth/lawyer-license/upload"""

    image_base64: str = Field(..., min_length=100, description="执业证图片/PDF base64")
    filename: str = Field(..., min_length=1, max_length=255)


class LicenseUploadResponse(BaseModel):
    """上传响应"""

    license_status: str
    ai_score: Optional[float] = None
    reason: Optional[str] = None
    ocr_confidence: Optional[float] = None
    extracted_fields: Optional[dict] = None


class LicenseReviewLogOut(BaseModel):
    """审核日志响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    from_status: Optional[str]
    to_status: str
    actor_type: str
    actor_id: Optional[int]
    ai_score: Optional[float]
    reason: Optional[str]
    created_at: datetime


class LicenseStatusResponse(BaseModel):
    """GET /api/auth/lawyer-license/status"""

    license_status: str
    license_image_url: Optional[str]
    license_reject_reason: Optional[str]
    license_submitted_at: Optional[datetime]
    license_reviewed_at: Optional[datetime]
    ocr_data: Optional[dict] = None
    review_logs: List[LicenseReviewLogOut] = []


class LicenseReviewRequest(BaseModel):
    """POST /api/auth/lawyer-license/review (admin)"""

    profile_id: int = Field(..., ge=1)
    decision: str = Field(..., pattern="^(approved|rejected)$")
    reason: str = Field(..., min_length=1, max_length=500)
