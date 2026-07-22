"""
LexPrime 智能法律问答 API (RAG 架构)
====================================

基于 RAG (Retrieval-Augmented Generation) 架构的法律问答系统，
支持自然语言提问，检索判例库和法规库，返回引用来源。

端点:
- POST /api/ai/qa            法律问答
- GET  /api/ai/qa/history    历史记录
- GET  /api/ai/qa/hot        热门问题
- GET  /api/ai/qa/health     健康检查

支持 mock 模式: 当 AI 服务不可用时返回模拟数据，确保前端可联调
"""
from __future__ import annotations

import time
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/ai/qa", tags=["ai-qa"])

MOCK_MODE = True

DISCLAIMER_FULL = (
    "LexPrime AI 法律问答基于检索增强生成 (RAG) 技术，"
    "引用判例和法规仅供参考，不构成正式法律意见，"
    "不替代律师专业判断。具体案件需结合实际情况评估。"
)

DISCLAIMER_SHORT = "AI 回答仅供参考，不构成法律意见。"


# ========== Request / Response Models ==========

class QARequest(BaseModel):
    """法律问答请求"""
    question: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None
    sources: Optional[List[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "question": "民间借贷利息最高可以约定多少？",
                "conversation_id": "qa-conv-001",
                "sources": ["cases", "laws"]
            }
        }


class QACitation(BaseModel):
    """引用来源"""
    type: str
    title: str
    reference: str
    snippet: str
    url: Optional[str] = None


class QAResponse(BaseModel):
    """法律问答响应"""
    answer: str
    conversation_id: str
    citations: List[QACitation]
    related_questions: List[str]
    disclaimer: str


class QAHistoryItem(BaseModel):
    """历史记录项"""
    id: str
    title: str
    question: str
    answer_preview: str
    created_at: str
    message_count: int


class QAHistoryResponse(BaseModel):
    """历史记录响应"""
    items: List[QAHistoryItem]
    total: int


class HotQuestion(BaseModel):
    """热门问题"""
    id: str
    question: str
    category: str
    view_count: int


class HotQuestionsResponse(BaseModel):
    """热门问题响应"""
    items: List[HotQuestion]
    categories: List[str]


# ========== Mock Data ==========

MOCK_HOT_QUESTIONS = [
    {
        "id": "hq-001",
        "question": "民间借贷利息最高可以约定多少？",
        "category": "借贷纠纷",
        "view_count": 1256
    },
    {
        "id": "hq-002",
        "question": "劳动合同到期不续签有赔偿吗？",
        "category": "劳动争议",
        "view_count": 987
    },
    {
        "id": "hq-003",
        "question": "离婚时夫妻共同财产如何分割？",
        "category": "婚姻家庭",
        "view_count": 876
    },
    {
        "id": "hq-004",
        "question": "开发商逾期交房怎么维权？",
        "category": "房产纠纷",
        "view_count": 765
    },
    {
        "id": "hq-005",
        "question": "交通事故赔偿标准是怎样的？",
        "category": "侵权责任",
        "view_count": 654
    },
    {
        "id": "hq-006",
        "question": "公司股东知情权如何行使？",
        "category": "公司法律",
        "view_count": 543
    },
    {
        "id": "hq-007",
        "question": "合同违约金过高可以调整吗？",
        "category": "合同纠纷",
        "view_count": 432
    },
    {
        "id": "hq-008",
        "question": "盗窃罪立案标准是多少？",
        "category": "刑事辩护",
        "view_count": 321
    }
]

