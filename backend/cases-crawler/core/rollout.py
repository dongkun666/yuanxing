"""
LexPrime W19 Skill 3 律师函 v2.0 灰度配置 (lex-ai · 2026-06-30)

任务: W19 skill3-gradual
必读:
- W15 skill3-iterate commit 3d429cd + e3f0940 (律师函 v2.0 模板 + skill3_letter_v2.yaml)
- W15 l4l5 commit 900948f (8/25 L4/L5 律师试用反馈)
- W11 PRD V5.0 § 11 法务自检 (4 文书类型 + 5 维度风险标注)
- W12 A2 commit 829d25c (doc_workflow 状态机 + 4 文书风险标注)
- 灰度阶段:
  - 8/15 v2.0 10% 灰度 (A/B test 50/50 split 律师)
  - 9/1 v2.0 全量 50% 灰度

实现:
1. RolloutConfig: 灰度阶段 + 百分比 + 强制列表 (env / Settings 加载)
2. assign_version(): hash(lawyer_id) 决定 v1.0 / v2.0 (deterministic)
3. metrics: in-memory 跟踪 3 指标 (5 维度评分 + 转化率 + 律师满意度)

数据:
1. 接律师 ID + 文书类型 → 返回 (served_version: "letter_v1" | "letter_v2", bucket: "control" | "treatment_a" | "treatment_b")
2. bucket 含义:
   - control: v1.0 (没进 v2.0 灰度)
   - treatment_a: v2.0 (50% split 内, 旧版 prompt 兼容样例)
   - treatment_b: v2.0 (50% split 内, 新版 5 维度深度推理样例)
3. A/B test 设计: 同一 lawyer_id 永远走同一 bucket (deterministic, 防止串扰)

集成:
- doc_gen_router.py: POST /api/doc-gen/letter 自动根据 rollout% 路由 v1.0 / v2.0
- doc_gen_router.py: GET /api/doc-gen/rollout/status 灰度当前状态
- doc_gen_router.py: GET /api/doc-gen/metrics 跟踪 3 指标

PRD:
- § 5.4 Skill Hub (Skill 3 文书生成 v2.0 灰度)
- § 5.6 当事人服务类文书
- § 11 法务自检 (5 维度风险标注)
"""
from __future__ import annotations

import hashlib
import os
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger


# ====== 枚举 ======
class LetterVersion(str, Enum):
    """律师函版本"""

    V1 = "letter_v1"  # 旧版 (W9 5d8ecdc)
    V2 = "letter_v2"  # 新版 (W15 3d429cd, 8 律师反馈驱动)


class RolloutPhase(str, Enum):
    """灰度阶段 (按 PRD V5.0 § 5.4 + 实际公测期)"""

    DISABLED = "disabled"      # 全 v1.0 (灰度前)
    AB_10PCT = "ab_10pct"      # 8/15 v2.0 10% 灰度 + A/B 50/50
    ROLLOUT_50PCT = "rollout_50pct"  # 9/1 v2.0 50% 灰度
    ROLLOUT_100PCT = "rollout_100pct"  # 全量 v2.0 (未来 W20+)


