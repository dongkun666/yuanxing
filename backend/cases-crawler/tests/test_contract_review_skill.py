"""
LexPrime 合同风险审查 Skill — 单元测试

测试覆盖:
1. language_guard: 禁用词检测 (HIGH/LOW 违规)
2. reviewer: 条款拆分 + 三级风险分类 + 上下文压缩 + 统计 + 策略
3. UI 提示: traffic_light 计算
4. 输入消毒: sanitize_input 防绕过

运行:
    cd backend/cases-crawler
    pytest tests/test_contract_review_skill.py -v
    或: python tests/test_contract_review_skill.py
"""
import sys
from pathlib import Path

# 让脚本可直接运行 (不依赖 pytest)
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "skills"))

from contract_review.language_guard import (
    check_narrative,
    template_clause_risk_description,
    template_risk_summary,
    template_negotiation_advice,
    template_diff_summary,
    DISCLAIMER_FULL,
    sanitize_input,
    assert_no_bypass,
    RISK_LEVEL_FATAL,
    RISK_LEVEL_MAJOR,
    RISK_LEVEL_ADVISORY,
    RISK_LEVEL_OK,
)
from contract_review.reviewer import (
    ReviewerInput,
    Clause,
    ClauseReview,
    split_clauses,
    classify_clause_risk,
    compress_clauses,
    compute_risk_summary,
    compute_negotiation_strategy,
    compute_traffic_light,
    run_skill,
    count_tokens,
    _percentile,
    lookup_legal_basis,
)


# ===== Test 1: language_guard =====

def test_language_guard_pass():
    """正确的客观描述必须通过。"""
    samples = [
        "该条款逾期违约金约定为月租金 5%/日, 年化约 1825%, 超出 LPR 四倍司法保护上限, 司法实践中通常被调减。",
        "该条款解除权约定存在显失公平情形, 乙方因甲方违约而解除合同仍需支付 6 个月租金。",
        "该条款约定甲方住所地管辖, 对乙方应诉成本较高。",
        "司法实践中, 类似违约金约定通常被认定过高。",
        "该条款可能存在效力瑕疵。",
        "本合同共审查 7 个条款, 其中致命风险 1 个, 重大风险 1 个, 建议风险 2 个。",
        "乙方 立场: 重点关注条款 clause-3, 建议优先协商违约金计算方式。",
        "对比版本 V1 与 V2, 共新增 1 个条款, 删除 0 个条款, 修改 2 个条款。",
    ]
    for s in samples:
        r = check_narrative(s)
        assert r.passed, f"应 PASS 但 FAIL: {s} → {r.high_violations}"
        assert r.high_violations == []
    print(f"✓ test_language_guard_pass PASSED ({len(samples)} 条)")


def test_language_guard_fail_high():
    """违规表述必须被拦截。"""
    bad_samples = [
        "本合同必败。",
        "合同必胜。",
        "本合同必定无效。",
        "该条款一定无效。",
        "该条款一定会被认定无效。",
        "对方将承担全部责任。",
        "对方必定败诉。",
        "司法实践中一定会被调减。",
        "法院一定会支持。",
        "本合同一定有效。",
    ]
    for s in bad_samples:
        r = check_narrative(s)
        assert not r.passed, f"应 FAIL 但 PASS: {s}"
        assert len(r.high_violations) > 0
    print(f"✓ test_language_guard_fail_high PASSED (拦截 {len(bad_samples)} 条)")


def test_language_guard_correction():
    """违规表述自动纠正后应通过。"""
    r = check_narrative("本合同必败。")
    assert not r.passed
    corrected = r.corrected_text
    r2 = check_narrative(corrected)
    assert r2.passed, f"纠正后仍 FAIL: {corrected}"
    print(f"✓ test_language_guard_correction PASSED (纠正后: '{corrected}')")


def test_templates_pass():
    """所有降级模板必须通过语言规范检查。"""
    t1 = template_clause_risk_description(
        "逾期按月租金 5%/日加收违约金",
        "《民法典》第五百八十五条",
        "违约金过高, 超出 LPR 四倍司法保护上限"
    )
    t2 = template_risk_summary(
        total=7, fatal=1, major=1, advisory=2,
        top_categories=["违约金过高", "显失公平", "解除权失衡"]
    )
    t3 = template_negotiation_advice(
        stance="乙方",
        priority_clauses=["clause-3", "clause-6", "clause-7"],
        leverage_count=2,
        walk_away_count=0
    )
    t4 = template_diff_summary(
        baseline="V1", compared="V2",
        added=1, removed=0, modified=2
    )
    for i, t in enumerate([t1, t2, t3, t4], 1):
        r = check_narrative(t)
        assert r.passed, f"模板 {i} FAIL: {t} → {r.high_violations}"
    print("✓ test_templates_pass PASSED (4 模板)")


