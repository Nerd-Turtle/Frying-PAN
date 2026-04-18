from sqlalchemy.orm import Session

from app.models.app_audit_event import AppAuditEvent


def log_app_event(
    db: Session,
    event_type: str,
    payload: str | None = None,
    actor_user_id: str | None = None,
    project_id: str | None = None,
) -> AppAuditEvent:
    event = AppAuditEvent(
        project_id=project_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        payload=payload,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
