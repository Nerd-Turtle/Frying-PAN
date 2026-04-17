"""Expand sources metadata

Revision ID: 20260417_02
Revises: 20260417_01
Create Date: 2026-04-17 20:05:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260417_02"
down_revision = "20260417_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sources", sa.Column("label", sa.String(length=255), nullable=True))
    op.add_column("sources", sa.Column("file_sha256", sa.String(length=64), nullable=True))
    op.add_column("sources", sa.Column("source_type", sa.String(length=50), nullable=True))
    op.add_column("sources", sa.Column("imported_at", sa.DateTime(timezone=True), nullable=True))

    op.execute("UPDATE sources SET label = filename WHERE label IS NULL")
    op.execute(
        "UPDATE sources SET file_sha256 = CONCAT('legacy-', id) WHERE file_sha256 IS NULL"
    )
    op.execute("UPDATE sources SET source_type = kind WHERE source_type IS NULL")
    op.execute("UPDATE sources SET imported_at = uploaded_at WHERE imported_at IS NULL")

    op.alter_column("sources", "label", nullable=False)
    op.alter_column("sources", "file_sha256", nullable=False)
    op.alter_column("sources", "source_type", nullable=False)
    op.alter_column("sources", "imported_at", nullable=False)

    op.create_unique_constraint(
        "uq_sources_project_checksum",
        "sources",
        ["project_id", "file_sha256"],
    )

    op.drop_column("sources", "kind")
    op.drop_column("sources", "uploaded_at")


def downgrade() -> None:
    op.add_column("sources", sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("sources", sa.Column("kind", sa.String(length=50), nullable=True))

    op.execute("UPDATE sources SET kind = source_type WHERE kind IS NULL")
    op.execute("UPDATE sources SET uploaded_at = imported_at WHERE uploaded_at IS NULL")

    op.alter_column("sources", "kind", nullable=False)
    op.alter_column("sources", "uploaded_at", nullable=False)

    op.drop_constraint("uq_sources_project_checksum", "sources", type_="unique")
    op.drop_column("sources", "imported_at")
    op.drop_column("sources", "source_type")
    op.drop_column("sources", "file_sha256")
    op.drop_column("sources", "label")
