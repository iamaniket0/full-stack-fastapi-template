import logging
import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import Settings, settings
from app.crud import create_user
from app.models import UserCreate
from tests.utils.utils import random_email, random_lower_string

LOGIN_URL = f"{settings.API_V1_STR}/login/access-token"


def unlock_url(email: str) -> str:
    return f"{settings.API_V1_STR}/login/unlock/{email}"


def create_user_with_password(db: Session) -> tuple[str, str]:
    email = random_email()
    password = random_lower_string()
    create_user(session=db, user_create=UserCreate(email=email, password=password))
    return email, password


def login(client: TestClient, email: str, password: str):  # type: ignore[no-untyped-def]
    return client.post(LOGIN_URL, data={"username": email, "password": password})


def fail_logins(client: TestClient, email: str, times: int) -> list[int]:
    return [login(client, email, "wrong-password").status_code for _ in range(times)]


def assert_locked_response(r) -> None:  # type: ignore[no-untyped-def]
    assert r.status_code == 429
    body = r.json()
    assert "access_token" not in body
    detail = body["detail"].lower()
    assert "too many failed attempts" in detail
    assert "try again later" in detail


# Criterion 1


def test_fifth_failure_returns_400_then_later_attempts_return_429(
    client: TestClient, db: Session
) -> None:
    email, _ = create_user_with_password(db)

    assert fail_logins(client, email, 4) == [400, 400, 400, 400]

    r = login(client, email, "wrong-password")
    assert r.status_code == 400

    assert_locked_response(login(client, email, "wrong-password"))
    assert_locked_response(login(client, email, "another-wrong-password"))


def test_lockout_matches_email_case_insensitively(
    client: TestClient, db: Session
) -> None:
    email, password = create_user_with_password(db)

    assert fail_logins(client, email.upper(), 5) == [400] * 5

    assert_locked_response(login(client, email, password))


def test_unknown_email_is_locked_out_the_same_way(client: TestClient) -> None:
    email = random_email()

    assert fail_logins(client, email, 5) == [400] * 5

    assert_locked_response(login(client, email, "wrong-password"))


# Criterion 2


def test_correct_password_during_lockout_returns_429_without_token(
    client: TestClient, db: Session
) -> None:
    email, password = create_user_with_password(db)
    fail_logins(client, email, 5)

    assert_locked_response(login(client, email, password))


# Criterion 3


def test_login_succeeds_after_lockout_expires(client: TestClient, db: Session) -> None:
    email, password = create_user_with_password(db)

    # A 3-second lockout stands in for the 15-minute default.
    with patch.object(settings, "LOGIN_LOCKOUT_MINUTES", 0.05):
        fail_logins(client, email, 5)
        assert_locked_response(login(client, email, password))

        time.sleep(4)

        r = login(client, email, password)
        assert r.status_code == 200
        assert r.json()["access_token"]


# Criterion 4


def test_successful_login_resets_failed_attempt_counter(
    client: TestClient, db: Session
) -> None:
    email, password = create_user_with_password(db)

    assert fail_logins(client, email, 3) == [400, 400, 400]
    assert login(client, email, password).status_code == 200

    assert fail_logins(client, email, 4) == [400, 400, 400, 400]

    # The counter started again at zero, so the lockout comes after 5 new failures.
    assert login(client, email, "wrong-password").status_code == 400
    assert_locked_response(login(client, email, password))


# Criterion 5


def test_lockout_of_one_email_does_not_affect_another(
    client: TestClient, db: Session
) -> None:
    email_a, password_a = create_user_with_password(db)
    email_b, password_b = create_user_with_password(db)

    fail_logins(client, email_a, 5)
    assert_locked_response(login(client, email_a, password_a))

    r = login(client, email_b, password_b)
    assert r.status_code == 200
    assert r.json()["access_token"]


# Criterion 6


def test_superuser_unlock_allows_immediate_login(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    email, password = create_user_with_password(db)
    fail_logins(client, email, 5)
    assert_locked_response(login(client, email, password))

    r = client.post(unlock_url(email), headers=superuser_token_headers)
    assert r.status_code == 200
    assert "message" in r.json()

    r = login(client, email, password)
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_unlock_resets_failed_attempts(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    email, password = create_user_with_password(db)
    fail_logins(client, email, 5)

    r = client.post(unlock_url(email), headers=superuser_token_headers)
    assert r.status_code == 200

    assert fail_logins(client, email, 5) == [400] * 5
    assert_locked_response(login(client, email, password))


def test_unlock_email_that_is_not_locked_succeeds(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.post(unlock_url(random_email()), headers=superuser_token_headers)
    assert r.status_code == 200
    assert "message" in r.json()


# Criterion 7


def test_regular_user_cannot_unlock(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    email, password = create_user_with_password(db)
    fail_logins(client, email, 5)
    assert_locked_response(login(client, email, password))

    r = client.post(unlock_url(email), headers=normal_user_token_headers)
    assert r.status_code == 403

    assert_locked_response(login(client, email, password))


def test_unauthenticated_cannot_unlock(client: TestClient, db: Session) -> None:
    email, password = create_user_with_password(db)
    fail_logins(client, email, 5)
    assert_locked_response(login(client, email, password))

    r = client.post(unlock_url(email))
    assert r.status_code == 401

    assert_locked_response(login(client, email, password))


# Criterion 8


def test_lockout_settings_have_defaults() -> None:
    assert settings.LOGIN_MAX_FAILED_ATTEMPTS == 5
    assert settings.LOGIN_ATTEMPT_WINDOW_MINUTES == 15
    assert settings.LOGIN_LOCKOUT_MINUTES == 15


def test_lockout_settings_are_read_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOGIN_MAX_FAILED_ATTEMPTS", "3")
    monkeypatch.setenv("LOGIN_ATTEMPT_WINDOW_MINUTES", "30")
    monkeypatch.setenv("LOGIN_LOCKOUT_MINUTES", "60")

    new_settings = Settings()  # type: ignore[call-arg]

    assert new_settings.LOGIN_MAX_FAILED_ATTEMPTS == 3
    assert new_settings.LOGIN_ATTEMPT_WINDOW_MINUTES == 30
    assert new_settings.LOGIN_LOCKOUT_MINUTES == 60


def test_configured_attempt_limit_is_applied(client: TestClient, db: Session) -> None:
    email, password = create_user_with_password(db)

    with patch.object(settings, "LOGIN_MAX_FAILED_ATTEMPTS", 2):
        assert fail_logins(client, email, 2) == [400, 400]
        assert_locked_response(login(client, email, password))


# Criterion 9


def test_lockout_is_logged_with_email_and_without_password(
    client: TestClient, db: Session, caplog: pytest.LogCaptureFixture
) -> None:
    email, password = create_user_with_password(db)
    wrong_password = "wrong-" + random_lower_string()

    with caplog.at_level(logging.INFO):
        for _ in range(5):
            login(client, email, wrong_password)
        assert_locked_response(login(client, email, password))

    lockout_records = [r for r in caplog.records if email in r.getMessage()]
    assert lockout_records, "expected a log entry mentioning the locked-out email"
    assert all(r.created > 0 for r in lockout_records)
    for record in caplog.records:
        message = record.getMessage()
        assert wrong_password not in message
        assert password not in message
