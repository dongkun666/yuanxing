#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LexPrime Track E · W6 律师评审评分自动汇总脚本 (W7 扩展: 含 review_questions JOIN)
==================================================================================

用途:
    评审 #1 #2 后 24h 内, PM 收集 5 律师 review-template.md 评分表 (Markdown)
    + 评审现场 review_questions 表 (SQLite),
    跑这个脚本自动汇总到 review-summary-w6.md + prd-feedback.md v1.0.

输入:
    --input  指定律师评分表目录 (默认 docs/interviews/reviews-w6/)
            每个文件命名: lawyer_review_skill2_{name}.md
            每份文件必须包含 §6.4 评分表 (D1/D2/D3/D4/D5)
    --db     SQLite 数据库路径 (W7 新增: 读 review_questions 表)
            默认 backend/cases-crawler/data/lexprime.db
    --prd-feedback    同时自动生成 docs/skills/contract-review/prd-feedback.md v1.0
            (W7 核心交付物)

输出:
    --output 指定汇总文件 (默认 docs/interviews/review-summary-w6.md)
            包含: §3 评分汇总表 + §4 综合排名 + §5 关键发现 + §6 律师问题清单

通过门槛 (跟 scoring-rubric.md §1.3 对齐):
    - 综合评分 >= 4.0
    - D1 (致命/重大准确率) >= 4.25 (硬门槛)
    - D4 (中立性) = 5 (硬门槛, 0 违规)
    - D2 (实用性) >= 4.0 (软门槛)
    - D3 (谈判策略) >= 3.25 (软门槛)

用法:
    python scripts/aggregate-review-scores.py
    python scripts/aggregate-review-scores.py --input docs/interviews/reviews-w6/ --output docs/interviews/review-summary-w6.md
    python scripts/aggregate-review-scores.py --db backend/cases-crawler/data/lexprime.db --prd-feedback
    python scripts/aggregate-review-scores.py --verbose
    python scripts/aggregate-review-scores.py --dry-run  # 仅打印不写文件

关联文件:
    - docs/skills/contract-review/scoring-rubric.md (评分细则)
    - docs/skills/contract-review/prd-feedback.md (W7 自动生成 v1.0)
    - docs/interviews/review-template.md (律师评分表模板)
    - docs/interviews/review-questions-w6.md (25 问评审题库)
    - docs/interviews/review-process-w6.md (评审流程)
    - docs/interviews/lawyer-profiles-w6.md (5 律师画像)

整理人: lex-coder (W6 Day 3 + W7 Day 2, 2026-06-29)
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# 评估 SQLite 可用性 (W7 读 review_questions 表)
try:
    import sqlite3  # noqa: F401
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False


# ============ 常量配置 ============

# 评分维度权重 (跟 scoring-rubric.md §1.1 对齐)
DIM_WEIGHTS = {
    "D1": 0.30,  # 三级风险识别准确率
    "D2": 0.25,  # 修改建议实用性
    "D3": 0.20,  # 谈判策略可执行性
    "D4": 0.15,  # LLM 输出中立性
    "D5": 0.10,  # 整体可用性 (UI 流程合理性)
}

# 评分维度名称
DIM_NAMES = {
    "D1": "三级风险识别准确率",
    "D2": "修改建议实用性",
    "D3": "谈判策略可执行性",
    "D4": "LLM 输出中立性",
    "D5": "整体可用性 (UI 流程合理性)",
}

# 通过门槛 (跟 scoring-rubric.md §1.3 对齐)
PASS_THRESHOLDS = {
    "综合": 4.0,
    "D1": 4.25,  # 硬门槛
    "D2": 4.0,   # 软门槛 (>= 70% 律师认可)
    "D3": 3.25,  # 软门槛 (>= 65% 律师认可)
    "D4": 5.0,   # 硬门槛 (0 违规)
    "D5": 3.5,   # 软门槛
}

# 律师画像对应 (从 lawyer-profiles-w6.md §1 总览)
LAWYER_PROFILES = {
    "L1": {"类型": "单飞律师", "专业": "民商 + 刑事", "执业年限": "8-15 年", "业务量": "5-10 件/月", "立场": "甲方/借款人"},
    "L2": {"类型": "小所合伙人", "专业": "民商 + 合同", "执业年限": "10-20 年", "业务量": "10-30 件/月", "立场": "乙方/主任"},
    "L3": {"类型": "小所 (婚姻家事)", "专业": "婚姻家事 + 合同", "执业年限": "5-10 年", "业务量": "5-10 件/月", "立场": "乙方/婚姻"},
    "L4": {"类型": "中所合伙人", "专业": "金融 + 商事", "执业年限": "15-25 年", "业务量": "30-100 件/月", "立场": "甲方/设备买方"},
    "L5": {"类型": "企业法务总监", "专业": "合同 + 合规", "执业年限": "8-15 年", "业务量": "100+ 件/月", "立场": "审查方/企业"},
}

# 评审场次
REVIEW_SESSIONS = {
    "评审 #1 (2026-07-19)": ["L1", "L2", "L3"],
    "评审 #2 (2026-07-26)": ["L4", "L5"],
}


# ============ 数据类 ============

@dataclass
class LawyerScore:
    """单个律师评分"""
    lawyer_id: str  # L1, L2, ...
    lawyer_name: str  # 真实姓名 (脱敏存储)
    review_session: str  # 评审 #1 / 评审 #2
    review_date: str  # 评审日期
    scores: dict = field(default_factory=dict)  # {"D1": 4.5, "D2": 4.0, ...}
    notes: str = ""  # 评分备注 (从 review-template §6-§10 提取)
    overall: float = 0.0  # 综合评分 (自动计算)
    pass_status: str = ""  # 通过/有条件通过/不通过

    def compute_overall(self) -> float:
        """计算综合评分 (按 DIM_WEIGHTS 加权)"""
        if not self.scores:
            return 0.0
        overall = sum(self.scores.get(dim, 0) * weight for dim, weight in DIM_WEIGHTS.items())
        self.overall = round(overall, 2)
        return self.overall

    def check_pass(self) -> str:
        """检查是否通过 (硬门槛 + 软门槛)"""
        # 硬门槛: D1 >= 4.25 + D4 = 5
        if self.scores.get("D1", 0) < PASS_THRESHOLDS["D1"]:
            return "不通过 (D1 致命/重大准确率 < 4.25)"
        if self.scores.get("D4", 0) < PASS_THRESHOLDS["D4"]:
            return "不通过 (D4 中立性 < 5, 0 违规硬门槛)"
        # 综合门槛
        if self.compute_overall() < PASS_THRESHOLDS["综合"]:
            return "不通过 (综合评分 < 4.0)"
        # 软门槛 (非阻断, 仅标注)
        soft_fail = []
        if self.scores.get("D2", 0) < PASS_THRESHOLDS["D2"]:
            soft_fail.append(f"D2 {self.scores.get('D2')} < 4.0")
        if self.scores.get("D3", 0) < PASS_THRESHOLDS["D3"]:
            soft_fail.append(f"D3 {self.scores.get('D3')} < 3.25")
        if self.scores.get("D5", 0) < PASS_THRESHOLDS["D5"]:
            soft_fail.append(f"D5 {self.scores.get('D5')} < 3.5")
        if soft_fail:
            return f"有条件通过 ({', '.join(soft_fail)})"
        return "通过"

    def to_dict(self) -> dict:
        return {
            "lawyer_id": self.lawyer_id,
            "lawyer_name": self.lawyer_name,
            "review_session": self.review_session,
            "review_date": self.review_date,
            "scores": self.scores,
            "overall": self.compute_overall(),
            "pass_status": self.check_pass(),
            "notes": self.notes,
        }


