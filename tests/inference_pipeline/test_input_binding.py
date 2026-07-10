"""Unit tests for input binding."""

from __future__ import annotations

import pytest

from inference_pipeline.runtime.input_binding import InputBinding
from inference_pipeline.runtime.input_schema import FeatureSpec, InputSchema, OutputType
from tests.inference_pipeline.execution_helpers import make_identity_input_schema


@pytest.mark.unit
def test_input_binding_produces_model_input_payload() -> None:
    payload, duration_ms = InputBinding().bind(
        schema=make_identity_input_schema(),
        features={"X": 2.5},
    )
    assert payload["input"] == [[2.5]]
    assert payload["feature_names"] == ["X"]
    assert duration_ms >= 0.0


@pytest.mark.unit
def test_input_binding_rejects_missing_feature() -> None:
    with pytest.raises(ValueError, match="missing required feature"):
        InputBinding().bind(schema=make_identity_input_schema(), features={})


@pytest.mark.unit
def test_input_binding_rejects_wrong_dtype() -> None:
    schema = InputSchema(
        features=(FeatureSpec(name="count", dtype="int32"),),
        output_type=OutputType.REGRESSION,
    )
    with pytest.raises(ValueError, match="incompatible dtype"):
        InputBinding().bind(schema=schema, features={"count": 1.5})


@pytest.mark.unit
def test_input_binding_rejects_wrong_shape() -> None:
    schema = InputSchema(
        features=(FeatureSpec(name="vector", dtype="float32", shape=(2,)),),
        output_type=OutputType.REGRESSION,
    )
    with pytest.raises(ValueError, match="shape mismatch"):
        InputBinding().bind(schema=schema, features={"vector": [1.0]})
