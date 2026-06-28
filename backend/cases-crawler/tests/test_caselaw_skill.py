"""
LexPrime 类案检索 Skill — 单元测试

测试覆盖:
1. language_guard: 禁用词检测 (HIGH/LOW 违规)
2. retrieval: 数据类 + 上下文压缩 + 统计生成
3. UI 提示: traffic_light 计算

运行:
    cd backend/cases-crawler
    pytest tests/test_caselaw_skill.py -v
    或: python -m pytest tests/test_caselaw_skill.py -v
"""
import sys
from pathlib import Path
from datetime import date

# 让脚本可直接运行 (不依赖 pytest)
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "skills"))

from caselaw.language_guard import (
    check_narrative, template_outcome_distribution, template_amount_stats,
    template_judge_style, template_overall, DISCLAIMER_FULL,
)
from caselaw.retrieval import (
    RetrievalInput, RetrievalConfig, CaseHit, VectorStore,
    compress_context, compute_statistics, compute_traffic_light,
    run_skill, count_tokens, _percentile,
)


# ===== Test 1: language_guard =====

def test_language_guard_pass():
    """正确的统计型描述必须通过。"""
    samples = [
        "近 3 年本法院 87 件类似案件中, 支持原告诉请 72 件 (约 83%)。",
        "该法官在同类案件中, 判赔金额中位数约 38 万元。",
        "检索到 87 件类案, 涉及争议焦点利率合规性 (65/87)。",
        "判赔金额中位数约 380000 元, 四分位距 210000-520000 元。",
        "该法官在 12 件民间借贷二审样本中, 支持原告诉请的比例约 83%。",
    ]
    for s in samples:
        r = check_narrative(s)
        assert r.passed, f"应 PASS 但 FAIL: {s} → {r.high_violations}"
        assert r.high_violations == []
    print("✓ test_language_guard_pass PASSED")


def test_language_guard_fail_high():
    """违规表述必须被拦截。"""
    bad_samples = [
        "本案胜诉率约 83%。",
        "本案胜诉率 80%。",
        "预计本案判赔 50 万元。",
        "预计 90 天内审结。",
        "本案将会胜诉。",
        "该法官审理案件偏袒原告。",
        "该法院支持原告。",
        "胜诉率约 50%。",
    ]
    for s in bad_samples:
        r = check_narrative(s)
        assert not r.passed, f"应 FAIL 但 PASS: {s}"
        assert len(r.high_violations) > 0
    print(f"✓ test_language_guard_fail_high PASSED (拦截 {len(bad_samples)} 条)")


def test_language_guard_correction():
    """违规表述自动纠正后应通过。"""
    r = check_narrative("本案胜诉率约 83%")
    assert not r.passed
    corrected = r.corrected_text
    r2 = check_narrative(corrected)
    assert r2.passed, f"纠正后仍 FAIL: {corrected}"
    print(f"✓ test_language_guard_correction PASSED (纠正后: '{corrected}')")


def test_templates_pass():
    """所有降级模板必须通过语言规范检查。"""
    t1 = template_outcome_distribution(87, 72)
    t2 = template_amount_stats(380000, 210000, 520000, 50000, 1200000)
    t3 = template_judge_style("王某", 12, 83.33, 87, "中等")
    t4 = template_overall(87, "民间借贷纠纷", "上海", 2022, 2025)
    for t in [t1, t2, t3, t4]:
        r = check_narrative(t)
        assert r.passed, f"模板 FAIL: {t} → {r.high_violations}"
    print("✓ test_templates_pass PASSED")


# ===== Test 2: 上下文压缩 =====

def test_compress_context_no_compression_needed():
    hits = [
        CaseHit(case_id=f"({2020+i}) 沪01民终 {1000+i} 号",
                case_name=f"案件{i}", court="上海一中院",
                cause="民间借贷纠纷", judgment_date="2024-01-01",
                year=2024, outcome="原告胜诉",
                amount_awarded_cny=100000, summary="简短摘要",
                dispute_focus=["利率合规性"], relevance_score=0.9)
        for i in range(5)
    ]
    compressed, trace = compress_context(hits, budget=8000)
    assert len(compressed) == 5
    assert trace.compression_strategy == "none"
    assert trace.compression_ratio == 1.0
    print("✓ test_compress_context_no_compression_needed PASSED")


