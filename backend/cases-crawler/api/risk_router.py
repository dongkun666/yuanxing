"""
LexPrime 案件风险预测 API
==========================

基于历史案例数据的统计分析，提供案件胜诉率预测、风险点识别、
相似案例对比等功能。

端点:
- POST /api/risk/predict          风险预测
- GET  /api/risk/similar-cases    相似案例
- GET  /api/risk/health           健康检查

支持 mock 模式: 返回模拟预测数据
"""
from __future__ import annotations

import time
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/risk", tags=["risk-prediction"])

MOCK_MODE = True

DISCLAIMER_FULL = (
    "LexPrime 案件风险预测基于历史案例数据统计分析，"
    "预测结果仅供参考，不构成对案件结果的保证或承诺。"
    "具体案件结果受多种因素影响，建议咨询专业律师获取准确法律意见。"
)


# ========== Request / Response Models ==========

class RiskPredictRequest(BaseModel):
    """风险预测请求"""
    case_type: str = Field(..., description="案件类型")
    cause: Optional[str] = None
    parties: Optional[Dict[str, str]] = None
    amount: Optional[str] = None
    court: Optional[str] = None
    facts: Optional[str] = None
    evidence: Optional[str] = None
    claims: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "case_type": "借款合同纠纷",
                "cause": "民间借贷纠纷",
                "amount": "50万元",
                "court": "北京市第一中级人民法院",
                "facts": "原告于2025年3月向被告出借50万元，约定年利率12%，借期1年...",
                "evidence": "借条、转账记录、微信聊天记录",
                "claims": "返还本金50万元及利息"
            }
        }


class RiskFactor(BaseModel):
    """风险因素"""
    name: str
    level: str
    description: str
    impact: float
    suggestion: str


class CaseSimilarity(BaseModel):
    """相似案例"""
    case_id: str
    case_name: str
    court: str
    case_number: str
    similarity: float
    result: str
    amount: Optional[str] = None
    judgment_date: Optional[str] = None


class RiskRadarData(BaseModel):
    """雷达图数据"""
    dimension: str
    score: float
    max_score: float


class RiskPredictResponse(BaseModel):
    """风险预测响应"""
    win_rate: float
    risk_level: str
    risk_score: float
    summary: str
    risk_factors: List[RiskFactor]
    similar_cases: List[CaseSimilarity]
    radar_data: List[RiskRadarData]
    suggestions: List[str]
    disclaimer: str


class SimilarCasesResponse(BaseModel):
    """相似案例响应"""
    cases: List[CaseSimilarity]
    total: int


# ========== Mock Data ==========

