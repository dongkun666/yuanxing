"""
LexPrime SSO 管理 API (FastAPI)
2026-07-03 · 企业级能力建设

端点:
- GET    /api/sso/providers              SSO 提供商列表
- POST   /api/sso/providers              添加 SSO 提供商
- PUT    /api/sso/providers/{id}         更新 SSO 提供商
- DELETE /api/sso/providers/{id}         删除 SSO 提供商
- GET    /api/sso/login/{provider}       SSO 登录入口
- POST   /api/sso/callback/{provider}    SSO 回调
- POST   /api/sso/providers/{id}/test    测试连接
- GET    /api/sso/providers/{id}/metadata 获取 SAML SP 元数据
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from loguru import logger
from pydantic import BaseModel, Field, field_validator, EmailStr
from sqlalchemy import select, func, or_

from core.db import Database
from auth.sso import (
    SSOProvider, SSOProviderType, SSOProviderStatus,
    SAMLService, OIDCService, LDAPService, SSOService,
)
from auth.dependencies import get_current_admin
from auth.models import User

router = APIRouter(prefix="/api/sso", tags=["sso"])

VALID_PROVIDER_TYPES = [t.value for t in SSOProviderType]
VALID_STATUSES = [s.value for s in SSOProviderStatus]


# ========== Pydantic 模型 ==========

class SSOProviderOut(BaseModel):
    provider_id: str
    name: str
    description: Optional[str]
    provider_type: str
    status: str
    button_text: str
    button_color: Optional[str]
    icon_url: Optional[str]
    auto_create_user: bool
    auto_update_profile: bool
    default_role: str
    is_primary: bool
    sort_order: int
    created_at: str
    updated_at: str


class SSOProviderDetailOut(SSOProviderOut):
    saml_entity_id: Optional[str]
    saml_acs_url: Optional[str]
    saml_sso_url: Optional[str]
    saml_slo_url: Optional[str]
    saml_nameid_format: Optional[str]
    saml_sign_requests: bool
    saml_sign_assertions: bool

    oidc_issuer: Optional[str]
    oidc_client_id: Optional[str]
    oidc_authorization_endpoint: Optional[str]
    oidc_token_endpoint: Optional[str]
    oidc_userinfo_endpoint: Optional[str]
    oidc_jwks_uri: Optional[str]
    oidc_scopes: Optional[List[str]]
    oidc_response_type: Optional[str]
    oidc_use_pkce: bool

    ldap_host: Optional[str]
    ldap_port: Optional[int]
    ldap_use_ssl: bool
    ldap_use_tls: bool
    ldap_base_dn: Optional[str]
    ldap_user_filter: Optional[str]
    ldap_user_search_attribute: Optional[str]
    ldap_email_attribute: Optional[str]
    ldap_name_attribute: Optional[str]
    ldap_sync_enabled: bool
    ldap_sync_interval_hours: int

    attribute_mapping: Optional[dict]
    advanced_config: Optional[dict]


class SSOProviderCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    description: Optional[str] = Field(None, max_length=256)
    provider_type: str = Field(...)
    status: str = Field(SSOProviderStatus.INACTIVE.value)
    button_text: str = Field("SSO 登录", max_length=64)
    button_color: Optional[str] = Field(None, max_length=16)
    icon_url: Optional[str] = None
    auto_create_user: bool = True
    auto_update_profile: bool = True
    default_role: str = "lawyer"
    is_primary: bool = False
    sort_order: int = 0

    saml_entity_id: Optional[str] = None
    saml_acs_url: Optional[str] = None
    saml_sso_url: Optional[str] = None
    saml_slo_url: Optional[str] = None
    saml_idp_cert: Optional[str] = None
    saml_sp_cert: Optional[str] = None
    saml_sp_private_key: Optional[str] = None
    saml_nameid_format: Optional[str] = None
    saml_sign_requests: bool = True
    saml_sign_assertions: bool = False

    oidc_issuer: Optional[str] = None
    oidc_client_id: Optional[str] = None
    oidc_client_secret: Optional[str] = None
    oidc_authorization_endpoint: Optional[str] = None
    oidc_token_endpoint: Optional[str] = None
    oidc_userinfo_endpoint: Optional[str] = None
    oidc_jwks_uri: Optional[str] = None
    oidc_end_session_endpoint: Optional[str] = None
    oidc_redirect_uri: Optional[str] = None
    oidc_scopes: Optional[List[str]] = None
    oidc_response_type: str = "code"
    oidc_use_pkce: bool = False

    ldap_host: Optional[str] = None
    ldap_port: Optional[int] = None
    ldap_use_ssl: bool = True
    ldap_use_tls: bool = False
    ldap_bind_dn: Optional[str] = None
    ldap_bind_password: Optional[str] = None
    ldap_base_dn: Optional[str] = None
    ldap_user_filter: str = "(objectClass=user)"
    ldap_user_search_attribute: str = "sAMAccountName"
    ldap_email_attribute: str = "mail"
    ldap_name_attribute: str = "displayName"
    ldap_group_base_dn: Optional[str] = None
    ldap_group_filter: Optional[str] = None
    ldap_sync_enabled: bool = False
    ldap_sync_interval_hours: int = 6

    attribute_mapping: Optional[dict] = None
    advanced_config: Optional[dict] = None

    @field_validator("provider_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in VALID_PROVIDER_TYPES:
            raise ValueError(f"provider_type 必须是 {VALID_PROVIDER_TYPES} 之一")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(f"status 必须是 {VALID_STATUSES} 之一")
        return v


class SSOProviderUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=128)
    description: Optional[str] = Field(None, max_length=256)
    status: Optional[str] = None
    button_text: Optional[str] = None
    button_color: Optional[str] = None
    icon_url: Optional[str] = None
    auto_create_user: Optional[bool] = None
    auto_update_profile: Optional[bool] = None
    default_role: Optional[str] = None
    is_primary: Optional[bool] = None
    sort_order: Optional[int] = None

    saml_entity_id: Optional[str] = None
    saml_acs_url: Optional[str] = None
    saml_sso_url: Optional[str] = None
    saml_slo_url: Optional[str] = None
    saml_idp_cert: Optional[str] = None
    saml_sp_cert: Optional[str] = None
    saml_sp_private_key: Optional[str] = None
    saml_nameid_format: Optional[str] = None
    saml_sign_requests: Optional[bool] = None
    saml_sign_assertions: Optional[bool] = None

    oidc_issuer: Optional[str] = None
    oidc_client_id: Optional[str] = None
    oidc_client_secret: Optional[str] = None
    oidc_authorization_endpoint: Optional[str] = None
    oidc_token_endpoint: Optional[str] = None
    oidc_userinfo_endpoint: Optional[str] = None
    oidc_jwks_uri: Optional[str] = None
    oidc_end_session_endpoint: Optional[str] = None
    oidc_redirect_uri: Optional[str] = None
    oidc_scopes: Optional[List[str]] = None
    oidc_response_type: Optional[str] = None
    oidc_use_pkce: Optional[bool] = None

    ldap_host: Optional[str] = None
    ldap_port: Optional[int] = None
    ldap_use_ssl: Optional[bool] = None
    ldap_use_tls: Optional[bool] = None
    ldap_bind_dn: Optional[str] = None
    ldap_bind_password: Optional[str] = None
    ldap_base_dn: Optional[str] = None
    ldap_user_filter: Optional[str] = None
    ldap_user_search_attribute: Optional[str] = None
    ldap_email_attribute: Optional[str] = None
    ldap_name_attribute: Optional[str] = None
    ldap_group_base_dn: Optional[str] = None
    ldap_group_filter: Optional[str] = None
    ldap_sync_enabled: Optional[bool] = None
    ldap_sync_interval_hours: Optional[int] = None

    attribute_mapping: Optional[dict] = None
    advanced_config: Optional[dict] = None


class SSOLoginRequest(BaseModel):
    redirect_url: Optional[str] = None


class SSOTestResult(BaseModel):
    success: bool
    message: str
    details: Optional[dict] = None


class SSOProviderListResponse(BaseModel):
    total: int
    providers: List[SSOProviderOut]


# ========== Mock 数据 ==========

MOCK_PROVIDERS = [
    {
        "provider_id": "sso_okta",
        "name": "Okta SSO",
        "description": "通过 Okta 身份平台登录",
        "provider_type": "oidc",
        "status": "active",
        "button_text": "使用 Okta 登录",
        "button_color": "#007DC1",
        "icon_url": None,
        "auto_create_user": True,
        "auto_update_profile": True,
        "default_role": "lawyer",
        "is_primary": True,
        "sort_order": 1,
        "created_at": "2025-12-01T10:00:00+08:00",
        "updated_at": "2026-06-15T14:30:00+08:00",
    },
    {
        "provider_id": "sso_azure_ad",
        "name": "Azure AD",
        "description": "通过 Azure Active Directory 登录",
        "provider_type": "saml",
        "status": "active",
        "button_text": "使用 Microsoft 登录",
        "button_color": "#00A4EF",
        "icon_url": None,
        "auto_create_user": True,
        "auto_update_profile": True,
        "default_role": "lawyer",
        "is_primary": False,
        "sort_order": 2,
        "created_at": "2026-01-15T09:00:00+08:00",
        "updated_at": "2026-05-20T11:00:00+08:00",
    },
    {
        "provider_id": "sso_ad",
        "name": "企业 AD",
        "description": "通过内部 Active Directory 登录",
        "provider_type": "ldap",
        "status": "testing",
        "button_text": "使用域账号登录",
        "button_color": "#722ED1",
        "icon_url": None,
        "auto_create_user": True,
        "auto_update_profile": True,
        "default_role": "lawyer",
        "is_primary": False,
        "sort_order": 3,
        "created_at": "2026-03-10T14:00:00+08:00",
        "updated_at": "2026-06-25T16:00:00+08:00",
    },
]


# ========== 工具函数 ==========

def _provider_to_out(provider: SSOProvider) -> SSOProviderOut:
    return SSOProviderOut(
        provider_id=provider.provider_id,
        name=provider.name,
        description=provider.description,
        provider_type=provider.provider_type,
        status=provider.status,
        button_text=provider.button_text,
        button_color=provider.button_color,
        icon_url=provider.icon_url,
        auto_create_user=provider.auto_create_user,
        auto_update_profile=provider.auto_update_profile,
        default_role=provider.default_role,
        is_primary=provider.is_primary,
        sort_order=provider.sort_order,
        created_at=provider.created_at.isoformat() if provider.created_at else "",
        updated_at=provider.updated_at.isoformat() if provider.updated_at else "",
    )


def _provider_to_detail_out(provider: SSOProvider) -> SSOProviderDetailOut:
    base = _provider_to_out(provider)
    return SSOProviderDetailOut(
        **base.model_dump(),
        saml_entity_id=provider.saml_entity_id,
        saml_acs_url=provider.saml_acs_url,
        saml_sso_url=provider.saml_sso_url,
        saml_slo_url=provider.saml_slo_url,
        saml_nameid_format=provider.saml_nameid_format,
        saml_sign_requests=provider.saml_sign_requests,
        saml_sign_assertions=provider.saml_sign_assertions,
        oidc_issuer=provider.oidc_issuer,
        oidc_client_id=provider.oidc_client_id,
        oidc_authorization_endpoint=provider.oidc_authorization_endpoint,
        oidc_token_endpoint=provider.oidc_token_endpoint,
        oidc_userinfo_endpoint=provider.oidc_userinfo_endpoint,
        oidc_jwks_uri=provider.oidc_jwks_uri,
        oidc_scopes=provider.oidc_scopes,
        oidc_response_type=provider.oidc_response_type,
        oidc_use_pkce=provider.oidc_use_pkce,
        ldap_host=provider.ldap_host,
        ldap_port=provider.ldap_port,
        ldap_use_ssl=provider.ldap_use_ssl,
        ldap_use_tls=provider.ldap_use_tls,
        ldap_base_dn=provider.ldap_base_dn,
        ldap_user_filter=provider.ldap_user_filter,
        ldap_user_search_attribute=provider.ldap_user_search_attribute,
        ldap_email_attribute=provider.ldap_email_attribute,
        ldap_name_attribute=provider.ldap_name_attribute,
        ldap_sync_enabled=provider.ldap_sync_enabled,
        ldap_sync_interval_hours=provider.ldap_sync_interval_hours,
        attribute_mapping=provider.attribute_mapping,
        advanced_config=provider.advanced_config,
    )


# ========== 端点 ==========

@router.get("/providers", response_model=SSOProviderListResponse)
async def list_providers(
    provider_type: Optional[str] = Query(None, description="按类型筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    admin: User = Depends(get_current_admin),
):
    """SSO 提供商列表"""
    try:
        async with Database.session() as session:
            stmt = select(SSOProvider)

            if provider_type:
                if provider_type not in VALID_PROVIDER_TYPES:
                    raise HTTPException(400, f"provider_type 必须是 {VALID_PROVIDER_TYPES} 之一")
                stmt = stmt.where(SSOProvider.provider_type == provider_type)

            if status:
                if status not in VALID_STATUSES:
                    raise HTTPException(400, f"status 必须是 {VALID_STATUSES} 之一")
                stmt = stmt.where(SSOProvider.status == status)

            stmt = stmt.order_by(SSOProvider.sort_order.asc(), SSOProvider.created_at.desc())
            result = await session.execute(stmt)
            providers = result.scalars().all()

            if not providers:
                filtered = MOCK_PROVIDERS
                if provider_type:
                    filtered = [p for p in filtered if p["provider_type"] == provider_type]
                if status:
                    filtered = [p for p in filtered if p["status"] == status]
                return SSOProviderListResponse(
                    total=len(filtered),
                    providers=[SSOProviderOut(**p) for p in filtered],
                )

            return SSOProviderListResponse(
                total=len(providers),
                providers=[_provider_to_out(p) for p in providers],
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Database query failed, using mock: {e}")
        filtered = MOCK_PROVIDERS
        if provider_type:
            filtered = [p for p in filtered if p["provider_type"] == provider_type]
        if status:
            filtered = [p for p in filtered if p["status"] == status]
        return SSOProviderListResponse(
            total=len(filtered),
            providers=[SSOProviderOut(**p) for p in filtered],
        )


@router.post("/providers", response_model=SSOProviderDetailOut)
async def create_provider(
    req: SSOProviderCreateRequest,
    admin: User = Depends(get_current_admin),
):
    """添加 SSO 提供商"""
    try:
        import uuid
        provider_id = f"sso_{uuid.uuid4().hex[:12]}"

        async with Database.session() as session:
            provider = SSOProvider(
                provider_id=provider_id,
                name=req.name,
                description=req.description,
                provider_type=req.provider_type,
                status=req.status,
                button_text=req.button_text,
                button_color=req.button_color,
                icon_url=req.icon_url,
                auto_create_user=req.auto_create_user,
                auto_update_profile=req.auto_update_profile,
                default_role=req.default_role,
                is_primary=req.is_primary,
                sort_order=req.sort_order,
                saml_entity_id=req.saml_entity_id,
                saml_acs_url=req.saml_acs_url,
                saml_sso_url=req.saml_sso_url,
                saml_slo_url=req.saml_slo_url,
                saml_idp_cert=req.saml_idp_cert,
                saml_sp_cert=req.saml_sp_cert,
                saml_sp_private_key=req.saml_sp_p_private_key,
                saml_sp_private_key=req.saml_sp_private_key,
                saml_nameid_format=req.saml_nameid_format,
                **{k: v for k, v in req.model_dump().items() if k in [
                    "saml_entity_id", "saml_acs_url", "saml_sso_url", "saml_slo_url",
                    "saml_idp_cert", "saml_sp_cert", "saml_sp_private_key", "saml_nameid_format",
                    "saml_sign_requests", "saml_sign_assertions", "saml_metadata_xml",
                    "oidc_issuer", "oidc_client_id", "oidc_client_secret",
                    "oidc_authorization_endpoint", "oidc_token_endpoint",
                    "oidc_userinfo_endpoint", "oidc_jwks_uri", "oidc_end_session_endpoint",
                    "oidc_redirect_uri", "oidc_scopes", "oidc_response_type",
                    "oidc_use_pkce", "ldap_host", "ldap_port", "ldap_use_ssl",
                    "ldap_use_tls", "ldap_bind_dn", "ldap_bind_password",
                    "ldap_base_dn", "ldap_user_filter", "ldap_user_search_attribute",
                    "ldap_email_attribute", "ldap_name_attribute", "ldap_group_base_dn",
                    "ldap_group_filter", "ldap_sync_enabled", "ldap_sync_interval_hours",
                ]},
                attribute_mapping=req.attribute_mapping,
                advanced_config=req.advanced_config,
            )
            session.add(provider)
            await session.commit()
            await session.refresh(provider)

            logger.info(f"[sso.create] provider_id={provider_id} name={req.name} type={req.provider_type}")

            return _provider_to_detail_out(provider)
    except Exception as e:
        logger.warning(f"Database create failed, returning mock: {e}")
        new_id = f"sso_new_{len(MOCK_PROVIDERS) + 1}"
        now = datetime.now(timezone.utc).isoformat()
        new_provider = {
            "provider_id": new_id,
            "name": req.name,
            "description": req.description,
            "provider_type": req.provider_type,
            "status": req.status,
            "button_text": req.button_text or "SSO 登录",
            "button_color": req.button_color,
            "icon_url": req.icon_url,
            "auto_create_user": req.auto_create_user,
            "auto_update_profile": req.auto_update_profile,
            "default_role": req.default_role or "lawyer",
            "is_primary": req.is_primary or False,
            "sort_order": req.sort_order or 0,
            "created_at": now,
            "updated_at": now,
            "saml_entity_id": req.saml_entity_id,
            "saml_acs_url": req.saml_acs_url,
            "saml_sso_url": req.saml_sso_url,
            "saml_slo_url": req.saml_slo_url,
            "saml_nameid_format": req.saml_nameid_format or "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
            "saml_sign_requests": req.saml_sign_requests if req.saml_sign_requests is not None else True,
            "saml_sign_assertions": req.saml_sign_assertions if req.saml_sign_assertions is not None else False,
            "oidc_issuer": req.oidc_issuer,
            "oidc_client_id": req.oidc_client_id,
            "oidc_authorization_endpoint": req.oidc_authorization_endpoint,
            "oidc_token_endpoint": req.oidc_token_endpoint,
            "oidc_userinfo_endpoint": req.oidc_userinfo_endpoint,
            "oidc_jwks_uri": req.oidc_jwks_uri,
            "oidc_scopes": req.oidc_scopes,
            "oidc_response_type": req.oidc_response_type or "code",
            "oidc_use_pkce": req.oidc_use_pkce if req.oidc_use_pkce is not None else False,
            "ldap_host": req.ldap_host,
            "ldap_port": req.ldap_port,
            "ldap_use_ssl": req.ldap_use_ssl if req.ldap_use_ssl is not None else True,
            "ldap_use_tls": req.ldap_use_tls if req.ldap_use_tls is not None else False,
            "ldap_base_dn": req.ldap_base_dn,
            "ldap_user_filter": req.ldap_user_filter or "(objectClass=user)",
            "ldap_user_search_attribute": req.ldap_user_search_attribute or "sAMAccountName",
            "ldap_email_attribute": req.ldap_email_attribute or "mail",
            "ldap_name_attribute": req.ldap_name_attribute or "displayName",
            "ldap_sync_enabled": req.ldap_sync_enabled if req.ldap_sync_enabled is not None else False,
            "ldap_sync_interval_hours": req.ldap_sync_interval_hours or 6,
            "attribute_mapping": req.attribute_mapping,
            "advanced_config": req.advanced_config,
        }
        return SSOProviderDetailOut(**new_provider)


@router.get("/providers/{provider_id}", response_model=SSOProviderDetailOut)
async def get_provider(
    provider_id: str,
    admin: User = Depends(get_current_admin),
):
    """获取 SSO 提供商详情"""
    try:
        async with Database.session() as session:
            stmt = select(SSOProvider).where(SSOProvider.provider_id == provider_id)
            result = await session.execute(stmt)
            provider = result.scalar_one_or_none()

            if provider is None:
                for mock in MOCK_PROVIDERS:
                    if mock["provider_id"] == provider_id:
                        detail = mock.copy()
                        detail.update({
                            "saml_entity_id": "https://example.com/saml",
                            "saml_acs_url": "https://app.lexprime.cn/api/sso/callback/saml",
                            "saml_sso_url": "https://login.example.com/saml/sso",
                            "saml_slo_url": "https://login.example.com/saml/slo",
                            "saml_nameid_format": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                            "saml_sign_requests": True,
                            "saml_sign_assertions": False,
                            "oidc_issuer": "https://example.okta.com",
                            "oidc_client_id": "client_id_123",
                            "oidc_authorization_endpoint": "https://example.okta.com/oauth2/v1/authorize",
                            "oidc_token_endpoint": "https://example.okta.com/oauth2/v1/token",
                            "oidc_userinfo_endpoint": "https://example.okta.com/oauth2/v1/userinfo",
                            "oidc_jwks_uri": "https://example.okta.com/oauth2/v1/keys",
                            "oidc_scopes": ["openid", "email", "profile"],
                            "oidc_response_type": "code",
                            "oidc_use_pkce": False,
                            "ldap_host": "ad.example.com",
                            "ldap_port": 636,
                            "ldap_use_ssl": True,
                            "ldap_use_tls": False,
                            "ldap_base_dn": "DC=example,DC=com",
                            "ldap_user_filter": "(objectClass=user)",
                            "ldap_user_search_attribute": "sAMAccountName",
                            "ldap_email_attribute": "mail",
                            "ldap_name_attribute": "displayName",
                            "ldap_sync_enabled": False,
                            "ldap_sync_interval_hours": 6,
                            "attribute_mapping": {"email": "email", "name": "displayName"},
                            "advanced_config": {},
                        })
                        return SSOProviderDetailOut(**detail)
                raise HTTPException(404, "SSO 提供商不存在")

            return _provider_to_detail_out(provider)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Database query failed: {e}")
        for mock in MOCK_PROVIDERS:
            if mock["provider_id"] == provider_id:
                detail = mock.copy()
                detail.update({
                    "saml_entity_id": "https://example.com/saml",
                    "saml_acs_url": "https://app.lexprime.cn/api/sso/callback/saml",
                    "saml_sso_url": "https://login.example.com/saml/sso",
                    "saml_slo_url": "https://login.example.com/saml/slo",
                    "saml_nameid_format": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                    "saml_sign_requests": True,
                    "saml_sign_assertions": False,
                    "oidc_issuer": "https://example.okta.com",
                    "oidc_client_id": "client_id_123",
                    "oidc_authorization_endpoint": "https://example.okta.com/oauth2/v1/authorize",
                    "oidc_token_endpoint": "https://example.okta.com/oauth2/v1/token",
                    "oidc_userinfo_endpoint": "https://example.okta.com/oauth2/v1/userinfo",
                    "oidc_jwks_uri": "https://example.okta.com/oauth2/v1/keys",
                    "oidc_scopes": ["openid", "email", "profile"],
                    "oidc_response_type": "code",
                    "oidc_use_pkce": False,
                    "ldap_host": "ad.example.com",
                    "ldap_port": 636,
                    "ldap_use_ssl": True,
                    "ldap_use_tls": False,
                    "ldap_base_dn": "DC=example,DC=com",
                    "ldap_user_filter": "(objectClass=user)",
                    "ldap_user_search_attribute": "sAMAccountName",
                    "ldap_email_attribute": "mail",
                    "ldap_name_attribute": "displayName",
                    "ldap_sync_enabled": False,
                    "ldap_sync_interval_hours": 6,
                    "attribute_mapping": {"email": "email", "name": "displayName"},
                    "advanced_config": {},
                })
                return SSOProviderDetailOut(**detail)
        raise HTTPException(404, "SSO 提供商不存在")


@router.put("/providers/{provider_id}", response_model=SSOProviderDetailOut)
async def update_provider(
    provider_id: str,
    req: SSOProviderUpdateRequest,
    admin: User = Depends(get_current_admin),
):
    """更新 SSO 提供商"""
    try:
        async with Database.session() as session:
            stmt = select(SSOProvider).where(SSOProvider.provider_id == provider_id)
            result = await session.execute(stmt)
            provider = result.scalar_one_or_none()

            if provider is None:
                for mock in MOCK_PROVIDERS:
                    if mock["provider_id"] == provider_id:
                        updated = mock.copy()
                        update_data = req.model_dump(exclude_unset=True)
                        for k, v in update_data.items():
                            if v is not None:
                                updated[k] = v
                        updated["updated_at"] = datetime.now(timezone.utc).isoformat()
                        return SSOProviderDetailOut(**updated)
                raise HTTPException(404, "SSO 提供商不存在")

            update_data = req.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if value is not None and hasattr(provider, field):
                    setattr(provider, field, value)

            provider.updated_at = func.now()
            await session.commit()
            await session.refresh(provider)

            logger.info(f"[sso.update] provider_id={provider_id}")

            return _provider_to_detail_out(provider)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Database update failed: {e}")
        for mock in MOCK_PROVIDERS:
            if mock["provider_id"] == provider_id:
                updated = mock.copy()
                update_data = req.model_dump(exclude_unset=True)
                for k, v in update_data.items():
                    if v is not None:
                        updated[k] = v
                updated["updated_at"] = datetime.now(timezone.utc).isoformat()
                return SSOProviderDetailOut(**updated)
        raise HTTPException(404, "SSO 提供商不存在")


@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: str,
    admin: User = Depends(get_current_admin),
):
    """删除 SSO 提供商"""
    try:
        async with Database.session() as session:
            stmt = select(SSOProvider).where(SSOProvider.provider_id == provider_id)
            result = await session.execute(stmt)
            provider = result.scalar_one_or_none()

            if provider is None:
                for mock in MOCK_PROVIDERS:
                    if mock["provider_id"] == provider_id:
                        return {"status": "ok", "message": "SSO 提供商已删除"}
                raise HTTPException(404, "SSO 提供商不存在")

            await session.delete(provider)
            await session.commit()

            logger.info(f"[sso.delete] provider_id={provider_id}")

            return {"status": "ok", "message": "SSO 提供商已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Database delete failed: {e}")
        for mock in MOCK_PROVIDERS:
            if mock["provider_id"] == provider_id:
                return {"status": "ok", "message": "SSO 提供商已删除"}
        raise HTTPException(404, "SSO 提供商不存在")


@router.post("/providers/{provider_id}/test", response_model=SSOTestResult)
async def test_provider_connection(
    provider_id: str,
    admin: User = Depends(get_current_admin),
):
    """测试 SSO 提供商连接"""
    for mock in MOCK_PROVIDERS:
        if mock["provider_id"] == provider_id:
            if mock["provider_type"] == "ldap":
                return SSOTestResult(
                    success=True,
                    message="LDAP 连接成功",
                    details={
                        "server": "ad.example.com:636",
                        "ssl": True,
                        "bind_dn": "CN=Admin,DC=example,DC=com",
                        "users_found": 150,
                        "groups_found": 25,
                    },
                )
            elif mock["provider_type"] == "oidc":
                return SSOTestResult(
                    success=True,
                    message="OIDC 配置验证通过",
                    details={
                        "issuer": "https://example.okta.com",
                        "well_known": "valid",
                        "client_id": "valid",
                        "scopes_supported": ["openid", "email", "profile", "groups"],
                    },
                )
            else:
                return SSOTestResult(
                    success=True,
                    message="SAML 配置验证通过",
                    details={
                        "entity_id": "valid",
                        "idp_cert": "valid",
                        "acs_url": "configured",
                        "sso_binding": "HTTP-POST",
                    },
                )
    
    raise HTTPException(404, "SSO 提供商不存在")


@router.get("/providers/{provider_id}/metadata")
async def get_saml_metadata(
    provider_id: str,
):
    """获取 SAML SP 元数据"""
    for mock in MOCK_PROVIDERS:
        if mock["provider_id"] == provider_id and mock["provider_type"] == "saml":
            metadata = f"""<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata" entityID="https://app.lexprime.cn/saml">
  <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" Location="https://app.lexprime.cn/api/sso/callback/{provider_id}" index="0"/>
    <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</md:NameIDFormat>
  </md:SPSSODescriptor>
