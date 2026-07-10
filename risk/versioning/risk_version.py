"""Risk versioning."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, VersionInfo
from versioning.connector_registry import get_connector_version_registry


class RiskVersion(PlatformModel):
    """Version record for a risk artifact."""

    risk_id: str = Field(min_length=1)
    version_id: str = Field(min_length=1)
    artifact_type: str = Field(min_length=1, default="policy")
    description: str = ""

    def to_version_info(self) -> VersionInfo:
        """Convert to a platform version info record."""
        return VersionInfo(version_id=self.version_id, description=self.description)

    def register(self, *, set_current: bool = True) -> RiskVersion:
        """Register this version in the platform connector version registry."""
        registry = get_connector_version_registry()
        registry.register(self.to_version_info(), set_current=set_current)
        return self

    @staticmethod
    def list_versions() -> tuple[VersionInfo, ...]:
        """Return all registered risk artifact versions."""
        return get_connector_version_registry().list_versions()