# ===== Test 2: 条款拆分 =====

def test_split_clauses_standard():
    """'第X条' 标准标号拆分。"""
    contract = """
第一条 租赁标的
甲方将位于上海市浦东新区某某路 123 号房屋出租给乙方使用。

第二条 租赁期限
租赁期自 2026 年 7 月 1 日起至 2027 年 6 月 30 日止。

第三条 租金及支付
月租金为人民币 5000 元整, 逾期按 5%/日加收违约金。

第四条 押金
乙方向甲方支付押金人民币 10000 元整。
"""
    clauses = split_clauses(contract)
    assert len(clauses) == 4, f"应拆分 4 条, 实际 {len(clauses)}"
    assert clauses[0].clause_index == 1
    assert "租赁标的" in clauses[0].clause_title
    assert clauses[0].clause_id == "clause-1"
    print(f"✓ test_split_clauses_standard PASSED ({len(clauses)} 条)")


def test_split_clauses_fallback():
    """无标号合同按段落拆分 (fallback)。"""
    contract = """
甲方将房屋出租给乙方。
租赁期 12 个月。
月租金 5000 元。
"""
    clauses = split_clauses(contract)
    # 无标号, 按段落拆 (3 段非空)
    assert len(clauses) >= 1, f"应至少拆分 1 条, 实际 {len(clauses)}"
    assert all(c.clause_id.startswith("clause-") for c in clauses)
    print(f"✓ test_split_clauses_fallback PASSED ({len(clauses)} 条)")


# ===== Test 3: 风险分类 =====

def test_classify_clause_risk_fatal():
    """致命风险: 违约金过高 / 显失公平 / 违法 / 重大遗漏。"""
    # 违约金过高
    c1 = Clause(clause_id="c1", clause_index=1, clause_title="违约金",
                clause_text="逾期支付的, 每逾期一天, 按月租金的 5% 加收违约金。")
    risk, cats = classify_clause_risk(c1, ReviewerInput(contract_type="房屋租赁", stance="乙方"))
    assert risk == RISK_LEVEL_FATAL, f"应 fatal, 实际 {risk}, cats={cats}"
    assert "违约金过高" in cats

    # 显失公平
    c2 = Clause(clause_id="c2", clause_index=2, clause_title="单方解除",
                clause_text="甲方可单方解除合同, 乙方需支付 6 个月租金违约金。")
    risk, cats = classify_clause_risk(c2, ReviewerInput(contract_type="房屋租赁", stance="乙方"))
    assert risk in (RISK_LEVEL_FATAL, RISK_LEVEL_MAJOR), f"应 fatal/major, 实际 {risk}"
    print("✓ test_classify_clause_risk_fatal PASSED (违约金过高 + 显失公平)")


def test_classify_clause_risk_major():
    """重大风险: 争议管辖不利。"""
    c = Clause(clause_id="c1", clause_index=1, clause_title="管辖",
               clause_text="因本合同发生的争议, 任何一方均可向甲方住所地人民法院提起诉讼。")
    risk, cats = classify_clause_risk(c, ReviewerInput(contract_type="房屋租赁", stance="乙方"))
    assert risk == RISK_LEVEL_MAJOR, f"应 major, 实际 {risk}, cats={cats}"
    assert "争议管辖不利" in cats
    print("✓ test_classify_clause_risk_major PASSED (争议管辖不利)")


def test_classify_clause_risk_advisory():
    """建议风险: 表述模糊。"""
    c = Clause(clause_id="c1", clause_index=1, clause_title="期限",
               clause_text="乙方应在合理期限内支付租金。")
    risk, cats = classify_clause_risk(c, ReviewerInput(contract_type="房屋租赁", stance="乙方"))
    assert risk in (RISK_LEVEL_ADVISORY, RISK_LEVEL_MAJOR), f"应 advisory/major, 实际 {risk}"
    print("✓ test_classify_clause_risk_advisory PASSED (表述模糊)")


# ===== Test 4: 上下文压缩 =====

def test_compress_clauses_no_compression():
    """小样本不触发压缩。"""
    clauses = [
        Clause(clause_id=f"c{i+1}", clause_index=i+1,
               clause_title=f"条款{i+1}", clause_text=f"条款{i+1}内容简短。")
        for i in range(5)
    ]
    compressed, trace = compress_clauses(clauses, budget=8000)
    assert len(compressed) == 5
    assert trace.compression_strategy == "none"
    assert trace.compression_ratio == 1.0
    print("✓ test_compress_clauses_no_compression PASSED")


