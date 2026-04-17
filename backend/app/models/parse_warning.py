from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ParseWarning(Base):
    __tablename__ = "parse_warnings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id"), index=True)
    scope_id: Mapped[str | None] = mapped_column(
        ForeignKey("scopes.id"),
        nullable=True,
        index=True,
    )
    warning_type: Mapped[str] = mapped_column(String(100), index=True)
    message: Mapped[str] = mapped_column(Text)
    source_xpath: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    source = relationship("Source", back_populates="parse_warnings")
    scope = relationship("Scope")
