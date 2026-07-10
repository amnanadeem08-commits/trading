"""Unit tests for model reload behavior."""

from __future__ import annotations

import pytest

from framework_adapters import (
    STUB_ADAPTER_ID,
    AdapterLifecycleEventType,
    AdapterRuntimeContext,
    EngineType,
    ModelRuntimeState,
)
from framework_adapters.adapters.stub_executor_factory import StubExecutorFactory
from ml_engine_plugins import STUB_ENGINE_ID
from tests.framework_adapters_helpers import make_bootstrapped_adapter_bridge


@pytest.mark.unit
def test_reload_model_replaces_cached_session() -> None:
    _runtime, bridge, adapter_runtime = make_bootstrapped_adapter_bridge()
    manager = adapter_runtime.model_runtime_manager
    context = AdapterRuntimeContext(
        engine_type=EngineType.STUB,
        artifact_format="stub",
        artifact_reference="artifacts/model.stub",
        model_id="model-1",
        model_version="1.0.0",
        executor_id=STUB_ENGINE_ID,
        attributes={"artifact_id": "artifact-1"},
    )
    manager.load_model(STUB_ADAPTER_ID, context=context)
    session_key = manager.build_session_key(STUB_ADAPTER_ID, context=context)

    updated_context = context.model_copy(update={"model_version": "2.0.0"})
    new_key = manager.build_session_key(STUB_ADAPTER_ID, context=updated_context)
    manager.reload_model(session_key, context=updated_context, adapter_id=STUB_ADAPTER_ID)

    old_record = manager.session_registry.lookup(session_key)
    new_record = manager.session_registry.lookup(new_key)
    assert old_record is None
    assert new_record is not None
    assert new_record.state == ModelRuntimeState.READY
    assert new_record.model_version == "2.0.0"

    stats = bridge.metrics_collector.statistics()
    assert stats.model_reload_count >= 1
    assert AdapterLifecycleEventType.MODEL_RELOADED in {
        event.event_type for event in bridge.lifecycle.events
    }


@pytest.mark.unit
def test_replace_session_updates_executor() -> None:
    _runtime, _bridge, adapter_runtime = make_bootstrapped_adapter_bridge()
    manager = adapter_runtime.model_runtime_manager
    context = AdapterRuntimeContext(
        engine_type=EngineType.STUB,
        artifact_format="stub",
        artifact_reference="artifacts/model.stub",
        model_id="model-2",
        executor_id=STUB_ENGINE_ID,
        attributes={"artifact_id": "artifact-2"},
    )
    manager.load_model(STUB_ADAPTER_ID, context=context)
    session_key = manager.build_session_key(STUB_ADAPTER_ID, context=context)
    replacement = StubExecutorFactory().create(executor_id="replacement-executor")
    updated = manager.replace_session(session_key, executor=replacement)
    assert updated.state == ModelRuntimeState.READY
    assert (
        manager.session_registry.get_executor(session_key).executor_id() == "replacement-executor"
    )
