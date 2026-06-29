"""
W7 律师评审问题收集 + 数据看板 API 测试 (lex-coder · 2026-06-29)

覆盖 3 新端点:
- POST /api/review/question     律师现场提交问题
- GET  /api/review/questions    问题列表 (按 lawyer_id / category / status 过滤)
- GET  /api/review/board        数据看板 (5 律师 × 5 合同 × 5 维度 + 评论 + 问题)

策略:
- pytest-asyncio fixture + httpx.AsyncClient + ASGITransport
- 复用 conftest.py DB + lifespan (跟 W6 一致)
- 用 _ClientWrapper 给 AsyncClient 加 session_factory 属性 (W2 已有模板)
"""
import pytest_asyncio
import pytest

from httpx import AsyncClient, ASGITransport


# ====== 常量 ======
LAWYER_IDS = ["L1", "L2", "L3", "L4", "L5"]
CONTRACT_IDS = [
    "demo-rental-beijing-2026",
    "demo-loan-shanghai-2026",
    "demo-labor-fulltime-2026",
    "demo-service-tech-2026",
    "demo-sales-goods-2026",
]
QUESTION_CATEGORIES = ["产品", "技术", "法务", "其他"]
QUESTION_STATUSES = ["open", "answered", "triaged", "deferred"]


def sample_question(lawyer_id: str, category: str = "产品", status: str = "open") -> dict:
    """生成示例问题"""
    return {
        "lawyer_id": lawyer_id,
        "question_text": f"{lawyer_id} 律师测试问题: Skill 2 在 {category} 维度有什么建议?",
        "category": category,
        "context": f"{lawyer_id} 律师使用场景: 房屋租赁场景",
        "status": status,
    }


# ====== Fixtures ======
@pytest_asyncio.fixture(scope="function")
async def _shared_engine():
    """共享的 in-memory SQLite engine (供 client + clean 共用)"""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from core.models import Base
    from api import review_router  # noqa: F401 触发 ReviewScore + ReviewQuestion 注册到 Base.metadata

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
    """FastAPI TestClient (用 in-memory DB)"""
    from api.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(_shared_engine):
    """每个测试前清空 review_scores + review_questions 表"""
    engine, factory = _shared_engine
    from api.review_router import ReviewScore, ReviewQuestion
    from sqlalchemy import delete

    async with factory() as session:
        await session.execute(delete(ReviewScore))
        await session.execute(delete(ReviewQuestion))
        await session.commit()
    yield


