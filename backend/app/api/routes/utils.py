from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from pydantic.networks import EmailStr

from app.api.deps import get_current_active_superuser
from app.models import Message
from app.utils import generate_test_email, send_email
from app.version import __version__

router = APIRouter(prefix="/utils", tags=["utils"])


class ServerTime(BaseModel):
    time: str


class VersionResponse(BaseModel):
    version: str


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/health-check/")
async def health_check() -> bool:
    return True


@router.get("/time/")
def get_time() -> ServerTime:
    """
    Return the current server time (UTC) in ISO 8601 format.
    """
    return ServerTime(time=datetime.now(UTC).isoformat())


@router.get("/version/")
def get_version() -> VersionResponse:
    """
    Return the app version.
    """
    return VersionResponse(version=__version__)
