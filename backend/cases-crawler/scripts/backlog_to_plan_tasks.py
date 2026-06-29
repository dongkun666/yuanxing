"""
W9 A2 backlog → plan task 转换脚本
(lex-coder · 2026-06-29)

数据源:
- prd_backlog 表 (W8 A2 backlog_router.py 新增) — 现有 42 ticket (17 P0 open + 18 P1 open)
- category: 产品 / 技术 / 法务 / 其他
- priority: P0 / P1 / P2 / P3
- owner: lex-pm / lex-coder / lex-ai / lex-design / unassigned

输出:
- docs/plans/plan-auto-w{N+1}-from-backlog.yaml — mavis team plan YAML 范本兼容
  - version: 1
  - plan.name / max_concurrency / auto_accept / verifier_config
  - tasks: 按 category 分组, 每个 group 1 task, ticket 列表嵌 description

为什么按 category 分组:
- W8 A2 owner 预设 (lex-coder/lex-ai/lex-pm/lex-design) 是种子级别, 跨类别混在一起调度
  会让单 task 的 scope 模糊
- 按 category 分组后, 每个 task 的 assigned_to 清晰 (技术类→lex-ai, 产品类→lex-pm/coder)
- 每个 group 包含的 ticket id 让 agent 直接拿单子干

执行:
  cd backend/cases-crawler
  python scripts/backlog_to_plan_tasks.py \\
      --week 10 \\
      --out ../docs/plans/plan-auto-w10-from-backlog.yaml \\
      --priorities P0,P1

W9 plan 接力 (plan_841af3e9 a2-backlog-to-plan-tasks):
- A1 完成 → prd_backlog 42 ticket 入库 (commit 5437535)
- A2 backlog_to_plan_tasks.py → 把 17 P0 + 18 P1 = 35 ticket 按 category 分组转 plan YAML
- A2 auto_schedule_backlog.py → 干跑调度 (不真启 plan engine)
- 验证: pytest + ruff, 详见 tests/test_backlog_to_plan_tasks.py
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 项目根路径 (跟 migrate_review_to_backlog.py 一致)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ====== prd_backlog 表元数据 (跟 api/backlog_router.py PrdBacklog 对齐) ======
BACKLOG_TABLE_COLUMNS = [
    "id",
    "source_question_id",
    "source_lawyer_id",
    "title",
    "description",
    "category",
    "priority",
    "owner",
    "status",
    "created_at",
    "updated_at",
]

# 仅当 status = open 时才纳入调度 (跟 backlog_router 的 BACKLOG_STATUSES 对齐)
SCHEDULABLE_STATUSES = ("open",)

# 跳过的状态 (调度时不纳入)
SKIPPABLE_STATUSES = ("in_progress", "done", "deferred", "wontfix")

# 默认 DB 路径 (跟 core/config.py Settings.database_url 一致)
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "lexprime.db"

# category → assigned_to 映射 (lex-* agent)
# 跟 migrate_review_to_backlog.py SEED 的 owner 字段对齐
CATEGORY_OWNER_MAP: Dict[str, str] = {
    "产品": "lex-pm",       # 产品需求 → PM 排期
    "技术": "lex-ai",       # 技术实现 → AI/数据 agent
    "法务": "lex-coder",    # 法务模板/UI → coder (实现最快的 agent)
    "其他": "lex-coder",    # 其他类默认派 coder
}

# 每个 category 的 task title 前缀 (W9+ 排期模板)
CATEGORY_TASK_TITLE = {
    "产品": "W{N} 产品 backlog P{priority} 调度 ({count} ticket)",
    "技术": "W{N} 技术 backlog P{priority} 调度 ({count} ticket)",
    "法务": "W{N} 法务 backlog P{priority} 调度 ({count} ticket)",
    "其他": "W{N} 其他 backlog P{priority} 调度 ({count} ticket)",
}


# ====== DB 读 ticket ======
def read_open_tickets(
    db_path: Path,
    priorities: Tuple[str, ...] = ("P0", "P1"),
    statuses: Tuple[str, ...] = SCHEDULABLE_STATUSES,
) -> List[Dict[str, Any]]:
    """从 SQLite prd_backlog 表读 tickets

    Args:
        db_path: SQLite 数据库文件路径
        priorities: 允许的 priority 元组, 默认 (P0, P1)
        statuses: 允许的 status 元组, 默认 open

    Returns:
        ticket dict 列表, 字段全小写 (SQLite 列名)
    """
    if not db_path.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")

    placeholders_p = ",".join("?" * len(priorities))
    placeholders_s = ",".join("?" * len(statuses))

    # 显式列出列名, 避免后续 schema 漂移
    columns_sql = ", ".join(BACKLOG_TABLE_COLUMNS)
    sql = f"""
        SELECT {columns_sql}
        FROM prd_backlog
        WHERE priority IN ({placeholders_p})
          AND status IN ({placeholders_s})
        ORDER BY
            CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1
                          WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 ELSE 4 END,
            category,
            id
    """

    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, priorities + statuses).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def filter_skip_statuses(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """过滤掉 SCHEDULABLE_STATUSES 之外的 ticket (保险, 防 SQL 漏写)

    实际查询已用 status IN (SCHEDULABLE_STATUSES), 这里防御性兜底
    """
    return [t for t in tickets if t.get("status") not in SKIPPABLE_STATUSES]


# ====== 分组 ======
def group_by_category(tickets: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """按 category 分组 ticket

    Returns:
        {category: [ticket_dict, ...]} 按 category 名索引, 顺序保持 lex-coder 习惯 (产品/技术/法务/其他)
    """
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for t in tickets:
        cat = t["category"]
        grouped[cat].append(t)
    return dict(grouped)


def group_by_priority(tickets: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """按 priority 分组 (备用, 跟 category 二选一)

    Returns:
        {priority: [ticket_dict, ...]}
    """
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for t in tickets:
        grouped[t["priority"]].append(t)
    return dict(grouped)


# ====== Plan YAML 构造 ======
def build_plan_yaml(
    week: int,
    tickets: List[Dict[str, Any]],
    grouped: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    max_concurrency: int = 2,
    max_cycles: int = 3,
    now: Optional[datetime] = None,
) -> str:
    """构造 mavis team plan YAML 字符串 (兼容 W8/W9 范本)

    Args:
        week: plan 周数 (e.g. 10 → W10 plan)
        tickets: 所有 ticket 列表 (read_open_tickets 返回)
        grouped: 预分组结果 (默认按 category)
        max_concurrency: 并发上限 (默认 2 跟 W9 plan 对齐)
        max_cycles: 单 task 最大 cycle 数
        now: 当前 UTC 时间 (用于 plan name 时间戳)

    Returns:
        plan YAML 字符串

    Notes:
        - 每个 group → 1 plan task, id = `{category-slug}-{week}-p{priority}`
          - 例: 产品 P0 → `product-w10-p0`; 法务 P1 → `legal-w10-p1`
        - task prompt 用 docstring 嵌 ticket 列表 (id / title / owner), 方便 agent 直接拿单子
        - 既然分组粒度 = category × priority (拆分后任务更多), 简洁起见简化: 一个 category 1 task
          (后续可分拆, 当前版本按 spec 落到 category 粒度)
    """
    if grouped is None:
        grouped = group_by_category(tickets)

    if now is None:
        now = datetime.now(timezone.utc)

    # CATEGORY → slug 映射 (用于 task id)
    category_slug_map = {
        "产品": "product",
        "技术": "tech",
        "法务": "legal",
        "其他": "misc",
    }

    # CATEGORY → 推断 assigned_to
    def _owner_for(cat: str, fallback: str = "lex-coder") -> str:
        return CATEGORY_OWNER_MAP.get(cat, fallback)

    plan_name = f"LexPrime Phase 4 Week {week} 自动调度 (from PRD backlog open P0/P1, {len(tickets)} ticket)"
    created_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    # 构造 task list
    task_blocks: List[str] = []
    task_counter = 0

    # 按 category 顺序遍历 (产品/技术/法务/其他), 保证 plan task id 稳定
    category_order = ["产品", "技术", "法务", "其他"]
    for cat in category_order:
        if cat not in grouped:
            continue
        cat_tickets = grouped[cat]
        slug = category_slug_map[cat]

        # 按 priority 分桶, 显示 ticket 数
        by_pri: Dict[str, int] = defaultdict(int)
        for t in cat_tickets:
            by_pri[t["priority"]] += 1
        priority_summary = ", ".join(
            f"{p}={by_pri[p]}" for p in ("P0", "P1", "P2", "P3") if by_pri[p] > 0
        ) or "0"

        # task id 包含 week 和 category (避免跨 week 冲突)
        task_id = f"{slug}-w{week}-auto"
        task_title = (
            f"W{week} {cat} backlog 自动调度 ({len(cat_tickets)} ticket: {priority_summary})"
        )
        # 推断 owner: 按 category 默认 + ticket 自身 owner 多数决
        owner_votes: Dict[str, int] = defaultdict(int)
        for t in cat_tickets:
            owner_votes[t.get("owner") or "unassigned"] += 1
        # 取多数, 平局时用 category 默认
        sorted_owners = sorted(owner_votes.items(), key=lambda kv: (-kv[1], kv[0]))
        if sorted_owners and sorted_owners[0][1] >= len(cat_tickets) / 2:
            assigned_to = sorted_owners[0][0]
        else:
            assigned_to = _owner_for(cat)

        task_counter += 1

        # 构造 ticket 列表 (Markdown 表格, agent 易读)
        ticket_lines: List[str] = []
        for t in cat_tickets:
            tid = t["id"]
            ttitle = t["title"][:60].replace("\n", " ")
            towner = t.get("owner") or "unassigned"
            tpri = t["priority"]
            ticket_lines.append(
                f"| #{tid} | {tpri} | {towner} | {ttitle} |"
            )
        ticket_table = "\n".join(ticket_lines) if ticket_lines else "_(无)_"

        # prompt 包含 ticket 清单 + 任务说明
        prompt = (
            f"W{week} A2 自动调度: 从 PRD backlog 拉取 {cat} 类 open P0/P1 ticket "
            f"({len(cat_tickets)} 个), assigned_to={assigned_to}. \n\n"
            f"必读文档:\n"
            f"- docs/plans/plan-auto-w{week}-from-backlog.yaml (本 plan 的源)\n"
            f"- A1 docs/prd/backlog-w8.md (评审反馈原话)\n"
            f"- A2 scripts/backlog_to_plan_tasks.py (转换脚本)\n"
            f"- W9 plan-09-w9-yaml.yaml 范本 (W8 commit 5cdaabe 模式)\n\n"
            f"待办 ticket 清单 (按 P0 优先):\n"
            f"| ID | Priority | Owner | Title |\n"
            f"| --- | --- | --- | --- |\n"
            f"{ticket_table}\n\n"
            f"工作范围:\n"
            f"1. 按 ticket 顺序逐一处理 (P0 先, P1 后)\n"
            f"2. 每完成 1 ticket 更新 prd_backlog.status = 'done' + updated_at\n"
            f"3. blocked > 2 cycle 推进 ticket 标 'deferred' (非 'wontfix', 留 W{week + 1} 重审)\n"
            f"4. 所有 ticket 处理完后, 写 deliverable.md 归档\n\n"
            f"不要做:\n"
            f"- 不要动不在 ticket 清单的 ticket (避免 scope creep)\n"
            f"- 不要改 prd_backlog.priority (本期由 A2 调度, 不重新分级)"
        )

        verify_prompt = (
            f"独立验证 W{week} {cat} backlog 自动调度完成度:\n"
            f"1. 全部 {len(cat_tickets)} ticket 状态变 done / deferred (open = 0)\n"
            f"2. deliverable.md 落档, 含 ticket id + 完成时间 + 阻塞原因 (如有)\n"
            f"3. pytest 100% + ruff 0\n"
            f"4. git log 显示 N+ commit (按 ticket 数)\n\n"
            f"PASS/FAIL 报告."
        )

        task_block = f"""
  # Task auto: {cat} backlog 调度 ({len(cat_tickets)} ticket)
  - id: '{task_id}'
    title: '{task_title}'
    prompt: |
{_indent(prompt, 6)}
    verify_prompt: |
{_indent(verify_prompt, 6)}
    assigned_to: '{assigned_to}'
    role: 'produce'
    verified_by: 'verifier'
    depends_on: []
    gates: []
    max_retries: 2
    timeout_ms: 1800000
    hang_alert_after_ms: 1500000
