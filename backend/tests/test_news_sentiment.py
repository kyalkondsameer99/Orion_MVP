"""Tests for news normalization, rule sentiment, catalyst summary, and API wiring."""

from __future__ import annotations

import datetime as dt

from fastapi.testclient import TestClient

from app.api.deps import get_news_sentiment_service
from app.main import app
from app.news.sentiment.rules import (
    RuleBasedSentimentEngine,
    label_from_score,
    score_text_lexicon,
)
from app.news.summary import build_catalyst_summary, detect_catalyst_tags
from app.news.types import NewsHeadline
from app.news.providers.stub import StubNewsProvider
from app.news.service import NewsSentimentService


def test_score_text_lexicon_positive_bias() -> None:
    s = score_text_lexicon("Company beats earnings and raises guidance on strong revenue growth")
    assert s > 0.2


def test_score_text_lexicon_negative_bias() -> None:
    s = score_text_lexicon("Firm misses estimates; regulators probe accounting; shares slip")
    assert s < -0.2


def test_label_from_score_thresholds() -> None:
    assert label_from_score(0.5) == "positive"
    assert label_from_score(-0.5) == "negative"
    assert label_from_score(0.0) == "neutral"


def test_rule_engine_aggregate() -> None:
    eng = RuleBasedSentimentEngine()
    hs = [
        NewsHeadline(
            id="1",
            symbol="TST",
            title="Upgrade and record profits as sales surge",
            source="x",
            url=None,
            published_at=dt.datetime.now(tz=dt.timezone.utc),
        ),
        NewsHeadline(
            id="2",
            symbol="TST",
            title="Minor partnership update",
            source="x",
            url=None,
            published_at=dt.datetime.now(tz=dt.timezone.utc),
        ),
    ]
    label, score = eng.score_headlines(hs)
    assert label in {"positive", "neutral", "negative"}
    assert -1.0 <= score <= 1.0


def test_detect_catalyst_tags() -> None:
    hs = [
        NewsHeadline(
            id="1",
            symbol="X",
            title="SEC probe into revenue recognition",
            source=None,
            url=None,
            published_at=None,
        ),
        NewsHeadline(
            id="2",
            symbol="X",
            title="New product launch next quarter",
            source=None,
            url=None,
            published_at=None,
        ),
    ]
    tags = detect_catalyst_tags(hs)
    assert "regulatory" in tags or "product" in tags


def test_build_catalyst_summary_non_empty() -> None:
    hs = [
        NewsHeadline(
            id="1",
            symbol="AB",
            title="Earnings beat expectations",
            source=None,
            url=None,
            published_at=None,
        )
    ]
    text = build_catalyst_summary(
        "AB",
        hs,
        sentiment="positive",
        sentiment_score=0.4,
        tags=["earnings"],
    )
    assert "AB" in text
    assert "earnings" in text.lower() or "1" in text


def test_news_digest_api_stub() -> None:
    app.dependency_overrides[get_news_sentiment_service] = lambda: NewsSentimentService(
        StubNewsProvider(),
        RuleBasedSentimentEngine(),
    )
    try:
        with TestClient(app, raise_server_exceptions=True) as client:
            r = client.get("/api/v1/news/AAPL", params={"limit": 4})
        assert r.status_code == 200
        data = r.json()
        assert data["symbol"] == "AAPL"
        assert data["provider"] == "stub"
        assert data["sentiment"] in {"positive", "neutral", "negative"}
        assert "summary" in data
        assert isinstance(data["headlines"], list)
        assert len(data["headlines"]) == 4
    finally:
        app.dependency_overrides.clear()
