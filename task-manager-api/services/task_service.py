"""Regras de negócio de Task — acessa db via models."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import case, func
from sqlalchemy.orm import joinedload

from database import db
from middlewares.error_handler import HttpError
from models.task import Task
from models.user import User
from models.category import Category
from services import notification_service


def _ensure_user(user_id: Optional[int]) -> None:
    if user_id is not None and User.query.get(user_id) is None:
        raise HttpError(404, "Usuário não encontrado")


def _ensure_category(category_id: Optional[int]) -> None:
    if category_id is not None and Category.query.get(category_id) is None:
        raise HttpError(404, "Categoria não encontrada")


def _serialize_tags(tags) -> Optional[str]:
    if tags is None:
        return None
    if isinstance(tags, list):
        return ",".join(t.strip() for t in tags if t)
    return str(tags)


def list_tasks(*, page: int, page_size: int) -> tuple[list[Task], int]:
    base = Task.query.options(joinedload(Task.user), joinedload(Task.category))
    total = base.count()
    items = base.order_by(Task.id).limit(page_size).offset((page - 1) * page_size).all()
    return items, total


def get_task(task_id: int) -> Task:
    task = Task.query.options(joinedload(Task.user), joinedload(Task.category)).get(task_id)
    if not task:
        raise HttpError(404, "Task não encontrada")
    return task


def create_task(data: dict) -> Task:
    _ensure_user(data.get("user_id"))
    _ensure_category(data.get("category_id"))

    due_date = data.get("due_date")
    if due_date is not None and not isinstance(due_date, datetime):
        # marshmallow devolve date; convertemos a datetime para coluna DateTime
        due_date = datetime.combine(due_date, datetime.min.time())

    task = Task(
        title=data["title"],
        description=data.get("description", ""),
        status=data.get("status", "pending"),
        priority=data.get("priority", 3),
        user_id=data.get("user_id"),
        category_id=data.get("category_id"),
        due_date=due_date,
        tags=_serialize_tags(data.get("tags")),
    )
    db.session.add(task)
    db.session.commit()

    if task.user_id and task.user:
        notification_service.notify_task_assigned(task.user, task)
    return task


def update_task(task_id: int, data: dict) -> Task:
    task = get_task(task_id)

    if "user_id" in data:
        _ensure_user(data["user_id"])
    if "category_id" in data:
        _ensure_category(data["category_id"])

    for key, value in data.items():
        if key == "tags":
            task.tags = _serialize_tags(value)
        elif key == "due_date" and value is not None and not isinstance(value, datetime):
            task.due_date = datetime.combine(value, datetime.min.time())
        else:
            setattr(task, key, value)

    task.updated_at = datetime.utcnow()
    db.session.commit()
    return task


def delete_task(task_id: int) -> None:
    task = get_task(task_id)
    db.session.delete(task)
    db.session.commit()


def search_tasks(*, q: str, status: str, priority: str, user_id: str) -> list[Task]:
    query = Task.query.options(joinedload(Task.user), joinedload(Task.category))
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Task.title.like(like), Task.description.like(like)))
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == int(priority))
    if user_id:
        query = query.filter(Task.user_id == int(user_id))
    return query.order_by(Task.id).all()


def stats() -> dict:
    """Resumo agregado sem N+1: uma query escalar para cada métrica."""
    counts = db.session.query(
        func.count(Task.id).label("total"),
        func.sum(case((Task.status == "pending", 1), else_=0)).label("pending"),
        func.sum(case((Task.status == "in_progress", 1), else_=0)).label("in_progress"),
        func.sum(case((Task.status == "done", 1), else_=0)).label("done"),
        func.sum(case((Task.status == "cancelled", 1), else_=0)).label("cancelled"),
        func.sum(
            case(
                (
                    db.and_(
                        Task.due_date.isnot(None),
                        Task.due_date < datetime.utcnow(),
                        Task.status.notin_(("done", "cancelled")),
                    ),
                    1,
                ),
                else_=0,
            )
        ).label("overdue"),
    ).one()

    total = counts.total or 0
    done = counts.done or 0
    return {
        "total": total,
        "pending": counts.pending or 0,
        "in_progress": counts.in_progress or 0,
        "done": done,
        "cancelled": counts.cancelled or 0,
        "overdue": counts.overdue or 0,
        "completion_rate": round((done / total) * 100, 2) if total > 0 else 0,
    }
