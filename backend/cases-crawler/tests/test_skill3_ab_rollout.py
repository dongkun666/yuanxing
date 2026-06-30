"""
W19 Skill 3 律师函 v2.0 灰度 (A/B test) 单元测试 (lex-ai · 2026-06-30)

任务: W19 skill3-gradual
必读:
- W15 skill3-iterate commit 3d429cd + e3f0940 (律师函 v2.0 模板)
- W11 PRD V5.0 § 11 法务自检 (4 文书类型 + 5 维度风险标注)
- W12 A2 commit 829d25c (doc_workflow 状态机)

覆盖:
1. RolloutConfig 基本配置 (默认值 + env 加载 + 边界检查)
2. assign_version 路由逻辑:
   - disabled 阶段 → 全 v1.0
   - ab_10pct 阶段 → 10% v2.0 (内 50/50 A/B)
   - rollout_50pct 阶段 → 50% v2.0 (内 50/50 A/B)
   - rollout_100pct 阶段 → 全 v2.0
3. force_v1 / force_v2 强制列表覆盖
4. hash 分配确定性 (同一 lawyer_id 永远同 bucket)
5. enabled_doc_types 控制 (非 letter 类型不走灰度)
6. MetricsCollector:
   - record 记录 + 锁安全
   - update_satisfaction (1-5 校验)
   - update_conversion (0/1 校验)
   - summary 按 bucket 汇总
7. 端点集成:
   - GET /api/doc-gen/rollout/status 返回 phase/pct/ab_split/force
   - GET /api/doc-gen/metrics 返回 summary
   - POST /api/doc-gen/letter 自动按 rollout 路由 (served_version + bucket)
   - POST /api/doc-gen/letter-v2 强制 v2.0 (不走灰度)

策略:
- pytest (无 asyncio 依赖, 纯单元测试)
- 不需要数据库 / httpx client (hash + config + dataclass 测试)
- 集成测试用 TestClient
"""
import os
from unittest.mock import patch

import pytest

from core.rollout import (
    GenerationMetric,
    LetterVersion,
    MetricsCollector,
    RolloutConfig,
    RolloutPhase,
    _hash_lawyer,
    assign_version,
    get_metrics_collector,
    set_rollout_config,
)


# ====== Fixtures ======
@pytest.fixture(autouse=True)
def reset_global_state():
    """每个测试前后重置全局配置 + metrics collector"""
    from core import rollout as rollout_mod
    rollout_mod._GLOBAL_CONFIG = None
    rollout_mod._GLOBAL_COLLECTOR = None
    yield
    rollout_mod._GLOBAL_CONFIG = None
    rollout_mod._GLOBAL_COLLECTOR = None


