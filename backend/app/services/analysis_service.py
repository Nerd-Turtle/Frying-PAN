from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.config_object import ConfigObject
from app.models.parse_warning import ParseWarning
from app.models.scope import Scope
from app.models.source import Source
from app.parsers.panorama_xml import PanoramaXmlParser, PanoramaXmlParserError
from app.services.event_service import log_project_event


@dataclass(frozen=True)
class SourceInventorySummary:
    scope_count: int
    object_count: int
    warning_count: int


def build_source_inventory(db: Session, source: Source) -> SourceInventorySummary:
    xml_path = Path(source.storage_path)
    xml_bytes = xml_path.read_bytes()

    parser = PanoramaXmlParser()
    try:
        parse_result = parser.parse(xml_bytes)
    except PanoramaXmlParserError as exc:
        source.parse_status = "parse_failed"
        db.add(source)
        db.commit()
        db.refresh(source)
        log_project_event(
            db=db,
            project_id=source.project_id,
            event_type="source.indexing.failed",
            payload=f"Source {source.id} failed XML parsing: {exc}",
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    db.execute(delete(ConfigObject).where(ConfigObject.source_id == source.id))
    db.execute(delete(ParseWarning).where(ParseWarning.source_id == source.id))
    db.execute(delete(Scope).where(Scope.source_id == source.id))
    db.commit()

    scope_lookup: dict[str, Scope] = {}
    for scope_record in sorted(parse_result.scopes, key=lambda scope: scope.scope_path.count("/")):
        scope = Scope(
            project_id=source.project_id,
            source_id=source.id,
            parent_scope_id=(
                scope_lookup[scope_record.parent_scope_path].id
                if scope_record.parent_scope_path is not None
                else None
            ),
            scope_type=scope_record.scope_type,
            scope_name=scope_record.scope_name,
            scope_path=scope_record.scope_path,
            readonly_id=scope_record.readonly_id,
            metadata_json=scope_record.metadata,
        )
        db.add(scope)
        db.flush()
        scope_lookup[scope.scope_path] = scope

    for object_record in parse_result.objects:
        db.add(
            ConfigObject(
                project_id=source.project_id,
                source_id=source.id,
                scope_id=scope_lookup[object_record.scope_path].id,
                object_type=object_record.object_type,
                object_name=object_record.object_name,
                source_xpath=object_record.source_xpath,
                raw_payload=object_record.raw_payload,
                normalized_payload=object_record.normalized_payload,
                normalized_hash=object_record.normalized_hash,
                parse_status=object_record.parse_status,
            )
        )

    for warning_record in parse_result.warnings:
        db.add(
            ParseWarning(
                project_id=source.project_id,
                source_id=source.id,
                scope_id=(
                    scope_lookup[warning_record.scope_path].id
                    if warning_record.scope_path is not None
                    else None
                ),
                warning_type=warning_record.warning_type,
                message=warning_record.message,
                source_xpath=warning_record.source_xpath,
                details=warning_record.details,
            )
        )

    source.parse_status = (
        "parsed_with_warnings" if parse_result.warnings else "parsed"
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    log_project_event(
        db=db,
        project_id=source.project_id,
        event_type="source.indexed",
        payload=(
            f"Source {source.id} indexed into {len(parse_result.scopes)} scopes, "
            f"{len(parse_result.objects)} objects, and {len(parse_result.warnings)} warnings."
        ),
    )

    return SourceInventorySummary(
        scope_count=len(parse_result.scopes),
        object_count=len(parse_result.objects),
        warning_count=len(parse_result.warnings),
    )
