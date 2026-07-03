"""
LexPrime AI 模块
==================

提供法律 AI 能力核心模块，包含：
- 领域预训练框架
- 语料库构建
- 模型评测框架
- RAG 引擎
- Agent 引擎
- 多模态处理

所有模块均支持 Mock 模式，确保在无真实 AI 服务时也能正常运行。
"""

from ai.pretrain import PretrainEngine, PretrainConfig, TrainingStatus
from ai.corpus_builder import CorpusBuilder, CorpusConfig
from ai.evaluation import EvaluationEngine, EvaluationConfig

__all__ = [
    "PretrainEngine",
    "PretrainConfig",
    "TrainingStatus",
    "CorpusBuilder",
    "CorpusConfig",
    "EvaluationEngine",
    "EvaluationConfig",
]
