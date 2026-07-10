"""Unit tests for inference runtime."""

from __future__ import annotations

import pytest

from inference_pipeline import InferenceStatus, run_inference_for_model
from tests.inference_pipeline_helpers import make_inference_runtime


@pytest.mark.unit
def test_inference_runtime_submit_and_execute() -> None:
    runtime = make_inference_runtime()
    result = run_inference_for_model(
        runtime,
        model_id="model-1",
        input_metadata={"feature_set_id": "fs-1"},
    )
    assert result.status == InferenceStatus.COMPLETED
    assert result.metadata.artifact_id


@pytest.mark.unit
def test_inference_runtime_resolve_model() -> None:
    runtime = make_inference_runtime()
    version = runtime.resolve_model("model-1")
    assert version.stage.value == "production"


@pytest.mark.unit
def test_inference_runtime_lifecycle_events() -> None:
    runtime = make_inference_runtime()
    run_inference_for_model(
        runtime,
        model_id="model-1",
        input_metadata={"feature_set_id": "fs-1"},
    )
    assert len(runtime.lifecycle.events) >= 3
