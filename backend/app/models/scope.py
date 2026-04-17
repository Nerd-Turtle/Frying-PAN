from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Scope(Base):
    __tablename__ = "scopes"
    __table_args__ = (
        UniqueConstraint("source_id", "scope_path", name="uq_scopes_source_path"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id"), index=True)
    parent_scope_id: Mapped[str | None] = mapped_column(
        ForeignKey("scopes.id"),
        nullable=True,
        index=True,
    )
    scope_type: Mapped[str] = mapped_column(String(50), index=True)
    scope_name: Mapped[str] = mapped_column(String(255))
    scope_path: Mapped[str] = mapped_column(String(500))
    readonly_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    source = relationship("Source", back_populates="scopes")
    parent_scope = relationship("Scope", remote_side="Scope.id", back_populates="child_scopes")
    child_scopes = relationship("Scope", back_populates="parent_scope")
    objects = relationship(
        "ConfigObject",
        back_populates="scope",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
