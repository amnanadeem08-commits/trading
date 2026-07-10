"""Unit tests for inference validation."""

from __future__ import annotations

import pytest

from inference_pipeline import InferenceRequest, InferenceValidator
from tests.inference_pipeline_helpers import make_inference_runtime


@pytest.mark.unit
def test_validate_request_success() -> None:
    validator = InferenceValidator()
    request = InferenceRequest(
        request_id="req-1",
        model_id="model-1",
        input_metadata={"id": "1"},
    )
    result = validator.validate_request(request)
    assert result.valid is True


@pytest.mark.unit
def test_validate_request_failure() -> None:
    validator = InferenceValidator()
    request = InferenceRequest(
        request_id="req-1",
        model_id="",
        input_metadata={"id": "1"},
    )
    result = validator.validate_request(request)
    assert result.valid is False


@pytest.mark.unit
def test_validate_model_exists() -> None:
    runtime = make_inference_runtime()
    validator = InferenceValidator()
    result = validator.validate_model_exists("model-1", runtime.model_registry)
    assert result.valid is True
