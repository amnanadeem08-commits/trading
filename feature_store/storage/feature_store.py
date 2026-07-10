"""Feature store facade."""

from __future__ import annotations

from threading import RLock

from feature_store.catalog.dataset_catalog import DatasetCatalog, DatasetCatalogEntry
from feature_store.exceptions import DatasetNotFoundError, DatasetRegistrationError
from feature_store.models.feature_dataset import FeatureDataset
from feature_store.models.feature_metadata import FeatureMetadata
from feature_store.models.feature_record import FeatureRecord
from feature_store.models.feature_snapshot import FeatureSnapshot
from feature_store.registry.dataset_registry import DatasetRegistry
from feature_store.registry.feature_registry import FeatureRegistry
from feature_store.storage.feature_cache import FeatureCache
from feature_store.storage.feature_repository import FeatureRepository
from feature_store.validation.validation_result import ValidationResult
from feature_store.validation.validator import FeatureStoreValidator
from feature_store.versioning.dataset_version import DatasetVersion, DatasetVersionRegistry


class FeatureStore:
    """Central repository for reusable feature datasets."""

    def __init__(
        self,
        *,
        repository: FeatureRepository | None = None,
        cache: FeatureCache | None = None,
        dataset_registry: DatasetRegistry | None = None,
        feature_registry: FeatureRegistry | None = None,
        catalog: DatasetCatalog | None = None,
        version_registry: DatasetVersionRegistry | None = None,
        validator: FeatureStoreValidator | None = None,
    ) -> None:
        self._repository = repository or FeatureRepository()
        self._cache = cache or FeatureCache()
        self._dataset_registry = dataset_registry or DatasetRegistry()
        self._feature_registry = feature_registry or FeatureRegistry()
        self._catalog = catalog or DatasetCatalog()
        self._versions = version_registry or DatasetVersionRegistry()
        self._validator = validator or FeatureStoreValidator()
        self._lock = RLock()

    @property
    def repository(self) -> FeatureRepository:
        return self._repository

    @property
    def cache(self) -> FeatureCache:
        return self._cache

    @property
    def dataset_registry(self) -> DatasetRegistry:
        return self._dataset_registry

    @property
    def feature_registry(self) -> FeatureRegistry:
        return self._feature_registry

    @property
    def catalog(self) -> DatasetCatalog:
        return self._catalog

    @property
    def version_registry(self) -> DatasetVersionRegistry:
        return self._versions

    @property
    def validator(self) -> FeatureStoreValidator:
        return self._validator

    def register_dataset(self, dataset: FeatureDataset) -> None:
        if not dataset.dataset_id.strip():
            msg = "Dataset id must not be empty"
            raise DatasetRegistrationError(msg)
        with self._lock:
            self._repository.register_dataset(dataset)
            self._dataset_registry.register(dataset)
            self._catalog.register(
                DatasetCatalogEntry(
                    dataset_id=dataset.dataset_id,
                    name=dataset.metadata.name,
                    version=dataset.version,
                    schema_id=dataset.metadata.schema_id,
                    symbol_id=dataset.metadata.symbol_id,
                    capabilities=("offline", "online", "snapshot"),
                    tags=dataset.tags,
                    lineage=dataset.lineage,
                )
            )
            self._versions.register(
                DatasetVersion(
                    dataset_id=dataset.dataset_id,
                    version=dataset.version,
                    description=dataset.metadata.name,
                    snapshot_id=f"snapshot-{dataset.dataset_id}-{dataset.version}",
                    record_count=dataset.record_count,
                    checksum=dataset.checksum,
                )
            )

    def ingest_records(self, records: tuple[FeatureRecord, ...]) -> None:
        with self._lock:
            self._repository.store_many(records)
            if records:
                dataset_id = records[0].dataset_id
                loaded = self._repository.load(dataset_id)
                self._cache.cache_offline(dataset_id, loaded)

    def load_offline(self, dataset_id: str) -> tuple[FeatureRecord, ...]:
        try:
            return self._cache.get_offline(dataset_id)
        except DatasetNotFoundError:
            records = self._repository.load(dataset_id)
            self._cache.cache_offline(dataset_id, records)
            return records

    def get_online(self, key: str) -> FeatureRecord:
        return self._cache.get_online(key)

    def put_online(self, key: str, record: FeatureRecord) -> None:
        self._cache.cache_online(key, record)

    def lookup_feature(self, record_id: str, *, dataset_id: str) -> FeatureRecord:
        return self._repository.lookup(record_id, dataset_id=dataset_id)

    def create_snapshot(self, dataset_id: str) -> FeatureSnapshot:
        return self._repository.create_snapshot(dataset_id)

    def get_snapshot(self, snapshot_id: str) -> FeatureSnapshot:
        return self._repository.get_snapshot(snapshot_id)

    def validate_dataset(self, dataset_id: str) -> ValidationResult:
        dataset = self._repository.get_dataset(dataset_id)
        records = self._repository.load(dataset_id)
        return self._validator.validate_dataset(dataset, records=records)

    def metadata(self, dataset_id: str) -> FeatureMetadata:
        return self._repository.get_dataset(dataset_id).metadata

    def version(self, dataset_id: str) -> str:
        return self._repository.get_dataset(dataset_id).version

    def list_datasets(self) -> tuple[str, ...]:
        return self._repository.list_datasets()

    def exists(self, dataset_id: str) -> bool:
        return self._repository.exists(dataset_id)
