from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.change_set import ChangeSet
from app.models.export_record import ExportRecord
from app.models.working_object import WorkingObject
from app.services.apply_service import ensure_working_state_baseline
from app.services.change_set_service import get_change_set_or_404


SUPPORTED_EXPORT_TYPES = {
    "address",
    "address_group",
    "service",
    "service_group",
    "tag",
}


def generate_project_export(
    db: Session,
    project_id: str,
    change_set_id: str | None = None,
    created_by_user_id: str | None = None,
) -> ExportRecord:
    change_set: ChangeSet | None = None
    if change_set_id is not None:
        change_set = get_change_set_or_404(db, project_id, change_set_id)
        if change_set.status != "applied":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only applied change sets may be exported.",
            )

    ensure_working_state_baseline(db=db, project_id=project_id)

    working_objects = list(
        db.scalars(
            select(WorkingObject)
            .where(
                WorkingObject.project_id == project_id,
                WorkingObject.state_status == "active",
            )
            .options(selectinload(WorkingObject.scope))
            .order_by(WorkingObject.object_type, WorkingObject.object_name)
        ).all()
    )
    xml_bytes, metadata = serialize_working_state_xml(working_objects)

    export_record = _store_export_artifact(
        db=db,
        project_id=project_id,
        change_set_id=change_set.id if change_set is not None else None,
        created_by_user_id=created_by_user_id,
        xml_bytes=xml_bytes,
        metadata=metadata,
    )
    return export_record


def serialize_working_state_xml(
    working_objects: list[WorkingObject],
) -> tuple[bytes, dict]:
    root = ET.Element(
        "config",
        {
            "version": "11.2.0",
            "generated-by": "frying-pan",
        },
    )
    shared_element = ET.SubElement(root, "shared")
    devices_element = ET.SubElement(root, "devices")
    device_entry = ET.SubElement(devices_element, "entry", {"name": "localhost.localdomain"})
    device_group_parent = ET.SubElement(device_entry, "device-group")

    grouped: dict[str, list[WorkingObject]] = {}
    for obj in working_objects:
        if obj.object_type not in SUPPORTED_EXPORT_TYPES:
            continue
        grouped.setdefault(obj.scope.scope_path, []).append(obj)

    for scope_path in sorted(grouped):
        if scope_path == "shared":
            scope_element = shared_element
        else:
            scope_element = _ensure_device_group_entry(device_group_parent, grouped[scope_path][0])
        _serialize_scope_objects(scope_element=scope_element, objects=grouped[scope_path])

    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    metadata = {
        "scope_count": len(grouped),
        "object_count": sum(len(items) for items in grouped.values()),
        "serializer": "working_state_v1",
        "supported_object_types": sorted(SUPPORTED_EXPORT_TYPES),
    }
    return xml_bytes, metadata


def _ensure_device_group_entry(root_parent: ET.Element, obj: WorkingObject) -> ET.Element:
    if obj.scope.scope_type != "device_group":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Unsupported export scope type '{obj.scope.scope_type}'.",
        )

    entry = ET.SubElement(root_parent, "entry", {"name": obj.scope.scope_name})
    description = obj.scope.metadata_json.get("description")
    if description:
        ET.SubElement(entry, "description").text = description
    ET.SubElement(entry, "devices")
    return entry


def _serialize_scope_objects(scope_element: ET.Element, objects: list[WorkingObject]) -> None:
    section_map: dict[str, ET.Element] = {}
    section_names = {
        "address": "address",
        "address_group": "address-group",
        "service": "service",
        "service_group": "service-group",
        "tag": "tag",
    }
    for object_type, section_name in section_names.items():
        section_objects = [
            obj for obj in objects if obj.object_type == object_type and obj.state_status == "active"
        ]
        if not section_objects:
            continue
        section_element = ET.SubElement(scope_element, section_name)
        section_map[object_type] = section_element
        for obj in sorted(section_objects, key=lambda item: item.object_name):
            entry = ET.SubElement(section_element, "entry", {"name": obj.object_name})
            _serialize_object_payload(entry=entry, obj=obj)


def _serialize_object_payload(entry: ET.Element, obj: WorkingObject) -> None:
    if obj.object_type == "address":
        value_kind = obj.raw_payload.get("value_kind")
        value = obj.raw_payload.get("value")
        if value_kind and value is not None:
            ET.SubElement(entry, value_kind).text = value
        return

    if obj.object_type == "address_group":
        group_kind = obj.raw_payload.get("group_kind")
        if group_kind == "static":
            static_element = ET.SubElement(entry, "static")
            for member in obj.raw_payload.get("members", []):
                ET.SubElement(static_element, "member").text = member
        elif group_kind == "dynamic":
            dynamic_element = ET.SubElement(entry, "dynamic")
            ET.SubElement(dynamic_element, "filter").text = obj.raw_payload.get("filter")
        return

    if obj.object_type == "service":
        protocol = obj.raw_payload.get("protocol")
        protocol_element = ET.SubElement(entry, "protocol")
        protocol_detail = ET.SubElement(protocol_element, protocol)
        if obj.raw_payload.get("port") is not None:
            ET.SubElement(protocol_detail, "port").text = obj.raw_payload.get("port")
        if obj.raw_payload.get("source_port") is not None:
            ET.SubElement(protocol_detail, "source-port").text = obj.raw_payload.get("source_port")
        if obj.raw_payload.get("override") == "no":
            override = ET.SubElement(protocol_detail, "override")
            ET.SubElement(override, "no")
        return

    if obj.object_type == "service_group":
        members = ET.SubElement(entry, "members")
        for member in obj.raw_payload.get("members", []):
            ET.SubElement(members, "member").text = member
        return

    if obj.object_type == "tag":
        if obj.raw_payload.get("color") is not None:
            ET.SubElement(entry, "color").text = obj.raw_payload.get("color")


def _store_export_artifact(
    db: Session,
    project_id: str,
    change_set_id: str | None,
    created_by_user_id: str | None,
    xml_bytes: bytes,
    metadata: dict,
) -> ExportRecord:
    settings = get_settings()
    export_dir = Path(settings.storage_root) / "exports" / project_id
    export_dir.mkdir(parents=True, exist_ok=True)

    filename = f"export-{uuid4()}.xml"
    storage_path = export_dir / filename
    storage_path.write_bytes(xml_bytes)

    digest = hashlib.sha256(xml_bytes).hexdigest()
    export_record = ExportRecord(
        project_id=project_id,
        created_by_user_id=created_by_user_id,
        change_set_id=change_set_id,
        filename=filename,
        storage_path=str(storage_path),
        file_sha256=digest,
        export_status="generated",
        metadata_json=metadata,
    )
    db.add(export_record)
    db.commit()
    db.refresh(export_record)
    return export_record
