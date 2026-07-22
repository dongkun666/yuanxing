"""
LexPrime 模型管理 API
======================

提供 AI 模型的列表查询、训练、状态监控、部署等管理功能。

端点:
- GET    /api/models              模型列表
- GET    /api/models/{id}         模型详情
- POST   /api/models/train        发起训练
- GET    /api/models/{id}/status  训练状态
- POST   /api/models/{id}/deploy  部署模型
- GET    /api/models/training/jobs 训练任务列表
- GET    /api/models/health       健康检查
"""
from __future__ import annotations

import time
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field

from ai.pretrain import (
    PretrainEngine,
    PretrainConfig,
    TrainingStatus,
    ModelType,
    get_pretrain_engine,
)
from ai.corpus_builder import CorpusBuilder, get_corpus_builder


router = APIRouter(prefix="/api/models", tags=["model-management"])


# ========== Request / Response Models ==========

class ModelOut(BaseModel):
    """模型输出"""
    version_id: str
    model_name: str
    model_type: str
    version: str
    base_model: str
    created_at: str
    status: str
    metrics: Dict[str, float]
    file_size: int
    deployed: bool
    description: str

    class Config:
        json_schema_extra = {
            "example": {
                "version_id": "mv-001",
                "model_name": "lexprime-embedding-v1",
                "model_type": "embedding",
                "version": "v1.0.0",
                "base_model": "BAAI/bge-small-zh-v1.5",
                "created_at": "2026-06-01T10:00:00",
                "status": "completed",
                "metrics": {
                    "cosine_similarity": 0.87,
                    "retrieval_recall@10": 0.82,
                },
                "file_size": 98765432,
                "deployed": True,
                "description": "LexPrime 基础 Embedding 模型 v1.0",
            }
        }


class TrainRequest(BaseModel):
    """训练请求"""
    model_name: str = Field(..., min_length=1, max_length=100, description="模型名称")
    model_type: str = Field("embedding", description="模型类型: embedding/llm/reranker/classifier")
    base_model: Optional[str] = Field(None, description="基础模型")
    description: Optional[str] = Field("", description="模型描述")
    epochs: int = Field(3, ge=1, le=50, description="训练轮数")
    batch_size: int = Field(8, ge=1, le=128, description="批次大小")
    learning_rate: float = Field(2e-5, ge=1e-7, le=1e-2, description="学习率")
    use_lora: bool = Field(True, description="是否使用 LoRA")
    corpus_ids: Optional[List[str]] = Field(None, description="使用的语料库 ID 列表")
    tags: Optional[List[str]] = Field(None, description="标签列表")

    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "lexprime-embedding-v2",
                "model_type": "embedding",
                "base_model": "BAAI/bge-small-zh-v1.5",
                "description": "增强版 Embedding 模型",
                "epochs": 3,
                "batch_size": 8,
                "learning_rate": 2e-5,
                "use_lora": True,
                "corpus_ids": ["ds-001", "ds-002"],
                "tags": ["embedding", "v2"],
            }
        }


class TrainResponse(BaseModel):
    """训练响应"""
    job_id: str
    status: str
    model_name: str
    created_at: str
    estimated_duration: str


class TrainingStatusOut(BaseModel):
    """训练状态输出"""
    job_id: str
    status: str
    current_epoch: int
    total_epochs: int
    current_step: int
    total_steps: int
    loss: float
    val_loss: float
    accuracy: float
    started_at: Optional[str]
    updated_at: Optional[str]
    estimated_completion: Optional[str]
    progress_percent: float
    error_message: Optional[str]


class DeployRequest(BaseModel):
    """部署请求"""
    version_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "version_id": "mv-002",
            }
        }


class DeployResponse(BaseModel):
    """部署响应"""
    version_id: str
    deployed: bool
    message: str


class TrainingJobListItem(BaseModel):
    """训练任务列表项"""
    job_id: str
    status: str
    model_name: str
    model_type: str
    started_at: Optional[str]
    updated_at: Optional[str]
    current_epoch: int
    total_epochs: int
    progress_percent: float


