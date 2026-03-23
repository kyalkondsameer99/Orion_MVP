"""News & sentiment HTTP API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_news_sentiment_service
from app.news.service import NewsSentimentService
from app.schemas.news import NewsDigestResponse

router = APIRouter()


@router.get(
    "/{symbol}",
    response_model=NewsDigestResponse,
    summary="Recent headlines with sentiment and catalyst summary",
)
def get_news_digest(
    symbol: str,
    limit: int = Query(default=20, ge=1, le=100),
    service: NewsSentimentService = Depends(get_news_sentiment_service),
) -> NewsDigestResponse:
    return service.digest(symbol, limit=limit)
