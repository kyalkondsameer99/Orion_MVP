"""Alpaca Paper Trading REST adapter (`httpx`, sync)."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any
from urllib.parse import quote

import httpx

from app.broker.errors import BrokerAPIError
from app.schemas.broker import (
    AccountOut,
    OrderListOut,
    OrderOut,
    PlaceOrderRequest,
    PositionListOut,
    PositionOut,
)


def _parse_dt(value: Any) -> dt.datetime | None:
    if value is None:
        return None
    if isinstance(value, dt.datetime):
        return value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)
    if isinstance(value, str):
        s = value.replace("Z", "+00:00")
        try:
            parsed = dt.datetime.fromisoformat(s)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed
    return None


def _dec(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def _msg_from_response(resp: httpx.Response) -> str:
    try:
        data = resp.json()
        if isinstance(data, dict) and data.get("message"):
            return str(data["message"])[:800]
    except Exception:
        pass
    return (resp.text or resp.reason_phrase or "broker error")[:800]


class AlpacaPaperBrokerAdapter:
    """Talks to `https://paper-api.alpaca.markets` (or override base URL)."""

    name = "alpaca_paper"

    def __init__(
        self,
        api_key_id: str,
        api_secret_key: str,
        *,
        base_url: str = "https://paper-api.alpaca.markets",
        client: httpx.Client | None = None,
    ) -> None:
        self._key_id = api_key_id
        self._secret = api_secret_key
        self._base = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=30.0)

    def close(self) -> None:
        self._client.close()

    def _headers(self) -> dict[str, str]:
        return {
            "APCA-API-KEY-ID": self._key_id,
            "APCA-API-SECRET-KEY": self._secret,
        }

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self._base}{path}"

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            r = self._client.request(method, self._url(path), headers=self._headers(), **kwargs)
        except httpx.HTTPError as e:
            raise BrokerAPIError(503, f"Broker transport error: {e}") from e
        if r.status_code >= 400:
            raise BrokerAPIError(r.status_code, _msg_from_response(r), body=r.text)
        return r

    def get_account(self) -> AccountOut:
        r = self._request("GET", "/v2/account")
        data = r.json()
        return AccountOut(
            id=str(data.get("id", "")),
            cash=_dec(data.get("cash")),
            equity=_dec(data.get("equity")),
            buying_power=_dec(data["buying_power"]) if data.get("buying_power") is not None else None,
            currency=str(data.get("currency") or "USD"),
            account_blocked=bool(data.get("account_blocked")),
            trading_blocked=bool(data.get("trading_blocked")),
            raw=data if isinstance(data, dict) else None,
        )

    def list_positions(self) -> PositionListOut:
        r = self._request("GET", "/v2/positions")
        rows = r.json()
        if not isinstance(rows, list):
            rows = []
        positions: list[PositionOut] = []
        for p in rows:
            if not isinstance(p, dict):
                continue
            qty = _dec(p.get("qty"))
            side = str(p.get("side") or "long").lower()
            if side not in {"long", "short"}:
                side = "long"
            positions.append(
                PositionOut(
                    symbol=str(p.get("symbol", "")),
                    qty=abs(qty),
                    side=side,  # type: ignore[arg-type]
                    avg_entry_price=_dec(p.get("avg_entry_price")),
                    market_value=_dec(p["market_value"]) if p.get("market_value") is not None else None,
                    cost_basis=_dec(p["cost_basis"]) if p.get("cost_basis") is not None else None,
                    unrealized_pl=_dec(p["unrealized_pl"]) if p.get("unrealized_pl") is not None else None,
                    asset_class=str(p["asset_class"]) if p.get("asset_class") else None,
                )
            )
        return PositionListOut(positions=positions)

    def list_orders(self, *, status: str | None, limit: int) -> OrderListOut:
        params: dict[str, Any] = {
            "limit": max(1, min(limit, 500)),
            "direction": "desc",
        }
        if status:
            params["status"] = status
        r = self._request("GET", "/v2/orders", params=params)
        rows = r.json()
        if not isinstance(rows, list):
            rows = []
        orders = [_map_order(o) for o in rows if isinstance(o, dict)]
        return OrderListOut(orders=orders)

    def place_order(self, body: PlaceOrderRequest) -> OrderOut:
        if body.order_type == "limit" and body.limit_price is None:
            raise BrokerAPIError(400, "limit_price is required for limit orders")
        if body.order_type == "market" and body.limit_price is not None:
            raise BrokerAPIError(400, "limit_price must be omitted for market orders")

        payload: dict[str, Any] = {
            "symbol": body.symbol.upper(),
            "qty": str(body.qty),
            "side": body.side,
            "type": body.order_type,
            "time_in_force": body.time_in_force,
        }
        if body.order_type == "limit" and body.limit_price is not None:
            payload["limit_price"] = str(body.limit_price)

        r = self._request("POST", "/v2/orders", json=payload)
        data = r.json()
        if not isinstance(data, dict):
            raise BrokerAPIError(502, "Unexpected broker response")
        return _map_order(data)

    def close_position(self, symbol: str) -> OrderOut:
        sym = symbol.strip().upper()
        path = f"/v2/positions/{quote(sym, safe='.^-')}"
        r = self._request("DELETE", path)
        data = r.json()
        if not isinstance(data, dict):
            raise BrokerAPIError(502, "Unexpected broker response when closing position")
        return _map_order(data)


def _map_order(data: dict[str, Any]) -> OrderOut:
    submitted = (
        _parse_dt(data.get("submitted_at"))
        or _parse_dt(data.get("created_at"))
        or _parse_dt(data.get("updated_at"))
    )
    return OrderOut(
        id=str(data.get("id", "")),
        client_order_id=str(data["client_order_id"]) if data.get("client_order_id") else None,
        symbol=str(data.get("symbol", "")),
        side=str(data.get("side", "buy")).lower(),  # type: ignore[arg-type]
        order_type=str(data.get("type", "market")),
        qty=_dec(data.get("qty")),
        filled_qty=_dec(data.get("filled_qty")),
        status=str(data.get("status", "new")),
        submitted_at=submitted,
        filled_avg_price=_dec(data["filled_avg_price"]) if data.get("filled_avg_price") is not None else None,
        limit_price=_dec(data["limit_price"]) if data.get("limit_price") is not None else None,
        raw=data,
    )
