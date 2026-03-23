"""User request/response models."""

from __future__ import annotations

import datetime as dt
import uuid

from pydantic import EmailStr, Field

from app.schemas.common import SchemaBase


class UserBase(SchemaBase):
    email: EmailStr
    full_name: str | None = None
    is_active: bool = True
    is_verified: bool = False


class UserCreate(UserBase):
    """Registration payload — hash `password` before persisting."""

    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(SchemaBase):
    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = Field(None, min_length=8, max_length=128)
    is_active: bool | None = None
    is_verified: bool | None = None


class UserInDB(UserBase):
    id: uuid.UUID
    hashed_password: str | None = None
    created_at: dt.datetime
    updated_at: dt.datetime


class UserRead(SchemaBase):
    """Public user shape — never include `hashed_password`."""

    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    is_active: bool
    is_verified: bool
    created_at: dt.datetime
    updated_at: dt.datetime
