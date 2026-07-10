"""Feature store dataset registry."""

from __future__ import annotations

from threading import RLock

from feature_store.exceptions import DatasetNotFoundError, DatasetRegistrationError
from feature_store.models.feature_dataset import FeatureDataset


class DatasetRegistry:
    """Thread-safe registry for feature datasets."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._datasets: dict[str, FeatureDataset] = {}
        self._versions: dict[str, tuple[str, ...]] = {}

    def register(self, dataset: FeatureDataset) -> None:
        dataset_id = dataset.dataset_id
        if not dataset_id.strip():
            msg = "Dataset id must not be empty"
            raise DatasetRegistrationError(msg)
        with self._lock:
            self._datasets[dataset_id] = dataset
            versions = self._versions.get(dataset_id, ())
            if dataset.version not in versions:
                self._versions[dataset_id] = (*versions, dataset.version)

    def lookup(self, dataset_id: str) -> FeatureDataset:
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

    def list_versions(self, dataset_id: str) -> tuple[str, ...]:
        with self._lock:
            versions = self._versions.get(dataset_id, ())
        if not versions:
            raise DatasetNotFoundError(dataset_id)
        return versions
