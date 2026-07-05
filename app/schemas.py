"""
app/schemas.py — Marshmallow schemas for input validation and serialization.

Each schema serves two roles:
  1. Deserialize + validate incoming JSON request bodies.
  2. Serialize SQLAlchemy model instances to JSON-safe dicts.
"""

from marshmallow import fields, validate, validates, ValidationError, EXCLUDE
from app import ma
from app.models import Task


class UserSchema(ma.Schema):
    """Schema for User registration and serialization."""

    class Meta:
        unknown = EXCLUDE

    id         = fields.Int(dump_only=True)
    username   = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email      = fields.Email(required=True)
    password   = fields.Str(required=True, load_only=True,
                             validate=validate.Length(min=6))
    created_at = fields.DateTime(dump_only=True)


class LoginSchema(ma.Schema):
    """Schema for login requests — email + password only."""

    class Meta:
        unknown = EXCLUDE

    email    = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


class ProjectSchema(ma.Schema):
    """Schema for Project creation, update, and serialization."""

    class Meta:
        unknown = EXCLUDE

    id          = fields.Int(dump_only=True)
    name        = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    description = fields.Str(load_default=None)
    owner_id    = fields.Int(dump_only=True)
    created_at  = fields.DateTime(dump_only=True)


class TaskSchema(ma.Schema):
    """Schema for Task creation, update, and serialization."""

    class Meta:
        unknown = EXCLUDE

    id          = fields.Int(dump_only=True)
    title       = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str(load_default=None)
    status      = fields.Str(
        load_default="todo",
        validate=validate.OneOf(Task.VALID_STATUSES),
    )
    priority    = fields.Str(
        load_default="medium",
        validate=validate.OneOf(Task.VALID_PRIORITIES),
    )
    due_date    = fields.DateTime(load_default=None, allow_none=True)
    assigned_to = fields.Int(load_default=None, allow_none=True)
    project_id  = fields.Int(dump_only=True)
    created_at  = fields.DateTime(dump_only=True)
    updated_at  = fields.DateTime(dump_only=True)


class TaskUpdateSchema(ma.Schema):
    """Schema for partial Task updates — all fields optional."""

    class Meta:
        unknown = EXCLUDE

    title       = fields.Str(validate=validate.Length(min=1, max=200))
    description = fields.Str()
    status      = fields.Str(validate=validate.OneOf(Task.VALID_STATUSES))
    priority    = fields.Str(validate=validate.OneOf(Task.VALID_PRIORITIES))
    due_date    = fields.DateTime(allow_none=True)
    assigned_to = fields.Int(allow_none=True)


# Singleton instances used by route handlers
user_schema        = UserSchema()
login_schema       = LoginSchema()
project_schema     = ProjectSchema()
project_list_schema = ProjectSchema(many=True)
task_schema        = TaskSchema()
task_list_schema   = TaskSchema(many=True)
task_update_schema = TaskUpdateSchema()
