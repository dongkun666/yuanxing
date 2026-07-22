"""
LexPrime 个性化推荐 API 路由
基于用户行为和偏好，提供智能推荐服务：案件推荐、律师推荐、模板推荐

端点:
- GET /api/recommend/cases      推荐案件
- GET /api/recommend/lawyers    推荐律师
- GET /api/recommend/templates  推荐模板
- POST /api/recommend/feedback  推荐反馈 (不感兴趣/收藏)
- GET /api/recommend/refresh    刷新推荐
- GET /api/recommend/health     健康检查
"""
from __future__ import annotations

import time
import hashlib
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/recommend", tags=["recommendation"])


# ============================================================================
# 常量
# ============================================================================

RECOMMENDATION_DISCLAIMER = """
**推荐系统声明**
本系统提供的推荐结果基于算法模型生成，仅供参考，不构成法律建议。
推荐结果会根据用户行为和偏好动态调整，可能存在偏差。
用户应结合自身专业判断进行决策。
"""

MOCK_MODE = True


# ============================================================================
# Pydantic 模型
# ============================================================================

class RecommendationItem(BaseModel):
    """推荐项基类"""
    id: str = Field(..., description="推荐项ID")
    type: str = Field(..., description="推荐类型: case/lawyer/template")
    score: float = Field(0.0, description="推荐分数 (0-1)")
    reasons: List[str] = Field(default_factory=list, description="推荐理由")
    match_percentage: int = Field(0, description="匹配度百分比")


class RecommendedCase(RecommendationItem):
    """推荐案件"""
    case_name: str = Field(..., description="案件名称")
    court: Optional[str] = Field(None, description="审理法院")
    cause: Optional[str] = Field(None, description="案由")
    cause_category: Optional[str] = Field(None, description="案由分类")
    judgment_date: Optional[str] = Field(None, description="判决日期")
    lex_score: Optional[int] = Field(None, description="LexPrime评分")
    case_type: str = "case"

    class Config:
        json_schema_extra = {
            "example": {
                "id": "CASE001",
                "type": "case",
                "score": 0.92,
                "reasons": ["与您关注的合同纠纷高度相关", "您收藏过类似案件", "同法院近期典型案例"],
                "match_percentage": 92,
                "case_name": "张三诉李四借款合同纠纷案",
                "court": "北京市第一中级人民法院",
                "cause": "借款合同纠纷",
                "cause_category": "合同纠纷",
                "judgment_date": "2026-03-15",
                "lex_score": 85
            }
        }


class RecommendedLawyer(RecommendationItem):
    """推荐律师"""
    name: str = Field(..., description="律师姓名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    firm_name: Optional[str] = Field(None, description="律所名称")
    specialties: List[str] = Field(default_factory=list, description="专业领域")
    win_rate: float = Field(0.0, description="胜诉率")
    total_cases: int = Field(0, description="总案件数")
    rating: float = Field(0.0, description="评分")
    experience_years: int = Field(0, description="执业年限")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "LAWYER001",
                "type": "lawyer",
                "score": 0.88,
                "reasons": ["擅长您关注的合同纠纷领域", "胜诉率高于行业平均", "与您有相似案件经验"],
                "match_percentage": 88,
                "name": "张明",
                "avatar_url": "/assets/images/avatar.jpg",
                "firm_name": "某律师事务所",
                "specialties": ["民商事诉讼", "合同纠纷", "知识产权"],
                "win_rate": 72.5,
                "total_cases": 156,
                "rating": 4.8,
                "experience_years": 8
            }
        }


class RecommendedTemplate(RecommendationItem):
    """推荐模板"""
    name: str = Field(..., description="模板名称")
    template_type: str = Field(..., description="模板类型")
    category: str = Field(..., description="分类")
    description: Optional[str] = Field(None, description="模板描述")
    usage_count: int = Field(0, description="使用次数")
    rating: float = Field(0.0, description="评分")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "TPL001",
                "type": "template",
                "score": 0.85,
                "reasons": ["与您正在处理的案件类型匹配", "高评分常用模板", "同领域律师推荐"],
                "match_percentage": 85,
                "name": "民事起诉状模板（合同纠纷）",
                "template_type": "complaint",
                "category": "诉讼文书",
                "description": "适用于合同纠纷类案件的民事起诉状模板",
                "usage_count": 1250,
                "rating": 4.7
            }
        }


