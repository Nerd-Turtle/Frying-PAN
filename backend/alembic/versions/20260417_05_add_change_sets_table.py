"""Add change sets table

Revision ID: 20260417_05
Revises: 20260417_04
Create Date: 2026-04-17 23:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260417_05"
down_revision = "20260417_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "change_sets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("preview_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("operations_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_change_sets_project_id"), "change_sets", ["project_id"], unique=False)
    op.create_index(op.f("ix_change_sets_status"), "change_sets", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_change_sets_status"), table_name="change_sets")
    op.drop_index(op.f("ix_change_sets_project_id"), table_name="change_sets")
    op.drop_table("change_sets")
