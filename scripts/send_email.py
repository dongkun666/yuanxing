#!/usr/bin/env python3
"""
W14 first-paid-triggers-729 邮件触发器 (SMTP 包装)

功能:
- SMTP 配置和发送
- 邮件模板管理
- 邮件队列管理

邮件模板:
- case_status_change: 案件状态变更通知
- task_reminder: 任务提醒
- system_notification: 系统通知
"""
import argparse
import sys
import smtplib
import json
import time
from pathlib import Path
from datetime import datetime
from collections import deque
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_CONFIG = {
    "host": "smtp.exmail.qq.com",
    "port": 465,
    "user": "founder@lexprime.cn",
    "password": "<REDACTED>",
    "from": "LexPrime 创始人 <founder@lexprime.cn>",
}

EMAIL_TEMPLATES = {
    "case_status_change": {
        "subject": "[LexPrime] 案件状态变更通知",
        "body": """尊敬的用户：

案件 #{{case_id}} "{{case_title}}" 的状态已变更：

原状态：{{from_status}}
新状态：{{to_status}}
变更时间：{{change_time}}
变更原因：{{reason}}

请及时查看案件详情。

LexPrime 智能法律助手
""",
    },
    "task_reminder": {
        "subject": "[LexPrime] 任务提醒",
        "body": """尊敬的用户：

您有以下任务需要处理：

任务名称：{{task_name}}
关联案件：{{case_title}}
截止时间：{{deadline}}

请及时处理。

LexPrime 智能法律助手
""",
    },
    "system_notification": {
        "subject": "[LexPrime] 系统通知",
        "body": """尊敬的用户：

{{message}}

LexPrime 智能法律助手
""",
    },
}

class EmailQueue:
    def __init__(self):
        self.queue = deque()
        self.running = False

    def enqueue(self, email_data):
        self.queue.append(email_data)
        print(f"[INFO] 邮件已加入队列: {email_data.get('to')}")

    def process_queue(self):
        if self.running:
            return
        self.running = True

        while self.queue:
            email_data = self.queue.popleft()
            try:
                send_email_smtp(
                    email_data["to"],
                    email_data["subject"],
                    email_data["body"],
                    dry_run=False,
                )
            except Exception as e:
                print(f"[ERROR] 邮件发送失败: {e}, 重新加入队列")
                self.queue.append(email_data)
                time.sleep(60)

        self.running = False


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
    """SMTP 发送邮件"""
    if dry_run:
        print(f"[DRY-RUN] SMTP 发送: to={to}, subject={subject}, body_length={len(body)}")
        return True

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_CONFIG["from"]
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP_SSL(SMTP_CONFIG["host"], SMTP_CONFIG["port"]) as server:
            server.login(SMTP_CONFIG["user"], SMTP_CONFIG["password"])
            server.send_message(msg)

        print(f"[INFO] SMTP 发送成功: to={to}, subject={subject}")
        return True
    except Exception as e:
        print(f"[ERROR] SMTP 发送失败: {e}")
        return False


def render_template(template_name: str, context: dict) -> tuple:
    """渲染邮件模板"""
    template = EMAIL_TEMPLATES.get(template_name)
    if not template:
        raise ValueError(f"邮件模板不存在: {template_name}")

    subject = template["subject"]
    body = template["body"]

    for key, value in context.items():
        subject = subject.replace(f"{{{{{key}}}}}", str(value))
        body = body.replace(f"{{{{{key}}}}}", str(value))

    return subject, body


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