# ============ 数据类: 评审现场问题 (W7) ============

@dataclass
class ReviewQuestion:
    """W7 评审现场律师问题 (从 SQLite review_questions 表读取)

    Schema:
        lawyer_id     TEXT (L1-L5)
        question_text TEXT
        category      TEXT (产品/技术/法务/其他)
        context       TEXT (可选)
        status        TEXT (open / answered / triaged / deferred)
        created_at    DATETIME
    """
    id: int
    lawyer_id: str
    question_text: str
    category: str
    context: Optional[str]
    status: str
    created_at: str


def load_questions_from_db(db_path: Path, verbose: bool = False) -> List[ReviewQuestion]:
    """从 SQLite 数据库读取 review_questions 表 (W7 新增)

    Args:
        db_path: SQLite 数据库文件路径 (默认 backend/cases-crawler/data/lexprime.db)
        verbose: 打印调试信息

    Returns:
        List[ReviewQuestion], 若表不存在或 DB 不可用返回 []
    """
    if not SQLITE_AVAILABLE:
        if verbose:
            print("[WARN] sqlite3 不可用, 跳过问题读取")
        return []
    if not db_path.exists():
        if verbose:
            print(f"[INFO] DB 文件不存在: {db_path}, 跳过问题读取")
        return []
    questions: List[ReviewQuestion] = []
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # 检查表是否存在 (W7 早期可能没建表)
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='review_questions'"
        )
        if not cur.fetchone():
            if verbose:
                print("[INFO] review_questions 表不存在, 跳过")
            conn.close()
            return []
        cur.execute(
            "SELECT id, lawyer_id, question_text, category, context, status, created_at "
            "FROM review_questions ORDER BY created_at DESC"
        )
        for row in cur.fetchall():
            questions.append(ReviewQuestion(
                id=row["id"],
                lawyer_id=row["lawyer_id"],
                question_text=row["question_text"],
                category=row["category"],
                context=row["context"],
                status=row["status"],
                created_at=row["created_at"] or "",
            ))
        conn.close()
        if verbose:
            print(f"[OK] 从 {db_path} 读取 {len(questions)} 条评审问题")
    except Exception as e:
        print(f"[WARN] 读取 review_questions 失败: {e}", file=sys.stderr)
    return questions


def aggregate_questions(questions: List[ReviewQuestion]) -> Dict[str, Any]:
    """聚合问题统计

    Returns:
        {
            "total": N,
            "by_category": {"产品": 3, ...},
            "by_status": {"open": 8, ...},
            "by_lawyer": {"L1": 2, ...},
            "open_questions": [...]  # 待 triage 问题列表
        }
    """
    by_category = Counter()
    by_status = Counter()
    by_lawyer = Counter()
    open_questions: List[ReviewQuestion] = []
    for q in questions:
        by_category[q.category] += 1
        by_status[q.status] += 1
        by_lawyer[q.lawyer_id] += 1
        if q.status == "open":
            open_questions.append(q)
    return {
        "total": len(questions),
        "by_category": dict(by_category),
        "by_status": dict(by_status),
        "by_lawyer": dict(by_lawyer),
        "open_questions": open_questions,
    }


# ============ Markdown 解析 ============

def parse_review_template(filepath: Path) -> Optional[LawyerScore]:
    """
    解析律师评分表 (review-template.md §6-§10) 提取 5 维度评分.

    期望的 Markdown 格式 (§6.4 评分表):
    | D1 三级识别准确率 | 30% | 4.5 | 1.35 | 致命/重大/建议 准确率 |
    | D2 修改建议实用性 | 25% | 4.0 | 1.0 | 质量 + 覆盖度 |
    | D3 谈判策略可执行性 | 20% | 3.5 | 0.7 | 优先级 + 筹码 + 红线 |
    | D4 LLM 输出中立性 | 15% | 5.0 | 0.75 | 0 违规 |
    | D5 UI 流程合理性 | 10% | 4.0 | 0.4 | 易用 + 加载 + 导出 |
    | **综合** | 100% | - | 4.2 | ≥ 4.0 通过 |

    也支持旧格式 (只有 D1-D5 列, 没有加权分):
    | D1 三级识别准确率 | 30% | 4.5 | ___ | 备注 |
    """
    if not filepath.exists():
        return None

    content = filepath.read_text(encoding="utf-8")

    # 提取律师基本信息
    lawyer_id = ""
    lawyer_name = ""
    review_date = ""
    review_session = ""

    # 律师 ID (从文件名推断: lawyer_review_skill2_L1_xxx.md)
    m = re.search(r"lawyer_review_skill2_(L\d)", filepath.stem)
    if m:
        lawyer_id = m.group(1)

    # 律师姓名 (从 §1.1 评审律师信息表提取)
    m = re.search(r"评审人\s*\|\s*([^\n|]+?)\s*\|", content)
    if m:
        lawyer_name = m.group(1).strip()
    if not lawyer_name:
        # 备选: 律师姓名
        m = re.search(r"律师姓名[：:]\s*([^\n]+)", content)
        if m:
            lawyer_name = m.group(1).strip()
    if not lawyer_name:
        lawyer_name = f"{lawyer_id}_脱敏"

    # 评审日期
    m = re.search(r"评审日期\s*\|\s*([^\n|]+?)\s*\|", content)
    if m:
        review_date = m.group(1).strip()

    # 评审场次
    m = re.search(r"评审场次\s*\|\s*([^\n|]+?)\s*\|", content)
    if m:
        review_session = m.group(1).strip()

    # 推断评审场次
    if not review_session:
        for session, lawyers in REVIEW_SESSIONS.items():
            if lawyer_id in lawyers:
                review_session = session
                break

    # 提取 5 维度评分
    scores = {}
    for dim in ["D1", "D2", "D3", "D4", "D5"]:
        # 模式 1: | D1 xxx | 30% | 4.5 | 1.35 | 备注 |
        pattern = rf"\|\s*{dim}\s+[^\n|]*?\|\s*\d+%\s*\|\s*([\d.]+)\s*\|"
        m = re.search(pattern, content)
        if m:
            scores[dim] = float(m.group(1))
            continue

        # 模式 2: | D1 xxx | 4.5 |
        pattern = rf"\|\s*{dim}\s+[^\n|]*?\|\s*([\d.]+)\s*\|"
        m = re.search(pattern, content)
        if m:
            scores[dim] = float(m.group(1))
            continue

        # 模式 3: **D1**: 4.5
        pattern = rf"\*\*{dim}\*\*[：:]\s*([\d.]+)"
        m = re.search(pattern, content)
        if m:
            scores[dim] = float(m.group(1))

    if not scores:
        return None

    score = LawyerScore(
        lawyer_id=lawyer_id,
        lawyer_name=lawyer_name,
        review_session=review_session,
        review_date=review_date,
        scores=scores,
    )
    score.compute_overall()
    score.pass_status = score.check_pass()

    return score


