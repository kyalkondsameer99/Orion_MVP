"""
Sentiment engines turn headline text into a score + discrete label.

Swap `RuleBasedSentimentEngine` for an LLM-backed class that implements the same protocol.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.news.types import NewsHeadline, SentimentLabel


@runtime_checkable
class SentimentEngine(Protocol):
    """Produces a continuous score in [-1, 1] and a tri-class label."""

    name: str

    def score_headlines(self, headlines: list[NewsHeadline]) -> tuple[SentimentLabel, float]:
        ...
