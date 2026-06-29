"""
LexPrime 公测邀请码 API Router (W6 Day 2 交付)

端点 (3 个):
- POST /api/invite/generate    admin 入口, 限流 5/min · 生成新邀请码
- POST /api/invite/redeem      用户入口, 1 码 1 用 · 核销 + 关联律师邮箱
- GET  /api/invite/status      查询邀请码状态 (admin/律师自助)

Schema:
- BETA2025-XXXX (4 位随机, 10000 种)
- 3 渠道: review (5 评审) / wechat-group (10 微信群) / founding-member (100 创史)
- 落地: docs/marketing/invite-codes-list.csv (lex-bd 已生成 115 码基线)
- 备份: SQLite (W6 dev) / PostgreSQL (W6 prod via auth_users.invite_code 关联)

PRD: § 11.2.1 公测期试用转化漏斗
Track: D · T-REF-invite (W6)
"""
from __future__ import annotations

import csv
import os
import re
import secrets
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, EmailStr, field_validator
from loguru import logger

from core.config import settings


router = APIRouter(prefix="/api/invite", tags=["marketing:invite"])


# ========== 配置 ==========
# CSV 基线 (lex-bd 已生成 115 码, 3 渠道分布)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CSV_PATH = _PROJECT_ROOT / "data" / "lexprime.db"  # 临时占位
CSV_PATH = Path(settings.log_file).parent.parent / "docs" / "marketing" / "invite-codes-list.csv"
# 修正: 找 yuanxing 项目根的 docs/marketing/invite-codes-list.csv
_CANDIDATE_CSV = [
    Path(__file__).resolve().parent.parent.parent.parent / "docs" / "marketing" / "invite-codes-list.csv",  # yuanxing/docs/marketing/
    Path(__file__).resolve().parent.parent.parent / "docs" / "marketing" / "invite-codes-list.csv",  # cases-crawler/docs/marketing/
    Path.cwd() / "docs" / "marketing" / "invite-codes-list.csv",
    Path.cwd().parent / "docs" / "marketing" / "invite-codes-list.csv",
]
for _p in _CANDIDATE_CSV:
    if _p.exists():
        CSV_PATH = _p
        break

# 内存级邀请码表 (W6 dev 简化, 不依赖 DB 启动)
# 生产应存 auth_users.invite_code + 独立 invite_codes 表
_INVITE_CACHE: dict = {}  # code -> {channel, status, redeemed_at, redeemed_email, batch}
_INVITE_LOCK = Lock()

# 限流 (W6 dev 用内存级, 生产用 Redis)
_RATE_LIMIT_BUCKET: dict = {}  # key -> [timestamp, count]


# ========== 邀请码 schema 校验 ==========
INVITE_PATTERN = re.compile(r"^BETA2025-\d{4}$")
CHANNELS = {"review", "wechat-group", "founding-member"}
BATCHES = {
    "review": ["B1-评审#1-0719", "B2-评审#2-0726"],
    "wechat-group": ["WX-私域群"],
    "founding-member": ["FM-创史001-100"],
}


# ========== Pydantic 模型 ==========

class GenerateRequest(BaseModel):
    """admin 生成邀请码请求"""
    channel: str = Field(..., description="review / wechat-group / founding-member")
    count: int = Field(1, ge=1, le=50, description="生成数量 (1-50)")
    batch: Optional[str] = Field(None, description="批次标识 (B1-评审#1-0719 等)")
    note: Optional[str] = Field(None, max_length=200)
    admin_token: str = Field(..., description="admin 鉴权 token (W6 dev 简化为字符串)")


class GenerateResponse(BaseModel):
    """生成响应"""
    generated: int
    codes: list
    channel: str
    batch: str
    created_at: str


