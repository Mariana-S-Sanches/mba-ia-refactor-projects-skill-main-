"""Schemas marshmallow para Category."""
from __future__ import annotations

from marshmallow import EXCLUDE, Schema, fields, validate


class CategoryCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(load_default="")
    color = fields.Str(load_default="#000000", validate=validate.Regexp(r"^#[0-9A-Fa-f]{6}$"))


class CategoryUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(validate=validate.Length(min=1, max=100))
    description = fields.Str()
    color = fields.Str(validate=validate.Regexp(r"^#[0-9A-Fa-f]{6}$"))


class CategoryOutSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    description = fields.Str()
    color = fields.Str()
    created_at = fields.Method("_fmt_created_at")
    task_count = fields.Int(dump_default=0)

    def _fmt_created_at(self, obj):
        return str(obj.created_at) if obj.created_at else None
