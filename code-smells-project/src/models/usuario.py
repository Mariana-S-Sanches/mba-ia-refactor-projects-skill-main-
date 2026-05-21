"""Acesso a dados da entidade Usuário (sem expor senha)."""
from __future__ import annotations

from typing import Optional

from src.db.connection import get_db


TIPOS_VALIDOS: tuple[str, ...] = ("cliente", "admin")


def _row_to_public(row) -> dict:
    """Representação SEM o hash de senha — usada nas respostas."""
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def list_all(*, page: int = 1, page_size: int = 50) -> list[dict]:
    offset = (page - 1) * page_size
    rows = get_db().execute(
        "SELECT * FROM usuarios ORDER BY id LIMIT ? OFFSET ?",
        (page_size, offset),
    ).fetchall()
    return [_row_to_public(r) for r in rows]


def get_by_id(user_id: int) -> Optional[dict]:
    row = get_db().execute(
        "SELECT * FROM usuarios WHERE id = ?", (user_id,)
    ).fetchone()
    return _row_to_public(row) if row else None


def get_by_email(email: str) -> Optional[dict]:
    """Retorna inclusive senha_hash — uso interno para autenticação."""
    row = get_db().execute(
        "SELECT * FROM usuarios WHERE email = ?", (email,)
    ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "senha_hash": row["senha_hash"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def create(*, nome: str, email: str, senha_hash: str, tipo: str = "cliente") -> int:
    db = get_db()
    cur = db.execute(
        "INSERT INTO usuarios (nome, email, senha_hash, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return cur.lastrowid
