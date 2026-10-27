from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlmodel import col, func, select

from app.api.deps import SessionDep, get_current_user
from app.models import User, UserStats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", dependencies=[Depends(get_current_user)])
def read_stats(session: SessionDep) -> UserStats:
    """
    User statistics for logged-in users: the total number of registered users and
    how many signed up in the last 7 days. Users without a sign-up date count only
    toward the total.
    """
    since = datetime.now(UTC) - timedelta(days=7)
    total_users = session.exec(select(func.count()).select_from(User)).one()
    new_users_last_7_days = session.exec(
        select(func.count()).select_from(User).where(col(User.created_at) >= since)
    ).one()
    return UserStats(
        total_users=total_users, new_users_last_7_days=new_users_last_7_days
    )
