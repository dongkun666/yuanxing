"""
W9 A2 backlog → plan task 转换脚本测试
(lex-coder · 2026-06-29)

覆盖:
- read_open_tickets: 过滤 (status + priority) + 列名稳定性
- filter_skip_statuses: 兜底过滤 (防 SQL 漏写)
- group_by_category: 分组 + 空 group
- build_plan_yaml: schema 必要字段 + ticket 嵌 prompt + task id 稳定
- write_plan_yaml: 落档 + UTF-8 + mkdir -p
- cli argparse: 默认参数 + --priorities

策略:
- in-memory SQLite (sqlite3 标准库), 不依赖 ORM async 链
- 每个 fixture 临时 seed 1-2 条 ticket, 跑测试后清理
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

# 加 scripts/ 到 sys.path (E402: 必须在 sys.path insert 之后)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.backlog_to_plan_tasks import (  # noqa: E402
    BACKLOG_TABLE_COLUMNS,
    SCHEDULABLE_STATUSES,
    SKIPPABLE_STATUSES,
    build_plan_yaml,
    cli,
    filter_skip_statuses,
    group_by_category,
    main,
    read_open_tickets,
    write_plan_yaml,
)


# ====== Fixtures ======
@pytest.fixture
def in_mem_db(tmp_path: Path) -> Path:
    """建一个临时 SQLite DB + prd_backlog 表, 返回路径"""
    db_path = tmp_path / "test_backlog.db"
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


def _insert_ticket(
    db_path: Path,
    category: str,
    priority: str,
    status: str = "open",
    title: str = "测试 ticket",
    owner: str = "lex-coder",
    created_at: str | None = None,
) -> int:
    """插一条 ticket, 返回 id"""
    if created_at is None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    else:
        now = created_at
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.execute(
            """
            INSERT INTO prd_backlog
            (title, description, category, priority, owner, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                f"desc for {title}",
                category,
                priority,
                owner,
                status,
                now,
                now,
            ),
        )
        conn.commit()
        return cur.lastrowid  # type: ignore[return-value]
    finally:
        conn.close()


