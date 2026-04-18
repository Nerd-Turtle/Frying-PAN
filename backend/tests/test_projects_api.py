import hashlib
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from tests.support import register_and_login


def _client() -> TestClient:
    return TestClient(app)


def test_project_create_list_and_detail_round_trip() -> None:
    project_name = f"project-{uuid4()}"

    with _client() as client:
        register_and_login(client)
        create_response = client.post(
            "/api/projects",
            json={
                "name": project_name,
                "description": "Phase 1 API validation",
            },
        )
        assert create_response.status_code == 201
        created_project = create_response.json()

        detail_response = client.get(f"/api/projects/{created_project['id']}")
        assert detail_response.status_code == 200
        detail = detail_response.json()

        assert detail["id"] == created_project["id"]
        assert detail["name"] == project_name
        assert detail["description"] == "Phase 1 API validation"
        assert detail["sources"] == []
        assert any(event["event_type"] == "project.created" for event in detail["events"])

        list_response = client.get("/api/projects")
        assert list_response.status_code == 200
        projects = list_response.json()

        matching_project = next(
            project for project in projects if project["id"] == created_project["id"]
        )
        assert matching_project["name"] == project_name


def test_source_upload_persists_metadata_file_and_events() -> None:
    project_name = f"project-{uuid4()}"
    filename = "phase1-source.xml"
    file_bytes = b"<config><shared><address /></shared></config>"
    expected_sha256 = hashlib.sha256(file_bytes).hexdigest()

    with _client() as client:
        register_and_login(client)
        project_response = client.post(
            "/api/projects",
            json={"name": project_name, "description": "Upload test"},
        )
        project_id = project_response.json()["id"]

        upload_response = client.post(
            f"/api/projects/{project_id}/sources/upload",
            files={"file": (filename, BytesIO(file_bytes), "application/xml")},
        )
        assert upload_response.status_code == 201
        source = upload_response.json()

        assert source["label"] == "phase1-source"
        assert source["filename"] == filename
        assert source["file_sha256"] == expected_sha256
        assert source["source_type"] == "panorama_xml"
        assert source["parse_status"] == "parsed"

        stored_file = Path(source["storage_path"])
        assert stored_file.exists()
        assert stored_file.read_bytes() == file_bytes

        detail_response = client.get(f"/api/projects/{project_id}")
        assert detail_response.status_code == 200
        detail = detail_response.json()

        assert len(detail["sources"]) == 1
        event_types = {event["event_type"] for event in detail["events"]}
        assert "project.created" in event_types
        assert "source.uploaded" in event_types
        assert "source.indexed" in event_types


def test_duplicate_source_upload_is_rejected_by_checksum() -> None:
    project_name = f"project-{uuid4()}"
    file_bytes = b"<config><shared><service /></shared></config>"

    with _client() as client:
        register_and_login(client)
        project_response = client.post(
            "/api/projects",
            json={"name": project_name, "description": "Duplicate upload test"},
        )
        project_id = project_response.json()["id"]

        first_upload = client.post(
            f"/api/projects/{project_id}/sources/upload",
            files={"file": ("duplicate-a.xml", BytesIO(file_bytes), "application/xml")},
        )
        assert first_upload.status_code == 201

        second_upload = client.post(
            f"/api/projects/{project_id}/sources/upload",
            files={"file": ("duplicate-b.xml", BytesIO(file_bytes), "application/xml")},
        )
        assert second_upload.status_code == 409
        assert (
            second_upload.json()["detail"]
            == "This source has already been imported into the project."
        )

        detail_response = client.get(f"/api/projects/{project_id}")
        assert detail_response.status_code == 200
        detail = detail_response.json()

        assert len(detail["sources"]) == 1
        event_types = [event["event_type"] for event in detail["events"]]
        assert "source.upload.rejected_duplicate" in event_types
