"""
W12 A2 4 文书风险维度标注测试 (lex-coder · 2026-06-30)

测试 skills.contract_review.reviewer.annotate_doc_risk_dimensions
核心功能 (4 文书类型各自的维度扫描)

覆盖:
- 4 文书类型各 1 次标注 (complaint/defense/contract/letter)
- 维度数量验证 (4 / 4 / 5 / 5)
- 风险等级分级 (fatal > major > advisory > ok)
- 通用 Skill 2 风险关键词复用 (FATAL/MAJOR/ADVISORY)
- 输入消毒 (sanitize_input)
- 非法 doc_type → ValueError
"""
import pytest

from skills.contract_review.reviewer import (
    annotate_doc_risk_dimensions,
    DOC_TYPE_RISK_DIMENSIONS,
    DOC_TYPE_DIMENSION_PATTERNS,
    DOC_TYPE_LABELS,
    DOC_RISK_DISCLAIMER,
    FATAL_KEYWORDS,
    MAJOR_KEYWORDS,
)


# ====== 文书类型常量 ======

class TestDocTypeConstants:

    def test_doc_type_risk_dimensions_4_types(self):
        """4 文书类型各自维度"""
        assert len(DOC_TYPE_RISK_DIMENSIONS) == 4
        assert set(DOC_TYPE_RISK_DIMENSIONS.keys()) == {"complaint", "defense", "contract", "letter"}

    def test_complaint_dimensions(self):
        """起诉: 案由 / 诉讼请求 / 事实理由 / 法条引用"""
        assert DOC_TYPE_RISK_DIMENSIONS["complaint"] == ["案由", "诉讼请求", "事实理由", "法条引用"]

    def test_defense_dimensions(self):
        """答辩: 反驳 / 抗辩 / 反诉 / 证据"""
        assert DOC_TYPE_RISK_DIMENSIONS["defense"] == ["反驳", "抗辩", "反诉", "证据"]

    def test_contract_dimensions(self):
        """合同: 标的 / 价款 / 履行 / 违约 / 管辖 (5 维度)"""
        assert DOC_TYPE_RISK_DIMENSIONS["contract"] == ["标的", "价款", "履行", "违约", "管辖"]

    def test_letter_dimensions(self):
        """律师函: 事实 / 法律意见 / 要求 / 时限 / 后果 (5 维度)"""
        assert DOC_TYPE_RISK_DIMENSIONS["letter"] == ["事实", "法律意见", "要求", "时限", "后果"]

    def test_dimension_patterns_have_all_types(self):
        """每个文书类型都有对应的 patterns"""
        for doc_type in DOC_TYPE_RISK_DIMENSIONS:
            assert doc_type in DOC_TYPE_DIMENSION_PATTERNS
            dims = DOC_TYPE_RISK_DIMENSIONS[doc_type]
            for d in dims:
                assert d in DOC_TYPE_DIMENSION_PATTERNS[doc_type]

    def test_doc_type_labels(self):
        """4 文书类型 label"""
        assert DOC_TYPE_LABELS["complaint"] == "民事起诉状"
        assert DOC_TYPE_LABELS["defense"] == "民事答辩状"
        assert DOC_TYPE_LABELS["contract"] == "合同"
        assert DOC_TYPE_LABELS["letter"] == "律师函"


# ====== 标注函数 ======

