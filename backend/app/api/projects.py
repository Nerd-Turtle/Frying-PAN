from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_ready_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectDetail, ProjectRead, ProjectUpdate
from app.schemas.source import SourceRead
from app.services.project_service import (
    create_project,
    delete_project,
    get_project_or_404,
    list_projects,
    update_project,
)
from app.services.source_service import import_source_upload

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectDetail])
def get_projects(
    current_user: User = Depends(get_current_ready_user),
    db: Session = Depends(get_db),
) -> list[ProjectDetail]:
    return list_projects(db, current_user.id)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project_endpoint(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_ready_user),
    db: Session = Depends(get_db),
) -> ProjectRead:
    return create_project(db, payload, actor=current_user)


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project_endpoint(
    project_id: str,
    current_user: User = Depends(get_current_ready_user),
    db: Session = Depends(get_db),
) -> ProjectDetail:
    return get_project_or_404(db, project_id, user_id=current_user.id)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project_endpoint(
    project_id: str,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_ready_user),
    db: Session = Depends(get_db),
) -> ProjectRead:
    return update_project(db=db, project_id=project_id, payload=payload, actor=current_user)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_endpoint(
    project_id: str,
    current_user: User = Depends(get_current_ready_user),
    db: Session = Depends(get_db),
) -> Response:
    delete_project(db=db, project_id=project_id, actor=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{project_id}/sources/upload",
    response_model=SourceRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_source(
    project_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_ready_user),
    db: Session = Depends(get_db),
) -> SourceRead:
    return import_source_upload(db=db, project_id=project_id, upload=file, actor=current_user)