"""
        task_blocks.append(task_block)

    # 拼装最终 YAML
    yaml = f"""version: 1
plan:
  name: '{plan_name}'
  max_concurrency: {max_concurrency}
  max_consecutive_failures: 2
  max_cycles: {max_cycles}
  auto_accept: true
  auto_reject_retries: 1
  verifier_config:
    default_verifiers: [verifier]
    audit_sample_rate: 0.0
  metadata:
    generated_by: 'scripts/backlog_to_plan_tasks.py'
    generated_at: '{created_iso}'
    source: 'prd_backlog WHERE status=open AND priority IN (P0,P1)'
    ticket_count: {len(tickets)}
    ticket_distribution:
{_yaml_kv_block("      ", {k: len(v) for k, v in grouped.items()})}
tasks:
{''.join(task_blocks)}
"""
    return yaml


def _indent(text: str, spaces: int) -> str:
    """统一缩进, 避免 YAML 解析错"""
    pad = " " * spaces
    return "\n".join(pad + line if line.strip() else line for line in text.splitlines())


def _yaml_kv_block(indent: str, kv: Dict[str, int]) -> str:
    """构造 YAML key: value 块 (每个 key 一行, 值作数字)"""
    return "\n".join(f"{indent}{k}: {v}" for k, v in kv.items())


# ====== 写文件 ======
def write_plan_yaml(out_path: Path, content: str) -> None:
    """写 plan YAML 到文件 (utf-8, 跨平台)
    落档前自动 mkdir -p parents
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")


