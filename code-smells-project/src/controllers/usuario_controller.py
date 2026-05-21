"""Controller de Usuário."""
from __future__ import annotations

from flask import jsonify, request

from src.middlewares.error_handler import HttpError
from src.models import usuario as usuario_model
from src.schemas.usuario_schema import CreateUsuarioSchema, LoginSchema
from src.services.auth_service import hash_password, verify_password
from src.utils.logger import get_logger

log = get_logger(__name__)


def listar_usuarios():
    page = max(int(request.args.get("page", 1)), 1)
    page_size = min(max(int(request.args.get("page_size", 50)), 1), 100)
    usuarios = usuario_model.list_all(page=page, page_size=page_size)
    return jsonify({"dados": usuarios, "sucesso": True, "page": page, "page_size": page_size}), 200


def buscar_usuario(id: int):
    user = usuario_model.get_by_id(id)
    if not user:
        raise HttpError(404, "Usuário não encontrado")
    return jsonify({"dados": user, "sucesso": True}), 200


def criar_usuario():
    data = CreateUsuarioSchema().load(request.get_json(silent=True) or {})
    if usuario_model.get_by_email(data["email"]) is not None:
        raise HttpError(409, "Email já cadastrado")
    user_id = usuario_model.create(
        nome=data["nome"],
        email=data["email"],
        senha_hash=hash_password(data["senha"]),
    )
    log.info("usuario.created id=%s email=%s", user_id, data["email"])
    return jsonify({"dados": {"id": user_id}, "sucesso": True}), 201


def login():
    data = LoginSchema().load(request.get_json(silent=True) or {})
    user = usuario_model.get_by_email(data["email"])
    if not user or not verify_password(data["senha"], user["senha_hash"]):
        log.info("login.failed email=%s", data["email"])
        raise HttpError(401, "Email ou senha inválidos")
    log.info("login.ok user_id=%s", user["id"])
    return (
        jsonify(
            {
                "dados": {
                    "id": user["id"],
                    "nome": user["nome"],
                    "email": user["email"],
                    "tipo": user["tipo"],
                },
                "sucesso": True,
                "mensagem": "Login OK",
            }
        ),
        200,
    )
