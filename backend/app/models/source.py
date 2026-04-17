from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Source(Base):
    __tablename__ = "sources"
    __table_args__ = (UniqueConstraint("project_id", "file_sha256", name="uq_sources_project_checksum"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    label: Mapped[str] = mapped_column(String(255))
    filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500), unique=True)
    file_sha256: Mapped[str] = mapped_column(String(64))
    source_type: Mapped[str] = mapped_column(String(50), default="panorama_xml")
    parse_status: Mapped[str] = mapped_column(String(50), default="uploaded")
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    project = relationship("Project", back_populates="sources")
