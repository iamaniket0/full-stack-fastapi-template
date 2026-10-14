from fastapi.testclient import TestClient


def test_ping(client: TestClient) -> None:
    r = client.get("/ping")
    assert r.status_code == 200
    assert r.json() == {"ok": True}
