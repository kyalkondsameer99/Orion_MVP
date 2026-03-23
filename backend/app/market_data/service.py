"""Orchestrates adapters + indicator math for API responses."""

from __future__ import annotations

import numpy as np
from fastapi import HTTPException, status

from app.core.symbols import InvalidSymbolError, normalize_symbol
from app.market_data import indicators as ind
from app.market_data.adapters.base import MarketDataAdapter
from app.market_data.types import Candle, Timeframe
from app.schemas.market_data import (
    CandleOut,
    IndicatorParams,
    MarketAnalysisResponse,
    OHLCVResponse,
    SeriesFloat,
)

DAILY_INTERVALS = frozenset({"1d", "1wk", "1mo"})
INTRADAY_INTERVALS = frozenset({"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"})


class MarketDataService:
    """Application service — validation, adapter dispatch, indicator packaging."""

    def __init__(self, adapter: MarketDataAdapter) -> None:
        self._adapter = adapter

    def get_ohlcv(
        self,
        symbol_raw: str,
        *,
        timeframe: Timeframe,
        interval: str,
        limit: int,
    ) -> OHLCVResponse:
        candles = self._load_candles(symbol_raw, timeframe=timeframe, interval=interval, limit=limit)
        sym = self._norm_symbol(symbol_raw)
        return _build_ohlcv_response(sym, timeframe, interval, candles)

    def analyze(
        self,
        symbol_raw: str,
        *,
        timeframe: Timeframe,
        interval: str,
        limit: int,
        params: IndicatorParams,
    ) -> MarketAnalysisResponse:
        candles = self._load_candles(symbol_raw, timeframe=timeframe, interval=interval, limit=limit)
        sym = self._norm_symbol(symbol_raw)
        ohlcv = _build_ohlcv_response(sym, timeframe, interval, candles)

        _, h, l, c, v = _to_numpy(candles)
        rsi_v = ind.rsi(c, params.rsi_period)
        sma_v = ind.sma(c, params.sma_period)
        ema_v = ind.ema(c, params.ema_period)
        macd_line, macd_sig, macd_hist = ind.macd(
            c,
            fast=params.macd_fast,
            slow=params.macd_slow,
            signal=params.macd_signal,
        )
        atr_v = ind.atr(h, l, c, params.atr_period)
        vol_z = ind.volume_spike_zscore(v, params.volume_lookback)
        vol_spike = _volume_spike_list(vol_z, params.volume_z_threshold)

        return MarketAnalysisResponse(
            **ohlcv.model_dump(),
            rsi=SeriesFloat(window=params.rsi_period, values=_nan_to_none(rsi_v)),
            sma=SeriesFloat(window=params.sma_period, values=_nan_to_none(sma_v)),
            ema=SeriesFloat(window=params.ema_period, values=_nan_to_none(ema_v)),
            macd={
                "fast": params.macd_fast,
                "slow": params.macd_slow,
                "signal": params.macd_signal,
                "line": _nan_to_none(macd_line),
                "signal_line": _nan_to_none(macd_sig),
                "histogram": _nan_to_none(macd_hist),
            },
            atr=SeriesFloat(window=params.atr_period, values=_nan_to_none(atr_v)),
            volume_zscore=SeriesFloat(window=params.volume_lookback, values=_nan_to_none(vol_z)),
            volume_spike=vol_spike,
        )

    def _norm_symbol(self, symbol_raw: str) -> str:
        try:
            return normalize_symbol(symbol_raw)
        except InvalidSymbolError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    def _load_candles(
        self,
        symbol_raw: str,
        *,
        timeframe: Timeframe,
        interval: str,
        limit: int,
    ) -> list[Candle]:
        sym = self._norm_symbol(symbol_raw)
        self._validate_interval(timeframe, interval)
        lim = max(1, min(limit, 5000))
        return self._adapter.fetch_ohlcv(sym, timeframe=timeframe, interval=interval, limit=lim)

    @staticmethod
    def _validate_interval(timeframe: Timeframe, interval: str) -> None:
        if timeframe == "daily" and interval not in DAILY_INTERVALS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid daily interval {interval!r}; allowed {sorted(DAILY_INTERVALS)}",
            )
        if timeframe == "intraday" and interval not in INTRADAY_INTERVALS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid intraday interval {interval!r}; allowed {sorted(INTRADAY_INTERVALS)}",
            )


def _build_ohlcv_response(symbol: str, timeframe: Timeframe, interval: str, candles: list[Candle]) -> OHLCVResponse:
    rows = [
        CandleOut(
            ts=c.ts,
            open=c.open,
            high=c.high,
            low=c.low,
            close=c.close,
            volume=c.volume,
        )
        for c in candles
    ]
    return OHLCVResponse(symbol=symbol, timeframe=timeframe, interval=interval, candles=rows)


def _to_numpy(candles: list[Candle]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    o = np.array([c.open for c in candles], dtype=float)
    h = np.array([c.high for c in candles], dtype=float)
    l = np.array([c.low for c in candles], dtype=float)
    c = np.array([c.close for c in candles], dtype=float)
    v = np.array([c.volume for c in candles], dtype=float)
    return o, h, l, c, v


def _nan_to_none(arr: np.ndarray) -> list[float | None]:
    out: list[float | None] = []
    for x in np.asarray(arr, dtype=float).ravel():
        if np.isnan(x):
            out.append(None)
        else:
            out.append(float(x))
    return out


def _volume_spike_list(z: np.ndarray, z_threshold: float) -> list[bool | None]:
    out: list[bool | None] = []
    for val in np.asarray(z, dtype=float).ravel():
        if np.isnan(val):
            out.append(None)
        else:
            out.append(bool(val > z_threshold))
    return out
