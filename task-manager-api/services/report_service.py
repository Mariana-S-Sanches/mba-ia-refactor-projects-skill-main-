"""Relatórios — agregados em SQL para evitar N+1."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import case, func

from database import db
from middlewares.error_handler import HttpError
from models.category import Category
from models.task import Task
from models.user import User


def summary() -> dict:
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)

    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    by_status = dict(
        db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all()
    )

    by_priority = dict(
        db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all()
    )

    overdue_rows = (
        Task.query.filter(
            Task.due_date.isnot(None),
            Task.due_date < now,
            Task.status.notin_(("done", "cancelled")),
        ).all()
    )
    overdue_list = [
        {
            "id": t.id,
            "title": t.title,
            "due_date": str(t.due_date),
            "days_overdue": (now - t.due_date).days,
        }
        for t in overdue_rows
    ]

    recent_created = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = (
        Task.query.filter(Task.status == "done", Task.updated_at >= seven_days_ago).count()
    )

    # Productividade por usuário em UMA query (sem N+1)
    user_stats_rows = (
        db.session.query(
            User.id,
            User.name,
            func.count(Task.id).label("total_tasks"),
            func.sum(case((Task.status == "done", 1), else_=0)).label("completed_tasks"),
        )
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id, User.name)
        .order_by(User.id)
        .all()
    )
    user_stats = []
    for uid, uname, total, completed in user_stats_rows:
        completed = completed or 0
        user_stats.append(
            {
                "user_id": uid,
                "user_name": uname,
                "total_tasks": total or 0,
                "completed_tasks": completed,
                "completion_rate": round((completed / total) * 100, 2) if total else 0,
            }
        )

    return {
        "generated_at": str(now),
        "overview": {
            "total_tasks": total_tasks,
            "total_users": total_users,
            "total_categories": total_categories,
        },
        "tasks_by_status": {
            "pending": by_status.get("pending", 0),
            "in_progress": by_status.get("in_progress", 0),
            "done": by_status.get("done", 0),
            "cancelled": by_status.get("cancelled", 0),
        },
        "tasks_by_priority": {
            "critical": by_priority.get(1, 0),
            "high": by_priority.get(2, 0),
            "medium": by_priority.get(3, 0),
            "low": by_priority.get(4, 0),
            "minimal": by_priority.get(5, 0),
        },
        "overdue": {"count": len(overdue_list), "tasks": overdue_list},
        "recent_activity": {
            "tasks_created_last_7_days": recent_created,
            "tasks_completed_last_7_days": recent_done,
        },
        "user_productivity": user_stats,
    }


def user_report(user_id: int) -> dict:
    user = User.query.get(user_id)
    if not user:
        raise HttpError(404, "Usuário não encontrado")

    now = datetime.utcnow()
    row = (
        db.session.query(
            func.count(Task.id).label("total"),
            func.sum(case((Task.status == "done", 1), else_=0)).label("done"),
            func.sum(case((Task.status == "pending", 1), else_=0)).label("pending"),
            func.sum(case((Task.status == "in_progress", 1), else_=0)).label("in_progress"),
            func.sum(case((Task.status == "cancelled", 1), else_=0)).label("cancelled"),
            func.sum(case((Task.priority <= 2, 1), else_=0)).label("high_priority"),
            func.sum(
                case(
                    (
                        db.and_(
                            Task.due_date.isnot(None),
                            Task.due_date < now,
                            Task.status.notin_(("done", "cancelled")),
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("overdue"),
        )
        .filter(Task.user_id == user_id)
        .one()
    )
    total = row.total or 0
    done = row.done or 0
    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "statistics": {
            "total_tasks": total,
            "done": done,
            "pending": row.pending or 0,
            "in_progress": row.in_progress or 0,
            "cancelled": row.cancelled or 0,
            "overdue": row.overdue or 0,
            "high_priority": row.high_priority or 0,
            "completion_rate": round((done / total) * 100, 2) if total else 0,
        },
    }