class RedeemRequest(BaseModel):
    """用户核销邀请码请求 (公测 landing 提交)"""
    code: str = Field(..., description="BETA2025-XXXX")
    email: str = Field(..., description="律师工作邮箱")
    source: Optional[str] = Field("beta-landing", description="landing / 微信 / 邮件 / 朋友圈")

    @field_validator("code")
    @classmethod
    def _validate_code(cls, v: str) -> str:
        v = v.strip().upper()
        if not INVITE_PATTERN.match(v):
            raise ValueError(f"邀请码格式错误, 应为 BETA2025-XXXX, 实际: {v}")
        return v

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError(f"邮箱格式错误: {v}")
        # 拒绝纯免费邮箱 (律师工作邮箱规范)
        free_domains = {"163.com", "126.com", "qq.com", "gmail.com", "outlook.com", "hotmail.com", "yahoo.com", "sina.com", "foxmail.com"}
        domain = v.split("@")[-1]
        if domain in free_domains:
            raise ValueError(f"请使用律师工作邮箱, 不接受 {domain} (免费邮箱)")
        return v


class RedeemResponse(BaseModel):
    """核销响应"""
    code: str
    channel: str
    batch: str
    redeemed: bool
    redeemed_at: str
    expires_at: str  # 30 天试用到期
    next: str  # 跳转地址


class StatusResponse(BaseModel):
    """状态查询响应"""
    code: str
    channel: Optional[str]
    batch: Optional[str]
    status: str  # unused / used / expired
    redeemed_at: Optional[str]
    redeemed_email: Optional[str]
    note: Optional[str]


# ========== 工具函数 ==========

def _load_csv_to_cache() -> int:
    """从 CSV 加载邀请码到内存 (W6 dev 简化). 启动时调用一次."""
    global _INVITE_CACHE
    if not CSV_PATH.exists():
        logger.warning(f"邀请码 CSV 不存在: {CSV_PATH} (W6 启动会重新生成)")
        return 0
    count = 0
    try:
        with CSV_PATH.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row.get("code", "").strip()
                if not code or not INVITE_PATTERN.match(code):
                    continue
                _INVITE_CACHE[code] = {
                    "channel": row.get("channel", "").strip(),
                    "batch": row.get("batch", "").strip(),
                    "status": row.get("status", "unused").strip() or "unused",
                    "redeemed_at": row.get("redeemed_at", "").strip() or None,
                    "redeemed_email": row.get("contact", "").strip() or None,
                    "note": row.get("notes", "").strip() or None,
                    "created_at": row.get("created_at", "").strip() or None,
                }
                count += 1
        logger.info(f"✓ 邀请码基线加载: {count} 条 (来源 {CSV_PATH.name})")
    except Exception as e:
        logger.error(f"邀请码 CSV 加载失败: {e}")
    return count


def _persist_to_csv(code: str, data: dict) -> bool:
    """把更新写回 CSV (简单 append + 全量 rewrite). W6 dev 简化, 生产应存 DB."""
    if not CSV_PATH.exists():
        return False
    try:
        rows = []
        with CSV_PATH.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or ["code", "channel", "batch", "status", "assigned_to", "contact", "redeemed_at", "trial_expires_at", "notes", "created_at"]
            for row in reader:
                if row.get("code") == code:
                    row.update({
                        "status": data.get("status", row.get("status", "unused")),
                        "contact": data.get("redeemed_email", row.get("contact", "")),
                        "redeemed_at": data.get("redeemed_at", row.get("redeemed_at", "")),
                        "trial_expires_at": data.get("expires_at", row.get("trial_expires_at", "")),
                    })
                rows.append(row)
        with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return True
    except Exception as e:
        logger.error(f"邀请码 CSV 持久化失败: {e}")
        return False


def _check_rate_limit(key: str, max_per_min: int = 5) -> bool:
    """内存级限流 (W6 dev, 生产用 Redis)."""
    now = time.time()
    bucket = _RATE_LIMIT_BUCKET.get(key, [now, 0])
    if now - bucket[0] > 60:
        bucket = [now, 0]
    if bucket[1] >= max_per_min:
        return False
    bucket[1] += 1
    _RATE_LIMIT_BUCKET[key] = bucket
    return True


