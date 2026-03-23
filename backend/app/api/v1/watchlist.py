"""Watchlist HTTP API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user_id, get_watchlist_service
from app.schemas.watchlist_item import WatchlistItemCreate, WatchlistItemRead, WatchlistListResponse
from app.services.watchlist_service import WatchlistService

router = APIRouter()


@router.get(
    "",
    response_model=WatchlistListResponse,
    summary="List watchlist symbols",
)
def list_watchlist(
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: WatchlistService = Depends(get_watchlist_service),
) -> WatchlistListResponse:
    return service.list_items(user_id)


@router.post(
    "",
    response_model=WatchlistItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a symbol to the watchlist",
)
def add_watchlist_item(
    body: WatchlistItemCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: WatchlistService = Depends(get_watchlist_service),
) -> WatchlistItemRead:
    return service.add_item(user_id, body)


@router.delete(
    "/{symbol}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Remove a symbol from the watchlist",
)
def remove_watchlist_item(
    symbol: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: WatchlistService = Depends(get_watchlist_service),
) -> None:
    service.remove_item(user_id, symbol)
