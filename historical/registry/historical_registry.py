"""Historical repository registry."""

from __future__ import annotations

from threading import RLock

from historical.datasets.dataset_registry import DatasetRegistry
from historical.datasets.historical_dataset import HistoricalDataset
from historical.query.query_engine import QueryEngine
from historical.replay.replay_engine import ReplayEngine
from historical.storage.repository import Repository
from historical.validation.validator import HistoricalValidator
from historical.versioning.historical_version import HistoricalVersionRegistry

_default_registry: HistoricalRegistry | None = None
_registry_lock = RLock()


class HistoricalRegistry:
    """Top-level registry coordinating historical repository components."""

    def __init__(
        self,
        *,
        repository: Repository | None = None,
        dataset_registry: DatasetRegistry | None = None,
        version_registry: HistoricalVersionRegistry | None = None,
        validator: HistoricalValidator | None = None,
    ) -> None:
        self._repository = repository or Repository(version_registry=version_registry)
        self._datasets = dataset_registry or DatasetRegistry()
        self._versions = version_registry or self._repository.version_registry
        self._validator = validator or HistoricalValidator()
        self._query = QueryEngine(self._repository)
        self._replay = ReplayEngine(self._repository)
        self._lock = RLock()

    @property
    def repository(self) -> Repository:
        return self._repository

    @property
    def datasets(self) -> DatasetRegistry:
        return self._datasets

    @property
    def versions(self) -> HistoricalVersionRegistry:
        return self._versions

    @property
    def validator(self) -> HistoricalValidator:
        return self._validator

    @property
    def query(self) -> QueryEngine:
        return self._query

    @property
    def replay(self) -> ReplayEngine:
        return self._replay

    def register(self, dataset: HistoricalDataset) -> None:
        """Register a dataset in both repository and dataset registry."""
        with self._lock:
            self._repository.register_dataset(dataset)
            if not self._datasets.exists(dataset.dataset_id):
                self._datasets.register(dataset)

    def resolve(self, dataset_id: str) -> HistoricalDataset:
        """Resolve a dataset from the dataset registry."""
        return self._datasets.resolve(dataset_id)

    def exists(self, dataset_id: str) -> bool:
        return self._datasets.exists(dataset_id) or self._repository.exists(dataset_id)

    def list(self) -> tuple[str, ...]:
        repository_ids = set(self._repository.list())
        registry_ids = set(self._datasets.list())
        return tuple(sorted(repository_ids | registry_ids))


def get_historical_registry() -> HistoricalRegistry:
    global _default_registry
    with _registry_lock:
        if _default_registry is None:
            _default_registry = HistoricalRegistry()
        return _default_registry


def reset_historical_registry() -> None:
    global _default_registry
    with _registry_lock:
        _default_registry = None
