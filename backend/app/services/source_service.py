from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.schemas.source import SourceRead
from app.services.analysis_service import record_placeholder_analysis
from app.services.event_service import log_project_event
from app.services.project_service import create_source_record, get_project_or_404
from app.services.storage_service import delete_stored_file, save_uploaded_source_file


def import_source_upload(
    db: Session, project_id: str, upload: UploadFile
) -> SourceRead:
    project = get_project_or_404(db, project_id)

    if not upload.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    stored_upload = save_uploaded_source_file(project_id=project.id, upload=upload)

    try:
        source = create_source_record(
            db=db,
            project_id=project.id,
            label=stored_upload.label,
            filename=stored_upload.filename,
            storage_path=stored_upload.storage_path,
            file_sha256=stored_upload.file_sha256,
        )
    except HTTPException as exc:
        delete_stored_file(stored_upload.storage_path)

        if exc.status_code == status.HTTP_409_CONFLICT:
            log_project_event(
                db=db,
                project_id=project.id,
                event_type="source.upload.rejected_duplicate",
                payload=(
                    f"Rejected duplicate source '{stored_upload.filename}' "
                    f"with checksum '{stored_upload.file_sha256}'."
                ),
            )

        raise

    # TODO: Replace this stub with a real indexing pipeline that parses XML
    # into canonical backend models before any semantic workflow is attempted.
    record_placeholder_analysis(db=db, project_id=project.id, source_id=source.id)
    return source
