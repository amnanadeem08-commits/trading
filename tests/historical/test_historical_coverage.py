"""Coverage tests for historical repository edge cases."""

from __future__ import annotations

import pytest

from historical import (
    DatasetNotFoundError,
    DatasetRegistrationError,
    HistoricalError,
    HistoricalValidationError,
    HistoricalVersionRegistry,
    InMemoryStorage,
    QueryEngine,
    QueryError,
    QueryRequest,
    QueryType,
    ReplayContext,
    ReplayEngine,
    ReplayError,
    Repository,
    StorageError,
    VersionError,
    get_dataset_registry,
    get_historical_registry,
    reset_dataset_registry,
    reset_historical_registry,
)
from historical.datasets.dataset_version import DatasetVersion
from tests.historical_helpers import make_sample_dataset, make_sample_record, seed_repository


def test_dataset_registry_singleton_and_unregister() -> None:
    reset_dataset_registry()
    registry = get_dataset_registry()
    dataset = make_sample_dataset()
    registry.register(dataset)
    registry.unregister("dataset-1")
    with pytest.raises(DatasetNotFoundError):
        registry.resolve("dataset-1")


def test_dataset_registry_empty_id_raises() -> None:
    from historical import DatasetRegistry

    registry = DatasetRegistry()
    dataset = make_sample_dataset().model_copy(update={"dataset_id": "   "})
    with pytest.raises(DatasetRegistrationError):
        registry.register(dataset)


def test_historical_registry_singleton() -> None:
    reset_historical_registry()
    first = get_historical_registry()
    second = get_historical_registry()
    assert first is second


def test_in_memory_storage_duplicate_record_raises() -> None:
    storage = InMemoryStorage()
    storage.register_dataset(make_sample_dataset())
    record = make_sample_record()
    storage.store(record)
    with pytest.raises(StorageError):
        storage.store(record)


def test_in_memory_storage_delete_version() -> None:
    storage = InMemoryStorage()
    storage.register_dataset(make_sample_dataset())
    storage.store(make_sample_record())
    storage.delete("dataset-1", version="1.0.0")
    assert storage.exists("dataset-1", version="1.0.0") is False


def test_in_memory_storage_missing_dataset_raises() -> None:
    storage = InMemoryStorage()
    with pytest.raises(DatasetNotFoundError):
        storage.get_dataset("missing")


def test_query_engine_error_paths() -> None:
    repository = Repository()
    engine = QueryEngine(repository)
    with pytest.raises(QueryError):
        engine.execute(QueryRequest(query_type=QueryType.BY_ID))
    with pytest.raises(QueryError):
        engine.execute(QueryRequest(query_type=QueryType.BY_VERSION))
    with pytest.raises(QueryError):
        engine.execute(QueryRequest(query_type=QueryType.TIME_RANGE))
    with pytest.raises(QueryError):
        engine.execute(QueryRequest(query_type=QueryType.CURSOR))


def test_query_metadata_filter_value() -> None:
    repository = Repository()
    dataset = make_sample_dataset()
    updated = dataset.model_copy(
        update={
            "metadata": dataset.metadata.model_copy(update={"attributes": {"owner": "platform"}})
        }
    )
    repository.register_dataset(updated)
    engine = QueryEngine(repository)
    from historical import QueryFilters

    result = engine.execute(
        QueryRequest(
            query_type=QueryType.METADATA,
            filters=QueryFilters(metadata_key="owner", metadata_value="missing"),
        )
    )
    assert result.matched is False


def test_replay_resume_completed_raises() -> None:
    repository = Repository()
    seed_repository(repository)
    engine = ReplayEngine(repository)
    engine.begin(ReplayContext(dataset_id="dataset-1", version="1.0.0"))
    while True:
        result = engine.next()
        if result is None or result.completed:
            break
    with pytest.raises(ReplayError):
        engine.resume()


def test_replay_reset_without_context_raises() -> None:
    engine = ReplayEngine(Repository())
    with pytest.raises(ReplayError):
        engine.reset()


def test_version_registry_errors() -> None:
    registry = HistoricalVersionRegistry()
    with pytest.raises(DatasetNotFoundError):
        registry.latest("missing")
    registry.register(
        DatasetVersion(
            dataset_id="dataset-1",
            version="1.0.0",
            snapshot_id="snapshot-1",
        )
    )
    with pytest.raises(VersionError):
        registry.rollback_metadata("dataset-1", target_version="9.9.9")


def test_historical_registry_properties_and_list() -> None:
    from historical import HistoricalRegistry

    registry = HistoricalRegistry()
    seed_repository(registry.repository)
    registry.register(make_sample_dataset())
    assert registry.repository.exists("dataset-1")
    assert registry.datasets.exists("dataset-1")
    assert registry.versions.latest("dataset-1").version == "1.0.0"
    assert "dataset-1" in registry.list()


def test_replay_engine_state_and_cursor() -> None:
    repository = Repository()
    seed_repository(repository)
    engine = ReplayEngine(repository)
    assert engine.state.value == "ready"
    engine.begin(ReplayContext(dataset_id="dataset-1", version="1.0.0"))
    assert engine.cursor.total == 3
    engine.pause()
    assert engine.state.value == "paused"


def test_in_memory_storage_list_versions_and_load_latest() -> None:
    storage = InMemoryStorage()
    storage.register_dataset(make_sample_dataset())
    storage.store(make_sample_record(version="1.0.0"))
    storage.store(make_sample_record(record_id="record-2", version="2.0.0", sequence=1))
    assert storage.list_versions("dataset-1") == ("1.0.0", "2.0.0")
    latest = storage.load("dataset-1")
    assert latest[0].version == "2.0.0"


def test_exception_types() -> None:
    assert isinstance(HistoricalError("bad"), Exception)
    assert isinstance(HistoricalValidationError("bad"), HistoricalError)
    assert DatasetNotFoundError("id").dataset_id == "id"


def test_validator_checksum_mismatch() -> None:
    from historical import HistoricalValidator

    repository = Repository()
    dataset = seed_repository(repository)
    mismatched = dataset.with_checksum("invalid")
    records = repository.load("dataset-1")
    result = HistoricalValidator().validate_checksum(mismatched, records)
    assert result.valid is False


def test_validator_schema_missing_field() -> None:
    from historical import HistoricalValidator

    validator = HistoricalValidator()
    dataset = make_sample_dataset()
    record = make_sample_record()
    bad_record = record.model_copy(update={"payload": {"timestamp": "x"}})
    result = validator.validate_schema(dataset, bad_record)
    assert result.valid is False
