from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.change_set import ChangeSet
from app.schemas.change_set import ChangeSetCreate
from app.services.project_service import get_project_or_404


ALLOWED_CHANGE_SET_STATUSES = {"draft", "preview", "applied"}


def create_change_set(
    db: Session,
    project_id: str,
    payload: ChangeSetCreate,
    status_value: str = "draft",
    preview_summary: dict | None = None,
    operations_payload: dict | None = None,
) -> ChangeSet:
    get_project_or_404(db, project_id)
    change_set = ChangeSet(
        project_id=project_id,
        name=payload.name.strip(),
        description=payload.description,
        status=status_value,
        preview_summary=preview_summary or {},
        operations_payload=operations_payload or {},
    )
    db.add(change_set)
    db.commit()
    db.refresh(change_set)
    return change_set


def get_change_set_or_404(db: Session, project_id: str, change_set_id: str) -> ChangeSet:
    statement = select(ChangeSet).where(
        ChangeSet.project_id == project_id,
        ChangeSet.id == change_set_id,
    )
    change_set = db.scalars(statement).first()
    if change_set is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Change set not found.",
        )
    return change_set


def update_change_set_status(
    db: Session, project_id: str, change_set_id: str, new_status: str
) -> ChangeSet:
    change_set = get_change_set_or_404(db, project_id, change_set_id)
    if new_status not in ALLOWED_CHANGE_SET_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported change set status.",
        )
    if new_status == "applied":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Apply lifecycle state is reserved until Phase 6.",
        )
    if change_set.status == new_status:
        return change_set
    if {change_set.status, new_status} - {"draft", "preview"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unsupported change set status transition.",
        )

    change_set.status = new_status
    db.add(change_set)
    db.commit()
    db.refresh(change_set)
    return change_set
