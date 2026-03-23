"""HTTP tests for `/api/v1/watchlist` endpoints."""

from __future__ import annotations

from urllib.parse import quote

from fastapi.testclient import TestClient


API_PREFIX = "/api/v1/watchlist"


def test_list_watchlist_empty(client: TestClient, auth_headers: dict[str, str]) -> None:
    r = client.get(API_PREFIX, headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {"items": []}


def test_add_and_list_watchlist(client: TestClient, auth_headers: dict[str, str]) -> None:
    payload = {"symbol": "aapl", "sort_order": 1, "notes": "tech"}
    r = client.post(API_PREFIX, json=payload, headers=auth_headers)
    assert r.status_code == 201
    body = r.json()
    assert body["symbol"] == "AAPL"
    assert body["notes"] == "tech"
    assert body["sort_order"] == 1
    assert "id" in body

    r2 = client.get(API_PREFIX, headers=auth_headers)
    assert r2.status_code == 200
    data = r2.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["symbol"] == "AAPL"


def test_add_duplicate_returns_409(client: TestClient, auth_headers: dict[str, str]) -> None:
    client.post(API_PREFIX, json={"symbol": "MSFT"}, headers=auth_headers)
    r = client.post(API_PREFIX, json={"symbol": "msft"}, headers=auth_headers)
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "symbol_already_exists"


def test_delete_watchlist_item(client: TestClient, auth_headers: dict[str, str]) -> None:
    client.post(API_PREFIX, json={"symbol": "NVDA"}, headers=auth_headers)
    r = client.delete(f"{API_PREFIX}/NVDA", headers=auth_headers)
    assert r.status_code == 204
    assert r.content == b""

    listed = client.get(API_PREFIX, headers=auth_headers).json()
    assert listed["items"] == []


def test_delete_not_found_returns_404(client: TestClient, auth_headers: dict[str, str]) -> None:
    r = client.delete(f"{API_PREFIX}/META", headers=auth_headers)
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "symbol_not_found"


def test_invalid_symbol_post_returns_422(client: TestClient, auth_headers: dict[str, str]) -> None:
    r = client.post(API_PREFIX, json={"symbol": "BAD@SYM"}, headers=auth_headers)
    assert r.status_code == 422


def test_missing_user_header_returns_401(client: TestClient) -> None:
    r = client.get(API_PREFIX)
    assert r.status_code == 401


def test_invalid_user_header_returns_400(client: TestClient) -> None:
    r = client.get(API_PREFIX, headers={"X-User-Id": "not-a-uuid"})
    assert r.status_code == 400


def test_delete_index_style_symbol(client: TestClient, auth_headers: dict[str, str]) -> None:
    sym = "^GSPC"
    client.post(API_PREFIX, json={"symbol": sym}, headers=auth_headers)
    path = f"{API_PREFIX}/{quote(sym, safe='')}"
    r = client.delete(path, headers=auth_headers)
    assert r.status_code == 204
