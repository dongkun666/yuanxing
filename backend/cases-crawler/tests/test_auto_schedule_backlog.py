"""
W9 A2 auto-schedule 调度器测试
(lex-coder · 2026-06-29)

覆盖:
- filter_tickets_since: 时间窗口过滤 (cron 增量)
- invoke_mavis_plan: dry-run 模式不真启 + cmd 拼装顺序
- build_schedule_log_markdown: 日志 必要 section
- run_schedule: 集成 (read → filter → group → yaml → invocation → log)

策略:
- in-memory SQLite + tmp_path, 不依赖真实 DB / plan engine
- 默认 dry_run=True (避免污染 owner plan 队列 + 不依赖 mavis in PATH)
"""
from __future__ import annotations

import shutil
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.auto_schedule_backlog import (  # noqa: E402
    build_schedule_log_markdown,
    cli,
    filter_tickets_since,
    invoke_mavis_plan,
    plan_yaml_path,
    run_schedule,
    schedule_log_path,
    write_schedule_log,
)


# ====== Fixtures ======
@pytest.fixture
def in_mem_db(tmp_path: Path) -> Path:
    """临时 SQLite + prd_backlog 表"""
    db_path = tmp_path / "test_auto_schedule.db"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """
            CREATE TABLE prd_backlog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_question_id INTEGER,
                source_lawyer_id VARCHAR(16),
                title VARCHAR(120) NOT NULL,
                description TEXT NOT NULL,
                category VARCHAR(16) NOT NULL,
                priority VARCHAR(4) NOT NULL,
                owner VARCHAR(16) NOT NULL DEFAULT 'unassigned',
                status VARCHAR(16) NOT NULL DEFAULT 'open',
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


def _seed_tickets(
    db_path: Path,
    tickets: list[dict],
) -> None:
    """seed 多条 ticket. dict keys: category / priority / status / title / owner / created_at (ISO str)"""
    conn = sqlite3.connect(str(db_path))
    try:
        for t in tickets:
            conn.execute(
                """
                INSERT INTO prd_backlog
                (title, description, category, priority, owner, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    t.get("title", "t"),
                    t.get("description", "d"),
                    t["category"],
                    t["priority"],
                    t.get("owner", "lex-coder"),
                    t.get("status", "open"),
                    t.get("created_at", "2026-06-29 12:00:00"),
                    t.get("created_at", "2026-06-29 12:00:00"),
                ),
            )
        conn.commit()
    finally:
        conn.close()


def _sample_tickets() -> list[dict]:
    return [
        {
            "category": "产品", "priority": "P0", "owner": "lex-coder",
            "title": "UI 团队协同", "description": "测试",
            "created_at": "2026-06-29 12:00:00",
        },
        {
            "category": "技术", "priority": "P1", "owner": "lex-ai",
            "title": "OCR 引擎", "description": "测试",
            "created_at": "2026-06-29 12:00:00",
        },
        {
            "category": "法务", "priority": "P0", "owner": "lex-coder",
            "title": "司法解释", "description": "测试",
            "created_at": "2026-06-29 12:00:00",
        },
    ]


