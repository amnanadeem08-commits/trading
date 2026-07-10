"""Unit tests for model warm-start behavior."""

from __future__ import annotations

import pytest

from framework_adapters import STUB_ADAPTER_ID, AdapterRuntimeContext, EngineType
from ml_engine_plugins import STUB_ENGINE_ID
from tests.framework_adapters_helpers import make_bootstrapped_adapter_bridge


@pytest.mark.unit
def test_warm_initialize_marks_runtime_warm() -> None:
    _runtime, bridge, adapter_runtime = make_bootstrapped_adapter_bridge()
    manager = adapter_runtime.model_runtime_manager
    manager.warm_initialize(adapter_id=STUB_ADAPTER_ID)
    assert manager.warm is True
    assert manager.lazy_initialized is True
    assert bridge.metrics_collector.statistics().warm_start_duration_ms >= 0.0


@pytest.mark.unit
def test_preload_model_eagerly_loads_session() -> None:
    _runtime, _bridge, adapter_runtime = make_bootstrapped_adapter_bridge()
    manager = adapter_runtime.model_runtime_manager
    context = AdapterRuntimeContext(
        engine_type=EngineType.STUB,
        artifact_format="stub",
        artifact_reference="artifacts/model.stub",
        model_id="warm-model",
        executor_id=STUB_ENGINE_ID,
        attributes={"artifact_id": "warm-artifact"},
    )
    executor = manager.preload_model(STUB_ADAPTER_ID, context=context)
    session_key = manager.build_session_key(STUB_ADAPTER_ID, context=context)
    record = manager.session_registry.lookup(session_key)
    assert executor.executor_id() == STUB_ENGINE_ID
    assert record is not None
    assert record.warm is False or record.cached is True