class RecommendationResponse(BaseModel):
    """推荐响应"""
    items: List[Dict[str, Any]] = Field(default_factory=list, description="推荐列表")
    total: int = Field(0, description="推荐总数")
    algorithm: str = Field("hybrid", description="推荐算法: collaborative/content/hybrid")
    disclaimer: str = Field("", description="免责声明")
    mock_mode: bool = False


class FeedbackRequest(BaseModel):
    """反馈请求"""
    item_id: str = Field(..., description="推荐项ID")
    item_type: str = Field(..., description="推荐类型")
    feedback_type: str = Field(..., pattern="^(dislike|like|favorite|ignore)$", description="反馈类型")
    reason: Optional[str] = Field(None, description="反馈原因")


class RecommendationRefreshResponse(BaseModel):
    """刷新推荐响应"""
    status: str = Field("success", description="状态")
    refreshed_at: str = Field(..., description="刷新时间")
    new_count: int = Field(0, description="新推荐数量")


# ============================================================================
# Mock 数据
# ============================================================================

def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


_MOCK_CASES: List[Dict[str, Any]] = [
    {
        "id": "CASE001",
        "type": "case",
        "case_name": "张三诉李四借款合同纠纷案",
        "court": "北京市第一中级人民法院",
        "cause": "借款合同纠纷",
        "cause_category": "合同纠纷",
        "judgment_date": "2026-03-15",
        "lex_score": 85
    },
    {
        "id": "CASE002",
        "type": "case",
        "case_name": "某公司诉王某买卖合同纠纷案",
        "court": "上海市浦东新区人民法院",
        "cause": "买卖合同纠纷",
        "cause_category": "合同纠纷",
        "judgment_date": "2026-02-20",
        "lex_score": 78
    },
    {
        "id": "CASE003",
        "type": "case",
        "case_name": "李某诉某公司劳动争议案",
        "court": "广州市天河区人民法院",
        "cause": "劳动争议",
        "cause_category": "劳动争议",
        "judgment_date": "2026-01-10",
        "lex_score": 82
    },
    {
        "id": "CASE004",
        "type": "case",
        "case_name": "某科技公司诉某公司知识产权侵权案",
        "court": "深圳市中级人民法院",
        "cause": "侵害商标权纠纷",
        "cause_category": "知识产权",
        "judgment_date": "2026-04-05",
        "lex_score": 90
    },
    {
        "id": "CASE005",
        "type": "case",
        "case_name": "王某诉张某离婚纠纷案",
        "court": "杭州市西湖区人民法院",
        "cause": "离婚纠纷",
        "cause_category": "婚姻家事",
        "judgment_date": "2026-02-28",
        "lex_score": 75
    },
    {
        "id": "CASE006",
        "type": "case",
        "case_name": "某银行诉某公司金融借款合同纠纷案",
        "court": "北京市西城区人民法院",
        "cause": "金融借款合同纠纷",
        "cause_category": "合同纠纷",
        "judgment_date": "2026-03-01",
        "lex_score": 88
    }
]

_MOCK_LAWYERS: List[Dict[str, Any]] = [
    {
        "id": "LAWYER001",
        "type": "lawyer",
        "name": "张明",
        "avatar_url": "/assets/images/avatar.jpg",
        "firm_name": "北京某律师事务所",
        "specialties": ["民商事诉讼", "合同纠纷", "知识产权"],
        "win_rate": 72.5,
        "total_cases": 156,
        "rating": 4.8,
        "experience_years": 8
    },
    {
        "id": "LAWYER002",
        "type": "lawyer",
        "name": "李华",
        "avatar_url": None,
        "firm_name": "上海某律师事务所",
        "specialties": ["公司法", "投融资", "并购重组"],
        "win_rate": 68.2,
        "total_cases": 203,
        "rating": 4.6,
        "experience_years": 12
    },
    {
        "id": "LAWYER003",
        "type": "lawyer",
        "name": "王芳",
        "avatar_url": None,
        "firm_name": "广州某律师事务所",
        "specialties": ["婚姻家事", "遗产继承", "财富管理"],
        "win_rate": 75.8,
        "total_cases": 128,
        "rating": 4.9,
        "experience_years": 6
    },
    {
        "id": "LAWYER004",
        "type": "lawyer",
        "name": "陈伟",
        "avatar_url": None,
        "firm_name": "深圳某律师事务所",
        "specialties": ["刑事辩护", "行政诉讼"],
        "win_rate": 65.3,
        "total_cases": 89,
        "rating": 4.5,
        "experience_years": 10
    },
    {
        "id": "LAWYER005",
        "type": "lawyer",
        "name": "刘洋",
        "avatar_url": None,
        "firm_name": "杭州某律师事务所",
        "specialties": ["劳动争议", "交通事故", "人身损害"],
        "win_rate": 70.1,
        "total_cases": 167,
        "rating": 4.7,
        "experience_years": 5
    }
]

