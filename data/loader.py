"""Dataset loading utilities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from data.dataset import BaseDataset, Dataset
from data.exceptions import DatasetLoadError
from data.result import DatasetResult, DatasetStatus
from models.common import utc_now


class DatasetLoader(ABC):
    """Abstract dataset loader."""

    @abstractmethod
    def load(self, dataset: Dataset) -> DatasetResult:
        """Load a dataset definition and return the result."""


class InMemoryDatasetLoader(DatasetLoader):
    """Loads datasets from in-memory implementations."""

    def __init__(self, implementations: dict[str, BaseDataset] | None = None) -> None:
        self._implementations: dict[str, BaseDataset] = dict(implementations or {})

    def register_implementation(self, implementation: BaseDataset) -> None:
        """Register an in-memory dataset implementation."""
        self._implementations[implementation.dataset_id()] = implementation

    def load(self, dataset: Dataset) -> DatasetResult:
        """Load records from a registered implementation."""
        started_at = utc_now()
        implementation = self._implementations.get(dataset.dataset_id)
        if implementation is None:
            msg = f"No in-memory implementation for dataset: {dataset.dataset_id}"
            raise DatasetLoadError(msg, dataset_id=dataset.dataset_id)
        try:
            records = implementation.load()
            transformed = implementation.transform(records)
            return DatasetResult(
                dataset_id=dataset.dataset_id,
                status=DatasetStatus.COMPLETED,
                record_count=len(transformed),
                metrics={"source": "in_memory"},
                started_at=started_at,
                completed_at=utc_now(),
            )
        except Exception as error:
            msg = f"Failed to load dataset '{dataset.dataset_id}': {error}"
            raise DatasetLoadError(msg, dataset_id=dataset.dataset_id) from error

    def load_records(self, dataset_id: str) -> tuple[dict[str, Any], ...]:
        """Load raw records for a dataset identifier."""
        implementation = self._implementations.get(dataset_id)
        if implementation is None:
            msg = f"No in-memory implementation for dataset: {dataset_id}"
            raise DatasetLoadError(msg, dataset_id=dataset_id)
        return implementation.load()
