"""Bootstrap helpers for artifact management integration."""

from __future__ import annotations

from artifact_management.integration.framework_adapter_bridge import (
    FrameworkAdapterArtifactBridge,
    build_artifact_bridge,
)
from artifact_management.lifecycle.artifact_lifecycle import ArtifactLifecycleEventType
from framework_adapters import MLEngineAdapterBridge, bootstrap_adapter_runtime, process_stub_plugin
from inference_pipeline import InferenceResponse, InferenceRuntime, run_inference_for_model
from ml_engine_plugins.engines.stub_engine import STUB_ENGINE_ID
from ml_runtime.execution.execution_result import ExecutionResult
from ml_runtime.runtime.ml_runtime import MLRuntime


def bootstrap_artifact_runtime(
    runtime: MLRuntime | None = None,
) -> tuple[MLRuntime, MLEngineAdapterBridge, FrameworkAdapterArtifactBridge]:
    """Bootstrap ML runtime, adapter bridge, and artifact bridge."""
    ml_runtime, adapter_bridge, _adapter_runtime = bootstrap_adapter_runtime(runtime)
    artifact_bridge = build_artifact_bridge()
    return ml_runtime, adapter_bridge, artifact_bridge


def run_artifact_adapter_execution(
    inference_response: InferenceResponse,
    ml_runtime: MLRuntime,
    *,
    executor_id: str = STUB_ENGINE_ID,
) -> ExecutionResult:
    """Execute ML runtime orchestration using an artifact-loaded executor."""
    return ml_runtime.execute(inference_response, executor_id=executor_id)


def run_full_artifact_adapter_pipeline(
    inference_runtime: InferenceRuntime,
    *,
    model_id: str,
    input_metadata: dict[str, object],
    executor_id: str = STUB_ENGINE_ID,
) -> tuple[
    InferenceResponse,
    ExecutionResult,
    MLRuntime,
    MLEngineAdapterBridge,
    FrameworkAdapterArtifactBridge,
]:
    """Run inference through artifact resolution and adapter loading."""
    ml_runtime, adapter_bridge, artifact_bridge = bootstrap_artifact_runtime()
    process_stub_plugin(adapter_bridge, plugin_id=executor_id)
    inference_response = run_inference_for_model(
        inference_runtime,
        model_id=model_id,
        input_metadata=input_metadata,
    )
    execution_result = run_artifact_adapter_execution(
        inference_response,
        ml_runtime,
        executor_id=executor_id,
    )
    return inference_response, execution_result, ml_runtime, adapter_bridge, artifact_bridge


def lifecycle_event_types(
    bridge: FrameworkAdapterArtifactBridge,
) -> set[ArtifactLifecycleEventType]:
    """Return lifecycle event types emitted by the artifact bridge."""
    return {event.event_type for event in bridge.lifecycle.events}
