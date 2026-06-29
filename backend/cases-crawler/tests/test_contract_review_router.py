"""
Skill 2 API Router 测试 (W5)

覆盖 4 endpoint:
- POST /api/contract-review/upload     (含 demo fixture 路径)
- GET  /api/contract-review/result/{id}
- POST /api/contract-review/negotiation
- POST /api/contract-review/export
- GET  /api/contract-review/health
- GET  /api/contract-review/fixtures

使用 FastAPI TestClient (同步模式, 跟现有 conftest 一致)
"""
import pytest
from fastapi.testclient import TestClient


# ===== Fixture =====

@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient (W5 dev: 复用现有 app, 不需要 DB)"""
    from api.main import app
    return TestClient(app)


@pytest.fixture(scope="module")
def sample_review_id(client):
    """先跑一次 demo upload, 拿到 review_id 供后续测试用"""
    resp = client.post("/api/contract-review/upload", json={
        "contract_type": "房屋租赁",
        "fixture_id": "demo-rental-beijing-2026",
        "stance": "乙方",
    })
    assert resp.status_code == 200, f"upload failed: {resp.text}"
    return resp.json()["review_id"]


# ===== Health =====

class TestHealth:
    def test_health_returns_ok(self, client):
        """health 应该返回 200 + skill metadata"""
        resp = client.get("/api/contract-review/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["skill_id"] == "lexprime.skill.contract-review"
        assert body["version"].startswith("0.2.0")
        assert body["fixtures_available"] == 5
        assert len(body["endpoints"]) == 4


class TestFixtures:
    def test_fixtures_returns_5(self, client):
        """fixtures 应该返回 5 份合同"""
        resp = client.get("/api/contract-review/fixtures")
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 5
        assert len(body["fixtures"]) == 5

    def test_fixtures_cover_5_types(self, client):
        """fixtures 覆盖 5 大合同类型"""
        resp = client.get("/api/contract-review/fixtures")
        types = {f["contract_type"] for f in resp.json()["fixtures"]}
        assert types == {"房屋租赁", "借款合同", "劳动合同", "服务合同", "销售合同"}


# ===== Upload =====

class TestUpload:
    def test_upload_with_fixture_id(self, client):
        """用 fixture_id 走 demo 路径"""
        resp = client.post("/api/contract-review/upload", json={
            "contract_type": "房屋租赁",
            "fixture_id": "demo-rental-beijing-2026",
            "stance": "乙方",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "completed"
        assert body["demo_mode"] is True
        assert body["fixture_id"] == "demo-rental-beijing-2026"
        assert body["review_id"].startswith("cr-")
        assert body["latency_ms"] >= 0
        assert body["next"].startswith("GET /api/contract-review/result/")

    def test_upload_with_real_text(self, client):
        """用真实合同文本走 reviewer 路径"""
        real_text = """第一条 标的
