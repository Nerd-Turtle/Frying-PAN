from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _client() -> TestClient:
    return TestClient(app)


def _register(client: TestClient, email: str, display_name: str) -> dict:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "display_name": display_name,
            "password": "Passw0rd!123",
            "organization_name": f"{display_name} Org",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_auth_session_round_trip_and_logout() -> None:
    with _client() as client:
        session = _register(
            client,
            email=f"user-{uuid4()}@example.com",
            display_name="Operator One",
        )
        assert session["user"]["display_name"] == "Operator One"
        assert len(session["organizations"]) == 1

        current_session = client.get("/api/auth/session")
        assert current_session.status_code == 200
        assert current_session.json()["user"]["email"] == session["user"]["email"]

        logout_response = client.post("/api/auth/logout")
        assert logout_response.status_code == 204

        after_logout = client.get("/api/auth/session")
        assert after_logout.status_code == 401


def test_project_access_is_restricted_by_membership() -> None:
    owner_email = f"owner-{uuid4()}@example.com"
    other_email = f"other-{uuid4()}@example.com"

    with _client() as owner_client:
        _register(owner_client, email=owner_email, display_name="Owner")
        project_response = owner_client.post(
            "/api/projects",
            json={"name": f"project-{uuid4()}", "description": "Membership boundary"},
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        detail_response = owner_client.get(f"/api/projects/{project_id}")
        assert detail_response.status_code == 200

    with _client() as other_client:
        _register(other_client, email=other_email, display_name="Other User")
        forbidden_response = other_client.get(f"/api/projects/{project_id}")
        assert forbidden_response.status_code == 404


def test_actor_aware_events_are_recorded_for_workbench_actions() -> None:
    xml_bytes = b"<config><shared><address><entry name='One'><ip-netmask>10.0.0.1/32</ip-netmask></entry></address></shared></config>"

    with _client() as client:
        session = _register(
            client,
            email=f"audit-{uuid4()}@example.com",
            display_name="Audit User",
        )
        actor_id = session["user"]["id"]

        project_response = client.post(
            "/api/projects",
            json={"name": f"project-{uuid4()}", "description": "Actor audit"},
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        upload_response = client.post(
            f"/api/projects/{project_id}/sources/upload",
            files={"file": ("audit.xml", BytesIO(xml_bytes), "application/xml")},
        )
        assert upload_response.status_code == 201

        analysis_response = client.post(f"/api/projects/{project_id}/analysis/run")
        assert analysis_response.status_code == 200

        change_set_response = client.post(
            f"/api/projects/{project_id}/change-sets",
            json={"name": "Audit draft", "description": "Actor attribution"},
        )
        assert change_set_response.status_code == 200
        change_set_id = change_set_response.json()["id"]

        apply_response = client.post(
            f"/api/projects/{project_id}/change-sets/{change_set_id}/apply"
        )
        assert apply_response.status_code == 200

        export_response = client.post(f"/api/projects/{project_id}/exports", json={})
        assert export_response.status_code == 200

        detail_response = client.get(f"/api/projects/{project_id}")
        assert detail_response.status_code == 200
        events = detail_response.json()["events"]
        assert any(event["actor_user_id"] == actor_id for event in events)
        assert any(event["event_type"] == "analysis.completed" for event in events)
        assert any(event["event_type"] == "change_set.created" for event in events)
        assert any(event["event_type"] == "change_set.applied" for event in events)
        assert any(event["event_type"] == "export.generated" for event in events)
