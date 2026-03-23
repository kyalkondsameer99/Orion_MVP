"""HTTP tests for recommendation persist / approve / reject / broker submit."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.api.deps import get_recommendation_workflow_service
from app.broker.service import BrokerService
from app.main import app
from app.models.audit_log import AuditLog
from app.models.enums import OrderStatus, RecommendationStatus
from app.models.recommendation import Recommendation
from app.models.recommendation_status_event import RecommendationStatusEvent
from app.models.trade_order import TradeOrder
from app.schemas.broker import OrderListOut, OrderOut, PlaceOrderRequest, PositionListOut
from app.services.recommendation_workflow_service import RecommendationWorkflowService


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


def _persist_payload() -> dict:
    return {
        "symbol": "AAPL",
        "engine": {
            "action": "BUY",
            "direction": "LONG",
            "entry_price": 100.0,
            "stop_loss": 95.0,
            "take_profit": 110.0,
            "confidence": 0.8,
            "technical_summary": "ok",
            "news_summary": "ok",
            "reason_summary": "ok",
        },
        "account_size": "10000.00",
        "risk_percent": 1.0,
    }


def test_list_recommendations_empty(
    workflow_client,
    workflow_auth_headers,
) -> None:
    r = workflow_client.get("/api/v1/recommendations/", headers=workflow_auth_headers)
    assert r.status_code == 200, r.text
    assert r.json() == {"items": []}


def test_list_recommendations_filters_and_includes_trade_order(
    workflow_client,
    workflow_auth_headers,
) -> None:
    pr = workflow_client.post(
        "/api/v1/recommendations/",
        json=_persist_payload(),
        headers=workflow_auth_headers,
    )
    assert pr.status_code == 200, pr.text
    rid = uuid.UUID(pr.json()["recommendation"]["id"])

    r_all = workflow_client.get("/api/v1/recommendations/", headers=workflow_auth_headers)
    assert r_all.status_code == 200
    assert len(r_all.json()["items"]) == 1
    assert r_all.json()["items"][0]["id"] == str(rid)

    r_sym = workflow_client.get(
        "/api/v1/recommendations/",
        params={"symbol": "aapl"},
        headers=workflow_auth_headers,
    )
    assert r_sym.status_code == 200
    assert len(r_sym.json()["items"]) == 1

    r_miss = workflow_client.get(
        "/api/v1/recommendations/",
        params={"symbol": "MSFT"},
        headers=workflow_auth_headers,
    )
    assert r_miss.status_code == 200
    assert r_miss.json()["items"] == []

    r_pending = workflow_client.get(
        "/api/v1/recommendations/",
        params={"status": "pending"},
        headers=workflow_auth_headers,
    )
    assert r_pending.status_code == 200
    assert len(r_pending.json()["items"]) == 1

    workflow_client.post(
        f"/api/v1/recommendations/{rid}/approve",
        headers=workflow_auth_headers,
    )
    r_approved = workflow_client.get(
        "/api/v1/recommendations/",
        params={"status": "approved"},
        headers=workflow_auth_headers,
    )
    assert r_approved.status_code == 200
    items = r_approved.json()["items"]
    assert len(items) == 1
    assert items[0]["trade_order_id"] is not None


def test_persist_creates_pending_status_event_and_audit(
    workflow_client,
    workflow_db_session,
    workflow_auth_headers,
) -> None:
    r = workflow_client.post(
        "/api/v1/recommendations/",
        json=_persist_payload(),
        headers=workflow_auth_headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["recommendation"]["status"] == "pending"
    rid = uuid.UUID(data["recommendation"]["id"])

    ev = workflow_db_session.scalars(
        select(RecommendationStatusEvent).where(RecommendationStatusEvent.recommendation_id == rid)
    ).all()
    assert len(ev) == 1
    assert ev[0].from_status == "none"
    assert ev[0].to_status == "pending"

    logs = workflow_db_session.scalars(select(AuditLog).where(AuditLog.resource_id == rid)).all()
    assert any(x.action == "recommendation.created" for x in logs)


def test_approve_creates_order_and_transition(
    workflow_client,
    workflow_db_session,
    workflow_auth_headers,
) -> None:
    pr = workflow_client.post(
        "/api/v1/recommendations/",
        json=_persist_payload(),
        headers=workflow_auth_headers,
    )
    rid = uuid.UUID(pr.json()["recommendation"]["id"])

    ar = workflow_client.post(
        f"/api/v1/recommendations/{rid}/approve",
        headers=workflow_auth_headers,
    )
    assert ar.status_code == 200, ar.text
    assert ar.json()["trade_order_id"] is not None

    rec = workflow_db_session.get(Recommendation, rid)
    assert rec is not None
    assert rec.status == RecommendationStatus.APPROVED

    orders = workflow_db_session.scalars(select(TradeOrder).where(TradeOrder.recommendation_id == rid)).all()
    assert len(orders) == 1

    ev = workflow_db_session.scalars(
        select(RecommendationStatusEvent).where(RecommendationStatusEvent.recommendation_id == rid)
    ).all()
    assert any(e.from_status == "pending" and e.to_status == "approved" for e in ev)

    logs = workflow_db_session.scalars(select(AuditLog).where(AuditLog.resource_id == rid)).all()
    assert any(x.action == "recommendation.approved" for x in logs)


def test_reject_pending(
    workflow_client,
    workflow_db_session,
    workflow_auth_headers,
) -> None:
    pr = workflow_client.post(
        "/api/v1/recommendations/",
        json=_persist_payload(),
        headers=workflow_auth_headers,
    )
    rid = uuid.UUID(pr.json()["recommendation"]["id"])

    rr = workflow_client.post(
        f"/api/v1/recommendations/{rid}/reject",
        headers=workflow_auth_headers,
    )
    assert rr.status_code == 200, rr.text
    assert rr.json()["recommendation"]["status"] == "rejected"

    rec = workflow_db_session.get(Recommendation, rid)
    assert rec is not None
    assert rec.status == RecommendationStatus.REJECTED

    ev = workflow_db_session.scalars(
        select(RecommendationStatusEvent).where(RecommendationStatusEvent.recommendation_id == rid)
    ).all()
    assert any(e.from_status == "pending" and e.to_status == "rejected" for e in ev)


def test_submit_requires_approved(
    workflow_client,
    workflow_db_session,
    workflow_auth_headers,
) -> None:
    fake_broker = BrokerService(_FakeBrokerAdapter())

    def _svc() -> RecommendationWorkflowService:
        return RecommendationWorkflowService(workflow_db_session, fake_broker)

    app.dependency_overrides[get_recommendation_workflow_service] = _svc
    try:
        pr = workflow_client.post(
            "/api/v1/recommendations/",
            json=_persist_payload(),
            headers=workflow_auth_headers,
        )
        rid = uuid.UUID(pr.json()["recommendation"]["id"])

        sr = workflow_client.post(
            f"/api/v1/recommendations/{rid}/submit",
            headers=workflow_auth_headers,
        )
        assert sr.status_code == 409
    finally:
        app.dependency_overrides.pop(get_recommendation_workflow_service, None)


def test_submit_after_approve_with_mock_broker(
    workflow_client,
    workflow_db_session,
    workflow_auth_headers,
) -> None:
    fake_broker = BrokerService(_FakeBrokerAdapter())

    def _svc() -> RecommendationWorkflowService:
        return RecommendationWorkflowService(workflow_db_session, fake_broker)

    app.dependency_overrides[get_recommendation_workflow_service] = _svc
    try:
        pr = workflow_client.post(
            "/api/v1/recommendations/",
            json=_persist_payload(),
            headers=workflow_auth_headers,
        )
        rid = uuid.UUID(pr.json()["recommendation"]["id"])

        workflow_client.post(
            f"/api/v1/recommendations/{rid}/approve",
            headers=workflow_auth_headers,
        )

        sr = workflow_client.post(
            f"/api/v1/recommendations/{rid}/submit",
            headers=workflow_auth_headers,
        )
        assert sr.status_code == 200, sr.text
        assert sr.json()["broker_order_id"] == "broker-ord-1"

        rec = workflow_db_session.get(Recommendation, rid)
        assert rec is not None
        assert rec.status == RecommendationStatus.SUBMITTED

        orders = workflow_db_session.scalars(select(TradeOrder).where(TradeOrder.recommendation_id == rid)).all()
        assert len(orders) == 1
        assert orders[0].status == OrderStatus.SUBMITTED

        ev = workflow_db_session.scalars(
            select(RecommendationStatusEvent).where(RecommendationStatusEvent.recommendation_id == rid)
        ).all()
        assert any(e.from_status == "approved" and e.to_status == "submitted" for e in ev)

        logs = workflow_db_session.scalars(select(AuditLog).where(AuditLog.resource_id == rid)).all()
        assert any(x.action == "recommendation.submitted_broker" for x in logs)
    finally:
        app.dependency_overrides.pop(get_recommendation_workflow_service, None)
