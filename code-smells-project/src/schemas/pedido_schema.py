"""Schemas marshmallow para pedido."""
from __future__ import annotations

from marshmallow import Schema, fields, validate

from src.models.pedido import STATUS_VALIDOS


class ItemPedidoSchema(Schema):
    produto_id = fields.Int(required=True, validate=validate.Range(min=1))
    quantidade = fields.Int(required=True, validate=validate.Range(min=1))


class CreatePedidoSchema(Schema):
    usuario_id = fields.Int(required=True, validate=validate.Range(min=1))
    itens = fields.List(
        fields.Nested(ItemPedidoSchema), required=True, validate=validate.Length(min=1)
    )


class UpdateStatusSchema(Schema):
    status = fields.Str(required=True, validate=validate.OneOf(STATUS_VALIDOS))
