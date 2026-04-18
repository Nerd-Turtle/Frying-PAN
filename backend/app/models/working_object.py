from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WorkingObject(Base):
    __tablename__ = "working_objects"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "source_object_id",
            name="uq_working_objects_project_source_object",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id"), index=True)
    source_object_id: Mapped[str] = mapped_column(ForeignKey("objects.id"), index=True)
    scope_id: Mapped[str] = mapped_column(ForeignKey("scopes.id"), index=True)
    object_type: Mapped[str] = mapped_column(String(100), index=True)
    object_name: Mapped[str] = mapped_column(String(255), index=True)
    source_xpath: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSONB)
    normalized_payload: Mapped[dict] = mapped_column(JSONB)
    normalized_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    state_status: Mapped[str] = mapped_column(String(50), default="active")
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

    scope = relationship("Scope")
