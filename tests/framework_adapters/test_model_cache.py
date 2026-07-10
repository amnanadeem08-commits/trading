"""Unit tests for model session cache behavior."""

from __future__ import annotations

import pytest

from framework_adapters import (
    STUB_ADAPTER_ID,
    AdapterRuntimeContext,
    EngineType,
    ModelSessionHealthChecker,
)
from ml_engine_plugins import STUB_ENGINE_ID
from tests.framework_adapters_helpers import make_bootstrapped_adapter_bridge


@pytest.mark.unit
def test_repeated_load_uses_cache_hit() -> None:
    _runtime, bridge, adapter_runtime = make_bootstrapped_adapter_bridge()
    manager = adapter_runtime.model_runtime_manager
    context = AdapterRuntimeContext(
        engine_type=EngineType.STUB,
        artifact_format="stub",
        artifact_reference="artifacts/model.stub",
        model_id="cache-model",
        executor_id=STUB_ENGINE_ID,
        attributes={"artifact_id": "cache-artifact"},
    )
    manager.get_or_load_model(STUB_ADAPTER_ID, context=context)
    manager.get_or_load_model(STUB_ADAPTER_ID, context=context)

    stats = bridge.metrics_collector.statistics()
    assert stats.cache_hits >= 1
    assert stats.cache_misses >= 1
    total = stats.cache_hits + stats.cache_misses
    assert stats.cache_hits / total > 0.0


@pytest.mark.unit
def test_invalidate_cache_by_model_id() -> None:
    _runtime, _bridge, adapter_runtime = make_bootstrapped_adapter_bridge()
    manager = adapter_runtime.model_runtime_manager
    context = AdapterRuntimeContext(
        engine_type=EngineType.STUB,
        artifact_format="stub",
        artifact_reference="artifacts/model.stub",
        model_id="invalidate-model",
        executor_id=STUB_ENGINE_ID,
        attributes={"artifact_id": "invalidate-artifact"},
    )
    manager.load_model(STUB_ADAPTER_ID, context=context)
    removed = manager.invalidate_cache(model_id="invalidate-model")
    assert removed == 1
    assert manager.session_registry.list_records() == ()


@pytest.mark.unit
def test_session_health_reports_ready_state() -> None:
    _runtime, _bridge, adapter_runtime = make_bootstrapped_adapter_bridge()
    manager = adapter_runtime.model_runtime_manager
    context = AdapterRuntimeContext(
        engine_type=EngineType.STUB,
        artifact_format="stub",
        artifact_reference="artifacts/model.stub",
        model_id="health-model",
        executor_id=STUB_ENGINE_ID,
        attributes={"artifact_id": "health-artifact"},
    )
    manager.load_model(STUB_ADAPTER_ID, context=context)
    session_key = manager.build_session_key(STUB_ADAPTER_ID, context=context)
    checker = ModelSessionHealthChecker(
        session_registry=manager.session_registry, warm=manager.warm
    )
    result = checker.check_session(session_key)
    assert result.ready is True
    assert result.loaded is True
    assert result.cached is True
