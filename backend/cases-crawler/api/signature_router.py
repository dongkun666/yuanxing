"""
LexPrime W12 A2 客户签字确认 API Router (lex-coder · 2026-06-30)

承接 core/doc_workflow.py 的 Signature ORM 模型
+ doc_workflow_router 的状态机 (签字后 lawyer_reviewed → client_signed)

端点 (2 个):
- POST /api/signature/{doc_id}  上传客户签字 (图片 + 律师执业证号 + 客户信息)
- GET  /api/signature/{doc_id}  查询签字状态

数据流:
1. 客户 / 律师提交 base64 图片 + 律师执业证号
2. 写入 Signature 表 (doc_id 唯一, 重复上传 → 更新)
3. 返回签字状态 + 时间戳

依赖:
- core.doc_workflow (Signature ORM)
- core.db (Database session)
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from loguru import logger
from sqlalchemy import select

from core.db import Database
from core.doc_workflow import Signature, DOC_WORKFLOW_DISCLAIMER


router = APIRouter(prefix="/api/signature", tags=["skill:signature"])


# ===== 限制 =====
# Base64 编码后 ≈ 原文件 × 1.37, 限 500KB 原文件 → ~685KB base64
MAX_SIGNATURE_IMAGE_B64_SIZE = 700 * 1024  # 700KB
ALLOWED_IMAGE_PREFIXES = ("data:image/png;base64,", "data:image/jpeg;base64,", "data:image/jpg;base64,")


# ===== Pydantic Models =====

class SignatureUploadRequest(BaseModel):
    """签字上传请求"""
    signature_image: str = Field(
        ...,
        min_length=100,
        max_length=MAX_SIGNATURE_IMAGE_B64_SIZE,
        description="Base64 编码的图片 (含 data:image/png;base64, 前缀)"
    )
    license_no: str = Field(..., min_length=5, max_length=64,
                             description="律师执业证号 (审计追溯)")
    client_name: Optional[str] = Field(None, max_length=128,
                                          description="客户姓名 (可选)")
    client_id_no: Optional[str] = Field(None, max_length=64,
                                           description="客户身份证号 / 护照号 (可选)")
    notes: Optional[str] = Field(None, max_length=500, description="备注")

    @field_validator("license_no")
    @classmethod
    def validate_license_no(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("律师执业证号不能为空")
        return v

    @field_validator("signature_image")
    @classmethod
    def validate_signature_image(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("signature_image 不能为空")
        if v.startswith("data:image"):
            if not any(v.startswith(p) for p in ALLOWED_IMAGE_PREFIXES):
                raise ValueError(
                    "signature_image 仅支持 data:image/png;base64 或 data:image/jpeg;base64 前缀"
                )
            # 校验 base64 部分
            b64_part = v.split(",", 1)[1] if "," in v else ""
            try:
                base64.b64decode(b64_part, validate=True)
            except Exception as e:
                raise ValueError(f"signature_image base64 解码失败: {e}")
        else:
            # 纯 base64 (不带前缀), 同样校验
            try:
                base64.b64decode(v, validate=True)
            except Exception as e:
                raise ValueError(f"signature_image base64 解码失败: {e}")
        return v


class SignatureUploadResponse(BaseModel):
    """签字上传响应"""
    doc_id: str
    license_no: str
    client_name: Optional[str]
    signed_at: str
    image_size_bytes: int
    notes: Optional[str]
    disclaimer: str = DOC_WORKFLOW_DISCLAIMER


class SignatureStatusResponse(BaseModel):
    """签字状态查询响应"""
    doc_id: str
    has_signature: bool
    license_no: Optional[str]
    client_name: Optional[str]
    signed_at: Optional[str]
    image_size_bytes: Optional[int]
    notes: Optional[str]
    disclaimer: str = DOC_WORKFLOW_DISCLAIMER


# ===== 端点 =====

@router.post("/{doc_id}", response_model=SignatureUploadResponse)
async def upload_signature(doc_id: str, req: SignatureUploadRequest):
    """上传客户签字
    
    注意: 一份文书只允许一份签字 (doc_id 唯一). 重复 POST 会覆盖 (返 200 而非 409).
    设计: 客户可能多次提交 (画错重画), 律师最终确认; 后端覆盖, 客户端不必担心 409.
    """
    # 校验 doc_id
    doc_id = doc_id.strip()
    if not doc_id:
        raise HTTPException(400, "doc_id 不能为空")

    # 计算图片大小 (base64 解码后字节数)
    if req.signature_image.startswith("data:image"):
        b64_part = req.signature_image.split(",", 1)[1]
    else:
        b64_part = req.signature_image
    image_bytes = base64.b64decode(b64_part)
    image_size = len(image_bytes)

    if image_size > 500 * 1024:
        raise HTTPException(413, f"签字图片过大: {image_size} bytes (限 500KB)")

    async with Database.session() as session:
        # 查询现有记录 (可能覆盖)
        stmt = select(Signature).where(Signature.doc_id == doc_id)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            # 覆盖
            existing.signature_image = req.signature_image
            existing.license_no = req.license_no
            existing.signed_at = datetime.now(timezone.utc)
            existing.client_name = req.client_name
            existing.client_id_no = req.client_id_no
            existing.notes = req.notes
            record = existing
            logger.info(f"[signature] 更新签字 doc_id={doc_id} license_no={req.license_no}")
        else:
            # 新建
            record = Signature(
                doc_id=doc_id,
                signature_image=req.signature_image,
                license_no=req.license_no,
                signed_at=datetime.now(timezone.utc),
                client_name=req.client_name,
                client_id_no=req.client_id_no,
                notes=req.notes,
            )
            session.add(record)
            logger.info(f"[signature] 新建签字 doc_id={doc_id} license_no={req.license_no}")

        await session.flush()
        await session.refresh(record)

        return SignatureUploadResponse(
            doc_id=record.doc_id,
            license_no=record.license_no,
            client_name=record.client_name,
            signed_at=record.signed_at.isoformat(),
            image_size_bytes=image_size,
            notes=record.notes,
        )


@router.get("/{doc_id}", response_model=SignatureStatusResponse)
async def get_signature(doc_id: str):
    """查询客户签字状态"""
    doc_id = doc_id.strip()
    if not doc_id:
        raise HTTPException(400, "doc_id 不能为空")

    async with Database.session() as session:
        stmt = select(Signature).where(Signature.doc_id == doc_id)
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()

        if record is None:
            return SignatureStatusResponse(
                doc_id=doc_id,
                has_signature=False,
                license_no=None,
                client_name=None,
                signed_at=None,
                image_size_bytes=None,
                notes=None,
            )

        # 计算图片大小
        b64_part = (
            record.signature_image.split(",", 1)[1]
            if record.signature_image.startswith("data:image")
            else record.signature_image
        )
        image_size = len(base64.b64decode(b64_part))

        return SignatureStatusResponse(
            doc_id=record.doc_id,
            has_signature=True,
            license_no=record.license_no,
            client_name=record.client_name,
            signed_at=record.signed_at.isoformat(),
            image_size_bytes=image_size,
            notes=record.notes,
        )


# ===== 健康检查 =====

@router.get("/health/info")
async def signature_health():
    """签字服务健康检查"""
    return {
        "status": "ok",
        "service_id": "lexprime.skill.signature",
        "version": "0.1.0-w12",
        "max_image_size_bytes": 500 * 1024,
        "allowed_prefixes": list(ALLOWED_IMAGE_PREFIXES),
        "endpoints": [
            "POST /api/signature/{doc_id}",
            "GET /api/signature/{doc_id}",
            "GET /api/signature/health/info",
        ],
    }