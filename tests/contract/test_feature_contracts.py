"""Contract tests for feature engineering framework."""

from __future__ import annotations

import inspect

import pytest

from feature_engineering import (
    Feature,
    FeatureCatalogEntry,
    FeatureExtractionPipeline,
    FeatureLifecycleManager,
    FeatureRegistry,
    FeatureSchema,
    FeatureSchemaRegistry,
    FeatureSchemaValidator,
    FeatureValidator,
    FeatureVector,
    FeatureVersionRegistry,
    build_pipeline_from_stream,
    run_extraction_from_stream,
)


@pytest.mark.contract
def test_feature_contract() -> None:
    fields = set(Feature.model_fields)
    assert "name" in fields
    assert "value" in fields
    assert "dtype" in fields


@pytest.mark.contract
def test_feature_vector_contract() -> None:
    fields = set(FeatureVector.model_fields)
    assert "vector_id" in fields
    assert "dataset_id" in fields
    assert "symbol_id" in fields
    assert "features" in fields
    assert "timestamp" in fields


@pytest.mark.contract
def test_feature_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(FeatureRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "lookup" in methods
    assert "version" in methods
    assert "metadata" in methods
    assert "capabilities" in methods


@pytest.mark.contract
def test_feature_extraction_pipeline_contract() -> None:
    methods = {
        name
        for name, _ in inspect.getmembers(FeatureExtractionPipeline, predicate=inspect.isfunction)
    }
    assert "extract_vector" in methods
    assert "extract_batch" in methods
    assert "extract_set" in methods
    assert "extract_window" in methods
    assert "run" in methods


@pytest.mark.contract
def test_feature_validator_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(FeatureValidator, predicate=inspect.isfunction)
    }
    assert "validate_vector" in methods
    assert "validate_batch" in methods
    assert "validate_set" in methods


@pytest.mark.contract
def test_feature_schema_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(FeatureSchemaRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "lookup" in methods
    assert "list" in methods


@pytest.mark.contract
def test_feature_schema_validator_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(FeatureSchemaValidator, predicate=inspect.isfunction)
    }
    assert "validate_vector" in methods
    assert "validate_batch" in methods


@pytest.mark.contract
def test_lifecycle_contract() -> None:
    methods = {
        name
        for name, _ in inspect.getmembers(FeatureLifecycleManager, predicate=inspect.isfunction)
    }
    assert "emit" in methods
    assert "on_event" in methods
    assert "emit_extraction_started" in methods
    assert "emit_extraction_completed" in methods


@pytest.mark.contract
def test_version_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(FeatureVersionRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "latest" in methods
    assert "list_versions" in methods
    assert "snapshot" in methods


@pytest.mark.contract
def test_catalog_entry_contract() -> None:
    fields = set(FeatureCatalogEntry.model_fields)
    assert "feature_id" in fields
    assert "schema_id" in fields
    assert "capabilities" in fields


@pytest.mark.contract
def test_market_data_bridge_contract() -> None:
    assert callable(build_pipeline_from_stream)
    assert callable(run_extraction_from_stream)


@pytest.mark.contract
def test_feature_schema_contract() -> None:
    fields = set(FeatureSchema.model_fields)
    assert "schema_id" in fields
    assert "required_fields" in fields
    assert "optional_fields" in fields
