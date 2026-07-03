"""
LexPrime 多文档摘要和对比 API
================================

支持多文档上传、对比分析、综合摘要等功能。
支持 PDF、Word、文本格式。

端点:
- POST /api/doc/compare          文档对比
- POST /api/doc/summarize-multi  多文档摘要
- GET  /api/doc/health           健康检查

支持 mock 模式: 返回模拟分析数据
"""
from __future__ import annotations

import time
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from loguru import logger
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/doc", tags=["doc-compare"])

MOCK_MODE = True

DISCLAIMER_FULL = (
    "LexPrime 文档对比和摘要功能基于 AI 智能分析，"
    "结果仅供参考，不构成法律意见。"
    "建议由专业律师进行审核和确认。"
)


# ========== Request / Response Models ==========

class DocItem(BaseModel):
    """文档项"""
    id: str
    name: str
    type: str
    size: int
    content: Optional[str] = None


class CompareRequest(BaseModel):
    """文档对比请求"""
    documents: List[DocItem]
    compare_type: Optional[str] = "contract"
    focus_areas: Optional[List[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "documents": [
                    {"id": "doc1", "name": "合同版本A.docx", "type": "docx", "size": 50000},
                    {"id": "doc2", "name": "合同版本B.docx", "type": "docx", "size": 52000}
                ],
                "compare_type": "contract",
                "focus_areas": ["价格条款", "违约责任", "保密条款"]
            }
        }


class DiffItem(BaseModel):
    """差异项"""
    section: str
    type: str
    doc1_content: str
    doc2_content: str
    severity: str
    description: str


class SamePoint(BaseModel):
    """相同点"""
    section: str
    content: str
    description: str


class DisputePoint(BaseModel):
    """争议焦点"""
    title: str
    description: str
    relevance: float
    related_clauses: List[str]


class CompareResponse(BaseModel):
    """文档对比响应"""
    doc1_name: str
    doc2_name: str
    similarities: List[SamePoint]
    differences: List[DiffItem]
    dispute_points: List[DisputePoint]
    summary: str
    stats: Dict[str, Any]
    disclaimer: str


class MultiSummarizeRequest(BaseModel):
    """多文档摘要请求"""
    documents: List[DocItem]
    summary_type: Optional[str] = "comprehensive"
    max_length: Optional[int] = 2000

    class Config:
        json_schema_extra = {
            "example": {
                "documents": [
                    {"id": "doc1", "name": "判决书A.docx", "type": "docx", "size": 80000},
                    {"id": "doc2", "name": "判决书B.docx", "type": "docx", "size": 75000}
                ],
                "summary_type": "comprehensive",
                "max_length": 2000
            }
        }


class DocSummary(BaseModel):
    """单文档摘要"""
    doc_id: str
    doc_name: str
    summary: str
    key_points: List[str]


class MultiSummarizeResponse(BaseModel):
    """多文档摘要响应"""
    comprehensive_summary: str
    individual_summaries: List[DocSummary]
    common_themes: List[str]
    key_findings: List[str]
    disclaimer: str


# ========== Mock Data ==========

