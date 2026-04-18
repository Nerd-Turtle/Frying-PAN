from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models.config_object import ConfigObject
from app.models.scope import Scope
from tests.support import register_and_login


EXAMPLE_XML_PATH = Path("/opt/frying-pan/Example-1.xml")


def _client() -> TestClient:
    return TestClient(app)


def test_project_analysis_reports_duplicate_name_value_and_normalization_findings() -> None:
    project_name = f"project-{uuid4()}"
    xml_bytes = EXAMPLE_XML_PATH.read_bytes()

    with _client() as client:
        register_and_login(client)
        project_response = client.post(
            "/api/projects",
            json={"name": project_name, "description": "Phase 4 analysis test"},
        )
        project_id = project_response.json()["id"]

        upload_response = client.post(
            f"/api/projects/{project_id}/sources/upload",
            files={"file": ("Example-1.xml", BytesIO(xml_bytes), "application/xml")},
        )
        assert upload_response.status_code == 201

        analysis_response = client.post(f"/api/projects/{project_id}/analysis/run")
        assert analysis_response.status_code == 200
        payload = analysis_response.json()

        assert payload["status"] == "ok"
        duplicate_name_keys = {
            (finding["object_type"], finding["key"])
            for finding in payload["report"]["duplicate_name_findings"]
        }
        assert ("address", "DUP-IP-ADDRESS") in duplicate_name_keys

        address_value_finding = next(
            finding
            for finding in payload["report"]["duplicate_value_findings"]
            if finding["object_type"] == "address"
            and finding["normalized_payload"]["address_text"] == "192.168.1.1/24"
        )
        assert len(address_value_finding["items"]) == 4

        suggestions = payload["report"]["normalization_suggestions"]
        assert len(suggestions) == 1
        assert suggestions[0]["object_name"] == "DUP-IP-ADDRESS"
        assert suggestions[0]["kind"] == "host_ipv4_to_cidr"
        assert suggestions[0]["original_value"] == "172.16.1.1"
        assert suggestions[0]["suggested_value"] == "172.16.1.1/32"


def test_project_analysis_filters_by_source_scope_and_object_type_without_mutation() -> None:
    project_name = f"project-{uuid4()}"
    xml_bytes = EXAMPLE_XML_PATH.read_bytes()
    second_source_xml = b"""
    <config version="11.2.0">
      <shared>
        <address>
          <entry name="Only-In-Source-2"><ip-netmask>203.0.113.10/32</ip-netmask></entry>
        </address>
      </shared>
    </config>
    """

    with _client() as client:
        register_and_login(client)
        project_response = client.post(
            "/api/projects",
            json={"name": project_name, "description": "Filter behavior test"},
        )
        project_id = project_response.json()["id"]

        first_upload = client.post(
            f"/api/projects/{project_id}/sources/upload",
            files={"file": ("Example-1.xml", BytesIO(xml_bytes), "application/xml")},
        )
        first_source = first_upload.json()

        second_upload = client.post(
            f"/api/projects/{project_id}/sources/upload",
            files={"file": ("source-2.xml", BytesIO(second_source_xml), "application/xml")},
        )
        assert second_upload.status_code == 201

        analysis_response = client.post(
            f"/api/projects/{project_id}/analysis/run",
            params={
                "source_id": first_source["id"],
                "object_type": "address",
                "scope_path": "shared",
            },
        )
        assert analysis_response.status_code == 200
        payload = analysis_response.json()

        assert payload["report"]["filters"] == {
            "source_id": first_source["id"],
            "object_type": "address",
            "scope_path": "shared",
        }
        assert payload["report"]["duplicate_name_findings"] == []
        assert payload["report"]["duplicate_value_findings"] == []
        assert payload["report"]["normalization_suggestions"] == []

        with SessionLocal() as db:
            object_row = db.scalars(
                select(ConfigObject)
                .join(Scope, ConfigObject.scope_id == Scope.id)
                .where(
                    ConfigObject.project_id == project_id,
                    ConfigObject.object_name == "DUP-IP-ADDRESS",
                    Scope.scope_path
                    == "shared/device-group:Device-Group-1/device-group:DG1-Sub-Group",
                )
            ).one()

        assert object_row.raw_payload["value"] == "172.16.1.1"
        assert object_row.normalized_payload["address_text"] == "172.16.1.1"


def test_project_analysis_reports_promotion_candidates_and_blockers() -> None:
    project_name = f"project-{uuid4()}"
    xml_bytes = EXAMPLE_XML_PATH.read_bytes()

    with _client() as client:
        register_and_login(client)
        project_response = client.post(
            "/api/projects",
            json={"name": project_name, "description": "Promotion analysis test"},
        )
        project_id = project_response.json()["id"]

        upload_response = client.post(
            f"/api/projects/{project_id}/sources/upload",
            files={"file": ("Example-1.xml", BytesIO(xml_bytes), "application/xml")},
        )
        assert upload_response.status_code == 201

        analysis_response = client.post(f"/api/projects/{project_id}/analysis/run")
        assert analysis_response.status_code == 200
        payload = analysis_response.json()["report"]

        candidate_names = {item["object_name"] for item in payload["promotion_candidates"]}
        assert "DG1-IP-Netmask" in candidate_names
        assert "DG1-Service-Group" in candidate_names

        blocker_by_name = {
            item["object_name"]: item for item in payload["promotion_blockers"]
        }
        assert "DG1-Group" in blocker_by_name
        assert "Nested-Groups" in blocker_by_name
        assert "DUP-IP-ADDRESS" in blocker_by_name

        assert "depends_on_non_shared_object" in blocker_by_name["DG1-Group"]["blockers"]
        assert blocker_by_name["Nested-Groups"]["mixed_scope_dependencies"] is True
        assert "mixed_scope_dependencies" in blocker_by_name["Nested-Groups"]["blockers"]
        assert "name_collision_in_shared" in blocker_by_name["DUP-IP-ADDRESS"]["blockers"]
