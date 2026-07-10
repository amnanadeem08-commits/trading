"""Contract tests for market data framework."""

from __future__ import annotations

import inspect

import pytest

from market_data import (
    Candle,
    MarketCatalogEntry,
    MarketDataRegistry,
    MarketLifecycleManager,
    MarketRecord,
    MarketSchemaValidator,
    MarketVersionRegistry,
    StreamBuffer,
    StreamContext,
    build_stream_from_repository,
    normalize_historical_payload,
    records_from_repository,
)


@pytest.mark.contract
def test_market_record_contract() -> None:
    fields = set(MarketRecord.model_fields)
    assert "record_id" in fields
    assert "dataset_id" in fields
    assert "symbol_id" in fields
    assert "record_type" in fields
    assert "timestamp" in fields
    assert "sequence" in fields


@pytest.mark.contract
def test_candle_contract() -> None:
    fields = set(Candle.model_fields)
    assert "open" in fields
    assert "high" in fields
    assert "low" in fields
    assert "close" in fields
    assert "volume" in fields
    methods = {name for name, _ in inspect.getmembers(Candle, predicate=inspect.isfunction)}
    assert "to_market_record" in methods


@pytest.mark.contract
def test_market_data_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(MarketDataRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "lookup" in methods
    assert "version" in methods
    assert "metadata" in methods
    assert "capabilities" in methods


@pytest.mark.contract
def test_stream_buffer_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(StreamBuffer, predicate=inspect.isfunction)}
    assert "next" in methods
    assert "seek" in methods
    assert "window" in methods
    assert "page" in methods
    assert "append" in methods
    assert "reset" in methods


@pytest.mark.contract
def test_stream_context_contract() -> None:
    fields = set(StreamContext.model_fields)
    assert "stream_id" in fields
    assert "dataset_id" in fields
    assert "buffer_size" in fields
    assert "batch_size" in fields
    assert "offset" in fields
    assert "window_size" in fields


@pytest.mark.contract
def test_validator_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(MarketSchemaValidator, predicate=inspect.isfunction)
    }
    assert "validate_record" in methods
    assert "validate_batch" in methods
    assert "validate_candle" in methods


@pytest.mark.contract
def test_lifecycle_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(MarketLifecycleManager, predicate=inspect.isfunction)
    }
    assert "emit" in methods
    assert "on_event" in methods


@pytest.mark.contract
def test_version_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(MarketVersionRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "latest" in methods
    assert "list_versions" in methods
    assert "snapshot" in methods


@pytest.mark.contract
def test_catalog_entry_contract() -> None:
    fields = set(MarketCatalogEntry.model_fields)
    assert "dataset_id" in fields
    assert "name" in fields
    assert "version" in fields
    assert "capabilities" in fields


@pytest.mark.contract
def test_historical_bridge_contract() -> None:
    assert callable(records_from_repository)
    assert callable(build_stream_from_repository)
    assert callable(normalize_historical_payload)
