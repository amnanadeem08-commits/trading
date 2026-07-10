"""Unit tests for output normalization."""

from __future__ import annotations

import pytest

from inference_pipeline.runtime.input_schema import OutputType
from inference_pipeline.runtime.output_normalizer import OutputNormalizer


@pytest.mark.unit
def test_output_normalizer_regression_values() -> None:
    result = OutputNormalizer().normalize(
        output_type=OutputType.REGRESSION,
        raw_outputs=[[[4.5]]],
    )
    assert result.values == [4.5]
    assert result.output_type == OutputType.REGRESSION


@pytest.mark.unit
def test_output_normalizer_binary_classification() -> None:
    result = OutputNormalizer().normalize(
        output_type=OutputType.BINARY_CLASSIFICATION,
        raw_outputs=[[0.8, 0.2]],
    )
    assert result.probabilities is not None
    assert result.label == 1


@pytest.mark.unit
def test_output_normalizer_multiclass_probabilities() -> None:
    result = OutputNormalizer().normalize(
        output_type=OutputType.MULTICLASS,
        raw_outputs=[[0.1, 0.7, 0.2]],
    )
    assert result.probabilities is not None
    assert result.label == 1
