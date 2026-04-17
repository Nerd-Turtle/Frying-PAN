from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.project import ProjectCreate, ProjectDetail, ProjectRead
from app.schemas.source import SourceRead
from app.services.analysis_service import record_placeholder_analysis
from app.services.project_service import (
    create_project,
    create_source_record,
    get_project_or_404,
    list_projects,
)
from app.services.storage_service import save_uploaded_source_file

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectDetail])
def get_projects(db: Session = Depends(get_db)) -> list[ProjectDetail]:
    return list_projects(db)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project_endpoint(
    payload: ProjectCreate, db: Session = Depends(get_db)
) -> ProjectRead:
    return create_project(db, payload)


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project_endpoint(project_id: str, db: Session = Depends(get_db)) -> ProjectDetail:
    return get_project_or_404(db, project_id)


@router.post(
    "/{project_id}/sources/upload",
    response_model=SourceRead,
    status_code=status.HTTP_201_CREATED,
)
def upload_source(
    project_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> SourceRead:
    project = get_project_or_404(db, project_id)

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    storage_path = save_uploaded_source_file(project_id=project.id, upload=file)
    source = create_source_record(
        db=db,
        project_id=project.id,
        filename=file.filename,
        storage_path=storage_path,
    )

    # TODO: Replace this stub with a real indexing pipeline that parses XML
    # into canonical backend models before any semantic workflow is attempted.
    record_placeholder_analysis(db=db, project_id=project.id, source_id=source.id)
    return source
