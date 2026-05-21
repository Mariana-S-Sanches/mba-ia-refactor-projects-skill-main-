"""Controller dos relatórios."""
from __future__ import annotations

from flask import jsonify

from services import report_service


def summary():
    return jsonify(report_service.summary()), 200


def user_report(user_id: int):
    return jsonify(report_service.user_report(user_id)), 200
