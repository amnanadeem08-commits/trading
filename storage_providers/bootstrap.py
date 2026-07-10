"""Bootstrap helpers for storage provider integration."""

from __future__ import annotations

from artifact_management import FrameworkAdapterArtifactBridge, bootstrap_artifact_runtime
from artifact_management.lifecycle.artifact_lifecycle import ArtifactLifecycleEventType
from framework_adapters import MLEngineAdapterBridge
from inference_pipeline import InferenceResponse, InferenceRuntime, run_inference_for_model
from ml_engine_plugins.engines.stub_engine import STUB_ENGINE_ID
from ml_runtime.execution.execution_result import ExecutionResult
from ml_runtime.runtime.ml_runtime import MLRuntime
from storage_providers.integration.artifact_management_bridge import (
    ArtifactManagementStorageBridge,
    build_storage_bridge,
)
from storage_providers.lifecycle.provider_lifecycle import ProviderLifecycleEventType


def bootstrap_storage_runtime(
    runtime: MLRuntime | None = None,
) -> tuple[
    MLRuntime,
    MLEngineAdapterBridge,
    FrameworkAdapterArtifactBridge,
    ArtifactManagementStorageBridge,
]:
    """Bootstrap ML runtime, adapter bridge, artifact bridge, and storage bridge."""
    ml_runtime, adapter_bridge, artifact_bridge = bootstrap_artifact_runtime(runtime)
    storage_bridge = build_storage_bridge(artifact_bridge=artifact_bridge)
    return ml_runtime, adapter_bridge, artifact_bridge, storage_bridge


def run_storage_provider_execution(
    inference_response: InferenceResponse,
    ml_runtime: MLRuntime,
    *,
    executor_id: str = STUB_ENGINE_ID,
) -> ExecutionResult:
    """Execute ML runtime orchestration after storage provider resolution."""
    return ml_runtime.execute(inference_response, executor_id=executor_id)


def run_full_storage_provider_pipeline(
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
    ArtifactManagementStorageBridge,
]:
    """Run inference through storage provider and artifact resolution."""
    ml_runtime, adapter_bridge, artifact_bridge, storage_bridge = bootstrap_storage_runtime()
    from framework_adapters import process_stub_plugin

    process_stub_plugin(adapter_bridge, plugin_id=executor_id)
    inference_response = run_inference_for_model(
        inference_runtime,
        model_id=model_id,
        input_metadata=input_metadata,
    )
    execution_result = run_storage_provider_execution(
        inference_response,
        ml_runtime,
        executor_id=executor_id,
    )
    storage_bridge.shutdown_default_providers()
    return (
        inference_response,
        execution_result,
        ml_runtime,
        adapter_bridge,
        artifact_bridge,
        storage_bridge,
    )


def provider_lifecycle_event_types(
    bridge: ArtifactManagementStorageBridge,
) -> set[ProviderLifecycleEventType]:
    """Return lifecycle event types emitted by the storage bridge."""
    return {event.event_type for event in bridge.provider_lifecycle.events}


def artifact_lifecycle_event_types(
    bridge: ArtifactManagementStorageBridge,
) -> set[ArtifactLifecycleEventType]:
    """Return artifact lifecycle event types from the nested artifact bridge."""
    return {event.event_type for event in bridge.artifact_lifecycle.events}
