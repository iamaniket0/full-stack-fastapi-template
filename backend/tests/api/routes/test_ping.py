from fastapi.testclient import TestClient

from app.core.config import settings


def test_ping(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/ping")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_ping_rejects_other_methods(client: TestClient) -> None:
    r = client.post(f"{settings.API_V1_STR}/ping")
    assert r.status_code == 405
