"""
Shared FastAPI dependencies (`Depends`).

Centralizing imports keeps route modules small and mocks predictable in tests.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.market_data.adapter_factory import build_market_data_adapter
from app.market_data.adapters.base import MarketDataAdapter
from app.market_data.service import MarketDataService
from app.news.providers.base import NewsProvider
from app.news.providers.stub import StubNewsProvider
from app.news.providers.yfinance_news import YFinanceNewsProvider
from app.news.sentiment.base import SentimentEngine
from app.news.sentiment.llm import LLMSentimentEngineNotConfigured
from app.news.sentiment.rules import RuleBasedSentimentEngine
from app.news.service import NewsSentimentService
from app.broker.adapters.alpaca import AlpacaPaperBrokerAdapter
from app.broker.service import BrokerService
from app.recommendation.config import RecommendationEngineConfig
from app.recommendation.service import RecommendationService
from app.services.recommendation_workflow_service import RecommendationWorkflowService
from app.services.watchlist_service import WatchlistService


def get_current_user_id(
    x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None,
) -> uuid.UUID:
    """
    Resolve the acting user from `X-User-Id` (UUID).

    Replace with JWT / session auth in production; kept explicit for MVP and tests.
    """
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-User-Id header",
        )
    try:
        return uuid.UUID(x_user_id.strip())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-User-Id header; expected a UUID",
        ) from None


def get_watchlist_service(db: Session = Depends(get_db)) -> WatchlistService:
    return WatchlistService(db)


def get_market_data_adapter(
    settings: Annotated[Settings, Depends(get_settings)],
) -> MarketDataAdapter:
    return build_market_data_adapter(settings)


def get_market_data_service(
    adapter: Annotated[MarketDataAdapter, Depends(get_market_data_adapter)],
) -> MarketDataService:
    return MarketDataService(adapter)


def get_news_provider(
    settings: Annotated[Settings, Depends(get_settings)],
) -> NewsProvider:
    if settings.NEWS_PROVIDER == "yfinance":
        return YFinanceNewsProvider()
    return StubNewsProvider()


def get_sentiment_engine(
    settings: Annotated[Settings, Depends(get_settings)],
) -> SentimentEngine:
    if settings.SENTIMENT_ENGINE == "llm":
        return LLMSentimentEngineNotConfigured()
    return RuleBasedSentimentEngine()


def get_news_sentiment_service(
    provider: Annotated[NewsProvider, Depends(get_news_provider)],
    sentiment: Annotated[SentimentEngine, Depends(get_sentiment_engine)],
) -> NewsSentimentService:
    return NewsSentimentService(provider, sentiment)


def get_recommendation_config() -> RecommendationEngineConfig:
    return RecommendationEngineConfig()


def get_recommendation_service(
    config: Annotated[RecommendationEngineConfig, Depends(get_recommendation_config)],
) -> RecommendationService:
    return RecommendationService(config)


def get_alpaca_adapter(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AlpacaPaperBrokerAdapter:
    if not settings.ALPACA_API_KEY_ID or not settings.ALPACA_API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Set ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY (or ALPACA_API_KEY / ALPACA_API_SECRET) for Alpaca paper trading.",
        )
    return AlpacaPaperBrokerAdapter(
        settings.ALPACA_API_KEY_ID,
        settings.ALPACA_API_SECRET_KEY,
        base_url=settings.ALPACA_PAPER_BASE_URL,
    )


def get_broker_service(
    adapter: Annotated[AlpacaPaperBrokerAdapter, Depends(get_alpaca_adapter)],
) -> BrokerService:
    return BrokerService(adapter)


def get_optional_broker_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> BrokerService | None:
    if not settings.ALPACA_API_KEY_ID or not settings.ALPACA_API_SECRET_KEY:
        return None
    adapter = AlpacaPaperBrokerAdapter(
        settings.ALPACA_API_KEY_ID,
        settings.ALPACA_API_SECRET_KEY,
        base_url=settings.ALPACA_PAPER_BASE_URL,
    )
    return BrokerService(adapter)


def get_recommendation_workflow_service(
    db: Annotated[Session, Depends(get_db)],
    broker: Annotated[BrokerService | None, Depends(get_optional_broker_service)],
) -> RecommendationWorkflowService:
    return RecommendationWorkflowService(db, broker)


def require_trading_enabled(
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Kill-switch: block order-like actions when `TRADING_ENABLED=false`."""
    if not settings.TRADING_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trading is disabled (TRADING_ENABLED=false).",
        )


__all__ = [
    "get_db",
    "get_settings",
    "get_current_user_id",
    "get_watchlist_service",
    "get_market_data_adapter",
    "get_market_data_service",
    "get_news_provider",
    "get_sentiment_engine",
    "get_news_sentiment_service",
    "get_recommendation_config",
    "get_recommendation_service",
    "get_alpaca_adapter",
    "get_broker_service",
    "get_optional_broker_service",
    "get_recommendation_workflow_service",
    "require_trading_enabled",
]
