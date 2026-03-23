"""Replace scaffold with full paper-trading domain tables.

Revision ID: 002
Revises: 001
Create Date: 2025-03-23

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f("ix_paper_positions_symbol"), table_name="paper_positions")
    op.drop_table("paper_positions")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "broker_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("external_account_id", sa.String(length=128), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("is_paper", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("credential_secret_ref", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "provider",
            "external_account_id",
            name="uq_broker_connection_user_provider_account",
        ),
    )
    op.create_index(
        op.f("ix_broker_connections_user_id"),
        "broker_connections",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_broker_connections_provider"),
        "broker_connections",
        ["provider"],
        unique=False,
    )

    op.create_table(
        "watchlist_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "symbol", name="uq_watchlist_user_symbol"),
    )
    op.create_index(
        op.f("ix_watchlist_items_user_id"),
        "watchlist_items",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_watchlist_items_symbol"),
        "watchlist_items",
        ["symbol"],
        unique=False,
    )

    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("watchlist_item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("side", sa.String(length=16), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("recommended_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["watchlist_item_id"], ["watchlist_items.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_recommendations_user_id"),
        "recommendations",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_recommendations_watchlist_item_id"),
        "recommendations",
        ["watchlist_item_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_recommendations_symbol"),
        "recommendations",
        ["symbol"],
        unique=False,
    )
    op.create_index(
        op.f("ix_recommendations_status"),
        "recommendations",
        ["status"],
        unique=False,
    )

    op.create_table(
        "trade_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("broker_connection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recommendation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("client_order_id", sa.String(length=128), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("side", sa.String(length=16), nullable=False),
        sa.Column("order_type", sa.String(length=32), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=24, scale=8), nullable=False),
        sa.Column("limit_price", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("stop_price", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("filled_quantity", sa.Numeric(precision=24, scale=8), nullable=False),
        sa.Column("avg_fill_price", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("time_in_force", sa.String(length=16), nullable=True),
        sa.Column("paper_trade", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("filled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["broker_connection_id"], ["broker_connections.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["recommendation_id"], ["recommendations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_trade_orders_user_id"),
        "trade_orders",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_trade_orders_broker_connection_id"),
        "trade_orders",
        ["broker_connection_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_trade_orders_recommendation_id"),
        "trade_orders",
        ["recommendation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_trade_orders_client_order_id"),
        "trade_orders",
        ["client_order_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_trade_orders_symbol"),
        "trade_orders",
        ["symbol"],
        unique=False,
    )
    op.create_index(
        op.f("ix_trade_orders_status"),
        "trade_orders",
        ["status"],
        unique=False,
    )

    op.create_table(
        "positions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("broker_connection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("opening_trade_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("side", sa.String(length=16), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=24, scale=8), nullable=False),
        sa.Column("avg_entry_price", sa.Numeric(precision=24, scale=8), nullable=False),
        sa.Column("unrealized_pnl", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("realized_pnl", sa.Numeric(precision=24, scale=8), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["broker_connection_id"], ["broker_connections.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["opening_trade_order_id"], ["trade_orders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_positions_user_id"),
        "positions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_positions_broker_connection_id"),
        "positions",
        ["broker_connection_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_positions_opening_trade_order_id"),
        "positions",
        ["opening_trade_order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_positions_symbol"),
        "positions",
        ["symbol"],
        unique=False,
    )
    op.create_index(
        op.f("ix_positions_status"),
        "positions",
        ["status"],
        unique=False,
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_type", sa.String(length=16), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audit_logs_user_id"),
        "audit_logs",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_action"),
        "audit_logs",
        ["action"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_resource_type"),
        "audit_logs",
        ["resource_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_resource_id"),
        "audit_logs",
        ["resource_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_created_at"),
        "audit_logs",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_logs_created_at"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_resource_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_resource_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index(op.f("ix_positions_status"), table_name="positions")
    op.drop_index(op.f("ix_positions_symbol"), table_name="positions")
    op.drop_index(op.f("ix_positions_opening_trade_order_id"), table_name="positions")
    op.drop_index(op.f("ix_positions_broker_connection_id"), table_name="positions")
    op.drop_index(op.f("ix_positions_user_id"), table_name="positions")
    op.drop_table("positions")

    op.drop_index(op.f("ix_trade_orders_status"), table_name="trade_orders")
    op.drop_index(op.f("ix_trade_orders_symbol"), table_name="trade_orders")
    op.drop_index(op.f("ix_trade_orders_client_order_id"), table_name="trade_orders")
    op.drop_index(op.f("ix_trade_orders_recommendation_id"), table_name="trade_orders")
    op.drop_index(op.f("ix_trade_orders_broker_connection_id"), table_name="trade_orders")
    op.drop_index(op.f("ix_trade_orders_user_id"), table_name="trade_orders")
    op.drop_table("trade_orders")

    op.drop_index(op.f("ix_recommendations_status"), table_name="recommendations")
    op.drop_index(op.f("ix_recommendations_symbol"), table_name="recommendations")
    op.drop_index(op.f("ix_recommendations_watchlist_item_id"), table_name="recommendations")
    op.drop_index(op.f("ix_recommendations_user_id"), table_name="recommendations")
    op.drop_table("recommendations")

    op.drop_index(op.f("ix_watchlist_items_symbol"), table_name="watchlist_items")
    op.drop_index(op.f("ix_watchlist_items_user_id"), table_name="watchlist_items")
    op.drop_table("watchlist_items")

    op.drop_index(op.f("ix_broker_connections_provider"), table_name="broker_connections")
    op.drop_index(op.f("ix_broker_connections_user_id"), table_name="broker_connections")
    op.drop_table("broker_connections")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.create_table(
        "paper_positions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("side", sa.String(length=8), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=24, scale=8), nullable=False),
        sa.Column("avg_entry_price", sa.Numeric(precision=24, scale=8), nullable=False),
        sa.Column(
            "opened_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_paper_positions_symbol"),
        "paper_positions",
        ["symbol"],
        unique=False,
    )
