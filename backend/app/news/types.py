"""Internal news domain types (provider-agnostic)."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Literal

SentimentLabel = Literal["positive", "neutral", "negative"]


@dataclass(frozen=True, slots=True)
class NewsHeadline:
    """Normalized headline row after provider mapping."""

    id: str
    symbol: str
    title: str
    source: str | None
    url: str | None
    published_at: dt.datetime | None
