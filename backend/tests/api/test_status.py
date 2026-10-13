from fastapi.testclient import TestClient


def test_status(client: TestClient) -> None:
    r = client.get("/status")
    assert r.status_code == 200
    assert r.json() == {"healthy": True}
