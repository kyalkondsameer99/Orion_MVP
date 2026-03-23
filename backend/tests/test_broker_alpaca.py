"""Alpaca paper broker adapter tests with mocked HTTP responses."""

from __future__ import annotations

from decimal import Decimal

import httpx
import pytest

from app.broker.adapters.alpaca import AlpacaPaperBrokerAdapter
from app.broker.errors import BrokerAPIError
from app.schemas.broker import PlaceOrderRequest


_ACCOUNT_JSON = {
    "id": "test-account",
    "cash": "100000.12",
    "equity": "100250.50",
    "buying_power": "200000",
    "currency": "USD",
    "account_blocked": False,
    "trading_blocked": False,
}

_POSITIONS_JSON = [
    {
        "asset_class": "us_equity",
        "symbol": "AAPL",
        "qty": "10",
        "side": "long",
        "avg_entry_price": "150",
        "market_value": "1600",
        "cost_basis": "1500",
        "unrealized_pl": "100",
    }
]

_ORDERS_JSON = [
    {
        "id": "ord-1",
        "client_order_id": "cli-1",
        "symbol": "AAPL",
        "qty": "1",
        "filled_qty": "1",
        "side": "buy",
        "type": "market",
        "status": "filled",
        "filled_avg_price": "150.2",
        "limit_price": None,
        "created_at": "2024-01-01T12:00:00Z",
    }
]

_ORDER_CREATE_RESP = {
    "id": "ord-2",
    "client_order_id": "cli-2",
    "symbol": "MSFT",
    "qty": "2",
    "filled_qty": "0",
    "side": "buy",
    "type": "limit",
    "status": "new",
    "limit_price": "300",
    "created_at": "2024-01-02T12:00:00Z",
}

_CLOSE_POSITION_RESP = {
    "id": "ord-close",
    "client_order_id": "cli-close",
    "symbol": "AAPL",
    "qty": "10",
    "filled_qty": "10",
    "side": "sell",
    "type": "market",
    "status": "filled",
    "filled_avg_price": "175",
    "created_at": "2024-01-03T12:00:00Z",
}


def _make_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/v2/account" and request.method == "GET":
            return httpx.Response(200, json=_ACCOUNT_JSON)
        if path == "/v2/positions" and request.method == "GET":
            return httpx.Response(200, json=_POSITIONS_JSON)
        if path == "/v2/orders" and request.method == "GET":
            return httpx.Response(200, json=_ORDERS_JSON)
        if path == "/v2/orders" and request.method == "POST":
            return httpx.Response(200, json=_ORDER_CREATE_RESP)
        if request.method == "DELETE" and path.startswith("/v2/positions/"):
            return httpx.Response(200, json=_CLOSE_POSITION_RESP)
        if path == "/v2/boom" and request.method == "GET":
            return httpx.Response(401, json={"message": "unauthorized"})
        return httpx.Response(404, text="not found")

    return httpx.MockTransport(handler)


@pytest.fixture
def adapter() -> AlpacaPaperBrokerAdapter:
    client = httpx.Client(transport=_make_transport())
    return AlpacaPaperBrokerAdapter("key-id", "secret", client=client)


def test_get_account_maps_fields(adapter: AlpacaPaperBrokerAdapter) -> None:
    acct = adapter.get_account()
    assert acct.id == "test-account"
    assert acct.cash == Decimal("100000.12")
    assert acct.equity == Decimal("100250.50")
    assert acct.buying_power == Decimal("200000")


def test_list_positions(adapter: AlpacaPaperBrokerAdapter) -> None:
    out = adapter.list_positions()
    assert len(out.positions) == 1
    p = out.positions[0]
    assert p.symbol == "AAPL"
    assert p.qty == Decimal("10")
    assert p.side == "long"


def test_list_orders(adapter: AlpacaPaperBrokerAdapter) -> None:
    out = adapter.list_orders(status="all", limit=10)
    assert len(out.orders) == 1
    assert out.orders[0].status == "filled"


def test_close_position(adapter: AlpacaPaperBrokerAdapter) -> None:
    o = adapter.close_position("AAPL")
    assert o.symbol == "AAPL"
    assert o.side == "sell"
    assert o.status == "filled"


def test_place_limit_order(adapter: AlpacaPaperBrokerAdapter) -> None:
    body = PlaceOrderRequest(
        symbol="MSFT",
        side="buy",
        order_type="limit",
        qty=Decimal("2"),
        limit_price=Decimal("300"),
    )
    o = adapter.place_order(body)
    assert o.symbol == "MSFT"
    assert o.order_type == "limit"
    assert o.status == "new"


def test_http_error_raises_broker_api_error() -> None:
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(401, json={"message": "bad"})))
    ad = AlpacaPaperBrokerAdapter("k", "s", client=client)
    with pytest.raises(BrokerAPIError) as ei:
        ad.get_account()
    assert ei.value.status_code == 401
