"""News & sentiment API contracts."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import Field

from app.schemas.common import SchemaBase

SentimentLabel = Literal["positive", "neutral", "negative"]


class NewsHeadlineOut(SchemaBase):
    """Stable headline shape regardless of upstream feed."""

    id: str
    symbol: str
    title: str
    source: str | None = None
    url: str | None = None
    published_at: dt.datetime | None = None


class NewsDigestResponse(SchemaBase):
    """Headlines plus aggregated sentiment and catalyst summary."""

    symbol: str
    provider: str = Field(..., description="News backend identifier (e.g. stub, yfinance).")
    sentiment: SentimentLabel
    sentiment_score: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Continuous score in [-1, 1]; label derived from thresholds.",
    )
    summary: str = Field(..., description="Short catalyst / theme summary.")
    catalyst_tags: list[str] = Field(default_factory=list, description="Detected theme tags.")
    headlines: list[NewsHeadlineOut]
    fetched_at: dt.datetime
