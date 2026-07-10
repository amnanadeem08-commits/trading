"""Plugin sandbox interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import Field

from models.common import PlatformModel


class ResourceLimits(PlatformModel):
    """Resource limit policy for plugin execution."""

    max_memory_mb: int | None = Field(default=None, ge=1)
    max_cpu_percent: float | None = Field(default=None, gt=0.0, le=100.0)


class PermissionModel(PlatformModel):
    """Permission grants requested by a plugin."""

    permissions: tuple[str, ...] = Field(default_factory=tuple)


class FilesystemAccessPolicy(PlatformModel):
    """Filesystem access policy for plugin execution."""

    allowed_paths: tuple[str, ...] = Field(default_factory=tuple)
    read_only: bool = True


class NetworkAccessPolicy(PlatformModel):
    """Network access policy for plugin execution."""

    allowed_hosts: tuple[str, ...] = Field(default_factory=tuple)
    outbound_only: bool = True


class EnvironmentAccessPolicy(PlatformModel):
    """Environment variable access policy."""

    allowed_variables: tuple[str, ...] = Field(default_factory=tuple)
    read_only: bool = True


class SecretsAccessPolicy(PlatformModel):
    """Secrets access policy."""

    allowed_secret_keys: tuple[str, ...] = Field(default_factory=tuple)
    read_only: bool = True


class PluginSandbox(ABC):
    """Sandbox policy interface. No isolation implementation."""

    @property
    @abstractmethod
    def resource_limits(self) -> ResourceLimits:
        """Return configured resource limits."""

    @property
    @abstractmethod
    def permissions(self) -> PermissionModel:
        """Return configured permissions."""

    @property
    @abstractmethod
    def filesystem_policy(self) -> FilesystemAccessPolicy:
        """Return filesystem access policy."""

    @property
    @abstractmethod
    def network_policy(self) -> NetworkAccessPolicy:
        """Return network access policy."""

    @property
    @abstractmethod
    def environment_policy(self) -> EnvironmentAccessPolicy:
        """Return environment variable access policy."""

    @property
    @abstractmethod
    def secrets_policy(self) -> SecretsAccessPolicy:
        """Return secrets access policy."""


class DefaultPluginSandbox(PluginSandbox):
    """Default sandbox policy derived from a plugin manifest."""

    def __init__(
        self,
        *,
        permissions: PermissionModel,
        resource_limits: ResourceLimits | None = None,
        filesystem_policy: FilesystemAccessPolicy | None = None,
        network_policy: NetworkAccessPolicy | None = None,
        environment_policy: EnvironmentAccessPolicy | None = None,
        secrets_policy: SecretsAccessPolicy | None = None,
    ) -> None:
        self._permissions = permissions
        self._resource_limits = resource_limits or ResourceLimits()
        self._filesystem_policy = filesystem_policy or FilesystemAccessPolicy()
        self._network_policy = network_policy or NetworkAccessPolicy()
        self._environment_policy = environment_policy or EnvironmentAccessPolicy()
        self._secrets_policy = secrets_policy or SecretsAccessPolicy()

    @property
    def resource_limits(self) -> ResourceLimits:
        return self._resource_limits

    @property
    def permissions(self) -> PermissionModel:
        return self._permissions

    @property
    def filesystem_policy(self) -> FilesystemAccessPolicy:
        return self._filesystem_policy

    @property
    def network_policy(self) -> NetworkAccessPolicy:
        return self._network_policy

    @property
    def environment_policy(self) -> EnvironmentAccessPolicy:
        return self._environment_policy

    @property
    def secrets_policy(self) -> SecretsAccessPolicy:
        return self._secrets_policy
