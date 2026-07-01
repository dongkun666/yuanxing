"""
W10 A1 Skill 1+2+3 一体化全流程测试 (lex-ai · 2026-06-29)

承接 W9 C1 Skill 3 文书生成 + W4 类案 + W3 Skill 2 合同审查, 律师一个案件跑完三步。

覆盖:
- POST /api/case/full-workflow happy path (1 案件 3 步)
- 4 种文书生成 (complaint/defense/contract/letter)
- 跳过子步骤 (skip_class_cases / skip_review / skip_docs)
- 错误处理 (空 lawyer_id / 空 cause / fixture 不可用)
- GET /api/case/full-workflow/{case_id} 缓存命中
- GET /api/case/full-workflow/healthz 状态

策略:
- 复用 W9 doc_gen_endpoints 的 _shared_engine fixture (in-memory SQLite)
- 用 demo fixture (demo-rental-beijing-2026) 简化 Skill 2 路径
"""
import pytest_asyncio
from httpx import AsyncClient, ASGITransport


# ====== 复用 W9 _shared_engine 模式 ======

@pytest_asyncio.fixture(scope="function")
async def _shared_engine():
    """共享的 in-memory SQLite engine (供 client 共用)"""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from core.models import Base
    from api import (  # noqa: F401
        review_router, backlog_router, doc_gen_router,
        full_workflow_router, contract_review_router, skill_endpoints,
    )

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        echo=False,
    )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 把 Database 全局指向 in-memory
    import core.db
    orig_engine = core.db.Database._engine
    orig_factory = core.db.Database._session_factory
    core.db.Database._engine = engine
    core.db.Database._session_factory = factory

    yield engine, factory

    core.db.Database._engine = orig_engine
    core.db.Database._session_factory = orig_factory
    await engine.dispose()


@pytest_asyncio.fixture
async def client(_shared_engine):
    """FastAPI AsyncClient (用 in-memory DB)"""
    from api.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ====== Health ======

class TestFullWorkflowHealth:
    async def test_healthz_returns_ok(self, client):
        resp = await client.get("/api/case/full-workflow/healthz")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["service_id"] == "lexprime.skill.full-workflow"
        assert body["version"].startswith("0.1.0")
        # 3 sub skills 都列
        assert "skill_1_caselaw" in body["sub_skills"]
        assert "skill_2_contract_review" in body["sub_skills"]
        assert "skill_3_doc_gen" in body["sub_skills"]

    async def test_healthz_endpoints_listed(self, client):
        resp = await client.get("/api/case/full-workflow/healthz")
        body = resp.json()
        assert "POST /api/case/full-workflow" in body["endpoints"]
        assert "GET /api/case/full-workflow/{case_id}" in body["endpoints"]


# ====== POST /api/case/full-workflow ======

