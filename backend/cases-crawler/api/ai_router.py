"""
LexPrime AI 服务统一 API (FastAPI 路由)
2026-07-03 · Phase 6 AI 服务后端接入

端点:
- POST /api/ai/chat             AI 对话
- POST /api/ai/case-summary     案件摘要
- POST /api/ai/polish           文书润色
- POST /api/ai/auto-fill        智能填空
- GET  /api/ai/health           健康检查
- GET  /api/ai/disclaimer       免责声明

支持 mock 模式: 当 AI 服务不可用时返回模拟数据, 确保前端可联调
"""
from __future__ import annotations

import time
import re
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/ai", tags=["ai-service"])


# ========== 强制免责声明 ==========

DISCLAIMER_FULL = (
    "LexPrime AI 服务输出基于模板规则引擎生成, "
    "仅作为辅助律师处理法律事务的参考, "
    "不构成正式法律意见, 不替代律师专业判断。"
    "具体案件需结合实际情况、客户期望及司法裁判进行评估。"
)

DISCLAIMER_SHORT = (
    "AI 输出仅供参考, 不构成法律意见。"
)

MOCK_MODE = True


# ========== Request / Response Models ==========

class ChatRequest(BaseModel):
    """AI 对话请求"""
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None
    stream: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "message": "帮我起草一份起诉状",
                "conversation_id": "conv-001",
                "stream": False
            }
        }


class ChatResponse(BaseModel):
    """AI 对话响应"""
    reply: str
    conversation_id: str
    disclaimer: str


class CaseSummaryRequest(BaseModel):
    """案件摘要请求"""
    case_name: Optional[str] = ""
    case_number: Optional[str] = ""
    case_type: Optional[str] = ""
    parties: Optional[str] = ""
    plaintiff: Optional[str] = ""
    defendant: Optional[str] = ""
    amount: Optional[str] = ""
    court: Optional[str] = ""
    cause: Optional[str] = ""
    claims: Optional[str] = ""
    facts: Optional[str] = ""
    evidence: Optional[str] = ""
    sign_date: Optional[str] = ""

    class Config:
        json_schema_extra = {
            "example": {
                "case_name": "张三诉李四借款合同纠纷案",
                "case_number": "(2026)京01民初123号",
                "case_type": "借款合同纠纷",
                "plaintiff": "张三",
                "defendant": "李四",
                "amount": "50万元",
                "court": "北京市第一中级人民法院",
                "cause": "借款合同纠纷",
                "claims": "1. 判令被告返还借款本金50万元; 2. 判令被告支付利息",
                "facts": "原被告于2025年3月签订借款合同..."
            }
        }


class CaseSummaryResponse(BaseModel):
    """案件摘要响应"""
    overview: str
    disputes: str
    evidence: str
    risk: str
    next_steps: str
    disclaimer: str


class PolishRequest(BaseModel):
    """文书润色请求"""
    content: str = Field(..., min_length=1, max_length=20000)
    options: Optional[Dict[str, bool]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "content": "借钱不还，打官司告他",
                "options": {
                    "legalTerms": True,
                    "logic": True,
                    "typos": True,
                    "format": True,
                    "tone": False
                }
            }
        }


class PolishDiffItem(BaseModel):
    """润色修改项"""
    original: str
    polished: str
    type: str


class PolishResponse(BaseModel):
    """文书润色响应"""
    polished_content: str
    modifications: List[PolishDiffItem]
    stats: Dict[str, int]
    disclaimer: str


class AutoFillRequest(BaseModel):
    """智能填空请求"""
    template_id: Optional[str] = ""
    case_info: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "complaint-001",
                "case_info": {
                    "plaintiff": "张三",
                    "defendant": "李四",
                    "cause": "借款合同纠纷",
                    "amount": "50万元",
                    "court": "北京市海淀区人民法院"
                }
            }
        }


class AutoFillResponse(BaseModel):
    """智能填空响应"""
    filled_fields: Dict[str, str]
    filled_count: int
    disclaimer: str


# ========== Mock AI Service ==========

