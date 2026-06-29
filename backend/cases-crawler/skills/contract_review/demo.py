"""
Skill 2 合同风险审查 - Demo 模式 Fixture Loader (W5)

复用 W4 lex-pm 测试合同模板 + W3-W4 reviewer 算法,提供 demo 模式 fallback:

1. **5 合同 fixture**: 房屋租赁 / 借款 / 劳动 / 服务 / 销售
   - 路径: backend/cases-crawler/data/fixtures/contract_review/*.json
   - 来源: 复用 W4 lex-pm test-contracts-results + W5 lex-coder 整理

2. **真实审查路径**: demo_run_review() 调用 reviewer.run_skill(),不调 LLM
   - 全部走规则层 (关键词扫描 + 法条关联 + 立场影响)
   - W4 双路召回 (LanceDB) 自动启用 (如索引就位)

3. **API 集成**: 4 endpoint 全部支持 ?demo=1 走 fixture 模式
   - 律师不需要真实上传文件也能体验审查流程
   - 试用版 onboarding 强制 demo 路径

设计原则 (跟 Skill 1 类案检索 demo 模式一致):
- 不调真实 LLM, 确保离线可用
- 走 reviewer 的完整算法, 确保审查质量与生产一致
- 5 合同 baseline 覆盖 8 大类前 5 类, 跟 PRD § 3.12.2 对齐
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

# Skill 内部 - 复用 W3-W4 reviewer
from skills.contract_review.reviewer import (
    ReviewerInput,
    ReviewerConfig,
    run_skill,
)

# ===== Fixtures 路径 =====

_FIXTURES_DIR = Path(__file__).parent.parent.parent / "data" / "fixtures" / "contract_review"

_FIXTURE_FILES = {
    "rental": "rental.json",
    "loan": "loan.json",
    "labor": "labor.json",
    "service": "service.json",
    "sales": "sales.json",
}

_FIXTURE_INDEX = {
    "demo-rental-beijing-2026": "rental",
    "demo-loan-shanghai-2026": "loan",
    "demo-labor-shenzhen-2026": "labor",
    "demo-service-hangzhou-2026": "service",
    "demo-sales-guangzhou-2026": "sales",
}


class FixtureError(Exception):
    """Fixture 加载错误"""
    pass


def list_fixtures() -> List[Dict[str, Any]]:
    """列出全部 5 个 demo fixture 摘要 (给前端 01-upload "示例合同" 下拉)

    Returns:
        list of dict: fixture_id, contract_type, contract_title, industry,
                      jurisdiction, amount, stance_default, risk_hint
    """
    fixtures = []
    for fix_id, key in _FIXTURE_INDEX.items():
        try:
            data = _load_fixture(fix_id)
            expected = data.get("expected_risks", {})
            risk_hint = (
                f"致命 {len(expected.get('fatal', []))} / "
                f"重大 {len(expected.get('major', []))} / "
                f"建议 {len(expected.get('advisory', []))}"
            )
            fixtures.append({
                "fixture_id": fix_id,
                "contract_type": data["contract_type"],
                "contract_title": data["contract_title"],
                "industry": data.get("industry", ""),
                "jurisdiction": data.get("jurisdiction", ""),
                "amount": data.get("amount", 0),
                "stance_default": data.get("stance_default", "审查方"),
                "risk_hint": risk_hint,
            })
        except Exception as e:
            logger.warning(f"加载 fixture 失败: {fix_id}, {e}")
    return fixtures


def load_fixture(fixture_id: str) -> Dict[str, Any]:
    """根据 fixture_id 加载合同 JSON

    Args:
        fixture_id: 形如 demo-rental-beijing-2026

    Returns:
        fixture dict (含 contract_text + 元数据)

    Raises:
        FixtureError: 不存在
    """
    return _load_fixture(fixture_id)


def _load_fixture(fixture_id: str) -> Dict[str, Any]:
    if fixture_id not in _FIXTURE_INDEX:
        raise FixtureError(f"未知 fixture_id: {fixture_id}, 可选: {list(_FIXTURE_INDEX.keys())}")
    key = _FIXTURE_INDEX[fixture_id]
    file_path = _FIXTURES_DIR / _FIXTURE_FILES[key]
    if not file_path.exists():
        raise FixtureError(f"fixture 文件不存在: {file_path}")
    return json.loads(file_path.read_text(encoding="utf-8"))


def run_fixture_review(
    fixture_id: str,
    stance: str = "审查方",
    contract_type: Optional[str] = None,
) -> Dict[str, Any]:
    """跑 fixture 合同的真实审查 (复用 W4 reviewer.run_skill)

    Args:
        fixture_id: demo-rental-beijing-2026 等
        stance: 甲方/乙方/丙方/审查方
        contract_type: 可选 override, 默认从 fixture 取

    Returns:
        dict: ReviewerOutput.to_dict() 结构
    """
    data = load_fixture(fixture_id)
    ri = ReviewerInput(
        contract_type=contract_type or data["contract_type"],
        contract_text=data["contract_text"],
        stance=stance,
        industry=data.get("industry", ""),
        amount=data.get("amount"),
        jurisdiction=data.get("jurisdiction", ""),
        include_suggestion=True,
        include_negotiation_strategy=True,
        case_id=fixture_id,  # 用 fixture_id 作为 case_id 标识
    )
    config = ReviewerConfig(retrieval_enabled=True)  # W4 双路召回

    t0 = time.time()
    out = run_skill(ri, config)
    out_dict = out.to_dict()
    out_dict["query_meta"]["fixture_id"] = fixture_id
    out_dict["query_meta"]["demo_mode"] = True
    out_dict["query_meta"]["demo_latency_ms"] = int((time.time() - t0) * 1000)
    # 替换 disclaimer 为 fixture 来源说明
    out_dict["disclaimer"] = (
        "本审查基于 demo 模式 fixture 合同, 仅为功能演示, "
        "不构成法律意见, 更不替代律师的专业判断。"
    )
    return out_dict


def render_markdown_report(review: Dict[str, Any]) -> str:
    """demo 模式: 把审查结果渲染为 Markdown 报告 (给 05-export 用)

    Args:
        review: run_fixture_review() 返回的 dict

    Returns:
        Markdown 字符串
    """
    meta = review["query_meta"]
    summary = review["risk_summary"]
    clauses = review["clause_reviews"]

    lines = [
        f"# 合同风险审查报告 · {meta.get('contract_type', 'N/A')}",
        "",
        f"> **审查模式**: Demo (Fixture: {meta.get('fixture_id', 'N/A')})  ",
        f"> **律师立场**: {meta.get('stance', 'N/A')}  ",
        f"> **审查耗时**: {meta.get('latency_ms', 'N/A')}ms  ",
        "> **审查引擎**: Skill 2 v0.1.0-draft  ",
        f"> **生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}  ",
        "",
        "---",
        "",
        "## 一、整体风险总览",
        "",
        f"- 🔴 致命风险: **{summary['fatal_count']}** 项",
        f"- 🟡 重大风险: **{summary['major_count']}** 项",
        f"- 🔵 建议风险: **{summary['advisory_count']}** 项",
        f"- 🟢 合规条款: **{summary['ok_count']}** 项",
        f"- **整体风险等级**: {summary['overall_risk_level']}",
        "",
        "### 整体叙述",
        "",
        summary.get("narrative", "(无)"),
        "",
        "---",
        "",
        "## 二、条款级详述",
        "",
    ]

    risk_emoji = {
        "fatal": "🔴",
        "major": "🟡",
        "advisory": "🔵",
        "ok": "🟢",
    }

    for c in clauses:
        level_emoji = risk_emoji.get(c["risk_level"], "⚪")
        lines.append(f"### {level_emoji} 第 {c['clause_index']} 条 · {c['clause_title']}  [{c['risk_level']}]")
        lines.append("")
        lines.append(f"**风险分类**: {', '.join(c.get('risk_categories', []))}")
        lines.append("")
        if c.get("legal_basis"):
            lines.append(f"**法律依据**: {'; '.join(c['legal_basis'])}")
            lines.append("")
        if c.get("risk_description"):
            lines.append(f"**风险描述**: {c['risk_description']}")
            lines.append("")
        if c.get("modification_suggestion"):
            lines.append(f"**修改建议**: {c['modification_suggestion']}")
            lines.append("")
        if c.get("modified_clause_template"):
            lines.append("**修改后条款模板**:")
            lines.append("")
            lines.append("```")
            lines.append(c["modified_clause_template"])
            lines.append("```")
            lines.append("")
        lines.append(f"**立场影响**: {c.get('stance_impact', '中性')} | **审查置信度**: {c.get('reviewer_confidence', 0):.0%}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # 谈判策略
    ns = review.get("negotiation_strategy", {})
    if ns:
        lines.append("## 三、谈判策略")
        lines.append("")
        if ns.get("stance_specific_advice"):
            lines.append(f"**立场建议**: {ns['stance_specific_advice']}")
            lines.append("")
        if ns.get("walk_away_signals"):
            lines.append("**红线条款** (建议放弃):")
            for s in ns["walk_away_signals"]:
                lines.append(f"- {s}")
            lines.append("")
        lines.append("---")
        lines.append("")

    # Disclaimer
    lines.append("## 四、免责声明")
    lines.append("")
    lines.append(review.get("disclaimer", "本审查仅为基于合同文本的客观风险标注与法律依据提示, 不构成法律意见。"))
    lines.append("")
    return "\n".join(lines)


def render_html_report(review: Dict[str, Any]) -> str:
    """demo 模式: 把审查结果渲染为 HTML 报告 (简化版, 给 05-export 预览)

    Args:
        review: run_fixture_review() 返回的 dict

    Returns:
        HTML 字符串
    """
    meta = review["query_meta"]
    summary = review["risk_summary"]
    clauses = review["clause_reviews"]

    risk_class = {
        "fatal": "border-l-4 border-danger bg-danger-tint",
        "major": "border-l-4 border-warning bg-warning-tint",
        "advisory": "border-l-4 border-brand bg-brand-tint3",
        "ok": "border-l-4 border-success bg-success-tint",
    }

    html_parts = [
        '<div class="contract-review-report">',
        f'<h1 class="text-xl font-bold mb-2">合同风险审查报告 · {meta.get("contract_type", "N/A")}</h1>',
        '<div class="text-xs text-fg-tertiary mb-4">',
        f'<div>审查模式: <span class="text-ai font-medium">Demo (Fixture: {meta.get("fixture_id", "N/A")})</span></div>',
        f'<div>律师立场: <span class="font-medium">{meta.get("stance", "N/A")}</span></div>',
        f'<div>审查耗时: <span class="font-medium text-success">{meta.get("latency_ms", "N/A")}ms</span></div>',
        '</div>',
        '<h2 class="text-lg font-semibold mt-4 mb-2">一、整体风险总览</h2>',
        '<div class="grid grid-cols-4 gap-2 mb-4">',
        f'<div class="bg-danger-tint p-3 rounded text-center"><div class="text-2xl font-bold text-danger">{summary["fatal_count"]}</div><div class="text-xs">致命</div></div>',
        f'<div class="bg-warning-tint p-3 rounded text-center"><div class="text-2xl font-bold text-warning">{summary["major_count"]}</div><div class="text-xs">重大</div></div>',
        f'<div class="bg-brand-tint3 p-3 rounded text-center"><div class="text-2xl font-bold text-brand">{summary["advisory_count"]}</div><div class="text-xs">建议</div></div>',
        f'<div class="bg-success-tint p-3 rounded text-center"><div class="text-2xl font-bold text-success">{summary["ok_count"]}</div><div class="text-xs">合规</div></div>',
        '</div>',
        f'<div class="bg-bg-subtle p-3 rounded text-sm mb-4">{summary.get("narrative", "")}</div>',
        '<h2 class="text-lg font-semibold mt-4 mb-2">二、条款级详述</h2>',
    ]

    for c in clauses:
        css_class = risk_class.get(c["risk_level"], "")
        html_parts.append(f'<div class="p-3 rounded mb-3 {css_class}">')
        html_parts.append(
            f'<div class="flex items-center justify-between mb-2">'
            f'<span class="font-medium">第 {c["clause_index"]} 条 · {c["clause_title"]}</span>'
            f'<span class="text-xs px-2 py-0.5 rounded bg-white">{c["risk_level"]}</span>'
            f'</div>'
        )
        if c.get("risk_description"):
            html_parts.append(f'<div class="text-sm mb-1"><strong>风险描述:</strong> {c["risk_description"]}</div>')
        if c.get("modification_suggestion"):
            html_parts.append(f'<div class="text-sm mb-1"><strong>修改建议:</strong> {c["modification_suggestion"]}</div>')
        html_parts.append('</div>')

    html_parts.append('</div>')
    return "\n".join(html_parts)