"""Unit tests for ML evaluation framework."""

from __future__ import annotations

import pytest

from ml import EvaluationMetrics, EvaluationState, InMemoryEvaluator
from tests.ml_helpers import SampleMLModel


@pytest.mark.unit
def test_evaluator_with_model_implementation() -> None:
    evaluator = InMemoryEvaluator()
    result = evaluator.evaluate(
        SampleMLModel(),
        dataset_id="records",
        predictions=({"score": 0.9},),
    )
    assert result.state == EvaluationState.COMPLETED
    assert result.metrics.values["accuracy"] == 0.95


@pytest.mark.unit
def test_evaluation_metrics_registration() -> None:
    metrics = EvaluationMetrics(
        evaluation_id="eval-1",
        model_id="sample-model",
    ).register("f1", 0.88)
    assert metrics.values["f1"] == 0.88
