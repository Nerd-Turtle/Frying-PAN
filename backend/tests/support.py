from uuid import uuid4

from fastapi.testclient import TestClient

BOOTSTRAP_USERNAME = "chef"
BOOTSTRAP_DEFAULT_PASSWORD = "chefchef"
BOOTSTRAP_WORKING_PASSWORD = "Passw0rd!123"


def ensure_admin_session(client: TestClient) -> dict:
    for password in (BOOTSTRAP_WORKING_PASSWORD, BOOTSTRAP_DEFAULT_PASSWORD):
        response = client.post(
            "/api/auth/login",
            json={"username": BOOTSTRAP_USERNAME, "password": password},
        )
        if response.status_code != 200:
            continue

        session = response.json()
        if session["password_change_required"]:
            changed = client.post(
                "/api/auth/change-password",
                json={
                    "current_password": password,
                    "new_password": BOOTSTRAP_WORKING_PASSWORD,
                },
            )
            assert changed.status_code == 200
            session = changed.json()
        return session

    raise AssertionError("Unable to establish the bootstrap admin session.")


def create_local_user(
    client: TestClient,
    *,
    username: str | None = None,
    display_name: str = "Test Operator",
    password: str = "Passw0rd!123",
    role: str = "operator",
    must_change_password: bool = False,
) -> dict:
    ensure_admin_session(client)
    user_name = username or f"user-{uuid4().hex[:8]}"
    response = client.post(
        "/api/admin/users",
        json={
            "username": user_name,
            "display_name": display_name,
            "password": password,
            "role": role,
            "must_change_password": must_change_password,
        },
    )
    assert response.status_code == 201
    return response.json()


def login_local(
    client: TestClient,
    *,
    username: str,
    password: str,
) -> dict:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    session = response.json()
    if session["password_change_required"]:
        changed = client.post(
            "/api/auth/change-password",
            json={
                "current_password": password,
                "new_password": f"{password}-updated",
            },
        )
        assert changed.status_code == 200
        session = changed.json()
    return session


def register_and_login(client: TestClient) -> dict:
    created = create_local_user(client)
    operator_client = client
    return login_local(
        operator_client,
        username=created["username"],
        password="Passw0rd!123",
    )
