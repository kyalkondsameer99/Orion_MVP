"""HTTP tests for internal GET /api/v1/orders/."""

from __future__ import annotations

import uuid

from app.models.enums import OrderStatus
from app.models.trade_order import TradeOrder


def test_orders_requires_auth(workflow_client) -> None:
    r = workflow_client.get("/api/v1/orders/")
    assert r.status_code == 401


def test_orders_empty_then_after_approve(
    workflow_client,
    workflow_db_session,
    workflow_auth_headers,
) -> None:
    empty = workflow_client.get("/api/v1/orders/", headers=workflow_auth_headers)
    assert empty.status_code == 200
    assert empty.json() == {"items": []}

    payload = {
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
    pr = workflow_client.post("/api/v1/recommendations/", json=payload, headers=workflow_auth_headers)
    assert pr.status_code == 200, pr.text
    rid = uuid.UUID(pr.json()["recommendation"]["id"])

    ar = workflow_client.post(
        f"/api/v1/recommendations/{rid}/approve",
        headers=workflow_auth_headers,
    )
    assert ar.status_code == 200, ar.text

    listed = workflow_client.get("/api/v1/orders/", headers=workflow_auth_headers)
    assert listed.status_code == 200
    data = listed.json()["items"]
    assert len(data) == 1
    assert data[0]["symbol"] == "AAPL"
    assert data[0]["recommendation_id"] == str(rid)
    assert data[0]["side"] == "buy"

    oid = uuid.UUID(data[0]["id"])
    row = workflow_db_session.get(TradeOrder, oid)
    assert row is not None
    assert row.status == OrderStatus.NEW

    filtered = workflow_client.get(
        "/api/v1/orders/",
        params={"symbol": "aapl"},
        headers=workflow_auth_headers,
    )
    assert filtered.status_code == 200
    assert len(filtered.json()["items"]) == 1

    st = workflow_client.get(
        "/api/v1/orders/",
        params={"status": "new"},
        headers=workflow_auth_headers,
    )
    assert st.status_code == 200
    assert len(st.json()["items"]) == 1
    assert st.json()["items"][0]["id"] == str(oid)


def test_orders_symbol_filter_invalid(
    workflow_client,
    workflow_auth_headers,
) -> None:
    r = workflow_client.get(
        "/api/v1/orders/",
        params={"symbol": "!!!"},
        headers=workflow_auth_headers,
    )
    assert r.status_code == 422
