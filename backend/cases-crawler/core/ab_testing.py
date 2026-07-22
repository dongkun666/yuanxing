"""
LexPrime A/B 测试系统
提供实验定义和管理、用户分桶、指标收集、统计显著性分析和实验报告生成

主要功能:
- 实验定义和管理：创建、启动、停止、删除实验
- 用户分桶：基于哈希的确定性分桶算法
- 指标收集：收集实验相关的用户行为指标
- 统计显著性分析：计算 p 值和置信区间
- 实验报告生成：生成完整的实验分析报告
"""
from __future__ import annotations

import math
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from collections import defaultdict
from loguru import logger
from pydantic import BaseModel, Field


# ============================================================================
# 枚举定义
# ============================================================================

class ExperimentStatus(str, Enum):
    """实验状态"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class VariantType(str, Enum):
    """变体类型"""
    CONTROL = "control"
    TREATMENT = "treatment"


class MetricType(str, Enum):
    """指标类型"""
    BINARY = "binary"
    CONTINUOUS = "continuous"
    COUNT = "count"
    DURATION = "duration"


class StatSignificance(str, Enum):
    """统计显著性"""
    NOT_SIGNIFICANT = "not_significant"
    POSITIVE = "positive"
    NEGATIVE = "negative"
    INCONCLUSIVE = "inconclusive"


# ============================================================================
# Pydantic 模型
# ============================================================================

class ExperimentVariant(BaseModel):
    """实验变体"""
    id: str = Field(..., description="变体ID")
    name: str = Field(..., description="变体名称")
    type: VariantType = Field(VariantType.TREATMENT, description="变体类型")
    traffic_percentage: float = Field(50.0, description="流量百分比")
    description: Optional[str] = Field(None, description="变体描述")
    config: Dict[str, Any] = Field(default_factory=dict, description="变体配置")


class ExperimentMetric(BaseModel):
    """实验指标"""
    name: str = Field(..., description="指标名称")
    type: MetricType = Field(MetricType.BINARY, description="指标类型")
    description: Optional[str] = Field(None, description="指标描述")
    is_primary: bool = Field(False, description="是否为主指标")
    unit: Optional[str] = Field(None, description="单位")


class Experiment(BaseModel):
    """A/B 实验定义"""
    id: str = Field(..., description="实验ID")
    name: str = Field(..., description="实验名称")
    description: Optional[str] = Field(None, description="实验描述")
    hypothesis: Optional[str] = Field(None, description="实验假设")
    status: ExperimentStatus = Field(ExperimentStatus.DRAFT, description="实验状态")
    variants: List[ExperimentVariant] = Field(default_factory=list, description="变体列表")
    metrics: List[ExperimentMetric] = Field(default_factory=list, description="指标列表")
    target_users: Optional[str] = Field(None, description="目标用户群")
    sample_size: int = Field(1000, description="预估样本量")
    min_effect_size: float = Field(0.05, description="最小可检测效应量")
    confidence_level: float = Field(0.95, description="置信水平")
    created_by: Optional[str] = Field(None, description="创建者")
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = Field(None, description="开始时间")
    ended_at: Optional[datetime] = Field(None, description="结束时间")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class MetricDataPoint(BaseModel):
    """指标数据点"""
    experiment_id: str = Field(..., description="实验ID")
    variant_id: str = Field(..., description="变体ID")
    user_id: str = Field(..., description="用户ID")
    metric_name: str = Field(..., description="指标名称")
    value: float = Field(0.0, description="指标值")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VariantStats(BaseModel):
    """变体统计数据"""
    variant_id: str = Field(..., description="变体ID")
    variant_name: str = Field(..., description="变体名称")
    user_count: int = Field(0, description="用户数")
    metric_stats: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="各指标统计")


class ExperimentReport(BaseModel):
    """实验报告"""
    experiment_id: str = Field(..., description="实验ID")
    experiment_name: str = Field(..., description="实验名称")
    status: ExperimentStatus = Field(..., description="实验状态")
    duration_days: float = Field(0.0, description="实验持续天数")
    total_users: int = Field(0, description="总用户数")
    variant_stats: List[VariantStats] = Field(default_factory=list, description="各变体统计")
    primary_metric_results: List[Dict[str, Any]] = Field(default_factory=list, description="主指标结果")
    secondary_metric_results: List[Dict[str, Any]] = Field(default_factory=list, description="次指标结果")
    overall_conclusion: str = Field("", description="总体结论")
    recommendation: str = Field("", description="建议")
    generated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# ============================================================================
# A/B 测试引擎
# ============================================================================

class ABTestingEngine:
    """A/B 测试引擎 - 核心实现"""

    _experiments: Dict[str, Experiment] = {}
    _metric_data: Dict[str, List[MetricDataPoint]] = defaultdict(list)
    _user_variants: Dict[str, Dict[str, str]] = defaultdict(dict)

    @classmethod
    def create_experiment(cls, experiment: Experiment) -> Experiment:
        """创建实验"""
        if experiment.id in cls._experiments:
            raise ValueError(f"实验ID已存在: {experiment.id}")

        cls._validate_experiment(experiment)
        cls._experiments[experiment.id] = experiment
        logger.info(f"实验已创建: {experiment.id} ({experiment.name})")
        return experiment

    @classmethod
    def _validate_experiment(cls, experiment: Experiment) -> None:
        """验证实验配置"""
        if not experiment.variants or len(experiment.variants) < 2:
            raise ValueError("实验至少需要2个变体")

        control_count = sum(1 for v in experiment.variants if v.type == VariantType.CONTROL)
        if control_count != 1:
            raise ValueError("实验必须有且仅有1个对照组")

        total_traffic = sum(v.traffic_percentage for v in experiment.variants)
        if abs(total_traffic - 100.0) > 0.01:
            raise ValueError(f"流量分配总和必须为100%，当前为 {total_traffic}%")

        if not experiment.metrics:
            raise ValueError("实验至少需要1个指标")

        primary_count = sum(1 for m in experiment.metrics if m.is_primary)
        if primary_count == 0:
            raise ValueError("实验至少需要1个主指标")

    @classmethod
    def get_experiment(cls, experiment_id: str) -> Optional[Experiment]:
        """获取实验"""
        return cls._experiments.get(experiment_id)

    @classmethod
    def list_experiments(
        cls,
        status: Optional[ExperimentStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Experiment], int]:
        """列出实验"""
        experiments = list(cls._experiments.values())

        if status:
            experiments = [e for e in experiments if e.status == status]

        experiments.sort(key=lambda e: e.created_at, reverse=True)
        total = len(experiments)
        experiments = experiments[offset:offset + limit]

        return experiments, total

    @classmethod
    def start_experiment(cls, experiment_id: str) -> Experiment:
        """启动实验"""
        experiment = cls.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"实验不存在: {experiment_id}")

        if experiment.status != ExperimentStatus.DRAFT:
            raise ValueError(f"只能启动草稿状态的实验，当前状态: {experiment.status.value}")

        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.now()

        logger.info(f"实验已启动: {experiment_id}")
        return experiment

    @classmethod
    def stop_experiment(cls, experiment_id: str) -> Experiment:
        """停止实验"""
        experiment = cls.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"实验不存在: {experiment_id}")

        if experiment.status != ExperimentStatus.RUNNING:
            raise ValueError(f"只能停止运行中的实验，当前状态: {experiment.status.value}")

        experiment.status = ExperimentStatus.COMPLETED
        experiment.ended_at = datetime.now()

        logger.info(f"实验已停止: {experiment_id}")
        return experiment

    @classmethod
    def get_user_variant(cls, experiment_id: str, user_id: str) -> Optional[str]:
        """获取用户所在的变体（确定性分桶）"""
        experiment = cls.get_experiment(experiment_id)
        if not experiment:
            return None

        if experiment.status not in (ExperimentStatus.RUNNING, ExperimentStatus.PAUSED):
            return None

        if user_id in cls._user_variants and experiment_id in cls._user_variants[user_id]:
            return cls._user_variants[user_id][experiment_id]

        variant_id = cls._bucket_user(experiment, user_id)
        cls._user_variants[user_id][experiment_id] = variant_id

        return variant_id

    @classmethod
    def _bucket_user(cls, experiment: Experiment, user_id: str) -> str:
        """基于哈希的用户分桶算法"""
        hash_key = f"{experiment.id}:{user_id}"
        hash_digest = hashlib.md5(hash_key.encode('utf-8')).hexdigest()
        hash_int = int(hash_digest[:8], 16)
        bucket = hash_int % 10000 / 100.0

        cumulative = 0.0
        for variant in experiment.variants:
            cumulative += variant.traffic_percentage
            if bucket < cumulative:
                return variant.id

        return experiment.variants[-1].id

    @classmethod
    def record_metric(
        cls,
        experiment_id: str,
        user_id: str,
        metric_name: str,
        value: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """记录指标数据"""
        experiment = cls.get_experiment(experiment_id)
        if not experiment or experiment.status != ExperimentStatus.RUNNING:
            return False

        variant_id = cls.get_user_variant(experiment_id, user_id)
        if not variant_id:
            return False

        metric = next((m for m in experiment.metrics if m.name == metric_name), None)
        if not metric:
            return False

        data_point = MetricDataPoint(
            experiment_id=experiment_id,
            variant_id=variant_id,
            user_id=user_id,
            metric_name=metric_name,
            value=value,
            metadata=metadata or {}
        )

        key = f"{experiment_id}:{metric_name}"
        cls._metric_data[key].append(data_point)

        logger.debug(f"记录指标: {experiment_id}/{variant_id}/{metric_name} = {value}")
        return True

    @classmethod
    def calculate_variant_stats(cls, experiment_id: str) -> List[VariantStats]:
        """计算各变体的统计数据"""
        experiment = cls.get_experiment(experiment_id)
        if not experiment:
            return []

        stats_list = []

        for variant in experiment.variants:
            users = set()
            metric_values: Dict[str, List[float]] = defaultdict(list)

            for metric in experiment.metrics:
                key = f"{experiment_id}:{metric.name}"
                data_points = cls._metric_data.get(key, [])
                variant_points = [p for p in data_points if p.variant_id == variant.id]

                for point in variant_points:
                    users.add(point.user_id)
                    metric_values[metric.name].append(point.value)

            metric_stats = {}
            for metric in experiment.metrics:
                values = metric_values.get(metric.name, [])
                if values:
                    metric_stats[metric.name] = {
                        'count': len(values),
                        'sum': sum(values),
                        'mean': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values),
                        'variance': cls._calculate_variance(values),
                        'std_dev': math.sqrt(cls._calculate_variance(values)) if len(values) > 1 else 0
                    }
                else:
                    metric_stats[metric.name] = {
                        'count': 0,
                        'sum': 0,
                        'mean': 0,
                        'min': 0,
                        'max': 0,
                        'variance': 0,
                        'std_dev': 0
                    }

            stats_list.append(VariantStats(
                variant_id=variant.id,
                variant_name=variant.name,
                user_count=len(users),
                metric_stats=metric_stats
            ))

        return stats_list

    @classmethod
    def _calculate_variance(cls, values: List[float]) -> float:
        """计算方差"""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance

    @classmethod
    def perform_ttest(
        cls,
        control_values: List[float],
        treatment_values: List[float]
    ) -> Dict[str, float]:
        """执行 t 检验（简化版 Welch's t-test）"""
        if len(control_values) < 2 or len(treatment_values) < 2:
            return {
                't_statistic': 0,
                'p_value': 1.0,
                'significant': False,
                'effect_size': 0,
                'ci_lower': 0,
                'ci_upper': 0
            }

        n1, n2 = len(control_values), len(treatment_values)
        mean1 = sum(control_values) / n1
        mean2 = sum(treatment_values) / n2
        var1 = cls._calculate_variance(control_values)
        var2 = cls._calculate_variance(treatment_values)

        se = math.sqrt(var1 / n1 + var2 / n2)
        if se == 0:
            return {
                't_statistic': 0,
                'p_value': 1.0,
                'significant': False,
                'effect_size': 0,
                'ci_lower': 0,
                'ci_upper': 0
            }

        t_stat = (mean2 - mean1) / se
        df = (var1 / n1 + var2 / n2) ** 2 / (
            (var1 / n1) ** 2 / (n1 - 1) + (var2 / n2) ** 2 / (n2 - 1)
        )

        p_value = cls._approximate_p_value(t_stat, df)
        effect_size = (mean2 - mean1) / math.sqrt((var1 + var2) / 2) if (var1 + var2) > 0 else 0

        ci_margin = 1.96 * se
        diff = mean2 - mean1

        return {
            't_statistic': round(t_stat, 4),
            'p_value': round(p_value, 4),
            'significant': p_value < 0.05,
            'effect_size': round(effect_size, 4),
            'mean_diff': round(diff, 4),
            'relative_lift': round((diff / mean1 * 100), 2) if mean1 != 0 else 0,
            'ci_lower': round(diff - ci_margin, 4),
            'ci_upper': round(diff + ci_margin, 4)
        }

    @classmethod
    def _approximate_p_value(cls, t_stat: float, df: float) -> float:
        """近似计算 p 值（简化版）"""
        t = abs(t_stat)
        a = df / (df + t * t)

        if df <= 1:
            return 1.0 - (2 / math.pi) * math.atan(t)

        x = df / (df + t * t)
        p = cls._betai(df / 2, 0.5, x)
        return p

    @classmethod
    def _betai(cls, a: float, b: float, x: float) -> float:
        """不完全 Beta 函数近似"""
        if x <= 0:
            return 0
        if x >= 1:
            return 1

        lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
        bt = math.exp(a * math.log(x) + b * math.log(1 - x) - lbeta)

        if x < (a + 1) / (a + b + 2):
            return bt * cls._betacf(a, b, x) / a
        else:
            return 1 - bt * cls._betacf(b, a, 1 - x) / b

    @classmethod
    def _betacf(cls, a: float, b: float, x: float, max_iter: int = 100) -> float:
        """连分数展开计算 Beta 函数"""
        qab = a + b
        qap = a + 1
        qam = a - 1
        c = 1.0
        d = 1.0 - qab * x / qap

        if abs(d) < 1e-10:
            d = 1e-10
        d = 1.0 / d
        h = d

        for m in range(1, max_iter + 1):
            m2 = 2 * m

            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            d = 1.0 + aa * d
            if abs(d) < 1e-10:
                d = 1e-10
            c = 1.0 + aa / c
            if abs(c) < 1e-10:
                c = 1e-10
            d = 1.0 / d
            h *= d * c

            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            d = 1.0 + aa * d
            if abs(d) < 1e-10:
                d = 1e-10
            c = 1.0 + aa / c
            if abs(c) < 1e-10:
                c = 1e-10
            d = 1.0 / d
            delta = d * c
            h *= delta

            if abs(delta - 1.0) < 3e-7:
                break

        return h

    @classmethod
    def generate_report(cls, experiment_id: str) -> ExperimentReport:
        """生成实验报告"""
        experiment = cls.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"实验不存在: {experiment_id}")

        variant_stats = cls.calculate_variant_stats(experiment_id)

        duration_days = 0.0
        if experiment.started_at:
            end_time = experiment.ended_at or datetime.now()
            duration_days = (end_time - experiment.started_at).total_seconds() / 86400

        total_users = sum(s.user_count for s in variant_stats)

        control_variant = next((v for v in experiment.variants if v.type == VariantType.CONTROL), None)
        treatment_variants = [v for v in experiment.variants if v.type == VariantType.TREATMENT]

        primary_results = []
        secondary_results = []

        if control_variant:
            control_stats = next((s for s in variant_stats if s.variant_id == control_variant.id), None)

            for metric in experiment.metrics:
                key = f"{experiment_id}:{metric.name}"
                all_data = cls._metric_data.get(key, [])

                control_values = [
                    p.value for p in all_data
                    if p.variant_id == control_variant.id
                ]

                for treatment in treatment_variants:
                    treatment_values = [
                        p.value for p in all_data
                        if p.variant_id == treatment.id
                    ]

                    ttest_result = cls.perform_ttest(control_values, treatment_values)

                    result = {
                        'metric_name': metric.name,
                        'metric_type': metric.type.value,
                        'is_primary': metric.is_primary,
                        'control_variant': control_variant.name,
                        'treatment_variant': treatment.name,
                        'control_mean': ttest_result.get('mean_diff', 0) and (sum(control_values) / len(control_values)) if control_values else 0,
                        'treatment_mean': sum(treatment_values) / len(treatment_values) if treatment_values else 0,
                        **ttest_result
                    }

                    if metric.is_primary:
                        primary_results.append(result)
                    else:
                        secondary_results.append(result)

        conclusion, recommendation = cls._generate_conclusion(
            experiment, primary_results, total_users, duration_days
        )

        report = ExperimentReport(
            experiment_id=experiment.id,
            experiment_name=experiment.name,
            status=experiment.status,
            duration_days=round(duration_days, 2),
            total_users=total_users,
            variant_stats=variant_stats,
            primary_metric_results=primary_results,
            secondary_metric_results=secondary_results,
            overall_conclusion=conclusion,
            recommendation=recommendation
        )

        logger.info(f"实验报告已生成: {experiment_id}")
        return report

    @classmethod
    def _generate_conclusion(
        cls,
        experiment: Experiment,
        primary_results: List[Dict[str, Any]],
        total_users: int,
        duration_days: float
    ) -> Tuple[str, str]:
        """生成实验结论和建议"""
        if not primary_results:
            return (
                "数据不足，无法得出明确结论",
                "建议继续运行实验，收集更多数据"
            )

        significant_count = sum(1 for r in primary_results if r.get('significant', False))
        positive_count = sum(
            1 for r in primary_results
            if r.get('significant', False) and r.get('mean_diff', 0) > 0
        )
        negative_count = sum(
            1 for r in primary_results
            if r.get('significant', False) and r.get('mean_diff', 0) < 0
        )

        if total_users < experiment.sample_size and duration_days < 7:
            conclusion = "实验数据量不足，暂未达到统计显著性"
            recommendation = f"建议继续运行实验，预计需要约 {experiment.sample_size} 个样本"
        elif significant_count == 0:
            conclusion = "未观察到统计显著的差异"
            recommendation = "各组之间没有显著差异，建议维持现有方案或调整实验假设"
        elif positive_count > 0 and negative_count == 0:
            conclusion = f"实验结果为正向显著，{positive_count} 个主指标有显著提升"
            top_result = max(primary_results, key=lambda r: r.get('relative_lift', 0))
            recommendation = (
                f"建议发布实验组方案，最大提升约 {top_result.get('relative_lift', 0):.1f}%"
            )
        elif negative_count > 0:
            conclusion = f"实验结果为负向显著，{negative_count} 个主指标显著下降"
            recommendation = "建议保留对照组方案，不建议发布实验版本"
        else:
            conclusion = "实验结果有显著差异，但影响方向不一致"
            recommendation = "建议深入分析各指标变化，综合评估后再做决策"

        return conclusion, recommendation

    @classmethod
    def delete_experiment(cls, experiment_id: str) -> bool:
        """删除实验"""
        if experiment_id not in cls._experiments:
            return False

        del cls._experiments[experiment_id]

        keys_to_delete = [k for k in cls._metric_data if k.startswith(f"{experiment_id}:")]
        for key in keys_to_delete:
            del cls._metric_data[key]

        for user_id in cls._user_variants:
            if experiment_id in cls._user_variants[user_id]:
                del cls._user_variants[user_id][experiment_id]

        logger.info(f"实验已删除: {experiment_id}")
        return True


