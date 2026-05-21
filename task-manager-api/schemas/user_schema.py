"""Schemas marshmallow para Usuário — versão PÚBLICA omite hash de senha."""
from __future__ import annotations

from marshmallow import EXCLUDE, Schema, fields, validate


VALID_ROLES = ("user", "admin", "manager")


class UserCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    role = fields.Str(load_default="user", validate=validate.OneOf(VALID_ROLES))


class UserUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(validate=validate.Length(min=2, max=100))
    email = fields.Email()
    password = fields.Str(validate=validate.Length(min=6))
    role = fields.Str(validate=validate.OneOf(VALID_ROLES))
    active = fields.Bool()


class LoginSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=1))


class UserPublicSchema(Schema):
    """SEM `password`. Use sempre que devolver usuário ao cliente."""

    id = fields.Int()
    name = fields.Str()
    email = fields.Str()
    role = fields.Str()
    active = fields.Bool()
    created_at = fields.Method("_fmt_created_at")

    def _fmt_created_at(self, obj):
        return str(obj.created_at) if obj.created_at else None
