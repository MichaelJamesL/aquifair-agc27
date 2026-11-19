"""create lead_feedback

Revision ID: 0001
Revises:
Create Date: 2026-11-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lead_feedback",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("lead_id", sa.String(length=64), nullable=False),
        sa.Column("inspector", sa.String(length=120), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("visited_at", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lead_feedback_lead_id"), "lead_feedback", ["lead_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_lead_feedback_lead_id"), table_name="lead_feedback")
    op.drop_table("lead_feedback")
