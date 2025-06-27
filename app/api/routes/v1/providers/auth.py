from datetime import datetime, timezone
from typing import Annotated, Optional

from fastapi import Cookie, Depends, Response
from pydantic import EmailStr
from sqlmodel import or_, select
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_401_UNAUTHORIZED

from app.api.routes.v1.dto.message import MessageDTO
from app.core.db.builders.permission import PermissionBuilder
from app.core.db.builders.role import RoleBuilder
from app.core.db.models import (
    LoginSession,
    User,
)
from app.core.db.setup import create_db_session
from app.core.security.checkers import (
    check_conditions,
    check_equality,
    check_existence,
    check_non_existence,
)
from app.core.security.permissions import ACTION_READWRITE, USER_RESOURCE
from app.utils.crypto import hash_password, verify_password


async def register(
    db_session: AsyncSession,
    username: str,
    email: EmailStr,
    password: str,
    password_confirm: str,
    name: str,
):
    check_non_existence(
        (
            await db_session.exec(
                select(User).where(
                    or_(User.email == email, User.username == username)
                )
            )
        ).first()
    )
    check_equality(password, password_confirm)
    hashed_password = hash_password(password=password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        name=name,
    )
    role = RoleBuilder().addUser(user).make()
    perm = (
        PermissionBuilder()
        .withActionName(ACTION_READWRITE)
        .withResourceName(USER_RESOURCE)
        .withResourceId(user.id)
        .forRole(role)
        .make()
    )

    db_session.add_all([user, perm, role])
    await db_session.commit()
    return MessageDTO(message="Registered !")


async def login(
    db_session: AsyncSession,
    email: EmailStr,
    password: str,
    response: Response,
):
    user = check_existence(
        (
            await db_session.exec(select(User).where(User.email == email))
        ).first()
    )
    check_conditions([verify_password(password, user.hashed_password)])

    login_session = LoginSession(user_id=user.id)
    db_session.add(login_session)
    await db_session.commit()
    response.set_cookie(
        key="user_session_id",
        value=login_session.id,
        httponly=True,
        expires=login_session.expires_at.astimezone(timezone.utc),
    )
    return MessageDTO(message="Logged in successfully.")


async def get_current_user(
    db_session: Annotated[AsyncSession, Depends(create_db_session)],
    session_id: Annotated[str | None, Cookie(alias="user_session_id")] = None,
):
    login_session = check_existence(
        await db_session.get(LoginSession, session_id),
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authenticated.",
    )
    check_conditions(
        [
            login_session.expires_at > datetime.utcnow(),
            not login_session.expired,
        ],
        detail="Not authenticated.",
    )
    return login_session.user


async def ws_get_current_user(
    db_session: Annotated[AsyncSession, Depends(create_db_session)],
    session_id: Annotated[str | None, Cookie(alias="user_session_id")] = None,
):
    login_session = check_existence(
        await db_session.get(LoginSession, session_id),
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authenticated.",
    )
    check_conditions(
        [
            login_session.expires_at > datetime.utcnow(),
            not login_session.expired,
        ],
        detail="Not authenticated.",
        is_ws=True,
    )
    return login_session.user
