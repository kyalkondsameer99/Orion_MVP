"""Recommendation (copilot) schemas."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal

from pydantic import Field

from app.models.enums import OrderSide, RecommendationSource, RecommendationStatus
from app.schemas.common import SchemaBase


class RecommendationBase(SchemaBase):
    symbol: str = Field(..., min_length=1, max_length=32)
    side: OrderSide
    confidence: Decimal = Field(..., ge=0, le=1)
    rationale: str | None = None
    status: RecommendationStatus = RecommendationStatus.PENDING
    source: RecommendationSource
    recommended_at: dt.datetime
    expires_at: dt.datetime | None = None


class RecommendationCreate(RecommendationBase):
    watchlist_item_id: uuid.UUID | None = None


class RecommendationUpdate(SchemaBase):
    status: RecommendationStatus | None = None
    rationale: str | None = None
    expires_at: dt.datetime | None = None


class RecommendationRead(RecommendationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    watchlist_item_id: uuid.UUID | None
    created_at: dt.datetime
    updated_at: dt.datetime
