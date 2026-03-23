"""
Pluggable broker backends — implement for Alpaca, IBKR, etc.

All methods use normalized request/response models from `app.schemas.broker`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.schemas.broker import (
    AccountOut,
    OrderListOut,
    OrderOut,
    PlaceOrderRequest,
    PositionListOut,
)


@runtime_checkable
class BrokerAdapter(Protocol):
    name: str

    def get_account(self) -> AccountOut:
        ...

    def list_positions(self) -> PositionListOut:
        ...

    def list_orders(self, *, status: str | None, limit: int) -> OrderListOut:
        ...

    def place_order(self, body: PlaceOrderRequest) -> OrderOut:
        ...

    def close_position(self, symbol: str) -> OrderOut:
        """Close an open position at the broker (e.g. Alpaca `DELETE /v2/positions/{symbol}`)."""
        ...