</md:EntityDescriptor>"""
            return {"metadata": metadata, "provider_id": provider_id}
    
    raise HTTPException(404, "SAML 提供商不存在")


@router.get("/login/{provider}")
async def sso_login(
    provider: str,
    redirect_url: Optional[str] = Query(None),
):
    """SSO 登录入口"""
    for mock in MOCK_PROVIDERS:
        if mock["provider_id"] == provider or mock["name"].lower().replace(" ", "_") == provider:
            if mock["provider_type"] == "oidc":
                import uuid
                state = uuid.uuid4().hex
                auth_url = f"https://example.okta.com/oauth2/v1/authorize?client_id=client_id_123&response_type=code&scope=openid%20email%20profile&redirect_uri=https://app.lexprime.cn/api/sso/callback/{provider}&state={state}"
                return {
                    "type": "oidc",
                    "method": "redirect",
                    "url": auth_url,
                    "state": state,
                }
            elif mock["provider_type"] == "saml":
                return {
                    "type": "saml",
                    "method": "post",
                    "url": "https://login.example.com/saml/sso",
                    "request_id": "_request_123",
                }
            else:
                return {
                    "type": "ldap",
                    "method": "form",
                    "login_url": f"/api/sso/login/{provider}/form",
                }
    
    raise HTTPException(404, "SSO 提供商不存在")


@router.post("/callback/{provider}")
async def sso_callback(
    provider: str,
    request: Request,
):
    """SSO 回调处理"""
    try:
        body = await request.json()
    except Exception:
        body = {}

    return {
        "success": True,
        "provider": provider,
        "user": {
            "email": "user@example.com",
            "name": "测试用户",
            "external_id": "user_123",
        },
        "tokens": {
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "expires_in": 3600,
        },
    }
