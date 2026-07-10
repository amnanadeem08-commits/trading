"""Market data version registry."""

from __future__ import annotations

from threading import RLock

from pydantic import Field

from market_data.exceptions import MarketRecordNotFoundError, MarketVersionError
from models.common import PlatformModel, UTCDateTime, utc_now


class MarketVersion(PlatformModel):
    """Version metadata for a market dataset."""

    dataset_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = ""
    snapshot_id: str = Field(min_length=1)
    created_at: UTCDateTime = Field(default_factory=utc_now)
    immutable: bool = True


class MarketVersionRegistry:
    """Thread-safe registry for market dataset versions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._versions: dict[str, tuple[MarketVersion, ...]] = {}

    def register(self, version: MarketVersion) -> None:
        with self._lock:
            existing = self._versions.get(version.dataset_id, ())
            if any(item.version == version.version for item in existing):
                return
            self._versions[version.dataset_id] = (*existing, version)

    def list_versions(self, dataset_id: str) -> tuple[MarketVersion, ...]:
        with self._lock:
            versions = self._versions.get(dataset_id, ())
        if not versions:
            raise MarketRecordNotFoundError(dataset_id)
        return versions

    def latest(self, dataset_id: str) -> MarketVersion:
        versions = self.list_versions(dataset_id)
        return versions[-1]

    def snapshot(self, snapshot_id: str) -> MarketVersion:
        with self._lock:
            for versions in self._versions.values():
                for version in versions:
                    if version.snapshot_id == snapshot_id:
                        return version
        msg = f"Snapshot not found: {snapshot_id}"
        raise MarketVersionError(msg)

    def list_datasets(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._versions.keys()))
