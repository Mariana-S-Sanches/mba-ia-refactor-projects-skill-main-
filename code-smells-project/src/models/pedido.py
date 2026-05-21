"""Acesso a dados das entidades Pedido e ItemPedido (com proteção contra N+1)."""
from __future__ import annotations

from typing import Optional

from src.db.connection import get_db


STATUS_VALIDOS: tuple[str, ...] = ("pendente", "aprovado", "enviado", "entregue", "cancelado")


def _list_pedidos_query(filtro_sql: str = "", params: tuple = ()) -> list[dict]:
    """Carrega pedidos + itens + nome do produto em duas queries (sem N+1)."""
    db = get_db()
    pedidos_rows = db.execute(
        f"SELECT * FROM pedidos {filtro_sql} ORDER BY id DESC", params
    ).fetchall()
    if not pedidos_rows:
        return []
    pedido_ids = [r["id"] for r in pedidos_rows]
    placeholders = ",".join("?" * len(pedido_ids))
    itens_rows = db.execute(
        f"""
        SELECT ip.pedido_id, ip.produto_id, ip.quantidade, ip.preco_unitario,
               COALESCE(p.nome, 'Desconhecido') AS produto_nome
        FROM itens_pedido ip
        LEFT JOIN produtos p ON p.id = ip.produto_id
        WHERE ip.pedido_id IN ({placeholders})
        """,
        tuple(pedido_ids),
    ).fetchall()
    itens_by_pedido: dict[int, list[dict]] = {}
    for it in itens_rows:
        itens_by_pedido.setdefault(it["pedido_id"], []).append(
            {
                "produto_id": it["produto_id"],
                "produto_nome": it["produto_nome"],
                "quantidade": it["quantidade"],
                "preco_unitario": it["preco_unitario"],
            }
        )
    return [
        {
            "id": r["id"],
            "usuario_id": r["usuario_id"],
            "status": r["status"],
            "total": r["total"],
            "criado_em": r["criado_em"],
            "itens": itens_by_pedido.get(r["id"], []),
        }
        for r in pedidos_rows
    ]


def list_all() -> list[dict]:
    return _list_pedidos_query()


def list_by_usuario(usuario_id: int) -> list[dict]:
    return _list_pedidos_query("WHERE usuario_id = ?", (usuario_id,))


def insert_pedido(usuario_id: int, total: float) -> int:
    db = get_db()
    cur = db.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    return cur.lastrowid


def insert_item(pedido_id: int, produto_id: int, quantidade: int, preco_unitario: float) -> None:
    get_db().execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
        "VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario),
    )


def update_status(pedido_id: int, novo_status: str) -> None:
    db = get_db()
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()


def aggregate_report() -> dict:
    """Lê todos os agregados em uma única passada."""
    db = get_db()
    row = db.execute(
        """
        SELECT
            COUNT(*) AS total,
            COALESCE(SUM(total), 0) AS faturamento,
            COALESCE(SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END), 0) AS pendentes,
            COALESCE(SUM(CASE WHEN status = 'aprovado' THEN 1 ELSE 0 END), 0) AS aprovados,
            COALESCE(SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END), 0) AS cancelados
        FROM pedidos
        """
    ).fetchone()
    return {
        "total": row["total"],
        "faturamento": row["faturamento"],
        "pendentes": row["pendentes"],
        "aprovados": row["aprovados"],
        "cancelados": row["cancelados"],
    }
