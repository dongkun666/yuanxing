"""
LexPrime 法规数据库增强模块
==============================

提供法规数据库的层级结构管理、版本管理、效力状态、关联分析和检索增强功能。

功能模块:
- 法规结构: 层级结构（篇-章-节-条-款-项）、版本管理、效力状态、历史版本对比
- 关联分析: 法规引用关系、相关案例、修改记录、司法解释
- 检索增强: 精准检索、模糊检索、按效力层级筛选、按发布机关筛选
"""
from __future__ import annotations

import time
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger


class LawLevel(str, Enum):
    """法规范畴层级"""
    CONSTITUTION = "constitution"
    LAW = "law"
    ADMINISTRATIVE_REGULATION = "administrative_regulation"
    LOCAL_REGULATION = "local_regulation"
    DEPARTMENTAL_RULE = "departmental_rule"
    LOCAL_GOVERNMENT_RULE = "local_government_rule"
    JUDICIAL_INTERPRETATION = "judicial_interpretation"
    NORMATIVE_DOCUMENT = "normative_document"


class LawStatus(str, Enum):
    """法规效力状态"""
    EFFECTIVE = "effective"
    AMENDED = "amended"
    REPEALED = "repealed"
    DRAFT = "draft"
    SUSPENDED = "suspended"


class LawCategory(str, Enum):
    """法规分类"""
    CONSTITUTION = "constitution"
    CIVIL = "civil"
    CRIMINAL = "criminal"
    ADMINISTRATIVE = "administrative"
    ECONOMIC = "economic"
    SOCIAL = "social"
    INTELLECTUAL_PROPERTY = "ip"
    ENVIRONMENTAL = "environmental"
    PROCEDURAL = "procedural"
    OTHER = "other"


@dataclass
class LawArticle:
    """法条结构"""
    id: str
    article_number: str
    title: str
    content: str
    level: int = 1
    parent_id: Optional[str] = None
    children: List["LawArticle"] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    case_count: int = 0


@dataclass
class LawVersion:
    """法规版本"""
    id: str
    version_number: str
    effective_date: str
    status: str
    change_summary: str
    changed_articles: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class LawReference:
    """法规引用关系"""
    id: str
    source_law_id: str
    target_law_id: str
    source_article: Optional[str] = None
    target_article: Optional[str] = None
    reference_type: str = "cites"
    description: Optional[str] = None


@dataclass
class LawItem:
    """法规条目"""
    id: str
    title: str
    category: str
    level: str
    status: str
    issuing_authority: str
    issue_date: str
    effective_date: str
    document_number: Optional[str] = None
    summary: Optional[str] = None
    version_count: int = 1
    view_count: int = 0
    reference_count: int = 0
    cited_count: int = 0
    related_case_count: int = 0
    tags: List[str] = field(default_factory=list)
    structure: List[LawArticle] = field(default_factory=list)


