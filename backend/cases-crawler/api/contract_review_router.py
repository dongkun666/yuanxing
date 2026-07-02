"""
Skill 2 合同风险审查 API Router (W5 实施)

端点 (4 个):
- POST /api/contract-review/upload        接收合同文本 (或 fixture_id) → 返回 review_id
- GET  /api/contract-review/result/{id}   返回完整审查结果 (clause_reviews + summary + strategy)
- POST /api/contract-review/negotiation   谈判策略增强 (基于 review_id + 立场)
- POST /api/contract-review/export        导出 Word/PDF/Markdown (简化为 Markdown + HTML)

Demo 模式 (W5 关键):
- ?demo=1 或 contract_text="" + fixture_id="demo-..." → 走 fixture 路径
- 5 合同 baseline 覆盖房屋租赁/借款/劳动/服务/销售
- 真实审查: 复用 W4 reviewer.run_skill(), 走规则层 (不调 LLM)

PRD: § 5.4 Skill Hub + § 5.6 当事人服务类文书
Track: E-skills · T-REF-22 (subagent RPC)
"""
from __future__ import annotations

import time
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, File, Form, UploadFile
from pydantic import BaseModel, Field
from loguru import logger

# Skill 内部
from skills.contract_review.reviewer import (
    ReviewerInput,
    ReviewerConfig,
    run_skill,
    ReviewerOutput,
    CONTRACT_TYPES,
    STANCES,
)
from skills.contract_review.language_guard import DISCLAIMER_FULL
from skills.contract_review.demo import (
    list_fixtures,
    run_fixture_review,
    render_markdown_report,
    render_html_report,
    FixtureError,
)

# 规则引擎
from skills.contract_review.rule_engine import (
    review_contract,
    get_default_manager,
    generate_visualization_data,
    generate_priority_list,
    group_suggestions_by_severity,
    apply_one_click_fix,
    RuleSeverity,
    RuleCategory,
)

# W5 Track B (lex-ai): OCR + PII 基础设施
from core.ocr import (
    OcrResult as EngineOcrResult,
    OcrEngineUnavailableError,
    OcrError,
    OcrUnsupportedFormatError,
    detect_mime,
    get_ocr_engine,
    current_engine_name,
    is_paddle_available,
)
from core.pii import sanitize_for_review, PiiReport

router = APIRouter(prefix="/api/contract-review", tags=["skill:contract-review"])


# ===== 内存级 review 缓存 (W5 dev/demo 简化) =====
# 生产应存 Redis/SQLite, W5 dev 先内存级足够
_REVIEW_CACHE: dict = {}


# ===== Request / Response Models =====

class UploadRequest(BaseModel):
    """上传合同请求 — 支持 3 路径: 文本粘贴 / OCR 输出 / fixture demo"""
    contract_type: str = Field(..., min_length=2, max_length=32, description="8 大类合同类型")
    contract_text: Optional[str] = Field(None, max_length=60000, description="合同文本 (≤ 60000 字, 超过 50000 字 reviewer 内部截断)")
    fixture_id: Optional[str] = Field(None, description="Demo 模式: fixture_id")
    stance: str = Field("审查方", description="甲方/乙方/丙方/审查方")
    industry: Optional[str] = Field(None, max_length=64)
    jurisdiction: Optional[str] = Field(None, max_length=64)
    amount: Optional[float] = Field(None, ge=0)
    focus_areas: list = Field(default_factory=list, max_length=10)
    include_negotiation_strategy: bool = Field(True, description="是否生成谈判策略")
    include_version_diff: bool = Field(False, description="是否做版本比对 (W5 占位)")
    case_id: Optional[str] = Field(None, description="案件 ID")


class UploadResponse(BaseModel):
    """上传响应"""
    review_id: str
    status: str
    latency_ms: int
    fixture_id: Optional[str] = None
    demo_mode: bool = False
    next: str  # "GET /api/contract-review/result/{review_id}"


