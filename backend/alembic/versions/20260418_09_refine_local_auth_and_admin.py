"""Refine local auth and admin management

Revision ID: 20260418_09
Revises: 20260418_08
Create Date: 2026-04-18 21:20:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260418_09"
down_revision = "20260418_08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("role", sa.String(length=50), nullable=False, server_default="operator"))
    op.add_column(
        "users",
        sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("users", "email", existing_type=sa.String(length=320), nullable=True)

    op.execute(
        """
        UPDATE users
        SET username = lower(
            coalesce(nullif(split_part(email, '@', 1), ''), 'user') || '-' || substr(id, 1, 8)
        )
        WHERE username IS NULL
        """
    )

    op.alter_column("users", "username", existing_type=sa.String(length=64), nullable=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    op.alter_column("users", "role", server_default=None)
    op.alter_column("users", "must_change_password", server_default=None)

    op.create_table(
        "app_audit_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_app_audit_events_actor_user_id"),
        "app_audit_events",
        ["actor_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_app_audit_events_event_type"),
        "app_audit_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_app_audit_events_project_id"),
        "app_audit_events",
        ["project_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_app_audit_events_project_id"), table_name="app_audit_events")
    op.drop_index(op.f("ix_app_audit_events_event_type"), table_name="app_audit_events")
    op.drop_index(op.f("ix_app_audit_events_actor_user_id"), table_name="app_audit_events")
    op.drop_table("app_audit_events")

    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.alter_column("users", "email", existing_type=sa.String(length=320), nullable=False)
    op.drop_column("users", "must_change_password")
    op.drop_column("users", "role")
    op.drop_column("users", "username")