class TestFullWorkflowHappyPath:
    async def test_full_workflow_demo_rental(self, client):
        """完整流水线: demo fixture + 4 文书"""
        payload = {
            "lawyer_id": "L1-test",
            "case_id": "WF-TEST-001",
            "cause": "房屋租赁纠纷",
            "facts": "甲方将位于北京朝阳区的房屋出租给乙方, 乙方逾期支付租金",
            "fixture_id": "demo-rental-beijing-2026",
            "stance": "乙方",
            "party_a": "张房东",
            "party_b": "李租客",
            "court": "北京市朝阳区人民法院",
            "amount": 50000.0,
            "lawyer_name": "王律师",
            "lawyer_phone": "13800001111",
            "include_docs": ["complaint", "defense", "contract", "letter"],
            "doc_output_format": "all",
        }
        resp = await client.post("/api/case/full-workflow", json=payload)
        assert resp.status_code == 200, f"full-workflow failed: {resp.text}"
        body = resp.json()

        # 顶层字段
        assert body["case_id"] == "WF-TEST-001"
        assert body["lawyer_id"] == "L1-test"
        assert body["cause"] == "房屋租赁纠纷"
        assert body["status"] in ("completed", "partial")
        assert body["case_summary_id"].startswith("cs-")
        assert body["latency_ms"] > 0
        assert "disclaimer" in body

        # 3 步状态
        assert body["step_class_cases"]["status"] in ("completed", "skipped", "failed")
        assert body["step_review"]["status"] in ("completed", "skipped", "failed")
        assert body["step_docs"]["status"] in ("completed", "skipped", "failed")

        # Skill 1: 类案
        if body["step_class_cases"]["status"] == "completed":
            assert body["class_cases"] is not None
            assert "results" in body["class_cases"]
            assert "statistics" in body["class_cases"]

        # Skill 2: 风险
        if body["step_review"]["status"] == "completed":
            assert body["risks"] is not None
            assert "risk_summary" in body["risks"]
            assert "clause_reviews" in body["risks"]

        # Skill 3: 4 文书
        assert "docs" in body
        for doc_type in ("complaint", "defense", "contract", "letter"):
            assert doc_type in body["docs"]
            doc = body["docs"][doc_type]
            assert doc["gen_id"].startswith("dg-")
            assert doc["doc_type"] == doc_type
            assert doc["markdown"]  # 非空
            assert doc["error"] is None

    async def test_full_workflow_partial_docs(self, client):
        """只生成 2 文书 (complaint + letter)"""
        payload = {
            "lawyer_id": "L-test",
            "case_id": "WF-TEST-002",
            "cause": "借款合同纠纷",
            "facts": "借款 50 万",
            "fixture_id": "demo-loan-shanghai-2026",
            "include_docs": ["complaint", "letter"],
            "doc_output_format": "markdown",
        }
        resp = await client.post("/api/case/full-workflow", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] in ("completed", "partial")
        assert "complaint" in body["docs"]
        assert "letter" in body["docs"]
        assert "defense" not in body["docs"]
        assert "contract" not in body["docs"]
        # markdown-only 模式无 docx_base64
        assert body["docs"]["complaint"]["docx_base64"] is None


# ====== 跳过子步骤 ======

