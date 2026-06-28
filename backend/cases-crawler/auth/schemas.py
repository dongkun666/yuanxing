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
    """W1 健康检查响应"""

    status: str = "ok"
    module: str = "auth"
    version: str = "0.1.0"
    tables_ready: bool
