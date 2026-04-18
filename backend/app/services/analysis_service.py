from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.config_object import ConfigObject
from app.models.config_reference import ConfigReference
from app.models.parse_warning import ParseWarning
from app.models.scope import Scope
from app.models.source import Source
from app.parsers.panorama_xml import PanoramaXmlParser, PanoramaXmlParserError
from app.services.event_service import log_project_event
from app.services.reference_service import (
    ReferenceResolutionSettings,
    resolve_references,
)


@dataclass(frozen=True)
class SourceInventorySummary:
    scope_count: int
    object_count: int
    reference_count: int
    warning_count: int


def build_source_inventory(
    db: Session,
    source: Source,
    resolution_settings: ReferenceResolutionSettings | None = None,
) -> SourceInventorySummary:
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
            actor_user_id=source.imported_by_user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    db.execute(delete(ConfigReference).where(ConfigReference.source_id == source.id))
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

    object_lookup: dict[tuple[str, str, str], ConfigObject] = {}
    for object_record in parse_result.objects:
        persisted_object = ConfigObject(
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
        db.add(persisted_object)
        db.flush()
        object_lookup[
            (
                object_record.scope_path,
                object_record.object_type,
                object_record.object_name,
            )
        ] = persisted_object

    resolved_references = resolve_references(
        scopes=parse_result.scopes,
        objects=parse_result.objects,
        references=parse_result.references,
        settings=resolution_settings,
    )
    for resolved_reference in resolved_references:
        owner_object = object_lookup[
            (
                resolved_reference.owner_scope_path,
                resolved_reference.owner_object_type,
                resolved_reference.owner_object_name,
            )
        ]
        resolved_object = None
        if (
            resolved_reference.resolved_scope_path is not None
            and resolved_reference.resolved_object_type is not None
            and resolved_reference.resolved_object_name is not None
        ):
            resolved_object = object_lookup[
                (
                    resolved_reference.resolved_scope_path,
                    resolved_reference.resolved_object_type,
                    resolved_reference.resolved_object_name,
                )
            ]

        db.add(
            ConfigReference(
                project_id=source.project_id,
                source_id=source.id,
                owner_object_id=owner_object.id,
                reference_kind=resolved_reference.reference_kind,
                reference_path=resolved_reference.reference_path,
                target_name=resolved_reference.target_name,
                target_type_hint="|".join(resolved_reference.target_type_hints),
                target_scope_hint=resolved_reference.target_scope_hint,
                resolved_object_id=resolved_object.id if resolved_object is not None else None,
                resolution_status=resolved_reference.resolution_status,
                metadata_json={
                    "resolved_scope_path": resolved_reference.resolved_scope_path,
                    "resolved_object_type": resolved_reference.resolved_object_type,
                    "resolved_object_name": resolved_reference.resolved_object_name,
                    "resolved_builtin_key": resolved_reference.resolved_builtin_key,
                    **(resolved_reference.metadata or {}),
                },
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
            f"{len(parse_result.objects)} objects, {len(resolved_references)} references, "
            f"and {len(parse_result.warnings)} warnings."
        ),
        actor_user_id=source.imported_by_user_id,
    )

    return SourceInventorySummary(
        scope_count=len(parse_result.scopes),
        object_count=len(parse_result.objects),
        reference_count=len(resolved_references),
        warning_count=len(parse_result.warnings),
    )
