from io import BytesIO
from pathlib import Path
from uuid import uuid4
import xml.etree.ElementTree as ET

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models.config_object import ConfigObject
from app.models.export_record import ExportRecord
from app.models.scope import Scope


EXAMPLE_XML_PATH = Path("/opt/frying-pan/Example-1.xml")


def _client() -> TestClient:
    return TestClient(app)


def test_export_generates_well_formed_xml_from_applied_working_state() -> None:
    project_name = f"project-{uuid4()}"
    xml_bytes = EXAMPLE_XML_PATH.read_bytes()

    with _client() as client:
        project_response = client.post(
            "/api/projects",
            json={"name": project_name, "description": "Export generation test"},
        )
        project_id = project_response.json()["id"]

        upload_response = client.post(
            f"/api/projects/{project_id}/sources/upload",
            files={"file": ("Example-1.xml", BytesIO(xml_bytes), "application/xml")},
        )
        assert upload_response.status_code == 201

        with SessionLocal() as db:
            objects = db.scalars(
                select(ConfigObject).join(Scope, ConfigObject.scope_id == Scope.id).where(
                    ConfigObject.project_id == project_id
                )
            ).all()
            object_by_key = {
                (obj.object_name, obj.object_type, obj.scope.scope_path): obj for obj in objects
            }

        dg1_group = object_by_key[
            ("DG1-Group", "address_group", "shared/device-group:Device-Group-1")
        ]
        dg1_service_group = object_by_key[
            ("DG1-Service-Group", "service_group", "shared/device-group:Device-Group-1")
        ]
        dg1_sub_dup = object_by_key[
            (
                "DUP-IP-ADDRESS",
                "address",
                "shared/device-group:Device-Group-1/device-group:DG1-Sub-Group",
            )
        ]

        preview_response = client.post(
            f"/api/projects/{project_id}/merge/preview",
            json={
                "name": "Exportable preview",
                "description": "Promote and normalize before export",
                "selected_object_ids": [dg1_group.id, dg1_service_group.id],
                "selected_normalizations": [
                    {"object_id": dg1_sub_dup.id, "kind": "host_ipv4_to_cidr"}
                ],
            },
        )
        assert preview_response.status_code == 200
        change_set = preview_response.json()

        apply_response = client.post(
            f"/api/projects/{project_id}/change-sets/{change_set['id']}/apply"
        )
        assert apply_response.status_code == 200

        export_response = client.post(
            f"/api/projects/{project_id}/exports",
            json={"change_set_id": change_set["id"]},
        )
        assert export_response.status_code == 200
        export_payload = export_response.json()

        assert export_payload["project_id"] == project_id
        assert export_payload["change_set_id"] == change_set["id"]
        assert export_payload["export_status"] == "generated"
        assert export_payload["metadata_json"]["serializer"] == "working_state_v1"

        artifact_path = Path(export_payload["storage_path"])
        assert artifact_path.exists()

        xml_root = ET.fromstring(artifact_path.read_bytes())
        assert xml_root.tag == "config"
        assert xml_root.attrib["generated-by"] == "frying-pan"

        shared_group = xml_root.find("./shared/address-group/entry[@name='DG1-Group']")
        assert shared_group is not None
        assert shared_group.find("./static/member").text == "DG1-IP-Netmask"

        shared_service_group = xml_root.find("./shared/service-group/entry[@name='DG1-Service-Group']")
        assert shared_service_group is not None
        assert shared_service_group.find("./members/member").text == "service-http"

        normalized_dup = xml_root.find(
            "./devices/entry[@name='localhost.localdomain']/device-group/"
            "entry[@name='DG1-Sub-Group']/address/entry[@name='DUP-IP-ADDRESS']/ip-netmask"
        )
        assert normalized_dup is not None
        assert normalized_dup.text == "172.16.1.1/32"

        with SessionLocal() as db:
            export_record = db.scalars(
                select(ExportRecord).where(ExportRecord.id == export_payload["id"])
            ).one()

        assert export_record.project_id == project_id
        assert export_record.change_set_id == change_set["id"]
        assert export_record.storage_path == export_payload["storage_path"]


def test_export_rejects_unapplied_change_set() -> None:
    project_name = f"project-{uuid4()}"
    xml_bytes = EXAMPLE_XML_PATH.read_bytes()

    with _client() as client:
        project_response = client.post(
            "/api/projects",
            json={"name": project_name, "description": "Export validation test"},
        )
        project_id = project_response.json()["id"]

        upload_response = client.post(
            f"/api/projects/{project_id}/sources/upload",
            files={"file": ("Example-1.xml", BytesIO(xml_bytes), "application/xml")},
        )
        assert upload_response.status_code == 201

        with SessionLocal() as db:
            dg1_service_group = db.scalars(
                select(ConfigObject)
                .join(Scope, ConfigObject.scope_id == Scope.id)
                .where(
                    ConfigObject.project_id == project_id,
                    ConfigObject.object_name == "DG1-Service-Group",
                    Scope.scope_path == "shared/device-group:Device-Group-1",
                )
            ).one()

        preview_response = client.post(
            f"/api/projects/{project_id}/merge/preview",
            json={
                "name": "Preview only",
                "description": "Should not export before apply",
                "selected_object_ids": [dg1_service_group.id],
                "selected_normalizations": [],
            },
        )
        assert preview_response.status_code == 200
        change_set = preview_response.json()

        export_response = client.post(
            f"/api/projects/{project_id}/exports",
            json={"change_set_id": change_set["id"]},
        )
        assert export_response.status_code == 409
        assert export_response.json()["detail"] == "Only applied change sets may be exported."
