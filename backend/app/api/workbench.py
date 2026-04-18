from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.analysis import AnalysisFilters, AnalysisRunResponse
from app.schemas.change_set import (
    ChangeSetCreate,
    ChangeSetRead,
    ChangeSetStatusUpdate,
    MergePreviewRequest,
)
from app.schemas.export import ExportRead, ExportRequest
from app.services.workbench_service import (
    request_export_generation,
    request_change_set_apply,
    request_change_set_create,
    request_change_set_read,
    request_change_set_status_update,
    request_merge_preview,
    request_project_analysis,
)

router = APIRouter(prefix="/projects", tags=["workbench"])


@router.post("/{project_id}/analysis/run", response_model=AnalysisRunResponse)
def run_analysis(
    project_id: str,
    source_id: str | None = Query(default=None),
    object_type: str | None = Query(default=None),
    scope_path: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisRunResponse:
    return request_project_analysis(
        db=db,
        project_id=project_id,
        actor=current_user,
        filters=AnalysisFilters(
            source_id=source_id,
            object_type=object_type,
            scope_path=scope_path,
        ),
    )


@router.post("/{project_id}/change-sets", response_model=ChangeSetRead)
def create_change_set_endpoint(
    project_id: str,
    payload: ChangeSetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChangeSetRead:
    return request_change_set_create(
        db=db,
        project_id=project_id,
        payload=payload,
        actor=current_user,
    )


@router.get("/{project_id}/change-sets/{change_set_id}", response_model=ChangeSetRead)
def get_change_set_endpoint(
    project_id: str,
    change_set_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChangeSetRead:
    return request_change_set_read(
        db=db,
        project_id=project_id,
        change_set_id=change_set_id,
        actor=current_user,
    )


@router.patch("/{project_id}/change-sets/{change_set_id}/status", response_model=ChangeSetRead)
def update_change_set_status_endpoint(
    project_id: str,
    change_set_id: str,
    payload: ChangeSetStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChangeSetRead:
    return request_change_set_status_update(
        db=db,
        project_id=project_id,
        change_set_id=change_set_id,
        new_status=payload.status,
        actor=current_user,
    )


@router.post("/{project_id}/change-sets/{change_set_id}/apply", response_model=ChangeSetRead)
def apply_change_set_endpoint(
    project_id: str,
    change_set_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChangeSetRead:
    return request_change_set_apply(
        db=db,
        project_id=project_id,
        change_set_id=change_set_id,
        actor=current_user,
    )


@router.post("/{project_id}/merge/preview", response_model=ChangeSetRead)
def preview_merge(
    project_id: str,
    payload: MergePreviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChangeSetRead:
    return request_merge_preview(
        db=db,
        project_id=project_id,
        payload=payload,
        actor=current_user,
    )


@router.post("/{project_id}/exports", response_model=ExportRead)
def export_project(
    project_id: str,
    payload: ExportRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExportRead:
    return request_export_generation(
        db=db,
        project_id=project_id,
        payload=payload or ExportRequest(),
        actor=current_user,
    )
