from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import LoginAttempt, UserCreate, UserUpdate
from tests.utils.utils import random_email, random_lower_string

LOGIN_URL = f"{settings.API_V1_STR}/login/access-token"


def test_failures_outside_window_start_a_new_count(db: Session) -> None:
    email = random_email()
    for _ in range(settings.LOGIN_MAX_FAILED_ATTEMPTS - 1):
        crud.record_failed_login(session=db, email=email)

    attempt = db.get(LoginAttempt, email)
    assert attempt
    attempt.first_failed_at = datetime.now(UTC) - timedelta(
        minutes=settings.LOGIN_ATTEMPT_WINDOW_MINUTES + 1
    )
    db.add(attempt)
    db.commit()

    crud.record_failed_login(session=db, email=email)
    db.refresh(attempt)
    assert attempt.failed_attempts == 1
    assert crud.get_login_locked_until(session=db, email=email) is None


def test_failure_after_expired_lockout_starts_a_new_count(db: Session) -> None:
    email = random_email()
    with patch.object(settings, "LOGIN_LOCKOUT_MINUTES", 0):
        for _ in range(settings.LOGIN_MAX_FAILED_ATTEMPTS):
            crud.record_failed_login(session=db, email=email)
    assert crud.get_login_locked_until(session=db, email=email) is None

    crud.record_failed_login(session=db, email=email)
    attempt = db.get(LoginAttempt, email)
    assert attempt
    db.refresh(attempt)
    assert attempt.failed_attempts == 1
    assert attempt.locked_until is None


def test_inactive_user_with_correct_password_is_not_counted(
    client: TestClient, db: Session
) -> None:
    email = random_email()
    password = random_lower_string()
    user = crud.create_user(
        session=db, user_create=UserCreate(email=email, password=password)
    )
    crud.update_user(session=db, db_user=user, user_in=UserUpdate(is_active=False))

    for _ in range(settings.LOGIN_MAX_FAILED_ATTEMPTS + 1):
        r = client.post(LOGIN_URL, data={"username": email, "password": password})
        assert r.status_code == 400
        assert r.json()["detail"] == "Inactive user"


def test_lockout_response_has_retry_after_header(client: TestClient) -> None:
    email = random_email()
    for _ in range(settings.LOGIN_MAX_FAILED_ATTEMPTS):
        client.post(LOGIN_URL, data={"username": email, "password": "wrong"})

    r = client.post(LOGIN_URL, data={"username": email, "password": "wrong"})
    assert r.status_code == 429
    assert 0 < int(r.headers["Retry-After"]) <= settings.LOGIN_LOCKOUT_MINUTES * 60
