"""Model version tracking."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, VersionInfo
from versioning.model_registry import get_model_registry


class ModelVersion(PlatformModel):
    """Version record for an ML model."""

    model_id: str = Field(min_length=1)
    version_id: str = Field(min_length=1)
    description: str = ""

    def to_version_info(self) -> VersionInfo:
        """Convert to a platform version info record."""
        return VersionInfo(version_id=self.version_id, description=self.description)

    def register(self, *, set_current: bool = True) -> ModelVersion:
        """Register this version in the platform model registry."""
        registry = get_model_registry()
        registry.register(self.to_version_info(), set_current=set_current)
        return self

    @staticmethod
    def current(model_id: str) -> VersionInfo | None:
        """Return the current version for a model identifier."""
        _ = model_id
        return get_model_registry().current()

    @staticmethod
    def list_versions() -> tuple[VersionInfo, ...]:
        """Return all registered model versions."""
        return get_model_registry().list_versions()
