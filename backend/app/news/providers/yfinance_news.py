"""Yahoo Finance headline feed via `yfinance` (when available)."""

from __future__ import annotations

import datetime as dt

import yfinance as yf

from app.news.types import NewsHeadline


class YFinanceNewsProvider:
    name = "yfinance"

    def fetch_headlines(self, symbol: str, *, limit: int) -> list[NewsHeadline]:
        sym = symbol.upper().strip()
        n = max(1, min(limit, 100))
        t = yf.Ticker(sym)
        raw = getattr(t, "news", None) or []
        out: list[NewsHeadline] = []
        for i, item in enumerate(raw[:n]):
            title = str(item.get("title") or "").strip()
            if not title:
                continue
            ts_raw = item.get("providerPublishTime")
            published: dt.datetime | None
            if isinstance(ts_raw, (int, float)):
                published = dt.datetime.fromtimestamp(int(ts_raw), tz=dt.timezone.utc)
            else:
                published = None
            hid = str(item.get("uuid") or f"{sym}-{i}")
            publisher = item.get("publisher")
            source = str(publisher).strip() if publisher is not None else None
            link = item.get("link")
            url = str(link).strip() if link else None
            out.append(
                NewsHeadline(
                    id=hid,
                    symbol=sym,
                    title=title,
                    source=source or None,
                    url=url or None,
                    published_at=published,
                )
            )
        return out