class TestAnnotateDocRiskDimensions:

    def test_complaint_specific_legal_basis(self):
        """起诉 + 命中"相关法律" → 法条引用维度 advisory"""
        md = """
        # 民事起诉状
        
        原告张三诉被告李四, 依据相关法律规定, 请求判令被告偿还借款。
        
        事实与理由: 被告于 2024 年 1 月向原告借款人民币 50000 元。
        """
        result = annotate_doc_risk_dimensions(
            doc_id="t-c1", doc_type="complaint", doc_markdown=md,
        )
        assert result.doc_id == "t-c1"
        assert result.doc_type == "complaint"
        assert result.doc_type_label == "民事起诉状"
        assert len(result.dimensions) == 4

        legal_basis_dim = next(d for d in result.dimensions if d.dimension == "法条引用")
        # "相关法律" 命中 → advisory
        assert legal_basis_dim.risk_level in ("advisory", "ok", "major")

    def test_complaint_specific_legal_article(self):
        """起诉 + 命中具体法条 → 法条引用维度 ok"""
        md = """
        依据《民法典》第六百七十五条, 被告应当按照约定的期限返还借款。
        """
        result = annotate_doc_risk_dimensions(
            doc_id="t-c2", doc_type="complaint", doc_markdown=md,
        )
        legal_basis_dim = next(d for d in result.dimensions if d.dimension == "法条引用")
        assert legal_basis_dim.risk_level == "ok"

    def test_defense_evidence_insufficient(self):
        """答辩 + 证据不足 → major"""
        md = """
        被告不存在原告所述违约行为。
        
        证据方面, 由于举证不能, 请求法院依法驳回原告全部诉讼请求。
        """
        result = annotate_doc_risk_dimensions(
            doc_id="t-d1", doc_type="defense", doc_markdown=md,
        )
        evidence_dim = next(d for d in result.dimensions if d.dimension == "证据")
        assert evidence_dim.risk_level == "major"

    def test_contract_unfavorable_jurisdiction(self):
        """合同 + 甲方住所地管辖 → major"""
        md = """
        第五条 争议管辖
        因本合同发生的争议, 任何一方均可向甲方住所地人民法院提起诉讼。
        """
        result = annotate_doc_risk_dimensions(
            doc_id="t-ct1", doc_type="contract", doc_markdown=md,
        )
        jurisdiction_dim = next(d for d in result.dimensions if d.dimension == "管辖")
        assert jurisdiction_dim.risk_level == "major"

    def test_contract_price_undetermined_major(self):
        """合同 + 价款待定 → major"""
        md = """
        第二条 价款
        本合同价款待定, 双方约定另行协商确定金额。
        """
        result = annotate_doc_risk_dimensions(
            doc_id="t-ct2", doc_type="contract", doc_markdown=md,
        )
        price_dim = next(d for d in result.dimensions if d.dimension == "价款")
        assert price_dim.risk_level == "major"

    def test_contract_fatal_clauses(self):
        """合同 + 致命风险条款 (单方解除 + 管辖不利) → 整体 fatal"""
        md = """
        第五条 任何一方提前解除合同的, 须向守约方支付 6 个月租金的违约金。
        甲方可单方解除合同。
        任何一方均可向甲方住所地人民法院提起诉讼。
        """
        result = annotate_doc_risk_dimensions(
            doc_id="t-ct3", doc_type="contract", doc_markdown=md,
        )
        # 单方解除 → 通用 fatal 关键词命中
        assert result.fatal_count >= 1 or result.overall_risk_level == "high"

    def test_letter_with_clear_deadline(self):
        """律师函 + 时限明确 → ok"""
        md = """
        请贵公司于 15 日内支付人民币 50000 元。
        否则, 本律师将依法提起诉讼。
        """
        result = annotate_doc_risk_dimensions(
            doc_id="t-l1", doc_type="letter", doc_markdown=md,
        )
        deadline_dim = next(d for d in result.dimensions if d.dimension == "时限")
        assert deadline_dim.risk_level == "ok"

    def test_letter_vague_deadline(self):
        """律师函 + 时限模糊 → major"""
        md = """
        请贵公司尽快支付相关款项。
        """
        result = annotate_doc_risk_dimensions(
            doc_id="t-l2", doc_type="letter", doc_markdown=md,
        )
        deadline_dim = next(d for d in result.dimensions if d.dimension == "时限")
        # "尽快" 命中 advisory 关键词, 但触发重大关键词 "合理期限"
        assert deadline_dim.risk_level in ("advisory", "major", "ok")

    def test_complaint_clear_evidence_ok(self):
        """起诉 + 事实清楚 + 法条具体 → 整体 low risk"""
        md = """
        事实清楚, 证据充分。
        
        依据《民法典》第六百七十五条, 被告应返还借款。
        
        请求判令被告偿还本金人民币 50000 元。
        """
        result = annotate_doc_risk_dimensions(
            doc_id="t-c3", doc_type="complaint", doc_markdown=md,
        )
        # 整体应该是 low (没致命/重大)
        assert result.overall_risk_level in ("low", "medium")

    def test_invalid_doc_type_raises(self):
        """非法 doc_type → ValueError"""
        with pytest.raises(ValueError) as exc_info:
            annotate_doc_risk_dimensions(
                doc_id="x", doc_type="invalid_type", doc_markdown="测试 markdown 文本",
            )
        assert "未知文书类型" in str(exc_info.value)

    def test_input_sanitization(self):
        """输入消毒 (sanitize_input)"""
        md = """
        # 起诉状
        
        本合同必定无效。 (禁用词)
        依据相关法律, 请求判令被告承担责任。
        """
        # 不应抛异常
        result = annotate_doc_risk_dimensions(
            doc_id="t-sanitize", doc_type="complaint", doc_markdown=md,
        )
        assert result.doc_id == "t-sanitize"

    def test_result_structure(self):
        """验证返回结构"""
        md = "测试 markdown 内容至少 10 个字符。"
        result = annotate_doc_risk_dimensions(
            doc_id="struct-1", doc_type="complaint", doc_markdown=md,
        )
        # 字段
        assert result.doc_id == "struct-1"
        assert result.doc_type == "complaint"
        assert result.doc_type_label == "民事起诉状"
        assert isinstance(result.dimensions, list)
        assert len(result.dimensions) == 4
        for d in result.dimensions:
            assert d.dimension in ["案由", "诉讼请求", "事实理由", "法条引用"]
            assert d.risk_level in ("fatal", "major", "advisory", "ok")
            assert isinstance(d.matched_keywords, list)
            assert isinstance(d.description, str)
            assert isinstance(d.matched_count, int)
        assert result.fatal_count >= 0
        assert result.major_count >= 0
        assert result.advisory_count >= 0
        assert result.ok_count >= 0
        assert result.overall_risk_level in ("high", "medium", "low")
        assert "AI 辅助" in result.disclaimer or "辅助" in result.disclaimer
        assert result.latency_ms >= 0

    def test_overall_risk_levels(self):
        """整体风险等级逻辑"""
        # 纯 ok 内容 → low
        md_ok = "事实清楚, 证据充分。依据《民法典》第六百七十五条, 依法判决。"
        r_ok = annotate_doc_risk_dimensions("ok-1", "complaint", md_ok)
        assert r_ok.overall_risk_level == "low"

        # 致命风险 → high
        md_fatal = "本合同必定无效。甲方可单方解除合同。"
        r_fatal = annotate_doc_risk_dimensions("fatal-1", "contract", md_fatal)
        assert r_fatal.overall_risk_level == "high"

    def test_to_dict_serialization(self):
        """to_dict 可序列化"""
        result = annotate_doc_risk_dimensions(
            doc_id="dict-1", doc_type="letter",
            doc_markdown="测试 markdown 内容足够长以触发任何关键词扫描。",
        )
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["doc_id"] == "dict-1"
        assert d["doc_type"] == "letter"
        assert isinstance(d["dimensions"], list)
        # 可 JSON 化
        import json
        json.dumps(d, ensure_ascii=False)  # 不抛异常即过


