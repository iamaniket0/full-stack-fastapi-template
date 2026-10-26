import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import Item, ItemCreate, LoginAttempt, User, UserCreate, UserUpdate

logger = logging.getLogger(__name__)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


# Dummy hash to use for timing attack prevention when user is not found
# This is an Argon2 hash of a random password, used to ensure constant-time comparison
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        # Prevent timing attacks by running password verification even when user doesn't exist
        # This ensures the response time is similar whether or not the email exists
        verify_password(password, DUMMY_HASH)
        return None
    verified, updated_password_hash = verify_password(password, db_user.hashed_password)
    if not verified:
        return None
    if updated_password_hash:
        db_user.hashed_password = updated_password_hash
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


def get_login_locked_until(*, session: Session, email: str) -> datetime | None:
    """Return when the email's lockout ends, or None if it is not locked out."""
    attempt = session.get(LoginAttempt, email.lower())
    if attempt and attempt.locked_until and attempt.locked_until > datetime.now(UTC):
        return attempt.locked_until
    return None


def record_failed_login(*, session: Session, email: str) -> None:
    """Count a failed login and lock the email out once the limit is reached."""
    email = email.lower()
    now = datetime.now(UTC)
    attempt = session.get(LoginAttempt, email, with_for_update=True)
    if attempt is None:
        attempt = LoginAttempt(email=email, failed_attempts=0, first_failed_at=now)
    window = timedelta(minutes=settings.LOGIN_ATTEMPT_WINDOW_MINUTES)
    lockout_expired = attempt.locked_until is not None and attempt.locked_until <= now
    if lockout_expired or attempt.first_failed_at + window < now:
        attempt.failed_attempts = 0
        attempt.first_failed_at = now
        attempt.locked_until = None
    attempt.failed_attempts += 1
    if attempt.failed_attempts >= settings.LOGIN_MAX_FAILED_ATTEMPTS:
        attempt.locked_until = now + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
        logger.warning(
            "Login locked out for email %s at %s after %d failed attempts, until %s",
            email,
            now.isoformat(),
            attempt.failed_attempts,
            attempt.locked_until.isoformat(),
        )
    session.add(attempt)
    session.commit()


def clear_failed_logins(*, session: Session, email: str) -> None:
    """Forget an email's failed attempts and lockout."""
    attempt = session.get(LoginAttempt, email.lower())
    if attempt:
        session.delete(attempt)
        session.commit()
