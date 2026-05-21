"""Controller de Produto — apenas orquestra request/response."""
from __future__ import annotations

from flask import jsonify, request

from src.middlewares.error_handler import HttpError
from src.models import produto as produto_model
from src.schemas.produto_schema import (
    CreateProdutoSchema,
    SearchProdutoSchema,
    UpdateProdutoSchema,
)
from src.utils.logger import get_logger

log = get_logger(__name__)


def listar_produtos():
    page = max(int(request.args.get("page", 1)), 1)
    page_size = min(max(int(request.args.get("page_size", 50)), 1), 100)
    produtos = produto_model.list_all(page=page, page_size=page_size)
    log.info("produto.list page=%s size=%s count=%s", page, page_size, len(produtos))
    return jsonify({"dados": produtos, "sucesso": True, "page": page, "page_size": page_size}), 200


def buscar_produto(id: int):
    produto = produto_model.get_by_id(id)
    if not produto:
        raise HttpError(404, "Produto não encontrado")
    return jsonify({"dados": produto, "sucesso": True}), 200


def criar_produto():
    data = CreateProdutoSchema().load(request.get_json(silent=True) or {})
    novo_id = produto_model.create(**data)
    log.info("produto.created id=%s", novo_id)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(id: int):
    if produto_model.get_by_id(id) is None:
        raise HttpError(404, "Produto não encontrado")
    data = UpdateProdutoSchema().load(request.get_json(silent=True) or {})
    produto_model.update(id, **data)
    log.info("produto.updated id=%s", id)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id: int):
    if produto_model.get_by_id(id) is None:
        raise HttpError(404, "Produto não encontrado")
    produto_model.delete(id)
    log.info("produto.deleted id=%s", id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos():
    params = SearchProdutoSchema().load(request.args.to_dict())
    resultados = produto_model.search(
        termo=params.get("q") or None,
        categoria=params.get("categoria"),
        preco_min=params.get("preco_min"),
        preco_max=params.get("preco_max"),
        page=params["page"],
        page_size=params["page_size"],
    )
    return (
        jsonify(
            {
                "dados": resultados,
                "total": len(resultados),
                "page": params["page"],
                "page_size": params["page_size"],
                "sucesso": True,
            }
        ),
        200,
    )