# ========== Helper Functions ==========

def _model_to_out(model) -> ModelOut:
    """将 ModelVersion 转换为输出模型"""
    return ModelOut(
        version_id=model.version_id,
        model_name=model.model_name,
        model_type=model.model_type.value if hasattr(model.model_type, 'value') else str(model.model_type),
        version=model.version,
        base_model=model.base_model,
        created_at=model.created_at,
        status=model.status,
        metrics=model.metrics,
        file_size=model.file_size,
        deployed=model.deployed,
        description=model.description,
    )


def _progress_to_status_out(progress) -> TrainingStatusOut:
    """将 TrainingProgress 转换为状态输出"""
    progress_percent = 0.0
    if progress.total_steps > 0:
        progress_percent = round((progress.current_step / progress.total_steps) * 100, 2)

    return TrainingStatusOut(
        job_id=progress.job_id,
        status=progress.status.value if hasattr(progress.status, 'value') else str(progress.status),
        current_epoch=progress.current_epoch,
        total_epochs=progress.total_epochs,
        current_step=progress.current_step,
        total_steps=progress.total_steps,
        loss=progress.loss,
        val_loss=progress.val_loss,
        accuracy=progress.accuracy,
        started_at=progress.started_at,
        updated_at=progress.updated_at,
        estimated_completion=progress.estimated_completion,
        progress_percent=progress_percent,
        error_message=progress.error_message,
    )


# ========== Endpoints ==========

@router.get("", response_model=Dict[str, Any])
async def list_models(
    model_type: Optional[str] = Query(None, description="模型类型筛选"),
    only_deployed: bool = Query(False, description="仅显示已部署模型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取模型列表"""
    t0 = time.time()

    try:
        engine = get_pretrain_engine()

        mt = None
        if model_type:
            try:
                mt = ModelType(model_type)
            except ValueError:
                pass

        all_models = engine.list_models(model_type=mt, only_deployed=only_deployed)

        total = len(all_models)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = all_models[start:end]

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"List models: {len(paginated)} items, {latency_ms}ms")

        return {
            "items": [_model_to_out(m) for m in paginated],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
    except Exception as e:
        logger.exception(f"List models failed: {e}")
        raise HTTPException(500, f"获取模型列表失败: {str(e)}")


@router.get("/{version_id}", response_model=ModelOut)
async def get_model_detail(version_id: str):
    """获取模型详情"""
    t0 = time.time()

    try:
        engine = get_pretrain_engine()
        model = engine.get_model(version_id)

        if not model:
            raise HTTPException(404, f"模型不存在: {version_id}")

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"Get model detail: {version_id}, {latency_ms}ms")

        return _model_to_out(model)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Get model detail failed: {e}")
        raise HTTPException(500, f"获取模型详情失败: {str(e)}")


@router.post("/train", response_model=TrainResponse)
async def train_model(req: TrainRequest):
    """发起模型训练"""
    t0 = time.time()

    try:
        engine = get_pretrain_engine()

        model_type = ModelType.EMBEDDING
        if req.model_type:
            try:
                model_type = ModelType(req.model_type)
            except ValueError:
                raise HTTPException(400, f"不支持的模型类型: {req.model_type}")

        config = PretrainConfig(
            model_name=req.model_name,
            model_type=model_type,
            base_model=req.base_model or "BAAI/bge-small-zh-v1.5",
            epochs=req.epochs,
            batch_size=req.batch_size,
            learning_rate=req.learning_rate,
            use_lora=req.use_lora,
            description=req.description or "",
            tags=req.tags or [],
        )

        progress = engine.create_training_job(config, corpus_ids=req.corpus_ids)

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Train model created: {progress.job_id}, "
            f"model={req.model_name}, {latency_ms}ms"
        )

        estimated_minutes = req.epochs * 30
        if estimated_minutes >= 60:
            estimated_duration = f"约 {estimated_minutes // 60} 小时 {estimated_minutes % 60} 分钟"
        else:
            estimated_duration = f"约 {estimated_minutes} 分钟"

        return TrainResponse(
            job_id=progress.job_id,
            status=progress.status.value if hasattr(progress.status, 'value') else str(progress.status),
            model_name=req.model_name,
            created_at=progress.updated_at or "",
            estimated_duration=estimated_duration,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Train model failed: {e}")
        raise HTTPException(500, f"发起训练失败: {str(e)}")


@router.get("/{job_id}/status", response_model=TrainingStatusOut)
async def get_training_status(job_id: str):
    """获取训练状态"""
    t0 = time.time()

    try:
        engine = get_pretrain_engine()
        progress = engine.get_training_status(job_id)

        if not progress:
            raise HTTPException(404, f"训练任务不存在: {job_id}")

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"Get training status: {job_id}, {latency_ms}ms")

        return _progress_to_status_out(progress)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Get training status failed: {e}")
        raise HTTPException(500, f"获取训练状态失败: {str(e)}")


