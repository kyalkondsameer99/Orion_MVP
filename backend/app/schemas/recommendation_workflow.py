"""Persisted recommendation lifecycle API."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal
from typing import Literal

from pydantic import Field

from app.schemas.common import SchemaBase
from app.schemas.recommendation_engine import RecommendationResponse


class PersistRecommendationRequest(SchemaBase):
    """Store an engine `RecommendationResponse` for user review (status=pending)."""

    symbol: str = Field(..., min_length=1, max_length=32)
    engine: RecommendationResponse
    account_size: Decimal = Field(..., gt=0)
    risk_percent: float = Field(..., ge=0.01, le=100.0)
    quantity: Decimal | None = Field(
        default=None,
        gt=0,
        description="Optional override; otherwise derived from risk and stop distance.",
    )


class RecommendationRecordOut(SchemaBase):
    id: uuid.UUID
    user_id: uuid.UUID
    symbol: str
    status: str
    recommendation_action: str | None
    trade_direction: str | None
    entry_price: Decimal | None
    stop_loss: Decimal | None
    take_profit: Decimal | None
    quantity: Decimal | None
    trade_order_id: uuid.UUID | None
    created_at: dt.datetime
    updated_at: dt.datetime

    # From `engine_snapshot` + model fallbacks — used when hydrating the UI from a saved row.
    confidence: float | None = None
    technical_summary: str | None = None
    news_summary: str | None = None
    reason_summary: str | None = None
    passed_risk_checks: bool | None = None
    reward_risk_ratio: float | None = None


class RecommendationActionResult(SchemaBase):
    recommendation: RecommendationRecordOut
    trade_order_id: uuid.UUID | None = None
    message: str = ""


class RecommendationSubmitResult(SchemaBase):
    recommendation_id: uuid.UUID
    broker_order_id: str | None = None
    message: str = ""


class RecommendationListResponse(SchemaBase):
    """Paginated-style list (limit only for MVP; offset can be added later)."""

    items: list[RecommendationRecordOut]


class PlaceOrderByRecommendationRequest(SchemaBase):
    """Starter-pack alias for `POST /orders/place` → submit approved rec to broker."""

    recommendation_id: uuid.UUID