class NegotiationRequest(BaseModel):
    """谈判策略请求"""
    review_id: str
    stance: Optional[str] = Field(None, description="切换立场 (可选, 默认沿用 review 中的立场)")
    additional_priorities: list = Field(default_factory=list, description="律师额外关注的优先条款 ID")


class ExportRequest(BaseModel):
    """导出请求"""
    review_id: str
    format: str = Field("markdown", pattern="^(markdown|html|word|pdf)$", description="导出格式")
    include_strategy: bool = Field(True)
    include_history: bool = Field(True)
    include_diff: bool = Field(False)
    include_footer: bool = Field(True)
    include_watermark: bool = Field(False)


# ===== 端点 1: 上传 (或 demo 入口) =====

@router.post("/upload")
async def upload_contract(req: UploadRequest):
    """合同上传 + 审查入口

    3 种模式:
    1. 真实文本: contract_text 非空 → 走 reviewer.run_skill()
    2. Demo 模式: fixture_id 提供 → 走 fixture loader
    3. 自动 demo: 都为空 → 提示前端引导选 fixture
    """
    t0 = time.time()
    review_id = f"cr-{uuid.uuid4().hex[:12]}"

    # --- 路径选择 ---
    if req.fixture_id:
        # Demo 路径
        try:
            review = run_fixture_review(req.fixture_id, stance=req.stance)
        except FixtureError as e:
            raise HTTPException(404, f"Demo fixture 不可用: {str(e)}")
        review["query_meta"]["case_id"] = req.case_id
        _REVIEW_CACHE[review_id] = review
        latency_ms = int((time.time() - t0) * 1000)
        return UploadResponse(
            review_id=review_id,
            status="completed",
            latency_ms=latency_ms,
            fixture_id=req.fixture_id,
            demo_mode=True,
            next=f"GET /api/contract-review/result/{review_id}",
        )

    if not req.contract_text or len(req.contract_text.strip()) < 50:
        raise HTTPException(
            400,
            "contract_text 必填 (≥ 50 字) 或提供 fixture_id 走 demo 模式",
        )

    # --- 真实审查路径 ---
    ri = ReviewerInput(
        contract_type=req.contract_type,
        contract_text=req.contract_text,
        stance=req.stance,
        industry=req.industry or "",
        amount=req.amount,
        jurisdiction=req.jurisdiction or "",
        focus_areas=req.focus_areas,
        include_suggestion=True,
        include_negotiation_strategy=req.include_negotiation_strategy,
        include_version_diff=req.include_version_diff,
        case_id=req.case_id,
    )
    config = ReviewerConfig(retrieval_enabled=True)  # W4 双路召回

    try:
        out: ReviewerOutput = run_skill(ri, config)
        out_dict = out.to_dict()
    except Exception as e:
        logger.exception(f"合同审查失败: {e}")
        raise HTTPException(500, f"审查失败: {str(e)}")

    out_dict["query_meta"]["case_id"] = req.case_id
    _REVIEW_CACHE[review_id] = out_dict

    latency_ms = int((time.time() - t0) * 1000)
    return UploadResponse(
        review_id=review_id,
        status="completed",
        latency_ms=latency_ms,
        fixture_id=None,
        demo_mode=False,
        next=f"GET /api/contract-review/result/{review_id}",
    )


# ===== 端点 2: 审查结果 =====

@router.get("/result/{review_id}")
async def get_result(review_id: str):
    """返回完整审查结果 (clause_reviews + summary + strategy + UI hints)

    给前端 02-review-result 页面用
    """
    if review_id not in _REVIEW_CACHE:
        raise HTTPException(404, f"review_id 不存在: {review_id} (可能已过期或未上传)")

    review = _REVIEW_CACHE[review_id]
    return review


# ===== 端点 3: 谈判策略 (重新生成 / 增强) =====

