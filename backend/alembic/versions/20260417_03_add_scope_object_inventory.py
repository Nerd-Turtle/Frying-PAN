"""Add scope, object, and parse warning inventory tables

Revision ID: 20260417_03
Revises: 20260417_02
Create Date: 2026-04-17 20:45:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260417_03"
down_revision = "20260417_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scopes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("parent_scope_id", sa.String(length=36), nullable=True),
        sa.Column("scope_type", sa.String(length=50), nullable=False),
        sa.Column("scope_name", sa.String(length=255), nullable=False),
        sa.Column("scope_path", sa.String(length=500), nullable=False),
        sa.Column("readonly_id", sa.String(length=64), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parent_scope_id"], ["scopes.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "scope_path", name="uq_scopes_source_path"),
    )
    op.create_index(op.f("ix_scopes_parent_scope_id"), "scopes", ["parent_scope_id"], unique=False)
    op.create_index(op.f("ix_scopes_project_id"), "scopes", ["project_id"], unique=False)
    op.create_index(op.f("ix_scopes_scope_type"), "scopes", ["scope_type"], unique=False)
    op.create_index(op.f("ix_scopes_source_id"), "scopes", ["source_id"], unique=False)

    op.create_table(
        "objects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("scope_id", sa.String(length=36), nullable=False),
        sa.Column("object_type", sa.String(length=100), nullable=False),
        sa.Column("object_name", sa.String(length=255), nullable=False),
        sa.Column("source_xpath", sa.String(length=1000), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("normalized_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("normalized_hash", sa.String(length=64), nullable=True),
        sa.Column("parse_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["scope_id"], ["scopes.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_id",
            "scope_id",
            "object_type",
            "object_name",
            name="uq_objects_source_scope_type_name",
        ),
    )
    op.create_index(op.f("ix_objects_normalized_hash"), "objects", ["normalized_hash"], unique=False)
    op.create_index(op.f("ix_objects_object_name"), "objects", ["object_name"], unique=False)
    op.create_index(op.f("ix_objects_object_type"), "objects", ["object_type"], unique=False)
    op.create_index(op.f("ix_objects_project_id"), "objects", ["project_id"], unique=False)
    op.create_index(op.f("ix_objects_scope_id"), "objects", ["scope_id"], unique=False)
    op.create_index(op.f("ix_objects_source_id"), "objects", ["source_id"], unique=False)

    op.create_table(
        "parse_warnings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("scope_id", sa.String(length=36), nullable=True),
        sa.Column("warning_type", sa.String(length=100), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source_xpath", sa.String(length=1000), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["scope_id"], ["scopes.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_parse_warnings_project_id"),
        "parse_warnings",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_parse_warnings_scope_id"),
        "parse_warnings",
        ["scope_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_parse_warnings_source_id"),
        "parse_warnings",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_parse_warnings_warning_type"),
        "parse_warnings",
        ["warning_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_parse_warnings_warning_type"), table_name="parse_warnings")
    op.drop_index(op.f("ix_parse_warnings_source_id"), table_name="parse_warnings")
    op.drop_index(op.f("ix_parse_warnings_scope_id"), table_name="parse_warnings")
    op.drop_index(op.f("ix_parse_warnings_project_id"), table_name="parse_warnings")
    op.drop_table("parse_warnings")

    op.drop_index(op.f("ix_objects_source_id"), table_name="objects")
    op.drop_index(op.f("ix_objects_scope_id"), table_name="objects")
    op.drop_index(op.f("ix_objects_project_id"), table_name="objects")
    op.drop_index(op.f("ix_objects_object_type"), table_name="objects")
    op.drop_index(op.f("ix_objects_object_name"), table_name="objects")
    op.drop_index(op.f("ix_objects_normalized_hash"), table_name="objects")
    op.drop_table("objects")

    op.drop_index(op.f("ix_scopes_source_id"), table_name="scopes")
    op.drop_index(op.f("ix_scopes_scope_type"), table_name="scopes")
    op.drop_index(op.f("ix_scopes_project_id"), table_name="scopes")
    op.drop_index(op.f("ix_scopes_parent_scope_id"), table_name="scopes")
    op.drop_table("scopes")
