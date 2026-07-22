"""
LexPrime 模型评测框架
======================

提供法律任务基准评测、评测数据集管理、多模型对比评测和评测报告生成。

支持 Mock 模式：当真实评测不可用时，返回模拟评测数据。
"""
from __future__ import annotations

import time
import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from loguru import logger


class EvaluationTaskType(str, Enum):
    """评测任务类型"""
    CASE_RETRIEVAL = "case_retrieval"
    LAW_REFERENCE = "law_reference"
    CONTRACT_REVIEW = "contract_review"
    QA = "qa"
    SUMMARIZATION = "summarization"
    EMBEDDING = "embedding"


class EvaluationStatus(str, Enum):
    """评测状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EvaluationDatasetType(str, Enum):
    """评测数据集类型"""
    STANDARD = "standard"
    CUSTOM = "custom"
    SYNTHETIC = "synthetic"


@dataclass
class EvaluationConfig:
    """评测配置"""
    task_type: EvaluationTaskType
    model_ids: List[str]
    dataset_id: str
    metrics: List[str] = field(default_factory=list)
    top_k: int = 10
    max_samples: int = 100
    seed: int = 42
    enable_ablation: bool = False
    ablation_vars: List[str] = field(default_factory=list)


@dataclass
class EvaluationMetrics:
    """评测指标"""
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    accuracy: float = 0.0
    mrr: float = 0.0
    ndcg: float = 0.0
    map_score: float = 0.0
    bleu: float = 0.0
    rouge_l: float = 0.0
    bert_score: float = 0.0
    latency_ms_avg: float = 0.0
    latency_ms_p95: float = 0.0
    tokens_per_second: float = 0.0
    custom_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class EvaluationDataset:
    """评测数据集"""
    dataset_id: str
    name: str
    description: str
    dataset_type: str
    task_type: str
    sample_count: int
    categories: Dict[str, int] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    status: str = "ready"
    source: str = ""


@dataclass
class EvaluationTestItem:
    """评测用例"""
    item_id: str
    query: str
    expected: Dict[str, Any]
    category: str
    difficulty: str = "medium"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationTask:
    """评测任务"""
    task_id: str
    name: str
    description: str
    task_type: str
    model_ids: List[str]
    dataset_id: str
    status: str
    progress: float = 0.0
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    created_at: str = ""
    total_samples: int = 0
    processed_samples: int = 0


@dataclass
class EvaluationResult:
    """评测结果"""
    result_id: str
    task_id: str
    model_id: str
    model_name: str
    metrics: EvaluationMetrics
    category_metrics: Dict[str, EvaluationMetrics] = field(default_factory=dict)
    error_cases: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = ""


@dataclass
class EvaluationReport:
    """评测报告"""
    report_id: str
    task_id: str
    task_name: str
    summary: str
    overall_winner: str
    model_comparison: List[Dict[str, Any]]
    error_analysis: str
    improvement_suggestions: List[str]
    created_at: str = ""


class EvaluationEngine:
    """评测引擎

    提供完整的模型评测能力：
    - 法律任务基准评测（案例检索、法规引用、合同审查、问答）
    - 评测数据集管理
    - 多模型对比评测
    - 版本对比评测
    - 消融实验
    - 详细评测报告生成
    """

    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        self._datasets: Dict[str, EvaluationDataset] = {}
        self._tasks: Dict[str, EvaluationTask] = {}
        self._results: Dict[str, List[EvaluationResult]] = {}
        self._reports: Dict[str, EvaluationReport] = {}
        self._benchmarks: Dict[str, Dict[str, Any]] = {}
        self._init_mock_data()

    def _init_mock_data(self):
        """初始化 Mock 数据"""
        now = datetime.now().isoformat()

        self._datasets = {
            "ds-bench-001": EvaluationDataset(
                dataset_id="ds-bench-001",
                name="LexBench 案例检索基准 v1.0",
                description="法律案例检索标准评测数据集，包含 1000 个查询和相关案例标注",
                dataset_type=EvaluationDatasetType.STANDARD.value,
                task_type=EvaluationTaskType.CASE_RETRIEVAL.value,
                sample_count=1000,
                categories={
                    "合同纠纷": 300,
                    "婚姻家庭": 200,
                    "劳动争议": 200,
                    "知识产权": 150,
                    "刑事辩护": 150,
                },
                created_at="2026-05-01T10:00:00",
                updated_at="2026-06-01T10:00:00",
                status="ready",
                source="lexprime_benchmark",
            ),
            "ds-bench-002": EvaluationDataset(
                dataset_id="ds-bench-002",
                name="LexBench 法规引用基准 v1.0",
                description="法律法规引用准确率评测数据集",
                dataset_type=EvaluationDatasetType.STANDARD.value,
                task_type=EvaluationTaskType.LAW_REFERENCE.value,
                sample_count=500,
                categories={
                    "民法": 200,
                    "刑法": 100,
                    "行政法": 100,
                    "商法": 100,
                },
                created_at="2026-05-15T10:00:00",
                updated_at="2026-06-10T10:00:00",
                status="ready",
                source="lexprime_benchmark",
            ),
            "ds-bench-003": EvaluationDataset(
                dataset_id="ds-bench-003",
                name="LexBench 合同审查基准 v1.0",
                description="合同风险审查召回率评测数据集",
                dataset_type=EvaluationDatasetType.STANDARD.value,
                task_type=EvaluationTaskType.CONTRACT_REVIEW.value,
                sample_count=200,
                categories={
                    "买卖合同": 50,
                    "借款合同": 40,
                    "劳动合同": 40,
                    "租赁合同": 35,
                    "技术合同": 35,
                },
                created_at="2026-06-01T10:00:00",
                updated_at="2026-06-20T10:00:00",
                status="ready",
                source="lexprime_benchmark",
            ),
            "ds-bench-004": EvaluationDataset(
                dataset_id="ds-bench-004",
                name="LexBench 法律问答基准 v1.0",
                description="法律问答准确率评测数据集",
                dataset_type=EvaluationDatasetType.STANDARD.value,
                task_type=EvaluationTaskType.QA.value,
                sample_count=800,
                categories={
                    "民事问答": 300,
                    "刑事问答": 200,
                    "行政问答": 150,
                    "程序问答": 150,
                },
                created_at="2026-06-05T10:00:00",
                updated_at="2026-06-25T10:00:00",
                status="ready",
                source="lexprime_benchmark",
            ),
        }

        self._tasks = {
            "task-001": EvaluationTask(
                task_id="task-001",
                name="Embedding 模型对比评测",
                description="对比 v1.0 和 v1.1 Embedding 模型在案例检索上的表现",
                task_type=EvaluationTaskType.CASE_RETRIEVAL.value,
                model_ids=["mv-001", "mv-002"],
                dataset_id="ds-bench-001",
                status=EvaluationStatus.COMPLETED.value,
                progress=1.0,
                started_at="2026-06-15T10:00:00",
                finished_at="2026-06-15T10:30:00",
                created_at="2026-06-15T09:00:00",
                total_samples=1000,
                processed_samples=1000,
            ),
            "task-002": EvaluationTask(
                task_id="task-002",
                name="合同审查模型评测",
                description="评测合同审查模型的风险召回率",
                task_type=EvaluationTaskType.CONTRACT_REVIEW.value,
                model_ids=["mv-003"],
                dataset_id="ds-bench-003",
                status=EvaluationStatus.COMPLETED.value,
                progress=1.0,
                started_at="2026-06-20T14:00:00",
                finished_at="2026-06-20T14:20:00",
                created_at="2026-06-20T13:00:00",
                total_samples=200,
                processed_samples=200,
            ),
            "task-003": EvaluationTask(
                task_id="task-003",
                name="RAG 系统效果评测",
                description="评测 RAG 系统的问答准确率",
                task_type=EvaluationTaskType.QA.value,
                model_ids=["rag-v1", "rag-v2"],
                dataset_id="ds-bench-004",
                status=EvaluationStatus.RUNNING.value,
                progress=0.65,
                started_at=now,
                finished_at=None,
                created_at="2026-07-03T09:00:00",
                total_samples=800,
                processed_samples=520,
            ),
        }

        self._benchmarks = {
            "case_retrieval": {
                "name": "案例检索基准",
                "description": "评测案例检索的准确率和召回率",
                "metrics": ["precision@10", "recall@10", "ndcg@10", "mrr", "map"],
            },
            "law_reference": {
                "name": "法规引用基准",
                "description": "评测法规引用的准确率",
                "metrics": ["precision", "recall", "f1", "accuracy"],
            },
            "contract_review": {
                "name": "合同审查基准",
                "description": "评测合同风险点的识别召回率",
                "metrics": ["recall", "precision", "f1", "false_negative_rate"],
            },
            "qa": {
                "name": "问答基准",
                "description": "评测法律问答的准确率",
                "metrics": ["accuracy", "f1", "bleu", "rouge_l"],
            },
        }

    def list_datasets(self, task_type: Optional[str] = None) -> List[EvaluationDataset]:
        """获取评测数据集列表

        Args:
            task_type: 按任务类型筛选

        Returns:
            数据集列表
        """
        datasets = list(self._datasets.values())

        if task_type:
            datasets = [d for d in datasets if d.task_type == task_type]

        datasets.sort(key=lambda x: x.updated_at, reverse=True)
        return datasets

    def get_dataset(self, dataset_id: str) -> Optional[EvaluationDataset]:
        """获取数据集详情"""
        return self._datasets.get(dataset_id)

    def create_dataset(self, name: str, description: str, task_type: str,
                       items: Optional[List[Dict[str, Any]]] = None) -> EvaluationDataset:
        """创建评测数据集

        Args:
            name: 数据集名称
            description: 描述
            task_type: 任务类型
            items: 评测用例列表

        Returns:
            创建的数据集
        """
        dataset_id = f"ds-{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        categories: Dict[str, int] = {}
        if items:
            for item in items:
                cat = item.get("category", "other")
                categories[cat] = categories.get(cat, 0) + 1

        dataset = EvaluationDataset(
            dataset_id=dataset_id,
            name=name,
            description=description,
            dataset_type=EvaluationDatasetType.CUSTOM.value,
            task_type=task_type,
            sample_count=len(items) if items else 0,
            categories=categories,
            created_at=now,
            updated_at=now,
            status="ready" if items else "empty",
            source="custom",
        )

        self._datasets[dataset_id] = dataset
        logger.info(f"Evaluation dataset created: {dataset_id}")
        return dataset

    def generate_test_items(self, template_type: str, count: int = 100) -> List[EvaluationTestItem]:
        """生成评测用例

        Args:
            template_type: 模板类型
            count: 生成数量

        Returns:
            评测用例列表
        """
        items = []
        templates = self._get_qa_templates(template_type)

        for i in range(count):
            template = templates[i % len(templates)]
            item = EvaluationTestItem(
                item_id=f"item-{uuid.uuid4().hex[:8]}",
                query=template["query"],
                expected=template["expected"],
                category=template.get("category", "general"),
                difficulty=template.get("difficulty", "medium"),
                metadata={"template_index": i % len(templates)},
            )
            items.append(item)

        return items

    def _get_qa_templates(self, template_type: str) -> List[Dict[str, Any]]:
        """获取问答模板"""
        if template_type == "case_retrieval":
            return [
                {
                    "query": "民间借贷利息最高可以约定多少？",
                    "expected": {"case_ids": ["case-001", "case-002"], "key_points": ["LPR4倍", "法定保护上限"]},
                    "category": "合同纠纷",
                    "difficulty": "easy",
                },
                {
                    "query": "劳动合同到期不续签有赔偿吗？",
                    "expected": {"case_ids": ["case-003", "case-004"], "key_points": ["经济补偿", "N+1"]},
                    "category": "劳动争议",
                    "difficulty": "medium",
                },
            ]
        elif template_type == "contract_review":
            return [
                {
                    "query": "审查这份买卖合同的风险",
                    "expected": {"risk_count": 5, "high_risk_count": 2},
                    "category": "买卖合同",
                    "difficulty": "medium",
                },
            ]
        else:
            return []

    def list_tasks(self, status: Optional[str] = None) -> List[EvaluationTask]:
        """获取评测任务列表

        Args:
            status: 按状态筛选

        Returns:
            任务列表
        """
        tasks = list(self._tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        tasks.sort(key=lambda x: x.created_at, reverse=True)
        return tasks

    def get_task(self, task_id: str) -> Optional[EvaluationTask]:
        """获取评测任务详情"""
        return self._tasks.get(task_id)

    def create_task(self, name: str, description: str, task_type: str,
                    model_ids: List[str], dataset_id: str) -> EvaluationTask:
        """创建评测任务

        Args:
            name: 任务名称
            description: 描述
            task_type: 任务类型
            model_ids: 待评测的模型 ID 列表
            dataset_id: 数据集 ID

        Returns:
            创建的任务
        """
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        dataset = self._datasets.get(dataset_id)
        total_samples = dataset.sample_count if dataset else 0

        task = EvaluationTask(
            task_id=task_id,
            name=name,
            description=description,
            task_type=task_type,
            model_ids=model_ids,
            dataset_id=dataset_id,
            status=EvaluationStatus.PENDING.value,
            progress=0.0,
            started_at=None,
            finished_at=None,
            created_at=now,
            total_samples=total_samples,
            processed_samples=0,
        )

        self._tasks[task_id] = task
        logger.info(f"Evaluation task created: {task_id}")
        return task

    def run_evaluation(self, task_id: str) -> bool:
        """运行评测任务

        Args:
            task_id: 任务 ID

        Returns:
            是否成功启动
        """
        task = self._tasks.get(task_id)
        if not task:
            return False

        task.status = EvaluationStatus.RUNNING.value
        task.started_at = datetime.now().isoformat()
        task.progress = 0.0

        logger.info(f"Evaluation task started: {task_id}")

        if self.mock_mode:
            import asyncio
            asyncio.create_task(self._simulate_evaluation(task_id))

        return True

    async def _simulate_evaluation(self, task_id: str):
        """模拟评测过程"""
        task = self._tasks.get(task_id)
        if not task:
            return

        total = task.total_samples or 100
        for i in range(1, total + 1):
            await asyncio.sleep(0.01)
            task.processed_samples = i
            task.progress = i / total

        task.status = EvaluationStatus.COMPLETED.value
        task.finished_at = datetime.now().isoformat()
        task.progress = 1.0

        self._generate_mock_results(task)

        logger.info(f"Evaluation task completed: {task_id}")

    def _generate_mock_results(self, task: EvaluationTask):
        """生成 Mock 评测结果"""
        results = []
        now = datetime.now().isoformat()

        model_names = {
            "mv-001": "lexprime-embedding-v1.0",
            "mv-002": "lexprime-embedding-v1.1",
            "mv-003": "lexprime-reranker-v1.0",
            "rag-v1": "rag-system-v1",
            "rag-v2": "rag-system-v2",
        }

        for idx, model_id in enumerate(task.model_ids):
            base_score = 0.75 + idx * 0.08

            metrics = EvaluationMetrics(
                precision=round(min(0.98, base_score + 0.05), 4),
                recall=round(min(0.95, base_score), 4),
                f1_score=round(min(0.96, base_score + 0.02), 4),
                accuracy=round(min(0.97, base_score + 0.03), 4),
                mrr=round(min(0.94, base_score - 0.02), 4),
                ndcg=round(min(0.92, base_score - 0.04), 4),
                map_score=round(min(0.90, base_score - 0.06), 4),
                latency_ms_avg=round(100 + idx * 20, 1),
                latency_ms_p95=round(150 + idx * 30, 1),
                tokens_per_second=round(500 - idx * 50, 1),
            )

            category_metrics = {}
            dataset = self._datasets.get(task.dataset_id)
            if dataset:
                for cat in dataset.categories.keys():
                    cat_variance = (hash(cat) % 20 - 10) / 100
                    category_metrics[cat] = EvaluationMetrics(
                        precision=round(max(0.5, min(0.99, metrics.precision + cat_variance)), 4),
                        recall=round(max(0.5, min(0.99, metrics.recall + cat_variance)), 4),
                        f1_score=round(max(0.5, min(0.99, metrics.f1_score + cat_variance)), 4),
                    )

            error_cases = [
                {
                    "item_id": f"err-{idx}-001",
                    "query": "测试查询1",
                    "expected": "预期结果",
                    "actual": "实际结果",
                    "error_type": "false_negative",
                    "severity": "high",
                },
                {
                    "item_id": f"err-{idx}-002",
                    "query": "测试查询2",
                    "expected": "预期结果",
                    "actual": "实际结果",
                    "error_type": "false_positive",
                    "severity": "medium",
                },
            ]

            result = EvaluationResult(
                result_id=f"result-{uuid.uuid4().hex[:8]}",
                task_id=task.task_id,
                model_id=model_id,
                model_name=model_names.get(model_id, f"model-{model_id}"),
                metrics=metrics,
                category_metrics=category_metrics,
                error_cases=error_cases,
                created_at=now,
            )
            results.append(result)

        self._results[task.task_id] = results

    def get_task_results(self, task_id: str) -> List[EvaluationResult]:
        """获取任务评测结果

        Args:
            task_id: 任务 ID

        Returns:
            评测结果列表
        """
        if task_id not in self._results:
            task = self._tasks.get(task_id)
            if task and task.status == EvaluationStatus.COMPLETED.value:
                self._generate_mock_results(task)

        return self._results.get(task_id, [])

    def compare_models(self, task_id: str) -> Dict[str, Any]:
        """对比模型评测结果

        Args:
            task_id: 任务 ID

        Returns:
            对比结果
        """
        results = self.get_task_results(task_id)
        if len(results) < 2:
            return {"results": results, "comparison": None}

        metrics_list = ["precision", "recall", "f1_score", "accuracy", "mrr", "ndcg"]

        comparison = []
        for metric in metrics_list:
            values = {}
            for r in results:
                values[r.model_name] = getattr(r.metrics, metric, 0.0)

            sorted_models = sorted(values.items(), key=lambda x: x[1], reverse=True)
            comparison.append({
                "metric": metric,
                "values": values,
                "winner": sorted_models[0][0] if sorted_models else "",
                "winner_value": sorted_models[0][1] if sorted_models else 0.0,
                "gap": sorted_models[0][1] - sorted_models[1][1] if len(sorted_models) >= 2 else 0.0,
            })

        return {
            "task_id": task_id,
            "model_count": len(results),
            "comparison": comparison,
            "overall_winner": self._determine_winner(results),
        }

    def _determine_winner(self, results: List[EvaluationResult]) -> str:
        """确定综合优胜模型"""
        if not results:
            return ""

        scores = {}
        for r in results:
            score = (
                r.metrics.precision * 0.25 +
                r.metrics.recall * 0.25 +
                r.metrics.f1_score * 0.2 +
                r.metrics.accuracy * 0.2 +
                r.metrics.ndcg * 0.1
            )
            scores[r.model_name] = score

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[0][0] if sorted_scores else ""

    def generate_report(self, task_id: str) -> Optional[EvaluationReport]:
        """生成评测报告

        Args:
            task_id: 任务 ID

        Returns:
            评测报告
        """
        task = self._tasks.get(task_id)
        if not task:
            return None

        results = self.get_task_results(task_id)
        if not results:
            return None

        comparison = self.compare_models(task_id)
        winner = comparison.get("overall_winner", "")

        model_comparison = []
        for r in results:
            model_comparison.append({
                "model_name": r.model_name,
                "model_id": r.model_id,
                "precision": r.metrics.precision,
                "recall": r.metrics.recall,
                "f1_score": r.metrics.f1_score,
                "accuracy": r.metrics.accuracy,
                "mrr": r.metrics.mrr,
                "ndcg": r.metrics.ndcg,
                "latency_ms_avg": r.metrics.latency_ms_avg,
            })

        summary = f"本次评测对比了 {len(results)} 个模型在{self._get_task_type_name(task.task_type)}任务上的表现。综合各项指标，{winner}表现最优。"

        error_analysis = (
            "错误分析显示，主要错误类型包括：\n"
            "1. 假阴性：部分相关案例未被检索到，主要原因是语义理解偏差\n"
            "2. 假阳性：部分不相关结果被返回，需要优化排序策略\n"
            "3. 长尾问题：低频法律概念的识别准确率有待提升"
        )

        suggestions = [
            "建议增加领域预训练数据，特别是低频法律概念的语料",
            "优化重排序模型，提升排序准确性",
            "增加同义词和法律术语词典，改善召回率",
            "针对长尾问题，可考虑引入知识图谱增强",
            "优化分块策略，确保关键信息不被截断",
        ]

        report = EvaluationReport(
            report_id=f"report-{uuid.uuid4().hex[:8]}",
            task_id=task_id,
            task_name=task.name,
            summary=summary,
            overall_winner=winner,
            model_comparison=model_comparison,
            error_analysis=error_analysis,
            improvement_suggestions=suggestions,
            created_at=datetime.now().isoformat(),
        )

        self._reports[report.report_id] = report
        return report

    def _get_task_type_name(self, task_type: str) -> str:
        """获取任务类型中文名"""
        names = {
            "case_retrieval": "案例检索",
            "law_reference": "法规引用",
            "contract_review": "合同审查",
            "qa": "法律问答",
            "summarization": "文本摘要",
            "embedding": "向量嵌入",
        }
        return names.get(task_type, task_type)

    def get_benchmarks(self) -> Dict[str, Dict[str, Any]]:
        """获取基准评测列表"""
        return self._benchmarks

    def list_error_cases(self, task_id: str, model_id: Optional[str] = None,
                         error_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取错误案例列表

        Args:
            task_id: 任务 ID
            model_id: 模型 ID 筛选
            error_type: 错误类型筛选

        Returns:
            错误案例列表
        """
        results = self.get_task_results(task_id)
        all_errors = []

        for r in results:
            if model_id and r.model_id != model_id:
                continue

            for err in r.error_cases:
                if error_type and err.get("error_type") != error_type:
                    continue
                err_item = dict(err)
                err_item["model_id"] = r.model_id
                err_item["model_name"] = r.model_name
                all_errors.append(err_item)

        return all_errors

    def export_report(self, report_id: str, format_type: str = "json") -> str:
        """导出评测报告

        Args:
            report_id: 报告 ID
            format_type: 导出格式 (json/markdown/html)

        Returns:
            导出的报告内容
        """
        report = self._reports.get(report_id)
        if not report:
            return ""

        if format_type == "json":
            return json.dumps({
                "report_id": report.report_id,
                "task_id": report.task_id,
                "task_name": report.task_name,
                "summary": report.summary,
                "overall_winner": report.overall_winner,
                "model_comparison": report.model_comparison,
                "error_analysis": report.error_analysis,
                "improvement_suggestions": report.improvement_suggestions,
                "created_at": report.created_at,
            }, ensure_ascii=False, indent=2)

        elif format_type == "markdown":
            md = f"# {report.task_name} - 评测报告\n\n"
            md += f"**生成时间**: {report.created_at}\n\n"
            md += f"## 概述\n\n{report.summary}\n\n"
            md += f"**综合优胜**: {report.overall_winner}\n\n"
            md += "## 模型对比\n\n"
            md += "| 模型 | Precision | Recall | F1 | Accuracy | NDCG |\n"
            md += "|------|-----------|--------|----|----------|------|\n"
            for m in report.model_comparison:
                md += f"| {m['model_name']} | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1_score']:.4f} | {m['accuracy']:.4f} | {m['ndcg']:.4f} |\n"
            md += "\n## 错误分析\n\n"
            md += report.error_analysis + "\n\n"
            md += "## 改进建议\n\n"
            for i, s in enumerate(report.improvement_suggestions, 1):
                md += f"{i}. {s}\n"
            return md

        return ""


_evaluation_instance: Optional[EvaluationEngine] = None


def get_evaluation_engine() -> EvaluationEngine:
    """获取评测引擎单例"""
    global _evaluation_instance
    if _evaluation_instance is None:
        _evaluation_instance = EvaluationEngine(mock_mode=True)
    return _evaluation_instance
