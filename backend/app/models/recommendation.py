"""AI / rules-driven trade idea surfaced to the user."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import OrderSide, RecommendationSource, RecommendationStatus
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.position import Position
    from app.models.trade_order import TradeOrder
    from app.models.user import User
    from app.models.watchlist_item import WatchlistItem


class Recommendation(Base, TimestampMixin):
    """
    Copilot output the user may accept, dismiss, or let expire.

    Optional link to a `WatchlistItem` when the idea came from that context.
    """

    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    watchlist_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("watchlist_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    related_position_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "positions.id",
            ondelete="SET NULL",
            name="fk_recommendations_related_position_id_positions",
            use_alter=True,
        ),
        nullable=True,
        index=True,
    )

    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    side: Mapped[OrderSide] = mapped_column(
        SAEnum(OrderSide, native_enum=False, length=16),
        nullable=False,
    )
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[RecommendationStatus] = mapped_column(
        SAEnum(RecommendationStatus, native_enum=False, length=32),
        default=RecommendationStatus.PENDING,
        nullable=False,
        index=True,
    )
    source: Mapped[RecommendationSource] = mapped_column(
        SAEnum(RecommendationSource, native_enum=False, length=32),
        nullable=False,
    )

    recommended_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Engine / approval workflow (nullable for legacy copilot rows)
    recommendation_action: Mapped[str | None] = mapped_column(String(8), nullable=True)
    trade_direction: Mapped[str | None] = mapped_column(String(8), nullable=True)
    entry_price: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)
    stop_loss: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)
    take_profit: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)
    account_size_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)
    risk_percent_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    engine_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    user: Mapped[User] = relationship(back_populates="recommendations")
    related_position: Mapped["Position | None"] = relationship(
        "Position",
        back_populates="monitor_exit_recommendations",
        foreign_keys=[related_position_id],
    )
    watchlist_item: Mapped[WatchlistItem | None] = relationship(back_populates="recommendations")
    trade_orders: Mapped[list[TradeOrder]] = relationship(back_populates="recommendation")
    status_events: Mapped[list["RecommendationStatusEvent"]] = relationship(
        "RecommendationStatusEvent",
        back_populates="recommendation",
        cascade="all, delete-orphan",
    )