# ====== Submit Question ======
class TestSubmitQuestion:
    async def test_submit_basic_question(self, client):
        """基本提交"""
        payload = sample_question("L1", "产品", "open")
        resp = await client.post("/api/review/question", json=payload)
        assert resp.status_code == 201, f"submit failed: {resp.text}"
        body = resp.json()
        assert body["lawyer_id"] == "L1"
        assert body["category"] == "产品"
        assert body["status"] == "open"
        assert body["question_id"] > 0

    async def test_submit_all_categories(self, client):
        """4 分类全部支持"""
        for cat in QUESTION_CATEGORIES:
            payload = sample_question("L1", cat)
            resp = await client.post("/api/review/question", json=payload)
            assert resp.status_code == 201, f"{cat} failed: {resp.text}"
            body = resp.json()
            assert body["category"] == cat

    async def test_submit_all_statuses(self, client):
        """4 状态全部支持"""
        for st in QUESTION_STATUSES:
            payload = sample_question("L1", "产品", st)
            resp = await client.post("/api/review/question", json=payload)
            assert resp.status_code == 201, f"{st} failed: {resp.text}"
            body = resp.json()
            assert body["status"] == st

    async def test_submit_invalid_lawyer(self, client):
        """非法 lawyer_id 拒绝"""
        payload = sample_question("INVALID")
        resp = await client.post("/api/review/question", json=payload)
        assert resp.status_code in (400, 422)

    async def test_submit_invalid_category(self, client):
        """非法 category 拒绝"""
        payload = sample_question("L1", "BOGUS")
        resp = await client.post("/api/review/question", json=payload)
        assert resp.status_code in (400, 422)

    async def test_submit_invalid_status(self, client):
        """非法 status 拒绝"""
        payload = sample_question("L1", "产品", "BOGUS")
        resp = await client.post("/api/review/question", json=payload)
        assert resp.status_code in (400, 422)

    async def test_submit_question_too_short(self, client):
        """question_text < 10 字拒绝"""
        payload = sample_question("L1")
        payload["question_text"] = "太短"  # < 10 字
        resp = await client.post("/api/review/question", json=payload)
        assert resp.status_code in (400, 422)

    async def test_submit_question_too_long(self, client):
        """question_text > 500 字拒绝"""
        payload = sample_question("L1")
        payload["question_text"] = "x" * 501
        resp = await client.post("/api/review/question", json=payload)
        assert resp.status_code in (400, 422)

    async def test_submit_context_optional(self, client):
        """context 是可选的"""
        payload = sample_question("L1")
        payload.pop("context")
        resp = await client.post("/api/review/question", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["context"] is None

    async def test_submit_context_too_long(self, client):
        """context > 1000 字拒绝"""
        payload = sample_question("L1")
        payload["context"] = "x" * 1001
        resp = await client.post("/api/review/question", json=payload)
        assert resp.status_code in (400, 422)

    async def test_submit_multiple_questions_same_lawyer(self, client):
        """同一律师可提交多条问题"""
        for i in range(3):
            payload = sample_question("L1", "产品")
            payload["question_text"] = f"L1 第 {i+1} 条问题: 测试多次提交场景"
            resp = await client.post("/api/review/question", json=payload)
            assert resp.status_code == 201

        # 查询应有 3 条
        resp = await client.get("/api/review/questions?lawyer_id=L1")
        assert resp.json()["total"] == 3

    async def test_submit_response_shape(self, client):
        """响应字段完整性"""
        payload = sample_question("L2", "技术")
        resp = await client.post("/api/review/question", json=payload)
        body = resp.json()
        assert "question_id" in body
        assert "lawyer_id" in body
        assert "question_text" in body
        assert "category" in body
        assert "context" in body
        assert "status" in body
        assert "created_at" in body
        assert "next" in body
        assert "/api/review/questions" in body["next"]


# ====== List Questions ======
class TestListQuestions:
    async def test_list_empty(self, client):
        """无问题时返回空列表"""
        resp = await client.get("/api/review/questions")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["by_category"] == {c: 0 for c in QUESTION_CATEGORIES}
        assert body["by_status"] == {s: 0 for s in QUESTION_STATUSES}
        assert body["questions"] == []

    async def test_list_after_submit(self, client):
        """提交后能查到"""
        await client.post("/api/review/question", json=sample_question("L1", "产品"))
        await client.post("/api/review/question", json=sample_question("L2", "技术"))

        resp = await client.get("/api/review/questions")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert body["by_category"]["产品"] == 1
        assert body["by_category"]["技术"] == 1

    async def test_list_filter_by_lawyer(self, client):
        """按 lawyer_id 过滤"""
        await client.post("/api/review/question", json=sample_question("L1"))
        await client.post("/api/review/question", json=sample_question("L2"))
        await client.post("/api/review/question", json=sample_question("L1", "技术"))

        resp = await client.get("/api/review/questions?lawyer_id=L1")
        body = resp.json()
        assert body["total"] == 2
        assert all(q["lawyer_id"] == "L1" for q in body["questions"])

    async def test_list_filter_by_category(self, client):
        """按 category 过滤"""
        await client.post("/api/review/question", json=sample_question("L1", "产品"))
        await client.post("/api/review/question", json=sample_question("L2", "技术"))
        await client.post("/api/review/question", json=sample_question("L3", "产品"))

        resp = await client.get("/api/review/questions?category=产品")
        body = resp.json()
        assert body["total"] == 2
        assert all(q["category"] == "产品" for q in body["questions"])

    async def test_list_filter_by_status(self, client):
        """按 status 过滤"""
        await client.post("/api/review/question", json=sample_question("L1", "产品", "open"))
        await client.post("/api/review/question", json=sample_question("L2", "技术", "answered"))
        await client.post("/api/review/question", json=sample_question("L3", "产品", "open"))

        resp = await client.get("/api/review/questions?status=open")
        body = resp.json()
        assert body["total"] == 2
        assert all(q["status"] == "open" for q in body["questions"])

    async def test_list_filter_combined(self, client):
        """组合过滤: L1 + 产品 + open"""
        await client.post("/api/review/question", json=sample_question("L1", "产品", "open"))
        await client.post("/api/review/question", json=sample_question("L1", "技术", "open"))
        await client.post("/api/review/question", json=sample_question("L1", "产品", "answered"))

        resp = await client.get("/api/review/questions?lawyer_id=L1&category=产品&status=open")
        body = resp.json()
        assert body["total"] == 1

    async def test_list_invalid_category(self, client):
        """非法 category 400"""
        resp = await client.get("/api/review/questions?category=BOGUS")
        assert resp.status_code == 400

    async def test_list_invalid_status(self, client):
        """非法 status 400"""
        resp = await client.get("/api/review/questions?status=BOGUS")
        assert resp.status_code == 400

    async def test_list_sorted_by_created_desc(self, client):
        """按 created_at DESC 排序"""
        for i in range(3):
            await client.post("/api/review/question", json=sample_question(f"L{i+1}", "产品"))

        resp = await client.get("/api/review/questions")
        questions = resp.json()["questions"]
        # 后提交的在前 (DESC)
        assert questions[0]["lawyer_id"] == "L3"
        assert questions[-1]["lawyer_id"] == "L1"


# ====== Board ======
class TestBoard:
    def default_scores(self, seed: int = 5) -> dict:
        """生成 5 维度评分, 全部 0-10 范围内 (高分档)"""
        return {
            "fatal_accuracy": 5 + seed,  # max 10 → seed <= 5
            "suggestion_practicality": 5 + seed,
            "strategy_executability": 5 + seed,
            "neutrality": 9,  # 高
            "ui_flow": 5 + seed,
        }

    async def test_board_empty(self, client):
        """空数据看板"""
        resp = await client.get("/api/review/board")
        assert resp.status_code == 200
        body = resp.json()
        assert body["summary"]["total_score_rows"] == 0
        assert body["summary"]["total_evaluations"] == 0
        assert body["summary"]["total_questions"] == 0
        assert body["summary"]["passes_threshold"] is False

    async def test_board_full_25_evaluations(self, client):
        """完整 25 条评分"""
        # 5 律师 × 5 合同 (seed=5 安全范围内)
        for lawyer in LAWYER_IDS:
            for contract in CONTRACT_IDS:
                payload = {
                    "lawyer_id": lawyer,
                    "contract_id": contract,
                    "scores": self.default_scores(5),
                }
                await client.post("/api/review/submit-score", json=payload)

        resp = await client.get("/api/review/board")
        body = resp.json()
        assert body["summary"]["total_score_rows"] == 125
        assert body["summary"]["total_evaluations"] == 25
        # 5 维度都有数据
        assert len(body["per_dimension"]) == 5
        # 5 律师都有数据
        assert len(body["per_lawyer"]) == 5
        # 5 合同都有数据
        assert len(body["per_contract"]) == 5

    async def test_board_with_questions(self, client):
        """评分 + 问题混合"""
        # 1 个评分
        await client.post("/api/review/submit-score", json={
            "lawyer_id": "L1",
            "contract_id": "demo-rental-beijing-2026",
            "scores": self.default_scores(5),
        })
        # 3 个问题
        for cat in ["产品", "技术", "法务"]:
            await client.post("/api/review/question", json=sample_question("L1", cat))

        resp = await client.get("/api/review/board")
        body = resp.json()
        assert body["summary"]["total_questions"] == 3
        assert body["questions_summary"]["by_category"]["产品"] == 1
        assert body["questions_summary"]["by_category"]["技术"] == 1
        assert body["questions_summary"]["by_category"]["法务"] == 1
        assert body["questions_summary"]["by_status"]["open"] == 3
        # L1 应有 3 个问题
        assert body["per_lawyer"]["L1"]["questions_count"] == 3

    async def test_board_per_dimension_shape(self, client):
        """per_dimension 字段"""
        await client.post("/api/review/submit-score", json={
            "lawyer_id": "L1",
            "contract_id": "demo-rental-beijing-2026",
            "scores": {
                "fatal_accuracy": 10, "suggestion_practicality": 8,
                "strategy_executability": 6, "neutrality": 10, "ui_flow": 4,
            },
        })

        resp = await client.get("/api/review/board")
        body = resp.json()
        fatal = body["per_dimension"]["fatal_accuracy"]
        assert "dimension" in fatal
        assert "dimension_label" in fatal
        assert "mean" in fatal
        assert "stdev" in fatal
        assert "n_scores" in fatal
        assert "per_lawyer" in fatal
        assert fatal["mean"] == 10.0
        assert fatal["per_lawyer"]["L1"] == 10.0

    async def test_board_per_lawyer_shape(self, client):
        """per_lawyer 字段"""
        await client.post("/api/review/submit-score", json={
            "lawyer_id": "L3",
            "contract_id": "demo-rental-beijing-2026",
            "scores": self.default_scores(5),
        })

        resp = await client.get("/api/review/board")
        body = resp.json()
        l3 = body["per_lawyer"]["L3"]
        assert l3["lawyer_id"] == "L3"
        assert "lawyer_type" in l3
        assert "venue" in l3
        assert "weighted_score" in l3
        assert "rubric_score" in l3
        assert "passes_rubric" in l3
        assert "evaluations_count" in l3
        assert "questions_count" in l3
        assert "questions" in l3
        assert isinstance(l3["questions"], list)

    async def test_board_per_contract_shape(self, client):
        """per_contract 字段"""
        for i, lawyer in enumerate(LAWYER_IDS):
            await client.post("/api/review/submit-score", json={
                "lawyer_id": lawyer,
                "contract_id": "demo-rental-beijing-2026",
                "scores": self.default_scores(i + 3),  # 3-7, 不超 10
            })

        resp = await client.get("/api/review/board")
        body = resp.json()
        rental = body["per_contract"]["demo-rental-beijing-2026"]
        assert rental["contract_id"] == "demo-rental-beijing-2026"
        assert rental["contract_type"] == "房屋租赁"
        assert rental["n_evaluations"] == 5
        assert rental["aggregate_score"] > 0

    async def test_board_prd_feedback(self, client):
        """prd_feedback_v1_0 自动生成"""
        await client.post("/api/review/submit-score", json={
            "lawyer_id": "L1",
            "contract_id": "demo-rental-beijing-2026",
            "scores": {
                "fatal_accuracy": 10, "suggestion_practicality": 8,
                "strategy_executability": 6, "neutrality": 10, "ui_flow": 4,
            },
        })

        resp = await client.get("/api/review/board")
        body = resp.json()
        feedback = body["prd_feedback_v1_0"]
        assert "rubric_score_1_5" in feedback
        assert "passes_threshold" in feedback
        assert "decision" in feedback
        assert "pain_points" in feedback
        assert "next_actions" in feedback
        # 高分应通过
        assert feedback["passes_threshold"] is True

    async def test_board_low_score_pain_points(self, client):
        """低分自动生成痛点"""
        await client.post("/api/review/submit-score", json={
            "lawyer_id": "L1",
            "contract_id": "demo-rental-beijing-2026",
            "scores": {
                "fatal_accuracy": 3, "suggestion_practicality": 4,
                "strategy_executability": 5, "neutrality": 8, "ui_flow": 7,
            },
        })

        resp = await client.get("/api/review/board")
        body = resp.json()
        feedback = body["prd_feedback_v1_0"]
        assert feedback["passes_threshold"] is False
        assert len(feedback["pain_points"]) >= 2

    async def test_board_comments_preserved(self, client):
        """comments_by_lawyer 完整保留"""
        await client.post("/api/review/submit-score", json={
            "lawyer_id": "L2",
            "contract_id": "demo-rental-beijing-2026",
            "scores": self.default_scores(5),
            "comments": {
                "fatal_accuracy": "L2 致命识别 OK",
                "suggestion_practicality": "L2 建议 OK",
                "strategy_executability": "",
                "neutrality": "",
                "ui_flow": "",
            },
        })

        resp = await client.get("/api/review/board")
        body = resp.json()
        l2_comments = body["comments_by_lawyer"]["L2"]["demo-rental-beijing-2026"]
        assert l2_comments["fatal_accuracy"] == "L2 致命识别 OK"
        assert l2_comments["suggestion_practicality"] == "L2 建议 OK"

    async def test_board_questions_per_lawyer(self, client):
        """每个律师的问题列表挂载"""
        # L1 提交 2 个问题, L2 提交 1 个
        await client.post("/api/review/question", json=sample_question("L1", "产品"))
        await client.post("/api/review/question", json=sample_question("L1", "技术"))
        await client.post("/api/review/question", json=sample_question("L2", "法务"))

        resp = await client.get("/api/review/board")
        body = resp.json()
        assert len(body["per_lawyer"]["L1"]["questions"]) == 2
        assert len(body["per_lawyer"]["L2"]["questions"]) == 1
        assert len(body["per_lawyer"]["L3"]["questions"]) == 0

    async def test_board_e2e_full_flow(self, client):
        """E2E: 完整 25 条评分 + 多条问题"""
        # 完整 25 条评分 (seed 在 3-5 之间避免超 10 分)
        for lawyer in LAWYER_IDS:
            for contract in CONTRACT_IDS:
                seed = (LAWYER_IDS.index(lawyer) + CONTRACT_IDS.index(contract)) % 3 + 3  # 3-5
                payload = {
                    "lawyer_id": lawyer,
                    "contract_id": contract,
                    "scores": self.default_scores(seed),
                }
                await client.post("/api/review/submit-score", json=payload)

        # 8 个问题 (每律师 1-2 个)
        for i, lawyer in enumerate(LAWYER_IDS):
            for j in range(2):
                if (i + j) % 2 == 0:
                    await client.post("/api/review/question", json=sample_question(lawyer, ["产品", "技术", "法务", "其他"][(i + j) % 4]))

        resp = await client.get("/api/review/board")
        body = resp.json()
        assert body["summary"]["total_evaluations"] == 25
        assert body["summary"]["total_score_rows"] == 125
        assert body["summary"]["total_questions"] >= 4  # 至少 4 条
        assert body["summary"]["passes_threshold"] is not None
        assert body["generated_at"]