"""
W9 A2 自动调度器: 读 prd_backlog open P0/P1 → 转 plan YAML → 干跑 mavis team plan engine
(lex-coder · 2026-06-29)

数据源:
- prd_backlog 表 (W8 A2 backlog_router.py 新增) — open P0/P1 ticket
- 复用 scripts/backlog_to_plan_tasks.py 主转换函数

输出:
- docs/plans/plan-auto-w{N+1}-from-backlog.yaml — 自动生成的 plan YAML
- docs/plans/backlog-auto-schedule-w{N}.md — 本次调度日志 (含 ticket 摘要 + 调度命令)
- (可选) 真启 mavis team plan run → 输出 plan_id + 监控 URL

为什么默认 dry-run:
- W9 A2 plan 接力 lex-pm owner, owner 的 plan 队列需要保护
  - 干跑只生成 YAML + 调度日志, 不污染 owner 队列
- 真启 `--commit` 时: 默认 root 用户 (Mavis 在父 session) 二次确认才允许
  - 本脚本保留入口, 但默认是 dry-run, 防止误调

执行:
  cd backend/cases-crawler
  python scripts/auto_schedule_backlog.py --week 10          # 干跑 + 调度日志
  python scripts/auto_schedule_backlog.py --week 10 --commit # 真启 mavis team plan run
  python scripts/auto_schedule_backlog.py --week 10 --since 24h  # 只看 24h 内新增

W9 plan 接力 (plan_841af3e9 a2-backlog-to-plan-tasks):
- A1 完成 → prd_backlog 42 ticket 入库 (commit 5437535)
- A2 backlog_to_plan_tasks.py → 转换脚本
- A2 auto_schedule_backlog.py → 干跑调度器 (本脚本)
- 验证: pytest + ruff, 详见 tests/test_auto_schedule_backlog.py
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 项目根路径 (跟 migrate_review_to_backlog.py / backlog_to_plan_tasks.py 一致)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# yuanxing 仓库根 (lex_coder_project 上一级, 即 yuanxing/)
REPO_ROOT = PROJECT_ROOT.parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 复用 backlog_to_plan_tasks 的核心函数 (E402: 函数顶部 import 因 sys.path insert 必须放后面)
from scripts.backlog_to_plan_tasks import (  # noqa: E402
    DEFAULT_DB_PATH,
    group_by_category,
    read_open_tickets,
    filter_skip_statuses,
    build_plan_yaml,
    write_plan_yaml,
)


# ====== 路径常量 ======
# 默认 plan YAML 落档目录 (跟 W8/W9 yaml 一致, yuanxing/docs/plans/)
DEFAULT_PLANS_DIR = REPO_ROOT / "docs" / "plans"


# 计划 YAML 落地路径 (W{N+1} 自动派生)
def plan_yaml_path(week: int, base_dir: Path) -> Path:
    """自动生成 plan YAML 路径 (W{N+1}-from-backlog)"""
    return base_dir / f"plan-auto-w{week + 1}-from-backlog.yaml"


# 调度日志落地路径 (W{N})
def schedule_log_path(week: int, base_dir: Path) -> Path:
    return base_dir / f"backlog-auto-schedule-w{week}.md"


# ====== 时间过滤 (cron 增量调度) ======
def filter_tickets_since(
    tickets: List[Dict[str, Any]],
    since_hours: int,
    now: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """只保留 created_at 在 since_hours 内的 ticket

    Notes:
        - SQLite 读回的 datetime 是 naive (无 tz), 这里统一当 UTC 处理
        - 用于 cron 增量调度: 每天 09:00 跑, 只看过去 24h 新增
    """
    if since_hours <= 0:
        return tickets

    if now is None:
        now = datetime.now(timezone.utc)

    # 容忍 now 也可能是 naive (测试 mock)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    cutoff = now - timedelta(hours=since_hours)
    kept: List[Dict[str, Any]] = []
    for t in tickets:
        created_raw = t.get("created_at")
        if not created_raw:
            # created_at 为空 → 保留 (兜底, 可能是历史数据)
            kept.append(t)
            continue
        # 解析 created_at 字符串 (SQLite 默认 'YYYY-MM-DD HH:MM:SS')
        try:
            created_str = str(created_raw).replace("T", " ").replace("Z", "")
            created_dt = datetime.fromisoformat(created_str)
        except (ValueError, TypeError):
            # 解析失败 → 保留 (兜底)
            kept.append(t)
            continue
        # 缺 tzinfo 当 UTC 处理
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc)
        if created_dt >= cutoff:
            kept.append(t)
    return kept


# ====== Mavis team plan run 封装 ======
def invoke_mavis_plan(
    plan_yaml: Path,
    dry_run: bool = True,
    session: Optional[str] = None,
    no_wait: bool = True,
) -> Dict[str, Any]:
    """调用 mavis team plan run 命令 (subprocess)

    Args:
        plan_yaml: plan YAML 文件路径
        dry_run: True → 拼出命令描述但不执行, False → subprocess.run 真启
        session: --from session id (默认 None → 让 mavis 取默认)
        no_wait: --no-wait 标志, True → 不等 plan 启动完成

    Returns:
        dict: 含 cmd (命令字符串) / returncode / stdout / stderr / dry_run / invoked_at / mavis_in_path / unavailable_reason
    """
    # 检查 mavis 是否在 PATH
    mavis_in_path = shutil.which("mavis") is not None
    if not mavis_in_path and not dry_run:
        # 真启模式: mavis 必须可用
        raise RuntimeError(
            "mavis CLI 不在 PATH (cannot find `mavis` binary). "
            "请确认 mavis 是否安装, 或在 PATH 加入 mavis 二进制所在路径.",
        )

    # 拼 cmd 数组 (mavis team plan run [options] <yaml>)
    cmd: List[str] = ["mavis", "team", "plan", "run"]
    if session:
        cmd.append(f"--from={session}")
    if no_wait:
        cmd.append("--no-wait")
    cmd.append(str(plan_yaml))

    cmd_str = " ".join(cmd)
    invoked_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # dry-run 模式: 拼 cmd 不执行
    if dry_run:
        unavailable_reason: Optional[str] = None
        if not mavis_in_path:
            unavailable_reason = (
                "mavis CLI not in PATH (dry-run only) — "
                "生成 plan YAML 成功, 真启需安装 mavis"
            )
        return {
            "cmd": cmd_str,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "dry_run": True,
            "invoked_at": invoked_at,
            "mavis_in_path": mavis_in_path,
            "unavailable_reason": unavailable_reason,
        }

    # 真启 (默认 timeout 60s, plan 启动是阻塞式)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        return {
            "cmd": cmd_str,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "dry_run": False,
            "invoked_at": invoked_at,
            "mavis_in_path": mavis_in_path,
            "unavailable_reason": None,
        }
    except subprocess.TimeoutExpired as e:
        return {
            "cmd": cmd_str,
            "returncode": -1,
            "stdout": (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or ""),
            "stderr": (e.stderr or b"").decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or ""),
            "dry_run": False,
            "invoked_at": invoked_at,
            "timeout": True,
        }


# ====== 调度日志 ======
def build_schedule_log_markdown(
    week: int,
    tickets: List[Dict[str, Any]],
    grouped: Dict[str, List[Dict[str, Any]]],
    plan_yaml_path: Path,
    plan_yaml_content: str,
    invocation_result: Dict[str, Any],
    priorities: Tuple[str, ...],
    since_hours: Optional[int] = None,
    now: Optional[datetime] = None,
) -> str:
    """构造 W{N} backlog auto-schedule 调度日志 Markdown

    Sections:
        - Status (dry-run / committed)
        - Source (DB path + filter)
        - Ticket distribution (by category × priority)
        - Generated plan YAML (path + 概要)
        - Schedule invocation (cmd + return)
        - Next steps
    """
    if now is None:
        now = datetime.now(timezone.utc)
    now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    status = "DRY-RUN (no mavis plan queued)" if invocation_result.get("dry_run") else "COMMITTED"

    # 票数总览
    by_priority: Dict[str, int] = {}
    for t in tickets:
        by_priority[t["priority"]] = by_priority.get(t["priority"], 0) + 1

    # 按 category 表格
    cat_lines = [
        "| Category | Count | Owner 集合 | Priority 分布 |",
        "| --- | ---: | --- | --- |",
    ]
    for cat in ("产品", "技术", "法务", "其他"):
        items = grouped.get(cat, [])
        if not items:
            continue
        owners = sorted({t.get("owner") or "unassigned" for t in items})
        pri_dist: Dict[str, int] = {}
        for t in items:
            pri_dist[t["priority"]] = pri_dist.get(t["priority"], 0) + 1
        pri_str = ", ".join(f"{p}={c}" for p, c in sorted(pri_dist.items()))
        cat_lines.append(f"| {cat} | {len(items)} | {', '.join(owners)} | {pri_str} |")
    cat_table = "\n".join(cat_lines)

    # 完整 ticket 列表
    ticket_lines = [
        "| ID | Category | Priority | Owner | Title |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for t in tickets:
        tid = t["id"]
        ttitle = (t["title"] or "")[:60].replace("\n", " ").replace("|", "\\|")
        towner = t.get("owner") or "unassigned"
        ticket_lines.append(
            f"| {tid} | {t['category']} | {t['priority']} | {towner} | {ttitle} |"
        )
    ticket_table = "\n".join(ticket_lines)

    # Plan YAML 摘录 (前 30 行, 避免 markdown 过长)
    yaml_preview_lines = plan_yaml_content.splitlines()[:30]
    yaml_preview = "\n".join(yaml_preview_lines) + "\n...(truncated, full plan YAML 见 " + plan_yaml_path.name + ")"

    cmd = invocation_result.get("cmd", "")
    returncode = invocation_result.get("returncode")
    stdout = invocation_result.get("stdout", "")
    stderr = invocation_result.get("stderr", "")
    timeout_happened = invocation_result.get("timeout", False)

    md = f"""# Backlog Auto-Schedule W{week} ({status})

