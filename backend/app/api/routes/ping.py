from fastapi import APIRouter

from app.models import Ping

router = APIRouter(tags=["utils"])


@router.get("/ping")
def ping() -> Ping:
    """
    Simple liveness check that returns {"ok": true}.
    """
    return Ping(ok=True)