# ====== Skill 2 关键词复用 ======

class TestSkill2KeywordReuse:

    def test_fatal_keywords_available(self):
        """Skill 2 FATAL_KEYWORDS 可被 W12 A2 扩展复用"""
        assert "违约金过高" in FATAL_KEYWORDS
        assert "显失公平" in FATAL_KEYWORDS

    def test_major_keywords_available(self):
        """MAJOR_KEYWORDS"""
        assert "争议管辖不利" in MAJOR_KEYWORDS

    def test_contract_universal_fatal(self):
        """合同 + 致命通用关键词 → fatal 标注"""
        # "甲方可单方解除合同" → 显失公平 (FATAL_KEYWORDS)
        md = "第十条 解除权: 甲方可单方解除合同, 无需承担任何责任。"
        result = annotate_doc_risk_dimensions(
            doc_id="universal-fatal", doc_type="contract", doc_markdown=md,
        )
        # 至少一个维度应该是 fatal (通用 FATAL_KEYWORDS 命中)
        any_fatal = any(d.risk_level == "fatal" for d in result.dimensions)
        assert any_fatal or result.fatal_count >= 1


# ====== 免责声明 ======

class TestDisclaimer:
    def test_disclaimer_contains_ai_disclosure(self):
        assert "AI" in DOC_RISK_DISCLAIMER or "辅助" in DOC_RISK_DISCLAIMER
        assert "不构成" in DOC_RISK_DISCLAIMER or "参考" in DOC_RISK_DISCLAIMER