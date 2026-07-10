"""Dataset persistence store."""

from __future__ import annotations

from abc import ABC, abstractmethod
from threading import RLock

from data.dataset import Dataset
from data.exceptions import DatasetNotFoundError, DatasetPersistenceError


class DatasetPersistenceStore(ABC):
    """Abstract persistence store for dataset definitions."""

    @abstractmethod
    def save(self, dataset: Dataset) -> None:
        """Persist a dataset definition."""

    @abstractmethod
    def load(self, dataset_id: str) -> Dataset:
        """Load a dataset definition by identifier."""

    @abstractmethod
    def delete(self, dataset_id: str) -> None:
        """Delete a persisted dataset definition."""

    @abstractmethod
    def list(self) -> tuple[str, ...]:
        """List persisted dataset identifiers."""


class InMemoryDatasetPersistenceStore(DatasetPersistenceStore):
    """In-memory dataset persistence store."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._datasets: dict[str, Dataset] = {}

    def save(self, dataset: Dataset) -> None:
        if not dataset.dataset_id.strip():
            msg = "Dataset id must not be empty"
            raise DatasetPersistenceError(msg)
        with self._lock:
            self._datasets[dataset.dataset_id] = dataset

    def load(self, dataset_id: str) -> Dataset:
        with self._lock:
            dataset = self._datasets.get(dataset_id)
        if dataset is None:
            raise DatasetNotFoundError(dataset_id)
        return dataset

    def delete(self, dataset_id: str) -> None:
        with self._lock:
            if dataset_id not in self._datasets:
                raise DatasetNotFoundError(dataset_id)
            del self._datasets[dataset_id]

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._datasets.keys()))
