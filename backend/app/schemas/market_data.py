"""Market data API contracts."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import Field

from app.schemas.common import SchemaBase


class CandleOut(SchemaBase):
    ts: dt.datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class OHLCVResponse(SchemaBase):
    symbol: str
    timeframe: Literal["daily", "intraday"]
    interval: str
    candles: list[CandleOut]


class SeriesFloat(SchemaBase):
    """Aligned series; `window` is the lookback (RSI period, SMA length, volume window, ...)."""

    window: int
    values: list[float | None]


class IndicatorParams(SchemaBase):
    rsi_period: int = Field(default=14, ge=2, le=200)
    sma_period: int = Field(default=20, ge=2, le=500)
    ema_period: int = Field(default=12, ge=2, le=500)
    macd_fast: int = Field(default=12, ge=2, le=200)
    macd_slow: int = Field(default=26, ge=2, le=500)
    macd_signal: int = Field(default=9, ge=2, le=200)
    atr_period: int = Field(default=14, ge=2, le=200)
    volume_lookback: int = Field(default=20, ge=2, le=500)
    volume_z_threshold: float = Field(default=2.0, ge=0.5, le=10.0)


class MarketAnalysisResponse(OHLCVResponse):
    rsi: SeriesFloat
    sma: SeriesFloat
    ema: SeriesFloat
    macd: dict[str, object]
    atr: SeriesFloat
    volume_zscore: SeriesFloat
    volume_spike: list[bool | None]
