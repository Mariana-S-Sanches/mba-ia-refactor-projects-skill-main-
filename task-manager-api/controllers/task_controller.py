"""Controller de Task — orquestra HTTP. Sem regras."""
from __future__ import annotations

from flask import jsonify, request

from config.settings import settings
from schemas.task_schema import TaskCreateSchema, TaskOutSchema, TaskUpdateSchema
from services import task_service


_out_one = TaskOutSchema()
_out_many = TaskOutSchema(many=True)


def list_tasks():
    page = max(int(request.args.get("page", 1)), 1)
    page_size = min(
        max(int(request.args.get("page_size", settings.DEFAULT_PAGE_SIZE)), 1),
        settings.MAX_PAGE_SIZE,
    )
    items, total = task_service.list_tasks(page=page, page_size=page_size)
    return jsonify(
        {
            "data": _out_many.dump(items),
            "page": page,
            "page_size": page_size,
            "total": total,
        }
    ), 200


def get_task(task_id: int):
    return jsonify(_out_one.dump(task_service.get_task(task_id))), 200


def create_task():
    data = TaskCreateSchema().load(request.get_json(silent=True) or {})
    task = task_service.create_task(data)
    return jsonify(_out_one.dump(task)), 201


def update_task(task_id: int):
    data = TaskUpdateSchema().load(request.get_json(silent=True) or {})
    task = task_service.update_task(task_id, data)
    return jsonify(_out_one.dump(task)), 200


def delete_task(task_id: int):
    task_service.delete_task(task_id)
    return jsonify({"message": "Task deletada com sucesso"}), 200


def search_tasks():
    items = task_service.search_tasks(
        q=request.args.get("q", ""),
        status=request.args.get("status", ""),
        priority=request.args.get("priority", ""),
        user_id=request.args.get("user_id", ""),
    )
    return jsonify(_out_many.dump(items)), 200


def task_stats():
    return jsonify(task_service.stats()), 200
