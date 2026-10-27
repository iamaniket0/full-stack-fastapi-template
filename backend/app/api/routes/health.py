from datetime import UTC, datetime

from fastapi import APIRouter

from app.models import HealthDetails, HealthStatus

router = APIRouter(prefix="/health", tags=["utils"])


@router.get("")
def health() -> HealthStatus:
    """
    Liveness check returning {"status": "ok"}. Does not check the database or other dependencies.
    """
    return HealthStatus(status="ok")


@router.get("/details")
def health_details() -> HealthDetails:
    """
    Health check returning {"status": "ok"} and the current server time (UTC) in ISO 8601 format.
    """
    return HealthDetails(status="ok", time=datetime.now(UTC).isoformat())
