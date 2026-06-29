"""
LexPrime W9 Skill 3 文书生成 API Router (lex-coder · 2026-06-29)

W9 C1 任务: 4 文书类型 + 4 模板 + 4 端点
评审 #1 #2 期间 (W7 prd-feedback) 律师最常问 Top 3 新需求 = 自动生成法律文书.
A1 prd-feedback 归并后, W9 C1 落地 Skill 3.

端点 (4 个):
- POST /api/doc-gen/complaint    起诉状生成
- POST /api/doc-gen/defense     答辩状生成
- POST /api/doc-gen/contract    合同生成
- POST /api/doc-gen/letter      律师函生成
- GET  /api/doc-gen/health      健康检查 (含 4 模板状态)

数据流:
1. 接律师提交 {lawyer_id, case_id, template, facts, evidence, claims, parties, court, ...}
2. 加载对应 Markdown 模板 (templates/docs/{complaint|defense|contract|letter}_v1.md)
3. 替换占位符 {{key}} → 律师字段值 (缺失字段用占位符原样兜底)
4. 渲染 Markdown 内容
5. 用 python-docx 1.2.0 生成 Word .docx (Base64 编码返回, 前端可下载)
6. 返回 JSON {markdown, docx_base64, docx_filename, template_id, filled_fields, missing_fields}

PRD:
- § 5.4 Skill Hub
- § 5.6 当事人服务类文书 (Skill 3 文书生成)

模板复用 W7 review_router 的 pattern: 内存级 _GEN_CACHE, 仅作幂等性查询 (本任务生成结果不强制缓存,
W10+ 计划接 Redis + 异步 Worker).

依赖:
- python-docx 1.2.0 (已装在 requirements 隐含环境)
- 无外部 LLM 调用, dev 简化 = 模板替换 (W9 不调 LLM, W10+ 可接入微调模型)
"""
from __future__ import annotations

import base64
import io
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field, field_validator

try:
    # python-docx 1.2.0 已装 (pip list 验证)
    from docx import Document as DocxDocument
    from docx.shared import Pt, Cm
    DOCX_AVAILABLE = True
except ImportError:  # pragma: no cover
    DOCX_AVAILABLE = False
    logger.warning("[doc-gen] python-docx 未安装, Word 导出降级为占位说明")


router = APIRouter(prefix="/api/doc-gen", tags=["skill:doc-gen"])


# ====== 4 文书类型常量 ======
DOC_TYPES = ["complaint", "defense", "contract", "letter"]

DOC_TYPE_LABELS = {
    "complaint": "民事起诉状",
    "defense": "民事答辩状",
    "contract": "合同",
    "letter": "律师函",
}

DOC_TYPE_ICONS = {
    "complaint": "mdi:gavel",
    "defense": "mdi:shield-check-outline",
    "contract": "mdi:file-document-edit-outline",
    "letter": "mdi:email-fast-outline",
}

TEMPLATE_FILES = {
    "complaint": "complaint_v1.md",
    "defense": "defense_v1.md",
    "contract": "contract_v1.md",
    "letter": "letter_v1.md",
}

TEMPLATE_VERSIONS = {
    "complaint": "v1.0-w9",
    "defense": "v1.0-w9",
    "contract": "v1.0-w9",
    "letter": "v1.0-w9",
}


# ====== 帮助函数: 模板路径 ======
def _templates_dir() -> Path:
    """backend/cases-crawler/api/doc_gen_router.py -> backend/cases-crawler/templates/docs"""
    here = Path(__file__).resolve().parent
    return here.parent / "templates" / "docs"


def _load_template(doc_type: str) -> str:
    """加载对应 Markdown 模板, 不存在 → FileNotFoundError"""
    if doc_type not in TEMPLATE_FILES:
        raise ValueError(f"未知文书类型: {doc_type}")
    fname = TEMPLATE_FILES[doc_type]
    fpath = _templates_dir() / fname
    if not fpath.exists():
        raise FileNotFoundError(f"模板不存在: {fpath}")
    return fpath.read_text(encoding="utf-8")


