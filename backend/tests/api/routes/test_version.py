from datetime import timedelta
from importlib.metadata import version

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import create_access_token

VERSION_URL = f"{settings.API_V1_STR}/version"
APP_VERSION = version("app")


def test_version(client: TestClient) -> None:
    r = client.get(VERSION_URL)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/json")
    assert r.json() == {"version": APP_VERSION}


def test_version_without_auth_token(client: TestClient) -> None:
    r = client.get(VERSION_URL, headers={})
    assert "authorization" not in {k.lower() for k in r.request.headers}
    assert r.status_code == 200
    assert r.json() == {"version": APP_VERSION}


def test_version_matches_backend_package_version(client: TestClient) -> None:
    assert APP_VERSION == "0.1.0"
    r = client.get(VERSION_URL)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["version"], str)
    assert data["version"] == "0.1.0"


def test_version_with_valid_token(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.get(VERSION_URL, headers=normal_user_token_headers)
    assert r.status_code == 200
    assert r.json() == {"version": APP_VERSION}


@pytest.mark.parametrize(
    "token",
    [
        "not-a-valid-token",
        create_access_token("someone", expires_delta=timedelta(minutes=-5)),
    ],
    ids=["invalid", "expired"],
)
def test_version_with_bad_bearer_token(client: TestClient, token: str) -> None:
    r = client.get(VERSION_URL, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == {"version": APP_VERSION}


@pytest.mark.parametrize("method", ["post", "put", "delete"])
def test_version_rejects_other_methods(client: TestClient, method: str) -> None:
    r = client.request(method.upper(), VERSION_URL)
    assert r.status_code == 405


def test_version_exposes_nothing_else(client: TestClient) -> None:
    r = client.get(VERSION_URL)
    assert r.status_code == 200
    data = r.json()
    assert set(data) == {"version"}
    body = r.text
    secrets = [settings.SECRET_KEY, settings.FIRST_SUPERUSER_PASSWORD]
    secrets += [h["password"] for h in settings.DATABASE_URL.hosts() if h["password"]]
    for secret in secrets:
        assert secret not in body
    assert str(settings.DATABASE_URL) not in body
    assert settings.FIRST_SUPERUSER not in body
    assert settings.PROJECT_NAME not in body


def test_version_in_openapi_docs(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    assert f"{settings.API_V1_STR}/version" in schema["paths"]
    operation = schema["paths"][f"{settings.API_V1_STR}/version"]["get"]
    assert "utils" in operation["tags"]
    response_schema = operation["responses"]["200"]["content"]["application/json"][
        "schema"
    ]
    assert "$ref" in response_schema
    name = response_schema["$ref"].rsplit("/", 1)[-1]
    model = schema["components"]["schemas"][name]
    assert set(model["properties"]) == {"version"}
    assert model["properties"]["version"]["type"] == "string"
    assert "version" in model.get("required", [])
