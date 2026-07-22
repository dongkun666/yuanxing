"""
LexPrime 法律知识图谱 API
============================

提供知识图谱的实体查询、关系探索、路径分析、相似实体发现等接口。

端点:
- GET /api/kg/entity/{id}        - 实体详情
- GET /api/kg/entity/search      - 实体搜索
- GET /api/kg/relation/{id}      - 关系详情
- GET /api/kg/graph              - 子图查询
- GET /api/kg/path               - 路径查询
- GET /api/kg/similar            - 相似实体
- GET /api/kg/stats              - 图谱统计
- GET /api/kg/health             - 健康检查
"""
from __future__ import annotations

import time
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field

from core.knowledge_graph import get_knowledge_graph, EntityType, RelationType


router = APIRouter(prefix="/api/kg", tags=["knowledge-graph"])

kg = get_knowledge_graph()


# ========== Response Models ==========

class KGEntityOut(BaseModel):
    """知识图谱实体输出模型"""
    id: str
    name: str
    type: str
    type_label: str
    sub_type: Optional[str] = None
    description: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    degree: int = 0
    color: str = "#165DFF"

    class Config:
        json_schema_extra = {
            "example": {
                "id": "case-001",
                "name": "张三诉李四借款合同纠纷案",
                "type": "case",
                "type_label": "案件",
                "sub_type": "借款合同纠纷",
                "description": "典型民间借贷纠纷案例",
                "properties": {
                    "case_number": "(2026)京01民初123号",
                    "court": "北京市第一中级人民法院",
                    "amount": "50万元"
                },
                "degree": 8,
                "color": "#165DFF"
            }
        }


class KGRelationOut(BaseModel):
    """知识图谱关系输出模型"""
    id: str
    source_id: str
    target_id: str
    type: str
    type_label: str
    label: str
    weight: float = 1.0
    properties: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "rel-001",
                "source_id": "case-001",
                "target_id": "person-001",
                "type": "plaintiff",
                "type_label": "原告",
                "label": "原告",
                "weight": 1.0,
                "properties": {}
            }
        }


class SubgraphOut(BaseModel):
    """子图输出模型"""
    nodes: List[KGEntityOut]
    edges: List[KGRelationOut]
    stats: Dict[str, Any]


class PathOut(BaseModel):
    """路径输出模型"""
    nodes: List[KGEntityOut]
    relations: List[KGRelationOut]
    length: int


class SimilarEntityOut(BaseModel):
    """相似实体输出模型"""
    entity: KGEntityOut
    similarity: float
    common_neighbors: int


class KGStatsOut(BaseModel):
    """知识图谱统计输出模型"""
    total_entities: int
    total_relations: int
    entity_types: Dict[str, int]
    relation_types: Dict[str, int]
    avg_degree: float
    max_degree: int
    density: float


# ========== 端点 ==========

@router.get("/health", summary="知识图谱服务健康检查")
async def kg_health():
    """知识图谱服务健康检查"""
    stats = kg.get_stats()
    return {
        "status": "ok",
        "service": "lexprime-knowledge-graph",
        "version": "1.0.0",
        "mock_mode": True,
        "entity_types": [e.value for e in EntityType],
        "relation_types": [r.value for r in RelationType],
        "stats": stats,
        "features": [
            "entity_extraction",
            "relation_extraction",
            "subgraph_query",
            "path_analysis",
            "similarity_search",
            "community_detection"
        ],
        "endpoints": [
            {"path": "/api/kg/entity/{id}", "method": "GET", "purpose": "实体详情"},
            {"path": "/api/kg/entity/search", "method": "GET", "purpose": "实体搜索"},
            {"path": "/api/kg/relation/{id}", "method": "GET", "purpose": "关系详情"},
            {"path": "/api/kg/graph", "method": "GET", "purpose": "子图查询"},
            {"path": "/api/kg/path", "method": "GET", "purpose": "路径查询"},
            {"path": "/api/kg/similar", "method": "GET", "purpose": "相似实体"},
            {"path": "/api/kg/stats", "method": "GET", "purpose": "图谱统计"}
        ]
    }


@router.get("/stats", response_model=KGStatsOut, summary="获取知识图谱统计信息")
async def get_kg_stats():
    """获取知识图谱的整体统计信息，包括实体数、关系数、类型分布等"""
    t0 = time.time()
    try:
        stats = kg.get_stats()
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"KG stats request processed in {latency_ms}ms")
        return KGStatsOut(**stats)
    except Exception as e:
        logger.exception(f"KG stats failed: {e}")
        raise HTTPException(500, f"获取图谱统计失败: {str(e)}")


