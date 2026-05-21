"""Routes de relatórios."""
from __future__ import annotations

from flask import Blueprint

from controllers import report_controller

report_bp = Blueprint("reports", __name__)

report_bp.add_url_rule(
    "/reports/summary", view_func=report_controller.summary, methods=["GET"]
)
report_bp.add_url_rule(
    "/reports/user/<int:user_id>",
    view_func=report_controller.user_report,
    methods=["GET"],
)
