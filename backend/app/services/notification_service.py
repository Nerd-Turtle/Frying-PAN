from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.app_audit_event import AppAuditEvent
from app.models.app_settings import AppSettings
from app.models.user import User
from app.schemas.notification import NotificationHistoryEntryRead


def get_or_create_app_settings(db: Session) -> AppSettings:
    settings = db.get(AppSettings, 1)
    if settings is None:
        settings = AppSettings(id=1, notification_timeout_seconds=10)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_notification_timeout(db: Session, timeout_seconds: int) -> AppSettings:
    settings = get_or_create_app_settings(db)
    settings.notification_timeout_seconds = timeout_seconds
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def list_notification_history(
    db: Session,
    user: User,
    limit: int = 25,
) -> list[NotificationHistoryEntryRead]:
    statement = (
        select(AppAuditEvent)
        .options(
            joinedload(AppAuditEvent.actor),
            joinedload(AppAuditEvent.project),
        )
        .order_by(AppAuditEvent.created_at.desc())
        .limit(limit)
    )

    if user.role != "admin":
        statement = statement.where(AppAuditEvent.actor_user_id == user.id)

    events = db.scalars(statement).all()
    return [
        NotificationHistoryEntryRead(
            id=event.id,
            event_type=event.event_type,
            payload=event.payload,
            actor_display_name=event.actor.display_name if event.actor else None,
            project_name=event.project.name if event.project else None,
            created_at=event.created_at,
        )
        for event in events
    ]
