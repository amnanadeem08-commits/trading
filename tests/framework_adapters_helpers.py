"""Helpers for framework adapter tests."""

from __future__ import annotations

from framework_adapters import (
    AdapterFactory,
    AdapterResolver,
    AdapterRuntime,
    MLEngineAdapterBridge,
    StubFrameworkAdapter,
    bootstrap_adapter_runtime,
    build_adapter_bridge,
    register_stub_adapter_factory,
)
from ml_engine_plugins import STUB_ENGINE_ID, StubMLEnginePlugin, create_stub_engine
from ml_runtime import MLRuntime, build_ml_runtime


def make_adapter_bridge() -> tuple[MLRuntime, MLEngineAdapterBridge]:
    runtime = build_ml_runtime()
    bridge = build_adapter_bridge(runtime)
    return runtime, bridge


def make_bootstrapped_adapter_bridge() -> tuple[MLRuntime, MLEngineAdapterBridge, AdapterRuntime]:
    return bootstrap_adapter_runtime()


def register_stub_adapter_factory_on(factory: AdapterFactory) -> None:
    register_stub_adapter_factory(factory)


def make_stub_plugin(*, plugin_id: str = STUB_ENGINE_ID) -> StubMLEnginePlugin:
    return StubMLEnginePlugin(plugin_id=plugin_id)


def make_stub_framework_adapter(*, adapter_id: str = STUB_ENGINE_ID) -> StubFrameworkAdapter:
    return StubFrameworkAdapter(adapter_id=adapter_id, executor_id=adapter_id)


def make_resolver_with_stub() -> AdapterResolver:
    factory = AdapterFactory()
    register_stub_adapter_factory_on(factory)
    return AdapterResolver(factory=factory)


def make_stub_engine_plugin() -> StubMLEnginePlugin:
    return create_stub_engine()