def mock_chat_reply(message: str) -> str:
    """生成 mock AI 对话回复"""
    input_text = (message or "").strip().lower()
    if not input_text:
        return "您好！请问有什么可以帮您的？"

    if any(kw in input_text for kw in ["起诉状", "起诉", "诉状"]):
        return (
            "好的！我来帮您起草起诉状。\n\n"
            "为了确保起诉状内容准确, 我需要了解以下信息:\n\n"
            "1. **原被告基本信息**: 姓名/名称、住所地、统一社会信用代码 (法人)\n"
            "2. **诉讼请求**: 例如要求被告支付货款 XX 元及利息\n"
            "3. **事实与理由**: 合同签订时间、主要条款、履行情况、违约事实\n"
            "4. **证据清单**: 合同、付款凭证、对账单、催款函等\n\n"
            "您可以分条告诉我, 也可以直接描述案件情况, "
            "我会按《民事诉讼法》第 122 条规定的起诉条件为您起草。"
        )

    if any(kw in input_text for kw in ["答辩", "应诉"]):
        return (
            "收到答辩状起草请求。答辩状一般包含以下结构:\n\n"
            "1. **答辩人基本信息**\n"
            "2. **案由**: 表明对原告诉讼请求的态度 (承认/反驳)\n"
            "3. **答辩理由**: 针对原告的诉求逐条回应, 并提出自己的主张\n"
            "4. **证据目录**\n"
            "5. **此致**: 写明受诉法院\n\n"
            "请告诉我:\n"
            "- 案件类型 (合同/侵权/婚姻家庭等)\n"
            "- 原告诉求的核心是什么\n"
            "- 您方的事实和理由\n"
            "- 您希望达到什么答辩目标"
        )

    if any(kw in input_text for kw in ["合同", "审查", "风险"]):
        return (
            "合同审查要点如下:\n\n"
            "1. **主体资格**: 核对对方营业执照、资质、法定代表人\n"
            "2. **标的与数量**: 是否明确具体, 避免歧义\n"
            "3. **价款与支付**: 金额、币种、支付方式、账期、违约金\n"
            "4. **履行期限、地点、方式**: 明确可量化的时间节点\n"
            "5. **违约责任**: 逾期违约金比例、损失赔偿计算方式\n"
            "6. **争议解决**: 仲裁 vs 诉讼, 管辖法院约定是否有效\n"
            "7. **不可抗力 / 情势变更**: 是否覆盖疫情、政策变化\n"
            "8. **合同生效、解除、终止条件**\n\n"
            "您可以把合同关键条款贴给我, 我帮您逐条扫描风险点。"
        )

    if any(kw in input_text for kw in ["证据", "举证"]):
        return (
            "证据准备要点:\n\n"
            "**三类核心证据**:\n"
            "1. **当事人主体证据**: 身份证 / 营业执照 / 法定代表人身份证明\n"
            "2. **法律关系证据**: 合同 / 协议 / 章程 / 决议\n"
            "3. **履行/侵权证据**: 履行凭证 / 损失凭证 / 现场照片 / 鉴定报告\n\n"
            "**提交注意**:\n"
            "- 证据清单 + 证明目的\n"
            "- 复印件与原件核对\n"
            "- 对方持有的证据可申请法院调取\n"
            "- 涉及商业秘密可申请不公开质证\n\n"
            "告诉我您的案件类型, 我可以列出针对性的证据清单模板。"
        )

    if any(kw in input_text for kw in ["类案", "判例", "检索"]):
        return (
            "类案检索思路:\n\n"
            "1. **确定案由**: 案由关键词 (如\"买卖合同纠纷\")\n"
            "2. **筛选维度**: 法院层级、审理程序、裁判年份、争议焦点\n"
            "3. **关键词组合**: 主体 + 行为 + 法律关系 + 诉求\n"
            "4. **重点关注**: 最高人民法院指导案例、公报案例、典型案例\n\n"
            "我可以帮您:\n"
            "- 总结某类案件近 3 年的裁判趋势\n"
            "- 提炼特定法院的裁判口径\n"
            "- 检索您手头案件最相似的 5-10 个判例\n\n"
            "请告诉我您想研究的法律问题或争议焦点。"
        )

    if any(kw in input_text for kw in ["你好", "您好", "hi", "hello"]):
        return (
            "您好！我是 LexPrime AI 助手, 可以帮您:\n\n"
            "- 起草法律文书 (起诉状 / 答辩状 / 合同 / 律师函等)\n"
            "- 审查合同风险\n"
            "- 检索类案与法条\n"
            "- 整理证据清单\n"
            "- 分析案件策略\n\n"
            "请问今天想处理什么法律事务?"
        )

    return (
        f"我已收到您的问题:「{message}」\n\n"
        "针对您的提问, 我建议按以下思路处理:\n\n"
        "1. **明确问题核心**: 先把争议焦点拆成 1-2 个核心法律问题\n"
        "2. **查找法律依据**: 检索相关法条 + 类案裁判口径\n"
        "3. **整理事实与证据**: 按时间线梳理, 区分主张与反驳\n"
        "4. **形成方案**: 文书 / 谈判 / 调解 / 诉讼 多种路径组合\n\n"
        "您可以补充更多案件细节, 例如:\n"
        "- 案件类型 (合同 / 侵权 / 婚姻 / 劳动 / 知识产权 等)\n"
        "- 当事人诉求\n"
        "- 当前所处阶段 (协商 / 起诉前 / 已立案 / 审理中)\n\n"
        "我可以进一步帮您出具针对性的方案。"
    )


