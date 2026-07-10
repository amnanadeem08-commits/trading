"""Unit tests for feature engineering bridge."""

from __future__ import annotations

import pytest

from feature_store import (
    FeatureRegistry,
    dataset_from_feature_set,
    record_from_vector,
    register_features_from_set,
)
from tests.feature_engineering_helpers import make_sample_feature_vector
from tests.feature_store_helpers import seed_feature_set_from_pipeline


@pytest.mark.unit
def test_record_from_vector() -> None:
    vector = make_sample_feature_vector()
    record = record_from_vector(vector)
    assert record.vector_id == vector.vector_id
    assert "close" in record.values


@pytest.mark.unit
def test_dataset_from_feature_set() -> None:
    feature_set, _ = seed_feature_set_from_pipeline(record_count=1)
    dataset = dataset_from_feature_set(feature_set)
    assert dataset.dataset_id == "dataset-1"


@pytest.mark.unit
def test_register_features_from_set() -> None:
    feature_set, _ = seed_feature_set_from_pipeline(record_count=1)
    registry = FeatureRegistry()
    entries = register_features_from_set(feature_set, registry)
    assert len(entries) > 0
    assert registry.exists("close") is True


@pytest.mark.unit
def test_ingest_empty_feature_set_registers_features_only() -> None:
    from feature_engineering import FeatureMetadata, FeatureSet

    empty_set = FeatureSet(
        feature_set_id="empty",
        vectors=(),
        metadata=FeatureMetadata(
            feature_set_id="empty",
            dataset_id="dataset-empty",
            symbol_id="symbol-1",
            schema_id="feature-schema-v1",
        ),
    )
    entries = register_features_from_set(empty_set, FeatureRegistry())
    assert entries == ()
