from sqlalchemy.orm import Session

from app.schemas.analysis import AnalysisFilters, AnalysisRunResponse
from app.schemas.project import PlaceholderActionResponse
from app.services.project_analysis_service import generate_project_analysis_report
from app.services.event_service import log_project_event
from app.services.project_service import get_project_or_404


def request_project_analysis(
    db: Session, project_id: str, filters: AnalysisFilters
) -> AnalysisRunResponse:
    project = get_project_or_404(db, project_id)
    report = generate_project_analysis_report(db=db, project_id=project.id, filters=filters)
    log_project_event(
        db=db,
        project_id=project.id,
        event_type="analysis.completed",
        payload=(
            f"Generated analysis report with "
            f"{len(report.duplicate_name_findings)} duplicate-name findings, "
            f"{len(report.duplicate_value_findings)} duplicate-value findings, "
            f"{len(report.normalization_suggestions)} normalization suggestions, "
            f"{len(report.promotion_candidates)} promotion candidates, and "
            f"{len(report.promotion_blockers)} promotion blockers."
        ),
    )
    return AnalysisRunResponse(
        status="ok",
        message="Analysis report generated from canonical project inventory.",
        report=report,
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