@router.post("/negotiation")
async def get_negotiation_strategy(req: NegotiationRequest):
    """谈判策略 — 可基于 review_id 切换立场重新生成

    给前端 04-negotiation 弹窗用
    """
    if req.review_id not in _REVIEW_CACHE:
        raise HTTPException(404, f"review_id 不存在: {req.review_id}")

    review = _REVIEW_CACHE[req.review_id]
    stance = req.stance or review["query_meta"].get("stance", "审查方")

    # 直接复用 review 的 negotiation_strategy (W5 dev 简化, 不重新跑审查)
    strategy = review.get("negotiation_strategy", {})

    # 切换立场时, 调整 stance_specific_advice (示意)
    if req.stance and req.stance != review["query_meta"].get("stance"):
        strategy = _adjust_strategy_for_stance(strategy, stance)
        # 更新 review 缓存
        review["negotiation_strategy"] = strategy
        review["query_meta"]["stance"] = stance

    # 合并 additional_priorities
    if req.additional_priorities:
        existing = strategy.get("priority_clauses", [])
        seen = set(existing)
        for p in req.additional_priorities:
            if p not in seen:
                existing.insert(0, p)
                seen.add(p)
        strategy["priority_clauses"] = existing[:10]

    return {
        "review_id": req.review_id,
        "stance": stance,
        "strategy": strategy,
        "disclaimer": DISCLAIMER_FULL,
    }


def _adjust_strategy_for_stance(strategy: dict, new_stance: str) -> dict:
    """立场切换时的策略调整 (W5 简化: 替换立场建议文字, 不重算整个)"""
    adjusted = dict(strategy)
    advice_map = {
        "甲方": (
            "作为甲方, 应重点利用首期付款条件与尾款质保金条款作为谈判筹码, "
            "对单方解除权与违约金条款从严要求, 防止乙方违约时救济困难。"
        ),
        "乙方": (
            "作为乙方, 应重点争取解除条件对等、违约金调减与管辖本地化, "
            "对单方解除权 (甲方独有) 强烈要求改为双向, 否则建议放弃合作。"
        ),
        "丙方": (
            "作为丙方 (担保方/第三方), 应严格限制担保责任范围与期限, "
            "对担保条款要求约定明确的反担保与追偿权。"
        ),
        "审查方": (
            "作为审查方 (受托审查), 应客观列出双方风险点, "
            "不偏向任何一方, 重点提示可执行性与司法救济路径。"
        ),
    }
    adjusted["stance_specific_advice"] = advice_map.get(new_stance, advice_map["审查方"])
    return adjusted


# ===== 端点 4: 导出 =====

@router.post("/export")
async def export_report(req: ExportRequest):
    """导出报告 (Markdown / HTML / Word 占位 / PDF 占位)

    W5 dev: 完整 Markdown + HTML, Word/PDF 占位返回 base64 占位说明
    """
    if req.review_id not in _REVIEW_CACHE:
        raise HTTPException(404, f"review_id 不存在: {req.review_id}")

    review = _REVIEW_CACHE[req.review_id]

    if req.format == "markdown":
        content = render_markdown_report(review)
        media_type = "text/markdown; charset=utf-8"
        filename = f"contract-review-{req.review_id}.md"
    elif req.format == "html":
        content = render_html_report(review)
        media_type = "text/html; charset=utf-8"
        filename = f"contract-review-{req.review_id}.html"
    elif req.format in ("word", "pdf"):
        # W5 dev 占位: 返回 Markdown 作为 fallback, 前端可提示用户
        content = render_markdown_report(review)
        media_type = "text/markdown; charset=utf-8"
        filename = f"contract-review-{req.review_id}.md"
        review = dict(review)
        review["export_note"] = (
            f"W5 dev 占位: {req.format} 导出暂未实现, 已返回 Markdown。"
            "W6+ 计划接入 docx + reportlab 库。"
        )
    else:
        raise HTTPException(400, f"不支持的导出格式: {req.format}")

    # 可选过滤
    if not req.include_strategy:
        # Markdown 移除 "三、谈判策略" 段 (HTML 简化处理)
        if req.format == "markdown" and "## 三、谈判策略" in content:
            content = content.split("## 三、谈判策略")[0] + "\n\n## 四、免责声明\n\n"
            content += review.get("disclaimer", DISCLAIMER_FULL) + "\n"

    return {
        "review_id": req.review_id,
        "format": req.format,
        "media_type": media_type,
        "filename": filename,
        "content": content,
        "size_bytes": len(content.encode("utf-8")),
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime()),
    }


