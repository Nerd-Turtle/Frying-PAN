from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.source import Source
from app.schemas.project import ProjectCreate
from app.services.event_service import log_project_event


def list_projects(db: Session) -> list[Project]:
    statement = select(Project).order_by(Project.created_at.desc())
    return list(db.scalars(statement).all())


def create_project(db: Session, payload: ProjectCreate) -> Project:
    project = Project(name=payload.name.strip(), description=payload.description)
    db.add(project)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A project with that name already exists.",
        ) from exc
    db.refresh(project)
    log_project_event(
        db=db,
        project_id=project.id,
        event_type="project.created",
        payload=f"Project '{project.name}' created.",
    )
    db.refresh(project)
    return project


def get_project_or_404(db: Session, project_id: str) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    return project


def create_source_record(
    db: Session, project_id: str, filename: str, storage_path: str
) -> Source:
    source = Source(
        project_id=project_id,
        filename=filename,
        storage_path=storage_path,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    log_project_event(
        db=db,
        project_id=project_id,
        event_type="source.uploaded",
        payload=f"Stored source file '{filename}' at '{storage_path}'.",
    )
    return source
