"""Historical data repository."""

from __future__ import annotations

from threading import RLock

from historical.datasets.dataset_metadata import HistoricalDatasetMetadata
from historical.datasets.dataset_version import DatasetVersion
from historical.datasets.historical_dataset import HistoricalDataset, compute_dataset_checksum
from historical.exceptions import DatasetRegistrationError
from historical.storage.in_memory_storage import InMemoryStorage
from historical.storage.repository_record import RepositoryRecord
from historical.storage.storage_backend import StorageBackend
from historical.versioning.historical_version import HistoricalVersionRegistry


class Repository:
    """Coordinates dataset registration and record storage."""

    def __init__(
        self,
        *,
        storage: StorageBackend | None = None,
        version_registry: HistoricalVersionRegistry | None = None,
    ) -> None:
        self._storage = storage or InMemoryStorage()
        self._versions = version_registry or HistoricalVersionRegistry()
        self._lock = RLock()

    @property
    def storage(self) -> StorageBackend:
        return self._storage

    @property
    def version_registry(self) -> HistoricalVersionRegistry:
        return self._versions

    def register_dataset(self, dataset: HistoricalDataset) -> None:
        """Register dataset metadata and version snapshot."""
        if not dataset.dataset_id.strip():
            msg = "Dataset id must not be empty"
            raise DatasetRegistrationError(msg)
        with self._lock:
            self._storage.register_dataset(dataset)
            self._versions.register(
                DatasetVersion(
                    dataset_id=dataset.dataset_id,
                    version=dataset.version,
                    description=dataset.metadata.description,
                    snapshot_id=f"snapshot-{dataset.dataset_id}-{dataset.version}",
                    record_count=dataset.record_count,
                    checksum=dataset.checksum,
                )
            )

    def store(self, record: RepositoryRecord) -> None:
        """Store a repository record."""
        with self._lock:
            self._storage.store(record)
            records = self._storage.load(record.dataset_id, version=record.version)
            dataset = self._storage.get_dataset(record.dataset_id)
            checksum = compute_dataset_checksum(
                tuple(item.payload for item in records),
            )
            start = records[0].timestamp if records else None
            end = records[-1].timestamp if records else None
            updated = (
                dataset.with_record_count(len(records))
                .with_checksum(checksum)
                .with_time_range(
                    start=start,
                    end=end,
                )
            )
            self._storage.register_dataset(updated)

    def load(self, dataset_id: str, *, version: str | None = None) -> tuple[RepositoryRecord, ...]:
        """Load records for a dataset."""
        return self._storage.load(dataset_id, version=version)

    def exists(self, dataset_id: str, *, version: str | None = None) -> bool:
        """Return whether dataset records exist."""
        return self._storage.exists(dataset_id, version=version)

    def delete(self, dataset_id: str, *, version: str | None = None) -> None:
        """Delete dataset records."""
        with self._lock:
            self._storage.delete(dataset_id, version=version)

    def list(self) -> tuple[str, ...]:
        """List dataset identifiers."""
        return self._storage.list_datasets()

    def version(self, dataset_id: str) -> DatasetVersion:
        """Return the latest version metadata for a dataset."""
        return self._versions.latest(dataset_id)

    def metadata(self, dataset_id: str) -> HistoricalDatasetMetadata:
        """Return dataset metadata."""
        dataset = self._storage.get_dataset(dataset_id)
        return dataset.metadata

    def get_dataset(self, dataset_id: str) -> HistoricalDataset:
        """Return the registered dataset definition."""
        return self._storage.get_dataset(dataset_id)

    def create_dataset(
        self,
        *,
        dataset_id: str,
        version: str,
        name: str,
        source: str = "internal",
        tags: tuple[str, ...] = (),
        fields: tuple[str, ...] = ("timestamp", "value"),
    ) -> HistoricalDataset:
        """Create and register a new historical dataset."""
        from historical.datasets.historical_dataset import HistoricalDatasetSchema

        metadata = HistoricalDatasetMetadata(
            dataset_id=dataset_id,
            name=name,
            source=source,
            tags=tags,
        )
        dataset = HistoricalDataset(
            dataset_id=dataset_id,
            version=version,
            metadata=metadata,
            source=source,
            tags=tags,
            dataset_schema=HistoricalDatasetSchema(
                fields=fields,
                required_fields=fields,
                timestamp_field="timestamp",
            ),
        )
        self.register_dataset(dataset)
        return dataset
