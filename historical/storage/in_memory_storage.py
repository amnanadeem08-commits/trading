"""In-memory storage backend."""

from __future__ import annotations

from threading import RLock

from historical.datasets.historical_dataset import HistoricalDataset
from historical.exceptions import DatasetNotFoundError, StorageError
from historical.storage.repository_record import RepositoryRecord
from historical.storage.storage_backend import StorageBackend


class InMemoryStorage(StorageBackend):
    """Thread-safe in-memory storage backend."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._datasets: dict[str, HistoricalDataset] = {}
        self._records: dict[str, dict[str, list[RepositoryRecord]]] = {}

    def register_dataset(self, dataset: HistoricalDataset) -> None:
        with self._lock:
            self._datasets[dataset.dataset_id] = dataset
            self._records.setdefault(dataset.dataset_id, {})

    def get_dataset(self, dataset_id: str) -> HistoricalDataset:
        with self._lock:
            dataset = self._datasets.get(dataset_id)
        if dataset is None:
            raise DatasetNotFoundError(dataset_id)
        return dataset

    def store(self, record: RepositoryRecord) -> None:
        with self._lock:
            if record.dataset_id not in self._datasets:
                raise DatasetNotFoundError(record.dataset_id)
            versions = self._records.setdefault(record.dataset_id, {})
            bucket = versions.setdefault(record.version, [])
            if any(item.record_id == record.record_id for item in bucket):
                msg = f"Duplicate record id: {record.record_id}"
                raise StorageError(msg)
            bucket.append(record)
            bucket.sort(key=lambda item: (item.sequence, item.timestamp))

    def load(self, dataset_id: str, *, version: str | None = None) -> tuple[RepositoryRecord, ...]:
        with self._lock:
            versions = self._records.get(dataset_id)
            if versions is None:
                raise DatasetNotFoundError(dataset_id)
            if version is None:
                if not versions:
                    return ()
                latest_version = sorted(versions.keys())[-1]
                records = versions[latest_version]
            else:
                records = versions.get(version, [])
        return tuple(records)

    def exists(self, dataset_id: str, *, version: str | None = None) -> bool:
        with self._lock:
            versions = self._records.get(dataset_id)
            if versions is None:
                return False
            if version is None:
                return any(len(bucket) > 0 for bucket in versions.values())
            return len(versions.get(version, [])) > 0

    def delete(self, dataset_id: str, *, version: str | None = None) -> None:
        with self._lock:
            if dataset_id not in self._records:
                raise DatasetNotFoundError(dataset_id)
            if version is None:
                del self._records[dataset_id]
                self._datasets.pop(dataset_id, None)
            else:
                versions = self._records[dataset_id]
                if version not in versions:
                    raise DatasetNotFoundError(dataset_id)
                del versions[version]

    def list_datasets(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._datasets.keys()))

    def list_versions(self, dataset_id: str) -> tuple[str, ...]:
        with self._lock:
            versions = self._records.get(dataset_id)
            if versions is None:
                raise DatasetNotFoundError(dataset_id)
            return tuple(sorted(versions.keys()))
