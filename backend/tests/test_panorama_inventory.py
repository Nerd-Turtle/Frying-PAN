from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models.config_object import ConfigObject
from app.models.config_reference import ConfigReference
from app.models.parse_warning import ParseWarning
from app.models.scope import Scope
from app.parsers.panorama_xml import PanoramaXmlParser


EXAMPLE_XML_PATH = Path("/opt/frying-pan/Example-1.xml")


def _client() -> TestClient:
    return TestClient(app)


def test_example_xml_parser_discovers_v1_scope_and_object_inventory() -> None:
    parser = PanoramaXmlParser()
    result = parser.parse(EXAMPLE_XML_PATH.read_bytes())

    scope_paths = {scope.scope_path for scope in result.scopes}
    assert scope_paths == {
        "shared",
        "shared/device-group:Device-Group-1",
        "shared/device-group:Device-Group-2",
        "shared/device-group:Device-Group-1/device-group:DG1-Sub-Group",
    }

    dg1_sub_group = next(
        scope for scope in result.scopes if scope.scope_name == "DG1-Sub-Group"
    )
    assert dg1_sub_group.parent_scope_path == "shared/device-group:Device-Group-1"
    assert dg1_sub_group.readonly_id == "14"

    assert len(result.objects) == 19
    assert len(result.references) == 6
    shared_address = next(
        obj for obj in result.objects if obj.object_name == "Shared-IP-Netmask"
    )
    assert shared_address.scope_path == "shared"
    assert shared_address.object_type == "address"
    assert shared_address.raw_payload == {
        "value_kind": "ip-netmask",
        "value": "192.168.1.1/24",
    }
    assert shared_address.normalized_payload == {
        "value_kind": "ip-netmask",
        "address_text": "192.168.1.1/24",
        "ip_version": 4,
    }

    warning_sections = {
        warning.details.get("section_name")
        for warning in result.warnings
        if warning.warning_type == "unsupported_scope_section"
    }
    assert "region" in warning_sections
    assert "pre-rulebase" in warning_sections
    assert "post-rulebase" in warning_sections

    nested_group_reference = next(
        reference
        for reference in result.references
        if reference.owner_object_name == "Nested-Groups"
        and reference.reference_path == "static/member[2]"
    )
    assert nested_group_reference.target_name == "Shared-Group"
    assert nested_group_reference.target_type_hints == ["address", "address_group"]


def test_example_xml_upload_persists_scope_object_and_warning_rows() -> None:
    project_name = f"project-{uuid4()}"
    xml_bytes = EXAMPLE_XML_PATH.read_bytes()

    with _client() as client:
        project_response = client.post(
            "/api/projects",
            json={"name": project_name, "description": "Phase 2 import test"},
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        upload_response = client.post(
            f"/api/projects/{project_id}/sources/upload",
            files={"file": ("Example-1.xml", BytesIO(xml_bytes), "application/xml")},
        )
        assert upload_response.status_code == 201
        source = upload_response.json()
        assert source["parse_status"] == "parsed_with_warnings"

        detail_response = client.get(f"/api/projects/{project_id}")
        assert detail_response.status_code == 200
        detail = detail_response.json()
        event_types = {event["event_type"] for event in detail["events"]}
        assert "source.uploaded" in event_types
        assert "source.indexed" in event_types

        with SessionLocal() as db:
            scopes = db.scalars(
                select(Scope).where(Scope.source_id == source["id"]).order_by(Scope.scope_path)
            ).all()
            objects = db.scalars(
                select(ConfigObject).where(ConfigObject.source_id == source["id"])
            ).all()
            references = db.scalars(
                select(ConfigReference).where(ConfigReference.source_id == source["id"])
            ).all()
            warnings = db.scalars(
                select(ParseWarning).where(ParseWarning.source_id == source["id"])
            ).all()

        assert len(scopes) == 4
        assert len(objects) == 19
        assert len(references) == 6
        assert len(warnings) > 0

        scope_by_name = {scope.scope_name: scope for scope in scopes}
        assert (
            scope_by_name["DG1-Sub-Group"].parent_scope_id
            == scope_by_name["Device-Group-1"].id
        )
        assert scope_by_name["DG1-Sub-Group"].scope_path == (
            "shared/device-group:Device-Group-1/device-group:DG1-Sub-Group"
        )

        matching_object = next(
            obj
            for obj in objects
            if obj.scope_id == scope_by_name["shared"].id
            and obj.object_name == "Shared-Service-Group"
        )
        assert matching_object.object_type == "service_group"
        assert matching_object.normalized_payload == {
            "members_ordered": ["service-http"]
        }

        builtin_references = [
            reference for reference in references if reference.resolution_status == "builtin"
        ]
        assert len(builtin_references) == 2
        assert all(
            reference.metadata_json["resolved_builtin_key"] == "service-http"
            for reference in builtin_references
        )

        shared_resolution = next(
            reference
            for reference in references
            if reference.target_name == "Shared-Group"
            and reference.resolution_status == "resolved_in_shared"
        )
        assert shared_resolution.metadata_json["resolved_scope_path"] == "shared"
