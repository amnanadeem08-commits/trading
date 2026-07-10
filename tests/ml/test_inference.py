"""Unit tests for ML inference framework."""

from __future__ import annotations

import pytest

from ml import InferenceContext, InMemoryPredictor
from tests.ml_helpers import SampleMLModel


@pytest.mark.unit
def test_predictor_returns_outputs() -> None:
    predictor = InMemoryPredictor()
    model = SampleMLModel()
    inputs = ({"id": "1", "value": 10}, {"id": "2", "value": 20})
    result = predictor.predict(model, inputs=inputs)
    assert len(result.outputs) == 2
    assert result.model_id == "sample-model"
    assert result.metadata["count"] == "2"


@pytest.mark.unit
def test_predictor_uses_inference_context() -> None:
    predictor = InMemoryPredictor()
    context = InferenceContext(
        inference_id="inf-ctx",
        model_id="sample-model",
        model_version="1.0.0",
        input_count=1,
    )
    result = predictor.predict(
        SampleMLModel(),
        inputs=({"id": "1"},),
        context=context,
    )
    assert result.inference_id == "inf-ctx"