# ====== 1. RolloutConfig 基本配置 ======
class TestRolloutConfig:
    def test_default_config(self):
        """默认配置: disabled, 0%, 50/50 split, 无强制"""
        cfg = RolloutConfig()
        assert cfg.phase == RolloutPhase.DISABLED
        assert cfg.rollout_pct == 0
        assert cfg.ab_split_within_v2 == (50, 50)
        assert cfg.force_v2_lawyers == []
        assert cfg.force_v1_lawyers == []
        assert cfg.enabled_doc_types == ["letter"]

    def test_invalid_rollout_pct(self):
        """rollout_pct 必须在 0-100"""
        with pytest.raises(ValueError, match="rollout_pct"):
            RolloutConfig(rollout_pct=-1)
        with pytest.raises(ValueError, match="rollout_pct"):
            RolloutConfig(rollout_pct=101)

    def test_invalid_ab_split(self):
        """ab_split_within_v2 之和必须=100"""
        with pytest.raises(ValueError, match="ab_split_within_v2"):
            RolloutConfig(ab_split_within_v2=(60, 50))
        with pytest.raises(ValueError, match="ab_split_within_v2"):
            RolloutConfig(ab_split_within_v2=(40, 40))

    def test_enabled_doc_types_required(self):
        """enabled_doc_types 不能为空"""
        with pytest.raises(ValueError, match="enabled_doc_types"):
            RolloutConfig(enabled_doc_types=[])

    def test_from_env_default(self):
        """env 默认值: disabled, 0%"""
        with patch.dict(os.environ, {}, clear=True):
            cfg = RolloutConfig.from_env()
            assert cfg.phase == RolloutPhase.DISABLED
            assert cfg.rollout_pct == 0

    def test_from_env_ab_10pct(self):
        """env: ab_10pct + 10% + 50/50"""
        env = {
            "LEX_SKILL3_ROLLOUT_PHASE": "ab_10pct",
            "LEX_SKILL3_ROLLOUT_PCT": "10",
            "LEX_SKILL3_AB_SPLIT": "50,50",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = RolloutConfig.from_env()
            assert cfg.phase == RolloutPhase.AB_10PCT
            assert cfg.rollout_pct == 10
            assert cfg.ab_split_within_v2 == (50, 50)

    def test_from_env_force_lists(self):
        """env: force_v2 / force_v1 列表解析"""
        env = {
            "LEX_SKILL3_ROLLOUT_PHASE": "ab_10pct",
            "LEX_SKILL3_ROLLOUT_PCT": "10",
            "LEX_SKILL3_FORCE_V2": "L001,L002,L003",
            "LEX_SKILL3_FORCE_V1": "L999",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = RolloutConfig.from_env()
            assert cfg.force_v2_lawyers == ["L001", "L002", "L003"]
            assert cfg.force_v1_lawyers == ["L999"]

    def test_from_env_invalid_phase_fallback(self):
        """env 未知 phase → fallback disabled (不抛错)"""
        env = {"LEX_SKILL3_ROLLOUT_PHASE": "totally_invalid"}
        with patch.dict(os.environ, env, clear=True):
            cfg = RolloutConfig.from_env()
            assert cfg.phase == RolloutPhase.DISABLED


# ====== 2. assign_version 路由逻辑 ======
class TestAssignVersion:
    def test_disabled_phase_all_v1(self):
        """disabled 阶段 → 全 v1.0"""
        set_rollout_config(RolloutConfig(phase=RolloutPhase.DISABLED, rollout_pct=0))
        for i in range(50):
            lawyer_id = f"lawyer_{i:04d}"
            version, bucket = assign_version(lawyer_id)
            assert version == LetterVersion.V1
            assert bucket == "control"

    def test_ab_10pct_10pct_v2(self):
        """ab_10pct 阶段 → ~10% v2.0"""
        cfg = RolloutConfig(phase=RolloutPhase.AB_10PCT, rollout_pct=10)
        set_rollout_config(cfg)

        v2_count = 0
        total = 1000
        for i in range(total):
            lawyer_id = f"lawyer_{i:04d}"
            version, _ = assign_version(lawyer_id)
            if version == LetterVersion.V2:
                v2_count += 1
        # ~10% (允许 5%-15% 波动, 1000 律师样本下)
        assert 50 <= v2_count <= 150, f"期望 ~100 v2, 实际 {v2_count}"

    def test_rollout_50pct_50pct_v2(self):
        """rollout_50pct 阶段 → ~50% v2.0"""
        cfg = RolloutConfig(phase=RolloutPhase.ROLLOUT_50PCT, rollout_pct=50)
        set_rollout_config(cfg)

        v2_count = 0
        total = 1000
        for i in range(total):
            lawyer_id = f"lawyer_{i:04d}"
            version, _ = assign_version(lawyer_id)
            if version == LetterVersion.V2:
                v2_count += 1
        # ~50% (允许 45%-55% 波动)
        assert 450 <= v2_count <= 550, f"期望 ~500 v2, 实际 {v2_count}"

    def test_rollout_100pct_all_v2(self):
        """rollout_100pct 阶段 → 全 v2.0"""
        set_rollout_config(RolloutConfig(phase=RolloutPhase.ROLLOUT_100PCT, rollout_pct=100))
        for i in range(20):
            lawyer_id = f"lawyer_{i:04d}"
            version, bucket = assign_version(lawyer_id)
            assert version == LetterVersion.V2
            assert bucket in ("treatment_a", "treatment_b")

    def test_ab_50_50_split_within_v2(self):
        """v2.0 内 50/50 A/B split"""
        cfg = RolloutConfig(phase=RolloutPhase.ROLLOUT_50PCT, rollout_pct=100)
        set_rollout_config(cfg)

        a_count = 0
        b_count = 0
        total = 1000
        for i in range(total):
            lawyer_id = f"lawyer_{i:04d}"
            _, bucket = assign_version(lawyer_id)
            if bucket == "treatment_a":
                a_count += 1
            elif bucket == "treatment_b":
                b_count += 1
        # ~50/50 (允许 45%-55%)
        assert 450 <= a_count <= 550, f"treatment_a 期望 ~500, 实际 {a_count}"
        assert 450 <= b_count <= 550, f"treatment_b 期望 ~500, 实际 {b_count}"

    def test_force_v2_overrides_rollout(self):
        """force_v2 律师无论 rollout% 多少都走 v2.0"""
        cfg = RolloutConfig(
            phase=RolloutPhase.DISABLED, rollout_pct=0, force_v2_lawyers=["L001", "L002"]
        )
        set_rollout_config(cfg)
        for lid in ["L001", "L002"]:
            version, bucket = assign_version(lid)
            assert version == LetterVersion.V2
            assert bucket == "treatment_a"  # force_v2 默认 treatment_a

    def test_force_v1_overrides_rollout(self):
        """force_v1 律师无论 rollout% 多少都走 v1.0"""
        cfg = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT,
            rollout_pct=100,
            force_v1_lawyers=["L999"],
        )
        set_rollout_config(cfg)
        version, bucket = assign_version("L999")
        assert version == LetterVersion.V1
        assert bucket == "control"

    def test_force_v2_higher_priority_than_force_v1(self):
        """force_v2 优先于 force_v1 (L001 在两个列表里)"""
        cfg = RolloutConfig(
            phase=RolloutPhase.DISABLED,
            rollout_pct=0,
            force_v1_lawyers=["L001"],
            force_v2_lawyers=["L001"],
        )
        set_rollout_config(cfg)
        version, _ = assign_version("L001")
        assert version == LetterVersion.V2  # force_v2 优先

    def test_deterministic_hash_assignment(self):
        """同一 lawyer_id 永远同 bucket (deterministic)"""
        cfg = RolloutConfig(phase=RolloutPhase.ROLLOUT_50PCT, rollout_pct=50)
        set_rollout_config(cfg)
        for i in range(50):
            lawyer_id = f"lawyer_{i:04d}"
            v1, b1 = assign_version(lawyer_id)
            v2, b2 = assign_version(lawyer_id)
            v3, b3 = assign_version(lawyer_id)
            assert v1 == v2 == v3
            assert b1 == b2 == b3

    def test_enabled_doc_types_filters(self):
        """enabled_doc_types 外的文书类型不走灰度"""
        cfg = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT,
            rollout_pct=100,
            enabled_doc_types=["letter"],
        )
        set_rollout_config(cfg)
        # complaint 不在 enabled_doc_types → 走 v1.0 (虽然 rollout 100%)
        version, bucket = assign_version("lawyer_0001", doc_type="complaint")
        assert version == LetterVersion.V1
        assert bucket == "control"


