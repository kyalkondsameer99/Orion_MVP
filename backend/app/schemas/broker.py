"""Broker API contracts (normalized across providers)."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.common import SchemaBase

OrderSide = Literal["buy", "sell"]
OrderType = Literal["market", "limit"]
TimeInForce = Literal["day", "gtc", "ioc", "fok"]


class AccountOut(SchemaBase):
    """Cash / equity snapshot."""

    id: str
    cash: Decimal
    equity: Decimal
    buying_power: Decimal | None = None
    currency: str = "USD"
    account_blocked: bool = False
    trading_blocked: bool = False
    raw: dict | None = Field(default=None, description="Optional upstream payload for debugging.")


class PositionOut(SchemaBase):
    symbol: str
    qty: Decimal
    side: Literal["long", "short"]
    avg_entry_price: Decimal
    market_value: Decimal | None = None
    cost_basis: Decimal | None = None
    unrealized_pl: Decimal | None = None
    asset_class: str | None = None


class PositionListOut(SchemaBase):
    positions: list[PositionOut]


class PlaceOrderRequest(SchemaBase):
    symbol: str = Field(..., min_length=1, max_length=32)
    side: OrderSide
    order_type: OrderType
    qty: Decimal = Field(..., gt=0)
    time_in_force: TimeInForce = "day"
    limit_price: Decimal | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_limit_price(self) -> PlaceOrderRequest:
        if self.order_type == "limit" and self.limit_price is None:
            raise ValueError("limit_price is required when order_type is 'limit'")
        if self.order_type == "market" and self.limit_price is not None:
            raise ValueError("limit_price must be omitted for market orders")
        return self


class OrderOut(SchemaBase):
    id: str
    client_order_id: str | None = None
    symbol: str
    side: OrderSide
    order_type: str
    qty: Decimal
    filled_qty: Decimal = Decimal("0")
    status: str
    submitted_at: dt.datetime | None = None
    filled_avg_price: Decimal | None = None
    limit_price: Decimal | None = None
    raw: dict | None = None


class OrderListOut(SchemaBase):
    orders: list[OrderOut]
