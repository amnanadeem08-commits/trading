"""Bootstrap helpers for built-in ML engine plugins."""

from __future__ import annotations

from inference_pipeline import InferenceResponse, InferenceRuntime, run_inference_for_model
from ml_engine_plugins.engines.stub_engine import STUB_ENGINE_ID, create_stub_engine
from ml_engine_plugins.ml_runtime_bridge import MLRuntimePluginBridge, build_plugin_bridge
from ml_engine_plugins.plugin_lifecycle import PluginLifecycleEventType
from ml_runtime.execution.execution_result import ExecutionResult
from ml_runtime.runtime.ml_runtime import MLRuntime, build_ml_runtime


def register_builtin_plugins(bridge: MLRuntimePluginBridge) -> None:
    """Register built-in ML engine plugin providers."""
    bridge.register_provider(create_stub_engine())


def bootstrap_plugin_runtime(
    runtime: MLRuntime | None = None,
    *,
    auto_discover: bool = True,
) -> tuple[MLRuntime, MLRuntimePluginBridge]:
    """Create ML runtime and bootstrap the default stub engine plugin."""
    ml_runtime = runtime or build_ml_runtime()
    bridge = build_plugin_bridge(ml_runtime)
    register_builtin_plugins(bridge)
    if auto_discover:
        bridge.discover_and_load()
    return ml_runtime, bridge


def run_stub_engine_execution(
    inference_response: InferenceResponse,
    ml_runtime: MLRuntime,
    *,
    executor_id: str = STUB_ENGINE_ID,
) -> ExecutionResult:
    """Execute ML runtime orchestration using the stub engine executor."""
    return ml_runtime.execute(inference_response, executor_id=executor_id)


def run_full_stub_engine_pipeline(
    inference_runtime: InferenceRuntime,
    *,
    model_id: str,
    input_metadata: dict[str, object],
    executor_id: str = STUB_ENGINE_ID,
) -> tuple[InferenceResponse, ExecutionResult, MLRuntime, MLRuntimePluginBridge]:
    """Run the full pipeline through the stub ML engine plugin."""
    ml_runtime, bridge = bootstrap_plugin_runtime()
    inference_response = run_inference_for_model(
        inference_runtime,
        model_id=model_id,
        input_metadata=input_metadata,
    )
    execution_result = run_stub_engine_execution(
        inference_response,
        ml_runtime,
        executor_id=executor_id,
    )
    return inference_response, execution_result, ml_runtime, bridge


def lifecycle_event_types(bridge: MLRuntimePluginBridge) -> set[PluginLifecycleEventType]:
    """Return lifecycle event types emitted by the bridge."""
    return {event.event_type for event in bridge.lifecycle.events}
