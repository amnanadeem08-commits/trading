"""Helpers for ML engine plugin tests."""

from __future__ import annotations

from ml_engine_plugins import (
    STUB_ENGINE_ID,
    MLRuntimePluginBridge,
    StubMLEnginePlugin,
    StubModelExecutor,
    bootstrap_plugin_runtime,
    build_plugin_bridge,
)
from ml_runtime import MLRuntime, build_ml_runtime

# Backward-compatible aliases for tests written during Task 11.
StubPluginExecutor = StubModelExecutor
StubMLPlugin = StubMLEnginePlugin


def make_plugin_bridge(
    *,
    plugin_id: str = STUB_ENGINE_ID,
) -> tuple[MLRuntime, MLRuntimePluginBridge]:
    runtime = build_ml_runtime()
    bridge = build_plugin_bridge(runtime)
    return runtime, bridge


def register_stub_plugin(
    bridge: MLRuntimePluginBridge,
    *,
    plugin_id: str = STUB_ENGINE_ID,
) -> tuple[str, ...]:
    bridge.register_provider(StubMLEnginePlugin(plugin_id=plugin_id))
    return bridge.discover_and_load()


def make_bootstrapped_runtime() -> tuple[MLRuntime, MLRuntimePluginBridge]:
    return bootstrap_plugin_runtime()