def test_compress_context_truncate():
    """构造一个会让 token 超 8000 的样本。"""
    big_summary = "裁判要旨: " + "本院认为, 原告主张事实清楚, 证据充分。" * 200
    hits = [
        CaseHit(case_id=f"({2020+i}) 京01民终 {1000+i} 号",
                case_name=f"案件{i}", court="北京一中院",
                cause="买卖合同纠纷", judgment_date="2023-06-15",
                year=2023, outcome="部分支持",
                amount_awarded_cny=500000, summary=big_summary,
                dispute_focus=["合同效力", "违约金过高"], relevance_score=0.85)
        for i in range(20)
    ]
    compressed, trace = compress_context(hits, budget=8000)
    assert trace.compression_strategy != "none"
    assert trace.compressed_token_count < trace.raw_token_count
    assert trace.compression_ratio < 1.0
    print(f"✓ test_compress_context_truncate PASSED ({trace.compression_strategy}, "
          f"{trace.raw_token_count}→{trace.compressed_token_count} tokens)")


# ===== Test 3: 统计生成 =====

def test_compute_statistics_basic():
    hits = []
    for i in range(50):
        outcome = ["原告胜诉", "被告胜诉", "部分支持", "调解"][i % 4]
        hits.append(CaseHit(
            case_id=f"({2020+i%5}) 沪01民终 {1000+i} 号",
            case_name=f"案件{i}", court="上海一中院",
            cause="民间借贷纠纷", judgment_date="2024-01-01",
            year=2020 + i%5, outcome=outcome,
            amount_awarded_cny=100000 + i * 1000,
            summary=f"案件{i}摘要", dispute_focus=["利率合规性"],
            relevance_score=0.8))
    ri = RetrievalInput(cause="民间借贷纠纷", top_k=20,
                        year_from=2020, year_to=2025)
    stats = compute_statistics(hits, ri)
    assert stats["sample_size"] == 50
    assert stats["outcome_distribution"]["原告胜诉"] == 13  # i % 4 == 0
    assert stats["support_rate_aggregate"]["support_total"] == 25  # 原告胜诉 + 部分支持
    assert abs(stats["support_rate_aggregate"]["support_pct"] - 50.0) < 0.01
    assert stats["amount_stats"]["median_cny"] > 0
    assert stats["top_dispute_focus"][0]["focus"] == "利率合规性"
    assert len(stats["narrative"]) > 0
    # 关键: narrative 必须通过 language_guard
    r = check_narrative(stats["narrative"])
    assert r.passed, f"统计 narrative 违规: {stats['narrative']} → {r.high_violations}"
    print(f"✓ test_compute_statistics_basic PASSED (sample={stats['sample_size']}, "
          f"support_pct={stats['support_rate_aggregate']['support_pct']})")


def test_compute_statistics_judge_style():
    hits = [
        CaseHit(case_id=f"({y}) 沪01民终 {1000+i} 号",
                case_name=f"案件{i}", court="上海一中院",
                cause="民间借贷纠纷", judgment_date=f"{y}-01-01",
                year=y, judge_name="王某", outcome="原告胜诉",
                amount_awarded_cny=200000, summary="x",
                dispute_focus=[], relevance_score=0.8)
        for i, y in enumerate([2024]*8)  # 8 件同法官样本
    ]
    ri = RetrievalInput(cause="民间借贷纠纷", judge_name="王某", top_k=10)
    stats = compute_statistics(hits, ri)
    assert stats["judge_style"] is not None
    assert stats["judge_style"]["judge_name"] == "王某"
    assert stats["judge_style"]["sample_size"] == 8
    assert stats["judge_style"]["support_pct"] == 100.0
    # judge narrative 也要通过语言规范
    r = check_narrative(stats["judge_style"]["narrative"])
    assert r.passed, f"judge_style narrative 违规: {stats['judge_style']['narrative']}"
    print(f"✓ test_compute_statistics_judge_style PASSED (样本={stats['judge_style']['sample_size']})")


def test_compute_statistics_judge_insufficient():
    """样本不足时不返回法官风格。"""
    hits = [
        CaseHit(case_id="(2024) 沪01民终 0001 号",
                case_name="案件1", court="上海一中院",
                cause="民间借贷纠纷", judgment_date="2024-01-01",
                year=2024, judge_name="王某", outcome="原告胜诉",
                amount_awarded_cny=100000, summary="x",
                dispute_focus=[], relevance_score=0.8)
    ]
    ri = RetrievalInput(cause="民间借贷纠纷", judge_name="王某", top_k=10)
    stats = compute_statistics(hits, ri)
    # 样本 < 5, judge_style 应标记"样本不足"
    assert stats["judge_style"] is not None
    assert stats["judge_style"]["evidence_admission_tendency"] == "样本不足"
    print(f"✓ test_compute_statistics_judge_insufficient PASSED")


