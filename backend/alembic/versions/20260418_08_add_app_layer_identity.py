"""Add app layer identity and access control tables

Revision ID: 20260418_08
Revises: 20260418_07
Create Date: 2026-04-18 03:10:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260418_08"
down_revision = "20260418_07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_status"), "users", ["status"], unique=False)

    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(
        op.f("ix_organizations_created_by_user_id"),
        "organizations",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(op.f("ix_organizations_slug"), "organizations", ["slug"], unique=True)

    op.create_table(
        "organization_memberships",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "user_id",
            name="uq_organization_memberships_org_user",
        ),
    )
    op.create_index(
        op.f("ix_organization_memberships_organization_id"),
        "organization_memberships",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organization_memberships_user_id"),
        "organization_memberships",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "app_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(op.f("ix_app_sessions_expires_at"), "app_sessions", ["expires_at"], unique=False)
    op.create_index(op.f("ix_app_sessions_token_hash"), "app_sessions", ["token_hash"], unique=True)
    op.create_index(op.f("ix_app_sessions_user_id"), "app_sessions", ["user_id"], unique=False)

    op.add_column("projects", sa.Column("organization_id", sa.String(length=36), nullable=True))
    op.add_column("projects", sa.Column("created_by_user_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(None, "projects", "organizations", ["organization_id"], ["id"])
    op.create_foreign_key(None, "projects", "users", ["created_by_user_id"], ["id"])
    op.create_index(op.f("ix_projects_organization_id"), "projects", ["organization_id"], unique=False)
    op.create_index(op.f("ix_projects_created_by_user_id"), "projects", ["created_by_user_id"], unique=False)

    op.drop_index(op.f("ix_projects_name"), table_name="projects")
    op.create_unique_constraint(
        "uq_projects_org_name",
        "projects",
        ["organization_id", "name"],
    )
    op.create_index(op.f("ix_projects_name"), "projects", ["name"], unique=False)

    op.create_table(
        "project_memberships",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "user_id",
            name="uq_project_memberships_project_user",
        ),
    )
    op.create_index(
        op.f("ix_project_memberships_project_id"),
        "project_memberships",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_memberships_user_id"),
        "project_memberships",
        ["user_id"],
        unique=False,
    )

    op.add_column("events", sa.Column("actor_user_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(None, "events", "users", ["actor_user_id"], ["id"])
    op.create_index(op.f("ix_events_actor_user_id"), "events", ["actor_user_id"], unique=False)

    op.add_column("sources", sa.Column("imported_by_user_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(None, "sources", "users", ["imported_by_user_id"], ["id"])
    op.create_index(
        op.f("ix_sources_imported_by_user_id"),
        "sources",
        ["imported_by_user_id"],
        unique=False,
    )

    op.add_column("change_sets", sa.Column("created_by_user_id", sa.String(length=36), nullable=True))
    op.add_column("change_sets", sa.Column("applied_by_user_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(None, "change_sets", "users", ["created_by_user_id"], ["id"])
    op.create_foreign_key(None, "change_sets", "users", ["applied_by_user_id"], ["id"])
    op.create_index(
        op.f("ix_change_sets_created_by_user_id"),
        "change_sets",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_change_sets_applied_by_user_id"),
        "change_sets",
        ["applied_by_user_id"],
        unique=False,
    )

    op.add_column("exports", sa.Column("created_by_user_id", sa.String(length=36), nullable=True))
    op.create_foreign_key(None, "exports", "users", ["created_by_user_id"], ["id"])
    op.create_index(
        op.f("ix_exports_created_by_user_id"),
        "exports",
        ["created_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_exports_created_by_user_id"), table_name="exports")
    op.drop_constraint(None, "exports", type_="foreignkey")
    op.drop_column("exports", "created_by_user_id")

    op.drop_index(op.f("ix_change_sets_applied_by_user_id"), table_name="change_sets")
    op.drop_index(op.f("ix_change_sets_created_by_user_id"), table_name="change_sets")
    op.drop_constraint(None, "change_sets", type_="foreignkey")
    op.drop_constraint(None, "change_sets", type_="foreignkey")
    op.drop_column("change_sets", "applied_by_user_id")
    op.drop_column("change_sets", "created_by_user_id")

    op.drop_index(op.f("ix_sources_imported_by_user_id"), table_name="sources")
    op.drop_constraint(None, "sources", type_="foreignkey")
    op.drop_column("sources", "imported_by_user_id")

    op.drop_index(op.f("ix_events_actor_user_id"), table_name="events")
    op.drop_constraint(None, "events", type_="foreignkey")
    op.drop_column("events", "actor_user_id")

    op.drop_index(op.f("ix_project_memberships_user_id"), table_name="project_memberships")
    op.drop_index(op.f("ix_project_memberships_project_id"), table_name="project_memberships")
    op.drop_table("project_memberships")

    op.drop_constraint("uq_projects_org_name", "projects", type_="unique")
    op.drop_index(op.f("ix_projects_name"), table_name="projects")
    op.create_index(op.f("ix_projects_name"), "projects", ["name"], unique=True)
    op.drop_index(op.f("ix_projects_created_by_user_id"), table_name="projects")
    op.drop_index(op.f("ix_projects_organization_id"), table_name="projects")
    op.drop_constraint(None, "projects", type_="foreignkey")
    op.drop_constraint(None, "projects", type_="foreignkey")
    op.drop_column("projects", "created_by_user_id")
    op.drop_column("projects", "organization_id")

    op.drop_index(op.f("ix_app_sessions_user_id"), table_name="app_sessions")
    op.drop_index(op.f("ix_app_sessions_token_hash"), table_name="app_sessions")
    op.drop_index(op.f("ix_app_sessions_expires_at"), table_name="app_sessions")
    op.drop_table("app_sessions")

    op.drop_index(
        op.f("ix_organization_memberships_user_id"),
        table_name="organization_memberships",
    )
    op.drop_index(
        op.f("ix_organization_memberships_organization_id"),
        table_name="organization_memberships",
    )
    op.drop_table("organization_memberships")

    op.drop_index(op.f("ix_organizations_slug"), table_name="organizations")
    op.drop_index(op.f("ix_organizations_created_by_user_id"), table_name="organizations")
    op.drop_table("organizations")

    op.drop_index(op.f("ix_users_status"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
