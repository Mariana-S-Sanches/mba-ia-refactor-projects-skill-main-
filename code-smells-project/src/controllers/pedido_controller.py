"""Controller de Pedido — toda regra está no service."""
from __future__ import annotations

from flask import jsonify, request

from src.models import pedido as pedido_model
from src.schemas.pedido_schema import CreatePedidoSchema, UpdateStatusSchema
from src.services import pedido_service


def criar_pedido():
    data = CreatePedidoSchema().load(request.get_json(silent=True) or {})
    resultado = pedido_service.criar_pedido(usuario_id=data["usuario_id"], itens=data["itens"])
    return (
        jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}),
        201,
    )


def listar_todos_pedidos():
    pedidos = pedido_model.list_all()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_pedidos_usuario(usuario_id: int):
    pedidos = pedido_model.list_by_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status_pedido(pedido_id: int):
    data = UpdateStatusSchema().load(request.get_json(silent=True) or {})
    pedido_service.atualizar_status(pedido_id, data["status"])
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
