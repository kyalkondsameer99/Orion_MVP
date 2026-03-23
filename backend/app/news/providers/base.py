"""Pluggable news providers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.news.types import NewsHeadline


@runtime_checkable
class NewsProvider(Protocol):
    """Fetch recent headlines; implementations normalize into `NewsHeadline`."""

    name: str

    def fetch_headlines(self, symbol: str, *, limit: int) -> list[NewsHeadline]:
        """Return newest-first or oldest-first? **Newest-first** for display consistency."""
        ...
