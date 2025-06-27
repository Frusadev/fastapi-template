from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.routes.v1.dto.auth import (
    LoginRequestDTO,
    RegisterRequestDTO,
    UserResponseDTO,
)
from app.api.routes.v1.dto.message import MessageDTO
from app.api.routes.v1.providers.auth import (
    get_current_user,
    login,
    register,
)
from app.core.db.models import User
from app.core.db.setup import create_db_session

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=MessageDTO)
async def register_user(
    request: RegisterRequestDTO,
    db_session: Annotated[AsyncSession, Depends(create_db_session)],
):
    """Register a new user account."""
    return await register(
        db_session=db_session,
        username=request.username,
        email=request.email,
        password=request.password,
        password_confirm=request.password_confirm,
        name=request.name,
    )


@router.post("/login", response_model=MessageDTO)
async def login_user(
    request: LoginRequestDTO,
    response: Response,
    db_session: Annotated[AsyncSession, Depends(create_db_session)],
):
    """Login user and create session."""
    return await login(
        db_session=db_session,
        email=request.email,
        password=request.password,
        response=response,
    )


@router.get("/me", response_model=UserResponseDTO)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current authenticated user information."""
    return current_user


@router.post("/logout", response_model=MessageDTO)
async def logout_user(
    response: Response,
):
    """Logout user by clearing session cookie."""
    response.delete_cookie(key="user_session_id", httponly=True)
    return MessageDTO(message="Logged out successfully.")