# ====== filter_tickets_since ======
class TestFilterTicketsSince:
    def test_zero_means_keep_all(self) -> None:
        """since_hours<=0 → 全部保留"""
        tickets = [{"id": 1, "created_at": "2020-01-01 12:00:00"}]
        kept = filter_tickets_since(tickets, since_hours=0)
        assert len(kept) == 1

    def test_filters_old(self) -> None:
        """since_hours=24 → 24h 前的过滤掉"""
        now = datetime(2026, 6, 29, 12, 0, 0, tzinfo=timezone.utc)
        old = (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
        fresh = (now - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
        tickets = [
            {"id": 1, "created_at": old},
            {"id": 2, "created_at": fresh},
        ]
        kept = filter_tickets_since(tickets, since_hours=24, now=now)
        assert {t["id"] for t in kept} == {2}

    def test_keeps_future_dates(self) -> None:
        """now 之后的也保留 (含 now)"""
        now = datetime(2026, 6, 29, 12, 0, 0, tzinfo=timezone.utc)
        future = (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        tickets = [{"id": 1, "created_at": future}]
        kept = filter_tickets_since(tickets, since_hours=24, now=now)
        assert {t["id"] for t in kept} == {1}

    def test_empty_created_at_kept(self) -> None:
        """created_at 为空 → 保留 (兜底)"""
        tickets = [{"id": 1, "created_at": ""}]
        kept = filter_tickets_since(tickets, since_hours=24)
        assert len(kept) == 1

    def test_naive_datetime_treated_as_utc(self) -> None:
        """没 tzinfo → 当 UTC 处理"""
        # 24h 前 (无 tz) 应该被过滤
        now = datetime(2026, 6, 29, 12, 0, 0, tzinfo=timezone.utc)
        old_str = "2026-06-28 12:00:00"  # 24h 前
        tickets = [{"id": 1, "created_at": old_str}]
        kept = filter_tickets_since(tickets, since_hours=23, now=now)
        assert kept == []


# ====== invoke_mavis_plan ======
class TestInvokeMavisPlan:
    def test_dry_run_does_not_execute(self, tmp_path: Path) -> None:
        """dry_run=True → 不真启, 即使 mavis 不在 PATH"""
        plan_yaml = tmp_path / "plan.yaml"
        plan_yaml.write_text("version: 1\n", encoding="utf-8")
        result = invoke_mavis_plan(plan_yaml, dry_run=True)
        assert result["dry_run"] is True
        assert result["returncode"] is None
        assert "mavis team plan run" in result["cmd"]

    def test_cmd_order_options_before_yaml(self, tmp_path: Path) -> None:
        """--no-wait 必须在 <yaml> 之前, 不是 'mavis team --no-wait ...'"""
        plan_yaml = tmp_path / "plan.yaml"
        plan_yaml.write_text("x", encoding="utf-8")
        result = invoke_mavis_plan(plan_yaml, dry_run=True, no_wait=True)
        cmd = result["cmd"]
        # 期望: mavis team plan run --no-wait <yaml>, 不是 mavis team --no-wait plan run <yaml>
        assert "mavis team plan run --no-wait" in cmd
        assert cmd.endswith(".yaml")
        assert "mavis team --no-wait" not in cmd

    def test_cmd_with_session(self, tmp_path: Path) -> None:
        """--from=session 拼到 cmd"""
        plan_yaml = tmp_path / "plan.yaml"
        result = invoke_mavis_plan(plan_yaml, dry_run=True, session="abc123")
        assert "--from=abc123" in result["cmd"]

    def test_no_wait_false(self, tmp_path: Path) -> None:
        """no_wait=False → cmd 不含 --no-wait"""
        plan_yaml = tmp_path / "plan.yaml"
        result = invoke_mavis_plan(plan_yaml, dry_run=True, no_wait=False)
        assert "--no-wait" not in result["cmd"]

    def test_dry_run_unavailable_mavis(self, tmp_path: Path, monkeypatch) -> None:
        """mavis 不在 PATH 但 dry_run=True → 仍允许 (不 raise)"""
        # Mock shutil.which 让它说找不到 mavis
        monkeypatch.setattr(shutil, "which", lambda x: None)
        plan_yaml = tmp_path / "plan.yaml"
        plan_yaml.write_text("x", encoding="utf-8")
        result = invoke_mavis_plan(plan_yaml, dry_run=True)
        assert result["dry_run"] is True
        assert result["mavis_in_path"] is False
        assert result["unavailable_reason"] is not None
        assert "mavis" in result["unavailable_reason"]


# ====== build_schedule_log_markdown ======
class TestBuildScheduleLogMarkdown:
    @pytest.fixture
    def sample_invocation(self) -> dict:
        return {
            "cmd": "mavis team plan run --no-wait /tmp/plan.yaml",
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "dry_run": True,
            "invoked_at": "2026-06-29T13:00:00Z",
            "mavis_in_path": False,
            "unavailable_reason": "mavis not in PATH",
        }

    def test_log_contains_status(
        self, tmp_path: Path, sample_invocation: dict
    ) -> None:
        tickets = [
            {
                "id": 1, "category": "产品", "priority": "P0",
                "owner": "lex-coder", "title": "UI 团队协同",
                "status": "open",
                "source_question_id": None, "source_lawyer_id": None,
                "description": "test",
                "created_at": "2026-06-29", "updated_at": "2026-06-29",
            },
        ]
        grouped = {"产品": tickets}
        plan_yaml = tmp_path / "plan.yaml"
        plan_yaml.write_text("version: 1\n", encoding="utf-8")

        log = build_schedule_log_markdown(
            week=9,
            tickets=tickets,
            grouped=grouped,
            plan_yaml_path=plan_yaml,
            plan_yaml_content="version: 1\n",
            invocation_result=sample_invocation,
            priorities=("P0", "P1"),
        )
        assert "# Backlog Auto-Schedule W9" in log
        assert "DRY-RUN" in log
        assert "1" in log  # ticket count
        assert "UI 团队协同" in log  # ticket title

    def test_log_contains_command(
        self, tmp_path: Path, sample_invocation: dict
    ) -> None:
        tickets: list[dict] = []
        log = build_schedule_log_markdown(
            week=9, tickets=tickets, grouped={},
            plan_yaml_path=tmp_path / "plan.yaml",
            plan_yaml_content="x",
            invocation_result=sample_invocation,
            priorities=("P0",),
        )
        assert "mavis team plan run --no-wait" in log

    def test_log_with_since_hours(
        self, tmp_path: Path, sample_invocation: dict
    ) -> None:
        """since_hours 信息出现在日志"""
        log = build_schedule_log_markdown(
            week=9, tickets=[], grouped={},
            plan_yaml_path=tmp_path / "plan.yaml",
            plan_yaml_content="x",
            invocation_result=sample_invocation,
            priorities=("P0",),
            since_hours=24,
        )
        # 过滤条件包含 since_hours
        assert "24" in log


# ====== write_schedule_log ======
class TestWriteScheduleLog:
    def test_writes_utf8(self, tmp_path: Path) -> None:
        path = tmp_path / "log.md"
        write_schedule_log(path, "中文\n")
        content = path.read_text(encoding="utf-8")
        assert content == "中文\n"

    def test_creates_parents(self, tmp_path: Path) -> None:
        path = tmp_path / "deep" / "log.md"
        write_schedule_log(path, "x")
        assert path.exists()


# ====== path helpers ======
class TestPathHelpers:
    def test_plan_yaml_path_week10(self, tmp_path: Path) -> None:
        assert plan_yaml_path(week=9, base_dir=tmp_path).name == "plan-auto-w10-from-backlog.yaml"

    def test_schedule_log_path_week9(self, tmp_path: Path) -> None:
        assert schedule_log_path(week=9, base_dir=tmp_path).name == "backlog-auto-schedule-w9.md"


# ====== run_schedule 集成 ======
class TestRunSchedule:
    def test_dry_run_writes_yaml_and_log(
        self, in_mem_db: Path, tmp_path: Path
    ) -> None:
        """主流程: dry-run 模式写 plan YAML + 调度日志, 不真启 mavis"""
        _seed_tickets(in_mem_db, _sample_tickets())

        plans_dir = tmp_path / "plans"
        result = run_schedule(
            db_path=in_mem_db,
            week=9,
            plans_dir=plans_dir,
            priorities=("P0", "P1"),
            commit=False,  # dry-run
        )

        assert result["ticket_count"] == 3
        assert result["plan_yaml_path"] == plans_dir / "plan-auto-w10-from-backlog.yaml"
        assert result["log_path"] == plans_dir / "backlog-auto-schedule-w9.md"
        assert result["plan_yaml_path"].exists()
        assert result["log_path"].exists()

        # invocation 是 dry-run
        assert result["invocation_result"]["dry_run"] is True

    def test_filters_skip_statuses(
        self, in_mem_db: Path, tmp_path: Path
    ) -> None:
        """in_progress / done 状态被过滤"""
        _seed_tickets(in_mem_db, [
            {"category": "产品", "priority": "P0", "status": "open",
             "title": "open", "created_at": "2026-06-29 12:00:00"},
            {"category": "产品", "priority": "P0", "status": "in_progress",
             "title": "in_progress", "created_at": "2026-06-29 12:00:00"},
            {"category": "产品", "priority": "P0", "status": "done",
             "title": "done", "created_at": "2026-06-29 12:00:00"},
            {"category": "产品", "priority": "P0", "status": "wontfix",
             "title": "wontfix", "created_at": "2026-06-29 12:00:00"},
        ])

        result = run_schedule(
            db_path=in_mem_db,
            week=9,
            plans_dir=tmp_path / "plans",
            priorities=("P0",),
            commit=False,
        )
        assert result["ticket_count"] == 1  # 只有 open

    def test_with_since_hours_incremental(
        self, in_mem_db: Path, tmp_path: Path
    ) -> None:
        """--since=N 增量过滤"""
        # created_at 设到不同时间
        now = datetime.now(timezone.utc)
        old = (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
        fresh = (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        _seed_tickets(in_mem_db, [
            {"category": "产品", "priority": "P0", "title": "old",
             "created_at": old},
            {"category": "产品", "priority": "P0", "title": "fresh",
             "created_at": fresh},
        ])

        result = run_schedule(
            db_path=in_mem_db,
            week=9,
            plans_dir=tmp_path / "plans",
            priorities=("P0",),
            since_hours=24,
            commit=False,
        )
        # 只有 fresh
        assert result["ticket_count"] == 1
        assert result["tickets"][0]["title"] == "fresh"

    def test_zero_tickets_writes_empty_plan(
        self, in_mem_db: Path, tmp_path: Path
    ) -> None:
        """无 ticket 时仍写 plan YAML (空 plan)"""
        result = run_schedule(
            db_path=in_mem_db,
            week=9,
            plans_dir=tmp_path / "plans",
            priorities=("P0",),
            commit=False,
        )
        assert result["ticket_count"] == 0
        assert result["plan_yaml_path"].exists()
        yaml_content = result["plan_yaml_path"].read_text(encoding="utf-8")
        assert "ticket_count: 0" in yaml_content


# ====== cli ======
class TestCLI:
    def test_cli_dry_run(self, in_mem_db: Path, tmp_path: Path, monkeypatch) -> None:
        """cli 默认 dry-run (用 monkeypatch sys.argv)"""
        _seed_tickets(in_mem_db, _sample_tickets())
        plans_dir = tmp_path / "plans"
        monkeypatch.setattr(sys, "argv", [
            "auto_schedule_backlog.py",
            "--db", str(in_mem_db),
            "--week", "9",
            "--plans-dir", str(plans_dir),
            "--priorities", "P0,P1",
            # 不传 --commit → dry-run
        ])
        rc = cli()
        assert rc == 0
        assert (plans_dir / "plan-auto-w10-from-backlog.yaml").exists()
        assert (plans_dir / "backlog-auto-schedule-w9.md").exists()

    def test_cli_invalid_priorities(
        self, in_mem_db: Path, tmp_path: Path, monkeypatch
    ) -> None:
        """空 --priorities → rc=2"""
        monkeypatch.setattr(sys, "argv", [
            "auto_schedule_backlog.py",
            "--db", str(in_mem_db),
            "--week", "9",
            "--plans-dir", str(tmp_path / "plans"),
            "--priorities", "",
        ])
        rc = cli()
        assert rc == 2
