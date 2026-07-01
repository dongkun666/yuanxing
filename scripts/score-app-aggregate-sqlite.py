#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LexPrime Track E · W6 律师评审评分自动汇总脚本
====================================================

用途:
    评审 #1 #2 后 24h 内, PM 收集 5 律师 review-template.md 评分表 (Markdown),
    跑这个脚本自动汇总到 review-summary-w6.md.

输入:
    --input  指定律师评分表目录 (默认 docs/interviews/reviews-w6/)
            每个文件命名: lawyer_review_skill2_{name}.md
            每份文件必须包含 §6.4 评分表 (D1/D2/D3/D4/D5)

输出:
    --output 指定汇总文件 (默认 docs/interviews/review-summary-w6.md)
            包含: §3 评分汇总表 + §4 综合排名 + §5 关键发现

通过门槛 (跟 scoring-rubric.md §1.3 对齐):
    - 综合评分 >= 4.0
    - D1 (致命/重大准确率) >= 4.25 (硬门槛)
    - D4 (中立性) = 5 (硬门槛, 0 违规)
    - D2 (实用性) >= 4.0 (软门槛)
    - D3 (谈判策略) >= 3.25 (软门槛)

用法:
    python scripts/aggregate-review-scores.py
    python scripts/aggregate-review-scores.py --input docs/interviews/reviews-w6/ --output docs/interviews/review-summary-w6.md
    python scripts/aggregate-review-scores.py --verbose
    python scripts/aggregate-review-scores.py --dry-run  # 仅打印不写文件

关联文件:
    - docs/skills/contract-review/scoring-rubric.md (评分细则)
    - docs/interviews/review-template.md (律师评分表模板)
    - docs/interviews/review-questions-w6.md (25 问评审题库)
    - docs/interviews/review-process-w6.md (评审流程)
    - docs/interviews/lawyer-profiles-w6.md (5 律师画像)

整理人: lex-pm (W6 Day 3, 2026-06-29)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


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
    verbose: bool = False,
) -> None:
    """生成汇总报告 review-summary-w6.md"""

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
    md.append(f"> **整理人**: 产品经理 (lex-pm) + 总指挥 (42081)")
    md.append(f"> **数据来源**: {input_dir} (5 律师评分表)")
    md.append(f"> **覆盖范围**: 评审 #1 (07-19, L1/L2/L3) + 评审 #2 (07-26, L4/L5) = 5 律师")
    md.append(f"> **关联文件**:")
    md.append(f"> - `lawyer-profiles-w6.md` (5 律师画像)")
    md.append(f"> - `review-questions-w6.md` (25 问评审题库)")
    md.append(f"> - `review-process-w6.md` (评审流程手册)")
    md.append(f"> - `contact-channel-w6.md` (律师咨询通道)")
    md.append(f"> - `../skills/contract-review/scoring-rubric.md` (评分细则)")
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

    # §6 行动建议
    md.append("---")
    md.append("")
    md.append("## 6. 行动建议 (PM 起草 → 总指挥拍板)")
    md.append("")

    if pass_count == total:
        md.append("### 6.1 立即行动")
        md.append("")
        md.append("- [ ] 5 律师 30 天免费试用卡激活率跟踪 (W6 末 - W7 末)")
        md.append("- [ ] 律师推荐语收集 → marketing")
        md.append("- [ ] 律师引荐 #R3 #R4 启动下一批评审")
        md.append("")
        md.append("### 6.2 短期改进 (W7 - W8)")
        md.append("")
        md.append("- [ ] 评分 4.0-4.5 维度 → P1 改进")
        md.append("- [ ] 反馈给 lex-ai Track E (P1 改进项)")
        md.append("- [ ] 反馈给 lex-design + lex-coder (UI 调整清单)")
        md.append("")
    elif fail_count > 0:
        md.append("### 6.1 P0 紧急改进 (W7)")
        md.append("")
        md.append("- [ ] 触发一票否决的律师反馈 → lex-ai Track E 紧急修复")
        md.append("- [ ] language_guard 强化 (D4 < 5 必须修复)")
        md.append("- [ ] 致命/重大识别算法优化 (D1 < 4.25 必须修复)")
        md.append("- [ ] 8 月底律师复评")
        md.append("")
        md.append("### 6.2 短期改进 (W7 - W8)")
        md.append("")
        md.append("- [ ] 评分 3.5-4.0 维度 → P1 改进")
        md.append("- [ ] 评分 3.5 以下维度 → P0 改进")
        md.append("")
    else:
        md.append("### 6.1 短期改进 (W7)")
        md.append("")
        md.append("- [ ] 软门槛未达维度 → P1 改进")
        md.append("- [ ] 律师反馈问题 → lex-ai Track E")
        md.append("- [ ] 8 月底律师复评")
        md.append("")

    # §7 附录
    md.append("---")
    md.append("")
    md.append("## 7. 附录: 评分计算公式")
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
    md.append("## 8. 整理人备注 (W6 PM)")
    md.append("")
    md.append(f"- **文档版本**: v1.0 (评审 #2 后 24h, 自动汇总)")
    md.append(f"- **生成工具**: scripts/aggregate-review-scores.py")
    md.append(f"- **下版本**: v1.1 (W7 律师试用 1 周后反馈更新)")
    md.append(f"- **联动文档**:")
    md.append(f"  - 5 份 lawyer_review_skill2_*.md (单律师独立文件)")
    md.append(f"  - `../skills/contract-review/prd-feedback.md` (v0.1 → v1.0 真实评审回填)")
    md.append(f"  - `analysis-w1-w3.md` §8.2 (Skill 2 反馈汇总)")
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


