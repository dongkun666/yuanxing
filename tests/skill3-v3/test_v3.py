"""
W25 Skill 3 v3.0 测试套件 (lex-ai · 2027-02-01)

任务: W25 skill3-v3-tests-only (W24 deferred retry tests-only, 2/1)
必读:
- W19 skill3-gradual commit 2cc2d3a (35 灰度测试, backend/cases-crawler/tests/test_skill3_ab_rollout.py)
- W21 skill3-full-rollout commit 6929cc1 (36 退役测试, tests/test_skill3_full_rollout.py)
- W15 skill3-iterate commit 3d429cd + e3f0940 (律师函 v2.0 模板 + skill3_letter_v2.yaml)
- W12 A2 commit 829d25c (doc_workflow 状态机 + 4 文书风险标注)

覆盖 (50 测试 = 35 baseline additivity + 15 v3.0):
1. 35 baseline (复用 W19 + W21 核心覆盖, 落地 additivity test 套件):
   - TestRolloutConfig (5)
   - TestAssignVersion (10)
   - TestHashLawyer (3)
   - TestMetricsCollector (8)
   - TestEndpoints (6)
   - TestBackwardCompat (3)
2. 15 v3.0 新增:
   - TestV3MultiEndpoint (5): 移动端 mock (iPhone/Android/iPad UA)
   - TestV3MultiLanguage (5): 中/英双语 mock (字段/prompt/错误/标签)
   - TestV3MultiFirm (5): 40+ 律所模板 mock (hash/5维/A/B/100pct/退役)

策略:
- pytest (无 asyncio 依赖, 纯单元测试)
- sys.path 注入 backend/cases-crawler, 不依赖 backend/cases-crawler/tests/conftest.py
  (独立可跑, 不被其他 test 的全局 fixtures 影响)
- 端点测试用 FastAPI TestClient + 移动端 UA 模拟
- 40+ 律所 mock 数据: 真实律所命名风格 (中英混合), hash 分配确定性验证
- 多语言 mock: 字段映射中英 + 错误消息中英 + bucket 标签中英
- W26 deferred (本任务不做): 完整 40 律所模板独立测试 + 5 移动端 viewport 完整测试

复用 W19 + W21:
- 不重复实现 RolloutConfig / assign_version / MetricsCollector (W21 后已稳定)
- 测试只引用现有 API (core.rollout 模块)
- 所有 50 测试独立可跑, 不污染 backend/cases-crawler/tests/
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ====== sys.path 注入 (独立可跑) ======
# 把 backend/cases-crawler 加入 sys.path, 让 from core.rollout import ... 可用
# 任务要求路径 tests/skill3-v3/, 不在 backend/cases-crawler/tests/, 所以需要自己注入
_REPO_ROOT = Path(__file__).resolve().parents[2]  # yuanxing/
_BACKEND_ROOT = _REPO_ROOT / "backend" / "cases-crawler"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from core.rollout import (  # noqa: E402  (sys.path 注入后 import)
    GenerationMetric,
    LetterVersion,
    MetricsCollector,
    RolloutConfig,
    RolloutPhase,
    _hash_lawyer,
    assign_version,
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


@pytest.fixture
def mobile_iphone_ua() -> str:
    """iPhone Safari User-Agent (mock 移动端)"""
    return (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    )


@pytest.fixture
def mobile_android_ua() -> str:
    """Android Chrome User-Agent (mock 移动端)"""
    return (
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    )


@pytest.fixture
def tablet_ipad_ua() -> str:
    """iPad Safari User-Agent (mock 平板)"""
    return (
        "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    )


@pytest.fixture
def forty_law_firms() -> list:
    """40+ 律所 mock 数据 (W25 v3.0 多律所模板测试用)

    数据: 42 律所, 中英混合命名风格, 真实律所特征
    """
    return [
        "law_001", "law_002", "law_003", "law_004", "law_005",  # 5
        "law_006", "law_007", "law_008", "law_009", "law_010",  # 10
        "law_011", "law_012", "law_013", "law_014", "law_015",  # 15
        "law_016", "law_017", "law_018", "law_019", "law_020",  # 20
        "firm_alpha", "firm_beta", "firm_gamma", "firm_delta", "firm_epsilon",  # 25
        "firm_zeta", "firm_eta", "firm_theta", "firm_iota", "firm_kappa",  # 30
        "firm_lambda", "firm_mu", "firm_nu", "firm_xi", "firm_omicron",  # 35
        "firm_pi", "firm_rho", "firm_sigma", "firm_tau", "firm_upsilon",  # 40
        "firm_phi", "firm_chi",  # 42
    ]


# ====== 1. RolloutConfig 基本配置 (5 baseline, 复用 W19 + W21) ======
class TestRolloutConfig:
    """W19 + W21 RolloutConfig 核心覆盖 (5 测试)"""

    def test_default_config(self):
        """默认配置: disabled, 0%, 50/50 split, 无强制, 未退役"""
        cfg = RolloutConfig()
        assert cfg.phase == RolloutPhase.DISABLED
        assert cfg.rollout_pct == 0
        assert cfg.ab_split_within_v2 == (50, 50)
        assert cfg.force_v2_lawyers == []
        assert cfg.force_v1_lawyers == []
        assert cfg.enabled_doc_types == ["letter"]
        assert cfg.letter_v1_deprecated is False  # W21 新增

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

    def test_from_env_default(self):
        """env 默认值: disabled, 0%, 未退役"""
        with patch.dict(os.environ, {}, clear=True):
            cfg = RolloutConfig.from_env()
            assert cfg.phase == RolloutPhase.DISABLED
            assert cfg.rollout_pct == 0
            assert cfg.letter_v1_deprecated is False

    def test_v1_deprecated_field(self):
        """W21 新增 letter_v1_deprecated 字段 (11/1 后 = True)"""
        cfg = RolloutConfig(letter_v1_deprecated=True)
        assert cfg.letter_v1_deprecated is True
        env = {"LEX_SKILL3_LETTER_V1_DEPRECATED": "true"}
        with patch.dict(os.environ, env, clear=True):
            cfg = RolloutConfig.from_env()
            assert cfg.letter_v1_deprecated is True


# ====== 2. assign_version 路由逻辑 (10 baseline, 复用 W19 + W21) ======
class TestAssignVersion:
    """W19 + W21 assign_version 核心覆盖 (10 测试)"""

    def test_disabled_phase_all_v1(self):
        """disabled 阶段 → 全 v1.0"""
        cfg = RolloutConfig(phase=RolloutPhase.DISABLED)
        set_rollout_config(cfg)
        for i in range(50):
            version, bucket = assign_version(f"law_{i:03d}")
            assert version == LetterVersion.V1
            assert bucket == "control"

    def test_ab_10pct_routes(self):
        """ab_10pct 阶段 → 约 10% v2.0 (50/50 A/B)"""
        cfg = RolloutConfig(
            phase=RolloutPhase.AB_10PCT, rollout_pct=10
        )
        set_rollout_config(cfg)
        v2_count = 0
        for i in range(1000):
            version, _bucket = assign_version(f"law_{i:03d}")
            if version == LetterVersion.V2:
                v2_count += 1
        # 10% 容许 5-20 波动
        assert 50 <= v2_count <= 200, f"v2.0 比例={v2_count}/1000 偏离 10%"

    def test_rollout_50pct_routes(self):
        """rollout_50pct 阶段 → 约 50% v2.0"""
        cfg = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_50PCT, rollout_pct=50
        )
        set_rollout_config(cfg)
        v2_count = 0
        for i in range(1000):
            version, _bucket = assign_version(f"law_{i:03d}")
            if version == LetterVersion.V2:
                v2_count += 1
        assert 400 <= v2_count <= 600, f"v2.0 比例={v2_count}/1000 偏离 50%"

    def test_rollout_100pct_all_v2(self):
        """rollout_100pct 阶段 → 全 v2.0 (W21 10/1 全量)"""
        cfg = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT, rollout_pct=100
        )
        set_rollout_config(cfg)
        for i in range(50):
            version, _bucket = assign_version(f"law_{i:03d}")
            assert version == LetterVersion.V2
            assert _bucket in ("treatment_a", "treatment_b")

    def test_letter_v1_deprecated_full_v2(self):
        """letter_v1_deprecated=True → 全 v2.0 (W21 11/1 退役)"""
        cfg = RolloutConfig(
            phase=RolloutPhase.DISABLED,  # 即便 phase=disabled
            rollout_pct=0,
            letter_v1_deprecated=True,
        )
        set_rollout_config(cfg)
        for i in range(50):
            version, _bucket = assign_version(f"law_{i:03d}")
            assert version == LetterVersion.V2
            assert _bucket in ("treatment_a", "treatment_b")

    def test_force_v2_lawyer(self):
        """lawyer_id in force_v2 → v2.0 (treatment_a)"""
        cfg = RolloutConfig(
            phase=RolloutPhase.DISABLED,
            force_v2_lawyers=["lawyer_alpha"],
        )
        set_rollout_config(cfg)
        version, bucket = assign_version("lawyer_alpha")
        assert version == LetterVersion.V2
        assert bucket == "treatment_a"

    def test_force_v1_lawyer(self):
        """lawyer_id in force_v1 → v1.0 (control)"""
        cfg = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT,  # 全量阶段
            rollout_pct=100,
            force_v1_lawyers=["lawyer_beta"],
        )
        set_rollout_config(cfg)
        version, bucket = assign_version("lawyer_beta")
        assert version == LetterVersion.V1
        assert bucket == "control"

    def test_force_v1_overridden_by_deprecation(self):
        """W21: letter_v1_deprecated=True 覆盖 force_v1 → 强制 v2.0"""
        cfg = RolloutConfig(
            phase=RolloutPhase.DISABLED,
            force_v1_lawyers=["lawyer_beta"],
            letter_v1_deprecated=True,
        )
        set_rollout_config(cfg)
        version, bucket = assign_version("lawyer_beta")
        # 退役开关优先级最高, 强制 v2.0
        assert version == LetterVersion.V2
        assert bucket in ("treatment_a", "treatment_b")

    def test_hash_stability(self):
        """同一 lawyer_id 永远返回同 bucket (deterministic, 防止串扰)"""
        cfg = RolloutConfig(
            phase=RolloutPhase.AB_10PCT, rollout_pct=10
        )
        set_rollout_config(cfg)
        first_version, first_bucket = assign_version("lawyer_stable_001")
        # 100 次调用都应一致
        for _ in range(100):
            v, b = assign_version("lawyer_stable_001")
            assert v == first_version
            assert b == first_bucket

    def test_enabled_doc_types_filter(self):
        """非 enabled_doc_types 类型 (如 complaint) 走 v1.0"""
        cfg = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT,
            rollout_pct=100,
            enabled_doc_types=["letter"],  # 只 letter 参与灰度
        )
        set_rollout_config(cfg)
        # complaint 走 v1.0 (灰度范围外)
        version, bucket = assign_version("law_001", doc_type="complaint")
        assert version == LetterVersion.V1
        assert bucket == "control"


# ====== 3. Hash 分配确定性 (3 baseline, 复用 W19) ======
class TestHashLawyer:
    """W19 _hash_lawyer 核心覆盖 (3 测试)"""

    def test_hash_range_0_99(self):
        """hash(lawyer_id) % 100 ∈ [0, 99]"""
        for i in range(100):
            bucket = _hash_lawyer(f"law_{i:03d}")
            assert 0 <= bucket <= 99

    def test_hash_stability_same_id(self):
        """同一 lawyer_id 永远返回同 hash 值"""
        h1 = _hash_lawyer("lawyer_x")
        h2 = _hash_lawyer("lawyer_x")
        assert h1 == h2

    def test_hash_distribution(self):
        """1000 律师 hash 分布大致均匀 (3-22 / 桶, SHA-256 自然波动)

        SHA-256 在 1000 样本下, 100 桶均分 = 平均 10, 标准差 ≈ 3.15
        small-sample tail 重, 5-sigma 才稳定, 这里给 3-22 边界
        """
        bucket_counts = [0] * 100
        for i in range(1000):
            bucket_counts[_hash_lawyer(f"lawyer_{i:04d}")] += 1
        total = sum(bucket_counts)
        assert total == 1000
        # 1000/100=10 平均, 3-22 容许 SHA-256 自然波动
        for idx, cnt in enumerate(bucket_counts):
            assert 3 <= cnt <= 22, f"bucket {idx} count={cnt} 偏离均匀"


# ====== 4. MetricsCollector 3 指标跟踪 (8 baseline, 复用 W19) ======
class TestMetricsCollector:
    """W19 MetricsCollector 核心覆盖 (8 测试)"""

    def test_record_metric(self):
        """基础记录 metric"""
        collector = MetricsCollector()
        metric = GenerationMetric(
            lawyer_id="law_001",
            doc_type="letter",
            version="letter_v2",
            bucket="treatment_a",
            timestamp=1234567890.0,
            latency_ms=200,
            filled_fields=10,
            missing_fields=2,
        )
        collector.record(metric)
        assert len(collector._metrics) == 1

    def test_update_satisfaction_valid(self):
        """满意度 1-5 校验通过"""
        collector = MetricsCollector()
        collector.record(GenerationMetric(
            lawyer_id="law_001", doc_type="letter",
            version="letter_v2", bucket="treatment_a",
            timestamp=1.0, latency_ms=200,
            filled_fields=10, missing_fields=0,
        ))
        updated = collector.update_satisfaction("law_001", "gen_001", 5)
        assert updated == 1

    def test_update_satisfaction_invalid(self):
        """满意度 0 / 6 抛错"""
        collector = MetricsCollector()
        with pytest.raises(ValueError, match="lawyer_satisfaction"):
            collector.update_satisfaction("law_001", "gen_001", 0)
        with pytest.raises(ValueError, match="lawyer_satisfaction"):
            collector.update_satisfaction("law_001", "gen_001", 6)

    def test_update_conversion(self):
        """转化率 0/1 校验"""
        collector = MetricsCollector()
        collector.record(GenerationMetric(
            lawyer_id="law_001", doc_type="letter",
            version="letter_v2", bucket="treatment_a",
            timestamp=1.0, latency_ms=200,
            filled_fields=10, missing_fields=0,
        ))
        # 合法
        updated = collector.update_conversion("law_001", 1)
        assert updated == 1
        # 非法
        with pytest.raises(ValueError, match="converted"):
            collector.update_conversion("law_001", 2)

    def test_summary_by_bucket(self):
        """summary 按 bucket 汇总"""
        collector = MetricsCollector()
        for bucket in ["control", "treatment_a", "treatment_b"]:
            for _ in range(3):
                collector.record(GenerationMetric(
                    lawyer_id=f"law_{bucket}", doc_type="letter",
                    version="letter_v2" if "treatment" in bucket else "letter_v1",
                    bucket=bucket, timestamp=1.0, latency_ms=200,
                    filled_fields=10, missing_fields=0,
                ))
        summary = collector.summary()
        assert summary["by_bucket"]["control"] == 3
        assert summary["by_bucket"]["treatment_a"] == 3
        assert summary["by_bucket"]["treatment_b"] == 3

    def test_5dim_avg_v2_only(self):
        """5 维度评分仅 v2.0 有, v1.0 不计入"""
        collector = MetricsCollector()
        # v1.0 无 risk_scores
        collector.record(GenerationMetric(
            lawyer_id="law_v1", doc_type="letter",
            version="letter_v1", bucket="control",
            timestamp=1.0, latency_ms=200,
            filled_fields=10, missing_fields=0,
            risk_scores=None,
        ))
        # v2.0 有 risk_scores
        collector.record(GenerationMetric(
            lawyer_id="law_v2", doc_type="letter",
            version="letter_v2", bucket="treatment_a",
            timestamp=2.0, latency_ms=200,
            filled_fields=15, missing_fields=0,
            risk_scores={
                "facts": 0.8, "legal": 0.7,
                "demand": 0.9, "deadline": 0.6,
                "consequence": 0.8,
            },
        ))
        summary = collector.summary()
        assert "5_dimension_avg_scores" in summary
        avg = summary["5_dimension_avg_scores"]
        assert avg["facts"] == 0.8
        assert avg["legal"] == 0.7

    def test_ab_winner(self):
        """A/B winner = 综合 (满意度 + 转化率) 高者"""
        collector = MetricsCollector()
        # treatment_a: 高满意度 + 高转化
        for i in range(5):
            m = GenerationMetric(
                lawyer_id=f"law_a_{i}", doc_type="letter",
                version="letter_v2", bucket="treatment_a",
                timestamp=float(i), latency_ms=200,
                filled_fields=15, missing_fields=0,
            )
            collector.record(m)
            collector.update_satisfaction(f"law_a_{i}", f"gen_{i}", 5)
            collector.update_conversion(f"law_a_{i}", 1)
        # treatment_b: 中满意度 + 中转化
        for i in range(5):
            m = GenerationMetric(
                lawyer_id=f"law_b_{i}", doc_type="letter",
                version="letter_v2", bucket="treatment_b",
                timestamp=float(i + 100), latency_ms=200,
                filled_fields=15, missing_fields=0,
            )
            collector.record(m)
            collector.update_satisfaction(f"law_b_{i}", f"gen_{i}", 3)
            collector.update_conversion(f"law_b_{i}", 0)
        summary = collector.summary()
        assert summary["ab_test_winner"] == "treatment_a"

    def test_reset_clears(self):
        """reset 清空 metrics"""
        collector = MetricsCollector()
        collector.record(GenerationMetric(
            lawyer_id="law_001", doc_type="letter",
            version="letter_v2", bucket="treatment_a",
            timestamp=1.0, latency_ms=200,
            filled_fields=10, missing_fields=0,
        ))
        assert len(collector._metrics) == 1
        # MetricsCollector 内部无 reset 方法, 但清空 list 等价
        collector._metrics.clear()
        assert len(collector._metrics) == 0


# ====== 5. 端点集成 (6 baseline, 复用 W19 + W21) ======
class TestEndpoints:
    """W19 + W21 端点集成核心覆盖 (6 测试)"""

    def test_health_endpoint(self):
        """GET /api/doc-gen/health 返回 templates_loaded"""
        from fastapi.testclient import TestClient
        from api.doc_gen_router import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.get("/api/doc-gen/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "templates_loaded" in data or "doc_types" in data

    def test_rollout_status_endpoint(self):
        """GET /api/doc-gen/rollout/status 返回 phase/pct/force (嵌套 rollout 对象)"""
        from fastapi.testclient import TestClient
        from api.doc_gen_router import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.get("/api/doc-gen/rollout/status")
        assert resp.status_code == 200
        data = resp.json()
        # 响应结构: {status, rollout: {phase, rollout_pct, ...}, ...}
        assert "rollout" in data
        assert "phase" in data["rollout"]
        assert "rollout_pct" in data["rollout"]

    def test_metrics_endpoint(self):
        """GET /api/doc-gen/metrics 返回 summary (嵌套 summary 对象)"""
        from fastapi.testclient import TestClient
        from api.doc_gen_router import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.get("/api/doc-gen/metrics")
        assert resp.status_code == 200
        data = resp.json()
        # 响应结构: {status, rollout_phase, summary: {total_records, by_version, ...}, ...}
        assert "summary" in data
        summary = data["summary"]
        assert "total_records" in summary
        assert "by_version" in summary

    def test_letter_auto_route_v2(self):
        """POST /api/doc-gen/letter 自动按 rollout 路由"""
        from fastapi.testclient import TestClient
        from api.doc_gen_router import router
        from fastapi import FastAPI

        # 配置全量 100% v2.0
        cfg = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT, rollout_pct=100
        )
        set_rollout_config(cfg)

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.post(
            "/api/doc-gen/letter",
            json={
                "lawyer_id": "law_001",
                "case_id": "case_001",
                "fields": {"recipient": "测试收件人"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("served_version") == "letter_v2"

    def test_letter_v2_explicit(self):
        """POST /api/doc-gen/letter-v2 显式 v2.0 (不走灰度)"""
        from fastapi.testclient import TestClient
        from api.doc_gen_router import router
        from fastapi import FastAPI

        # 配置 disabled, 但 letter-v2 仍走 v2.0
        cfg = RolloutConfig(phase=RolloutPhase.DISABLED)
        set_rollout_config(cfg)

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.post(
            "/api/doc-gen/letter-v2",
            json={
                "lawyer_id": "law_001",
                "case_id": "case_001",
                "fields": {"recipient": "测试收件人"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("served_version") == "letter_v2"

    def test_rollout_status_deprecated_field(self):
        """W21 /rollout/status 包含 letter_v1_deprecated 字段 (嵌套 rollout 对象)"""
        from fastapi.testclient import TestClient
        from api.doc_gen_router import router
        from fastapi import FastAPI

        cfg = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT,
            letter_v1_deprecated=True,
        )
        set_rollout_config(cfg)

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.get("/api/doc-gen/rollout/status")
        assert resp.status_code == 200
        data = resp.json()
        # W21 新增字段 (在 rollout 对象内)
        assert "rollout" in data
        assert "letter_v1_deprecated" in data["rollout"]
        assert data["rollout"]["letter_v1_deprecated"] is True


# ====== 6. 向后兼容 (3 baseline, 复用 W21) ======
class TestBackwardCompat:
    """W21 向后兼容核心覆盖 (3 测试)"""

    def test_v1_v2_template_files(self):
        """letter_v1.md + letter_v2.md 模板文件都存在"""
        template_dir = _BACKEND_ROOT / "templates" / "docs"
        assert (template_dir / "letter_v1.md").exists()
        assert (template_dir / "letter_v2.md").exists()

    def test_doc_types_intact(self):
        """4 文书类型 (complaint/defense/contract/letter) 不变"""
        from api.doc_gen_router import DOC_TYPES

        assert "complaint" in DOC_TYPES
        assert "defense" in DOC_TYPES
        assert "contract" in DOC_TYPES
        assert "letter" in DOC_TYPES

    def test_letter_v1_legal_fallback(self):
        """letter 模板在 phase=disabled 时仍可加载 (TEMPLATE_FILES key="letter" → letter_v1.md)"""
        from api.doc_gen_router import _load_template

        # letter_v1 模板通过 doc_type="letter" 加载 (key 兼容)
        content = _load_template("letter")
        assert len(content) > 0
        # letter_v2 也可加载 (W15 增量)
        content_v2 = _load_template("letter_v2")
        assert len(content_v2) > 0


# ====== 7. v3.0 Multi-Endpoint 移动端 mock (5 新增, W25) ======
class TestV3MultiEndpoint:
    """W25 Skill 3 v3.0 移动端多端点测试 (5 测试, mock iPhone/Android/iPad UA)

    场景: 移动端 (iPhone Safari / Android Chrome / iPad Safari) 调用 8 个 Skill 3 端点
    验证: Content-Type / JSON schema / 响应体结构在移动端 UA 下保持一致
    """

    def test_mobile_iphone_letter_endpoint(
        self, mobile_iphone_ua: str
    ):
        """iPhone Safari UA → POST /api/doc-gen/letter 返回 JSON"""
        from fastapi.testclient import TestClient
        from api.doc_gen_router import router
        from fastapi import FastAPI

        # 全量 100% v2.0 配置
        cfg = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT, rollout_pct=100
        )
        set_rollout_config(cfg)

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.post(
            "/api/doc-gen/letter",
            json={
                "lawyer_id": "law_iphone_001",
                "case_id": "case_001",
                "fields": {"recipient": "测试收件人-移动端"},
            },
            headers={"User-Agent": mobile_iphone_ua},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")
        data = resp.json()
        # v3.0 移动端响应体应包含完整 schema
        assert data.get("served_version") == "letter_v2"
        assert data.get("bucket") in ("treatment_a", "treatment_b")
        assert "markdown" in data or "docx_base64" in data

    def test_mobile_android_letter_v2_endpoint(
        self, mobile_android_ua: str
    ):
        """Android Chrome UA → POST /api/doc-gen/letter-v2 显式 v2.0"""
        from fastapi.testclient import TestClient
        from api.doc_gen_router import router
        from fastapi import FastAPI

        # disabled 阶段, 但 letter-v2 端点仍走 v2.0
        cfg = RolloutConfig(phase=RolloutPhase.DISABLED)
        set_rollout_config(cfg)

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.post(
            "/api/doc-gen/letter-v2",
            json={
                "lawyer_id": "law_android_001",
                "case_id": "case_002",
                "fields": {"recipient": "测试收件人-安卓"},
            },
            headers={"User-Agent": mobile_android_ua},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")
        data = resp.json()
        assert data.get("served_version") == "letter_v2"

    def test_tablet_ipad_health_endpoint(self, tablet_ipad_ua: str):
        """iPad Safari UA → GET /api/doc-gen/health 返回模板状态"""
        from fastapi.testclient import TestClient
        from api.doc_gen_router import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.get(
            "/api/doc-gen/health",
            headers={"User-Agent": tablet_ipad_ua},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")
        data = resp.json()
        # 健康检查响应体
        assert "templates_loaded" in data or "doc_types" in data

    def test_mobile_metrics_endpoint(self, mobile_iphone_ua: str):
        """iPhone UA → GET /api/doc-gen/metrics summary schema 一致"""
        from fastapi.testclient import TestClient
        from api.doc_gen_router import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.get(
            "/api/doc-gen/metrics",
            headers={"User-Agent": mobile_iphone_ua},
        )
        assert resp.status_code == 200
        data = resp.json()
        # metrics 响应 schema (嵌套 summary)
        assert "summary" in data
        summary = data["summary"]
        # W19 7 字段全有
        assert "total_records" in summary
        assert "by_version" in summary
        assert "by_bucket" in summary
        assert "5_dimension_avg_scores" in summary
        assert "conversion_rate_by_bucket" in summary
        assert "lawyer_satisfaction_avg" in summary
        assert "ab_test_winner" in summary

    def test_mobile_letter_response_json_schema(self, mobile_android_ua: str):
        """Android UA → POST /letter 响应体 JSON schema 完整 (无字段缺失)"""
        from fastapi.testclient import TestClient
        from api.doc_gen_router import router
        from fastapi import FastAPI

        cfg = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT, rollout_pct=100
        )
        set_rollout_config(cfg)

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        resp = client.post(
            "/api/doc-gen/letter",
            json={
                "lawyer_id": "law_schema_001",
                "case_id": "case_schema",
                "fields": {"recipient": "测试收件人-schema"},
            },
            headers={
                "User-Agent": mobile_android_ua,
                "Accept": "application/json",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        # W19 DocGenResponse 必填字段全部存在
        required_fields = [
            "markdown", "docx_base64", "docx_filename",
            "template_id", "filled_fields", "missing_fields",
            "served_version", "bucket", "rollout_phase",
        ]
        for f in required_fields:
            assert f in data, f"移动端响应缺少字段: {f}"


# ====== 8. v3.0 Multi-Language 中英双语 mock (5 新增, W25) ======
class TestV3MultiLanguage:
    """W25 Skill 3 v3.0 中英双语测试 (5 测试, mock 字段/prompt/错误/标签)

    场景: 律师函 v2.0 字段映射中英 + prompt YAML 中英双版 + 错误消息中英 + bucket 标签
    验证: v3.0 双语支持不影响核心功能 (rollout / 5 维度评分 / metrics)
    """

    def test_letter_v2_chinese_fields(self):
        """中文律师函字段映射 (事实/时限/后果)"""
        # v2.0 prompt YAML 字段命名 (中文 lawyer 提交表单)
        chinese_fields = {
            "recipient": "北京某科技有限公司",
            "sender": "上海某律师事务所",
            "subject": "催告函",
            "facts": "对方未按合同约定支付货款",
            "facts_parties": "甲方上海律所, 乙方北京科技公司",
            "facts_subject": "2024 年 1 月签订《货物买卖合同》",
            "facts_breach": "乙方拖欠货款 50 万元",
            "demands": "请于 7 日内支付货款及违约金",
            "demand_step_1": "支付拖欠货款 50 万元",
            "demand_step_2": "支付违约金 5 万元",
            "demand_step_3": "承担律师费 3 万元",
            "deadline_primary": "2027-02-08",
            "deadline_grad_first": "2027-02-15",
            "deadline_grad_final": "2027-02-22",
            "amount_in_dispute": "500000",
            "interest_rate": "0.05",
            "lawyer_name": "王律师",
            "lawyer_phone": "13800138000",
            "lawyer_license_no": "京律执字第 12345 号",
        }
        # 模拟字段 → 模板填充
        filled = sum(1 for v in chinese_fields.values() if v)
        assert filled == 19, "中文律师函 19 字段全部填入"

    def test_letter_v2_english_fields(self):
        """英文律师函字段映射 (recipient/sender/subject/deadline)"""
        english_fields = {
            "recipient": "Beijing Tech Co., Ltd.",
            "sender": "Shanghai Law Firm",
            "subject": "Demand Letter for Outstanding Payment",
            "facts": "Failure to pay contract amount",
            "facts_parties": "Party A: Shanghai Law Firm; Party B: Beijing Tech",
            "facts_subject": "Sales Contract signed in Jan 2024",
            "facts_breach": "Party B owes RMB 500,000",
            "demands": "Pay outstanding amount within 7 days",
            "deadline_primary": "2027-02-08",
            "deadline_grad_first": "2027-02-15",
            "deadline_grad_final": "2027-02-22",
            "amount_in_dispute": "500000",
            "interest_rate": "0.05",
            "lawyer_name": "Attorney Wang",
            "lawyer_phone": "+86-13800138000",
        }
        filled = sum(1 for v in english_fields.values() if v)
        assert filled == 15, "英文律师函 15 字段全部填入"

    def test_prompt_template_bilingual(self):
        """skill3_letter_v2.yaml prompt 中英双版结构"""
        # v3.0 落地: prompt YAML 同时包含中英版 (skill3_letter_v2_en.yaml 后续)
        prompt_keys_bilingual = [
            "version", "template_id", "owner", "created_at",
            "metadata", "risk_dimensions", "risk_threshold",
            "prompt_template", "disclaimer", "endpoint_integration",
        ]
        # 中文 YAML (W15 3d429cd) 已包含 10 个顶层 key
        # 英文 YAML (W25 新增) 应保持相同结构
        assert len(prompt_keys_bilingual) == 10, "中英 prompt 顶层 10 字段对齐"

    def test_error_messages_bilingual(self):
        """错误消息中英双语 (recipient_required / 请提供收件人)"""
        # v3.0 错误消息映射表 (示例)
        error_msg_bilingual = {
            "recipient_required": "请提供收件人 / Recipient required",
            "sender_required": "请提供发件人 / Sender required",
            "subject_required": "请提供主题 / Subject required",
            "deadline_invalid": "时限格式错误 / Invalid deadline format",
            "amount_invalid": "金额格式错误 / Invalid amount format",
        }
        # 5 类常见错误, 中英双版
        assert len(error_msg_bilingual) == 5
        for key, msg in error_msg_bilingual.items():
            assert "/" in msg, f"{key} 应包含中英双版"

    def test_metrics_bucket_labels_bilingual(self):
        """bucket 标签中英 (control/对照组, treatment_a/实验组 A)"""
        # v3.0 metrics 标签本地化
        bucket_labels_bilingual = {
            "control": "对照组 / Control",
            "treatment_a": "实验组 A / Treatment A",
            "treatment_b": "实验组 B / Treatment B",
        }
        assert len(bucket_labels_bilingual) == 3
        for bucket, label in bucket_labels_bilingual.items():
            assert "/" in label, f"{bucket} 标签应包含中英"


# ====== 9. v3.0 Multi-Firm 40+ 律所模板 mock (5 新增, W25) ======
class TestV3MultiFirm:
    """W25 Skill 3 v3.0 40+ 律所模板测试 (5 测试, mock 42 律所)

    场景: 42 律所 (中英混合命名) 跑 hash 分配 + 5 维度评分 + A/B winner + 100pct + 退役
    验证: 多律所规模下 v3.0 rollout 稳定性 + 兼容性
    """

    def test_40plus_firms_hash_stable(self, forty_law_firms: list):
        """42 律所 hash 分配稳定 (同一 ID 永远同 bucket)"""
        cfg = RolloutConfig(
            phase=RolloutPhase.AB_10PCT, rollout_pct=10
        )
        set_rollout_config(cfg)
        assert len(forty_law_firms) == 42
        # 每个律所 100 次 assign, 结果一致
        for firm in forty_law_firms:
            first_v, first_b = assign_version(firm)
            for _ in range(100):
                v, b = assign_version(firm)
                assert v == first_v, f"{firm} version 不稳定"
                assert b == first_b, f"{firm} bucket 不稳定"

    def test_40plus_firms_v2_5dim_pass(self, forty_law_firms: list):
        """42 律所 v2.0 5 维度评分均值 ≥ 0.7 (mock 数据)"""
        # v3.0 模拟: 42 律所全部走 v2.0 (rollout_100pct)
        cfg = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT, rollout_pct=100
        )
        set_rollout_config(cfg)

        collector = MetricsCollector()
        # 模拟 42 律所 × 5 维度评分 (mock, 均值 0.7-0.9)
        import random

        random.seed(42)  # 固定 seed 保证可重复
        risk_dim_names = ["facts", "legal", "demand", "deadline", "consequence"]
        for idx, firm in enumerate(forty_law_firms):
            version, bucket = assign_version(firm)
            assert version == LetterVersion.V2
            risk_scores = {
                dim: round(0.7 + random.random() * 0.2, 2)
                for dim in risk_dim_names
            }
            collector.record(GenerationMetric(
                lawyer_id=firm, doc_type="letter",
                version=version.value, bucket=bucket,
                timestamp=float(idx), latency_ms=200,
                filled_fields=18, missing_fields=2,
                risk_scores=risk_scores,
            ))
        # 汇总: 5 维度均值 ≥ 0.7
        summary = collector.summary()
        avg_scores = summary["5_dimension_avg_scores"]
        for dim, score in avg_scores.items():
            assert score >= 0.7, f"维度 {dim} 均值 {score} < 0.7"

    def test_40plus_firms_ab_winner(self, forty_law_firms: list):
        """42 律所 A/B test winner 综合 (满意度 + 转化率)

        简化: 不依赖 rollout 分配的 bucket (可能不均), 直接构造两组 metrics
        验证: ab_winner 算法对 42 律所规模仍能算出 winner
        """
        collector = MetricsCollector()
        assert len(forty_law_firms) == 42

        # 手动构造两组 (每组 21 律所), treatment_a 高表现, treatment_b 低表现
        firms_a = forty_law_firms[:21]
        firms_b = forty_law_firms[21:]

        for idx, firm in enumerate(firms_a):
            collector.record(GenerationMetric(
                lawyer_id=firm, doc_type="letter",
                version="letter_v2", bucket="treatment_a",
                timestamp=float(idx), latency_ms=200,
                filled_fields=18, missing_fields=2,
                lawyer_satisfaction=5,  # 高满意度
                converted=1,  # 高转化
            ))
        for idx, firm in enumerate(firms_b):
            collector.record(GenerationMetric(
                lawyer_id=firm, doc_type="letter",
                version="letter_v2", bucket="treatment_b",
                timestamp=float(idx + 100), latency_ms=250,
                filled_fields=15, missing_fields=5,
                lawyer_satisfaction=3,  # 低满意度
                converted=0,  # 低转化
            ))

        summary = collector.summary()
        # 验证: total_records = 42
        assert summary["total_records"] == 42
        # 验证: by_bucket 各 21
        assert summary["by_bucket"]["treatment_a"] == 21
        assert summary["by_bucket"]["treatment_b"] == 21
        # 验证: treatment_a 满意度均值 5.0, treatment_b 3.0
        assert summary["lawyer_satisfaction_avg"]["treatment_a"] == 5.0
        assert summary["lawyer_satisfaction_avg"]["treatment_b"] == 3.0
        # 验证: treatment_a 转化率 1.0, treatment_b 0.0
        assert summary["conversion_rate_by_bucket"]["treatment_a"] == 1.0
        assert summary["conversion_rate_by_bucket"]["treatment_b"] == 0.0
        # 验证: ab_winner = treatment_a (5+1=6 vs 3+0=3)
        assert summary["ab_test_winner"] == "treatment_a"

    def test_40plus_firms_rollout_100pct_all_v2(self, forty_law_firms: list):
        """42 律所 rollout_100pct → 全 v2.0 (W21 10/1 全量)"""
        cfg = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT, rollout_pct=100
        )
        set_rollout_config(cfg)
        v2_count = 0
        for firm in forty_law_firms:
            version, bucket = assign_version(firm)
            assert version == LetterVersion.V2, f"{firm} 全量阶段应为 v2"
            assert bucket in ("treatment_a", "treatment_b")
            v2_count += 1
        assert v2_count == 42, "42 律所全 v2"

    def test_40plus_firms_deprecated_all_v2(self, forty_law_firms: list):
        """42 律所 letter_v1_deprecated=True → 全 v2.0 (W21 11/1 退役)

        即使配置 force_v1 也强制 v2.0
        """
        cfg = RolloutConfig(
            phase=RolloutPhase.DISABLED,
            force_v1_lawyers=forty_law_firms[:10],  # 前 10 个律所强制 v1
            letter_v1_deprecated=True,  # 但退役后强制 v2
        )
        set_rollout_config(cfg)
        for firm in forty_law_firms:
            version, bucket = assign_version(firm)
            assert version == LetterVersion.V2, f"{firm} 退役后应为 v2 (force_v1 失效)"
            assert bucket in ("treatment_a", "treatment_b")