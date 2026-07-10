"""Unit tests for feature engineering models."""

from __future__ import annotations

import pytest

from feature_engineering import Feature, FeatureBatch, FeatureSet, FeatureWindow
from tests.feature_engineering_helpers import (
    make_extraction_context,
    make_feature_schema,
    make_sample_feature_vector,
)


@pytest.mark.unit
def test_feature_model_fields() -> None:
    feature = Feature(name="close", value=100.0, dtype="float")
    assert feature.name == "close"
    assert feature.value == 100.0


@pytest.mark.unit
def test_feature_vector_fields() -> None:
    vector = make_sample_feature_vector()
    assert vector.vector_id == "vector-1"
    assert len(vector.features) == 2


@pytest.mark.unit
def test_feature_batch_fields() -> None:
    vector = make_sample_feature_vector()
    batch = FeatureBatch(
        batch_id="batch-1",
        pipeline_id="pipeline-1",
        dataset_id="dataset-1",
        symbol_id="symbol-1",
        vectors=(vector,),
        total=1,
    )
    assert batch.completed is False
    assert len(batch.vectors) == 1


@pytest.mark.unit
def test_feature_window_fields() -> None:
    vector = make_sample_feature_vector()
    window = FeatureWindow(
        window_id="window-1",
        dataset_id="dataset-1",
        symbol_id="symbol-1",
        vectors=(vector,),
        window_size=1,
    )
    assert window.offset == 0


@pytest.mark.unit
def test_feature_set_fields() -> None:
    vector = make_sample_feature_vector()
    schema = make_feature_schema()
    from feature_engineering import FeatureMetadata

    metadata = FeatureMetadata(
        feature_set_id="set-1",
        dataset_id="dataset-1",
        symbol_id="symbol-1",
        schema_id=schema.schema_id,
        feature_count=2,
        record_count=1,
    )
    feature_set = FeatureSet(feature_set_id="set-1", vectors=(vector,), metadata=metadata)
    assert feature_set.metadata.schema_id == schema.schema_id


@pytest.mark.unit
def test_extraction_context_fields() -> None:
    context = make_extraction_context()
    assert context.pipeline_id == "pipeline-1"
    assert context.batch_size == 10
