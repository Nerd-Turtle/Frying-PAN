"""Add working state tables

Revision ID: 20260418_06
Revises: 20260417_05
Create Date: 2026-04-18 00:10:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260418_06"
down_revision = "20260417_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "working_objects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("source_object_id", sa.String(length=36), nullable=False),
        sa.Column("scope_id", sa.String(length=36), nullable=False),
        sa.Column("object_type", sa.String(length=100), nullable=False),
        sa.Column("object_name", sa.String(length=255), nullable=False),
        sa.Column("source_xpath", sa.String(length=1000), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("normalized_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("normalized_hash", sa.String(length=64), nullable=True),
        sa.Column("state_status", sa.String(length=50), nullable=False),
        sa.Column("last_change_set_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["last_change_set_id"], ["change_sets.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["scope_id"], ["scopes.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.ForeignKeyConstraint(["source_object_id"], ["objects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "source_object_id",
            name="uq_working_objects_project_source_object",
        ),
    )
    op.create_index(op.f("ix_working_objects_last_change_set_id"), "working_objects", ["last_change_set_id"], unique=False)
    op.create_index(op.f("ix_working_objects_normalized_hash"), "working_objects", ["normalized_hash"], unique=False)
    op.create_index(op.f("ix_working_objects_object_name"), "working_objects", ["object_name"], unique=False)
    op.create_index(op.f("ix_working_objects_object_type"), "working_objects", ["object_type"], unique=False)
    op.create_index(op.f("ix_working_objects_project_id"), "working_objects", ["project_id"], unique=False)
    op.create_index(op.f("ix_working_objects_scope_id"), "working_objects", ["scope_id"], unique=False)
    op.create_index(op.f("ix_working_objects_source_id"), "working_objects", ["source_id"], unique=False)
    op.create_index(op.f("ix_working_objects_source_object_id"), "working_objects", ["source_object_id"], unique=False)

    op.create_table(
        "working_references",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("source_reference_id", sa.String(length=36), nullable=False),
        sa.Column("owner_object_id", sa.String(length=36), nullable=False),
        sa.Column("reference_kind", sa.String(length=100), nullable=False),
        sa.Column("reference_path", sa.String(length=500), nullable=False),
        sa.Column("target_name", sa.String(length=255), nullable=False),
        sa.Column("target_type_hint", sa.String(length=255), nullable=True),
        sa.Column("target_scope_hint", sa.String(length=500), nullable=True),
        sa.Column("resolved_object_id", sa.String(length=36), nullable=True),
        sa.Column("resolution_status", sa.String(length=100), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("last_change_set_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["last_change_set_id"], ["change_sets.id"]),
        sa.ForeignKeyConstraint(["owner_object_id"], ["working_objects.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["resolved_object_id"], ["working_objects.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.ForeignKeyConstraint(["source_reference_id"], ["references.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "source_reference_id",
            name="uq_working_references_project_source_reference",
        ),
    )
    op.create_index(op.f("ix_working_references_last_change_set_id"), "working_references", ["last_change_set_id"], unique=False)
    op.create_index(op.f("ix_working_references_owner_object_id"), "working_references", ["owner_object_id"], unique=False)
    op.create_index(op.f("ix_working_references_project_id"), "working_references", ["project_id"], unique=False)
    op.create_index(op.f("ix_working_references_reference_kind"), "working_references", ["reference_kind"], unique=False)
    op.create_index(op.f("ix_working_references_resolution_status"), "working_references", ["resolution_status"], unique=False)
    op.create_index(op.f("ix_working_references_resolved_object_id"), "working_references", ["resolved_object_id"], unique=False)
    op.create_index(op.f("ix_working_references_source_id"), "working_references", ["source_id"], unique=False)
    op.create_index(op.f("ix_working_references_source_reference_id"), "working_references", ["source_reference_id"], unique=False)
    op.create_index(op.f("ix_working_references_target_name"), "working_references", ["target_name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_working_references_target_name"), table_name="working_references")
    op.drop_index(op.f("ix_working_references_source_reference_id"), table_name="working_references")
    op.drop_index(op.f("ix_working_references_source_id"), table_name="working_references")
    op.drop_index(op.f("ix_working_references_resolved_object_id"), table_name="working_references")
    op.drop_index(op.f("ix_working_references_resolution_status"), table_name="working_references")
    op.drop_index(op.f("ix_working_references_reference_kind"), table_name="working_references")
    op.drop_index(op.f("ix_working_references_project_id"), table_name="working_references")
    op.drop_index(op.f("ix_working_references_owner_object_id"), table_name="working_references")
    op.drop_index(op.f("ix_working_references_last_change_set_id"), table_name="working_references")
    op.drop_table("working_references")

    op.drop_index(op.f("ix_working_objects_source_object_id"), table_name="working_objects")
    op.drop_index(op.f("ix_working_objects_source_id"), table_name="working_objects")
    op.drop_index(op.f("ix_working_objects_scope_id"), table_name="working_objects")
    op.drop_index(op.f("ix_working_objects_project_id"), table_name="working_objects")
    op.drop_index(op.f("ix_working_objects_object_type"), table_name="working_objects")
    op.drop_index(op.f("ix_working_objects_object_name"), table_name="working_objects")
    op.drop_index(op.f("ix_working_objects_normalized_hash"), table_name="working_objects")
    op.drop_index(op.f("ix_working_objects_last_change_set_id"), table_name="working_objects")
    op.drop_table("working_objects")
