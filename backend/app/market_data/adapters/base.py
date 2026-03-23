"""
Pluggable market data providers.

Implement `MarketDataAdapter` (or duck-type the protocol) and register via settings.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.market_data.types import Candle, Timeframe


@runtime_checkable
class MarketDataAdapter(Protocol):
    """Fetches OHLCV candles; swap implementations for Alpaca, Polygon, etc."""

    def fetch_ohlcv(
        self,
        symbol: str,
        *,
        timeframe: Timeframe,
        interval: str,
        limit: int,
    ) -> list[Candle]:
        """
        Return newest-first or oldest-first? **Oldest-first** (chronological) for all adapters.

        `interval` matches yfinance-style tokens: `1d`, `1h`, `15m`, ...
        """
        ...
