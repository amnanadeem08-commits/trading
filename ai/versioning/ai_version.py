"""AI versioning."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, VersionInfo
from versioning.prompt_registry import get_prompt_registry


class AIVersion(PlatformModel):
    """Version record for an AI artifact."""

    artifact_id: str = Field(min_length=1)
    version_id: str = Field(min_length=1)
    artifact_type: str = Field(min_length=1, default="agent")
    description: str = ""

    def to_version_info(self) -> VersionInfo:
        """Convert to a platform version info record."""
        return VersionInfo(version_id=self.version_id, description=self.description)

    def register(self, *, set_current: bool = True) -> AIVersion:
        """Register this version in the platform prompt registry."""
        registry = get_prompt_registry()
        registry.register(self.to_version_info(), set_current=set_current)
        return self

    @staticmethod
    def list_versions() -> tuple[VersionInfo, ...]:
        """Return all registered AI artifact versions."""
        return get_prompt_registry().list_versions()
