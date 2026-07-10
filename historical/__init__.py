"""Historical data repository public API."""

from historical.datasets.dataset_metadata import HistoricalDatasetMetadata
from historical.datasets.dataset_registry import (
    DatasetRegistry,
    get_dataset_registry,
    reset_dataset_registry,
)
from historical.datasets.dataset_version import DatasetVersion
from historical.datasets.historical_dataset import (
    HistoricalDataset,
    HistoricalDatasetSchema,
    compute_dataset_checksum,
)
from historical.exceptions import (
    DatasetNotFoundError,
    DatasetRegistrationError,
    HistoricalError,
    HistoricalValidationError,
    QueryError,
    ReplayError,
    StorageError,
    VersionError,
)
from historical.lifecycle.historical_lifecycle import (
    HistoricalLifecycleEvent,
    HistoricalLifecycleEventType,
    HistoricalLifecycleManager,
)
from historical.query.filters import QueryFilters
from historical.query.query_engine import QueryEngine
from historical.query.query_request import QueryRequest, QueryType
from historical.query.query_result import QueryResult
from historical.registry.historical_registry import (
    HistoricalRegistry,
    get_historical_registry,
    reset_historical_registry,
)
from historical.replay.replay_context import ReplayContext
from historical.replay.replay_cursor import ReplayCursor, ReplayState
from historical.replay.replay_engine import ReplayEngine
from historical.replay.replay_result import ReplayResult
from historical.storage.in_memory_storage import InMemoryStorage
from historical.storage.repository import Repository
from historical.storage.repository_record import RepositoryRecord
from historical.storage.storage_backend import StorageBackend
from historical.validation.validation_result import HistoricalValidationResult
from historical.validation.validator import HistoricalValidator
from historical.versioning.historical_version import (
    HistoricalVersionRegistry,
    HistoricalVersionSnapshot,
)

__all__ = [
    "DatasetNotFoundError",
    "DatasetRegistrationError",
    "DatasetRegistry",
    "DatasetVersion",
    "HistoricalDataset",
    "HistoricalDatasetMetadata",
    "HistoricalDatasetSchema",
    "HistoricalError",
    "HistoricalLifecycleEvent",
    "HistoricalLifecycleEventType",
    "HistoricalLifecycleManager",
    "HistoricalRegistry",
    "HistoricalValidationError",
    "HistoricalValidationResult",
    "HistoricalValidator",
    "HistoricalVersionRegistry",
    "HistoricalVersionSnapshot",
    "InMemoryStorage",
    "QueryEngine",
    "QueryError",
    "QueryFilters",
    "QueryRequest",
    "QueryResult",
    "QueryType",
    "ReplayContext",
    "ReplayCursor",
    "ReplayEngine",
    "ReplayError",
    "ReplayResult",
    "ReplayState",
    "Repository",
    "RepositoryRecord",
    "StorageBackend",
    "StorageError",
    "VersionError",
    "compute_dataset_checksum",
    "get_dataset_registry",
    "get_historical_registry",
    "reset_dataset_registry",
    "reset_historical_registry",
]
