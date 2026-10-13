from fastapi import APIRouter

from app.models import Message

router = APIRouter(tags=["hello"])


@router.get("/hello")
def hello() -> Message:
    """
    Say hello.
    """
    return Message(message="Hello, World!")
