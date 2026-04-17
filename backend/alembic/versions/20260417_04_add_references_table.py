"""Add canonical references table

Revision ID: 20260417_04
Revises: 20260417_03
Create Date: 2026-04-17 22:10:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260417_04"
down_revision = "20260417_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "references",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("owner_object_id", sa.String(length=36), nullable=False),
        sa.Column("reference_kind", sa.String(length=100), nullable=False),
        sa.Column("reference_path", sa.String(length=500), nullable=False),
        sa.Column("target_name", sa.String(length=255), nullable=False),
        sa.Column("target_type_hint", sa.String(length=255), nullable=True),
        sa.Column("target_scope_hint", sa.String(length=500), nullable=True),
        sa.Column("resolved_object_id", sa.String(length=36), nullable=True),
        sa.Column("resolution_status", sa.String(length=100), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_object_id"], ["objects.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["resolved_object_id"], ["objects.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_references_owner_object_id"),
        "references",
        ["owner_object_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_references_project_id"),
        "references",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_references_reference_kind"),
        "references",
        ["reference_kind"],
        unique=False,
    )
    op.create_index(
        op.f("ix_references_resolution_status"),
        "references",
        ["resolution_status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_references_resolved_object_id"),
        "references",
        ["resolved_object_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_references_source_id"),
        "references",
        ["source_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_references_target_name"),
        "references",
        ["target_name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_references_target_name"), table_name="references")
    op.drop_index(op.f("ix_references_source_id"), table_name="references")
    op.drop_index(op.f("ix_references_resolved_object_id"), table_name="references")
    op.drop_index(op.f("ix_references_resolution_status"), table_name="references")
    op.drop_index(op.f("ix_references_reference_kind"), table_name="references")
    op.drop_index(op.f("ix_references_project_id"), table_name="references")
    op.drop_index(op.f("ix_references_owner_object_id"), table_name="references")
    op.drop_table("references")
