"""Helpers for ML runtime tests."""

from __future__ import annotations

from typing import Any

from inference_pipeline import InferenceResponse, InferenceRuntime
from ml_runtime import (
    MLRuntime,
    ModelExecutor,
    RuntimeContext,
    build_ml_runtime,
    run_inference_and_execute,
)
from ml_runtime.execution.execution_metadata import ExecutionMetadata
from ml_runtime.execution.execution_result import ExecutionResult, ExecutionStatus
from tests.inference_pipeline_helpers import make_inference_runtime


class StubModelExecutor(ModelExecutor):
    """Stub executor for runtime tests. No framework binding."""

    def __init__(
        self, *, executor_id: str = "stub-executor", fail_on_execute: bool = False
    ) -> None:
        self._executor_id = executor_id
        self._fail_on_execute = fail_on_execute
        self.loaded = False
        self.unloaded = False

    def executor_id(self) -> str:
        return self._executor_id

    def load(self, *, artifact_reference: str, metadata: dict[str, object]) -> None:
        self.loaded = True
        _ = artifact_reference, metadata

    def execute(self, context: RuntimeContext) -> ExecutionResult:
        if self._fail_on_execute:
            msg = "stub execution failed"
            raise RuntimeError(msg)
        return ExecutionResult(
            execution_id=f"exec-{context.session_id}",
            request_id=context.request_id,
            status=ExecutionStatus.COMPLETED,
            metadata=ExecutionMetadata(
                execution_id=f"exec-{context.session_id}",
                request_id=context.request_id,
                model_id=context.model_id,
                model_version=context.model_version,
                artifact_reference=context.artifact_reference,
                executor_id=context.executor_id,
                correlation_id=context.correlation_id,
                trace_id=context.trace_id,
                started_at=__import__("models.common", fromlist=["utc_now"]).utc_now(),
            ),
            message="stub execution completed",
        )

    def execute_batch(
        self,
        contexts: tuple[RuntimeContext, ...],
    ) -> tuple[ExecutionResult, ...]:
        return tuple(self.execute(context) for context in contexts)

    def unload(self) -> None:
        self.unloaded = True

    def health(self) -> dict[str, Any]:
        return {"status": "healthy", "executor_id": self._executor_id}


def make_ml_runtime(*, executor_id: str = "stub-executor") -> MLRuntime:
    runtime = build_ml_runtime()
    runtime.register_executor(
        StubModelExecutor(executor_id=executor_id),
        name="Stub Executor",
        version="1.0.0",
        capabilities=("load", "execute", "unload"),
    )
    return runtime


def make_inference_and_ml_runtime(
    *,
    executor_id: str = "stub-executor",
) -> tuple[InferenceRuntime, MLRuntime]:
    inference_runtime = make_inference_runtime()
    ml_runtime = make_ml_runtime(executor_id=executor_id)
    return inference_runtime, ml_runtime


def run_full_runtime_flow(
    *,
    model_id: str = "model-1",
    input_metadata: dict[str, object] | None = None,
    executor_id: str = "stub-executor",
) -> tuple[InferenceResponse, ExecutionResult]:
    inference_runtime, ml_runtime = make_inference_and_ml_runtime(executor_id=executor_id)
    return run_inference_and_execute(
        inference_runtime,
        ml_runtime,
        model_id=model_id,
        input_metadata=input_metadata or {"feature_set_id": "dataset-1"},
        executor_id=executor_id,
    )