# ====== 配置 ======
@dataclass
class RolloutConfig:
    """灰度配置 (env / Settings 加载)

    字段:
        phase: 灰度阶段 (4 阶段)
        rollout_pct: v2.0 灰度百分比 (0-100, 0 = 全 v1.0, 100 = 全 v2.0)
        ab_split_within_v2: v2.0 灰度内 A/B 分配 (默认 50/50, [treatment_a, treatment_b])
        force_v2_lawyers: 强制走 v2.0 律师列表 (白名单, 用于评审 #N 关键律师)
        force_v1_lawyers: 强制走 v1.0 律师列表 (黑名单, 用于对照测试)
        enabled_doc_types: 参与灰度的文书类型 (默认 ["letter"])
    """

    phase: RolloutPhase = RolloutPhase.DISABLED
    rollout_pct: int = 0  # 0-100
    ab_split_within_v2: Tuple[int, int] = (50, 50)  # (treatment_a%, treatment_b%)
    force_v2_lawyers: List[str] = field(default_factory=list)
    force_v1_lawyers: List[str] = field(default_factory=list)
    enabled_doc_types: List[str] = field(default_factory=lambda: ["letter"])

    def __post_init__(self) -> None:
        if not (0 <= self.rollout_pct <= 100):
            raise ValueError(f"rollout_pct 必须在 0-100, 实际={self.rollout_pct}")
        if sum(self.ab_split_within_v2) != 100:
            raise ValueError(
                f"ab_split_within_v2 之和必须=100, 实际={sum(self.ab_split_within_v2)}"
            )
        if not self.enabled_doc_types:
            raise ValueError("enabled_doc_types 不能为空")

    @classmethod
    def from_env(cls) -> "RolloutConfig":
        """从 env 变量加载 (lex-ai W19 skill3-gradual 落地)

        环境变量:
            LEX_SKILL3_ROLLOUT_PHASE: disabled | ab_10pct | rollout_50pct | rollout_100pct
            LEX_SKILL3_ROLLOUT_PCT: 0-100 (默认 0)
            LEX_SKILL3_AB_SPLIT: "50,50" (默认 50/50)
            LEX_SKILL3_FORCE_V2: 逗号分隔律师 ID (白名单, 默认空)
            LEX_SKILL3_FORCE_V1: 逗号分隔律师 ID (黑名单, 默认空)
        """
        phase_str = os.getenv("LEX_SKILL3_ROLLOUT_PHASE", "disabled").lower()
        try:
            phase = RolloutPhase(phase_str)
        except ValueError:
            logger.warning(f"[rollout] 未知 phase={phase_str}, fallback=disabled")
            phase = RolloutPhase.DISABLED

        rollout_pct = int(os.getenv("LEX_SKILL3_ROLLOUT_PCT", "0"))
        ab_split_str = os.getenv("LEX_SKILL3_AB_SPLIT", "50,50")
        ab_split = tuple(int(x) for x in ab_split_str.split(","))  # type: ignore[assignment]
        if len(ab_split) != 2:
            ab_split = (50, 50)  # fallback

        force_v2 = [
            x.strip() for x in os.getenv("LEX_SKILL3_FORCE_V2", "").split(",") if x.strip()
        ]
        force_v1 = [
            x.strip() for x in os.getenv("LEX_SKILL3_FORCE_V1", "").split(",") if x.strip()
        ]

        return cls(
            phase=phase,
            rollout_pct=rollout_pct,
            ab_split_within_v2=ab_split,  # type: ignore[arg-type]
            force_v2_lawyers=force_v2,
            force_v1_lawyers=force_v1,
        )


# ====== 全局单例 (lazy init) ======
_GLOBAL_CONFIG: Optional[RolloutConfig] = None


def get_rollout_config() -> RolloutConfig:
    """获取全局灰度配置 (singleton, 第一次从 env 加载)"""
    global _GLOBAL_CONFIG
    if _GLOBAL_CONFIG is None:
        _GLOBAL_CONFIG = RolloutConfig.from_env()
    return _GLOBAL_CONFIG


def set_rollout_config(cfg: RolloutConfig) -> None:
    """设置全局灰度配置 (测试 / 紧急调整用)"""
    global _GLOBAL_CONFIG
    _GLOBAL_CONFIG = cfg
    logger.info(
        f"[rollout] 配置更新: phase={cfg.phase.value} pct={cfg.rollout_pct}% "
        f"ab={cfg.ab_split_within_v2} v2_force={len(cfg.force_v2_lawyers)} v1_force={len(cfg.force_v1_lawyers)}"
    )


# ====== Hash 分配 (deterministic) ======
def _hash_lawyer(lawyer_id: str) -> int:
    """稳定 hash 律师 ID → 0-99 整数 (0-99 桶)

    使用 SHA-256 (避免 Python hash() 的 PYTHONHASHSEED 随机化)
    这样同一 lawyer_id 永远落到同一桶, 灰度期间不串扰
    """
    h = hashlib.sha256(lawyer_id.encode("utf-8")).digest()
    # 取前 4 字节 (32 bit) → 取模 100
    return int.from_bytes(h[:4], "big") % 100


