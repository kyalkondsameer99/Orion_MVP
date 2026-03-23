"""
LLM-backed sentiment (placeholder).

Implement `score_headlines` using your model client; keep the `SentimentEngine` protocol stable.
"""

from __future__ import annotations

from app.news.types import NewsHeadline, SentimentLabel


class LLMSentimentEngineNotConfigured:
    """
    Stub implementation — swap with a real LLM client without changing routes.

    Wire this in settings only after you add prompts, retries, and cost controls.
    """

    name = "llm"

    def score_headlines(self, headlines: list[NewsHeadline]) -> tuple[SentimentLabel, float]:
        raise NotImplementedError(
            "LLMSentimentEngineNotConfigured: implement `score_headlines` with your LLM provider."
        )
