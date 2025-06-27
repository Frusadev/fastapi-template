from datetime import datetime
from typing import Annotated, Optional

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.core.db.models import User
from app.api.routes.v1.dto.message import MessageDTO


async def get_hello_message(name: Optional[str] = None) -> MessageDTO:
    if name:
        return MessageDTO(message=f"Hello, {name}!")
    return MessageDTO(message="Hello, World!")


async def get_time_greeting() -> MessageDTO:
    current_hour = datetime.now().hour
    
    if 5 <= current_hour < 12:
        greeting = "Good morning"
    elif 12 <= current_hour < 17:
        greeting = "Good afternoon"
    elif 17 <= current_hour < 21:
        greeting = "Good evening"
    else:
        greeting = "Good night"
    
    return MessageDTO(message=f"{greeting}! Welcome to our API.")


async def get_user_greeting(current_user: User) -> MessageDTO:
    current_hour = datetime.now().hour
    if 5 <= current_hour < 12:
        greeting = "Good morning"
    elif 12 <= current_hour < 17:
        greeting = "Good afternoon"
    elif 17 <= current_hour < 21:
        greeting = "Good evening"
    else:
        greeting = "Good night"
    
    return MessageDTO(message=f"{greeting}, {current_user.name}! Nice to see you again.")


async def get_api_info() -> dict:
    return {
        "name": "FastAPI Template",
        "version": "1.0.0",
        "description": "A template for FastAPI applications with authentication",
        "timestamp": datetime.now().isoformat(),
        "status": "active"
    }


async def get_user_count(db_session: AsyncSession) -> dict:
    result = await db_session.exec(select(User))
    users = result.all()
    return {
        "total_users": len(users),
        "message": f"There are currently {len(users)} registered users"
    }
