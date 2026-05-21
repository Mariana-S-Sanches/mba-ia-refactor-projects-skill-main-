"""Tratamento centralizado de erros."""
from __future__ import annotations

import logging

from flask import Flask, jsonify
from marshmallow import ValidationError

log = logging.getLogger(__name__)


class HttpError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def register(app: Flask) -> None:
    @app.errorhandler(HttpError)
    def _http_error(err: HttpError):
        return jsonify({"error": err.message}), err.status

    @app.errorhandler(ValidationError)
    def _validation_error(err: ValidationError):
        return jsonify({"error": "Dados inválidos", "details": err.messages}), 400

    @app.errorhandler(404)
    def _not_found(_e):
        return jsonify({"error": "Recurso não encontrado"}), 404

    @app.errorhandler(405)
    def _not_allowed(_e):
        return jsonify({"error": "Método não permitido"}), 405

    @app.errorhandler(Exception)
    def _unhandled(err: Exception):
        log.exception("Unhandled exception: %s", err)
        return jsonify({"error": "Erro interno do servidor"}), 500
