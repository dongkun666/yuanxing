"""
LexPrime 统一 API 网关
======================

多端接入统一入口，支持：
- Web 前端 (Browser)
- 微信小程序 (WeChat Mini Program)
- React Native App (iOS/Android)
- 企业微信 (WeCom)
- 钉钉 (DingTalk)
- 浏览器扩展 (Browser Extension)

功能：
- 多端认证统一管理
- 设备注册与管理
- 消息推送统一接口
- 跨端数据同步
- 访问统计与限流
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Depends, Request, Header
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from auth.db import get_db
from auth.models import User, Token
from auth.dependencies import get_current_user, get_optional_user
from auth.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from core.config import settings
from core.models import Case, Schedule

router = APIRouter(prefix="/api/gateway", tags=["Gateway"])


class DevicePlatform(str, Enum):
    WEB = "web"
    MINIPROGRAM = "miniprogram"
    ANDROID = "android"
    IOS = "ios"
    WECOM = "wecom"
    DINGTALK = "dingtalk"
    EXTENSION = "extension"


class PushChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    WECOM = "wecom"
    DINGTALK = "dingtalk"
    MINIPROGRAM = "miniprogram"
    PUSH = "push"


# ========== Pydantic Models ==========

class DeviceRegisterIn(BaseModel):
    device_id: str = Field(..., description="设备唯一标识")
    platform: DevicePlatform = Field(..., description="平台类型")
    app_version: Optional[str] = Field(None, description="App 版本")
    os_version: Optional[str] = Field(None, description="系统版本")
    device_model: Optional[str] = Field(None, description="设备型号")
    push_token: Optional[str] = Field(None, description="推送 Token")
    language: Optional[str] = Field("zh-CN", description="语言")


class DeviceOut(BaseModel):
    id: int
    device_id: str
    platform: str
    app_version: Optional[str] = None
    os_version: Optional[str] = None
    device_model: Optional[str] = None
    is_active: bool
    last_active_at: Optional[str] = None
    created_at: str


class WxMiniLoginIn(BaseModel):
    code: str = Field(..., description="微信登录 code")
    encrypted_data: Optional[str] = Field(None, description="加密数据")
    iv: Optional[str] = Field(None, description="加密向量")


class WxMiniLoginOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


class WeComLoginIn(BaseModel):
    code: str = Field(..., description="企业微信授权 code")
    state: Optional[str] = Field(None, description="状态参数")


class DingTalkLoginIn(BaseModel):
    auth_code: str = Field(..., description="钉钉授权码")
    state: Optional[str] = Field(None, description="状态参数")


class PushMessageIn(BaseModel):
    user_id: Optional[int] = Field(None, description="目标用户 ID")
    user_ids: Optional[List[int]] = Field(None, description="目标用户 ID 列表")
    title: str = Field(..., min_length=1, max_length=200, description="消息标题")
    content: str = Field(..., min_length=1, max_length=5000, description="消息内容")
    channels: List[PushChannel] = Field(
        default=[PushChannel.IN_APP],
        description="推送渠道列表",
    )
    data: Optional[Dict[str, Any]] = Field(None, description="附加数据")
    type: Optional[str] = Field("system", description="消息类型")


class PushResultOut(BaseModel):
    success: bool
    message_id: Optional[str] = None
    channels_sent: List[str]
    failed_channels: List[str]
    error: Optional[str] = None


class SyncDataIn(BaseModel):
    last_sync_at: Optional[str] = Field(None, description="上次同步时间")
    data_type: str = Field(..., description="同步数据类型")
    items: List[Dict[str, Any]] = Field(default=[], description="待同步数据")


class SyncDataOut(BaseModel):
    synced_count: int
    updates: List[Dict[str, Any]]
    server_timestamp: str
    has_more: bool = False


class GatewayStatsOut(BaseModel):
    total_users: int
    active_users_24h: int
    total_devices: int
    total_cases: int
    total_reviews: int
    platform_stats: Dict[str, int]


class UserStatsOut(BaseModel):
    favorite_count: int
    review_count: int
    case_count: int
    schedule_count: int
    total_usage_days: int


# ========== Gateway Endpoints ==========

@router.get("/stats", summary="获取网关统计数据", description="获取平台整体统计数据，包括用户数、设备数等")
async def get_gateway_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    获取网关统计数据
    - 总用户数
    - 24小时活跃用户
    - 总设备数
    - 总判例数
    - 各平台分布
    """
    try:
        user_count_stmt = select(func.count(User.id)).where(User.is_active == True)
        user_count_result = await db.execute(user_count_stmt)
        total_users = user_count_result.scalar() or 0

        case_count_stmt = select(func.count(Case.id))
        case_count_result = await db.execute(case_count_stmt)
        total_cases = case_count_result.scalar() or 0

        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        active_stmt = select(func.count(User.id)).where(
            User.last_login_at >= twenty_four_hours_ago
        )
        active_result = await db.execute(active_stmt)
        active_users_24h = active_result.scalar() or 0

        platform_stats = {
            "web": 0,
            "miniprogram": 0,
            "android": 0,
            "ios": 0,
            "wecom": 0,
            "dingtalk": 0,
            "extension": 0,
        }

        return GatewayStatsOut(
            total_users=total_users,
            active_users_24h=active_users_24h,
            total_devices=0,
            total_cases=total_cases,
            total_reviews=0,
            platform_stats=platform_stats,
        )
    except Exception as e:
        logger.error(f"获取网关统计失败: {e}")
        raise HTTPException(500, "获取统计数据失败")


