"""Data access layer — keep SQLAlchemy details out of services and routes."""

from app.repositories.watchlist_repository import WatchlistRepository

__all__ = ["WatchlistRepository"]
