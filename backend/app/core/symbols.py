"""
Ticker symbol validation and normalization for watchlists and orders.

Rules (paper-trading friendly, US-style equities and index proxies):
- 1–32 characters after trim
- Uppercase letters, digits, `.`, `-`, and optional leading `^` for indices (e.g. `BRK.A`, `^GSPC`)
"""

from __future__ import annotations

import re

# Optional leading `^` for index-style symbols (e.g. `^GSPC`), or standard tickers (`BRK.A`).
_SYMBOL_RE = re.compile(
    r"^(?:\^[A-Z0-9][A-Z0-9.\-^]{0,29}|[A-Z0-9][A-Z0-9.\-^]{0,31})$"
)


class InvalidSymbolError(ValueError):
    """Raised when a symbol string fails format validation."""


def normalize_symbol(raw: str) -> str:
    """
    Strip whitespace, uppercase, and validate against `_SYMBOL_RE`.

    Raises:
        InvalidSymbolError: if empty or pattern mismatch after normalization.
    """
    if raw is None:
        raise InvalidSymbolError("Symbol is required")
    s = raw.strip().upper()
    if not s:
        raise InvalidSymbolError("Symbol cannot be empty")
    if not _SYMBOL_RE.fullmatch(s):
        raise InvalidSymbolError(
            "Symbol must be 1–32 chars: letters, digits, '.', '-', or '^' (index-style)"
        )
    return s
