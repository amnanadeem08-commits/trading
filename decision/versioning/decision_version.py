"""Decision versioning."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, VersionInfo
from versioning.schema_registry import get_schema_registry


class DecisionVersion(PlatformModel):
    """Version record for a decision artifact."""

    decision_id: str = Field(min_length=1)
    version_id: str = Field(min_length=1)
    artifact_type: str = Field(min_length=1, default="policy")
    description: str = ""

    def to_version_info(self) -> VersionInfo:
        """Convert to a platform version info record."""
        return VersionInfo(version_id=self.version_id, description=self.description)

    def register(self, *, set_current: bool = True) -> DecisionVersion:
        """Register this version in the platform schema registry."""
        registry = get_schema_registry()
        registry.register(self.to_version_info(), set_current=set_current)
        return self

    @staticmethod
    def list_versions() -> tuple[VersionInfo, ...]:
        """Return all registered decision artifact versions."""
        return get_schema_registry().list_versions()
