"""Unit tests for model runtime manager."""

from __future__ import annotations

import pytest

from framework_adapters import (
    STUB_ADAPTER_ID,
    AdapterLifecycleEventType,
    AdapterRuntimeContext,
    AdapterValidationError,
    EngineType,
    ModelRuntimeState,
)
from ml_engine_plugins import STUB_ENGINE_ID
from tests.framework_adapters_helpers import make_bootstrapped_adapter_bridge


def _stub_context(
    *, model_id: str = "model-1", artifact_id: str = "artifact-1"
) -> AdapterRuntimeContext:
    return AdapterRuntimeContext(
        engine_type=EngineType.STUB,
        artifact_format="stub",
        artifact_reference="artifacts/model.stub",
        model_id=model_id,
        model_version="1.0.0",
        executor_id=STUB_ENGINE_ID,
        attributes={"artifact_id": artifact_id},
    )


@pytest.mark.unit
def test_model_runtime_manager_loads_and_caches_session() -> None:
    _runtime, bridge, adapter_runtime = make_bootstrapped_adapter_bridge()
    manager = adapter_runtime.model_runtime_manager
    context = _stub_context()

    first = manager.get_or_load_model(STUB_ADAPTER_ID, context=context)
    second = manager.get_or_load_model(STUB_ADAPTER_ID, context=context)

    assert first.executor_id() == STUB_ENGINE_ID
    assert second.executor_id() == STUB_ENGINE_ID
    session_key = manager.build_session_key(STUB_ADAPTER_ID, context=context)
    record = manager.session_registry.lookup(session_key)
    assert record is not None
    assert record.state == ModelRuntimeState.READY
    assert record.cached is True

    stats = bridge.metrics_collector.statistics()
    assert stats.model_load_count >= 1
    assert stats.cache_hits >= 1
    assert stats.session_reuse_count >= 1

    event_types = {event.event_type for event in bridge.lifecycle.events}
    assert AdapterLifecycleEventType.MODEL_LOADING in event_types
    assert AdapterLifecycleEventType.MODEL_READY in event_types
    assert AdapterLifecycleEventType.MODEL_REUSED in event_types


@pytest.mark.unit
def test_model_runtime_manager_unloads_session() -> None:
    _runtime, bridge, adapter_runtime = make_bootstrapped_adapter_bridge()
    manager = adapter_runtime.model_runtime_manager
    context = _stub_context()
    manager.load_model(STUB_ADAPTER_ID, context=context)
    session_key = manager.build_session_key(STUB_ADAPTER_ID, context=context)
    manager.unload_model(session_key, force=True)
    assert manager.session_registry.lookup(session_key) is None

    stats = bridge.metrics_collector.statistics()
    assert stats.model_unload_count >= 1
    assert AdapterLifecycleEventType.MODEL_UNLOADED in {
        event.event_type for event in bridge.lifecycle.events
    }


@pytest.mark.unit
def test_model_runtime_manager_warm_and_lazy_initialize() -> None:
    _runtime, bridge, adapter_runtime = make_bootstrapped_adapter_bridge()
    manager = adapter_runtime.model_runtime_manager
    manager.lazy_initialize()
    assert manager.lazy_initialized is True
    manager.warm_initialize(adapter_id=STUB_ADAPTER_ID)
    assert manager.warm is True
    assert bridge.metrics_collector.statistics().warm_start_duration_ms >= 0.0


@pytest.mark.unit
def test_model_runtime_manager_rejects_unverified_checksum() -> None:
    _runtime, bridge, adapter_runtime = make_bootstrapped_adapter_bridge()
    manager = adapter_runtime.model_runtime_manager
    context = _stub_context()
    context = context.model_copy(
        update={
            "attributes": {
                "artifact_id": "artifact-1",
                "checksum": "abc",
                "checksum_verified": False,
            }
        }
    )
    with pytest.raises(AdapterValidationError):
        manager.load_model(STUB_ADAPTER_ID, context=context)

    stats = bridge.metrics_collector.statistics()
    assert stats.failed_model_loads >= 1
    assert AdapterLifecycleEventType.MODEL_LOAD_FAILED in {
        event.event_type for event in bridge.lifecycle.events
    }
