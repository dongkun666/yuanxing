"""
LexPrime W9 + W15 + W19 + W21 Skill 3 文书生成 API Router (lex-coder / lex-ai · 2026-06-30)

W9 C1 任务: 4 文书类型 + 4 模板 + 4 端点
评审 #1 #2 期间 (W7 prd-feedback) 律师最常问 Top 3 新需求 = 自动生成法律文书.
A1 prd-feedback 归并后, W9 C1 落地 Skill 3.

W15 skill3-iterate 扩展:
- letter_v2 模板 (基于 8 律师试用反馈 mock 驱动迭代)
- 新增端点: POST /api/doc-gen/letter-v2
- 集成 doc_workflow (5 状态机) + signature_router (W12 A2 commit 829d25c + 85278db)

W19 skill3-gradual 灰度:
- 8/15 v2.0 10% 灰度 (A/B test 50/50 split 律师)
- 9/1 v2.0 全量 50% 灰度
- POST /api/doc-gen/letter 自动按灰度配置路由 v1.0 / v2.0
- 新增端点: GET /api/doc-gen/rollout/status, GET /api/doc-gen/metrics
- 跟踪 3 指标: 5 维度评分 + 转化率 + 律师满意度

W21 skill3-full-rollout:
- 10/1 全量 100% (phase=rollout_100pct): 100% 律师走 v2.0
- 11/1 v1.0 退役 (letter_v1_deprecated=True): 强制 v2.0, 即使 force_v1 也无效
- 兼容性: 现有 v1.0 文书数据保留 (W12 A2 doc_workflow 不动), 11/1 后只支持 v2.0 生成

端点 (8 个):
- POST /api/doc-gen/complaint         起诉状生成
- POST /api/doc-gen/defense           答辩状生成
- POST /api/doc-gen/contract          合同生成
- POST /api/doc-gen/letter            律师函生成 (W19 灰度自动路由 v1.0 / v2.0)
- POST /api/doc-gen/letter-v2         律师函生成 (W15 反馈驱动, 显式 v2.0)
- GET  /api/doc-gen/health            健康检查 (含 5 模板状态 + 灰度状态)
- GET  /api/doc-gen/rollout/status    灰度阶段 + 百分比 + 强制列表
- GET  /api/doc-gen/metrics           3 指标汇总 (5 维度评分 + 转化率 + 律师满意度)

数据流:
1. 接律师提交 {lawyer_id, case_id, template, facts, evidence, claims, parties, court, ...}
2. 加载对应 Markdown 模板 (templates/docs/{complaint|defense|contract|letter}_v1.md + letter_v2.md)
3. 替换占位符 {{key}} → 律师字段值 (缺失字段用占位符原样兜底)
4. 渲染 Markdown 内容
5. 用 python-docx 1.2.0 生成 Word .docx (Base64 编码返回, 前端可下载)
6. 返回 JSON {markdown, docx_base64, docx_filename, template_id, filled_fields, missing_fields}

PRD:
- § 5.4 Skill Hub
- § 5.6 当事人服务类文书 (Skill 3 文书生成)
- § 11 法务自检

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

# W19 skill3-gradual 灰度配置 + 指标跟踪
from core.rollout import (
    LetterVersion,
    assign_version,
    get_metrics_collector,
    get_rollout_config,
)

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
    "letter_v2": "letter_v2.md",  # W15 skill3-iterate (8 律师反馈驱动)
}

TEMPLATE_VERSIONS = {
    "complaint": "v1.0-w9",
    "defense": "v1.0-w9",
    "contract": "v1.0-w9",
    "letter": "v1.0-w9",
    "letter_v2": "v2.0-w15",  # W15 skill3-iterate
}

# letter_v2 不计入 4 主类型 (DOC_TYPES), 但暴露端点 + health 报告
ADDITIONAL_LETTER_VERSIONS = ["letter_v2"]


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
        f"\n[LexPrime 元枢法智 · Skill 3 文书生成 · {TEMPLATE_VERSIONS.get(doc_type, 'v1.0')} · "
        f"类型={DOC_TYPE_LABELS.get(doc_type, doc_type)} · 生成时间={datetime.now(timezone.utc).isoformat()}]"
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
    # ---- W19 skill3-gradual 灰度字段 ----
    served_version: Optional[str] = Field(
        None,
        description="(W19 灰度) 实际服务的版本: letter_v1 / letter_v2 / complaint_v1 / ...",
    )
    bucket: Optional[str] = Field(
        None,
        description="(W19 灰度) A/B 测试 bucket: control / treatment_a / treatment_b",
    )
    rollout_phase: Optional[str] = Field(
        None,
        description="(W19 灰度) 灰度阶段: disabled / ab_10pct / rollout_50pct / rollout_100pct",
    )


# 强制 AI 辅助声明 (复用 Skill 2 / Skill 1 风格)
DISCLAIMER_FULL = (
    "本文书由 LexPrime 元枢法智 (Skill 3 文书生成 v0.1.0-w9) 自动生成, "
    "内容基于律师提供的事实与证据整理。本文书仅供参考与辅助律师起草使用, "
    "不构成正式法律意见, 律师应根据案件实际情况进行审核、修改和完善。"
)

# v2.0 文书免责声明 (含 8 律师反馈迭代说明)
DISCLAIMER_V2 = (
    "本律师函由 LexPrime 元枢法智 (Skill 3 文书生成 v2.0-w15) 自动生成, "
    "内容基于律师提供的事实整理, 用于辅助律师起草。本函件仅供参考, "
    "律师应根据案件实际情况、相关法律法规进行审核、修改和完善。 "
    "本版本基于 8 律师试用反馈 (mock) 迭代, 新增: (1) 时限梯度 "
    "(2) 法条具体引用 (3) 三段式事实 (4) 后果量化 (5) 履行步骤细化 "
    "(6) 客户签字栏 (7) AI 5 维度风险标注块 (8) doc_workflow + signature_router 集成说明。"
)


# ====== 帮助函数: 生成文书 ======
async def _generate_doc(
    doc_type: str, req: DocGenRequest, force_version: Optional[str] = None
) -> DocGenResponse:
    """生成文书的内部实现 (4 端点共用)

    Args:
        doc_type: 4 种之一 (complaint/defense/contract/letter)
        req: DocGenRequest
        force_version: 强制使用某个版本 (跳过 rollout 路由)
            - "letter" → 走 rollout 路由
            - "letter_v2" → 强制 v2.0
            - "letter_v1" → 强制 v1.0 (灰度反向回退)
            - None → 按 endpoint 默认 (gen_letter 自动路由, gen_letter_v2 强制 v2)

    Returns:
        DocGenResponse (含 markdown + docx_base64 + W19 灰度字段)
    """
    t0 = time.time()

    # W19 skill3-gradual: 灰度路由 (仅 letter 启用)
    served_version = doc_type  # 用于响应报告
    template_key = doc_type     # 用于加载模板
    bucket: Optional[str] = None
    rollout_cfg = get_rollout_config()
    rollout_phase = rollout_cfg.phase.value
    if force_version is not None:
        # 显式 v2.0 (letter-v2 端点) → 用 v2 模板
        if force_version == "letter_v2":
            template_key = "letter_v2"
            served_version = "letter_v2"
        else:
            # force_version == "letter_v1" (灰度反向回退, 未来用)
            template_key = "letter"
            served_version = "letter_v1"
        bucket = "explicit"
    elif doc_type == "letter":
        # POST /api/doc-gen/letter 自动按 rollout 路由
        version, bucket = assign_version(req.lawyer_id, "letter")
        template_key = _LETTER_VERSION_TO_TEMPLATE_KEY[version]
        served_version = version.value

    # 1. 加载模板
    try:
        template_md = _load_template(template_key)
    except FileNotFoundError as e:
        logger.error(f"[doc-gen.{template_key}] 模板缺失: {e}")
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
                doc_type=template_key,
                title=DOC_TYPE_LABELS.get(template_key, "律师函 v2.0"),
            )
            docx_base64 = base64.b64encode(docx_bytes).decode("ascii")
            docx_filename = f"{template_key}-{gen_id}.docx"
            docx_size = len(docx_bytes)
        except Exception as e:
            logger.exception(f"[doc-gen.{template_key}] docx 生成失败: {e}")
            raise HTTPException(500, f"docx 生成失败: {e}")

    # 5. markdown 单独请求时跳过 docx
    if req.output_format == "markdown":
        docx_base64 = None
        docx_filename = None
        docx_size = None

    latency_ms = int((time.time() - t0) * 1000)
    generated_at = datetime.now(timezone.utc).isoformat()

    logger.info(
        f"[doc-gen.{template_key}] gen_id={gen_id} lawyer={req.lawyer_id} "
        f"bucket={bucket} phase={rollout_phase} "
        f"filled={len(filled)}/{len(all_keys)} missing={len(missing)} "
        f"format={req.output_format} latency={latency_ms}ms"
    )

    # W19 skill3-gradual: 记录 metric (3 指标跟踪)
    try:
        # 提取 v2.0 5 维度风险评分 (如果有)
        risk_scores: Optional[Dict[str, float]] = None
        if served_version == "letter_v2":
            risk_scores = {}
            for dim in ("facts", "legal", "demand", "deadline", "consequence"):
                raw = req.fields.get(f"risk_dim_{dim}")
                if raw is not None:
                    try:
                        risk_scores[dim] = float(raw)
                    except (TypeError, ValueError):
                        pass
        from core.rollout import GenerationMetric
        get_metrics_collector().record(
            GenerationMetric(
                lawyer_id=req.lawyer_id,
                doc_type=template_key,
                version=served_version,
                bucket=bucket or "explicit",
                timestamp=time.time(),
                latency_ms=latency_ms,
                filled_fields=len(filled),
                missing_fields=len(missing),
                risk_scores=risk_scores,
            )
        )
    except Exception as e:
        # metric 记录失败不影响主流程
        logger.warning(f"[doc-gen.metrics] 记录失败: {e}")

    return DocGenResponse(
        gen_id=gen_id,
        doc_type=doc_type,
        doc_type_label=DOC_TYPE_LABELS.get(template_key, template_key),
        template_id=_TEMPLATE_ID_MAP.get(template_key, template_key),
        template_version=TEMPLATE_VERSIONS.get(template_key, "v1.0-w9"),
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
        disclaimer=DISCLAIMER_V2 if served_version == "letter_v2" else DISCLAIMER_FULL,
        next="GET /api/doc-gen/health",
        served_version=served_version,
        bucket=bucket,
        rollout_phase=rollout_phase,
    )


# template_id 映射 (v1 主类型保持 "complaint_v1" 不变, v2 用 "letter_v2")
_TEMPLATE_ID_MAP = {
    "complaint": "complaint_v1",
    "defense": "defense_v1",
    "contract": "contract_v1",
    "letter": "letter_v1",
    "letter_v2": "letter_v2",
}

# W19 skill3-gradual: LetterVersion -> TEMPLATE_FILES key 映射
# (template key 用于加载 .md 文件, served_version 用于响应报告)
_LETTER_VERSION_TO_TEMPLATE_KEY = {
    LetterVersion.V1: "letter",
    LetterVersion.V2: "letter_v2",
}


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


# ====== 端点 4: POST /api/doc-gen/letter (W19 灰度自动路由) ======
@router.post("/letter", response_model=DocGenResponse)
async def gen_letter(req: DocGenRequest):
    """律师函生成 (W19 灰度自动路由 v1.0 / v2.0)

    W19 skill3-gradual 灰度:
    - 灰度阶段 disabled: 全部 v1.0
    - 灰度阶段 ab_10pct (8/15 起): 10% 律师走 v2.0 (内 50/50 A/B)
    - 灰度阶段 rollout_50pct (9/1 起): 50% 律师走 v2.0 (内 50/50 A/B)
    - 灰度阶段 rollout_100pct (10/1 起, W21): 全部 v2.0

    W21 skill3-full-rollout:
    - 10/1 全量 100% (phase=rollout_100pct, letter_v1_deprecated=False):
      100% 律师走 v2.0, A/B test 关闭
    - 11/1 v1.0 退役 (letter_v1_deprecated=True):
      即使 force_v1 也强制 v2.0, 兼容旧 v1 数据走 v2 模板重渲
    - 兼容性: 现有 v1.0 文书数据保留 (W12 A2 doc_workflow 不动)

    路由依据: hash(lawyer_id) → bucket (deterministic, 防止串扰)
    强制列表: env LEX_SKILL3_FORCE_V1 / LEX_SKILL3_FORCE_V2
              (11/1 退役后 force_v1 无效, 全部走 v2)

    必填建议字段 (v1):
        recipient, sender, subject, facts, demands, deadline, consequence,
        lawyer_name, lawyer_phone

    必填建议字段 (v2 增量, 已在 letter_v2 文档列):
        lawyer_license_no, facts_parties/subject/breach, demand_step_1/2/3,
        deadline_primary/grad_first/grad_final, amount_in_dispute, interest_rate,
        risk_dim_facts/legal/demand/deadline/consequence, risk_overall

    显式 v2.0: 用 POST /api/doc-gen/letter-v2 (不走灰度)

    返回:
        - served_version: 实际服务的版本 (letter_v1 / letter_v2)
        - bucket: control / treatment_a / treatment_b
        - rollout_phase: 当前灰度阶段
    """
    return await _generate_doc("letter", req)


# ====== 端点 5: POST /api/doc-gen/letter-v2 (W15 skill3-iterate, 显式 v2.0) ======
@router.post("/letter-v2", response_model=DocGenResponse)
async def gen_letter_v2(req: DocGenRequest):
    """律师函 v2.0 生成 (模板: letter_v2.md, W15 skill3-iterate, 显式 v2.0)

    基于 8 律师试用反馈 (mock) 迭代, 包含以下升级:
    - 时限梯度 (deadline_primary + deadline_grad_*)
    - 法条具体引用 (legal_basis / legal_basis_civil)
    - 三段式事实 (facts_parties / facts_subject / facts_breach)
    - 后果量化 (amount_in_dispute + interest_rate + consequence_other)
    - 履行步骤细化 (demand_step_1/2/3)
    - 客户签字栏 (lawyer_license_no)
    - AI 5 维度风险标注块 (risk_dim_facts/legal/demand/deadline/consequence + risk_overall)
    - doc_workflow + signature_router 集成说明

    必填建议字段:
        recipient, sender, subject, facts, demands, deadline, consequence,
        lawyer_name, lawyer_phone, lawyer_license_no,
        facts_parties, facts_subject, facts_breach,
        demand_step_1, deadline_primary, deadline_grad_first, deadline_grad_final,
        amount_in_dispute, interest_rate,
        risk_dim_facts, risk_dim_legal, risk_dim_demand, risk_dim_deadline, risk_dim_consequence, risk_overall

    集成:
    - doc_workflow: PATCH /api/doc-gen/{doc_id}/state (W12 A2)
    - signature_router: POST /api/signature/{doc_id} (W12 A2)
    - 风险标注: POST /api/doc-gen/{doc_id}/risk-annotation (W12 A2)

    注: 显式 v2.0 端点, 不走灰度路由. 灰度验证请用 /api/doc-gen/letter.
    """
    return await _generate_doc("letter_v2", req, force_version="letter_v2")


# ====== 端点 6: GET /api/doc-gen/health ======
@router.get("/health")
async def doc_gen_health():
    """Skill 3 文书生成 健康检查 (4 主模板 + 1 letter_v2 扩展模板)

    返回:
        - status            ok / degraded
        - templates_loaded  所有模板是否都能加载 (4 主 + letter_v2)
        - docx_available    python-docx 是否可用
        - template_field_counts  每模板字段数 (用于前端 UI hint)
        - additional_versions  letter 类型的 v2.0 等扩展
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

    # W15 扩展: letter_v2 状态 (附加版本)
    additional_versions: Dict[str, Dict[str, Any]] = {}
    for doc_type in ADDITIONAL_LETTER_VERSIONS:
        try:
            md = _load_template(doc_type)
            fields = _extract_placeholders(md)
            additional_versions[doc_type] = {
                "label": DOC_TYPE_LABELS.get(doc_type, "律师函 v2.0"),
                "version": TEMPLATE_VERSIONS[doc_type],
                "loaded": True,
                "field_count": len(fields),
                "fields": fields,
                "path": str(_templates_dir() / TEMPLATE_FILES[doc_type]),
            }
        except Exception as e:
            additional_versions[doc_type] = {
                "label": "律师函 v2.0",
                "version": TEMPLATE_VERSIONS[doc_type],
                "loaded": False,
                "error": str(e),
                "path": str(_templates_dir() / TEMPLATE_FILES[doc_type]),
            }

    all_loaded = all(s.get("loaded") for s in template_status.values()) and all(
        s.get("loaded") for s in additional_versions.values()
    )

    return {
        "status": "ok" if (all_loaded and DOCX_AVAILABLE) else "degraded",
        "service_id": "lexprime.skill.doc-gen",
        "version": "0.2.0-w15",  # W15 升级到 0.2.0
        "docx_available": DOCX_AVAILABLE,
        "templates": template_status,
        "additional_versions": additional_versions,  # W15: letter_v2
        "template_count": len(DOC_TYPES),
        "additional_versions_count": len(ADDITIONAL_LETTER_VERSIONS),
        "templates_loaded": sum(1 for s in template_status.values() if s.get("loaded")),
        "additional_versions_loaded": sum(1 for s in additional_versions.values() if s.get("loaded")),
        "doc_types": DOC_TYPES,
        "doc_type_labels": DOC_TYPE_LABELS,
        # W19 skill3-gradual 灰度状态 (合并 rollout/status 摘要)
        "rollout": _rollout_status_dict(),
        "endpoints": [
            "POST /api/doc-gen/complaint",
            "POST /api/doc-gen/defense",
            "POST /api/doc-gen/contract",
            "POST /api/doc-gen/letter",
            "POST /api/doc-gen/letter-v2",
            "GET /api/doc-gen/health",
            "GET /api/doc-gen/rollout/status",
            "GET /api/doc-gen/metrics",
        ],
    }


