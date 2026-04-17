from sqlalchemy.orm import Session

from app.schemas.project import PlaceholderActionResponse
from app.services.event_service import log_project_event
from app.services.project_service import get_project_or_404


def request_project_analysis(
    db: Session, project_id: str
) -> PlaceholderActionResponse:
    project = get_project_or_404(db, project_id)
    log_project_event(
        db=db,
        project_id=project.id,
        event_type="analysis.requested",
        payload="TODO: implement canonical Panorama source analysis pipeline",
    )
    return PlaceholderActionResponse(
        status="placeholder",
        message=(
            "Analysis pipeline is not implemented yet. "
            "This endpoint currently records an event only."
        ),
    )


def request_merge_preview(
    db: Session, project_id: str
) -> PlaceholderActionResponse:
    project = get_project_or_404(db, project_id)
    log_project_event(
        db=db,
        project_id=project.id,
        event_type="merge.preview.requested",
        payload="TODO: implement merge planning against canonical backend models",
    )
    return PlaceholderActionResponse(
        status="placeholder",
        message=(
            "Merge preview is not implemented yet. "
            "Future work belongs in backend merge services, not the frontend."
        ),
    )


def request_export_generation(
    db: Session, project_id: str
) -> PlaceholderActionResponse:
    project = get_project_or_404(db, project_id)
    log_project_event(
        db=db,
        project_id=project.id,
        event_type="export.requested",
        payload="TODO: implement XML export from normalized internal models",
    )
    return PlaceholderActionResponse(
        status="placeholder",
        message=(
            "Export generation is not implemented yet. "
            "This will later render XML from canonical backend models."
        ),
    )
