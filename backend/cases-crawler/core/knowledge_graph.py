"""
LexPrime 法律知识图谱核心模块
=================================

提供法律领域的知识图谱能力，包括实体提取、关系抽取、图谱存储和图分析。

实体类型:
- 人物实体: 当事人、律师、法官
- 机构实体: 法院、律所、公司
- 法律实体: 法条、案由、罪名
- 事件实体: 案件、合同、判决

关系类型:
- 诉讼关系: 原告-被告
- 代理关系: 律师-当事人
- 引用关系: 案件-法条
- 层级关系: 上级法院-下级法院

图谱应用:
- 关联分析
- 路径推理
- 相似实体发现
- 社区发现
"""
from __future__ import annotations

import time
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger


class EntityType(str, Enum):
    """实体类型枚举"""
    PERSON = "person"
    LAWYER = "lawyer"
    JUDGE = "judge"
    COURT = "court"
    LAW_FIRM = "law_firm"
    COMPANY = "company"
    LAW_ARTICLE = "law_article"
    CAUSE = "cause"
    CHARGE = "charge"
    CASE = "case"
    CONTRACT = "contract"
    JUDGMENT = "judgment"


class RelationType(str, Enum):
    """关系类型枚举"""
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    REPRESENTS = "represents"
    CITES = "cites"
    SUPERIOR = "superior"
    EMPLOYS = "employs"
    TRIES = "tries"
    INVOLVES = "involves"
    RELATED_TO = "related_to"
    SHAREHOLDER = "shareholder"
    SUBSIDIARY = "subsidiary"


ENTITY_TYPE_LABELS = {
    EntityType.PERSON: "当事人",
    EntityType.LAWYER: "律师",
    EntityType.JUDGE: "法官",
    EntityType.COURT: "法院",
    EntityType.LAW_FIRM: "律所",
    EntityType.COMPANY: "公司",
    EntityType.LAW_ARTICLE: "法条",
    EntityType.CAUSE: "案由",
    EntityType.CHARGE: "罪名",
    EntityType.CASE: "案件",
    EntityType.CONTRACT: "合同",
    EntityType.JUDGMENT: "判决",
}

ENTITY_TYPE_COLORS = {
    EntityType.PERSON: "#F53F3F",
    EntityType.LAWYER: "#722ED1",
    EntityType.JUDGE: "#F7BA1E",
    EntityType.COURT: "#00B42A",
    EntityType.LAW_FIRM: "#3491FA",
    EntityType.COMPANY: "#FF7D00",
    EntityType.LAW_ARTICLE: "#14C9C9",
    EntityType.CAUSE: "#86909C",
    EntityType.CHARGE: "#D91AD9",
    EntityType.CASE: "#165DFF",
    EntityType.CONTRACT: "#0FC6C2",
    EntityType.JUDGMENT: "#7BC616",
}

RELATION_TYPE_LABELS = {
    RelationType.PLAINTIFF: "原告",
    RelationType.DEFENDANT: "被告",
    RelationType.REPRESENTS: "代理",
    RelationType.CITES: "引用",
    RelationType.SUPERIOR: "上级法院",
    RelationType.EMPLOYS: "雇佣",
    RelationType.TRIES: "审理",
    RelationType.INVOLVES: "涉及",
    RelationType.RELATED_TO: "相关",
    RelationType.SHAREHOLDER: "股东",
    RelationType.SUBSIDIARY: "子公司",
}


@dataclass
class KGEntity:
    """知识图谱实体"""
    id: str
    name: str
    type: EntityType
    sub_type: Optional[str] = None
    description: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    degree: int = 0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value if isinstance(self.type, EntityType) else self.type,
            "type_label": ENTITY_TYPE_LABELS.get(self.type, self.type),
            "sub_type": self.sub_type,
            "description": self.description,
            "properties": self.properties,
            "degree": self.degree,
            "color": ENTITY_TYPE_COLORS.get(self.type, "#165DFF"),
            "created_at": self.created_at,
        }


