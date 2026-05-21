"""Regras de negócio de Usuário."""
from __future__ import annotations

from sqlalchemy.orm import joinedload

from database import db
from middlewares.error_handler import HttpError
from models.task import Task
from models.user import User
from services.auth_service import hash_password, verify_password


def list_users(*, page: int, page_size: int) -> tuple[list[User], int]:
    base = User.query
    total = base.count()
    items = base.order_by(User.id).limit(page_size).offset((page - 1) * page_size).all()
    return items, total


def get_user(user_id: int) -> User:
    user = User.query.get(user_id)
    if not user:
        raise HttpError(404, "Usuário não encontrado")
    return user


def create_user(data: dict) -> User:
    if User.query.filter_by(email=data["email"]).first():
        raise HttpError(409, "Email já cadastrado")
    user = User(
        name=data["name"],
        email=data["email"],
        password=hash_password(data["password"]),
        role=data.get("role", "user"),
    )
    db.session.add(user)
    db.session.commit()
    return user


def update_user(user_id: int, data: dict) -> User:
    user = get_user(user_id)
    if "email" in data and data["email"] != user.email:
        if User.query.filter_by(email=data["email"]).first():
            raise HttpError(409, "Email já cadastrado")
        user.email = data["email"]
    if "name" in data:
        user.name = data["name"]
    if "password" in data:
        user.password = hash_password(data["password"])
    if "role" in data:
        user.role = data["role"]
    if "active" in data:
        user.active = data["active"]
    db.session.commit()
    return user


def delete_user(user_id: int) -> None:
    user = get_user(user_id)
    # Remove tasks associadas (mantendo o contrato original do projeto)
    Task.query.filter_by(user_id=user_id).delete(synchronize_session=False)
    db.session.delete(user)
    db.session.commit()


def tasks_of(user_id: int) -> list[Task]:
    get_user(user_id)
    return (
        Task.query.options(joinedload(Task.user), joinedload(Task.category))
        .filter_by(user_id=user_id)
        .order_by(Task.id)
        .all()
    )


def authenticate(email: str, password: str) -> User:
    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(password, user.password):
        raise HttpError(401, "Credenciais inválidas")
    if not user.active:
        raise HttpError(403, "Usuário inativo")
    return user
