"""Registro centralizado de rotas — apenas mapeamento HTTP → controller."""
from __future__ import annotations

from flask import Flask

from src.controllers import (
    pedido_controller,
    produto_controller,
    relatorio_controller,
    system_controller,
    usuario_controller,
)


def register(app: Flask) -> None:
    # Sistema
    app.add_url_rule("/", "index", system_controller.index, methods=["GET"])
    app.add_url_rule("/health", "health", system_controller.health_check, methods=["GET"])

    # Produtos
    app.add_url_rule("/produtos", "listar_produtos", produto_controller.listar_produtos, methods=["GET"])
    app.add_url_rule("/produtos/busca", "buscar_produtos", produto_controller.buscar_produtos, methods=["GET"])
    app.add_url_rule("/produtos/<int:id>", "buscar_produto", produto_controller.buscar_produto, methods=["GET"])
    app.add_url_rule("/produtos", "criar_produto", produto_controller.criar_produto, methods=["POST"])
    app.add_url_rule("/produtos/<int:id>", "atualizar_produto", produto_controller.atualizar_produto, methods=["PUT"])
    app.add_url_rule("/produtos/<int:id>", "deletar_produto", produto_controller.deletar_produto, methods=["DELETE"])

    # Usuários e autenticação
    app.add_url_rule("/usuarios", "listar_usuarios", usuario_controller.listar_usuarios, methods=["GET"])
    app.add_url_rule("/usuarios/<int:id>", "buscar_usuario", usuario_controller.buscar_usuario, methods=["GET"])
    app.add_url_rule("/usuarios", "criar_usuario", usuario_controller.criar_usuario, methods=["POST"])
    app.add_url_rule("/login", "login", usuario_controller.login, methods=["POST"])

    # Pedidos
    app.add_url_rule("/pedidos", "criar_pedido", pedido_controller.criar_pedido, methods=["POST"])
    app.add_url_rule("/pedidos", "listar_todos_pedidos", pedido_controller.listar_todos_pedidos, methods=["GET"])
    app.add_url_rule(
        "/pedidos/usuario/<int:usuario_id>",
        "listar_pedidos_usuario",
        pedido_controller.listar_pedidos_usuario,
        methods=["GET"],
    )
    app.add_url_rule(
        "/pedidos/<int:pedido_id>/status",
        "atualizar_status_pedido",
        pedido_controller.atualizar_status_pedido,
        methods=["PUT"],
    )

    # Relatórios
    app.add_url_rule(
        "/relatorios/vendas", "relatorio_vendas", relatorio_controller.relatorio_vendas, methods=["GET"]
    )
