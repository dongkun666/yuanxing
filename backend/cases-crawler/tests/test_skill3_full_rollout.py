"""
W21 Skill 3 律师函 v2.0 全量 100% rollout + 11/1 v1.0 退役 单元测试 (lex-ai · 2026-06-30)

任务: W21 skill3-full-rollout
必读:
- W19 skill3-gradual commit 2cc2d3a (35 灰度测试 + rollout.py 模块)
- W15 skill3-iterate commit 3d429cd + e3f0940 (律师函 v2.0 模板 + skill3_letter_v2.yaml)
- W12 A2 commit 829d25c (doc_workflow 状态机 + 4 文书风险标注)
- W11 PRD V5.0 § 5.4 Skill Hub + § 5.6 当事人服务类文书

覆盖:
1. RolloutConfig 新增字段:
   - letter_v1_deprecated (bool, 默认 False) - 11/1 v1.0 退役开关
   - from_env() 加载 LEX_SKILL3_LETTER_V1_DEPRECATED
2. rollout_100pct 大样本 (200+ 律师) 验证 100% v2.0:
   - 全部返回 LetterVersion.V2
   - bucket 全在 (treatment_a / treatment_b) 范围内
   - rollout_pct=100 时所有律师均走 v2.0
3. 11/1 v1.0 退役逻辑 (letter_v1_deprecated=True):
   - 即使 force_v1_lawyers 也强制 v2.0
   - rollout_pct=0 时仍全 v2.0 (退役开关优先级最高)
   - rollout_pct=100 时全 v2.0 (双保险)
   - enabled_doc_types 外的类型 (如 complaint) 不受影响
4. rollout_100pct + letter_v1_deprecated=False (10/1 全量 100%, 但 v1 仍可用):
   - force_v1 律师仍走 v1 (向后兼容)
   - 其他律师全 v2
5. 端点集成 (TestClient):
   - GET /rollout/status 返回 letter_v1_deprecated + deprecated_after_date + backward_compat_note
   - POST /letter 在 rollout_100pct 时全 v2
   - POST /letter 在 letter_v1_deprecated=True 时全 v2 (即使 force_v1)
   - POST /letter-v2 不变 (显式 v2, 不走灰度)
6. 兼容性:
   - 现有 v1.0 文书数据保留 (W12 A2 doc_workflow 不动)
   - 4 文书类型 (complaint/defense/contract/letter) 不变
   - letter_v1 模板文件保留 (供历史数据查询)

策略:
- 复用 test_skill3_ab_rollout.py 的纯单元测试模式 (无 DB, 无 asyncio)
- 端点测试用 FastAPI TestClient (与 W19 一致)
- 100+ 律师大样本验证稳定性
"""
import os
from unittest.mock import patch

import pytest

