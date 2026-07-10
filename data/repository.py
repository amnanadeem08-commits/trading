"""Dataset repository."""

from __future__ import annotations

from abc import ABC, abstractmethod
from threading import RLock

from data.dataset import Dataset
from data.exceptions import DatasetNotFoundError


class DatasetRepository(ABC):
    """Abstract repository for dataset definitions."""

    @abstractmethod
    def add(self, dataset: Dataset) -> None:
        """Add a dataset to the repository."""

    @abstractmethod
    def get(self, dataset_id: str) -> Dataset:
        """Retrieve a dataset by identifier."""

    @abstractmethod
    def remove(self, dataset_id: str) -> None:
        """Remove a dataset from the repository."""

    @abstractmethod
    def list(self) -> tuple[str, ...]:
        """List dataset identifiers in the repository."""


class InMemoryDatasetRepository(DatasetRepository):
    """Thread-safe in-memory dataset repository."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._datasets: dict[str, Dataset] = {}

    def add(self, dataset: Dataset) -> None:
        with self._lock:
            self._datasets[dataset.dataset_id] = dataset

    def get(self, dataset_id: str) -> Dataset:
        with self._lock:
            dataset = self._datasets.get(dataset_id)
        if dataset is None:
            raise DatasetNotFoundError(dataset_id)
        return dataset

    def remove(self, dataset_id: str) -> None:
        with self._lock:
            if dataset_id not in self._datasets:
                raise DatasetNotFoundError(dataset_id)
            del self._datasets[dataset_id]

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._datasets.keys()))

    def all(self) -> tuple[Dataset, ...]:
        """Return all datasets in the repository."""
        with self._lock:
            return tuple(self._datasets[dataset_id] for dataset_id in sorted(self._datasets))