# ====== W19 skill3-gradual: rollout 状态字典 (供 /health + /rollout/status 复用) ======
def _rollout_status_dict() -> Dict[str, Any]:
    """灰度配置摘要 (dict 形式, 供多个端点共享)

    W21 skill3-full-rollout 扩展:
        - letter_v1_deprecated: 11/1 退役开关 (False=10/1 全量 100%, True=11/1 退役后)
        - deprecated_after_date: 退役触发日期 ("2026-11-01")
        - backward_compat_note: 现有 v1.0 文书数据保留说明
    """
    cfg = get_rollout_config()
    return {
        "phase": cfg.phase.value,
        "rollout_pct": cfg.rollout_pct,
        "ab_split_within_v2": list(cfg.ab_split_within_v2),
        "enabled_doc_types": list(cfg.enabled_doc_types),
        "force_v2_lawyers_count": len(cfg.force_v2_lawyers),
        "force_v1_lawyers_count": len(cfg.force_v1_lawyers),
        "force_v2_lawyers": list(cfg.force_v2_lawyers),  # 完整列表, 供 owner 验证
        "force_v1_lawyers": list(cfg.force_v1_lawyers),
        # W21 skill3-full-rollout 新增字段
        "letter_v1_deprecated": cfg.letter_v1_deprecated,  # 11/1 退役开关
        "deprecated_after_date": "2026-11-01",  # 退役触发日期
        "backward_compat_note": (
            "现有 v1.0 文书数据保留 (W12 A2 doc_workflow 不动), "
            "11/1 之后只支持 v2.0 生成 (POST /api/doc-gen/letter 自动走 v2.0)"
        ),
        "phases_legend": {
            "disabled": "全 v1.0 (灰度前)",
            "ab_10pct": "8/15 v2.0 10% 灰度 + A/B 50/50 split",
            "rollout_50pct": "9/1 v2.0 全量 50% 灰度",
            "rollout_100pct": "10/1 v2.0 全量 100% (W21)",
        },
        "env_overrides": {
            "LEX_SKILL3_ROLLOUT_PHASE": cfg.phase.value,
            "LEX_SKILL3_ROLLOUT_PCT": cfg.rollout_pct,
            "LEX_SKILL3_AB_SPLIT": ",".join(str(x) for x in cfg.ab_split_within_v2),
            "LEX_SKILL3_FORCE_V2_count": len(cfg.force_v2_lawyers),
            "LEX_SKILL3_FORCE_V1_count": len(cfg.force_v1_lawyers),
            "LEX_SKILL3_LETTER_V1_DEPRECATED": cfg.letter_v1_deprecated,  # W21 新增
        },
    }


