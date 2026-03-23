"""Coordinates news providers, sentiment engines, and catalyst summaries."""

from __future__ import annotations

import datetime as dt

from fastapi import HTTPException, status

from app.core.symbols import InvalidSymbolError, normalize_symbol
from app.news.providers.base import NewsProvider
from app.news.sentiment.base import SentimentEngine
from app.news.summary import build_catalyst_summary, detect_catalyst_tags
from app.news.types import NewsHeadline
from app.schemas.news import NewsDigestResponse, NewsHeadlineOut


class NewsSentimentService:
    """Application service — validation, normalization to API schemas."""

    def __init__(
        self,
        provider: NewsProvider,
        sentiment: SentimentEngine,
    ) -> None:
        self._provider = provider
        self._sentiment = sentiment

    def digest(self, symbol_raw: str, *, limit: int) -> NewsDigestResponse:
        sym = self._norm_symbol(symbol_raw)
        lim = max(1, min(limit, 100))
        try:
            headlines = self._provider.fetch_headlines(sym, limit=lim)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"News provider error: {e}",
            ) from e

        label, score = self._sentiment.score_headlines(headlines)
        tags = detect_catalyst_tags(headlines)
        summary = build_catalyst_summary(
            sym,
            headlines,
            sentiment=label,
            sentiment_score=score,
            tags=tags,
        )

        return NewsDigestResponse(
            symbol=sym,
            provider=self._provider.name,
            sentiment=label,
            sentiment_score=score,
            summary=summary,
            catalyst_tags=tags,
            headlines=[self._to_out(h) for h in headlines],
            fetched_at=dt.datetime.now(tz=dt.timezone.utc),
        )

    @staticmethod
    def _to_out(h: NewsHeadline) -> NewsHeadlineOut:
        return NewsHeadlineOut(
            id=h.id,
            symbol=h.symbol,
            title=h.title,
            source=h.source,
            url=h.url,
            published_at=h.published_at,
        )

    @staticmethod
    def _norm_symbol(symbol_raw: str) -> str:
        try:
            return normalize_symbol(symbol_raw)
        except InvalidSymbolError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
