"""Add notification settings singleton table

Revision ID: 20260422_01
Revises: 20260419_01
Create Date: 2026-04-22 00:10:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260422_01"
down_revision = "20260419_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("notification_timeout_seconds", sa.Integer(), nullable=False, server_default="10"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        """
        INSERT INTO app_settings (id, notification_timeout_seconds)
        VALUES (1, 10)
        """
    )
    op.alter_column("app_settings", "notification_timeout_seconds", server_default=None)


def downgrade() -> None:
    op.drop_table("app_settings")
