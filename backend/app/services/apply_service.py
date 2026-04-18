from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.change_set import ChangeSet
from app.models.config_object import ConfigObject
from app.models.config_reference import ConfigReference
from app.models.scope import Scope
from app.models.working_object import WorkingObject
from app.models.working_reference import WorkingReference


def apply_change_set(db: Session, change_set: ChangeSet) -> ChangeSet:
    blocked_objects = change_set.operations_payload.get("blocked_objects", [])
    if blocked_objects:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot apply a change set with blocked objects.",
        )
    if change_set.status == "applied":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Change set has already been applied.",
        )

    try:
        _ensure_working_state_baseline(db=db, project_id=change_set.project_id)
        _apply_object_operations(db=db, change_set=change_set)
        _apply_reference_rewrites(db=db, change_set=change_set)
        _apply_normalization_operations(db=db, change_set=change_set)

        change_set.status = "applied"
        change_set.applied_at = datetime.now(timezone.utc)
        db.add(change_set)
        db.commit()
        db.refresh(change_set)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:  # pragma: no cover - defensive transaction guard
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Failed to apply change set: {exc}",
        ) from exc

    return change_set


def _ensure_working_state_baseline(db: Session, project_id: str) -> None:
    existing = db.scalars(
        select(WorkingObject.id).where(WorkingObject.project_id == project_id).limit(1)
    ).first()
    if existing is not None:
        return

    source_objects = list(
        db.scalars(
            select(ConfigObject)
            .where(ConfigObject.project_id == project_id)
            .order_by(ConfigObject.created_at)
        ).all()
    )
    working_object_by_source_id: dict[str, WorkingObject] = {}
    for source_object in source_objects:
        working_object = WorkingObject(
            project_id=project_id,
            source_id=source_object.source_id,
            source_object_id=source_object.id,
            scope_id=source_object.scope_id,
            object_type=source_object.object_type,
            object_name=source_object.object_name,
            source_xpath=source_object.source_xpath,
            raw_payload=source_object.raw_payload,
            normalized_payload=source_object.normalized_payload,
            normalized_hash=source_object.normalized_hash,
        )
        db.add(working_object)
        db.flush()
        working_object_by_source_id[source_object.id] = working_object

    source_references = list(
        db.scalars(
            select(ConfigReference)
            .where(ConfigReference.project_id == project_id)
            .order_by(ConfigReference.created_at)
        ).all()
    )
    for source_reference in source_references:
        db.add(
            WorkingReference(
                project_id=project_id,
                source_id=source_reference.source_id,
                source_reference_id=source_reference.id,
                owner_object_id=working_object_by_source_id[source_reference.owner_object_id].id,
                reference_kind=source_reference.reference_kind,
                reference_path=source_reference.reference_path,
                target_name=source_reference.target_name,
                target_type_hint=source_reference.target_type_hint,
                target_scope_hint=source_reference.target_scope_hint,
                resolved_object_id=(
                    working_object_by_source_id[source_reference.resolved_object_id].id
                    if source_reference.resolved_object_id is not None
                    else None
                ),
                resolution_status=source_reference.resolution_status,
                metadata_json=source_reference.metadata_json,
            )
        )
    db.flush()


def _apply_object_operations(db: Session, change_set: ChangeSet) -> None:
    for operation in change_set.operations_payload.get("object_operations", []):
        if operation.get("operation") != "promote_to_shared":
            continue
        source_object_id = operation["object_id"]
        working_object = db.scalars(
            select(WorkingObject).where(
                WorkingObject.project_id == change_set.project_id,
                WorkingObject.source_object_id == source_object_id,
            )
        ).first()
        if working_object is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Working object for source object {source_object_id} was not found.",
            )

        shared_scope = db.scalars(
            select(Scope).where(
                Scope.source_id == working_object.source_id,
                Scope.scope_path == "shared",
            )
        ).first()
        if shared_scope is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Shared scope for source {working_object.source_id} was not found.",
            )

        conflict = db.scalars(
            select(WorkingObject).where(
                WorkingObject.project_id == change_set.project_id,
                WorkingObject.scope_id == shared_scope.id,
                WorkingObject.object_type == working_object.object_type,
                WorkingObject.object_name == working_object.object_name,
                WorkingObject.id != working_object.id,
            )
        ).first()
        if conflict is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Working-state shared collision for "
                    f"{working_object.object_type}:{working_object.object_name}."
                ),
            )

        working_object.scope_id = shared_scope.id
        working_object.last_change_set_id = change_set.id
        db.add(working_object)
    db.flush()


def _apply_reference_rewrites(db: Session, change_set: ChangeSet) -> None:
    for operation in change_set.operations_payload.get("reference_rewrites", []):
        source_reference_id = operation["reference_id"]
        working_reference = db.scalars(
            select(WorkingReference).where(
                WorkingReference.project_id == change_set.project_id,
                WorkingReference.source_reference_id == source_reference_id,
            )
        ).first()
        if working_reference is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Working reference {source_reference_id} was not found.",
            )

        target_working_object = db.scalars(
            select(WorkingObject).where(
                WorkingObject.project_id == change_set.project_id,
                WorkingObject.source_object_id == operation["target_object_id"],
            )
        ).first()
        if target_working_object is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Target working object {operation['target_object_id']} was not found.",
            )

        working_reference.resolution_status = "resolved_in_shared"
        working_reference.resolved_object_id = target_working_object.id
        working_reference.last_change_set_id = change_set.id
        working_reference.metadata_json = {
            **working_reference.metadata_json,
            "resolved_scope_path": operation["to_resolved_scope_path"],
            "resolved_object_name": target_working_object.object_name,
            "resolved_object_type": target_working_object.object_type,
        }
        db.add(working_reference)
    db.flush()


def _apply_normalization_operations(db: Session, change_set: ChangeSet) -> None:
    for operation in change_set.operations_payload.get("normalization_operations", []):
        source_object_id = operation["object_id"]
        working_object = db.scalars(
            select(WorkingObject).where(
                WorkingObject.project_id == change_set.project_id,
                WorkingObject.source_object_id == source_object_id,
            )
        ).first()
        if working_object is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Working object {source_object_id} was not found for normalization.",
            )

        raw_payload = dict(working_object.raw_payload)
        normalized_payload = dict(working_object.normalized_payload)
        raw_payload["value"] = operation["to_value"]
        normalized_payload["address_text"] = operation["to_value"]
        normalized_payload["ip_version"] = 6 if ":" in operation["to_value"] else 4

        working_object.raw_payload = raw_payload
        working_object.normalized_payload = normalized_payload
        working_object.normalized_hash = _payload_hash(normalized_payload)
        working_object.last_change_set_id = change_set.id
        db.add(working_object)
    db.flush()


def _payload_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
