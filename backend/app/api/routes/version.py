from fastapi import APIRouter

from app.models import Version

router = APIRouter(tags=["utils"])


@router.get("/version")
def version() -> Version:
    """
    Return the API version.
    """
    return Version(version="1.0.0")
