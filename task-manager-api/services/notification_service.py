"""Serviço de notificação — agora chamado pelo task_service.

Em produção, conecta a SMTP usando credenciais de env. Em dev, com
SMTP_HOST vazio, apenas registra no logger (não tenta conectar).
"""
from __future__ import annotations

import logging
import smtplib
from datetime import datetime

from config.settings import settings

log = logging.getLogger(__name__)


def _send_email(to: str, subject: str, body: str) -> bool:
    if not settings.SMTP_HOST:
        log.info("notification.email.dev_skip to=%s subject=%s", to, subject)
        return True
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(settings.SMTP_USER or "no-reply@localhost", to, message)
        log.info("notification.email.sent to=%s subject=%s", to, subject)
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("notification.email.fail to=%s err=%s", to, exc)
        return False


def notify_task_assigned(user, task) -> None:
    subject = f"Nova task atribuída: {task.title}"
    body = (
        f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n"
        f"Prioridade: {task.priority}\nStatus: {task.status}"
    )
    _send_email(user.email, subject, body)


def notify_task_overdue(user, task) -> None:
    subject = f"Task atrasada: {task.title}"
    body = (
        f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n"
        f"Data limite: {task.due_date}"
    )
    _send_email(user.email, subject, body)
