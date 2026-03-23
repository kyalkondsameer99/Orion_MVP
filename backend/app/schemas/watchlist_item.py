"""Watchlist item schemas."""

from __future__ import annotations

import datetime as dt
import uuid

from pydantic import Field, field_validator

from app.core.symbols import InvalidSymbolError, normalize_symbol
from app.schemas.common import SchemaBase


class WatchlistItemBase(SchemaBase):
    symbol: str = Field(..., min_length=1, max_length=32)
    sort_order: int = 0
    notes: str | None = None

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, value: str) -> str:
        try:
            return normalize_symbol(value)
        except InvalidSymbolError as e:
            raise ValueError(str(e)) from e


class WatchlistItemCreate(WatchlistItemBase):
    pass


class WatchlistItemUpdate(SchemaBase):
    symbol: str | None = Field(None, min_length=1, max_length=32)
    sort_order: int | None = None
    notes: str | None = None

    @field_validator("symbol")
    @classmethod
    def validate_symbol_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return normalize_symbol(value)
        except InvalidSymbolError as e:
            raise ValueError(str(e)) from e


class WatchlistItemRead(WatchlistItemBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: dt.datetime
    updated_at: dt.datetime


class WatchlistListResponse(SchemaBase):
    """Envelope for stable list JSON (`{ "items": [...] }`)."""

    items: list[WatchlistItemRead]
