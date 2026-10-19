"""
End-to-end tests for the backend.

Each test walks through a complete user journey using only the public HTTP API,
chaining several endpoints together the way a real client (e.g. the frontend)
would, instead of exercising a single endpoint in isolation.
"""

import csv
import io
import re
from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import settings
from tests.utils.utils import random_email, random_lower_string

API = settings.API_V1_STR


def signup(
    client: TestClient, email: str, password: str, full_name: str
) -> dict[str, Any]:
    r = client.post(
        f"{API}/users/signup",
        json={"email": email, "password": password, "full_name": full_name},
    )
    assert r.status_code == 200, r.text
    user: dict[str, Any] = r.json()
    return user


def login(client: TestClient, email: str, password: str) -> dict[str, str]:
    r = client.post(
        f"{API}/login/access-token", data={"username": email, "password": password}
    )
    assert r.status_code == 200, r.text
    token = r.json()
    assert token["token_type"] == "bearer"
    return {"Authorization": f"Bearer {token['access_token']}"}


def login_status(client: TestClient, email: str, password: str) -> int:
    r = client.post(
        f"{API}/login/access-token", data={"username": email, "password": password}
    )
    return int(r.status_code)


def test_new_user_full_lifecycle(client: TestClient) -> None:
    email = random_email()
    password = random_lower_string()

    # Sign up and log in
    user = signup(client, email, password, "Journey User")
    assert user["email"] == email
    assert user["is_active"] is True
    assert user["is_superuser"] is False
    headers = login(client, email, password)

    r = client.post(f"{API}/login/test-token", headers=headers)
    assert r.status_code == 200
    assert r.json()["id"] == user["id"]

    # Signing up again with the same email is rejected
    r = client.post(f"{API}/users/signup", json={"email": email, "password": password})
    assert r.status_code == 400

    # Update own profile
    r = client.patch(
        f"{API}/users/me", headers=headers, json={"full_name": "Renamed User"}
    )
    assert r.status_code == 200
    r = client.get(f"{API}/users/me", headers=headers)
    assert r.json()["full_name"] == "Renamed User"
    assert r.json()["email"] == email

    # A brand new user has no items
    r = client.get(f"{API}/items/count", headers=headers)
    assert r.json() == 0

    # Create items
    r = client.post(
        f"{API}/items/",
        headers=headers,
        json={"title": "First", "description": "first item"},
    )
    assert r.status_code == 200
    first = r.json()
    assert first["owner_id"] == user["id"]
    r = client.post(f"{API}/items/", headers=headers, json={"title": "Second"})
    assert r.status_code == 200
    second = r.json()

    r = client.get(f"{API}/items/", headers=headers)
    assert r.status_code == 200
    listing = r.json()
    assert listing["count"] == 2
    # Newest first
    assert [i["id"] for i in listing["data"]] == [second["id"], first["id"]]
    assert client.get(f"{API}/items/count", headers=headers).json() == 2

    # Read and update an item
    r = client.get(f"{API}/items/{first['id']}", headers=headers)
    assert r.status_code == 200
    assert r.json()["title"] == "First"
    r = client.put(
        f"{API}/items/{first['id']}",
        headers=headers,
        json={"title": "First (edited)"},
    )
    assert r.status_code == 200
    assert r.json()["title"] == "First (edited)"
    assert r.json()["description"] == "first item"

    # Export reflects the current state of the user's items
    r = client.get(f"{API}/items/export", headers=headers)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    rows = list(csv.reader(io.StringIO(r.text)))
    assert rows[0] == ["id", "title", "description"]
    assert sorted(rows[1:]) == sorted(
        [
            [first["id"], "First (edited)", "first item"],
            [second["id"], "Second", ""],
        ]
    )

    # Delete an item
    r = client.delete(f"{API}/items/{second['id']}", headers=headers)
    assert r.status_code == 200
    assert client.get(f"{API}/items/{second['id']}", headers=headers).status_code == 404
    assert client.get(f"{API}/items/count", headers=headers).json() == 1

    # Change password: old one stops working, new one works
    new_password = random_lower_string()
    r = client.patch(
        f"{API}/users/me/password",
        headers=headers,
        json={"current_password": password, "new_password": new_password},
    )
    assert r.status_code == 200
    assert login_status(client, email, password) == 400
    headers = login(client, email, new_password)

    # Delete the account: the user can no longer log in or use their token
    r = client.delete(f"{API}/users/me", headers=headers)
    assert r.status_code == 200
    assert login_status(client, email, new_password) == 400
    assert client.get(f"{API}/users/me", headers=headers).status_code == 404


