"""Unit tests for adapter runtime manager."""

from __future__ import annotations

import pytest

from framework_adapters import (
    STUB_ADAPTER_ID,
    AdapterLifecycleEventType,
    AdapterResolutionError,
    AdapterRuntimeContext,
    AdapterState,
    AdapterValidationError,
    EngineType,
    MetadataFrameworkAdapter,
)
from ml_engine_plugins import STUB_ENGINE_ID
from tests.framework_adapters_helpers import make_bootstrapped_adapter_bridge


@pytest.mark.unit
def test_adapter_runtime_initializes_and_emits_lifecycle() -> None:
    _runtime, bridge, adapter_runtime = make_bootstrapped_adapter_bridge()
    assert adapter_runtime.initialized is True
    event_types = {event.event_type for event in bridge.lifecycle.events}
    assert AdapterLifecycleEventType.ADAPTER_INITIALIZED in event_types


@pytest.mark.unit
def test_adapter_runtime_selects_by_engine_type_and_priority() -> None:
    _runtime, bridge, adapter_runtime = make_bootstrapped_adapter_bridge()
    custom_adapter = MetadataFrameworkAdapter(
        adapter_id="custom-runtime-adapter",
        name="Custom Runtime Adapter",
        version="1.0.0",
        engine_type=EngineType.CUSTOM,
        supported_artifact_formats=("binary",),
        priority=50,
    )
    adapter_runtime.register_adapter(custom_adapter, priority=50)

    context = AdapterRuntimeContext(
        engine_type=EngineType.CUSTOM,
        artifact_format="binary",
        model_id="model-1",
    )
    selected = adapter_runtime.select_adapter(context)
    assert selected == "custom-runtime-adapter"

    stats = bridge.metrics_collector.statistics()
    assert stats.adapter_usage >= 1
    assert stats.adapter_selection_latency_ms >= 0.0


@pytest.mark.unit
def test_adapter_runtime_selects_default_stub_adapter() -> None:
    _runtime, bridge, adapter_runtime = make_bootstrapped_adapter_bridge()
    context = AdapterRuntimeContext(engine_type=EngineType.STUB, artifact_format="stub")
    selected = adapter_runtime.select_adapter(context)
    assert selected == STUB_ADAPTER_ID
    assert bridge.registry.get_default_adapter_id() == STUB_ADAPTER_ID


@pytest.mark.unit
def test_adapter_runtime_load_and_unload_adapter() -> None:
    _runtime, bridge, adapter_runtime = make_bootstrapped_adapter_bridge()
    context = AdapterRuntimeContext(
        engine_type=EngineType.STUB,
        artifact_format="stub",
        artifact_reference="artifacts/model.stub",
        model_id="model-1",
        executor_id=STUB_ENGINE_ID,
    )
    adapter_id = adapter_runtime.select_adapter(context)
    executor = adapter_runtime.load_adapter(adapter_id, context=context)
    assert executor.executor_id() == STUB_ENGINE_ID

    event_types = {event.event_type for event in bridge.lifecycle.events}
    assert AdapterLifecycleEventType.ADAPTER_SELECTED in event_types
    assert AdapterLifecycleEventType.ADAPTER_LOADED in event_types

    stats = bridge.metrics_collector.statistics()
    assert stats.adapter_loads >= 1
    assert stats.adapter_load_time_ms >= 0.0

    adapter_runtime.unload_adapter(adapter_id)
    assert AdapterLifecycleEventType.ADAPTER_UNLOADED in {
        event.event_type for event in bridge.lifecycle.events
    }


@pytest.mark.unit
def test_adapter_runtime_rejects_unknown_engine_type() -> None:
    _runtime, _bridge, adapter_runtime = make_bootstrapped_adapter_bridge()
    context = AdapterRuntimeContext(engine_type=EngineType.TENSORFLOW)
    with pytest.raises(AdapterResolutionError):
        adapter_runtime.select_adapter(context)


@pytest.mark.unit
def test_adapter_runtime_shutdown_clears_state() -> None:
    _runtime, bridge, adapter_runtime = make_bootstrapped_adapter_bridge()
    adapter_runtime.shutdown()
    assert adapter_runtime.initialized is False
    for record in bridge.registry.list():
        assert record.state == AdapterState.SHUTDOWN


@pytest.mark.unit
def test_adapter_runtime_rejects_incompatible_artifact_format() -> None:
    _runtime, bridge, adapter_runtime = make_bootstrapped_adapter_bridge()
    adapter_runtime.register_adapter(
        MetadataFrameworkAdapter(
            adapter_id="format-adapter",
            name="Format Adapter",
            version="1.0.0",
            engine_type=EngineType.CUSTOM,
            supported_artifact_formats=("binary",),
            priority=10,
        )
    )
    context = AdapterRuntimeContext(
        engine_type=EngineType.CUSTOM,
        artifact_format="unsupported",
    )
    with pytest.raises(AdapterValidationError):
        adapter_runtime.select_adapter(context)

    stats = bridge.metrics_collector.statistics()
    assert stats.adapter_failures >= 1