# ====== 端点 7: GET /api/doc-gen/rollout/status (W19 skill3-gradual) ======
@router.get("/rollout/status")
async def rollout_status():
    """Skill 3 律师函 v2.0 灰度状态 (W19 skill3-gradual)

    返回:
        - phase: 当前灰度阶段
        - rollout_pct: v2.0 灰度百分比 (0-100)
        - ab_split_within_v2: A/B 分配比例 [treatment_a%, treatment_b%]
        - enabled_doc_types: 参与灰度的文书类型
        - force_v2_lawyers: 强制 v2.0 律师列表 (白名单, 用于评审 #N 关键律师)
        - force_v1_lawyers: 强制 v1.0 律师列表 (黑名单, 用于对照测试)
        - phases_legend: 阶段说明
        - env_overrides: 当前生效的 env 变量

    配置方式 (env):
        - LEX_SKILL3_ROLLOUT_PHASE: disabled | ab_10pct | rollout_50pct | rollout_100pct
        - LEX_SKILL3_ROLLOUT_PCT: 0-100 (默认 0)
        - LEX_SKILL3_AB_SPLIT: "50,50" (默认 50/50)
        - LEX_SKILL3_FORCE_V2: 逗号分隔律师 ID (白名单, 默认空)
        - LEX_SKILL3_FORCE_V1: 逗号分隔律师 ID (黑名单, 默认空)

    注: 灰度阶段切换 (8/15 + 9/1) 走 cron + env 切换, 不需要重启服务.
    """
    return {
        "status": "ok",
        "service_id": "lexprime.skill.doc-gen.rollout",
        "rollout": _rollout_status_dict(),
        "next": "GET /api/doc-gen/metrics",
    }


