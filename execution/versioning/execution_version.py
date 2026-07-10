"""Execution versioning."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, VersionInfo
from versioning.strategy_registry import get_strategy_registry


class ExecutionVersion(PlatformModel):
    """Version record for an execution artifact."""

    execution_id: str = Field(min_length=1)
    version_id: str = Field(min_length=1)
    artifact_type: str = Field(min_length=1, default="contract")
    description: str = ""

    def to_version_info(self) -> VersionInfo:
        """Convert to a platform version info record."""
        return VersionInfo(version_id=self.version_id, description=self.description)

    def register(self, *, set_current: bool = True) -> ExecutionVersion:
        """Register this version in the platform artifact registry."""
        registry = get_strategy_registry()
        registry.register(self.to_version_info(), set_current=set_current)
        return self

    def is_compatible(self, *, version_id: str | None = None) -> bool:
        """Return whether this version is compatible with the platform registry."""
        registry = get_strategy_registry()
        versions = registry.list_versions()
        if not versions:
            return True
        if version_id is not None:
            return registry.exists(version_id)
        current = registry.current()
        return current is not None

    @staticmethod
    def list_versions() -> tuple[VersionInfo, ...]:
        """Return all registered execution artifact versions."""
        return get_strategy_registry().list_versions()
