"""Controller de Usuário."""
from __future__ import annotations

from flask import jsonify, request

from config.settings import settings
from schemas.task_schema import TaskOutSchema
from schemas.user_schema import (
    LoginSchema,
    UserCreateSchema,
    UserPublicSchema,
    UserUpdateSchema,
)
from services import user_service
from services.auth_service import create_token


_out_one = UserPublicSchema()
_out_many = UserPublicSchema(many=True)
_task_out_many = TaskOutSchema(many=True)


def list_users():
    page = max(int(request.args.get("page", 1)), 1)
    page_size = min(
        max(int(request.args.get("page_size", settings.DEFAULT_PAGE_SIZE)), 1),
        settings.MAX_PAGE_SIZE,
    )
    items, total = user_service.list_users(page=page, page_size=page_size)
    return jsonify(
        {"data": _out_many.dump(items), "page": page, "page_size": page_size, "total": total}
    ), 200


def get_user(user_id: int):
    user = user_service.get_user(user_id)
    payload = _out_one.dump(user)
    payload["tasks"] = _task_out_many.dump(user.tasks)
    return jsonify(payload), 200


def create_user():
    data = UserCreateSchema().load(request.get_json(silent=True) or {})
    user = user_service.create_user(data)
    return jsonify(_out_one.dump(user)), 201


def update_user(user_id: int):
    data = UserUpdateSchema().load(request.get_json(silent=True) or {})
    user = user_service.update_user(user_id, data)
    return jsonify(_out_one.dump(user)), 200


def delete_user(user_id: int):
    user_service.delete_user(user_id)
    return jsonify({"message": "Usuário deletado com sucesso"}), 200


def user_tasks(user_id: int):
    items = user_service.tasks_of(user_id)
    return jsonify(_task_out_many.dump(items)), 200


def login():
    data = LoginSchema().load(request.get_json(silent=True) or {})
    user = user_service.authenticate(data["email"], data["password"])
    token = create_token(user.id, user.role)
    return jsonify(
        {"message": "Login realizado com sucesso", "user": _out_one.dump(user), "token": token}
    ), 200
