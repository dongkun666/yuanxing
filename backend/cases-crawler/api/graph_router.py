"""
LexPrime 法律关系图谱 API
==========================

可视化法律关系网络，支持案件、企业、律师多维度关系图谱。

节点类型: 当事人、律师、法院、案件、法规
关系类型: 诉讼关系、代理关系、引用关系

端点:
- GET /api/graph/case/{id}     案件关系图谱
- GET /api/graph/company/{id}  企业关系图谱
- GET /api/graph/lawyer/{id}   律师关系图谱
- GET /api/graph/health        健康检查

支持 mock 模式: 返回模拟图谱数据
"""
from __future__ import annotations

import time
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/graph", tags=["graph"])

MOCK_MODE = True


# ========== Request / Response Models ==========

class GraphNode(BaseModel):
    """图谱节点"""
    id: str
    label: str
    type: str
    sub_type: Optional[str] = None
    size: int = 30
    color: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class GraphEdge(BaseModel):
    """图谱边（关系）"""
    id: str
    source: str
    target: str
    label: str
    type: str
    value: Optional[float] = None


class GraphResponse(BaseModel):
    """图谱响应"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    center_node_id: str
    stats: Dict[str, Any]


# ========== Mock Data ==========

NODE_COLORS = {
    "case": "#165DFF",
    "person": "#F53F3F",
    "company": "#FF7D00",
    "lawyer": "#722ED1",
    "court": "#00B42A",
    "law": "#14C9C9"
}

def get_case_graph(case_id: str) -> Dict[str, Any]:
    """生成案件关系图谱 mock 数据"""
    nodes = [
        {
            "id": "case-001",
            "label": "张三诉李四借款合同纠纷案",
            "type": "case",
            "sub_type": "借款合同纠纷",
            "size": 50,
            "color": NODE_COLORS["case"],
            "data": {
                "case_number": "(2026)京01民初123号",
                "court": "北京市第一中级人民法院",
                "amount": "50万元",
                "status": "一审中"
            }
        },
        {
            "id": "person-001",
            "label": "张三",
            "type": "person",
            "sub_type": "原告",
            "size": 35,
            "color": NODE_COLORS["person"],
            "data": {"role": "原告", "gender": "男"}
        },
        {
            "id": "person-002",
            "label": "李四",
            "type": "person",
            "sub_type": "被告",
            "size": 35,
            "color": NODE_COLORS["person"],
            "data": {"role": "被告", "gender": "男"}
        },
        {
            "id": "lawyer-001",
            "label": "王律师",
            "type": "lawyer",
            "sub_type": "原告代理",
            "size": 32,
            "color": NODE_COLORS["lawyer"],
            "data": {"firm": "北京某律师事务所", "role": "原告代理人"}
        },
        {
            "id": "lawyer-002",
            "label": "赵律师",
            "type": "lawyer",
            "sub_type": "被告代理",
            "size": 32,
            "color": NODE_COLORS["lawyer"],
            "data": {"firm": "北京某律师事务所", "role": "被告代理人"}
        },
        {
            "id": "court-001",
            "label": "北京市第一中级人民法院",
            "type": "court",
            "sub_type": "审理法院",
            "size": 40,
            "color": NODE_COLORS["court"],
            "data": {"level": "中级人民法院"}
        },
        {
            "id": "law-001",
            "label": "民法典 第667条",
            "type": "law",
            "sub_type": "借款合同定义",
            "size": 28,
            "color": NODE_COLORS["law"],
            "data": {"article": "第六百六十七条"}
        },
        {
            "id": "law-002",
            "label": "民间借贷规定 第25条",
            "type": "law",
            "sub_type": "利率限制",
            "size": 28,
            "color": NODE_COLORS["law"],
            "data": {"article": "第二十五条"}
        },
        {
            "id": "company-001",
            "label": "北京某投资公司",
            "type": "company",
            "sub_type": "担保人",
            "size": 36,
            "color": NODE_COLORS["company"],
            "data": {"role": "连带责任保证人"}
        }
    ]

    edges = [
        {
            "id": "edge-001",
            "source": "case-001",
            "target": "person-001",
            "label": "原告",
            "type": "litigation",
            "value": 1
        },
        {
            "id": "edge-002",
            "source": "case-001",
            "target": "person-002",
            "label": "被告",
            "type": "litigation",
            "value": 1
        },
        {
            "id": "edge-003",
            "source": "person-001",
            "target": "lawyer-001",
            "label": "委托代理",
            "type": "agency",
            "value": 1
        },
        {
            "id": "edge-004",
            "source": "person-002",
            "target": "lawyer-002",
            "label": "委托代理",
            "type": "agency",
            "value": 1
        },
        {
            "id": "edge-005",
            "source": "case-001",
            "target": "court-001",
            "label": "审理",
            "type": "jurisdiction",
            "value": 1
        },
        {
            "id": "edge-006",
            "source": "case-001",
            "target": "law-001",
            "label": "引用",
            "type": "citation",
            "value": 1
        },
        {
            "id": "edge-007",
            "source": "case-001",
            "target": "law-002",
            "label": "引用",
            "type": "citation",
            "value": 1
        },
        {
            "id": "edge-008",
            "source": "case-001",
            "target": "company-001",
            "label": "担保人",
            "type": "guarantee",
            "value": 1
        },
        {
            "id": "edge-009",
            "source": "person-001",
            "target": "person-002",
            "label": "借款关系",
            "type": "civil_relation",
            "value": 1
        }
    ]

    stats = {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "node_types": {
            "case": 1,
            "person": 2,
            "lawyer": 2,
            "court": 1,
            "law": 2,
            "company": 1
        },
        "relation_types": {
            "litigation": 2,
            "agency": 2,
            "jurisdiction": 1,
            "citation": 2,
            "guarantee": 1,
            "civil_relation": 1
        }
    }

    return {
        "nodes": nodes,
        "edges": edges,
        "center_node_id": "case-001",
        "stats": stats
    }


def get_company_graph(company_id: str) -> Dict[str, Any]:
    """生成企业关系图谱 mock 数据"""
    nodes = [
        {
            "id": "company-001",
            "label": "北京某科技有限公司",
            "type": "company",
            "sub_type": "目标企业",
            "size": 50,
            "color": NODE_COLORS["company"],
            "data": {
                "unified_id": "91110101MA01ABCDEF",
                "legal_rep": "张三",
                "registered_capital": "1000万元",
                "status": "存续"
            }
        },
        {
            "id": "person-001",
            "label": "张三",
            "type": "person",
            "sub_type": "法定代表人",
            "size": 35,
            "color": NODE_COLORS["person"],
            "data": {"role": "法定代表人、股东", "share_ratio": "60%"}
        },
        {
            "id": "person-002",
            "label": "李四",
            "type": "person",
            "sub_type": "股东",
            "size": 32,
            "color": NODE_COLORS["person"],
            "data": {"role": "股东", "share_ratio": "40%"}
        },
        {
            "id": "company-002",
            "label": "北京某投资合伙企业",
            "type": "company",
            "sub_type": "子公司",
            "size": 38,
            "color": NODE_COLORS["company"],
            "data": {"relation": "全资子公司"}
        },
        {
            "id": "company-003",
            "label": "上海某贸易公司",
            "type": "company",
            "sub_type": "合作伙伴",
            "size": 34,
            "color": NODE_COLORS["company"],
            "data": {"relation": "长期合作伙伴"}
        },
        {
            "id": "case-001",
            "label": "某买卖合同纠纷案",
            "type": "case",
            "sub_type": "作为原告",
            "size": 36,
            "color": NODE_COLORS["case"],
            "data": {"case_number": "(2025)沪01民初456号", "role": "原告"}
        },
        {
            "id": "case-002",
            "label": "某借款合同纠纷案",
            "type": "case",
            "sub_type": "作为被告",
            "size": 36,
            "color": NODE_COLORS["case"],
            "data": {"case_number": "(2026)京01民初789号", "role": "被告"}
        },
        {
            "id": "lawyer-001",
            "label": "王律师",
            "type": "lawyer",
            "sub_type": "常年法律顾问",
            "size": 32,
            "color": NODE_COLORS["lawyer"],
            "data": {"firm": "北京某律师事务所"}
        },
        {
            "id": "court-001",
            "label": "北京知识产权法院",
            "type": "court",
            "sub_type": "管辖法院",
            "size": 36,
            "color": NODE_COLORS["court"],
            "data": {}
        }
    ]

    edges = [
        {
            "id": "edge-001",
            "source": "company-001",
            "target": "person-001",
            "label": "法定代表人",
            "type": "executive",
            "value": 1
        },
        {
            "id": "edge-002",
            "source": "company-001",
            "target": "person-002",
            "label": "股东 (40%)",
            "type": "shareholder",
            "value": 0.8
        },
        {
            "id": "edge-003",
            "source": "company-001",
            "target": "company-002",
            "label": "全资子公司",
            "type": "subsidiary",
            "value": 1
        },
        {
            "id": "edge-004",
            "source": "company-001",
            "target": "company-003",
            "label": "合作关系",
            "type": "partner",
            "value": 0.6
        },
        {
            "id": "edge-005",
            "source": "company-001",
            "target": "case-001",
            "label": "原告",
            "type": "litigation",
            "value": 1
        },
        {
            "id": "edge-006",
            "source": "company-001",
            "target": "case-002",
            "label": "被告",
            "type": "litigation",
            "value": 1
        },
        {
            "id": "edge-007",
            "source": "company-001",
            "target": "lawyer-001",
            "label": "法律顾问",
            "type": "agency",
            "value": 1
        },
        {
            "id": "edge-008",
            "source": "case-001",
            "target": "court-001",
            "label": "审理",
            "type": "jurisdiction",
            "value": 1
        },
        {
            "id": "edge-009",
            "source": "person-001",
            "target": "person-002",
            "label": "一致行动人",
            "type": "agreement",
            "value": 0.7
        }
    ]

    stats = {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "node_types": {
            "company": 3,
            "person": 2,
            "case": 2,
            "lawyer": 1,
            "court": 1
        },
        "related_cases": 2,
        "related_companies": 2
    }

    return {
        "nodes": nodes,
        "edges": edges,
        "center_node_id": "company-001",
        "stats": stats
    }


def get_lawyer_graph(lawyer_id: str) -> Dict[str, Any]:
    """生成律师关系图谱 mock 数据"""
    nodes = [
        {
            "id": "lawyer-001",
            "label": "王律师",
            "type": "lawyer",
            "sub_type": "合伙人",
            "size": 50,
            "color": NODE_COLORS["lawyer"],
            "data": {
                "firm": "北京某律师事务所",
                "position": "高级合伙人",
                "specialties": ["合同纠纷", "公司法律", "知识产权"],
                "experience_years": 15
            }
        },
        {
            "id": "case-001",
            "label": "某科技公司股权纠纷案",
            "type": "case",
            "sub_type": "代理原告",
            "size": 36,
            "color": NODE_COLORS["case"],
            "data": {"case_number": "(2026)京01民初001号", "result": "胜诉"}
        },
        {
            "id": "case-002",
            "label": "某房地产开发合同案",
            "type": "case",
            "sub_type": "代理被告",
            "size": 36,
            "color": NODE_COLORS["case"],
            "data": {"case_number": "(2025)京02民初002号", "result": "调解"}
        },
        {
            "id": "case-003",
            "label": "某知识产权侵权案",
            "type": "case",
            "sub_type": "代理原告",
            "size": 36,
            "color": NODE_COLORS["case"],
            "data": {"case_number": "(2026)京73民初003号", "result": "审理中"}
        },
        {
            "id": "case-004",
            "label": "某并购重组项目",
            "type": "case",
            "sub_type": "非诉业务",
            "size": 34,
            "color": NODE_COLORS["case"],
            "data": {"type": "非诉", "amount": "5亿元"}
        },
        {
            "id": "company-001",
            "label": "北京某科技公司",
            "type": "company",
            "sub_type": "常年客户",
            "size": 38,
            "color": NODE_COLORS["company"],
            "data": {"client_type": "常年法律顾问单位"}
        },
        {
            "id": "company-002",
            "label": "北京某房地产公司",
            "type": "company",
            "sub_type": "重要客户",
            "size": 36,
            "color": NODE_COLORS["company"],
            "data": {"client_type": "重要客户"}
        },
        {
            "id": "lawyer-002",
            "label": "李律师",
            "type": "lawyer",
            "sub_type": "同事",
            "size": 30,
            "color": NODE_COLORS["lawyer"],
            "data": {"firm": "北京某律师事务所", "position": "合伙人"}
        },
        {
            "id": "lawyer-003",
            "label": "张律师",
            "type": "lawyer",
            "sub_type": "同事",
            "size": 30,
            "color": NODE_COLORS["lawyer"],
            "data": {"firm": "北京某律师事务所", "position": "资深律师"}
        },
        {
            "id": "court-001",
            "label": "北京市第一中级人民法院",
            "type": "court",
            "sub_type": "经常出庭",
            "size": 38,
            "color": NODE_COLORS["court"],
            "data": {}
        }
    ]

    edges = [
        {
            "id": "edge-001",
            "source": "lawyer-001",
            "target": "case-001",
            "label": "代理原告",
            "type": "agency",
            "value": 1
        },
        {
            "id": "edge-002",
            "source": "lawyer-001",
            "target": "case-002",
            "label": "代理被告",
            "type": "agency",
            "value": 1
        },
        {
            "id": "edge-003",
            "source": "lawyer-001",
            "target": "case-003",
            "label": "代理原告",
            "type": "agency",
            "value": 1
        },
        {
            "id": "edge-004",
            "source": "lawyer-001",
            "target": "case-004",
            "label": "主办律师",
            "type": "agency",
            "value": 0.8
        },
        {
            "id": "edge-005",
            "source": "lawyer-001",
            "target": "company-001",
            "label": "法律顾问",
            "type": "client",
            "value": 1
        },
        {
            "id": "edge-006",
            "source": "lawyer-001",
            "target": "company-002",
            "label": "专项法律顾问",
            "type": "client",
            "value": 0.7
        },
        {
            "id": "edge-007",
            "source": "lawyer-001",
            "target": "lawyer-002",
            "label": "合伙人",
            "type": "colleague",
            "value": 0.9
        },
        {
            "id": "edge-008",
            "source": "lawyer-001",
            "target": "lawyer-003",
            "label": "团队成员",
            "type": "colleague",
            "value": 0.8
        },
        {
            "id": "edge-009",
            "source": "case-001",
            "target": "court-001",
            "label": "审理",
            "type": "jurisdiction",
            "value": 1
        },
        {
            "id": "edge-010",
            "source": "case-002",
            "target": "court-001",
            "label": "审理",
            "type": "jurisdiction",
            "value": 1
        },
        {
            "id": "edge-011",
            "source": "company-001",
            "target": "case-001",
            "label": "当事人",
            "type": "litigation",
            "value": 1
        }
    ]

    stats = {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "node_types": {
            "lawyer": 3,
            "case": 4,
            "company": 2,
            "court": 1
        },
        "total_cases": 4,
        "total_clients": 2,
        "win_rate": "67%"
    }

    return {
        "nodes": nodes,
        "edges": edges,
        "center_node_id": "lawyer-001",
        "stats": stats
    }


# ========== 端点 ==========

@router.get("/health")
async def graph_health():
    """法律关系图谱服务健康检查"""
    return {
        "status": "ok",
        "service": "lexprime-graph",
        "version": "1.0.0",
        "mock_mode": MOCK_MODE,
        "features": [
            "case_graph",
            "company_graph",
            "lawyer_graph"
        ],
        "node_types": ["case", "person", "company", "lawyer", "court", "law"],
        "relation_types": ["litigation", "agency", "citation", "jurisdiction", "shareholder"],
        "endpoints": [
            {"path": "/api/graph/case/{id}", "method": "GET", "purpose": "案件关系图谱"},
            {"path": "/api/graph/company/{id}", "method": "GET", "purpose": "企业关系图谱"},
            {"path": "/api/graph/lawyer/{id}", "method": "GET", "purpose": "律师关系图谱"}
        ]
    }


@router.get("/case/{case_id}", response_model=GraphResponse)
async def get_case_relation_graph(case_id: str):
    """获取案件关系图谱

    包含当事人、律师、法院、引用法规等节点和关系
    """
    t0 = time.time()

    try:
        data = get_case_graph(case_id)

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Graph case request processed in {latency_ms}ms, "
            f"nodes={len(data['nodes'])}, edges={len(data['edges'])}, "
            f"mock_mode={MOCK_MODE}"
        )

        return GraphResponse(
            nodes=[GraphNode(**n) for n in data["nodes"]],
            edges=[GraphEdge(**e) for e in data["edges"]],
            center_node_id=data["center_node_id"],
            stats=data["stats"]
        )
    except Exception as e:
        logger.exception(f"Graph case failed: {e}")
        raise HTTPException(500, f"获取案件关系图谱失败: {str(e)}")


@router.get("/company/{company_id}", response_model=GraphResponse)
async def get_company_relation_graph(company_id: str):
    """获取企业关系图谱

    包含股东、子公司、合作伙伴、涉诉案件等节点和关系
    """
    t0 = time.time()

    try:
        data = get_company_graph(company_id)

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Graph company request processed in {latency_ms}ms, "
            f"nodes={len(data['nodes'])}, edges={len(data['edges'])}, "
            f"mock_mode={MOCK_MODE}"
        )

        return GraphResponse(
            nodes=[GraphNode(**n) for n in data["nodes"]],
            edges=[GraphEdge(**e) for e in data["edges"]],
            center_node_id=data["center_node_id"],
            stats=data["stats"]
        )
    except Exception as e:
        logger.exception(f"Graph company failed: {e}")
        raise HTTPException(500, f"获取企业关系图谱失败: {str(e)}")


@router.get("/lawyer/{lawyer_id}", response_model=GraphResponse)
async def get_lawyer_relation_graph(lawyer_id: str):
    """获取律师关系图谱

    包含代理案件、客户、同事、律所等节点和关系
    """
    t0 = time.time()

    try:
        data = get_lawyer_graph(lawyer_id)

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Graph lawyer request processed in {latency_ms}ms, "
            f"nodes={len(data['nodes'])}, edges={len(data['edges'])}, "
            f"mock_mode={MOCK_MODE}"
        )

        return GraphResponse(
            nodes=[GraphNode(**n) for n in data["nodes"]],
            edges=[GraphEdge(**e) for e in data["edges"]],
            center_node_id=data["center_node_id"],
            stats=data["stats"]
        )
    except Exception as e:
        logger.exception(f"Graph lawyer failed: {e}")
        raise HTTPException(500, f"获取律师关系图谱失败: {str(e)}")
