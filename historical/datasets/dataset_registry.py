"""Historical dataset registry."""

from __future__ import annotations

from threading import RLock

from historical.datasets.historical_dataset import HistoricalDataset
from historical.exceptions import DatasetNotFoundError, DatasetRegistrationError

_default_registry: DatasetRegistry | None = None
_registry_lock = RLock()


class DatasetRegistry:
    """Thread-safe registry for historical dataset definitions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._datasets: dict[str, HistoricalDataset] = {}

    def register(self, dataset: HistoricalDataset) -> None:
        """Register a historical dataset definition."""
        dataset_id = dataset.dataset_id
        if not dataset_id.strip():
            msg = "Dataset id must not be empty"
            raise DatasetRegistrationError(msg)
        with self._lock:
            if dataset_id in self._datasets:
                msg = f"Dataset already registered: {dataset_id}"
                raise DatasetRegistrationError(msg)
            self._datasets[dataset_id] = dataset

    def unregister(self, dataset_id: str) -> None:
        """Remove a dataset definition from the registry."""
        with self._lock:
            if dataset_id not in self._datasets:
                raise DatasetNotFoundError(dataset_id)
            del self._datasets[dataset_id]

    def resolve(self, dataset_id: str) -> HistoricalDataset:
        """Resolve a registered dataset by identifier."""
        with self._lock:
            dataset = self._datasets.get(dataset_id)
        if dataset is None:
            raise DatasetNotFoundError(dataset_id)
        return dataset

    def exists(self, dataset_id: str) -> bool:
        with self._lock:
            return dataset_id in self._datasets

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._datasets.keys()))

    def all(self) -> tuple[HistoricalDataset, ...]:
        with self._lock:
            return tuple(self._datasets[dataset_id] for dataset_id in sorted(self._datasets))


def get_dataset_registry() -> DatasetRegistry:
    """Return the process-wide dataset registry singleton."""
    global _default_registry
    with _registry_lock:
        if _default_registry is None:
            _default_registry = DatasetRegistry()
        return _default_registry


def reset_dataset_registry() -> None:
    """Reset the process-wide dataset registry singleton."""
    global _default_registry
    with _registry_lock:
        _default_registry = None
