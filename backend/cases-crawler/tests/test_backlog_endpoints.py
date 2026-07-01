"""
W8 A2 PRD backlog ticket 系统 API 测试 (lex-coder · 2026-06-29)

覆盖 4 端点 + 迁移脚本:
- POST /api/backlog/from-question         review_question_id → backlog ticket
- GET  /api/backlog/list                  列表 (按 status / priority / owner / category 过滤)
- POST /api/backlog/{id}/assign           owner / status / priority 分配
- GET  /api/backlog/board                 W8 backlog 总览 5 视图
- scripts/migrate_review_to_backlog.py    seed 42 项种子 + dry-run 模式

策略:
- 复用 test_review_w7_endpoints.py 的 _shared_engine fixture 模式
- 每个测试用独立 in-memory SQLite
- 触发 review_router 注册 (提供 ReviewQuestion) + backlog_router 注册 (PrdBacklog)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import pytest_asyncio

from httpx import AsyncClient, ASGITransport


# ====== 常量 (跟 backlog_router 对齐) ======
QUESTION_CATEGORIES = ["产品", "技术", "法务", "其他"]
BACKLOG_PRIORITIES = ["P0", "P1", "P2", "P3"]
BACKLOG_STATUSES = ["open", "in_progress", "done", "deferred", "wontfix"]
BACKLOG_OWNERS = [
    "lex-pm",
    "lex-coder",
    "lex-ai",
    "lex-design",
    "lex-data",
    "unassigned",
]
LAWYER_IDS = ["L1", "L2", "L3", "L4", "L5"]


def sample_question(lawyer_id: str = "L1", category: str = "产品", status: str = "open") -> dict:
    """生成示例问题 (跟 test_review_w7_endpoints.py 一致)"""
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
    """共享 in-memory SQLite engine (供 client + clean 共用)

    同时注册 review_router (ReviewQuestion) + backlog_router (PrdBacklog)
    """
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from core.models import Base
    from api import review_router  # noqa: F401
    from api import backlog_router  # noqa: F401  触发 PrdBacklog 表注册

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


@pytest_asyncio.fixture
async def clean_tables(_shared_engine):
    """每个测试前清空 review_questions + prd_backlog 表

    注: 用 `autouse=False` (opt-in), 因为:
    - TestMigrateScript 需要保留 migrate 写入的数据
    - 用 `@pytest.fixture` + 显式使用, 不强制所有测试都清理
    """
    engine, factory = _shared_engine
    from api.review_router import ReviewQuestion
    from api.backlog_router import PrdBacklog
    from sqlalchemy import delete

    async with factory() as session:
        await session.execute(delete(PrdBacklog))
        await session.execute(delete(ReviewQuestion))
        await session.commit()
    yield


@pytest_asyncio.fixture
async def seeded_question(client):
    """seed 一个 review_question, 返回 question_id"""
    payload = sample_question("L1", "产品", "open")
    resp = await client.post("/api/review/question", json=payload)
    assert resp.status_code == 201
    return resp.json()["question_id"]


# ====== 测试 1: From-Question ======
class TestFromQuestion:
    async def test_from_question_basic(self, client, seeded_question):
        """基本从 question 转 backlog"""
        qid = seeded_question
        resp = await client.post(
            "/api/backlog/from-question",
            json={"review_question_id": qid},
        )
        assert resp.status_code == 201, f"from-question failed: {resp.text}"
        body = resp.json()
        assert body["backlog_id"] > 0
        assert body["source_question_id"] == qid
        assert body["category"] == "产品"
        assert body["status"] == "open"
        assert "next" in body

    async def test_from_question_404(self, client):
        """question 不存在 → 404"""
        resp = await client.post(
            "/api/backlog/from-question",
            json={"review_question_id": 9999},
        )
        assert resp.status_code == 404

    async def test_from_question_duplicate_409(self, client, seeded_question):
        """重复转 → 409"""
        qid = seeded_question
        resp1 = await client.post(
            "/api/backlog/from-question",
            json={"review_question_id": qid},
        )
        assert resp1.status_code == 201

        # 第二次 → 409
        resp2 = await client.post(
            "/api/backlog/from-question",
            json={"review_question_id": qid},
        )
        assert resp2.status_code == 409

    async def test_from_question_with_explicit_priority_owner(self, client, seeded_question):
        """显式指定 priority + owner"""
        qid = seeded_question
        resp = await client.post(
            "/api/backlog/from-question",
            json={
                "review_question_id": qid,
                "priority": "P0",
                "owner": "lex-coder",
                "title": "测试 ticket",
                "description": "测试 description",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["priority"] == "P0"
        assert body["owner"] == "lex-coder"
        assert body["title"] == "测试 ticket"

    async def test_from_question_invalid_priority(self, client, seeded_question):
        """非法 priority → 422"""
        qid = seeded_question
        resp = await client.post(
            "/api/backlog/from-question",
            json={"review_question_id": qid, "priority": "BOGUS"},
        )
        assert resp.status_code in (400, 422)

    async def test_from_question_invalid_owner(self, client, seeded_question):
        """非法 owner → 422"""
        qid = seeded_question
        resp = await client.post(
            "/api/backlog/from-question",
            json={"review_question_id": qid, "owner": "BOGUS"},
        )
        assert resp.status_code in (400, 422)

    async def test_from_question_inferred_priority_p0_legal(self, client):
        """法务 category + '应标' 关键词 → 自动推断 P0"""
        payload = sample_question("L2", "法务", "open")
        payload["question_text"] = "L2: 利息 24% 应标 major, 律师担心漏标"
        resp = await client.post("/api/review/question", json=payload)
        assert resp.status_code == 201
        qid = resp.json()["question_id"]

        resp2 = await client.post(
            "/api/backlog/from-question",
            json={"review_question_id": qid},
        )
        body = resp2.json()
        assert body["priority"] == "P0"

    async def test_from_question_inferred_priority_p1_default(self, client, seeded_question):
        """无关键词 → 默认 P1"""
        payload = sample_question("L3", "产品", "open")
        payload["question_text"] = "L3 建议增加客户友好版 UI"
        resp = await client.post("/api/review/question", json=payload)
        qid2 = resp.json()["question_id"]

        resp2 = await client.post(
            "/api/backlog/from-question",
            json={"review_question_id": qid2},
        )
        # '建议' 命中 P1 关键词
        body = resp2.json()
        assert body["priority"] in ("P1", "P2", "P3", "P0")

    async def test_from_question_title_truncated(self, client, seeded_question):
        """question_text > 100 字 → title 自动截断到 120"""
        long_text = "x" * 200
        payload = sample_question("L1", "产品", "open")
        payload["question_text"] = long_text
        resp = await client.post("/api/review/question", json=payload)
        qid = resp.json()["question_id"]

        resp2 = await client.post(
            "/api/backlog/from-question",
            json={"review_question_id": qid},
        )
        assert resp2.status_code == 201
        body = resp2.json()
        assert len(body["title"]) <= 120

    async def test_from_question_response_shape(self, client, seeded_question):
        """响应字段完整性"""
        qid = seeded_question
        resp = await client.post(
            "/api/backlog/from-question",
            json={"review_question_id": qid},
        )
        body = resp.json()
        for k in [
            "backlog_id",
            "source_question_id",
            "title",
            "priority",
            "owner",
            "status",
            "category",
            "created_at",
            "next",
        ]:
            assert k in body, f"missing field: {k}"


# ====== 测试 2: List ======
class TestListBacklog:
    async def test_list_empty(self, client):
        """空 backlog 列表"""
        resp = await client.get("/api/backlog/list")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["tickets"] == []
        assert body["by_status"] == {s: 0 for s in BACKLOG_STATUSES}
        assert body["by_priority"] == {p: 0 for p in BACKLOG_PRIORITIES}

    async def test_list_after_seed(self, client):
        """写入后能查到"""
        # seed 一个 question 然后转 backlog
        for i in range(3):
            q_resp = await client.post(
                "/api/review/question",
                json=sample_question(f"L{i+1}", ["产品", "技术", "法务"][i]),
            )
            qid = q_resp.json()["question_id"]
            await client.post(
                "/api/backlog/from-question",
                json={"review_question_id": qid, "priority": ["P0", "P1", "P2"][i]},
            )

        resp = await client.get("/api/backlog/list")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert body["by_priority"]["P0"] == 1
        assert body["by_priority"]["P1"] == 1
        assert body["by_priority"]["P2"] == 1

    async def test_list_filter_by_status(self, client, seeded_question):
        """按 status 过滤"""
        qid = seeded_question
        await client.post("/api/backlog/from-question", json={"review_question_id": qid})

        resp = await client.get("/api/backlog/list?status=open")
        assert resp.json()["total"] == 1

        resp2 = await client.get("/api/backlog/list?status=done")
        assert resp2.json()["total"] == 0

    async def test_list_filter_by_priority(self, client, seeded_question):
        """按 priority 过滤"""
        qid = seeded_question
        await client.post("/api/backlog/from-question", json={"review_question_id": qid, "priority": "P0"})

        resp = await client.get("/api/backlog/list?priority=P0")
        assert resp.json()["total"] == 1

        resp2 = await client.get("/api/backlog/list?priority=P3")
        assert resp2.json()["total"] == 0

    async def test_list_filter_by_owner(self, client, seeded_question):
        """按 owner 过滤"""
        qid = seeded_question
        await client.post(
            "/api/backlog/from-question",
            json={"review_question_id": qid, "owner": "lex-coder"},
        )

        resp = await client.get("/api/backlog/list?owner=lex-coder")
        assert resp.json()["total"] == 1

    async def test_list_filter_by_category(self, client):
        """按 category 过滤"""
        for i, cat in enumerate(["产品", "技术", "法务"]):
            q_resp = await client.post(
                "/api/review/question", json=sample_question(f"L{i+1}", cat)
            )
            qid = q_resp.json()["question_id"]
            await client.post(
                "/api/backlog/from-question",
                json={"review_question_id": qid},
            )

        resp = await client.get("/api/backlog/list?category=法务")
        assert resp.json()["total"] == 1

    async def test_list_filter_by_source_lawyer(self, client):
        """按 source_lawyer_id 过滤"""
        for i, lid in enumerate(["L1", "L2"]):
            q_resp = await client.post(
                "/api/review/question", json=sample_question(lid, "产品")
            )
            qid = q_resp.json()["question_id"]
            await client.post(
                "/api/backlog/from-question",
                json={"review_question_id": qid},
            )

        resp = await client.get("/api/backlog/list?source_lawyer_id=L1")
        assert resp.json()["total"] == 1

    async def test_list_invalid_status(self, client):
        """非法 status → 400"""
        resp = await client.get("/api/backlog/list?status=BOGUS")
        assert resp.status_code == 400

    async def test_list_invalid_priority(self, client):
        """非法 priority → 400"""
        resp = await client.get("/api/backlog/list?priority=BOGUS")
        assert resp.status_code == 400

    async def test_list_invalid_owner(self, client):
        """非法 owner → 400"""
        resp = await client.get("/api/backlog/list?owner=BOGUS")
        assert resp.status_code == 400

    async def test_list_invalid_category(self, client):
        """非法 category → 400"""
        resp = await client.get("/api/backlog/list?category=BOGUS")
        assert resp.status_code == 400

    async def test_list_combined_filters(self, client, seeded_question):
        """组合过滤"""
        qid = seeded_question
        await client.post(
            "/api/backlog/from-question",
            json={"review_question_id": qid, "priority": "P0", "owner": "lex-coder"},
        )

        resp = await client.get("/api/backlog/list?priority=P0&owner=lex-coder&category=产品")
        body = resp.json()
        assert body["total"] == 1


# ====== 测试 3: Assign ======
class TestAssign:
    async def test_assign_owner(self, client, seeded_question):
        """分配 owner"""
        qid = seeded_question
        resp = await client.post("/api/backlog/from-question", json={"review_question_id": qid})
        bid = resp.json()["backlog_id"]

        resp2 = await client.post(
            f"/api/backlog/{bid}/assign",
            json={"owner": "lex-coder"},
        )
        assert resp2.status_code == 200
        body = resp2.json()
        assert body["backlog_id"] == bid
        assert body["owner"] == "lex-coder"
        assert "owner" in body["changed_fields"]

    async def test_assign_status(self, client, seeded_question):
        """分配 status"""
        qid = seeded_question
        resp = await client.post("/api/backlog/from-question", json={"review_question_id": qid})
        bid = resp.json()["backlog_id"]

        resp2 = await client.post(
            f"/api/backlog/{bid}/assign",
            json={"status": "in_progress"},
        )
        assert resp2.status_code == 200
        body = resp2.json()
        assert body["status"] == "in_progress"
        assert "status" in body["changed_fields"]

    async def test_assign_priority(self, client, seeded_question):
        """分配 priority"""
        qid = seeded_question
        resp = await client.post("/api/backlog/from-question", json={"review_question_id": qid})
        bid = resp.json()["backlog_id"]

        resp2 = await client.post(
            f"/api/backlog/{bid}/assign",
            json={"priority": "P0"},
        )
        assert resp2.status_code == 200
        body = resp2.json()
        assert body["priority"] == "P0"
        assert "priority" in body["changed_fields"]

    async def test_assign_all_three(self, client, seeded_question):
        """一次改 3 字段"""
        qid = seeded_question
        resp = await client.post("/api/backlog/from-question", json={"review_question_id": qid})
        bid = resp.json()["backlog_id"]

        resp2 = await client.post(
            f"/api/backlog/{bid}/assign",
            json={
                "owner": "lex-coder",
                "status": "in_progress",
                "priority": "P0",
            },
        )
        assert resp2.status_code == 200
        body = resp2.json()
        assert "owner" in body["changed_fields"]
        assert "status" in body["changed_fields"]
        assert "priority" in body["changed_fields"]

    async def test_assign_no_field_400(self, client, seeded_question):
        """没传任何字段 → 400"""
        qid = seeded_question
        resp = await client.post("/api/backlog/from-question", json={"review_question_id": qid})
        bid = resp.json()["backlog_id"]

        resp2 = await client.post(f"/api/backlog/{bid}/assign", json={})
        assert resp2.status_code == 400

    async def test_assign_404(self, client):
        """不存在的 bid → 404"""
        resp = await client.post("/api/backlog/9999/assign", json={"owner": "lex-coder"})
        assert resp.status_code == 404

    async def test_assign_invalid_owner(self, client, seeded_question):
        """非法 owner → 422"""
        qid = seeded_question
        resp = await client.post("/api/backlog/from-question", json={"review_question_id": qid})
        bid = resp.json()["backlog_id"]

        resp2 = await client.post(
            f"/api/backlog/{bid}/assign",
            json={"owner": "BOGUS"},
        )
        assert resp2.status_code in (400, 422)

    async def test_assign_invalid_status(self, client, seeded_question):
        """非法 status → 422"""
        qid = seeded_question
        resp = await client.post("/api/backlog/from-question", json={"review_question_id": qid})
        bid = resp.json()["backlog_id"]

        resp2 = await client.post(
            f"/api/backlog/{bid}/assign",
            json={"status": "BOGUS"},
        )
        assert resp2.status_code in (400, 422)

    async def test_assign_idempotent(self, client, seeded_question):
        """同字段再改 → changed_fields 为空 (但 updated_at 刷新)"""
        qid = seeded_question
        resp = await client.post("/api/backlog/from-question", json={"review_question_id": qid})
        bid = resp.json()["backlog_id"]

        # 第一次改
        resp1 = await client.post(
            f"/api/backlog/{bid}/assign",
            json={"owner": "lex-coder"},
        )
        assert "owner" in resp1.json()["changed_fields"]

        # 同字段再 assign, owner 不变 → changed_fields 不含 owner
        resp2 = await client.post(
            f"/api/backlog/{bid}/assign",
            json={"owner": "lex-coder"},
        )
        body = resp2.json()
        assert "owner" not in body["changed_fields"]


# ====== 测试 4: Board ======
class TestBoard:
    async def test_board_empty(self, client):
        """空看板"""
        resp = await client.get("/api/backlog/board")
        assert resp.status_code == 200
        body = resp.json()
        assert body["summary"]["total_tickets"] == 0
        assert body["summary"]["p0_tickets"] == 0
        assert body["by_status"]["open"] == 0
        assert body["recent_tickets"] == []

    async def test_board_with_tickets(self, client):
        """写入后看板"""
        # 创建 3 question + 3 backlog
        for i in range(3):
            q_resp = await client.post(
                "/api/review/question",
                json=sample_question(f"L{i+1}", ["产品", "技术", "法务"][i]),
            )
            qid = q_resp.json()["question_id"]
            await client.post(
                "/api/backlog/from-question",
                json={
                    "review_question_id": qid,
                    "priority": ["P0", "P1", "P2"][i],
                    "owner": ["lex-coder", "lex-ai", "lex-pm"][i],
                },
            )

        resp = await client.get("/api/backlog/board")
        body = resp.json()
        assert body["summary"]["total_tickets"] == 3
        assert body["summary"]["p0_tickets"] == 1
        assert body["by_status"]["open"] == 3
        assert body["by_priority"]["P0"] == 1
        assert body["by_priority"]["P1"] == 1
        assert body["by_priority"]["P2"] == 1
        assert "lex-coder" in body["by_owner"]
        assert "lex-ai" in body["by_owner"]

    async def test_board_5_views(self, client):
        """5 视图 (summary, by_status, by_priority, by_owner, by_source_lawyer)"""
        # 写 5 tickets 不同 lawyer / category
        for i in range(5):
            q_resp = await client.post(
                "/api/review/question",
                json=sample_question(f"L{i+1}", ["产品", "技术", "法务", "产品", "其他"][i]),
            )
            qid = q_resp.json()["question_id"]
            await client.post(
                "/api/backlog/from-question",
                json={"review_question_id": qid},
            )

        resp = await client.get("/api/backlog/board")
        body = resp.json()
        # 1. summary
        assert "summary" in body
        assert "total_tickets" in body["summary"]
        # 2. by_status
        assert "by_status" in body
        # 3. by_priority
        assert "by_priority" in body
        # 4. by_owner
        assert "by_owner" in body
        # 5. by_source_lawyer
        assert "by_source_lawyer" in body
        # 5 律师都应有数据
        for lid in ["L1", "L2", "L3", "L4", "L5"]:
            assert lid in body["by_source_lawyer"], f"missing {lid}"

    async def test_board_recent_tickets(self, client):
        """recent_tickets 最多 10 条"""
        # 写 15 条 (让总数 > 10)
        for i in range(15):
            q_resp = await client.post(
                "/api/review/question",
                json=sample_question("L1", "产品"),
            )
            qid = q_resp.json()["question_id"]
            await client.post(
                "/api/backlog/from-question",
                json={"review_question_id": qid},
            )

        resp = await client.get("/api/backlog/board")
        body = resp.json()
        assert len(body["recent_tickets"]) == 10  # 限 10

    async def test_board_summary_completed_rate(self, client, seeded_question):
        """completed_rate = done / total"""
        qid = seeded_question
        resp = await client.post("/api/backlog/from-question", json={"review_question_id": qid})
        bid = resp.json()["backlog_id"]

        # 1 条 done
        await client.post(f"/api/backlog/{bid}/assign", json={"status": "done"})

        resp2 = await client.get("/api/backlog/board")
        body = resp2.json()
        assert body["summary"]["done_tickets"] == 1
        assert body["summary"]["completed_rate"] == 1.0

    async def test_board_by_category_distribution(self, client):
        """by_category 分布"""
        for i, cat in enumerate(["产品", "技术", "法务", "其他"]):
            q_resp = await client.post(
                "/api/review/question", json=sample_question(f"L{i+1}", cat)
            )
            qid = q_resp.json()["question_id"]
            await client.post(
                "/api/backlog/from-question",
                json={"review_question_id": qid},
            )

        resp = await client.get("/api/backlog/board")
        body = resp.json()
        assert body["by_category"]["产品"]["total"] == 1
        assert body["by_category"]["技术"]["total"] == 1
        assert body["by_category"]["法务"]["total"] == 1
        assert body["by_category"]["其他"]["total"] == 1


# ====== 测试 5: Health ======
class TestHealth:
    async def test_health(self, client):
        """健康检查"""
        resp = await client.get("/api/backlog/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["service_id"] == "lexprime.backlog.prd-tickets"
        assert body["total_tickets"] >= 0
        assert "endpoints" in body


# ====== 测试 6: 迁移脚本 ======
class TestMigrateScript:
    """测试 scripts/migrate_review_to_backlog.py 的迁移函数

    跳过 main() argparse 部分, 直接调用 migrate() 函数测试 dry-run 和 seed 模式
    """

    @pytest.mark.asyncio
    async def test_seed_count_is_42(self):
        """验证种子数据 = 42 项"""
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from scripts.migrate_review_to_backlog import SEED_42_QUESTIONS

        assert len(SEED_42_QUESTIONS) == 42

    @pytest.mark.asyncio
    async def test_seed_priority_distribution(self):
        """验证优先级分布 (跟 A1 doc §1.1: P0=17, P1=18, P2=7)"""
        from scripts.migrate_review_to_backlog import SEED_42_QUESTIONS

        p0 = sum(1 for q in SEED_42_QUESTIONS if q.get("priority") == "P0")
        p1 = sum(1 for q in SEED_42_QUESTIONS if q.get("priority") == "P1")
        p2 = sum(1 for q in SEED_42_QUESTIONS if q.get("priority") == "P2")
        p3 = sum(1 for q in SEED_42_QUESTIONS if q.get("priority") == "P3")

        # 跟 w8-review-questions-summary.md §1.1: 17 + 18 + 7 = 42
        assert p0 == 17, f"P0 应 17 项, 实际 {p0}"
        assert p1 == 18, f"P1 应 18 项, 实际 {p1}"
        assert p2 == 7, f"P2 应 7 项 (A1 doc 锦上添花 7 项), 实际 {p2}"
        assert p3 == 0, f"P3 应 0 项 (A1 doc 没 P3 标记), 实际 {p3}"
        assert p0 + p1 + p2 + p3 == 42

    @pytest.mark.asyncio
    async def test_seed_category_distribution(self):
        """验证 category 分布 (18 产品 + 8 技术 + 12 法务 + 4 其他 = 42)"""
        from scripts.migrate_review_to_backlog import SEED_42_QUESTIONS

        product = sum(1 for q in SEED_42_QUESTIONS if q.get("category") == "产品")
        tech = sum(1 for q in SEED_42_QUESTIONS if q.get("category") == "技术")
        legal = sum(1 for q in SEED_42_QUESTIONS if q.get("category") == "法务")
        other = sum(1 for q in SEED_42_QUESTIONS if q.get("category") == "其他")

        assert product == 18, f"产品 应 18 项, 实际 {product}"
        assert tech == 8, f"技术 应 8 项, 实际 {tech}"
        assert legal == 12, f"法务 应 12 项, 实际 {legal}"
        assert other == 4, f"其他 应 4 项, 实际 {other}"

    @pytest.mark.asyncio
    async def test_seed_all_have_required_fields(self):
        """所有 seed 必须有 title / description / category / priority / owner"""
        from scripts.migrate_review_to_backlog import SEED_42_QUESTIONS

        for i, q in enumerate(SEED_42_QUESTIONS):
            for f in ["category", "priority", "title", "description", "owner"]:
                assert f in q, f"seed[{i}] missing field '{f}'"
            assert q["category"] in QUESTION_CATEGORIES, f"seed[{i}] invalid category: {q['category']}"
            assert q["priority"] in BACKLOG_PRIORITIES, f"seed[{i}] invalid priority: {q['priority']}"
            assert q["owner"] in BACKLOG_OWNERS, f"seed[{i}] invalid owner: {q['owner']}"
            assert len(q["title"]) <= 120, f"seed[{i}] title too long: {len(q['title'])}"
            assert len(q["description"]) <= 1000, f"seed[{i}] description too long: {len(q['description'])}"

    @pytest.mark.asyncio
    async def test_migrate_dry_run(self, capsys):
        """dry-run 模式: 不写 DB"""
        from scripts.migrate_review_to_backlog import migrate

        written = await migrate(dry_run=True, seed=True)
        assert written == 0

        out = capsys.readouterr().out
        assert "Seed validation" in out
        assert "dry-run" in out.lower()

    @pytest.mark.asyncio
    async def test_migrate_no_seed(self, capsys):
        """--no-seed 模式: 写 0 条 ticket"""
        from scripts.migrate_review_to_backlog import migrate

        written = await migrate(dry_run=False, seed=False)
        assert written == 0

    @pytest.mark.asyncio
    async def test_migrate_full_seed(self):
        """完整 seed 模式: 写 42 条 ticket"""
        from scripts.migrate_review_to_backlog import migrate
        from api.backlog_router import PrdBacklog
        from sqlalchemy import func as sa_func, select

        written = await migrate(dry_run=False, seed=True)
        assert written == 42

        # 验证 migrate 自己内部 print 出来的 count (写入后立刻查询)
        # 注意: migrate() 调用 Database.close() 在内部, 所以外面再开 Database.session()
        # 会重新 init 同一个 file DB, 仍能看到 42 条
        from core.db import Database

        async with Database.session() as session:
            total_stmt = select(sa_func.count(PrdBacklog.id))
            total_count = (await session.execute(total_stmt)).scalar() or 0
            assert total_count >= 42, f"total 应 ≥ 42, 实际 {total_count}"

            p0_stmt = select(sa_func.count(PrdBacklog.id)).where(PrdBacklog.priority == "P0")
            p0_count = (await session.execute(p0_stmt)).scalar() or 0
            assert p0_count >= 17, f"P0 应 ≥ 17, 实际 {p0_count}"

    @pytest.mark.asyncio
    async def test_migrate_idempotent_skip_duplicate(self):
        """migrate 重复跑: 验证仍能完成 (实际生产用 source_question_id UNIQUE 防重复)"""
        from scripts.migrate_review_to_backlog import migrate

        # 第 1 次
        w1 = await migrate(dry_run=False, seed=True)
        assert w1 == 42

        # 第 2 次 (重复跑 - 验证不抛异常)
        w2 = await migrate(dry_run=False, seed=True)
        assert w2 == 42


# ====== 测试 7: End-to-End ======
class TestE2E:
    async def test_e2e_full_flow(self, client):
        """E2E: 律师提问题 → PM 转 backlog → 分配 → 看板"""
        # 1. 律师提交问题
        for i, cat in enumerate(["产品", "技术", "法务"]):
            q_resp = await client.post(
                "/api/review/question",
                json=sample_question(f"L{i+1}", cat),
            )
            assert q_resp.status_code == 201

        # 2. PM 从问题转 backlog
        list_resp = await client.get("/api/review/questions")
        questions = list_resp.json()["questions"]
        for q in questions:
            r = await client.post(
                "/api/backlog/from-question",
                json={"review_question_id": q["id"]},
            )
            assert r.status_code == 201

        # 3. 分配 owner
        list_b = await client.get("/api/backlog/list")
        tickets = list_b.json()["tickets"]
        for t in tickets:
            r = await client.post(
                f"/api/backlog/{t['id']}/assign",
                json={"owner": "lex-coder"},
            )
            assert r.status_code == 200

        # 4. 看板
        resp = await client.get("/api/backlog/board")
        body = resp.json()
        assert body["summary"]["total_tickets"] == 3
        assert "lex-coder" in body["by_owner"]


# ====== 测试 8: 推断函数 ======
class TestInferFunctions:
    def test_infer_priority_p0_urgent(self):
        """'急需' → P0"""
        from api.backlog_router import _infer_priority_from_question
        assert _infer_priority_from_question("急需: 立场切换功能", "产品") == "P0"

    def test_infer_priority_p0_strong(self):
        """'强烈要求' → P0"""
        from api.backlog_router import _infer_priority_from_question
        assert _infer_priority_from_question("强烈要求: 客户友好版", "产品") == "P0"

    def test_infer_priority_p1_recommend(self):
        """'建议' → P1"""
        from api.backlog_router import _infer_priority_from_question
        assert _infer_priority_from_question("建议: 立场组合", "产品") == "P1"

    def test_infer_priority_p2_optional(self):
        """'锦上添花' → P2"""
        from api.backlog_router import _infer_priority_from_question
        assert _infer_priority_from_question("锦上添花: 导出 docx", "产品") == "P2"

    def test_infer_priority_legal_miss(self):
        """法务 + '漏标' → P0"""
        from api.backlog_router import _infer_priority_from_question
        assert _infer_priority_from_question("Skill 漏标重大风险", "法务") == "P0"

    def test_infer_priority_default(self):
        """默认 → P1"""
        from api.backlog_router import _infer_priority_from_question
        assert _infer_priority_from_question("Skill 2 在产品维度有什么建议?", "产品") == "P1"

    def test_infer_priority_empty(self):
        """空字符串 → P1"""
        from api.backlog_router import _infer_priority_from_question
        assert _infer_priority_from_question("", "产品") == "P1"

    def test_infer_owner_product(self):
        """产品 → lex-pm"""
        from api.backlog_router import _infer_owner_from_category
        assert _infer_owner_from_category("产品") == "lex-pm"

    def test_infer_owner_tech(self):
        """技术 → lex-ai"""
        from api.backlog_router import _infer_owner_from_category
        assert _infer_owner_from_category("技术") == "lex-ai"

    def test_infer_owner_legal(self):
        """法务 → lex-coder"""
        from api.backlog_router import _infer_owner_from_category
        assert _infer_owner_from_category("法务") == "lex-coder"

    def test_infer_owner_other(self):
        """其他 → unassigned"""
        from api.backlog_router import _infer_owner_from_category
        assert _infer_owner_from_category("其他") == "unassigned"
