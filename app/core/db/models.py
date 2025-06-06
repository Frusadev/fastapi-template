from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from app.utils.crypto import gen_id


class RoleUserLink(SQLModel, table=True):
    user_id: str = Field(foreign_key="user.id", primary_key=True)
    role_id: str = Field(foreign_key="role.id", primary_key=True)


class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: gen_id(10), primary_key=True)
    email: str
    username: str
    name: str
    login_sessions: list["LoginSession"] = Relationship(back_populates="user")
    auth_sessions: list["AuthSession"] = Relationship(back_populates="user")
    roles: list["Role"] = Relationship(
        back_populates="users", link_model=RoleUserLink
    )


class Role(SQLModel, table=True):
    id: str = Field(default_factory=gen_id, primary_key=True)
    name: str | None = None
    permissions: list["Permission"] = Relationship(back_populates="role")
    users: list[User] = Relationship(
        back_populates="roles", link_model=RoleUserLink
    )


class Permission(SQLModel, table=True):
    permission_id: str = Field(default_factory=gen_id, primary_key=True)
    name: str = Field(primary_key=True)
    role_id: str | None = Field(foreign_key="role.id", default=None)
    role: Role = Relationship(back_populates="permissions")


class LoginSession(SQLModel, table=True):
    id: str = Field(default_factory=lambda: gen_id(30), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=60)
    )
    expired: bool = False
    user: User = Relationship(back_populates="login_sessions")


class AuthSession(SQLModel, table=True):
    id: str = Field(default_factory=lambda: gen_id(50), primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=2)
    )
    expired: bool = False
    user: User = Relationship(back_populates="auth_sessions")
