from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ConfigObject(Base):
    __tablename__ = "objects"
    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "scope_id",
            "object_type",
            "object_name",
            name="uq_objects_source_scope_type_name",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id"), index=True)
    scope_id: Mapped[str] = mapped_column(ForeignKey("scopes.id"), index=True)
    object_type: Mapped[str] = mapped_column(String(100), index=True)
    object_name: Mapped[str] = mapped_column(String(255), index=True)
    source_xpath: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSONB)
    normalized_payload: Mapped[dict] = mapped_column(JSONB)
    normalized_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    parse_status: Mapped[str] = mapped_column(String(50), default="parsed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    source = relationship("Source", back_populates="objects")
    scope = relationship("Scope", back_populates="objects")
    outgoing_references = relationship(
        "ConfigReference",
        foreign_keys="ConfigReference.owner_object_id",
        back_populates="owner_object",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    incoming_references = relationship(
        "ConfigReference",
        foreign_keys="ConfigReference.resolved_object_id",
        back_populates="resolved_object",
        lazy="selectin",
    )
