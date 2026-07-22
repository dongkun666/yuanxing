"""
LexPrime 法律领域预训练框架
============================

提供法律文本语料处理、模型微调配置、训练流程管理和模型版本管理。

支持 Mock 模式：当真实训练环境不可用时，返回模拟训练进度和结果。
"""
from __future__ import annotations

import time
import uuid
import asyncio
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field

from loguru import logger


class TrainingStatus(str, Enum):
    """训练状态枚举"""
    PENDING = "pending"
    QUEUED = "queued"
    TRAINING = "training"
    EVALUATING = "evaluating"
    SAVING = "saving"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModelType(str, Enum):
    """模型类型枚举"""
    EMBEDDING = "embedding"
    LLM = "llm"
    RERANKER = "reranker"
    CLASSIFIER = "classifier"


@dataclass
class PretrainConfig:
    """预训练配置"""
    model_name: str = "BAAI/bge-small-zh-v1.5"
    model_type: ModelType = ModelType.EMBEDDING
    base_model: str = "BAAI/bge-small-zh-v1.5"
    output_dir: str = "./models"
    epochs: int = 3
    batch_size: int = 8
    learning_rate: float = 2e-5
    warmup_steps: int = 100
    max_seq_length: int = 512
    use_quantization: bool = False
    use_lora: bool = True
    lora_r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    train_size: float = 0.9
    val_size: float = 0.1
    seed: int = 42
    fp16: bool = True
    gradient_accumulation_steps: int = 2
    logging_steps: int = 10
    save_steps: int = 100
    eval_steps: int = 100
    early_stopping_patience: int = 3
    task_type: str = "legal_embedding"
    domain: str = "general_law"
    description: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class ModelVersion:
    """模型版本信息"""
    version_id: str
    model_name: str
    model_type: ModelType
    version: str
    base_model: str
    created_at: str
    status: str
    metrics: Dict[str, float] = field(default_factory=dict)
    training_config: Dict[str, Any] = field(default_factory=dict)
    corpus_info: Dict[str, Any] = field(default_factory=dict)
    file_size: int = 0
    deployed: bool = False
    description: str = ""


@dataclass
class TrainingProgress:
    """训练进度信息"""
    job_id: str
    status: TrainingStatus
    current_epoch: int = 0
    total_epochs: int = 0
    current_step: int = 0
    total_steps: int = 0
    loss: float = 0.0
    val_loss: float = 0.0
    accuracy: float = 0.0
    started_at: Optional[str] = None
    updated_at: Optional[str] = None
    estimated_completion: Optional[str] = None
    error_message: Optional[str] = None


