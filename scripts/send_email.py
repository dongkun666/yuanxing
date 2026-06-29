#!/usr/bin/env python3
"""
W14 first-paid-triggers-729 邮件触发器 (SMTP 包装)

公测前 (7/22 前) 补全:
- SMTP 配置 (SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASS / SMTP_FROM)
- 邮件正文解析 (从 first-paid-triggers-runbook.md § 3.1 提取 800 字)
- 发送结果日志 (成功/失败/重试)
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime

# TODO: 公测前补全 SMTP 配置
SMTP_CONFIG = {
    "host": "smtp.exmail.qq.com",  # QQ 企业邮箱 (placeholder)
    "port": 465,
    "user": "founder@lexprime.cn",
    "pass": "<REDACTED>",  # 公测前填实
    "from": "LexPrime 创始人 <founder@lexprime.cn>",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="W14 first-paid-triggers-729 邮件触发器")
    p.add_argument("--to", required=True, help="收件人邮箱")
    p.add_argument("--subject", required=True, help="邮件主题")
    p.add_argument("--body", required=True, help="邮件正文路径 (first-paid-triggers-runbook.md)")
    p.add_argument("--body-section", default="### 3.1", help="邮件正文小节 (默认 3.1 提前 6 天)")
    p.add_argument("--invite-code", required=True, help="律师邀请码 (BETA2025-XXXX)")
    p.add_argument("--trigger-id", default="first-paid-triggers-729", help="触发器 ID")
    p.add_argument("--trigger-time", required=True, help="触发时间 (ISO 8601)")
    p.add_argument("--dry-run", action="store_true", help="Dry-run 模式 (不真发)")
    return p.parse_args()


def extract_email_body(body_path: str, section: str) -> str:
    """从 first-paid-triggers-runbook.md § X.Y 提取邮件正文"""
    body_file = Path(body_path)
    if not body_file.exists():
        raise FileNotFoundError(f"邮件模板不存在: {body_path}")

    content = body_file.read_text(encoding="utf-8")
    # 简单 markdown section 提取 (公测前可优化为更严格的 AST 解析)
    lines = content.split("\n")
    in_section = False
    body_lines = []

    for line in lines:
        if line.strip().startswith(section):
            in_section = True
            continue
        if in_section:
            if line.strip().startswith("### ") and not line.strip().startswith(section):
                break
            body_lines.append(line)

    return "\n".join(body_lines).strip()


def send_email_smtp(to: str, subject: str, body: str, dry_run: bool = False) -> bool:
    """SMTP 发送邮件 (公测前补全)"""
    if dry_run:
        print(f"[DRY-RUN] SMTP 发送: to={to}, subject={subject}, body_length={len(body)}")
        return True

    # TODO: 公测前补全 SMTP 发送逻辑
    # import smtplib
    # from email.mime.text import MIMEText
    #
    # msg = MIMEText(body, "plain", "utf-8")
    # msg["Subject"] = subject
    # msg["From"] = SMTP_CONFIG["from"]
    # msg["To"] = to
    #
    # try:
    #     with smtplib.SMTP_SSL(SMTP_CONFIG["host"], SMTP_CONFIG["port"]) as server:
    #         server.login(SMTP_CONFIG["user"], SMTP_CONFIG["pass"])
    #         server.send_message(msg)
    #     return True
    # except Exception as e:
    #     print(f"[ERROR] SMTP 发送失败: {e}")
    #     return False

    print(f"[PLACEHOLDER] SMTP 未配置 (公测前补全): to={to}, subject={subject}")
    return True


def main() -> int:
    args = parse_args()

    print(f"[INFO] {datetime.now().isoformat()} send_email START")
    print(f"[INFO] to={args.to}, subject={args.subject}, invite_code={args.invite_code}")

    # 1. 提取邮件正文
    try:
        body = extract_email_body(args.body, args.body_section)
        print(f"[INFO] 邮件正文提取成功: {len(body)} 字")
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return 1

    # 2. SMTP 发送
    success = send_email_smtp(args.to, args.subject, body, dry_run=args.dry_run)

    if success:
        print(f"[INFO] send_email OK")
        return 0
    else:
        print(f"[ERROR] send_email FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())