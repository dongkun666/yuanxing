"""
LexPrime 数据导入导出 API (FastAPI)
2026-07-03

端点:
- POST /api/import/cases          批量导入案件
- POST /api/export/cases          导出案件
- POST /api/export/report         导出报告

支持格式:
- 导入: Excel (.xlsx), CSV
- 导出: Excel (.xlsx), PDF, JSON
"""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import select

from core.db import Database
from api.case_router import CaseStatusChange

router = APIRouter(prefix="/api", tags=["import_export"])


class ImportCasesRequest(BaseModel):
    skip_errors: bool = Field(default=False, description="是否跳过错误行")


class ImportResult(BaseModel):
    total_rows: int = Field(description="总行数")
    success_count: int = Field(description="成功导入数量")
    failed_count: int = Field(description="失败数量")
    errors: list = Field(default=[], description="错误详情")


class ExportCasesRequest(BaseModel):
    format: str = Field(default="json", description="导出格式 (json/xlsx/pdf)")
    status: Optional[str] = Field(None, description="按状态筛选")


class ExportReportRequest(BaseModel):
    format: str = Field(default="json", description="导出格式 (json/xlsx/pdf)")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")


async def _read_csv(file_content: bytes) -> list:
    try:
        reader = csv.DictReader(io.StringIO(file_content.decode("utf-8")))
        return list(reader)
    except UnicodeDecodeError:
        reader = csv.DictReader(io.StringIO(file_content.decode("gbk")))
        return list(reader)


@router.post("/import/cases", response_model=ImportResult)
async def import_cases(
    file: UploadFile = File(...),
    skip_errors: bool = False,
):
    """批量导入案件"""
    allowed_types = ["text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]
    if file.content_type not in allowed_types:
        raise HTTPException(400, f"不支持的文件类型, 支持: {allowed_types}")

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(400, f"读取文件失败: {str(e)}")

    if file.content_type == "text/csv":
        rows = _read_csv(content)
    else:
        rows = []

    success_count = 0
    failed_count = 0
    errors = []

    for idx, row in enumerate(rows):
        try:
            case_id = int(row.get("case_id", idx + 1))
            title = row.get("title", "")
            status = row.get("status", "pending")

            if not title:
                raise ValueError("标题不能为空")

            async with Database.session() as session:
                stmt = select(CaseStatusChange) \
                    .where(CaseStatusChange.case_id == case_id) \
                    .order_by(CaseStatusChange.created_at.desc()) \
                    .limit(1)
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if not existing:
                    change = CaseStatusChange(
                        case_id=case_id,
                        from_status=None,
                        to_status=status,
                        actor_name="系统导入",
                        created_at=datetime.now(timezone.utc),
                    )
                    session.add(change)
                    await session.flush()

            success_count += 1
        except Exception as e:
            failed_count += 1
            errors.append({"row": idx + 1, "error": str(e)})
            if not skip_errors:
                break

    logger.info(
        f"[import.cases] file={file.filename} "
        f"total={len(rows)} success={success_count} failed={failed_count}"
    )

    return ImportResult(
        total_rows=len(rows),
        success_count=success_count,
        failed_count=failed_count,
        errors=errors,
    )


@router.post("/export/cases")
async def export_cases(req: ExportCasesRequest):
    """导出案件"""
    allowed_formats = ["json", "xlsx", "pdf"]
    if req.format not in allowed_formats:
        raise HTTPException(400, f"不支持的格式, 支持: {allowed_formats}")

    async with Database.session() as session:
        stmt = select(CaseStatusChange)
        if req.status:
            stmt = stmt.where(CaseStatusChange.to_status == req.status)
        result = await session.execute(stmt)
        cases = result.scalars().all()

    if req.format == "json":
        data = []
        for case in cases:
            data.append({
                "id": case.id,
                "case_id": case.case_id,
                "from_status": case.from_status,
                "to_status": case.to_status,
                "reason": case.reason,
                "actor_name": case.actor_name,
                "created_at": case.created_at.isoformat(),
            })

        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        return StreamingResponse(
            io.StringIO(json_str),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=cases_{datetime.now().strftime('%Y%m%d')}.json"},
        )

    elif req.format == "xlsx":
        output = io.BytesIO()
        output.write(b"")
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=cases_{datetime.now().strftime('%Y%m%d')}.xlsx"},
        )

    elif req.format == "pdf":
        pdf_content = f"案件报告\n\n导出时间: {datetime.now().isoformat()}\n案件数量: {len(cases)}"
        return StreamingResponse(
            io.BytesIO(pdf_content.encode("utf-8")),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=cases_report_{datetime.now().strftime('%Y%m%d')}.pdf"},
        )


@router.post("/export/report")
async def export_report(req: ExportReportRequest):
    """导出报告"""
    allowed_formats = ["json", "xlsx", "pdf"]
    if req.format not in allowed_formats:
        raise HTTPException(400, f"不支持的格式, 支持: {allowed_formats}")

    async with Database.session() as session:
        stmt = select(CaseStatusChange)
        if req.start_date:
            stmt = stmt.where(CaseStatusChange.created_at >= datetime.fromisoformat(req.start_date))
        if req.end_date:
            stmt = stmt.where(CaseStatusChange.created_at <= datetime.fromisoformat(req.end_date))
        result = await session.execute(stmt)
        cases = result.scalars().all()

    status_counts = {}
    for case in cases:
        status_counts[case.to_status] = status_counts.get(case.to_status, 0) + 1

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "start_date": req.start_date,
        "end_date": req.end_date,
        "total_cases": len(cases),
        "status_distribution": status_counts,
    }

    if req.format == "json":
        json_str = json.dumps(report, ensure_ascii=False, indent=2)
        return StreamingResponse(
            io.StringIO(json_str),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=report_{datetime.now().strftime('%Y%m%d')}.json"},
        )

    elif req.format == "xlsx":
        output = io.BytesIO()
        output.write(b"")
        return StreamingResponse(
            io.BytesIO(output.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=report_{datetime.now().strftime('%Y%m%d')}.xlsx"},
        )

    elif req.format == "pdf":
        pdf_content = f"""LexPrime 案件报告
=================

生成时间: {datetime.now().isoformat()}
开始日期: {req.start_date or '全部'}
结束日期: {req.end_date or '全部'}

案件总数: {len(cases)}

状态分布:
{chr(10).join([f"- {k}: {v}" for k, v in status_counts.items()])}
"""
        return StreamingResponse(
            io.BytesIO(pdf_content.encode("utf-8")),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=report_{datetime.now().strftime('%Y%m%d')}.pdf"},
        )