# ===== 健康检查 + Fixtures 列表 =====

@router.get("/health")
async def skill_health():
    """Skill 健康检查"""
    fixtures = list_fixtures()
    return {
        "status": "ok",
        "skill_id": "lexprime.skill.contract-review",
        "version": "0.2.0-w5",
        "data_sources": ["reviewer_rule_engine", "fixture_5_baseline", "lancedb_w4"],
        "fixtures_available": len(fixtures),
        "endpoints": [
            "POST /api/contract-review/upload",
            "GET /api/contract-review/result/{review_id}",
            "POST /api/contract-review/negotiation",
            "POST /api/contract-review/export",
        ],
    }


@router.get("/fixtures")
async def get_fixtures():
    """列出 demo 模式可用的 5 合同 fixture (给前端 01-upload "示例合同" 下拉)"""
    return {
        "fixtures": list_fixtures(),
        "count": len(list_fixtures()),
    }


@router.get("/disclaimer")
async def skill_disclaimer():
    """返回强制免责声明 (前端可独立 fetch 渲染)"""
    return {
        "full": DISCLAIMER_FULL,
        "short": "本审查仅为基于合同文本的客观风险标注与法律依据提示, 不构成法律意见, 更不替代律师的专业判断。",
    }


# ============================================================
# W5 Track B (lex-ai): OCR 上传 + PII 脱敏 + Skill 2 集成
# ============================================================
# 端点:
# - POST /api/contract-review/ocr-upload   图片/PDF → OCR → PII → 风险审查
# - GET  /api/contract-review/ocr-health   OCR 引擎状态
#
# 流程 (ocr-upload):
# 1. 接收 multipart file (PNG/JPG/PDF, 含扫描件)
# 2. core.ocr.get_ocr_engine() 跑 OCR → raw_text + confidence
# 3. core.pii.sanitize_for_review() PII 脱敏 → sanitized_text + PiiReport
# 4. skills.contract_review.reviewer.run_skill() 审查 → ReviewerOutput
# 5. 合并 OCR + PII + 审查结果 → OcrUploadResponse
# ============================================================

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB (单文件)
SUPPORTED_MIMES = {
    "image/png", "image/jpeg", "image/gif",
    "image/bmp", "image/webp",
    "application/pdf",
}


class OcrInfo(BaseModel):
    """OCR 识别元信息 (W5 Track B)"""
    confidence: float
    source_engine: str
    detected_mime: str
    page_count: int
    line_count: int
    raw_text_length: int


class PiiInfo(BaseModel):
    """PII 脱敏报告 (W5 Track B)"""
    id_card_count: int = 0
    mobile_count: int = 0
    bank_card_count: int = 0
    email_count: int = 0
    address_count: int = 0
    person_name_count: int = 0
    total: int = 0
    samples: list = Field(default_factory=list)


class OcrUploadResponse(BaseModel):
    """OCR 上传审查响应 (W5 Track B)"""
    ocr: OcrInfo
    pii: PiiInfo
    sanitized_text: str
    review: dict
    query_meta: dict
    latency_ms: int
    disclaimer: str
    ui_hints: dict = Field(default_factory=dict)


@router.get("/ocr-health")
async def ocr_health():
    """W5 Track B: OCR 引擎 + PII 健康检查"""
    return {
        "status": "ok",
        "skill_id": "lexprime.skill.contract-review",
        "version": "0.3.0-w5",
        "ocr_engine": current_engine_name(),
        "ocr_engine_paddle_available": is_paddle_available(),
        "supported_mimes": sorted(SUPPORTED_MIMES),
        "max_upload_bytes": MAX_UPLOAD_BYTES,
        "pii_types": ["id_card", "mobile", "bank_card", "email", "address", "person_name"],
    }