@dataclass
class KGRelation:
    """知识图谱关系"""
    id: str
    source_id: str
    target_id: str
    type: RelationType
    label: Optional[str] = None
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type.value if isinstance(self.type, RelationType) else self.type,
            "type_label": RELATION_TYPE_LABELS.get(self.type, self.type),
            "label": self.label or RELATION_TYPE_LABELS.get(self.type, self.type),
            "weight": self.weight,
            "properties": self.properties,
            "created_at": self.created_at,
        }


class KnowledgeGraph:
    """法律知识图谱类

    提供实体管理、关系抽取、图查询和分析功能。
    支持内存模式和 Neo4j 模式（可选）。
    """

    def __init__(self, use_neo4j: bool = False):
        self._entities: Dict[str, KGEntity] = {}
        self._relations: Dict[str, KGRelation] = {}
        self._adjacency: Dict[str, List[Tuple[str, str]]] = {}
        self._use_neo4j = use_neo4j
        self._init_mock_data()

    def _init_mock_data(self):
        """初始化模拟数据"""
        entities = [
            KGEntity(id="case-001", name="张三诉李四借款合同纠纷案", type=EntityType.CASE,
                     sub_type="借款合同纠纷", description="典型民间借贷纠纷案例",
                     properties={"case_number": "(2026)京01民初123号", "court": "北京市第一中级人民法院",
                                 "amount": "50万元", "status": "已判决"}, degree=8),
            KGEntity(id="case-002", name="王五与赵六股权纠纷案", type=EntityType.CASE,
                     sub_type="股权转让纠纷", description="公司股权争议案件",
                     properties={"case_number": "(2026)京02民初456号", "court": "北京市第二中级人民法院",
                                 "amount": "200万元", "status": "审理中"}, degree=6),
            KGEntity(id="case-003", name="某科技公司专利侵权案", type=EntityType.CASE,
                     sub_type="专利侵权纠纷", description="知识产权侵权诉讼",
                     properties={"case_number": "(2026)京73民初789号", "court": "北京知识产权法院",
                                 "amount": "1000万元", "status": "一审中"}, degree=7),
            KGEntity(id="person-001", name="张三", type=EntityType.PERSON,
                     sub_type="原告", properties={"gender": "男", "age": 35}, degree=3),
            KGEntity(id="person-002", name="李四", type=EntityType.PERSON,
                     sub_type="被告", properties={"gender": "男", "age": 40}, degree=3),
            KGEntity(id="person-003", name="王五", type=EntityType.PERSON,
                     sub_type="原告", properties={"gender": "男", "age": 45}, degree=3),
            KGEntity(id="person-004", name="赵六", type=EntityType.PERSON,
                     sub_type="被告", properties={"gender": "男", "age": 50}, degree=3),
            KGEntity(id="lawyer-001", name="王律师", type=EntityType.LAWYER,
                     sub_type="原告代理", description="北京某律师事务所高级合伙人",
                     properties={"firm": "北京正义律师事务所", "experience": 15,
                                 "specialties": ["合同纠纷", "公司法律事务"]}, degree=4),
            KGEntity(id="lawyer-002", name="李律师", type=EntityType.LAWYER,
                     sub_type="被告代理", description="北京某律师事务所合伙人",
                     properties={"firm": "北京正义律师事务所", "experience": 12,
                                 "specialties": ["民商事诉讼", "仲裁"]}, degree=3),
            KGEntity(id="lawyer-003", name="张律师", type=EntityType.LAWYER,
                     sub_type="知识产权律师", description="专注知识产权领域",
                     properties={"firm": "北京智衡律师事务所", "experience": 10,
                                 "specialties": ["专利", "商标", "著作权"]}, degree=3),
            KGEntity(id="judge-001", name="陈法官", type=EntityType.JUDGE,
                     sub_type="审判长", properties={"court": "北京市第一中级人民法院", "level": "高级法官"}, degree=2),
            KGEntity(id="judge-002", name="刘法官", type=EntityType.JUDGE,
                     sub_type="审判员", properties={"court": "北京知识产权法院", "level": "一级法官"}, degree=2),
            KGEntity(id="court-001", name="北京市第一中级人民法院", type=EntityType.COURT,
                     sub_type="中级人民法院", properties={"level": "中级", "region": "北京市"}, degree=4),
            KGEntity(id="court-002", name="北京市第二中级人民法院", type=EntityType.COURT,
                     sub_type="中级人民法院", properties={"level": "中级", "region": "北京市"}, degree=2),
            KGEntity(id="court-003", name="北京知识产权法院", type=EntityType.COURT,
                     sub_type="专门法院", properties={"level": "中级", "region": "北京市"}, degree=3),
            KGEntity(id="court-004", name="北京市高级人民法院", type=EntityType.COURT,
                     sub_type="高级人民法院", properties={"level": "高级", "region": "北京市"}, degree=3),
            KGEntity(id="court-005", name="最高人民法院", type=EntityType.COURT,
                     sub_type="最高人民法院", properties={"level": "最高", "region": "北京市"}, degree=2),
            KGEntity(id="firm-001", name="北京正义律师事务所", type=EntityType.LAW_FIRM,
                     properties={"size": "大型", "lawyers_count": 120, "specialties": ["民商事", "刑事", "公司法"]}, degree=3),
            KGEntity(id="firm-002", name="北京智衡律师事务所", type=EntityType.LAW_FIRM,
                     properties={"size": "中型", "lawyers_count": 35, "specialties": ["知识产权", "反垄断"]}, degree=2),
            KGEntity(id="company-001", name="北京创新科技有限公司", type=EntityType.COMPANY,
                     sub_type="原告", properties={"industry": "软件和信息技术服务业", "region": "北京市",
                                                "legal_rep": "王五"}, degree=4),
            KGEntity(id="company-002", name="北京智联科技股份有限公司", type=EntityType.COMPANY,
                     sub_type="被告", properties={"industry": "互联网科技", "region": "北京市",
                                                "legal_rep": "赵六"}, degree=4),
            KGEntity(id="company-003", name="北京宏达投资有限公司", type=EntityType.COMPANY,
                     properties={"industry": "投资", "region": "北京市", "legal_rep": "钱七"}, degree=2),
            KGEntity(id="law-001", name="民法典 第六百六十七条", type=EntityType.LAW_ARTICLE,
                     sub_type="借款合同定义", description="借款合同是借款人向贷款人借款，到期返还借款并支付利息的合同。",
                     properties={"law": "民法典", "part": "第三编 合同", "chapter": "第十二章 借款合同"}, degree=2),
            KGEntity(id="law-002", name="民法典 第五百七十七条", type=EntityType.LAW_ARTICLE,
                     sub_type="违约责任", description="当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。",
                     properties={"law": "民法典", "part": "第三编 合同", "chapter": "第一分编 通则"}, degree=3),
            KGEntity(id="law-003", name="公司法 第七十一条", type=EntityType.LAW_ARTICLE,
                     sub_type="股权转让", description="有限责任公司的股东之间可以相互转让其全部或者部分股权。",
                     properties={"law": "公司法", "part": "第三章 有限责任公司的股权转让"}, degree=2),
            KGEntity(id="law-004", name="专利法 第六十五条", type=EntityType.LAW_ARTICLE,
                     sub_type="侵权赔偿", description="侵犯专利权的赔偿数额按照权利人因被侵权所受到的实际损失确定。",
                     properties={"law": "专利法", "part": "第七章 专利权的保护"}, degree=2),
            KGEntity(id="cause-001", name="借款合同纠纷", type=EntityType.CAUSE,
                     properties={"category": "合同纠纷", "level": "四级案由"}, degree=2),
            KGEntity(id="cause-002", name="股权转让纠纷", type=EntityType.CAUSE,
                     properties={"category": "与公司有关的纠纷", "level": "四级案由"}, degree=2),
            KGEntity(id="cause-003", name="专利侵权纠纷", type=EntityType.CAUSE,
                     properties={"category": "知识产权权属、侵权纠纷", "level": "四级案由"}, degree=2),
            KGEntity(id="charge-001", name="职务侵占罪", type=EntityType.CHARGE,
                     properties={"criminal_law": "刑法第271条", "max_penalty": "无期徒刑"}, degree=1),
            KGEntity(id="contract-001", name="借款合同", type=EntityType.CONTRACT,
                     properties={"type": "借款合同", "amount": "50万元", "term": "1年"}, degree=2),
        ]

        for entity in entities:
            self._entities[entity.id] = entity
            self._adjacency[entity.id] = []

        relations = [
            KGRelation(id="rel-001", source_id="case-001", target_id="person-001",
                       type=RelationType.PLAINTIFF, label="原告", weight=1.0),
            KGRelation(id="rel-002", source_id="case-001", target_id="person-002",
                       type=RelationType.DEFENDANT, label="被告", weight=1.0),
            KGRelation(id="rel-003", source_id="person-001", target_id="lawyer-001",
                       type=RelationType.REPRESENTS, label="委托代理", weight=1.0),
            KGRelation(id="rel-004", source_id="person-002", target_id="lawyer-002",
                       type=RelationType.REPRESENTS, label="委托代理", weight=1.0),
            KGRelation(id="rel-005", source_id="case-001", target_id="court-001",
                       type=RelationType.TRIES, label="审理", weight=1.0),
            KGRelation(id="rel-006", source_id="case-001", target_id="law-001",
                       type=RelationType.CITES, label="引用法条", weight=1.0),
            KGRelation(id="rel-007", source_id="case-001", target_id="law-002",
                       type=RelationType.CITES, label="引用法条", weight=0.8),
            KGRelation(id="rel-008", source_id="case-001", target_id="cause-001",
                       type=RelationType.INVOLVES, label="涉及案由", weight=1.0),
            KGRelation(id="rel-009", source_id="case-001", target_id="contract-001",
                       type=RelationType.RELATED_TO, label="涉案合同", weight=1.0),
            KGRelation(id="rel-010", source_id="case-001", target_id="judge-001",
                       type=RelationType.RELATED_TO, label="审判长", weight=0.8),
            KGRelation(id="rel-011", source_id="case-002", target_id="person-003",
                       type=RelationType.PLAINTIFF, label="原告", weight=1.0),
            KGRelation(id="rel-012", source_id="case-002", target_id="person-004",
                       type=RelationType.DEFENDANT, label="被告", weight=1.0),
            KGRelation(id="rel-013", source_id="case-002", target_id="court-002",
                       type=RelationType.TRIES, label="审理", weight=1.0),
            KGRelation(id="rel-014", source_id="case-002", target_id="law-003",
                       type=RelationType.CITES, label="引用法条", weight=1.0),
            KGRelation(id="rel-015", source_id="case-002", target_id="cause-002",
                       type=RelationType.INVOLVES, label="涉及案由", weight=1.0),
            KGRelation(id="rel-016", source_id="case-003", target_id="company-001",
                       type=RelationType.PLAINTIFF, label="原告", weight=1.0),
            KGRelation(id="rel-017", source_id="case-003", target_id="company-002",
                       type=RelationType.DEFENDANT, label="被告", weight=1.0),
            KGRelation(id="rel-018", source_id="case-003", target_id="court-003",
                       type=RelationType.TRIES, label="审理", weight=1.0),
            KGRelation(id="rel-019", source_id="case-003", target_id="law-004",
                       type=RelationType.CITES, label="引用法条", weight=1.0),
            KGRelation(id="rel-020", source_id="case-003", target_id="cause-003",
                       type=RelationType.INVOLVES, label="涉及案由", weight=1.0),
            KGRelation(id="rel-021", source_id="case-003", target_id="lawyer-003",
                       type=RelationType.REPRESENTS, label="原告代理", weight=1.0),
            KGRelation(id="rel-022", source_id="case-003", target_id="judge-002",
                       type=RelationType.RELATED_TO, label="主审法官", weight=0.8),
            KGRelation(id="rel-023", source_id="lawyer-001", target_id="firm-001",
                       type=RelationType.EMPLOYS, label="任职于", weight=1.0),
            KGRelation(id="rel-024", source_id="lawyer-002", target_id="firm-001",
                       type=RelationType.EMPLOYS, label="任职于", weight=1.0),
            KGRelation(id="rel-025", source_id="lawyer-003", target_id="firm-002",
                       type=RelationType.EMPLOYS, label="任职于", weight=1.0),
            KGRelation(id="rel-026", source_id="court-001", target_id="court-004",
                       type=RelationType.SUPERIOR, label="上级法院", weight=1.0),
            KGRelation(id="rel-027", source_id="court-002", target_id="court-004",
                       type=RelationType.SUPERIOR, label="上级法院", weight=1.0),
            KGRelation(id="rel-028", source_id="court-003", target_id="court-004",
                       type=RelationType.SUPERIOR, label="上级法院", weight=1.0),
            KGRelation(id="rel-029", source_id="court-004", target_id="court-005",
                       type=RelationType.SUPERIOR, label="上级法院", weight=1.0),
            KGRelation(id="rel-030", source_id="company-003", target_id="company-001",
                       type=RelationType.SHAREHOLDER, label="持股20%", weight=0.6),
            KGRelation(id="rel-031", source_id="person-003", target_id="company-001",
                       type=RelationType.SHAREHOLDER, label="持股60%", weight=1.0),
            KGRelation(id="rel-032", source_id="person-004", target_id="company-002",
                       type=RelationType.SHAREHOLDER, label="持股70%", weight=1.0),
        ]

        for rel in relations:
            self._relations[rel.id] = rel
            if rel.source_id in self._adjacency:
                self._adjacency[rel.source_id].append((rel.target_id, rel.id))
            if rel.target_id in self._adjacency:
                self._adjacency[rel.target_id].append((rel.source_id, rel.id))

    def get_entity(self, entity_id: str) -> Optional[KGEntity]:
        """根据ID获取实体"""
        return self._entities.get(entity_id)

    def search_entities(self, query: str, entity_type: Optional[str] = None,
                        limit: int = 20) -> List[KGEntity]:
        """搜索实体

        Args:
            query: 搜索关键词
            entity_type: 实体类型过滤
            limit: 返回数量限制

        Returns:
            匹配的实体列表
        """
        results = []
        query_lower = query.lower()

        for entity in self._entities.values():
            if entity_type and entity.type.value != entity_type:
                continue

            name_match = query_lower in entity.name.lower()
            desc_match = entity.description and query_lower in entity.description.lower()

            if name_match or desc_match:
                results.append(entity)
                if len(results) >= limit:
                    break

        return sorted(results, key=lambda e: e.degree, reverse=True)

    def get_relation(self, relation_id: str) -> Optional[KGRelation]:
        """根据ID获取关系"""
        return self._relations.get(relation_id)

    def get_entity_relations(self, entity_id: str, relation_type: Optional[str] = None,
                             direction: str = "all") -> List[KGRelation]:
        """获取实体的所有关系

        Args:
            entity_id: 实体ID
            relation_type: 关系类型过滤
            direction: 方向 (outgoing/incoming/all)

        Returns:
            关系列表
        """
        results = []

        for rel in self._relations.values():
            if direction == "outgoing" and rel.source_id != entity_id:
                continue
            if direction == "incoming" and rel.target_id != entity_id:
                continue
            if direction == "all" and rel.source_id != entity_id and rel.target_id != entity_id:
                continue
            if relation_type and rel.type.value != relation_type:
                continue
            results.append(rel)

        return results

    def get_neighbors(self, entity_id: str, entity_type: Optional[str] = None,
                      relation_type: Optional[str] = None, depth: int = 1) -> List[KGEntity]:
        """获取实体的邻居节点

        Args:
            entity_id: 实体ID
            entity_type: 邻居实体类型过滤
            relation_type: 关系类型过滤
            depth: 深度 (当前仅支持1层)

        Returns:
            邻居实体列表
        """
        if entity_id not in self._adjacency:
            return []

        neighbor_ids = set()
        for neighbor_id, rel_id in self._adjacency[entity_id]:
            if relation_type:
                rel = self._relations.get(rel_id)
                if rel and rel.type.value != relation_type:
                    continue
            neighbor_ids.add(neighbor_id)

        neighbors = []
        for nid in neighbor_ids:
            entity = self._entities.get(nid)
            if entity:
                if entity_type and entity.type.value != entity_type:
                    continue
                neighbors.append(entity)

        return sorted(neighbors, key=lambda e: e.degree, reverse=True)

    def get_subgraph(self, center_id: str, depth: int = 2,
                     entity_types: Optional[List[str]] = None,
                     relation_types: Optional[List[str]] = None,
                     max_nodes: int = 50) -> Dict[str, Any]:
        """获取以某实体为中心的子图

        Args:
            center_id: 中心实体ID
            depth: 遍历深度
            entity_types: 实体类型过滤
            relation_types: 关系类型过滤
            max_nodes: 最大节点数

        Returns:
            子图数据 (nodes, edges, stats)
        """
        visited = set()
        nodes = []
        edges = []
        queue = [(center_id, 0)]

        while queue and len(nodes) < max_nodes:
            current_id, current_depth = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            entity = self._entities.get(current_id)
            if entity:
                if entity_types and entity.type.value not in entity_types:
                    continue
                nodes.append(entity.to_dict())

            if current_depth < depth:
                for neighbor_id, rel_id in self._adjacency.get(current_id, []):
                    if neighbor_id not in visited:
                        rel = self._relations.get(rel_id)
                        if rel:
                            if relation_types and rel.type.value not in relation_types:
                                continue
                            edges.append(rel.to_dict())
                            queue.append((neighbor_id, current_depth + 1))

        stats = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "center_id": center_id,
            "depth": depth,
        }

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": stats,
        }

    def find_path(self, start_id: str, end_id: str,
                  max_depth: int = 4,
                  relation_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """查找两个实体之间的路径

        Args:
            start_id: 起始实体ID
            end_id: 目标实体ID
            max_depth: 最大路径深度
            relation_types: 关系类型过滤

        Returns:
            路径列表，每条路径包含节点和关系
        """
        if start_id not in self._entities or end_id not in self._entities:
            return []

        paths = []
        queue = [(start_id, [start_id], [])]
        visited = set()

        while queue:
            current_id, path_nodes, path_rels = queue.pop(0)
            if len(path_nodes) > max_depth + 1:
                continue

            if current_id == end_id and len(path_nodes) > 1:
                path_entities = [self._entities[nid].to_dict() for nid in path_nodes if nid in self._entities]
                path_relations = [self._relations[rid].to_dict() for rid in path_rels if rid in self._relations]
                paths.append({
                    "nodes": path_entities,
                    "relations": path_relations,
                    "length": len(path_nodes) - 1,
                })
                if len(paths) >= 5:
                    break
                continue

            if current_id in visited:
                continue
            visited.add(current_id)

            for neighbor_id, rel_id in self._adjacency.get(current_id, []):
                if neighbor_id in path_nodes:
                    continue
                rel = self._relations.get(rel_id)
                if rel and relation_types and rel.type.value not in relation_types:
                    continue
                queue.append((neighbor_id, path_nodes + [neighbor_id], path_rels + [rel_id]))

        return sorted(paths, key=lambda p: p["length"])

    def find_similar_entities(self, entity_id: str,
                              entity_type: Optional[str] = None,
                              top_k: int = 10) -> List[Dict[str, Any]]:
        """发现相似实体

        基于共同邻居数计算相似度（Jaccard 相似度）

        Args:
            entity_id: 目标实体ID
            entity_type: 相似实体类型过滤
            top_k: 返回数量

        Returns:
            相似实体列表，带相似度分数
        """
        if entity_id not in self._entities:
            return []

        target_neighbors = set()
        for neighbor_id, _ in self._adjacency.get(entity_id, []):
            target_neighbors.add(neighbor_id)

        if not target_neighbors:
            return []

        similarities = []

        for other_id, other_entity in self._entities.items():
            if other_id == entity_id:
                continue
            if entity_type and other_entity.type.value != entity_type:
                continue

            other_neighbors = set()
            for neighbor_id, _ in self._adjacency.get(other_id, []):
                other_neighbors.add(neighbor_id)

            if not other_neighbors:
                continue

            intersection = target_neighbors & other_neighbors
            union = target_neighbors | other_neighbors

            if union:
                jaccard = len(intersection) / len(union)
                if jaccard > 0:
                    similarities.append({
                        "entity": other_entity.to_dict(),
                        "similarity": round(jaccard, 4),
                        "common_neighbors": len(intersection),
                    })

        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        """获取知识图谱统计信息"""
        type_counts = {}
        for entity in self._entities.values():
            t = entity.type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        rel_type_counts = {}
        for rel in self._relations.values():
            t = rel.type.value
            rel_type_counts[t] = rel_type_counts.get(t, 0) + 1

        degrees = [e.degree for e in self._entities.values()]
        avg_degree = sum(degrees) / len(degrees) if degrees else 0

        return {
            "total_entities": len(self._entities),
            "total_relations": len(self._relations),
            "entity_types": type_counts,
            "relation_types": rel_type_counts,
            "avg_degree": round(avg_degree, 2),
            "max_degree": max(degrees) if degrees else 0,
            "density": round(
                (2 * len(self._relations)) / (len(self._entities) * (len(self._entities) - 1)), 6
            ) if len(self._entities) > 1 else 0,
        }

    def detect_communities(self) -> List[List[str]]:
        """社区发现（简单实现：基于连通分量）

        Returns:
            社区列表，每个社区是实体ID列表
        """
        visited = set()
        communities = []

        for entity_id in self._entities:
            if entity_id in visited:
                continue

            community = []
            stack = [entity_id]

            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                community.append(current)

                for neighbor_id, _ in self._adjacency.get(current, []):
                    if neighbor_id not in visited:
                        stack.append(neighbor_id)

            if community:
                communities.append(community)

        return sorted(communities, key=len, reverse=True)

    def extract_entities_from_text(self, text: str) -> List[KGEntity]:
        """从文本中提取实体（模拟实现）

        Args:
            text: 法律文本

        Returns:
            提取的实体列表
        """
        extracted = []
        text_lower = text.lower()

        for entity in self._entities.values():
            if entity.name.lower() in text_lower:
                extracted.append(entity)

        return extracted

    def extract_relations_from_text(self, text: str) -> List[KGRelation]:
        """从文本中抽取关系（模拟实现）

        Args:
            text: 法律文本

        Returns:
            抽取的关系列表
        """
        entities = self.extract_entities_from_text(text)
        entity_ids = {e.id for e in entities}
        relations = []

        for rel in self._relations.values():
            if rel.source_id in entity_ids and rel.target_id in entity_ids:
                relations.append(rel)

        return relations


_kg_instance: Optional[KnowledgeGraph] = None


def get_knowledge_graph() -> KnowledgeGraph:
    """获取知识图谱单例"""
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = KnowledgeGraph()
        logger.info("KnowledgeGraph initialized (mock mode)")
    return _kg_instance
