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

        from app.db.session import SessionLocal
        from app.models.app_audit_event import AppAuditEvent
        from sqlalchemy import select

        db = SessionLocal()
        try:
            event_types = set(
                db.scalars(
                    select(AppAuditEvent.event_type).where(
                        AppAuditEvent.actor_user_id == session["user"]["id"]
                    )
                ).all()
            )
        finally:
            db.close()

        assert "auth.login.succeeded" in event_types
        assert "auth.logout" in event_types


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


def test_user_can_update_own_profile_details() -> None:
    username = f"profile-{uuid4().hex[:8]}"

    with _client() as admin_client:
        create_local_user(
            admin_client,
            username=username,
            display_name="Original Name",
            password="Passw0rd!123",
            must_change_password=False,
        )

    with _client() as user_client:
        login_response = user_client.post(
            "/api/auth/login",
            json={"username": username, "password": "Passw0rd!123"},
        )
        assert login_response.status_code == 200

        profile_response = user_client.patch(
            "/api/auth/profile",
            json={"display_name": "Updated Name", "email": "updated@example.com"},
        )
        assert profile_response.status_code == 200
        updated = profile_response.json()
        assert updated["username"] == username
        assert updated["display_name"] == "Updated Name"
        assert updated["email"] == "updated@example.com"

        from app.db.session import SessionLocal
        from app.models.app_audit_event import AppAuditEvent
        from sqlalchemy import select

        db = SessionLocal()
        try:
            event_types = set(
                db.scalars(
                    select(AppAuditEvent.event_type).where(
                        AppAuditEvent.actor_user_id == updated["id"]
                    )
                ).all()
            )
        finally:
            db.close()

        assert "auth.login.succeeded" in event_types
        assert "auth.profile.updated" in event_types


def test_ready_user_can_read_active_user_directory() -> None:
    active_username = f"directory-active-{uuid4().hex[:8]}"
    disabled_username = f"directory-disabled-{uuid4().hex[:8]}"

    with _client() as admin_client:
        create_local_user(
            admin_client,
            username=active_username,
            display_name="Directory Active",
            password="Passw0rd!123",
            must_change_password=False,
        )
        disabled_user = create_local_user(
            admin_client,
            username=disabled_username,
            display_name="Directory Disabled",
            password="Passw0rd!123",
            must_change_password=False,
        )
        disable_response = admin_client.patch(
            f"/api/admin/users/{disabled_user['id']}",
            json={"status": "disabled"},
        )
        assert disable_response.status_code == 200

    with _client() as operator_client:
        register_and_login(operator_client)
        directory_response = operator_client.get("/api/auth/user-directory")
        assert directory_response.status_code == 200

        directory = directory_response.json()
        assert any(user["username"] == active_username for user in directory)
        assert all(user["username"] != disabled_username for user in directory)
        assert all(set(user.keys()) == {"id", "username", "display_name"} for user in directory)


