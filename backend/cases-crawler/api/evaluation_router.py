"""
评测管理 API
============

提供模型评测相关的 API 接口：
- 评测任务列表/详情
- 创建/运行评测任务
- 评测结果查询
- 模型对比
- 评测报告生成/导出
- 数据集管理
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from ai.evaluation import (
    get_evaluation_engine,
    EvaluationConfig,
    EvaluationTaskType,
    EvaluationStatus,
)

router = APIRouter(prefix="/api/evaluation", tags=["评测管理"])

evaluation_engine = get_evaluation_engine()


class CreateTaskRequest(BaseModel):
    name: str
    description: str = ""
    task_type: str
    model_ids: List[str]
    dataset_id: str


class CreateDatasetRequest(BaseModel):
    name: str
    description: str = ""
    task_type: str
    items: Optional[List[Dict[str, Any]]] = None


class GenerateItemsRequest(BaseModel):
    template_type: str
    count: int = 100


@router.get("/datasets")
async def list_datasets(
    task_type: Optional[str] = Query(None, description="任务类型筛选"),
):
    """获取评测数据集列表"""
    datasets = evaluation_engine.list_datasets(task_type=task_type)
    return {
        "code": 0,
        "msg": "success",
        "data": [
            {
                "dataset_id": d.dataset_id,
                "name": d.name,
                "description": d.description,
                "dataset_type": d.dataset_type,
                "task_type": d.task_type,
                "sample_count": d.sample_count,
                "categories": d.categories,
                "created_at": d.created_at,
                "updated_at": d.updated_at,
                "status": d.status,
                "source": d.source,
            }
            for d in datasets
        ],
    }


@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str):
    """获取数据集详情"""
    dataset = evaluation_engine.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")

    return {
        "code": 0,
        "msg": "success",
        "data": {
            "dataset_id": dataset.dataset_id,
            "name": dataset.name,
            "description": dataset.description,
            "dataset_type": dataset.dataset_type,
            "task_type": dataset.task_type,
            "sample_count": dataset.sample_count,
            "categories": dataset.categories,
            "created_at": dataset.created_at,
            "updated_at": dataset.updated_at,
            "status": dataset.status,
            "source": dataset.source,
        },
    }


@router.post("/datasets")
async def create_dataset(req: CreateDatasetRequest):
    """创建评测数据集"""
    dataset = evaluation_engine.create_dataset(
        name=req.name,
        description=req.description,
        task_type=req.task_type,
        items=req.items,
    )

    return {
        "code": 0,
        "msg": "创建成功",
        "data": {
            "dataset_id": dataset.dataset_id,
            "name": dataset.name,
        },
    }


@router.post("/datasets/generate-items")
async def generate_test_items(req: GenerateItemsRequest):
    """生成评测用例"""
    items = evaluation_engine.generate_test_items(
        template_type=req.template_type,
        count=req.count,
    )

    return {
        "code": 0,
        "msg": "生成成功",
        "data": {
            "count": len(items),
            "items": [
                {
                    "item_id": item.item_id,
                    "query": item.query,
                    "expected": item.expected,
                    "category": item.category,
                    "difficulty": item.difficulty,
                }
                for item in items
            ],
        },
    }


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = Query(None, description="状态筛选"),
):
    """获取评测任务列表"""
    tasks = evaluation_engine.list_tasks(status=status)
    return {
        "code": 0,
        "msg": "success",
        "data": [
            {
                "task_id": t.task_id,
                "name": t.name,
                "description": t.description,
                "task_type": t.task_type,
                "model_ids": t.model_ids,
                "dataset_id": t.dataset_id,
                "status": t.status,
                "progress": t.progress,
                "started_at": t.started_at,
                "finished_at": t.finished_at,
                "created_at": t.created_at,
                "total_samples": t.total_samples,
                "processed_samples": t.processed_samples,
            }
            for t in tasks
        ],
    }


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """获取评测任务详情"""
    task = evaluation_engine.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {
        "code": 0,
        "msg": "success",
        "data": {
            "task_id": task.task_id,
            "name": task.name,
            "description": task.description,
            "task_type": task.task_type,
            "model_ids": task.model_ids,
            "dataset_id": task.dataset_id,
            "status": task.status,
            "progress": task.progress,
            "started_at": task.started_at,
            "finished_at": task.finished_at,
            "created_at": task.created_at,
            "total_samples": task.total_samples,
            "processed_samples": task.processed_samples,
        },
    }


@router.post("/tasks")
async def create_task(req: CreateTaskRequest):
    """创建评测任务"""
    task = evaluation_engine.create_task(
        name=req.name,
        description=req.description,
        task_type=req.task_type,
        model_ids=req.model_ids,
        dataset_id=req.dataset_id,
    )

    return {
        "code": 0,
        "msg": "创建成功",
        "data": {
            "task_id": task.task_id,
            "name": task.name,
            "status": task.status,
        },
    }


@router.post("/tasks/{task_id}/run")
async def run_task(task_id: str):
    """运行评测任务"""
    success = evaluation_engine.run_evaluation(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {
        "code": 0,
        "msg": "评测任务已启动",
        "data": {"task_id": task_id, "status": "running"},
    }


@router.get("/tasks/{task_id}/results")
async def get_task_results(task_id: str):
    """获取任务评测结果"""
    task = evaluation_engine.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    results = evaluation_engine.get_task_results(task_id)

    return {
        "code": 0,
        "msg": "success",
        "data": [
            {
                "result_id": r.result_id,
                "task_id": r.task_id,
                "model_id": r.model_id,
                "model_name": r.model_name,
                "metrics": {
                    "precision": r.metrics.precision,
                    "recall": r.metrics.recall,
                    "f1_score": r.metrics.f1_score,
                    "accuracy": r.metrics.accuracy,
                    "mrr": r.metrics.mrr,
                    "ndcg": r.metrics.ndcg,
                    "map_score": r.metrics.map_score,
                    "bleu": r.metrics.bleu,
                    "rouge_l": r.metrics.rouge_l,
                    "bert_score": r.metrics.bert_score,
                    "latency_ms_avg": r.metrics.latency_ms_avg,
                    "latency_ms_p95": r.metrics.latency_ms_p95,
                    "tokens_per_second": r.metrics.tokens_per_second,
                    "custom_metrics": r.metrics.custom_metrics,
                },
                "category_metrics": {
                    cat: {
                        "precision": cm.precision,
                        "recall": cm.recall,
                        "f1_score": cm.f1_score,
                    }
                    for cat, cm in r.category_metrics.items()
                },
                "error_count": len(r.error_cases),
                "created_at": r.created_at,
            }
            for r in results
        ],
    }


@router.get("/tasks/{task_id}/compare")
async def compare_models(task_id: str):
    """对比模型评测结果"""
    task = evaluation_engine.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    comparison = evaluation_engine.compare_models(task_id)

    return {
        "code": 0,
        "msg": "success",
        "data": comparison,
    }


@router.get("/tasks/{task_id}/errors")
async def list_error_cases(
    task_id: str,
    model_id: Optional[str] = Query(None, description="模型 ID 筛选"),
    error_type: Optional[str] = Query(None, description="错误类型筛选"),
):
    """获取错误案例列表"""
    task = evaluation_engine.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    errors = evaluation_engine.list_error_cases(
        task_id=task_id,
        model_id=model_id,
        error_type=error_type,
    )

    return {
        "code": 0,
        "msg": "success",
        "data": errors,
    }


@router.post("/tasks/{task_id}/report")
async def generate_report(task_id: str):
    """生成评测报告"""
    task = evaluation_engine.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    report = evaluation_engine.generate_report(task_id)
    if not report:
        raise HTTPException(status_code=500, detail="报告生成失败")

    return {
        "code": 0,
        "msg": "生成成功",
        "data": {
            "report_id": report.report_id,
            "task_id": report.task_id,
            "task_name": report.task_name,
            "summary": report.summary,
            "overall_winner": report.overall_winner,
            "model_comparison": report.model_comparison,
            "error_analysis": report.error_analysis,
            "improvement_suggestions": report.improvement_suggestions,
            "created_at": report.created_at,
        },
    }


@router.get("/tasks/{task_id}/report/export")
async def export_report(
    task_id: str,
    format_type: str = Query("json", description="导出格式: json/markdown"),
):
    """导出评测报告"""
    report = evaluation_engine.generate_report(task_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    content = evaluation_engine.export_report(report.report_id, format_type)

    return {
        "code": 0,
        "msg": "导出成功",
        "data": {
            "report_id": report.report_id,
            "format": format_type,
            "content": content,
        },
    }


@router.get("/benchmarks")
async def list_benchmarks():
    """获取基准评测列表"""
    benchmarks = evaluation_engine.get_benchmarks()
    return {
        "code": 0,
        "msg": "success",
        "data": benchmarks,
    }
