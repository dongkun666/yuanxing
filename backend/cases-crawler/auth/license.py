"""
LexPrime Auth 律师执业证认证模块 (W3)
2026-06-29

律师执业证上传 + AI 初审 + 人工复审:
- W3 dev: OCR + AI 都用 mock (deterministic, 0 外部依赖)
- W4+ 接真 PaddleOCR / 阿里云 OCR (接口已留)

状态机:
    pending → ai_reviewing → human_reviewing → approved
                          ↘ rejected (AI 直接拒绝, 低置信度)

W3 endpoint:
- POST /api/auth/lawyer-license/upload   上传执业证 + 触发 AI 初审
- GET  /api/auth/lawyer-license/status   当前审核状态
- POST /api/auth/lawyer-license/review   admin 人工复审 (需 admin 权限)

字段提取 (mock):
- name: 从文件名/email 启发
- license_no: 从文件名匹配 11-17 位数字+字母
- firm: 占位 "待审核律所"
- practice_areas: 占位 ["民商事", "合同纠纷"]
"""
from __future__ import annotations

import base64
import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import LawyerProfile, LicenseReviewLog, User
from auth.ratelimit import license_upload_key_by_user, rate_limit_check
from auth.security import AuthError
from core.config import settings


# ========== 业务异常 ==========
class LicenseError(AuthError):
    code = "license_error"


class LicenseNotFoundError(LicenseError):
    code = "license_not_found"


class LicenseAlreadyApprovedError(LicenseError):
    code = "license_already_approved"


class LicenseInvalidImageError(LicenseError):
    code = "license_invalid_image"


class LicenseOcrFailedError(LicenseError):
    code = "license_ocr_failed"


class LicenseAiReviewFailedError(LicenseError):
    code = "license_ai_review_failed"


# ========== 数据结构 ==========
@dataclass(frozen=True)
class OcrResult:
    """OCR 提取的执业证字段"""

    raw_text: str
    name: Optional[str]
    license_no: Optional[str]
    firm: Optional[str]
    practice_areas: list[str]
    issue_date: Optional[str]
    confidence: float  # OCR 置信度 (0-1)


@dataclass(frozen=True)
class AiReviewResult:
    """AI 初审结果"""

    score: float  # 0-1 综合分
    passed: bool
    reason: str
    checks: dict[str, bool]  # 各项校验明细


# ========== OCR Mock (W3 dev) ==========
# 真 OCR 接入指南 (W4+):
# - 调 PaddleOCR / 阿里云 OCR API
# - 用同一份 OcrResult dataclass 返回
# - service 层的 _run_ocr() 替换实现即可
def _run_ocr_mock(image_data: bytes, filename: str) -> OcrResult:
    """
    OCR mock - W3 dev 用

    规则:
    - 文件名提取 license_no (匹配 [A-Z0-9-]{8,17})
    - name 用 "律师-<hash前6位>"
    - firm 固定占位
    - confidence 跟文件大小相关 (大文件置信度高)
    """
    # license_no 提取 (常见格式: 110101-2018-A0001, 6位地区码 + 年份 + 序号)
    license_match = re.search(
        r"((?:[A-Z0-9]{2,6}[-/]?\d{4}[-/]?[A-Z]?\d{3,8}))",
        filename.upper(),
    )
    license_no = license_match.group(1) if license_match else None

    # name 占位
    digest = hashlib.md5(filename.encode("utf-8")).hexdigest()[:6].upper()
    name = f"律师-{digest}"

    # confidence: 文件大小 (bytes) / 1MB, 上限 0.95
    size_kb = len(image_data) / 1024
    confidence = min(0.95, 0.5 + size_kb / 2000)
    confidence = round(confidence, 2)

    raw_text = (
        f"律师执业证\n"
        f"姓名: {name}\n"
        f"执业证号: {license_no or '未识别'}\n"
        f"执业机构: 待审核律所\n"
        f"执业证类别: 专职律师\n"
        f"发证机关: 司法部\n"
    )

    return OcrResult(
        raw_text=raw_text,
        name=name,
        license_no=license_no,
        firm="待审核律所",
        practice_areas=["民商事", "合同纠纷"],
        issue_date=None,
        confidence=confidence,
    )


def _run_ocr(image_data: bytes, filename: str) -> OcrResult:
    """
    OCR 调度 (W3 dev: mock)
    - settings.auth_license_ocr_engine = "mock" -> _run_ocr_mock
    - W4+ "paddle" / "aliyun" -> 接真 API
    """
    engine = settings.auth_license_ocr_engine
    if engine == "mock":
        return _run_ocr_mock(image_data, filename)
    # W4+ 真接入
    logger.warning(f"[auth.license.ocr] engine={engine} not implemented, fallback to mock")
    return _run_ocr_mock(image_data, filename)


