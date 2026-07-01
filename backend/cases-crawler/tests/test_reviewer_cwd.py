"""
W10 A1 reviewer.py _get_risk_index cwd 独立性测试 (lex-ai · 2026-06-29)

D4 producer blocker #2 修复验证:
- _get_risk_index() 在任意 cwd 下都返回相同绝对路径
- 不依赖 os.chdir 到 cases-crawler/

策略:
- chdir 到 /tmp/C:\\ 等任意目录, 验证路径不变
- 不实际加载 LanceDB 索引 (idx.has_risks() 可能 False, fallback None)
"""
import os


def test_get_risk_index_path_is_absolute():
    """_get_risk_index_path() 返回绝对路径 (不依赖 cwd)"""
    from skills.contract_review.reviewer import _get_risk_index_path
    p = _get_risk_index_path()
    assert os.path.isabs(p), f"not absolute: {p}"
    # 路径应该指向 backend/cases-crawler/data/lancedb
    assert p.endswith(os.path.join("data", "lancedb"))


def test_get_risk_index_path_independent_of_cwd(tmp_path):
    """从 /tmp/ 跑, 路径还是绝对且指向 cases-crawler"""
    from skills.contract_review.reviewer import _get_risk_index_path
    original_cwd = os.getcwd()
    try:
        os.chdir(str(tmp_path))
        p = _get_risk_index_path()
        assert os.path.isabs(p)
        assert p.endswith(os.path.join("data", "lancedb"))
        assert "cases-crawler" in p
    finally:
        os.chdir(original_cwd)


def test_get_risk_index_path_independent_of_windows_root():
    """从 C:\\ 跑也 OK"""
    from skills.contract_review.reviewer import _get_risk_index_path
    original_cwd = os.getcwd()
    try:
        os.chdir("C:\\")
        p = _get_risk_index_path()
        assert os.path.isabs(p)
        assert p.endswith(os.path.join("data", "lancedb"))
    finally:
        os.chdir(original_cwd)


def test_get_risk_index_returns_none_or_index_without_raising(tmp_path):
    """_get_risk_index() 不抛异常, 即使索引不存在也返回 None"""
    from skills.contract_review import reviewer
    # 重置单例, 避免上次测试污染
    reviewer.reset_risk_index()
    original_cwd = os.getcwd()
    try:
        os.chdir(str(tmp_path))
        # 不应抛 ImportError 或 FileNotFoundError
        idx = reviewer._get_risk_index()
        # 索引不存在 (data/lancedb 目录在 venv 中可能空) → fallback None
        assert idx is None or hasattr(idx, "search_similar_risks")
    finally:
        os.chdir(original_cwd)
        reviewer.reset_risk_index()


def test_retrieval_disabled_skips_index_load():
    """retrieval_enabled=False 时, reviewer.run_skill 不做 LanceDB 检索 (但仍检查索引)

    这是 W10 A1 默认配置 (full_workflow_router 用 retrieval_enabled=False),
    跟 cwd 修复解耦 — 即使 _get_risk_index 有问题, 也跑得通
    """
    from skills.contract_review.reviewer import (
        ReviewerInput, ReviewerConfig, run_skill, reset_risk_index,
    )
    reset_risk_index()
    ri = ReviewerInput(
        contract_type="房屋租赁",
        contract_text="第一条 标的\n甲方将位于上海市浦东新区某某路 123 号房屋出租给乙方使用。\n"
                      "第二条 租金\n月租金为人民币 5000 元整。\n第三条 违约\n逾期按日千分之五加收违约金。",
        stance="乙方",
    )
    config = ReviewerConfig(retrieval_enabled=False)
    out = run_skill(ri, config=config)
    out_dict = out.to_dict()
    assert "clause_reviews" in out_dict
    assert "risk_summary" in out_dict
    # retrieval_enabled=False → fatal_major_clauses=0 (没真跑检索)
    stats = out_dict["ui_hints"]["retrieval_stats"]
    assert stats["fatal_major_clauses"] == 0  # 没跑 fatal/major 路径
    assert stats["clauses_with_evidence"] == 0
    reset_risk_index()


def test_config_path_uses_relative_path_unchanged():
    """IndexConfig 默认 lancedb_path 是相对路径 (保持向后兼容)"""
    from core.lancedb_index import IndexConfig
    cfg = IndexConfig()
    # 默认仍是相对路径 (跟旧版一致)
    assert "data/lancedb" in cfg.lancedb_path
    # 但 reviewer 用绝对路径 (修复点)
    from skills.contract_review.reviewer import _get_risk_index_path
    p = _get_risk_index_path()
    assert os.path.isabs(p)


def test_review_skill_works_from_different_cwd(tmp_path):
    """E2E: chdir 到任意目录, reviewer.run_skill 仍能跑"""
    from skills.contract_review.reviewer import (
        ReviewerInput, ReviewerConfig, run_skill, reset_risk_index,
    )
    reset_risk_index()
    original_cwd = os.getcwd()
    try:
        os.chdir(str(tmp_path))
        ri = ReviewerInput(
            contract_type="借款合同",
            contract_text="第一条 借款金额\n甲方借给乙方人民币 50 万元。\n第二条 利率\n年利率 24%。",
            stance="审查方",
        )
        config = ReviewerConfig(retrieval_enabled=False)
        out = run_skill(ri, config=config)
        out_dict = out.to_dict()
        assert "clause_reviews" in out_dict
        # 跟 cwd 无关, 不应该抛 FileNotFoundError
    finally:
        os.chdir(original_cwd)
        reset_risk_index()