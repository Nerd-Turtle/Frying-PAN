from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from tests.support import (
    BOOTSTRAP_WORKING_PASSWORD,
    create_local_user,
    ensure_admin_session,
    register_and_login,
)


def _client() -> TestClient:
    return TestClient(app)


def test_bootstrap_admin_requires_password_change_then_supports_session_and_logout() -> None:
    with _client() as client:
        session = ensure_admin_session(client)
        assert session["user"]["username"] == "chef"
        assert session["user"]["role"] == "admin"
        assert session["password_change_required"] is False

        current_session = client.get("/api/auth/session")
        assert current_session.status_code == 200
        assert current_session.json()["user"]["username"] == "chef"

        logout_response = client.post("/api/auth/logout")
        assert logout_response.status_code == 204

        after_logout = client.get("/api/auth/session")
        assert after_logout.status_code == 401


def test_admin_can_create_local_user_and_user_can_login() -> None:
    username = f"operator-{uuid4().hex[:8]}"

    with _client() as admin_client:
        ensure_admin_session(admin_client)
        create_response = admin_client.post(
            "/api/admin/users",
            json={
                "username": username,
                "display_name": "Operator One",
                "password": BOOTSTRAP_WORKING_PASSWORD,
                "role": "operator",
                "must_change_password": False,
            },
        )
        assert create_response.status_code == 201
        created = create_response.json()
        assert created["username"] == username
        assert created["role"] == "operator"

        list_response = admin_client.get("/api/admin/users")
        assert list_response.status_code == 200
        assert any(user["username"] == username for user in list_response.json())

    with _client() as operator_client:
        login_response = operator_client.post(
            "/api/auth/login",
            json={"username": username, "password": BOOTSTRAP_WORKING_PASSWORD},
        )
        assert login_response.status_code == 200
        session = login_response.json()
        assert session["user"]["username"] == username
        assert session["password_change_required"] is False


def test_password_change_is_required_before_workbench_access() -> None:
    username = f"mustchange-{uuid4().hex[:8]}"

    with _client() as admin_client:
        create_local_user(
            admin_client,
            username=username,
            display_name="Needs Reset",
            password="Passw0rd!123",
            must_change_password=True,
        )

    with _client() as operator_client:
        login_response = operator_client.post(
            "/api/auth/login",
            json={"username": username, "password": "Passw0rd!123"},
        )
        assert login_response.status_code == 200
        assert login_response.json()["password_change_required"] is True

        blocked_project_response = operator_client.get("/api/projects")
        assert blocked_project_response.status_code == 403

        change_response = operator_client.post(
            "/api/auth/change-password",
            json={
                "current_password": "Passw0rd!123",
                "new_password": "Passw0rd!123-updated",
            },
        )
        assert change_response.status_code == 200
        assert change_response.json()["password_change_required"] is False

        allowed_project_response = operator_client.get("/api/projects")
        assert allowed_project_response.status_code == 200


def test_project_access_is_restricted_by_membership() -> None:
    owner_username = f"owner-{uuid4().hex[:8]}"
    other_username = f"other-{uuid4().hex[:8]}"

    with _client() as admin_client:
        create_local_user(
            admin_client,
            username=owner_username,
            display_name="Owner",
            password="Passw0rd!123",
        )
        create_local_user(
            admin_client,
            username=other_username,
            display_name="Other User",
            password="Passw0rd!123",
        )

    with _client() as owner_client:
        login_response = owner_client.post(
            "/api/auth/login",
            json={"username": owner_username, "password": "Passw0rd!123"},
        )
        assert login_response.status_code == 200
        project_response = owner_client.post(
            "/api/projects",
            json={"name": f"project-{uuid4()}", "description": "Membership boundary"},
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        detail_response = owner_client.get(f"/api/projects/{project_id}")
        assert detail_response.status_code == 200

    with _client() as other_client:
        login_response = other_client.post(
            "/api/auth/login",
            json={"username": other_username, "password": "Passw0rd!123"},
        )
        assert login_response.status_code == 200
        forbidden_response = other_client.get(f"/api/projects/{project_id}")
        assert forbidden_response.status_code == 404


def test_actor_aware_events_are_recorded_for_workbench_actions() -> None:
    xml_bytes = b"<config><shared><address><entry name='One'><ip-netmask>10.0.0.1/32</ip-netmask></entry></address></shared></config>"

    with _client() as client:
        session = register_and_login(client)
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


def test_admin_user_management_actions_are_audited() -> None:
    username = f"audit-user-{uuid4().hex[:8]}"

    with _client() as client:
        admin_session = ensure_admin_session(client)
        actor_id = admin_session["user"]["id"]

        create_response = client.post(
            "/api/admin/users",
            json={
                "username": username,
                "display_name": "Audited User",
                "password": "Passw0rd!123",
                "must_change_password": True,
            },
        )
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]

        update_response = client.patch(
            f"/api/admin/users/{user_id}",
            json={"status": "disabled"},
        )
        assert update_response.status_code == 200

        from app.db.session import SessionLocal
        from app.models.app_audit_event import AppAuditEvent
        from sqlalchemy import select

        db = SessionLocal()
        try:
            events = list(
                db.scalars(
                    select(AppAuditEvent).where(AppAuditEvent.actor_user_id == actor_id)
                ).all()
            )
        finally:
            db.close()

        event_types = {event.event_type for event in events}
        assert "admin.user.created" in event_types
        assert "admin.user.updated" in event_types