# ====== 3. Hash 函数单元测试 ======
class TestHashLawyer:
    def test_hash_deterministic(self):
        """hash 同一输入永远同输出"""
        assert _hash_lawyer("lawyer_0001") == _hash_lawyer("lawyer_0001")
        assert _hash_lawyer("L001") == _hash_lawyer("L001")

    def test_hash_range_0_99(self):
        """hash 输出 0-99 整数"""
        for i in range(100):
            h = _hash_lawyer(f"lawyer_{i:04d}")
            assert 0 <= h <= 99

    def test_hash_distribution(self):
        """hash 大致均匀分布 (1000 律师样本下 0-99 桶均分)"""
        from collections import Counter

        counts = Counter()
        for i in range(1000):
            counts[_hash_lawyer(f"lawyer_{i:04d}")] += 1
        # 每个桶 1000/100 = 10 次, 允许 5-15 波动
        for bucket_id, count in counts.items():
            assert 5 <= count <= 20, f"bucket {bucket_id} count={count} 偏离过大"


# ====== 4. MetricsCollector ======
class TestMetricsCollector:
    def test_record_and_summary_empty(self):
        """空 collector summary 不报错"""
        c = MetricsCollector()
        s = c.summary()
        assert s["total_records"] == 0
        assert s["by_version"] == {}
        assert s["ab_test_winner"] is None
        assert "实测为主" in s["note"]

    def test_record_and_summary_basic(self):
        """基本 record + summary"""
        c = MetricsCollector()
        c.record(
            GenerationMetric(
                lawyer_id="L001",
                doc_type="letter_v2",
                version="letter_v2",
                bucket="treatment_a",
                timestamp=1.0,
                latency_ms=100,
                filled_fields=10,
                missing_fields=2,
            )
        )
        c.record(
            GenerationMetric(
                lawyer_id="L002",
                doc_type="letter_v1",
                version="letter_v1",
                bucket="control",
                timestamp=2.0,
                latency_ms=120,
                filled_fields=8,
                missing_fields=4,
            )
        )
        s = c.summary()
        assert s["total_records"] == 2
        assert s["by_version"] == {"letter_v2": 1, "letter_v1": 1}
        assert s["by_bucket"] == {"treatment_a": 1, "control": 1}

    def test_record_risk_scores_v2_only(self):
        """5 维度评分只在 v2.0 收集"""
        c = MetricsCollector()
        c.record(
            GenerationMetric(
                lawyer_id="L001",
                doc_type="letter_v2",
                version="letter_v2",
                bucket="treatment_a",
                timestamp=1.0,
                latency_ms=100,
                filled_fields=10,
                missing_fields=0,
                risk_scores={"facts": 0.8, "legal": 0.6, "demand": 0.7, "deadline": 0.5, "consequence": 0.9},
            )
        )
        c.record(
            GenerationMetric(
                lawyer_id="L002",
                doc_type="letter_v1",
                version="letter_v1",
                bucket="control",
                timestamp=2.0,
                latency_ms=120,
                filled_fields=8,
                missing_fields=0,
                # v1 没有 risk_scores
            )
        )
        s = c.summary()
        # 只算 v2.0 的
        assert s["5_dimension_avg_scores"]["facts"] == 0.8
        assert s["5_dimension_avg_scores"]["legal"] == 0.6

    def test_update_satisfaction_validation(self):
        """update_satisfaction 必须在 1-5"""
        c = MetricsCollector()
        c.record(
            GenerationMetric(
                lawyer_id="L001",
                doc_type="letter_v2",
                version="letter_v2",
                bucket="treatment_a",
                timestamp=1.0,
                latency_ms=100,
                filled_fields=10,
                missing_fields=0,
            )
        )
        with pytest.raises(ValueError, match="1-5"):
            c.update_satisfaction("L001", "gen-1", 0)
        with pytest.raises(ValueError, match="1-5"):
            c.update_satisfaction("L001", "gen-1", 6)

    def test_update_conversion_validation(self):
        """update_converted 必须 0/1"""
        c = MetricsCollector()
        c.record(
            GenerationMetric(
                lawyer_id="L001",
                doc_type="letter_v2",
                version="letter_v2",
                bucket="treatment_a",
                timestamp=1.0,
                latency_ms=100,
                filled_fields=10,
                missing_fields=0,
            )
        )
        with pytest.raises(ValueError, match="0/1"):
            c.update_conversion("L001", 2)

    def test_ab_test_winner(self):
        """A/B winner = 综合评分 (满意度 + 转化率) 高者"""
        c = MetricsCollector()
        # treatment_a: 满意度 5, 转化率 100%
        c.record(
            GenerationMetric(
                lawyer_id="A1",
                doc_type="letter_v2",
                version="letter_v2",
                bucket="treatment_a",
                timestamp=1.0,
                latency_ms=100,
                filled_fields=10,
                missing_fields=0,
                lawyer_satisfaction=5,
                converted=1,
            )
        )
        # treatment_b: 满意度 4, 转化率 50%
        c.record(
            GenerationMetric(
                lawyer_id="B1",
                doc_type="letter_v2",
                version="letter_v2",
                bucket="treatment_b",
                timestamp=2.0,
                latency_ms=100,
                filled_fields=10,
                missing_fields=0,
                lawyer_satisfaction=4,
                converted=0,
            )
        )
        s = c.summary()
        # treatment_a: 5+1=6, treatment_b: 4+0=4 → a 胜
        assert s["ab_test_winner"] == "treatment_a"

    def test_reset(self):
        """reset 清空所有 metric"""
        c = MetricsCollector()
        c.record(
            GenerationMetric(
                lawyer_id="L001",
                doc_type="letter_v2",
                version="letter_v2",
                bucket="treatment_a",
                timestamp=1.0,
                latency_ms=100,
                filled_fields=10,
                missing_fields=0,
            )
        )
        assert c.summary()["total_records"] == 1
        c.reset()
        assert c.summary()["total_records"] == 0

    def test_global_collector_singleton(self):
        """get_metrics_collector 返回单例"""
        c1 = get_metrics_collector()
        c2 = get_metrics_collector()
        assert c1 is c2


