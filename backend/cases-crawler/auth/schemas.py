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
