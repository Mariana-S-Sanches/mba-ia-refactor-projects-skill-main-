"""Regras de negócio de Category."""
from __future__ import annotations

from sqlalchemy import func

from database import db
from middlewares.error_handler import HttpError
from models.category import Category
from models.task import Task


def list_categories() -> list[dict]:
    """Inclui `task_count` em uma única query (sem N+1)."""
    rows = (
        db.session.query(Category, func.count(Task.id).label("task_count"))
        .outerjoin(Task, Task.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.id)
        .all()
    )
    result = []
    for cat, count in rows:
        d = cat.to_dict() if hasattr(cat, "to_dict") else {
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "color": cat.color,
            "created_at": str(cat.created_at) if cat.created_at else None,
        }
        d["task_count"] = count
        result.append(d)
    return result


def get_category(cat_id: int) -> Category:
    cat = Category.query.get(cat_id)
    if not cat:
        raise HttpError(404, "Categoria não encontrada")
    return cat


def create_category(data: dict) -> Category:
    cat = Category(
        name=data["name"],
        description=data.get("description", ""),
        color=data.get("color", "#000000"),
    )
    db.session.add(cat)
    db.session.commit()
    return cat


def update_category(cat_id: int, data: dict) -> Category:
    cat = get_category(cat_id)
    for key in ("name", "description", "color"):
        if key in data:
            setattr(cat, key, data[key])
    db.session.commit()
    return cat


def delete_category(cat_id: int) -> None:
    cat = get_category(cat_id)
    db.session.delete(cat)
    db.session.commit()