def mock_case_summary(req: CaseSummaryRequest) -> Dict[str, str]:
    """生成 mock 案件摘要"""
    case_name = req.case_name or "某案件"
    case_type = req.case_type or req.cause or "合同纠纷"
    case_number = req.case_number or "(2026)京01民初XX号"
    court = req.court or "北京市第一中级人民法院"
    amount = req.amount or "XX万元"
    plaintiff = req.plaintiff or "原告"
    defendant = req.defendant or "被告"
    parties = req.parties or f"{plaintiff}与{defendant}"
    sign_date = req.sign_date or "2025年"

    overview = (
        f"**案件概况**\n\n"
        f"本案为{case_type}案件，案号为{case_number}。\n\n"
        f"**当事人情况：**\n"
        f"- {parties}\n"
        f"- 涉案金额：{amount}\n"
        f"- 受理法院：{court}\n\n"
        f"**案件背景：**\n"
        f"原被告双方于{sign_date}签订相关合同，后因履行过程中产生争议，原告遂提起诉讼。"
    )

    disputes = (
        "**争议焦点**\n\n"
        "1. **合同效力问题**：案涉合同是否合法有效，双方权利义务如何认定\n"
        "2. **违约事实认定**：被告是否存在违约行为，违约程度如何\n"
        "3. **损失计算标准**：原告主张的损失金额是否有事实和法律依据\n"
        "4. **责任承担比例**：双方是否均有过错，责任如何划分"
    )

    evidence = (
        "**证据分析**\n\n"
        "**优势证据：**\n"
        "- 书面合同原件，证明双方权利义务关系\n"
        "- 履行凭证（送货单/对账单/转账记录等），证明合同履行情况\n"
        "- 沟通记录（邮件/微信/函件），证明双方协商过程\n\n"
        "**证据薄弱点：**\n"
        "- 部分口头约定缺乏书面佐证\n"
        "- 损失计算依据需进一步补强\n"
        "- 部分证据形成时间存在疑点"
    )

    risk = (
        "**风险评估**\n\n"
        "**诉讼风险（中等偏高）：**\n"
        "- 事实认定风险：部分事实缺乏直接证据支持\n"
        "- 法律适用风险：相关法律条款存在解释空间\n"
        "- 执行风险：被告偿付能力需进一步调查\n\n"
        "**建议应对：**\n"
        "- 补充关键证据，形成完整证据链\n"
        "- 申请财产保全，确保判决可执行\n"
        "- 做好调解预案，降低诉讼成本"
    )

    next_steps = (
        "**下一步建议**\n\n"
        "1. **证据补强**（3日内）：补充完善关键证据，特别是损失计算依据\n"
        "2. **保全申请**（5日内）：向法院申请财产保全，查封被告银行账户及资产\n"
        "3. **庭前准备**（开庭前）：准备质证意见、代理词、答辩预案\n"
        "4. **调解策略**：在诉讼过程中保持调解渠道，争取最优解决方案\n"
        "5. **执行预案**：提前调查被告财产线索，为执行阶段做准备"
    )

    return {
        "overview": overview,
        "disputes": disputes,
        "evidence": evidence,
        "risk": risk,
        "next_steps": next_steps
    }


