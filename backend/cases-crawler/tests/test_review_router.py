"""
W6 律师评审 Score App API Router 测试 (lex-coder · 2026-06-29)

覆盖 5 endpoint:
- GET  /api/review/contracts         5 测试合同 + 5 律师 + 5 维度 metadata
- POST /api/review/submit-score      5 律师 × 1 合同 × 5 维度评分提交
- GET  /api/review/my-scores         律师历史
- GET  /api/review/summary           团队汇总 (平均分 / 方差 / 评论 / prd-feedback v1.0)
- GET  /api/review/health            健康检查

策略:
- pytest-asyncio fixture + httpx.AsyncClient + ASGITransport
- 复用现有 conftest.py DB + lifespan (W2 已经踩过坑, ASGITransport 默认不触发 lifespan)
"""
import pytest_asyncio

from httpx import AsyncClient, ASGITransport


# ====== 常量: 5 律师 + 5 合同 + 5 维度 ======
LAWYER_IDS = ["L1", "L2", "L3", "L4", "L5"]
CONTRACT_IDS = [
    "demo-rental-beijing-2026",
    "demo-loan-shanghai-2026",
    "demo-labor-fulltime-2026",
    "demo-service-tech-2026",
    "demo-sales-goods-2026",
]
DIM_IDS = [
    "fatal_accuracy",
    "suggestion_practicality",
    "strategy_executability",
    "neutrality",
    "ui_flow",
]


def default_scores(seed: int = 5) -> dict:
    """生成 5 维度评分 (默认 5, seed 用于差异)"""
    return {
        "fatal_accuracy": max(0, min(10, 5 + seed - 2)),
        "suggestion_practicality": max(0, min(10, 6 + seed - 2)),
        "strategy_executability": max(0, min(10, 5 + seed - 2)),
        "neutrality": max(0, min(10, 8 + (seed % 2))),
        "ui_flow": max(0, min(10, 4 + seed - 2)),
    }


def default_comments(lawyer_id: str) -> dict:
    """生成示例评论"""
    return {
        "fatal_accuracy": f"{lawyer_id} - 致命风险识别基本到位, 但 1 处租赁合同押金条款漏报",
        "suggestion_practicality": f"{lawyer_id} - 修改建议可执行但缺行业惯例 (房屋租赁)",
        "strategy_executability": f"{lawyer_id} - 谈判策略的 priority_clauses 排序需优化",
        "neutrality": f"{lawyer_id} - 中立性 OK, 无'必败/必胜'等违规",
        "ui_flow": f"{lawyer_id} - UI 流程 5 步内可完成, 但致命条款展开有点慢",
    }


# ====== Fixtures ======
@pytest_asyncio.fixture(scope="function")
async def _shared_engine():
    """共享的 in-memory SQLite engine (供 client + clean_review_scores 共用)"""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from core.models import Base
    from api import review_router  # noqa: F401 触发 ReviewScore 注册到 Base.metadata

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        echo=False,
    )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 把 Database 全局指向 in-memory (避免触发 persistent SQLite init)
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
async def clean_review_scores(_shared_engine):
    """每个测试前清空 review_scores 表 (用 in-memory DB)"""
    engine, factory = _shared_engine
    from api.review_router import ReviewScore
    from sqlalchemy import delete

    async with factory() as session:
        await session.execute(delete(ReviewScore))
        await session.commit()
    yield


# ====== Contracts ======
class TestContracts:
    async def test_contracts_returns_5(self, client):
        """5 测试合同 fixture 加载"""
        resp = await client.get("/api/review/contracts")
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 5
        assert len(body["contracts"]) == 5

    async def test_contracts_cover_5_types(self, client):
        """覆盖 5 大合同类型"""
        resp = await client.get("/api/review/contracts")
        types = {c["contract_type"] for c in resp.json()["contracts"]}
        assert "房屋租赁" in types
        assert "借款合同" in types
        assert "劳动合同" in types
        assert "服务合同" in types
        assert "销售合同" in types

    async def test_contracts_have_expected_risks(self, client):
        """每份合同含预期风险 (fatal/major/advisory)"""
        resp = await client.get("/api/review/contracts")
        for c in resp.json()["contracts"]:
            assert "expected_risks" in c
            assert "fatal" in c["expected_risks"]

    async def test_contracts_provides_lawyer_metadata(self, client):
        """返回律师 metadata (L1-L5 + 类型 + 排期)"""
        resp = await client.get("/api/review/contracts")
        body = resp.json()
        assert len(body["lawyer_options"]) == 5
        for lo in body["lawyer_options"]:
            assert lo["id"] in LAWYER_IDS
            assert lo["type"] in ["单飞", "小所", "中所", "企业法务"]
            assert "7/19" in lo["venue"] or "7/26" in lo["venue"]

    async def test_contracts_provides_dimension_metadata(self, client):
        """返回 5 维度 metadata + 权重"""
        resp = await client.get("/api/review/contracts")
        body = resp.json()
        assert len(body["dimension_meta"]) == 5
        weights = {d["id"]: d["weight"] for d in body["dimension_meta"]}
        # W5 rubric §1.1 权重
        assert weights["fatal_accuracy"] == 0.30
        assert weights["suggestion_practicality"] == 0.25
        assert weights["strategy_executability"] == 0.20
        assert weights["neutrality"] == 0.15
        assert weights["ui_flow"] == 0.10


