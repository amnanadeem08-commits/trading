"""Dataset version registry."""

from __future__ import annotations

from threading import RLock

from pydantic import Field

from data.exceptions import DatasetNotFoundError
from models.common import PlatformModel, UTCDateTime, utc_now


class DatasetVersion(PlatformModel):
    """Version metadata for a dataset."""

    dataset_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = ""
    created_at: UTCDateTime = Field(default_factory=utc_now)


class DatasetVersionRegistry:
    """Thread-safe registry for dataset versions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._versions: dict[str, tuple[DatasetVersion, ...]] = {}

    def register(self, version: DatasetVersion) -> None:
        """Register a dataset version."""
        with self._lock:
            existing = self._versions.get(version.dataset_id, ())
            if any(item.version == version.version for item in existing):
                return
            self._versions[version.dataset_id] = (*existing, version)

    def list_versions(self, dataset_id: str) -> tuple[DatasetVersion, ...]:
        """List versions for a dataset."""
        with self._lock:
            versions = self._versions.get(dataset_id, ())
        if not versions:
            raise DatasetNotFoundError(dataset_id)
        return versions

    def latest(self, dataset_id: str) -> DatasetVersion:
        """Return the latest version for a dataset."""
        versions = self.list_versions(dataset_id)
        return versions[-1]

    def list_datasets(self) -> tuple[str, ...]:
        """List dataset identifiers with registered versions."""
        with self._lock:
            return tuple(sorted(self._versions.keys()))
