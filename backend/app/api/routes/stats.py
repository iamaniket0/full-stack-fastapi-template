from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import col, func, select

from app.api.deps import SessionDep, TokenDep, get_current_user
from app.models import User, UserStats

router = APIRouter(prefix="/stats", tags=["stats"])


def get_stats_user(session: SessionDep, token: TokenDep) -> User:
    """
    Same as get_current_user, but a token that fails validation gives 401, not 403.
    """
    try:
        return get_current_user(session, token)
    except HTTPException as exc:
        if exc.status_code != status.HTTP_403_FORBIDDEN:
            raise
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@router.get("", dependencies=[Depends(get_stats_user)])
def read_stats(session: SessionDep) -> UserStats:
    """
    User statistics for logged-in users: the total number of registered users and
    how many signed up in the last 7 days. Users without a sign-up date count only
    toward the total.

    A missing, invalid, malformed or expired token gives 401.
    """
    since = datetime.now(UTC) - timedelta(days=7)
    total_users = session.exec(select(func.count()).select_from(User)).one()
    new_users_last_7_days = session.exec(
        select(func.count()).select_from(User).where(col(User.created_at) >= since)
    ).one()
    return UserStats(
        total_users=total_users, new_users_last_7_days=new_users_last_7_days
    )
