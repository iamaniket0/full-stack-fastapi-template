from fastapi.testclient import TestClient

from app.core.config import settings


def test_version(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/version")
    assert r.status_code == 200
    assert r.json() == {"version": "1.0.0"}


def test_version_rejects_other_methods(client: TestClient) -> None:
    r = client.post(f"{settings.API_V1_STR}/version")
    assert r.status_code == 405
