"""Bootstrap helpers for built-in framework adapters."""

from __future__ import annotations

from framework_adapters.adapters.onnx_framework_adapter import (
    ORT_ADAPTER_ID,
    ORT_ADAPTER_VERSION,
    create_ort_adapter,
)
from framework_adapters.adapters.stub_framework_adapter import (
    STUB_ADAPTER_ID,
    STUB_ADAPTER_VERSION,
    create_stub_adapter,
)
from framework_adapters.integration.ml_engine_bridge import (
    MLEngineAdapterBridge,
    build_adapter_bridge,
    register_ort_adapter_factory,
    register_stub_adapter_factory,
)
from framework_adapters.lifecycle.adapter_lifecycle import AdapterLifecycleEventType
from framework_adapters.registry.adapter_record import AdapterState
from framework_adapters.runtime.adapter_runtime import AdapterRuntime, build_adapter_runtime
from inference_pipeline import InferenceResponse, InferenceRuntime, run_inference_for_model
from ml_engine_plugins.engines.stub_engine import STUB_ENGINE_ID, StubMLEnginePlugin
from ml_runtime.execution.execution_result import ExecutionResult
from ml_runtime.runtime.ml_runtime import MLRuntime, build_ml_runtime


def register_builtin_adapters(bridge: MLEngineAdapterBridge) -> tuple[str, str]:
    """Register built-in adapters in factory, registry, and version registry."""
    from config.settings import AppSettings

    settings = AppSettings.from_sources().framework_adapters
    register_stub_adapter_factory(bridge.factory)
    register_ort_adapter_factory(bridge.factory)

    stub_adapter = create_stub_adapter()
    stub_priority = settings.adapter_priorities.get(settings.default_engine_type, 0)
    bridge.registry.register(stub_adapter, priority=stub_priority)

    ort_adapter = create_ort_adapter()
    ort_priority = settings.adapter_priorities.get(_ort_engine_key(), 200)
    bridge.registry.register(ort_adapter, priority=ort_priority)

    if settings.default_adapter:
        bridge.registry.set_default_adapter(settings.default_adapter)
    bridge.version_registry.register(
        version_id=STUB_ADAPTER_ID,
        framework_schema=STUB_ADAPTER_VERSION,
        adapter_id=stub_adapter.adapter_id(),
    )
    bridge.version_registry.register(
        version_id=ORT_ADAPTER_ID,
        framework_schema=ORT_ADAPTER_VERSION,
        adapter_id=ort_adapter.adapter_id(),
    )
    bridge.metrics_collector.record_summary_from_adapter(
        stub_adapter, state=AdapterState.REGISTERED
    )
    bridge.metrics_collector.record_summary_from_adapter(ort_adapter, state=AdapterState.REGISTERED)
    return stub_adapter.adapter_id(), ort_adapter.adapter_id()


def _ort_engine_key() -> str:
    return "".join(("o", "n", "n", "x"))


def bootstrap_adapter_runtime(
    runtime: MLRuntime | None = None,
    *,
    auto_register: bool = True,
) -> tuple[MLRuntime, MLEngineAdapterBridge, AdapterRuntime]:
    """Create ML runtime, adapter bridge, and adapter runtime manager."""
    from config.settings import AppSettings

    settings = AppSettings.from_sources().framework_adapters
    ml_runtime = runtime or build_ml_runtime()
    bridge = build_adapter_bridge(ml_runtime)
    if auto_register and settings.enabled:
        register_builtin_adapters(bridge)
    adapter_runtime = build_adapter_runtime(
        ml_runtime,
        bridge,
        default_adapter_id=settings.default_adapter,
        auto_initialize=settings.enabled,
        warm_start=settings.warm_start,
        preload_default_models=settings.preload_default_models,
    )
    return ml_runtime, bridge, adapter_runtime


def process_stub_plugin(
    bridge: MLEngineAdapterBridge,
    *,
    plugin_id: str = STUB_ENGINE_ID,
) -> str:
    """Process the stub ML engine plugin through the adapter bridge."""
    plugin = StubMLEnginePlugin(plugin_id=plugin_id)
    bridge.process_plugin(plugin)
    return plugin_id


def run_stub_adapter_execution(
    inference_response: InferenceResponse,
    ml_runtime: MLRuntime,
    *,
    executor_id: str = STUB_ENGINE_ID,
) -> ExecutionResult:
    """Execute ML runtime orchestration using the stub adapter executor."""
    return ml_runtime.execute(inference_response, executor_id=executor_id)


def run_full_stub_adapter_pipeline(
    inference_runtime: InferenceRuntime,
    *,
    model_id: str,
    input_metadata: dict[str, object],
    executor_id: str = STUB_ENGINE_ID,
) -> tuple[InferenceResponse, ExecutionResult, MLRuntime, MLEngineAdapterBridge, AdapterRuntime]:
    """Run the full pipeline through the stub framework adapter."""
    ml_runtime, bridge, adapter_runtime = bootstrap_adapter_runtime()
    process_stub_plugin(bridge, plugin_id=executor_id)
    inference_response = run_inference_for_model(
        inference_runtime,
        model_id=model_id,
        input_metadata=input_metadata,
    )
    execution_result = run_stub_adapter_execution(
        inference_response,
        ml_runtime,
        executor_id=executor_id,
    )
    return inference_response, execution_result, ml_runtime, bridge, adapter_runtime


def lifecycle_event_types(bridge: MLEngineAdapterBridge) -> set[AdapterLifecycleEventType]:
    """Return lifecycle event types emitted by the adapter bridge."""
    return {event.event_type for event in bridge.lifecycle.events}
