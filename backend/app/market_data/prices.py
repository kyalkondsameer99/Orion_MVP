"""Latest mark price from OHLCV adapters (no FastAPI layer)."""

from __future__ import annotations

from decimal import Decimal

from app.market_data.adapters.base import MarketDataAdapter
from app.market_data.types import Timeframe


def fetch_last_price(adapter: MarketDataAdapter, symbol: str) -> Decimal:
    """
    Use the most recent intraday bar when possible; fall back to daily close.
    """
    candles = adapter.fetch_ohlcv(symbol, timeframe="intraday", interval="5m", limit=5)
    if not candles:
        candles = adapter.fetch_ohlcv(symbol, timeframe="daily", interval="1d", limit=1)
    if not candles:
        msg = f"No market data returned for {symbol!r}"
        raise ValueError(msg)
    return Decimal(str(candles[-1].close))
