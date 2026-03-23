"""Construct market data adapters from settings (API deps + workers share this)."""

from __future__ import annotations

from app.core.config import Settings
from app.market_data.adapters.base import MarketDataAdapter
from app.market_data.adapters.stub import StubMarketDataAdapter
from app.market_data.adapters.yfinance_adapter import YFinanceMarketDataAdapter


def build_market_data_adapter(settings: Settings) -> MarketDataAdapter:
    if settings.MARKET_DATA_PROVIDER == "yfinance":
        return YFinanceMarketDataAdapter()
    return StubMarketDataAdapter()