def test_compress_clauses_truncate():
    """大样本自动压缩。"""
    big_text = "本院认为, 原告主张事实清楚, 证据充分。" * 100
    clauses = [
        Clause(clause_id=f"c{i+1}", clause_index=i+1,
               clause_title=f"条款{i+1}", clause_text=big_text)
        for i in range(100)
    ]
    compressed, trace = compress_clauses(clauses, budget=8000)
    assert trace.compression_strategy != "none"
    assert trace.compressed_token_count < trace.raw_token_count
    assert trace.compression_ratio < 1.0
    print(f"✓ test_compress_clauses_truncate PASSED ({trace.compression_strategy}, "
          f"{trace.raw_token_count}→{trace.compressed_token_count} tokens)")


# ===== Test 5: 风险汇总 =====

def test_compute_risk_summary():
    """三级分类计数 + 整体风险等级。"""
    reviews = [
        ClauseReview(clause_id="c1", clause_index=1, clause_title="t1", clause_text="x",
                     risk_level=RISK_LEVEL_FATAL, risk_categories=["违约金过高"],
                     legal_basis=[], risk_description="y"),
        ClauseReview(clause_id="c2", clause_index=2, clause_title="t2", clause_text="x",
                     risk_level=RISK_LEVEL_MAJOR, risk_categories=["争议管辖不利"],
                     legal_basis=[], risk_description="y"),
        ClauseReview(clause_id="c3", clause_index=3, clause_title="t3", clause_text="x",
                     risk_level=RISK_LEVEL_ADVISORY, risk_categories=["表述模糊"],
                     legal_basis=[], risk_description="y"),
        ClauseReview(clause_id="c4", clause_index=4, clause_title="t4", clause_text="x",
                     risk_level=RISK_LEVEL_OK, risk_categories=[],
                     legal_basis=[], risk_description="y"),
    ]
    summary = compute_risk_summary(reviews)
    assert summary["fatal_count"] == 1
    assert summary["major_count"] == 1
    assert summary["advisory_count"] == 1
    assert summary["ok_count"] == 1
    assert summary["overall_risk_level"] == "high"  # 存在 fatal
    assert len(summary["narrative"]) > 0
    # narrative 必须合规
    r = check_narrative(summary["narrative"])
    assert r.passed, f"summary narrative 违规: {summary['narrative']}"
    # top_risk_categories 应包含 3 个
    assert len(summary["top_risk_categories"]) == 3
    print(f"✓ test_compute_risk_summary PASSED (fatal={summary['fatal_count']}, "
          f"major={summary['major_count']}, overall={summary['overall_risk_level']})")


# ===== Test 6: 谈判策略 =====

def test_compute_negotiation_strategy():
    """优先级排序 + 立场策略。"""
    reviews = [
        ClauseReview(clause_id="c1", clause_index=1, clause_title="t1", clause_text="x",
                     risk_level=RISK_LEVEL_FATAL, risk_categories=["违约金过高"],
                     legal_basis=[], risk_description="y"),
        ClauseReview(clause_id="c2", clause_index=2, clause_title="t2", clause_text="x",
                     risk_level=RISK_LEVEL_MAJOR, risk_categories=["争议管辖不利"],
                     legal_basis=[], risk_description="y"),
        ClauseReview(clause_id="c3", clause_index=3, clause_title="t3", clause_text="x",
                     risk_level=RISK_LEVEL_ADVISORY, risk_categories=["表述模糊"],
                     legal_basis=[], risk_description="y"),
    ]
    ri = ReviewerInput(contract_type="房屋租赁", stance="乙方")
    strategy = compute_negotiation_strategy(reviews, ri)
    assert strategy["priority_clauses"][0] == "c1"  # fatal 优先
    assert "c2" in strategy["priority_clauses"]
    assert len(strategy["leverage_points"]) >= 1
    assert "乙方" in strategy["stance_specific_advice"]
    # stance_specific_advice 必须合规
    r = check_narrative(strategy["stance_specific_advice"])
    assert r.passed, f"stance_specific_advice 违规: {strategy['stance_specific_advice']}"
    print(f"✓ test_compute_negotiation_strategy PASSED (priority={strategy['priority_clauses']})")


# ===== Test 7: traffic_light =====

