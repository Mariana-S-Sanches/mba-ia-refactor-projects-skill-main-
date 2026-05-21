"""Controller dos relatórios."""
from __future__ import annotations

from flask import jsonify

from src.services import relatorio_service


def relatorio_vendas():
    return jsonify({"dados": relatorio_service.relatorio_vendas(), "sucesso": True}), 200
