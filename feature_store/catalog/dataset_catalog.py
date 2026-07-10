"""Dataset catalog contracts."""

from __future__ import annotations

from threading import RLock

from pydantic import Field

from feature_store.exceptions import DatasetNotFoundError
from models.common import PlatformModel, UTCDateTime, utc_now


class DatasetCatalogEntry(PlatformModel):
    """Catalog entry for a registered feature dataset."""

    dataset_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    schema_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    capabilities: tuple[str, ...] = Field(default_factory=tuple)
    tags: tuple[str, ...] = Field(default_factory=tuple)
    lineage: tuple[str, ...] = Field(default_factory=tuple)
    attributes: dict[str, str] = Field(default_factory=dict)
    created_at: UTCDateTime = Field(default_factory=utc_now)


class DatasetCatalog:
    """Thread-safe catalog for feature datasets."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._entries: dict[str, DatasetCatalogEntry] = {}

    def register(self, entry: DatasetCatalogEntry) -> None:
        with self._lock:
            self._entries[entry.dataset_id] = entry

    def lookup(self, dataset_id: str) -> DatasetCatalogEntry:
        with self._lock:
            entry = self._entries.get(dataset_id)
        if entry is None:
            raise DatasetNotFoundError(dataset_id)
        return entry

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._entries.keys()))

    def capabilities(self, dataset_id: str) -> tuple[str, ...]:
        return self.lookup(dataset_id).capabilities
