"""Contract tests for historical data repository."""

from __future__ import annotations

import inspect

import pytest

from historical import (
    DatasetRegistry,
    HistoricalDataset,
    HistoricalLifecycleManager,
    HistoricalRegistry,
    HistoricalValidator,
    QueryEngine,
    QueryRequest,
    QueryResult,
    QueryType,
    ReplayEngine,
    ReplayResult,
    Repository,
    RepositoryRecord,
)


@pytest.mark.contract
def test_repository_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(Repository, predicate=inspect.isfunction)}
    assert "register_dataset" in methods
    assert "store" in methods
    assert "load" in methods
    assert "exists" in methods
    assert "delete" in methods
    assert "list" in methods
    assert "version" in methods
    assert "metadata" in methods


@pytest.mark.contract
def test_historical_dataset_contract() -> None:
    fields = set(HistoricalDataset.model_fields)
    assert "dataset_id" in fields
    assert "version" in fields
    assert "metadata" in fields
    assert "dataset_schema" in fields
    assert "time_range_start" in fields
    assert "time_range_end" in fields
    assert "record_count" in fields
    assert "checksum" in fields
    assert "source" in fields
    assert "tags" in fields


@pytest.mark.contract
def test_replay_engine_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(ReplayEngine, predicate=inspect.isfunction)}
    assert "begin" in methods
    assert "next" in methods
    assert "seek" in methods
    assert "pause" in methods
    assert "resume" in methods
    assert "stop" in methods
    assert "reset" in methods


@pytest.mark.contract
def test_query_engine_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(QueryEngine, predicate=inspect.isfunction)}
    assert "execute" in methods
    assert "lookup_by_id" in methods
    assert "lookup_by_version" in methods
    assert "query_time_range" in methods


@pytest.mark.contract
def test_repository_record_contract() -> None:
    fields = set(RepositoryRecord.model_fields)
    assert "record_id" in fields
    assert "dataset_id" in fields
    assert "version" in fields
    assert "timestamp" in fields
    assert "payload" in fields
    assert "sequence" in fields


@pytest.mark.contract
def test_replay_result_contract() -> None:
    fields = set(ReplayResult.model_fields)
    assert "record" in fields
    assert "completed" in fields
    assert "position" in fields


@pytest.mark.contract
def test_query_result_contract() -> None:
    fields = set(QueryResult.model_fields)
    assert "matched" in fields
    assert "datasets" in fields
    assert "records" in fields
    assert "metadata" in fields


@pytest.mark.contract
def test_historical_registry_contract() -> None:
    registry = HistoricalRegistry()
    assert registry.repository is not None
    assert registry.query is not None
    assert registry.replay is not None
    assert registry.validator is not None


@pytest.mark.contract
def test_dataset_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(DatasetRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "resolve" in methods
    assert "list" in methods


@pytest.mark.contract
def test_validator_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(HistoricalValidator, predicate=inspect.isfunction)
    }
    assert "validate_dataset" in methods
    assert "validate_schema" in methods
    assert "validate_timestamps" in methods
    assert "validate_duplicates" in methods
    assert "validate_checksum" in methods
    assert "validate_metadata" in methods


@pytest.mark.contract
def test_lifecycle_contract() -> None:
    methods = {
        name
        for name, _ in inspect.getmembers(HistoricalLifecycleManager, predicate=inspect.isfunction)
    }
    assert "emit" in methods
    assert "on_event" in methods


@pytest.mark.contract
def test_query_request_contract() -> None:
    request = QueryRequest(query_type=QueryType.BY_ID)
    assert request.query_type.value == "by_id"