@router.post("/ocr-upload", response_model=OcrUploadResponse)
async def contract_review_ocr_upload(
    file: UploadFile = File(..., description="合同图片 (PNG/JPG) 或 PDF (含扫描件)"),
    contract_type: str = Form("其他", description="合同类型 (房屋租赁/借款合同/...)"),
    stance: str = Form("审查方", description="立场 (甲方/乙方/丙方/审查方)"),
    industry: str = Form("", description="行业 (可选)"),
    jurisdiction: str = Form("", description="管辖地 (可选)"),
    amount: Optional[float] = Form(None, description="涉案金额 (可选)"),
    focus_areas: str = Form("", description="重点关注领域, 逗号分隔 (可选)"),
    case_id: Optional[str] = Form(None, description="关联案件 ID (可选)"),
    skip_pii: bool = Form(False, description="跳过 PII 脱敏 (调试用, 默认 False)"),
):
    """W5 Track B: 图片/PDF 合同 OCR 识别 + PII 脱敏 + 风险审查

    流程:
    1. 校验文件 (大小 ≤ 20MB, MIME 在支持列表)
    2. core.ocr.get_ocr_engine() 跑 OCR (默认 mock, 配 LEX_OCR_ENGINE=paddle 走真 paddle)
    3. core.pii.sanitize_for_review() 脱敏 PII (身份证/手机/银行卡/邮箱/地址/人名)
    4. skills.contract_review.run_skill() 审查 → ReviewerOutput
    5. 合并响应 (OCR + PII + 风险列表 + disclaimer)

    Note:
    - 必传 file, 其他 form 字段均可选
    - 失败时返回 4xx (校验) / 5xx (引擎异常)
    - 生产 PaddleOCR 部署见 docs/ocr-deployment.md
    """
    t0 = time.time()

    # ---- 1) 校验 ----
    if contract_type not in CONTRACT_TYPES:
        contract_type = "其他"
    if stance not in STANCES:
        stance = "审查方"
    focus_list = (
        [a.strip() for a in focus_areas.split(",") if a.strip()]
        if focus_areas else []
    )

    # ---- 2) 读 bytes ----
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(400, "file is empty")
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            413,
            f"file too large: {len(file_bytes)} bytes > {MAX_UPLOAD_BYTES} bytes",
        )

    mime = file.content_type or detect_mime(file_bytes, file.filename or "")
    if mime not in SUPPORTED_MIMES:
        raise HTTPException(
            415,
            f"unsupported mime: {mime}. supported: {sorted(SUPPORTED_MIMES)}",
        )

    # ---- 3) OCR ----
    try:
        engine = get_ocr_engine()
        engine_result: EngineOcrResult = engine.run(
            file_bytes,
            filename=file.filename or "",
            mime_type=mime,
        )
    except OcrEngineUnavailableError as e:
        logger.error(f"[contract-review.ocr] engine unavailable: {e}")
        raise HTTPException(503, f"OCR engine unavailable: {e}")
    except OcrUnsupportedFormatError as e:
        raise HTTPException(415, f"OCR unsupported format: {e}")
    except OcrError as e:
        logger.exception(f"[contract-review.ocr] engine error: {e}")
        raise HTTPException(500, f"OCR engine error: {e}")
    except Exception as e:
        logger.exception(f"[contract-review.ocr] unexpected: {e}")
        raise HTTPException(500, f"OCR unexpected: {e}")

    if not engine_result.raw_text or not engine_result.raw_text.strip():
        raise HTTPException(
            422,
            "OCR returned empty text. File may be unreadable or blank.",
        )

    # ---- 4) PII 脱敏 ----
    if skip_pii:
        sanitized_text = engine_result.raw_text
        pii_report = PiiReport()
    else:
        sanitized_text, pii_report = sanitize_for_review(engine_result.raw_text)

    # ---- 5) Skill 2 审查 ----
    ri = ReviewerInput(
        contract_type=contract_type,
        contract_text=sanitized_text,
        stance=stance,
        industry=industry or "",
        amount=amount,
        jurisdiction=jurisdiction or "",
        focus_areas=focus_list,
        case_id=case_id,
    )
    try:
        config = ReviewerConfig(retrieval_enabled=False)  # W5 简化, 不依赖索引
        review_output = run_skill(ri, config=config)
    except Exception as e:
        logger.exception(f"[contract-review.skill] run_skill failed: {e}")
        raise HTTPException(500, f"contract review failed: {e}")

    latency_ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[contract-review.ocr-upload] engine={engine.name} "
        f"mime={mime} size={len(file_bytes)}B "
        f"ocr_conf={engine_result.confidence:.2f} "
        f"pii_total={pii_report.total} "
        f"clauses={len(review_output.clause_reviews)} "
        f"latency={latency_ms}ms"
    )

    return OcrUploadResponse(
        ocr=OcrInfo(
            confidence=round(engine_result.confidence, 4),
            source_engine=engine_result.source_engine,
            detected_mime=engine_result.detected_mime,
            page_count=engine_result.page_count,
            line_count=len(engine_result.lines),
            raw_text_length=len(engine_result.raw_text),
        ),
        pii=PiiInfo(**pii_report.to_dict()),
        sanitized_text=sanitized_text,
        review=review_output.to_dict(),
        query_meta=review_output.query_meta,
        latency_ms=latency_ms,
        disclaimer=DISCLAIMER_FULL,
        ui_hints=review_output.ui_hints,
    )


