"""Add exports table

Revision ID: 20260418_07
Revises: 20260418_06
Create Date: 2026-04-18 00:55:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260418_07"
down_revision = "20260418_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("change_set_id", sa.String(length=36), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("file_sha256", sa.String(length=64), nullable=False),
        sa.Column("export_status", sa.String(length=50), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["change_set_id"], ["change_sets.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_path"),
    )
    op.create_index(op.f("ix_exports_change_set_id"), "exports", ["change_set_id"], unique=False)
    op.create_index(op.f("ix_exports_export_status"), "exports", ["export_status"], unique=False)
    op.create_index(op.f("ix_exports_project_id"), "exports", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_exports_project_id"), table_name="exports")
    op.drop_index(op.f("ix_exports_export_status"), table_name="exports")
    op.drop_index(op.f("ix_exports_change_set_id"), table_name="exports")
    op.drop_table("exports")
