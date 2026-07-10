"""Unit tests for ML runtime."""

from __future__ import annotations

import pytest

from ml_runtime import ExecutionStatus, MLRuntime, build_ml_runtime
from tests.ml_runtime_helpers import make_ml_runtime, run_full_runtime_flow


@pytest.mark.unit
def test_build_ml_runtime_initializes() -> None:
    runtime = build_ml_runtime()
    assert isinstance(runtime, MLRuntime)
    assert runtime.validator is not None
    assert runtime.version_registry.latest() is not None


@pytest.mark.unit
def test_register_and_execute() -> None:
    inference_response, execution_result = run_full_runtime_flow()
    assert inference_response.status.value == "completed"
    assert execution_result.status == ExecutionStatus.COMPLETED
    assert execution_result.metadata is not None
    assert execution_result.metadata.model_version


@pytest.mark.unit
def test_shutdown_clears_registry() -> None:
    runtime = make_ml_runtime()
    assert len(runtime.registry.list()) == 1
    runtime.shutdown()
    assert runtime.registry.list() == ()


@pytest.mark.unit
def test_execute_fails_without_executor() -> None:
    runtime = build_ml_runtime()
    inference_runtime = __import__(
        "tests.inference_pipeline_helpers", fromlist=["make_inference_runtime"]
    ).make_inference_runtime()
    from inference_pipeline import run_inference_for_model
    from ml_runtime import RuntimeValidationError

    response = run_inference_for_model(
        inference_runtime,
        model_id="model-1",
        input_metadata={"id": "1"},
    )
    with pytest.raises(RuntimeValidationError):
        runtime.execute(response, executor_id="missing")