_MOCK_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "TPL001",
        "type": "template",
        "name": "民事起诉状模板（合同纠纷）",
        "template_type": "complaint",
        "category": "诉讼文书",
        "description": "适用于合同纠纷类案件的民事起诉状模板",
        "usage_count": 1250,
        "rating": 4.7
    },
    {
        "id": "TPL002",
        "type": "template",
        "name": "劳动合同模板",
        "template_type": "contract",
        "category": "合同模板",
        "description": "标准劳动合同模板，包含试用期、薪资、社保等条款",
        "usage_count": 3560,
        "rating": 4.8
    },
    {
        "id": "TPL003",
        "type": "template",
        "name": "法律意见书模板",
        "template_type": "opinion",
        "category": "法律文书",
        "description": "通用法律意见书模板，适用于各类法律咨询",
        "usage_count": 890,
        "rating": 4.6
    },
    {
        "id": "TPL004",
        "type": "template",
        "name": "股权转让协议模板",
        "template_type": "agreement",
        "category": "合同模板",
        "description": "有限责任公司股权转让协议标准模板",
        "usage_count": 2100,
        "rating": 4.9
    },
    {
        "id": "TPL005",
        "type": "template",
        "name": "离婚协议书模板",
        "template_type": "agreement",
        "category": "婚姻家事",
        "description": "自愿离婚协议书模板，包含财产分割、子女抚养条款",
        "usage_count": 1850,
        "rating": 4.5
    },
    {
        "id": "TPL006",
        "type": "template",
        "name": "答辩状模板",
        "template_type": "defense",
        "category": "诉讼文书",
        "description": "民事答辩状通用模板",
        "usage_count": 980,
        "rating": 4.4
    }
]


def _generate_reasons(item_type: str, item: Dict[str, Any], user_preferences: Dict[str, Any]) -> List[str]:
    """生成推荐理由"""
    reasons = []
    random.seed(hash(item["id"]))

    base_reasons = {
        "case": [
            "与您关注的领域高度相关",
            "您收藏过类似案件",
            "同法院近期典型案例",
            "高 LexScore 评分案件",
            "您浏览过同类型案件",
            "同类案件胜诉率较高",
            "最新判决的典型案例"
        ],
        "lawyer": [
            "擅长您关注的专业领域",
            "胜诉率高于行业平均",
            "与您有相似案件经验",
            "高评分资深律师",
            "同律所律师推荐",
            "客户评价优秀",
            "多年执业经验"
        ],
        "template": [
            "与您正在处理的案件类型匹配",
            "高评分常用模板",
            "同领域律师推荐",
            "使用量排名靠前",
            "您之前使用过同类模板",
            "最新更新的模板",
            "官方认证优质模板"
        ]
    }

    available_reasons = base_reasons.get(item_type, [])
    num_reasons = random.randint(2, 3)
    selected = random.sample(available_reasons, min(num_reasons, len(available_reasons)))
    reasons.extend(selected)

    if user_preferences.get("categories"):
        categories = user_preferences["categories"]
        cause = item.get("cause_category") or item.get("category") or ""
        if any(cat in cause for cat in categories):
            reasons.insert(0, "符合您的偏好设置")

    return reasons


