"""Recommendation engine API contracts."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import Field

from app.schemas.common import SchemaBase
from app.schemas.market_data import CandleOut


class NewsContextIn(SchemaBase):
    """Condensed news / sentiment passed into the engine."""

    sentiment: Literal["positive", "neutral", "negative"]
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    summary: str = Field(default="", max_length=8000)


class TechnicalIndicatorsIn(SchemaBase):
    """
    Last-bar indicator values (aligned with the final candle in `candles`).

    Omitted fields reduce scoring weight gracefully.
    """

    rsi: float | None = Field(default=None, ge=0.0, le=100.0)
    ema: float | None = None
    sma: float | None = None
    macd_line: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    atr: float | None = Field(default=None, ge=0.0)


class RecommendationRequest(SchemaBase):
    symbol: str
    candles: list[CandleOut] = Field(..., min_length=1)
    indicators: TechnicalIndicatorsIn
    news: NewsContextIn
    account_size: Decimal = Field(..., gt=0)
    risk_percent: float = Field(
        ...,
        ge=0.01,
        le=100.0,
        description="Percent of account to risk on this trade (e.g. 1.0 = 1%).",
    )


Action = Literal["BUY", "SELL", "HOLD"]
Direction = Literal["LONG", "SHORT", "NONE"]


class RecommendationResponse(SchemaBase):
    action: Action
    direction: Direction
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    technical_summary: str
    news_summary: str
    reason_summary: str
    passed_risk_checks: bool = True
    reward_risk_ratio: float | None = Field(
        default=None,
        description="Realized reward:risk for the proposed levels (None if HOLD).",
    )
