"""Tratamento centralizado de erros."""
from __future__ import annotations

from flask import Flask, jsonify
from marshmallow import ValidationError

from src.utils.logger import get_logger

log = get_logger(__name__)


class HttpError(Exception):
    """Erro com status HTTP previsível (4xx)."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def register(app: Flask) -> None:
    @app.errorhandler(HttpError)
    def _http_error(err: HttpError):
        return jsonify({"erro": err.message, "sucesso": False}), err.status

    @app.errorhandler(ValidationError)
    def _validation_error(err: ValidationError):
        return jsonify({"erro": "Dados inválidos", "detalhes": err.messages, "sucesso": False}), 400

    @app.errorhandler(404)
    def _not_found(_err):
        return jsonify({"erro": "Recurso não encontrado", "sucesso": False}), 404

    @app.errorhandler(405)
    def _method_not_allowed(_err):
        return jsonify({"erro": "Método não permitido", "sucesso": False}), 405

    @app.errorhandler(Exception)
    def _unhandled(err: Exception):
        log.exception("Unhandled exception: %s", err)
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
