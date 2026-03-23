"""Deterministic synthetic OHLCV for tests and offline dev."""

from __future__ import annotations

import datetime as dt
import math

from app.market_data.types import Candle, Timeframe


class StubMarketDataAdapter:
    """Generates smooth pseudo-price paths without network I/O."""

    def fetch_ohlcv(
        self,
        symbol: str,
        *,
        timeframe: Timeframe,
        interval: str,
        limit: int,
    ) -> list[Candle]:
        n = max(1, min(limit, 5000))
        base = sum(ord(c) for c in symbol[:8]) % 97 + 20.0
        step_hours = _interval_to_hours(interval, timeframe)
        now = dt.datetime.now(tz=dt.timezone.utc).replace(microsecond=0)
        out: list[Candle] = []
        for i in range(n):
            t = now - dt.timedelta(hours=step_hours * (n - 1 - i))
            phase = i * 0.17
            wobble = 0.6 * math.sin(phase) + 0.15 * math.sin(3 * phase)
            close = base + wobble + i * 0.01
            o = close - 0.05
            h = close + 0.12
            l = close - 0.11
            v = 1_000_000 + i * 137 + (hash(symbol) % 997) * 100
            out.append(
                Candle(
                    ts=t,
                    open=o,
                    high=h,
                    low=l,
                    close=close,
                    volume=float(v),
                )
            )
        return out


def _interval_to_hours(interval: str, timeframe: Timeframe) -> float:
    if timeframe == "daily":
        return 24.0
    mapping = {
        "1m": 1 / 60,
        "2m": 2 / 60,
        "5m": 5 / 60,
        "15m": 15 / 60,
        "30m": 30 / 60,
        "60m": 1.0,
        "90m": 1.5,
        "1h": 1.0,
    }
    return float(mapping.get(interval, 1.0))
