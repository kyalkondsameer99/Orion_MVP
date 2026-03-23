"""Lexicon-based sentiment — deterministic and easy to regression-test."""

from __future__ import annotations

import re

from app.news.types import NewsHeadline, SentimentLabel

# Minimal finance lexicon; extend or load from config as needed.
_POS = frozenset(
    {
        "beat",
        "beats",
        "bull",
        "bullish",
        "growth",
        "upgrade",
        "upgrades",
        "outperform",
        "record",
        "profit",
        "rally",
        "strong",
        "surge",
        "gain",
        "gains",
        "approval",
        "acquisition",
        "partnership",
        "raises guidance",
    }
)
_NEG = frozenset(
    {
        "miss",
        "misses",
        "bear",
        "bearish",
        "downgrade",
        "downgrades",
        "lawsuit",
        "probe",
        "investigation",
        "decline",
        "loss",
        "losses",
        "weak",
        "warning",
        "recall",
        "layoff",
        "layoffs",
        "cuts guidance",
        "cuts",
        "slips",
        "uncertainty",
    }
)

_TOKEN_RE = re.compile(r"[a-z0-9']+")


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def score_text_lexicon(text: str) -> float:
    """Map a single headline to roughly [-1, 1] using token hits."""
    toks = set(_tokens(text))
    if not toks:
        return 0.0
    pos_hits = sum(1 for t in toks if t in _POS)
    neg_hits = sum(1 for t in toks if t in _NEG)
    # Phrase-level boosts (substring scan — coarse but useful for multi-word cues).
    low = text.lower()
    if "raises guidance" in low or "raise guidance" in low:
        pos_hits += 1
    if "cuts guidance" in low or "cut guidance" in low:
        neg_hits += 1
    if pos_hits == neg_hits == 0:
        return 0.0
    return (pos_hits - neg_hits) / (pos_hits + neg_hits + 1e-6)


def aggregate_scores(scores: list[float]) -> float:
    if not scores:
        return 0.0
    return float(sum(scores) / len(scores))


def label_from_score(score: float, *, pos_thr: float = 0.15, neg_thr: float = -0.15) -> SentimentLabel:
    if score > pos_thr:
        return "positive"
    if score < neg_thr:
        return "negative"
    return "neutral"


class RuleBasedSentimentEngine:
    name = "rules"

    def score_headlines(self, headlines: list[NewsHeadline]) -> tuple[SentimentLabel, float]:
        if not headlines:
            return "neutral", 0.0
        parts = [score_text_lexicon(h.title) for h in headlines]
        s = aggregate_scores(parts)
        return label_from_score(s), max(-1.0, min(1.0, s))
