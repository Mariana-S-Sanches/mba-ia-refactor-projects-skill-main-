"""Routes de Category — novo blueprint isolado, extraído de report_routes."""
from __future__ import annotations

from flask import Blueprint

from controllers import category_controller

category_bp = Blueprint("categories", __name__)

category_bp.add_url_rule(
    "/categories", view_func=category_controller.list_categories, methods=["GET"]
)
category_bp.add_url_rule(
    "/categories", view_func=category_controller.create_category, methods=["POST"]
)
category_bp.add_url_rule(
    "/categories/<int:cat_id>", view_func=category_controller.update_category, methods=["PUT"]
)
category_bp.add_url_rule(
    "/categories/<int:cat_id>", view_func=category_controller.delete_category, methods=["DELETE"]
)
