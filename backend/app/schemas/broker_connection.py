"""Broker connection schemas."""

from __future__ import annotations

import datetime as dt
import uuid

from pydantic import Field

from app.models.enums import BrokerProvider, ConnectionStatus
from app.schemas.common import SchemaBase


class BrokerConnectionBase(SchemaBase):
    provider: BrokerProvider
    external_account_id: str | None = Field(None, max_length=128)
    display_name: str | None = Field(None, max_length=255)
    is_paper: bool = True
    credential_secret_ref: str | None = Field(None, max_length=512)


class BrokerConnectionCreate(BrokerConnectionBase):
    pass


class BrokerConnectionUpdate(SchemaBase):
    external_account_id: str | None = Field(None, max_length=128)
    display_name: str | None = Field(None, max_length=255)
    is_paper: bool | None = None
    credential_secret_ref: str | None = Field(None, max_length=512)
    status: ConnectionStatus | None = None
    last_error: str | None = None
    last_sync_at: dt.datetime | None = None


class BrokerConnectionRead(SchemaBase):
    """
    API response shape — omit raw secret material; `credential_secret_ref` is internal-only.
    """

    id: uuid.UUID
    user_id: uuid.UUID
    provider: BrokerProvider
    external_account_id: str | None
    display_name: str | None
    is_paper: bool
    status: ConnectionStatus
    last_error: str | None
    last_sync_at: dt.datetime | None
    created_at: dt.datetime
    updated_at: dt.datetime
