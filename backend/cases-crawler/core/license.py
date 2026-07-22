"""
LexPrime 私有化部署 - 离线激活系统
2026-07-03 · 企业级能力建设

功能模块:
- License 生成与验证
- 机器指纹采集
- 离线激活
- 使用期限管理
- 功能模块授权
"""
from __future__ import annotations

import os
import json
import base64
import hashlib
import platform
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy import String, Text, DateTime, Boolean, Integer, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

from core.models import Base
from core.config import settings


class LicenseStatus(str, Enum):
    """License 状态"""
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALID = "invalid"
    REVOKED = "revoked"
    TRIAL = "trial"
    NOT_ACTIVATED = "not_activated"


class LicenseTier(str, Enum):
    """License 版本"""
    COMMUNITY = "community"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    ULTIMATE = "ultimate"


class LicenseModule(str, Enum):
    """功能模块"""
    CASE_SEARCH = "case_search"
    CONTRACT_REVIEW = "contract_review"
    DOC_GENERATION = "doc_generation"
    AI_SERVICES = "ai_services"
    MULTI_TENANT = "multi_tenant"
    SSO = "sso"
    AUDIT_LOG = "audit_log"
    ORG_MANAGEMENT = "org_management"
    API_ACCESS = "api_access"
    DATA_EXPORT = "data_export"
    CUSTOM_BRANDING = "custom_branding"
    PRIORITY_SUPPORT = "priority_support"


# ========== License 模型 ==========

class License(Base):
    """
    License 表

    存储系统激活的 License 信息。
    """
    __tablename__ = "licenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    license_key: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)
    license_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    tier: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=LicenseStatus.NOT_ACTIVATED.value, index=True, nullable=False)

    customer_name: Mapped[str] = mapped_column(String(256))
    customer_email: Mapped[Optional[str]] = mapped_column(String(128))
    customer_company: Mapped[Optional[str]] = mapped_column(String(256))

    machine_fingerprint: Mapped[Optional[str]] = mapped_column(String(512), index=True)
    machine_info: Mapped[Optional[dict]] = mapped_column(JSON)

    issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    trial_days: Mapped[int] = mapped_column(Integer, default=0)

    max_users: Mapped[int] = mapped_column(Integer, default=10)
    max_tenants: Mapped[int] = mapped_column(Integer, default=1)
    max_storage_gb: Mapped[int] = mapped_column(Integer, default=100)
    max_api_calls_per_day: Mapped[int] = mapped_column(Integer, default=10000)

    modules: Mapped[Optional[List[str]]] = mapped_column(JSON)
    features: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    is_offline: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    activation_code: Mapped[Optional[str]] = mapped_column(Text)

    last_check_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_check_result: Mapped[Optional[str]] = mapped_column(String(64))

    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", onupdate="now()", nullable=False
    )

    __table_args__ = (
        Index("idx_license_status_tier", "status", "tier"),
        Index("idx_license_expires", "expires_at"),
    )


# ========== 机器指纹 ==========

class MachineFingerprint:
    """
    机器指纹 - 框架性实现

    采集机器硬件和系统信息, 生成唯一机器指纹。
    """

    @staticmethod
    def get_machine_info() -> dict:
        """
        获取机器信息 - 框架性实现

        返回:
            包含系统信息、硬件信息的字典
        """
        try:
            hostname = platform.node()
            system = platform.system()
            release = platform.release()
            version = platform.version()
            machine = platform.machine()
            processor = platform.processor()
            cpu_count = os.cpu_count() or 0

            try:
                import socket
                ip_addresses = []
                hostname_full = socket.gethostname()
                try:
                    ip_addresses = socket.gethostbyname_ex(hostname_full)[2]
                except Exception:
                    pass
            except Exception:
                ip_addresses = []
                hostname_full = hostname

            try:
                mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                                        for elements in range(0, 8 * 6, 8)][::-1])
            except Exception:
                mac_address = ""

            return {
                "hostname": hostname,
                "system": system,
                "system_release": release,
                "system_version": version,
                "architecture": machine,
                "processor": processor,
                "cpu_count": cpu_count,
                "ip_addresses": ip_addresses,
                "mac_address": mac_address,
                "boot_disk_serial": MachineFingerprint._get_disk_serial(),
                "motherboard_serial": MachineFingerprint._get_board_serial(),
            }
        except Exception:
            return {
                "hostname": "unknown",
                "system": platform.system(),
                "architecture": platform.machine(),
                "cpu_count": os.cpu_count() or 0,
            }

    @staticmethod
    def _get_disk_serial() -> str:
        """获取磁盘序列号 - 框架性实现"""
        try:
            if platform.system() == "Linux":
                try:
                    with open("/root/lexprime_disk_id", "r") as f:
                        return f.read().strip()
                except Exception:
                    pass
                return "disk_" + hashlib.md5(platform.node().encode()).hexdigest()[:16]
            elif platform.system() == "Windows":
                return "disk_" + hashlib.md5(platform.node().encode()).hexdigest()[:16]
            else:
                return "disk_" + hashlib.md5(platform.node().encode()).hexdigest()[:16]
        except Exception:
            return ""

    @staticmethod
    def _get_board_serial() -> str:
        """获取主板序列号 - 框架性实现"""
        try:
            return "board_" + hashlib.sha256(
                (platform.node() + platform.processor() + platform.machine()).encode()
            ).hexdigest()[:16]
        except Exception:
            return ""

    @staticmethod
    def generate_fingerprint() -> str:
        """
        生成机器指纹 - 框架性实现

        返回:
            机器指纹字符串
        """
        info = MachineFingerprint.get_machine_info()

        fingerprint_source = "|".join([
            info.get("mac_address", ""),
            info.get("boot_disk_serial", ""),
            info.get("motherboard_serial", ""),
            info.get("hostname", ""),
            info.get("processor", ""),
        ])

        fingerprint = hashlib.sha256(fingerprint_source.encode()).hexdigest()
        return fingerprint

    @staticmethod
    def get_hardware_id() -> str:
        """
        获取硬件 ID (短格式)

        返回:
            短格式硬件 ID
        """
        fp = MachineFingerprint.generate_fingerprint()
        return fp[:32].upper()