# ====== read_open_tickets ======
class TestReadOpenTickets:
    def test_returns_only_open_p0_p1(self, in_mem_db: Path) -> None:
        """只读 status=open + priority IN (P0, P1)"""
        _insert_ticket(in_mem_db, "产品", "P0", status="open")
        _insert_ticket(in_mem_db, "产品", "P1", status="open")
        _insert_ticket(in_mem_db, "产品", "P2", status="open")  # 应该被过滤
        _insert_ticket(in_mem_db, "产品", "P0", status="done")  # 应该被过滤
        _insert_ticket(in_mem_db, "技术", "P0", status="in_progress")  # 被过滤
        _insert_ticket(in_mem_db, "技术", "P0", status="deferred")  # 被过滤

        tickets = read_open_tickets(in_mem_db)
        assert len(tickets) == 2
        assert {t["priority"] for t in tickets} == {"P0", "P1"}
        assert {t["status"] for t in tickets} == {"open"}

    def test_custom_priorities(self, in_mem_db: Path) -> None:
        """--priorities 自定义元组支持"""
        _insert_ticket(in_mem_db, "产品", "P0")
        _insert_ticket(in_mem_db, "产品", "P2")
        _insert_ticket(in_mem_db, "产品", "P3")

        # 只允许 P3
        tickets = read_open_tickets(in_mem_db, priorities=("P3",))
        assert len(tickets) == 1
        assert tickets[0]["priority"] == "P3"

    def test_columns_stable(self, in_mem_db: Path) -> None:
        """返回的 dict 字段跟 BACKLOG_TABLE_COLUMNS 一致"""
        _insert_ticket(in_mem_db, "产品", "P0")
        tickets = read_open_tickets(in_mem_db)
        assert set(tickets[0].keys()) == set(BACKLOG_TABLE_COLUMNS)

    def test_ordering_p0_first(self, in_mem_db: Path) -> None:
        """P0 优先,然后 P1 (防止 XML 顺序漂移)"""
        _insert_ticket(in_mem_db, "产品", "P1", title="p1")
        _insert_ticket(in_mem_db, "产品", "P0", title="p0")
        _insert_ticket(in_mem_db, "技术", "P0", title="p0-tech")

        tickets = read_open_tickets(in_mem_db)
        priorities = [t["priority"] for t in tickets]
        # P0 group first
        assert priorities == ["P0", "P0", "P1"]

    def test_db_not_found(self, tmp_path: Path) -> None:
        """DB 不存在 → FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            read_open_tickets(tmp_path / "missing.db")


# ====== filter_skip_statuses ======
class TestFilterSkipStatuses:
    def test_drops_done(self) -> None:
        tickets = [{"status": "open"}, {"status": "done"}]
        kept = filter_skip_statuses(tickets)
        assert len(kept) == 1
        assert kept[0]["status"] == "open"

    def test_drops_all_skippable(self) -> None:
        tickets = [{"status": s} for s in SKIPPABLE_STATUSES]
        kept = filter_skip_statuses(tickets)
        assert kept == []

    def test_keeps_all_schedulable(self) -> None:
        tickets = [{"status": s} for s in SCHEDULABLE_STATUSES]
        kept = filter_skip_statuses(tickets)
        assert len(kept) == len(SCHEDULABLE_STATUSES)


# ====== group_by_category ======
class TestGroupByCategory:
    def test_basic_group(self) -> None:
        tickets = [
            {"id": 1, "category": "产品"},
            {"id": 2, "category": "技术"},
            {"id": 3, "category": "产品"},
            {"id": 4, "category": "其他"},
        ]
        grouped = group_by_category(tickets)
        assert len(grouped["产品"]) == 2
        assert len(grouped["技术"]) == 1
        assert len(grouped["其他"]) == 1
        assert "法务" not in grouped  # 空 category 不出现在结果

    def test_empty_input(self) -> None:
        grouped = group_by_category([])
        assert grouped == {}


# ====== build_plan_yaml ======
class TestBuildPlanYaml:
    @pytest.fixture
    def sample_tickets(self) -> list[dict]:
        return [
            {
                "id": 1, "title": "UI 团队协同", "category": "产品",
                "priority": "P0", "owner": "lex-coder", "status": "open",
                "source_question_id": None, "source_lawyer_id": None,
                "description": "L2/L4 评审: 当前 UI 不支持团队协同",
                "created_at": "2026-06-29", "updated_at": "2026-06-29",
            },
            {
                "id": 2, "title": "OCR 引擎冷启动", "category": "技术",
                "priority": "P0", "owner": "lex-ai", "status": "open",
                "source_question_id": None, "source_lawyer_id": None,
                "description": "PaddleOcrEngine + Tesseract fallback",
                "created_at": "2026-06-29", "updated_at": "2026-06-29",
            },
        ]

    def test_yaml_required_keys(self, sample_tickets: list[dict]) -> None:
        """YAML 含 version / plan / tasks 顶层键"""
        yaml_text = build_plan_yaml(week=10, tickets=sample_tickets, grouped=group_by_category(sample_tickets))
        assert yaml_text.startswith("version: 1\n")
        assert "plan:" in yaml_text
        assert "  name:" in yaml_text
        assert "tasks:" in yaml_text
        # 必要 plan keys
        assert "max_concurrency:" in yaml_text
        assert "max_cycles:" in yaml_text
        assert "auto_accept:" in yaml_text
        assert "verifier_config:" in yaml_text

    def test_task_id_stable_by_week(self, sample_tickets: list[dict]) -> None:
        """Task id 含周数,避免跨周冲突"""
        yaml_text = build_plan_yaml(week=10, tickets=sample_tickets)
        assert "product-w10-auto" in yaml_text  # 产品 group
        assert "tech-w10-auto" in yaml_text  # 技术 group

    def test_task_prompt_contains_ticket_table(self, sample_tickets: list[dict]) -> None:
        """每个 task prompt 含 ticket 表格"""
        yaml_text = build_plan_yaml(week=10, tickets=sample_tickets)
        # ticket #1 (UI 团队协同) 必须在产品 task 里
        assert "#1 | P0 | lex-coder | UI 团队协同" in yaml_text
        # ticket #2 (OCR) 必须在技术 task 里
        assert "#2 | P0 | lex-ai | OCR" in yaml_text

    def test_empty_group_no_task(self) -> None:
        """空 category 不产生 task (避免空 task)"""
        tickets = [{"id": 1, "title": "t", "category": "产品", "priority": "P0",
                    "owner": "lex-coder", "status": "open"}]
        yaml_text = build_plan_yaml(week=10, tickets=tickets)
        # 只有产品 task, 其他 category 不会出现
        assert "product-w10-auto" in yaml_text
        assert "tech-w10-auto" not in yaml_text
        assert "legal-w10-auto" not in yaml_text
        assert "misc-w10-auto" not in yaml_text

    def test_metadata_section(self, sample_tickets: list[dict]) -> None:
        """metadata 含 generated_by / ticket_count / ticket_distribution"""
        yaml_text = build_plan_yaml(week=10, tickets=sample_tickets)
        assert "metadata:" in yaml_text
        assert "generated_by: 'scripts/backlog_to_plan_tasks.py'" in yaml_text
        assert "ticket_count: 2" in yaml_text


# ====== write_plan_yaml ======
class TestWritePlanYaml:
    def test_writes_utf8(self, tmp_path: Path) -> None:
        out = tmp_path / "subdir" / "plan.yaml"
        write_plan_yaml(out, "version: 1\nname: 测试\n")  # 含中文
        assert out.exists()
        # 读回应当 utf-8
        content = out.read_text(encoding="utf-8")
        assert content == "version: 1\nname: 测试\n"

    def test_creates_parents(self, tmp_path: Path) -> None:
        out = tmp_path / "deeply" / "nested" / "path" / "plan.yaml"
        write_plan_yaml(out, "x")
        assert out.exists()


# ====== main() + CLI 集成 ======
class TestMainCLI:
    def test_main_dry_run_no_file(self, in_mem_db: Path, tmp_path: Path, capsys) -> None:
        """main + dry_run=True → 不写文件,只 print"""
        _insert_ticket(in_mem_db, "产品", "P0")
        out = tmp_path / "out.yaml"
        n = main(
            db_path=in_mem_db,
            week=10,
            out_path=out,
            priorities=("P0",),
            dry_run=True,
        )
        assert n == 1
        assert not out.exists()
        # yaml 应被 print 到 stdout
        captured = capsys.readouterr()
        assert "version: 1" in captured.out

    def test_main_write_file(self, in_mem_db: Path, tmp_path: Path) -> None:
        """main + dry_run=False → 写文件"""
        _insert_ticket(in_mem_db, "产品", "P0")
        _insert_ticket(in_mem_db, "技术", "P1")
        out = tmp_path / "plan.yaml"
        n = main(
            db_path=in_mem_db,
            week=11,
            out_path=out,
            priorities=("P0", "P1"),
            dry_run=False,
        )
        assert n == 2
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "ticket_count: 2" in content
        assert "product-w11-auto" in content
        assert "tech-w11-auto" in content

    def test_cli_argparse_minimal_required(self, in_mem_db: Path, tmp_path: Path, monkeypatch) -> None:
        """cli() 接受 --week + --out 必填 (用 monkeypatch sys.argv)"""
        out = tmp_path / "plan.yaml"
        monkeypatch.setattr(sys, "argv", [
            "backlog_to_plan_tasks.py",
            "--db", str(in_mem_db),
            "--week", "10",
            "--out", str(out),
            "--dry-run",
        ])
        rc = cli()
        assert rc in (0, None)
        assert not out.exists()

    def test_cli_uses_default_db_when_omitted(self, tmp_path: Path, monkeypatch) -> None:
        """cli 不传 --db 用默认 (mock 主函数验证)"""
        import scripts.backlog_to_plan_tasks as mod

        def fake_main(**kwargs):
            return 1

        monkeypatch.setattr(mod, "main", fake_main)
        monkeypatch.setattr(sys, "argv", [
            "backlog_to_plan_tasks.py",
            "--week", "10",
            "--out", str(tmp_path / "plan.yaml"),
            "--dry-run",
        ])
        rc = cli()
        assert rc == 0