# ====== 5. 端点集成测试 (用 TestClient) ======
class TestEndpointsIntegration:
    """端点集成: /rollout/status + /metrics + /letter 自动路由

    注: 复用 test_skill3_letter_v2.py 的 in-memory SQLite + StaticPool fixture
    这里只测路由 / metric 记录, 不测完整文档生成内容
    """

    @pytest.fixture
    def client(self):
        """FastAPI TestClient (纯路由测试, 不需要 DB)

        rollout/status + metrics 端点不依赖 DB, 只测路由
        letter / letter-v2 端点用 letter-v2 (避免 doc_workflow 副作用)
        """
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)

    def test_rollout_status_endpoint(self, client):
        """GET /api/doc-gen/rollout/status 返回 phase/pct/ab_split/force"""
        set_rollout_config(
            RolloutConfig(
                phase=RolloutPhase.AB_10PCT,
                rollout_pct=10,
                force_v2_lawyers=["L001", "L002"],
            )
        )
        r = client.get("/api/doc-gen/rollout/status")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["rollout"]["phase"] == "ab_10pct"
        assert data["rollout"]["rollout_pct"] == 10
        assert data["rollout"]["ab_split_within_v2"] == [50, 50]
        assert data["rollout"]["force_v2_lawyers"] == ["L001", "L002"]
        assert "phases_legend" in data["rollout"]
        assert "env_overrides" in data["rollout"]

    def test_metrics_endpoint_empty(self, client):
        """GET /api/doc-gen/metrics 空状态"""
        r = client.get("/api/doc-gen/metrics")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["summary"]["total_records"] == 0
        assert data["summary"]["ab_test_winner"] is None
        assert "实测为主" in data["summary"]["note"]

    def test_letter_auto_routing_disabled(self, client):
        """disabled 阶段: /letter 全走 v1.0"""
        set_rollout_config(RolloutConfig(phase=RolloutPhase.DISABLED, rollout_pct=0))
        r = client.post(
            "/api/doc-gen/letter",
            json={
                "lawyer_id": "lawyer_0001",
                "fields": {"sender": "张律师", "recipient": "李四"},
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["served_version"] == "letter_v1"
        assert data["bucket"] == "control"
        assert data["rollout_phase"] == "disabled"

    def test_letter_v2_explicit_forces_v2(self, client):
        """POST /api/doc-gen/letter-v2 强制 v2.0 (不走灰度)"""
        set_rollout_config(RolloutConfig(phase=RolloutPhase.DISABLED, rollout_pct=0))
        r = client.post(
            "/api/doc-gen/letter-v2",
            json={
                "lawyer_id": "lawyer_0001",
                "fields": {"sender": "张律师", "recipient": "李四"},
            },
        )
        assert r.status_code == 200
        data = r.json()
        # letter-v2 端点不参与灰度, bucket = "explicit"
        assert data["served_version"] == "letter_v2"
        assert data["bucket"] == "explicit"

    def test_letter_auto_routing_ab_10pct(self, client):
        """ab_10pct 阶段: ~10% 律师走 v2.0"""
        set_rollout_config(RolloutConfig(phase=RolloutPhase.AB_10PCT, rollout_pct=10))
        v2_count = 0
        total = 200
        for i in range(total):
            r = client.post(
                "/api/doc-gen/letter",
                json={
                    "lawyer_id": f"lawyer_{i:04d}",
                    "fields": {"sender": "张", "recipient": "李"},
                },
            )
            if r.status_code == 200 and r.json()["served_version"] == "letter_v2":
                v2_count += 1
        # ~10% 律师
        assert 5 <= v2_count <= 35, f"期望 ~20 v2, 实际 {v2_count}"

    def test_metrics_recorded_after_letter_generation(self, client):
        """生成 letter 后 metrics 计数 +1"""
        set_rollout_config(RolloutConfig(phase=RolloutPhase.DISABLED, rollout_pct=0))
        r0 = client.get("/api/doc-gen/metrics")
        assert r0.json()["summary"]["total_records"] == 0

        # 显式 v2.0 (避免灰度影响, 用 letter-v2)
        r1 = client.post(
            "/api/doc-gen/letter-v2",
            json={"lawyer_id": "L_TEST", "fields": {}},
        )
        assert r1.status_code == 200

        r2 = client.get("/api/doc-gen/metrics")
        assert r2.json()["summary"]["total_records"] == 1
        assert r2.json()["summary"]["by_version"].get("letter_v2") == 1
        assert r2.json()["summary"]["by_bucket"].get("explicit") == 1
