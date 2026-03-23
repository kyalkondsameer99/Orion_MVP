"""Broker integration errors — map upstream failures without leaking secrets."""

from __future__ import annotations


class BrokerConfigurationError(RuntimeError):
    """Missing API credentials or invalid broker configuration."""


class BrokerAPIError(RuntimeError):
    """Alpaca (or other) HTTP/API error."""

    def __init__(self, status_code: int, message: str, *, body: str | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body
