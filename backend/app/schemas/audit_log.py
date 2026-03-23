"""Audit log schemas (append-only)."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from pydantic import Field

from app.models.enums import AuditActorType
from app.schemas.common import SchemaBase


class AuditLogCreate(SchemaBase):
    """Ingest path for recording auditable events."""

    user_id: uuid.UUID | None = None
    actor_type: AuditActorType
    action: str = Field(..., min_length=1, max_length=128)
    resource_type: str | None = Field(None, max_length=64)
    resource_id: uuid.UUID | None = None
    payload: dict[str, Any] | None = None
    ip_address: str | None = Field(None, max_length=45)
    user_agent: str | None = Field(None, max_length=512)


class AuditLogRead(SchemaBase):
    id: uuid.UUID
    user_id: uuid.UUID | None
    actor_type: AuditActorType
    action: str
    resource_type: str | None
    resource_id: uuid.UUID | None
    payload: dict[str, Any] | None
    ip_address: str | None
    user_agent: str | None
    created_at: dt.datetime
