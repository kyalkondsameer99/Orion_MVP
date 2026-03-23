"""HTTP tests for POST /api/v1/positions/exit and /api/v1/positions/{id}/exit."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import select

from app.api.deps import get_broker_service
from app.broker.service import BrokerService
from app.main import app
from app.models.audit_log import AuditLog
from app.models.enums import PositionSide, PositionStatus
from app.models.position import Position
from app.schemas.broker import OrderListOut, OrderOut, PlaceOrderRequest, PositionListOut


class _FakeBrokerAdapter:
    name = "fake"

    def get_account(self):
        raise NotImplementedError

    def list_positions(self) -> PositionListOut:
        return PositionListOut(positions=[])

    def list_orders(self, *, status: str | None = None, limit: int = 50) -> OrderListOut:
        return OrderListOut(orders=[])

    def place_order(self, body: PlaceOrderRequest) -> OrderOut:
        return OrderOut(
            id="broker-ord-1",
            client_order_id=None,
            symbol=body.symbol,
            side=body.side,
            order_type=body.order_type,
            qty=body.qty,
            status="new",
        )

    def close_position(self, symbol: str) -> OrderOut:
        return OrderOut(
            id="broker-close-1",
            client_order_id=None,
            symbol=symbol.upper(),
            side="sell",
            order_type="market",
            qty=Decimal("1"),
            status="filled",
        )


def test_exit_requires_auth(workflow_client) -> None:
    r = workflow_client.post("/api/v1/positions/exit", json={"symbol": "AAPL"})
    assert r.status_code == 401


def test_exit_by_symbol_closes_internal_row(
    workflow_client,
    workflow_db_session,
    workflow_auth_headers,
    workflow_user_id: uuid.UUID,
) -> None:
    fake = BrokerService(_FakeBrokerAdapter())

    def _broker() -> BrokerService:
        return fake

    app.dependency_overrides[get_broker_service] = _broker
    try:
        pos = Position(
            user_id=workflow_user_id,
            symbol="AAPL",
            side=PositionSide.LONG,
            quantity=Decimal("2"),
            avg_entry_price=Decimal("150"),
            status=PositionStatus.OPEN,
            opened_at=dt.datetime.now(tz=dt.timezone.utc),
        )
        workflow_db_session.add(pos)
        workflow_db_session.commit()
        workflow_db_session.refresh(pos)

        r = workflow_client.post(
            "/api/v1/positions/exit",
            json={"symbol": "aapl"},
            headers=workflow_auth_headers,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["broker_order"]["symbol"] == "AAPL"
        assert data["closed_internal_positions"] == 1

        workflow_db_session.refresh(pos)
        assert pos.status == PositionStatus.CLOSED
        assert pos.closed_at is not None

        logs = workflow_db_session.scalars(
            select(AuditLog).where(AuditLog.user_id == workflow_user_id)
        ).all()
        assert any(x.action == "position.exit_broker" for x in logs)
    finally:
        app.dependency_overrides.pop(get_broker_service, None)


def test_exit_invalid_symbol(
    workflow_client,
    workflow_auth_headers,
) -> None:
    fake = BrokerService(_FakeBrokerAdapter())

    app.dependency_overrides[get_broker_service] = lambda: fake
    try:
        r = workflow_client.post(
            "/api/v1/positions/exit",
            json={"symbol": "!!!"},
            headers=workflow_auth_headers,
        )
        assert r.status_code == 422
    finally:
        app.dependency_overrides.pop(get_broker_service, None)


def test_exit_by_id_not_found(
    workflow_client,
    workflow_auth_headers,
) -> None:
    fake = BrokerService(_FakeBrokerAdapter())
    app.dependency_overrides[get_broker_service] = lambda: fake
    try:
        rid = uuid.uuid4()
        r = workflow_client.post(
            f"/api/v1/positions/{rid}/exit",
            headers=workflow_auth_headers,
        )
        assert r.status_code == 404
    finally:
        app.dependency_overrides.pop(get_broker_service, None)


def test_exit_by_id_success(
    workflow_client,
    workflow_db_session,
    workflow_auth_headers,
    workflow_user_id: uuid.UUID,
) -> None:
    fake = BrokerService(_FakeBrokerAdapter())
    app.dependency_overrides[get_broker_service] = lambda: fake
    try:
        pos = Position(
            user_id=workflow_user_id,
            symbol="MSFT",
            side=PositionSide.LONG,
            quantity=Decimal("1"),
            avg_entry_price=Decimal("300"),
            status=PositionStatus.OPEN,
            opened_at=dt.datetime.now(tz=dt.timezone.utc),
        )
        workflow_db_session.add(pos)
        workflow_db_session.commit()
        workflow_db_session.refresh(pos)

        r = workflow_client.post(
            f"/api/v1/positions/{pos.id}/exit",
            headers=workflow_auth_headers,
        )
        assert r.status_code == 200, r.text
        workflow_db_session.refresh(pos)
        assert pos.status == PositionStatus.CLOSED
    finally:
        app.dependency_overrides.pop(get_broker_service, None)
