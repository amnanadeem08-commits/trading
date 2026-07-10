"""Storage backend contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from historical.datasets.historical_dataset import HistoricalDataset
from historical.storage.repository_record import RepositoryRecord


class StorageBackend(ABC):
    """Abstract storage backend for historical records."""

    @abstractmethod
    def store(self, record: RepositoryRecord) -> None:
        """Persist a repository record."""

    @abstractmethod
    def load(self, dataset_id: str, *, version: str | None = None) -> tuple[RepositoryRecord, ...]:
        """Load records for a dataset."""

    @abstractmethod
    def exists(self, dataset_id: str, *, version: str | None = None) -> bool:
        """Return whether records exist for a dataset."""

    @abstractmethod
    def delete(self, dataset_id: str, *, version: str | None = None) -> None:
        """Delete records for a dataset."""

    @abstractmethod
    def list_datasets(self) -> tuple[str, ...]:
        """List dataset identifiers with stored records."""

    @abstractmethod
    def register_dataset(self, dataset: HistoricalDataset) -> None:
        """Register dataset metadata in storage."""

    @abstractmethod
    def get_dataset(self, dataset_id: str) -> HistoricalDataset:
        """Retrieve dataset metadata from storage."""

    @abstractmethod
    def list_versions(self, dataset_id: str) -> tuple[str, ...]:
        """List stored versions for a dataset."""
