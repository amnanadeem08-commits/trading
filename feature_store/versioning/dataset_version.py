"""Feature store dataset version registry."""

from __future__ import annotations

from threading import RLock

from pydantic import Field

from feature_store.exceptions import DatasetNotFoundError, FeatureVersionError
from models.common import PlatformModel, UTCDateTime, utc_now


class DatasetVersion(PlatformModel):
    """Version metadata for a feature store dataset."""

    dataset_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = ""
    snapshot_id: str = Field(min_length=1)
    record_count: int = Field(ge=0, default=0)
    checksum: str = ""
    created_at: UTCDateTime = Field(default_factory=utc_now)
    immutable: bool = True


class DatasetVersionRegistry:
    """Thread-safe registry for feature dataset versions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._versions: dict[str, tuple[DatasetVersion, ...]] = {}

    def register(self, version: DatasetVersion) -> None:
        with self._lock:
            existing = self._versions.get(version.dataset_id, ())
            if any(item.version == version.version for item in existing):
                return
            self._versions[version.dataset_id] = (*existing, version)

    def list_versions(self, dataset_id: str) -> tuple[DatasetVersion, ...]:
        with self._lock:
            versions = self._versions.get(dataset_id, ())
        if not versions:
            raise DatasetNotFoundError(dataset_id)
        return versions

    def latest(self, dataset_id: str) -> DatasetVersion:
        versions = self.list_versions(dataset_id)
        return versions[-1]

    def snapshot(self, snapshot_id: str) -> DatasetVersion:
        with self._lock:
            for versions in self._versions.values():
                for version in versions:
                    if version.snapshot_id == snapshot_id:
                        return version
        msg = f"Snapshot not found: {snapshot_id}"
        raise FeatureVersionError(msg)

    def list_datasets(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._versions.keys()))
