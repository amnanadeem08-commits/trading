"""Data layer public API."""

from data.cache import DatasetCache, InMemoryDatasetCache
from data.dataset import BaseDataset, Dataset
from data.decorators import dataset, dataset_metadata
from data.dependency import (
    DatasetDependency,
    DependencyGraph,
    build_dependency_graph,
    detect_cycle,
    topological_order,
)
from data.exceptions import (
    CircularDatasetDependencyError,
    DataError,
    DatasetCacheError,
    DatasetLoadError,
    DatasetNotFoundError,
    DatasetPersistenceError,
    DatasetRegistrationError,
    DatasetStateError,
    DatasetValidationError,
    SchemaValidationError,
)
from data.lifecycle import (
    DatasetLifecycleEvent,
    DatasetLifecycleEventType,
    DatasetLifecycleManager,
)
from data.lineage import LineageRecord, LineageTracker
from data.loader import DatasetLoader, InMemoryDatasetLoader
from data.metadata import DatasetMetadata
from data.persistence import DatasetPersistenceStore, InMemoryDatasetPersistenceStore
from data.provenance import ProvenanceRecord, ProvenanceTracker
from data.registry import DatasetRegistry, get_dataset_registry, reset_dataset_registry
from data.repository import DatasetRepository, InMemoryDatasetRepository
from data.result import DatasetResult, DatasetStatus
from data.schema import DatasetSchema, SchemaField
from data.serialization import deserialize_metadata, serialize_metadata
from data.state import TERMINAL_DATASET_STATES, DatasetState
from data.transformer import DataTransformer
from data.validation import DatasetValidationResult, validate_dataset, validate_dataset_set
from data.validator import SchemaValidationResult, SchemaValidator
from data.versioning import DatasetVersion, DatasetVersionRegistry

__all__ = [
    "TERMINAL_DATASET_STATES",
    "BaseDataset",
    "CircularDatasetDependencyError",
    "DataError",
    "DataTransformer",
    "Dataset",
    "DatasetCache",
    "DatasetCacheError",
    "DatasetDependency",
    "DatasetLifecycleEvent",
    "DatasetLifecycleEventType",
    "DatasetLifecycleManager",
    "DatasetLoadError",
    "DatasetLoader",
    "DatasetMetadata",
    "DatasetNotFoundError",
    "DatasetPersistenceError",
    "DatasetPersistenceStore",
    "DatasetRegistrationError",
    "DatasetRegistry",
    "DatasetRepository",
    "DatasetResult",
    "DatasetSchema",
    "DatasetState",
    "DatasetStateError",
    "DatasetStatus",
    "DatasetValidationError",
    "DatasetValidationResult",
    "DatasetVersion",
    "DatasetVersionRegistry",
    "DependencyGraph",
    "InMemoryDatasetCache",
    "InMemoryDatasetLoader",
    "InMemoryDatasetPersistenceStore",
    "InMemoryDatasetRepository",
    "LineageRecord",
    "LineageTracker",
    "ProvenanceRecord",
    "ProvenanceTracker",
    "SchemaField",
    "SchemaValidationError",
    "SchemaValidationResult",
    "SchemaValidator",
    "build_dependency_graph",
    "dataset",
    "dataset_metadata",
    "deserialize_metadata",
    "detect_cycle",
    "get_dataset_registry",
    "reset_dataset_registry",
    "serialize_metadata",
    "topological_order",
    "validate_dataset",
    "validate_dataset_set",
]