# ============================================================================
# 内置示例实验
# ============================================================================

def create_sample_experiments() -> None:
    """创建示例实验"""
    sample1 = Experiment(
        id="exp_homepage_redesign_001",
        name="首页改版测试",
        description="测试新版首页设计对用户参与度的影响",
        hypothesis="新版首页设计将提高用户平均停留时间和功能探索率",
        status=ExperimentStatus.RUNNING,
        variants=[
            ExperimentVariant(
                id="control",
                name="对照组",
                type=VariantType.CONTROL,
                traffic_percentage=50.0,
                description="现有首页设计",
                config={"layout": "classic"}
            ),
            ExperimentVariant(
                id="treatment_a",
                name="实验组A",
                type=VariantType.TREATMENT,
                traffic_percentage=50.0,
                description="新版首页设计",
                config={"layout": "modern", "show_quick_actions": True}
            )
        ],
        metrics=[
            ExperimentMetric(
                name="session_duration",
                type=MetricType.CONTINUOUS,
                description="平均会话时长(秒)",
                is_primary=True,
                unit="秒"
            ),
            ExperimentMetric(
                name="features_explored",
                type=MetricType.COUNT,
                description="探索功能数量",
                is_primary=True,
                unit="个"
            ),
            ExperimentMetric(
                name="bounce_rate",
                type=MetricType.BINARY,
                description="跳出率",
                is_primary=False,
                unit="%"
            )
        ],
        sample_size=2000,
        min_effect_size=0.1,
        confidence_level=0.95,
        created_by="admin",
        started_at=datetime.now() - timedelta(days=3)
    )

    sample2 = Experiment(
        id="exp_onboarding_flow_002",
        name="引导流程优化",
        description="测试简化版引导流程对新用户激活率的影响",
        hypothesis="简化引导流程将提高新用户的完成率和次日留存",
        status=ExperimentStatus.DRAFT,
        variants=[
            ExperimentVariant(
                id="control",
                name="对照组",
                type=VariantType.CONTROL,
                traffic_percentage=33.3,
                description="现有5步引导流程",
                config={"steps": 5}
            ),
            ExperimentVariant(
                id="treatment_a",
                name="实验组A",
                type=VariantType.TREATMENT,
                traffic_percentage=33.3,
                description="3步引导流程",
                config={"steps": 3}
            ),
            ExperimentVariant(
                id="treatment_b",
                name="实验组B",
                type=VariantType.TREATMENT,
                traffic_percentage=33.4,
                description="单步引导+可跳过",
                config={"steps": 1, "skippable": True}
            )
        ],
        metrics=[
            ExperimentMetric(
                name="onboarding_completion",
                type=MetricType.BINARY,
                description="引导完成率",
                is_primary=True,
                unit="%"
            ),
            ExperimentMetric(
                name="day1_retention",
                type=MetricType.BINARY,
                description="次日留存率",
                is_primary=True,
                unit="%"
            )
        ],
        sample_size=3000,
        min_effect_size=0.08,
        confidence_level=0.95,
        created_by="product_manager"
    )

    ABTestingEngine.create_experiment(sample1)
    ABTestingEngine.create_experiment(sample2)

    logger.info("示例实验已创建")


# ============================================================================
# 初始化
# ============================================================================

def init_ab_testing_engine() -> None:
    """初始化 A/B 测试引擎"""
    create_sample_experiments()
    logger.info("A/B 测试引擎初始化完成")