def _is_admin(token: str) -> bool:
    """admin 鉴权 (W6 dev 简化为固定 token, 生产用 JWT)."""
    # 公测期固定 admin token (总指挥分发), 不走强鉴权
    expected = os.environ.get("LEXPRIME_ADMIN_TOKEN", "lexprime-w6-admin-dev")
    return token == expected


# ========== 启动钩子: 加载 CSV 基线 ==========

@router.on_event("startup")
async def _startup_load_invite_codes():
    _load_csv_to_cache()


# ========== 端点 ==========

@router.post("/generate", response_model=GenerateResponse)
async def generate_invite_codes(req: GenerateRequest, request: Request):
    """
    admin 入口: 生成新邀请码
    - 限流 5/min (按 admin_token 维度)
    - 一次性生成 1-50 个
    - 写入 CSV (W6 dev 简化, 生产用 auth_users.invite_code 关联)
    """
    # 1. 鉴权
    if not _is_admin(req.admin_token):
        raise HTTPException(401, "admin_token 无效")

    # 2. 限流
    if not _check_rate_limit(f"gen:{req.admin_token}", max_per_min=5):
        raise HTTPException(429, "rate_limit: 生成过于频繁, 每分钟最多 5 次")

    # 3. 校验
    if req.channel not in CHANNELS:
        raise HTTPException(400, f"channel 必须是 {CHANNELS}, 实际: {req.channel}")
    if req.count > 50:
        raise HTTPException(400, "单次生成最多 50 个")

    # 4. 选 batch
    batch = req.batch or (BATCHES[req.channel][0] if BATCHES.get(req.channel) else f"W6-{req.channel}")

    # 5. 生成 codes (避免跟已用的重复)
    codes = []
    with _INVITE_LOCK:
        for _ in range(req.count):
            for attempt in range(20):
                # 4 位随机, 0-9999
                rand4 = f"{secrets.randbelow(10000):04d}"
                code = f"BETA2025-{rand4}"
                if code not in _INVITE_CACHE:
                    break
            else:
                raise HTTPException(500, f"已用尽 10000 种组合, 请考虑扩容 schema (BETA2026-XXXX)")
            _INVITE_CACHE[code] = {
                "channel": req.channel,
                "batch": batch,
                "status": "unused",
                "redeemed_at": None,
                "redeemed_email": None,
                "note": req.note or f"admin 生成 {datetime.now(timezone.utc).isoformat()}",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            codes.append(code)

    # 6. 追加到 CSV
    try:
        file_exists = CSV_PATH.exists()
        with CSV_PATH.open("a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["code", "channel", "batch", "status", "assigned_to", "contact", "redeemed_at", "trial_expires_at", "notes", "created_at"])
            for c in codes:
                d = _INVITE_CACHE[c]
                writer.writerow([c, d["channel"], d["batch"], "unused", "", "", "", "", d["note"], d["created_at"]])
    except Exception as e:
        logger.warning(f"CSV 追加失败 (内存已有, 启动会重载): {e}")

    return GenerateResponse(
        generated=len(codes),
        codes=codes,
        channel=req.channel,
        batch=batch,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/redeem", response_model=RedeemResponse)
async def redeem_invite_code(req: RedeemRequest, request: Request):
    """
    用户入口: 核销邀请码 (公测 landing 提交触发)
    - 1 码 1 用 (status 变为 used + 关联 email + 记录 redeemed_at)
    - 30 天试用到期时间 = now + 30 days
    - 限流 10/min/email (防刷)
    - 邮箱重复使用同一码 → 幂等返回已核销
    """
    # 1. 限流 (按 email)
    if not _check_rate_limit(f"redeem:{req.email}", max_per_min=10):
        raise HTTPException(429, "rate_limit: 提交过于频繁, 请稍后再试")

    # 2. 加载基线 (如未启动 hook)
    if not _INVITE_CACHE:
        _load_csv_to_cache()

    # 3. 查找邀请码
    with _INVITE_LOCK:
        code_data = _INVITE_CACHE.get(req.code)
        if not code_data:
            raise HTTPException(404, "code_invalid: 邀请码不存在")

        # 4. 状态检查
        if code_data["status"] == "used":
            # 幂等: 同邮箱 + 同码 → 返回已核销 (避免重复点击)
            if code_data.get("redeemed_email") == req.email:
                expires_at = code_data.get("expires_at") or ""
                return RedeemResponse(
                    code=req.code,
                    channel=code_data.get("channel", ""),
                    batch=code_data.get("batch", ""),
                    redeemed=True,
                    redeemed_at=code_data.get("redeemed_at", ""),
                    expires_at=expires_at,
                    next="/templates/views/login.html?registered=1&code=" + req.code,
                )
            raise HTTPException(409, "code_used: 邀请码已被使用, 1 码 1 用")
        elif code_data["status"] == "expired":
            raise HTTPException(410, "code_expired: 邀请码已过期 (公测期 7/15 - 8/9)")

        # 5. 核销
        now = datetime.now(timezone.utc)
        expires = now.timestamp() + 30 * 86400  # 30 天
        expires_iso = datetime.fromtimestamp(expires, timezone.utc).isoformat()
        code_data.update({
            "status": "used",
            "redeemed_at": now.isoformat(),
            "redeemed_email": req.email,
            "expires_at": expires_iso,
            "source": req.source,
        })
        _INVITE_CACHE[req.code] = code_data
        # 异步写回 CSV (不阻塞响应)
        _persist_to_csv(req.code, code_data)

    logger.info(f"邀请码核销: {req.code} → {req.email} (channel={code_data.get('channel')})")

    return RedeemResponse(
        code=req.code,
        channel=code_data.get("channel", ""),
        batch=code_data.get("batch", ""),
        redeemed=True,
        redeemed_at=code_data["redeemed_at"],
        expires_at=code_data["expires_at"],
        next="/templates/views/login.html?registered=1&code=" + req.code,
    )


@router.get("/status/{code}", response_model=StatusResponse)
async def get_invite_status(code: str, request: Request, admin_token: Optional[str] = None):
    """
    查询邀请码状态
    - 默认: 仅返回 status (unused/used/expired), 不暴露 email (隐私)
    - 带 admin_token: 完整信息 (供 BD dashboard 跟踪)
    """
    code = code.strip().upper()
    if not INVITE_PATTERN.match(code):
        raise HTTPException(400, "邀请码格式错误")

    if not _INVITE_CACHE:
        _load_csv_to_cache()

    code_data = _INVITE_CACHE.get(code)
    if not code_data:
        raise HTTPException(404, "code_invalid: 邀请码不存在")

    is_admin = admin_token and _is_admin(admin_token)
    return StatusResponse(
        code=code,
        channel=code_data.get("channel") if is_admin else None,
        batch=code_data.get("batch") if is_admin else None,
        status=code_data.get("status", "unused"),
        redeemed_at=code_data.get("redeemed_at") if is_admin else None,
        redeemed_email=code_data.get("redeemed_email") if is_admin else None,
        note=code_data.get("note") if is_admin else None,
    )


# ========== 批量工具 (admin 内部) ==========

@router.get("/stats")
async def invite_stats(admin_token: str):
    """admin 入口: 邀请码全局统计 (供 dashboard-w6.md §3 用)"""
    if not _is_admin(admin_token):
        raise HTTPException(401, "admin_token 无效")

    if not _INVITE_CACHE:
        _load_csv_to_cache()

    stats = {
        "total": len(_INVITE_CACHE),
        "by_status": {"unused": 0, "used": 0, "expired": 0},
        "by_channel": {"review": 0, "wechat-group": 0, "founding-member": 0},
        "by_batch": {},
    }
    for code, data in _INVITE_CACHE.items():
        s = data.get("status", "unused")
        c = data.get("channel", "")
        b = data.get("batch", "unknown")
        stats["by_status"][s] = stats["by_status"].get(s, 0) + 1
        stats["by_channel"][c] = stats["by_channel"].get(c, 0) + 1
        stats["by_batch"][b] = stats["by_batch"].get(b, 0) + 1

    return stats