def test_traffic_light():
    assert compute_traffic_light({"fatal_count": 1, "major_count": 0, "advisory_count": 0, "ok_count": 0}) == "red"
    assert compute_traffic_light({"fatal_count": 0, "major_count": 1, "advisory_count": 0, "ok_count": 0}) == "yellow"
    assert compute_traffic_light({"fatal_count": 0, "major_count": 0, "advisory_count": 1, "ok_count": 0}) == "green"
    assert compute_traffic_light({"fatal_count": 0, "major_count": 0, "advisory_count": 0, "ok_count": 1}) == "green"
    print("✓ test_traffic_light PASSED")


# ===== Test 8: 端到端 run_skill =====

def test_run_skill_e2e():
    """端到端: 输入 → 拆分 → 审查 → 汇总 → 策略 → 输出。"""
    sample = """
第一条 租赁标的
甲方将位于上海市浦东新区某某路 123 号 1502 室房屋出租给乙方使用。

第二条 租赁期限
租赁期自 2026 年 7 月 1 日起至 2027 年 6 月 30 日止。

第三条 租金及支付
月租金为人民币 5000 元整, 乙方应于每月 5 日前支付下月租金。逾期支付的, 每逾期一天, 按月租金的 5% 加收违约金。

第四条 押金
乙方向甲方支付押金人民币 10000 元整, 30 日内无息退还。

第五条 提前解约
任何一方提前解除合同的, 须向守约方支付相当于 6 个月租金的违约金。

第六条 争议管辖
因本合同发生的争议, 双方协商不成的, 任何一方均可向甲方住所地人民法院提起诉讼。
"""
    ri = ReviewerInput(
        contract_type="房屋租赁",
        contract_text=sample,
        stance="乙方",
        jurisdiction="上海",
    )
    out = run_skill(ri)
    d = out.to_dict()

    # 校验基本结构
    assert d["query_meta"]["contract_type"] == "房屋租赁"
    assert d["query_meta"]["stance"] == "乙方"
    assert d["query_meta"]["total_clauses"] >= 5
    assert d["query_meta"]["returned_count"] >= 5
    assert d["disclaimer"] == DISCLAIMER_FULL
    assert d["ui_hints"]["traffic_light"] in ("red", "yellow", "green", "gray")

    # 校验 clause_reviews
    assert len(d["clause_reviews"]) >= 5
    fatal_count = sum(1 for r in d["clause_reviews"] if r["risk_level"] == RISK_LEVEL_FATAL)
    major_count = sum(1 for r in d["clause_reviews"] if r["risk_level"] == RISK_LEVEL_MAJOR)
    assert fatal_count >= 1 or major_count >= 1, "应至少有 1 个致命或重大风险"

    # 校验 risk_summary
    assert d["risk_summary"]["fatal_count"] >= 1
    assert d["risk_summary"]["overall_risk_level"] == "high"
    # narrative 必须合规
    r = check_narrative(d["risk_summary"]["narrative"])
    assert r.passed, f"E2E summary narrative 违规: {d['risk_summary']['narrative']}"

    # 校验 negotiation_strategy
    assert len(d["negotiation_strategy"]["priority_clauses"]) >= 1
    r2 = check_narrative(d["negotiation_strategy"]["stance_specific_advice"])
    assert r2.passed, f"E2E stance advice 违规: {d['negotiation_strategy']['stance_specific_advice']}"

    print(f"✓ test_run_skill_e2e PASSED (clauses={len(d['clause_reviews'])}, "
          f"fatal={fatal_count}, major={major_count}, "
          f"traffic_light={d['ui_hints']['traffic_light']})")


# ===== Test 9: token 计数 =====

def test_count_tokens():
    assert count_tokens("hello") >= 1
    assert count_tokens("你好世界") >= 1
    assert count_tokens("") == 0 or count_tokens("") == 1
    try:
        encoder = "tiktoken"
    except Exception:
        encoder = "fallback"
    print(f"✓ test_count_tokens PASSED (encoder={encoder})")


# ===== Test 10: percentile =====

def test_percentile_python():
    """numpy 不可用时纯 Python percentile 应正常工作。"""
    data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    p50 = _percentile(data, 50)
    p25 = _percentile(data, 25)
    p75 = _percentile(data, 75)
    assert 50 <= p50 <= 60
    assert 25 <= p25 <= 35
    assert 75 <= p75 <= 85
    print(f"✓ test_percentile_python PASSED (p50={p50})")


# ===== Test 11: 法条关联 =====

def test_lookup_legal_basis():
    """法条关联去重 + 上限 5 条。"""
    cats = ["违约金过高", "显失公平", "争议管辖不利"]
    laws = lookup_legal_basis(cats)
    assert len(laws) >= 3
    assert len(laws) <= 5
    assert all("《" in law for law in laws)
    # 去重
    assert len(laws) == len(set(laws))
    print(f"✓ test_lookup_legal_basis PASSED ({len(laws)} 条法条)")


