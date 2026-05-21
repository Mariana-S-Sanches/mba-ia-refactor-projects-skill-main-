"""Model de Task — com regra `is_overdue` enxuta usada em toda a app."""
from __future__ import annotations

from datetime import datetime

from database import db


VALID_STATUSES = ("pending", "in_progress", "done", "cancelled")


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="pending")
    priority = db.Column(db.Integer, default=3)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship("User", backref="tasks")
    category = db.relationship("Category", backref="tasks")

    def is_overdue(self) -> bool:
        return bool(
            self.due_date
            and self.due_date < datetime.utcnow()
            and self.status not in ("done", "cancelled")
        )

    def tags_as_list(self) -> list[str]:
        return self.tags.split(",") if self.tags else []
