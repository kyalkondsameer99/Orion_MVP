"""Executable order — paper or routed to a broker adapter."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import OrderSide, OrderStatus, OrderType, TimeInForce
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.broker_connection import BrokerConnection
    from app.models.position import Position
    from app.models.recommendation import Recommendation
    from app.models.user import User


class TradeOrder(Base, TimestampMixin):
    """
    Order lifecycle for paper trading or broker execution.

    `client_order_id` must be unique for idempotency with brokers / internal routing.
    """

    __tablename__ = "trade_orders"

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
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recommendations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    client_order_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    side: Mapped[OrderSide] = mapped_column(
        SAEnum(OrderSide, native_enum=False, length=16),
        nullable=False,
    )
    order_type: Mapped[OrderType] = mapped_column(
        SAEnum(OrderType, native_enum=False, length=32),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    limit_price: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)
    stop_price: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)

    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, native_enum=False, length=32),
        default=OrderStatus.NEW,
        nullable=False,
        index=True,
    )
    filled_quantity: Mapped[Decimal] = mapped_column(Numeric(24, 8), default=Decimal("0"), nullable=False)
    avg_fill_price: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)

    time_in_force: Mapped[TimeInForce | None] = mapped_column(
        SAEnum(TimeInForce, native_enum=False, length=16),
        nullable=True,
    )
    paper_trade: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    submitted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    filled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="trade_orders")
    broker_connection: Mapped[BrokerConnection | None] = relationship(back_populates="trade_orders")
    recommendation: Mapped[Recommendation | None] = relationship(back_populates="trade_orders")
    positions_opened: Mapped[list[Position]] = relationship(
        back_populates="opening_trade_order",
    )
