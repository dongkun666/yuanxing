"""
LexPrime A/B 测试管理 API 路由
提供实验的创建、管理、启动停止和报告生成接口

端点:
- GET /api/ab/experiments - 实验列表
- POST /api/ab/experiments - 创建实验
- GET /api/ab/experiments/{id} - 实验详情
- POST /api/ab/experiments/{id}/start - 启动实验
- POST /api/ab/experiments/{id}/stop - 停止实验
- GET /api/ab/experiments/{id}/report - 实验报告
- POST /api/ab/experiments/{id}/metrics - 记录指标
- GET /api/ab/health - 健康检查
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field

from core.ab_testing import (
    ABTestingEngine,
    Experiment,
    ExperimentStatus,
    ExperimentVariant,
    ExperimentMetric,
    VariantType,
    MetricType,
    ExperimentReport
)

router = APIRouter(prefix="/api/ab", tags=["ab-testing"])


# ============================================================================
# Pydantic 请求模型
# ============================================================================

class CreateExperimentRequest(BaseModel):
    """创建实验请求"""
    name: str = Field(..., description="实验名称")
    description: Optional[str] = Field(None, description="实验描述")
    hypothesis: Optional[str] = Field(None, description="实验假设")
    variants: List[Dict[str, Any]] = Field(default_factory=list, description="变体列表")
    metrics: List[Dict[str, Any]] = Field(default_factory=list, description="指标列表")
    target_users: Optional[str] = Field(None, description="目标用户群")
    sample_size: int = Field(1000, ge=10, description="预估样本量")
    min_effect_size: float = Field(0.05, gt=0, description="最小可检测效应量")
    confidence_level: float = Field(0.95, gt=0, lt=1, description="置信水平")


class RecordMetricRequest(BaseModel):
    """记录指标请求"""
    user_id: str = Field(..., description="用户ID")
    metric_name: str = Field(..., description="指标名称")
    value: float = Field(1.0, description="指标值")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


# ============================================================================
# 端点
# ============================================================================

@router.get("/health", summary="健康检查", description="检查A/B测试服务状态")
async def health():
    return {
        "status": "ok",
        "service": "ab-testing",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/experiments", summary="实验列表", description="获取A/B实验列表，支持按状态筛选")
async def list_experiments(
    status: Optional[str] = Query(None, description="实验状态筛选"),
    limit: int = Query(100, ge=1, le=500, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    try:
        status_enum = None
        if status:
            try:
                status_enum = ExperimentStatus(status)
            except ValueError:
                raise HTTPException(400, f"无效的实验状态: {status}")

        experiments, total = ABTestingEngine.list_experiments(
            status=status_enum,
            limit=limit,
            offset=offset
        )

        return {
            "items": [e.dict() for e in experiments],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"获取实验列表失败: {e}")
        raise HTTPException(500, f"获取实验列表失败: {e}")


@router.post("/experiments", response_model=Experiment, summary="创建实验", description="创建新的A/B实验")
async def create_experiment(req: CreateExperimentRequest):
    try:
        experiment_id = f"exp_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        variants = []
        for i, v in enumerate(req.variants):
            vtype = VariantType(v.get("type", "treatment"))
            variants.append(ExperimentVariant(
                id=v.get("id", f"variant_{i}"),
                name=v.get("name", f"变体{i + 1}"),
                type=vtype,
                traffic_percentage=float(v.get("traffic_percentage", 50)),
                description=v.get("description"),
                config=v.get("config", {})
            ))

        metrics = []
        for i, m in enumerate(req.metrics):
            mtype = MetricType(m.get("type", "binary"))
            metrics.append(ExperimentMetric(
                name=m.get("name", f"metric_{i}"),
                type=mtype,
                description=m.get("description"),
                is_primary=m.get("is_primary", False),
                unit=m.get("unit")
            ))

        experiment = Experiment(
            id=experiment_id,
            name=req.name,
            description=req.description,
            hypothesis=req.hypothesis,
            status=ExperimentStatus.DRAFT,
            variants=variants,
            metrics=metrics,
            target_users=req.target_users,
            sample_size=req.sample_size,
            min_effect_size=req.min_effect_size,
            confidence_level=req.confidence_level
        )

        result = ABTestingEngine.create_experiment(experiment)
        return result

    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"创建实验失败: {e}")
        raise HTTPException(500, f"创建实验失败: {e}")


@router.get("/experiments/{experiment_id}", response_model=Experiment, summary="实验详情",
            description="获取指定实验的详细信息")
async def get_experiment(experiment_id: str):
    try:
        experiment = ABTestingEngine.get_experiment(experiment_id)
        if not experiment:
            raise HTTPException(404, f"实验不存在: {experiment_id}")
        return experiment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实验详情失败: {e}")
        raise HTTPException(500, f"获取实验详情失败: {e}")


@router.post("/experiments/{experiment_id}/start", response_model=Experiment,
             summary="启动实验", description="启动指定的A/B实验")
async def start_experiment(experiment_id: str):
    try:
        experiment = ABTestingEngine.start_experiment(experiment_id)
        logger.info(f"实验已启动: {experiment_id}")
        return experiment
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"启动实验失败: {e}")
        raise HTTPException(500, f"启动实验失败: {e}")


@router.post("/experiments/{experiment_id}/stop", response_model=Experiment,
             summary="停止实验", description="停止指定的A/B实验")
async def stop_experiment(experiment_id: str):
    try:
        experiment = ABTestingEngine.stop_experiment(experiment_id)
        logger.info(f"实验已停止: {experiment_id}")
        return experiment
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"停止实验失败: {e}")
        raise HTTPException(500, f"停止实验失败: {e}")


@router.get("/experiments/{experiment_id}/report", response_model=ExperimentReport,
            summary="实验报告", description="生成并返回实验的统计分析报告")
async def get_experiment_report(experiment_id: str):
    try:
        experiment = ABTestingEngine.get_experiment(experiment_id)
        if not experiment:
            raise HTTPException(404, f"实验不存在: {experiment_id}")

        report = ABTestingEngine.generate_report(experiment_id)
        return report

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"生成实验报告失败: {e}")
        raise HTTPException(500, f"生成实验报告失败: {e}")


@router.post("/experiments/{experiment_id}/metrics", summary="记录指标",
             description="记录实验的指标数据点")
async def record_metric(experiment_id: str, req: RecordMetricRequest):
    try:
        experiment = ABTestingEngine.get_experiment(experiment_id)
        if not experiment:
            raise HTTPException(404, f"实验不存在: {experiment_id}")

        success = ABTestingEngine.record_metric(
            experiment_id=experiment_id,
            user_id=req.user_id,
            metric_name=req.metric_name,
            value=req.value,
            metadata=req.metadata
        )

        if not success:
            return {
                "success": False,
                "message": "指标记录失败（实验未运行或指标不存在）"
            }

        return {
            "success": True,
            "message": "指标记录成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"记录指标失败: {e}")
        raise HTTPException(500, f"记录指标失败: {e}")


@router.get("/experiments/{experiment_id}/variant", summary="获取用户变体",
            description="获取指定用户在实验中的变体分配")
async def get_user_variant(
    experiment_id: str,
    user_id: str = Query(..., description="用户ID")
):
    try:
        experiment = ABTestingEngine.get_experiment(experiment_id)
        if not experiment:
            raise HTTPException(404, f"实验不存在: {experiment_id}")

        variant_id = ABTestingEngine.get_user_variant(experiment_id, user_id)

        variant = None
        if variant_id:
            variant = next((v for v in experiment.variants if v.id == variant_id), None)

        return {
            "experiment_id": experiment_id,
            "user_id": user_id,
            "variant_id": variant_id,
            "variant": variant.dict() if variant else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户变体失败: {e}")
        raise HTTPException(500, f"获取用户变体失败: {e}")


@router.get("/experiments/{experiment_id}/stats", summary="实验统计",
            description="获取实验的实时统计数据")
async def get_experiment_stats(experiment_id: str):
    try:
        experiment = ABTestingEngine.get_experiment(experiment_id)
        if not experiment:
            raise HTTPException(404, f"实验不存在: {experiment_id}")

        variant_stats = ABTestingEngine.calculate_variant_stats(experiment_id)

        total_users = sum(s.user_count for s in variant_stats)

        return {
            "experiment_id": experiment_id,
            "experiment_name": experiment.name,
            "status": experiment.status.value,
            "total_users": total_users,
            "variant_stats": [s.dict() for s in variant_stats]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实验统计失败: {e}")
        raise HTTPException(500, f"获取实验统计失败: {e}")


@router.delete("/experiments/{experiment_id}", summary="删除实验", description="删除指定的A/B实验")
async def delete_experiment(experiment_id: str):
    try:
        success = ABTestingEngine.delete_experiment(experiment_id)
        if not success:
            raise HTTPException(404, f"实验不存在: {experiment_id}")

        return {
            "success": True,
            "message": "实验已删除"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除实验失败: {e}")
        raise HTTPException(500, f"删除实验失败: {e}")
