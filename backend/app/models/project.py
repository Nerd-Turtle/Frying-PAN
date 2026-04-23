from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_projects_org_name"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    organization_id: Mapped[str | None] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    visibility: Mapped[str] = mapped_column(String(20), default="public", index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"),
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
    created_by_user = relationship("User", foreign_keys=[created_by_user_id], lazy="joined")

    sources = relationship(
        "Source",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    events = relationship(
        "EventRecord",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="desc(EventRecord.created_at)",
    )
    memberships = relationship(
        "ProjectMembership",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProjectMembership.created_at",
    )
    organization = relationship("Organization", back_populates="projects", lazy="joined")

    @property
    def created_by_display_name(self) -> str | None:
        if self.created_by_user is None:
            return None
        return self.created_by_user.display_name

    @property
    def owner_user_id(self) -> str | None:
        owner_membership = next(
            (membership for membership in self.memberships if membership.role == "owner"),
            None,
        )
        if owner_membership is None:
            return None
        return owner_membership.user_id

    @property
    def owner_display_name(self) -> str | None:
        owner_membership = next(
            (membership for membership in self.memberships if membership.role == "owner"),
            None,
        )
        if owner_membership is None or owner_membership.user is None:
            return None
        return owner_membership.user.display_name

    @property
    def collaborators(self) -> list["ProjectMembership"]:
        return [membership for membership in self.memberships if membership.role != "owner"]