# ========== License 管理 ==========

class LicenseManager:
    """
    License 管理器 - 框架性实现

    提供 License 的生成、验证、激活等功能。
    """

    # 内置的默认 License (用于开发/演示)
    _default_license: Optional[dict] = None

    @staticmethod
    def generate_license_key(
        tier: str,
        customer_name: str,
        max_users: int = 10,
        max_tenants: int = 1,
        modules: Optional[List[str]] = None,
        duration_days: int = 365,
        is_offline: bool = True,
    ) -> dict:
        """
        生成 License - 框架性实现

        参数:
            tier: 版本
            customer_name: 客户名称
            max_users: 最大用户数
            max_tenants: 最大租户数
            modules: 授权模块列表
            duration_days: 有效期天数
            is_offline: 是否离线激活

        返回:
            License 信息字典
        """
        import secrets

        license_id = f"LIC-{secrets.token_hex(6).upper()}"
        license_key = LicenseManager._generate_license_key(tier, license_id)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=duration_days)

        if modules is None:
            modules = [m.value for m in LicenseModule]

        license_data = {
            "license_id": license_id,
            "license_key": license_key,
            "tier": tier,
            "customer_name": customer_name,
            "max_users": max_users,
            "max_tenants": max_tenants,
            "modules": modules,
            "issued_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "is_offline": is_offline,
            "features": {
                "ai_services": True,
                "advanced_search": True,
                "data_export": True,
                "api_access": True,
            },
        }

        return license_data

    @staticmethod
    def _generate_license_key(tier: str, license_id: str) -> str:
        """生成 License Key - 框架性实现"""
        import secrets
        random_part = secrets.token_hex(12).upper()
        return f"{tier[:3].upper()}-{license_id}-{random_part[:8]}-{random_part[8:16]}-{random_part[16:24]}"

    @staticmethod
    def verify_license(license_key: str, machine_fingerprint: Optional[str] = None) -> dict:
        """
        验证 License - 框架性实现

        参数:
            license_key: License Key
            machine_fingerprint: 机器指纹

        返回:
            验证结果
        """
        if not license_key:
            return {
                "valid": False,
                "status": LicenseStatus.NOT_ACTIVATED.value,
                "message": "未激活",
            }

        if machine_fingerprint is None:
            machine_fingerprint = MachineFingerprint.generate_fingerprint()

        is_valid = LicenseManager._check_signature(license_key)

        if not is_valid:
            return {
                "valid": False,
                "status": LicenseStatus.INVALID.value,
                "message": "License 无效",
            }

        license_info = LicenseManager._parse_license_key(license_key)

        now = datetime.now(timezone.utc)
        if license_info.get("expires_at") and license_info["expires_at"] < now:
            return {
                "valid": False,
                "status": LicenseStatus.EXPIRED.value,
                "message": "License 已过期",
                "expires_at": license_info["expires_at"].isoformat(),
            }

        return {
            "valid": True,
            "status": LicenseStatus.ACTIVE.value,
            "message": "License 有效",
            "license_id": license_info.get("license_id"),
            "tier": license_info.get("tier", LicenseTier.PROFESSIONAL.value),
            "expires_at": license_info.get("expires_at", now + timedelta(days=365)).isoformat(),
            "max_users": license_info.get("max_users", 100),
            "max_tenants": license_info.get("max_tenants", 1),
            "modules": license_info.get("modules", [m.value for m in LicenseModule]),
            "features": license_info.get("features", {}),
        }

    @staticmethod
    def _check_signature(license_key: str) -> bool:
        """校验 License 签名 - 框架性实现"""
        if not license_key:
            return False

        if license_key.startswith("PRO-") or license_key.startswith("ENT-") or license_key.startswith("ULT-"):
            return True

        if license_key == settings.license_key if hasattr(settings, "license_key") else None:
            return True

        return len(license_key) >= 20

    @staticmethod
    def _parse_license_key(license_key: str) -> dict:
        """解析 License Key - 框架性实现"""
        parts = license_key.split("-")
        tier = LicenseTier.PROFESSIONAL.value

        if len(parts) >= 1:
            prefix = parts[0].upper()
            if prefix == "ENT":
                tier = LicenseTier.ENTERPRISE.value
            elif prefix == "ULT":
                tier = LicenseTier.ULTIMATE.value
            elif prefix == "PRO":
                tier = LicenseTier.PROFESSIONAL.value
            elif prefix == "COM":
                tier = LicenseTier.COMMUNITY.value

        license_id = "-".join(parts[:2]) if len(parts) >= 2 else license_key

        now = datetime.now(timezone.utc)
        return {
            "license_id": license_id,
            "tier": tier,
            "customer_name": "企业客户",
            "max_users": 100 if tier == LicenseTier.ENTERPRISE.value else 50,
            "max_tenants": 10 if tier == LicenseTier.ENTERPRISE.value else 1,
            "modules": [m.value for m in LicenseModule],
            "issued_at": now - timedelta(days=30),
            "expires_at": now + timedelta(days=335),
            "features": {
                "ai_services": True,
                "advanced_search": True,
                "data_export": True,
                "api_access": True,
                "custom_branding": tier == LicenseTier.ENTERPRISE.value,
                "priority_support": tier == LicenseTier.ENTERPRISE.value,
            },
        }

    @staticmethod
    def activate_offline(activation_code: str, machine_fingerprint: Optional[str] = None) -> dict:
        """
        离线激活 - 框架性实现

        参数:
            activation_code: 激活码
            machine_fingerprint: 机器指纹

        返回:
            激活结果
        """
        if not activation_code:
            return {
                "success": False,
                "message": "激活码不能为空",
            }

        if machine_fingerprint is None:
            machine_fingerprint = MachineFingerprint.generate_fingerprint()

        try:
            decoded = base64.b64decode(activation_code).decode("utf-8")
            license_data = json.loads(decoded)
        except Exception:
            try:
                license_data = {
                    "license_key": activation_code,
                    "tier": LicenseTier.PROFESSIONAL.value,
                    "customer_name": "企业客户",
                    "duration_days": 365,
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"激活码无效: {e}",
                }

        license_key = license_data.get("license_key", activation_code)
        verification = LicenseManager.verify_license(license_key, machine_fingerprint)

        if not verification["valid"]:
            return {
                "success": False,
                "message": verification["message"],
                "status": verification["status"],
            }

        return {
            "success": True,
            "message": "激活成功",
            "license_id": verification.get("license_id"),
            "tier": verification.get("tier"),
            "expires_at": verification.get("expires_at"),
            "max_users": verification.get("max_users"),
            "modules": verification.get("modules"),
        }

    @staticmethod
    def get_current_license() -> dict:
        """
        获取当前 License - 框架性实现

        返回:
            当前 License 信息
        """
        if LicenseManager._default_license:
            return LicenseManager._default_license

        try:
            license_key = getattr(settings, "license_key", None)
            if license_key:
                verification = LicenseManager.verify_license(license_key)
                LicenseManager._default_license = verification
                return verification
        except Exception:
            pass

        now = datetime.now(timezone.utc)
        return {
            "valid": True,
            "status": LicenseStatus.TRIAL.value,
            "message": "试用版",
            "tier": LicenseTier.PROFESSIONAL.value,
            "license_id": "TRIAL-000001",
            "issued_at": (now - timedelta(days=15)).isoformat(),
            "expires_at": (now + timedelta(days=15)).isoformat(),
            "trial_days_remaining": 15,
            "max_users": 5,
            "max_tenants": 1,
            "modules": [
                LicenseModule.CASE_SEARCH.value,
                LicenseModule.CONTRACT_REVIEW.value,
                LicenseModule.DOC_GENERATION.value,
                LicenseModule.AI_SERVICES.value,
            ],
            "features": {
                "ai_services": True,
                "advanced_search": True,
                "data_export": False,
                "api_access": False,
            },
        }

    @staticmethod
    def check_module_enabled(module: str) -> bool:
        """
        检查模块是否已授权 - 框架性实现

        参数:
            module: 模块名称

        返回:
            是否启用
        """
        license_info = LicenseManager.get_current_license()
        modules = license_info.get("modules", [])
        return module in modules or "*" in modules

    @staticmethod
    def get_days_remaining() -> int:
        """
        获取剩余天数

        返回:
            剩余天数
        """
        license_info = LicenseManager.get_current_license()
        expires_at_str = license_info.get("expires_at")
        if not expires_at_str:
            return 999

        try:
            expires_at = datetime.fromisoformat(expires_at_str)
            now = datetime.now(timezone.utc)
            remaining = (expires_at - now).days
            return max(0, remaining)
        except Exception:
            return 999

    @staticmethod
    def is_expired() -> bool:
        """License 是否过期"""
        return LicenseManager.get_days_remaining() <= 0

    @staticmethod
    def is_trial() -> bool:
        """是否为试用版"""
        license_info = LicenseManager.get_current_license()
        return license_info.get("status") == LicenseStatus.TRIAL.value

    @staticmethod
    def get_max_users() -> int:
        """获取最大用户数"""
        license_info = LicenseManager.get_current_license()
        return license_info.get("max_users", 10)

    @staticmethod
    def get_max_tenants() -> int:
        """获取最大租户数"""
        license_info = LicenseManager.get_current_license()
        return license_info.get("max_tenants", 1)

    @staticmethod
    def get_tier() -> str:
        """获取版本"""
        license_info = LicenseManager.get_current_license()
        return license_info.get("tier", LicenseTier.PROFESSIONAL.value)

    @staticmethod
    def get_tier_name() -> str:
        """获取版本名称"""
        tier_names = {
            LicenseTier.COMMUNITY.value: "社区版",
            LicenseTier.PROFESSIONAL.value: "专业版",
            LicenseTier.ENTERPRISE.value: "企业版",
            LicenseTier.ULTIMATE.value: "旗舰版",
        }
        return tier_names.get(LicenseManager.get_tier(), "专业版")


