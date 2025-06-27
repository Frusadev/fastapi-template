from collections.abc import Sequence
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)

from app.core.db.models import Permission, Role
from app.core.security.checkers import check_existence

EXEMPLE_RESOURCE = "resource"
USER_RESOURCE = "user"

ACTION_CREATE = "c"
ACTION_READ = "r"
ACTION_READWRITE = "rw"
ACTION_UPDATE = "w"
ACTION_DELETE = "d"


async def create_global_permission(
    role_id: str,
    db_session: AsyncSession,
    resource_name: str,
    action_name: str,
    commit: bool = True,
):
    role = await db_session.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Role not found."
        )
    permission_in_db = (
        await db_session.exec(
            select(Permission).where(
                Permission.role_id == role_id,
                Permission.name == f"{resource_name}:{action_name}",
            )
        )
    ).first()
    if permission_in_db:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail="The user already has this permission.",
        )
    permission = Permission(
        name=f"{resource_name}:{action_name}",
        role_id=role_id,
    )
    if commit:
        db_session.add(permission)
        await db_session.commit()
        await db_session.refresh(permission)
    else:
        db_session.add(permission)
        return permission


async def create_permission(
    _role: Role | None,
    db_session: AsyncSession,
    resource_name: str,
    resource_id: Any,
    action_name: str,
    commit: bool = True,
):
    role = check_existence(
        _role,
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Not authorized to access this resource.",
    )
    permission_in_db = (
        await db_session.exec(
            select(Permission).where(
                Permission.role_id == role.id,
                Permission.name
                == f"{resource_name}:{str(resource_id)}:{action_name}",
            )
        )
    ).first()
    if permission_in_db:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail="The user already has this permission.",
        )
    permission = Permission(
        name=f"{resource_name}:{resource_id}:{action_name}",
        role_id=role.id,
    )
    if commit:
        db_session.add(permission)
        await db_session.commit()
        await db_session.refresh(permission)
    return permission


async def has_permission(
    db_session: AsyncSession,
    role: Role,
    resource_name: str,
    resource_id: str,
    action_name: str,
) -> bool:
    permission = (
        await db_session.exec(
            select(Permission).where(
                Permission.role_id == role.id,
                Permission.name == f"{resource_name}:{resource_id}:{action_name}",
            )
        )
    ).first()
    return permission is not None


async def has_global_permission(
    db_session: AsyncSession,
    role: Role,
    resource_name: str,
    action_name: str,
) -> bool:
    permission = (
        await db_session.exec(
            select(Permission).where(
                Permission.role_id == role.id,
                Permission.name == f"{resource_name}:{action_name}",
            )
        )
    ).first()
    return permission is not None


class PermissionCheckModel(BaseModel):
    resource_name: str
    resource_id: Any
    action_names: list[str]


class GlobalPermissionCheckModel(BaseModel):
    resource_name: str
    action_names: list[str]


class PermissionChecker(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    db_session: AsyncSession
    roles: list[Role]
    bypass_role: str | None = None
    pcheck_models: Sequence[PermissionCheckModel | GlobalPermissionCheckModel]

    async def _is_allowed(
        self,
        role: Role,
        pcheck: PermissionCheckModel | GlobalPermissionCheckModel,
        action_name: str,
    ) -> bool:
        if isinstance(pcheck, PermissionCheckModel):
            return await has_permission(
                db_session=self.db_session,
                role=role,
                resource_name=pcheck.resource_name,
                resource_id=str(pcheck.resource_id),
                action_name=action_name,
            )
        elif isinstance(pcheck, GlobalPermissionCheckModel):
            return await has_global_permission(
                db_session=self.db_session,
                role=role,
                resource_name=pcheck.resource_name,
                action_name=action_name,
            )

    async def check(self, either: bool = False) -> bool:
        if self.bypass_role in [role.name for role in self.roles]:
            return True
        if either:
            # Check if any permission is satisfied
            for role in self.roles:
                for pcheck in self.pcheck_models:
                    for action_name in pcheck.action_names:
                        if await self._is_allowed(role, pcheck, action_name):
                            return True
            raise HTTPException(401, "Not authorized to access this resource")

        # Check if all permissions are satisfied for at least one role
        for role in self.roles:
            all_permissions_satisfied = True
            for pcheck in self.pcheck_models:
                for action_name in pcheck.action_names:
                    if not await self._is_allowed(role, pcheck, action_name):
                        all_permissions_satisfied = False
                        break
                if not all_permissions_satisfied:
                    break
            if all_permissions_satisfied:
                return True

        raise HTTPException(401, "Not authorized to access resource")
