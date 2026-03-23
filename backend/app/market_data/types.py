"""Shared types for OHLCV series and timeframe selection."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from enum import Enum
from typing import Literal

Timeframe = Literal["daily", "intraday"]


class MarketInterval(str, Enum):
    """Normalized interval tokens passed to adapters."""

    M1 = "1m"
    M2 = "2m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    M60 = "60m"
    M90 = "90m"
    H1 = "1h"
    D1 = "1d"
    W1 = "1wk"
    MO1 = "1mo"


@dataclass(frozen=True, slots=True)
class Candle:
    """Single OHLCV bar."""

    ts: dt.datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
