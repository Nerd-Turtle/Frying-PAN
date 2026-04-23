from pathlib import Path
import shutil

from fastapi import HTTPException, status
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.app_audit_event import AppAuditEvent
from app.models.change_set import ChangeSet
from app.models.config_object import ConfigObject
from app.models.config_reference import ConfigReference
from app.models.event import EventRecord
from app.models.export_record import ExportRecord
from app.models.parse_warning import ParseWarning
from app.models.project import Project
from app.models.project_membership import ProjectMembership
from app.models.scope import Scope
from app.models.source import Source
from app.models.user import User
from app.models.working_object import WorkingObject
from app.models.working_reference import WorkingReference
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.core.config import get_settings
from app.services.app_audit_service import log_app_event
from app.services.storage_service import delete_stored_file
from app.services.event_service import log_project_event
from app.services.organization_service import (
    get_default_organization_for_user,
    require_organization_membership,
)


def list_projects(db: Session, user_id: str) -> list[Project]:
    statement = (
        select(Project)
        .outerjoin(
            ProjectMembership,
            and_(
                ProjectMembership.project_id == Project.id,
                ProjectMembership.user_id == user_id,
            ),
        )
        .where(
            or_(
                Project.visibility == "public",
                ProjectMembership.user_id == user_id,
            )
        )
        .order_by(func.lower(Project.name), Project.created_at.asc())
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
        visibility=payload.visibility,
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
        _sync_project_contributors(
            db=db,
            project=project,
            contributor_usernames=payload.contributor_usernames,
            owner_user_id=actor.id,
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
            statement.outerjoin(
                ProjectMembership,
                and_(
                    ProjectMembership.project_id == Project.id,
                    ProjectMembership.user_id == user_id,
                ),
            )
            .where(
                or_(
                    Project.visibility == "public",
                    ProjectMembership.user_id == user_id,
                )
            )
        )
    project = db.scalars(statement).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    return project


def get_project_owner_or_404(db: Session, project_id: str, user_id: str) -> Project:
    statement = (
        select(Project)
        .join(ProjectMembership, ProjectMembership.project_id == Project.id)
        .where(
            Project.id == project_id,
            ProjectMembership.user_id == user_id,
            ProjectMembership.role == "owner",
        )
    )
    project = db.scalars(statement).first()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    return project


def update_project(db: Session, project_id: str, payload: ProjectUpdate, actor: User) -> Project:
    project = get_project_owner_or_404(db=db, project_id=project_id, user_id=actor.id)

    if payload.name is not None:
        project.name = payload.name.strip()
    if "description" in payload.model_fields_set:
        project.description = payload.description.strip() if payload.description else None
    if payload.visibility is not None:
        project.visibility = payload.visibility
    if payload.contributor_usernames is not None:
        _sync_project_contributors(
            db=db,
            project=project,
            contributor_usernames=payload.contributor_usernames,
            owner_user_id=actor.id,
        )

    db.add(project)
    try:
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
        event_type="project.updated",
        payload=f"Project '{project.name}' updated.",
        actor_user_id=actor.id,
    )
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: str, actor: User) -> None:
    project = get_project_owner_or_404(db=db, project_id=project_id, user_id=actor.id)
    project_name = project.name

    export_paths = list(
        db.scalars(select(ExportRecord.storage_path).where(ExportRecord.project_id == project.id)).all()
    )
    source_paths = list(
        db.scalars(select(Source.storage_path).where(Source.project_id == project.id)).all()
    )

    log_app_event(
        db=db,
        event_type="project.deleted",
        payload=f"User '{actor.username}' deleted project '{project_name}'.",
        actor_user_id=actor.id,
    )

    for storage_path in export_paths + source_paths:
        delete_stored_file(storage_path)

    for model in (
        ExportRecord,
        ChangeSet,
        WorkingReference,
        WorkingObject,
        ConfigReference,
        ConfigObject,
        ParseWarning,
        Scope,
        Source,
        EventRecord,
        AppAuditEvent,
    ):
        if hasattr(model, "project_id"):
            db.execute(delete(model).where(model.project_id == project.id))

    db.execute(delete(ProjectMembership).where(ProjectMembership.project_id == project.id))
    db.execute(delete(Project).where(Project.id == project.id))
    db.commit()

    storage_root = Path(get_settings().storage_root)
    for path in (
        storage_root / "uploads" / project.id,
        storage_root / "exports" / project.id,
        storage_root / "projects" / project.id,
    ):
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)


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


def _sync_project_contributors(
    db: Session,
    project: Project,
    contributor_usernames: list[str],
    owner_user_id: str,
) -> None:
    normalized_usernames: list[str] = []
    for username in contributor_usernames:
        normalized = username.strip().lower()
        if not normalized or normalized in normalized_usernames:
            continue
        normalized_usernames.append(normalized)

    contributor_users: list[User] = []
    for username in normalized_usernames:
        user = db.scalars(select(User).where(User.username == username)).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{username}' was not found.",
            )
        if user.id == owner_user_id:
            continue
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"User '{username}' is not active.",
            )
        contributor_users.append(user)

    existing_contributors = {
        membership.user_id: membership
        for membership in project.memberships
        if membership.role != "owner"
    }
    desired_contributor_ids = {user.id for user in contributor_users}

    for user in contributor_users:
        membership = existing_contributors.get(user.id)
        if membership is None:
            db.add(
                ProjectMembership(
                    project_id=project.id,
                    user_id=user.id,
                    role="contributor",
                )
            )
            continue
        membership.role = "contributor"
        db.add(membership)

    for user_id, membership in existing_contributors.items():
        if user_id in desired_contributor_ids:
            continue
        db.delete(membership)