MOCK_HISTORY = [
    {
        "id": "qa-conv-001",
        "title": "民间借贷利息计算",
        "question": "民间借贷利息最高可以约定多少？",
        "answer_preview": "根据《最高人民法院关于审理民间借贷案件适用法律若干问题的规定》...",
        "created_at": "2026-07-02 14:30",
        "message_count": 5
    },
    {
        "id": "qa-conv-002",
        "title": "劳动合同赔偿",
        "question": "公司违法解除劳动合同怎么赔偿？",
        "answer_preview": "根据《劳动合同法》第87条规定，用人单位违反本法规定解除或者终止劳动合同的...",
        "created_at": "2026-07-01 10:15",
        "message_count": 3
    },
    {
        "id": "qa-conv-003",
        "title": "离婚财产分割",
        "question": "离婚时房产怎么分？",
        "answer_preview": "离婚时房产分割需要考虑多种因素，包括购房时间、出资情况、登记情况等...",
        "created_at": "2026-06-28 16:45",
        "message_count": 7
    }
]


def mock_qa_answer(question: str) -> Dict[str, Any]:
    """生成 mock 问答回答"""
    q = (question or "").strip().lower()

    citations = []
    related_questions = []

    if any(kw in q for kw in ["利息", "利率", "lpr", "民间借贷"]):
        answer = (
            "## 民间借贷利息法律规定\n\n"
            "根据现行法律规定，民间借贷利息遵循以下规则：\n\n"
            "### 1. 利率上限\n\n"
            "出借人请求借款人按照合同约定利率支付利息的，人民法院应予支持，"
            "**但是双方约定的利率超过合同成立时一年期贷款市场报价利率（LPR）四倍的除外**。\n\n"
            "### 2. LPR 参考标准\n\n"
            "以 2026 年 7 月为例，一年期 LPR 为 3.45%，因此民间借贷利率上限为：\n"
            "- **年利率上限：13.8%**（3.45% × 4）\n"
            "- 超出部分不受法律保护\n\n"
            "### 3. 逾期利息\n\n"
            "借贷双方对逾期利率有约定的，从其约定，但是以不超过合同成立时一年期 LPR 四倍为限。\n\n"
            "未约定逾期利率或者约定不明的，人民法院可以区分不同情况处理：\n"
            "- 既未约定借期内利率，也未约定逾期利率，出借人主张借款人自逾期还款之日起参照当时一年期 LPR 标准计算的利息承担逾期还款违约责任的，人民法院应予支持\n"
            "- 约定了借期内利率但是未约定逾期利率，出借人主张借款人自逾期还款之日起按照借期内利率支付资金占用期间利息的，人民法院应予支持\n\n"
            "### 4. 复利限制\n\n"
            "借贷双方对前期借款本息结算后将利息计入后期借款本金并重新出具债权凭证，"
            "如果前期利率没有超过合同成立时一年期 LPR 四倍，重新出具的债权凭证载明的金额可认定为后期借款本金。"
            "超过部分的利息，不应认定为后期借款本金。"
        )
        citations = [
            {
                "type": "law",
                "title": "最高人民法院关于审理民间借贷案件适用法律若干问题的规定",
                "reference": "第25条",
                "snippet": "出借人请求借款人按照合同约定利率支付利息的，人民法院应予支持，但是双方约定的利率超过合同成立时一年期贷款市场报价利率四倍的除外。",
                "url": None
            },
            {
                "type": "law",
                "title": "最高人民法院关于审理民间借贷案件适用法律若干问题的规定",
                "reference": "第28条",
                "snippet": "借贷双方对逾期利率有约定的，从其约定，但是以不超过合同成立时一年期贷款市场报价利率四倍为限。",
                "url": None
            },
            {
                "type": "case",
                "title": "张三诉李四民间借贷纠纷案",
                "reference": "(2025)京01民初123号",
                "snippet": "本案中，双方约定的年利率为18%，超过了合同成立时一年期LPR四倍的上限，对超出部分本院不予支持。",
                "url": "/cases/case-abc123"
            }
        ]
        related_questions = [
            "逾期利息怎么计算？",
            "借条没有约定利息怎么办？",
            "复利合法吗？",
            "已支付的超额利息能要回吗？"
        ]
    elif any(kw in q for kw in ["劳动合同", "解除", "赔偿", "经济补偿"]):
        answer = (
            "## 劳动合同解除赔偿标准\n\n"
            "用人单位解除劳动合同的赔偿标准，根据解除原因不同而有所区别：\n\n"
            "### 1. 违法解除赔偿金（2N）\n\n"
            "用人单位违反《劳动合同法》规定解除或者终止劳动合同的，应当依照经济补偿标准的**二倍**向劳动者支付赔偿金。\n\n"
            "### 2. 经济补偿金（N）\n\n"
            "有下列情形之一的，用人单位应当向劳动者支付经济补偿：\n"
            "- 劳动者依照本法第三十八条规定解除劳动合同的\n"
            "- 用人单位依照本法第三十六条规定向劳动者提出解除劳动合同并与劳动者协商一致解除劳动合同的\n"
            "- 用人单位依照本法第四十条规定解除劳动合同的\n"
            "- 用人单位依照本法第四十一条第一款规定解除劳动合同的\n"
            "- 除用人单位维持或者提高劳动合同约定条件续订劳动合同，劳动者不同意续订的情形外，依照本法第四十四条第一项规定终止固定期限劳动合同的\n\n"
            "### 3. 经济补偿计算\n\n"
            "经济补偿按劳动者在本单位工作的年限：\n"
            "- **每满一年支付一个月工资**的标准向劳动者支付\n"
            "- 六个月以上不满一年的，按一年计算\n"
            "- 不满六个月的，向劳动者支付**半个月工资**的经济补偿\n\n"
            "劳动者月工资高于用人单位所在直辖市、设区的市级人民政府公布的本地区上年度职工月平均工资三倍的，"
            "向其支付经济补偿的标准按职工月平均工资三倍的数额支付，向其支付经济补偿的年限最高不超过十二年。\n\n"
            "### 4. 代通知金（+1）\n\n"
            "有下列情形之一的，用人单位提前三十日以书面形式通知劳动者本人或者额外支付劳动者一个月工资后，可以解除劳动合同：\n"
            "- 劳动者患病或者非因工负伤，在规定的医疗期满后不能从事原工作，也不能从事由用人单位另行安排的工作的\n"
            "- 劳动者不能胜任工作，经过培训或者调整工作岗位，仍不能胜任工作的\n"
            "- 劳动合同订立时所依据的客观情况发生重大变化，致使劳动合同无法履行，经用人单位与劳动者协商，未能就变更劳动合同内容达成协议的"
        )
        citations = [
            {
                "type": "law",
                "title": "中华人民共和国劳动合同法",
                "reference": "第47条",
                "snippet": "经济补偿按劳动者在本单位工作的年限，每满一年支付一个月工资的标准向劳动者支付。六个月以上不满一年的，按一年计算；不满六个月的，向劳动者支付半个月工资的经济补偿。",
                "url": None
            },
            {
                "type": "law",
                "title": "中华人民共和国劳动合同法",
                "reference": "第87条",
                "snippet": "用人单位违反本法规定解除或者终止劳动合同的，应当依照本法第四十七条规定的经济补偿标准的二倍向劳动者支付赔偿金。",
                "url": None
            },
            {
                "type": "case",
                "title": "王五诉某科技公司劳动争议案",
                "reference": "(2025)京03民终456号",
                "snippet": "关于违法解除劳动合同的赔偿金，本院认为，用人单位未能举证证明其解除行为的合法性，应当依照劳动合同法第八十七条的规定支付赔偿金。",
                "url": "/cases/case-def456"
            }
        ]
        related_questions = [
            "试用期被辞退有赔偿吗？",
            "公司裁员怎么赔偿？",
            "被动离职和主动离职的区别？",
            "赔偿金要交个税吗？"
        ]
    elif any(kw in q for kw in ["离婚", "财产分割", "夫妻共同财产"]):
        answer = (
            "## 离婚财产分割法律规定\n\n"
            "离婚时，夫妻共同财产的分割遵循以下原则和规则：\n\n"
            "### 1. 夫妻共同财产范围\n\n"
            "夫妻在婚姻关系存续期间所得的下列财产，为夫妻的共同财产，归夫妻共同所有：\n"
            "- 工资、奖金、劳务报酬\n"
            "- 生产、经营、投资的收益\n"
            "- 知识产权的收益\n"
            "- 继承或者受赠的财产（但遗嘱或者赠与合同中确定只归一方的财产除外）\n"
            "- 其他应当归共同所有的财产\n\n"
            "### 2. 个人财产范围\n\n"
            "下列财产为夫妻一方的个人财产：\n"
            "- 一方的婚前财产\n"
            "- 一方因受到人身损害获得的赔偿或者补偿\n"
            "- 遗嘱或者赠与合同中确定只归一方的财产\n"
            "- 一方专用的生活用品\n"
            "- 其他应当归一方的财产\n\n"
            "### 3. 分割原则\n\n"
            "离婚时，夫妻的共同财产由双方协议处理；协议不成的，由人民法院根据财产的具体情况，"
            "按照**照顾子女、女方和无过错方权益**的原则判决。\n\n"
            "### 4. 房产分割特殊规则\n\n"
            "房产分割是离婚财产分割中的重点和难点，常见情形包括：\n"
            "- **婚前全款购房**：属于个人财产，不参与分割\n"
            "- **婚前贷款购房，婚后共同还贷**：房产归登记方所有，婚后共同还贷及增值部分由登记方对另一方进行补偿\n"
            "- **婚后购房**：属于夫妻共同财产，原则上均等分割\n"
            "- **父母出资购房**：根据出资时间、登记情况、是否明确赠与等因素综合判断"
        )
        citations = [
            {
                "type": "law",
                "title": "中华人民共和国民法典",
                "reference": "第1062条",
                "snippet": "夫妻在婚姻关系存续期间所得的下列财产，为夫妻的共同财产，归夫妻共同所有：（一）工资、奖金、劳务报酬；（二）生产、经营、投资的收益...",
                "url": None
            },
            {
                "type": "law",
                "title": "中华人民共和国民法典",
                "reference": "第1087条",
                "snippet": "离婚时，夫妻的共同财产由双方协议处理；协议不成的，由人民法院根据财产的具体情况，按照照顾子女、女方和无过错方权益的原则判决。",
                "url": None
            },
            {
                "type": "case",
                "title": "赵六诉钱七离婚纠纷案",
                "reference": "(2025)沪01民终789号",
                "snippet": "关于涉案房屋的分割，本院认为，该房屋系被告婚前签订买卖合同，以个人财产支付首付款并在银行贷款，婚后用夫妻共同财产还贷，不动产登记于被告名下...",
                "url": "/cases/case-ghi789"
            }
        ]
        related_questions = [
            "婚前买房婚后加名有用吗？",
            "父母出资买房算共同财产吗？",
            "离婚时股权怎么分？",
            "出轨方会净身出户吗？"
        ]
    else:
        answer = (
            f"## 关于「{question}」的法律分析\n\n"
            "针对您提出的法律问题，我将从以下几个方面进行分析：\n\n"
            "### 一、法律依据\n\n"
            "处理此类问题，主要涉及以下法律法规：\n"
            "- 《中华人民共和国民法典》相关规定\n"
            "- 相关司法解释和指导意见\n"
            "- 最高人民法院发布的典型案例\n\n"
            "### 二、核心要点\n\n"
            "1. **主体资格审查**：确认各方当事人的主体资格和权利能力\n"
            "2. **法律关系认定**：明确各方之间的法律关系性质\n"
            "3. **权利义务划分**：根据法律规定和合同约定确定各方权利义务\n"
            "4. **责任承担方式**：分析可能的违约责任或侵权责任\n"
            "5. **争议解决途径**：协商、调解、仲裁、诉讼等多种途径\n\n"
            "### 三、建议\n\n"
            "为更好地维护您的合法权益，建议：\n"
            "- 收集和保全相关证据材料\n"
            "- 咨询专业律师获取针对性法律意见\n"
            "- 注意诉讼时效和除斥期间\n"
            "- 考虑多种纠纷解决方式的成本和收益\n\n"
            "如果您能提供更多详细信息，我可以给出更具体的分析和建议。"
        )
        citations = [
            {
                "type": "law",
                "title": "中华人民共和国民法典",
                "reference": "总则编",
                "snippet": "民事主体从事民事活动，应当遵循自愿原则，按照自己的意思设立、变更、终止民事法律关系。",
                "url": None
            },
            {
                "type": "case",
                "title": "某公司诉某企业合同纠纷案",
                "reference": "(2025)京01民初999号",
                "snippet": "人民法院审理民事案件，必须以事实为根据，以法律为准绳，依照法律规定实行合议、回避、公开审判和两审终审制度。",
                "url": "/cases/case-xyz999"
            }
        ]
        related_questions = [
            "需要收集哪些证据？",
            "诉讼时效是多久？",
            "请律师要多少钱？",
            "可以先调解吗？"
        ]

    return {
        "answer": answer,
        "citations": citations,
        "related_questions": related_questions
    }


