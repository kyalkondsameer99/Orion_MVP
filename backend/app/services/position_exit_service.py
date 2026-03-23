"""Close paper positions at the broker and reconcile internal `positions` rows."""

from __future__ import annotations

import datetime as dt
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.broker.errors import BrokerAPIError
from app.broker.service import BrokerService
from app.core.symbols import InvalidSymbolError, normalize_symbol
from app.models.audit_log import AuditLog
from app.models.enums import AuditActorType, PositionStatus
from app.models.position import Position
from app.schemas.broker import OrderOut
from app.schemas.position import PositionExitRequest, PositionExitResponse


def _audit_exit(
    db: Session,
    *,
    user_id: uuid.UUID,
    symbol: str,
    broker_order: OrderOut,
    internal_closed: int,
    position_id: uuid.UUID | None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            actor_type=AuditActorType.USER,
            action="position.exit_broker",
            resource_type="position",
            resource_id=position_id,
            payload={
                "symbol": symbol,
                "broker_order_id": broker_order.id,
                "internal_rows_closed": internal_closed,
            },
        )
    )


def _close_internal_open_rows(
    db: Session,
    *,
    user_id: uuid.UUID,
    symbol: str,
) -> tuple[int, uuid.UUID | None]:
    stmt = select(Position).where(
        Position.user_id == user_id,
        Position.symbol == symbol,
        Position.status == PositionStatus.OPEN,
    )
    rows = list(db.scalars(stmt).all())
    first_id = rows[0].id if rows else None
    now = dt.datetime.now(tz=dt.timezone.utc)
    for p in rows:
        p.status = PositionStatus.CLOSED
        p.closed_at = now
    return len(rows), first_id


def exit_paper_position_by_symbol(
    db: Session,
    *,
    user_id: uuid.UUID,
    body: PositionExitRequest,
    broker: BrokerService,
) -> PositionExitResponse:
    try:
        sym = normalize_symbol(body.symbol)
    except InvalidSymbolError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    try:
        broker_order = broker.close_position(sym)
    except BrokerAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        ) from e

    n, first_id = _close_internal_open_rows(db, user_id=user_id, symbol=sym)
    _audit_exit(
        db,
        user_id=user_id,
        symbol=sym,
        broker_order=broker_order,
        internal_closed=n,
        position_id=first_id,
    )
    db.commit()
    msg = (
        "Position closed at broker; internal rows updated."
        if n
        else "Position closed at broker."
    )
    return PositionExitResponse(
        broker_order=broker_order,
        closed_internal_positions=n,
        message=msg,
    )


def exit_paper_position_by_id(
    db: Session,
    *,
    user_id: uuid.UUID,
    position_id: uuid.UUID,
    broker: BrokerService,
) -> PositionExitResponse:
    pos = db.get(Position, position_id)
    if pos is None or pos.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found")
    if pos.status != PositionStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Position is not open",
        )
    return exit_paper_position_by_symbol(
        db,
        user_id=user_id,
        body=PositionExitRequest(symbol=pos.symbol),
        broker=broker,
    )
