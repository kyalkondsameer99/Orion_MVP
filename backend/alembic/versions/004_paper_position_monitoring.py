"""Paper position monitoring: SL/TP columns and link exit recommendations."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "positions",
        sa.Column("stop_loss_price", sa.Numeric(precision=24, scale=8), nullable=True),
    )
    op.add_column(
        "positions",
        sa.Column("take_profit_price", sa.Numeric(precision=24, scale=8), nullable=True),
    )
    op.add_column(
        "recommendations",
        sa.Column("related_position_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_recommendations_related_position_id_positions"),
        "recommendations",
        "positions",
        ["related_position_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_recommendations_related_position_id"),
        "recommendations",
        ["related_position_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_recommendations_related_position_id"), table_name="recommendations")
    op.drop_constraint(
        op.f("fk_recommendations_related_position_id_positions"),
        "recommendations",
        type_="foreignkey",
    )
    op.drop_column("recommendations", "related_position_id")
    op.drop_column("positions", "take_profit_price")
    op.drop_column("positions", "stop_loss_price")
