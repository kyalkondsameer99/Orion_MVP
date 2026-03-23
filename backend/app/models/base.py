"""Declarative base for SQLAlchemy models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Subclass this for all ORM models (Alembic imports `Base.metadata`)."""

    pass
