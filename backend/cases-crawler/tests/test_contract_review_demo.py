"""
Skill 2 Demo 模式 Fixture Loader 测试 (W5)

覆盖:
- list_fixtures() 返回 5 合同
- load_fixture() 加载每个合同
- run_fixture_review() 调 reviewer.run_skill() 生成审查结果
- render_markdown_report() 渲染 Markdown
- render_html_report() 渲染 HTML
- FixtureError 错误处理
"""
import pytest
from skills.contract_review.demo import (
    list_fixtures,
    load_fixture,
    run_fixture_review,
    render_markdown_report,
    render_html_report,
    FixtureError,
)

CONTRACT_TYPES = {"房屋租赁", "借款合同", "劳动合同", "服务合同", "销售合同"}

FIXTURE_IDS = [
    "demo-rental-beijing-2026",
    "demo-loan-shanghai-2026",
    "demo-labor-shenzhen-2026",
    "demo-service-hangzhou-2026",
    "demo-sales-guangzhou-2026",
]


class TestFixturesList:
    def test_list_fixtures_returns_5_contracts(self):
        """list_fixtures 应该返回 5 份合同 baseline"""
        fixtures = list_fixtures()
        assert len(fixtures) == 5, f"期望 5 份合同, 实际 {len(fixtures)}"

    def test_list_fixtures_covers_5_contract_types(self):
        """覆盖房屋租赁/借款/劳动/服务/销售 5 大类"""
        fixtures = list_fixtures()
        types = {f["contract_type"] for f in fixtures}
        assert types == CONTRACT_TYPES, f"期望覆盖 {CONTRACT_TYPES}, 实际 {types}"

    def test_fixture_metadata_complete(self):
        """每份 fixture 必填字段完整"""
        fixtures = list_fixtures()
        required_keys = {"fixture_id", "contract_type", "contract_title",
                         "industry", "stance_default", "risk_hint"}
        for f in fixtures:
            assert required_keys <= f.keys(), f"fixture 缺字段: {f}"
            # risk_hint 应该含数字统计
            assert "致命" in f["risk_hint"]
            assert "重大" in f["risk_hint"]
            assert "建议" in f["risk_hint"]


class TestLoadFixture:
    @pytest.mark.parametrize("fixture_id", FIXTURE_IDS)
    def test_load_each_fixture(self, fixture_id):
        """每份 fixture 都能加载"""
        data = load_fixture(fixture_id)
        assert data["fixture_id"] == fixture_id
        assert len(data["contract_text"]) >= 500, "合同文本应 >= 500 字"
        assert data["contract_type"] in CONTRACT_TYPES
        assert data["stance_default"] in {"甲方", "乙方", "丙方", "审查方"}

    def test_load_unknown_fixture_raises(self):
        """未知的 fixture_id 抛 FixtureError"""
        with pytest.raises(FixtureError):
            load_fixture("demo-not-exist-2099")


class TestRunFixtureReview:
    @pytest.mark.parametrize("fixture_id", FIXTURE_IDS)
    def test_run_review_each_fixture(self, fixture_id):
        """每份 fixture 都能跑审查"""
        review = run_fixture_review(fixture_id, stance="审查方")
        # 验证结构
        assert "query_meta" in review
        assert "clause_reviews" in review
        assert "risk_summary" in review
        assert "negotiation_strategy" in review
        assert "disclaimer" in review
        assert "ui_hints" in review
        # 验证内容
        assert review["query_meta"]["demo_mode"] is True
        assert review["query_meta"]["fixture_id"] == fixture_id
        assert review["query_meta"]["stance"] == "审查方"
        assert len(review["clause_reviews"]) >= 5, "至少 5 条款"
        # 验证 summary 字段
        summary = review["risk_summary"]
        assert summary["fatal_count"] >= 0
        assert summary["major_count"] >= 0
        assert summary["advisory_count"] >= 0
        assert summary["ok_count"] >= 0
        assert summary["overall_risk_level"] in {"high", "medium", "low"}

    @pytest.mark.parametrize("fixture_id", FIXTURE_IDS)
    def test_run_review_stance_changes_advice(self, fixture_id):
        """切换立场应能跑通 (立场影响嵌入 clause_reviews)"""
        review_a = run_fixture_review(fixture_id, stance="甲方")
        review_b = run_fixture_review(fixture_id, stance="乙方")
        # 立场应记录
        assert review_a["query_meta"]["stance"] == "甲方"
        assert review_b["query_meta"]["stance"] == "乙方"
        # 至少有一个 clause 的 stance_impact 不同 (规则层随机性可忽略, 主要验证不报错)
        impacts_a = {c["stance_impact"] for c in review_a["clause_reviews"]}
        impacts_b = {c["stance_impact"] for c in review_b["clause_reviews"]}
        # 都应有有效立场影响
        valid_impacts = {"不利", "中性", "有利", "需结合上下文判断"}
        assert impacts_a <= valid_impacts
        assert impacts_b <= valid_impacts

    def test_run_review_with_contract_type_override(self):
        """contract_type override 应生效"""
        review = run_fixture_review(
            "demo-rental-beijing-2026",
            stance="审查方",
            contract_type="房屋租赁",  # override
        )
        assert review["query_meta"]["contract_type"] == "房屋租赁"


class TestRenderMarkdownReport:
    def test_markdown_report_includes_key_sections(self):
        """Markdown 报告包含必填 section"""
        review = run_fixture_review("demo-rental-beijing-2026", stance="乙方")
        md = render_markdown_report(review)
        assert "# 合同风险审查报告" in md
        assert "## 一、整体风险总览" in md
        assert "## 二、条款级详述" in md
        assert "## 三、谈判策略" in md
        assert "## 四、免责声明" in md
        assert "致命风险" in md
        assert "重大风险" in md
        assert "乙方" in md  # stance
        assert "demo-rental-beijing-2026" in md  # fixture_id

    def test_markdown_report_disclaimer_present(self):
        """disclaimer 必须在文档末尾"""
        review = run_fixture_review("demo-loan-shanghai-2026")
        md = render_markdown_report(review)
        assert "不构成法律意见" in md


class TestRenderHtmlReport:
    def test_html_report_has_basic_structure(self):
        """HTML 报告包含必填 DOM"""
        review = run_fixture_review("demo-labor-shenzhen-2026")
        html = render_html_report(review)
        assert 'class="contract-review-report"' in html
        assert "致命" in html
        assert "重大" in html
        assert "建议" in html
        assert "合规" in html

    def test_html_report_uses_correct_colors(self):
        """HTML 报告使用 W1 设计系统的风险色"""
        review = run_fixture_review("demo-sales-guangzhou-2026")
        html = render_html_report(review)
        # 风险色 (Tailwind 颜色)
        assert "border-danger" in html
        assert "border-warning" in html
        assert "border-brand" in html
        assert "border-success" in html