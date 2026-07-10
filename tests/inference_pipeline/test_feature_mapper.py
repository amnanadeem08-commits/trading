"""Unit tests for schema-driven feature mapping."""

from __future__ import annotations

import pytest

from inference_pipeline.runtime.feature_mapper import FeatureMapper
from inference_pipeline.runtime.input_schema import FeatureSpec, InputSchema, OutputType
from tests.inference_pipeline.execution_helpers import make_identity_input_schema


@pytest.mark.unit
def test_feature_mapper_orders_features_by_schema() -> None:
    schema = InputSchema(
        features=(
            FeatureSpec(name="b", dtype="float32"),
            FeatureSpec(name="a", dtype="float32"),
        ),
        output_type=OutputType.REGRESSION,
    )
    matrix, duration_ms = FeatureMapper().map_row(schema=schema, features={"a": 1.0, "b": 2.0})
    assert matrix == [[2.0, 1.0]]
    assert duration_ms >= 0.0


@pytest.mark.unit
def test_feature_mapper_uses_optional_default() -> None:
    schema = InputSchema(
        features=(
            FeatureSpec(name="required", dtype="float32"),
            FeatureSpec(name="optional", dtype="float32", optional=True, default=0.5),
        ),
        output_type=OutputType.REGRESSION,
    )
    matrix, _ = FeatureMapper().map_row(schema=schema, features={"required": 3.0})
    assert matrix == [[3.0, 0.5]]


@pytest.mark.unit
def test_feature_mapper_detects_missing_feature() -> None:
    with pytest.raises(ValueError, match="missing required feature"):
        FeatureMapper().map_row(schema=make_identity_input_schema(), features={})


@pytest.mark.unit
def test_feature_mapper_rejects_batch_execution() -> None:
    schema = make_identity_input_schema()
    with pytest.raises(ValueError, match="batch execution is not enabled"):
        FeatureMapper().map_batch(
            schema=schema,
            feature_rows=({"X": 1.0}, {"X": 2.0}),
        )
