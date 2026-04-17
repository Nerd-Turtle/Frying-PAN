from app.services.project_service import log_project_event


def record_placeholder_analysis(db, project_id: str, source_id: str) -> None:
    # TODO: Replace this event marker with a real pipeline that parses the
    # uploaded XML into canonical Panorama config models and stores inventory
    # or dependency metadata for later diff/merge work.
    log_project_event(
        db=db,
        project_id=project_id,
        event_type="source.indexing.placeholder",
        payload=f"Source {source_id} uploaded. Semantic analysis not implemented yet.",
    )
