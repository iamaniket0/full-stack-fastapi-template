from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import create_access_token


def test_health_details(client: TestClient) -> None:
    before = datetime.now(UTC)
    r = client.get(f"{settings.API_V1_STR}/health/details")
    after = datetime.now(UTC)

    assert r.status_code == 200
    data = r.json()
    assert set(data) == {"status", "time"}
    assert data["status"] == "ok"
    server_time = datetime.fromisoformat(data["time"])
    assert server_time.utcoffset() == timedelta(0)
    assert before - timedelta(seconds=1) <= server_time <= after + timedelta(seconds=1)


def test_health_details_rejects_other_methods(client: TestClient) -> None:
    r = client.post(f"{settings.API_V1_STR}/health/details")
    assert r.status_code == 405


def test_health(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_health_without_auth_token(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/health", headers={})
    assert "authorization" not in {k.lower() for k in r.request.headers}
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.parametrize(
    "token",
    [
        "not-a-valid-token",
        create_access_token("someone", expires_delta=timedelta(minutes=-5)),
    ],
    ids=["invalid", "expired"],
)
def test_health_with_bad_bearer_token(client: TestClient, token: str) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/health",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.parametrize("method", ["post", "put", "delete"])
def test_health_rejects_other_methods(client: TestClient, method: str) -> None:
    r = client.request(method.upper(), f"{settings.API_V1_STR}/health")
    assert r.status_code == 405


def test_health_ignores_query_params(client: TestClient) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/health", params={"foo": "bar", "verbose": "1"}
    )
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_health_details_unchanged_alongside_health(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

    r = client.get(f"{settings.API_V1_STR}/health/details")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    server_time = datetime.fromisoformat(data["time"])
    assert server_time.utcoffset() == timedelta(0)


def test_health_in_openapi_docs(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    operation = schema["paths"][f"{settings.API_V1_STR}/health"]["get"]
    assert "utils" in operation["tags"]
    response_schema = operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]
    if "$ref" in response_schema:
        name = response_schema["$ref"].rsplit("/", 1)[-1]
        response_schema = schema["components"]["schemas"][name]
    assert "status" in response_schema["properties"]