def mock_compare(req: CompareRequest) -> Dict[str, Any]:
    """生成 mock 文档对比结果"""
    doc1_name = req.documents[0].name if req.documents else "文档1"
    doc2_name = req.documents[1].name if len(req.documents) > 1 else "文档2"

    similarities = [
        {
            "section": "合同主体",
            "content": "双方均对甲乙双方的主体信息进行了约定，包括名称、地址、法定代表人等基本信息。",
            "description": "两份合同均明确约定了合同双方的基本信息，主体条款一致。"
        },
        {
            "section": "保密义务",
            "content": "双方均负有保密义务，不得向第三方披露商业秘密。",
            "description": "保密条款的基本原则和义务范围基本一致。"
        },
        {
            "section": "争议解决",
            "content": "均约定协商不成时通过诉讼方式解决争议。",
            "description": "争议解决方式均约定为诉讼，基本原则相同。"
        }
    ]

    differences = [
        {
            "section": "合同金额",
            "type": "price",
            "doc1_content": "合同总金额为人民币 50 万元整。",
            "doc2_content": "合同总金额为人民币 55 万元整。",
            "severity": "high",
            "description": "合同总金额增加了 5 万元，增幅 10%，属于重大变更。"
        },
        {
            "section": "付款方式",
            "type": "payment",
            "doc1_content": "合同签订后支付 30% 预付款，验收合格后支付 65%，质保金 5%。",
            "doc2_content": "合同签订后支付 50% 预付款，验收合格后支付 45%，质保金 5%。",
            "severity": "medium",
            "description": "预付款比例从 30% 提高到 50%，对收款方更有利。"
        },
        {
            "section": "交付期限",
            "type": "time",
            "doc1_content": "乙方应在合同签订后 30 日内完成交付。",
            "doc2_content": "乙方应在合同签订后 45 日内完成交付。",
            "severity": "medium",
            "description": "交付期限延长了 15 天，需评估对项目进度的影响。"
        },
        {
            "section": "违约金比例",
            "type": "penalty",
            "doc1_content": "逾期交付的，每日按合同总金额的 0.1% 支付违约金。",
            "doc2_content": "逾期交付的，每日按合同总金额的 0.05% 支付违约金。",
            "severity": "high",
            "description": "违约金比例降低了 50%，违约责任明显减轻。"
        },
        {
            "section": "质保期",
            "type": "warranty",
            "doc1_content": "质保期为验收合格后 12 个月。",
            "doc2_content": "质保期为验收合格后 24 个月。",
            "severity": "medium",
            "description": "质保期延长了一倍，增加了乙方的质量责任。"
        },
        {
            "section": "管辖法院",
            "type": "jurisdiction",
            "doc1_content": "由甲方所在地人民法院管辖。",
            "doc2_content": "由合同签订地人民法院管辖。",
            "severity": "low",
            "description": "管辖法院约定有所变化，需确认合同签订地位置。"
        }
    ]

    dispute_points = [
        {
            "title": "合同价款变更",
            "description": "两份合同在总金额上存在 5 万元的差异，需确认变更原因及是否合理。",
            "relevance": 0.95,
            "related_clauses": ["第一条 合同标的", "第二条 合同价款"]
        },
        {
            "title": "付款条件调整",
            "description": "预付款比例从 30% 提高到 50%，可能影响甲方的资金安排和风险控制。",
            "relevance": 0.85,
            "related_clauses": ["第三条 付款方式", "第四条 付款进度"]
        },
        {
            "title": "违约责任不对等",
            "description": "违约金比例降低，可能导致乙方违约成本下降，需评估风险。",
            "relevance": 0.90,
            "related_clauses": ["第七条 违约责任", "第八条 逾期责任"]
        }
    ]

    summary = (
        f"经对比分析，《{doc1_name}》与《{doc2_name}》在整体结构和主要条款上基本一致，"
        "但在合同金额、付款方式、交付期限、违约责任等方面存在重要差异。\n\n"
        "**主要相同点**：合同主体、保密义务、争议解决方式等核心条款基本一致。\n\n"
        "**主要差异点**：\n"
        "1. 合同金额增加 5 万元（+10%）\n"
        "2. 预付款比例从 30% 提高到 50%\n"
        "3. 交付期限延长 15 天\n"
        "4. 违约金比例降低 50%\n"
        "5. 质保期从 12 个月延长到 24 个月\n\n"
        "**风险提示**：违约金比例的大幅降低可能增加乙方违约的道德风险，"
        "建议审慎评估此变更的必要性和风险。"
    )

    stats = {
        "total_sections_compared": 15,
        "same_sections": 8,
        "different_sections": 5,
        "new_sections": 1,
        "removed_sections": 1,
        "high_risk_diffs": 2,
        "medium_risk_diffs": 3,
        "low_risk_diffs": 1,
        "similarity_score": 72.5
    }

    return {
        "doc1_name": doc1_name,
        "doc2_name": doc2_name,
        "similarities": similarities,
        "differences": differences,
        "dispute_points": dispute_points,
        "summary": summary,
        "stats": stats
    }


