"""Acesso a dados e regras locais da entidade Produto."""
from __future__ import annotations

from typing import Iterable, Optional

from src.db.connection import get_db


CATEGORIAS_VALIDAS: tuple[str, ...] = (
    "informatica",
    "moveis",
    "vestuario",
    "geral",
    "eletronicos",
    "livros",
)

NOME_MIN_LEN = 2
NOME_MAX_LEN = 200


def _row_to_dict(row) -> dict:
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": bool(row["ativo"]),
        "criado_em": row["criado_em"],
    }


def list_all(*, page: int = 1, page_size: int = 50) -> list[dict]:
    offset = (page - 1) * page_size
    rows = get_db().execute(
        "SELECT * FROM produtos ORDER BY id LIMIT ? OFFSET ?",
        (page_size, offset),
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_by_id(produto_id: int) -> Optional[dict]:
    row = get_db().execute(
        "SELECT * FROM produtos WHERE id = ?", (produto_id,)
    ).fetchone()
    return _row_to_dict(row) if row else None


def create(*, nome: str, descricao: str, preco: float, estoque: int, categoria: str) -> int:
    db = get_db()
    cur = db.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
        "VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cur.lastrowid


def update(
    produto_id: int,
    *,
    nome: str,
    descricao: str,
    preco: float,
    estoque: int,
    categoria: str,
) -> None:
    db = get_db()
    db.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? "
        "WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()


def delete(produto_id: int) -> None:
    db = get_db()
    db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()


def search(
    termo: Optional[str] = None,
    categoria: Optional[str] = None,
    preco_min: Optional[float] = None,
    preco_max: Optional[float] = None,
    *,
    page: int = 1,
    page_size: int = 50,
) -> list[dict]:
    clauses: list[str] = ["1 = 1"]
    params: list = []
    if termo:
        clauses.append("(nome LIKE ? OR descricao LIKE ?)")
        like = f"%{termo}%"
        params.extend([like, like])
    if categoria:
        clauses.append("categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        clauses.append("preco >= ?")
        params.append(preco_min)
    if preco_max is not None:
        clauses.append("preco <= ?")
        params.append(preco_max)

    offset = (page - 1) * page_size
    sql = "SELECT * FROM produtos WHERE " + " AND ".join(clauses) + " ORDER BY id LIMIT ? OFFSET ?"
    params.extend([page_size, offset])
    rows = get_db().execute(sql, tuple(params)).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_many_by_ids(ids: Iterable[int]) -> dict[int, dict]:
    """Para evitar N+1: busca vários produtos de uma vez."""
    ids = list(ids)
    if not ids:
        return {}
    placeholders = ",".join("?" * len(ids))
    rows = get_db().execute(
        f"SELECT * FROM produtos WHERE id IN ({placeholders})", tuple(ids)
    ).fetchall()
    return {row["id"]: _row_to_dict(row) for row in rows}


def decrement_stock(produto_id: int, quantidade: int) -> None:
    db = get_db()
    db.execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
        (quantidade, produto_id),
    )
