from fastapi.testclient import TestClient


def test_version(client: TestClient) -> None:
    r = client.get("/version")
    assert r.status_code == 200
    assert r.json() == {"version": "1.0.0"}
