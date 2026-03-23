"""Trade order schemas."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal

from pydantic import Field

from app.models.enums import OrderSide, OrderStatus, OrderType, TimeInForce
from app.schemas.common import SchemaBase


class TradeOrderBase(SchemaBase):
    symbol: str = Field(..., min_length=1, max_length=32)
    side: OrderSide
    order_type: OrderType
    quantity: Decimal = Field(..., gt=0)
    limit_price: Decimal | None = Field(None, gt=0)
    stop_price: Decimal | None = Field(None, gt=0)
    time_in_force: TimeInForce | None = None
    paper_trade: bool = True


class TradeOrderCreate(TradeOrderBase):
    client_order_id: str = Field(..., min_length=8, max_length=128)
    broker_connection_id: uuid.UUID | None = None
    recommendation_id: uuid.UUID | None = None


class TradeOrderUpdate(SchemaBase):
    status: OrderStatus | None = None
    filled_quantity: Decimal | None = Field(None, ge=0)
    avg_fill_price: Decimal | None = Field(None, ge=0)
    submitted_at: dt.datetime | None = None
    filled_at: dt.datetime | None = None


class TradeOrderRead(TradeOrderBase):
    id: uuid.UUID
    user_id: uuid.UUID
    broker_connection_id: uuid.UUID | None
    recommendation_id: uuid.UUID | None
    client_order_id: str
    status: OrderStatus
    filled_quantity: Decimal
    avg_fill_price: Decimal | None
    submitted_at: dt.datetime | None
    filled_at: dt.datetime | None
    created_at: dt.datetime
    updated_at: dt.datetime


class TradeOrderListResponse(SchemaBase):
    """Internal paper / broker-routed orders persisted for the user."""

    items: list[TradeOrderRead]