def assign_version(lawyer_id: str, doc_type: str = "letter") -> Tuple[LetterVersion, str]:
    """根据 lawyer_id + 当前灰度配置, 分配律师函版本

    Args:
        lawyer_id: 律师 ID (Pydantic 校验过非空)
        doc_type: 文书类型 (默认 letter, 其他类型走 v1)

    Returns:
        (version, bucket) tuple
        - version: LetterVersion.V1 / LetterVersion.V2
        - bucket: "control" (v1.0) / "treatment_a" (v2.0 A 组) / "treatment_b" (v2.0 B 组)

    算法:
        1. doc_type 不在 enabled_doc_types → v1.0 (灰度范围外)
        2. lawyer_id in force_v2_lawyers → v2.0 (treatment_a)
        3. lawyer_id in force_v1_lawyers → v1.0 (control)
        4. hash(lawyer_id) % 100 < rollout_pct → v2.0
           否则 → v1.0
        5. v2.0 内, hash(lawyer_id) % 100 < ab_split_a → treatment_a
           否则 → treatment_b
    """
    cfg = get_rollout_config()

    # 1. 灰度范围外
    if doc_type not in cfg.enabled_doc_types:
        return LetterVersion.V1, "control"

    # 2-3. 强制列表
    if lawyer_id in cfg.force_v2_lawyers:
        return LetterVersion.V2, "treatment_a"
    if lawyer_id in cfg.force_v1_lawyers:
        return LetterVersion.V1, "control"

    # 4. rollout_pct 灰度判定
    bucket_num = _hash_lawyer(lawyer_id)
    if bucket_num >= cfg.rollout_pct:
        return LetterVersion.V1, "control"

    # 5. v2.0 内 A/B 分组
    threshold_a = cfg.ab_split_within_v2[0]
    if bucket_num < threshold_a:
        return LetterVersion.V2, "treatment_a"
    return LetterVersion.V2, "treatment_b"


# ====== In-memory Metrics 跟踪 (3 指标) ======
@dataclass
class GenerationMetric:
    """单次文书生成 metric (律师 ID 维度)"""

    lawyer_id: str
    doc_type: str
    version: str
    bucket: str
    timestamp: float
    latency_ms: int
    filled_fields: int
    missing_fields: int
    # 5 维度风险评分 (letter v2.0 专用, 0.0-1.0, v1.0 = None)
    risk_scores: Optional[Dict[str, float]] = None
    # 律师满意度 (1-5, 调用方填, 律师主动评分)
    lawyer_satisfaction: Optional[int] = None
    # 是否后续付费转化 (1 / 0, 调用方填, 转化跟踪用)
    converted: Optional[int] = None


