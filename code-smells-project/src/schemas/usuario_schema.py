"""Schemas marshmallow para usuário."""
from __future__ import annotations

from marshmallow import Schema, fields, validate


class CreateUsuarioSchema(Schema):
    nome = fields.Str(required=True, validate=validate.Length(min=2, max=120))
    email = fields.Email(required=True)
    senha = fields.Str(required=True, validate=validate.Length(min=6))


class LoginSchema(Schema):
    email = fields.Email(required=True)
    senha = fields.Str(required=True, validate=validate.Length(min=1))
