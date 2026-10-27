from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, func, select

from app.core.config import settings
from app.core.security import create_access_token
from app.models import User
from tests.utils.user import create_random_user

STATS_URL = f"{settings.API_V1_STR}/stats"


def get_stats(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    r = client.get(STATS_URL, headers=headers)
    assert r.status_code == 200
    data: dict[str, Any] = r.json()
    assert isinstance(data["total_users"], int)
    assert isinstance(data["new_users_last_7_days"], int)
    return data


def create_user_signed_up_at(db: Session, created_at: datetime | None) -> User:
    user = create_random_user(db)
    user.created_at = created_at
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def assert_no_user_counts(body: Any) -> None:
    assert isinstance(body, dict)
    assert "total_users" not in body
    assert "new_users_last_7_days" not in body


def test_stats_logged_in_user(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    data = get_stats(client, normal_user_token_headers)
    total_in_db = db.exec(select(func.count()).select_from(User)).one()
    assert data["total_users"] == total_in_db
    assert 0 <= data["new_users_last_7_days"] <= data["total_users"]


def test_stats_new_user_counts_as_recent(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    before = get_stats(client, normal_user_token_headers)
    create_random_user(db)
    after = get_stats(client, normal_user_token_headers)
    assert after["total_users"] == before["total_users"] + 1
    assert after["new_users_last_7_days"] == before["new_users_last_7_days"] + 1


def test_stats_2_days_and_10_days_ago(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    before = get_stats(client, normal_user_token_headers)
    now = datetime.now(UTC)
    create_user_signed_up_at(db, now - timedelta(days=2))
    create_user_signed_up_at(db, now - timedelta(days=10))
    after = get_stats(client, normal_user_token_headers)
    assert after["total_users"] == before["total_users"] + 2
    assert after["new_users_last_7_days"] == before["new_users_last_7_days"] + 1


def test_stats_just_over_7_days_ago_not_recent(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    before = get_stats(client, normal_user_token_headers)
    create_user_signed_up_at(db, datetime.now(UTC) - timedelta(days=7, minutes=1))
    after = get_stats(client, normal_user_token_headers)
    assert after["total_users"] == before["total_users"] + 1
    assert after["new_users_last_7_days"] == before["new_users_last_7_days"]


def test_stats_just_under_7_days_ago_is_recent(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    before = get_stats(client, normal_user_token_headers)
    create_user_signed_up_at(
        db, datetime.now(UTC) - timedelta(days=7) + timedelta(minutes=1)
    )
    after = get_stats(client, normal_user_token_headers)
    assert after["total_users"] == before["total_users"] + 1
    assert after["new_users_last_7_days"] == before["new_users_last_7_days"] + 1


def test_stats_user_without_sign_up_date(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    before = get_stats(client, normal_user_token_headers)
    user = create_user_signed_up_at(db, None)
    assert user.created_at is None
    after = get_stats(client, normal_user_token_headers)
    assert after["total_users"] == before["total_users"] + 1
    assert after["new_users_last_7_days"] == before["new_users_last_7_days"]


def test_stats_without_auth_token(client: TestClient) -> None:
    r = client.get(STATS_URL)
    assert "authorization" not in {k.lower() for k in r.request.headers}
    assert r.status_code == 401
    assert_no_user_counts(r.json())


@pytest.mark.parametrize(
    "token",
    [
        "not-a-valid-token",
        "abc.def.ghi",
        create_access_token("someone", expires_delta=timedelta(minutes=-5)),
    ],
    ids=["invalid", "malformed", "expired"],
)
def test_stats_with_bad_bearer_token(client: TestClient, token: str) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get(STATS_URL, headers=headers)
    other = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert other.status_code == 403
    assert r.status_code == other.status_code
    assert_no_user_counts(r.json())


def test_stats_normal_user_sees_same_counts_as_superuser(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers)
    assert r.json()["is_superuser"] is False
    normal = get_stats(client, normal_user_token_headers)
    superuser = get_stats(client, superuser_token_headers)
    assert normal == superuser