# ===== Test 4: traffic_light =====

def test_traffic_light():
    assert compute_traffic_light({"sample_size": 0, "support_rate_aggregate": {"support_pct": 0}}) == "gray"
    assert compute_traffic_light({"sample_size": 30, "support_rate_aggregate": {"support_pct": 70}}) == "green"
    assert compute_traffic_light({"sample_size": 15, "support_rate_aggregate": {"support_pct": 50}}) == "yellow"
    assert compute_traffic_light({"sample_size": 5, "support_rate_aggregate": {"support_pct": 20}}) == "red"
    assert compute_traffic_light({"sample_size": 25, "support_rate_aggregate": {"support_pct": 25}}) == "red"
    print("✓ test_traffic_light PASSED")


# ===== Test 5: 端到端 run_skill =====

def test_run_skill_e2e():
    """端到端: 模拟检索 → 压缩 → 统计 → 输出。"""
    mock_hits = [
        CaseHit(case_id=f"({2020+i%5}) 沪01民终 {1000+i} 号",
                case_name=f"案件{i}", court="上海一中院",
                cause="民间借贷纠纷", judgment_date=f"{2020+i%5}-06-15",
                year=2020 + i%5, judge_name="王某" if i % 2 == 0 else "李某",
                outcome=["原告胜诉", "被告胜诉", "部分支持", "调解"][i%4],
                amount_awarded_cny=100000 + (i % 10) * 50000,
                summary=f"案件{i}的简要裁判摘要, 涉及民间借贷纠纷。",
                dispute_focus=["利率合规性", "本金认定"][i%2:i%2+1],
                relevance_score=0.7 + (i % 30) / 100)
        for i in range(30)
    ]

    class MockStore(VectorStore):
        def metadata_filter(self, ri, candidate_limit=500):
            return mock_hits
        def vector_search(self, ri, candidates):
            return sorted(candidates, key=lambda h: -h.relevance_score)[:ri.top_k]

    ri = RetrievalInput(cause="民间借贷纠纷", facts="借给被告 50 万元",
                        court="上海一中院", year_from=2020, year_to=2025,
                        region="上海", top_k=20, include_judge_style=True)
    out = run_skill(ri, MockStore())
    d = out.to_dict()

    assert d["query_meta"]["returned_count"] == 20
    assert d["query_meta"]["latency_ms"] >= 0
    assert d["statistics"]["sample_size"] == 20
    assert d["disclaimer"] == DISCLAIMER_FULL
    assert d["ui_hints"]["traffic_light"] in ("green", "yellow", "red", "gray")
    # narrative 必须合规
    r = check_narrative(d["statistics"]["narrative"])
    assert r.passed, f"E2E narrative 违规: {d['statistics']['narrative']}"
    print(f"✓ test_run_skill_e2e PASSED (latency={d['query_meta']['latency_ms']}ms, "
          f"traffic_light={d['ui_hints']['traffic_light']})")


# ===== Test 6: token 计数 =====

def test_count_tokens():
    assert count_tokens("hello") >= 1
    assert count_tokens("你好世界") >= 1
    assert count_tokens("") == 0 or count_tokens("") == 1
    print(f"✓ test_count_tokens PASSED (encoder={'tiktoken' if count_tokens.__doc__ else 'fallback'})")


# ===== Test 7: percentile 纯 Python 实现 =====

def test_percentile_python():
    """numpy 不可用时纯 Python percentile 应正常工作。"""
    data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    p50 = _percentile(data, 50)
    p25 = _percentile(data, 25)
    p75 = _percentile(data, 75)
    # 中位数应在 50-60 之间
    assert 50 <= p50 <= 60, f"p50={p50}"
    assert 25 <= p25 <= 35, f"p25={p25}"
    assert 75 <= p75 <= 85, f"p75={p75}"
    print(f"✓ test_percentile_python PASSED (p50={p50}, p25={p25}, p75={p75})")


# ===== Main =====

if __name__ == "__main__":
    tests = [
        test_language_guard_pass,
        test_language_guard_fail_high,
        test_language_guard_correction,
        test_templates_pass,
        test_compress_context_no_compression_needed,
        test_compress_context_truncate,
        test_compute_statistics_basic,
        test_compute_statistics_judge_style,
        test_compute_statistics_judge_insufficient,
        test_traffic_light,
        test_run_skill_e2e,
        test_count_tokens,
        test_percentile_python,
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