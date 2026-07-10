"""Historical version registry."""

from __future__ import annotations

from threading import RLock

from pydantic import Field

from historical.datasets.dataset_version import DatasetVersion
from historical.exceptions import DatasetNotFoundError, VersionError
from models.common import PlatformModel, UTCDateTime, utc_now


class HistoricalVersionSnapshot(PlatformModel):
    """Immutable snapshot metadata for rollback."""

    snapshot_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    checksum: str = ""
    created_at: UTCDateTime = Field(default_factory=utc_now)
    rollback_target: str | None = None


class HistoricalVersionRegistry:
    """Thread-safe registry for dataset versions and snapshots."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._versions: dict[str, tuple[DatasetVersion, ...]] = {}
        self._snapshots: dict[str, HistoricalVersionSnapshot] = {}

    def register(self, version: DatasetVersion) -> None:
        with self._lock:
            existing = self._versions.get(version.dataset_id, ())
            if any(item.version == version.version for item in existing):
                return
            self._versions[version.dataset_id] = (*existing, version)
            self._snapshots[version.snapshot_id] = HistoricalVersionSnapshot(
                snapshot_id=version.snapshot_id,
                dataset_id=version.dataset_id,
                version=version.version,
                checksum=version.checksum,
            )

    def list_versions(self, dataset_id: str) -> tuple[DatasetVersion, ...]:
        with self._lock:
            versions = self._versions.get(dataset_id, ())
        if not versions:
            raise DatasetNotFoundError(dataset_id)
        return versions

    def latest(self, dataset_id: str) -> DatasetVersion:
        versions = self.list_versions(dataset_id)
        return versions[-1]

    def snapshot(self, snapshot_id: str) -> HistoricalVersionSnapshot:
        with self._lock:
            snapshot = self._snapshots.get(snapshot_id)
        if snapshot is None:
            msg = f"Snapshot not found: {snapshot_id}"
            raise VersionError(msg)
        return snapshot

    def rollback_metadata(
        self, dataset_id: str, *, target_version: str
    ) -> HistoricalVersionSnapshot:
        """Return rollback metadata without mutating stored versions."""
        versions = self.list_versions(dataset_id)
        if not any(item.version == target_version for item in versions):
            msg = f"Rollback target not found: {target_version}"
            raise VersionError(msg)
        return HistoricalVersionSnapshot(
            snapshot_id=f"rollback-{dataset_id}-{target_version}",
            dataset_id=dataset_id,
            version=target_version,
            rollback_target=target_version,
            created_at=utc_now(),
        )

    def list_datasets(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._versions.keys()))