# ====== Submit Score =====
class TestSubmitScore:
    async def test_submit_basic_scores(self, client):
        """基本提交"""
        payload = {
            "lawyer_id": "L1",
            "contract_id": "demo-rental-beijing-2026",
            "contract_type": "房屋租赁",
            "scores": default_scores(7),
            "comments": default_comments("L1"),
        }
        resp = await client.post("/api/review/submit-score", json=payload)
        assert resp.status_code == 200, f"submit failed: {resp.text}"
        body = resp.json()
        assert body["lawyer_id"] == "L1"
        assert body["contract_id"] == "demo-rental-beijing-2026"
        assert body["contract_type"] == "房屋租赁"
        assert len(body["score_ids"]) == 5  # 展开成 5 行
        # 5 维度算术平均 (default_scores(7) 算出高分)
        assert 8.0 <= body["aggregate_score"] <= 11.0

    async def test_submit_invalid_lawyer(self, client):
        """非法 lawyer_id 拒绝"""
        payload = {
            "lawyer_id": "INVALID",
            "contract_id": "demo-rental-beijing-2026",
            "scores": default_scores(5),
        }
        resp = await client.post("/api/review/submit-score", json=payload)
        assert resp.status_code in (400, 422)

    async def test_submit_invalid_contract(self, client):
        """非法 contract_id 拒绝"""
        payload = {
            "lawyer_id": "L1",
            "contract_id": "demo-bogus-2026",
            "scores": default_scores(5),
        }
        resp = await client.post("/api/review/submit-score", json=payload)
        assert resp.status_code in (400, 422)

    async def test_submit_score_out_of_range(self, client):
        """score 超 0-10 范围拒绝"""
        bad_scores = default_scores()
        bad_scores["fatal_accuracy"] = 15  # 超范围
        payload = {
            "lawyer_id": "L1",
            "contract_id": "demo-rental-beijing-2026",
            "scores": bad_scores,
        }
        resp = await client.post("/api/review/submit-score", json=payload)
        assert resp.status_code in (400, 422)

    async def test_submit_wrong_dimension_count(self, client):
        """scores 维度数量不对拒绝"""
        payload = {
            "lawyer_id": "L1",
            "contract_id": "demo-rental-beijing-2026",
            "scores": {"fatal_accuracy": 5},  # 只 1 个维度
        }
        resp = await client.post("/api/review/submit-score", json=payload)
        assert resp.status_code in (400, 422)

    async def test_submit_unknown_dimension(self, client):
        """未知 dimension 拒绝"""
        bad_scores = default_scores()
        bad_scores["bogus_dimension"] = 5
        payload = {
            "lawyer_id": "L1",
            "contract_id": "demo-rental-beijing-2026",
            "scores": bad_scores,
        }
        resp = await client.post("/api/review/submit-score", json=payload)
        assert resp.status_code in (400, 422)

    async def test_submit_duplicate_conflict(self, client):
        """重复提交同 (lawyer, contract) 5 行 - 409 冲突"""
        payload = {
            "lawyer_id": "L1",
            "contract_id": "demo-rental-beijing-2026",
            "scores": default_scores(7),
            "comments": default_comments("L1"),
        }
        # 首次提交
        resp1 = await client.post("/api/review/submit-score", json=payload)
        assert resp1.status_code == 200
        # 重复提交应 409
        resp2 = await client.post("/api/review/submit-score", json=payload)
        assert resp2.status_code == 409, f"expected 409, got {resp2.status_code}: {resp2.text}"

    async def test_submit_partial_scores(self, client):
        """不传 comments 应 OK (容错)"""
        payload = {
            "lawyer_id": "L1",
            "contract_id": "demo-rental-beijing-2026",
            "scores": default_scores(8),
        }
        resp = await client.post("/api/review/submit-score", json=payload)
        assert resp.status_code == 200

    async def test_submit_comment_too_long(self, client):
        """评论 > 200 字拒绝"""
        bad_comments = default_comments("L1")
        bad_comments["fatal_accuracy"] = "x" * 201
        payload = {
            "lawyer_id": "L1",
            "contract_id": "demo-rental-beijing-2026",
            "scores": default_scores(5),
            "comments": bad_comments,
        }
        resp = await client.post("/api/review/submit-score", json=payload)
        assert resp.status_code in (400, 422)