# ============ 汇总报告生成 ============

def generate_summary(
    scores: list[LawyerScore],
    output_path: Path,
    input_dir: Path,
    questions: Optional[List[ReviewQuestion]] = None,
    verbose: bool = False,
) -> None:
    """生成汇总报告 review-summary-w6.md (含律师问题 section)"""

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 计算综合统计
    all_overalls = [s.overall for s in scores if s.overall > 0]
    avg_overall = round(sum(all_overalls) / len(all_overalls), 2) if all_overalls else 0.0

    # 维度平均分
    dim_avgs = {}
    for dim in DIM_WEIGHTS.keys():
        dim_scores = [s.scores.get(dim, 0) for s in scores if dim in s.scores]
        if dim_scores:
            dim_avgs[dim] = round(sum(dim_scores) / len(dim_scores), 2)

    # 通过率
    pass_count = sum(1 for s in scores if "通过" in s.pass_status and "不" not in s.pass_status)
    conditional_count = sum(1 for s in scores if "有条件通过" in s.pass_status)
    fail_count = sum(1 for s in scores if "不通过" in s.pass_status)
    total = len(scores)

    # 排名 (按综合评分)
    ranked = sorted(scores, key=lambda x: x.overall, reverse=True)

    # 构建 Markdown
    md = []
    md.append("# W6 律师评审 #1 #2 综合评分汇总 (review-summary-w6.md)")
    md.append("")
    md.append(f"> **生成时间**: {now}")
    md.append("> **整理人**: 产品经理 (lex-pm) + 总指挥 (42081)")
    md.append(f"> **数据来源**: {input_dir} (5 律师评分表)")
    md.append("> **覆盖范围**: 评审 #1 (07-19, L1/L2/L3) + 评审 #2 (07-26, L4/L5) = 5 律师")
    md.append("> **关联文件**:")
    md.append("> - `lawyer-profiles-w6.md` (5 律师画像)")
    md.append("> - `review-questions-w6.md` (25 问评审题库)")
    md.append("> - `review-process-w6.md` (评审流程手册)")
    md.append("> - `contact-channel-w6.md` (律师咨询通道)")
    md.append("> - `../skills/contract-review/scoring-rubric.md` (评分细则)")
    md.append("")

    # §1 综合结论
    md.append("---")
    md.append("")
    md.append("## 1. 综合结论")
    md.append("")
    if pass_count == total:
        verdict = "🟢 **全部通过**"
    elif pass_count + conditional_count == total:
        verdict = "🟡 **全部有条件通过** (软门槛触发 P0/P1 改进)"
    elif fail_count == total:
        verdict = "🔴 **全部不通过** (硬门槛不达标, 触发 W7 P0 修复)"
    elif fail_count > 0:
        verdict = f"🟠 **{pass_count + conditional_count}/{total} 通过, {fail_count} 不通过** (混合结果)"
    else:
        verdict = "⚪ **待评审**"

    md.append(f"### 1.1 评审结论: {verdict}")
    md.append("")
    md.append(f"- **通过率**: {pass_count}/{total} ({round(100 * pass_count / total, 1)}%) 完全通过")
    md.append(f"- **有条件通过率**: {conditional_count}/{total} ({round(100 * conditional_count / total, 1)}%)")
    md.append(f"- **不通过率**: {fail_count}/{total} ({round(100 * fail_count / total, 1)}%)")
    md.append(f"- **综合评分均值**: {avg_overall} / 5.0 (门槛 ≥ 4.0)")
    md.append("")

    md.append("### 1.2 5 维度均值")
    md.append("")
    md.append("| 维度 | 均值 | 门槛 | 状态 |")
    md.append("|---|---|---|---|")
    for dim, weight in DIM_WEIGHTS.items():
        avg = dim_avgs.get(dim, 0.0)
        threshold = PASS_THRESHOLDS.get(dim, 4.0)
        status = "✅ 通过" if avg >= threshold else "❌ 不达标"
        md.append(f"| {dim} {DIM_NAMES[dim]} | {avg} | ≥ {threshold} | {status} |")
    md.append("")

    # §2 律师画像 + 评审侧重
    md.append("---")
    md.append("")
    md.append("## 2. 律师画像 + 评审侧重 (来自 lawyer-profiles-w6.md)")
    md.append("")
    md.append("| 律师 | 类型 | 专业 | 执业年限 | 业务量 (件/月) | 立场 | 评审场次 | 评审侧重 |")
    md.append("|---|---|---|---|---|---|---|---|")
    for s in scores:
        profile = LAWYER_PROFILES.get(s.lawyer_id, {})
        md.append(
            f"| {s.lawyer_id} {s.lawyer_name} | {profile.get('类型', '-')} | {profile.get('专业', '-')} | "
            f"{profile.get('执业年限', '-')} | {profile.get('业务量', '-')} | {profile.get('立场', '-')} | "
            f"{s.review_session} | {profile.get('类型', '-')} 视角 |"
        )
    md.append("")

    # §3 评分汇总表
    md.append("---")
    md.append("")
    md.append("## 3. 评分汇总表 (5 律师 × 5 维度)")
    md.append("")
    md.append("| 律师 | D1 (30%) | D2 (25%) | D3 (20%) | D4 (15%) | D5 (10%) | 综合 | 通过状态 |")
    md.append("|---|---|---|---|---|---|---|---|")
    for s in ranked:
        d1 = s.scores.get("D1", 0)
        d2 = s.scores.get("D2", 0)
        d3 = s.scores.get("D3", 0)
        d4 = s.scores.get("D4", 0)
        d5 = s.scores.get("D5", 0)
        overall = s.overall
        status = s.pass_status
        md.append(
            f"| {s.lawyer_id} | {d1} | {d2} | {d3} | {d4} | {d5} | **{overall}** | {status} |"
        )
    md.append("")
    md.append(f"**均值**: D1 {dim_avgs.get('D1', '-')} / D2 {dim_avgs.get('D2', '-')} / "
              f"D3 {dim_avgs.get('D3', '-')} / D4 {dim_avgs.get('D4', '-')} / "
              f"D5 {dim_avgs.get('D5', '-')} / **综合 {avg_overall}**")
    md.append("")

    # §4 综合排名
    md.append("---")
    md.append("")
    md.append("## 4. 综合排名")
    md.append("")
    md.append("| 排名 | 律师 | 综合评分 | 通过状态 | 类型 |")
    md.append("|---|---|---|---|---|")
    for i, s in enumerate(ranked, 1):
        profile = LAWYER_PROFILES.get(s.lawyer_id, {})
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, "  ")
        md.append(f"| {medal} #{i} | {s.lawyer_id} {s.lawyer_name} | {s.overall} | {s.pass_status} | {profile.get('类型', '-')} |")
    md.append("")

    # §5 关键发现
    md.append("---")
    md.append("")
    md.append("## 5. 关键发现 (PM 整理)")
    md.append("")
    md.append("### 5.1 强项 (评分 ≥ 4.5 维度)")
    md.append("")
    strong_dims = [(dim, avg) for dim, avg in dim_avgs.items() if avg >= 4.5]
    if strong_dims:
        for dim, avg in strong_dims:
            md.append(f"- ✅ **{dim} {DIM_NAMES[dim]}** (均值 {avg}): 律师认可度高")
    else:
        md.append("- (无 ≥ 4.5 维度)")
    md.append("")

    md.append("### 5.2 弱项 (评分 < 3.5 维度)")
    md.append("")
    weak_dims = [(dim, avg) for dim, avg in dim_avgs.items() if avg < 3.5]
    if weak_dims:
        for dim, avg in weak_dims:
            md.append(f"- ⚠️ **{dim} {DIM_NAMES[dim]}** (均值 {avg}): 需 P0 改进")
    else:
        md.append("- (无 < 3.5 维度)")
    md.append("")

    md.append("### 5.3 一票否决项检查")
    md.append("")
    veto_failed = []
    for s in scores:
        if s.scores.get("D1", 0) < 4.25:
            veto_failed.append(f"  - {s.lawyer_id}: D1 = {s.scores.get('D1')} (< 4.25, 致命/重大漏检)")
        if s.scores.get("D4", 0) < 5.0:
            veto_failed.append(f"  - {s.lawyer_id}: D4 = {s.scores.get('D4')} (< 5.0, 中立性违规)")

    if veto_failed:
        md.append("**触发一票否决**:")
        for line in veto_failed:
            md.append(line)
    else:
        md.append("**未触发一票否决** ✅")
    md.append("")

    md.append("### 5.4 律师反馈亮点")
    md.append("")
    md.append("(评审后 24h 由 PM 整理, 替换此节)")
    md.append("")
    md.append("- (待律师评分表整理后回填)")
    md.append("")

    md.append("### 5.5 律师反馈问题")
    md.append("")
    md.append("(评审后 24h 由 PM 整理, 替换此节)")
    md.append("")
    md.append("- (待律师评分表整理后回填)")
    md.append("")

    # §6 W7 新增: 律师现场问题汇总 (从 SQLite review_questions 读取)
    md.append("---")
    md.append("")
    md.append("## 6. 律师现场问题汇总 (W7 review_questions JOIN)")
    md.append("")
    if questions is None or len(questions) == 0:
        md.append("(评审现场无律师提交问题, 或 SQLite review_questions 表为空)")
        md.append("")
        md.append("**说明**: 律师在评审现场口头提到但 Skill 2 答不到 / 想深挖 / PRD 建议的问题, 应通过")
        md.append("`POST /api/review/question` 端点实时提交到 SQLite review_questions 表.")
        md.append("")
    else:
        q_stats = aggregate_questions(questions)
        md.append(f"**总问题数**: {q_stats['total']} 条 (评审现场 PM 助理录入)")
        md.append("")
        md.append("### 6.1 问题分布")
        md.append("")
        md.append("**按分类**:")
        md.append("")
        md.append("| 分类 | 数量 | 占比 |")
        md.append("|---|---|---|")
        for cat, cnt in sorted(q_stats["by_category"].items(), key=lambda x: -x[1]):
            pct = round(100 * cnt / max(q_stats["total"], 1), 1)
            md.append(f"| {cat} | {cnt} | {pct}% |")
        md.append("")
        md.append("**按状态**:")
        md.append("")
        md.append("| 状态 | 数量 | 含义 |")
        md.append("|---|---|---|")
        status_meaning = {
            "open": "待 triage (PM 24h 内分派)",
            "triaged": "已分派 (转给对应 agent)",
            "answered": "已回答 (在产品会议答复律师)",
            "deferred": "延后 (W8+ 处理)",
        }
        for st, cnt in sorted(q_stats["by_status"].items(), key=lambda x: -x[1]):
            md.append(f"| {st} | {cnt} | {status_meaning.get(st, '-')} |")
        md.append("")
        md.append("**按律师**:")
        md.append("")
        md.append("| 律师 | 问题数 |")
        md.append("|---|---|")
        for lid, cnt in sorted(q_stats["by_lawyer"].items()):
            md.append(f"| {lid} | {cnt} |")
        md.append("")

        # 6.2 待 triage 问题清单 (P0 - 优先处理)
        md.append("### 6.2 待 triage 问题清单 (status=open)")
        md.append("")
        open_qs = q_stats["open_questions"]
        if open_qs:
            md.append("| # | 律师 | 分类 | 问题 | 场景 | 提交时间 |")
            md.append("|---|---|---|---|---|---|")
            for i, q in enumerate(open_qs, 1):
                ctx = (q.context or "")[:80] + ("..." if q.context and len(q.context) > 80 else "")
                md.append(f"| {i} | {q.lawyer_id} | {q.category} | {q.question_text} | {ctx} | {q.created_at} |")
        else:
            md.append("✅ 所有问题已 triage 或 answered")
        md.append("")

        # 6.3 Top 5 改进 + Top 3 新需求 (prd-feedback v1.0 自动生成源)
        md.append("### 6.3 律师问题 → PRD v1.0 改进候选 (自动生成)")
        md.append("")
        md.append("基于律师问题分类 + 评分均值, 自动识别:")
        md.append("")
        # 从评分 + 问题综合推断 Top 改进
        weak_dims = [(dim, avg) for dim, avg in dim_avgs.items() if avg < 4.0]
        if weak_dims or questions:
            md.append("**Top 5 改进候选**:")
            md.append("")
            md.append("| 优先级 | 类别 | 维度/问题 | 触发源 | 建议 |")
            md.append("|---|---|---|---|---|")
            pri_counter = 0
            # 1. 低分维度
            for dim, avg in sorted(weak_dims, key=lambda x: x[1])[:3]:
                pri_counter += 1
                md.append(f"| P{pri_counter} | 评分 | {dim} {DIM_NAMES[dim]} (均值 {avg}) | rubric < 4.0 | 扩大{dim}召回 + W7 复评 |")
            # 2. 高频问题分类
            top_cat = q_stats["by_category"].most_common(1)
            if top_cat:
                cat, cnt = top_cat[0]
                pri_counter += 1
                md.append(f"| P{pri_counter} | 问题 | {cat}类 ({cnt} 条) | 律师现场提到 ≥ 2 次 | 转 lex-{'ai' if cat == '技术' else 'design' if cat == '产品' else 'coder'} track |")
            # 3. 中立性问题
            if "法务" in q_stats["by_category"]:
                pri_counter += 1
                md.append(f"| P{pri_counter} | 中立性 | 法务类问题 | 中立性违规风险 | language_guard 强化 + 全量 output.json 抽样审计 |")
            md.append("")
            md.append("**Top 3 新需求候选**:")
            md.append("")
            md.append("| # | 类别 | 来源 | 描述 |")
            md.append("|---|---|---|---|")
            # 从具体问题里取代表性 3 条
            sample_qs = [q for q in questions if q.status == "open"][:3]
            for i, q in enumerate(sample_qs, 1):
                md.append(f"| {i} | {q.category} | {q.lawyer_id} 现场 | {q.question_text[:60]}{'...' if len(q.question_text) > 60 else ''} |")
            md.append("")

    # §7 行动建议 (W7 重新编号)
    md.append("---")
    md.append("")
    md.append("## 7. 行动建议 (PM 起草 → 总指挥拍板)")
    md.append("")

    if pass_count == total:
        md.append("### 7.1 立即行动")
        md.append("")
        md.append("- [ ] 5 律师 30 天免费试用卡激活率跟踪 (W6 末 - W7 末)")
        md.append("- [ ] 律师推荐语收集 → marketing")
        md.append("- [ ] 律师引荐 #R3 #R4 启动下一批评审")
        md.append("")
        md.append("### 7.2 短期改进 (W7 - W8)")
        md.append("")
        md.append("- [ ] 评分 4.0-4.5 维度 → P1 改进")
        md.append("- [ ] 反馈给 lex-ai Track E (P1 改进项)")
        md.append("- [ ] 反馈给 lex-design + lex-coder (UI 调整清单)")
        md.append("")
        if questions:
            md.append("### 7.3 律师问题 triage (W7 新增)")
            md.append("")
            md.append(f"- [ ] review_questions 表 {len(questions)} 条问题 → 24h 内 triage")
            md.append("- [ ] status=open 问题分配到对应 agent (lex-ai / lex-design / lex-coder)")
            md.append("- [ ] 1 周后回访律师确认已解决问题 → status=answered")
            md.append("")
    elif fail_count > 0:
        md.append("### 7.1 P0 紧急改进 (W7)")
        md.append("")
        md.append("- [ ] 触发一票否决的律师反馈 → lex-ai Track E 紧急修复")
        md.append("- [ ] language_guard 强化 (D4 < 5 必须修复)")
        md.append("- [ ] 致命/重大识别算法优化 (D1 < 4.25 必须修复)")
        md.append("- [ ] 8 月底律师复评")
        md.append("")
        md.append("### 7.2 短期改进 (W7 - W8)")
        md.append("")
        md.append("- [ ] 评分 3.5-4.0 维度 → P1 改进")
        md.append("- [ ] 评分 3.5 以下维度 → P0 改进")
        md.append("")
    else:
        md.append("### 7.1 短期改进 (W7)")
        md.append("")
        md.append("- [ ] 软门槛未达维度 → P1 改进")
        md.append("- [ ] 律师反馈问题 → lex-ai Track E")
        md.append("- [ ] 8 月底律师复评")
        md.append("")

    # §8 附录
    md.append("---")
    md.append("")
    md.append("## 8. 附录: 评分计算公式")
    md.append("")
    md.append("```")
    md.append("综合评分 = 0.30 × D1 + 0.25 × D2 + 0.20 × D3 + 0.15 × D4 + 0.10 × D5")
    md.append("")
    md.append("通过条件:")
    md.append("  - 综合评分 >= 4.0")
    md.append("  - D1 (致命/重大准确率) >= 4.25 (硬门槛)")
    md.append("  - D4 (中立性) = 5 (硬门槛, 0 违规)")
    md.append("  - D2 (实用性) >= 4.0 (软门槛, >= 70% 律师认可)")
    md.append("  - D3 (谈判策略) >= 3.25 (软门槛, >= 65% 律师认可)")
    md.append("```")
    md.append("")
    md.append("## 9. 整理人备注 (W7 PM)")
    md.append("")
    md.append("- **文档版本**: v1.0 (评审 #2 后 24h, 自动汇总)")
    md.append("- **生成工具**: scripts/aggregate-review-scores.py (W7 扩展: 含 review_questions JOIN)")
    md.append("- **下版本**: v1.1 (W7 律师试用 1 周后反馈更新)")
    md.append("- **联动文档**:")
    md.append("  - 5 份 lawyer_review_skill2_*.md (单律师独立文件)")
    md.append("  - `../skills/contract-review/prd-feedback.md` (v0.1 → v1.0 真实评审回填)")
    md.append("  - `analysis-w1-w3.md` §8.2 (Skill 2 反馈汇总)")
    md.append("- **数据源**:")
    md.append("  - Markdown: docs/interviews/reviews-w6/ (5 律师评分表)")
    md.append("  - SQLite: review_questions 表 (评审现场 PM 助理录入)")
    md.append("")
    md.append("---")
    md.append("")
    md.append(f"**生成时间**: {now} · **整理人**: 产品经理 (lex-pm) + 总指挥 (42081)")

    # 写文件
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(md), encoding="utf-8")

    if verbose:
        print(f"[OK] 汇总报告已生成: {output_path}")
        print(f"     综合评分均值: {avg_overall}")
        print(f"     通过: {pass_count} | 有条件通过: {conditional_count} | 不通过: {fail_count}")
        if questions:
            print(f"     律师问题: {len(questions)} 条 (按 category: {dict(Counter(q.category for q in questions))})")


