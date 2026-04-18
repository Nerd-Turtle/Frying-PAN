from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WorkingReference(Base):
    __tablename__ = "working_references"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "source_reference_id",
            name="uq_working_references_project_source_reference",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id"), index=True)
    source_reference_id: Mapped[str] = mapped_column(ForeignKey("references.id"), index=True)
    owner_object_id: Mapped[str] = mapped_column(ForeignKey("working_objects.id"), index=True)
    reference_kind: Mapped[str] = mapped_column(String(100), index=True)
    reference_path: Mapped[str] = mapped_column(String(500))
    target_name: Mapped[str] = mapped_column(String(255), index=True)
    target_type_hint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_scope_hint: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resolved_object_id: Mapped[str | None] = mapped_column(
        ForeignKey("working_objects.id"),
        nullable=True,
        index=True,
    )
    resolution_status: Mapped[str] = mapped_column(String(100), index=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    last_change_set_id: Mapped[str | None] = mapped_column(
        ForeignKey("change_sets.id"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    owner_object = relationship("WorkingObject", foreign_keys=[owner_object_id])
    resolved_object = relationship("WorkingObject", foreign_keys=[resolved_object_id])
