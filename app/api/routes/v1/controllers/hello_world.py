from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.routes.v1.dto.hello_world import (
    ApiInfoResponseDTO,
    UserCountResponseDTO,
)
from app.api.routes.v1.dto.message import MessageDTO
from app.api.routes.v1.providers.auth import get_current_user
from app.api.routes.v1.providers.hello_world import (
    get_api_info,
    get_hello_message,
    get_time_greeting,
    get_user_count,
    get_user_greeting,
)
from app.core.db.models import User
from app.core.db.setup import create_db_session

router = APIRouter(prefix="/hello", tags=["Hello World"])


@router.get("/", response_model=MessageDTO)
async def hello_world(
    name: Annotated[str | None, Query(description="Optional name for personalized greeting")] = None,
):
    """Get a simple hello message, optionally personalized with a name."""
    return await get_hello_message(name)


@router.get("/greeting", response_model=MessageDTO)
async def time_greeting():
    """Get a time-based greeting message."""
    return await get_time_greeting()


@router.get("/user-greeting", response_model=MessageDTO)
async def user_greeting(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get a personalized greeting for the authenticated user."""
    return await get_user_greeting(current_user)


@router.get("/info", response_model=ApiInfoResponseDTO)
async def api_info():
    """Get basic API information."""
    return await get_api_info()


@router.get("/stats", response_model=UserCountResponseDTO)
async def user_stats(
    db_session: Annotated[AsyncSession, Depends(create_db_session)],
):
    """Get user statistics (requires authentication)."""
    return await get_user_count(db_session)