class TestFullWorkflowSkipSteps:
    async def test_skip_class_cases(self, client):
        """skip_class_cases=True 不跑类案检索"""
        payload = {
            "lawyer_id": "L-test",
            "case_id": "WF-SKIP-1",
            "cause": "测试案由",
            "fixture_id": "demo-rental-beijing-2026",
            "skip_class_cases": True,
            "include_docs": ["complaint"],
        }
        resp = await client.post("/api/case/full-workflow", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["step_class_cases"]["status"] == "skipped"
        assert body["class_cases"] is not None
        assert body["class_cases"].get("skipped") is True

    async def test_skip_review_no_contract(self, client):
        """无 contract_text 无 fixture → 跳过 review"""
        payload = {
            "lawyer_id": "L-test",
            "case_id": "WF-SKIP-2",
            "cause": "测试案由",
            "skip_review": True,
            "include_docs": ["letter"],
        }
        resp = await client.post("/api/case/full-workflow", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["step_review"]["status"] == "skipped"
        assert body["risks"] is not None
        assert body["risks"].get("skipped") is True

    async def test_skip_docs(self, client):
        """skip_docs=True 不跑文书生成"""
        payload = {
            "lawyer_id": "L-test",
            "case_id": "WF-SKIP-3",
            "cause": "测试案由",
            "fixture_id": "demo-rental-beijing-2026",
            "skip_docs": True,
        }
        resp = await client.post("/api/case/full-workflow", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["step_docs"]["status"] == "skipped"
        assert body["docs"] == {}


# ====== 错误处理 ======

class TestFullWorkflowErrors:
    async def test_empty_lawyer_id_422(self, client):
        """lawyer_id 为空 → 422"""
        payload = {
            "lawyer_id": "",
            "case_id": "WF-ERR-1",
            "cause": "测试",
            "fixture_id": "demo-rental-beijing-2026",
        }
        resp = await client.post("/api/case/full-workflow", json=payload)
        assert resp.status_code == 422

    async def test_empty_cause_422(self, client):
        """cause 为空 → 422"""
        payload = {
            "lawyer_id": "L-test",
            "case_id": "WF-ERR-2",
            "cause": "",
            "fixture_id": "demo-rental-beijing-2026",
        }
        resp = await client.post("/api/case/full-workflow", json=payload)
        assert resp.status_code == 422

    async def test_invalid_fixture_partial_status(self, client):
        """fixture_id 不存在 → 不致命, 整体 status=partial, step_review=failed

        设计: 任一子步骤失败 → 整体 partial, 不强制整体 404/500 (graceful degradation)
        """
        payload = {
            "lawyer_id": "L-test",
            "case_id": "WF-ERR-3",
            "cause": "测试",
            "fixture_id": "nonexistent-fixture-2026",
        }
        resp = await client.post("/api/case/full-workflow", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "partial"
        assert body["step_review"]["status"] == "failed"
        assert body["risks"] is None


# ====== GET /api/case/full-workflow/{case_id} ======

class TestGetFullWorkflowResult:
    async def test_get_by_case_summary_id(self, client):
        """先用 POST 拿 summary_id, 再 GET 拿结果"""
        payload = {
            "lawyer_id": "L-test",
            "case_id": "WF-GET-1",
            "cause": "测试案由",
            "fixture_id": "demo-rental-beijing-2026",
            "include_docs": ["letter"],
        }
        post_resp = await client.post("/api/case/full-workflow", json=payload)
        assert post_resp.status_code == 200
        body = post_resp.json()
        summary_id = body["case_summary_id"]

        get_resp = await client.get(f"/api/case/full-workflow/{summary_id}")
        assert get_resp.status_code == 200
        get_body = get_resp.json()
        assert get_body["case_summary_id"] == summary_id

    async def test_get_by_case_id(self, client):
        """GET 用 case_id 也命中 (缓存双索引)"""
        payload = {
            "lawyer_id": "L-test",
            "case_id": "WF-GET-2",
            "cause": "测试案由",
            "fixture_id": "demo-rental-beijing-2026",
            "include_docs": ["letter"],
        }
        await client.post("/api/case/full-workflow", json=payload)
        get_resp = await client.get("/api/case/full-workflow/WF-GET-2")
        assert get_resp.status_code == 200

    async def test_get_nonexistent_404(self, client):
        """不存在 → 404"""
        resp = await client.get("/api/case/full-workflow/nonexistent-case-id")
        assert resp.status_code == 404


# ====== 校验与兜底 ======

class TestFullWorkflowValidation:
    async def test_invalid_doc_type_filtered(self, client):
        """include_docs 含非法 doc_type → 自动过滤"""
        payload = {
            "lawyer_id": "L-test",
            "case_id": "WF-VAL-1",
            "cause": "测试",
            "fixture_id": "demo-rental-beijing-2026",
            "include_docs": ["complaint", "invalid_type", "letter"],
        }
        resp = await client.post("/api/case/full-workflow", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        # 只生成 complaint + letter
        assert "complaint" in body["docs"]
        assert "letter" in body["docs"]
        assert "invalid_type" not in body["docs"]

    async def test_invalid_contract_type_fallback(self, client):
        """contract_type 非法 → fallback "其他" """
        payload = {
            "lawyer_id": "L-test",
            "case_id": "WF-VAL-2",
            "cause": "测试",
            "contract_type": "不是有效的合同类型",
            "contract_text": "第一条 标的\n" + "这是一份很长的合同文本。" * 20,
            "include_docs": ["contract"],
        }
        resp = await client.post("/api/case/full-workflow", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        # 文书里 contract_type 应该是 "其他"
        assert "其他" in body["docs"]["contract"]["markdown"] or "其他" in str(body["risks"].get("query_meta", {}))