# ============ PRD v1.0 自动生成 (W7) ============

def generate_prd_feedback(
    scores: List[LawyerScore],
    questions: List[ReviewQuestion],
    output_path: Path,
    verbose: bool = False,
) -> None:
    """W7 自动生成 docs/skills/contract-review/prd-feedback.md v1.0

    输入:
        scores      - 5 律师评分
        questions   - 评审现场问题 (review_questions)
        output_path - 输出 prd-feedback.md

    内容:
        - 评分 + 问题 → Top 5 改进候选
        - 评分 + 问题 → Top 3 新需求候选
        - 评分维度对比 (vs PRD v0.7.2 § 5.4)
        - 评审通过结论 (用于 PRD release gate)
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 维度均值
    dim_avgs: Dict[str, float] = {}
    for dim in DIM_WEIGHTS.keys():
        dim_scores = [s.scores.get(dim, 0) for s in scores if dim in s.scores]
        if dim_scores:
            dim_avgs[dim] = round(sum(dim_scores) / len(dim_scores), 2)

    all_overalls = [s.overall for s in scores if s.overall > 0]
    avg_overall = round(sum(all_overalls) / len(all_overalls), 2) if all_overalls else 0.0

    # 综合结论
    d1 = dim_avgs.get("D1", 0)
    d4 = dim_avgs.get("D4", 0)
    passes = avg_overall >= 4.0 and d1 >= 4.25 and d4 >= 5.0

    # 问题聚合
    q_stats = aggregate_questions(questions) if questions else {
        "total": 0,
        "by_category": {},
        "by_status": {},
        "by_lawyer": {},
        "open_questions": [],
    }

    # 律师画像
    lawyer_summary = []
    for s in scores:
        profile = LAWYER_PROFILES.get(s.lawyer_id, {})
        lawyer_summary.append({
            "lawyer_id": s.lawyer_id,
            "name": s.lawyer_name,
            "type": profile.get("类型", "-"),
            "overall": s.overall,
            "pass_status": s.pass_status,
        })

    # 写文件
    md: List[str] = []
    md.append("<!-- LexPrime Track E · Skill 2 合同风险审查 · PRD 反馈 (W7 自动生成) -->")
    md.append("# PRD 反馈 · Skill 2 合同风险审查 (W7 律师评审真实反馈)")
    md.append("")
    md.append("> **适用范围**: W6 评审 #1 #2 后, 律师真实评分 + 现场问题汇总 → 自动生成 PRD v1.0 调整建议")
    md.append("> **版本**: v1.0 (W7, 2026-06-29, **评审后自动汇总**)")
    md.append(f"> **生成时间**: {now}")
    md.append("> **生成工具**: scripts/aggregate-review-scores.py --prd-feedback")
    md.append("> **上一版本**: v0.1 (W4 评审准备阶段 PM 起草, 已废)")
    md.append("> **关联文件**:")
    md.append("> - `scoring-rubric.md` (5 评分维度)")
    md.append("> - `../../../docs/interviews/review-summary-w6.md` (评分汇总)")
    md.append("> - `../../../docs/interviews/lawyer-profiles-w6.md` (5 律师画像)")
    md.append("> - `../../../docs/prd/04-cross-cutting.md` § 5.4 (Skill Hub)")
    md.append("> - `../../../docs/prd/03-core-steps.md` § 3.12.2 (各类合同)")
    md.append("")

    # §0 评审结论 (PRD release gate)
    md.append("---")
    md.append("")
    md.append("## 0. 评审结论 (PRD v1.0 release gate)")
    md.append("")
    if passes:
        decision = "🟢 **通过** - Skill 2 达到 v1.0 release 门槛, 可进入 W8 公测"
    elif not scores:
        decision = "⚪ **数据不足** - 等待律师评审提交"
    elif avg_overall >= 3.5:
        decision = "🟡 **有条件通过** - P0 改进后 W7 复评, 暂不 release"
    else:
        decision = "🔴 **不通过** - 重新设计后 W8+ 复评"
    md.append(f"### 决策: {decision}")
    md.append("")
    md.append("| 指标 | 实际 | 门槛 | 通过 |")
    md.append("|---|---|---|---|")
    md.append(f"| 综合评分 (5 律师平均) | {avg_overall} | ≥ 4.0 | {'✅' if avg_overall >= 4.0 else '❌'} |")
    md.append(f"| D1 致命/重大准确率 | {d1} | ≥ 4.25 (硬) | {'✅' if d1 >= 4.25 else '❌'} |")
    md.append(f"| D4 中立性 (硬门槛) | {d4} | = 5.0 (硬, 0 违规) | {'✅' if d4 >= 5.0 else '❌'} |")
    md.append(f"| D2 实用性 | {dim_avgs.get('D2', '-')} | ≥ 4.0 (软) | {'✅' if dim_avgs.get('D2', 0) >= 4.0 else '❌'} |")
    md.append(f"| D3 谈判策略 | {dim_avgs.get('D3', '-')} | ≥ 3.25 (软) | {'✅' if dim_avgs.get('D3', 0) >= 3.25 else '❌'} |")
    md.append(f"| D5 UI 流程 | {dim_avgs.get('D5', '-')} | ≥ 3.5 (软) | {'✅' if dim_avgs.get('D5', 0) >= 3.5 else '❌'} |")
    md.append("")
    md.append(f"**评审通过率**: {sum(1 for s in scores if '通过' in s.pass_status and '不' not in s.pass_status)}/{len(scores)} 完全通过")
    md.append(f"**律师问题**: {q_stats['total']} 条 (status=open 待 triage: {len(q_stats['open_questions'])})")
    md.append("")

    # §1 Top 5 改进候选 (W7 核心交付物)
    md.append("---")
    md.append("")
    md.append("## 1. Top 5 改进候选 (W7 评审驱动)")
    md.append("")
    md.append("基于 5 律师评分均值 + 现场问题分类, 自动识别 P0/P1 改进项:")
    md.append("")
    md.append("| # | 优先级 | 维度/类别 | 触发源 | PRD 调整建议 | 负责人 |")
    md.append("|---|---|---|---|---|---|")
    counter = 0

    # 1-3: 低分维度
    weak_dims = [(dim, avg) for dim, avg in dim_avgs.items() if avg < 4.0]
    for dim, avg in sorted(weak_dims, key=lambda x: x[1])[:3]:
        counter += 1
        if dim == "D1":
            owner = "lex-ai"
            prd = "§ 3.12.2 致命风险关键词召回扩大 + § 5.4 风险分级标准补『期限异常』边界"
        elif dim == "D2":
            owner = "lex-ai"
            prd = "§ 3.12.2 modified_clause_template 行业版本管理 + 接入 LPR 数据"
        elif dim == "D3":
            owner = "lex-ai"
            prd = "§ 5.4 接入 60+ 类案大数据 + W7 丰富立场感知建议"
        elif dim == "D4":
            owner = "lex-ai"
            prd = "language_guard.py 正则升级 + 全量 output.json 抽样审计"
        elif dim == "D5":
            owner = "lex-coder"
            prd = "W7 性能调优 (P95 < 2s) + 导出格式补 PDF 真实导出"
        else:
            owner = "lex-pm"
            prd = "TBD"
        md.append(f"| {counter} | P0 | {dim} {DIM_NAMES[dim]} (均值 {avg}) | rubric < 4.0 | {prd} | {owner} |")

    # 4: 高频问题分类
    if q_stats["by_category"]:
        top_cat_name, top_cat_cnt = Counter(q_stats["by_category"]).most_common(1)[0]
        counter += 1
        if top_cat_cnt >= 2:
            cat_owner = "lex-ai" if top_cat_name == "技术" else "lex-design" if top_cat_name == "产品" else "lex-coder"
            md.append(f"| {counter} | P1 | {top_cat_name}类问题 ({top_cat_cnt} 条) | 律师现场 ≥ 2 次 | § 11 法务自检加 {top_cat_name} 类自查清单 | {cat_owner} |")

    # 5: 中立性 (硬门槛必须)
    if d4 < 5.0:
        counter += 1
        md.append(f"| {counter} | P0 | D4 中立性 ({d4}) | 硬门槛 | § 5.7 强化 language_guard + 抽样审计 | lex-ai |")
    md.append("")

    # §2 Top 3 新需求候选
    md.append("---")
    md.append("")
    md.append("## 2. Top 3 新需求候选 (W7 评审驱动)")
    md.append("")
    md.append("基于律师现场开放问题 (status=open), 自动识别新功能需求:")
    md.append("")
    if not questions:
        md.append("(评审现场无律师问题, 或 review_questions 表为空)")
        md.append("")
        md.append("**注**: 评审现场 PM 助理应通过 `POST /api/review/question` 端点实时录入.")
        md.append("")
    else:
        # 取代表性 open 状态问题
        sample_qs = q_stats["open_questions"][:3] if q_stats["open_questions"] else questions[:3]
        md.append("| # | 类别 | 来源律师 | 需求描述 | 建议落点 |")
        md.append("|---|---|---|---|---|")
        for i, q in enumerate(sample_qs, 1):
            dest = "Skill 2" if q.category == "法务" else "Skill Hub" if q.category == "技术" else "产品" if q.category == "产品" else "TBD"
            md.append(f"| {i} | {q.category} | {q.lawyer_id} ({LAWYER_PROFILES.get(q.lawyer_id, {}).get('类型', '-')}) | {q.question_text} | § 11.3 {dest} |")
        md.append("")

    # §3 评分对比 (vs PRD v0.7.2 § 5.4)
    md.append("---")
    md.append("")
    md.append("## 3. 评分对比 vs PRD v0.7.2 § 5.4 验收标准")
    md.append("")
    md.append("| PRD § 5.4 验收项 | 目标 | 实际 | 状态 |")
    md.append("|---|---|---|---|")
    md.append(f"| 致命/重大/建议识别准确率 | ≥ 85% | D1 = {d1}/5 | {'✅ 达标' if d1 >= 4.25 else '❌ 未达标'} |")
    md.append(f"| 修改建议律师认可度 | ≥ 70% | D2 = {dim_avgs.get('D2', '-')}/5 | {'✅ 达标' if dim_avgs.get('D2', 0) >= 4.0 else '❌ 未达标'} |")
    md.append(f"| 谈判策略可执行 | ≥ 65% | D3 = {dim_avgs.get('D3', '-')}/5 | {'✅ 达标' if dim_avgs.get('D3', 0) >= 3.25 else '❌ 未达标'} |")
    md.append(f"| LLM 输出中立性 | 0 违规 | D4 = {d4}/5 | {'✅ 达标' if d4 >= 5.0 else '❌ 未达标'} |")
    md.append(f"| UI 流程合理 | ≥ 70% | D5 = {dim_avgs.get('D5', '-')}/5 | {'✅ 达标' if dim_avgs.get('D5', 0) >= 3.5 else '❌ 未达标'} |")
    md.append("")

    # §4 律师画像评分
    md.append("---")
    md.append("")
    md.append("## 4. 律师画像 × 评分")
    md.append("")
    md.append("| 律师 | 类型 | 综合 | 通过状态 |")
    md.append("|---|---|---|---|")
    for ls in lawyer_summary:
        md.append(f"| {ls['lawyer_id']} {ls['name']} | {ls['type']} | {ls['overall']} | {ls['pass_status']} |")
    md.append("")

    # §5 PRD § 5.4 调整建议 (自动生成)
    md.append("---")
    md.append("")
    md.append("## 5. PRD § 5.4 调整建议 (W7 → W8 PRD v1.0)")
    md.append("")
    md.append("**调整项** (按优先级排序):")
    md.append("")
    if weak_dims:
        for dim, avg in sorted(weak_dims, key=lambda x: x[1]):
            md.append(f"- [P0/P1] **{dim} {DIM_NAMES[dim]}** 均值 {avg} → PRD § 5.4 加此维度复评 checklist")
    if q_stats["by_category"]:
        for cat, cnt in Counter(q_stats["by_category"]).most_common():
            if cnt >= 2:
                md.append(f"- [P1] **{cat}类问题** {cnt} 条 → PRD § 11 法务自检加 {cat} 自查表")
    md.append("")

    # §6 W7 → W8 行动
    md.append("---")
    md.append("")
    md.append("## 6. W7 → W8 行动 (PM 派单)")
    md.append("")
    md.append("- [ ] **W7 末**: 律师试用 1 周反馈跟踪 (5 律师)")
    md.append("- [ ] **W8 初**: 按 Top 5 改进分配到对应 agent (lex-ai / lex-design / lex-coder)")
    md.append("- [ ] **W8 中**: PRD v1.0 release (基于本文件 § 1 § 2 § 5)")
    md.append("- [ ] **W8 末**: 公测启动 + 邀请码发放")
    md.append("")

    # §7 整理人备注
    md.append("---")
    md.append("")
    md.append("## 7. 整理人备注 (W7 自动生成)")
    md.append("")
    md.append("- **生成工具**: scripts/aggregate-review-scores.py --prd-feedback")
    md.append("- **数据源**:")
    md.append("  - Markdown 评分: docs/interviews/reviews-w6/lawyer_review_skill2_L{1..5}_*.md")
    md.append(f"  - SQLite 现场问题: review_questions 表 ({q_stats['total']} 条)")
    md.append("- **联动文档**:")
    md.append("  - review-summary-w6.md (评分汇总)")
    md.append("  - scoring-rubric.md (评分细则)")
    md.append("- **下一版本**: v1.1 (W7 律师试用 1 周后反馈更新)")
    md.append("")
    md.append("---")
    md.append("")
    md.append(f"**生成时间**: {now} · **生成工具**: scripts/aggregate-review-scores.py --prd-feedback")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(md), encoding="utf-8")

    if verbose:
        print(f"[OK] prd-feedback.md v1.0 已生成: {output_path}")
        print(f"     综合评分: {avg_overall}, 通过: {passes}")
        print(f"     Top 5 改进: {counter} 条, 新需求: {min(len(sample_qs) if questions else 0, 3)} 条")


# ============ CLI 入口 ============

def main():
    parser = argparse.ArgumentParser(
        description="LexPrime W6 律师评审评分自动汇总脚本 (W7 扩展: 含 review_questions JOIN)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python scripts/aggregate-review-scores.py
    python scripts/aggregate-review-scores.py --input docs/interviews/reviews-w6/
    python scripts/aggregate-review-scores.py --output docs/interviews/review-summary-w6.md
    python scripts/aggregate-review-scores.py --verbose
    python scripts/aggregate-review-scores.py --dry-run
    python scripts/aggregate-review-scores.py --db backend/cases-crawler/data/lexprime.db --prd-feedback
        """,
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("docs/interviews/reviews-w6"),
        help="律师评分表目录 (默认: docs/interviews/reviews-w6/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/interviews/review-summary-w6.md"),
        help="汇总报告输出文件 (默认: docs/interviews/review-summary-w6.md)",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("backend/cases-crawler/data/lexprime.db"),
        help="SQLite 数据库路径 (W7 读 review_questions 表, 默认: backend/cases-crawler/data/lexprime.db)",
    )
    parser.add_argument(
        "--prd-feedback",
        action="store_true",
        help="(W7 新增) 同时生成 docs/skills/contract-review/prd-feedback.md v1.0",
    )
    parser.add_argument(
        "--prd-output",
        type=Path,
        default=Path("docs/skills/contract-review/prd-feedback.md"),
        help="prd-feedback.md 输出路径 (默认: docs/skills/contract-review/prd-feedback.md)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="打印详细信息",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅打印不写文件",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="同时输出 JSON 格式评分数据",
    )

    args = parser.parse_args()

    if args.verbose:
        print(f"[INFO] 输入目录: {args.input}")
        print(f"[INFO] 输出文件: {args.output}")
        print(f"[INFO] SQLite DB: {args.db}")
        if args.prd_feedback:
            print(f"[INFO] PRD feedback: {args.prd_output}")

    # 找律师评分表
    if not args.input.exists():
        print(f"[ERROR] 输入目录不存在: {args.input}", file=sys.stderr)
        sys.exit(1)

    files = sorted(args.input.glob("lawyer_review_skill2_*.md"))
    if not files:
        print(f"[WARN] 输入目录无 lawyer_review_skill2_*.md 文件: {args.input}", file=sys.stderr)
        print("[INFO] 期望文件名格式: lawyer_review_skill2_L1_xxx.md")
        sys.exit(2)

    if args.verbose:
        print(f"[INFO] 找到 {len(files)} 份律师评分表:")
        for f in files:
            print(f"       - {f.name}")

    # 解析评分表
    scores: List[LawyerScore] = []
    for f in files:
        s = parse_review_template(f)
        if s:
            scores.append(s)
            if args.verbose:
                print(f"[OK] {f.name}: 综合 {s.overall}, {s.pass_status}")
        else:
            print(f"[WARN] {f.name}: 解析失败, 跳过", file=sys.stderr)

    if not scores:
        print("[ERROR] 无有效评分表, 请检查文件格式", file=sys.stderr)
        sys.exit(3)

    # W7 新增: 从 SQLite 读取 review_questions
    questions: List[ReviewQuestion] = []
    if args.db:
        questions = load_questions_from_db(args.db, verbose=args.verbose)

    # 输出 JSON
    if args.json:
        json_data = {
            "generated_at": datetime.now().isoformat(),
            "lawyer_count": len(scores),
            "question_count": len(questions),
            "scores": [s.to_dict() for s in scores],
            "questions": [
                {
                    "id": q.id,
                    "lawyer_id": q.lawyer_id,
                    "question_text": q.question_text,
                    "category": q.category,
                    "context": q.context,
                    "status": q.status,
                    "created_at": q.created_at,
                }
                for q in questions
            ],
        }
        json_path = args.output.with_suffix(".json")
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.verbose:
            print(f"[OK] JSON 评分+问题数据: {json_path}")

    # 生成汇总
    if args.dry_run:
        print("[DRY-RUN] 仅打印, 不写文件")
        for s in scores:
            print(f"  {s.lawyer_id} {s.lawyer_name}: 综合 {s.overall}, {s.pass_status}")
        if questions:
            print(f"  律师问题: {len(questions)} 条")
            for q in questions[:5]:
                print(f"    [{q.category}/{q.status}] {q.lawyer_id}: {q.question_text[:60]}")
    else:
        generate_summary(scores, args.output, args.input, questions=questions, verbose=args.verbose)
        # W7 新增: 自动生成 prd-feedback.md v1.0
        if args.prd_feedback:
            generate_prd_feedback(scores, questions, args.prd_output, verbose=args.verbose)


if __name__ == "__main__":
    main()