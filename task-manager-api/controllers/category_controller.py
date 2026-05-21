"""Controller de Category — extraído de report_routes."""
from __future__ import annotations

from flask import jsonify, request

from schemas.category_schema import (
    CategoryCreateSchema,
    CategoryOutSchema,
    CategoryUpdateSchema,
)
from services import category_service


_out_one = CategoryOutSchema()


def list_categories():
    return jsonify(category_service.list_categories()), 200


def create_category():
    data = CategoryCreateSchema().load(request.get_json(silent=True) or {})
    cat = category_service.create_category(data)
    return jsonify(_out_one.dump(cat)), 201


def update_category(cat_id: int):
    data = CategoryUpdateSchema().load(request.get_json(silent=True) or {})
    cat = category_service.update_category(cat_id, data)
    return jsonify(_out_one.dump(cat)), 200


def delete_category(cat_id: int):
    category_service.delete_category(cat_id)
    return jsonify({"message": "Categoria deletada"}), 200
