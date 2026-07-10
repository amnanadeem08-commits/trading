"""Plugin manifest contract."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel
from plugins.capability import Capability
from plugins.dependency import PluginDependency
from plugins.sandbox import PermissionModel


class PlatformVersionConstraint(PlatformModel):
    """Platform version compatibility bounds."""

    minimum: str = Field(min_length=1)
    maximum: str | None = None


class ApiVersionConstraint(PlatformModel):
    """API version compatibility bounds."""

    minimum_api_version: str = Field(min_length=1)
    maximum_api_version: str | None = None


class PluginManifest(PlatformModel):
    """Declarative plugin manifest."""

    api_version: str = Field(min_length=1)
    api_version_bounds: ApiVersionConstraint
    platform_version: PlatformVersionConstraint
    dependencies: tuple[PluginDependency, ...] = Field(default_factory=tuple)
    permissions: PermissionModel = Field(default_factory=PermissionModel)
    capabilities: tuple[Capability, ...] = Field(default_factory=tuple)