@router.get("/entity/search", response_model=List[KGEntityOut], summary="搜索实体")
async def search_entities(
    q: str = Query(..., min_length=1, max_length=100, description="搜索关键词"),
    entity_type: Optional[str] = Query(None, description="实体类型过滤"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
):
    """根据关键词搜索知识图谱中的实体

    - **q**: 搜索关键词
    - **entity_type**: 可选的实体类型过滤 (person/lawyer/judge/court/law_firm/company/law_article/cause/charge/case/contract/judgment)
    - **limit**: 返回结果数量限制
    """
    t0 = time.time()
    try:
        entities = kg.search_entities(q, entity_type=entity_type, limit=limit)
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"KG entity search request processed in {latency_ms}ms, "
            f"query='{q}', type={entity_type}, results={len(entities)}"
        )
        return [KGEntityOut(**e.to_dict()) for e in entities]
    except Exception as e:
        logger.exception(f"KG entity search failed: {e}")
        raise HTTPException(500, f"实体搜索失败: {str(e)}")


@router.get("/entity/{entity_id}", response_model=KGEntityOut, summary="获取实体详情")
async def get_entity_detail(entity_id: str):
    """根据实体ID获取实体的详细信息

    - **entity_id**: 实体唯一标识
    """
    t0 = time.time()
    try:
        entity = kg.get_entity(entity_id)
        if not entity:
            raise HTTPException(404, f"实体不存在: {entity_id}")

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"KG entity detail request processed in {latency_ms}ms, entity_id={entity_id}")
        return KGEntityOut(**entity.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"KG entity detail failed: {e}")
        raise HTTPException(500, f"获取实体详情失败: {str(e)}")


@router.get("/relation/{relation_id}", response_model=KGRelationOut, summary="获取关系详情")
async def get_relation_detail(relation_id: str):
    """根据关系ID获取关系的详细信息

    - **relation_id**: 关系唯一标识
    """
    t0 = time.time()
    try:
        relation = kg.get_relation(relation_id)
        if not relation:
            raise HTTPException(404, f"关系不存在: {relation_id}")

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"KG relation detail request processed in {latency_ms}ms, relation_id={relation_id}")
        return KGRelationOut(**relation.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"KG relation detail failed: {e}")
        raise HTTPException(500, f"获取关系详情失败: {str(e)}")


@router.get("/graph", response_model=SubgraphOut, summary="子图查询")
async def get_subgraph(
    center_id: str = Query(..., description="中心实体ID"),
    depth: int = Query(2, ge=1, le=4, description="遍历深度"),
    entity_types: Optional[str] = Query(None, description="实体类型过滤，逗号分隔"),
    relation_types: Optional[str] = Query(None, description="关系类型过滤，逗号分隔"),
    max_nodes: int = Query(50, ge=10, le=200, description="最大节点数")
):
    """获取以指定实体为中心的子图

    - **center_id**: 中心实体的ID
    - **depth**: 遍历深度 (1-4)
    - **entity_types**: 实体类型过滤，多个类型用逗号分隔
    - **relation_types**: 关系类型过滤，多个类型用逗号分隔
    - **max_nodes**: 返回的最大节点数量
    """
    t0 = time.time()
    try:
        entity_type_list = entity_types.split(",") if entity_types else None
        relation_type_list = relation_types.split(",") if relation_types else None

        subgraph = kg.get_subgraph(
            center_id=center_id,
            depth=depth,
            entity_types=entity_type_list,
            relation_types=relation_type_list,
            max_nodes=max_nodes
        )

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"KG subgraph request processed in {latency_ms}ms, "
            f"center_id={center_id}, depth={depth}, "
            f"nodes={subgraph['stats']['total_nodes']}, edges={subgraph['stats']['total_edges']}"
        )

        return SubgraphOut(
            nodes=[KGEntityOut(**n) for n in subgraph["nodes"]],
            edges=[KGRelationOut(**e) for e in subgraph["edges"]],
            stats=subgraph["stats"]
        )
    except Exception as e:
        logger.exception(f"KG subgraph failed: {e}")
        raise HTTPException(500, f"子图查询失败: {str(e)}")


@router.get("/path", summary="路径查询")
async def find_path(
    start_id: str = Query(..., description="起始实体ID"),
    end_id: str = Query(..., description="目标实体ID"),
    max_depth: int = Query(4, ge=1, le=6, description="最大路径深度"),
    relation_types: Optional[str] = Query(None, description="关系类型过滤，逗号分隔")
):
    """查找两个实体之间的路径

    - **start_id**: 起始实体ID
    - **end_id**: 目标实体ID
    - **max_depth**: 最大路径深度 (1-6)
    - **relation_types**: 关系类型过滤，多个类型用逗号分隔

    返回从起始实体到目标实体的多条路径，按路径长度排序。
    """
    t0 = time.time()
    try:
        relation_type_list = relation_types.split(",") if relation_types else None

        paths = kg.find_path(
            start_id=start_id,
            end_id=end_id,
            max_depth=max_depth,
            relation_types=relation_type_list
        )

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"KG path request processed in {latency_ms}ms, "
            f"start_id={start_id}, end_id={end_id}, paths={len(paths)}"
        )

        return {
            "start_id": start_id,
            "end_id": end_id,
            "max_depth": max_depth,
            "paths_count": len(paths),
            "paths": paths
        }
    except Exception as e:
        logger.exception(f"KG path failed: {e}")
        raise HTTPException(500, f"路径查询失败: {str(e)}")


