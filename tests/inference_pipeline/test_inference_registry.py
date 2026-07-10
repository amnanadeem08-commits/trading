"""Unit tests for inference registry."""

from __future__ import annotations

import pytest

from inference_pipeline import InferenceRegistry, InferenceRequestNotFoundError, InferenceStatus
from inference_pipeline.responses.inference_result import InferenceResult
from tests.inference_pipeline_helpers import make_inference_runtime


@pytest.mark.unit
def test_inference_registry_register_and_lookup() -> None:
    runtime = make_inference_runtime()
    from inference_pipeline import run_inference_for_model

    run_inference_for_model(
        runtime,
        model_id="model-1",
        input_metadata={"id": "1"},
    )
    history = runtime.inference_registry.history("model-1")
    assert len(history) == 1
    entry = runtime.inference_registry.lookup(history[0].request_id)
    assert entry.status == InferenceStatus.COMPLETED


@pytest.mark.unit
def test_inference_registry_latest_and_clear() -> None:
    registry = InferenceRegistry()
    result = InferenceResult(request_id="req-1", status=InferenceStatus.COMPLETED)
    registry.register(result)
    assert registry.latest("") is None
    registry.clear()
    with pytest.raises(InferenceRequestNotFoundError):
        registry.lookup("req-1")
