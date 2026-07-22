"""
LexPrime API - 法律智能服务平台核心接口
============================================

LexPrime 是一款面向律师和律所的法律智能服务平台，提供类案检索、合同审查、
文书生成、律师协作等全流程法律业务支持。

本 API 服务作为 LexPrime 的核心后端接口层，基于 FastAPI 构建，
提供自动生成的 OpenAPI 文档，支持 RESTful 风格。

API 版本: 0.1.0
文档地址: /docs (Swagger UI) | /redoc (ReDoc)
服务地址: http://127.0.0.1:3847

主要功能模块:
- 判例检索: 获取法院判例数据，支持筛选和全文搜索
- 法规查询: 获取法律法规数据
- 企业查询: 获取企业工商信息
- 合同审查: AI 驱动的合同风险审查
- 文书生成: 智能法律文书生成
- Marketplace: 律师协作与转介绍平台
- AI 服务: 案件分析、文书润色、智能填空
- 日程管理: 律师日程安排
- 客户管理: 客户信息管理

认证方式: Bearer Token (JWT)
"""
import os
import json
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List, Optional, Any
from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
from loguru import logger

from core.db import Database, ESClient, Neo4jClient
from core.config import settings
from core.models import Case, Law, Company, Lawyer, Firm, FirmTimeEntry


def _get_log_file_path() -> str:
    """获取日志文件路径"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, f"frontend_{datetime.now().strftime('%Y-%m-%d')}.log")


def _write_log_entry(entry_type: str, data: dict):
    """写入日志条目到文件"""
    try:
        log_path = _get_log_file_path()
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": entry_type,
            "data": data,
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Failed to write log entry: {e}")


# ========== Pydantic 模型 ==========

class CaseOut(BaseModel):
    """判例输出模型 (精简版)

    用于判例列表展示，包含案件基本信息和评分数据。
    """
    id: int = Field(..., description="数据库主键")
    doc_id: Optional[str] = Field(None, description="文档唯一标识")
    case_id: Optional[str] = Field(None, description="案件编号")
    case_name: Optional[str] = Field(None, description="案件名称")
    court: Optional[str] = Field(None, description="审理法院")
    cause: Optional[str] = Field(None, description="案由")
    cause_category: Optional[str] = Field(None, description="案由分类")
    cause_color: Optional[str] = Field(None, description="案由颜色标记")
    judgment_date: Optional[str] = Field(None, description="判决日期 (ISO 8601)")
    year: Optional[int] = Field(None, description="判决年份")
    lex_score: Optional[int] = Field(None, description="LexPrime 评分 (0-100)")
    view_count: int = Field(..., description="查看次数")
    favorite_count: int = Field(..., description="收藏次数")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 12345,
                "doc_id": "case-abc123",
                "case_id": "(2026)京01民初123号",
                "case_name": "张三诉李四借款合同纠纷案",
                "court": "北京市第一中级人民法院",
                "cause": "借款合同纠纷",
                "cause_category": "合同纠纷",
                "cause_color": "#ef4444",
                "judgment_date": "2026-03-15",
                "year": 2026,
                "lex_score": 85,
                "view_count": 156,
                "favorite_count": 12
            }
        }


class CaseDetail(CaseOut):
    """判例详情模型

    在精简版基础上增加完整案件信息，用于案件详情页展示。
    """
    parties: Optional[str] = Field(None, description="当事人信息")
    legal_basis: Optional[str] = Field(None, description="法律依据")
    full_text: Optional[str] = Field(None, description="判决书全文")
    source: str = Field(..., description="数据来源")
    source_url: Optional[str] = Field(None, description="来源链接")
    keywords: Optional[List[str]] = Field(None, description="关键词列表")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 12345,
                "doc_id": "case-abc123",
                "case_name": "张三诉李四借款合同纠纷案",
                "court": "北京市第一中级人民法院",
                "cause": "借款合同纠纷",
                "parties": "原告：张三；被告：李四",
                "legal_basis": "《民法典》第五百七十七条",
                "full_text": "原告张三与被告李四于2025年3月签订借款合同...",
                "source": "中国裁判文书网",
                "source_url": "http://wenshu.court.gov.cn/xxx",
                "keywords": ["借款", "合同", "违约"]
            }
        }


class LawOut(BaseModel):
    """法规输出模型"""
    id: int = Field(..., description="数据库主键")
    law_id: str = Field(..., description="法规编号")
    title: str = Field(..., description="法规名称")
    law_type: str = Field(..., description="法规类型")
    status: Optional[str] = Field(None, description="效力状态")
    issue_date: Optional[str] = Field(None, description="发布日期")
    effective_date: Optional[str] = Field(None, description="生效日期")
    level: Optional[int] = Field(None, description="效力层级")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1001,
                "law_id": "民法典",
                "title": "中华人民共和国民法典",
                "law_type": "法律",
                "status": "现行有效",
                "issue_date": "2020-05-28",
                "effective_date": "2021-01-01",
                "level": 1
            }
        }


class CompanyOut(BaseModel):
    """企业信息输出模型"""
    id: int = Field(..., description="数据库主键")
    unified_id: str = Field(..., description="统一社会信用代码")
    company_name: str = Field(..., description="企业名称")
    legal_rep: Optional[str] = Field(None, description="法定代表人")
    business_status: Optional[str] = Field(None, description="经营状态")
    industry: Optional[str] = Field(None, description="所属行业")
    region: Optional[str] = Field(None, description="所属地区")
    is_zxgk: bool = Field(..., description="是否在执行公开名单")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 2001,
                "unified_id": "91110101MA01ABCDEF",
                "company_name": "北京示例科技有限公司",
                "legal_rep": "王五",
                "business_status": "存续",
                "industry": "软件和信息技术服务业",
                "region": "北京市",
                "is_zxgk": False
            }
        }


class SearchRequest(BaseModel):
    """全文搜索请求模型"""
    query: str = Field(..., min_length=2, max_length=200, description="搜索关键词 (至少2个字符)")
    index: str = Field("cases", pattern="^(cases|laws|companies)$", description="搜索索引 (cases/laws/companies)")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页数量")
    filters: Optional[dict] = Field(None, description="额外过滤条件")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "借款合同 违约",
                "index": "cases",
                "page": 1,
                "size": 20,
                "filters": {"cause_category": "合同纠纷"}
            }
        }


class TimeEntryIn(BaseModel):
    """工时记录输入模型"""
    lawyer_id: str = Field(..., description="律师 ID")
    case_id: Optional[int] = Field(None, description="关联案件 ID")
    entry_date: str = Field(..., description="工作日期 (YYYY-MM-DD)")
    hours: float = Field(..., ge=0, le=24, description="工时数")
    description: Optional[str] = Field(None, description="工作描述")
    billable: bool = Field(True, description="是否可计费")
    rate: Optional[float] = Field(None, ge=0, description="小时费率")

    class Config:
        json_schema_extra = {
            "example": {
                "lawyer_id": "L001",
                "case_id": 12345,
                "entry_date": "2026-03-15",
                "hours": 4.5,
                "description": "起草起诉状",
                "billable": True,
                "rate": 800.0
            }
        }


# ========== App lifespan ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.init()
    await ESClient.init()
    await Neo4jClient.init()
    logger.info("LexPrime API started")
    yield
    await Database.close()
    await ESClient.close()
    await Neo4jClient.close()
    logger.info("LexPrime API stopped")


app = FastAPI(
    title="LexPrime API",
    description="""