from core.rollout import (
    LetterVersion,
    MetricsCollector,
    RolloutConfig,
    RolloutPhase,
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


# ====== 1. RolloutConfig 新增字段 (letter_v1_deprecated) ======
class TestRolloutConfigV1Deprecated:
    """W21 新增字段 letter_v1_deprecated 单元测试"""

    def test_default_no_deprecation(self):
        """默认 letter_v1_deprecated=False (10/1 之前)"""
        cfg = RolloutConfig()
        assert cfg.letter_v1_deprecated is False

    def test_deprecated_flag_init(self):
        """letter_v1_deprecated=True (11/1 之后)"""
        cfg = RolloutConfig(letter_v1_deprecated=True)
        assert cfg.letter_v1_deprecated is True

    def test_from_env_deprecated_false(self):
        """env 未设置 → 默认 False"""
        with patch.dict(os.environ, {}, clear=True):
            cfg = RolloutConfig.from_env()
            assert cfg.letter_v1_deprecated is False

    def test_from_env_deprecated_true(self):
        """env: LEX_SKILL3_LETTER_V1_DEPRECATED=true"""
        env = {"LEX_SKILL3_LETTER_V1_DEPRECATED": "true"}
        with patch.dict(os.environ, env, clear=True):
            cfg = RolloutConfig.from_env()
            assert cfg.letter_v1_deprecated is True

    def test_from_env_deprecated_one(self):
        """env: LEX_SKILL3_LETTER_V1_DEPRECATED=1"""
        env = {"LEX_SKILL3_LETTER_V1_DEPRECATED": "1"}
        with patch.dict(os.environ, env, clear=True):
            cfg = RolloutConfig.from_env()
            assert cfg.letter_v1_deprecated is True

    def test_from_env_deprecated_yes(self):
        """env: LEX_SKILL3_LETTER_V1_DEPRECATED=yes"""
        env = {"LEX_SKILL3_LETTER_V1_DEPRECATED": "yes"}
        with patch.dict(os.environ, env, clear=True):
            cfg = RolloutConfig.from_env()
            assert cfg.letter_v1_deprecated is True

    def test_from_env_deprecated_false_string(self):
        """env: LEX_SKILL3_LETTER_V1_DEPRECATED=false (显式 false)"""
        env = {"LEX_SKILL3_LETTER_V1_DEPRECATED": "false"}
        with patch.dict(os.environ, env, clear=True):
            cfg = RolloutConfig.from_env()
            assert cfg.letter_v1_deprecated is False

    def test_combined_with_rollout_100pct(self):
        """rollout_100pct + letter_v1_deprecated=True (10/1 期间可临时开启)"""
        cfg = RolloutConfig.from_env() if False else RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT,
            rollout_pct=100,
            letter_v1_deprecated=True,
        )
        assert cfg.phase == RolloutPhase.ROLLOUT_100PCT
        assert cfg.rollout_pct == 100
        assert cfg.letter_v1_deprecated is True


# ====== 2. rollout_100pct 大样本验证 (200+ 律师) ======
class TestRollout100PctLargeSample:
    """10/1 全量 100% 阶段: 大样本验证 100% v2.0"""

    def test_100pct_200_lawyers_all_v2(self):
        """rollout_100pct 阶段 + 200 律师样本 → 100% LetterVersion.V2"""
        cfg = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT,
            rollout_pct=100,
        )
        set_rollout_config(cfg)

        v1_count = 0
        v2_count = 0
        total = 200
        for i in range(total):
            lawyer_id = f"lawyer_{i:04d}"
            version, _ = assign_version(lawyer_id)
            if version == LetterVersion.V1:
                v1_count += 1
            else:
                v2_count += 1
        # 200/200 全部 v2
        assert v1_count == 0, f"rollout_100pct 不应有 v1, 实际 {v1_count}"
        assert v2_count == total, f"期望 {total} v2, 实际 {v2_count}"

    def test_100pct_bucket_distribution(self):
        """rollout_100pct + ab_split=50/50 → ~50% treatment_a + ~50% treatment_b"""
        cfg = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT,
            rollout_pct=100,
            ab_split_within_v2=(50, 50),
        )
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
            else:
                pytest.fail(f"rollout_100pct 不应有 bucket={bucket} (非 treatment_a/b)")
        # ~50/50 (允许 45%-55%)
        assert 450 <= a_count <= 550, f"treatment_a 期望 ~500, 实际 {a_count}"
        assert 450 <= b_count <= 550, f"treatment_b 期望 ~500, 实际 {b_count}"

    def test_100pct_no_control_bucket(self):
        """rollout_100pct 阶段不应出现 control bucket"""
        cfg = RolloutConfig(phase=RolloutPhase.ROLLOUT_100PCT, rollout_pct=100)
        set_rollout_config(cfg)

        for i in range(100):
            lawyer_id = f"lawyer_{i:04d}"
            version, bucket = assign_version(lawyer_id)
            assert bucket != "control", f"rollout_100pct 不应有 control bucket, 实际={bucket}"
            assert bucket in ("treatment_a", "treatment_b")

    def test_100pct_deterministic_hash(self):
        """rollout_100pct 阶段 + hash 稳定 (同一 lawyer_id 永远同 bucket)"""
        cfg = RolloutConfig(phase=RolloutPhase.ROLLOUT_100PCT, rollout_pct=100)
        set_rollout_config(cfg)

        for i in range(50):
            lawyer_id = f"lawyer_{i:04d}"
            v1, b1 = assign_version(lawyer_id)
            v2, b2 = assign_version(lawyer_id)
            v3, b3 = assign_version(lawyer_id)
            assert v1 == v2 == v3 == LetterVersion.V2
            assert b1 == b2 == b3

    def test_100pct_force_v1_overridden(self):
        """rollout_100pct + force_v1 律师: W19 设计 force_v1 优先级高于 phase=100% 的 hash 判定
        (W19 实现: force_v1 在 hash 判定前 return, 所以即便 phase=100% 也走 v1)
        W21 退役开关 (letter_v1_deprecated=True) 才能覆盖 force_v1
        """
        cfg = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT,
            rollout_pct=100,
            force_v1_lawyers=["L999"],
        )
        set_rollout_config(cfg)
        # rollout 100% + force_v1: W19 设计 → L999 走 v1 (force 优先级)
        version, _ = assign_version("L999")
        assert version == LetterVersion.V1, "W19 设计: force_v1 优先级高于 hash 判定"
        # 其他律师走 v2 (rollout 100%)
        version, _ = assign_version("lawyer_0001")
        assert version == LetterVersion.V2

    def test_100pct_with_deprecation_force_v1_overridden(self):
        """rollout_100pct + letter_v1_deprecated=True + force_v1: 退役开关优先级最高, 强制 v2"""
        cfg = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT,
            rollout_pct=100,
            force_v1_lawyers=["L999"],
            letter_v1_deprecated=True,  # W21 11/1 退役后
        )
        set_rollout_config(cfg)
        version, bucket = assign_version("L999")
        assert version == LetterVersion.V2
        assert bucket in ("treatment_a", "treatment_b")


