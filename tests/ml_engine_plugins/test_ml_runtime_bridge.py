"""Unit tests for ML runtime plugin bridge."""

from __future__ import annotations

import pytest

from ml_engine_plugins import MLRuntimePluginBridge
from tests.ml_engine_plugins_helpers import make_plugin_bridge, register_stub_plugin


@pytest.mark.unit
def test_plugin_bridge_registers_with_runtime() -> None:
    runtime, bridge = make_plugin_bridge()
    registered = register_stub_plugin(bridge)
    assert registered == ("stub-engine",)
    assert len(runtime.registry.list()) == 1


@pytest.mark.unit
def test_plugin_bridge_callback_registration() -> None:
    from ml_runtime import build_ml_runtime

    runtime = build_ml_runtime()
    calls: list[str] = []

    def callback(executor: object, name: str, version: str, capabilities: tuple[str, ...]) -> None:
        _ = name, version, capabilities
        calls.append(executor.executor_id())

    bridge = MLRuntimePluginBridge(runtime, registration_callback=callback)
    bridge.register_provider(
        __import__("tests.ml_engine_plugins_helpers", fromlist=["StubMLPlugin"]).StubMLPlugin(
            plugin_id="callback-engine"
        )
    )
    bridge.discover_and_load()
    assert calls == ["callback-engine"]
