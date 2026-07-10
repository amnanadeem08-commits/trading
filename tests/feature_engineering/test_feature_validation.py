"""Unit tests for feature validation."""

from __future__ import annotations

import pytest

from feature_engineering import (
    FeatureBatch,
    FeatureValidator,
    NonEmptyVectorRule,
    RequiredFieldsRule,
)
from tests.feature_engineering_helpers import make_sample_feature_vector


@pytest.mark.unit
def test_validate_vector_success() -> None:
    validator = FeatureValidator(rules=(NonEmptyVectorRule(),))
    vector = make_sample_feature_vector()
    result = validator.validate_vector(vector)
    assert result.valid is True


@pytest.mark.unit
def test_validate_vector_missing() -> None:
    validator = FeatureValidator()
    result = validator.validate_vector(None)
    assert result.valid is False
    assert "Feature vector is required" in result.errors


@pytest.mark.unit
def test_required_fields_rule() -> None:
    rule = RequiredFieldsRule(required_fields=("close",))
    vector = make_sample_feature_vector()
    result = rule.validate(vector)
    assert result.valid is True


@pytest.mark.unit
def test_required_fields_rule_missing() -> None:
    rule = RequiredFieldsRule(required_fields=("missing_field",))
    vector = make_sample_feature_vector()
    result = rule.validate(vector)
    assert result.valid is False


@pytest.mark.unit
def test_validate_batch_duplicates() -> None:
    validator = FeatureValidator()
    vector = make_sample_feature_vector()
    batch = FeatureBatch(
        batch_id="batch-1",
        pipeline_id="pipeline-1",
        dataset_id="dataset-1",
        symbol_id="symbol-1",
        vectors=(vector, vector),
    )
    result = validator.validate_batch(batch)
    assert result.valid is False
    assert "Duplicate vector ids detected" in result.errors


@pytest.mark.unit
def test_validate_set() -> None:
    validator = FeatureValidator(rules=(NonEmptyVectorRule(),))
    vector = make_sample_feature_vector()
    from feature_engineering import FeatureMetadata, FeatureSet

    metadata = FeatureMetadata(
        feature_set_id="set-1",
        dataset_id="dataset-1",
        symbol_id="symbol-1",
        schema_id="feature-schema-v1",
    )
    feature_set = FeatureSet(feature_set_id="set-1", vectors=(vector,), metadata=metadata)
    result = validator.validate_set(feature_set)
    assert result.valid is True
