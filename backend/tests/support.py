from uuid import uuid4

from fastapi.testclient import TestClient


def register_and_login(client: TestClient) -> dict:
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"user-{uuid4()}@example.com",
            "display_name": "Test Operator",
            "password": "Passw0rd!123",
            "organization_name": "Test Lab",
        },
    )
    assert response.status_code == 201
    return response.json()
