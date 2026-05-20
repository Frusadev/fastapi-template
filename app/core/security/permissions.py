from collections.abc import Sequence
from typing import Any, Literal

from fastapi import HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
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


def create_global_permission(
    role_id: str,
    db_session: Session,
    resource_name: str,
    action_name: str,
    commit: bool = True,
):
    role = db_session.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="Role not found."
        )
    permission_in_db = db_session.exec(
        select(Permission).where(
            Permission.role_id == role_id,
            Permission.name == f"{resource_name}:{action_name}",
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
        db_session.commit()
        db_session.refresh(permission)
    else:
        db_session.add(permission)
        return permission


def create_permission(
    _role: Role | None,
    db_session: Session,
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
    permission_in_db = db_session.exec(
        select(Permission).where(
            Permission.role_id == role.id,
            Permission.name
            == f"{resource_name}:{str(resource_id)}:{action_name}",
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
        db_session.commit()
        db_session.refresh(permission)
    return permission


def has_permission(
    db_session: Session,
    role: Role,
    resource_name: str,
    resource_id: str,
    action_name: str,
) -> bool:
    permission = db_session.exec(
        select(Permission).where(
            Permission.role_id == role.id,
            Permission.name == f"{resource_name}:{resource_id}:{action_name}",
        )
    ).first()
    return permission is not None


def has_global_permission(
    db_session: Session,
    role: Role,
    resource_name: str,
    action_name: str,
) -> bool:
    permission = db_session.exec(
        select(Permission).where(
            Permission.role_id == role.id,
            Permission.name == f"{resource_name}:{action_name}",
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
    db_session: Session
    roles: list[Role]
    bypass_role: Literal["admin", "superadmin"] | str | None = None
    pcheck_models: Sequence[PermissionCheckModel | GlobalPermissionCheckModel]

    def _is_allowed(
        self,
        role: Role,
        pcheck: PermissionCheckModel | GlobalPermissionCheckModel,
        action_name: str,
    ) -> bool:
        if isinstance(pcheck, PermissionCheckModel):
            if pcheck.action_name == "r":
                return has_permission(
                    db_session=self.db_session,
                    role=role,
                    resource_name=pcheck.resource_name,
                    resource_id=str(pcheck.resource_id),
                    action_name=action_name,
                ) or has_permission(
                    db_session=self.db_session,
                    role=role,
                    resource_name=pcheck.resource_name,
                    resource_id=str(pcheck.resource_id),
                    action_name="rw",
                )
            return has_permission(
                db_session=self.db_session,
                role=role,
                resource_name=pcheck.resource_name,
                resource_id=str(pcheck.resource_id),
                action_name=action_name,
            )
        elif isinstance(pcheck, GlobalPermissionCheckModel):
            if pcheck.action_name == "r":
                return has_global_permission(
                    db_session=self.db_session,
                    role=role,
                    resource_name=pcheck.resource_name,
                    action_name=action_name,
                ) or has_global_permission(
                    db_session=self.db_session,
                    role=role,
                    resource_name=pcheck.resource_name,
                    action_name="rw",
                )
            return has_global_permission(
                db_session=self.db_session,
                role=role,
                resource_name=pcheck.resource_name,
                action_name=action_name,
            )

    def check(
        self,
        either: bool = False, # If True, the function will return True if at least one of the permissions is satisfied. If False, the function will return True only if all permissions are satisfied for at least one role.
        raise_exception: bool = True,
        backwards: bool = False,  # If True, the function will return False if the permissions are satisfied and True if they are not. This can be useful for cases where you want to check if a user does NOT have certain permissions.
        error_message: str = "Not authorized to access this resource",
    ) -> bool:
        if self.bypass_role in [
            role.name for role in self.roles if role.name is not None
        ]:
            return True
        if either:
            for role in self.roles:
                for pcheck in self.pcheck_models:
                    if self._is_allowed(role, pcheck, pcheck.action_name):
                        return True if not backwards else False
            if raise_exception:
                raise HTTPException(401, error_message)
            return False if not backwards else True

        for role in self.roles:
            all_permissions_satisfied = True
            for pcheck in self.pcheck_models:
                if not self._is_allowed(role, pcheck, pcheck.action_name):
                    all_permissions_satisfied = False
                    break
                if not all_permissions_satisfied:
                    break
            if all_permissions_satisfied:
                return True if not backwards else False
        if raise_exception:
            raise HTTPException(401, error_message)
        return False if not backwards else True
