"""Tests for deterministic recommendation engine."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app
from app.recommendation.config import RecommendationEngineConfig
from app.recommendation.engine import run_recommendation
from app.schemas.market_data import CandleOut
from app.schemas.recommendation_engine import (
    NewsContextIn,
    RecommendationRequest,
    TechnicalIndicatorsIn,
)


def _candles(n: int = 6, price: float = 100.0) -> list[CandleOut]:
    ts = dt.datetime.now(tz=dt.timezone.utc)
    out: list[CandleOut] = []
    for i in range(n):
        o = price - 0.1 + i * 0.01
        c = price + i * 0.02
        h = c + 0.2
        l = o - 0.2
        out.append(
            CandleOut(
                ts=ts + dt.timedelta(hours=i),
                open=o,
                high=h,
                low=l,
                close=c,
                volume=1e6,
            )
        )
    return out


def test_long_trade_meets_min_rr() -> None:
    cfg = RecommendationEngineConfig(max_position_fraction=1.0, technical_score_threshold=20.0)
    last_close = 100.0
    candles = _candles(6, price=last_close)
    req = RecommendationRequest(
        symbol="AAPL",
        candles=candles,
        indicators=TechnicalIndicatorsIn(
            rsi=25.0,
            ema=95.0,
            sma=90.0,
            macd_histogram=0.5,
            atr=1.0,
        ),
        news=NewsContextIn(sentiment="positive", sentiment_score=0.4, summary="Earnings beat."),
        account_size=Decimal("500000"),
        risk_percent=0.5,
    )
    out = run_recommendation(req, cfg)
    assert out.action == "BUY"
    assert out.direction == "LONG"
    assert out.entry_price is not None and out.stop_loss is not None and out.take_profit is not None
    assert out.reward_risk_ratio is not None and out.reward_risk_ratio >= 2.0 - 1e-6
    rr = (out.take_profit - out.entry_price) / (out.entry_price - out.stop_loss)
    assert rr >= 2.0 - 1e-6


def test_short_trade_meets_min_rr() -> None:
    cfg = RecommendationEngineConfig(max_position_fraction=1.0, technical_score_threshold=20.0)
    req = RecommendationRequest(
        symbol="AAPL",
        candles=_candles(6, price=100.0),
        indicators=TechnicalIndicatorsIn(
            rsi=76.0,
            ema=105.0,
            sma=110.0,
            macd_histogram=-0.4,
            atr=1.0,
        ),
        news=NewsContextIn(sentiment="negative", sentiment_score=-0.2, summary="Downgrade chatter."),
        account_size=Decimal("500000"),
        risk_percent=0.5,
    )
    out = run_recommendation(req, cfg)
    assert out.action == "SELL"
    assert out.direction == "SHORT"
    assert out.reward_risk_ratio is not None and out.reward_risk_ratio >= 2.0 - 1e-6
    assert out.stop_loss is not None and out.entry_price is not None and out.take_profit is not None
    risk = out.stop_loss - out.entry_price
    reward = out.entry_price - out.take_profit
    assert risk > 0 and (reward / risk) >= 2.0 - 1e-6


def test_news_veto_blocks_long() -> None:
    cfg = RecommendationEngineConfig(max_position_fraction=1.0)
    req = RecommendationRequest(
        symbol="AAPL",
        candles=_candles(6),
        indicators=TechnicalIndicatorsIn(
            rsi=25.0,
            ema=95.0,
            sma=90.0,
            macd_histogram=0.5,
            atr=1.0,
        ),
        news=NewsContextIn(sentiment="negative", sentiment_score=-0.9, summary="SEC probe"),
        account_size=Decimal("500000"),
        risk_percent=0.5,
    )
    out = run_recommendation(req, cfg)
    assert out.action == "HOLD"
    assert "News" in out.reason_summary or "news" in out.reason_summary.lower()


def test_position_cap_rejects() -> None:
    cfg = RecommendationEngineConfig(max_position_fraction=0.01, technical_score_threshold=20.0)
    req = RecommendationRequest(
        symbol="AAPL",
        candles=_candles(6),
        indicators=TechnicalIndicatorsIn(
            rsi=25.0,
            ema=95.0,
            sma=90.0,
            macd_histogram=0.5,
            atr=1.0,
        ),
        news=NewsContextIn(sentiment="positive", sentiment_score=0.2, summary="ok"),
        account_size=Decimal("100000"),
        risk_percent=2.0,
    )
    out = run_recommendation(req, cfg)
    assert out.action == "HOLD"
    assert "notional" in out.reason_summary.lower()


def test_api_analyze_endpoint() -> None:
    payload = {
        "symbol": "MSFT",
        "candles": [c.model_dump(mode="json") for c in _candles(6)],
        "indicators": {
            "rsi": 25.0,
            "ema": 95.0,
            "sma": 90.0,
            "macd_histogram": 0.5,
            "atr": 1.0,
        },
        "news": {"sentiment": "neutral", "sentiment_score": 0.0, "summary": "Mixed news."},
        "account_size": "1000000",
        "risk_percent": 0.25,
    }
    with TestClient(app, raise_server_exceptions=True) as client:
        r = client.post("/api/v1/recommendations/analyze", json=payload)
        r2 = client.post("/api/v1/recommendations/generate", json=payload)
    assert r.status_code == 200
    assert r2.status_code == 200
    assert r.json() == r2.json()
    data = r.json()
    assert data["action"] in {"BUY", "SELL", "HOLD"}
    assert data["direction"] in {"LONG", "SHORT", "NONE"}
