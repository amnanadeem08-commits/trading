"""Unit tests for ML engine adapter bridge."""

from __future__ import annotations

import pytest

from framework_adapters import (
    AdapterLifecycleEventType,
    AdapterState,
)
from ml_engine_plugins import STUB_ENGINE_ID
from ml_runtime import ExecutorNotFoundError
from tests.framework_adapters_helpers import make_adapter_bridge, make_stub_plugin


@pytest.mark.unit
def test_ml_engine_bridge_process_plugin_registers_executor() -> None:
    runtime, bridge = make_adapter_bridge()
    plugin = make_stub_plugin()
    executor = bridge.process_plugin(plugin)
    assert executor.executor_id() == STUB_ENGINE_ID
    assert runtime.registry.lookup(STUB_ENGINE_ID).executor_id() == STUB_ENGINE_ID
    assert bridge.registry.lookup(STUB_ENGINE_ID).state == AdapterState.LOADED


@pytest.mark.unit
def test_ml_engine_bridge_emits_lifecycle_events() -> None:
    _, bridge = make_adapter_bridge()
    bridge.process_plugin(make_stub_plugin())
    event_types = {event.event_type for event in bridge.lifecycle.events}
    assert AdapterLifecycleEventType.ADAPTER_DISCOVERED in event_types
    assert AdapterLifecycleEventType.ADAPTER_VALIDATED in event_types
    assert AdapterLifecycleEventType.ADAPTER_REGISTERED in event_types
    assert AdapterLifecycleEventType.ADAPTER_LOADED in event_types


@pytest.mark.unit
def test_ml_engine_bridge_shutdown_adapter() -> None:
    runtime, bridge = make_adapter_bridge()
    bridge.process_plugin(make_stub_plugin())
    bridge.shutdown_adapter(STUB_ENGINE_ID)
    assert bridge.registry.lookup(STUB_ENGINE_ID).state == AdapterState.SHUTDOWN
    with pytest.raises(ExecutorNotFoundError):
        runtime.registry.lookup(STUB_ENGINE_ID)