class PretrainEngine:
    """法律领域预训练引擎

    提供模型微调训练的完整流程管理，包括：
    - 训练任务创建和调度
    - 训练进度跟踪
    - 模型版本管理
    - 模型部署管理
    """

    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        self._training_jobs: Dict[str, TrainingProgress] = {}
        self._model_versions: Dict[str, ModelVersion] = {}
        self._deployed_models: Dict[str, str] = {}
        self._init_mock_data()

    def _init_mock_data(self):
        """初始化 Mock 数据"""
        now = datetime.now().isoformat()

        self._model_versions = {
            "mv-001": ModelVersion(
                version_id="mv-001",
                model_name="lexprime-embedding-v1",
                model_type=ModelType.EMBEDDING,
                version="v1.0.0",
                base_model="BAAI/bge-small-zh-v1.5",
                created_at="2026-06-01T10:00:00",
                status="completed",
                metrics={
                    "cosine_similarity": 0.87,
                    "retrieval_recall@10": 0.82,
                    "ndcg@10": 0.78,
                    "accuracy": 0.89,
                },
                training_config={
                    "epochs": 3,
                    "batch_size": 8,
                    "learning_rate": 2e-5,
                },
                corpus_info={
                    "total_docs": 50000,
                    "legal_cases": 30000,
                    "regulations": 15000,
                    "contracts": 5000,
                },
                file_size=98765432,
                deployed=True,
                description="LexPrime 基础 Embedding 模型 v1.0",
            ),
            "mv-002": ModelVersion(
                version_id="mv-002",
                model_name="lexprime-embedding-v1.1",
                model_type=ModelType.EMBEDDING,
                version="v1.1.0",
                base_model="BAAI/bge-small-zh-v1.5",
                created_at="2026-06-15T14:30:00",
                status="completed",
                metrics={
                    "cosine_similarity": 0.89,
                    "retrieval_recall@10": 0.85,
                    "ndcg@10": 0.81,
                    "accuracy": 0.91,
                },
                training_config={
                    "epochs": 4,
                    "batch_size": 16,
                    "learning_rate": 1e-5,
                },
                corpus_info={
                    "total_docs": 80000,
                    "legal_cases": 50000,
                    "regulations": 20000,
                    "contracts": 10000,
                },
                file_size=102345678,
                deployed=False,
                description="LexPrime Embedding 模型 v1.1，增强合同领域理解",
            ),
            "mv-003": ModelVersion(
                version_id="mv-003",
                model_name="lexprime-reranker-v1",
                model_type=ModelType.RERANKER,
                version="v1.0.0",
                base_model="BAAI/bge-reranker-base",
                created_at="2026-06-20T09:00:00",
                status="completed",
                metrics={
                    "map@10": 0.83,
                    "ndcg@10": 0.86,
                    "mrr": 0.88,
                },
                training_config={
                    "epochs": 2,
                    "batch_size": 4,
                    "learning_rate": 3e-6,
                },
                corpus_info={
                    "total_pairs": 100000,
                    "positive_pairs": 50000,
                    "negative_pairs": 50000,
                },
                file_size=456789012,
                deployed=True,
                description="LexPrime 重排序模型 v1.0",
            ),
        }

        self._deployed_models = {
            "embedding": "mv-001",
            "reranker": "mv-003",
        }

    def list_models(self, model_type: Optional[ModelType] = None,
                    only_deployed: bool = False) -> List[ModelVersion]:
        """获取模型列表

        Args:
            model_type: 按模型类型筛选
            only_deployed: 仅返回已部署模型

        Returns:
            模型版本列表
        """
        models = list(self._model_versions.values())

        if model_type:
            models = [m for m in models if m.model_type == model_type]

        if only_deployed:
            models = [m for m in models if m.deployed]

        models.sort(key=lambda x: x.created_at, reverse=True)
        return models

    def get_model(self, version_id: str) -> Optional[ModelVersion]:
        """获取模型详情

        Args:
            version_id: 模型版本 ID

        Returns:
            模型版本信息，不存在则返回 None
        """
        return self._model_versions.get(version_id)

    def create_training_job(self, config: PretrainConfig,
                            corpus_ids: Optional[List[str]] = None) -> TrainingProgress:
        """创建训练任务

        Args:
            config: 预训练配置
            corpus_ids: 使用的语料库 ID 列表

        Returns:
            训练进度信息
        """
        job_id = f"job-{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()

        total_steps = config.epochs * 1000

        progress = TrainingProgress(
            job_id=job_id,
            status=TrainingStatus.QUEUED,
            current_epoch=0,
            total_epochs=config.epochs,
            current_step=0,
            total_steps=total_steps,
            loss=0.0,
            val_loss=0.0,
            accuracy=0.0,
            started_at=None,
            updated_at=now,
            estimated_completion=None,
            error_message=None,
        )

        self._training_jobs[job_id] = progress

        logger.info(f"Training job created: {job_id}, model={config.model_name}")

        if self.mock_mode:
            asyncio.create_task(self._simulate_training(job_id, config))

        return progress

    async def _simulate_training(self, job_id: str, config: PretrainConfig):
        """模拟训练过程（Mock 模式）"""
        await asyncio.sleep(1)

        if job_id not in self._training_jobs:
            return

        progress = self._training_jobs[job_id]
        progress.status = TrainingStatus.TRAINING
        progress.started_at = datetime.now().isoformat()

        total_steps = config.epochs * 1000

        for epoch in range(1, config.epochs + 1):
            for step in range(1, 1001):
                if job_id not in self._training_jobs:
                    return
                if self._training_jobs[job_id].status == TrainingStatus.CANCELLED:
                    return

                await asyncio.sleep(0.01)

                current_step = (epoch - 1) * 1000 + step
                progress.current_epoch = epoch
                progress.current_step = current_step
                progress.loss = max(0.1, 2.0 - (current_step / total_steps) * 1.8)
                progress.val_loss = max(0.15, 2.2 - (current_step / total_steps) * 1.9)
                progress.accuracy = min(0.95, 0.5 + (current_step / total_steps) * 0.45)
                progress.updated_at = datetime.now().isoformat()

        progress.status = TrainingStatus.EVALUATING
        await asyncio.sleep(0.5)

        progress.status = TrainingStatus.SAVING
        await asyncio.sleep(0.3)

        version_id = f"mv-{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        model_version = ModelVersion(
            version_id=version_id,
            model_name=config.model_name,
            model_type=config.model_type,
            version=f"v{len(self._model_versions) + 1}.0.0",
            base_model=config.base_model,
            created_at=now,
            status="completed",
            metrics={
                "cosine_similarity": 0.85 + 0.1 * (hash(job_id) % 10) / 10,
                "retrieval_recall@10": 0.80 + 0.1 * (hash(job_id) % 10) / 10,
                "ndcg@10": 0.75 + 0.1 * (hash(job_id) % 10) / 10,
                "accuracy": 0.85 + 0.1 * (hash(job_id) % 10) / 10,
            },
            training_config={
                "epochs": config.epochs,
                "batch_size": config.batch_size,
                "learning_rate": config.learning_rate,
                "use_lora": config.use_lora,
            },
            corpus_info={
                "corpus_ids": corpus_ids or [],
                "total_docs": 50000 + (hash(job_id) % 50000),
            },
            file_size=90000000 + (hash(job_id) % 50000000),
            deployed=False,
            description=config.description or f"训练任务 {job_id} 产出模型",
        )

        self._model_versions[version_id] = model_version

        progress.status = TrainingStatus.COMPLETED
        progress.updated_at = now

        logger.info(f"Training job completed: {job_id}, version={version_id}")

    def get_training_status(self, job_id: str) -> Optional[TrainingProgress]:
        """获取训练状态

        Args:
            job_id: 训练任务 ID

        Returns:
            训练进度信息，不存在则返回 None
        """
        return self._training_jobs.get(job_id)

    def list_training_jobs(self, status: Optional[TrainingStatus] = None,
                           limit: int = 20) -> List[TrainingProgress]:
        """获取训练任务列表

        Args:
            status: 按状态筛选
            limit: 返回数量限制

        Returns:
            训练任务列表
        """
        jobs = list(self._training_jobs.values())

        if status:
            jobs = [j for j in jobs if j.status == status]

        jobs.sort(key=lambda x: x.updated_at or "", reverse=True)
        return jobs[:limit]

    def cancel_training(self, job_id: str) -> bool:
        """取消训练任务

        Args:
            job_id: 训练任务 ID

        Returns:
            是否成功取消
        """
        if job_id not in self._training_jobs:
            return False

        job = self._training_jobs[job_id]
        if job.status in (TrainingStatus.COMPLETED, TrainingStatus.FAILED, TrainingStatus.CANCELLED):
            return False

        job.status = TrainingStatus.CANCELLED
        job.updated_at = datetime.now().isoformat()
        logger.info(f"Training job cancelled: {job_id}")
        return True

    def deploy_model(self, version_id: str) -> bool:
        """部署模型

        Args:
            version_id: 模型版本 ID

        Returns:
            是否成功部署
        """
        model = self._model_versions.get(version_id)
        if not model:
            return False

        model.deployed = True
        self._deployed_models[model.model_type.value] = version_id

        logger.info(f"Model deployed: {version_id}, type={model.model_type}")
        return True

    def undeploy_model(self, version_id: str) -> bool:
        """下架模型

        Args:
            version_id: 模型版本 ID

        Returns:
            是否成功下架
        """
        model = self._model_versions.get(version_id)
        if not model:
            return False

        model.deployed = False

        model_type_key = model.model_type.value
        if self._deployed_models.get(model_type_key) == version_id:
            del self._deployed_models[model_type_key]

        logger.info(f"Model undeployed: {version_id}")
        return True

    def get_deployed_model(self, model_type: ModelType) -> Optional[ModelVersion]:
        """获取已部署的指定类型模型

        Args:
            model_type: 模型类型

        Returns:
            已部署的模型版本，不存在则返回 None
        """
        version_id = self._deployed_models.get(model_type.value)
        if not version_id:
            return None
        return self._model_versions.get(version_id)

    def process_legal_corpus(self, texts: List[str],
                             task_type: str = "embedding") -> Dict[str, Any]:
        """处理法律文本语料（预处理）

        Args:
            texts: 原始文本列表
            task_type: 任务类型 (embedding/reranker/classification)

        Returns:
            处理结果统计
        """
        if not texts:
            return {"total": 0, "valid": 0, "skipped": 0}

        valid_texts = []
        skipped = 0

        for text in texts:
            if not text or len(text.strip()) < 10:
                skipped += 1
                continue
            cleaned = self._clean_legal_text(text)
            if len(cleaned) >= 10:
                valid_texts.append(cleaned)
            else:
                skipped += 1

        return {
            "total": len(texts),
            "valid": len(valid_texts),
            "skipped": skipped,
            "avg_length": sum(len(t) for t in valid_texts) / len(valid_texts) if valid_texts else 0,
            "task_type": task_type,
        }

    def _clean_legal_text(self, text: str) -> str:
        """清洗法律文本"""
        import re

        cleaned = text.strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', cleaned)
        return cleaned


_engine_instance: Optional[PretrainEngine] = None


def get_pretrain_engine() -> PretrainEngine:
    """获取预训练引擎单例"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = PretrainEngine(mock_mode=True)
    return _engine_instance
