from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ConfigReference(Base):
    __tablename__ = "references"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id"), index=True)
    owner_object_id: Mapped[str] = mapped_column(ForeignKey("objects.id"), index=True)
    reference_kind: Mapped[str] = mapped_column(String(100), index=True)
    reference_path: Mapped[str] = mapped_column(String(500))
    target_name: Mapped[str] = mapped_column(String(255), index=True)
    target_type_hint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_scope_hint: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resolved_object_id: Mapped[str | None] = mapped_column(
        ForeignKey("objects.id"),
        nullable=True,
        index=True,
    )
    resolution_status: Mapped[str] = mapped_column(String(100), index=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    source = relationship("Source", back_populates="references")
    owner_object = relationship(
        "ConfigObject",
        foreign_keys=[owner_object_id],
        back_populates="outgoing_references",
    )
    resolved_object = relationship(
        "ConfigObject",
        foreign_keys=[resolved_object_id],
        back_populates="incoming_references",
    )