# ========== AI 初审 Mock (W3 dev) ==========
def _ai_review_license(ocr: OcrResult, user: User) -> AiReviewResult:
    """
    AI 初审 mock - W3 dev 用

    通过条件 (满足 4/4):
    1. OCR confidence >= 0.6
    2. license_no 格式合法
    3. name 不为空
    4. firm 不为空

    score: 4 项 check 中通过的占比
    真实 AI 接入 (W4+):
    - Qwen2.5-72B 多模态 (输入 OCR + 图片 hash, 输出 score + 风险点)
    - 或专门律师执业证分类模型
    """
    checks = {
        "ocr_confidence_ok": ocr.confidence >= 0.6,
        "license_no_format_ok": bool(
            ocr.license_no and re.match(r"^[A-Z0-9-/]{8,17}$", ocr.license_no)
        ),
        "name_present": bool(ocr.name),
        "firm_present": bool(ocr.firm),
    }
    passed_count = sum(1 for v in checks.values() if v)
    score = passed_count / len(checks)

    # 故意: 如果 email 是 "reject@test.lexprime" 则强制低分 (测试路径)
    if user.email.startswith("reject@"):
        score = 0.3

    return AiReviewResult(
        score=score,
        passed=score >= settings.auth_license_ai_min_score,
        reason=f"AI 初审通过 {passed_count}/{len(checks)} 项, 评分 {score:.2f}",
        checks=checks,
    )


# ========== 文件存储 ==========
_LICENSE_DIR = Path("./data/licenses")


def _save_license_image(user_id: int, image_data: bytes, ext: str) -> str:
    """
    保存执业证图片到本地 (不上云)

    Returns:
        相对路径 (用于 license_image_url)
    """
    _LICENSE_DIR.mkdir(parents=True, exist_ok=True)
    user_dir = _LICENSE_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    file_path = user_dir / f"license_{timestamp}.{ext}"
    file_path.write_bytes(image_data)
    return str(file_path)


