"""Application user — owns connections, watchlists, orders, and positions."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.broker_connection import BrokerConnection
    from app.models.position import Position
    from app.models.recommendation import Recommendation
    from app.models.trade_order import TradeOrder
    from app.models.watchlist_item import WatchlistItem


class User(Base, TimestampMixin):
    """
    End-user account.

    `hashed_password` may be null for pure OAuth / broker-token flows.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    broker_connections: Mapped[list[BrokerConnection]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    watchlist_items: Mapped[list[WatchlistItem]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    recommendations: Mapped[list[Recommendation]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    trade_orders: Mapped[list[TradeOrder]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    positions: Mapped[list[Position]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    recommendation_status_events: Mapped[list["RecommendationStatusEvent"]] = relationship(
        "RecommendationStatusEvent",
        back_populates="user",
    )
