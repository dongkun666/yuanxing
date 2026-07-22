"""
LexPrime 邮件服务模块
2026-07-03

功能:
- 邮件模板管理
- 邮件队列管理
- 邮件发送 API
- 集成到业务流程

邮件模板:
- case_status_change: 案件状态变更通知
- task_reminder: 任务提醒
- system_notification: 系统通知
"""
from __future__ import annotations

import asyncio
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, List
from collections import deque

from loguru import logger


SMTP_CONFIG = {
    "host": "smtp.exmail.qq.com",
    "port": 465,
    "user": "founder@lexprime.cn",
    "password": "<REDACTED>",
    "from": "LexPrime <founder@lexprime.cn>",
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
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmailQueue, cls).__new__(cls)
            cls._instance.queue = deque()
            cls._instance.running = False
            cls._instance.semaphore = asyncio.Semaphore(5)
        return cls._instance

    def enqueue(self, email_data: Dict[str, Any]):
        self.queue.append(email_data)
        logger.info(f"[email.queue] 邮件已加入队列: {email_data.get('to')}")

    async def process_queue(self):
        if self.running:
            return
        self.running = True

        while self.queue:
            email_data = self.queue.popleft()
            async with self.semaphore:
                try:
                    await self._send_email(email_data)
                except Exception as e:
                    logger.error(f"[email.queue] 邮件发送失败: {e}, 重新加入队列")
                    self.queue.append(email_data)
                    await asyncio.sleep(60)

        self.running = False

    async def _send_email(self, email_data: Dict[str, Any]):
        try:
            msg = MIMEMultipart()
            msg["From"] = SMTP_CONFIG["from"]
            msg["To"] = email_data["to"]
            msg["Subject"] = email_data["subject"]

            body = email_data["body"]
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP_SSL(SMTP_CONFIG["host"], SMTP_CONFIG["port"]) as server:
                server.login(SMTP_CONFIG["user"], SMTP_CONFIG["password"])
                server.send_message(msg)

            logger.info(f"[email.send] 邮件发送成功: {email_data['to']}")
            return True
        except Exception as e:
            logger.error(f"[email.send] 邮件发送失败: {email_data['to']}, error={e}")
            return False


class EmailService:
    def __init__(self):
        self.queue = EmailQueue()

    async def send_email(self, to: str, subject: str, body: str, immediate: bool = False):
        email_data = {
            "to": to,
            "subject": subject,
            "body": body,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        if immediate:
            return await self.queue._send_email(email_data)

        self.queue.enqueue(email_data)

        if not self.queue.running:
            asyncio.create_task(self.queue.process_queue())

        return True

    async def send_template_email(self, template_name: str, to: str, context: Dict[str, Any]):
        template = EMAIL_TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"邮件模板不存在: {template_name}")

        subject = template["subject"]
        body = template["body"]

        for key, value in context.items():
            subject = subject.replace(f"{{{{{key}}}}}", str(value))
            body = body.replace(f"{{{{{key}}}}}", str(value))

        return await self.send_email(to, subject, body)

    async def send_case_status_change_email(self, to: str, case_id: int, case_title: str, from_status: str, to_status: str, reason: Optional[str] = None):
        status_map = {
            "pending": "待处理",
            "reviewing": "审查中",
            "matching": "匹配中",
            "in_progress": "进行中",
            "closed": "结案",
            "archived": "归档",
        }

        context = {
            "case_id": case_id,
            "case_title": case_title,
            "from_status": status_map.get(from_status, from_status) if from_status else "新建",
            "to_status": status_map.get(to_status, to_status),
            "change_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "reason": reason or "无",
        }

        return await self.send_template_email("case_status_change", to, context)

    async def send_task_reminder_email(self, to: str, task_name: str, case_title: str, deadline: str):
        context = {
            "task_name": task_name,
            "case_title": case_title,
            "deadline": deadline,
        }

        return await self.send_template_email("task_reminder", to, context)

    async def send_system_notification_email(self, to: str, message: str):
        context = {
            "message": message,
        }

        return await self.send_template_email("system_notification", to, context)


email_service = EmailService()