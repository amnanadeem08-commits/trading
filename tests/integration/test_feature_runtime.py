"""Integration test for feature engineering pipeline."""

from __future__ import annotations

import pytest

from feature_engineering import (
    FeatureValidator,
    NonEmptyVectorRule,
    build_pipeline_from_stream,
    extract_batch_from_stream,
    extract_set_from_stream,
    run_extraction_from_stream,
)
from tests.feature_engineering_helpers import seed_historical_and_stream


@pytest.mark.integration
def test_market_data_to_feature_batch_flow() -> None:
    _, stream = seed_historical_and_stream(record_count=3)
    batch = extract_batch_from_stream(stream, pipeline_id="integration-batch")
    assert len(batch.vectors) == 3
    assert batch.dataset_id == "dataset-1"


@pytest.mark.integration
def test_market_data_to_feature_set_flow() -> None:
    _, stream = seed_historical_and_stream(record_count=2)
    feature_set = extract_set_from_stream(stream, pipeline_id="integration-set")
    assert feature_set.metadata.record_count == 2
    assert len(feature_set.vectors[0].features) > 0


@pytest.mark.integration
def test_full_extraction_pipeline_validates() -> None:
    _, stream = seed_historical_and_stream(record_count=3)
    result = run_extraction_from_stream(stream, max_batches=1)
    validator = FeatureValidator(rules=(NonEmptyVectorRule(),))
    assert result.feature_set is not None
    validation = validator.validate_set(result.feature_set)
    assert validation.valid is True


@pytest.mark.integration
def test_pipeline_from_stream_reusable() -> None:
    _, stream = seed_historical_and_stream(record_count=2)
    pipeline = build_pipeline_from_stream(stream)
    first = pipeline.extract_batch(page=0)
    assert len(first.vectors) == 2
