"""
LexPrime 系统设置 API (FastAPI)
2026-07-03

端点:
- GET  /api/settings              获取系统设置
- PUT  /api/settings              更新系统设置

设置分类:
- basic:       基本设置 (网站名称、Logo、描述)
- notification: 通知设置 (邮件通知开关、频率)
- security:    安全设置 (密码策略、登录尝试次数)
- data:        数据设置 (自动清理、备份策略)
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, DateTime, Index, select

from core.db import Database
from core.models import Base

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(String(64), primary_key=True)
    category = Column(String(32), nullable=False, index=True)
    key = Column(String(64), nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(String(256))
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_settings_category_key", "category", "key"),
    )


class BasicSettings(BaseModel):
    site_name: str = Field(default="LexPrime", description="网站名称")
    site_description: str = Field(default="智能法律助手", description="网站描述")
    logo_url: str = Field(default="", description="Logo URL")


class NotificationSettings(BaseModel):
    email_notification_enabled: bool = Field(default=True, description="邮件通知开关")
    notification_frequency: str = Field(default="daily", description="通知频率 (即时/每日/每周)")


class SecuritySettings(BaseModel):
    password_min_length: int = Field(default=8, description="密码最小长度")
    password_require_uppercase: bool = Field(default=True, description="要求大写字母")
    password_require_lowercase: bool = Field(default=True, description="要求小写字母")
    password_require_number: bool = Field(default=True, description="要求数字")
    password_require_special: bool = Field(default=False, description="要求特殊字符")
    max_login_attempts: int = Field(default=5, description="最大登录尝试次数")
    lockout_duration_minutes: int = Field(default=15, description="锁定时长(分钟)")


class DataSettings(BaseModel):
    auto_cleanup_enabled: bool = Field(default=True, description="自动清理开关")
    auto_cleanup_days: int = Field(default=90, description="自动清理保留天数")
    backup_enabled: bool = Field(default=True, description="备份开关")
    backup_frequency: str = Field(default="daily", description="备份频率")


class SettingsResponse(BaseModel):
    basic: BasicSettings
    notification: NotificationSettings
    security: SecuritySettings
    data: DataSettings


class SettingsUpdateRequest(BaseModel):
    basic: Optional[BasicSettings] = None
    notification: Optional[NotificationSettings] = None
    security: Optional[SecuritySettings] = None
    data: Optional[DataSettings] = None


DEFAULT_SETTINGS = {
    "basic": {
        "site_name": "LexPrime",
        "site_description": "智能法律助手",
        "logo_url": "",
    },
    "notification": {
        "email_notification_enabled": True,
        "notification_frequency": "daily",
    },
    "security": {
        "password_min_length": 8,
        "password_require_uppercase": True,
        "password_require_lowercase": True,
        "password_require_number": True,
        "password_require_special": False,
        "max_login_attempts": 5,
        "lockout_duration_minutes": 15,
    },
    "data": {
        "auto_cleanup_enabled": True,
        "auto_cleanup_days": 90,
        "backup_enabled": True,
        "backup_frequency": "daily",
    },
}


async def _load_settings() -> dict:
    result = {}
    for category, defaults in DEFAULT_SETTINGS.items():
        result[category] = defaults.copy()

    async with Database.session() as session:
        stmt = select(SystemSetting)
        settings_result = await session.execute(stmt)
        settings = settings_result.scalars().all()

        for setting in settings:
            if setting.category not in result:
                result[setting.category] = {}
            try:
                result[setting.category][setting.key] = setting.value
            except (ValueError, TypeError):
                result[setting.category][setting.key] = setting.value

    return result


async def _save_settings(settings: dict):
    async with Database.session() as session:
        for category, items in settings.items():
            for key, value in items.items():
                stmt = select(SystemSetting).where(
                    SystemSetting.category == category,
                    SystemSetting.key == key,
                )
                result = await session.execute(stmt)
                setting = result.scalar_one_or_none()

                if setting:
                    setting.value = str(value)
                    setting.updated_at = datetime.now(timezone.utc)
                else:
                    new_setting = SystemSetting(
                        id=f"{category}.{key}",
                        category=category,
                        key=key,
                        value=str(value),
                        updated_at=datetime.now(timezone.utc),
                    )
                    session.add(new_setting)


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """获取系统设置"""
    settings = await _load_settings()

    return SettingsResponse(
        basic=BasicSettings(**settings.get("basic", DEFAULT_SETTINGS["basic"])),
        notification=NotificationSettings(**settings.get("notification", DEFAULT_SETTINGS["notification"])),
        security=SecuritySettings(**settings.get("security", DEFAULT_SETTINGS["security"])),
        data=DataSettings(**settings.get("data", DEFAULT_SETTINGS["data"])),
    )


@router.put("", response_model=SettingsResponse)
async def update_settings(req: SettingsUpdateRequest):
    """更新系统设置"""
    settings = await _load_settings()

    if req.basic:
        settings["basic"].update(req.basic.dict(exclude_unset=True))

    if req.notification:
        settings["notification"].update(req.notification.dict(exclude_unset=True))

    if req.security:
        settings["security"].update(req.security.dict(exclude_unset=True))

    if req.data:
        settings["data"].update(req.data.dict(exclude_unset=True))

    await _save_settings(settings)

    logger.info("[settings.update] 系统设置已更新")

    return SettingsResponse(
        basic=BasicSettings(**settings.get("basic", DEFAULT_SETTINGS["basic"])),
        notification=NotificationSettings(**settings.get("notification", DEFAULT_SETTINGS["notification"])),
        security=SecuritySettings(**settings.get("security", DEFAULT_SETTINGS["security"])),
        data=DataSettings(**settings.get("data", DEFAULT_SETTINGS["data"])),
    )