# ====== 3. 11/1 v1.0 退役逻辑 ======
class TestLetterV1Deprecation:
    """W21 11/1 v1.0 退役逻辑 (letter_v1_deprecated=True)"""

    def test_deprecated_force_v1_overridden(self):
        """letter_v1_deprecated=True: 即使 force_v1 也强制 v2.0"""
        cfg = RolloutConfig(
            phase=RolloutPhase.DISABLED,  # 即使 phase 关闭
            rollout_pct=0,
            force_v1_lawyers=["L999"],
            letter_v1_deprecated=True,
        )
        set_rollout_config(cfg)
        version, bucket = assign_version("L999")
        assert version == LetterVersion.V2, "退役开关应覆盖 force_v1"
        assert bucket in ("treatment_a", "treatment_b")

    def test_deprecated_disabled_phase_still_v2(self):
        """letter_v1_deprecated=True + phase=disabled + rollout_pct=0 → 全 v2"""
        cfg = RolloutConfig(
            phase=RolloutPhase.DISABLED,
            rollout_pct=0,
            letter_v1_deprecated=True,
        )
        set_rollout_config(cfg)

        for i in range(50):
            lawyer_id = f"lawyer_{i:04d}"
            version, _ = assign_version(lawyer_id)
            assert version == LetterVersion.V2, "退役后 phase=disabled 也强制 v2"

    def test_deprecated_priority_over_force_lists(self):
        """退役开关优先级最高: 优于 force_v1 / force_v2 / hash 判定"""
        cfg = RolloutConfig(
            phase=RolloutPhase.DISABLED,
            rollout_pct=0,
            force_v1_lawyers=["L001"],
            force_v2_lawyers=["L002"],
            letter_v1_deprecated=True,
        )
        set_rollout_config(cfg)
        # L001 在 force_v1, 但退役后强制 v2
        v1, b1 = assign_version("L001")
        assert v1 == LetterVersion.V2
        # L002 在 force_v2, 仍走 v2 (treatment_a 默认, 但退役后用 hash 判定)
        v2, b2 = assign_version("L002")
        assert v2 == LetterVersion.V2
        # 都进入 hash 判定的 v2 bucket (treatment_a 或 treatment_b)
        assert b1 in ("treatment_a", "treatment_b")
        assert b2 in ("treatment_a", "treatment_b")

    def test_deprecated_letter_only(self):
        """退役只影响 letter 类型: complaint / defense / contract 不受影响"""
        cfg = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT,
            rollout_pct=100,
            letter_v1_deprecated=True,
            enabled_doc_types=["letter"],  # 灰度范围
        )
        set_rollout_config(cfg)
        # complaint 不在 enabled_doc_types → 灰度范围外 → v1.0 (退役不影响)
        version, bucket = assign_version("lawyer_0001", doc_type="complaint")
        assert version == LetterVersion.V1
        assert bucket == "control"
        # defense 同理
        version, bucket = assign_version("lawyer_0001", doc_type="defense")
        assert version == LetterVersion.V1

    def test_deprecated_with_rollout_100pct_double_safety(self):
        """rollout_100pct + letter_v1_deprecated=True: 双保险全 v2"""
        cfg = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT,
            rollout_pct=100,
            letter_v1_deprecated=True,
        )
        set_rollout_config(cfg)
        for i in range(100):
            lawyer_id = f"lawyer_{i:04d}"
            version, bucket = assign_version(lawyer_id)
            assert version == LetterVersion.V2
            assert bucket in ("treatment_a", "treatment_b")

    def test_deprecated_default_false_preserves_v1(self):
        """letter_v1_deprecated=False (默认): 现有 v1 行为不变"""
        cfg = RolloutConfig(
            phase=RolloutPhase.DISABLED,
            rollout_pct=0,
            # letter_v1_deprecated 默认 False, 不传
        )
        set_rollout_config(cfg)
        version, bucket = assign_version("lawyer_0001")
        assert version == LetterVersion.V1
        assert bucket == "control"