# ========== 业务逻辑 ==========
async def upload_license(
    user: User,
    image_base64: str,
    filename: str,
    db: AsyncSession,
) -> tuple[LawyerProfile, float, str]:
    """返回 (profile, ai_score, ai_reason)"""
    """
    上传律师执业证 + 触发 AI 初审

    Args:
        user: 当前 user
        image_base64: 图片/PDF base64 (data URL 也支持, 自动剥前缀)
        filename: 原始文件名 (用于 OCR 启发)
        db: AsyncSession

    Returns:
        更新后的 LawyerProfile

    Raises:
        LicenseInvalidImageError: base64 解码失败
        LicenseOcrFailedError: OCR 失败
        LicenseAlreadyApprovedError: 已通过审核 (不允许重新上传)
        LicenseError: 限流等
    """
    # 限流
    decision = rate_limit_check(
        key=license_upload_key_by_user(user.id),
        limit=settings.auth_max_failed_logins,
        window_seconds=3600,
    )
    if not decision.allowed:
        raise LicenseError(
            f"too many upload attempts, retry in {decision.retry_after}s"
        )

    # 拿 profile
    result = await db.execute(
        select(LawyerProfile).where(LawyerProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise LicenseNotFoundError(f"lawyer profile not found for user id={user.id}")

    if profile.license_status == "approved":
        raise LicenseAlreadyApprovedError("license already approved, no need to re-upload")

    # 解析 base64 (支持 data URL 前缀)
    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]
    try:
        image_data = base64.b64decode(image_base64)
    except Exception as e:
        raise LicenseInvalidImageError(f"failed to decode base64: {e}") from e

    if len(image_data) < 100:
        raise LicenseInvalidImageError("image too small (likely empty)")

    if len(image_data) > 10 * 1024 * 1024:
        raise LicenseInvalidImageError("image too large (>10MB)")

    # 文件扩展名
    ext = "jpg"
    if "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext not in ("jpg", "jpeg", "png", "pdf", "webp"):
            ext = "jpg"

    # 状态: pending → ai_reviewing
    from_status = profile.license_status
    profile.license_status = "ai_reviewing"
    profile.license_image_url = _save_license_image(user.id, image_data, ext)
    profile.license_submitted_at = datetime.now(tz=timezone.utc)

    # 写日志 (user 上传)
    log = LicenseReviewLog(
        profile_id=profile.id,
        user_id=user.id,
        from_status=from_status,
        to_status="ai_reviewing",
        actor_type="user",
        actor_id=user.id,
        reason=f"uploaded {filename}",
    )
    db.add(log)
    await db.flush()

    # OCR
    try:
        ocr = _run_ocr(image_data, filename)
    except Exception as e:
        profile.license_status = "pending"
        await db.commit()
        raise LicenseOcrFailedError(f"OCR failed: {e}") from e

    profile.license_ocr_data = {
        "raw_text": ocr.raw_text,
        "name": ocr.name,
        "license_no": ocr.license_no,
        "firm": ocr.firm,
        "practice_areas": ocr.practice_areas,
        "issue_date": ocr.issue_date,
        "confidence": ocr.confidence,
    }

    # AI 初审
    ai = _ai_review_license(ocr, user)

    if ai.passed:
        # AI 通过 -> 进入人工复审
        profile.license_status = "human_reviewing"
        log = LicenseReviewLog(
            profile_id=profile.id,
            user_id=user.id,
            from_status="ai_reviewing",
            to_status="human_reviewing",
            actor_type="ai",
            actor_id=None,
            ai_score=ai.score,
            reason=ai.reason,
            extra={"checks": ai.checks},
        )
        db.add(log)
    else:
        # AI 不通过 -> 直接拒绝 (用户可重新上传)
        profile.license_status = "rejected"
        profile.license_reject_reason = ai.reason
        log = LicenseReviewLog(
            profile_id=profile.id,
            user_id=user.id,
            from_status="ai_reviewing",
            to_status="rejected",
            actor_type="ai",
            actor_id=None,
            ai_score=ai.score,
            reason=ai.reason,
            extra={"checks": ai.checks},
        )
        db.add(log)

    await db.commit()
    await db.refresh(profile)

    logger.info(
        f"[auth.license.upload] user id={user.id} "
        f"ocr_confidence={ocr.confidence} ai_score={ai.score:.2f} "
        f"-> status={profile.license_status}"
    )

    return profile, ai.score, ai.reason


async def get_license_status(
    user: User,
    db: AsyncSession,
) -> tuple[LawyerProfile, list[LicenseReviewLog]]:
    """
    查询律师执业证审核状态 + 历史

    Returns:
        (profile, list of review logs)
    """
    result = await db.execute(
        select(LawyerProfile).where(LawyerProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise LicenseNotFoundError(f"lawyer profile not found for user id={user.id}")

    logs_result = await db.execute(
        select(LicenseReviewLog)
        .where(LicenseReviewLog.profile_id == profile.id)
        .order_by(LicenseReviewLog.created_at.asc())
    )
    logs = logs_result.scalars().all()
    return profile, logs


async def admin_review_license(
    profile_id: int,
    decision: str,
    reason: str,
    admin: User,
    db: AsyncSession,
) -> LawyerProfile:
    """
    admin 人工复审

    Args:
        profile_id: 律师 profile id
        decision: "approved" / "rejected"
        reason: 审核理由
        admin: 当前 admin user (actor)
        db: AsyncSession

    Returns:
        更新后的 profile

    Raises:
        LicenseNotFoundError
        LicenseError: 状态不允许复审 (e.g. 已 approved)
    """
    if decision not in ("approved", "rejected"):
        raise LicenseError(f"invalid decision: {decision}")

    if admin.role not in ("admin", "firm_admin"):
        raise LicenseError(f"user role '{admin.role}' cannot review licenses")

    result = await db.execute(
        select(LawyerProfile).where(LawyerProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise LicenseNotFoundError(f"profile id={profile_id} not found")

    if profile.license_status not in ("human_reviewing", "ai_reviewing"):
        raise LicenseError(
            f"profile status '{profile.license_status}' not reviewable "
            f"(must be human_reviewing or ai_reviewing)"
        )

    from_status = profile.license_status
    profile.license_status = decision
    profile.license_reviewed_at = datetime.now(tz=timezone.utc)
    profile.license_reviewed_by = admin.id
    if decision == "rejected":
        profile.license_reject_reason = reason

    log = LicenseReviewLog(
        profile_id=profile.id,
        user_id=profile.user_id,
        from_status=from_status,
        to_status=decision,
        actor_type="admin",
        actor_id=admin.id,
        reason=reason,
    )
    db.add(log)
    await db.commit()
    await db.refresh(profile)

    logger.info(
        f"[auth.license.review] admin id={admin.id} profile_id={profile.id} "
        f"{from_status} -> {decision} reason={reason[:80]}"
    )

    return profile


# ========== 自检 ==========
def _self_check() -> None:
    # OCR mock
    ocr = _run_ocr_mock(b"fake-image-data-" * 100, "lawyer_110101-2018-A0001.jpg")
    assert ocr.name
    assert ocr.license_no == "110101-2018-A0001"
    assert 0 < ocr.confidence <= 0.95

    # AI review
    user = User(email="test@example.com", password_hash="x")
    ai = _ai_review_license(ocr, user)
    assert 0 <= ai.score <= 1
    assert isinstance(ai.passed, bool)

    # Reject 路径
    bad_user = User(email="reject@test.lexprime", password_hash="x")
    bad_ai = _ai_review_license(ocr, bad_user)
    assert bad_ai.score < settings.auth_license_ai_min_score

    logger.debug("auth.license self-check OK")


_self_check()