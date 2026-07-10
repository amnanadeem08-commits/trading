"""Inference pipeline bridge for ML runtime integration."""

from __future__ import annotations

from inference_pipeline import InferenceResponse, InferenceRuntime, run_inference_for_model
from ml_runtime.execution.execution_result import ExecutionResult
from ml_runtime.execution.model_executor import ModelExecutor
from ml_runtime.runtime.ml_runtime import MLRuntime, build_ml_runtime

__all__ = [
    "MLRuntime",
    "ModelExecutor",
    "build_ml_runtime",
    "execute_runtime_for_inference",
    "run_inference_and_execute",
]


def execute_runtime_for_inference(
    runtime: MLRuntime,
    inference_response: InferenceResponse,
    *,
    executor_id: str,
) -> ExecutionResult:
    """Execute ML runtime orchestration for a completed inference response."""
    return runtime.execute(inference_response, executor_id=executor_id)


def run_inference_and_execute(
    inference_runtime: InferenceRuntime,
    ml_runtime: MLRuntime,
    *,
    model_id: str,
    input_metadata: dict[str, object],
    executor_id: str,
) -> tuple[InferenceResponse, ExecutionResult]:
    """Run inference orchestration then ML runtime execution."""
    inference_response = run_inference_for_model(
        inference_runtime,
        model_id=model_id,
        input_metadata=input_metadata,
    )
    execution_result = execute_runtime_for_inference(
        ml_runtime,
        inference_response,
        executor_id=executor_id,
    )
    return inference_response, execution_result