# ====== 4. 端点集成 (TestClient) ======
class TestEndpointsFullRollout:
    """端点集成: rollout_100pct + v1.0 退役"""

    @pytest.fixture
    def client(self):
        """FastAPI TestClient (纯路由测试, 不需要 DB)"""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)

    def test_rollout_status_includes_deprecation_fields(self, client):
        """GET /rollout/status 返回 letter_v1_deprecated + deprecated_after_date"""
        set_rollout_config(
            RolloutConfig(
                phase=RolloutPhase.ROLLOUT_100PCT,
                rollout_pct=100,
                letter_v1_deprecated=True,
            )
        )
        r = client.get("/api/doc-gen/rollout/status")
        assert r.status_code == 200
        data = r.json()
        assert data["rollout"]["letter_v1_deprecated"] is True
        assert data["rollout"]["deprecated_after_date"] == "2026-11-01"
        assert "W12 A2 doc_workflow" in data["rollout"]["backward_compat_note"]
        assert data["rollout"]["env_overrides"]["LEX_SKILL3_LETTER_V1_DEPRECATED"] is True

    def test_rollout_status_phase_100pct(self, client):
        """GET /rollout/status phase=rollout_100pct"""
        set_rollout_config(
            RolloutConfig(phase=RolloutPhase.ROLLOUT_100PCT, rollout_pct=100)
        )
        r = client.get("/api/doc-gen/rollout/status")
        data = r.json()
        assert data["rollout"]["phase"] == "rollout_100pct"
        assert data["rollout"]["rollout_pct"] == 100

    def test_letter_endpoint_100pct_all_v2(self, client):
        """POST /letter 在 rollout_100pct 时所有律师全 v2.0"""
        set_rollout_config(
            RolloutConfig(phase=RolloutPhase.ROLLOUT_100PCT, rollout_pct=100)
        )
        for i in range(20):
            r = client.post(
                "/api/doc-gen/letter",
                json={
                    "lawyer_id": f"lawyer_{i:04d}",
                    "fields": {"sender": "张律师", "recipient": "李四"},
                },
            )
            assert r.status_code == 200
            data = r.json()
            assert data["served_version"] == "letter_v2", f"lawyer_{i:04d} 应走 v2"
            assert data["bucket"] in ("treatment_a", "treatment_b")
            assert data["rollout_phase"] == "rollout_100pct"

    def test_letter_endpoint_v1_deprecated_all_v2(self, client):
        """POST /letter 在 letter_v1_deprecated=True 时即使 force_v1 也全 v2"""
        set_rollout_config(
            RolloutConfig(
                phase=RolloutPhase.DISABLED,
                rollout_pct=0,
                force_v1_lawyers=["L999"],
                letter_v1_deprecated=True,
            )
        )
        # L999 在 force_v1, 但退役开关强制 v2
        r = client.post(
            "/api/doc-gen/letter",
            json={"lawyer_id": "L999", "fields": {"sender": "张", "recipient": "李"}},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["served_version"] == "letter_v2"
        assert data["bucket"] in ("treatment_a", "treatment_b")

    def test_letter_v2_endpoint_unchanged(self, client):
        """POST /letter-v2 显式 v2.0 不受退役开关影响"""
        set_rollout_config(
            RolloutConfig(
                phase=RolloutPhase.DISABLED,
                rollout_pct=0,
                letter_v1_deprecated=True,
            )
        )
        r = client.post(
            "/api/doc-gen/letter-v2",
            json={"lawyer_id": "lawyer_0001", "fields": {}},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["served_version"] == "letter_v2"
        assert data["bucket"] == "explicit"  # 显式端点, 不参与灰度

    def test_metrics_recorded_after_100pct_generation(self, client):
        """rollout_100pct 生成 letter 后 metrics 正确记录"""
        set_rollout_config(
            RolloutConfig(phase=RolloutPhase.ROLLOUT_100PCT, rollout_pct=100)
        )
        # 5 个律师生成
        for i in range(5):
            client.post(
                "/api/doc-gen/letter",
                json={"lawyer_id": f"L_full_{i}", "fields": {}},
            )
        r = client.get("/api/doc-gen/metrics")
        data = r.json()
        assert data["rollout_phase"] == "rollout_100pct"
        assert data["summary"]["total_records"] == 5
        assert data["summary"]["by_version"].get("letter_v2") == 5
        # 没有 letter_v1 记录
        assert data["summary"]["by_version"].get("letter_v1", 0) == 0
        # bucket 全在 treatment_a/b
        by_bucket = data["summary"]["by_bucket"]
        assert "control" not in by_bucket or by_bucket.get("control", 0) == 0

    def test_health_endpoint_includes_rollout_100pct(self, client):
        """GET /health 报告 rollout 状态 (含 rollout_100pct + letter_v1_deprecated)"""
        set_rollout_config(
            RolloutConfig(
                phase=RolloutPhase.ROLLOUT_100PCT,
                rollout_pct=100,
                letter_v1_deprecated=False,
            )
        )
        r = client.get("/api/doc-gen/health")
        assert r.status_code == 200
        data = r.json()
        assert "rollout" in data
        assert data["rollout"]["phase"] == "rollout_100pct"
        assert data["rollout"]["rollout_pct"] == 100
        assert data["rollout"]["letter_v1_deprecated"] is False
        assert data["rollout"]["deprecated_after_date"] == "2026-11-01"


# ====== 5. 兼容性测试 (W12 A2 doc_workflow 不动) ======
class TestBackwardCompatibility:
    """兼容性: 11/1 退役不影响其他功能"""

    def test_v1_template_file_still_exists(self):
        """letter_v1.md 文件仍存在 (供历史数据查询, 不删除)"""
        from pathlib import Path
        # templates/docs/letter_v1.md
        template_path = (
            Path(__file__).resolve().parent.parent
            / "templates"
            / "docs"
            / "letter_v1.md"
        )
        assert template_path.exists(), f"letter_v1.md 应保留: {template_path}"
        # 含 deprecated banner
        content = template_path.read_text(encoding="utf-8")
        assert "W21 skill3-full-rollout" in content
        assert "退役公告" in content or "退役" in content

    def test_v2_template_file_exists(self):
        """letter_v2.md 仍存在 (10/1 之后主用)"""
        from pathlib import Path
        template_path = (
            Path(__file__).resolve().parent.parent
            / "templates"
            / "docs"
            / "letter_v2.md"
        )
        assert template_path.exists()

    def test_v2_prompt_yaml_exists(self):
        """skill3_letter_v2.yaml 仍存在"""
        from pathlib import Path
        prompt_path = (
            Path(__file__).resolve().parent.parent
            / "prompts"
            / "skill3_letter_v2.yaml"
        )
        assert prompt_path.exists()

    def test_4_doc_types_unchanged(self):
        """4 文书类型 (complaint/defense/contract/letter) 不变"""
        # 通过 doc_gen_router 的 DOC_TYPES 常量验证
        from api.doc_gen_router import DOC_TYPES
        assert DOC_TYPES == ["complaint", "defense", "contract", "letter"]

    def test_letter_version_enum_has_both(self):
        """LetterVersion.V1 + V2 都在 (向后兼容 + 退役后 v1 不再分配)"""
        assert LetterVersion.V1.value == "letter_v1"
        assert LetterVersion.V2.value == "letter_v2"

    def test_metrics_collector_works_after_100pct(self):
        """MetricsCollector 在 100pct 后仍正常工作 (10/1 + 11/1 持续跟踪)"""
        from core.rollout import GenerationMetric

        c = MetricsCollector()
        c.record(
            GenerationMetric(
                lawyer_id="L100",
                doc_type="letter_v2",
                version="letter_v2",
                bucket="treatment_a",
                timestamp=1.0,
                latency_ms=100,
                filled_fields=20,
                missing_fields=2,
            )
        )
        s = c.summary()
        assert s["total_records"] == 1
        assert s["by_version"]["letter_v2"] == 1


# ====== 6. 综合场景 (W21 全链路验证) ======
class TestFullRolloutEndToEnd:
    """W21 全链路: 10/1 全量 100% + 11/1 退役一站式验证"""

    def test_full_rollout_scenario(self):
        """模拟完整场景: 10/1 全量 100% → 11/1 退役 (切换两个阶段)"""
        # 阶段 1: 10/1 全量 100% (letter_v1_deprecated=False)
        cfg1 = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT,
            rollout_pct=100,
            letter_v1_deprecated=False,
        )
        set_rollout_config(cfg1)

        # 全 200 律师走 v2
        for i in range(200):
            version, _ = assign_version(f"lawyer_{i:04d}")
            assert version == LetterVersion.V2

        # 阶段 2: 11/1 退役 (letter_v1_deprecated=True)
        cfg2 = RolloutConfig(
            phase=RolloutPhase.ROLLOUT_100PCT,
            rollout_pct=100,
            letter_v1_deprecated=True,
        )
        set_rollout_config(cfg2)

        # 仍全 v2 (phase 100% 已经全 v2, 退役开关二次保险)
        for i in range(200):
            version, bucket = assign_version(f"lawyer_{i:04d}")
            assert version == LetterVersion.V2
            assert bucket in ("treatment_a", "treatment_b")

    def test_deprecation_independent_of_phase(self):
        """退役开关独立于 phase: 即使 phase=disabled 也强制 v2"""
        # 10/1 全量 100% 期间, owner 可独立打开退役开关测试
        # 不需要先切到 rollout_100pct
        cfg = RolloutConfig(
            phase=RolloutPhase.DISABLED,  # 任意 phase
            rollout_pct=0,
            letter_v1_deprecated=True,
        )
        set_rollout_config(cfg)
        version, _ = assign_version("any_lawyer")
        assert version == LetterVersion.V2

    def test_metrics_after_deprecation(self):
        """退役后 metrics 仍记录 (用于 11/1 之后持续跟踪)"""
        c = get_metrics_collector()
        # 模拟 11/1 之后生成 3 次 v2 (退役后强制)
        for i in range(3):
            c.record(_make_metric(f"L_dep_{i}", "letter_v2", "treatment_a"))
        s = c.summary()
        assert s["total_records"] == 3
        assert all(v == "letter_v2" for v in s["by_version"].keys())


def _make_metric(lawyer_id: str, version: str, bucket: str):  # helper
    """构造 GenerationMetric 实例 (helper)"""
    from core.rollout import GenerationMetric
    return GenerationMetric(
        lawyer_id=lawyer_id,
        doc_type=version,
        version=version,
        bucket=bucket,
        timestamp=0.0,
        latency_ms=100,
        filled_fields=15,
        missing_fields=2,
    )