# LexPrime API - 法律智能服务平台

LexPrime 是一款面向律师和律所的法律智能服务平台，提供全流程法律业务支持。

## 核心功能模块

### 📚 判例检索
- 获取法院判例数据
- 支持多维度筛选
- Elasticsearch 全文搜索

### 📖 法规查询
- 法律法规数据查询
- 按类型/状态筛选

### 🏢 企业查询
- 企业工商信息
- 执行公开状态查询

### 📋 合同审查
- AI 驱动的合同风险审查
- OCR 图片合同识别
- 规则引擎审查

### 📝 文书生成
- 智能法律文书生成
- 多模板支持

### 👥 Marketplace
- 律师协作平台
- 转介绍系统
- 跨境文件服务

### 🤖 AI 服务
- 案件分析摘要
- 文书润色
- 智能填空

## 快速开始

```bash
# 启动服务
uvicorn api.main:app --host 0.0.0.0 --port 3847

# 访问文档
# Swagger UI: http://localhost:3847/docs
# ReDoc: http://localhost:3847/redoc
```

## 认证

所有 API 接口需要在请求头中携带 Bearer Token:

```
Authorization: Bearer <your_token>
```
""",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志中间件
try:
    from api.logging_middleware import logging_middleware
    app.middleware("http")(logging_middleware)
    logger.info("请求日志中间件已注册")
except Exception as e:
    logger.warning(f"请求日志中间件加载失败 (非致命): {e}")


# ========== Skill Hub 端点 (Track E) ==========
# 类案检索 Skill (W7 实现)
try:
    from api.skill_endpoints import router as skill_router
    app.include_router(skill_router)
    logger.info("Skill Hub: 类案检索 router registered")
except Exception as e:
    logger.warning(f"Skill Hub 类案检索 router 加载失败 (非致命): {e}")

# 合同风险审查 Skill (W5 实施 · lex-coder)
try:
    from api.contract_review_router import router as contract_review_router
    app.include_router(contract_review_router)
    logger.info("Skill Hub: 合同风险审查 (Skill 2) router registered")
except Exception as e:
    logger.warning(f"Skill Hub 合同审查 router 加载失败 (非致命): {e}")

# 公测邀请码 Router (W6 实施 · lex-design)
# 端点: POST /api/invite/generate (admin) / POST /api/invite/redeem (用户)
try:
    from api.invite_router import router as invite_router
    app.include_router(invite_router)
    logger.info("Marketing: 公测邀请码 router registered (W6)")
except Exception as e:
    logger.warning(f"Marketing 邀请码 router 加载失败 (非致命): {e}")

# W6 律师评审 Score App (lex-coder · 2026-06-29)
# 5 律师 × 5 测试合同 = 25 条评分
# 端点: /api/review/contracts, /api/review/submit-score, /api/review/my-scores, /api/review/summary
# W7: +3 端点 (POST /question, GET /questions, GET /board)
try:
    from api.review_router import router as review_router
    app.include_router(review_router)
    logger.info("W6 律师评审 Score App router registered (W7 扩 3 端点)")
except Exception as e:
    logger.warning(f"W6 律师评审 Score App router 加载失败 (非致命): {e}")

# W8 (lex-coder · 2026-06-29) PRD backlog ticket 系统
# A2: 把 W7 review_questions 表问题 → prd_backlog 表 ticket, 给 plan engine 自动调度
# 端点: /api/backlog/from-question, /api/backlog/list, /api/backlog/{id}/assign, /api/backlog/board
try:
    from api.backlog_router import router as backlog_router
    app.include_router(backlog_router)
    logger.info("W8 PRD backlog ticket router registered (A2)")
except Exception as e:
    logger.warning(f"W8 PRD backlog ticket router 加载失败 (非致命): {e}")

# W9 (lex-coder · 2026-06-29) Skill 3 文书生成
# C1: 评审 #1 #2 律师最常问 Top 3 = 自动生成法律文书, 4 端点 + 4 模板
# 端点: /api/doc-gen/complaint, /api/doc-gen/defense, /api/doc-gen/contract, /api/doc-gen/letter
try:
    from api.doc_gen_router import router as doc_gen_router
    app.include_router(doc_gen_router)
    logger.info("W9 Skill 3 文书生成 router registered (C1)")
except Exception as e:
    logger.warning(f"W9 Skill 3 文书生成 router 加载失败 (非致命): {e}")

# W10 A1 (lex-ai · 2026-06-29) Skill 1+2+3 一体化全流程
# W9 C1 4 端点 + W4 类案 + W3 Skill 2 合同审查, 律师一个案件跑完三步
# 端点: POST /api/case/full-workflow, GET /api/case/full-workflow/{case_id}, GET /api/case/full-workflow/health
try:
    from api.full_workflow_router import router as full_workflow_router
    app.include_router(full_workflow_router)
    logger.info("W10 Skill 1+2+3 一体化 router registered (A1)")
except Exception as e:
    logger.warning(f"W10 Skill 一体化 router 加载失败 (非致命): {e}")

# W12 A2 (lex-coder · 2026-06-30) 双审工作流 (5 状态机 + 4 文书风险标注)
# 承接 W9 C1 4 文书 + W10 A1 一体化 + W3 Skill 2 reviewer
# 端点: GET/PATCH /api/doc-gen/{doc_id}/state, POST /api/doc-gen/{doc_id}/risk-annotation,
#       GET /api/doc-gen/workflow/board, GET /api/doc-gen/workflow/health
try:
    # 显式 import core.doc_workflow 注册 ORM 模型到 Base.metadata
    from core import doc_workflow as _dw  # noqa: F401
    from api.doc_workflow_router import router as doc_workflow_router
    app.include_router(doc_workflow_router)
    logger.info("W12 A2 双审工作流状态机 router registered")
except Exception as e:
    logger.warning(f"W12 A2 双审工作流 router 加载失败 (非致命): {e}")

# W12 A2 (lex-coder · 2026-06-30) 客户签字确认 (signature_router)
# 端点: POST /api/signature/{doc_id}, GET /api/signature/{doc_id}
try:
    from api.signature_router import router as signature_router
    app.include_router(signature_router)
    logger.info("W12 A2 客户签字 router registered")
except Exception as e:
    logger.warning(f"W12 A2 客户签字 router 加载失败 (非致命): {e}")

# W29 phase6-1-backend (lex-coder · 2026-07-01) Phase 6.1 Marketplace API
# 7 端点 + 1 health + 1 disclaimer + 1 manifest = 10 endpoints
# 端点: /api/marketplace/lawyers (POST/GET), /api/marketplace/cases (POST/GET),
#       /api/marketplace/referrals (POST), /api/marketplace/cross-border (POST),
#       /api/marketplace/metrics (GET)
try:
    # 显式 import core.marketplace_engine 注册 ORM 模型到 Base.metadata
    from core import marketplace_engine as _mp_engine  # noqa: F401
    from api.marketplace_router import router as marketplace_router
    app.include_router(marketplace_router)
    logger.info("W29 phase6-1-backend Marketplace API router registered")
except Exception as e:
    logger.warning(f"W29 phase6-1-backend Marketplace API router 加载失败 (非致命): {e}")

# W30 phase6-ai-backend (lex-ai · 2026-07-03) AI 服务统一 API
# 4 核心端点 + 1 health + 1 disclaimer = 6 endpoints
# 端点: POST /api/ai/chat, POST /api/ai/case-summary,
#       POST /api/ai/polish, POST /api/ai/auto-fill
try:
    from api.ai_router import router as ai_router
    app.include_router(ai_router)
    logger.info("W30 phase6-ai-backend AI 服务统一 API router registered")
except Exception as e:
    logger.warning(f"W30 phase6-ai-backend AI 服务 API router 加载失败 (非致命): {e}")

# 智能法律问答系统 API
# 端点: POST /api/ai/qa, GET /api/ai/qa/history, GET /api/ai/qa/hot
try:
    from api.ai_qa_router import router as ai_qa_router
    app.include_router(ai_qa_router)
    logger.info("智能法律问答系统 AI QA router registered")
except Exception as e:
    logger.warning(f"智能法律问答系统 AI QA router 加载失败 (非致命): {e}")

# 法律关系图谱 API
# 端点: GET /api/graph/case/{id}, GET /api/graph/company/{id}, GET /api/graph/lawyer/{id}
try:
    from api.graph_router import router as graph_router
    app.include_router(graph_router)
    logger.info("法律关系图谱 Graph router registered")
except Exception as e:
    logger.warning(f"法律关系图谱 Graph router 加载失败 (非致命): {e}")

# 案件风险预测 API
# 端点: POST /api/risk/predict, GET /api/risk/similar-cases
try:
    from api.risk_router import router as risk_router
    app.include_router(risk_router)
    logger.info("案件风险预测 Risk router registered")
except Exception as e:
    logger.warning(f"案件风险预测 Risk router 加载失败 (非致命): {e}")

# 智能合同生成 API
# 端点: POST /api/contract/generate, GET /api/contract/templates
try:
    from api.contract_gen_router import router as contract_gen_router
    app.include_router(contract_gen_router)
    logger.info("智能合同生成 Contract Gen router registered")
except Exception as e:
    logger.warning(f"智能合同生成 Contract Gen router 加载失败 (非致命): {e}")

# 多文档摘要和对比 API
# 端点: POST /api/doc/compare, POST /api/doc/summarize-multi
try:
    from api.doc_compare_router import router as doc_compare_router
    app.include_router(doc_compare_router)
    logger.info("多文档摘要和对比 Doc Compare router registered")
except Exception as e:
    logger.warning(f"多文档摘要和对比 Doc Compare router 加载失败 (非致命): {e}")

# W31 phase6-clients-backend (lex-coder · 2026-07-02) 客户管理 API
# 7 端点 + 1 health = 8 endpoints
# 端点: GET /api/clients (列表/搜索/过滤), GET /api/clients/{client_id} (详情),
#       POST /api/clients (创建), PUT /api/clients/{client_id} (更新),
#       DELETE /api/clients/{client_id} (删除),
#       POST /api/clients/{client_id}/conflict-check (利益冲突检查),
#       GET /api/clients/stats (统计)
# W31: 客户管理 API
try:
    from api.clients_router import router as clients_router
    app.include_router(clients_router)
    logger.info("W31 phase6-clients-backend 客户管理 API router registered")
except Exception as e:
    logger.warning(f"clients_router 加载失败: {e}")

# 日程管理 (lex-coder · 2026-07-02) Phase 6
# 4 CRUD + 1 conflicts + 1 today + 1 health = 7 endpoints
# 端点: GET/POST /api/schedule, PUT/DELETE /api/schedule/{id},
#       GET /api/schedule/conflicts, GET /api/schedule/today
try:
    from api.schedule_router import router as schedule_router
    app.include_router(schedule_router)
    logger.info("日程管理 schedule_router registered")
except Exception as e:
    logger.warning(f"schedule_router 加载失败: {e}")

# 用户管理 API
# 端点: GET/PUT/DELETE /api/users, GET /api/users/{id}, POST /api/users/batch-status
try:
    from api.users_router import router as users_router
    app.include_router(users_router)
    logger.info("用户管理 users_router registered")
except Exception as e:
    logger.warning(f"users_router 加载失败: {e}")

# 系统设置 API
# 端点: GET/PUT /api/settings
try:
    from api.settings_router import router as settings_router
    app.include_router(settings_router)
    logger.info("系统设置 settings_router registered")
except Exception as e:
    logger.warning(f"settings_router 加载失败: {e}")

# 案件管理 API
# 端点: POST /api/cases/{case_id}/status, GET /api/cases/{case_id}/timeline, POST /api/cases/{case_id}/note
try:
    from api.case_router import router as case_router
    app.include_router(case_router)
    logger.info("案件管理 case_router registered")
except Exception as e:
    logger.warning(f"case_router 加载失败: {e}")

# 数据导入导出 API
# 端点: POST /api/import/cases, POST /api/export/cases, POST /api/export/report
try:
    from api.import_export_router import router as import_export_router
    app.include_router(import_export_router)
    logger.info("数据导入导出 import_export_router registered")
except Exception as e:
    logger.warning(f"import_export_router 加载失败: {e}")

# 数据分析 API
# 端点: GET /api/analytics/dashboard, GET /api/analytics/trends,
#       GET /api/analytics/lawyer/{id}, GET /api/analytics/case-types,
#       GET /api/analytics/heatmap
try:
    from api.analytics_router import router as analytics_router
    app.include_router(analytics_router)
    logger.info("数据分析 analytics_router registered")
except Exception as e:
    logger.warning(f"analytics_router 加载失败: {e}")

# 团队协作 API
# 端点: GET /api/collaboration/members, POST /api/collaboration/tasks,
#       POST /api/collaboration/comments, PUT /api/collaboration/permissions,
#       GET /api/collaboration/files, GET /api/collaboration/stats
try:
    from api.collaboration_router import router as collaboration_router
    app.include_router(collaboration_router)
    logger.info("团队协作 collaboration_router registered")
except Exception as e:
    logger.warning(f"collaboration_router 加载失败: {e}")

# 个性化推荐 API
# 端点: GET /api/recommend/cases, GET /api/recommend/lawyers,
#       GET /api/recommend/templates, POST /api/recommend/feedback,
#       GET /api/recommend/refresh
try:
    from api.recommendation_router import router as recommendation_router
    app.include_router(recommendation_router)
    logger.info("个性化推荐 recommendation_router registered")
except Exception as e:
    logger.warning(f"recommendation_router 加载失败: {e}")

# 订阅计费系统 API
# 端点: GET /api/subscription/plans, GET /api/subscription/current,
#       POST /api/subscription/subscribe, POST /api/subscription/cancel,
#       GET /api/subscription/invoices
try:
    from api.subscription_router import router as subscription_router
    app.include_router(subscription_router)
    logger.info("订阅计费系统 subscription_router registered")
except Exception as e:
    logger.warning(f"subscription_router 加载失败: {e}")

# 支付集成 API (Mock)
# 端点: POST /api/payment/create, POST /api/payment/notify,
#       GET /api/payment/{id}, GET /api/payment/methods
try:
    from api.payment_router import router as payment_router
    app.include_router(payment_router)
    logger.info("支付集成 payment_router registered")
except Exception as e:
    logger.warning(f"payment_router 加载失败: {e}")

# 邀请裂变 v2 API
# 端点: GET /api/invite/code, POST /api/invite/redeem,
#       GET /api/invite/records, GET /api/invite/rewards, GET /api/invite/stats
try:
    from api.invite_router_v2 import router as invite_router_v2
    app.include_router(invite_router_v2)
    logger.info("邀请裂变 v2 invite_router_v2 registered")
except Exception as e:
    logger.warning(f"invite_router_v2 加载失败: {e}")

# 用户增长分析 API (admin)
# 端点: GET /api/growth/overview, GET /api/growth/funnel,
#       GET /api/growth/retention, GET /api/growth/activation, GET /api/growth/revenue
try:
    from api.growth_router import router as growth_router
    app.include_router(growth_router)
    logger.info("用户增长分析 growth_router registered")
except Exception as e:
    logger.warning(f"growth_router 加载失败: {e}")

# 统一 API 网关 - 多端接入
# 端点: /api/gateway/*
# 功能: 多端认证、设备管理、消息推送、数据同步
try:
    from api.gateway_router import router as gateway_router
    app.include_router(gateway_router)
    logger.info("统一 API 网关 gateway_router registered")
except Exception as e:
    logger.warning(f"gateway_router 加载失败: {e}")


# 模型管理 API
# 端点: GET /api/models, GET /api/models/{id}, POST /api/models/train,
#       GET /api/models/{id}/status, POST /api/models/{id}/deploy
try:
    from api.model_router import router as model_router
    app.include_router(model_router)
    logger.info("模型管理 model_router registered")
except Exception as e:
    logger.warning(f"模型管理 model_router 加载失败 (非致命): {e}")

# 评测管理 API
# 端点: /api/evaluation/*
# 功能: 评测任务管理、数据集管理、模型对比、评测报告
try:
    from api.evaluation_router import router as evaluation_router
    app.include_router(evaluation_router)
    logger.info("评测管理 evaluation_router registered")
except Exception as e:
    logger.warning(f"评测管理 evaluation_router 加载失败 (非致命): {e}")

# 企业级 - 多租户管理 API
# 端点: GET/POST/PUT/DELETE /api/tenants, /api/tenants/{id}/suspend, /api/tenants/{id}/activate
try:
    from core import multitenancy as _mt  # noqa: F401
    from api.tenant_router import router as tenant_router
    app.include_router(tenant_router)
    logger.info("企业级 - 多租户管理 tenant_router registered")
except Exception as e:
    logger.warning(f"多租户管理 tenant_router 加载失败 (非致命): {e}")

# 企业级 - SSO 单点登录 API
# 端点: GET/POST/PUT/DELETE /api/sso/providers, /api/sso/login/{provider}, /api/sso/callback/{provider}
try:
    from auth import sso as _sso  # noqa: F401
    from api.sso_router import router as sso_router
    app.include_router(sso_router)
    logger.info("企业级 - SSO 单点登录 sso_router registered")
except Exception as e:
    logger.warning(f"SSO 单点登录 sso_router 加载失败 (非致命): {e}")

# 企业级 - 审计日志 API
# 端点: GET /api/audit/logs, /api/audit/logs/{id}, /api/audit/export, /api/audit/stats, /api/audit/report
try:
    from core import audit_log as _audit  # noqa: F401
    from api.audit_router import router as audit_router
    app.include_router(audit_router)
    logger.info("企业级 - 审计日志 audit_router registered")
except Exception as e:
    logger.warning(f"审计日志 audit_router 加载失败 (非致命): {e}")

# 企业级 - 组织架构管理 API
# 端点: GET/POST/PUT/DELETE /api/org/departments, /api/org/teams, /api/org/roles, /api/org/members
try:
    from core import organization as _org  # noqa: F401
    from api.org_router import router as org_router
    app.include_router(org_router)
    logger.info("企业级 - 组织架构管理 org_router registered")
except Exception as e:
    logger.warning(f"组织架构管理 org_router 加载失败 (非致命): {e}")


# ========== Phase 7 数据资产模块 ==========

# 法律知识图谱 API
# 端点: GET /api/kg/entity/{id}, GET /api/kg/entity/search, GET /api/kg/relation/{id},
#       GET /api/kg/graph, GET /api/kg/path, GET /api/kg/similar
try:
    from api.kg_router import router as kg_router
    app.include_router(kg_router)
    logger.info("Phase 7 - 法律知识图谱 kg_router registered")
except Exception as e:
    logger.warning(f"法律知识图谱 kg_router 加载失败 (非致命): {e}")

# 判例数据库管理 API
# 端点: GET /api/cases-db/stats, GET /api/cases-db/tags, POST /api/cases-db/import,
#       POST /api/cases-db/dedupe, GET /api/cases-db/quality, POST /api/cases-db/reindex
try:
    from api.case_db_router import router as case_db_router
    app.include_router(case_db_router)
    logger.info("Phase 7 - 判例数据库 case_db_router registered")
except Exception as e:
    logger.warning(f"判例数据库 case_db_router 加载失败 (非致命): {e}")

# 法规数据库管理 API
# 端点: GET /api/laws-db/stats, GET /api/laws-db/categories, POST /api/laws-db/import,
#       GET /api/laws-db/{id}/versions, GET /api/laws-db/{id}/references, POST /api/laws-db/reindex
try:
    from api.law_db_router import router as law_db_router
    app.include_router(law_db_router)
    logger.info("Phase 7 - 法规数据库 law_db_router registered")
except Exception as e:
    logger.warning(f"法规数据库 law_db_router 加载失败 (非致命): {e}")

# 企业数据库管理 API
# 端点: GET /api/companies-db/stats, POST /api/companies-db/import,
#       GET /api/companies-db/{id}/equity, GET /api/companies-db/{id}/risk,
#       GET /api/companies-db/{id}/relations, POST /api/companies-db/reindex
try:
    from api.company_db_router import router as company_db_router
    app.include_router(company_db_router)
    logger.info("Phase 7 - 企业数据库 company_db_router registered")
except Exception as e:
    logger.warning(f"企业数据库 company_db_router 加载失败 (非致命): {e}")

# 律师数据库管理 API
# 端点: GET /api/lawyers-db/stats, POST /api/lawyers-db/import,
#       GET /api/lawyers-db/{id}/profile, GET /api/lawyers-db/{id}/cases,
#       GET /api/lawyers-db/match, POST /api/lawyers-db/reindex
try:
    from api.lawyer_db_router import router as lawyer_db_router
    app.include_router(lawyer_db_router)
    logger.info("Phase 7 - 律师数据库 lawyer_db_router registered")
except Exception as e:
    logger.warning(f"律师数据库 lawyer_db_router 加载失败 (非致命): {e}")


# ========== 端点 ==========

@app.get("/api/health", summary="健康检查", description="检查数据库、Elasticsearch、Neo4j 的连接状态和延迟")
async def health():
    import time
    
    db_status = {
        "connected": Database._engine is not None,
        "backend": Database._backend if hasattr(Database, "_backend") else "unknown",
    }
    
    if Database._engine is not None:
        try:
            start_time = time.time()
            async with Database.session() as session:
                await session.execute("SELECT 1")
            db_status["latency_ms"] = round((time.time() - start_time) * 1000, 2)
            db_status["query_ok"] = True
        except Exception as e:
            db_status["query_ok"] = False
            db_status["error"] = str(e)
    
    es_status = {
        "connected": ESClient._client is not None,
        "using_mock": ESClient.is_mock(),
    }
    
    if ESClient._client is not None and not ESClient.is_mock():
        try:
            start_time = time.time()
            await ESClient._client.info()
            es_status["latency_ms"] = round((time.time() - start_time) * 1000, 2)
            es_status["query_ok"] = True
        except Exception as e:
            es_status["query_ok"] = False
            es_status["error"] = str(e)
    
    neo4j_status = {
        "connected": Neo4jClient._driver is not None,
        "available": Neo4jClient.is_available(),
    }
    
    if Neo4jClient._driver is not None:
        try:
            start_time = time.time()
            async with Neo4jClient._driver.session() as session:
                await session.run("RETURN 1").single()
            neo4j_status["latency_ms"] = round((time.time() - start_time) * 1000, 2)
            neo4j_status["query_ok"] = True
        except Exception as e:
            neo4j_status["query_ok"] = False
            neo4j_status["error"] = str(e)
    
    all_ok = (
        db_status.get("connected", False) and
        es_status.get("connected", False) and
        neo4j_status.get("available", True)
    )
    
    return {
        "status": "ok" if all_ok else "degraded",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat(),
        "databases": {
            "main": db_status,
            "elasticsearch": es_status,
            "neo4j": neo4j_status,
        },
        "environment": settings.api_debug and "development" or "production",
    }


class FrontendError(BaseModel):
    """前端错误日志模型"""
    timestamp: str = Field(..., description="错误发生时间")
    user: dict = Field({}, description="用户信息")
    browser: dict = Field({}, description="浏览器信息")
    page: dict = Field({}, description="页面信息")
    error: dict = Field({}, description="错误详情")
    type: str = Field("frontend_error", description="日志类型")


class FrontendPerformance(BaseModel):
    """前端性能日志模型"""
    timestamp: str = Field(..., description="记录时间")
    user: dict = Field({}, description="用户信息")
    browser: dict = Field({}, description="浏览器信息")
    page: dict = Field({}, description="页面信息")
    performance: dict = Field({}, description="性能数据")
    type: str = Field("frontend_performance", description="日志类型")


class LogsRequest(BaseModel):
    """前端日志请求模型"""
    errors: Optional[List[FrontendError]] = Field(None, description="错误日志列表")
    performance: Optional[List[FrontendPerformance]] = Field(None, description="性能日志列表")


@app.post("/api/logs", summary="接收前端日志", description="接收前端上报的错误日志和性能数据，用于监控和分析")
async def receive_frontend_logs(req: LogsRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    
    if req.errors:
        for error in req.errors:
            logger.error("frontend_error", extra={
                "client_ip": client_ip,
                **error.dict(),
            })
            _write_log_entry("frontend_error", error.dict())
    
    if req.performance:
        for perf in req.performance:
            logger.info("frontend_performance", extra={
                "client_ip": client_ip,
                **perf.dict(),
            })
            _write_log_entry("frontend_performance", perf.dict())
    
    return {"status": "ok", "received_errors": len(req.errors or []), "received_performance": len(req.performance or [])}


# --- 判例 ---

@app.get("/api/cases", summary="获取判例列表", description="获取判例列表，支持按案由、案由分类、年份、法院筛选，默认返回精简数据")
async def list_cases(
    cause: Optional[str] = Query(None, description="案由关键词"),
    cause_category: Optional[str] = Query(None, description="案由分类"),
    year: Optional[int] = Query(None, description="判决年份"),
    court: Optional[str] = Query(None, description="法院名称"),
    limit: int = Query(50, le=500, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    full: bool = Query(False, description="是否返回完整字段"),
):
    async with Database.session() as session:
        from sqlalchemy import select
        stmt = select(Case).order_by(Case.lex_score.desc(), Case.judgment_date.desc())
        if cause_category:
            stmt = stmt.where(Case.cause_category == cause_category)
        if year:
            stmt = stmt.where(Case.year == year)
        if court:
            stmt = stmt.where(Case.court.contains(court))
        if cause:
            stmt = stmt.where(Case.cause.contains(cause))
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        cases = result.scalars().all()
        if full:
            # 完整数据 (给前端 view)
            return [CaseDetail(
                id=c.id, doc_id=c.doc_id, case_id=c.case_id, case_name=c.case_name,
                court=c.court, cause=c.cause, cause_category=c.cause_category,
                cause_color=c.cause_color,
                judgment_date=c.judgment_date.isoformat() if c.judgment_date else None,
                year=c.year, lex_score=c.lex_score,
                view_count=c.view_count, favorite_count=c.favorite_count,
                parties=c.parties, legal_basis=c.legal_basis,
                full_text=c.full_text_plain or c.full_text, source=c.source, source_url=c.source_url,
                keywords=c.keywords or [],
            ) for c in cases]
        else:
            return [CaseOut(
                id=c.id, doc_id=c.doc_id, case_id=c.case_id, case_name=c.case_name,
                court=c.court, cause=c.cause, cause_category=c.cause_category,
                cause_color=c.cause_color,
                judgment_date=c.judgment_date.isoformat() if c.judgment_date else None,
                year=c.year, lex_score=c.lex_score,
                view_count=c.view_count, favorite_count=c.favorite_count,
            ) for c in cases]


@app.get("/api/cases/{doc_id}", response_model=CaseDetail, summary="获取判例详情", description="根据文档ID获取判例完整信息，包含判决书全文、法律依据等")
async def get_case(doc_id: str):
    async with Database.session() as session:
        from sqlalchemy import select
        stmt = select(Case).where(Case.doc_id == doc_id)
        result = await session.execute(stmt)
        c = result.scalar_one_or_none()
        if not c:
            raise HTTPException(404, "Case not found")
        # 增加查看次数
        c.view_count += 1
        await session.commit()
        return CaseDetail(
            id=c.id, doc_id=c.doc_id, case_id=c.case_id, case_name=c.case_name,
            court=c.court, cause=c.cause, cause_category=c.cause_category,
            cause_color=c.cause_color,
            judgment_date=c.judgment_date.isoformat() if c.judgment_date else None,
            year=c.year, lex_score=c.lex_score,
            view_count=c.view_count, favorite_count=c.favorite_count,
            parties=c.parties, legal_basis=c.legal_basis,
            full_text=c.full_text, source=c.source, source_url=c.source_url,
            keywords=c.keywords,
        )


# --- 搜索 (ES 全文检索) ---

@app.post("/api/search", summary="全文搜索", description="通过 Elasticsearch 进行判例、法规、企业的全文搜索，支持分页和过滤")
async def search(req: SearchRequest):
    es = ESClient.get()
    index_name = {
        "cases": settings.es_index_cases,
        "laws": settings.es_index_laws,
        "companies": settings.es_index_companies,
    }[req.index]

    from_ = (req.page - 1) * req.size
    query = {
        "multi_match": {
            "query": req.query,
            "fields": ["*"],
            "type": "best_fields",
        }
    }
    if req.filters:
        # 简单 filter 应用
        filter_clauses = []
        for k, v in req.filters.items():
            filter_clauses.append({"term": {k: v}})
        body = {
            "query": {"bool": {"must": [query], "filter": filter_clauses}},
            "from": from_,
            "size": req.size,
        }
    else:
        body = {"query": query, "from": from_, "size": req.size}

    try:
        resp = await es.search(index=index_name, body=body)
        hits = resp["hits"]["hits"]
        total = resp["hits"]["total"]["value"]
        return {
            "total": total,
            "page": req.page,
            "size": req.size,
            "items": [h["_source"] for h in hits],
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(500, f"Search failed: {e}")


# --- 法规 ---

@app.get("/api/laws", response_model=List[LawOut], summary="获取法规列表", description="获取法律法规列表，支持按类型和效力状态筛选")
async def list_laws(
    law_type: Optional[str] = Query(None, description="法规类型"),
    status: Optional[str] = Query(None, description="效力状态"),
    limit: int = Query(50, le=200, description="每页数量"),
):
    async with Database.session() as session:
        from sqlalchemy import select
        stmt = select(Law).order_by(Law.effective_date.desc())
        if law_type:
            stmt = stmt.where(Law.law_type == law_type)
        if status:
            stmt = stmt.where(Law.status == status)
        stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        laws = result.scalars().all()
        return [LawOut(
            id=l.id, law_id=l.law_id, title=l.title, law_type=l.law_type,
            status=l.status, issue_date=l.issue_date.isoformat() if l.issue_date else None,
            effective_date=l.effective_date.isoformat() if l.effective_date else None,
            level=l.level,
        ) for l in laws]


# --- 企业 ---

@app.get("/api/companies", response_model=List[CompanyOut], summary="获取企业列表", description="获取企业工商信息列表，支持按名称、地区和执行公开状态筛选")
async def list_companies(
    name: Optional[str] = Query(None, description="企业名称关键词"),
    is_zxgk: Optional[bool] = Query(None, description="是否在执行公开名单"),
    region: Optional[str] = Query(None, description="所属地区"),
    limit: int = Query(50, le=200, description="每页数量"),
):
    async with Database.session() as session:
        from sqlalchemy import select
        stmt = select(Company).order_by(Company.id.desc())
        if name:
            stmt = stmt.where(Company.company_name.contains(name))
        if is_zxgk is not None:
            stmt = stmt.where(Company.is_zxgk == is_zxgk)
        if region:
            stmt = stmt.where(Company.region == region)
        stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        comps = result.scalars().all()
        return [CompanyOut(
            id=c.id, unified_id=c.unified_id, company_name=c.company_name,
            legal_rep=c.legal_rep, business_status=c.business_status,
            industry=c.industry, region=c.region, is_zxgk=c.is_zxgk,
        ) for c in comps]


# --- 律所版 0.1 ---

@app.get("/api/firm/lawyers", summary="获取律所律师列表", description="根据律所ID获取该律所的律师列表，支持按角色筛选")
async def list_firm_lawyers(firm_id: str = Query(..., description="律所ID"), role: Optional[str] = Query(None, description="角色筛选")):
    async with Database.session() as session:
        from sqlalchemy import select
        stmt = select(Lawyer).where(Lawyer.firm_id == firm_id, Lawyer.is_active == True)
        if role:
            stmt = stmt.where(Lawyer.role == role)
        result = await session.execute(stmt)
        lawyers = result.scalars().all()
        return [{
            "id": l.id, "name": l.name, "email": l.email, "role": l.role,
            "specialties": l.specialties, "avatar_url": l.avatar_url,
        } for l in lawyers]


@app.post("/api/firm/time-entries", summary="创建工时记录", description="为律所律师创建工时记录，包含工作日期、工时数、费率等信息")
async def create_time_entry(entry: TimeEntryIn, firm_id: str = Query(..., description="律所ID")):
    async with Database.session() as session:
        from decimal import Decimal
        record = FirmTimeEntry(
            firm_id=firm_id,
            lawyer_id=entry.lawyer_id,
            case_id=entry.case_id,
            entry_date=entry.entry_date,
            hours=Decimal(str(entry.hours)),
            description=entry.description,
            billable=entry.billable,
            rate=Decimal(str(entry.rate)) if entry.rate else None,
            amount=Decimal(str(entry.hours * entry.rate)) if entry.rate else None,
        )
        session.add(record)
        await session.commit()
        return {"id": record.id, "status": "created"}


@app.get("/api/firm/stats", summary="获取律所统计", description="获取律所的律师数量和本月工时统计")
async def firm_stats(firm_id: str = Query(..., description="律所ID")):
    from sqlalchemy import select, func
    async with Database.session() as session:
        # 律师数
        lawyer_stmt = select(func.count(Lawyer.id)).where(Lawyer.firm_id == firm_id, Lawyer.is_active == True)
        lawyer_count = (await session.execute(lawyer_stmt)).scalar() or 0

        # 工时本月
        from datetime import date
        first_of_month = date.today().replace(day=1)
        time_stmt = select(func.sum(FirmTimeEntry.hours)).where(
            FirmTimeEntry.firm_id == firm_id,
            FirmTimeEntry.entry_date >= first_of_month,
        )
        month_hours = (await session.execute(time_stmt)).scalar() or 0

        return {
            "lawyer_count": lawyer_count,
            "month_hours": float(month_hours),
            "firm_id": firm_id,
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