# ====== 端点 8: GET /api/doc-gen/metrics (W19 skill3-gradual) ======
@router.get("/metrics")
async def doc_gen_metrics():
    """Skill 3 文书生成 3 指标汇总 (W19 skill3-gradual)

    3 指标:
    1. 5 维度评分 (letter v2.0 自动生成, 1+ lawyer 评分):
       - 事实 / 法律意见 / 要求 / 时限 / 后果
    2. 转化率: 生成后 7 天内 lawyer 是否付费
    3. 律师满意度: 1-5 主动评分 (调用方更新 via POST /api/doc-gen/metrics/update)

    返回:
        - total_records: 总生成次数
        - by_version: {letter_v1: N, letter_v2: N, complaint_v1: N, ...}
        - by_bucket: {control: N, treatment_a: N, treatment_b: N}
        - 5_dimension_avg_scores: {facts: 0.X, legal: 0.X, demand: 0.X, ...}
        - conversion_rate_by_bucket: {control: 0.X, treatment_a: 0.X, treatment_b: 0.X}
        - lawyer_satisfaction_avg: {control: 4.X, treatment_a: 4.X, treatment_b: 4.X}
        - ab_test_winner: "treatment_a" | "treatment_b" | null (A/B test 赢家, 综合 3 指标)
        - note: "实测为主, owner 8/15 + 9/1 跑灰度后填实"

    注: in-memory 存储, 重启后清零. 生产应接 Prometheus / OpenTelemetry.
    实际数字全部 [实测填实], owner 8/15 + 9/1 跑完灰度后用 patch 替换 placeholder.
    """
    return {
        "status": "ok",
        "service_id": "lexprime.skill.doc-gen.metrics",
        "rollout_phase": get_rollout_config().phase.value,
        "summary": get_metrics_collector().summary(),
        "next": "GET /api/doc-gen/rollout/status",
    }