# ========== 激活请求生成 ==========

class ActivationRequest:
    """
    激活请求 - 框架性实现

    用于生成离线激活请求文件。
    """

    @staticmethod
    def generate_request(customer_info: Optional[dict] = None) -> dict:
        """
        生成激活请求 - 框架性实现

        参数:
            customer_info: 客户信息

        返回:
            激活请求信息
        """
        machine_info = MachineFingerprint.get_machine_info()
        fingerprint = MachineFingerprint.generate_fingerprint()
        hardware_id = MachineFingerprint.get_hardware_id()

        request_id = f"REQ-{uuid.uuid4().hex[:12].upper()}"
        now = datetime.now(timezone.utc)

        request_data = {
            "request_id": request_id,
            "request_time": now.isoformat(),
            "machine_fingerprint": fingerprint,
            "hardware_id": hardware_id,
            "machine_info": {
                "hostname": machine_info.get("hostname"),
                "system": machine_info.get("system"),
                "system_release": machine_info.get("system_release"),
                "architecture": machine_info.get("architecture"),
                "cpu_count": machine_info.get("cpu_count"),
            },
            "customer_info": customer_info or {},
            "version": "1.0",
            "product": "LexPrime",
            "product_version": "0.1.0",
        }

        request_code = base64.b64encode(
            json.dumps(request_data, ensure_ascii=False).encode("utf-8")
        ).decode("utf-8")

        return {
            "request_id": request_id,
            "hardware_id": hardware_id,
            "machine_fingerprint": fingerprint,
            "request_code": request_code,
            "request_data": request_data,
            "expires_at": (now + timedelta(days=7)).isoformat(),
        }

    @staticmethod
    def export_request_file(output_path: str, customer_info: Optional[dict] = None) -> str:
        """
        导出激活请求文件 - 框架性实现

        参数:
            output_path: 输出路径
            customer_info: 客户信息

        返回:
            文件路径
        """
        request = ActivationRequest.generate_request(customer_info)

        output_data = {
            "product": "LexPrime 私有化部署激活请求",
            "version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "hardware_id": request["hardware_id"],
            "request_code": request["request_code"],
            "machine_info": request["request_data"]["machine_info"],
            "customer_info": request["request_data"]["customer_info"],
        }

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        return output_path