# ====== 主入口 ======
def main(
    db_path: Path,
    week: int,
    out_path: Path,
    priorities: Tuple[str, ...] = ("P0", "P1"),
    dry_run: bool = False,
) -> int:
    """主流程: 读 → 过滤 → 分组 → 构造 → 写文件

    Returns:
        ticket 数 (写入了多少), 0 = no op
    """
    tickets = read_open_tickets(db_path, priorities=priorities)
    tickets = filter_skip_statuses(tickets)
    grouped = group_by_category(tickets)

    # 打印 dry-run 报告
    print(f"📊 Read {len(tickets)} open tickets (priorities={priorities}) from {db_path}")
    for cat, items in sorted(grouped.items()):
        owners = sorted({t.get("owner") or "unassigned" for t in items})
        priors = sorted({t["priority"] for t in items})
        print(f"  · {cat}: {len(items)} ticket (priority={priors}, owner∈{owners})")

    yaml_text = build_plan_yaml(week=week, tickets=tickets, grouped=grouped)

    if dry_run:
        print("\n[dry-run] 不写文件, 仅打印 YAML:")
        print("-" * 60)
        print(yaml_text)
        print("-" * 60)
        return len(tickets)

    write_plan_yaml(out_path, yaml_text)
    print(f"\n✅ Plan YAML written: {out_path}")
    print(f"   {len(tickets)} tickets → {len(grouped)} plan tasks")
    return len(tickets)


def cli(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert prd_backlog open P0/P1 tickets to mavis team plan YAML (by category)",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="SQLite DB path (default: backend/cases-crawler/data/lexprime.db)",
    )
    parser.add_argument(
        "--week",
        type=int,
        required=True,
        help="Plan 周数, 用于 task id 和文件名 (e.g. 10 → plan-auto-w10-from-backlog.yaml)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="输出 YAML 路径 (相对或绝对)",
    )
    parser.add_argument(
        "--priorities",
        type=str,
        default="P0,P1",
        help="允许的 priority 列表, 逗号分隔 (默认 P0,P1)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印 YAML 到 stdout, 不写文件",
    )
    args = parser.parse_args(argv)

    # 解析 priorities (大写去空格)
    priorities_tuple = tuple(p.strip().upper() for p in args.priorities.split(",") if p.strip())
    if not priorities_tuple:
        print("❌ --priorities 不能为空")
        return 2

    n = main(
        db_path=args.db,
        week=args.week,
        out_path=args.out,
        priorities=priorities_tuple,
        dry_run=args.dry_run,
    )
    return 0 if n >= 0 else 1


if __name__ == "__main__":
    sys.exit(cli())
