"""Application service over a `BrokerAdapter` (thin façade for routes)."""

from __future__ import annotations

from app.broker.adapters.base import BrokerAdapter
from app.schemas.broker import (
    AccountOut,
    OrderListOut,
    OrderOut,
    PlaceOrderRequest,
    PositionListOut,
)


class BrokerService:
    def __init__(self, adapter: BrokerAdapter) -> None:
        self._adapter = adapter

    def get_account(self) -> AccountOut:
        return self._adapter.get_account()

    def list_positions(self) -> PositionListOut:
        return self._adapter.list_positions()

    def list_orders(self, *, status: str | None = None, limit: int = 50) -> OrderListOut:
        return self._adapter.list_orders(status=status, limit=limit)

    def place_order(self, body: PlaceOrderRequest) -> OrderOut:
        return self._adapter.place_order(body)

    def close_position(self, symbol: str) -> OrderOut:
        return self._adapter.close_position(symbol)
