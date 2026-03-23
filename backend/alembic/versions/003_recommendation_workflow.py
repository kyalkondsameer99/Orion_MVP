"""Recommendation approval workflow columns and status event log.

Revision ID: 003
Revises: 002
Create Date: 2025-03-23

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "recommendations",
        sa.Column("recommendation_action", sa.String(length=8), nullable=True),
    )
    op.add_column(
        "recommendations",
        sa.Column("trade_direction", sa.String(length=8), nullable=True),
    )
    op.add_column(
        "recommendations",
        sa.Column("entry_price", sa.Numeric(precision=24, scale=8), nullable=True),
    )
    op.add_column(
        "recommendations",
        sa.Column("stop_loss", sa.Numeric(precision=24, scale=8), nullable=True),
    )
    op.add_column(
        "recommendations",
        sa.Column("take_profit", sa.Numeric(precision=24, scale=8), nullable=True),
    )
    op.add_column(
        "recommendations",
        sa.Column("quantity", sa.Numeric(precision=24, scale=8), nullable=True),
    )
    op.add_column(
        "recommendations",
        sa.Column("account_size_snapshot", sa.Numeric(precision=24, scale=8), nullable=True),
    )
    op.add_column(
        "recommendations",
        sa.Column("risk_percent_snapshot", sa.Numeric(precision=8, scale=4), nullable=True),
    )
    op.add_column(
        "recommendations",
        sa.Column("engine_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.create_table(
        "recommendation_status_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommendation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=False),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["recommendation_id"], ["recommendations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_recommendation_status_events_recommendation_id"),
        "recommendation_status_events",
        ["recommendation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_recommendation_status_events_user_id"),
        "recommendation_status_events",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_recommendation_status_events_created_at"),
        "recommendation_status_events",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_recommendation_status_events_created_at"), table_name="recommendation_status_events")
    op.drop_index(op.f("ix_recommendation_status_events_user_id"), table_name="recommendation_status_events")
    op.drop_index(op.f("ix_recommendation_status_events_recommendation_id"), table_name="recommendation_status_events")
    op.drop_table("recommendation_status_events")

    op.drop_column("recommendations", "engine_snapshot")
    op.drop_column("recommendations", "risk_percent_snapshot")
    op.drop_column("recommendations", "account_size_snapshot")
    op.drop_column("recommendations", "quantity")
    op.drop_column("recommendations", "take_profit")
    op.drop_column("recommendations", "stop_loss")
    op.drop_column("recommendations", "entry_price")
    op.drop_column("recommendations", "trade_direction")
    op.drop_column("recommendations", "recommendation_action")
