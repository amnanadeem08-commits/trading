"""Feature version registry."""

from __future__ import annotations

from threading import RLock

from pydantic import Field

from feature_engineering.exceptions import FeatureNotFoundError, FeatureVersionError
from models.common import PlatformModel, UTCDateTime, utc_now


class FeatureVersion(PlatformModel):
    """Version metadata for a feature definition."""

    feature_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    schema_id: str = Field(min_length=1)
    description: str = ""
    snapshot_id: str = Field(min_length=1)
    created_at: UTCDateTime = Field(default_factory=utc_now)
    immutable: bool = True


class FeatureVersionRegistry:
    """Thread-safe registry for feature versions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._versions: dict[str, tuple[FeatureVersion, ...]] = {}

    def register(self, version: FeatureVersion) -> None:
        with self._lock:
            existing = self._versions.get(version.feature_id, ())
            if any(item.version == version.version for item in existing):
                return
            self._versions[version.feature_id] = (*existing, version)

    def list_versions(self, feature_id: str) -> tuple[FeatureVersion, ...]:
        with self._lock:
            versions = self._versions.get(feature_id, ())
        if not versions:
            raise FeatureNotFoundError(feature_id)
        return versions

    def latest(self, feature_id: str) -> FeatureVersion:
        versions = self.list_versions(feature_id)
        return versions[-1]

    def snapshot(self, snapshot_id: str) -> FeatureVersion:
        with self._lock:
            for versions in self._versions.values():
                for version in versions:
                    if version.snapshot_id == snapshot_id:
                        return version
        msg = f"Snapshot not found: {snapshot_id}"
        raise FeatureVersionError(msg)

    def list_features(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._versions.keys()))
