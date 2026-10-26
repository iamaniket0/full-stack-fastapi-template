import ipaddress
import re
import socket
import tomllib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest
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


# --- GET /utils/ip/ -----------------------------------------------------------

IP_URL = f"{settings.API_V1_STR}/utils/ip/"


class FakeIpLookup:
    """
    Stands in for the external IP lookup service by intercepting every real
    httpx transport (sync and async). The TestClient uses its own transport,
    so requests to the app itself are not affected.
    """

    def __init__(self) -> None:
        self.calls: list[httpx.Request] = []
        self.body = "203.0.113.7"
        self.status_code = 200
        self.error: Exception | None = None

    def respond(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        if self.error is not None:
            raise self.error
        if request.url.params.get("format") == "json":
            return httpx.Response(
                self.status_code, json={"ip": self.body}, request=request
            )
        return httpx.Response(self.status_code, text=self.body, request=request)


@pytest.fixture
def ip_lookup(monkeypatch: pytest.MonkeyPatch) -> FakeIpLookup:
    fake = FakeIpLookup()

    def handle_request(
        _self: httpx.HTTPTransport, request: httpx.Request
    ) -> httpx.Response:
        return fake.respond(request)

    async def handle_async_request(
        _self: httpx.AsyncHTTPTransport, request: httpx.Request
    ) -> httpx.Response:
        return fake.respond(request)

    def no_network(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("Real network access attempted during tests")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", handle_request)
    monkeypatch.setattr(
        httpx.AsyncHTTPTransport, "handle_async_request", handle_async_request
    )
    monkeypatch.setattr(socket, "create_connection", no_network)
    monkeypatch.setattr(socket, "getaddrinfo", no_network)
    return fake


@pytest.mark.parametrize("address", ["203.0.113.7", "2001:db8::1"])
def test_get_ip_superuser(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    ip_lookup: FakeIpLookup,
    address: str,
) -> None:
    ip_lookup.body = address
    r = client.get(IP_URL, headers=superuser_token_headers)

    assert r.status_code == 200
    data = r.json()
    assert set(data) == {"ip"}
    assert ipaddress.ip_address(data["ip"]) == ipaddress.ip_address(address)
    assert len(ip_lookup.calls) >= 1


def test_get_ip_unauthenticated(client: TestClient, ip_lookup: FakeIpLookup) -> None:
    # Guard against a pass-by-404: the route must exist in the API schema.
    assert IP_URL in client.get(f"{settings.API_V1_STR}/openapi.json").json()["paths"]

    r = client.get(IP_URL)

    assert r.status_code == 401
    assert ip_lookup.calls == []


def test_get_ip_normal_user_forbidden(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    ip_lookup: FakeIpLookup,
) -> None:
    r = client.get(IP_URL, headers=normal_user_token_headers)

    assert r.status_code == 403
    assert ip_lookup.calls == []


@pytest.mark.parametrize(
    "failure",
    ["unreachable", "timeout", "server_error", "not_found"],
)
def test_get_ip_lookup_failure_returns_502(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    ip_lookup: FakeIpLookup,
    failure: str,
) -> None:
    if failure == "unreachable":
        ip_lookup.error = httpx.ConnectError("connection refused")
    elif failure == "timeout":
        ip_lookup.error = httpx.ReadTimeout("timed out")
    elif failure == "server_error":
        ip_lookup.status_code = 500
    else:
        ip_lookup.status_code = 404

    r = client.get(IP_URL, headers=superuser_token_headers)

    assert r.status_code == 502
    detail = r.json()["detail"]
    assert isinstance(detail, str)
    assert detail.strip()
    assert len(ip_lookup.calls) >= 1


@pytest.mark.parametrize(
    "bad_value",
    ["not-an-ip", "999.1.1.1", "<html>oops</html>", ""],
)
def test_get_ip_invalid_value_returns_502(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    ip_lookup: FakeIpLookup,
    bad_value: str,
) -> None:
    ip_lookup.body = bad_value
    r = client.get(IP_URL, headers=superuser_token_headers)

    assert r.status_code == 502
    assert "ip" not in r.json()
    if bad_value:
        assert bad_value not in r.text
    assert len(ip_lookup.calls) >= 1


def test_backend_dependencies_unchanged() -> None:
    pyproject = Path(__file__).resolve().parents[3] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text())

    assert data["project"]["dependencies"] == [
        "fastapi[standard]>=0.141.1,<1.0.0",
        "python-multipart<1.0.0,>=0.0.27",
        "email-validator<3.0.0.0,>=2.1.0.post1",
        "pydantic>=2.13.5",
        "emails>=1.1.2,<2.0",
        "jinja2<4.0.0,>=3.1.4",
        "alembic>=1.19.1,<2.0.0",
        "httpx<1.0.0,>=0.25.1",
        "psycopg[binary]>=3.3.6,<4.0.0",
        "sqlmodel>=0.0.46,<1.0.0",
        "pydantic-settings<3.0.0,>=2.2.1",
        "sentry-sdk[fastapi]>=2.70.0,<3.0.0",
        "pyjwt>=2.15.0,<3.0.0",
        "pwdlib[argon2,bcrypt]>=0.3.1",
    ]
    all_deps = data["project"]["dependencies"] + data["dependency-groups"]["dev"]
    names = [re.split(r"[\[<>=!~ ;]", dep, maxsplit=1)[0].lower() for dep in all_deps]
    assert "requests" not in names


def test_get_ip_in_openapi_under_utils_tag(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/openapi.json")

    assert r.status_code == 200
    paths = r.json()["paths"]
    assert IP_URL in paths
    operation = paths[IP_URL]["get"]
    assert "utils" in operation["tags"]
    assert "200" in operation["responses"]