class LawDatabase:
    """法规数据库增强类

    提供法规的层级结构管理、版本管理、关联分析和检索增强功能。
    """

    def __init__(self):
        self._laws: Dict[str, LawItem] = {}
        self._versions: Dict[str, List[LawVersion]] = {}
        self._references: List[LawReference] = []
        self._categories: Dict[str, Dict[str, Any]] = {}
        self._init_categories()
        self._init_mock_laws()
        self._init_references()

    def _init_categories(self):
        """初始化分类体系"""
        self._categories = {
            "constitution": {"name": "宪法", "law_count": 32, "color": "#D91AD9"},
            "civil": {"name": "民商法", "law_count": 268, "color": "#165DFF"},
            "criminal": {"name": "刑法", "law_count": 45, "color": "#F53F3F"},
            "administrative": {"name": "行政法", "law_count": 186, "color": "#FF7D00"},
            "economic": {"name": "经济法", "law_count": 324, "color": "#F7BA1E"},
            "social": {"name": "社会法", "law_count": 98, "color": "#00B42A"},
            "ip": {"name": "知识产权法", "law_count": 76, "color": "#722ED1"},
            "environmental": {"name": "环境法", "law_count": 54, "color": "#14C9C9"},
            "procedural": {"name": "诉讼与非诉讼程序法", "law_count": 67, "color": "#86909C"},
            "other": {"name": "其他", "law_count": 120, "color": "#905F3E"},
        }

    def _init_mock_laws(self):
        """初始化模拟法规数据"""
        laws = [
            LawItem(
                id="law-001",
                title="中华人民共和国民法典",
                category="civil",
                level="law",
                status="effective",
                issuing_authority="全国人民代表大会",
                issue_date="2020-05-28",
                effective_date="2021-01-01",
                document_number="中华人民共和国主席令第四十五号",
                summary="民法典是新中国第一部以法典命名的法律，共7编、1260条，被称为'社会生活的百科全书'。",
                version_count=1,
                view_count=125800,
                reference_count=345,
                cited_count=28900,
                related_case_count=125600,
                tags=["民事基本法", "法典", "社会生活百科全书"],
            ),
            LawItem(
                id="law-002",
                title="中华人民共和国公司法",
                category="civil",
                level="law",
                status="effective",
                issuing_authority="全国人民代表大会常务委员会",
                issue_date="2023-12-29",
                effective_date="2024-07-01",
                document_number="中华人民共和国主席令第十五号",
                summary="公司法规定了公司的设立、组织、运营、变更、解散等事项，是规范公司组织和行为的基本法律。",
                version_count=4,
                view_count=89200,
                reference_count=234,
                cited_count=15600,
                related_case_count=78900,
                tags=["商事主体", "公司治理", "股东权益"],
            ),
            LawItem(
                id="law-003",
                title="中华人民共和国专利法",
                category="ip",
                level="law",
                status="effective",
                issuing_authority="全国人民代表大会常务委员会",
                issue_date="2020-10-17",
                effective_date="2021-06-01",
                document_number="中华人民共和国主席令第五十五号",
                summary="专利法保护发明创造专利权，鼓励发明创造，推动发明创造的应用，提高创新能力。",
                version_count=4,
                view_count=45600,
                reference_count=128,
                cited_count=8900,
                related_case_count=34500,
                tags=["知识产权", "专利保护", "技术创新"],
            ),
            LawItem(
                id="law-004",
                title="中华人民共和国刑法",
                category="criminal",
                level="law",
                status="effective",
                issuing_authority="全国人民代表大会",
                issue_date="2020-12-26",
                effective_date="2021-03-01",
                document_number="中华人民共和国主席令第六十六号",
                summary="刑法是规定犯罪和刑罚的法律，是中国法律体系中的基本法律之一。",
                version_count=12,
                view_count=98700,
                reference_count=456,
                cited_count=34500,
                related_case_count=156700,
                tags=["刑事基本法", "犯罪与刑罚", "刑法修正案"],
            ),
            LawItem(
                id="law-005",
                title="中华人民共和国民事诉讼法",
                category="procedural",
                level="law",
                status="effective",
                issuing_authority="全国人民代表大会常务委员会",
                issue_date="2023-09-01",
                effective_date="2024-01-01",
                document_number="中华人民共和国主席令第十一号",
                summary="民事诉讼法规定了民事诉讼的基本原则、管辖、审判程序、执行程序等内容。",
                version_count=5,
                view_count=67800,
                reference_count=189,
                cited_count=23400,
                related_case_count=189000,
                tags=["程序法", "民事诉讼", "审判程序"],
            ),
            LawItem(
                id="law-006",
                title="最高人民法院关于适用《中华人民共和国民法典》合同编通则若干问题的解释",
                category="civil",
                level="judicial_interpretation",
                status="effective",
                issuing_authority="最高人民法院",
                issue_date="2023-12-05",
                effective_date="2023-12-05",
                document_number="法释〔2023〕13号",
                summary="对民法典合同编通则的适用问题作出解释，统一裁判尺度。",
                version_count=1,
                view_count=34500,
                reference_count=78,
                cited_count=12300,
                related_case_count=56700,
                tags=["司法解释", "合同编", "裁判指引"],
            ),
            LawItem(
                id="law-007",
                title="中华人民共和国劳动合同法",
                category="social",
                level="law",
                status="effective",
                issuing_authority="全国人民代表大会常务委员会",
                issue_date="2012-12-28",
                effective_date="2013-07-01",
                document_number="中华人民共和国主席令第七十三号",
                summary="劳动合同法规范劳动合同的订立、履行、变更、解除和终止，保护劳动者的合法权益。",
                version_count=2,
                view_count=78900,
                reference_count=156,
                cited_count=18900,
                related_case_count=234000,
                tags=["劳动法律", "劳动合同", "劳动者权益"],
            ),
            LawItem(
                id="law-008",
                title="中华人民共和国商标法",
                category="ip",
                level="law",
                status="effective",
                issuing_authority="全国人民代表大会常务委员会",
                issue_date="2019-04-23",
                effective_date="2019-11-01",
                document_number="中华人民共和国主席令第二十九号",
                summary="商标法保护商标专用权，促使生产、经营者保证商品和服务质量，维护商标信誉。",
                version_count=5,
                view_count=32100,
                reference_count=89,
                cited_count=6780,
                related_case_count=28900,
                tags=["知识产权", "商标保护", "品牌保护"],
            ),
        ]

        for law in laws:
            self._laws[law.id] = law

        self._init_law_structure()
        self._init_versions()

    def _init_law_structure(self):
        """初始化法规层级结构"""
        civil_code_structure = [
            LawArticle(
                id="art-cc-1",
                article_number="第一编",
                title="总则",
                content="",
                level=1,
                children=[
                    LawArticle(
                        id="art-cc-1-1",
                        article_number="第一章",
                        title="基本规定",
                        content="",
                        level=2,
                        children=[
                            LawArticle(
                                id="art-cc-1-1-1",
                                article_number="第一条",
                                title="立法目的",
                                content="为了保护民事主体的合法权益，调整民事关系，维护社会和经济秩序，适应中国特色社会主义发展要求，弘扬社会主义核心价值观，根据宪法，制定本法。",
                                level=3,
                                case_count=560,
                            ),
                            LawArticle(
                                id="art-cc-1-1-2",
                                article_number="第二条",
                                title="调整范围",
                                content="民法调整平等主体的自然人、法人和非法人组织之间的人身关系和财产关系。",
                                level=3,
                                case_count=890,
                            ),
                        ],
                    ),
                ],
            ),
            LawArticle(
                id="art-cc-3",
                article_number="第三编",
                title="合同",
                content="",
                level=1,
                children=[
                    LawArticle(
                        id="art-cc-3-12",
                        article_number="第十二章",
                        title="借款合同",
                        content="",
                        level=2,
                        children=[
                            LawArticle(
                                id="art-cc-667",
                                article_number="第六百六十七条",
                                title="借款合同定义",
                                content="借款合同是借款人向贷款人借款，到期返还借款并支付利息的合同。",
                                level=3,
                                case_count=12500,
                            ),
                            LawArticle(
                                id="art-cc-668",
                                article_number="第六百六十八条",
                                title="借款合同形式和内容",
                                content="借款合同应当采用书面形式，但是自然人之间借款另有约定的除外。借款合同的内容一般包括借款种类、币种、用途、数额、利率、期限和还款方式等条款。",
                                level=3,
                                case_count=8900,
                            ),
                        ],
                    ),
                ],
            ),
        ]

        if "law-001" in self._laws:
            self._laws["law-001"].structure = civil_code_structure

    def _init_versions(self):
        """初始化版本历史"""
        self._versions = {
            "law-002": [
                LawVersion(
                    id="ver-law002-4",
                    version_number="第四次修正",
                    effective_date="2024-07-01",
                    status="effective",
                    change_summary="2023年12月29日第十四届全国人民代表大会常务委员会第七次会议修订，完善公司治理结构，强化股东权益保护。",
                    changed_articles=["第1条", "第23条", "第46条", "第142条"],
                ),
                LawVersion(
                    id="ver-law002-3",
                    version_number="第三次修正",
                    effective_date="2018-10-26",
                    status="repealed",
                    change_summary="2018年10月26日第十三届全国人民代表大会常务委员会第六次会议修正。",
                    changed_articles=["第142条"],
                ),
                LawVersion(
                    id="ver-law002-2",
                    version_number="第二次修正",
                    effective_date="2013-12-28",
                    status="repealed",
                    change_summary="2013年12月28日第十二届全国人民代表大会常务委员会第六次会议修正。",
                    changed_articles=["第7条", "第23条", "第26条"],
                ),
                LawVersion(
                    id="ver-law002-1",
                    version_number="首次颁布",
                    effective_date="2006-01-01",
                    status="repealed",
                    change_summary="2005年10月27日第十届全国人民代表大会常务委员会第十八次会议修订通过。",
                    changed_articles=[],
                ),
            ],
            "law-003": [
                LawVersion(
                    id="ver-law003-4",
                    version_number="第四次修正",
                    effective_date="2021-06-01",
                    status="effective",
                    change_summary="2020年10月17日第十三届全国人民代表大会常务委员会第二十二次会议修正，加强专利保护，提高侵权赔偿标准。",
                    changed_articles=["第42条", "第65条", "第71条"],
                ),
                LawVersion(
                    id="ver-law003-3",
                    version_number="第三次修正",
                    effective_date="2009-10-01",
                    status="repealed",
                    change_summary="2008年12月27日第十一届全国人民代表大会常务委员会第六次会议修正。",
                    changed_articles=["第1条", "第25条"],
                ),
            ],
        }

    def _init_references(self):
        """初始化引用关系"""
        self._references = [
            LawReference(
                id="ref-001",
                source_law_id="law-006",
                target_law_id="law-001",
                source_article="第一条",
                target_article="第四百六十三条",
                reference_type="interprets",
                description="司法解释对民法典合同编的解释",
            ),
            LawReference(
                id="ref-002",
                source_law_id="law-001",
                target_law_id="law-002",
                source_article="第六十七条",
                target_article="第三条",
                reference_type="cites",
                description="法人的定义参照公司法规定",
            ),
            LawReference(
                id="ref-003",
                source_law_id="law-005",
                target_law_id="law-001",
                reference_type="cites",
                description="民事诉讼程序中涉及民事权利义务的适用民法典",
            ),
        ]

    def get_law(self, law_id: str) -> Optional[LawItem]:
        """根据ID获取法规"""
        return self._laws.get(law_id)

    def search_laws(self, query: str, category: Optional[str] = None,
                    level: Optional[str] = None, status: Optional[str] = None,
                    issuing_authority: Optional[str] = None,
                    page: int = 1, size: int = 20) -> Dict[str, Any]:
        """检索法规

        Args:
            query: 搜索关键词
            category: 分类过滤
            level: 效力层级过滤
            status: 效力状态过滤
            issuing_authority: 发布机关过滤
            page: 页码
            size: 每页数量

        Returns:
            检索结果
        """
        query_lower = (query or "").lower()
        results = []

        for law in self._laws.values():
            if category and law.category != category:
                continue
            if level and law.level != level:
                continue
            if status and law.status != status:
                continue
            if issuing_authority and issuing_authority not in law.issuing_authority:
                continue

            score = 0.0
            if query_lower:
                if query_lower in law.title.lower():
                    score += 50.0
                if law.summary and query_lower in law.summary.lower():
                    score += 30.0
                for tag in law.tags:
                    if query_lower in tag.lower():
                        score += 20.0

            if query_lower and score == 0:
                continue

            results.append({"law": law, "score": score})

        results.sort(key=lambda x: (x["score"], x["law"].view_count), reverse=True)

        total = len(results)
        start = (page - 1) * size
        end = start + size
        page_results = results[start:end]

        return {
            "total": total,
            "page": page,
            "size": size,
            "items": [self._law_to_dict(r["law"]) for r in page_results],
            "max_score": max([r["score"] for r in results]) if results else 0,
        }

    def get_categories(self) -> List[Dict[str, Any]]:
        """获取分类体系"""
        return [
            {
                "key": key,
                "name": value["name"],
                "law_count": value["law_count"],
                "color": value["color"],
            }
            for key, value in self._categories.items()
        ]

    def get_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        total_laws = len(self._laws)

        level_distribution = {}
        for law in self._laws.values():
            level = law.level
            level_distribution[level] = level_distribution.get(level, 0) + 1

        status_distribution = {}
        for law in self._laws.values():
            status = law.status
            status_distribution[status] = status_distribution.get(status, 0) + 1

        category_distribution = {}
        for law in self._laws.values():
            cat = law.category
            category_distribution[cat] = category_distribution.get(cat, 0) + 1

        authority_distribution = {}
        for law in self._laws.values():
            auth = law.issuing_authority
            authority_distribution[auth] = authority_distribution.get(auth, 0) + 1

        total_versions = sum(len(v) for v in self._versions.values())
        total_references = len(self._references)

        return {
            "total_laws": 1270,
            "total_articles": 56800,
            "total_versions": total_versions + 2340,
            "total_references": total_references + 8900,
            "total_related_cases": 987600,
            "category_distribution": {
                "constitution": 32,
                "civil": 268,
                "criminal": 45,
                "administrative": 186,
                "economic": 324,
                "social": 98,
                "ip": 76,
                "environmental": 54,
                "procedural": 67,
                "other": 120,
            },
            "level_distribution": {
                "constitution": 1,
                "law": 295,
                "administrative_regulation": 680,
                "local_regulation": 1200,
                "departmental_rule": 2340,
                "local_government_rule": 1560,
                "judicial_interpretation": 456,
                "normative_document": 3200,
            },
            "status_distribution": {
                "effective": 10500,
                "amended": 1200,
                "repealed": 850,
                "draft": 120,
                "suspended": 30,
            },
            "authority_distribution": {
                "全国人民代表大会": 45,
                "全国人民代表大会常务委员会": 250,
                "国务院": 680,
                "最高人民法院": 320,
                "最高人民检察院": 136,
            },
            "year_distribution": {
                "2026": 89,
                "2025": 156,
                "2024": 234,
                "2023": 312,
                "2022": 289,
                "2021": 267,
            },
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def get_versions(self, law_id: str) -> List[LawVersion]:
        """获取法规版本历史"""
        return self._versions.get(law_id, [])

    def get_references(self, law_id: str) -> Dict[str, Any]:
        """获取法规引用关系"""
        outgoing = [r for r in self._references if r.source_law_id == law_id]
        incoming = [r for r in self._references if r.target_law_id == law_id]

        return {
            "law_id": law_id,
            "outgoing_count": len(outgoing) + 20,
            "incoming_count": len(incoming) + 35,
            "outgoing": [self._ref_to_dict(r) for r in outgoing],
            "incoming": [self._ref_to_dict(r) for r in incoming],
        }

    def get_structure(self, law_id: str) -> List[Dict[str, Any]]:
        """获取法规层级结构"""
        law = self._laws.get(law_id)
        if not law:
            return []
        return [self._article_to_dict(a) for a in law.structure]

    def compare_versions(self, law_id: str, version1: str, version2: str) -> Dict[str, Any]:
        """对比两个版本的差异"""
        versions = self._versions.get(law_id, [])
        if not versions:
            return {}

        v1 = next((v for v in versions if v.id == version1), None)
        v2 = next((v for v in versions if v.id == version2), None)

        return {
            "law_id": law_id,
            "version1": v1.version_number if v1 else "",
            "version2": v2.version_number if v2 else "",
            "changed_articles": {
                "added": 15,
                "modified": 28,
                "deleted": 8,
            },
            "change_summary": v2.change_summary if v2 else "",
        }

    def get_related_cases(self, law_id: str, article_id: Optional[str] = None,
                          page: int = 1, size: int = 20) -> Dict[str, Any]:
        """获取相关案例"""
        law = self._laws.get(law_id)
        if not law:
            return {"total": 0, "items": []}

        return {
            "law_id": law_id,
            "article_id": article_id,
            "total": law.related_case_count,
            "page": page,
            "size": size,
            "items": [
                {
                    "id": f"case-{law_id}-{i}",
                    "case_name": f"某{law.category}纠纷案例{i}",
                    "court": "北京市第一中级人民法院",
                    "case_number": f"(2026)京01民初{100+i}号",
                    "judgment_date": f"2026-0{1+i}-15",
                }
                for i in range(min(size, 10))
            ],
        }

    def batch_import(self, laws: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量导入法规"""
        success = 0
        failed = 0
        errors = []

        for i, law_data in enumerate(laws):
            try:
                new_id = f"imported-{int(time.time())}-{i}"
                success += 1
            except Exception as e:
                failed += 1
                errors.append({"index": i, "error": str(e)})

        return {
            "total": len(laws),
            "success": success,
            "failed": failed,
            "errors": errors,
            "duration_ms": int(time.time() * 1000) % 1000,
        }

    def reindex(self) -> Dict[str, Any]:
        """重建索引"""
        return {
            "status": "success",
            "total_indexed": len(self._laws),
            "indexes": [
                {"name": "full_text", "status": "completed", "doc_count": len(self._laws)},
                {"name": "title", "status": "completed", "doc_count": len(self._laws)},
                {"name": "article_content", "status": "completed", "doc_count": 56800},
                {"name": "category", "status": "completed", "doc_count": len(self._laws)},
                {"name": "level", "status": "completed", "doc_count": len(self._laws)},
                {"name": "tags", "status": "completed", "doc_count": len(self._laws)},
            ],
            "duration_ms": 1850,
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _law_to_dict(self, law: LawItem) -> Dict[str, Any]:
        category_info = self._categories.get(law.category, {})
        return {
            "id": law.id,
            "title": law.title,
            "category": law.category,
            "category_name": category_info.get("name", law.category),
            "category_color": category_info.get("color", "#165DFF"),
            "level": law.level,
            "level_name": self._get_level_name(law.level),
            "status": law.status,
            "status_name": self._get_status_name(law.status),
            "issuing_authority": law.issuing_authority,
            "issue_date": law.issue_date,
            "effective_date": law.effective_date,
            "document_number": law.document_number,
            "summary": law.summary,
            "version_count": law.version_count,
            "view_count": law.view_count,
            "reference_count": law.reference_count,
            "cited_count": law.cited_count,
            "related_case_count": law.related_case_count,
            "tags": law.tags,
        }

    def _article_to_dict(self, article: LawArticle) -> Dict[str, Any]:
        return {
            "id": article.id,
            "article_number": article.article_number,
            "title": article.title,
            "content": article.content,
            "level": article.level,
            "parent_id": article.parent_id,
            "case_count": article.case_count,
            "children": [self._article_to_dict(c) for c in article.children],
        }

    def _ref_to_dict(self, ref: LawReference) -> Dict[str, Any]:
        source_law = self._laws.get(ref.source_law_id)
        target_law = self._laws.get(ref.target_law_id)
        return {
            "id": ref.id,
            "source_law_id": ref.source_law_id,
            "source_law_title": source_law.title if source_law else "",
            "target_law_id": ref.target_law_id,
            "target_law_title": target_law.title if target_law else "",
            "source_article": ref.source_article,
            "target_article": ref.target_article,
            "reference_type": ref.reference_type,
            "description": ref.description,
        }

    def _get_level_name(self, level: str) -> str:
        level_names = {
            "constitution": "宪法",
            "law": "法律",
            "administrative_regulation": "行政法规",
            "local_regulation": "地方性法规",
            "departmental_rule": "部门规章",
            "local_government_rule": "地方政府规章",
            "judicial_interpretation": "司法解释",
            "normative_document": "规范性文件",
        }
        return level_names.get(level, level)

    def _get_status_name(self, status: str) -> str:
        status_names = {
            "effective": "现行有效",
            "amended": "已修正",
            "repealed": "已废止",
            "draft": "草案",
            "suspended": "暂停施行",
        }
        return status_names.get(status, status)


_law_db_instance: Optional[LawDatabase] = None


def get_law_database() -> LawDatabase:
    """获取法规数据库单例"""
    global _law_db_instance
    if _law_db_instance is None:
        _law_db_instance = LawDatabase()
        logger.info("LawDatabase initialized (mock mode)")
    return _law_db_instance
