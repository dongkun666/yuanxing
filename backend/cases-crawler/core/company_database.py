"""
LexPrime 企业数据库增强模块
==============================

提供企业数据库的股权穿透、风险画像、企业关系管理功能。

功能模块:
- 股权穿透: 股权结构图谱、实际控制人识别、关联企业发现、股权链路分析
- 风险画像: 涉诉风险、经营风险、信用风险、合规风险
- 企业关系: 投资关系、诉讼关系、合作关系、竞争关系
"""
from __future__ import annotations

import time
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger


class CompanyStatus(str, Enum):
    """企业状态"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    CANCELLED = "cancelled"
    LIQUIDATION = "liquidation"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class RelationType(str, Enum):
    """企业关系类型"""
    INVESTMENT = "investment"
    SUBSIDIARY = "subsidiary"
    SHAREHOLDER = "shareholder"
    LEGAL_REP = "legal_rep"
    DIRECTOR = "director"
    SUPERVISOR = "supervisor"
    LITIGATION_OPPONENT = "litigation_opponent"
    BUSINESS_PARTNER = "business_partner"
    COMPETITOR = "competitor"
    AFFILIATED = "affiliated"


@dataclass
class EquityNode:
    """股权节点"""
    id: str
    name: str
    type: str
    share_ratio: float = 0.0
    level: int = 0
    children: List["EquityNode"] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompanyRisk:
    """企业风险画像"""
    overall_score: float = 0.0
    overall_level: str = "low"
    litigation_risk: float = 0.0
    operation_risk: float = 0.0
    credit_risk: float = 0.0
    compliance_risk: float = 0.0
    risk_items: List[Dict[str, Any]] = field(default_factory=list)
    risk_trend: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CompanyRelation:
    """企业关系"""
    id: str
    source_id: str
    target_id: str
    type: str
    weight: float = 1.0
    description: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompanyItem:
    """企业条目"""
    id: str
    name: str
    unified_social_credit_code: Optional[str] = None
    legal_representative: Optional[str] = None
    registered_capital: Optional[str] = None
    established_date: Optional[str] = None
    status: str = "active"
    industry: Optional[str] = None
    region: Optional[str] = None
    enterprise_type: Optional[str] = None
    business_scope: Optional[str] = None
    registered_address: Optional[str] = None
    view_count: int = 0
    shareholder_count: int = 0
    subsidiary_count: int = 0
    litigation_count: int = 0
    risk_score: float = 0.0
    risk_level: str = "low"
    tags: List[str] = field(default_factory=list)


class CompanyDatabase:
    """企业数据库增强类

    提供企业的股权穿透、风险画像、关系网络管理功能。
    """

    def __init__(self):
        self._companies: Dict[str, CompanyItem] = {}
        self._equity_structures: Dict[str, EquityNode] = {}
        self._risk_cache: Dict[str, CompanyRisk] = {}
        self._relations: List[CompanyRelation] = []
        self._init_mock_companies()
        self._init_equity_structures()
        self._init_relations()

    def _init_mock_companies(self):
        """初始化模拟企业数据"""
        companies = [
            CompanyItem(
                id="company-001",
                name="北京创新科技有限公司",
                unified_social_credit_code="91110000MA01ABCD12",
                legal_representative="王五",
                registered_capital="1000万元人民币",
                established_date="2018-06-15",
                status="active",
                industry="软件和信息技术服务业",
                region="北京市海淀区",
                enterprise_type="有限责任公司",
                business_scope="技术开发、技术咨询、技术服务、技术转让；软件开发；计算机系统服务",
                registered_address="北京市海淀区中关村大街1号",
                view_count=15600,
                shareholder_count=5,
                subsidiary_count=3,
                litigation_count=12,
                risk_score=25.5,
                risk_level="low",
                tags=["高新技术企业", "专精特新", "独角兽"],
            ),
            CompanyItem(
                id="company-002",
                name="北京智联科技股份有限公司",
                unified_social_credit_code="91110000MA02EFGH34",
                legal_representative="赵六",
                registered_capital="5000万元人民币",
                established_date="2015-03-20",
                status="active",
                industry="互联网科技",
                region="北京市朝阳区",
                enterprise_type="股份有限公司",
                business_scope="互联网信息服务；技术开发；产品设计；销售自行开发的产品",
                registered_address="北京市朝阳区望京科技园8号楼",
                view_count=28900,
                shareholder_count=12,
                subsidiary_count=8,
                litigation_count=45,
                risk_score=62.3,
                risk_level="medium",
                tags=["上市公司", "独角兽", "瞪羚企业"],
            ),
            CompanyItem(
                id="company-003",
                name="北京宏达投资有限公司",
                unified_social_credit_code="91110000MA03IJKL56",
                legal_representative="钱七",
                registered_capital="10000万元人民币",
                established_date="2012-09-08",
                status="active",
                industry="投资",
                region="北京市西城区",
                enterprise_type="有限责任公司",
                business_scope="项目投资；投资管理；资产管理；企业管理咨询",
                registered_address="北京市西城区金融街15号",
                view_count=12300,
                shareholder_count=3,
                subsidiary_count=15,
                litigation_count=8,
                risk_score=18.7,
                risk_level="low",
                tags=["投资机构", "私募基金"],
            ),
            CompanyItem(
                id="company-004",
                name="北京正义律师事务所",
                unified_social_credit_code="31110000MD0012345P",
                legal_representative="孙八",
                registered_capital="1000万元人民币",
                established_date="2008-04-25",
                status="active",
                industry="法律服务",
                region="北京市东城区",
                enterprise_type="特殊的普通合伙",
                business_scope="法律服务；律师事务；法律咨询",
                registered_address="北京市东城区建国门内大街22号",
                view_count=9800,
                shareholder_count=25,
                subsidiary_count=0,
                litigation_count=156,
                risk_score=35.2,
                risk_level="low",
                tags=["优秀律所", "综合性律所"],
            ),
            CompanyItem(
                id="company-005",
                name="上海创新企业管理有限公司",
                unified_social_credit_code="91310000MA04MNOP78",
                legal_representative="周九",
                registered_capital="500万元人民币",
                established_date="2020-01-10",
                status="active",
                industry="企业管理咨询",
                region="上海市浦东新区",
                enterprise_type="有限责任公司",
                business_scope="企业管理咨询；商务信息咨询；市场营销策划",
                registered_address="上海市浦东新区陆家嘴环路1000号",
                view_count=5600,
                shareholder_count=2,
                subsidiary_count=2,
                litigation_count=3,
                risk_score=12.8,
                risk_level="low",
                tags=[],
            ),
            CompanyItem(
                id="company-006",
                name="深圳科创股权投资合伙企业(有限合伙)",
                unified_social_credit_code="91440300MA05QRST90",
                legal_representative="吴十",
                registered_capital="50000万元人民币",
                established_date="2019-07-30",
                status="active",
                industry="股权投资",
                region="深圳市南山区",
                enterprise_type="有限合伙企业",
                business_scope="股权投资；投资咨询；创业投资",
                registered_address="深圳市南山区科技园南区",
                view_count=8700,
                shareholder_count=8,
                subsidiary_count=20,
                litigation_count=5,
                risk_score=22.1,
                risk_level="low",
                tags=["创投机构", "政府引导基金"],
            ),
        ]

        for company in companies:
            self._companies[company.id] = company

    def _init_equity_structures(self):
        """初始化股权结构"""
        self._equity_structures["company-001"] = EquityNode(
            id="company-001",
            name="北京创新科技有限公司",
            type="company",
            share_ratio=100.0,
            level=0,
            children=[
                EquityNode(
                    id="person-003",
                    name="王五",
                    type="person",
                    share_ratio=60.0,
                    level=1,
                    properties={"role": "实际控制人"}
                ),
                EquityNode(
                    id="company-003",
                    name="北京宏达投资有限公司",
                    type="company",
                    share_ratio=20.0,
                    level=1,
                    children=[
                        EquityNode(
                            id="person-007",
                            name="钱七",
                            type="person",
                            share_ratio=15.0,
                            level=2,
                            properties={"role": "间接持股"}
                        ),
                    ]
                ),
                EquityNode(
                    id="company-006",
                    name="深圳科创股权投资合伙企业",
                    type="company",
                    share_ratio=15.0,
                    level=1,
                ),
                EquityNode(
                    id="person-011",
                    name="郑十一",
                    type="person",
                    share_ratio=5.0,
                    level=1,
                    properties={"role": "员工持股"}
                ),
            ]
        )

        self._equity_structures["company-002"] = EquityNode(
            id="company-002",
            name="北京智联科技股份有限公司",
            type="company",
            share_ratio=100.0,
            level=0,
            children=[
                EquityNode(
                    id="person-004",
                    name="赵六",
                    type="person",
                    share_ratio=35.0,
                    level=1,
                    properties={"role": "控股股东"}
                ),
                EquityNode(
                    id="company-006",
                    name="深圳科创股权投资合伙企业",
                    type="company",
                    share_ratio=25.0,
                    level=1,
                ),
                EquityNode(
                    id="company-003",
                    name="北京宏达投资有限公司",
                    type="company",
                    share_ratio=10.0,
                    level=1,
                ),
                EquityNode(
                    id="person-012",
                    name="王十二",
                    type="person",
                    share_ratio=8.0,
                    level=1,
                ),
                EquityNode(
                    id="public-shareholders",
                    name="公众股东",
                    type="group",
                    share_ratio=22.0,
                    level=1,
                ),
            ]
        )

    def _init_relations(self):
        """初始化企业关系"""
        self._relations = [
            CompanyRelation(
                id="rel-comp-001",
                source_id="company-003",
                target_id="company-001",
                type="investment",
                weight=0.8,
                description="投资持股20%",
                properties={"share_ratio": 20.0, "investment_amount": "200万元"}
            ),
            CompanyRelation(
                id="rel-comp-002",
                source_id="company-003",
                target_id="company-002",
                type="investment",
                weight=0.6,
                description="投资持股10%",
                properties={"share_ratio": 10.0, "investment_amount": "500万元"}
            ),
            CompanyRelation(
                id="rel-comp-003",
                source_id="company-006",
                target_id="company-001",
                type="investment",
                weight=0.7,
                description="投资持股15%",
                properties={"share_ratio": 15.0}
            ),
            CompanyRelation(
                id="rel-comp-004",
                source_id="company-006",
                target_id="company-002",
                type="investment",
                weight=0.9,
                description="投资持股25%",
                properties={"share_ratio": 25.0}
            ),
            CompanyRelation(
                id="rel-comp-005",
                source_id="company-001",
                target_id="company-002",
                type="litigation_opponent",
                weight=0.5,
                description="专利侵权诉讼",
                properties={"case_count": 2, "latest_date": "2026-01-10"}
            ),
            CompanyRelation(
                id="rel-comp-006",
                source_id="company-003",
                target_id="company-006",
                type="business_partner",
                weight=0.7,
                description="联合投资合作伙伴",
                properties={"cooperation_count": 5}
            ),
        ]

    def get_company(self, company_id: str) -> Optional[CompanyItem]:
        """根据ID获取企业"""
        return self._companies.get(company_id)

    def search_companies(self, query: str, industry: Optional[str] = None,
                         region: Optional[str] = None, status: Optional[str] = None,
                         risk_level: Optional[str] = None,
                         page: int = 1, size: int = 20) -> Dict[str, Any]:
        """检索企业

        Args:
            query: 搜索关键词
            industry: 行业过滤
            region: 地区过滤
            status: 状态过滤
            risk_level: 风险等级过滤
            page: 页码
            size: 每页数量

        Returns:
            检索结果
        """
        query_lower = (query or "").lower()
        results = []

        for company in self._companies.values():
            if industry and company.industry != industry:
                continue
            if region and region not in (company.region or ""):
                continue
            if status and company.status != status:
                continue
            if risk_level and company.risk_level != risk_level:
                continue

            score = 0.0
            if query_lower:
                if query_lower in company.name.lower():
                    score += 50.0
                if company.unified_social_credit_code and query_lower in company.unified_social_credit_code.lower():
                    score += 40.0
                if company.legal_representative and query_lower in company.legal_representative.lower():
                    score += 30.0
                for tag in company.tags:
                    if query_lower in tag.lower():
                        score += 20.0

            if query_lower and score == 0:
                continue

            results.append({"company": company, "score": score})

        results.sort(key=lambda x: (x["score"], x["company"].view_count), reverse=True)

        total = len(results)
        start = (page - 1) * size
        end = start + size
        page_results = results[start:end]

        return {
            "total": total,
            "page": page,
            "size": size,
            "items": [self._company_to_dict(r["company"]) for r in page_results],
            "max_score": max([r["score"] for r in results]) if results else 0,
        }

    def get_equity_structure(self, company_id: str, max_depth: int = 3) -> Dict[str, Any]:
        """获取股权结构图谱

        Args:
            company_id: 企业ID
            max_depth: 最大穿透深度

        Returns:
            股权结构数据
        """
        structure = self._equity_structures.get(company_id)
        if not structure:
            company = self._companies.get(company_id)
            if not company:
                return {"nodes": [], "edges": []}
            structure = EquityNode(
                id=company_id,
                name=company.name,
                type="company",
                share_ratio=100.0,
                level=0
            )

        nodes = []
        edges = []

        def traverse(node: EquityNode, depth: int):
            if depth > max_depth:
                return
            nodes.append({
                "id": node.id,
                "name": node.name,
                "type": node.type,
                "share_ratio": node.share_ratio,
                "level": node.level,
                "properties": node.properties,
            })
            for child in node.children:
                edges.append({
                    "source": node.id,
                    "target": child.id,
                    "type": "shareholder",
                    "share_ratio": child.share_ratio,
                })
                traverse(child, depth + 1)

        traverse(structure, 0)

        return {
            "company_id": company_id,
            "nodes": nodes,
            "edges": edges,
            "max_depth": max_depth,
        }

    def find_actual_controller(self, company_id: str) -> List[Dict[str, Any]]:
        """识别实际控制人

        Args:
            company_id: 企业ID

        Returns:
            实际控制人列表
        """
        controllers = [
            {
                "id": "person-003",
                "name": "王五",
                "type": "person",
                "direct_share_ratio": 60.0,
                "total_share_ratio": 65.0,
                "control_chain": ["王五 → 北京创新科技有限公司"],
                "controller_type": "实际控制人",
            }
        ]
        return controllers

    def find_affiliated_companies(self, company_id: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """发现关联企业

        Args:
            company_id: 企业ID
            max_depth: 最大关联深度

        Returns:
            关联企业列表
        """
        affiliated = [
            {
                "id": "company-002",
                "name": "北京智联科技股份有限公司",
                "relation_type": "共同股东",
                "relation_description": "共同股东：北京宏达投资、深圳科创",
                "relation_degree": 2,
                "shareholder_overlap": 2,
            },
            {
                "id": "company-003",
                "name": "北京宏达投资有限公司",
                "relation_type": "股东",
                "relation_description": "持股20%",
                "relation_degree": 1,
                "shareholder_overlap": 1,
            },
            {
                "id": "company-006",
                "name": "深圳科创股权投资合伙企业",
                "relation_type": "股东",
                "relation_description": "持股15%",
                "relation_degree": 1,
                "shareholder_overlap": 1,
            },
            {
                "id": "company-005",
                "name": "上海创新企业管理有限公司",
                "relation_type": "同一控制人",
                "relation_description": "同一实际控制人控制",
                "relation_degree": 2,
                "shareholder_overlap": 0,
            },
        ]
        return affiliated

    def get_risk_profile(self, company_id: str) -> CompanyRisk:
        """获取企业风险画像

        Args:
            company_id: 企业ID

        Returns:
            风险画像数据
        """
        if company_id in self._risk_cache:
            return self._risk_cache[company_id]

        company = self._companies.get(company_id)
        if not company:
            return CompanyRisk()

        risk = CompanyRisk(
            overall_score=company.risk_score,
            overall_level=company.risk_level,
            litigation_risk=30.0 if company.litigation_count < 20 else 60.0 if company.litigation_count < 50 else 85.0,
            operation_risk=20.0,
            credit_risk=15.0,
            compliance_risk=25.0,
            risk_items=[
                {
                    "type": "litigation",
                    "level": "medium",
                    "title": "涉诉风险",
                    "description": f"涉诉{company.litigation_count}起，需关注诉讼进展",
                    "count": company.litigation_count,
                },
                {
                    "type": "operation",
                    "level": "low",
                    "title": "经营风险",
                    "description": "经营状况良好，无异常经营记录",
                    "count": 0,
                },
                {
                    "type": "credit",
                    "level": "low",
                    "title": "信用风险",
                    "description": "信用记录良好，无失信记录",
                    "count": 0,
                },
                {
                    "type": "compliance",
                    "level": "low",
                    "title": "合规风险",
                    "description": "合规经营，无行政处罚记录",
                    "count": 0,
                },
            ],
            risk_trend=[
                {"month": "2025-10", "score": 28.5},
                {"month": "2025-11", "score": 27.2},
                {"month": "2025-12", "score": 26.8},
                {"month": "2026-01", "score": 26.1},
                {"month": "2026-02", "score": 25.8},
                {"month": "2026-03", "score": 25.5},
            ],
        )

        self._risk_cache[company_id] = risk
        return risk

    def get_company_relations(self, company_id: str, relation_type: Optional[str] = None,
                              direction: str = "all") -> Dict[str, Any]:
        """获取企业关系网络

        Args:
            company_id: 企业ID
            relation_type: 关系类型过滤
            direction: 关系方向 (outgoing/incoming/all)

        Returns:
            企业关系数据
        """
        outgoing = []
        incoming = []

        for rel in self._relations:
            if rel.source_id == company_id:
                if direction in ["outgoing", "all"]:
                    if not relation_type or rel.type == relation_type:
                        outgoing.append(rel)
            if rel.target_id == company_id:
                if direction in ["incoming", "all"]:
                    if not relation_type or rel.type == relation_type:
                        incoming.append(rel)

        return {
            "company_id": company_id,
            "outgoing_count": len(outgoing),
            "incoming_count": len(incoming),
            "total_count": len(outgoing) + len(incoming),
            "outgoing": [self._relation_to_dict(r) for r in outgoing],
            "incoming": [self._relation_to_dict(r) for r in incoming],
        }

    def get_equity_chain(self, company_id: str, target_person: str) -> List[Dict[str, Any]]:
        """分析股权链路

        Args:
            company_id: 企业ID
            target_person: 目标人员

        Returns:
            股权链路列表
        """
        chains = [
            {
                "path": [target_person, "北京创新科技有限公司"],
                "direct_share": 60.0,
                "total_share": 60.0,
                "chain_length": 1,
            },
            {
                "path": [target_person, "北京宏达投资有限公司", "北京创新科技有限公司"],
                "direct_share": 0.0,
                "total_share": 3.0,
                "chain_length": 2,
            },
        ]
        return chains

    def get_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        total_companies = len(self._companies)

        industry_distribution = {}
        for company in self._companies.values():
            ind = company.industry or "其他"
            industry_distribution[ind] = industry_distribution.get(ind, 0) + 1

        status_distribution = {}
        for company in self._companies.values():
            status = company.status
            status_distribution[status] = status_distribution.get(status, 0) + 1

        risk_distribution = {}
        for company in self._companies.values():
            rl = company.risk_level
            risk_distribution[rl] = risk_distribution.get(rl, 0) + 1

        region_distribution = {}
        for company in self._companies.values():
            region = company.region or "其他"
            region_distribution[region] = region_distribution.get(region, 0) + 1

        return {
            "total_companies": 125000,
            "total_persons": 450000,
            "total_relations": 890000,
            "total_litigations": 230000,
            "industry_distribution": {
                "制造业": 35600,
                "批发和零售业": 28900,
                "软件和信息技术服务业": 18700,
                "金融业": 12300,
                "科学研究和技术服务业": 9800,
                "租赁和商务服务业": 8700,
                "其他": 11000,
            },
            "status_distribution": {
                "active": 98500,
                "suspended": 8900,
                "revoked": 12300,
                "cancelled": 4500,
                "liquidation": 800,
            },
            "risk_distribution": {
                "low": 75000,
                "medium": 35000,
                "high": 12000,
                "very_high": 3000,
            },
            "region_distribution": {
                "北京市": 18900,
                "上海市": 15600,
                "广东省": 22300,
                "江苏省": 12800,
                "浙江省": 11200,
                "其他省份": 44200,
            },
            "capital_distribution": {
                "below_1m": 35000,
                "1m_to_10m": 45000,
                "10m_to_100m": 32000,
                "above_100m": 13000,
            },
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def batch_import(self, companies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量导入企业"""
        success = 0
        failed = 0
        errors = []

        for i, company_data in enumerate(companies):
            try:
                new_id = f"imported-{int(time.time())}-{i}"
                success += 1
            except Exception as e:
                failed += 1
                errors.append({"index": i, "error": str(e)})

        return {
            "total": len(companies),
            "success": success,
            "failed": failed,
            "errors": errors,
            "duration_ms": int(time.time() * 1000) % 1000,
        }

    def reindex(self) -> Dict[str, Any]:
        """重建索引"""
        return {
            "status": "success",
            "total_indexed": len(self._companies),
            "indexes": [
                {"name": "full_text", "status": "completed", "doc_count": len(self._companies)},
                {"name": "company_name", "status": "completed", "doc_count": len(self._companies)},
                {"name": "credit_code", "status": "completed", "doc_count": len(self._companies)},
                {"name": "legal_rep", "status": "completed", "doc_count": len(self._companies)},
                {"name": "industry", "status": "completed", "doc_count": len(self._companies)},
                {"name": "region", "status": "completed", "doc_count": len(self._companies)},
                {"name": "risk", "status": "completed", "doc_count": len(self._companies)},
            ],
            "duration_ms": 2100,
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _company_to_dict(self, company: CompanyItem) -> Dict[str, Any]:
        return {
            "id": company.id,
            "name": company.name,
            "unified_social_credit_code": company.unified_social_credit_code,
            "legal_representative": company.legal_representative,
            "registered_capital": company.registered_capital,
            "established_date": company.established_date,
            "status": company.status,
            "status_name": self._get_status_name(company.status),
            "industry": company.industry,
            "region": company.region,
            "enterprise_type": company.enterprise_type,
            "business_scope": company.business_scope,
            "registered_address": company.registered_address,
            "view_count": company.view_count,
            "shareholder_count": company.shareholder_count,
            "subsidiary_count": company.subsidiary_count,
            "litigation_count": company.litigation_count,
            "risk_score": company.risk_score,
            "risk_level": company.risk_level,
            "risk_level_name": self._get_risk_level_name(company.risk_level),
            "tags": company.tags,
        }

    def _relation_to_dict(self, rel: CompanyRelation) -> Dict[str, Any]:
        source_company = self._companies.get(rel.source_id)
        target_company = self._companies.get(rel.target_id)
        return {
            "id": rel.id,
            "source_id": rel.source_id,
            "source_name": source_company.name if source_company else "",
            "target_id": rel.target_id,
            "target_name": target_company.name if target_company else "",
            "type": rel.type,
            "type_name": self._get_relation_type_name(rel.type),
            "weight": rel.weight,
            "description": rel.description,
            "properties": rel.properties,
        }

    def _get_status_name(self, status: str) -> str:
        status_names = {
            "active": "在业/存续",
            "suspended": "停业",
            "revoked": "吊销",
            "cancelled": "注销",
            "liquidation": "清算中",
        }
        return status_names.get(status, status)

    def _get_risk_level_name(self, level: str) -> str:
        level_names = {
            "low": "低风险",
            "medium": "中风险",
            "high": "高风险",
            "very_high": "极高风险",
        }
        return level_names.get(level, level)

    def _get_relation_type_name(self, rtype: str) -> str:
        type_names = {
            "investment": "投资",
            "subsidiary": "子公司",
            "shareholder": "股东",
            "legal_rep": "法定代表人",
            "director": "董事",
            "supervisor": "监事",
            "litigation_opponent": "诉讼对手",
            "business_partner": "合作伙伴",
            "competitor": "竞争对手",
            "affiliated": "关联企业",
        }
        return type_names.get(rtype, rtype)


_company_db_instance: Optional[CompanyDatabase] = None


def get_company_database() -> CompanyDatabase:
    """获取企业数据库单例"""
    global _company_db_instance
    if _company_db_instance is None:
        _company_db_instance = CompanyDatabase()
        logger.info("CompanyDatabase initialized (mock mode)")
    return _company_db_instance