# ============ CLI 入口 ============

def main():
    parser = argparse.ArgumentParser(
        description="LexPrime W6 律师评审评分自动汇总脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python scripts/aggregate-review-scores.py
    python scripts/aggregate-review-scores.py --input docs/interviews/reviews-w6/
    python scripts/aggregate-review-scores.py --output docs/interviews/review-summary-w6.md
    python scripts/aggregate-review-scores.py --verbose
    python scripts/aggregate-review-scores.py --dry-run
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

    # 找律师评分表
    if not args.input.exists():
        print(f"[ERROR] 输入目录不存在: {args.input}", file=sys.stderr)
        sys.exit(1)

    files = sorted(args.input.glob("lawyer_review_skill2_*.md"))
    if not files:
        print(f"[WARN] 输入目录无 lawyer_review_skill2_*.md 文件: {args.input}", file=sys.stderr)
        print(f"[INFO] 期望文件名格式: lawyer_review_skill2_L1_xxx.md")
        sys.exit(2)

    if args.verbose:
        print(f"[INFO] 找到 {len(files)} 份律师评分表:")
        for f in files:
            print(f"       - {f.name}")

    # 解析评分表
    scores = []
    for f in files:
        s = parse_review_template(f)
        if s:
            scores.append(s)
            if args.verbose:
                print(f"[OK] {f.name}: 综合 {s.overall}, {s.pass_status}")
        else:
            print(f"[WARN] {f.name}: 解析失败, 跳过", file=sys.stderr)

    if not scores:
        print(f"[ERROR] 无有效评分表, 请检查文件格式", file=sys.stderr)
        sys.exit(3)

    # 输出 JSON
    if args.json:
        json_data = {
            "generated_at": datetime.now().isoformat(),
            "lawyer_count": len(scores),
            "scores": [s.to_dict() for s in scores],
        }
        json_path = args.output.with_suffix(".json")
        json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.verbose:
            print(f"[OK] JSON 评分数据: {json_path}")

    # 生成汇总
    if args.dry_run:
        print("[DRY-RUN] 仅打印, 不写文件")
        for s in scores:
            print(f"  {s.lawyer_id} {s.lawyer_name}: 综合 {s.overall}, {s.pass_status}")
    else:
        generate_summary(scores, args.output, args.input, verbose=args.verbose)


if __name__ == "__main__":
    main()