from sqlalchemy.orm import Session

from app.schemas.analysis import AnalysisFilters, AnalysisRunResponse
from app.schemas.change_set import (
    ChangeSetCreate,
    ChangeSetRead,
    MergePreviewRequest,
)
from app.schemas.project import PlaceholderActionResponse
from app.merge.workbench import MergeWorkbench, NormalizationSelectionRecord
from app.services.apply_service import apply_change_set
from app.services.change_set_service import (
    create_change_set,
    get_change_set_or_404,
    update_change_set_status,
)
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
    db: Session, project_id: str, payload: MergePreviewRequest
) -> ChangeSetRead:
    project = get_project_or_404(db, project_id)
    preview_plan = MergeWorkbench().preview(
        db=db,
        project_id=project.id,
        selected_object_ids=payload.selected_object_ids,
        selected_normalizations=[
            NormalizationSelectionRecord(
                object_id=item.object_id,
                kind=item.kind,
            )
            for item in payload.selected_normalizations
        ],
    )
    change_set = create_change_set(
        db=db,
        project_id=project.id,
        payload=ChangeSetCreate(name=payload.name, description=payload.description),
        status_value="preview",
        preview_summary=preview_plan.preview_summary,
        operations_payload=preview_plan.operations_payload,
    )
    log_project_event(
        db=db,
        project_id=project.id,
        event_type="merge.preview.created",
        payload=(
            f"Created preview change set {change_set.id} with "
            f"{change_set.preview_summary.get('planned_object_count', 0)} object operations, "
            f"{change_set.preview_summary.get('reference_rewrite_count', 0)} reference rewrites, "
            f"{change_set.preview_summary.get('normalization_count', 0)} normalization operations, "
            f"and {change_set.preview_summary.get('blocked_object_count', 0)} blocked objects."
        ),
    )
    return change_set


def request_change_set_create(
    db: Session, project_id: str, payload: ChangeSetCreate
) -> ChangeSetRead:
    project = get_project_or_404(db, project_id)
    change_set = create_change_set(db=db, project_id=project.id, payload=payload)
    log_project_event(
        db=db,
        project_id=project.id,
        event_type="change_set.created",
        payload=f"Created draft change set {change_set.id}.",
    )
    return change_set


def request_change_set_read(
    db: Session, project_id: str, change_set_id: str
) -> ChangeSetRead:
    get_project_or_404(db, project_id)
    return get_change_set_or_404(db, project_id, change_set_id)


def request_change_set_status_update(
    db: Session, project_id: str, change_set_id: str, new_status: str
) -> ChangeSetRead:
    project = get_project_or_404(db, project_id)
    change_set = update_change_set_status(
        db=db,
        project_id=project.id,
        change_set_id=change_set_id,
        new_status=new_status,
    )
    log_project_event(
        db=db,
        project_id=project.id,
        event_type="change_set.status.updated",
        payload=f"Updated change set {change_set.id} to status '{change_set.status}'.",
    )
    return change_set


def request_change_set_apply(
    db: Session, project_id: str, change_set_id: str
) -> ChangeSetRead:
    project = get_project_or_404(db, project_id)
    change_set = get_change_set_or_404(db, project_id, change_set_id)
    applied_change_set = apply_change_set(db=db, change_set=change_set)
    log_project_event(
        db=db,
        project_id=project.id,
        event_type="change_set.applied",
        payload=(
            f"Applied change set {applied_change_set.id} with "
            f"{applied_change_set.preview_summary.get('planned_object_count', 0)} object operations, "
            f"{applied_change_set.preview_summary.get('reference_rewrite_count', 0)} reference rewrites, "
            f"and {applied_change_set.preview_summary.get('normalization_count', 0)} normalization operations."
        ),
    )
    return applied_change_set


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
