from importlib.metadata import version as package_version

from fastapi import APIRouter

from app.models import AppVersion

router = APIRouter(prefix="/version", tags=["utils"])


@router.get("")
def version() -> AppVersion:
    """
    Return the backend app version, read from the installed package metadata.
    """
    return AppVersion(version=package_version("app"))