# ========== 端点 ==========

@router.get("/health")
async def qa_health():
    """法律问答服务健康检查"""
    return {
        "status": "ok",
        "service": "lexprime-ai-qa",
        "version": "1.0.0",
        "mock_mode": MOCK_MODE,
        "features": [
            "natural_language_qa",
            "rag_retrieval",
            "citation_tracing",
            "conversation_history",
            "related_questions"
        ],
        "sources": ["cases", "laws", "regulations"],
        "endpoints": [
            {"path": "/api/ai/qa", "method": "POST", "purpose": "法律问答"},
            {"path": "/api/ai/qa/history", "method": "GET", "purpose": "历史记录"},
            {"path": "/api/ai/qa/hot", "method": "GET", "purpose": "热门问题"}
        ]
    }


@router.get("/disclaimer")
async def qa_disclaimer():
    """返回免责声明"""
    return {
        "full": DISCLAIMER_FULL,
        "short": DISCLAIMER_SHORT
    }


@router.post("", response_model=QAResponse)
async def ask_question(req: QARequest):
    """法律问答接口

    输入: 自然语言问题 + 可选对话历史
    输出: AI 回答 + 引用来源 + 相关问题
    """
    t0 = time.time()

    try:
        result = mock_qa_answer(req.question)
        conversation_id = req.conversation_id or f"qa-conv-{int(time.time())}"

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"AI QA request processed in {latency_ms}ms, "
            f"citations={len(result['citations'])}, "
            f"mock_mode={MOCK_MODE}"
        )

        return QAResponse(
            answer=result["answer"],
            conversation_id=conversation_id,
            citations=[QACitation(**c) for c in result["citations"]],
            related_questions=result["related_questions"],
            disclaimer=DISCLAIMER_FULL
        )
    except Exception as e:
        logger.exception(f"AI QA failed: {e}")
        raise HTTPException(500, f"法律问答服务异常: {str(e)}")


@router.get("/history", response_model=QAHistoryResponse)
async def get_history(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取问答历史记录"""
    try:
        items = [QAHistoryItem(**item) for item in MOCK_HISTORY]
        return QAHistoryResponse(
            items=items,
            total=len(MOCK_HISTORY)
        )
    except Exception as e:
        logger.exception(f"Get QA history failed: {e}")
        raise HTTPException(500, f"获取历史记录失败: {str(e)}")


@router.get("/hot", response_model=HotQuestionsResponse)
async def get_hot_questions(category: Optional[str] = Query(None, description="分类筛选")):
    """获取热门问题"""
    try:
        items = [HotQuestion(**q) for q in MOCK_HOT_QUESTIONS]
        if category:
            items = [q for q in items if q.category == category]

        categories = list(set(q["category"] for q in MOCK_HOT_QUESTIONS))

        return HotQuestionsResponse(
            items=items,
            categories=categories
        )
    except Exception as e:
        logger.exception(f"Get hot questions failed: {e}")
        raise HTTPException(500, f"获取热门问题失败: {str(e)}")
