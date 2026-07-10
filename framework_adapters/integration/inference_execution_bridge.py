"""Bridge inference execution pipeline to adapter runtime."""

from __future__ import annotations

from typing import Any

from framework_adapters import AdapterRuntime, AdapterRuntimeContext
from framework_adapters.adapters.ort_executor import _ort_engine_value
from inference_pipeline.responses.inference_response import InferenceResponse
from inference_pipeline.runtime.execution_router import ExecutionOutcomeAdapter, ExecutionRouter
from inference_pipeline.runtime.inference_context import InferenceExecutionContext
from ml_runtime.execution.execution_result import ExecutionStatus


def _resolve_engine_type() -> Any:
    from framework_adapters import EngineType

    target = _ort_engine_value()
    return next(item for item in EngineType if item.value == target)


class AdapterRuntimeExecutionRouter:
    """Routes orchestrated inference through AdapterRuntime."""

    def __init__(self, *, adapter_runtime: AdapterRuntime) -> None:
        self._adapter_runtime = adapter_runtime

    def route(
        self,
        inference_response: InferenceResponse,
        *,
        execution_context: InferenceExecutionContext,
        bound_input: dict[str, object],
    ) -> ExecutionOutcomeAdapter:
        metadata = inference_response.metadata
        context = AdapterRuntimeContext(
            engine_type=_resolve_engine_type(),
            artifact_format=str(bound_input.get("artifact_format", "ort")),
            artifact_reference=str(bound_input.get("artifact_reference", metadata.artifact_id)),
            model_id=execution_context.model_id,
            model_version=metadata.version_id,
            executor_id=execution_context.adapter_id,
            attributes={
                "artifact_id": execution_context.artifact_id or metadata.artifact_id,
                "checksum": metadata.checksum,
                "checksum_verified": True,
                "location": bound_input.get("location", {}),
                **bound_input,
            },
        )
        result = self._adapter_runtime.route_execution(inference_response, context=context)
        status = "completed" if result.status == ExecutionStatus.COMPLETED else "failed"
        attributes: dict[str, object] = {}
        if result.metadata is not None:
            attributes = dict(result.metadata.attributes)
        return ExecutionOutcomeAdapter(
            status=status,
            message=result.message,
            attributes=attributes,
        )


def build_execution_router(adapter_runtime: AdapterRuntime) -> ExecutionRouter:
    """Create an execution router backed by AdapterRuntime."""
    return AdapterRuntimeExecutionRouter(adapter_runtime=adapter_runtime)
