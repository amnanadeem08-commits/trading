"""Unit tests for ML feature pipeline."""

from __future__ import annotations

import pytest

from ml import FeatureSet, IdentityFeaturePipeline


@pytest.mark.unit
def test_identity_feature_pipeline_transform() -> None:
    pipeline = IdentityFeaturePipeline(
        feature_set_id="features-records",
        name="Records Features",
        version="1.0.0",
        source_dataset_id="records",
    )
    records = ({"id": "1", "value": 1}, {"id": "2", "value": 2})
    feature_set = pipeline.transform(records)
    assert isinstance(feature_set, FeatureSet)
    assert feature_set.feature_set_id == "features-records"
    assert len(feature_set.records) == 2
    assert feature_set.metadata.field_count == 2


@pytest.mark.unit
def test_feature_pipeline_metadata() -> None:
    pipeline = IdentityFeaturePipeline(
        feature_set_id="features-records",
        name="Records Features",
        version="1.0.0",
        source_dataset_id="records",
    )
    assert pipeline.metadata().source_dataset_id == "records"
