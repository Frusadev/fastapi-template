from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class HelloRequestDTO(BaseModel):
    name: Optional[str] = None


class ApiInfoResponseDTO(BaseModel):
    name: str
    version: str
    description: str
    timestamp: str
    status: str


class UserCountResponseDTO(BaseModel):
    total_users: int
    message: str
