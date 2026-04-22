from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.app_audit_event import AppAuditEvent
from app.models.event import EventRecord
from app.schemas.notification import AuditLogEntryRead


def list_audit_log(db: Session, limit: int = 100) -> list[AuditLogEntryRead]:
    app_events = db.scalars(
        select(AppAuditEvent)
        .options(
            joinedload(AppAuditEvent.actor),
            joinedload(AppAuditEvent.project),
        )
        .order_by(AppAuditEvent.created_at.desc())
        .limit(limit)
    ).all()

    project_events = db.scalars(
        select(EventRecord)
        .options(
            joinedload(EventRecord.actor),
            joinedload(EventRecord.project),
        )
        .order_by(EventRecord.created_at.desc())
        .limit(limit)
    ).all()

    combined = [
        AuditLogEntryRead(
            id=event.id,
            source="application",
            event_type=event.event_type,
            payload=event.payload,
            actor_display_name=event.actor.display_name if event.actor else None,
            project_name=event.project.name if event.project else None,
            created_at=event.created_at,
        )
        for event in app_events
    ] + [
        AuditLogEntryRead(
            id=event.id,
            source="project",
            event_type=event.event_type,
            payload=event.payload,
            actor_display_name=event.actor.display_name if event.actor else None,
            project_name=event.project.name if event.project else None,
            created_at=event.created_at,
        )
        for event in project_events
    ]

    combined.sort(key=lambda entry: entry.created_at, reverse=True)
    return combined[:limit]