def mock_polish(content: str, options: Dict[str, bool]) -> Dict[str, Any]:
    """mock 文书润色"""
    opts = options or {}
    result = content
    modifications = []

    legal_terms_map = [
        ("借钱", "借款"),
        ("欠钱", "拖欠款项"),
        ("不给钱", "拒不支付"),
        ("说好了", "约定"),
        ("答应", "承诺"),
        ("打官司", "提起诉讼"),
        ("告他", "追究其法律责任"),
        ("差不多", "大致相当"),
        ("大概", "约计"),
    ]

    typos_map = [
        ("做为", "作为"),
        ("签定", "签订"),
        ("帐号", "账号"),
        ("帐户", "账户"),
        ("其它", "其他"),
    ]

    logic_map = [
        ("因此，", "综上所述，"),
        ("因为", "鉴于"),
        ("所以", "故"),
    ]

    tone_map = [
        ("你方", "贵方"),
        ("我们", "我方"),
        ("你公司", "贵司"),
        ("我公司", "我司"),
    ]

    if opts.get("legalTerms", True):
        for orig, pol in legal_terms_map:
            if orig in result:
                count = result.count(orig)
                result = result.replace(orig, pol)
                modifications.append({
                    "original": orig,
                    "polished": pol,
                    "type": "legal_terms"
                })

    if opts.get("typos", True):
        for orig, pol in typos_map:
            if orig in result:
                result = result.replace(orig, pol)
                modifications.append({
                    "original": orig,
                    "polished": pol,
                    "type": "typo"
                })

    if opts.get("logic", True):
        for orig, pol in logic_map:
            if orig in result:
                result = result.replace(orig, pol)
                modifications.append({
                    "original": orig,
                    "polished": pol,
                    "type": "logic"
                })

    if opts.get("tone", False):
        for orig, pol in tone_map:
            if orig in result:
                result = result.replace(orig, pol)
                modifications.append({
                    "original": orig,
                    "polished": pol,
                    "type": "tone"
                })

    if opts.get("format", True):
        result = re.sub(r'\n{3,}', '\n\n', result)
        result = re.sub(r'[ \t]+$', '', result, flags=re.MULTILINE)
        result = re.sub(r'^[ \t]+', '', result, flags=re.MULTILINE)

    stats = {
        "total_modifications": len(modifications),
        "legal_terms": sum(1 for m in modifications if m["type"] == "legal_terms"),
        "typos": sum(1 for m in modifications if m["type"] == "typo"),
        "logic": sum(1 for m in modifications if m["type"] == "logic"),
        "tone": sum(1 for m in modifications if m["type"] == "tone"),
    }

    return {
        "polished_content": result,
        "modifications": modifications,
        "stats": stats
    }


def mock_auto_fill(template_id: str, case_info: Dict[str, Any]) -> Dict[str, Any]:
    """mock 智能填空"""
    info = case_info or {}
    filled = {}

    field_mappings = {
        "plaintiff": ["plaintiff", "原告", "client_name"],
        "defendant": ["defendant", "被告", "opponent_name"],
        "cause": ["cause", "案由", "case_type"],
        "amount": ["amount", "标的金额", "claim_amount"],
        "court": ["court", "受理法院", "court_name"],
        "phone": ["phone", "联系电话"],
        "legalRep": ["legalRep", "法定代表人", "legal_rep"],
        "claims": ["claims", "诉讼请求"],
        "facts": ["facts", "事实与理由"],
    }

    for target_field, source_keys in field_mappings.items():
        for key in source_keys:
            if key in info and info[key]:
                filled[target_field] = str(info[key])
                break

    return {
        "filled_fields": filled,
        "filled_count": len(filled)
    }


# ========== 端点 ==========