# ====== My Scores =====
class TestMyScores:
    async def test_my_scores_empty(self, client):
        """无评分时返回空列表"""
        resp = await client.get("/api/review/my-scores?lawyer_id=L1")
        assert resp.status_code == 200
        body = resp.json()
        assert body["lawyer_id"] == "L1"
        assert body["total"] == 0
        assert body["scores"] == []

    async def test_my_scores_after_submit(self, client):
        """提交后能查到"""
        payload = {
            "lawyer_id": "L2",
            "contract_id": "demo-loan-shanghai-2026",
            "scores": default_scores(6),
            "comments": default_comments("L2"),
        }
        await client.post("/api/review/submit-score", json=payload)

        resp = await client.get("/api/review/my-scores?lawyer_id=L2")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 5  # 5 维度行
        assert all(s["lawyer_id"] == "L2" for s in body["scores"])
        assert all(s["dimension"] in DIM_IDS for s in body["scores"])

    async def test_my_scores_filter_by_lawyer(self, client):
        """按 lawyer_id 过滤 (L1 的不会出现在 L2 列表)"""
        # L1 提交
        p1 = {
            "lawyer_id": "L1",
            "contract_id": "demo-rental-beijing-2026",
            "scores": default_scores(5),
        }
        await client.post("/api/review/submit-score", json=p1)

        # L2 提交
        p2 = {
            "lawyer_id": "L2",
            "contract_id": "demo-loan-shanghai-2026",
            "scores": default_scores(6),
        }
        await client.post("/api/review/submit-score", json=p2)

        resp = await client.get("/api/review/my-scores?lawyer_id=L1")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 5
        assert all(s["lawyer_id"] == "L1" for s in body["scores"])


# ====== Summary =====
class TestSummary:
    async def test_summary_empty(self, client):
        """空数据汇总"""
        resp = await client.get("/api/review/summary")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_evaluations"] == 0
        assert body["total_score_rows"] == 0
        assert body["prd_feedback_v1_0"]["decision"] == "数据不足 - 等待律师评审提交"

    async def test_summary_after_5_lawyers_5_contracts(self, client):
        """完整 25 条评分 (5 律师 × 5 合同)"""
        for lawyer in LAWYER_IDS:
            for contract in CONTRACT_IDS:
                payload = {
                    "lawyer_id": lawyer,
                    "contract_id": contract,
                    "contract_type": "房屋租赁",
                    "scores": default_scores(7),
                    "comments": default_comments(lawyer),
                }
                resp = await client.post("/api/review/submit-score", json=payload)
                assert resp.status_code == 200

        resp = await client.get("/api/review/summary")
        body = resp.json()
        assert body["total_evaluations"] == 25
        assert body["total_score_rows"] == 125  # 25 × 5 维度
        assert body["prd_feedback_v1_0"]["passes_threshold"] is True  # 全部 7 分高于门槛

    async def test_summary_per_lawyer_aggregate(self, client):
        """per_lawyer 聚合字段"""
        p = {
            "lawyer_id": "L1",
            "contract_id": "demo-rental-beijing-2026",
            "scores": {
                "fatal_accuracy": 10, "suggestion_practicality": 8,
                "strategy_executability": 6, "neutrality": 10, "ui_flow": 4,
            },
        }
        await client.post("/api/review/submit-score", json=p)

        resp = await client.get("/api/review/summary")
        body = resp.json()
        assert "L1" in body["per_lawyer"]
        l1 = body["per_lawyer"]["L1"]
        # 5 维度评分
        assert l1["dimension_scores"]["fatal_accuracy"] == 10.0
        assert l1["dimension_scores"]["neutrality"] == 10.0
        assert l1["dimension_scores"]["ui_flow"] == 4.0
        # 综合 (加权 W5 rubric §1.3)
        # 0.30*10 + 0.25*8 + 0.20*6 + 0.15*10 + 0.10*4 = 3+2+1.2+1.5+0.4 = 8.1
        assert l1["weighted_score_0_10"] == 8.1
        # rubric 5 分: 8.1/2 = 4.05
        assert 4.0 <= l1["rubric_score_1_5"] <= 4.1

    async def test_summary_per_dimension_variance(self, client):
        """per_dimension 含 mean + stdev"""
        # L1 高分 (10 capped), L2 低分 (3)
        await client.post("/api/review/submit-score", json={
            "lawyer_id": "L1", "contract_id": "demo-rental-beijing-2026",
            "scores": {**default_scores(10)},  # fatal capped at 10
        })
        await client.post("/api/review/submit-score", json={
            "lawyer_id": "L2", "contract_id": "demo-rental-beijing-2026",
            "scores": {**default_scores(0)},  # fatal = 3
        })

        resp = await client.get("/api/review/summary")
        body = resp.json()
        # fatal_accuracy: L1=10 (capped), L2=3 → mean=6.5, stdev > 0
        fatal = body["per_dimension"]["fatal_accuracy"]
        assert fatal["mean"] == 6.5
        assert fatal["stdev"] > 0
        assert fatal["n_lawyers"] == 2

    async def test_summary_pain_points_low_score(self, client):
        """低分自动生成 pain_points"""
        await client.post("/api/review/submit-score", json={
            "lawyer_id": "L1", "contract_id": "demo-rental-beijing-2026",
            "scores": {
                "fatal_accuracy": 3, "suggestion_practicality": 4,
                "strategy_executability": 5, "neutrality": 8, "ui_flow": 7,
            },
        })
        resp = await client.get("/api/review/summary")
        body = resp.json()
        assert body["prd_feedback_v1_0"]["passes_threshold"] is False
        assert len(body["prd_feedback_v1_0"]["pain_points"]) >= 2  # 至少 fatal + suggestion 痛点

    async def test_summary_comments_by_lawyer(self, client):
        """comments_by_lawyer 完整保留评论"""
        await client.post("/api/review/submit-score", json={
            "lawyer_id": "L3", "contract_id": "demo-rental-beijing-2026",
            "scores": default_scores(7),
            "comments": {
                "fatal_accuracy": "L3 评论 - 致命识别 OK",
                "suggestion_practicality": "L3 评论 - 建议实用但表述不专业",
                "strategy_executability": "",
                "neutrality": "",
                "ui_flow": "",
            },
        })
        resp = await client.get("/api/review/summary")
        body = resp.json()
        l3 = body["comments_by_lawyer"]["L3"]
        rental = l3["demo-rental-beijing-2026"]
        assert rental["fatal_accuracy"] == "L3 评论 - 致命识别 OK"
        assert rental["suggestion_practicality"].startswith("L3 评论")


