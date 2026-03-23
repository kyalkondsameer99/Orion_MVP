"""Watchlist use-cases — validation, orchestration, HTTP-friendly errors."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.symbols import InvalidSymbolError, normalize_symbol
from app.repositories.watchlist_repository import WatchlistRepository
from app.schemas.watchlist_item import WatchlistItemCreate, WatchlistItemRead
from app.schemas.watchlist_item import WatchlistListResponse


class WatchlistService:
    """Business logic for listing, adding, and removing watchlist symbols."""

    def __init__(self, session: Session) -> None:
        self._repo = WatchlistRepository(session)

    def list_items(self, user_id: uuid.UUID) -> WatchlistListResponse:
        rows = self._repo.list_for_user(user_id)
        return WatchlistListResponse(
            items=[WatchlistItemRead.model_validate(r) for r in rows],
        )

    def add_item(self, user_id: uuid.UUID, body: WatchlistItemCreate) -> WatchlistItemRead:
        # `WatchlistItemCreate` validates / normalizes `symbol` via Pydantic.
        symbol = body.symbol

        if self._repo.get_by_user_and_symbol(user_id, symbol):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "symbol_already_exists", "symbol": symbol},
            )

        try:
            row = self._repo.create(
                user_id=user_id,
                symbol=symbol,
                sort_order=body.sort_order,
                notes=body.notes,
            )
        except IntegrityError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "symbol_already_exists", "symbol": symbol},
            ) from e

        return WatchlistItemRead.model_validate(row)

    def remove_item(self, user_id: uuid.UUID, symbol_raw: str) -> None:
        try:
            symbol = normalize_symbol(symbol_raw)
        except InvalidSymbolError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            ) from e

        deleted = self._repo.delete_by_user_and_symbol(user_id, symbol)
        if deleted == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "symbol_not_found", "symbol": symbol},
            )
