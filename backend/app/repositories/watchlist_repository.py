"""Persistence for `WatchlistItem` rows."""

from __future__ import annotations

import uuid

from sqlalchemy import Select, delete, select
from sqlalchemy.orm import Session

from app.models.user import User as _User  # noqa: F401 — ensure `users` table exists for FKs
from app.models.watchlist_item import WatchlistItem


class WatchlistRepository:
    """Repository-style API over SQLAlchemy for watchlist CRUD."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_user(self, user_id: uuid.UUID) -> list[WatchlistItem]:
        stmt: Select[tuple[WatchlistItem]] = (
            select(WatchlistItem)
            .where(WatchlistItem.user_id == user_id)
            .order_by(WatchlistItem.sort_order.asc(), WatchlistItem.symbol.asc())
        )
        return list(self._session.scalars(stmt).all())

    def get_by_user_and_symbol(self, user_id: uuid.UUID, symbol: str) -> WatchlistItem | None:
        stmt = select(WatchlistItem).where(
            WatchlistItem.user_id == user_id,
            WatchlistItem.symbol == symbol,
        )
        return self._session.scalars(stmt).first()

    def create(
        self,
        *,
        user_id: uuid.UUID,
        symbol: str,
        sort_order: int,
        notes: str | None,
    ) -> WatchlistItem:
        row = WatchlistItem(
            user_id=user_id,
            symbol=symbol,
            sort_order=sort_order,
            notes=notes,
        )
        self._session.add(row)
        self._session.flush()
        self._session.refresh(row)
        return row

    def delete_by_user_and_symbol(self, user_id: uuid.UUID, symbol: str) -> int:
        """Return number of rows deleted (0 or 1)."""
        stmt = delete(WatchlistItem).where(
            WatchlistItem.user_id == user_id,
            WatchlistItem.symbol == symbol,
        )
        result = self._session.execute(stmt)
        return int(result.rowcount or 0)