# ====== Health ======
class TestHealth:
    async def test_health(self, client):
        resp = await client.get("/api/review/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["lawyers_count"] == 5
        assert body["contracts_count"] == 5
        assert body["dimensions_count"] == 5
        assert body["expected_evaluations"] == 25
        assert "POST /api/review/submit-score" in body["endpoints"]


# ====== E2E: 25 条评分聚合 (评审完整流程) ======
class TestEndToEnd:
    async def test_full_25_evaluation_flow(self, client):
        """完整 W6 评审流程: 5 律师 × 5 合同 = 25 条评分"""
        # Step 1: 加载合同
        await client.get("/api/review/contracts")

        # Step 2: 5 律师 × 5 合同提交 (使用差异化评分)
        for i, lawyer in enumerate(LAWYER_IDS):
            for j, contract in enumerate(CONTRACT_IDS):
                # 不同律师不同合同给出不同评分 (i+j 控制差异)
                seed = (i + j) % 4 + 6  # 6-9
                scores = {
                    "fatal_accuracy": min(10, max(0, seed + (i % 2))),
                    "suggestion_practicality": min(10, max(0, seed - 1 + (j % 2))),
                    "strategy_executability": min(10, max(0, seed - 2)),
                    "neutrality": min(10, max(0, 9 - (i % 2))),
                    "ui_flow": min(10, max(0, seed - 1)),
                }
                payload = {
                    "lawyer_id": lawyer,
                    "contract_id": contract,
                    "scores": scores,
                    "comments": {d: f"{lawyer}/{contract}/{d} 评论" for d in DIM_IDS},
                }
                resp = await client.post("/api/review/submit-score", json=payload)
                assert resp.status_code == 200

        # Step 3: 汇总
        resp = await client.get("/api/review/summary")
        body = resp.json()
        assert body["total_evaluations"] == 25
        assert body["total_score_rows"] == 125
        # 5 律师全部有评分
        for lid in LAWYER_IDS:
            assert lid in body["per_lawyer"]
            assert body["per_lawyer"][lid]["evaluations_count"] == 5
        # 5 合同全部有评分
        for cid in CONTRACT_IDS:
            assert cid in body["per_contract"]
        # PRD 决策 (基于评分自动生成)
        assert "decision" in body["prd_feedback_v1_0"]
        assert "pain_points" in body["prd_feedback_v1_0"]
