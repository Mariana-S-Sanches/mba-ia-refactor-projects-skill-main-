"""Model de Usuário — sem hashing inline (delegado ao auth_service)."""
from __future__ import annotations

from datetime import datetime

from database import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    # Armazenamos bcrypt-hash (~60 chars); a coluna existente VARCHAR(255) acomoda.
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="user")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