@router.get("/similar", summary="相似实体发现")
async def find_similar_entities(
    entity_id: str = Query(..., description="目标实体ID"),
    entity_type: Optional[str] = Query(None, description="相似实体类型过滤"),
    top_k: int = Query(10, ge=1, le=50, description="返回数量")
):
    """发现与指定实体相似的其他实体

    基于共同邻居的 Jaccard 相似度计算。

    - **entity_id**: 目标实体ID
    - **entity_type**: 可选的相似实体类型过滤
    - **top_k**: 返回的相似实体数量
    """
    t0 = time.time()
    try:
        similar = kg.find_similar_entities(
            entity_id=entity_id,
            entity_type=entity_type,
            top_k=top_k
        )

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"KG similar request processed in {latency_ms}ms, "
            f"entity_id={entity_id}, results={len(similar)}"
        )

        return {
            "entity_id": entity_id,
            "similar_count": len(similar),
            "results": similar
        }
    except Exception as e:
        logger.exception(f"KG similar failed: {e}")
        raise HTTPException(500, f"相似实体发现失败: {str(e)}")


@router.get("/entity/{entity_id}/relations", summary="获取实体的关系列表")
async def get_entity_relations(
    entity_id: str,
    relation_type: Optional[str] = Query(None, description="关系类型过滤"),
    direction: str = Query("all", description="方向: outgoing/incoming/all")
):
    """获取指定实体的所有关系

    - **entity_id**: 实体ID
    - **relation_type**: 可选的关系类型过滤
    - **direction**: 关系方向 (outgoing/incoming/all)
    """
    t0 = time.time()
    try:
        entity = kg.get_entity(entity_id)
        if not entity:
            raise HTTPException(404, f"实体不存在: {entity_id}")

        relations = kg.get_entity_relations(
            entity_id=entity_id,
            relation_type=relation_type,
            direction=direction
        )

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"KG entity relations request processed in {latency_ms}ms, "
            f"entity_id={entity_id}, relations={len(relations)}"
        )

        return {
            "entity_id": entity_id,
            "entity_name": entity.name,
            "direction": direction,
            "relation_type": relation_type,
            "total": len(relations),
            "relations": [KGRelationOut(**r.to_dict()) for r in relations]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"KG entity relations failed: {e}")
        raise HTTPException(500, f"获取实体关系失败: {str(e)}")


@router.get("/entity/{entity_id}/neighbors", summary="获取实体的邻居节点")
async def get_entity_neighbors(
    entity_id: str,
    entity_type: Optional[str] = Query(None, description="邻居实体类型过滤"),
    relation_type: Optional[str] = Query(None, description="关系类型过滤")
):
    """获取指定实体的邻居节点

    - **entity_id**: 实体ID
    - **entity_type**: 可选的邻居实体类型过滤
    - **relation_type**: 可选的关系类型过滤
    """
    t0 = time.time()
    try:
        entity = kg.get_entity(entity_id)
        if not entity:
            raise HTTPException(404, f"实体不存在: {entity_id}")

        neighbors = kg.get_neighbors(
            entity_id=entity_id,
            entity_type=entity_type,
            relation_type=relation_type
        )

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"KG entity neighbors request processed in {latency_ms}ms, "
            f"entity_id={entity_id}, neighbors={len(neighbors)}"
        )

        return {
            "entity_id": entity_id,
            "entity_name": entity.name,
            "entity_type": entity_type,
            "relation_type": relation_type,
            "total": len(neighbors),
            "neighbors": [KGEntityOut(**n.to_dict()) for n in neighbors]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"KG entity neighbors failed: {e}")
        raise HTTPException(500, f"获取邻居节点失败: {str(e)}")


@router.get("/communities", summary="社区发现")
async def detect_communities(
    min_size: int = Query(2, ge=2, description="社区最小大小")
):
    """发现知识图谱中的社区结构

    基于连通分量的简单社区发现算法。

    - **min_size**: 社区最小成员数量
    """
    t0 = time.time()
    try:
        communities = kg.detect_communities()
        filtered = [c for c in communities if len(c) >= min_size]

        community_details = []
        for idx, comm in enumerate(filtered[:10]):
            entities = []
            for eid in comm:
                entity = kg.get_entity(eid)
                if entity:
                    entities.append({
                        "id": entity.id,
                        "name": entity.name,
                        "type": entity.type.value
                    })
            community_details.append({
                "community_id": f"comm-{idx+1}",
                "size": len(comm),
                "entities": entities[:20],
                "entity_ids": comm
            })

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"KG communities request processed in {latency_ms}ms, "
            f"communities={len(filtered)}"
        )

        return {
            "total_communities": len(filtered),
            "min_size": min_size,
            "communities": community_details
        }
    except Exception as e:
        logger.exception(f"KG communities failed: {e}")
        raise HTTPException(500, f"社区发现失败: {str(e)}")