def mock_multi_summarize(req: MultiSummarizeRequest) -> Dict[str, Any]:
    """生成 mock 多文档摘要"""
    individual_summaries = []
    common_themes = [
        "合同违约责任认定",
        "损害赔偿计算标准",
        "合同履行抗辩权",
        "证据认定规则"
    ]
    key_findings = [
        "两份判决均支持了原告的主要诉讼请求",
        "违约金调整均以实际损失为基础",
        "法院均适用了《民法典》相关条款",
        "举证责任分配遵循'谁主张谁举证'原则"
    ]

    for i, doc in enumerate(req.documents):
        key_points = [
            "案件基本事实认定清楚，证据充分",
            "法院适用法律正确，程序合法",
            "判决支持了原告的主要诉讼请求",
            "被告需承担违约责任并赔偿损失"
        ]

        summary = (
            f"《{doc.name}》一案，法院经审理查明：原告与被告签订合同后，"
            "原告按约履行了义务，但被告未按约定履行付款义务，已构成违约。"
            "法院认为，原被告之间的合同关系合法有效，双方均应按约履行。"
            "被告未按约定支付款项，应承担相应的违约责任。"
            "最终判决被告支付原告货款及违约金，并承担本案诉讼费用。"
        )

        individual_summaries.append({
            "doc_id": doc.id,
            "doc_name": doc.name,
            "summary": summary,
            "key_points": key_points
        })

    comprehensive_summary = (
        "## 多文档综合摘要\n\n"
        "本次共分析 " + str(len(req.documents)) + " 份法律文书，均涉及合同纠纷类案件。\n\n"
        "### 一、案件共性\n\n"
        "1. **法律关系**：均为合同纠纷，涉及买卖合同、服务合同等类型\n"
        "2. **争议焦点**：主要集中在违约责任认定、损害赔偿计算等方面\n"
        "3. **法律适用**：均适用《民法典》合同编相关规定\n"
        "4. **裁判结果**：原告的主要诉讼请求均得到法院支持\n\n"
        "### 二、核心观点\n\n"
        "1. 合同依法成立并生效，对双方具有法律约束力\n"
        "2. 一方不履行合同义务的，应当承担违约责任\n"
        "3. 违约金以补偿性为主，惩罚性为辅\n"
        "4. 当事人对自己的主张有责任提供证据\n\n"
        "### 三、实务启示\n\n"
        "1. 合同条款应明确具体，避免模糊表述\n"
        "2. 注意保存履行证据，包括书面文件、沟通记录等\n"
        "3. 违约金约定应合理，过高可能被法院调整\n"
        "4. 发生争议后及时主张权利，避免超过诉讼时效"
    )

    return {
        "comprehensive_summary": comprehensive_summary,
        "individual_summaries": individual_summaries,
        "common_themes": common_themes,
        "key_findings": key_findings
    }


# ========== 端点 ==========

@router.get("/health")
async def doc_health():
    """文档对比和摘要服务健康检查"""
    return {
        "status": "ok",
        "service": "lexprime-doc-compare",
        "version": "1.0.0",
        "mock_mode": MOCK_MODE,
        "features": [
            "multi_document_compare",
            "similarity_analysis",
            "difference_detection",
            "dispute_point_identification",
            "multi_document_summary",
            "common_theme_extraction"
        ],
        "supported_formats": ["pdf", "docx", "doc", "txt"],
        "endpoints": [
            {"path": "/api/doc/compare", "method": "POST", "purpose": "文档对比"},
            {"path": "/api/doc/summarize-multi", "method": "POST", "purpose": "多文档摘要"}
        ]
    }


@router.post("/compare", response_model=CompareResponse)
async def compare_documents(req: CompareRequest):
    """文档对比接口

    输入: 多份文档 + 对比类型 + 关注领域
    输出: 相同点、不同点、争议焦点、对比摘要
    """
    t0 = time.time()

    try:
        if not req.documents or len(req.documents) < 2:
            raise HTTPException(400, "请至少上传两份文档进行对比")

        result = mock_compare(req)

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Document compare processed in {latency_ms}ms, "
            f"docs={len(req.documents)}, "
            f"diffs={len(result['differences'])}, "
            f"mock_mode={MOCK_MODE}"
        )

        return CompareResponse(
            doc1_name=result["doc1_name"],
            doc2_name=result["doc2_name"],
            similarities=[SamePoint(**s) for s in result["similarities"]],
            differences=[DiffItem(**d) for d in result["differences"]],
            dispute_points=[DisputePoint(**dp) for dp in result["dispute_points"]],
            summary=result["summary"],
            stats=result["stats"],
            disclaimer=DISCLAIMER_FULL
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Document compare failed: {e}")
        raise HTTPException(500, f"文档对比服务异常: {str(e)}")


@router.post("/summarize-multi", response_model=MultiSummarizeResponse)
async def summarize_multi_documents(req: MultiSummarizeRequest):
    """多文档摘要接口

    输入: 多份文档 + 摘要类型 + 最大长度
    输出: 综合摘要 + 各文档摘要 + 共同主题 + 核心发现
    """
    t0 = time.time()

    try:
        if not req.documents or len(req.documents) == 0:
            raise HTTPException(400, "请至少上传一份文档")

        result = mock_multi_summarize(req)

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Multi-doc summarize processed in {latency_ms}ms, "
            f"docs={len(req.documents)}, "
            f"mock_mode={MOCK_MODE}"
        )

        return MultiSummarizeResponse(
            comprehensive_summary=result["comprehensive_summary"],
            individual_summaries=[DocSummary(**ds) for ds in result["individual_summaries"]],
            common_themes=result["common_themes"],
            key_findings=result["key_findings"],
            disclaimer=DISCLAIMER_FULL
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Multi-doc summarize failed: {e}")
        raise HTTPException(500, f"多文档摘要服务异常: {str(e)}")
