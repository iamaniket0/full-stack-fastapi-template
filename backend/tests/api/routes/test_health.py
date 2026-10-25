from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.core.config import settings


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
