"""Broker (Alpaca paper) HTTP API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_broker_service, require_trading_enabled
from app.broker.errors import BrokerAPIError
from app.broker.service import BrokerService
from app.schemas.broker import (
    AccountOut,
    OrderListOut,
    OrderOut,
    PlaceOrderRequest,
    PositionListOut,
)

router = APIRouter()


def _map_broker_error(exc: BrokerAPIError) -> HTTPException:
    code = exc.status_code
    if code in (401, 403, 404, 422, 429):
        return HTTPException(status_code=code, detail=str(exc))
    if 400 <= code < 500:
        return HTTPException(status_code=code, detail=str(exc))
    return HTTPException(status_code=502, detail=str(exc))


@router.get("/account", response_model=AccountOut, summary="Alpaca account (paper)")
def broker_account(
    service: Annotated[BrokerService, Depends(get_broker_service)],
) -> AccountOut:
    try:
        return service.get_account()
    except BrokerAPIError as e:
        raise _map_broker_error(e) from e


@router.get("/positions", response_model=PositionListOut, summary="Open positions")
def broker_positions(
    service: Annotated[BrokerService, Depends(get_broker_service)],
) -> PositionListOut:
    try:
        return service.list_positions()
    except BrokerAPIError as e:
        raise _map_broker_error(e) from e


@router.get("/orders", response_model=OrderListOut, summary="Order history")
def broker_orders(
    service: Annotated[BrokerService, Depends(get_broker_service)],
    status: str | None = Query(
        default="all",
        description="Alpaca filter: open, closed, or all.",
    ),
    limit: int = Query(default=50, ge=1, le=500),
) -> OrderListOut:
    try:
        return service.list_orders(status=status, limit=limit)
    except BrokerAPIError as e:
        raise _map_broker_error(e) from e


@router.post("/orders", response_model=OrderOut, summary="Place a market or limit order")
def broker_place_order(
    body: PlaceOrderRequest,
    service: Annotated[BrokerService, Depends(get_broker_service)],
    _: Annotated[None, Depends(require_trading_enabled)],
) -> OrderOut:
    try:
        return service.place_order(body)
    except BrokerAPIError as e:
        raise _map_broker_error(e) from e
