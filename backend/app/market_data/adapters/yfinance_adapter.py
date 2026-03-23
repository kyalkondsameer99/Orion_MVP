"""Yahoo Finance-backed adapter (yfinance)."""

from __future__ import annotations

import datetime as dt

import pandas as pd
import yfinance as yf

from app.market_data.types import Candle, Timeframe


class YFinanceMarketDataAdapter:
    """Maps normalized intervals to `yfinance` downloads."""

    def fetch_ohlcv(
        self,
        symbol: str,
        *,
        timeframe: Timeframe,
        interval: str,
        limit: int,
    ) -> list[Candle]:
        n = max(1, min(limit, 8000))
        period = _pick_period(timeframe, interval, n)
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=False)
        if df is None or df.empty:
            return []

        df = df.tail(n)
        out: list[Candle] = []
        for idx, row in df.iterrows():
            ts = idx.to_pydatetime()
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=dt.timezone.utc)
            else:
                ts = ts.astimezone(dt.timezone.utc)
            vol_raw = row["Volume"]
            volume = 0.0 if pd.isna(vol_raw) else float(vol_raw)
            out.append(
                Candle(
                    ts=ts,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=volume,
                )
            )
        return out


def _pick_period(timeframe: Timeframe, interval: str, limit: int) -> str:
    """Heuristic `period=` strings for yfinance (it caps intraday history)."""
    if timeframe == "daily":
        if limit <= 400:
            return "2y"
        return "max"
    # intraday
    if interval in {"1m", "2m"}:
        return "7d"
    if interval in {"5m", "15m", "30m", "60m", "90m", "1h"}:
        return "60d"
    return "60d"
