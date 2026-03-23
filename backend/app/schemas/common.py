"""Shared Pydantic configuration for API models."""

from pydantic import BaseModel, ConfigDict


class SchemaBase(BaseModel):
    """Enable ORM mode for SQLAlchemy model conversion."""

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
