from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(320), unique=True, index=True, nullable=True)
    display_name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(50), default="operator", index=True)
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)
    must_change_password: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    organization_memberships = relationship(
        "OrganizationMembership",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    project_memberships = relationship(
        "ProjectMembership",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    sessions = relationship(
        "AppSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
