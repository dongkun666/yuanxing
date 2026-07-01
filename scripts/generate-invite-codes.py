#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LexPrime W6 公测邀请码生成脚本 (BD/运营).

按 BETA2025-XXXX 格式生成 115 个邀请码 (4 位随机, 10000 种组合):
- 5 律师评审 (评审 #1 07-19 + 评审 #2 07-26, 涵盖 单飞/小所/中所/企业法务 4 类)
- 10 微信群律师 (总指挥私域律师朋友)
- 100 创始体验官 (前 100 名律师, 1 年个人版 5 折 ¥449/年 + 终身优先客服)

输出:
- docs/marketing/invite-codes-list.csv (115 行 + 表头)

用法:
    python scripts/generate-invite-codes.py
    python scripts/generate-invite-codes.py --regen          # 强制重写 CSV
    python scripts/generate-invite-codes.py --verify        # 校验现有 CSV 完整性

数据契约 (与 landing / 邀请码系统对齐):
- backend/cases-crawler/api/invite_router.py (W6 Task 3 lex-design 落地)
- POST /api/invite/redeem 入参 { code: "BETA2025-XXXX" }
- 1 码 1 用, 状态机: unused → redeemed → active (注册成功) → expired/converted

设计原则:
- **确定性生成**: 按区间分配 (评审 0001-0005 / 微信群 0006-0015 / 创史 0016-0115), 复核可重跑
- **可审计**: CSV 每行带 channel + batch + status + notes, 触达时由总指挥填 assigned_to/contact
- **不依赖外部库**: 仅用标准库 csv + argparse, W6 BD/运营一上手就跑
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 中国时区 UTC+8
CST = timezone(timedelta(hours=8))

# 邀请码格式: BETA2025-XXXX (4 位数字, 10000 种)
CODE_PREFIX = "BETA2025-"
CODE_FORMAT = "BETA2025-{:04d}"

# 115 邀请码分配规范: 每行一个邀请码
# 格式: (channel, batch, note_template) 三元组, 由 build_rows() 按区间展开
SPECS = [
    # 评审律师 (评审 #1 L1-L3 在 07-19 + 评审 #2 L4-L5 在 07-26)
    ("review", "B1-评审#1-0719", "L1-单飞律师 (评审 #1, 民商/刑事)"),
    ("review", "B1-评审#1-0719", "L2-小所合伙人 (评审 #1, 民商/合同)"),
    ("review", "B1-评审#1-0719", "L3-小所婚姻家事 (评审 #1, 婚姻家事/合同)"),
    ("review", "B2-评审#2-0726", "L4-中所合伙人 (评审 #2, 金融/商事)"),
    ("review", "B2-评审#2-0726", "L5-企业法务总监 (评审 #2, 合同/合规)"),
] + [
    # 微信群律师 (10 位): 总指挥私域律师朋友
    ("wechat-group", "WX-私域群", "微信群律师-第{:02d}号 (总指挥私域)".format(idx))
    for idx in range(1, 11)
] + [
    # 创始体验官 (100 位): 前 100 名律师, 1 年 ¥449 5 折
    ("founding-member", "FM-创史001-100", "创史体验官-第{:03d}名 (¥449/年)".format(idx))
    for idx in range(1, 101)
]

# 校验: 5 评审 + 10 微信群 + 100 创史 = 115
assert len(SPECS) == 115, f"SPECS 长度 {len(SPECS)} != 115, 请检查分配"


def build_rows():
    """按 SPECS 顺序生成 115 行邀请码 (编号 0001-0115)."""
    rows = []
    now = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")
    for n, (channel, batch, notes) in enumerate(SPECS, start=1):
        rows.append({
            "code": CODE_FORMAT.format(n),
            "channel": channel,
            "batch": batch,
            "status": "unused",          # unused → redeemed → active → converted/expired
            "assigned_to": "",            # 由总指挥触达后填 (律师姓名)
            "contact": "",                # 由总指挥触达后填 (微信/邮箱)
            "redeemed_at": "",            # 律师首次注册时间 (运营填)
            "trial_expires_at": "",       # 30 天试用到期日 (运营填)
            "notes": notes,
            "created_at": now,
        })
    return rows


def write_csv(rows, csv_path: Path, force: bool = False) -> None:
    """写 CSV; force=False 时若已存在则 skip."""
    if csv_path.exists() and not force:
        print(f"[skip] CSV 已存在: {csv_path} (用 --regen 强制重写)", file=sys.stderr)
        return
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[ok] 写入 {len(rows)} 行 → {csv_path}", file=sys.stderr)


def verify_csv(csv_path: Path) -> bool:
    """校验 CSV 完整性: 115 行 / 无重复 / 格式正确 / 区间分布对得上."""
    if not csv_path.exists():
        print(f"[fail] CSV 不存在: {csv_path}", file=sys.stderr)
        return False
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if len(rows) != 115:
        print(f"[fail] 行数 {len(rows)} != 115", file=sys.stderr)
        return False
    codes = [r["code"] for r in rows]
    if len(set(codes)) != 115:
        print("[fail] 邀请码有重复", file=sys.stderr)
        return False
    # 格式校验
    import re
    pat = re.compile(r"^BETA2025-\d{4}$")
    for c in codes:
        if not pat.match(c):
            print(f"[fail] 格式错误: {c}", file=sys.stderr)
            return False
    # 区间分布校验
    expected = {"review": 5, "wechat-group": 10, "founding-member": 100}
    actual = {}
    for r in rows:
        actual[r["channel"]] = actual.get(r["channel"], 0) + 1
    if actual != expected:
        print(f"[fail] 分布 {actual} != 预期 {expected}", file=sys.stderr)
        return False
    print(f"[ok] CSV 校验通过: {len(rows)} 行 / 3 渠道分布正确 / 格式合规", file=sys.stderr)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="LexPrime W6 公测邀请码生成")
    parser.add_argument("--regen", action="store_true", help="强制重写 CSV")
    parser.add_argument("--verify", action="store_true", help="仅校验 CSV 完整性, 不写")
    parser.add_argument(
        "--out",
        type=str,
        default="docs/marketing/invite-codes-list.csv",
        help="输出 CSV 路径 (相对仓库根目录)",
    )
    args = parser.parse_args()

    # 仓库根目录: scripts/generate-invite-codes.py → ..
    repo_root = Path(__file__).resolve().parent.parent
    csv_path = repo_root / args.out

    if args.verify:
        return 0 if verify_csv(csv_path) else 1

    rows = build_rows()
    write_csv(rows, csv_path, force=args.regen)
    # 写完顺便校验一次
    return 0 if verify_csv(csv_path) else 1


if __name__ == "__main__":
    sys.exit(main())
