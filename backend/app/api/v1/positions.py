"""Open positions (broker list) + paper exit — closes at Alpaca + optional DB rows."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_broker_service, get_current_user_id, get_db, require_trading_enabled
from app.broker.errors import BrokerAPIError
from app.broker.service import BrokerService
from app.schemas.broker import PositionListOut
from app.schemas.position import PositionExitRequest, PositionExitResponse
from app.services.position_exit_service import (
    exit_paper_position_by_id,
    exit_paper_position_by_symbol,
)


def _map_broker_error(exc: BrokerAPIError) -> HTTPException:
    code = exc.status_code
    if code in (401, 403, 404, 422, 429):
        return HTTPException(status_code=code, detail=str(exc))
    if 400 <= code < 500:
        return HTTPException(status_code=code, detail=str(exc))
    return HTTPException(status_code=502, detail=str(exc))


router = APIRouter()


@router.get(
    "/",
    response_model=PositionListOut,
    summary="Open positions at broker (starter-pack alias for GET /positions)",
)
def list_open_positions_broker(
    service: Annotated[BrokerService, Depends(get_broker_service)],
) -> PositionListOut:
    try:
        return service.list_positions()
    except BrokerAPIError as e:
        raise _map_broker_error(e) from e


@router.post(
    "/exit",
    response_model=PositionExitResponse,
    summary="Close an open position at the broker (by symbol)",
)
def exit_position_by_symbol(
    body: PositionExitRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
    broker: Annotated[BrokerService, Depends(get_broker_service)],
    _: Annotated[None, Depends(require_trading_enabled)],
) -> PositionExitResponse:
    return exit_paper_position_by_symbol(db, user_id=user_id, body=body, broker=broker)


@router.post(
    "/{position_id}/exit",
    response_model=PositionExitResponse,
    summary="Close by internal position id (uses stored symbol at broker)",
)
def exit_position_by_id(
    position_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
    broker: Annotated[BrokerService, Depends(get_broker_service)],
    _: Annotated[None, Depends(require_trading_enabled)],
) -> PositionExitResponse:
    return exit_paper_position_by_id(db, user_id=user_id, position_id=position_id, broker=broker)
