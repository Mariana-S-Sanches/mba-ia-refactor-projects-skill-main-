"""Endpoints de sistema: index e health (sem expor secrets)."""
from __future__ import annotations

from flask import jsonify

from src.db.connection import get_db


def index():
    return jsonify(
        {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "2.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        }
    )


def health_check():
    """Health-check minimalista: não vaza configuração interna."""
    db = get_db()
    try:
        db.execute("SELECT 1")
        return jsonify({"status": "ok", "database": "connected"}), 200
    except Exception:
        return jsonify({"status": "degraded", "database": "unreachable"}), 503