# ============================================================
# 规则引擎 API (Rule Engine)
# ============================================================
# 端点:
# - POST /api/contract-review/review-text     文本审查（走规则引擎）
# - GET  /api/contract-review/rules           获取规则列表（按分类分组）
# - PUT  /api/contract-review/rules/{rule_id} 修改规则配置（启用/禁用/权重）
# - POST /api/contract-review/apply-fix       应用一键修复
# ============================================================


class ReviewTextRequest(BaseModel):
    """文本审查请求"""
    contract_text: str = Field(..., min_length=10, max_length=100000, description="合同文本")
    contract_type: str = Field("其他", description="合同类型")
    stance: Optional[str] = Field("审查方", description="立场 (甲方/乙方/丙方/审查方)")


class ReviewTextResponse(BaseModel):
    """文本审查响应"""
    matches: list
    risk_summary: dict
    visualization: dict
    priority_list: list
    suggestions_by_severity: list
    review_time_ms: int
    match_count: int
    disclaimer: str


@router.post("/review-text", response_model=ReviewTextResponse)
async def review_text_endpoint(req: ReviewTextRequest):
    """基于规则引擎的文本审查

    直接使用规则引擎对合同文本进行审查，返回结构化的审查结果。
    不依赖 LLM，纯规则匹配，速度快。
    """
    t0 = time.time()

    try:
        result = review_contract(
            contract_text=req.contract_text,
            contract_type=req.contract_type,
        )
    except Exception as e:
        logger.exception(f"规则引擎审查失败: {e}")
        raise HTTPException(500, f"审查失败: {str(e)}")

    visualization = generate_visualization_data(result.matches)
    priority_list = generate_priority_list(result.matches, top_n=20)
    suggestions_by_severity = [
        g.to_dict() for g in group_suggestions_by_severity(result.matches)
    ]

    latency_ms = int((time.time() - t0) * 1000)

    return ReviewTextResponse(
        matches=[m.to_dict() for m in result.matches],
        risk_summary=result.risk_summary.to_dict(),
        visualization=visualization,
        priority_list=priority_list,
        suggestions_by_severity=suggestions_by_severity,
        review_time_ms=latency_ms,
        match_count=len(result.matches),
        disclaimer=DISCLAIMER_FULL,
    )


class RuleListResponse(BaseModel):
    """规则列表响应"""
    rules: list
    categories: list
    stats: dict


