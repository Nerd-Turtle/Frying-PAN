"""Add project visibility controls

Revision ID: 20260423_01
Revises: 20260422_01
Create Date: 2026-04-23 00:20:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260423_01"
down_revision = "20260422_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("visibility", sa.String(length=20), nullable=False, server_default="public"),
    )
    op.create_index(op.f("ix_projects_visibility"), "projects", ["visibility"], unique=False)
    op.execute("UPDATE projects SET visibility = 'public' WHERE visibility IS NULL")
    op.alter_column("projects", "visibility", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_projects_visibility"), table_name="projects")
    op.drop_column("projects", "visibility")