def test_password_recovery_flow(client: TestClient) -> None:
    email = random_email()
    password = random_lower_string()
    signup(client, email, password, "Forgetful User")

    # Request a recovery email and grab the reset link it would contain
    with patch("app.api.routes.login.send_email") as send_email:
        r = client.post(f"{API}/password-recovery/{email}")
    assert r.status_code == 200
    send_email.assert_called_once()
    assert send_email.call_args.kwargs["email_to"] == email
    match = re.search(
        r"/reset-password\?token=([\w\-.]+)",
        send_email.call_args.kwargs["html_content"],
    )
    assert match, "reset link not found in recovery email"
    token = match.group(1)

    # Use the token to set a new password
    new_password = random_lower_string()
    r = client.post(
        f"{API}/reset-password/",
        json={"token": token, "new_password": new_password},
    )
    assert r.status_code == 200
    assert r.json() == {"message": "Password updated successfully"}

    assert login_status(client, email, password) == 400
    login(client, email, new_password)


def test_users_cannot_access_each_others_items(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    alice_email, alice_password = random_email(), random_lower_string()
    bob_email, bob_password = random_email(), random_lower_string()
    signup(client, alice_email, alice_password, "Alice")
    signup(client, bob_email, bob_password, "Bob")
    alice = login(client, alice_email, alice_password)
    bob = login(client, bob_email, bob_password)

    r = client.post(f"{API}/items/", headers=alice, json={"title": "Alice's secret"})
    item_id = r.json()["id"]

    # Bob cannot see, change or delete Alice's item
    assert client.get(f"{API}/items/{item_id}", headers=bob).status_code == 403
    assert (
        client.put(
            f"{API}/items/{item_id}", headers=bob, json={"title": "hacked"}
        ).status_code
        == 403
    )
    assert client.delete(f"{API}/items/{item_id}", headers=bob).status_code == 403
    assert client.get(f"{API}/items/", headers=bob).json() == {"data": [], "count": 0}
    assert client.get(f"{API}/items/count", headers=bob).json() == 0
    export_rows = list(
        csv.reader(io.StringIO(client.get(f"{API}/items/export", headers=bob).text))
    )
    assert export_rows == [["id", "title", "description"]]

    # Bob cannot use admin endpoints
    assert client.get(f"{API}/users/", headers=bob).status_code == 403

    # Alice's item is untouched, and a superuser can still see it
    r = client.get(f"{API}/items/{item_id}", headers=alice)
    assert r.json()["title"] == "Alice's secret"
    r = client.get(f"{API}/items/{item_id}", headers=superuser_token_headers)
    assert r.status_code == 200


def test_superuser_manages_user_lifecycle(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    email = random_email()
    password = random_lower_string()

    # Admin creates an account
    with patch("app.api.routes.users.send_email"):
        r = client.post(
            f"{API}/users/",
            headers=superuser_token_headers,
            json={"email": email, "password": password, "full_name": "Managed"},
        )
    assert r.status_code == 200
    user_id = r.json()["id"]

    # The new user logs in and creates an item
    headers = login(client, email, password)
    r = client.post(f"{API}/items/", headers=headers, json={"title": "Managed item"})
    item_id = r.json()["id"]

    # Admin can look the user up and sees the item
    r = client.get(f"{API}/users/{user_id}", headers=superuser_token_headers)
    assert r.status_code == 200
    assert r.json()["email"] == email
    r = client.get(f"{API}/items/{item_id}", headers=superuser_token_headers)
    assert r.json()["owner_id"] == user_id

    # Admin deactivates the user: login and existing tokens stop working
    r = client.patch(
        f"{API}/users/{user_id}",
        headers=superuser_token_headers,
        json={"is_active": False},
    )
    assert r.status_code == 200
    assert r.json()["is_active"] is False
    assert login_status(client, email, password) == 400
    assert client.get(f"{API}/users/me", headers=headers).status_code == 400

    # Admin reactivates the user
    r = client.patch(
        f"{API}/users/{user_id}",
        headers=superuser_token_headers,
        json={"is_active": True},
    )
    assert r.status_code == 200
    headers = login(client, email, password)

    # Admin deletes the user, which also removes their items
    r = client.delete(f"{API}/users/{user_id}", headers=superuser_token_headers)
    assert r.status_code == 200
    r = client.get(f"{API}/users/{user_id}", headers=superuser_token_headers)
    assert r.status_code == 404
    r = client.get(f"{API}/items/{item_id}", headers=superuser_token_headers)
    assert r.status_code == 404
    assert login_status(client, email, password) == 400


def test_protected_endpoints_require_authentication(client: TestClient) -> None:
    assert client.get(f"{API}/utils/health-check/").json() is True

    for method, path in [
        ("GET", "/users/me"),
        ("GET", "/users/"),
        ("GET", "/items/"),
        ("GET", "/items/count"),
        ("GET", "/items/export"),
        ("POST", "/items/"),
        ("POST", "/login/test-token"),
    ]:
        r = client.request(method, f"{API}{path}")
        assert r.status_code == 401, f"{method} {path} returned {r.status_code}"

    r = client.get(
        f"{API}/users/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert r.status_code == 403
