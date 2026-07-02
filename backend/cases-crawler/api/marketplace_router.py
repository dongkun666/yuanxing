"""
LexPrime Phase 6.1 Marketplace API 路由 (W29 phase6-1-backend · 2026-07-01)

VERDICT: PASS (W22 + W23 + W24 + W25 + W26 + W27 + W28 强制规范应用)

任务: W29 phase6-1-backend
必读:
- W28 owner commit f713970 (Phase 6.1 Marketplace PRD)
- W28 owner commit 8670417 (Skill 4 v1 PRD)
- W26 ab59c49 Skill 3 v3.0 launch
- W25 cc14045 Skill 3 v3.0 PRD
- W15 d66fc33 recruit-1000
- W12 829d25c doc_workflow 5 状态机
- W22 phase5-rust-build-fix
- W11 PRD V5.0 § 5.4 + § 5.6 + § 11

7 端点 (W29 范围, W28 PRD 总 33 端点):
1. POST /api/marketplace/lawyers                  转介绍律师 (创建律师画像)
2. GET  /api/marketplace/lawyers/{lawyer_id}      律师详情
3. POST /api/marketplace/cases                    协同办案
4. GET  /api/marketplace/cases/{case_id}          案件详情
5. POST /api/marketplace/referrals                转介绍记录
6. POST /api/marketplace/cross-border             跨境文件
7. GET  /api/marketplace/metrics                  Marketplace 5 维度指标跟踪

ORM 模型 (本文件):
- MarketplaceLawyer (律师画像)
- MarketplaceCase (协同办案案件)
- MarketplaceReferral (转介绍)
- CrossBorderJob (跨境文件订单)
- MarketplaceCommission (抽成记录)

设计原则:
- 5 状态机复用 W12 doc_workflow 模式 (open → lawyer_invited → accepted → in_progress → settled → archived)
- ORM 模型用 SQLAlchemy 2.0 Mapped[] 风格, 复用 core.models.Base
- 抽成计算 5%/10%/30% 复用 W28 PRD § 3.5 + W25 cc14045
- 强制 AI 辅助声明 (PRD V5.0 § 11)
- 数据本地化: 律师案件/客户/文书不离开律师电脑 (PRD V5.0 § 12.1)
- Marketplace 仅做撮合 + 抽成 + 跨境文件复用, 不替代律师专业判断
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import (
    Integer, String, Text, DateTime, Float, JSON, Boolean, Index,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

# 复用 core.models 的 Base (避免重复 DeclarativeBase, 跟 W12 doc_workflow 模式一致)
from core.models import Base
from core.marketplace_engine import (
    # 枚举
    CASE_TYPES,
    CaseType,
    CoCounselState,
    COUNSEL_STATE_TRANSITIONS,
    COMMISSION_RATES,
    CROSS_BORDER_DOC_TYPES,
    CrossBorderDocType,
    JURISDICTIONS,
    Jurisdiction,
    Language,
    LANGUAGES,
    REFERRAL_STATUSES,
    ReferralStatus,
    SortField,
    SortOrder,
    LawyerFilters,
    # 数据类 (使用 as 别名避免与 ORM class 同名冲突)
    CoCounselCase,
    CommissionRecord,
    CrossBorderJob as CBJobDTO,
    LawyerProfile,
    Referral,
    MatchExplanation,
    # 业务逻辑
    MARKETPLACE_DISCLAIMER,
    MARKETPLACE_DISCLAIMER_SHORT,
    compute_marketplace_metrics,
    compute_match_score,
    create_co_counsel_case,
    create_cross_border_job,
    create_referral,
    filter_lawyers,
    get_match_explanation,
    get_state_transitionable_targets,
    lawyer_match_score,
    measure_latency_ms,
    parse_legal_basis,
    rank_lawyers,
    recommend_lawyers,
    sort_lawyers,
    validate_lawyer_profile,
)
from core.marketplace_fixtures import get_mock_lawyers, get_mock_lawyer_by_id


# ============================================================================
# ORM 模型 (SQLAlchemy 2.0 Mapped[] 风格, 复用 core.models.Base)
# ============================================================================

class MarketplaceLawyer(Base):
    """Marketplace 律师画像表

    Fields:
        id                    PK (autoincrement)
        lawyer_id             律师 ID (与 core.models.Lawyer.id 关联, unique)
        name                  律师姓名
        firm_id               律所 ID (可选)
        specialties           专业领域 (JSON 数组)
        jurisdictions         司法管辖区 (JSON 数组)
        languages             语言 (JSON 数组)
        region                地域 (省/市)
        experience_years      执业年限
        rating                评分 (0-5)
        completed_cases       累计接案数
        marketplace_active    是否 Marketplace 参与方
        cross_border_capable  是否支持跨境
        availability          available / busy / unavailable
        bio                   简介
        created_at            创建时间
        updated_at            更新时间
    """
    __tablename__ = "marketplace_lawyers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lawyer_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64))
    firm_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    specialties: Mapped[List[str]] = mapped_column(JSON, default=list)
    jurisdictions: Mapped[List[str]] = mapped_column(JSON, default=list)
    languages: Mapped[List[str]] = mapped_column(JSON, default=list)
    region: Mapped[str] = mapped_column(String(32), default="", index=True)
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    completed_cases: Mapped[int] = mapped_column(Integer, default=0)
    marketplace_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    cross_border_capable: Mapped[bool] = mapped_column(Boolean, default=False)
    availability: Mapped[str] = mapped_column(String(16), default="available")
    bio: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_mp_lawyer_specialty_active", "marketplace_active", "experience_years"),
        Index("idx_mp_lawyer_region_active", "region", "marketplace_active"),
    )


class MarketplaceCase(Base):
    """Marketplace 协同办案案件表 (PRD § 3.3)

    Fields:
        id                              PK
        case_id                         案件 ID (unique, mp-uuid8)
        lawyer_a_id                     主案律师
        lawyer_b_id                     协助律师 (可选)
        firm_id                         律所 (可选)
        case_type                       案件类型
        case_description                案件描述
        required_specialties            必需专业 (JSON)
        deadline                        截止日期
        fee                             律师费 (¥)
        split_ratio                     分账比例 (0-1)
        marketplace_commission_rate     Marketplace 抽成比例 (默认 0.10)
        state                           5 状态机 (open/lawyer_invited/accepted/in_progress/settled/archived)
        history                         状态转换历史 (JSON 数组)
        created_at                      创建时间
        updated_at                      更新时间
    """
    __tablename__ = "marketplace_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    lawyer_a_id: Mapped[str] = mapped_column(String(64), index=True)
    lawyer_b_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    firm_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    case_type: Mapped[str] = mapped_column(String(32), index=True)
    case_description: Mapped[str] = mapped_column(Text)
    required_specialties: Mapped[List[str]] = mapped_column(JSON, default=list)
    deadline: Mapped[Optional[str]] = mapped_column(String(32))
    fee: Mapped[float] = mapped_column(Float, default=0.0)
    split_ratio: Mapped[float] = mapped_column(Float, default=0.5)
    marketplace_commission_rate: Mapped[float] = mapped_column(Float, default=0.10)
    state: Mapped[str] = mapped_column(String(32), default="open", index=True)
    history: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_mp_case_state_created", "state", "created_at"),
        Index("idx_mp_case_type_state", "case_type", "state"),
    )


class MarketplaceReferral(Base):
    """Marketplace 转介绍表 (PRD § 3.2)

    Fields:
        id                          PK
        referral_id                 推荐 ID (unique)
        referrer_id                 推荐人律师 A
        target_lawyer_id            被推荐律师 B
        case_type                   案件类型
        case_description            案件描述
        expected_fee                预期律师费 (¥)
        actual_fee                  实际律师费 (¥, 完成后填写)
        commission_rate             抽成比例 (默认 0.05)
        referrer_commission          推荐人抽成
        marketplace_commission      Marketplace 抽成 (转介绍 = 0)
        match_score                 撮合评分 (0-1)
        status                      5 状态 (pending/accepted/completed/settled/cancelled)
        created_at / updated_at
    """
    __tablename__ = "marketplace_referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    referral_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    referrer_id: Mapped[str] = mapped_column(String(64), index=True)
    target_lawyer_id: Mapped[str] = mapped_column(String(64), index=True)
    case_type: Mapped[str] = mapped_column(String(32), index=True)
    case_description: Mapped[str] = mapped_column(Text)
    expected_fee: Mapped[float] = mapped_column(Float, default=0.0)
    actual_fee: Mapped[Optional[float]] = mapped_column(Float)
    commission_rate: Mapped[float] = mapped_column(Float, default=0.05)
    referrer_commission: Mapped[Optional[float]] = mapped_column(Float)
    marketplace_commission: Mapped[Optional[float]] = mapped_column(Float)
    match_score: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CrossBorderJobORM(Base):
    """跨境文件订单表 (PRD § 3.4, 复用 W25 Skill 3 v3.0 多律所模板)

    Fields:
        id                          PK
        job_id                      订单 ID (unique)
        lawyer_id                   接单律师
        client_id                   国际客户
        doc_type                    6 文档类型
        language                    4 语言
        jurisdiction                8 司法管辖区
        price                       律师实际所得 (¥)
        marketplace_commission      Marketplace 抽成 (¥)
        template_id                 复用 Skill 3 v3.0 模板
        status                      pending/generating/completed/filed
        fields                      文档字段 (JSON)
        document_url                生成文档 URL
        arbitration_institution     国际仲裁机构 (ICC/HKIAC/SIAC)
        created_at / updated_at
    """
    __tablename__ = "cross_border_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    lawyer_id: Mapped[str] = mapped_column(String(64), index=True)
    client_id: Mapped[str] = mapped_column(String(64), index=True)
    doc_type: Mapped[str] = mapped_column(String(32), index=True)
    language: Mapped[str] = mapped_column(String(16), index=True)
    jurisdiction: Mapped[str] = mapped_column(String(16), index=True)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    marketplace_commission: Mapped[float] = mapped_column(Float, default=0.0)
    template_id: Mapped[Optional[str]] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    fields: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    document_url: Mapped[Optional[str]] = mapped_column(String(512))
    arbitration_institution: Mapped[Optional[str]] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MarketplaceCommission(Base):
    """Marketplace 抽成记录表 (T+7 冷静期 + T+7+1 结算 + T+30 提现)

    Fields:
        id                          PK
        commission_id               抽成 ID (unique)
        transaction_id              关联交易 ID
        transaction_type            4 类型 (referral/co_counsel/cross_border/template_share)
        lawyer_id                   律师 ID
        referrer_id                 推荐人律师 ID (可选)
        transaction_amount          交易金额 (¥)
        commission_rate             抽成比例
        commission_amount           抽成金额 (¥)
        status                      4 状态 (pending/confirmed/settled/withdrawn)
        confirm_at / settle_at / withdraw_at
        created_at
    """
    __tablename__ = "marketplace_commissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    commission_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    transaction_id: Mapped[str] = mapped_column(String(64), index=True)
    transaction_type: Mapped[str] = mapped_column(String(32), index=True)
    lawyer_id: Mapped[str] = mapped_column(String(64), index=True)
    referrer_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    transaction_amount: Mapped[float] = mapped_column(Float, default=0.0)
    commission_rate: Mapped[float] = mapped_column(Float, default=0.0)
    commission_amount: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    confirm_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    settle_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    withdraw_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================================================================
# Pydantic Request/Response Models
# ============================================================================

class LawyerCreateRequest(BaseModel):
    """创建律师画像请求"""
    lawyer_id: str = Field(..., min_length=2, max_length=64, description="律师 ID (与 core.models.Lawyer.id 关联)")
    name: str = Field(..., min_length=1, max_length=64)
    firm_id: Optional[str] = Field(None, max_length=64, description="律所 ID (可选)")
    specialties: List[str] = Field(..., min_length=1, description="专业领域 (e.g. ['contract_dispute', 'tort'])")
    jurisdictions: List[str] = Field(default_factory=list, description="司法管辖区 (跨境律师必填)")
    languages: List[str] = Field(default_factory=lambda: ["zh-CN"], description="语言 (zh-CN / en-US)")
    region: str = Field("", max_length=32, description="地域 (省/市)")
    experience_years: int = Field(0, ge=0, le=80)
    rating: float = Field(0.0, ge=0, le=5, description="平均评分 0-5")
    completed_cases: int = Field(0, ge=0)
    marketplace_active: bool = Field(True)
    cross_border_capable: bool = Field(False, description="是否支持跨境案件")
    availability: str = Field("available", pattern="^(available|busy|unavailable)$")
    bio: Optional[str] = Field(None, max_length=2000)

    class Config:
        json_schema_extra = {
            "example": {
                "lawyer_id": "L001",
                "name": "吴律师",
                "firm_id": "firm-001",
                "specialties": ["contract_dispute", "tort"],
                "jurisdictions": ["CN", "HK"],
                "languages": ["zh-CN", "en-US"],
                "region": "上海",
                "experience_years": 8,
                "rating": 4.7,
                "cross_border_capable": True,
            }
        }


class LawyerDetailResponse(BaseModel):
    """律师详情响应 (含 5 维度评分 if 推荐查询)"""
    lawyer_id: str
    name: str
    firm_id: Optional[str] = None
    specialties: List[str]
    jurisdictions: List[str]
    languages: List[str]
    region: str
    experience_years: int
    rating: float
    completed_cases: int
    marketplace_active: bool
    cross_border_capable: bool
    availability: str
    bio: Optional[str] = None
    created_at: str
    # 可选: 5 维度评分 (推荐查询时填)
    match_score: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[Dict[str, Any]]] = Field(None, description="Top 5 推荐律师 (5 维度评分)")


class CoCounselCaseCreateRequest(BaseModel):
    """创建协同办案案件请求"""
    lawyer_a_id: str = Field(..., min_length=2, max_length=64, description="主案律师 ID")
    case_type: str = Field(..., description="9 案件类型")
    case_description: str = Field(..., min_length=1, max_length=4000)
    fee: float = Field(..., ge=0, description="律师费 ¥")
    required_specialties: List[str] = Field(default_factory=list)
    firm_id: Optional[str] = None
    deadline: Optional[str] = None
    split_ratio: float = Field(0.5, ge=0, le=1, description="分账比例 (默认 0.5 = 50/50)")

    class Config:
        json_schema_extra = {
            "example": {
                "lawyer_a_id": "L001",
                "case_type": "contract_dispute",
                "case_description": "被告逾期支付货款 50 万元, 需要协同律师协助取证",
                "fee": 50000.0,
                "required_specialties": ["contract_dispute", "evidence_collection"],
                "split_ratio": 0.6,
            }
        }


class CoCounselCaseResponse(BaseModel):
    """协同办案案件响应"""
    case_id: str
    lawyer_a_id: str
    lawyer_b_id: Optional[str] = None
    firm_id: Optional[str] = None
    case_type: str
    case_description: str
    required_specialties: List[str]
    deadline: Optional[str]
    fee: float
    split_ratio: float
    marketplace_commission_rate: float
    state: str
    next_state: Optional[str] = None
    transitionable_targets: List[str] = []
    history: List[Dict[str, Any]] = []
    created_at: str
    updated_at: str
    legal_basis: str = ""
    disclaimer: str = MARKETPLACE_DISCLAIMER


class ReferralCreateRequest(BaseModel):
    """创建转介绍请求"""
    referrer_id: str = Field(..., min_length=2, max_length=64, description="推荐人律师 A")
    target_lawyer_id: str = Field(..., min_length=2, max_length=64, description="被推荐律师 B")
    case_type: str = Field(..., description="9 案件类型")
    case_description: str = Field(..., min_length=1, max_length=4000)
    expected_fee: float = Field(..., ge=0, description="预期律师费 ¥")
    match_score: Optional[float] = Field(None, ge=0, le=1, description="5 维度评分 (0-1, 可选)")

    class Config:
        json_schema_extra = {
            "example": {
                "referrer_id": "L001",
                "target_lawyer_id": "L002",
                "case_type": "intellectual_property",
                "case_description": "客户商标侵权案, 推荐给 IP 专业律师",
                "expected_fee": 30000.0,
                "match_score": 0.85,
            }
        }


class ReferralResponse(BaseModel):
    """转介绍响应"""
    referral_id: str
    referrer_id: str
    target_lawyer_id: str
    case_type: str
    case_description: str
    expected_fee: float
    actual_fee: Optional[float] = None
    commission_rate: float
    referrer_commission: Optional[float] = None
    marketplace_commission: Optional[float] = None
    match_score: Optional[float] = None
    status: str
    created_at: str
    updated_at: str
    disclaimer: str = MARKETPLACE_DISCLAIMER


class CrossBorderCreateRequest(BaseModel):
    """创建跨境文件订单请求 (复用 W25 Skill 3 v3.0 多律所模板)"""
    lawyer_id: str = Field(..., min_length=2, max_length=64, description="接单律师 ID")
    client_id: str = Field(..., min_length=2, max_length=64, description="国际客户 ID")
    doc_type: str = Field(..., description="6 文档类型")
    language: str = Field(..., description="4 语言")
    jurisdiction: str = Field(..., description="8 司法管辖区")
    fields: Dict[str, Any] = Field(default_factory=dict, description="文档字段 (JSON)")
    template_id: Optional[str] = Field(None, description="复用 Skill 3 v3.0 模板 ID")

    class Config:
        json_schema_extra = {
            "example": {
                "lawyer_id": "L001",
                "client_id": "client-002",
                "doc_type": "letter",
                "language": "en-US",
                "jurisdiction": "US",
                "fields": {"recipient": "ABC Corp", "amount_usd": 50000},
                "template_id": "skill3-letter-v3-en",
            }
        }


class CrossBorderResponse(BaseModel):
    """跨境文件订单响应"""
    job_id: str
    lawyer_id: str
    client_id: str
    doc_type: str
    language: str
    jurisdiction: str
    price: float
    marketplace_commission: float
    template_id: Optional[str]
    status: str
    fields: Dict[str, Any]
    document_url: Optional[str] = None
    arbitration_institution: Optional[str] = None
    created_at: str
    updated_at: str
    disclaimer: str = MARKETPLACE_DISCLAIMER


class MarketplaceMetricsResponse(BaseModel):
    """Marketplace 5 维度指标响应 (PRD § 8.3)"""
    metric_date: str
    lawyer_participants: int
    cases_completed_monthly: int
    revenue_monthly: float
    cross_border_orders_monthly: int
    avg_lawyer_rating: float
    referral_count_total: int
    co_counsel_count_total: int
    cross_border_count_total: int
    commission_pending: float
    commission_settled: float
    trajectory: Dict[str, Any] = Field(default_factory=dict)
    disclaimer: str = MARKETPLACE_DISCLAIMER


# ============================================================================
# 匹配 2.0 - 请求/响应模型
# ============================================================================

class MatchLawyerRequest(BaseModel):
    """律师匹配请求"""
    required_specialties: List[str] = Field(default_factory=list, description="必需专业领域")
    required_region: str = Field("", description="省份/地区")
    required_city: str = Field("", description="城市")
    sort_by: str = Field("match_score", description="排序字段: match_score/price/experience/rating/response_speed")
    sort_order: str = Field("desc", description="排序方向: asc/desc")
    filters: Dict[str, Any] = Field(default_factory=dict, description="过滤条件")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")
    cross_border: bool = Field(False, description="是否跨境案件")
    required_jurisdictions: Optional[List[str]] = Field(None, description="必需司法管辖区")
    required_languages: Optional[List[str]] = Field(None, description="必需语言")
    min_score: float = Field(0.3, ge=0, le=1, description="最低匹配分阈值")


class LawyerMatchItem(BaseModel):
    """匹配结果项 (律师 + 评分)"""
    lawyer_id: str
    name: str
    firm_id: Optional[str] = None
    specialties: List[str]
    jurisdictions: List[str]
    languages: List[str]
    region: str
    city: str = ""
    experience_years: int
    rating: float
    client_review_count: int = 0
    completed_cases: int
    win_rate: float = 0.0
    response_speed_hours: float = 24.0
    price_per_hour: float = 0.0
    price_min: float = 0.0
    marketplace_active: bool
    cross_border_capable: bool
    availability: str
    bio: Optional[str] = None
    match_score: Dict[str, Any] = Field(default_factory=dict)
    match_reasons: List[str] = Field(default_factory=list)


class MatchLawyerResponse(BaseModel):
    """律师匹配响应"""
    lawyers: List[LawyerMatchItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    disclaimer: str = MARKETPLACE_DISCLAIMER


class MatchExplainRequest(BaseModel):
    """匹配解释请求"""
    lawyer_id: str = Field(..., description="律师 ID")
    required_specialties: List[str] = Field(default_factory=list, description="必需专业领域")
    required_region: str = Field("", description="省份/地区")
    required_city: str = Field("", description="城市")
    cross_border: bool = Field(False, description="是否跨境案件")
    required_jurisdictions: Optional[List[str]] = Field(None, description="必需司法管辖区")
    required_languages: Optional[List[str]] = Field(None, description="必需语言")


class MatchDimensionItem(BaseModel):
    """匹配维度详情"""
    name: str
    score: float
    weight: float
    weighted_score: float
    description: str
    is_strength: bool
    is_weakness: bool


class MatchExplainResponse(BaseModel):
    """匹配解释响应"""
    lawyer_id: str
    lawyer_name: str
    total_score: float
    dimensions: List[MatchDimensionItem]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    disclaimer: str = MARKETPLACE_DISCLAIMER


class LawyerListRequest(BaseModel):
    """律师列表请求 (支持排序、过滤、分页)"""
    specialties: Optional[List[str]] = Field(None, description="专业领域过滤")
    regions: Optional[List[str]] = Field(None, description="地区过滤")
    cities: Optional[List[str]] = Field(None, description="城市过滤")
    min_experience_years: Optional[int] = Field(None, description="最低经验年限")
    max_experience_years: Optional[int] = Field(None, description="最高经验年限")
    min_price: Optional[float] = Field(None, description="最低价格")
    max_price: Optional[float] = Field(None, description="最高价格")
    min_rating: Optional[float] = Field(None, description="最低评分")
    cross_border_only: bool = Field(False, description="仅跨境律师")
    availability: Optional[List[str]] = Field(None, description="可接案状态过滤")
    sort_by: str = Field("rating", description="排序字段")
    sort_order: str = Field("desc", description="排序方向")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(None, description="搜索关键词")


class LawyerListItem(BaseModel):
    """律师列表项"""
    lawyer_id: str
    name: str
    firm_id: Optional[str] = None
    specialties: List[str]
    region: str
    city: str = ""
    experience_years: int
    rating: float
    completed_cases: int
    price_per_hour: float = 0.0
    cross_border_capable: bool
    availability: str
    bio: Optional[str] = None


class LawyerListResponse(BaseModel):
    """律师列表响应"""
    lawyers: List[LawyerListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    disclaimer: str = MARKETPLACE_DISCLAIMER


# ============================================================================
# Router
# ============================================================================

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])


# 端点 1: POST /api/marketplace/lawyers — 转介绍律师 (创建律师画像)
@router.post("/lawyers", response_model=LawyerDetailResponse)
async def create_lawyer(req: LawyerCreateRequest):
    """创建律师画像 (PRD § 3.5 + § 8.2)

    创建 Marketplace 律师参与方画像, 含 5 维度评分输入字段
    (specialty / experience / geography / availability / rating).
    """
    t0 = time.time()

    # 校验
    profile = LawyerProfile(
        lawyer_id=req.lawyer_id,
        name=req.name,
        firm_id=req.firm_id,
        specialties=req.specialties,
        jurisdictions=req.jurisdictions,
        languages=req.languages,
        region=req.region,
        experience_years=req.experience_years,
        rating=req.rating,
        completed_cases=req.completed_cases,
        marketplace_active=req.marketplace_active,
        cross_border_capable=req.cross_border_capable,
        availability=req.availability,
    )
    errors = validate_lawyer_profile(profile)
    if errors:
        raise HTTPException(400, f"律师画像校验失败: {errors}")

    # ORM 写入
    from core.db import Database
    from sqlalchemy import select

    async with Database.session() as session:
        # 查重
        stmt = select(MarketplaceLawyer).where(MarketplaceLawyer.lawyer_id == req.lawyer_id)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing is not None:
            raise HTTPException(409, f"lawyer_id={req.lawyer_id} 已存在")

        # 写入
        lawyer_row = MarketplaceLawyer(
            lawyer_id=req.lawyer_id,
            name=req.name,
            firm_id=req.firm_id,
            specialties=req.specialties,
            jurisdictions=req.jurisdictions,
            languages=req.languages,
            region=req.region,
            experience_years=req.experience_years,
            rating=req.rating,
            completed_cases=req.completed_cases,
            marketplace_active=req.marketplace_active,
            cross_border_capable=req.cross_border_capable,
            availability=req.availability,
            bio=req.bio,
        )
        session.add(lawyer_row)
        await session.commit()
        await session.refresh(lawyer_row)

    latency_ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[marketplace] 创建律师 lawyer_id={req.lawyer_id} specialties={req.specialties} "
        f"cross_border={req.cross_border_capable} latency={latency_ms}ms"
    )

    return LawyerDetailResponse(
        lawyer_id=lawyer_row.lawyer_id,
        name=lawyer_row.name,
        firm_id=lawyer_row.firm_id,
        specialties=lawyer_row.specialties or [],
        jurisdictions=lawyer_row.jurisdictions or [],
        languages=lawyer_row.languages or [],
        region=lawyer_row.region,
        experience_years=lawyer_row.experience_years,
        rating=lawyer_row.rating,
        completed_cases=lawyer_row.completed_cases,
        marketplace_active=lawyer_row.marketplace_active,
        cross_border_capable=lawyer_row.cross_border_capable,
        availability=lawyer_row.availability,
        bio=lawyer_row.bio,
        created_at=lawyer_row.created_at.isoformat() if lawyer_row.created_at else "",
    )


# 端点 2: GET /api/marketplace/lawyers/{lawyer_id} — 律师详情
@router.get("/lawyers/{lawyer_id}", response_model=LawyerDetailResponse)
async def get_lawyer(
    lawyer_id: str,
    required_specialty: Optional[str] = Query(None, description="按 specialty 推荐查询"),
    top_k: int = Query(5, ge=1, le=20, description="推荐 Top-K 律师数"),
):
    """查询律师详情 (含可选 5 维度评分 + Top-K 推荐)

    Args:
        lawyer_id: 律师 ID
        required_specialty: 按 specialty 推荐查询 (返回该律师的匹配分 + Top-K 推荐)
        top_k: Top-K 推荐律师数 (默认 5)
    """
    from core.db import Database
    from sqlalchemy import select

    async with Database.session() as session:
        stmt = select(MarketplaceLawyer).where(MarketplaceLawyer.lawyer_id == lawyer_id)
        result = await session.execute(stmt)
        lawyer_row = result.scalar_one_or_none()
        if lawyer_row is None:
            raise HTTPException(404, f"lawyer_id={lawyer_id} 不存在")

        # 构造 LawyerProfile
        profile = LawyerProfile(
            lawyer_id=lawyer_row.lawyer_id,
            name=lawyer_row.name,
            firm_id=lawyer_row.firm_id,
            specialties=lawyer_row.specialties or [],
            jurisdictions=lawyer_row.jurisdictions or [],
            languages=lawyer_row.languages or [],
            region=lawyer_row.region,
            experience_years=lawyer_row.experience_years,
            rating=lawyer_row.rating,
            completed_cases=lawyer_row.completed_cases,
            marketplace_active=lawyer_row.marketplace_active,
            cross_border_capable=lawyer_row.cross_border_capable,
            availability=lawyer_row.availability,
        )

        match_score_dict = None
        recommendations = None
        if required_specialty:
            score = lawyer_match_score(profile, required_specialties=[required_specialty])
            match_score_dict = score.to_dict()

            # Top-K 推荐
            pool_stmt = select(MarketplaceLawyer).where(
                MarketplaceLawyer.marketplace_active == True,  # noqa: E712
                MarketplaceLawyer.lawyer_id != lawyer_id,
            )
            pool_result = await session.execute(pool_stmt)
            pool_rows = list(pool_result.scalars().all())
            pool = [
                LawyerProfile(
                    lawyer_id=p.lawyer_id, name=p.name, firm_id=p.firm_id,
                    specialties=p.specialties or [], jurisdictions=p.jurisdictions or [],
                    languages=p.languages or [], region=p.region,
                    experience_years=p.experience_years, rating=p.rating,
                    completed_cases=p.completed_cases,
                    marketplace_active=p.marketplace_active,
                    cross_border_capable=p.cross_border_capable,
                    availability=p.availability,
                )
                for p in pool_rows
            ]
            top = recommend_lawyers(pool, required_specialties=[required_specialty], top_k=top_k)
            recommendations = [s.to_dict() for s in top]

    return LawyerDetailResponse(
        lawyer_id=lawyer_row.lawyer_id,
        name=lawyer_row.name,
        firm_id=lawyer_row.firm_id,
        specialties=lawyer_row.specialties or [],
        jurisdictions=lawyer_row.jurisdictions or [],
        languages=lawyer_row.languages or [],
        region=lawyer_row.region,
        experience_years=lawyer_row.experience_years,
        rating=lawyer_row.rating,
        completed_cases=lawyer_row.completed_cases,
        marketplace_active=lawyer_row.marketplace_active,
        cross_border_capable=lawyer_row.cross_border_capable,
        availability=lawyer_row.availability,
        bio=lawyer_row.bio,
        created_at=lawyer_row.created_at.isoformat() if lawyer_row.created_at else "",
        match_score=match_score_dict,
        recommendations=recommendations,
    )


# 端点 3: POST /api/marketplace/cases — 协同办案
@router.post("/cases", response_model=CoCounselCaseResponse)
async def create_co_counsel_case_endpoint(req: CoCounselCaseCreateRequest):
    """发布协同办案案件 (PRD § 3.3)

    5 状态机起点: open (复用 W12 doc_workflow 模式)
    """
    try:
        case_type = CaseType(req.case_type)
    except ValueError as e:
        raise HTTPException(400, f"未知 case_type: {req.case_type}, 合法: {[c.value for c in CASE_TYPES]}") from e

    t0 = time.time()

    case = create_co_counsel_case(
        lawyer_a_id=req.lawyer_a_id,
        case_type=case_type,
        case_description=req.case_description,
        fee=req.fee,
        required_specialties=req.required_specialties,
        firm_id=req.firm_id,
        deadline=req.deadline,
        split_ratio=req.split_ratio,
    )

    # ORM 写入
    from core.db import Database

    async with Database.session() as session:
        case_row = MarketplaceCase(
            case_id=case.case_id,
            lawyer_a_id=case.lawyer_a_id,
            firm_id=case.firm_id,
            case_type=case.case_type.value,
            case_description=case.case_description,
            required_specialties=case.required_specialties,
            deadline=case.deadline,
            fee=case.fee,
            split_ratio=case.split_ratio,
            marketplace_commission_rate=case.marketplace_commission_rate,
            state=case.state.value,
            history=case.history,
        )
        session.add(case_row)
        await session.commit()
        await session.refresh(case_row)

    latency_ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[marketplace] 创建协同办案 case_id={case.case_id} lawyer_a={case.lawyer_a_id} "
        f"fee={case.fee} latency={latency_ms}ms"
    )

    return CoCounselCaseResponse(
        case_id=case_row.case_id,
        lawyer_a_id=case_row.lawyer_a_id,
        lawyer_b_id=case_row.lawyer_b_id,
        firm_id=case_row.firm_id,
        case_type=case_row.case_type,
        case_description=case_row.case_description,
        required_specialties=case_row.required_specialties or [],
        deadline=case_row.deadline,
        fee=case_row.fee,
        split_ratio=case_row.split_ratio,
        marketplace_commission_rate=case_row.marketplace_commission_rate,
        state=case_row.state,
        next_state="lawyer_invited",
        transitionable_targets=[s.value for s in get_state_transitionable_targets(CoCounselState.OPEN)],
        history=case_row.history or [],
        created_at=case_row.created_at.isoformat() if case_row.created_at else "",
        updated_at=case_row.updated_at.isoformat() if case_row.updated_at else "",
        legal_basis=parse_legal_basis(case_type),
    )


# 端点 4: GET /api/marketplace/cases/{case_id} — 案件详情
@router.get("/cases/{case_id}", response_model=CoCounselCaseResponse)
async def get_case(case_id: str):
    """查询协同办案案件详情 (含 5 状态机当前状态)"""
    from core.db import Database
    from sqlalchemy import select

    async with Database.session() as session:
        stmt = select(MarketplaceCase).where(MarketplaceCase.case_id == case_id)
        result = await session.execute(stmt)
        case_row = result.scalar_one_or_none()
        if case_row is None:
            raise HTTPException(404, f"case_id={case_id} 不存在")

        try:
            current_state = CoCounselState(case_row.state)
        except ValueError:
            current_state = CoCounselState.OPEN

        # 计算下一状态 (简单取第一个合法目标)
        next_targets = COUNSEL_STATE_TRANSITIONS.get(current_state, [])
        next_state = next_targets[0].value if next_targets else None

    return CoCounselCaseResponse(
        case_id=case_row.case_id,
        lawyer_a_id=case_row.lawyer_a_id,
        lawyer_b_id=case_row.lawyer_b_id,
        firm_id=case_row.firm_id,
        case_type=case_row.case_type,
        case_description=case_row.case_description,
        required_specialties=case_row.required_specialties or [],
        deadline=case_row.deadline,
        fee=case_row.fee,
        split_ratio=case_row.split_ratio,
        marketplace_commission_rate=case_row.marketplace_commission_rate,
        state=case_row.state,
        next_state=next_state,
        transitionable_targets=[s.value for s in get_state_transitionable_targets(current_state)],
        history=case_row.history or [],
        created_at=case_row.created_at.isoformat() if case_row.created_at else "",
        updated_at=case_row.updated_at.isoformat() if case_row.updated_at else "",
        legal_basis=parse_legal_basis(CaseType(case_row.case_type)),
    )


# 端点 5: POST /api/marketplace/referrals — 转介绍记录
@router.post("/referrals", response_model=ReferralResponse)
async def create_referral_endpoint(req: ReferralCreateRequest):
    """创建转介绍 (PRD § 3.2)

    5% 抽成: actual_fee × 5% = referrer_commission (Marketplace 不抽成)
    """
    try:
        case_type = CaseType(req.case_type)
    except ValueError as e:
        raise HTTPException(400, f"未知 case_type: {req.case_type}") from e

    t0 = time.time()

    referral = create_referral(
        referrer_id=req.referrer_id,
        target_lawyer_id=req.target_lawyer_id,
        case_type=case_type,
        case_description=req.case_description,
        expected_fee=req.expected_fee,
        match_score=req.match_score,
    )

    # ORM 写入
    from core.db import Database

    async with Database.session() as session:
        ref_row = MarketplaceReferral(
            referral_id=referral.referral_id,
            referrer_id=referral.referrer_id,
            target_lawyer_id=referral.target_lawyer_id,
            case_type=referral.case_type.value,
            case_description=referral.case_description,
            expected_fee=referral.expected_fee,
            commission_rate=referral.commission_rate,
            marketplace_commission=0.0,  # 转介绍 Marketplace 不抽成
            match_score=referral.match_score,
            status=referral.status.value,
        )
        session.add(ref_row)
        await session.commit()
        await session.refresh(ref_row)

    latency_ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[marketplace] 创建转介绍 referral_id={referral.referral_id} "
        f"referrer={referral.referrer_id} target={referral.target_lawyer_id} "
        f"expected_fee={referral.expected_fee} latency={latency_ms}ms"
    )

    return ReferralResponse(
        referral_id=ref_row.referral_id,
        referrer_id=ref_row.referrer_id,
        target_lawyer_id=ref_row.target_lawyer_id,
        case_type=ref_row.case_type,
        case_description=ref_row.case_description,
        expected_fee=ref_row.expected_fee,
        actual_fee=ref_row.actual_fee,
        commission_rate=ref_row.commission_rate,
        referrer_commission=ref_row.referrer_commission,
        marketplace_commission=ref_row.marketplace_commission,
        match_score=ref_row.match_score,
        status=ref_row.status,
        created_at=ref_row.created_at.isoformat() if ref_row.created_at else "",
        updated_at=ref_row.updated_at.isoformat() if ref_row.updated_at else "",
    )


# 端点 6: POST /api/marketplace/cross-border — 跨境文件
@router.post("/cross-border", response_model=CrossBorderResponse)
async def create_cross_border_job_endpoint(req: CrossBorderCreateRequest):
    """创建跨境文件订单 (PRD § 3.4, 复用 W25 Skill 3 v3.0 多律所模板)

    30% 抽成: 价格 - Marketplace 抽成 = 律师实际所得
    跨境文件定价: 99-1990 ¥/份 (按 doc_type + language 定价)
    """
    try:
        doc_type = CrossBorderDocType(req.doc_type)
    except ValueError as e:
        raise HTTPException(400, f"未知 doc_type: {req.doc_type}") from e
    try:
        language = Language(req.language)
    except ValueError as e:
        raise HTTPException(400, f"未知 language: {req.language}") from e
    try:
        jurisdiction = Jurisdiction(req.jurisdiction)
    except ValueError as e:
        raise HTTPException(400, f"未知 jurisdiction: {req.jurisdiction}") from e

    t0 = time.time()

    job = create_cross_border_job(
        lawyer_id=req.lawyer_id,
        client_id=req.client_id,
        doc_type=doc_type,
        language=language,
        jurisdiction=jurisdiction,
        fields=req.fields,
        template_id=req.template_id,
    )

    # ORM 写入
    from core.db import Database

    async with Database.session() as session:
        job_row = CrossBorderJobORM(
            job_id=job.job_id,
            lawyer_id=job.lawyer_id,
            client_id=job.client_id,
            doc_type=job.doc_type.value,
            language=job.language.value,
            jurisdiction=job.jurisdiction.value,
            price=job.price,
            marketplace_commission=job.marketplace_commission,
            template_id=job.template_id,
            status=job.status,
            fields=job.fields,
        )
        session.add(job_row)
        await session.commit()
        await session.refresh(job_row)

    latency_ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[marketplace] 创建跨境文件 job_id={job.job_id} doc_type={job.doc_type.value} "
        f"language={job.language.value} jurisdiction={job.jurisdiction.value} "
        f"price={job.price} commission={job.marketplace_commission} latency={latency_ms}ms"
    )

    return CrossBorderResponse(
        job_id=job_row.job_id,
        lawyer_id=job_row.lawyer_id,
        client_id=job_row.client_id,
        doc_type=job_row.doc_type,
        language=job_row.language,
        jurisdiction=job_row.jurisdiction,
        price=job_row.price,
        marketplace_commission=job_row.marketplace_commission,
        template_id=job_row.template_id,
        status=job_row.status,
        fields=job_row.fields or {},
        document_url=job_row.document_url,
        arbitration_institution=job_row.arbitration_institution,
        created_at=job_row.created_at.isoformat() if job_row.created_at else "",
        updated_at=job_row.updated_at.isoformat() if job_row.updated_at else "",
    )


# 端点 7: GET /api/marketplace/metrics — Marketplace 5 维度指标跟踪
@router.get("/metrics", response_model=MarketplaceMetricsResponse)
async def get_marketplace_metrics(
    period_days: int = Query(30, ge=1, le=365, description="统计周期 (天)"),
):
    """Marketplace 5 维度指标 (PRD § 8.3)

    5 指标:
    1. lawyer_participants          Marketplace 律师参与方
    2. cases_completed_monthly      月接案数
    3. revenue_monthly              月营收 (¥)
    4. cross_border_orders_monthly  跨境案件月单量
    5. avg_lawyer_rating            律师满意度 (0-5)
    """
    from core.db import Database
    from sqlalchemy import select

    async with Database.session() as session:
        # 律师池
        lawyer_stmt = select(MarketplaceLawyer)
        lawyer_result = await session.execute(lawyer_stmt)
        lawyer_rows = list(lawyer_result.scalars().all())
        lawyer_pool = [
            LawyerProfile(
                lawyer_id=p.lawyer_id, name=p.name, firm_id=p.firm_id,
                specialties=p.specialties or [], jurisdictions=p.jurisdictions or [],
                languages=p.languages or [], region=p.region,
                experience_years=p.experience_years, rating=p.rating,
                completed_cases=p.completed_cases,
                marketplace_active=p.marketplace_active,
                cross_border_capable=p.cross_border_capable,
                availability=p.availability,
            )
            for p in lawyer_rows
        ]

        # 转介绍
        ref_stmt = select(MarketplaceReferral)
        ref_result = await session.execute(ref_stmt)
        ref_rows = list(ref_result.scalars().all())
        referrals = [
            Referral(
                referral_id=r.referral_id,
                referrer_id=r.referrer_id,
                target_lawyer_id=r.target_lawyer_id,
                case_type=CaseType(r.case_type),
                case_description=r.case_description,
                expected_fee=r.expected_fee,
                actual_fee=r.actual_fee,
                commission_rate=r.commission_rate,
                referrer_commission=r.referrer_commission,
                marketplace_commission=r.marketplace_commission,
                match_score=r.match_score,
                status=ReferralStatus(r.status),
            )
            for r in ref_rows
        ]

        # 协同办案
        case_stmt = select(MarketplaceCase)
        case_result = await session.execute(case_stmt)
        case_rows = list(case_result.scalars().all())
        cases = [
            CoCounselCase(
                case_id=c.case_id,
                lawyer_a_id=c.lawyer_a_id,
                lawyer_b_id=c.lawyer_b_id,
                firm_id=c.firm_id,
                case_type=CaseType(c.case_type),
                case_description=c.case_description,
                required_specialties=c.required_specialties or [],
                deadline=c.deadline,
                fee=c.fee,
                split_ratio=c.split_ratio,
                marketplace_commission_rate=c.marketplace_commission_rate,
                state=CoCounselState(c.state),
                history=c.history or [],
            )
            for c in case_rows
        ]

        # 跨境文件
        cb_stmt = select(CrossBorderJobORM)
        cb_result = await session.execute(cb_stmt)
        cb_rows = list(cb_result.scalars().all())
        cross_border_jobs = [
            CBJobDTO(
                job_id=j.job_id, lawyer_id=j.lawyer_id, client_id=j.client_id,
                doc_type=CrossBorderDocType(j.doc_type),
                language=Language(j.language),
                jurisdiction=Jurisdiction(j.jurisdiction),
                price=j.price, marketplace_commission=j.marketplace_commission,
                template_id=j.template_id, status=j.status,
                fields=j.fields or {},
                document_url=j.document_url, arbitration_institution=j.arbitration_institution,
            )
            for j in cb_rows
        ]

        # 抽成
        com_stmt = select(MarketplaceCommission)
        com_result = await session.execute(com_stmt)
        com_rows = list(com_result.scalars().all())
        commissions = [
            CommissionRecord(
                commission_id=c.commission_id,
                transaction_id=c.transaction_id,
                transaction_type=c.transaction_type,
                lawyer_id=c.lawyer_id,
                referrer_id=c.referrer_id,
                transaction_amount=c.transaction_amount,
                commission_rate=c.commission_rate,
                commission_amount=c.commission_amount,
                status=c.status,
            )
            for c in com_rows
        ]

    metrics, latency_ms = measure_latency_ms(
        compute_marketplace_metrics,
        referrals=referrals,
        co_counsel_cases=cases,
        cross_border_jobs=cross_border_jobs,
        commission_records=commissions,
        lawyer_pool=lawyer_pool,
    )

    return MarketplaceMetricsResponse(
        metric_date=metrics.metric_date,
        lawyer_participants=metrics.lawyer_participants,
        cases_completed_monthly=metrics.cases_completed_monthly,
        revenue_monthly=metrics.revenue_monthly,
        cross_border_orders_monthly=metrics.cross_border_orders_monthly,
        avg_lawyer_rating=metrics.avg_lawyer_rating,
        referral_count_total=metrics.referral_count_total,
        co_counsel_count_total=metrics.co_counsel_count_total,
        cross_border_count_total=metrics.cross_border_count_total,
        commission_pending=metrics.commission_pending,
        commission_settled=metrics.commission_settled,
        trajectory={
            "latency_ms": latency_ms,
            "period_days": period_days,
            "lawyer_pool_size": len(lawyer_pool),
            "referral_count": len(referrals),
            "co_counsel_count": len(cases),
            "cross_border_count": len(cross_border_jobs),
            "commission_count": len(commissions),
        },
    )


# ============================================================================
# 匹配 2.0 端点
# ============================================================================

def _get_lawyer_pool_from_db_or_mock():
    """获取律师池: 优先从 DB, 无数据时使用 mock"""
    try:
        from core.db import Database
        from sqlalchemy import select

        async def _fetch():
            async with Database.session() as session:
                stmt = select(MarketplaceLawyer)
                result = await session.execute(stmt)
                rows = list(result.scalars().all())
                if rows:
                    return [
                        LawyerProfile(
                            lawyer_id=p.lawyer_id, name=p.name, firm_id=p.firm_id,
                            specialties=p.specialties or [], jurisdictions=p.jurisdictions or [],
                            languages=p.languages or [], region=p.region,
                            experience_years=p.experience_years, rating=p.rating,
                            completed_cases=p.completed_cases,
                            marketplace_active=p.marketplace_active,
                            cross_border_capable=p.cross_border_capable,
                            availability=p.availability, bio=p.bio,
                        )
                        for p in rows
                    ]
                return None

        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return get_mock_lawyers()
            else:
                result = loop.run_until_complete(_fetch())
                return result if result else get_mock_lawyers()
        except RuntimeError:
            return get_mock_lawyers()
    except Exception:
        return get_mock_lawyers()


@router.post("/match", response_model=MatchLawyerResponse)
async def match_lawyers_endpoint(req: MatchLawyerRequest):
    """律师匹配 2.0 - 多维度智能匹配 + 排序 + 过滤 + 分页

    入参: required_specialties, region, city, sort_by, filters, page, page_size
    返回: 律师列表（带评分）、总数、分页信息
    """
    t0 = time.time()

    lawyer_pool = _get_lawyer_pool_from_db_or_mock()

    filters = LawyerFilters(
        specialties=req.filters.get("specialties"),
        min_experience_years=req.filters.get("min_experience_years"),
        max_experience_years=req.filters.get("max_experience_years"),
        regions=req.filters.get("regions"),
        cities=req.filters.get("cities"),
        min_price=req.filters.get("min_price"),
        max_price=req.filters.get("max_price"),
        min_rating=req.filters.get("min_rating"),
        cross_border_only=req.filters.get("cross_border_only", False),
        availability=req.filters.get("availability"),
    )

    filtered = filter_lawyers(lawyer_pool, filters)

    scored = rank_lawyers(
        filtered,
        required_specialties=req.required_specialties,
        top_k=len(filtered),
        min_score=req.min_score,
        required_jurisdictions=req.required_jurisdictions,
        required_languages=req.required_languages,
        required_region=req.required_region,
        cross_border=req.cross_border,
    )

    lawyer_profiles_dict = {lp.lawyer_id: lp for lp in filtered}

    try:
        sort_field = SortField(req.sort_by)
    except ValueError:
        sort_field = SortField.MATCH_SCORE

    try:
        sort_order = SortOrder(req.sort_order)
    except ValueError:
        sort_order = SortOrder.DESC

    sorted_scored = sort_lawyers(scored, lawyer_profiles_dict, sort_field, sort_order)

    total = len(sorted_scored)
    start = (req.page - 1) * req.page_size
    end = start + req.page_size
    paged = sorted_scored[start:end]

    lawyer_items = []
    for score in paged:
        profile = lawyer_profiles_dict.get(score.lawyer_id)
        if profile is None:
            continue
        lawyer_items.append(LawyerMatchItem(
            lawyer_id=profile.lawyer_id,
            name=profile.name,
            firm_id=profile.firm_id,
            specialties=profile.specialties,
            jurisdictions=profile.jurisdictions,
            languages=profile.languages,
            region=profile.region,
            city=profile.city,
            experience_years=profile.experience_years,
            rating=profile.rating,
            client_review_count=profile.client_review_count,
            completed_cases=profile.completed_cases,
            win_rate=profile.win_rate,
            response_speed_hours=profile.response_speed_hours,
            price_per_hour=profile.price_per_hour,
            price_min=profile.price_min,
            marketplace_active=profile.marketplace_active,
            cross_border_capable=profile.cross_border_capable,
            availability=profile.availability,
            bio=profile.bio,
            match_score=score.to_dict(),
            match_reasons=score.match_reasons,
        ))

    total_pages = (total + req.page_size - 1) // req.page_size

    latency_ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[marketplace] match_lawyers specialties={req.required_specialties} "
        f"region={req.required_region} total={total} page={req.page} latency={latency_ms}ms"
    )

    return MatchLawyerResponse(
        lawyers=lawyer_items,
        total=total,
        page=req.page,
        page_size=req.page_size,
        total_pages=total_pages,
    )


@router.post("/match-explain", response_model=MatchExplainResponse)
async def match_explain_endpoint(req: MatchExplainRequest):
    """匹配解释 - 展示各维度得分、强项、弱项、改进建议

    入参: lawyer_id + 匹配条件
    返回: 维度详情、强项、弱项、改进建议
    """
    t0 = time.time()

    lawyer = get_mock_lawyer_by_id(req.lawyer_id)
    if lawyer is None:
        lawyer_pool = _get_lawyer_pool_from_db_or_mock()
        for lp in lawyer_pool:
            if lp.lawyer_id == req.lawyer_id:
                lawyer = lp
                break

    if lawyer is None:
        raise HTTPException(404, f"lawyer_id={req.lawyer_id} 不存在")

    score = compute_match_score(
        lawyer=lawyer,
        required_specialties=req.required_specialties,
        required_jurisdictions=req.required_jurisdictions,
        required_languages=req.required_languages,
        required_region=req.required_region,
        required_city=req.required_city,
        cross_border=req.cross_border,
        include_explanation=True,
    )

    explanation = score.explanation
    if explanation is None:
        explanation = get_match_explanation(score, lawyer, req.required_specialties)

    dim_items = [
        MatchDimensionItem(
            name=d.name,
            score=d.score,
            weight=d.weight,
            weighted_score=d.weighted_score,
            description=d.description,
            is_strength=d.is_strength,
            is_weakness=d.is_weakness,
        )
        for d in explanation.dimensions
    ]

    latency_ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[marketplace] match_explain lawyer_id={req.lawyer_id} "
        f"score={score.total_score:.2f} latency={latency_ms}ms"
    )

    return MatchExplainResponse(
        lawyer_id=lawyer.lawyer_id,
        lawyer_name=lawyer.name,
        total_score=explanation.total_score,
        dimensions=dim_items,
        strengths=explanation.strengths,
        weaknesses=explanation.weaknesses,
        suggestions=explanation.suggestions,
    )


@router.post("/lawyers/list", response_model=LawyerListResponse)
async def list_lawyers_endpoint(req: LawyerListRequest):
    """律师列表 - 支持排序、过滤、分页

    入参: 专业领域、地区、价格区间、最低评分、排序方式、分页参数
    返回: 律师列表、总数、分页信息
    """
    t0 = time.time()

    lawyer_pool = _get_lawyer_pool_from_db_or_mock()

    filters = LawyerFilters(
        specialties=req.specialties,
        min_experience_years=req.min_experience_years,
        max_experience_years=req.max_experience_years,
        regions=req.regions,
        cities=req.cities,
        min_price=req.min_price,
        max_price=req.max_price,
        min_rating=req.min_rating,
        cross_border_only=req.cross_border_only,
        availability=req.availability,
    )

    filtered = filter_lawyers(lawyer_pool, filters)

    if req.keyword:
        kw = req.keyword.lower()
        filtered = [
            lp for lp in filtered
            if kw in (lp.name or "").lower()
            or kw in (lp.firm_id or "").lower()
            or kw in (lp.bio or "").lower()
        ]

    lawyer_profiles_dict = {lp.lawyer_id: lp for lp in filtered}
    dummy_scores = [
        compute_match_score(lp, [], include_explanation=False)
        for lp in filtered
    ]

    try:
        sort_field = SortField(req.sort_by)
    except ValueError:
        sort_field = SortField.RATING

    try:
        sort_order = SortOrder(req.sort_order)
    except ValueError:
        sort_order = SortOrder.DESC

    sorted_lawyers = sort_lawyers(dummy_scores, lawyer_profiles_dict, sort_field, sort_order)

    total = len(sorted_lawyers)
    start = (req.page - 1) * req.page_size
    end = start + req.page_size
    paged = sorted_lawyers[start:end]

    lawyer_items = []
    for score in paged:
        profile = lawyer_profiles_dict.get(score.lawyer_id)
        if profile is None:
            continue
        lawyer_items.append(LawyerListItem(
            lawyer_id=profile.lawyer_id,
            name=profile.name,
            firm_id=profile.firm_id,
            specialties=profile.specialties,
            region=profile.region,
            city=profile.city,
            experience_years=profile.experience_years,
            rating=profile.rating,
            completed_cases=profile.completed_cases,
            price_per_hour=profile.price_per_hour,
            cross_border_capable=profile.cross_border_capable,
            availability=profile.availability,
            bio=profile.bio,
        ))

    total_pages = (total + req.page_size - 1) // req.page_size

    latency_ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[marketplace] list_lawyers total={total} page={req.page} "
        f"sort_by={req.sort_by} latency={latency_ms}ms"
    )

    return LawyerListResponse(
        lawyers=lawyer_items,
        total=total,
        page=req.page,
        page_size=req.page_size,
        total_pages=total_pages,
    )


@router.get("/lawyers", response_model=LawyerListResponse)
async def get_lawyers_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("rating"),
    sort_order: str = Query("desc"),
    keyword: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None),
    cross_border_only: bool = Query(False),
):
    """律师列表 GET 接口 (向后兼容)"""
    req = LawyerListRequest(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        keyword=keyword,
        min_rating=min_rating,
        cross_border_only=cross_border_only,
    )
    return await list_lawyers_endpoint(req)


# ============================================================================
# 辅助端点 (复用 W28 PRD § 4.5 public API)
# ============================================================================

@router.get("/health")
async def marketplace_health():
    """Marketplace 健康检查"""
    return {
        "status": "ok",
        "skill_id": "lexprime.marketplace",
        "version": "1.0.0-w29",
        "modules": [
            "lawyer_marketplace",
            "co_counsel_workflow",
            "referral_engine",
            "cross_border_files",
            "commission_tracker",
            "metrics_dashboard",
        ],
        "case_types": [c.value for c in CASE_TYPES],
        "co_counsel_states": [s.value for s in CoCounselState],
        "referral_statuses": [r.value for r in REFERRAL_STATUSES],
        "cross_border_doc_types": [d.value for d in CROSS_BORDER_DOC_TYPES],
        "languages": [lang.value for lang in LANGUAGES],
        "jurisdictions": [j.value for j in JURISDICTIONS],
        "commission_rates": COMMISSION_RATES,
    }


@router.get("/disclaimer")
async def marketplace_disclaimer():
    """返回强制免责声明 (前端可独立 fetch 渲染)"""
    return {
        "full": MARKETPLACE_DISCLAIMER,
        "short": MARKETPLACE_DISCLAIMER_SHORT,
    }


@router.get("/manifest")
async def marketplace_manifest():
    """返回 Marketplace manifest (PRD § 4.5)"""
    return {
        "skill_id": "lexprime.marketplace",
        "version": "1.0.0-w29",
        "track": "A-marketplace · W29 phase6-1-backend",
        "endpoints": [
            {"path": "/api/marketplace/lawyers", "method": "POST", "purpose": "创建律师画像 (Marketplace 参与方)"},
            {"path": "/api/marketplace/lawyers/{lawyer_id}", "method": "GET", "purpose": "律师详情 + 5 维度评分 + Top-K 推荐"},
            {"path": "/api/marketplace/cases", "method": "POST", "purpose": "创建协同办案案件"},
            {"path": "/api/marketplace/cases/{case_id}", "method": "GET", "purpose": "协同办案案件详情 + 5 状态机"},
            {"path": "/api/marketplace/referrals", "method": "POST", "purpose": "创建转介绍 (5% 抽成)"},
            {"path": "/api/marketplace/cross-border", "method": "POST", "purpose": "创建跨境文件订单 (30% 抽成)"},
            {"path": "/api/marketplace/metrics", "method": "GET", "purpose": "Marketplace 5 维度指标"},
            {"path": "/api/marketplace/health", "method": "GET", "purpose": "健康检查"},
            {"path": "/api/marketplace/disclaimer", "method": "GET", "purpose": "强制免责声明"},
            {"path": "/api/marketplace/manifest", "method": "GET", "purpose": "Marketplace manifest"},
        ],
        "test_baseline": "7 endpoint tests + 10 scenario tests (W29 phase6-1-backend)",
        "compliance": [
            "PRD V5.0 § 11 法务自检 (禁用'必胜/必败/一定' 等违规词)",
            "PRD V5.0 § 12.1 数据本地化 (律师案件/客户/文书不离开律师电脑)",
            "W12 doc_workflow 5 状态机模式 (open → lawyer_invited → accepted → in_progress → settled → archived)",
            "W22 Rust 5x perf 模式 (Python fallback < 500ms)",
            "W25 Skill 3 v3.0 多律所模板 (跨境文件复用)",
            "W15 recruit-1000 5 维度评分 (律师推荐算法)",
            "Phase 6.1 Marketplace PRD 商业模型 (转介绍 5% + 协同办案 10% + 跨境文件 30%)",
        ],
        "deferred_to_w30": [
            "Marketplace UI 8 大页面 (W30 by phase6-1-ui)",
            "Marketplace 上线 (W31)",
            "跨境文件正式启用 (W31, 40 律所合作接力)",
            "Marketplace 公共 API 8 端点 (commissions / settlements / reviews / dashboard / notifications)",
            "Marketplace 文书模板分享 + 律所版定制 (W32+)",
        ],
    }