@router.get("/rules", response_model=RuleListResponse)
async def get_rules_endpoint():
    """获取所有内置规则（按分类分组）

    用于前端规则引擎可视化展示。
    """
    manager = get_default_manager()
    all_rules = manager.get_all_rules()

    # 按分类分组
    rules_by_category = {}
    for rule in all_rules:
        cat_name = rule.category.display_name
        if cat_name not in rules_by_category:
            rules_by_category[cat_name] = []
        rules_by_category[cat_name].append(rule.to_dict())

    # 分类列表
    categories = []
    for cat in RuleCategory:
        count = len([r for r in all_rules if r.category == cat])
        if count > 0:
            categories.append({
                "value": cat.value,
                "label": cat.display_name,
                "count": count,
                "enabled_count": len([r for r in all_rules if r.category == cat and r.enabled]),
            })

    stats = manager.rule_count()
    stats["by_severity"] = manager.severity_stats()
    stats["by_category"] = manager.category_stats()

    return RuleListResponse(
        rules=[r.to_dict() for r in all_rules],
        categories=categories,
        stats=stats,
    )


class UpdateRuleRequest(BaseModel):
    """修改规则配置请求"""
    enabled: Optional[bool] = Field(None, description="是否启用")
    weight: Optional[float] = Field(None, ge=0.1, le=10.0, description="权重 (0.1-10.0)")


class UpdateRuleResponse(BaseModel):
    """修改规则配置响应"""
    rule_id: str
    enabled: bool
    weight: float
    success: bool


@router.put("/rules/{rule_id}", response_model=UpdateRuleResponse)
async def update_rule_endpoint(rule_id: str, req: UpdateRuleRequest):
    """修改规则配置（启用/禁用/权重）

    用于演示规则管理功能。生产环境应增加权限校验。
    """
    manager = get_default_manager()
    rule = manager.get_rule(rule_id)

    if not rule:
        raise HTTPException(404, f"规则不存在: {rule_id}")

    if req.enabled is not None:
        if req.enabled:
            manager.enable_rule(rule_id)
        else:
            manager.disable_rule(rule_id)

    if req.weight is not None:
        manager.set_rule_weight(rule_id, req.weight)

    # 重新获取更新后的规则
    rule = manager.get_rule(rule_id)

    return UpdateRuleResponse(
        rule_id=rule_id,
        enabled=rule.enabled,
        weight=rule.weight,
        success=True,
    )


class ApplyFixRequest(BaseModel):
    """一键修复请求"""
    contract_text: str = Field(..., description="原始合同文本")
    matches: list = Field(default_factory=list, description="要修复的匹配结果")
    severity_filter: Optional[str] = Field(None, description="只修复指定严重程度 (high/medium/low/info)")


class ApplyFixResponse(BaseModel):
    """一键修复响应"""
    original_text: str
    fixed_text: str
    applied_count: int
    skipped_count: int
    skipped_reasons: list


@router.post("/apply-fix", response_model=ApplyFixResponse)
async def apply_fix_endpoint(req: ApplyFixRequest):
    """应用一键修复

    对可自动修复的问题应用修改建议。
    """
    from skills.contract_review.rule_engine.models import RuleMatch

    # 构造 RuleMatch 列表（简化版，只取必要字段）
    matches = []
    for m in req.matches:
        try:
            sev = RuleSeverity.from_string(m.get("severity", "info"))
            cat = RuleCategory(m.get("category", "wording"))
            match = RuleMatch(
                rule_id=m.get("rule_id", ""),
                rule_name=m.get("rule_name", ""),
                category=cat,
                severity=sev,
                position=m.get("position", 0),
                length=m.get("length", 0),
                original_text=m.get("original_text", ""),
                problem_description=m.get("problem_description", ""),
                modification_suggestion=m.get("modification_suggestion", ""),
                one_click_fix=m.get("one_click_fix", ""),
                legal_basis=m.get("legal_basis", []),
                confidence=m.get("confidence", 0.8),
            )
            matches.append(match)
        except Exception as e:
            logger.warning(f"解析 match 失败: {e}")
            continue

    severity_filter = None
    if req.severity_filter:
        severity_filter = RuleSeverity.from_string(req.severity_filter)

    result = apply_one_click_fix(
        contract_text=req.contract_text,
        matches=matches,
        severity_filter=severity_filter,
    )

    return ApplyFixResponse(
        original_text=result.original_text,
        fixed_text=result.fixed_text,
        applied_count=result.applied_count,
        skipped_count=result.skipped_count,
        skipped_reasons=result.skipped_reasons,
    )