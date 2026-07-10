"""Feature store cache."""

from __future__ import annotations

from threading import RLock

from feature_store.exceptions import DatasetNotFoundError
from feature_store.models.feature_record import FeatureRecord


class FeatureCache:
    """In-memory cache for offline and online feature retrieval."""

    def __init__(self, *, max_entries: int = 1000) -> None:
        self._lock = RLock()
        self._max_entries = max_entries
        self._offline: dict[str, tuple[FeatureRecord, ...]] = {}
        self._online: dict[str, FeatureRecord] = {}

    @property
    def max_entries(self) -> int:
        return self._max_entries

    def cache_offline(self, dataset_id: str, records: tuple[FeatureRecord, ...]) -> None:
        with self._lock:
            self._offline[dataset_id] = records

    def get_offline(self, dataset_id: str) -> tuple[FeatureRecord, ...]:
        with self._lock:
            records = self._offline.get(dataset_id)
        if records is None:
            raise DatasetNotFoundError(dataset_id)
        return records

    def cache_online(self, key: str, record: FeatureRecord) -> None:
        with self._lock:
            if len(self._online) >= self._max_entries and key not in self._online:
                oldest = next(iter(self._online))
                self._online.pop(oldest, None)
            self._online[key] = record

    def get_online(self, key: str) -> FeatureRecord:
        with self._lock:
            record = self._online.get(key)
        if record is None:
            raise DatasetNotFoundError(key)
        return record

    def invalidate(self, dataset_id: str) -> None:
        with self._lock:
            self._offline.pop(dataset_id, None)

    def clear(self) -> None:
        with self._lock:
            self._offline.clear()
            self._online.clear()
