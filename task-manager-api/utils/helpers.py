"""Helpers utilitários.

Validação de payload migrou para schemas/. `process_task_data` foi removido
porque duplicava as regras agora vivas em schemas/task_schema.py.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional


def format_date(date_obj) -> Optional[str]:
    return str(date_obj) if date_obj else None


def calculate_percentage(part: float, total: float) -> float:
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$", email))


def parse_date(date_string: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_string, fmt)
        except (TypeError, ValueError):
            continue
    return None


VALID_STATUSES = ("pending", "in_progress", "done", "cancelled")
VALID_ROLES = ("user", "admin", "manager")
