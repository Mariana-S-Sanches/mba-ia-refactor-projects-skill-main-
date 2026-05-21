"""Schemas marshmallow para validação de payload de produto."""
from __future__ import annotations

from marshmallow import Schema, fields, validate

from src.models.produto import CATEGORIAS_VALIDAS, NOME_MAX_LEN, NOME_MIN_LEN


class CreateProdutoSchema(Schema):
    nome = fields.Str(
        required=True, validate=validate.Length(min=NOME_MIN_LEN, max=NOME_MAX_LEN)
    )
    descricao = fields.Str(load_default="")
    preco = fields.Float(required=True, validate=validate.Range(min=0))
    estoque = fields.Int(required=True, validate=validate.Range(min=0))
    categoria = fields.Str(
        load_default="geral",
        validate=validate.OneOf(CATEGORIAS_VALIDAS),
    )


class UpdateProdutoSchema(CreateProdutoSchema):
    pass


class SearchProdutoSchema(Schema):
    q = fields.Str(load_default="")
    categoria = fields.Str(load_default=None, allow_none=True)
    preco_min = fields.Float(load_default=None, allow_none=True)
    preco_max = fields.Float(load_default=None, allow_none=True)
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    page_size = fields.Int(load_default=50, validate=validate.Range(min=1, max=100))
