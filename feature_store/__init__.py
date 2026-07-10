"""Feature store public API."""

from feature_store.catalog.dataset_catalog import DatasetCatalog, DatasetCatalogEntry
from feature_store.exceptions import (
    DatasetNotFoundError,
    DatasetRegistrationError,
    FeatureRecordNotFoundError,
    FeatureStoreError,
    FeatureStoreValidationError,
    FeatureVersionError,
    SnapshotNotFoundError,
)
from feature_store.integration.feature_engineering_bridge import (
    build_reproducible_dataset,
    dataset_from_feature_set,
    ingest_feature_set,
    record_from_vector,
    records_from_feature_set,
    register_features_from_set,
)
from feature_store.lifecycle.feature_store_lifecycle import (
    DatasetCreatedEvent,
    DatasetUpdatedEvent,
    DatasetValidatedEvent,
    FeatureStoreLifecycleEvent,
    FeatureStoreLifecycleEventType,
    FeatureStoreLifecycleManager,
    SnapshotCreatedEvent,
)
from feature_store.models.feature_dataset import FeatureDataset, compute_feature_dataset_hash
from feature_store.models.feature_metadata import FeatureMetadata
from feature_store.models.feature_record import FeatureRecord
from feature_store.models.feature_snapshot import FeatureSnapshot
from feature_store.registry.dataset_registry import DatasetRegistry
from feature_store.registry.feature_registry import (
    FeatureRegistry,
    FeatureRegistryEntry,
    get_feature_store_registry,
    reset_feature_store_registry,
)
from feature_store.storage.feature_cache import FeatureCache
from feature_store.storage.feature_repository import FeatureRepository
from feature_store.storage.feature_store import FeatureStore
from feature_store.validation.validation_result import ValidationResult
from feature_store.validation.validator import FeatureStoreValidator
from feature_store.versioning.dataset_version import DatasetVersion, DatasetVersionRegistry

__all__ = [
    "DatasetCatalog",
    "DatasetCatalogEntry",
    "DatasetCreatedEvent",
    "DatasetNotFoundError",
    "DatasetRegistrationError",
    "DatasetRegistry",
    "DatasetUpdatedEvent",
    "DatasetValidatedEvent",
    "DatasetVersion",
    "DatasetVersionRegistry",
    "FeatureCache",
    "FeatureDataset",
    "FeatureMetadata",
    "FeatureRecord",
    "FeatureRecordNotFoundError",
    "FeatureRegistry",
    "FeatureRegistryEntry",
    "FeatureRepository",
    "FeatureSnapshot",
    "FeatureStore",
    "FeatureStoreError",
    "FeatureStoreLifecycleEvent",
    "FeatureStoreLifecycleEventType",
    "FeatureStoreLifecycleManager",
    "FeatureStoreValidationError",
    "FeatureStoreValidator",
    "FeatureVersionError",
    "SnapshotCreatedEvent",
    "SnapshotNotFoundError",
    "ValidationResult",
    "build_reproducible_dataset",
    "compute_feature_dataset_hash",
    "dataset_from_feature_set",
    "get_feature_store_registry",
    "ingest_feature_set",
    "record_from_vector",
    "records_from_feature_set",
    "register_features_from_set",
    "reset_feature_store_registry",
]