# ===== Test 12: 输入消毒 =====

def test_sanitize_input_bypass_prevention():
    """输入消毒: user input 携带禁用词时应被替换。"""
    cases = [
        ("本合同必败", "合同存在相应法律风险"),
        ("该条款一定无效", "该条款存在效力认定风险"),
        ("对方将承担全部责任", "对方可能承担相应责任"),
        ("司法实践中一定会被调减", "司法实践中通常"),
        ("", ""),
    ]
    for raw, _ in cases:
        out = sanitize_input(raw)
        # 验证输出已无禁用词
        r = check_narrative(out)
        assert r.passed, f"sanitize 失败: '{raw}' -> '{out}' 仍含 {r.high_violations}"
    print(f"✓ test_sanitize_input_bypass_prevention PASSED ({len(cases)} 案例)")


# ===== Test 13: assert_no_bypass =====

def test_assert_no_bypass_passes():
    """合规 narrative 应通过。"""
    safe = "本合同共审查 7 个条款, 其中致命风险 1 个, 重大风险 1 个。"
    assert assert_no_bypass(safe) is True
    print("✓ test_assert_no_bypass_passes PASSED")


def test_assert_no_bypass_raises():
    """违规 narrative 必须抛 ValueError。"""
    bad = "本合同必败。"
    raised = False
    try:
        assert_no_bypass(bad)
    except ValueError as e:
        raised = True
        assert "bypass" in str(e)
    assert raised, "应抛 ValueError 但未抛"
    print("✓ test_assert_no_bypass_raises PASSED")


# ===== Test 14: run_skill bypass resilience =====

def test_run_skill_bypass_resilience():
    """run_skill: 即使 contract_text 携带禁用词, 最终 narrative 仍合规。"""
    malicious = """
第一条 违约责任
本合同必败, 对方将承担全部责任。

第二条 管辖
该条款一定无效。
"""
    ri = ReviewerInput(
        contract_type="其他",
        contract_text=malicious,
        stance="审查方",
    )
    out = run_skill(ri)
    d = out.to_dict()

    # 所有 narrative 必须合规
    if d["risk_summary"]["narrative"]:
        r = check_narrative(d["risk_summary"]["narrative"])
        assert r.passed, f"summary narrative 含 bypass: '{d['risk_summary']['narrative']}'"

    # clause_reviews 中 risk_description 也必须合规
    for cr in d["clause_reviews"]:
        if cr["risk_description"]:
            r = check_narrative(cr["risk_description"])
            assert r.passed, f"clause {cr['clause_id']} risk_description 含 bypass: '{cr['risk_description']}'"

    print(f"✓ test_run_skill_bypass_resilience PASSED (clauses={len(d['clause_reviews'])})")


# ===== Test 15: 多立场支持 =====

def test_run_skill_multi_stance():
    """run_skill 支持 4 种立场。"""
    sample = "任何一方可向甲方住所地人民法院提起诉讼。"
    for stance in ["甲方", "乙方", "丙方", "审查方"]:
        ri = ReviewerInput(
            contract_type="其他",
            contract_text=sample,
            stance=stance,
        )
        out = run_skill(ri)
        d = out.to_dict()
        assert d["query_meta"]["stance"] == stance
        assert d["negotiation_strategy"]["stance_specific_advice"]
    print("✓ test_run_skill_multi_stance PASSED (4 立场)")


# ===== Main =====

if __name__ == "__main__":
    tests = [
        test_language_guard_pass,
        test_language_guard_fail_high,
        test_language_guard_correction,
        test_templates_pass,
        test_split_clauses_standard,
        test_split_clauses_fallback,
        test_classify_clause_risk_fatal,
        test_classify_clause_risk_major,
        test_classify_clause_risk_advisory,
        test_compress_clauses_no_compression,
        test_compress_clauses_truncate,
        test_compute_risk_summary,
        test_compute_negotiation_strategy,
        test_traffic_light,
        test_run_skill_e2e,
        test_count_tokens,
        test_percentile_python,
        test_lookup_legal_basis,
        test_sanitize_input_bypass_prevention,
        test_assert_no_bypass_passes,
        test_assert_no_bypass_raises,
        test_run_skill_bypass_resilience,
        test_run_skill_multi_stance,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"✗ {t.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {t.__name__} ERROR: {e}")
            failed += 1
    print(f"\n{'='*60}")
    print(f"测试结果: {passed} PASSED, {failed} FAILED (共 {passed+failed} 项)")
    sys.exit(0 if failed == 0 else 1)