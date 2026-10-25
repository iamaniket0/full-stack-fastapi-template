from datetime import UTC, datetime

from fastapi import APIRouter

from app.models import HealthDetails

router = APIRouter(prefix="/health", tags=["utils"])


@router.get("/details")
def health_details() -> HealthDetails:
    """
    Health check that returns status "ok" and the current server time (UTC) in ISO 8601 format.
    """
    return HealthDetails(status="ok", time=datetime.now(UTC).isoformat())
