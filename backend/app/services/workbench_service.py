from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.analysis import AnalysisFilters, AnalysisRunResponse
from app.schemas.change_set import (
    ChangeSetCreate,
    ChangeSetRead,
    MergePreviewRequest,
)
from app.schemas.export import ExportRead, ExportRequest
from app.merge.workbench import MergeWorkbench, NormalizationSelectionRecord
from app.services.apply_service import apply_change_set
from app.services.change_set_service import (
    create_change_set,
    get_change_set_or_404,
    update_change_set_status,
)
from app.services.project_analysis_service import generate_project_analysis_report
from app.services.event_service import log_project_event
from app.services.export_service import generate_project_export
from app.services.project_service import get_project_or_404


def request_project_analysis(
    db: Session, project_id: str, filters: AnalysisFilters, actor: User
) -> AnalysisRunResponse:
    project = get_project_or_404(db, project_id, user_id=actor.id)
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
        actor_user_id=actor.id,
    )
    return AnalysisRunResponse(
        status="ok",
        message="Analysis report generated from canonical project inventory.",
        report=report,
    )


def request_merge_preview(
    db: Session, project_id: str, payload: MergePreviewRequest, actor: User
) -> ChangeSetRead:
    project = get_project_or_404(db, project_id, user_id=actor.id)
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
        actor=actor,
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
        actor_user_id=actor.id,
    )
    return change_set


def request_change_set_create(
    db: Session, project_id: str, payload: ChangeSetCreate, actor: User
) -> ChangeSetRead:
    project = get_project_or_404(db, project_id, user_id=actor.id)
    change_set = create_change_set(db=db, project_id=project.id, payload=payload, actor=actor)
    log_project_event(
        db=db,
        project_id=project.id,
        event_type="change_set.created",
        payload=f"Created draft change set {change_set.id}.",
        actor_user_id=actor.id,
    )
    return change_set


def request_change_set_read(
    db: Session, project_id: str, change_set_id: str, actor: User
) -> ChangeSetRead:
    get_project_or_404(db, project_id, user_id=actor.id)
    return get_change_set_or_404(db, project_id, change_set_id)


def request_change_set_status_update(
    db: Session, project_id: str, change_set_id: str, new_status: str, actor: User
) -> ChangeSetRead:
    project = get_project_or_404(db, project_id, user_id=actor.id)
    change_set = update_change_set_status(
        db=db,
        project_id=project.id,
        change_set_id=change_set_id,
        new_status=new_status,
        actor=actor,
    )
    log_project_event(
        db=db,
        project_id=project.id,
        event_type="change_set.status.updated",
        payload=f"Updated change set {change_set.id} to status '{change_set.status}'.",
        actor_user_id=actor.id,
    )
    return change_set


def request_change_set_apply(
    db: Session, project_id: str, change_set_id: str, actor: User
) -> ChangeSetRead:
    project = get_project_or_404(db, project_id, user_id=actor.id)
    change_set = get_change_set_or_404(db, project_id, change_set_id)
    applied_change_set = apply_change_set(db=db, change_set=change_set, actor=actor)
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
        actor_user_id=actor.id,
    )
    return applied_change_set


def request_export_generation(
    db: Session, project_id: str, payload: ExportRequest, actor: User
) -> ExportRead:
    project = get_project_or_404(db, project_id, user_id=actor.id)
    export_record = generate_project_export(
        db=db,
        project_id=project.id,
        change_set_id=payload.change_set_id,
        created_by_user_id=actor.id,
    )
    log_project_event(
        db=db,
        project_id=project.id,
        event_type="export.generated",
        payload=(
            f"Generated export {export_record.id} for project {project.id}"
            + (
                f" from applied change set {export_record.change_set_id}."
                if export_record.change_set_id is not None
                else "."
            )
        ),
        actor_user_id=actor.id,
    )
    return export_record