@router.post("/{version_id}/deploy", response_model=DeployResponse)
async def deploy_model(version_id: str):
    """部署模型"""
    t0 = time.time()

    try:
        engine = get_pretrain_engine()
        model = engine.get_model(version_id)

        if not model:
            raise HTTPException(404, f"模型不存在: {version_id}")

        success = engine.deploy_model(version_id)

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"Deploy model: {version_id}, success={success}, {latency_ms}ms")

        if success:
            return DeployResponse(
                version_id=version_id,
                deployed=True,
                message="模型部署成功",
            )
        else:
            raise HTTPException(500, "模型部署失败")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Deploy model failed: {e}")
        raise HTTPException(500, f"部署模型失败: {str(e)}")


@router.get("/training/jobs", response_model=Dict[str, Any])
async def list_training_jobs(
    status: Optional[str] = Query(None, description="状态筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
):
    """获取训练任务列表"""
    t0 = time.time()

    try:
        engine = get_pretrain_engine()

        s = None
        if status:
            try:
                s = TrainingStatus(status)
            except ValueError:
                pass

        jobs = engine.list_training_jobs(status=s, limit=limit)

        result = []
        for job in jobs:
            progress_percent = 0.0
            if job.total_steps > 0:
                progress_percent = round((job.current_step / job.total_steps) * 100, 2)

            result.append(TrainingJobListItem(
                job_id=job.job_id,
                status=job.status.value if hasattr(job.status, 'value') else str(job.status),
                model_name="",
                model_type="",
                started_at=job.started_at,
                updated_at=job.updated_at,
                current_epoch=job.current_epoch,
                total_epochs=job.total_epochs,
                progress_percent=progress_percent,
            ))

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"List training jobs: {len(result)} items, {latency_ms}ms")

        return {
            "items": result,
            "total": len(result),
        }
    except Exception as e:
        logger.exception(f"List training jobs failed: {e}")
        raise HTTPException(500, f"获取训练任务列表失败: {str(e)}")


@router.get("/health")
async def model_health():
    """模型管理健康检查"""
    engine = get_pretrain_engine()
    models = engine.list_models()
    deployed = [m for m in models if m.deployed]

    return {
        "status": "ok",
        "service": "model-management",
        "version": "1.0.0",
        "mock_mode": engine.mock_mode,
        "stats": {
            "total_models": len(models),
            "deployed_models": len(deployed),
            "model_types": list(set(
                m.model_type.value if hasattr(m.model_type, 'value') else str(m.model_type)
                for m in models
            )),
        },
        "endpoints": [
            {"path": "/api/models", "method": "GET", "purpose": "模型列表"},
            {"path": "/api/models/{id}", "method": "GET", "purpose": "模型详情"},
            {"path": "/api/models/train", "method": "POST", "purpose": "发起训练"},
            {"path": "/api/models/{id}/status", "method": "GET", "purpose": "训练状态"},
            {"path": "/api/models/{id}/deploy", "method": "POST", "purpose": "部署模型"},
        ],
    }
