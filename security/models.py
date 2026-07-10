"""Security RBAC and identity models."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel


class PermissionAction(StrEnum):
    """Canonical permission actions."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class Permission(PlatformModel):
    """Permission granted to a role."""

    resource: str = Field(min_length=1)
    action: PermissionAction


class Role(PlatformModel):
    """Role with assigned permissions."""

    role_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    permissions: tuple[Permission, ...] = Field(default_factory=tuple)


class Identity(PlatformModel):
    """Authenticated identity."""

    identity_id: str = Field(min_length=1)
    roles: tuple[str, ...] = Field(default_factory=tuple)
    attributes: dict[str, str] = Field(default_factory=dict)

    def has_role(self, role_id: str) -> bool:
        return role_id in self.roles
