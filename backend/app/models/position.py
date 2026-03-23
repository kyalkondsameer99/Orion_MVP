"""Open or closed portfolio position (paper or synced from broker)."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import PositionSide, PositionStatus
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.broker_connection import BrokerConnection
    from app.models.recommendation import Recommendation
    from app.models.trade_order import TradeOrder
    from app.models.user import User


class Position(Base, TimestampMixin):
    """
    Holdings snapshot for paper trading.

    `opening_trade_order_id` links the position to the order that opened it (optional).
    """

    __tablename__ = "positions"

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
    broker_connection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("broker_connections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    opening_trade_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trade_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    side: Mapped[PositionSide] = mapped_column(
        SAEnum(PositionSide, native_enum=False, length=16),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    avg_entry_price: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    stop_loss_price: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)
    take_profit_price: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)
    unrealized_pnl: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)
    realized_pnl: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)

    status: Mapped[PositionStatus] = mapped_column(
        SAEnum(PositionStatus, native_enum=False, length=16),
        default=PositionStatus.OPEN,
        nullable=False,
        index=True,
    )
    opened_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="positions")
    broker_connection: Mapped[BrokerConnection | None] = relationship(back_populates="positions")
    opening_trade_order: Mapped[TradeOrder | None] = relationship(
        back_populates="positions_opened",
        foreign_keys=[opening_trade_order_id],
    )
    monitor_exit_recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation",
        back_populates="related_position",
    )