def mock_risk_predict(req: RiskPredictRequest) -> Dict[str, Any]:
    """生成 mock 风险预测结果"""
    case_type = (req.case_type or req.cause or "合同纠纷").lower()

    if any(kw in case_type for kw in ["借款", "借贷", "民间借贷"]):
        win_rate = 72.5
        risk_level = "中等"
        risk_score = 45
        summary = (
            "根据历史案例数据分析，本案为民间借贷纠纷，整体胜诉概率约为 72.5%。"
            "案件核心风险点在于证据完整性和被告偿付能力，建议重点关注借条效力、"
            "转账凭证、利息约定合法性等方面。"
        )
        risk_factors = [
            {
                "name": "证据完整性",
                "level": "低风险",
                "description": "现有证据较为完整，包含借条和转账记录",
                "impact": 15,
                "suggestion": "补充借款用途证明、催款记录等，进一步夯实证据链"
            },
            {
                "name": "利息约定合法性",
                "level": "中风险",
                "description": "需核实约定利率是否超过法定上限",
                "impact": 25,
                "suggestion": "核对年利率是否超过 LPR 四倍，超出部分可能不被支持"
            },
            {
                "name": "被告偿付能力",
                "level": "高风险",
                "description": "被告财产状况不明，存在执行风险",
                "impact": 35,
                "suggestion": "建议诉前调查被告财产线索，考虑申请财产保全"
            },
            {
                "name": "诉讼时效",
                "level": "低风险",
                "description": "借款未超过诉讼时效",
                "impact": 10,
                "suggestion": "注意保留催款记录，确保时效中断"
            },
            {
                "name": "管辖法院",
                "level": "低风险",
                "description": "管辖约定明确，法院审理此类案件经验丰富",
                "impact": 15,
                "suggestion": "可参考该法院同类案件裁判口径"
            }
        ]
    elif any(kw in case_type for kw in ["劳动", "劳动合同", "劳动争议"]):
        win_rate = 58.3
        risk_level = "中高"
        risk_score = 58
        summary = (
            "根据历史案例数据分析，本案为劳动争议纠纷，整体胜诉概率约为 58.3%。"
            "劳动争议案件中，劳动者的胜诉率通常高于用人单位，但需视具体诉求和证据情况而定。"
            "建议重点关注劳动关系认定、规章制度合法性、证据充分性等方面。"
        )
        risk_factors = [
            {
                "name": "劳动关系认定",
                "level": "低风险",
                "description": "劳动合同明确，劳动关系清晰",
                "impact": 10,
                "suggestion": "准备劳动合同、社保缴纳记录、工资流水等证据"
            },
            {
                "name": "规章制度合法性",
                "level": "中风险",
                "description": "公司规章制度的制定程序和公示情况需核实",
                "impact": 30,
                "suggestion": "核查规章制度是否经过民主程序制定并公示告知"
            },
            {
                "name": "证据充分性",
                "level": "中风险",
                "description": "部分主张缺乏直接证据支持",
                "impact": 25,
                "suggestion": "补充收集考勤记录、绩效评估、沟通记录等证据"
            },
            {
                "name": "解除程序合法性",
                "level": "高风险",
                "description": "解除劳动合同的程序可能存在瑕疵",
                "impact": 40,
                "suggestion": "重点审查解除通知、工会告知程序、送达方式等"
            },
            {
                "name": "赔偿计算标准",
                "level": "中风险",
                "description": "经济补偿或赔偿金计算基数可能存在争议",
                "impact": 20,
                "suggestion": "准确计算离职前12个月平均工资，包括奖金补贴"
            }
        ]
    else:
        win_rate = 65.0
        risk_level = "中等"
        risk_score = 50
        summary = (
            "根据历史案例数据分析，本案为" + (req.case_type or "合同纠纷") + "，"
            "整体胜诉概率约为 65%。案件结果受多种因素影响，包括证据充分性、"
            "法律适用、法官自由裁量等。建议全面评估风险，做好诉讼策略准备。"
        )
        risk_factors = [
            {
                "name": "证据充分性",
                "level": "中风险",
                "description": "核心事实有基本证据支持，但部分细节需补强",
                "impact": 25,
                "suggestion": "补充完善关键证据，形成完整证据链"
            },
            {
                "name": "法律适用",
                "level": "中风险",
                "description": "相关法律条款存在一定解释空间",
                "impact": 20,
                "suggestion": "检索类似案例，梳理有利裁判观点"
            },
            {
                "name": "对方抗辩",
                "level": "中风险",
                "description": "对方可能提出多项抗辩理由",
                "impact": 30,
                "suggestion": "预判对方可能的抗辩策略，提前准备应对方案"
            },
            {
                "name": "执行风险",
                "level": "中风险",
                "description": "判决后执行效果存在不确定性",
                "impact": 35,
                "suggestion": "考虑诉讼保全，调查对方财产状况"
            },
            {
                "name": "诉讼周期",
                "level": "低风险",
                "description": "预计审理周期在合理范围内",
                "impact": 10,
                "suggestion": "做好时间规划，可考虑调解等快速解决方式"
            }
        ]

    radar_data = [
        {"dimension": "证据充分性", "score": 75, "max_score": 100},
        {"dimension": "法律支持度", "score": 70, "max_score": 100},
        {"dimension": "事实清晰度", "score": 65, "max_score": 100},
        {"dimension": "对方抗辩力", "score": 45, "max_score": 100},
        {"dimension": "执行可能性", "score": 55, "max_score": 100},
        {"dimension": "时间成本", "score": 60, "max_score": 100}
    ]

    similar_cases = [
        {
            "case_id": "case-001",
            "case_name": "张某诉李某民间借贷纠纷案",
            "court": "北京市第一中级人民法院",
            "case_number": "(2025)京01民初123号",
            "similarity": 0.92,
            "result": "原告胜诉",
            "amount": "48万元",
            "judgment_date": "2025-12-15"
        },
        {
            "case_id": "case-002",
            "case_name": "王某诉赵某借款合同纠纷案",
            "court": "北京市朝阳区人民法院",
            "case_number": "(2025)京0105民初456号",
            "similarity": 0.85,
            "result": "部分支持",
            "amount": "60万元",
            "judgment_date": "2025-11-20"
        },
        {
            "case_id": "case-003",
            "case_name": "刘某诉陈某民间借贷纠纷案",
            "court": "北京市海淀区人民法院",
            "case_number": "(2025)京0108民初789号",
            "similarity": 0.78,
            "result": "原告胜诉",
            "amount": "35万元",
            "judgment_date": "2025-10-08"
        },
        {
            "case_id": "case-004",
            "case_name": "周某诉吴某借款纠纷案",
            "court": "北京市西城区人民法院",
            "case_number": "(2026)京0102民初012号",
            "similarity": 0.72,
            "result": "调解结案",
            "amount": "55万元",
            "judgment_date": "2026-01-20"
        },
        {
            "case_id": "case-005",
            "case_name": "郑某诉孙某民间借贷案",
            "court": "北京市东城区人民法院",
            "case_number": "(2025)京0101民初345号",
            "similarity": 0.68,
            "result": "部分支持",
            "amount": "42万元",
            "judgment_date": "2025-09-10"
        }
    ]

    suggestions = [
        "尽快收集和整理全部证据材料，形成完整证据链",
        "建议诉前调查被告财产线索，必要时申请财产保全",
        "考虑先发律师函进行催告，争取协商解决",
        "详细计算诉讼请求金额，包括本金、利息、违约金等",
        "准备好庭审应对方案，预判对方可能的抗辩理由",
        "可考虑调解或和解，降低时间成本和不确定性"
    ]

    return {
        "win_rate": win_rate,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "summary": summary,
        "risk_factors": risk_factors,
        "similar_cases": similar_cases,
        "radar_data": radar_data,
        "suggestions": suggestions
    }