def _extract_placeholders(template_md: str) -> List[str]:
    """从模板提取所有 {{key}} 占位符 (去重 + 排序)"""
    keys = re.findall(r"\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}", template_md)
    # 去重但保持出现顺序
    seen: set = set()
    unique: List[str] = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            unique.append(k)
    return unique


def _render_template(template_md: str, fields: Dict[str, Any]) -> tuple[str, List[str], List[str]]:
    """渲染模板: 替换 {{key}} → fields[key], 返回 (渲染后 md, 已填充字段, 缺失字段)

    规则:
    1. fields 中有的 key → 替换为 str(fields[key])
    2. fields 中没有的 key → 保留原 {{key}} 兜底 (前端可识别未填字段)
    3. 已填充字段 = 替换成功的 key 列表
    4. 缺失字段 = 模板中存在但 fields 没传 / 值为空的 key 列表
    """
    all_keys = _extract_placeholders(template_md)
    filled: List[str] = []
    missing: List[str] = []
    rendered = template_md

    for k in all_keys:
        val = fields.get(k)
        if val is None or (isinstance(val, str) and not val.strip()):
            # 缺失或空 → 保留原占位符
            missing.append(k)
        else:
            rendered = rendered.replace("{{" + k + "}}", str(val))
            filled.append(k)

    return rendered, filled, missing


# ====== 帮助函数: Markdown → docx ======
def _md_to_docx_bytes(md_text: str, doc_type: str, title: str = "") -> bytes:
    """将 Markdown 文本转换为 .docx 字节流

    实现策略 (W9 dev 简化, 不引入 markdown parser):
    - 第 1 行作为标题 (Heading 1, 居中)
    - '## xxx' → Heading 2
    - '### xxx' → Heading 3
    - '**xxx**' → Bold runs
    - '-' / '*' 开头 → list paragraph
    - '---' → 空行 + 分割
    - 普通段落 → Normal style

    Args:
        md_text:  渲染后的 Markdown 文本
        doc_type: 文书类型 (用于 docx 内嵌元信息)
        title:    文档标题 (默认 = doc_type label)

    Returns:
        docx 字节流 (bytes)
    """
    if not DOCX_AVAILABLE:
        # 降级: 返回纯文本占位
        return f"# {doc_type} (docx unavailable - install python-docx)".encode("utf-8")

    doc = DocxDocument()
    # 设置默认字体 (中文: 宋体, 英文: Times New Roman)
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(11)

    # 文档标题 (居中 Heading 1)
    if title:
        h = doc.add_heading(level=1)
        run = h.add_run(title)
        run.font.size = Pt(16)
        h.alignment = 1  # center

    lines = md_text.splitlines()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            doc.add_paragraph("")
            continue

        # 跳过原始 H1 (已在 title 处理)
        if stripped.startswith("# ") and not title:
            t = stripped[2:].strip()
            h = doc.add_heading(level=1)
            h.add_run(t)
            continue

        # H2
        if stripped.startswith("## "):
            t = stripped[3:].strip()
            doc.add_heading(t, level=2)
            continue

        # H3
        if stripped.startswith("### "):
            t = stripped[4:].strip()
            doc.add_heading(t, level=3)
            continue

        # H4+
        if stripped.startswith("#### "):
            t = stripped[5:].strip()
            doc.add_heading(t, level=4)
            continue

        # 分割线
        if stripped == "---":
            doc.add_paragraph("─" * 40)
            continue

        # 引用块 (> ...)
        if stripped.startswith("> "):
            t = stripped[2:].strip()
            p = doc.add_paragraph()
            run = p.add_run(t)
            run.italic = True
            run.font.size = Pt(10)
            p.paragraph_format.left_indent = Cm(0.5)
            continue

        # 列表项 (- / *)
        if stripped.startswith("- ") or stripped.startswith("* "):
            t = stripped[2:].strip()
            doc.add_paragraph(t, style="List Bullet")
            continue

        # 有序列表 (1. xxx)
        m = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if m:
            doc.add_paragraph(m.group(2), style="List Number")
            continue

        # 普通段落 (含 **bold** 简单处理)
        p = doc.add_paragraph()
        # 切分 **xxx** bold
        parts = re.split(r"(\*\*[^*]+\*\*)", line)
        for part in parts:
            if not part:
                continue
            if part.startswith("**") and part.endswith("**"):
                run = p.add_run(part[2:-2])
                run.bold = True
            else:
                p.add_run(part)

    # 注入元信息 (注释)
    meta_p = doc.add_paragraph()
    meta_run = meta_p.add_run(
        f"\n[LexPrime 元枢法智 · Skill 3 文书生成 · {TEMPLATE_VERSIONS[doc_type]} · "
        f"类型={DOC_TYPE_LABELS[doc_type]} · 生成时间={datetime.now(timezone.utc).isoformat()}]"
    )
    meta_run.font.size = Pt(8)
    meta_run.font.color.rgb = None  # 灰色
    meta_run.italic = True

    # 序列化
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()