甲方将位于上海市浦东新区某路 100 号的房屋出租给乙方使用。
第二条 租金
月租金 10,000 元,逾期按日千分之五加收违约金。
第三条 违约
乙方逾期支付租金超过 15 日的,甲方有权单方解除合同。"""
        resp = client.post("/api/contract-review/upload", json={
            "contract_type": "房屋租赁",
            "contract_text": real_text,
            "stance": "乙方",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["demo_mode"] is False
        assert body["fixture_id"] is None

    def test_upload_with_empty_text_and_no_fixture_fails(self, client):
        """文本为空且无 fixture_id 应报错"""
        resp = client.post("/api/contract-review/upload", json={
            "contract_type": "房屋租赁",
            "contract_text": "",
            "stance": "乙方",
        })
        assert resp.status_code == 400
        assert "必填" in resp.json()["detail"] or "fixture_id" in resp.json()["detail"]

    def test_upload_with_unknown_fixture_fails(self, client):
        """未知 fixture_id 应 404"""
        resp = client.post("/api/contract-review/upload", json={
            "contract_type": "房屋租赁",
            "fixture_id": "demo-not-exist-2099",
            "stance": "乙方",
        })
        assert resp.status_code == 404

    def test_upload_text_too_long_truncated(self, client):
        """接近上限 (50000 字) 应能跑通 (reviewer 内部 context 压缩, 不报错)"""
        # 49000 字 (在 50000 字以内, 但条款多到需要 context 压缩)
        long_text = "第一条 测试\n" + "x" * 49000
        resp = client.post("/api/contract-review/upload", json={
            "contract_type": "服务合同",
            "contract_text": long_text,
            "stance": "审查方",
        })
        # 跑通 + 走 context 压缩
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "completed"


# ===== Result =====

class TestResult:
    def test_get_result_returns_full_review(self, client, sample_review_id):
        """获取完整审查结果"""
        resp = client.get(f"/api/contract-review/result/{sample_review_id}")
        assert resp.status_code == 200
        body = resp.json()
        # 验证完整 schema
        assert "query_meta" in body
        assert "clause_reviews" in body
        assert "risk_summary" in body
        assert "negotiation_strategy" in body
        assert "disclaimer" in body
        assert "ui_hints" in body
        # 验证 ui_hints 含 traffic_light
        assert "traffic_light" in body["ui_hints"]

    def test_get_result_unknown_id_404(self, client):
        """不存在的 review_id 应 404"""
        resp = client.get("/api/contract-review/result/cr-nonexistent")
        assert resp.status_code == 404


# ===== Negotiation =====

class TestNegotiation:
    def test_negotiation_returns_strategy(self, client, sample_review_id):
        """谈判策略接口返回 strategy"""
        resp = client.post("/api/contract-review/negotiation", json={
            "review_id": sample_review_id,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "strategy" in body
        assert "stance" in body
        assert "disclaimer" in body

    def test_negotiation_stance_switch(self, client, sample_review_id):
        """切换立场应调整 stance_specific_advice"""
        resp_a = client.post("/api/contract-review/negotiation", json={
            "review_id": sample_review_id,
            "stance": "甲方",
        })
        resp_b = client.post("/api/contract-review/negotiation", json={
            "review_id": sample_review_id,
            "stance": "乙方",
        })
        # 立场建议文字应不同 (因为立场不同)
        advice_a = resp_a.json()["strategy"]["stance_specific_advice"]
        advice_b = resp_b.json()["strategy"]["stance_specific_advice"]
        # 至少 "甲方" 应在 advice_a 中, "乙方" 在 advice_b 中
        assert "甲方" in advice_a or "乙方" in advice_a
        assert "乙方" in advice_b or "甲方" in advice_b
        # 如果都包含, 应有差异
        if "甲方" in advice_a and "乙方" in advice_b:
            assert advice_a != advice_b

    def test_negotiation_additional_priorities(self, client, sample_review_id):
        """额外优先条款应合并"""
        resp = client.post("/api/contract-review/negotiation", json={
            "review_id": sample_review_id,
            "additional_priorities": ["clause-99", "clause-98"],
        })
        assert resp.status_code == 200
        priorities = resp.json()["strategy"]["priority_clauses"]
        assert "clause-99" in priorities
        assert "clause-98" in priorities

    def test_negotiation_unknown_id_404(self, client):
        resp = client.post("/api/contract-review/negotiation", json={
            "review_id": "cr-nonexistent",
        })
        assert resp.status_code == 404


# ===== Export =====

class TestExport:
    def test_export_markdown(self, client, sample_review_id):
        """Markdown 导出"""
        resp = client.post("/api/contract-review/export", json={
            "review_id": sample_review_id,
            "format": "markdown",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["format"] == "markdown"
        assert body["filename"].endswith(".md")
        assert "# 合同风险审查报告" in body["content"]
        assert body["size_bytes"] > 1000

    def test_export_html(self, client, sample_review_id):
        """HTML 导出"""
        resp = client.post("/api/contract-review/export", json={
            "review_id": sample_review_id,
            "format": "html",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["format"] == "html"
        assert body["filename"].endswith(".html")
        assert 'class="contract-review-report"' in body["content"]

    def test_export_word_fallback_to_markdown(self, client, sample_review_id):
        """Word 导出 (W5 占位返回 Markdown)"""
        resp = client.post("/api/contract-review/export", json={
            "review_id": sample_review_id,
            "format": "word",
        })
        assert resp.status_code == 200
        body = resp.json()
        # W5 占位
        assert body["format"] == "word"
        assert body["content"]

    def test_export_pdf_fallback_to_markdown(self, client, sample_review_id):
        """PDF 导出 (W5 占位返回 Markdown)"""
        resp = client.post("/api/contract-review/export", json={
            "review_id": sample_review_id,
            "format": "pdf",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["format"] == "pdf"

    def test_export_unknown_format_400(self, client, sample_review_id):
        """不支持的格式应 422 (Pydantic 校验) 或 400"""
        resp = client.post("/api/contract-review/export", json={
            "review_id": sample_review_id,
            "format": "rtf",  # 不支持
        })
        assert resp.status_code in (400, 422), f"期望 400/422, 实际 {resp.status_code}"

    def test_export_without_strategy(self, client, sample_review_id):
        """不含策略的导出应移除谈判策略段"""
        resp = client.post("/api/contract-review/export", json={
            "review_id": sample_review_id,
            "format": "markdown",
            "include_strategy": False,
        })
        assert resp.status_code == 200
        content = resp.json()["content"]
        assert "## 三、谈判策略" not in content

    def test_export_unknown_id_404(self, client):
        resp = client.post("/api/contract-review/export", json={
            "review_id": "cr-nonexistent",
            "format": "markdown",
        })
        assert resp.status_code == 404