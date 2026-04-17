from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.project import PlaceholderActionResponse
from app.services.workbench_service import (
    request_export_generation,
    request_merge_preview,
    request_project_analysis,
)

router = APIRouter(prefix="/projects", tags=["workbench"])


@router.post("/{project_id}/analysis/run", response_model=PlaceholderActionResponse)
def run_analysis(project_id: str, db: Session = Depends(get_db)) -> PlaceholderActionResponse:
    return request_project_analysis(db=db, project_id=project_id)


@router.post("/{project_id}/merge/preview", response_model=PlaceholderActionResponse)
def preview_merge(project_id: str, db: Session = Depends(get_db)) -> PlaceholderActionResponse:
    return request_merge_preview(db=db, project_id=project_id)


@router.post("/{project_id}/exports", response_model=PlaceholderActionResponse)
def export_project(project_id: str, db: Session = Depends(get_db)) -> PlaceholderActionResponse:
    return request_export_generation(db=db, project_id=project_id)
