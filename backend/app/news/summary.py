"""Rule-based catalyst tagging + short narrative (LLM can replace this module later)."""

from __future__ import annotations

import re

from app.news.types import NewsHeadline, SentimentLabel

_THEME_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("earnings", re.compile(r"\bearnings\b|\beps\b|\bguidance\b|\brevenue\b", re.I)),
    ("analyst", re.compile(r"\banalyst\b|\bupgrade\b|\bdowngrade\b|\boutperform\b", re.I)),
    ("regulatory", re.compile(r"\bsec\b|\bprobe\b|\binvestigation\b|\bregulator", re.I)),
    ("legal", re.compile(r"\blawsuit\b|\blitigation\b|\bsettlement\b", re.I)),
    ("product", re.compile(r"\bproduct\b|\blaunch\b|\bpartnership\b", re.I)),
    ("macro", re.compile(r"\brate\b|\binflation\b|\brecession\b|\bmacro\b", re.I)),
]


def detect_catalyst_tags(headlines: list[NewsHeadline]) -> list[str]:
    """Return ordered unique theme tags found across titles."""
    found: list[str] = []
    blob = " ".join(h.title for h in headlines)
    for tag, pat in _THEME_PATTERNS:
        if pat.search(blob) and tag not in found:
            found.append(tag)
    return found


def build_catalyst_summary(
    symbol: str,
    headlines: list[NewsHeadline],
    *,
    sentiment: SentimentLabel,
    sentiment_score: float,
    tags: list[str],
) -> str:
    """Compact human-readable summary; replace with LLM summarization when ready."""
    n = len(headlines)
    if n == 0:
        return f"No recent headlines available for {symbol}."

    tag_part = ", ".join(tags) if tags else "general corporate news"
    tone = {
        "positive": "constructive",
        "negative": "cautious",
        "neutral": "mixed-to-neutral",
    }[sentiment]

    return (
        f"{symbol}: scanned {n} headline(s). Dominant themes: {tag_part}. "
        f"Aggregate tone looks {tone} (score {sentiment_score:+.2f})."
    )