# ========== 端点 ==========

@router.get("/health")
async def risk_health():
    """案件风险预测服务健康检查"""
    return {
        "status": "ok",
        "service": "lexprime-risk-prediction",
        "version": "1.0.0",
        "mock_mode": MOCK_MODE,
        "features": [
            "win_rate_prediction",
            "risk_factor_analysis",
            "similar_case_comparison",
            "radar_chart_visualization",
            "actionable_suggestions"
        ],
        "supported_case_types": [
            "民间借贷纠纷",
            "劳动合同纠纷",
            "买卖合同纠纷",
            "租赁合同纠纷",
            "知识产权纠纷",
            "婚姻家庭纠纷"
        ],
        "endpoints": [
            {"path": "/api/risk/predict", "method": "POST", "purpose": "风险预测"},
            {"path": "/api/risk/similar-cases", "method": "GET", "purpose": "相似案例"}
        ]
    }


@router.post("/predict", response_model=RiskPredictResponse)
async def predict_risk(req: RiskPredictRequest):
    """案件风险预测接口

    输入: 案件基本信息（类型、案由、标的额、法院、事实理由等）
    输出: 胜诉率、风险等级、风险因素、相似案例、雷达图数据、建议
    """
    t0 = time.time()

    try:
        result = mock_risk_predict(req)

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Risk prediction processed in {latency_ms}ms, "
            f"win_rate={result['win_rate']}%, "
            f"risk_level={result['risk_level']}, "
            f"mock_mode={MOCK_MODE}"
        )

        return RiskPredictResponse(
            win_rate=result["win_rate"],
            risk_level=result["risk_level"],
            risk_score=result["risk_score"],
            summary=result["summary"],
            risk_factors=[RiskFactor(**rf) for rf in result["risk_factors"]],
            similar_cases=[CaseSimilarity(**sc) for sc in result["similar_cases"]],
            radar_data=[RiskRadarData(**rd) for rd in result["radar_data"]],
            suggestions=result["suggestions"],
            disclaimer=DISCLAIMER_FULL
        )
    except Exception as e:
        logger.exception(f"Risk prediction failed: {e}")
        raise HTTPException(500, f"案件风险预测服务异常: {str(e)}")


@router.get("/similar-cases", response_model=SimilarCasesResponse)
async def get_similar_cases(
    case_type: str = Query(..., description="案件类型"),
    cause: Optional[str] = Query(None, description="案由"),
    court: Optional[str] = Query(None, description="法院"),
    limit: int = Query(10, ge=1, le=50, description="返回数量")
):
    """获取相似案例"""
    try:
        cases = [
            CaseSimilarity(
                case_id="case-001",
                case_name="张某诉李某民间借贷纠纷案",
                court="北京市第一中级人民法院",
                case_number="(2025)京01民初123号",
                similarity=0.92,
                result="原告胜诉",
                amount="48万元",
                judgment_date="2025-12-15"
            ),
            CaseSimilarity(
                case_id="case-002",
                case_name="王某诉赵某借款合同纠纷案",
                court="北京市朝阳区人民法院",
                case_number="(2025)京0105民初456号",
                similarity=0.85,
                result="部分支持",
                amount="60万元",
                judgment_date="2025-11-20"
            ),
            CaseSimilarity(
                case_id="case-003",
                case_name="刘某诉陈某民间借贷纠纷案",
                court="北京市海淀区人民法院",
                case_number="(2025)京0108民初789号",
                similarity=0.78,
                result="原告胜诉",
                amount="35万元",
                judgment_date="2025-10-08"
            )
        ]
        return SimilarCasesResponse(
            cases=cases[:limit],
            total=len(cases)
        )
    except Exception as e:
        logger.exception(f"Get similar cases failed: {e}")
        raise HTTPException(500, f"获取相似案例失败: {str(e)}")
