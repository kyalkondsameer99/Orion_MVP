"""Deterministic sample headlines for tests and offline dev."""

from __future__ import annotations

import datetime as dt
import hashlib

from app.news.types import NewsHeadline


class StubNewsProvider:
    name = "stub"

    def fetch_headlines(self, symbol: str, *, limit: int) -> list[NewsHeadline]:
        sym = symbol.upper().strip()
        n = max(1, min(limit, 50))
        now = dt.datetime.now(tz=dt.timezone.utc)
        templates = [
            (
                f"{sym} beats earnings expectations; shares rally on strong guidance",
                "positive",
            ),
            (
                f"Analysts upgrade {sym} citing margin expansion and record revenue",
                "positive",
            ),
            (
                f"Regulators probe {sym} over disclosure; stock slips on uncertainty",
                "negative",
            ),
            (
                f"{sym} announces product partnership — muted market reaction",
                "neutral",
            ),
        ]
        out: list[NewsHeadline] = []
        for i in range(n):
            title, _ = templates[i % len(templates)]
            ts = now - dt.timedelta(hours=i * 3)
            hid = hashlib.sha256(f"{sym}-{i}-{title}".encode()).hexdigest()[:16]
            out.append(
                NewsHeadline(
                    id=hid,
                    symbol=sym,
                    title=title,
                    source="stub-wire",
                    url=f"https://news.example.com/{sym.lower()}/{hid}",
                    published_at=ts,
                )
            )
        return out