@router.get("/health")
async def ai_health():
    """AI 服务健康检查"""
    return {
        "status": "ok",
        "service": "lexprime-ai-service",
        "version": "1.0.0",
        "mock_mode": MOCK_MODE,
        "endpoints": [
            {"path": "/api/ai/chat", "method": "POST", "purpose": "AI 对话"},
            {"path": "/api/ai/case-summary", "method": "POST", "purpose": "案件摘要"},
            {"path": "/api/ai/polish", "method": "POST", "purpose": "文书润色"},
            {"path": "/api/ai/auto-fill", "method": "POST", "purpose": "智能填空"},
        ],
        "features": [
            "case_summary",
            "document_polish",
            "auto_fill",
            "chat",
        ]
    }


@router.get("/disclaimer")
async def ai_disclaimer():
    """返回强制免责声明"""
    return {
        "full": DISCLAIMER_FULL,
        "short": DISCLAIMER_SHORT,
    }


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(req: ChatRequest):
    """AI 对话接口

    输入: 用户消息 + 可选对话历史
    输出: AI 回复 + 对话ID
    """
    t0 = time.time()

    try:
        reply = mock_chat_reply(req.message)
        conversation_id = req.conversation_id or f"conv-{int(time.time())}"

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"AI chat request processed in {latency_ms}ms, mock_mode={MOCK_MODE}")

        return ChatResponse(
            reply=reply,
            conversation_id=conversation_id,
            disclaimer=DISCLAIMER_FULL
        )
    except Exception as e:
        logger.exception(f"AI chat failed: {e}")
        raise HTTPException(500, f"AI 对话服务异常: {str(e)}")


@router.post("/case-summary", response_model=CaseSummaryResponse)
async def ai_case_summary(req: CaseSummaryRequest):
    """案件摘要接口

    输入: 案件基本信息（当事人、案由、诉讼请求、事实理由等）
    输出: 案件概况、争议焦点、证据分析、风险评估、下一步建议
    """
    t0 = time.time()

    try:
        summary = mock_case_summary(req)

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"AI case summary processed in {latency_ms}ms, mock_mode={MOCK_MODE}")

        return CaseSummaryResponse(
            overview=summary["overview"],
            disputes=summary["disputes"],
            evidence=summary["evidence"],
            risk=summary["risk"],
            next_steps=summary["next_steps"],
            disclaimer=DISCLAIMER_FULL
        )
    except Exception as e:
        logger.exception(f"AI case summary failed: {e}")
        raise HTTPException(500, f"案件摘要服务异常: {str(e)}")


@router.post("/polish", response_model=PolishResponse)
async def ai_polish(req: PolishRequest):
    """文书润色接口

    输入: content + options（法律用语/逻辑优化/错别字/格式统一/语气调整）
    输出: 润色后内容、修改列表
    """
    t0 = time.time()

    try:
        result = mock_polish(req.content, req.options or {})

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"AI polish processed in {latency_ms}ms, "
            f"modifications={result['stats']['total_modifications']}, "
            f"mock_mode={MOCK_MODE}"
        )

        return PolishResponse(
            polished_content=result["polished_content"],
            modifications=[PolishDiffItem(**m) for m in result["modifications"]],
            stats=result["stats"],
            disclaimer=DISCLAIMER_FULL
        )
    except Exception as e:
        logger.exception(f"AI polish failed: {e}")
        raise HTTPException(500, f"文书润色服务异常: {str(e)}")


@router.post("/auto-fill", response_model=AutoFillResponse)
async def ai_auto_fill(req: AutoFillRequest):
    """智能填空接口

    输入: template_id + case_info
    输出: 填充后的字段键值对
    """
    t0 = time.time()

    try:
        result = mock_auto_fill(req.template_id, req.case_info)

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"AI auto-fill processed in {latency_ms}ms, "
            f"filled={result['filled_count']} fields, "
            f"mock_mode={MOCK_MODE}"
        )

        return AutoFillResponse(
            filled_fields=result["filled_fields"],
            filled_count=result["filled_count"],
            disclaimer=DISCLAIMER_FULL
        )
    except Exception as e:
        logger.exception(f"AI auto-fill failed: {e}")
        raise HTTPException(500, f"智能填空服务异常: {str(e)}")
