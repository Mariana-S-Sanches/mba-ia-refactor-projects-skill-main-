"""Schemas marshmallow para Task — validação + serialização."""
from __future__ import annotations

from marshmallow import EXCLUDE, Schema, fields, post_dump, validate

from models.task import VALID_STATUSES


class TaskCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    description = fields.Str(load_default="")
    status = fields.Str(load_default="pending", validate=validate.OneOf(VALID_STATUSES))
    priority = fields.Int(load_default=3, validate=validate.Range(min=1, max=5))
    user_id = fields.Int(load_default=None, allow_none=True)
    category_id = fields.Int(load_default=None, allow_none=True)
    due_date = fields.Date(load_default=None, allow_none=True)
    tags = fields.List(fields.Str(), load_default=None, allow_none=True)


class TaskUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    title = fields.Str(validate=validate.Length(min=3, max=200))
    description = fields.Str()
    status = fields.Str(validate=validate.OneOf(VALID_STATUSES))
    priority = fields.Int(validate=validate.Range(min=1, max=5))
    user_id = fields.Int(allow_none=True)
    category_id = fields.Int(allow_none=True)
    due_date = fields.Date(allow_none=True)
    tags = fields.List(fields.Str(), allow_none=True)


class TaskOutSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    description = fields.Str()
    status = fields.Str()
    priority = fields.Int()
    user_id = fields.Int(allow_none=True)
    category_id = fields.Int(allow_none=True)
    created_at = fields.Method("_fmt_created_at")
    updated_at = fields.Method("_fmt_updated_at")
    due_date = fields.Method("_fmt_due_date")
    tags = fields.Method("_tags_list")
    overdue = fields.Method("_overdue")
    user_name = fields.Method("_user_name")
    category_name = fields.Method("_category_name")

    def _fmt_created_at(self, obj):
        return str(obj.created_at) if obj.created_at else None

    def _fmt_updated_at(self, obj):
        return str(obj.updated_at) if obj.updated_at else None

    def _fmt_due_date(self, obj):
        return str(obj.due_date) if obj.due_date else None

    def _tags_list(self, obj):
        return obj.tags_as_list()

    def _overdue(self, obj):
        return obj.is_overdue()

    def _user_name(self, obj):
        return obj.user.name if obj.user else None

    def _category_name(self, obj):
        return obj.category.name if obj.category else None