# ====== Pydantic Models ======
class DocGenRequest(BaseModel):
    """文书生成通用请求 (4 端点复用)

    字段:
        lawyer_id   代理律师编号 / 律所 (必填, 用于审计)
        case_id     案号 (可选, 用于关联案件)
        template    模板 ID (默认 = 端点对应的类型, 也可显式覆盖)
        fields      文书字段字典 (key = 占位符, value = 字段值)
                    例: {"plaintiff_name": "张三", "facts": "原告于 2023-01-01 借款..."}
        output_format  输出格式 (默认 markdown + docx_base64, 也可只 markdown)
    """
    lawyer_id: str = Field(..., min_length=1, max_length=64, description="代理律师编号 / 律所")
    case_id: Optional[str] = Field(None, max_length=64, description="案号 (可选)")
    template: Optional[str] = Field(None, description="模板 ID (默认跟端点一致)")
    fields: Dict[str, Any] = Field(default_factory=dict, description="文书字段字典")
    output_format: str = Field("all", description="all / markdown / docx")

    @field_validator("lawyer_id")
    @classmethod
    def validate_lawyer_id(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("lawyer_id 不能为空")
        return v

    @field_validator("output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ("all", "markdown", "docx"):
            raise ValueError("output_format 必须是 all / markdown / docx 之一")
        return v


class DocGenResponse(BaseModel):
    """文书生成响应"""
    gen_id: str = Field(..., description="本次生成的 UUID")
    doc_type: str
    doc_type_label: str
    template_id: str
    template_version: str
    lawyer_id: str
    case_id: Optional[str]
    markdown: str = Field(..., description="渲染后的 Markdown 文本")
    docx_base64: Optional[str] = Field(None, description="Word docx 文件 Base64 编码")
    docx_filename: Optional[str] = Field(None, description="docx 下载文件名")
    docx_size_bytes: Optional[int] = Field(None, description="docx 文件大小")
    filled_fields: List[str] = Field(..., description="已成功填充的字段")
    missing_fields: List[str] = Field(..., description="模板中存在但未填充的字段")
    field_count: int = Field(..., description="模板总字段数")
    latency_ms: int
    generated_at: str
    disclaimer: str = Field(..., description="AI 辅助声明")
    next: str = Field(..., description="建议下一步 (GET /api/doc-gen/health)")


# 强制 AI 辅助声明 (复用 Skill 2 / Skill 1 风格)
DISCLAIMER_FULL = (
    "本文书由 LexPrime 元枢法智 (Skill 3 文书生成 v0.1.0-w9) 自动生成, "
    "内容基于律师提供的事实与证据整理。本文书仅供参考与辅助律师起草使用, "
    "不构成正式法律意见, 律师应根据案件实际情况进行审核、修改和完善。"
)


# ====== 帮助函数: 生成文书 ======
async def _generate_doc(doc_type: str, req: DocGenRequest) -> DocGenResponse:
    """生成文书的内部实现 (4 端点共用)

    Args:
        doc_type: 4 种之一 (complaint/defense/contract/letter)
        req: DocGenRequest

    Returns:
        DocGenResponse (含 markdown + docx_base64)
    """
    t0 = time.time()

    # 1. 加载模板
    try:
        template_md = _load_template(doc_type)
    except FileNotFoundError as e:
        logger.error(f"[doc-gen.{doc_type}] 模板缺失: {e}")
        raise HTTPException(500, f"模板缺失: {e}")
    except ValueError as e:
        raise HTTPException(400, str(e))

    # 2. 渲染占位符
    all_keys = _extract_placeholders(template_md)
    rendered_md, filled, missing = _render_template(template_md, req.fields)

    # 3. 自动注入一些隐含字段 (律师未传也兜底)
    rendered_md = rendered_md.replace("{{date}}", req.fields.get("date") or
                                      datetime.now().strftime("%Y 年 %m 月 %d 日"))
    if "lawyer_id" in all_keys and not req.fields.get("lawyer_id"):
        # 即使 Pydantic 校验过, 也兜底确保 rendered 中 lawyer_id 不留占位符
        rendered_md = rendered_md.replace("{{lawyer_id}}", req.lawyer_id)
        if "lawyer_id" not in filled:
            filled.append("lawyer_id")
        if "lawyer_id" in missing:
            missing.remove("lawyer_id")

    gen_id = f"dg-{uuid.uuid4().hex[:12]}"
    docx_base64: Optional[str] = None
    docx_filename: Optional[str] = None
    docx_size: Optional[int] = None

    # 4. 生成 docx (按需)
    if req.output_format in ("all", "docx"):
        try:
            docx_bytes = _md_to_docx_bytes(
                rendered_md,
                doc_type=doc_type,
                title=DOC_TYPE_LABELS[doc_type],
            )
            docx_base64 = base64.b64encode(docx_bytes).decode("ascii")
            docx_filename = f"{doc_type}-{gen_id}.docx"
            docx_size = len(docx_bytes)
        except Exception as e:
            logger.exception(f"[doc-gen.{doc_type}] docx 生成失败: {e}")
            raise HTTPException(500, f"docx 生成失败: {e}")

    # 5. markdown 单独请求时跳过 docx
    if req.output_format == "markdown":
        docx_base64 = None
        docx_filename = None
        docx_size = None

    latency_ms = int((time.time() - t0) * 1000)
    generated_at = datetime.now(timezone.utc).isoformat()

    logger.info(
        f"[doc-gen.{doc_type}] gen_id={gen_id} lawyer={req.lawyer_id} "
        f"filled={len(filled)}/{len(all_keys)} missing={len(missing)} "
        f"format={req.output_format} latency={latency_ms}ms"
    )

    return DocGenResponse(
        gen_id=gen_id,
        doc_type=doc_type,
        doc_type_label=DOC_TYPE_LABELS[doc_type],
        template_id=f"{doc_type}_v1",
        template_version=TEMPLATE_VERSIONS[doc_type],
        lawyer_id=req.lawyer_id,
        case_id=req.case_id,
        markdown=rendered_md,
        docx_base64=docx_base64,
        docx_filename=docx_filename,
        docx_size_bytes=docx_size,
        filled_fields=filled,
        missing_fields=missing,
        field_count=len(all_keys),
        latency_ms=latency_ms,
        generated_at=generated_at,
        disclaimer=DISCLAIMER_FULL,
        next="GET /api/doc-gen/health",
    )


# ====== 端点 1: POST /api/doc-gen/complaint ======
@router.post("/complaint", response_model=DocGenResponse)
async def gen_complaint(req: DocGenRequest):
    """民事起诉状生成 (模板: complaint_v1.md)

    必填建议字段:
        plaintiff_name, defendant_name, court, cause, facts, evidence, claims

    输出:
        markdown (str) + docx_base64 (Base64 编码的 .docx 文件)
    """
    return await _generate_doc("complaint", req)


# ====== 端点 2: POST /api/doc-gen/defense ======
@router.post("/defense", response_model=DocGenResponse)
async def gen_defense(req: DocGenRequest):
    """民事答辩状生成 (模板: defense_v1.md)

    必填建议字段:
        plaintiff_name, defendant_name, court, cause, facts, evidence, claims_response
    """
    return await _generate_doc("defense", req)


# ====== 端点 3: POST /api/doc-gen/contract ======
@router.post("/contract", response_model=DocGenResponse)
async def gen_contract(req: DocGenRequest):
    """合同生成 (模板: contract_v1.md)

    适用类型 (8 大类合同):
        房屋租赁 / 借款 / 劳动 / 服务 / 销售 / 承揽 / 委托 / 其他

    必填建议字段:
        contract_type, party_a, party_b, subject, amount, start_date, end_date
    """
    return await _generate_doc("contract", req)


# ====== 端点 4: POST /api/doc-gen/letter ======
@router.post("/letter", response_model=DocGenResponse)
async def gen_letter(req: DocGenRequest):
    """律师函生成 (模板: letter_v1.md)

    必填建议字段:
        recipient, sender, subject, facts, demands, deadline, consequence,
        lawyer_name, lawyer_phone
    """
    return await _generate_doc("letter", req)


# ====== 端点 5: GET /api/doc-gen/health ======
@router.get("/health")
async def doc_gen_health():
    """Skill 3 文书生成 健康检查 (4 模板状态)

    返回:
        - status            ok / degraded
        - templates_loaded  4 模板是否都能加载
        - docx_available    python-docx 是否可用
        - template_field_counts  每模板字段数 (用于前端 UI hint)
    """
    template_status: Dict[str, Dict[str, Any]] = {}
    for doc_type in DOC_TYPES:
        try:
            md = _load_template(doc_type)
            fields = _extract_placeholders(md)
            template_status[doc_type] = {
                "label": DOC_TYPE_LABELS[doc_type],
                "icon": DOC_TYPE_ICONS[doc_type],
                "version": TEMPLATE_VERSIONS[doc_type],
                "loaded": True,
                "field_count": len(fields),
                "fields": fields,
                "path": str(_templates_dir() / TEMPLATE_FILES[doc_type]),
            }
        except Exception as e:
            template_status[doc_type] = {
                "label": DOC_TYPE_LABELS[doc_type],
                "icon": DOC_TYPE_ICONS[doc_type],
                "version": TEMPLATE_VERSIONS[doc_type],
                "loaded": False,
                "error": str(e),
                "path": str(_templates_dir() / TEMPLATE_FILES[doc_type]),
            }

    all_loaded = all(s.get("loaded") for s in template_status.values())

    return {
        "status": "ok" if (all_loaded and DOCX_AVAILABLE) else "degraded",
        "service_id": "lexprime.skill.doc-gen",
        "version": "0.1.0-w9",
        "docx_available": DOCX_AVAILABLE,
        "templates": template_status,
        "template_count": len(DOC_TYPES),
        "templates_loaded": sum(1 for s in template_status.values() if s.get("loaded")),
        "doc_types": DOC_TYPES,
        "doc_type_labels": DOC_TYPE_LABELS,
        "endpoints": [
            "POST /api/doc-gen/complaint",
            "POST /api/doc-gen/defense",
            "POST /api/doc-gen/contract",
            "POST /api/doc-gen/letter",
            "GET /api/doc-gen/health",
        ],
    }