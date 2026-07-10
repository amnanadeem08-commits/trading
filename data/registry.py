"""Dataset registry."""

from __future__ import annotations

from threading import RLock

from data.dataset import BaseDataset, Dataset
from data.exceptions import DatasetNotFoundError, DatasetRegistrationError
from data.validation import DatasetValidationResult, validate_dataset, validate_dataset_set

_default_registry: DatasetRegistry | None = None
_registry_lock = RLock()


class DatasetRegistry:
    """Thread-safe registry for dataset definitions and types."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._datasets: dict[str, Dataset] = {}
        self._types: dict[str, type[BaseDataset]] = {}

    def register(self, dataset: Dataset) -> None:
        """Register a dataset definition."""
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
        with self._lock:
            if dataset_id not in self._datasets:
                raise DatasetNotFoundError(dataset_id)
            del self._datasets[dataset_id]

    def register_type(self, dataset_type: type[BaseDataset]) -> None:
        """Register a dataset implementation type."""
        instance = dataset_type()
        dataset_id = instance.dataset_id()
        with self._lock:
            self._types[dataset_id] = dataset_type

    def unregister_type(self, dataset_id: str) -> None:
        with self._lock:
            if dataset_id not in self._types:
                raise DatasetNotFoundError(dataset_id)
            del self._types[dataset_id]

    def resolve(self, dataset_id: str) -> Dataset:
        """Resolve a registered dataset by identifier."""
        with self._lock:
            dataset = self._datasets.get(dataset_id)
        if dataset is None:
            raise DatasetNotFoundError(dataset_id)
        return dataset

    def resolve_type(self, dataset_id: str) -> type[BaseDataset]:
        """Resolve a registered dataset type by identifier."""
        with self._lock:
            dataset_type = self._types.get(dataset_id)
        if dataset_type is None:
            raise DatasetNotFoundError(dataset_id)
        return dataset_type

    def exists(self, dataset_id: str) -> bool:
        with self._lock:
            return dataset_id in self._datasets

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._datasets.keys()))

    def list_types(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._types.keys()))

    def validate(self, dataset: Dataset) -> DatasetValidationResult:
        """Validate a single dataset definition."""
        return validate_dataset(dataset)

    def validate_set(self, datasets: tuple[Dataset, ...] | None = None) -> DatasetValidationResult:
        """Validate registered datasets or a provided set."""
        if datasets is None:
            with self._lock:
                datasets = tuple(self._datasets.values())
        return validate_dataset_set(datasets)


def get_dataset_registry() -> DatasetRegistry:
    """Return the process-wide default dataset registry."""
    global _default_registry
    with _registry_lock:
        if _default_registry is None:
            _default_registry = DatasetRegistry()
        return _default_registry


def reset_dataset_registry() -> None:
    """Reset the default dataset registry. Intended for tests."""
    global _default_registry
    with _registry_lock:
        _default_registry = None