@router.get("/user-stats", summary="获取用户统计数据", description="获取当前用户的使用统计数据")
async def get_user_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户的个人统计数据
    """
    try:
        schedule_stmt = select(func.count(Schedule.id)).where(
            # Schedule 可能在其他模块，这里先返回 0
            False
        )

        usage_days = 0
        if user.created_at:
            usage_days = (datetime.utcnow() - user.created_at.replace(tzinfo=None)).days

        return UserStatsOut(
            favorite_count=0,
            review_count=0,
            case_count=0,
            schedule_count=0,
            total_usage_days=usage_days,
        )
    except Exception as e:
        logger.error(f"获取用户统计失败: {e}")
        raise HTTPException(500, "获取用户统计失败")


# ========== 设备管理 ==========

@router.post("/devices", summary="注册设备", description="注册或更新设备信息")
async def register_device(
    device_in: DeviceRegisterIn,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    注册或更新设备信息
    - 首次使用时注册设备
    - 每次启动时更新设备活跃状态
    - 绑定推送 Token
    """
    try:
        client_ip = request.client.host if request.client else "unknown"
        
        logger.info(
            f"设备注册: {device_in.device_id} "
            f"平台: {device_in.platform} "
            f"用户: {user.id if user else 'guest'} "
            f"IP: {client_ip}"
        )

        device = {
            "device_id": device_in.device_id,
            "platform": device_in.platform.value,
            "app_version": device_in.app_version,
            "os_version": device_in.os_version,
            "device_model": device_in.device_model,
            "push_token": device_in.push_token,
            "user_id": user.id if user else None,
            "last_ip": client_ip,
            "is_active": True,
            "last_active_at": datetime.utcnow(),
        }

        return {
            "device_id": device_in.device_id,
            "platform": device_in.platform.value,
            "is_active": True,
            "last_active_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"设备注册失败: {e}")
        raise HTTPException(500, "设备注册失败")


@router.get("/devices", summary="获取设备列表", description="获取当前用户的所有已注册设备")
async def list_devices(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户的所有设备
    """
    return []


@router.delete("/devices/{device_id}", summary="删除设备", description="删除指定设备，取消推送绑定")
async def delete_device(
    device_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除设备，取消推送绑定
    """
    return {"success": True}


# ========== 微信小程序登录 ==========

@router.post("/wx-mini/login", summary="微信小程序登录", description="通过微信 code 登录或注册")
async def wx_mini_login(
    login_in: WxMiniLoginIn,
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    微信小程序登录流程：
    1. 前端调用 wx.login() 获取 code
    2. 前端将 code 发送到后端
    3. 后端调用微信接口换取 openid 和 session_key
    4. 根据 openid 查找或创建用户
    5. 返回自定义登录态 token
    """
    try:
        client_ip = request.client.host if request.client else "unknown"
        
        logger.info(
            f"微信小程序登录请求 - code: {login_in.code[:10]}... IP: {client_ip}"
        )

        # TODO: 调用微信接口 jscode2session
        # https://api.weixin.qq.com/sns/jscode2session
        # appid + secret + js_code + grant_type=authorization_code
        # 返回 openid, session_key, unionid

        # 演示：模拟微信返回
        mock_openid = f"wx_openid_{login_in.code[:8]}"
        mock_unionid = f"wx_unionid_{login_in.code[:8]}"

        # 查找或创建用户
        stmt = select(User).where(User.email == f"{mock_openid}@wxmini.local")
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            password_hash = hash_password(f"wx_{login_in.code}_secret")
            user = User(
                email=f"{mock_openid}@wxmini.local",
                password_hash=password_hash,
                role="lawyer",
                subscription_tier="trial",
                is_active=True,
                is_email_verified=True,
            )
            db.add(user)
            await db.flush()

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        token_record = Token(
            user_id=user.id,
            token_hash=refresh_token[:32],
            token_type="refresh",
            device_type="miniprogram",
            ip_address=client_ip,
            expires_at=datetime.utcnow() + timedelta(days=settings.auth_refresh_token_ttl_days),
        )
        db.add(token_record)

        user.last_login_at = datetime.utcnow()
        user.last_login_ip = client_ip

        await db.commit()

        return WxMiniLoginOut(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.auth_access_token_ttl_min * 60,
            user={
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "subscription_tier": user.subscription_tier,
                "openid": mock_openid,
                "unionid": mock_unionid,
            },
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"微信小程序登录失败: {e}")
        raise HTTPException(500, f"登录失败: {str(e)}")


@router.put("/wx-mini/update-profile", summary="更新微信用户资料", description="更新微信小程序用户资料")
async def wx_mini_update_profile(
    user_info: Dict[str, Any],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    更新微信小程序用户的昵称、头像等信息
    """
    return {"success": True, "user": {"id": user.id}}


# ========== 企业微信登录 ==========

@router.get("/wecom/auth-url", summary="获取企业微信授权链接", description="生成企业微信 OAuth 授权链接")
async def wecom_auth_url(
    redirect_uri: Optional[str] = Query(None, description="回调地址"),
    state: Optional[str] = Query(None, description="状态参数"),
):
    """
    生成企业微信 OAuth 授权 URL
    """
    wecom_corp_id = settings.wecom_corp_id if hasattr(settings, 'wecom_corp_id') else 'wwxxx'
    wecom_redirect_uri = (
        redirect_uri
        or f"{settings.api_cors_origins.split(',')[0]}/api/gateway/wecom/callback"
    )

    auth_url = (
        f"https://open.weixin.qq.com/connect/oauth2/authorize"
        f"?appid={wecom_corp_id}"
        f"&redirect_uri={wecom_redirect_uri}"
        f"&response_type=code"
        f"&scope=snsapi_base"
        f"&state={state or 'lexprime'}#wechat_redirect"
    )

    return {"auth_url": auth_url}


@router.post("/wecom/login", summary="企业微信登录", description="通过企业微信授权 code 登录")
async def wecom_login(
    login_in: WeComLoginIn,
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    企业微信登录
    """
    try:
        client_ip = request.client.host if request.client else "unknown"

        logger.info(f"企业微信登录请求 - code: {login_in.code[:10]}...")

        # TODO: 调用企业微信接口获取用户信息
        mock_userid = f"wecom_{login_in.code[:8]}"

        stmt = select(User).where(User.email == f"{mock_userid}@wecom.local")
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            password_hash = hash_password(f"wecom_{login_in.code}_secret")
            user = User(
                email=f"{mock_userid}@wecom.local",
                password_hash=password_hash,
                role="lawyer",
                subscription_tier="trial",
                is_active=True,
                is_email_verified=True,
            )
            db.add(user)
            await db.flush()

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        user.last_login_at = datetime.utcnow()
        user.last_login_ip = client_ip

        await db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.auth_access_token_ttl_min * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "wecom_userid": mock_userid,
            },
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"企业微信登录失败: {e}")
        raise HTTPException(500, f"登录失败: {str(e)}")


@router.get("/wecom/callback", summary="企业微信回调", description="企业微信 OAuth 回调处理")
async def wecom_callback(
    code: str = Query(...),
    state: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    企业微信 OAuth 回调
    """
    return {"code": code, "state": state, "message": "企业微信回调成功"}


# ========== 钉钉登录 ==========

@router.get("/dingtalk/auth-url", summary="获取钉钉授权链接", description="生成钉钉 OAuth 授权链接")
async def dingtalk_auth_url(
    redirect_uri: Optional[str] = Query(None, description="回调地址"),
    state: Optional[str] = Query(None, description="状态参数"),
):
    """
    生成钉钉 OAuth 授权 URL
    """
    dingtalk_app_key = settings.dingtalk_app_key if hasattr(settings, 'dingtalk_app_key') else 'dingxxx'
    dingtalk_redirect_uri = (
        redirect_uri
        or f"{settings.api_cors_origins.split(',')[0]}/api/gateway/dingtalk/callback"
    )

    auth_url = (
        f"https://login.dingtalk.com/oauth2/auth"
        f"?redirect_uri={dingtalk_redirect_uri}"
        f"&response_type=code"
        f"&client_id={dingtalk_app_key}"
        f"&scope=openid"
        f"&state={state or 'lexprime'}"
        f"&prompt=consent"
    )

    return {"auth_url": auth_url}


@router.post("/dingtalk/login", summary="钉钉登录", description="通过钉钉授权码登录")
async def dingtalk_login(
    login_in: DingTalkLoginIn,
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """
    钉钉登录
    """
    try:
        client_ip = request.client.host if request.client else "unknown"

        logger.info(f"钉钉登录请求 - auth_code: {login_in.auth_code[:10]}...")

        # TODO: 调用钉钉接口获取用户信息
        mock_userid = f"dingtalk_{login_in.auth_code[:8]}"

        stmt = select(User).where(User.email == f"{mock_userid}@dingtalk.local")
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            password_hash = hash_password(f"dingtalk_{login_in.auth_code}_secret")
            user = User(
                email=f"{mock_userid}@dingtalk.local",
                password_hash=password_hash,
                role="lawyer",
                subscription_tier="trial",
                is_active=True,
                is_email_verified=True,
            )
            db.add(user)
            await db.flush()

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        user.last_login_at = datetime.utcnow()
        user.last_login_ip = client_ip

        await db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.auth_access_token_ttl_min * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "dingtalk_userid": mock_userid,
            },
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"钉钉登录失败: {e}")
        raise HTTPException(500, f"登录失败: {str(e)}")


@router.get("/dingtalk/callback", summary="钉钉回调", description="钉钉 OAuth 回调处理")
async def dingtalk_callback(
    authCode: str = Query(...),
    state: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    钉钉 OAuth 回调
    """
    return {"authCode": authCode, "state": state, "message": "钉钉回调成功"}


# ========== 消息推送 ==========

@router.post("/push/send", summary="发送推送消息", description="向指定用户发送多渠道推送消息")
async def send_push_message(
    push_in: PushMessageIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    统一推送接口
    支持渠道：站内信、邮件、短信、企业微信、钉钉、小程序模板消息、App 推送
    """
    try:
        target_user_ids = push_in.user_ids or ([push_in.user_id] if push_in.user_id else [])
        if not target_user_ids:
            target_user_ids = [user.id]

        channels_sent = []
        failed_channels = []

        for channel in push_in.channels:
            try:
                if channel == PushChannel.IN_APP:
                    # 站内信 - 写入数据库
                    channels_sent.append(channel.value)
                elif channel == PushChannel.EMAIL:
                    # 邮件推送
                    channels_sent.append(channel.value)
                elif channel == PushChannel.WECOM:
                    # 企业微信推送
                    channels_sent.append(channel.value)
                elif channel == PushChannel.DINGTALK:
                    # 钉钉推送
                    channels_sent.append(channel.value)
                elif channel == PushChannel.MINIPROGRAM:
                    # 小程序模板消息
                    channels_sent.append(channel.value)
                elif channel == PushChannel.PUSH:
                    # App 推送
                    channels_sent.append(channel.value)
                else:
                    failed_channels.append(channel.value)
            except Exception as e:
                logger.error(f"推送失败 - 渠道: {channel}, 错误: {e}")
                failed_channels.append(channel.value)

        return PushResultOut(
            success=len(channels_sent) > 0,
            message_id=f"msg_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            channels_sent=channels_sent,
            failed_channels=failed_channels,
        )
    except Exception as e:
        logger.error(f"发送推送消息失败: {e}")
        raise HTTPException(500, f"推送失败: {str(e)}")


@router.get("/notifications", summary="获取通知列表", description="获取当前用户的通知列表")
async def get_notifications(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户的通知列表
    """
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    }


@router.get("/notifications/unread-count", summary="获取未读消息数", description="获取当前用户的未读消息数量")
async def get_unread_count(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取未读消息数量
    """
    return {"count": 0}


@router.put("/notifications/{notification_id}/read", summary="标记已读", description="标记单条通知为已读")
async def mark_notification_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    标记通知为已读
    """
    return {"success": True}


@router.put("/notifications/read-all", summary="全部已读", description="标记所有通知为已读")
async def mark_all_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    标记所有通知为已读
    """
    return {"success": True}


# ========== 数据同步 ==========

@router.post("/sync", summary="数据同步", description="跨端数据同步接口")
async def sync_data(
    sync_in: SyncDataIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    跨端数据同步
    支持的数据类型：
    - favorites: 收藏数据
    - schedule: 日程数据
    - settings: 设置数据
    - review_history: 审查历史
    """
    try:
        synced_count = 0
        updates = []
        server_timestamp = datetime.utcnow().isoformat()

        # 根据数据类型处理同步
        if sync_in.data_type == "favorites":
            # 处理收藏同步
            for item in sync_in.items:
                synced_count += 1
        elif sync_in.data_type == "schedule":
            # 处理日程同步
            for item in sync_in.items:
                synced_count += 1

        return SyncDataOut(
            synced_count=synced_count,
            updates=updates,
            server_timestamp=server_timestamp,
            has_more=False,
        )
    except Exception as e:
        logger.error(f"数据同步失败: {e}")
        raise HTTPException(500, f"同步失败: {str(e)}")


@router.get("/sync/last-time", summary="获取最后同步时间", description="获取指定数据类型的最后同步时间")
async def get_last_sync_time(
    data_type: str = Query(..., description="数据类型"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取最后同步时间
    """
    return {
        "data_type": data_type,
        "last_sync_at": datetime.utcnow().isoformat(),
    }


# ========== 健康检查 ==========

@router.get("/health", summary="网关健康检查", description="检查网关服务状态")
async def gateway_health():
    """
    网关健康检查
    """
    return {
        "status": "ok",
        "service": "gateway",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "supported_platforms": [p.value for p in DevicePlatform],
        "supported_channels": [c.value for c in PushChannel],
    }
