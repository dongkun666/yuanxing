"""
W12 A2 双审工作流状态机测试 (lex-coder · 2026-06-30)

覆盖:
- 5 状态转换函数 (draft → ai_reviewed → lawyer_reviewed → client_signed → archived)
- transition_back (回退)
- 非法转换 → StateTransitionError
- DocReviewState ORM 持久化
- history JSON 累积
- get_workflow_status / list_workflow_by_state 查询
- PATCH /api/doc-gen/{doc_id}/state 端点 (happy path + error cases)
- POST /api/doc-gen/{doc_id}/risk-annotation 端点
- GET /api/doc-gen/workflow/board 端点
- GET /api/doc-gen/workflow/health 端点

策略:
- 复用 _shared_engine fixture 模式 (W10 A1)
- in-memory SQLite + StaticPool
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport


# ====== Fixtures ======

@pytest_asyncio.fixture(scope="function")
async def _shared_engine():
    """共享的 in-memory SQLite engine"""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from core.models import Base
    from core import doc_workflow  # noqa: F401  注册 DocReviewState + Signature

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        echo=False,
    )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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
    from api.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ====== State Machine: Core Functions ======

class TestStateMachineCore:
    """测试 core.doc_workflow 状态机核心函数"""

    async def test_full_forward_transitions(self, _shared_engine):
        """draft → ai_reviewed → lawyer_reviewed → client_signed → archived (完整前向)"""
        from core.doc_workflow import (
            DocState, transition_to_ai_reviewed, transition_to_lawyer_reviewed,
            transition_to_client_signed, transition_to_archived,
        )
        _, factory = _shared_engine

        async with factory() as session:
            # 1) draft → ai_reviewed
            status = await transition_to_ai_reviewed(
                session, doc_id="doc-1", case_id="case-1", doc_type="complaint",
                actor="lawyer-A", reason="AI 风险标注完成",
                risk_summary={"fatal_count": 0, "major_count": 1},
            )
            assert status.state == DocState.AI_REVIEWED.value
            assert status.next_state == DocState.LAWYER_REVIEWED.value
            assert status.previous_state == DocState.DRAFT.value
            assert len(status.history) == 1

            # 2) ai_reviewed → lawyer_reviewed
            status = await transition_to_lawyer_reviewed(
                session, doc_id="doc-1",
                actor="lawyer-A", reason="律师审核通过",
                lawyer_notes="法条引用已修正",
            )
            assert status.state == DocState.LAWYER_REVIEWED.value
            assert "法条引用已修正" in status.lawyer_notes
            assert len(status.history) == 2

            # 3) lawyer_reviewed → client_signed
            status = await transition_to_client_signed(
                session, doc_id="doc-1",
                actor="lawyer-A", reason="客户已签字",
            )
            assert status.state == DocState.CLIENT_SIGNED.value
            assert len(status.history) == 3

            # 4) client_signed → archived
            status = await transition_to_archived(
                session, doc_id="doc-1",
                actor="lawyer-A", reason="归档, 法律留痕",
            )
            assert status.state == DocState.ARCHIVED.value
            assert status.next_state is None  # 终态
            assert status.previous_state == DocState.CLIENT_SIGNED.value
            assert len(status.history) == 4

            await session.commit()

    async def test_transition_back_from_lawyer_reviewed(self, _shared_engine):
        """lawyer_reviewed → ai_reviewed (返工)"""
        from core.doc_workflow import (
            DocState, transition_to_ai_reviewed, transition_to_lawyer_reviewed,
            transition_back,
        )
        _, factory = _shared_engine

        async with factory() as session:
            await transition_to_ai_reviewed(
                session, doc_id="doc-2", case_id="case-2", doc_type="defense",
                actor="lawyer-B", reason="初次标注",
            )
            await transition_to_lawyer_reviewed(
                session, doc_id="doc-2",
                actor="lawyer-B", reason="初审通过",
            )
            status = await transition_back(
                session, doc_id="doc-2",
                actor="lawyer-B", reason="发现新风险, 返工",
            )
            assert status.state == DocState.AI_REVIEWED.value
            assert status.history[-1]["from_state"] == DocState.LAWYER_REVIEWED.value
            assert status.history[-1]["to_state"] == DocState.AI_REVIEWED.value
            assert status.history[-1]["reason"] == "发现新风险, 返工"

            await session.commit()

    async def test_transition_back_from_archived_raises(self, _shared_engine):
        """archived → 无法回退 (终态)"""
        from core.doc_workflow import (
            StateTransitionError, transition_to_ai_reviewed, transition_to_lawyer_reviewed,
            transition_to_client_signed, transition_to_archived, transition_back,
        )
        _, factory = _shared_engine

        async with factory() as session:
            await transition_to_ai_reviewed(session, doc_id="d", case_id="c", doc_type="letter",
                                              actor="L", reason="init")
            await transition_to_lawyer_reviewed(session, doc_id="d", actor="L", reason="r1")
            await transition_to_client_signed(session, doc_id="d", actor="L", reason="r2")
            await transition_to_archived(session, doc_id="d", actor="L", reason="r3")

            with pytest.raises(StateTransitionError) as exc_info:
                await transition_back(session, doc_id="d", actor="L", reason="undo")
            assert exc_info.value.code == "no_previous_state"

    async def test_invalid_skip_transition_raises(self, _shared_engine):
        """draft → lawyer_reviewed (跳过 ai_reviewed, 非法)"""
        from core.doc_workflow import (
            StateTransitionError, transition_to_lawyer_reviewed,
        )
        _, factory = _shared_engine

        async with factory() as session:
            with pytest.raises(StateTransitionError) as exc_info:
                await transition_to_lawyer_reviewed(
                    session, doc_id="d", actor="L", reason="skip",
                )
            assert exc_info.value.code == "invalid_transition"
            assert "ai_reviewed" in exc_info.value.message

    async def test_new_doc_creates_draft_state(self, _shared_engine):
        """首次 transition 自动从 draft 创建"""
        from core.doc_workflow import DocState, transition_to_ai_reviewed
        _, factory = _shared_engine

        async with factory() as session:
            status = await transition_to_ai_reviewed(
                session, doc_id="new-1", case_id="case-N", doc_type="contract",
                actor="lawyer-X", reason="新建标注",
            )
            assert status.doc_id == "new-1"
            assert status.doc_type == "contract"
            assert status.state == DocState.AI_REVIEWED.value
            # history 第 1 条: draft → ai_reviewed
            assert status.history[0]["from_state"] == DocState.DRAFT.value
            assert status.history[0]["to_state"] == DocState.AI_REVIEWED.value

            await session.commit()

    async def test_history_accumulates(self, _shared_engine):
        """history JSON 累积, 不覆盖"""
        from core.doc_workflow import (
            transition_to_ai_reviewed, transition_to_lawyer_reviewed,
            get_workflow_status,
        )
        _, factory = _shared_engine

        async with factory() as session:
            await transition_to_ai_reviewed(
                session, doc_id="h-1", case_id="c-h", doc_type="letter",
                actor="lawyer-H", reason="第 1 步",
            )
            await session.commit()

        async with factory() as session:
            await transition_to_lawyer_reviewed(
                session, doc_id="h-1", actor="lawyer-H", reason="第 2 步",
            )
            await session.commit()

        async with factory() as session:
            status = await get_workflow_status(session, "h-1")
            assert len(status.history) == 2
            assert status.history[0]["reason"] == "第 1 步"
            assert status.history[1]["reason"] == "第 2 步"

    async def test_get_workflow_status_none_for_unknown_doc(self, _shared_engine):
        """未知 doc_id → None"""
        from core.doc_workflow import get_workflow_status
        _, factory = _shared_engine

        async with factory() as session:
            status = await get_workflow_status(session, "nonexistent")
            assert status is None

    async def test_list_workflow_by_state(self, _shared_engine):
        """按状态查询"""
        from core.doc_workflow import (
            DocState, transition_to_ai_reviewed, list_workflow_by_state,
        )
        _, factory = _shared_engine

        async with factory() as session:
            for i in range(3):
                await transition_to_ai_reviewed(
                    session, doc_id=f"list-{i}", case_id=f"c-{i}", doc_type="complaint",
                    actor="L", reason=f"init-{i}",
                )
            await session.commit()

        async with factory() as session:
            ai_records = await list_workflow_by_state(session, DocState.AI_REVIEWED.value)
            assert len(ai_records) == 3
            for r in ai_records:
                assert r.state == DocState.AI_REVIEWED.value


# ====== HTTP API: PATCH /state ======

class TestPatchDocWorkflowState:
    """测试 PATCH /api/doc-gen/{doc_id}/state 端点"""

    async def test_patch_creates_new_draft_and_advances(self, client):
        """PATCH 第一次自动从 draft 创建, 再 PATCH 推进"""
        # 1) 第一次 PATCH: draft → ai_reviewed (新建)
        resp = await client.patch(
            "/api/doc-gen/api-test-1/state",
            json={
                "target_state": "ai_reviewed",
                "actor": "lawyer-api",
                "reason": "API 测试 1",
                "case_id": "case-api-1",
                "doc_type": "complaint",
                "risk_summary": {"fatal_count": 0, "major_count": 1},
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["state"] == "ai_reviewed"
        assert body["doc_id"] == "api-test-1"
        assert body["doc_type"] == "complaint"
        assert body["doc_type_label"] == "民事起诉状"
        assert body["state_label"] == "AI 已审"
        assert body["has_signature"] is False
        assert len(body["history"]) == 1
        assert body["current_risk_summary"]["major_count"] == 1

    async def test_patch_chain_4_transitions(self, client):
        """完整链路 4 次 PATCH"""
        doc_id = "chain-1"

        for target in ["ai_reviewed", "lawyer_reviewed", "client_signed", "archived"]:
            payload = {"target_state": target, "actor": "L", "reason": f"→ {target}",
                        "case_id": "case-c", "doc_type": "letter"}
            if target == "lawyer_reviewed":
                payload["lawyer_notes"] = f"律师备注 @ {target}"
            resp = await client.patch(f"/api/doc-gen/{doc_id}/state", json=payload)
            assert resp.status_code == 200, f"target={target} failed: {resp.text}"
            assert resp.json()["state"] == target

    async def test_patch_back_transition(self, client):
        """transition_back=True 回退"""
        doc_id = "back-1"
        # 先推进到 lawyer_reviewed
        for target in ["ai_reviewed", "lawyer_reviewed"]:
            await client.patch(f"/api/doc-gen/{doc_id}/state", json={
                "target_state": target, "actor": "L", "reason": f"→ {target}",
                "case_id": "c-b", "doc_type": "defense",
            })
        # 回退
        resp = await client.patch(f"/api/doc-gen/{doc_id}/state", json={
            "transition_back": True, "actor": "L", "reason": "返工",
        })
        assert resp.status_code == 200
        assert resp.json()["state"] == "ai_reviewed"

    async def test_patch_invalid_transition_409(self, client):
        """非法转换 → 409"""
        doc_id = "invalid-1"
        # 第一次到 ai_reviewed
        await client.patch(f"/api/doc-gen/{doc_id}/state", json={
            "target_state": "ai_reviewed", "actor": "L", "reason": "init",
            "case_id": "c-i", "doc_type": "contract",
        })
        # 尝试跳到 archived
        resp = await client.patch(f"/api/doc-gen/{doc_id}/state", json={
            "target_state": "archived", "actor": "L", "reason": "skip",
        })
        assert resp.status_code == 409
        assert "状态转换失败" in resp.json()["detail"]

    async def test_patch_both_target_and_back_400(self, client):
        """target_state 和 transition_back 互斥 → 400"""
        resp = await client.patch("/api/doc-gen/x/state", json={
            "target_state": "ai_reviewed",
            "transition_back": True,
            "actor": "L", "reason": "conflict",
        })
        assert resp.status_code == 400

    async def test_patch_neither_target_nor_back_400(self, client):
        """两者都没指定 → 400"""
        resp = await client.patch("/api/doc-gen/x/state", json={
            "actor": "L", "reason": "noop",
        })
        assert resp.status_code == 400


# ====== HTTP API: GET /state ======

class TestGetDocWorkflowState:
    """测试 GET /api/doc-gen/{doc_id}/state"""

    async def test_get_returns_current_state(self, client):
        """GET 拿当前状态"""
        # 先创建 (draft → ai_reviewed → lawyer_reviewed)
        await client.patch("/api/doc-gen/get-1/state", json={
            "target_state": "ai_reviewed", "actor": "L", "reason": "init",
            "case_id": "c-g", "doc_type": "complaint",
        })
        await client.patch("/api/doc-gen/get-1/state", json={
            "target_state": "lawyer_reviewed", "actor": "L", "reason": "律师审",
            "lawyer_notes": "test note",
        })
        resp = await client.get("/api/doc-gen/get-1/state")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["state"] == "lawyer_reviewed"
        assert body["state_label"] == "律师已审"
        assert body["lawyer_notes"] == "test note"

    async def test_get_nonexistent_404(self, client):
        """不存在 → 404"""
        resp = await client.get("/api/doc-gen/nonexistent-xyz/state")
        assert resp.status_code == 404


# ====== HTTP API: POST /risk-annotation ======

class TestRiskAnnotation:
    """测试 POST /api/doc-gen/{doc_id}/risk-annotation"""

    async def test_annotate_complaint(self, client):
        """标注起诉状"""
        resp = await client.post("/api/doc-gen/risk-c1/risk-annotation", json={
            "doc_id": "risk-c1",
            "doc_type": "complaint",
            "doc_markdown": (
                "# 民事起诉状\n\n"
                "原告张三诉被告李四借款纠纷一案, 请求判令被告偿还本金人民币 50000 元。\n\n"
                "依据相关法律规定, 被告应承担违约责任。\n\n"
                "事实: 2024 年 1 月原告借款给被告, 被告至今未还。"
            ),
            "case_id": "c-risk-1",
        })
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["doc_type"] == "complaint"
        assert body["doc_type_label"] == "民事起诉状"
        assert len(body["dimensions"]) == 4  # 起诉 4 维度
        dim_names = [d["dimension"] for d in body["dimensions"]]
        assert dim_names == ["案由", "诉讼请求", "事实理由", "法条引用"]
        assert body["latency_ms"] >= 0
        # "相关法律" 命中 → 法条引用维度 advisory
        legal_basis_dim = next(d for d in body["dimensions"] if d["dimension"] == "法条引用")
        assert legal_basis_dim["risk_level"] in ("advisory", "ok")

    async def test_annotate_contract_fatal_clause(self, client):
        """标注合同 + 命中致命风险"""
        resp = await client.post("/api/doc-gen/risk-contract-1/risk-annotation", json={
            "doc_id": "risk-contract-1",
            "doc_type": "contract",
            "doc_markdown": (
                "# 房屋租赁合同\n\n"
                "第一条 标的: 甲方将位于上海市浦东新区的房屋出租给乙方。\n\n"
                "第二条 价款: 租金人民币 5000 元/月, 合理期限支付。\n\n"
                "第三条 履行: 乙方应于 30 日内支付租金。\n\n"
                "第四条 违约: 逾期支付的, 按月租金的 5% 加收违约金。\n\n"
                "第五条 管辖: 任何一方均可向甲方住所地人民法院提起诉讼。"
            ),
        })
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["doc_type"] == "contract"
        assert len(body["dimensions"]) == 5  # 合同 5 维度
        # 管辖维度命中"甲方住所地" → major
        jurisdiction_dim = next(d for d in body["dimensions"] if d["dimension"] == "管辖")
        assert jurisdiction_dim["risk_level"] == "major"

    async def test_annotate_letter_with_deadline(self, client):
        """标注律师函 + 时限明确"""
        resp = await client.post("/api/doc-gen/risk-letter-1/risk-annotation", json={
            "doc_id": "risk-letter-1",
            "doc_type": "letter",
            "doc_markdown": (
                "致: 某公司\n\n"
                "事实: 贵公司于 2024 年 1 月违约。\n\n"
                "本律师认为贵公司应停止违约行为。\n\n"
                "要求: 请贵公司于 15 日内支付人民币 50000 元。\n\n"
                "否则, 本律师将依法提起诉讼。"
            ),
        })
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body["dimensions"]) == 5  # 律师函 5 维度

    async def test_annotate_defense(self, client):
        """标注答辩状"""
        resp = await client.post("/api/doc-gen/risk-defense-1/risk-annotation", json={
            "doc_id": "risk-defense-1",
            "doc_type": "defense",
            "doc_markdown": (
                "# 民事答辩状\n\n"
                "被告不存在原告所述违约行为。\n\n"
                "本案已超过诉讼时效, 原告请求依法驳回。\n\n"
                "证据充分, 证人证言足以证明被告未违约。"
            ),
        })
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body["dimensions"]) == 4
        assert body["doc_type"] == "defense"

    async def test_annotate_invalid_doc_type_400(self, client):
        """非法 doc_type → 400"""
        resp = await client.post("/api/doc-gen/x/risk-annotation", json={
            "doc_id": "x", "doc_type": "invalid_type", "doc_markdown": "测试 markdown 文本填充长度",
        })
        assert resp.status_code == 422  # pydantic 校验失败

    async def test_annotate_doc_id_mismatch_400(self, client):
        """URL doc_id 与 body doc_id 不一致 → 400"""
        resp = await client.post("/api/doc-gen/url-id/risk-annotation", json={
            "doc_id": "body-id", "doc_type": "complaint",
            "doc_markdown": "测试 markdown 内容至少 10 个字符",
        })
        assert resp.status_code == 400
        assert "不一致" in resp.json()["detail"]


# ====== HTTP API: GET /workflow/board ======

class TestWorkflowBoard:
    async def test_board_returns_all_states(self, client):
        """看板返所有状态"""
        # 创建 3 个不同状态的文档
        await client.patch("/api/doc-gen/board-1/state", json={
            "target_state": "ai_reviewed", "actor": "L", "reason": "init",
            "case_id": "c-b", "doc_type": "complaint",
        })
        await client.patch("/api/doc-gen/board-2/state", json={
            "target_state": "ai_reviewed", "actor": "L", "reason": "init",
            "case_id": "c-b", "doc_type": "defense",
        })

        resp = await client.get("/api/doc-gen/workflow/board")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 2
        assert body["state_filter"] is None

    async def test_board_filter_by_state(self, client):
        """按状态过滤"""
        # 创建 2 ai_reviewed + 1 lawyer_reviewed
        for i in range(2):
            await client.patch(f"/api/doc-gen/f-{i}/state", json={
                "target_state": "ai_reviewed", "actor": "L", "reason": "init",
                "case_id": "c-f", "doc_type": "complaint",
            })
        await client.patch("/api/doc-gen/f-3/state", json={
            "target_state": "ai_reviewed", "actor": "L", "reason": "a",
            "case_id": "c-f", "doc_type": "letter",
        })
        await client.patch("/api/doc-gen/f-3/state", json={
            "target_state": "lawyer_reviewed", "actor": "L", "reason": "b",
        })

        resp = await client.get("/api/doc-gen/workflow/board?state=lawyer_reviewed")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["state_filter"] == "lawyer_reviewed"
        assert body["items"][0]["state"] == "lawyer_reviewed"

    async def test_board_invalid_state_400(self, client):
        """非法状态 → 400"""
        resp = await client.get("/api/doc-gen/workflow/board?state=invalid_state")
        assert resp.status_code == 400


# ====== HTTP API: GET /workflow/health ======

class TestWorkflowHealth:
    async def test_health_ok(self, client):
        resp = await client.get("/api/doc-gen/workflow/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["service_id"] == "lexprime.skill.doc-workflow"
        assert "draft" in body["states"]
        assert "ai_reviewed" in body["states"]
        assert "complaint" in body["doc_type_dimensions"]
        assert "contract" in body["doc_type_dimensions"]
        # 4 endpoints 都列出
        assert any("PATCH" in e for e in body["endpoints"])