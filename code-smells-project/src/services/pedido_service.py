"""Regra de negócio de pedido — orquestra modelos com transação."""
from __future__ import annotations

from src.db.connection import get_db
from src.middlewares.error_handler import HttpError
from src.models import pedido as pedido_model
from src.models import produto as produto_model
from src.services import notification_service


def criar_pedido(usuario_id: int, itens: list[dict]) -> dict:
    if not itens:
        raise HttpError(400, "Pedido deve ter pelo menos 1 item")

    produto_ids = [int(i["produto_id"]) for i in itens]
    produtos_by_id = produto_model.get_many_by_ids(produto_ids)

    for item in itens:
        produto = produtos_by_id.get(int(item["produto_id"]))
        if produto is None:
            raise HttpError(400, f"Produto {item['produto_id']} não encontrado")
        if produto["estoque"] < int(item["quantidade"]):
            raise HttpError(400, f"Estoque insuficiente para {produto['nome']}")

    total = sum(
        produtos_by_id[int(i["produto_id"])]["preco"] * int(i["quantidade"])
        for i in itens
    )

    db = get_db()
    try:
        db.execute("BEGIN")
        pedido_id = pedido_model.insert_pedido(usuario_id=usuario_id, total=total)
        for item in itens:
            produto = produtos_by_id[int(item["produto_id"])]
            pedido_model.insert_item(
                pedido_id=pedido_id,
                produto_id=int(item["produto_id"]),
                quantidade=int(item["quantidade"]),
                preco_unitario=produto["preco"],
            )
            produto_model.decrement_stock(int(item["produto_id"]), int(item["quantidade"]))
        db.commit()
    except Exception:
        db.rollback()
        raise

    notification_service.notify_pedido_criado(pedido_id=pedido_id, usuario_id=usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def atualizar_status(pedido_id: int, novo_status: str) -> None:
    pedido_model.update_status(pedido_id, novo_status)
    notification_service.notify_status_changed(pedido_id, novo_status)
