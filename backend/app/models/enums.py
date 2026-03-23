"""Domain enums stored as VARCHAR (portable, migration-friendly)."""

from __future__ import annotations

from enum import Enum


class BrokerProvider(str, Enum):
    """Supported broker integrations (extend as you add adapters)."""

    ALPACA = "alpaca"
    IBKR = "ibkr"
    SIMULATED = "simulated"
    CUSTOM = "custom"


class ConnectionStatus(str, Enum):
    """Lifecycle of a linked broker account."""

    PENDING = "pending"
    ACTIVE = "active"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class OrderSide(str, Enum):
    """Order / intent direction."""

    BUY = "buy"
    SELL = "sell"


class PositionSide(str, Enum):
    """Open position direction."""

    LONG = "long"
    SHORT = "short"


class OrderType(str, Enum):
    """Basic order types for paper trading."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    """Broker-agnostic order lifecycle."""

    NEW = "new"
    SUBMITTED = "submitted"
    PENDING = "pending"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TimeInForce(str, Enum):
    """How long an order remains active."""

    DAY = "day"
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"


class RecommendationStatus(str, Enum):
    """Copilot / engine recommendation workflow."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"
    EXPIRED = "expired"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUBMITTED = "submitted"


class RecommendationSource(str, Enum):
    """Where a recommendation originated."""

    COPILOT = "copilot"
    RULE = "rule"
    IMPORT = "import"
    ENGINE = "engine"
    POSITION_MONITOR = "position_monitor"


class PositionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class AuditActorType(str, Enum):
    """Who performed an auditable action."""

    USER = "user"
    SYSTEM = "system"
    ADMIN = "admin"