> 自动生成于 {now_iso}, 来自 PRD backlog open {'+'.join(priorities)} ticket → mavis team plan YAML

## 状态

- **Status**: {status}
- **调度命令**: `mavis team plan run --no-wait {plan_yaml_path}`
- **Plan YAML**: [{plan_yaml_path.name}](./{plan_yaml_path.name}) (full path: `{plan_yaml_path}`)
- **触发**: scripts/auto_schedule_backlog.py (W9 A2)

## 数据源

- **Database**: `prd_backlog` (SQLite)
- **过滤条件**: `status='open' AND priority IN {priorities} {('AND created_at >= NOW() - ' + str(since_hours) + 'h') if since_hours else ''}`
- **Ticket 总数**: {len(tickets)}

## Ticket 分布 (按 category)

{cat_table}

## Ticket 明细 (按 priority, P0 → P3, ID 升序)

{ticket_table}

## 生成的 Plan YAML 概要

```yaml
{yaml_preview}
```

## Schedule Invocation

```bash
{cmd}
```

### 执行结果

- **returncode**: `{returncode}` {'(timeout)' if timeout_happened else ''}
- **stdout**:
```
{stdout or '_(dry-run, no output)_'}
```
- **stderr**:
```
{stderr or '_(none)_'}
```

## 下一步

