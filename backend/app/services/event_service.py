from sqlalchemy.orm import Session

from app.models.event import EventRecord


def log_project_event(
    db: Session,
    project_id: str,
    event_type: str,
    payload: str | None = None,
    actor_user_id: str | None = None,
) -> EventRecord:
    event = EventRecord(
        project_id=project_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        payload=payload,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
