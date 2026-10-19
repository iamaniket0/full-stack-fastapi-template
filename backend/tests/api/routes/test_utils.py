from datetime import UTC, datetime, timedelta
from importlib.metadata import version

from fastapi.testclient import TestClient

from app.core.config import settings


def test_get_time(client: TestClient) -> None:
    before = datetime.now(UTC)
    r = client.get(f"{settings.API_V1_STR}/utils/time/")
    after = datetime.now(UTC)

    assert r.status_code == 200
    server_time = datetime.fromisoformat(r.json()["time"])
    assert server_time.tzinfo is not None
    assert before - timedelta(seconds=1) <= server_time <= after + timedelta(seconds=1)


def test_get_version(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/utils/version/")

    assert r.status_code == 200
    assert r.json() == {"version": version("app")}