1. W{week} A2 deliverable: 转 plan YAML + 调度日志 ✓
2. Owner (Mavis/lex-pm) 验收: 启动 `mavis team plan run {plan_yaml_path}` 真启 plan (本期 A2 默认 dry-run, 不污染 owner 队列)
3. 真实运行后: worker agent 按 task 处理 ticket, 完成后写 deliverable.md
4. cron 集成: `scripts/cron/auto-schedule-backlog.sh` 每日 09:00 跑, 增量调度 (since 24h)

---
*本日志由 scripts/auto_schedule_backlog.py 自动生成 · W9 A2 自动调度*
"""
    return md


def write_schedule_log(log_path: Path, content: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(content, encoding="utf-8")


# ====== 主流程 ======
def run_schedule(
    db_path: Path,
    week: int,
    plans_dir: Path,
    priorities: Tuple[str, ...] = ("P0", "P1"),
    since_hours: Optional[int] = None,
    commit: bool = False,
    session: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """主流程: 读 ticket → 过滤 → 分组 → 生成 plan YAML → 调用 mavis (干跑/真启) → 写调度日志

    Returns:
        dict 含 ticket_count / plan_yaml_path / log_path / invocation_result / tickets / grouped
    """
    if now is None:
        now = datetime.now(timezone.utc)

    # 1. 读 ticket
    tickets = read_open_tickets(db_path, priorities=priorities)
    tickets = filter_skip_statuses(tickets)

    # 2. 时间过滤 (cron 增量)
    if since_hours is not None:
        tickets = filter_tickets_since(tickets, since_hours=since_hours, now=now)

    # 3. 分组
    grouped = group_by_category(tickets)

    # 4. 构造 plan YAML (写 W{week+1})
    plan_yaml = plan_yaml_path(week, plans_dir)
    yaml_text = build_plan_yaml(week=week + 1, tickets=tickets, grouped=grouped, now=now)
    write_plan_yaml(plan_yaml, yaml_text)

    # 5. 调用 mavis (默认 dry-run)
    invocation = invoke_mavis_plan(
        plan_yaml=plan_yaml,
        dry_run=not commit,
        session=session,
        no_wait=True,
    )

    # 6. 调度日志 (W{week}, 跟 plan 错一周便于区分)
    log_path = schedule_log_path(week, plans_dir)
    log_text = build_schedule_log_markdown(
        week=week,
        tickets=tickets,
        grouped=grouped,
        plan_yaml_path=plan_yaml,
        plan_yaml_content=yaml_text,
        invocation_result=invocation,
        priorities=priorities,
        since_hours=since_hours,
        now=now,
    )
    write_schedule_log(log_path, log_text)

    return {
        "ticket_count": len(tickets),
        "plan_yaml_path": plan_yaml,
        "log_path": log_path,
        "invocation_result": invocation,
        "tickets": tickets,
        "grouped": grouped,
    }


# ====== CLI ======
def cli(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Auto-schedule prd_backlog open P0/P1 ticket → mavis team plan YAML + dry-run invoke. "
            "默认 dry-run, 不真启 plan engine."
        ),
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="SQLite DB path (默认: backend/cases-crawler/data/lexprime.db)",
    )
    parser.add_argument(
        "--week",
        type=int,
        required=True,
        help="Plan 周数 (当前 W), 用于调度日志命名",
    )
    parser.add_argument(
        "--plans-dir",
        type=Path,
        default=DEFAULT_PLANS_DIR,
        help="plan YAML + 调度日志 落档目录 (默认 yuanxing/docs/plans)",
    )
    parser.add_argument(
        "--priorities",
        type=str,
        default="P0,P1",
        help="允许的 priority 列表, 逗号分隔 (默认 P0,P1)",
    )
    parser.add_argument(
        "--since",
        type=int,
        default=None,
        help="只看 N 小时前到现在新增的 ticket (cron 增量用, 默认全量)",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="真启 mavis team plan run (默认 dry-run, 不污染 owner 队列)",
    )
    parser.add_argument(
        "--from",
        dest="session",
        type=str,
        default=None,
        help="mavis --from session id (owner 监控用)",
    )
    args = parser.parse_args(argv)

    priorities_tuple = tuple(p.strip().upper() for p in args.priorities.split(",") if p.strip())
    if not priorities_tuple:
        print("❌ --priorities 不能为空")
        return 2

    result = run_schedule(
        db_path=args.db,
        week=args.week,
        plans_dir=args.plans_dir,
        priorities=priorities_tuple,
        since_hours=args.since,
        commit=args.commit,
        session=args.session,
    )

    inv = result["invocation_result"]
    status = "COMMITTED" if not inv.get("dry_run") else "DRY-RUN"
    print(f"✅ Auto-schedule W{args.week} {status}")
    print(f"   {result['ticket_count']} tickets scheduled")
    print(f"   plan YAML: {result['plan_yaml_path']}")
    print(f"   log:       {result['log_path']}")
    print(f"   cmd:       {inv['cmd']}")
    if inv.get("returncode") is not None:
        print(f"   return:    {inv['returncode']}")

    return 0


if __name__ == "__main__":
    sys.exit(cli())
