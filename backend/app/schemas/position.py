"""Position schemas."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal

from pydantic import Field

from app.models.enums import PositionSide, PositionStatus
from app.schemas.broker import OrderOut
from app.schemas.common import SchemaBase


class PositionBase(SchemaBase):
    symbol: str = Field(..., min_length=1, max_length=32)
    side: PositionSide
    quantity: Decimal = Field(..., gt=0)
    avg_entry_price: Decimal = Field(..., gt=0)
    unrealized_pnl: Decimal | None = None
    realized_pnl: Decimal | None = None
    status: PositionStatus = PositionStatus.OPEN
    opened_at: dt.datetime
    closed_at: dt.datetime | None = None


class PositionCreate(PositionBase):
    broker_connection_id: uuid.UUID | None = None
    opening_trade_order_id: uuid.UUID | None = None


class PositionUpdate(SchemaBase):
    quantity: Decimal | None = Field(None, gt=0)
    avg_entry_price: Decimal | None = Field(None, gt=0)
    unrealized_pnl: Decimal | None = None
    realized_pnl: Decimal | None = None
    status: PositionStatus | None = None
    closed_at: dt.datetime | None = None


class PositionRead(PositionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    broker_connection_id: uuid.UUID | None
    opening_trade_order_id: uuid.UUID | None
    created_at: dt.datetime
    updated_at: dt.datetime


class PositionExitRequest(SchemaBase):
    """Close a broker-held position for this symbol (Alpaca: DELETE /v2/positions/{symbol})."""

    symbol: str = Field(..., min_length=1, max_length=32)


class PositionExitResponse(SchemaBase):
    broker_order: OrderOut
    closed_internal_positions: int = 0
    message: str = ""