def test_private_project_access_is_restricted_but_contributors_can_work() -> None:
    owner_username = f"owner-{uuid4().hex[:8]}"
    contributor_username = f"contrib-{uuid4().hex[:8]}"
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
            username=contributor_username,
            display_name="Contributor",
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
            json={
                "name": f"project-{uuid4()}",
                "description": "Membership boundary",
                "visibility": "private",
                "contributor_usernames": [contributor_username],
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        detail_response = owner_client.get(f"/api/projects/{project_id}")
        assert detail_response.status_code == 200

    with _client() as contributor_client:
        login_response = contributor_client.post(
            "/api/auth/login",
            json={"username": contributor_username, "password": "Passw0rd!123"},
        )
        assert login_response.status_code == 200
        detail_response = contributor_client.get(f"/api/projects/{project_id}")
        assert detail_response.status_code == 200

    with _client() as other_client:
        login_response = other_client.post(
            "/api/auth/login",
            json={"username": other_username, "password": "Passw0rd!123"},
        )
        assert login_response.status_code == 200
        forbidden_response = other_client.get(f"/api/projects/{project_id}")
        assert forbidden_response.status_code == 404


def test_public_project_is_visible_to_any_ready_user() -> None:
    owner_username = f"public-owner-{uuid4().hex[:8]}"
    other_username = f"public-other-{uuid4().hex[:8]}"

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
            json={"name": f"project-{uuid4()}", "description": "Public boundary"},
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

    with _client() as other_client:
        login_response = other_client.post(
            "/api/auth/login",
            json={"username": other_username, "password": "Passw0rd!123"},
        )
        assert login_response.status_code == 200

        list_response = other_client.get("/api/projects")
        assert list_response.status_code == 200
        assert any(project["id"] == project_id for project in list_response.json())

        detail_response = other_client.get(f"/api/projects/{project_id}")
        assert detail_response.status_code == 200


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


def test_notification_settings_can_be_read_and_updated_by_admin() -> None:
    with _client() as client:
        ensure_admin_session(client)

        current_response = client.get("/api/notifications/settings")
        assert current_response.status_code == 200
        assert current_response.json()["notification_timeout_seconds"] == 10

        update_response = client.patch(
            "/api/notifications/settings",
            json={"notification_timeout_seconds": 15},
        )
        assert update_response.status_code == 200
        assert update_response.json()["notification_timeout_seconds"] == 15

        history_response = client.get("/api/notifications/history?limit=10")
        assert history_response.status_code == 200
        assert any(
            entry["event_type"] == "admin.notifications.updated"
            for entry in history_response.json()
        )


def test_operator_can_read_notification_settings_but_cannot_update_them() -> None:
    username = f"notify-{uuid4().hex[:8]}"

    with _client() as admin_client:
        create_local_user(
            admin_client,
            username=username,
            display_name="Notify Operator",
            password="Passw0rd!123",
            must_change_password=False,
        )

    with _client() as operator_client:
        login_response = operator_client.post(
            "/api/auth/login",
            json={"username": username, "password": "Passw0rd!123"},
        )
        assert login_response.status_code == 200

        current_response = operator_client.get("/api/notifications/settings")
        assert current_response.status_code == 200

        update_response = operator_client.patch(
            "/api/notifications/settings",
            json={"notification_timeout_seconds": 12},
        )
        assert update_response.status_code == 403


def test_admin_audit_log_endpoint_returns_entries() -> None:
    username = f"audit-view-{uuid4().hex[:8]}"

    with _client() as client:
        ensure_admin_session(client)
        create_response = client.post(
            "/api/admin/users",
            json={
                "username": username,
                "display_name": "Audit Viewer",
                "password": "Passw0rd!123",
                "must_change_password": False,
            },
        )
        assert create_response.status_code == 201

        audit_response = client.get("/api/admin/audit-log?limit=25")
        assert audit_response.status_code == 200
        entries = audit_response.json()
        assert any(entry["event_type"] == "admin.user.created" for entry in entries)


def test_failed_login_and_validation_errors_are_audited() -> None:
    with _client() as client:
        failed_login = client.post(
            "/api/auth/login",
            json={"username": "chef", "password": "wrongpass"},
        )
        assert failed_login.status_code == 401

        validation_error = client.post(
            "/api/admin/users",
            json={
                "username": "shortpass",
                "display_name": "Short Pass",
                "password": "blah",
                "must_change_password": False,
            },
        )
        assert validation_error.status_code in {401, 422}

        from app.db.session import SessionLocal
        from app.models.app_audit_event import AppAuditEvent
        from sqlalchemy import select

        db = SessionLocal()
        try:
            event_types = set(db.scalars(select(AppAuditEvent.event_type)).all())
        finally:
            db.close()

        assert "auth.login.failed" in event_types


def test_admin_validation_failures_are_audited() -> None:
    with _client() as client:
        ensure_admin_session(client)
        response = client.post(
            "/api/admin/users",
            json={
                "username": "validation-user",
                "display_name": "Validation User",
                "password": "blah",
                "must_change_password": False,
            },
        )
        assert response.status_code == 422

        from app.db.session import SessionLocal
        from app.models.app_audit_event import AppAuditEvent
        from sqlalchemy import select

        db = SessionLocal()
        try:
            event_types = set(db.scalars(select(AppAuditEvent.event_type)).all())
        finally:
            db.close()

        assert "app.request.validation_failed" in event_types
