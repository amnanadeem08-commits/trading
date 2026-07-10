"""Unit tests for the concrete stub ML engine."""

from __future__ import annotations

import pytest

from ml_engine_plugins import (
    STUB_ENGINE_ID,
    STUB_ENGINE_VERSION,
    StubModelExecutor,
    bootstrap_plugin_runtime,
    create_stub_engine,
    register_builtin_plugins,
)
from ml_engine_plugins.plugin_capability import PluginCapability
from ml_runtime.runtime.runtime_context import RuntimeContext


@pytest.mark.unit
def test_stub_engine_plugin_contract() -> None:
    plugin = create_stub_engine()
    assert plugin.plugin_id() == STUB_ENGINE_ID
    assert plugin.metadata().version == STUB_ENGINE_VERSION
    assert PluginCapability.EXECUTE in plugin.capabilities()


@pytest.mark.unit
def test_stub_model_executor_lifecycle() -> None:
    executor = StubModelExecutor()
    executor.load(artifact_reference="artifact-1", metadata={"model_id": "model-1"})
    assert executor.loaded is True
    assert executor.load_count == 1
    assert executor.health()["status"] == "healthy"
    executor.unload()
    assert executor.loaded is False
    assert executor.unload_count == 1


@pytest.mark.unit
def test_stub_model_executor_execute_metadata_only() -> None:
    executor = StubModelExecutor()
    context = RuntimeContext(
        session_id="session-1",
        request_id="req-1",
        model_id="model-1",
        model_version="v-1",
        artifact_reference="artifact-1",
        executor_id=STUB_ENGINE_ID,
        input_metadata={"id": "1"},
        correlation_id="c",
        trace_id="t",
    )
    result = executor.execute(context)
    assert result.metadata is not None
    assert result.metadata.attributes.get("engine_type") == "stub"
    assert "prediction" not in result.model_dump()


@pytest.mark.unit
def test_bootstrap_registers_stub_engine() -> None:
    runtime, bridge = bootstrap_plugin_runtime()
    assert runtime.registry.metadata(STUB_ENGINE_ID) is not None
    assert bridge.registry.lookup(STUB_ENGINE_ID).plugin_id == STUB_ENGINE_ID


@pytest.mark.unit
def test_register_builtin_plugins_only_stub() -> None:
    from ml_engine_plugins import build_plugin_bridge
    from ml_runtime import build_ml_runtime

    runtime = build_ml_runtime()
    bridge = build_plugin_bridge(runtime)
    register_builtin_plugins(bridge)
    discovered = bridge.discovery.discover()
    assert len(discovered) == 1
    assert discovered[0].plugin_id() == STUB_ENGINE_ID
