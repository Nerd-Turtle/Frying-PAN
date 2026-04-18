from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.organization_membership import OrganizationMembership
from app.models.project import Project
from app.models.project_membership import ProjectMembership
from app.models.source import Source
from app.models.user import User
from app.schemas.project import ProjectCreate
from app.services.event_service import log_project_event
from app.services.organization_service import (
    get_default_organization_for_user,
    require_organization_membership,
)


def list_projects(db: Session, user_id: str) -> list[Project]:
    statement = (
        select(Project)
        .join(ProjectMembership, ProjectMembership.project_id == Project.id)
        .where(ProjectMembership.user_id == user_id)
        .order_by(Project.created_at.desc())
    )
    return list(db.scalars(statement).all())


def create_project(db: Session, payload: ProjectCreate, actor: User) -> Project:
    organization_id = payload.organization_id
    if organization_id is None:
        organization_id = get_default_organization_for_user(db=db, user_id=actor.id).id
    else:
        require_organization_membership(
            db=db,
            organization_id=organization_id,
            user_id=actor.id,
        )

    project = Project(
        organization_id=organization_id,
        name=payload.name.strip(),
        description=payload.description,
        created_by_user_id=actor.id,
    )
    db.add(project)
    try:
        db.flush()
        db.add(
            ProjectMembership(
                project_id=project.id,
                user_id=actor.id,
                role="owner",
            )
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A project with that name already exists in this context.",
        ) from exc
    db.refresh(project)
    log_project_event(
        db=db,
        project_id=project.id,
        event_type="project.created",
        payload=f"Project '{project.name}' created.",
        actor_user_id=actor.id,
    )
    db.refresh(project)
    return project


def get_project_or_404(db: Session, project_id: str, user_id: str | None = None) -> Project:
    statement = select(Project).where(Project.id == project_id)
    if user_id is not None:
        statement = (
            statement.join(ProjectMembership, ProjectMembership.project_id == Project.id)
            .where(ProjectMembership.user_id == user_id)
        )
    project = db.scalars(statement).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    return project


def create_source_record(
    db: Session,
    project_id: str,
    label: str,
    filename: str,
    storage_path: str,
    file_sha256: str,
    imported_by_user_id: str | None = None,
    source_type: str = "panorama_xml",
) -> Source:
    existing_source = find_source_by_checksum(
        db=db,
        project_id=project_id,
        file_sha256=file_sha256,
    )
    if existing_source is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This source has already been imported into the project.",
        )

    source = Source(
        project_id=project_id,
        label=label,
        filename=filename,
        storage_path=storage_path,
        file_sha256=file_sha256,
        imported_by_user_id=imported_by_user_id,
        source_type=source_type,
    )
    db.add(source)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This source has already been imported into the project.",
        ) from exc
    db.refresh(source)
    log_project_event(
        db=db,
        project_id=project_id,
        event_type="source.uploaded",
        payload=f"Stored source file '{filename}' at '{storage_path}'.",
        actor_user_id=imported_by_user_id,
    )
    return source


def find_source_by_checksum(
    db: Session, project_id: str, file_sha256: str
) -> Source | None:
    statement = select(Source).where(
        Source.project_id == project_id,
        Source.file_sha256 == file_sha256,
    )
    return db.scalars(statement).first()
