#!/usr/bin/env python3
"""
W14 first-paid-triggers-729 触达日志写入 (dashboard log)

公测前 (7/22 前) 补全:
- dashboard-paid-triggers.md § 2 触达率明细表 真实数据填入
- 5 律师触达节点写入 (邮件/微信/朋友圈)
- 每天 23:00 批量更新 (BD 跑)
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="W14 first-paid-triggers-729 触达日志写入")
    p.add_argument("--trigger-id", required=True, help="触发器 ID (e.g., first-paid-triggers-729)")
    p.add_argument("--trigger-time", required=True, help="触发时间 (ISO 8601)")
    p.add_argument("--trigger-channel", required=True, help="触发通道 (email / wechat / moments)")
    p.add_argument("--trigger-target", required=True, help="触发目标 (e.g., 5-lawyers)")
    p.add_argument("--trigger-success", type=int, default=0, help="触发成功数")
    p.add_argument("--trigger-fail", type=int, default=0, help="触发失败数")
    p.add_argument("--trigger-dry-run", type=int, default=0, help="Dry-run 模式 (1=dry-run, 0=commit)")
    p.add_argument("--log-file", required=True, help="dashboard 路径 (dashboard-paid-triggers.md)")
    p.add_argument("--dry-run", action="store_true", help="Dry-run 模式 (不写 dashboard)")
    return p.parse_args()


def format_log_entry(args: argparse.Namespace) -> str:
    """格式化触达日志条目"""
    timestamp = datetime.now().isoformat(timespec="seconds")
    return f"""
| {timestamp} | {args.trigger_id} | {args.trigger_channel} | {args.trigger_target} | {args.trigger_success}/{args.trigger_success + args.trigger_fail} | {"DRY-RUN" if args.trigger_dry_run else "COMMIT"} | {args.trigger_time} |
"""


def append_to_dashboard(log_file: Path, entry: str, dry_run: bool = False) -> bool:
    """追加触达日志到 dashboard"""
    if dry_run:
        print(f"[DRY-RUN] 触达日志 (不写入): {entry}")
        return True

    if not log_file.exists():
        print(f"[ERROR] dashboard 不存在: {log_file}")
        return False

    # TODO: 公测前补全 dashboard 写入逻辑
    # 找到 § 2 触达率明细表, 追加新行
    # 这里先用 print 模拟
    print(f"[INFO] 触达日志写入: {log_file}")
    print(f"[INFO] 条目: {entry.strip()}")

    # 简单追加到文件末尾 (公测前可优化为表格内精确插入)
    try:
        with log_file.open("a", encoding="utf-8") as f:
            f.write(f"\n<!-- trigger log: {datetime.now().isoformat()} -->\n")
            f.write(entry)
        return True
    except Exception as e:
        print(f"[ERROR] 写入失败: {e}")
        return False


def main() -> int:
    args = parse_args()

    print(f"[INFO] {datetime.now().isoformat()} log_trigger START")
    print(f"[INFO] trigger_id={args.trigger_id}, channel={args.trigger_channel}, target={args.trigger_target}")
    print(f"[INFO] success={args.trigger_success}, fail={args.trigger_fail}, dry_run={args.trigger_dry_run}")

    log_file = Path(args.log_file)
    entry = format_log_entry(args)

    success = append_to_dashboard(log_file, entry, dry_run=args.dry_run)

    if success:
        print(f"[INFO] log_trigger OK")
        return 0
    else:
        print(f"[ERROR] log_trigger FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())