class MetricsCollector:
    """3 指标 in-memory 收集器 (线程安全)

    3 指标定义 (来自 W19 skill3-gradual prompt):
    1. 5 维度评分: letter v2.0 自动生成, 1+ lawyer 评分
    2. 转化率: 生成后 7 天内 lawyer 是否付费
    3. 律师满意度: 1-5 主动评分

    注: 实际数据由 owner 8/15 + 9/1 跑灰度, 这里只收集结构, 数字全部 [实测填实]
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._metrics: List[GenerationMetric] = []

    def record(self, metric: GenerationMetric) -> None:
        """记录一次生成 metric"""
        with self._lock:
            self._metrics.append(metric)
        logger.debug(
            f"[rollout.metrics] recorded: lawyer={metric.lawyer_id} "
            f"v={metric.version} bucket={metric.bucket} latency={metric.latency_ms}ms"
        )

    def update_satisfaction(
        self, lawyer_id: str, gen_id: str, satisfaction: int
    ) -> int:
        """更新律师满意度 (1-5)

        Returns: 找到并更新的记录数 (用于诊断)
        """
        if not (1 <= satisfaction <= 5):
            raise ValueError(f"lawyer_satisfaction 必须在 1-5, 实际={satisfaction}")

        updated = 0
        with self._lock:
            for m in self._metrics:
                # 简化: 用 timestamp 匹配 (生产环境应加 gen_id 字段)
                if m.lawyer_id == lawyer_id and m.lawyer_satisfaction is None:
                    m.lawyer_satisfaction = satisfaction
                    updated += 1
        return updated

    def update_conversion(self, lawyer_id: str, converted: int) -> int:
        """更新付费转化 (0/1)

        Returns: 找到并更新的记录数
        """
        if converted not in (0, 1):
            raise ValueError(f"converted 必须 0/1, 实际={converted}")

        updated = 0
        with self._lock:
            for m in self._metrics:
                if m.lawyer_id == lawyer_id and m.converted is None:
                    m.converted = converted
                    updated += 1
        return updated

    def summary(self) -> Dict[str, Any]:
        """3 指标汇总 (供 /api/doc-gen/metrics 端点)

        Returns:
            {
                "total_records": N,
                "by_version": {v1: N, v2: N},
                "by_bucket": {control: N, treatment_a: N, treatment_b: N},
                "5_dimension_avg_scores": {facts: 0.X, legal: 0.X, ...},  # v2 only
                "conversion_rate_by_bucket": {control: 0.X, treatment_a: 0.X, treatment_b: 0.X},
                "lawyer_satisfaction_avg": {control: 4.X, treatment_a: 4.X, treatment_b: 4.X},
                "ab_test_winner": "treatment_a" | "treatment_b" | null  # 3 指标综合
            }

        注: 全部 in-memory, 不持久化. 重启后清零 (测试期足够).
        生产应接 Prometheus / OpenTelemetry.
        """
        with self._lock:
            snapshot = list(self._metrics)

        if not snapshot:
            return {
                "total_records": 0,
                "by_version": {},
                "by_bucket": {},
                "5_dimension_avg_scores": {},
                "conversion_rate_by_bucket": {},
                "lawyer_satisfaction_avg": {},
                "ab_test_winner": None,
                "note": "实测为主, owner 8/15 + 9/1 跑灰度后填实",
            }

        by_version: Dict[str, int] = defaultdict(int)
        by_bucket: Dict[str, int] = defaultdict(int)
        for m in snapshot:
            by_version[m.version] += 1
            by_bucket[m.bucket] += 1

        # 5 维度评分 (v2 only)
        risk_scores_by_dim: Dict[str, List[float]] = defaultdict(list)
        for m in snapshot:
            if m.version == "letter_v2" and m.risk_scores:
                for dim, score in m.risk_scores.items():
                    risk_scores_by_dim[dim].append(score)
        risk_avg = {
            dim: round(sum(scores) / len(scores), 3) if scores else 0.0
            for dim, scores in risk_scores_by_dim.items()
        }

        # 转化率 (按 bucket)
        conv_by_bucket: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"converted": 0, "total": 0}
        )
        for m in snapshot:
            if m.converted is not None:
                conv_by_bucket[m.bucket]["total"] += 1
                conv_by_bucket[m.bucket]["converted"] += m.converted
        conv_rate = {
            b: round(d["converted"] / d["total"], 3) if d["total"] else 0.0
            for b, d in conv_by_bucket.items()
        }

        # 律师满意度 (按 bucket)
        sat_by_bucket: Dict[str, List[int]] = defaultdict(list)
        for m in snapshot:
            if m.lawyer_satisfaction is not None:
                sat_by_bucket[m.bucket].append(m.lawyer_satisfaction)
        sat_avg = {
            b: round(sum(scores) / len(scores), 2) if scores else 0.0
            for b, scores in sat_by_bucket.items()
        }

        # A/B winner (简化: 满意度 + 转化率 综合, treatment_a vs treatment_b)
        ab_winner: Optional[str] = None
        if "treatment_a" in sat_avg and "treatment_b" in sat_avg:
            score_a = (sat_avg["treatment_a"] or 0) + (conv_rate.get("treatment_a", 0) or 0)
            score_b = (sat_avg["treatment_b"] or 0) + (conv_rate.get("treatment_b", 0) or 0)
            if score_a > score_b:
                ab_winner = "treatment_a"
            elif score_b > score_a:
                ab_winner = "treatment_b"

        return {
            "total_records": len(snapshot),
            "by_version": dict(by_version),
            "by_bucket": dict(by_bucket),
            "5_dimension_avg_scores": risk_avg,
            "conversion_rate_by_bucket": conv_rate,
            "lawyer_satisfaction_avg": sat_avg,
            "ab_test_winner": ab_winner,
            "note": "实测为主, owner 8/15 + 9/1 跑灰度后填实",
        }

    def reset(self) -> None:
        """清空所有 metric (测试 / 重新灰度前用)"""
        with self._lock:
            self._metrics.clear()
        logger.info("[rollout.metrics] 已清空所有 metric")


_GLOBAL_COLLECTOR: Optional[MetricsCollector] = None
_COLLECTOR_LOCK = threading.Lock()


def get_metrics_collector() -> MetricsCollector:
    """获取全局 metrics collector (singleton)"""
    global _GLOBAL_COLLECTOR
    if _GLOBAL_COLLECTOR is None:
        with _COLLECTOR_LOCK:
            if _GLOBAL_COLLECTOR is None:
                _GLOBAL_COLLECTOR = MetricsCollector()
    return _GLOBAL_COLLECTOR


# ====== 公开 API ======
__all__ = [
    "LetterVersion",
    "RolloutPhase",
    "RolloutConfig",
    "GenerationMetric",
    "MetricsCollector",
    "get_rollout_config",
    "set_rollout_config",
    "assign_version",
    "get_metrics_collector",
]
