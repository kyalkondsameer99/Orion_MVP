"""Market data HTTP API."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_market_data_service
from app.market_data.service import MarketDataService
from app.schemas.market_data import IndicatorParams, MarketAnalysisResponse, OHLCVResponse

router = APIRouter()


@router.get(
    "/{symbol}/ohlcv",
    response_model=OHLCVResponse,
    summary="Fetch OHLCV candles",
)
def get_ohlcv(
    symbol: str,
    timeframe: Literal["daily", "intraday"] = Query(..., description="Daily bars or intraday."),
    interval: str = Query(
        ...,
        description="Provider interval token, e.g. `1d`, `1h`, `15m`.",
    ),
    limit: int = Query(default=120, ge=1, le=5000),
    service: MarketDataService = Depends(get_market_data_service),
) -> OHLCVResponse:
    return service.get_ohlcv(symbol, timeframe=timeframe, interval=interval, limit=limit)


@router.get(
    "/{symbol}/analysis",
    response_model=MarketAnalysisResponse,
    summary="OHLCV plus RSI, SMA, EMA, MACD, ATR, and volume spike (z-score)",
)
def get_analysis(
    symbol: str,
    timeframe: Literal["daily", "intraday"] = Query(...),
    interval: str = Query(...),
    limit: int = Query(default=120, ge=1, le=5000),
    params: IndicatorParams = Depends(),
    service: MarketDataService = Depends(get_market_data_service),
) -> MarketAnalysisResponse:
    return service.analyze(
        symbol,
        timeframe=timeframe,
        interval=interval,
        limit=limit,
        params=params,
    )
