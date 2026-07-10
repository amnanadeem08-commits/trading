"""Contract tests for feature store."""

from __future__ import annotations

import inspect

import pytest

from feature_store import (
    DatasetCatalog,
    DatasetRegistry,
    DatasetVersionRegistry,
    FeatureCache,
    FeatureDataset,
    FeatureRecord,
    FeatureRegistry,
    FeatureRepository,
    FeatureSnapshot,
    FeatureStore,
    FeatureStoreLifecycleManager,
    FeatureStoreValidator,
    ingest_feature_set,
)


@pytest.mark.contract
def test_feature_record_contract() -> None:
    fields = set(FeatureRecord.model_fields)
    assert "record_id" in fields
    assert "dataset_id" in fields
    assert "vector_id" in fields
    assert "values" in fields


@pytest.mark.contract
def test_feature_dataset_contract() -> None:
    fields = set(FeatureDataset.model_fields)
    assert "dataset_id" in fields
    assert "version" in fields
    assert "metadata" in fields
    assert "checksum" in fields
    assert "lineage" in fields


@pytest.mark.contract
def test_feature_snapshot_contract() -> None:
    fields = set(FeatureSnapshot.model_fields)
    assert "snapshot_id" in fields
    assert "dataset_id" in fields
    assert "record_count" in fields


@pytest.mark.contract
def test_feature_store_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(FeatureStore, predicate=inspect.isfunction)}
    assert "register_dataset" in methods
    assert "ingest_records" in methods
    assert "load_offline" in methods
    assert "get_online" in methods
    assert "create_snapshot" in methods
    assert "validate_dataset" in methods
    assert "lookup_feature" in methods


@pytest.mark.contract
def test_feature_repository_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(FeatureRepository, predicate=inspect.isfunction)
    }
    assert "register_dataset" in methods
    assert "store" in methods
    assert "load" in methods
    assert "create_snapshot" in methods


@pytest.mark.contract
def test_feature_cache_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(FeatureCache, predicate=inspect.isfunction)}
    assert "cache_offline" in methods
    assert "get_offline" in methods
    assert "cache_online" in methods
    assert "get_online" in methods


@pytest.mark.contract
def test_dataset_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(DatasetRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "lookup" in methods
    assert "list_versions" in methods


@pytest.mark.contract
def test_feature_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(FeatureRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "lookup" in methods


@pytest.mark.contract
def test_dataset_catalog_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(DatasetCatalog, predicate=inspect.isfunction)}
    assert "register" in methods
    assert "lookup" in methods
    assert "capabilities" in methods


@pytest.mark.contract
def test_validator_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(FeatureStoreValidator, predicate=inspect.isfunction)
    }
    assert "validate_record" in methods
    assert "validate_dataset" in methods
    assert "validate_checksum" in methods


@pytest.mark.contract
def test_lifecycle_contract() -> None:
    methods = {
        name
        for name, _ in inspect.getmembers(
            FeatureStoreLifecycleManager, predicate=inspect.isfunction
        )
    }
    assert "emit" in methods
    assert "emit_dataset_created" in methods
    assert "emit_snapshot_created" in methods


@pytest.mark.contract
def test_version_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(DatasetVersionRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "latest" in methods
    assert "snapshot" in methods


@pytest.mark.contract
def test_bridge_contract() -> None:
    assert callable(ingest_feature_set)