def _calculate_score(item_type: str, item: Dict[str, Any], user_preferences: Dict[str, Any]) -> float:
    """计算推荐分数"""
    base_score = 0.6
    random.seed(hash(item["id"] + str(time.time() // 3600)))
    variance = random.uniform(-0.1, 0.2)

    if item_type == "case":
        lex_score = item.get("lex_score", 70)
        base_score = 0.5 + (lex_score / 200)
    elif item_type == "lawyer":
        win_rate = item.get("win_rate", 60)
        rating = item.get("rating", 4.0)
        base_score = 0.5 + (win_rate / 200) + ((rating - 4) / 10)
    elif item_type == "template":
        rating = item.get("rating", 4.0)
        usage = item.get("usage_count", 100)
        base_score = 0.5 + ((rating - 4) / 10) + min(usage / 10000, 0.2)

    if user_preferences.get("categories"):
        categories = user_preferences["categories"]
        cause = item.get("cause_category") or item.get("category") or ""
        if any(cat in cause for cat in categories):
            base_score += 0.1

    final_score = min(0.98, max(0.3, base_score + variance))
    return round(final_score, 2)


def _measure_latency_ms(start_time: float) -> float:
    return round((time.time() - start_time) * 1000, 2)


# ============================================================================
# 用户偏好存储 (内存版 mock)
# ============================================================================

_user_preferences: Dict[str, Dict[str, Any]] = {}
_user_feedback: Dict[str, List[Dict[str, Any]]] = {}


def _get_user_preferences(user_id: str) -> Dict[str, Any]:
    """获取用户偏好"""
    if user_id not in _user_preferences:
        _user_preferences[user_id] = {
            "categories": ["合同纠纷", "知识产权"],
            "viewed_cases": [],
            "favorite_cases": [],
            "viewed_lawyers": [],
            "used_templates": [],
            "last_active": _now_iso()
        }
    return _user_preferences[user_id]


# ============================================================================
# 端点
# ============================================================================

@router.get("/health", summary="推荐系统 API 健康检查")
async def recommendation_health():
    """检查推荐系统 API 是否可用"""
    return {
        "status": "ok",
        "service": "recommendation",
        "version": "1.0.0",
        "mock_mode": MOCK_MODE,
        "algorithm": "hybrid",
        "timestamp": _now_iso(),
        "disclaimer": RECOMMENDATION_DISCLAIMER.strip()
    }


@router.get("/cases", summary="推荐案件")
async def recommend_cases(
    user_id: str = Query("default", description="用户ID"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    algorithm: str = Query("hybrid", pattern="^(collaborative|content|hybrid)$", description="推荐算法"),
):
    """
    获取个性化案件推荐：
    - 基于用户浏览历史和收藏
    - 基于内容相似度
    - 混合推荐算法
    """
    start_time = time.time()
    logger.info(f"[Recommendation] 案件推荐, user_id={user_id}, limit={limit}")

    try:
        prefs = _get_user_preferences(user_id)

        cases = _MOCK_CASES.copy()

        if category:
            cases = [c for c in cases if c.get("cause_category") == category]

        for case in cases:
            case["score"] = _calculate_score("case", case, prefs)
            case["reasons"] = _generate_reasons("case", case, prefs)
            case["match_percentage"] = int(case["score"] * 100)

        cases.sort(key=lambda x: x["score"], reverse=True)

        limited_cases = cases[:limit]
        result = [RecommendedCase(**c).model_dump() for c in limited_cases]

        latency = _measure_latency_ms(start_time)
        logger.info(f"[Recommendation] 案件推荐完成, 返回{len(result)}条, 耗时={latency}ms")

        return RecommendationResponse(
            items=result,
            total=len(cases),
            algorithm=algorithm,
            disclaimer=RECOMMENDATION_DISCLAIMER.strip(),
            mock_mode=MOCK_MODE
        )

    except Exception as e:
        logger.error(f"[Recommendation] 案件推荐失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取案件推荐失败: {str(e)}")


@router.get("/lawyers", summary="推荐律师")
async def recommend_lawyers(
    user_id: str = Query("default", description="用户ID"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    specialty: Optional[str] = Query(None, description="专业领域筛选"),
    algorithm: str = Query("hybrid", pattern="^(collaborative|content|hybrid)$", description="推荐算法"),
):
    """
    获取个性化律师推荐：
    - 基于专业领域匹配
    - 基于胜诉率和评分
    - 基于相似用户推荐
    """
    start_time = time.time()
    logger.info(f"[Recommendation] 律师推荐, user_id={user_id}, limit={limit}")

    try:
        prefs = _get_user_preferences(user_id)

        lawyers = _MOCK_LAWYERS.copy()

        if specialty:
            lawyers = [l for l in lawyers if specialty in l.get("specialties", [])]

        for lawyer in lawyers:
            lawyer["score"] = _calculate_score("lawyer", lawyer, prefs)
            lawyer["reasons"] = _generate_reasons("lawyer", lawyer, prefs)
            lawyer["match_percentage"] = int(lawyer["score"] * 100)

        lawyers.sort(key=lambda x: x["score"], reverse=True)

        limited_lawyers = lawyers[:limit]
        result = [RecommendedLawyer(**l).model_dump() for l in limited_lawyers]

        latency = _measure_latency_ms(start_time)
        logger.info(f"[Recommendation] 律师推荐完成, 返回{len(result)}条, 耗时={latency}ms")

        return RecommendationResponse(
            items=result,
            total=len(lawyers),
            algorithm=algorithm,
            disclaimer=RECOMMENDATION_DISCLAIMER.strip(),
            mock_mode=MOCK_MODE
        )

    except Exception as e:
        logger.error(f"[Recommendation] 律师推荐失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取律师推荐失败: {str(e)}")


@router.get("/templates", summary="推荐模板")
async def recommend_templates(
    user_id: str = Query("default", description="用户ID"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    template_type: Optional[str] = Query(None, description="模板类型筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    algorithm: str = Query("hybrid", pattern="^(collaborative|content|hybrid)$", description="推荐算法"),
):
    """
    获取个性化模板推荐：
    - 基于使用历史
    - 基于案件类型匹配
    - 基于热门和评分
    """
    start_time = time.time()
    logger.info(f"[Recommendation] 模板推荐, user_id={user_id}, limit={limit}")

    try:
        prefs = _get_user_preferences(user_id)

        templates = _MOCK_TEMPLATES.copy()

        if template_type:
            templates = [t for t in templates if t.get("template_type") == template_type]
        if category:
            templates = [t for t in templates if t.get("category") == category]

        for template in templates:
            template["score"] = _calculate_score("template", template, prefs)
            template["reasons"] = _generate_reasons("template", template, prefs)
            template["match_percentage"] = int(template["score"] * 100)

        templates.sort(key=lambda x: x["score"], reverse=True)

        limited_templates = templates[:limit]
        result = [RecommendedTemplate(**t).model_dump() for t in limited_templates]

        latency = _measure_latency_ms(start_time)
        logger.info(f"[Recommendation] 模板推荐完成, 返回{len(result)}条, 耗时={latency}ms")

        return RecommendationResponse(
            items=result,
            total=len(templates),
            algorithm=algorithm,
            disclaimer=RECOMMENDATION_DISCLAIMER.strip(),
            mock_mode=MOCK_MODE
        )

    except Exception as e:
        logger.error(f"[Recommendation] 模板推荐失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模板推荐失败: {str(e)}")


@router.post("/feedback", summary="推荐反馈")
async def recommendation_feedback(
    req: FeedbackRequest,
    user_id: str = Query("default", description="用户ID"),
):
    """
    提交推荐反馈：
    - dislike: 不感兴趣
    - like: 感兴趣
    - favorite: 收藏
    - ignore: 忽略
    """
    start_time = time.time()
    logger.info(f"[Recommendation] 提交反馈, user_id={user_id}, item_id={req.item_id}, type={req.feedback_type}")

    try:
        if user_id not in _user_feedback:
            _user_feedback[user_id] = []

        feedback_entry = {
            "item_id": req.item_id,
            "item_type": req.item_type,
            "feedback_type": req.feedback_type,
            "reason": req.reason,
            "created_at": _now_iso()
        }
        _user_feedback[user_id].append(feedback_entry)

        prefs = _get_user_preferences(user_id)
        if req.feedback_type == "favorite":
            if req.item_type == "case" and req.item_id not in prefs["favorite_cases"]:
                prefs["favorite_cases"].append(req.item_id)
        elif req.feedback_type == "dislike":
            pass

        latency = _measure_latency_ms(start_time)
        logger.info(f"[Recommendation] 反馈提交成功, 耗时={latency}ms")

        return {
            "status": "success",
            "message": "反馈已记录",
            "feedback": feedback_entry
        }

    except Exception as e:
        logger.error(f"[Recommendation] 提交反馈失败: {e}")
        raise HTTPException(status_code=500, detail=f"提交反馈失败: {str(e)}")


@router.get("/refresh", response_model=RecommendationRefreshResponse, summary="刷新推荐")
async def refresh_recommendations(
    user_id: str = Query("default", description="用户ID"),
    type: str = Query("all", pattern="^(all|case|lawyer|template)$", description="推荐类型"),
):
    """刷新推荐结果"""
    start_time = time.time()
    logger.info(f"[Recommendation] 刷新推荐, user_id={user_id}, type={type}")

    try:
        prefs = _get_user_preferences(user_id)
        prefs["last_active"] = _now_iso()

        new_count = 0
        if type == "all" or type == "case":
            new_count += 2
        if type == "all" or type == "lawyer":
            new_count += 1
        if type == "all" or type == "template":
            new_count += 1

        latency = _measure_latency_ms(start_time)
        logger.info(f"[Recommendation] 推荐刷新完成, 新推荐{new_count}条, 耗时={latency}ms")

        return RecommendationRefreshResponse(
            status="success",
            refreshed_at=_now_iso(),
            new_count=new_count
        )

    except Exception as e:
        logger.error(f"[Recommendation] 刷新推荐失败: {e}")
        raise HTTPException(status_code=500, detail=f"刷新推荐失败: {str(e)}")
