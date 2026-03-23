"""Linked broker account (paper or live) for a user."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import BrokerProvider, ConnectionStatus
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.position import Position
    from app.models.trade_order import TradeOrder
    from app.models.user import User


class BrokerConnection(Base, TimestampMixin):
    """
    Credentials / routing for a broker API.

    Store only opaque references to secrets (vault/KMS) in `credential_secret_ref`.
    """

    __tablename__ = "broker_connections"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "provider",
            "external_account_id",
            name="uq_broker_connection_user_provider_account",
        ),
    )

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

    provider: Mapped[BrokerProvider] = mapped_column(
        SAEnum(BrokerProvider, native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    external_account_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_paper: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    credential_secret_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[ConnectionStatus] = mapped_column(
        SAEnum(ConnectionStatus, native_enum=False, length=32),
        default=ConnectionStatus.PENDING,
        nullable=False,
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_sync_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="broker_connections")
    trade_orders: Mapped[list[TradeOrder]] = relationship(back_populates="broker_connection")
    positions: Mapped[list[Position]] = relationship(back_populates="broker_connection")
