import ipaddress
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic.networks import EmailStr

from app.api.deps import get_current_active_superuser
from app.models import Message, PublicIP, ServerTime
from app.utils import generate_test_email, send_email

router = APIRouter(prefix="/utils", tags=["utils"])

PUBLIC_IP_LOOKUP_URL = "https://api.ipify.org"
PUBLIC_IP_LOOKUP_TIMEOUT = 5.0


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


@router.get(
    "/ip/",
    dependencies=[Depends(get_current_active_superuser)],
    responses={502: {"description": "The public IP lookup service failed"}},
)
def get_public_ip() -> PublicIP:
    """
    Return the server's public IP address, as seen by an external lookup service.
    """
    try:
        response = httpx.get(PUBLIC_IP_LOOKUP_URL, timeout=PUBLIC_IP_LOOKUP_TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPError:
        raise HTTPException(
            status_code=502, detail="Could not reach the public IP lookup service"
        )
    try:
        ip = ipaddress.ip_address(response.text.strip())
    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="The public IP lookup service returned an invalid address",
        )
    return PublicIP(ip=str(ip))
